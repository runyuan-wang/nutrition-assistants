"""Strict claim-slide-PMID traceability for PubMed mode."""

from __future__ import annotations

import re

from pydantic import BaseModel, Field

from src.pubmed.models import PubMedRecord
from src.schemas.lesson import CitationRecord, LessonPackage, LessonSlide, ReferenceType


PMID_RE = re.compile(r"^[1-9]\d*$")


class ClaimTraceEntry(BaseModel):
    """Traceability mapping for a single health claim."""

    claim_id: str
    claim_text: str
    supporting_pmids: list[str] = Field(default_factory=list)
    slide_numbers: list[int] = Field(default_factory=list)
    traceability_status: str = Field(
        default="traceable",
        pattern="^(traceable|untraceable|warning)$",
    )
    warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class EvidenceTraceabilityReport(BaseModel):
    """Overall traceability report for a PubMed-mode lesson package."""

    topic: str
    total_claims: int
    total_references: int
    total_pmids_in_records: int
    claim_traces: list[ClaimTraceEntry] = Field(default_factory=list)
    global_errors: list[str] = Field(default_factory=list)
    global_warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


def _slide_text(slide: LessonSlide) -> str:
    return "\n".join([slide.title, *slide.key_points, slide.speaker_notes])


def _reference_mismatches(
    reference: CitationRecord, record: PubMedRecord
) -> list[str]:
    expected = {
        "citation_id": record.citation_id,
        "title": record.title,
        "authors": record.authors,
        "year": record.publication_year,
        "journal_or_org": record.journal,
        "doi": record.doi,
        "pmid": record.pmid,
        "url": record.source_url,
        "reference_type": ReferenceType.PUBMED_RETRIEVED,
    }
    return [
        field
        for field, expected_value in expected.items()
        if getattr(reference, field) != expected_value
    ]


