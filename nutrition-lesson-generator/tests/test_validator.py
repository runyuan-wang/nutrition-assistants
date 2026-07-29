"""Tests for the quality validator, including negative cases."""

from __future__ import annotations

import pytest

from src.pipeline.validator import QualityValidator
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


def _minimal_package() -> LessonPackage:
    metadata = LessonMetadata(
        title="Minimal",
        topic="Minimal",
        audience="general adults",
        language=Language.EN,
        learning_objectives=["Objective"],
    )
    return LessonPackage(
        metadata=metadata,
        generation={
            "provider_name": "mock",
            "provider_version": "0.1.0",
            "generation_mode": "offline",
        },
        slides=[LessonSlide(slide_number=1, title="Slide")],
        claims=[],
        references=[],
    )


def test_empty_package_passes():
    package = _minimal_package()
    report = QualityValidator().validate(package)
    assert report.pass_quality_gate is True
    assert report.total_slides == 1
    assert report.total_claims == 0


def test_claim_without_citation_fails():
    package = _minimal_package()
    # Create a valid claim first, then mutate to simulate a missing citation.
    claim = HealthClaim(
        claim_id="C1",
        claim_text="A claim without citation",
        citation_ids=["R_PLACEHOLDER"],
        evidence_statement="Evidence statement text.",
        interpretation="Interpretation text.",
        practical_advice="Practical advice text.",
    )
    claim.citation_ids = []
    package.claims.append(claim)
    report = QualityValidator().validate(package)
    assert report.pass_quality_gate is False
    assert any(i.rule == "claim_requires_citation" for i in report.issues)


def test_causal_observational_claim_fails():
    package = _minimal_package()
    ref = CitationRecord(
        citation_id="R1",
        reference_type=ReferenceType.DEVELOPMENT_FIXTURE,
        evidence_level=EvidenceLevel.OBSERVATIONAL,
    )
    package.references.append(ref)
    package.claims.append(
        HealthClaim(
            claim_id="C1",
            claim_text="Fiber causes health",
            citation_ids=["R1"],
            evidence_statement="Evidence statement text.",
            interpretation="Interpretation text.",
            practical_advice="Practical advice text.",
            evidence_level=EvidenceLevel.OBSERVATIONAL,
            is_causal=True,
        )
    )
    report = QualityValidator().validate(package)
    assert report.pass_quality_gate is False
    assert any(i.rule == "no_causal_overstatement" for i in report.issues)


def test_disease_treatment_claim_fails():
    package = _minimal_package()
    ref = CitationRecord(
        citation_id="R1",
        reference_type=ReferenceType.DEVELOPMENT_FIXTURE,
    )
    package.references.append(ref)
    package.claims.append(
        HealthClaim(
            claim_id="C1",
            claim_text="Treats diabetes",
            citation_ids=["R1"],
            evidence_statement="Evidence statement text.",
            interpretation="Interpretation text.",
            practical_advice="Practical advice text.",
            is_disease_treatment_claim=True,
        )
    )
    report = QualityValidator().validate(package)
    assert report.pass_quality_gate is False
    assert any(i.rule == "no_disease_treatment_claims" for i in report.issues)


def test_unsupported_number_flagged():
    package = _minimal_package()
    ref = CitationRecord(
        citation_id="R1",
        reference_type=ReferenceType.PROVIDER_GENERATED,
    )
    package.references.append(ref)
    package.claims.append(
        HealthClaim(
            claim_id="C1",
            claim_text="Increases fiber by 25%",
            citation_ids=["R1"],
            evidence_statement="Evidence statement text.",
            interpretation="Interpretation text.",
            practical_advice="Practical advice text.",
        )
    )
    report = QualityValidator().validate(package)
    assert any(i.rule == "unsupported_numerical_claim" for i in report.issues)
    assert report.unsupported_numerical_claims == 1


def test_supported_number_with_fixture_passes():
    package = _minimal_package()
    ref = CitationRecord(
        citation_id="R1",
        reference_type=ReferenceType.DEVELOPMENT_FIXTURE,
        doi="10.1234/example",
        year=2020,
    )
    package.references.append(ref)
    package.claims.append(
        HealthClaim(
            claim_id="C1",
            claim_text="Increases fiber by 25%",
            citation_ids=["R1"],
            evidence_statement="Evidence statement text.",
            interpretation="Interpretation text.",
            practical_advice="Practical advice text.",
        )
    )
    report = QualityValidator().validate(package)
    assert report.unsupported_numerical_claims == 0
    assert report.pass_quality_gate is True


def test_provider_generated_citation_info():
    package = _minimal_package()
    package.references.append(
        CitationRecord(
            citation_id="R1",
            reference_type=ReferenceType.PROVIDER_GENERATED,
        )
    )
    report = QualityValidator().validate(package)
    assert any(
        i.rule == "provider_generated_citation" and i.severity == "info"
        for i in report.issues
    )
