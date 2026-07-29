"""Canonical Pydantic schemas for nutrition lesson packages.

Design goals:
- Stable citation identifiers that survive re-runs.
- Every substantive health claim maps to one or more citations.
- Clear separation of evidence, interpretation, and practical advice.
- Explicit provenance for verified development fixtures vs. provider output.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class Audience(str, Enum):
    """Target audience presets."""

    GENERAL_ADULTS = "general adults"
    HEALTH_EDUCATORS = "health educators"
    REGISTERED_DIETITIANS = "registered dietitians"
    STUDENTS = "students"


class Language(str, Enum):
    """Supported output languages."""

    EN = "en"


class EvidenceLevel(str, Enum):
    """Conservative evidence level for claims."""

    SYSTEMATIC_REVIEW = "systematic review / meta-analysis"
    NONSYSTEMATIC_REVIEW = "review / nonsystematic"
    RCT = "randomized controlled trial"
    OBSERVATIONAL = "observational study"
    EXPERT_GUIDANCE = "expert guidance / consensus"
    MECHANISTIC = "mechanistic / preclinical"
    UNVERIFIED = "unverified / provider-generated"


class ReferenceType(str, Enum):
    """Provenance of a citation record."""

    DEVELOPMENT_FIXTURE = "development_fixture"
    PROVIDER_GENERATED = "provider_generated"
    PUBMED_RETRIEVED = "pubmed_retrieved"


class CitationRecord(BaseModel):
    """A single reference / citation."""

    citation_id: str = Field(
        ...,
        min_length=1,
        description="Stable citation identifier used across the lesson package.",
    )
    title: str | None = Field(
        None,
        description="Article or report title; None if not verified.",
    )
    authors: str | None = Field(
        None,
        description="Author string or organization.",
    )
    year: int | None = Field(
        None,
        ge=1900,
        le=2100,
        description="Publication year.",
    )
    journal_or_org: str | None = Field(
        None,
        description="Journal, publisher, or issuing organization.",
    )
    doi: str | None = Field(
        None,
        description="Verified DOI; None if unavailable.",
    )
    pmid: str | None = Field(
        None,
        description="Verified PubMed identifier; None if unavailable.",
    )
    url: str | None = Field(
        None,
        description="Stable URL to the source.",
    )
    evidence_level: EvidenceLevel = Field(
        default=EvidenceLevel.UNVERIFIED,
        description="Conservative evidence classification.",
    )
    reference_type: ReferenceType = Field(
        default=ReferenceType.PROVIDER_GENERATED,
        description="Provenance of this citation record.",
    )
    provenance_note: str = Field(
        default="",
        description="How the citation metadata was verified, if applicable.",
    )
    population: str | None = Field(
        None,
        description="Study population or applicability notes.",
    )
    limitations: str | None = Field(
        None,
        description="Key limitations of the cited evidence.",
    )

    @field_validator("doi")
    @classmethod
    def _doi_prefix(cls, v: str | None) -> str | None:
        if v and not v.startswith("10."):
            raise ValueError("DOI must start with '10.'")
        return v

    model_config = {"extra": "forbid"}


class HealthClaim(BaseModel):
    """A substantive health/science claim embedded in the lesson."""

    claim_id: str = Field(..., min_length=1)
    claim_text: str = Field(..., min_length=3)
    slide_numbers: list[int] = Field(
        default_factory=list,
        description="Slides where this claim appears.",
    )
    citation_ids: list[str] = Field(
        default_factory=list,
        description="Citations supporting this claim.",
    )
    evidence_statement: str = Field(
        ...,
        min_length=3,
        description="What the cited evidence actually shows, phrased conservatively.",
    )
    interpretation: str = Field(
        ...,
        min_length=3,
        description="How the evidence is interpreted in an educational context.",
    )
    practical_advice: str = Field(
        ...,
        min_length=3,
        description="Food-based or behavioral guidance, not treatment/dosing instructions.",
    )
    evidence_level: EvidenceLevel = Field(default=EvidenceLevel.UNVERIFIED)
    is_causal: bool = Field(
        default=False,
        description="True only if the claim is framed as causal; flagged otherwise.",
    )
    is_disease_treatment_claim: bool = Field(
        default=False,
        description="True if the claim promises diagnosis/treatment/cure.",
    )
    study_design: str | None = Field(
        None,
        description="Study design of the primary cited evidence.",
    )
    population: str | None = Field(
        None,
        description="Population to which the cited evidence applies.",
    )
    limitations: str | None = Field(
        None,
        description="Limitations affecting interpretation.",
    )

    @model_validator(mode="after")
    def _citation_required(self) -> "HealthClaim":
        if not self.citation_ids:
            raise ValueError(f"Claim '{self.claim_id}' must cite at least one reference.")
        return self

    model_config = {"extra": "forbid"}


class LessonSlide(BaseModel):
    """A single slide in the lesson."""

    slide_number: int = Field(..., ge=1)
    title: str = Field(..., min_length=1)
    slide_type: str = Field(
        default="content",
        description="E.g., title, content, section, evidence, summary, references.",
    )
    key_points: list[str] = Field(default_factory=list)
    speaker_notes: str = Field(default="")
    citation_ids: list[str] = Field(default_factory=list)
    notes_for_educator: str = Field(
        default="",
        description="Teaching tips / safety notes specific to this slide.",
    )

    model_config = {"extra": "forbid"}


class LessonMetadata(BaseModel):
    """Top-level metadata for a lesson."""

    title: str = Field(..., min_length=1)
    topic: str = Field(..., min_length=1)
    audience: str = Field(..., min_length=1)
    language: Language = Field(default=Language.EN)
    duration_minutes: int = Field(default=30, ge=5, le=180)
    learning_objectives: list[str] = Field(default_factory=list, min_length=1)
    disclaimer: str = Field(
        default=(
            "This lesson is for educational purposes only and is not medical, "
            "diagnostic, or treatment advice. Consult a qualified health professional "
            "for personal guidance."
        )
    )

    model_config = {"extra": "forbid"}


class GenerationMetadata(BaseModel):
    """Provenance of the generation run."""

    provider_name: str = Field(..., min_length=1)
    provider_version: str = Field(default="0.1.0")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    generation_mode: str = Field(
        default="offline",
        description="offline = no live external retrieval; online = live retrieval.",
    )
    is_deterministic_fixture: bool = Field(
        default=False,
        description="True when the lesson is a verified development fixture.",
    )
    prompt_used: str | None = Field(default=None)

    model_config = {"extra": "forbid"}


class QualityIssue(BaseModel):
    """A single issue raised by the quality checker."""

    severity: str = Field(..., pattern="^(error|warning|info)$")
    rule: str = Field(..., min_length=1)
    claim_id: str | None = Field(default=None)
    slide_number: int | None = Field(default=None)
    message: str = Field(..., min_length=1)
    suggestion: str = Field(default="")

    model_config = {"extra": "forbid"}


class QualityReport(BaseModel):
    """Structured quality report for a lesson package."""

    package_title: str = Field(..., min_length=1)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_slides: int = Field(default=0, ge=0)
    total_claims: int = Field(default=0, ge=0)
    total_citations: int = Field(default=0, ge=0)
    claims_with_citations: int = Field(default=0, ge=0)
    causal_claims: int = Field(default=0, ge=0)
    disease_treatment_claims: int = Field(default=0, ge=0)
    unsupported_numerical_claims: int = Field(default=0, ge=0)
    unverified_citations: int = Field(default=0, ge=0)
    issues: list[QualityIssue] = Field(default_factory=list)
    summary: str = Field(default="")
    pass_quality_gate: bool = Field(default=False)

    model_config = {"extra": "forbid"}


class LessonPackage(BaseModel):
    """Canonical lesson package — the single source of truth for all exports."""

    schema_version: str = Field(default="0.1.0")
    metadata: LessonMetadata
    generation: GenerationMetadata
    slides: list[LessonSlide] = Field(default_factory=list, min_length=1)
    claims: list[HealthClaim] = Field(default_factory=list)
    references: list[CitationRecord] = Field(default_factory=list)

    @model_validator(mode="after")
    def _citation_ids_exist(self) -> "LessonPackage":
        ref_ids = {r.citation_id for r in self.references}
        for claim in self.claims:
            for cid in claim.citation_ids:
                if cid not in ref_ids:
                    raise ValueError(
                        f"Claim '{claim.claim_id}' cites unknown reference '{cid}'."
                    )
        for slide in self.slides:
            for cid in slide.citation_ids:
                if cid not in ref_ids:
                    raise ValueError(
                        f"Slide {slide.slide_number} cites unknown reference '{cid}'."
                    )
        return self

    @model_validator(mode="after")
    def _unique_citation_ids(self) -> "LessonPackage":
        ids = [r.citation_id for r in self.references]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate citation_id values in references.")
        return self

    @model_validator(mode="after")
    def _unique_claim_ids(self) -> "LessonPackage":
        ids = [c.claim_id for c in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate claim_id values in claims.")
        return self

    def to_canonical_dict(self) -> str:
        """Return a pretty-printed JSON-serialized canonical representation."""
        import json

        return json.dumps(self.model_dump(mode="json"), indent=2, ensure_ascii=False)

    model_config = {"extra": "forbid"}