def build_traceability_report(
    package: LessonPackage,
    records: list[PubMedRecord],
) -> EvidenceTraceabilityReport:
    """Build a diagnostic report without mutating or repairing the package."""
    global_errors: list[str] = []
    global_warnings: list[str] = []

    record_pmids_list = [record.pmid for record in records]
    record_pmids = set(record_pmids_list)
    if len(record_pmids_list) != len(record_pmids):
        global_errors.append("Duplicate PMIDs exist in normalized PubMed records.")
    for pmid in record_pmids_list:
        if not PMID_RE.fullmatch(pmid):
            global_errors.append(f"Normalized record contains invalid PMID {pmid!r}.")

    reference_ids = [reference.citation_id for reference in package.references]
    if len(reference_ids) != len(set(reference_ids)):
        global_errors.append("Duplicate citation_id values exist in references.")
    reference_pmids = [reference.pmid for reference in package.references if reference.pmid]
    if len(reference_pmids) != len(set(reference_pmids)):
        global_errors.append("Duplicate PMIDs exist in package references.")

    slide_numbers_all = [slide.slide_number for slide in package.slides]
    if len(slide_numbers_all) != len(set(slide_numbers_all)):
        global_errors.append("Duplicate slide numbers exist in the lesson package.")

    record_lookup = {record.pmid: record for record in records}
    ref_lookup = {reference.citation_id: reference for reference in package.references}
    slide_lookup = {slide.slide_number: slide for slide in package.slides}

    for reference in package.references:
        if reference.reference_type != ReferenceType.PUBMED_RETRIEVED:
            global_errors.append(
                f"Reference {reference.citation_id} is not pubmed_retrieved."
            )
        if not reference.pmid:
            global_errors.append(
                f"Reference {reference.citation_id} has no PMID."
            )
            continue
        if not PMID_RE.fullmatch(reference.pmid):
            global_errors.append(
                f"Reference {reference.citation_id} has invalid PMID {reference.pmid!r}."
            )
            continue
        record = record_lookup.get(reference.pmid)
        if record is None:
            global_errors.append(
                f"Reference {reference.citation_id} PMID {reference.pmid} is absent "
                "from normalized PubMed records."
            )
            continue
        mismatches = _reference_mismatches(reference, record)
        if mismatches:
            global_errors.append(
                f"Reference {reference.citation_id} does not match normalized record "
                f"fields: {', '.join(mismatches)}."
            )

    expected_reference_ids = {record.citation_id for record in records}
    actual_reference_ids = set(reference_ids)
    missing_references = sorted(expected_reference_ids - actual_reference_ids)
    extra_references = sorted(actual_reference_ids - expected_reference_ids)
    if missing_references:
        global_errors.append(
            "Normalized records missing from references: "
            + ", ".join(missing_references)
        )
    if extra_references:
        global_errors.append(
            "References not derived from normalized records: "
            + ", ".join(extra_references)
        )

    claim_traces: list[ClaimTraceEntry] = []
    for claim in package.claims:
        warnings: list[str] = []
        supporting_pmids: list[str] = []
        status = "traceable"

        if not claim.citation_ids:
            status = "untraceable"
            warnings.append("Claim has no citations.")

        for citation_id in claim.citation_ids:
            reference = ref_lookup.get(citation_id)
            if reference is None:
                status = "untraceable"
                warnings.append(f"Claim cites unknown reference '{citation_id}'.")
                continue
            if not reference.pmid:
                status = "untraceable"
                warnings.append(f"Reference '{citation_id}' has no PMID.")
                continue
            if reference.pmid not in record_pmids:
                status = "untraceable"
                warnings.append(
                    f"PMID {reference.pmid} was not found in normalized records."
                )
                continue
            if reference.reference_type != ReferenceType.PUBMED_RETRIEVED:
                status = "untraceable"
                warnings.append(
                    f"Reference '{citation_id}' is not marked pubmed_retrieved."
                )
                continue
            supporting_pmids.append(reference.pmid)

        unique_pmids = list(dict.fromkeys(supporting_pmids))
        listed_slides = sorted(set(claim.slide_numbers))
        if len(listed_slides) != len(claim.slide_numbers):
            status = "untraceable"
            warnings.append("Claim contains duplicate slide-number mappings.")
        if not listed_slides:
            status = "untraceable"
            warnings.append("Claim has no slide-number mapping.")

        visible_slides: list[int] = []
        cited_visible_slides: list[int] = []
        for slide in package.slides:
            if claim.claim_text in _slide_text(slide):
                visible_slides.append(slide.slide_number)
                if set(claim.citation_ids) & set(slide.citation_ids):
                    cited_visible_slides.append(slide.slide_number)
                else:
                    status = "untraceable"
                    warnings.append(
                        f"Claim text is visible on slide {slide.slide_number} without "
                        "one of its citations."
                    )

        for slide_number in listed_slides:
            slide = slide_lookup.get(slide_number)
            if slide is None:
                status = "untraceable"
                warnings.append(f"Mapped slide {slide_number} does not exist.")
                continue
            if claim.claim_text not in _slide_text(slide):
                status = "untraceable"
                warnings.append(
                    f"Claim text is not visible on mapped slide {slide_number}."
                )
            if not (set(claim.citation_ids) & set(slide.citation_ids)):
                status = "untraceable"
                warnings.append(
                    f"Mapped slide {slide_number} does not carry a claim citation."
                )

        if sorted(cited_visible_slides) != listed_slides:
            status = "untraceable"
            warnings.append(
                "Claim slide_numbers do not exactly match the visible, cited slides "
                f"(listed={listed_slides}, observed={sorted(cited_visible_slides)})."
            )
        if not visible_slides:
            status = "untraceable"
            warnings.append("Claim text is not visible on any slide.")

        claim_traces.append(
            ClaimTraceEntry(
                claim_id=claim.claim_id,
                claim_text=claim.claim_text,
                supporting_pmids=unique_pmids,
                slide_numbers=listed_slides,
                traceability_status=status,
                warnings=list(dict.fromkeys(warnings)),
            )
        )

    missing_abstract_pmids = [
        record.pmid
        for record in records
        if not record.abstract or not record.abstract.strip()
    ]
    if missing_abstract_pmids:
        global_warnings.append(
            "No claims were permitted from title-only records without abstracts: "
            + ", ".join(missing_abstract_pmids)
        )
    if not package.claims:
        global_warnings.append(
            "No abstract-supported health claims were generated; evidence is insufficient."
        )

    return EvidenceTraceabilityReport(
        topic=package.metadata.topic,
        total_claims=len(package.claims),
        total_references=len(package.references),
        total_pmids_in_records=len(record_pmids),
        claim_traces=claim_traces,
        global_errors=list(dict.fromkeys(global_errors)),
        global_warnings=list(dict.fromkeys(global_warnings)),
    )


def validate_pubmed_traceability(
    package: LessonPackage,
    records: list[PubMedRecord],
) -> None:
    """Fail closed on invented/unlinked citations or invalid claim-slide mappings."""
    report = build_traceability_report(package, records)
    failures = list(report.global_errors)
    for trace in report.claim_traces:
        if trace.traceability_status != "traceable":
            failures.extend(
                f"{trace.claim_id}: {warning}" for warning in trace.warnings
            )
    if failures:
        raise ValueError(
            "PubMed traceability validation failed: "
            + "; ".join(dict.fromkeys(failures))
        )


def validate_no_invented_pmids(
    package: LessonPackage,
    records: list[PubMedRecord],
) -> None:
    """Backward-compatible name for the now-strict PubMed integrity gate."""
    validate_pubmed_traceability(package, records)
