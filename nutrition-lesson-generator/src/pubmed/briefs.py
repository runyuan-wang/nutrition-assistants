"""Generate conservative EvidenceBrief objects from PubMedRecord objects."""

from __future__ import annotations

import re

from src.pubmed.models import EvidenceBrief, PubMedRecord
from src.pubmed.normalizer import infer_evidence_level, infer_study_type


def generate_evidence_briefs(
    records: list[PubMedRecord],
    topic: str,
) -> list[EvidenceBrief]:
    """Create one brief per record using only retrieved PubMed metadata."""
    return [_record_to_brief(record, topic) for record in records]


def _record_to_brief(record: PubMedRecord, topic: str) -> EvidenceBrief:
    return EvidenceBrief(
        evidence_id=record.citation_id,
        pmid=record.pmid,
        study_type=infer_study_type(record.publication_types, record.title),
        population="not_reported",
        intervention_or_exposure="not_reported",
        comparator="not_reported",
        outcomes="not_reported",
        key_findings=_derive_key_findings(record),
        limitations=_derive_limitations(record),
        evidence_level=infer_evidence_level(
            record.publication_types, record.title
        ),
        relevance_to_topic=(
            f"Candidate record returned by the PubMed query for '{topic}'; "
            "topical relevance requires human review."
        ),
        # Retrieval plus an abstract does not by itself establish that a source
        # is ready for public education. Full-text and professional review remain
        # required, so this flag stays false in the current abstract-only layer.
        usable_for_public_education=False,
    )


def _derive_key_findings(record: PubMedRecord) -> str:
    """Return a labelled abstract excerpt, never a generated summary."""
    if not record.abstract or not record.abstract.strip():
        return "not_reported"
    normalized = " ".join(record.abstract.split())
    first_sentence = re.split(r"(?<=[.!?])\s+", normalized, maxsplit=1)[0].strip()
    if not first_sentence:
        return "not_reported"
    return (
        "Abstract excerpt from PubMed (not full-text reviewed): "
        f"{first_sentence}"
    )


def _derive_limitations(record: PubMedRecord) -> str:
    if record.abstract and record.abstract.strip():
        return (
            "Abstract-only record; the full article and its methods, results, "
            "applicability, and limitations require nutrition-professional review."
        )
    return (
        "Insufficient evidence for a health claim: PubMed returned no abstract. "
        "No summary or finding was generated from the title alone."
    )
