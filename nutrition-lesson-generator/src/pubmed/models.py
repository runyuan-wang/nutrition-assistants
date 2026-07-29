"""Typed models for PubMed evidence retrieval."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from pydantic import BaseModel, Field, field_validator, model_validator


_DATE_RE = re.compile(r"^\d{4}(?:/\d{2}/\d{2})?$")


def _date_sort_value(value: str, *, end: bool) -> datetime:
    """Parse the accepted PubMed date formats for range validation."""
    if not _DATE_RE.fullmatch(value):
        raise ValueError("date must use YYYY or YYYY/MM/DD")
    if len(value) == 4:
        suffix = "/12/31" if end else "/01/01"
        value = f"{value}{suffix}"
    try:
        return datetime.strptime(value, "%Y/%m/%d")
    except ValueError as exc:
        raise ValueError("date must be a real calendar date in YYYY or YYYY/MM/DD format") from exc


class PubMedSearchQuery(BaseModel):
    """Search request metadata saved alongside retrieval outputs."""

    topic: str = Field(..., min_length=1)
    final_query: str = Field(..., min_length=1)
    date_range: tuple[str | None, str | None] = Field(
        default=(None, None),
        description="Optional (start, end) publication-date filter as YYYY or YYYY/MM/DD.",
    )
    requested_max_count: int = Field(..., ge=1, le=200)
    retrieval_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("topic", "final_query")
    @classmethod
    def _strip_nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value

    @field_validator("date_range")
    @classmethod
    def _valid_date_range(
        cls, value: tuple[str | None, str | None]
    ) -> tuple[str | None, str | None]:
        start, end = value
        start = start.strip() if start else None
        end = end.strip() if end else None
        start_value = _date_sort_value(start, end=False) if start else None
        end_value = _date_sort_value(end, end=True) if end else None
        if start_value and end_value and start_value > end_value:
            raise ValueError("date_range start must not be after end")
        return start, end

    model_config = {"extra": "forbid"}


class PubMedRecord(BaseModel):
    """A normalized PubMed article record.

    Unavailable metadata is represented explicitly as None or an empty list;
    no fields are fabricated.
    """

    pmid: str = Field(..., pattern=r"^[1-9]\d*$")
    title: str | None = Field(
        None,
        description="Article title; None when PubMed did not return one.",
    )
    abstract: str | None = Field(
        None,
        description="Article abstract; None when not returned by EFetch.",
    )
    authors: str | None = Field(
        None,
        description="Formatted author string; None if unavailable.",
    )
    journal: str | None = Field(None)
    publication_year: int | None = Field(None, ge=1800, le=2100)
    publication_types: list[str] = Field(default_factory=list)
    doi: str | None = Field(None)
    mesh_terms: list[str] = Field(default_factory=list)
    language: str | None = Field(None)
    source_url: str = Field(..., min_length=1)
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @field_validator("title", "abstract", "authors", "journal", "doi", "language")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("doi")
    @classmethod
    def _valid_doi_prefix(cls, value: str | None) -> str | None:
        if value and not value.startswith("10."):
            raise ValueError("DOI returned by PubMed must start with '10.'")
        return value

    @property
    def citation_id(self) -> str:
        return f"PMID_{self.pmid}"

    model_config = {"extra": "forbid"}


class EvidenceBrief(BaseModel):
    """A conservative structured view of one retrieved PubMed record.

    When the record does not report an element, the value is ``not_reported``.
    Abstract excerpts are explicitly labelled and are never presented as a
    full-text-reviewed conclusion.
    """

    evidence_id: str = Field(..., min_length=1)
    pmid: str = Field(..., pattern=r"^[1-9]\d*$")
    study_type: str = Field(default="not_reported")
    population: str = Field(default="not_reported")
    intervention_or_exposure: str = Field(default="not_reported")
    comparator: str = Field(default="not_reported")
    outcomes: str = Field(default="not_reported")
    key_findings: str = Field(default="not_reported")
    limitations: str = Field(default="not_reported")
    evidence_level: str = Field(default="not_reported")
    relevance_to_topic: str = Field(default="not_reported")
    usable_for_public_education: bool = Field(default=False)

    @model_validator(mode="after")
    def _evidence_id_matches_pmid(self) -> "EvidenceBrief":
        expected = f"PMID_{self.pmid}"
        if self.evidence_id != expected:
            raise ValueError(
                f"evidence_id '{self.evidence_id}' must equal '{expected}'"
            )
        return self

    model_config = {"extra": "forbid"}
