"""Tests for MockProvider and end-to-end offline generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.pipeline.generator import LessonGenerator
from src.providers.mock_provider import MockProvider
from src.schemas.lesson import Language, LessonPackage


CANONICAL_TOPIC = "Dietary Fiber and Gut Health"


def test_mock_provider_generates_dietary_fiber_fixture():
    provider = MockProvider()
    package = provider.generate(
        topic=CANONICAL_TOPIC,
        audience="general adults",
        language=Language.EN,
        duration_minutes=30,
    )
    assert isinstance(package, LessonPackage)
    assert package.generation.is_deterministic_fixture is True
    assert len(package.slides) >= 9
    assert len(package.references) >= 5
    assert len(package.claims) >= 5
    assert all(claim.citation_ids for claim in package.claims)


def test_curated_fixture_reference_identifiers_are_exact():
    package = MockProvider().generate(
        topic=CANONICAL_TOPIC,
        audience="general adults",
        language=Language.EN,
        duration_minutes=30,
    )
    actual = {r.citation_id: (r.pmid, r.doi) for r in package.references}
    assert actual == {
        "Makki2018": ("29902436", "10.1016/j.chom.2018.05.012"),
        "Reynolds2019": ("30638909", "10.1016/S0140-6736(18)31809-9"),
        "Slavin2013": ("23609775", "10.3390/nu5041417"),
        "USDA2020": (None, None),
        "Quagliani2017": ("30202317", "10.1177/1559827615588079"),
    }


def test_mock_provider_rejects_unsupported_language():
    provider = MockProvider()
    with pytest.raises(Exception):
        provider.generate(
            topic=CANONICAL_TOPIC,
            audience="general adults",
            language=Language("es"),
        )


def test_mock_provider_generic_fallback_is_safe():
    provider = MockProvider()
    package = provider.generate(
        topic="Quantum Nutrition",
        audience="general adults",
        language=Language.EN,
    )
    assert package.generation.is_deterministic_fixture is False
    # Generic fallback must not fabricate verified citations.
    assert any(r.citation_id == "NO_EVIDENCE_OFFLINE" for r in package.references)
    assert len(package.claims) == 0


def test_generator_exports_all_six_outputs(tmp_path: Path):
    generator = LessonGenerator(output_dir=tmp_path)
    package = generator.generate(
        topic=CANONICAL_TOPIC,
        audience="general adults",
        language=Language.EN,
    )
    out = generator.export_package(package, tmp_path)

    expected = {
        "lesson_spec.json",
        "lesson_outline.md",
        "speaker_notes.md",
        "references.md",
        "quality_report.md",
        "nutrition_lesson.pptx",
    }
    found = {p.name for p in out.iterdir()}
    assert expected <= found, f"Missing outputs: {expected - found}"


def test_spec_round_trip_from_saved_file(tmp_path: Path):
    generator = LessonGenerator(output_dir=tmp_path)
    package = generator.generate(
        topic=CANONICAL_TOPIC,
        audience="general adults",
        language=Language.EN,
    )
    generator.export_package(package, tmp_path)

    spec_path = tmp_path / "lesson_spec.json"
    data = json.loads(spec_path.read_text(encoding="utf-8"))
    reloaded = LessonPackage(**data)
    assert reloaded.metadata.title == package.metadata.title
    assert len(reloaded.slides) == len(package.slides)


def test_quality_report_not_hardcoded(tmp_path: Path):
    generator = LessonGenerator(output_dir=tmp_path)
    package = generator.generate(
        topic=CANONICAL_TOPIC,
        audience="general adults",
        language=Language.EN,
    )
    report = generator.validator.validate(package)
    assert report.total_claims == len(package.claims)
    assert report.total_citations == len(package.references)
    assert report.total_slides == len(package.slides)
