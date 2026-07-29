"""Integration tests for PubMed-mode lesson generation.

These tests use fixture PubMed records and mocked retrieval; they do not call
NCBI over the network.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src.pipeline.generator import LessonGenerator
from src.pubmed.client import PubMedRetrievalResult
from src.pubmed.models import EvidenceBrief, PubMedRecord, PubMedSearchQuery
from src.pubmed.normalizer import parse_efetch_xml
from src.pubmed.traceability import (
    build_traceability_report,
    validate_no_invented_pmids,
)
from src.schemas.lesson import CitationRecord, EvidenceLevel, HealthClaim, Language, LessonPackage, LessonSlide, ReferenceType


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
EFETCH_XML = (FIXTURE_DIR / "pubmed_efetch.xml").read_text(encoding="utf-8")


def _fixture_records() -> list[PubMedRecord]:
    return parse_efetch_xml(EFETCH_XML)


def _fixture_result(max_results: int = 3) -> PubMedRetrievalResult:
    records = _fixture_records()[:max_results]
    briefs = [
        EvidenceBrief(
            evidence_id=r.citation_id,
            pmid=r.pmid,
            study_type="review",
            evidence_level="review / nonsystematic",
            key_findings=r.title,
        )
        for r in records
    ]
    return PubMedRetrievalResult(
        query=PubMedSearchQuery(
            topic="Dietary Fiber and Gut Health",
            final_query="test query",
            requested_max_count=max_results,
        ),
        raw_esearch={"esearchresult": {"idlist": [r.pmid for r in records]}},
        raw_efetch=EFETCH_XML,
        records=records,
        briefs=briefs,
    )


def _fake_pubmed_client_class() -> Any:
    class FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def retrieve(self, topic: str, max_results: int = 10, **kwargs: Any) -> PubMedRetrievalResult:
            return _fixture_result(max_results=max_results)

    return FakeClient


def test_pubmed_lesson_builder_creates_traceable_claims(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "src.pipeline.generator.PubMedClient",
        _fake_pubmed_client_class(),
    )
    generator = LessonGenerator()
    package = generator.generate(
        topic="Dietary Fiber and Gut Health",
        audience="general adults",
        language=Language.EN,
        duration_minutes=10,
        evidence_source="pubmed",
        max_pubmed_results=3,
    )

    assert isinstance(package, LessonPackage)
    assert package.generation.provider_name == "pubmed"
    # The fixture has three records but one has no abstract; title-only records
    # remain referenced and visible but do not become health claims.
    assert len(package.claims) == 2
    assert len(package.references) == 3
    assert all(claim.citation_ids for claim in package.claims)
    assert "claim_30202317" not in {claim.claim_id for claim in package.claims}
    assert all(ref.reference_type == ReferenceType.PUBMED_RETRIEVED for ref in package.references)


def test_claim_to_pmid_traceability(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "src.pipeline.generator.PubMedClient",
        _fake_pubmed_client_class(),
    )
    generator = LessonGenerator()
    package = generator.generate(
        topic="Dietary Fiber and Gut Health",
        audience="general adults",
        language=Language.EN,
        duration_minutes=10,
        evidence_source="pubmed",
        max_pubmed_results=3,
    )

    records = _fixture_records()
    report = build_traceability_report(package, records)
    assert report.total_claims == 2
    assert report.total_pmids_in_records == 3
    assert not report.global_errors
    assert any("30202317" in warning for warning in report.global_warnings)
    for trace in report.claim_traces:
        assert trace.traceability_status == "traceable"
        assert len(trace.supporting_pmids) >= 1
        assert all(pmid in {r.pmid for r in records} for pmid in trace.supporting_pmids)


def test_references_only_from_retrieved_records(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        "src.pipeline.generator.PubMedClient",
        _fake_pubmed_client_class(),
    )
    generator = LessonGenerator()
    package = generator.generate(
        topic="Dietary Fiber and Gut Health",
        audience="general adults",
        language=Language.EN,
        evidence_source="pubmed",
        max_pubmed_results=3,
    )

    record_pmids = {r.pmid for r in _fixture_records()}
    for ref in package.references:
        assert ref.pmid in record_pmids


def test_invented_citation_rejected():
    records = _fixture_records()
    bad_ref = CitationRecord(
        citation_id="PMID_99999999",
        title="Fabricated record",
        pmid="99999999",
        reference_type=ReferenceType.PUBMED_RETRIEVED,
        evidence_level=EvidenceLevel.UNVERIFIED,
    )
    good_ref = CitationRecord(
        citation_id=f"PMID_{records[0].pmid}",
        title=records[0].title,
        pmid=records[0].pmid,
        reference_type=ReferenceType.PUBMED_RETRIEVED,
        evidence_level=EvidenceLevel.NONSYSTEMATIC_REVIEW,
    )
    claim = HealthClaim(
        claim_id="C1",
        claim_text="Claim supported by fabricated record",
        citation_ids=[bad_ref.citation_id],
        evidence_statement="Evidence",
        interpretation="Interpretation",
        practical_advice="Advice",
    )
    package = LessonPackage(
        metadata={
            "title": "Test",
            "topic": "Test",
            "audience": "general adults",
            "learning_objectives": ["Obj"],
        },
        generation={
            "provider_name": "pubmed",
            "provider_version": "0.2.0",
            "generation_mode": "online",
        },
        slides=[LessonSlide(slide_number=1, title="Test")],
        claims=[claim],
        references=[bad_ref, good_ref],
    )

    with pytest.raises(ValueError, match="PMID 99999999"):
        validate_no_invented_pmids(package, records)


def test_pubmed_mode_output_tree(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    monkeypatch.setattr(
        "src.pipeline.generator.PubMedClient",
        _fake_pubmed_client_class(),
    )
    generator = LessonGenerator(output_dir=tmp_path)
    package = generator.generate(
        topic="Dietary Fiber and Gut Health",
        audience="general adults",
        language=Language.EN,
        duration_minutes=10,
        evidence_source="pubmed",
        max_pubmed_results=3,
    )

    out = generator.export_package(
        package,
        tmp_path,
        pubmed_request={
            "topic": "Dietary Fiber and Gut Health",
            "audience": "general adults",
            "language": "en",
            "duration_minutes": 10,
            "evidence_source": "pubmed",
            "max_pubmed_results": 3,
        },
    )

    expected = {
        "request.json",
        "search_query.json",
        "pubmed_raw.json",
        "pubmed_records.json",
        "evidence_brief.json",
        "evidence_traceability.json",
        "lesson_spec.json",
        "lesson_outline.md",
        "speaker_notes.md",
        "references.md",
        "quality_report.md",
        "nutrition_lesson.pptx",
    }
    found = {p.name for p in out.iterdir()}
    assert expected <= found, f"Missing outputs: {expected - found}"

    # Verify saved records round-trip and match the package references.
    saved_records = json.loads((out / "pubmed_records.json").read_text())
    saved_pmids = {r["pmid"] for r in saved_records}
    package_pmids = {ref.pmid for ref in package.references if ref.pmid}
    assert saved_pmids == package_pmids

    trace = json.loads((out / "evidence_traceability.json").read_text())
    assert trace["total_claims"] == len(package.claims)
    for entry in trace["claim_traces"]:
        assert entry["traceability_status"] == "traceable"
