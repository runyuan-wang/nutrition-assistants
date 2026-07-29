"""Tests for Pydantic schemas and JSON round-trips."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from src.schemas.lesson import (
    CitationRecord,
    EvidenceLevel,
    HealthClaim,
    Language,
    LessonMetadata,
    LessonPackage,
    LessonSlide,
    ReferenceType,
)


def test_lesson_metadata_validation():
    metadata = LessonMetadata(
        title="Test Lesson",
        topic="Test Topic",
        audience="general adults",
        language=Language.EN,
        duration_minutes=30,
        learning_objectives=["Learn something useful."],
    )
    assert metadata.language == Language.EN
    assert metadata.duration_minutes == 30


def test_duration_bounds():
    with pytest.raises(ValidationError):
        LessonMetadata(
            title="T",
            topic="T",
            audience="general adults",
            duration_minutes=3,
            learning_objectives=["Obj"],
        )


def test_citation_doi_prefix():
    with pytest.raises(ValidationError):
        CitationRecord(citation_id="BAD", doi="not-a-doi")

    rec = CitationRecord(
        citation_id="GOOD",
        doi="10.1234/example",
        title="Example",
        year=2020,
        reference_type=ReferenceType.DEVELOPMENT_FIXTURE,
    )
    assert rec.doi.startswith("10.")


def test_health_claim_requires_citation():
    with pytest.raises(ValidationError):
        HealthClaim(
            claim_id="C1",
            claim_text="Some claim",
            evidence_statement="Evidence statement text.",
            interpretation="Interpretation text.",
            practical_advice="Practical advice text.",
        )


def test_package_citation_reference_integrity():
    ref = CitationRecord(
        citation_id="R1",
        title="Reference One",
        year=2020,
        reference_type=ReferenceType.DEVELOPMENT_FIXTURE,
    )
    claim = HealthClaim(
        claim_id="C1",
        claim_text="Claim one",
        citation_ids=["R1"],
        evidence_statement="Evidence statement text.",
        interpretation="Interpretation text.",
        practical_advice="Practical advice text.",
    )
    slide = LessonSlide(
        slide_number=1,
        title="Slide",
        key_points=["Point"],
        citation_ids=["R1"],
    )
    metadata = LessonMetadata(
        title="T",
        topic="T",
        audience="general adults",
        learning_objectives=["Obj"],
    )
    package = LessonPackage(
        metadata=metadata,
        generation={
            "provider_name": "mock",
            "provider_version": "0.1.0",
            "generation_mode": "offline",
        },
        slides=[slide],
        claims=[claim],
        references=[ref],
    )
    assert package.references[0].citation_id == "R1"


def test_package_rejects_unknown_citation():
    metadata = LessonMetadata(
        title="T",
        topic="T",
        audience="general adults",
        learning_objectives=["Obj"],
    )
    with pytest.raises(ValidationError):
        LessonPackage(
            metadata=metadata,
            generation={
                "provider_name": "mock",
                "provider_version": "0.1.0",
                "generation_mode": "offline",
            },
            slides=[
                LessonSlide(
                    slide_number=1,
                    title="Slide",
                    citation_ids=["UNKNOWN"],
                )
            ],
            claims=[],
            references=[],
        )


def test_canonical_json_round_trip():
    ref = CitationRecord(
        citation_id="R1",
        title="Reference One",
        year=2020,
        reference_type=ReferenceType.DEVELOPMENT_FIXTURE,
    )
    metadata = LessonMetadata(
        title="T",
        topic="T",
        audience="general adults",
        learning_objectives=["Obj"],
    )
    package = LessonPackage(
        metadata=metadata,
        generation={
            "provider_name": "mock",
            "provider_version": "0.1.0",
            "generation_mode": "offline",
        },
        slides=[
            LessonSlide(
                slide_number=1,
                title="Slide",
                key_points=["Point"],
            )
        ],
        claims=[],
        references=[ref],
    )
    json_text = package.to_canonical_dict()
    data = json.loads(json_text)
    assert data["schema_version"] == "0.1.0"
    assert data["metadata"]["title"] == "T"
    assert data["references"][0]["citation_id"] == "R1"
