"""Build a LessonPackage from retrieved PubMed records without an LLM."""

from __future__ import annotations

from src import __version__
from src.pubmed.briefs import generate_evidence_briefs
from src.pubmed.models import EvidenceBrief, PubMedRecord
from src.pubmed.normalizer import infer_evidence_level
from src.schemas.lesson import (
    CitationRecord,
    EvidenceLevel,
    GenerationMetadata,
    HealthClaim,
    Language,
    LessonMetadata,
    LessonPackage,
    LessonSlide,
    ReferenceType,
)


class PubMedLessonBuilder:
    """Assemble a conservative lesson strictly from retrieved metadata."""

    def __init__(
        self,
        topic: str,
        audience: str,
        language: Language,
        duration_minutes: int,
        records: list[PubMedRecord],
    ) -> None:
        self.topic = topic
        self.audience = audience
        self.language = language
        self.duration_minutes = duration_minutes
        self.records = records
        self.briefs = generate_evidence_briefs(records, topic)
        self.brief_by_pmid: dict[str, EvidenceBrief] = {
            brief.pmid: brief for brief in self.briefs
        }

    def build(self) -> LessonPackage:
        references = [self._record_to_citation(record) for record in self.records]
        claims = [
            claim
            for record in self.records
            if (claim := self._record_to_claim(record)) is not None
        ]
        slides = self._build_slides(claims)

        metadata = LessonMetadata(
            title=f"{self.topic}: Candidate Evidence from PubMed",
            topic=self.topic,
            audience=self.audience,
            language=self.language,
            duration_minutes=self.duration_minutes,
            learning_objectives=[
                f"Review candidate PubMed records retrieved for {self.topic}.",
                "Identify study types and publication years reported by PubMed.",
                "Distinguish abstract excerpts from full-text-reviewed conclusions.",
                "Locate the original records using PubMed identifiers (PMIDs).",
            ],
        )

        generation = GenerationMetadata(
            provider_name="pubmed",
            provider_version=__version__,
            generation_mode="online",
            is_deterministic_fixture=False,
            prompt_used=(
                f"topic={self.topic}; audience={self.audience}; "
                f"language={self.language.value}; duration={self.duration_minutes}; "
                f"evidence_source=pubmed; records={len(self.records)}"
            ),
        )

        return LessonPackage(
            metadata=metadata,
            generation=generation,
            slides=slides,
            claims=claims,
            references=references,
        )

    def _record_to_citation(self, record: PubMedRecord) -> CitationRecord:
        brief = self.brief_by_pmid.get(record.pmid)
        evidence_level = (
            brief.evidence_level
            if brief
            else infer_evidence_level(record.publication_types, record.title)
        )
        try:
            level = EvidenceLevel(evidence_level)
        except ValueError:
            level = EvidenceLevel.UNVERIFIED

        return CitationRecord(
            citation_id=record.citation_id,
            title=record.title,
            authors=record.authors,
            year=record.publication_year,
            journal_or_org=record.journal,
            doi=record.doi,
            pmid=record.pmid,
            url=record.source_url,
            evidence_level=level,
            reference_type=ReferenceType.PUBMED_RETRIEVED,
            provenance_note=(
                "Retrieved from PubMed via official NCBI E-utilities on "
                f"{record.retrieved_at.isoformat()}."
            ),
            population=brief.population if brief else "not_reported",
            limitations=brief.limitations if brief else "not_reported",
        )

    def _record_to_claim(self, record: PubMedRecord) -> HealthClaim | None:
        brief = self.brief_by_pmid.get(record.pmid)
        # A title alone cannot support a health/nutrition claim. Missing abstracts
        # stay visible in the evidence slide, but produce no claim or summary.
        if (
            brief is None
            or not record.abstract
            or not record.abstract.strip()
            or brief.key_findings == "not_reported"
        ):
            return None

        try:
            level = EvidenceLevel(brief.evidence_level)
        except ValueError:
            level = EvidenceLevel.UNVERIFIED

        claim_text = f"PubMed PMID {record.pmid} reports: {brief.key_findings}"
        return HealthClaim(
            claim_id=f"claim_{record.pmid}",
            claim_text=claim_text,
            slide_numbers=[],
            citation_ids=[record.citation_id],
            evidence_statement=brief.key_findings,
            interpretation=(
                f"This is a candidate record returned by the query for {self.topic}; "
                "topical relevance and evidence quality have not been independently "
                "adjudicated."
            ),
            practical_advice=(
                "Do not convert this abstract excerpt into health advice until the "
                "full text is reviewed by a qualified nutrition professional."
            ),
            evidence_level=level,
            is_causal=False,
            is_disease_treatment_claim=False,
            study_design=brief.study_type,
            population=brief.population,
            limitations=brief.limitations,
        )

    def _build_slides(self, claims: list[HealthClaim]) -> list[LessonSlide]:
        claims_by_pmid = {
            claim.claim_id.removeprefix("claim_"): claim for claim in claims
        }
        slides: list[LessonSlide] = [
            LessonSlide(
                slide_number=1,
                title=self.topic,
                slide_type="title",
                key_points=[
                    "Candidate evidence retrieved from official PubMed metadata.",
                ],
                speaker_notes=(
                    "This lesson is educational, not medical advice. PubMed retrieval "
                    "does not establish evidence quality or topical applicability."
                ),
            ),
            LessonSlide(
                slide_number=2,
                title="Learning Objectives",
                slide_type="content",
                key_points=[
                    f"Review candidate PubMed records retrieved for {self.topic}.",
                    "Identify reported study types and publication years.",
                    "Distinguish abstract excerpts from full-text conclusions.",
                    "Locate original sources using PMIDs.",
                ],
                speaker_notes=(
                    "Set expectations: these are query-returned records, not treatment "
                    "recommendations or a completed evidence appraisal."
                ),
            ),
        ]

        for slide_number, record in enumerate(self.records, start=3):
            brief = self.brief_by_pmid.get(record.pmid)
            claim = claims_by_pmid.get(record.pmid)
            display_title = record.title or "Title not reported by PubMed"
            title_short = (
                f"{display_title[:120]}..."
                if len(display_title) > 120
                else display_title
            )
            if claim is not None:
                claim.slide_numbers = [slide_number]
                claim_points = [
                    f"Claim: {claim.claim_text}",
                    f"Study type: {brief.study_type if brief else 'not_reported'}",
                    f"Year: {record.publication_year or 'not_reported'}",
                    f"Journal: {record.journal or 'not_reported'}",
                    f"PMID: {record.pmid}",
                ]
                note = (
                    f"Visible claim ID: {claim.claim_id}. "
                    f"Limitations: {claim.limitations or 'not_reported'}"
                )
            else:
                claim_points = [
                    "Insufficient evidence for a health claim: PubMed returned no abstract.",
                    "No summary or finding was generated from the title alone.",
                    f"Year: {record.publication_year or 'not_reported'}",
                    f"Journal: {record.journal or 'not_reported'}",
                    f"PMID: {record.pmid}",
                ]
                note = (
                    "No health claim was generated for this record because the "
                    "abstract was unavailable."
                )

            slides.append(
                LessonSlide(
                    slide_number=slide_number,
                    title=title_short,
                    slide_type="evidence",
                    key_points=claim_points,
                    speaker_notes=note,
                    citation_ids=[record.citation_id],
                )
            )

        evidence_slide_number = len(slides) + 1
        missing_abstract_count = sum(
            1 for record in self.records if not record.abstract or not record.abstract.strip()
        )
        slides.append(
            LessonSlide(
                slide_number=evidence_slide_number,
                title="Evidence and Limitations",
                slide_type="content",
                key_points=[
                    "This lesson uses PubMed metadata and labelled abstract excerpts only.",
                    "Retrieval does not guarantee relevance, quality, or causal support.",
                    "Full-text review by a nutrition professional is required before use.",
                    f"Records without abstracts: {missing_abstract_count}; no claims were generated from them.",
                ],
                speaker_notes=(
                    "Reinforce conservative interpretation and the explicit missing-data "
                    "boundary. No treatment promises are made."
                ),
            )
        )

        summary_slide_number = evidence_slide_number + 1
        slides.append(
            LessonSlide(
                slide_number=summary_slide_number,
                title="Summary",
                slide_type="summary",
                key_points=[
                    f"Retrieved {len(self.records)} PubMed record(s) for {self.topic}.",
                    f"Generated {len(claims)} abstract-linked claim(s).",
                    "Every generated claim is linked to a retrieved PMID and visible slide.",
                    "Human full-text review remains required.",
                ],
                speaker_notes="Close by restating the educational and review boundaries.",
            )
        )

        references_slide_number = summary_slide_number + 1
        ref_points: list[str] = []
        for record in self.records:
            year = f", {record.publication_year}" if record.publication_year else ""
            authors = record.authors or "Authors not reported"
            first_author = authors.split(",")[0].strip()
            ref_points.append(
                f"PMID: {record.pmid} — {first_author}{year}; "
                f"{record.title or 'title not reported'}"
            )
        slides.append(
            LessonSlide(
                slide_number=references_slide_number,
                title="References",
                slide_type="references",
                key_points=ref_points,
                speaker_notes="Use PMIDs to open the official PubMed records.",
                citation_ids=[record.citation_id for record in self.records],
            )
        )
        return slides
