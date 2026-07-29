"""Parse NCBI EFetch XML into normalized PubMedRecord objects."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from xml.etree import ElementTree as ET

from src.pubmed.models import PubMedRecord


PMID_RE = re.compile(r"^[1-9]\d*$")

# Priority matters: PubMed records may carry both a specific type and "Review".
STUDY_TYPE_PRIORITY: tuple[tuple[str, str], ...] = (
    ("Meta-Analysis", "meta-analysis"),
    ("Systematic Review", "systematic review"),
    ("Randomized Controlled Trial", "randomized controlled trial"),
    ("Controlled Clinical Trial", "controlled clinical trial"),
    ("Clinical Trial", "clinical trial"),
    ("Observational Study", "observational study"),
    ("Cohort Studies", "cohort study"),
    ("Case-Control Studies", "case-control study"),
    ("Cross-Sectional Studies", "cross-sectional study"),
    ("Practice Guideline", "practice guideline"),
    ("Guideline", "guideline"),
    ("Consensus Development Conference", "consensus"),
    ("Review", "review"),
)


def parse_efetch_xml(xml_text: str) -> list[PubMedRecord]:
    """Parse an EFetch XML response into deduplicated validated records.

    A malformed XML body or invalid PMID is an explicit failure. Duplicate
    PubMedArticle entries are deduplicated by PMID while preserving first-seen
    order.
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"Malformed PubMed XML: {exc}") from exc

    records: list[PubMedRecord] = []
    seen_pmids: set[str] = set()

    for article in root.findall(".//PubmedArticle"):
        pmid_el = article.find("./MedlineCitation/PMID")
        if pmid_el is None or not pmid_el.text:
            raise ValueError("PubMedArticle is missing its MedlineCitation PMID.")
        pmid = pmid_el.text.strip()
        if not PMID_RE.fullmatch(pmid):
            raise ValueError(f"Invalid PMID in EFetch response: {pmid!r}")
        if pmid in seen_pmids:
            continue
        seen_pmids.add(pmid)
        records.append(_article_to_record(article, pmid))

    return records


def _article_to_record(article: ET.Element, pmid: str) -> PubMedRecord:
    title = _get_text(article, ".//ArticleTitle")

    abstract_parts: list[str] = []
    abstract_el = article.find(".//Abstract")
    if abstract_el is not None:
        for text_el in abstract_el.findall("AbstractText"):
            label = (text_el.get("Label") or "").strip()
            text = " ".join(" ".join(text_el.itertext()).split())
            if text:
                abstract_parts.append(f"{label}: {text}" if label else text)
    abstract = "\n\n".join(abstract_parts) if abstract_parts else None

    return PubMedRecord(
        pmid=pmid,
        title=title,
        abstract=abstract,
        authors=_format_authors(article),
        journal=_get_text(article, ".//Journal/Title")
        or _get_text(article, ".//Journal/ISOAbbreviation"),
        publication_year=_extract_year(article),
        publication_types=_extract_publication_types(article),
        doi=_extract_doi(article),
        mesh_terms=_extract_mesh_terms(article),
        language=_get_text(article, ".//Language"),
        source_url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        retrieved_at=datetime.now(timezone.utc),
    )


def _get_text(parent: ET.Element, path: str) -> str | None:
    el = parent.find(path)
    if el is None:
        return None
    text = " ".join(" ".join(el.itertext()).split())
    return text or None


def _format_authors(article: ET.Element) -> str | None:
    author_list = article.find(".//AuthorList")
    if author_list is None:
        return None

    parts: list[str] = []
    for author in author_list.findall("Author"):
        collective = _get_text(author, "CollectiveName")
        if collective:
            parts.append(collective)
            continue
        last = _get_text(author, "LastName") or ""
        initials = _get_text(author, "Initials") or ""
        if last:
            parts.append(f"{last} {initials}".strip())

    return ", ".join(parts) if parts else None


def _extract_year(article: ET.Element) -> int | None:
    for path in (
        ".//PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubMedPubDate[@PubStatus='pubmed']/Year",
        ".//PubMedPubDate[@PubStatus='entrez']/Year",
    ):
        value = _get_text(article, path)
        if value:
            try:
                year = int(value)
            except ValueError:
                continue
            if 1800 <= year <= 2100:
                return year

    medline_date = _get_text(article, ".//PubDate/MedlineDate")
    if medline_date:
        match = re.search(r"\b(?:18|19|20)\d{2}\b", medline_date)
        if match:
            return int(match.group(0))
    return None


def _extract_publication_types(article: ET.Element) -> list[str]:
    type_list = article.find(".//PublicationTypeList")
    if type_list is None:
        return []
    result: list[str] = []
    for item in type_list.findall("PublicationType"):
        text = " ".join(" ".join(item.itertext()).split())
        if text:
            result.append(text)
    return result


def _extract_doi(article: ET.Element) -> str | None:
    for article_id in article.findall(".//ArticleIdList/ArticleId"):
        if article_id.get("IdType") == "doi" and article_id.text:
            return article_id.text.strip()
    return None


def _extract_mesh_terms(article: ET.Element) -> list[str]:
    headings = article.find(".//MeshHeadingList")
    if headings is None:
        return []
    terms: list[str] = []
    for heading in headings.findall("MeshHeading"):
        descriptor = heading.find("DescriptorName")
        if descriptor is not None:
            text = " ".join(" ".join(descriptor.itertext()).split())
            if text:
                terms.append(text)
    return terms


def _title_mentions_randomized(title: str | None) -> bool:
    title_lower = (title or "").lower()
    if re.search(r"\bnon[- ]?randomi[sz]ed\b", title_lower):
        return False
    return bool(re.search(r"\brandomi[sz]ed\b", title_lower))


def infer_study_type(
    publication_types: list[str], title: str | None = None
) -> str:
    """Infer a concise study-type label from NLM metadata."""
    type_set = set(publication_types)
    for publication_type, label in STUDY_TYPE_PRIORITY:
        if publication_type in type_set:
            return label

    title_lower = (title or "").lower()
    if "meta-analysis" in title_lower:
        return "meta-analysis"
    if "systematic review" in title_lower:
        return "systematic review"
    if _title_mentions_randomized(title):
        return "randomized controlled trial"
    if "cohort" in title_lower:
        return "cohort study"
    return "not_reported"


def infer_evidence_level(
    publication_types: list[str], title: str | None = None
) -> str:
    """Map reported NLM types to the project's evidence vocabulary."""
    pts = {pt.lower() for pt in publication_types}
    if "meta-analysis" in pts or "systematic review" in pts:
        return "systematic review / meta-analysis"
    if "randomized controlled trial" in pts or _title_mentions_randomized(title):
        return "randomized controlled trial"
    if {
        "observational study",
        "cohort studies",
        "case-control studies",
        "cross-sectional studies",
    } & pts:
        return "observational study"
    if {
        "guideline",
        "practice guideline",
        "consensus development conference",
    } & pts:
        return "expert guidance / consensus"
    if "review" in pts:
        return "review / nonsystematic"
    return "not_reported"
