"""Fixture-based tests for the PubMed client and normalizer.

No live NCBI network calls are made by default.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from src.pubmed.briefs import generate_evidence_briefs
from src.pubmed.client import PubMedClient, PubMedClientConfig, PubMedError
from src.pubmed.models import PubMedRecord
from src.pubmed.normalizer import infer_evidence_level, infer_study_type, parse_efetch_xml


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
EFETCH_XML = (FIXTURE_DIR / "pubmed_efetch.xml").read_text(encoding="utf-8")
ESEARCH_JSON = json.loads((FIXTURE_DIR / "pubmed_esearch.json").read_text(encoding="utf-8"))


def _efetch_response() -> "_FakeResponse":
    return _FakeResponse(200, EFETCH_XML)


class _FakeResponse:
    def __init__(self, status_code: int, text: str, json_data: dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self.text = text
        self._json = json_data

    def json(self) -> dict[str, Any]:
        if self._json is None:
            raise ValueError("No JSON payload")
        return self._json


class _SearchThenFetch:
    """Fake httpx client that returns the fixture ESearch and EFetch responses."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def get(self, url: str, *, params: dict[str, Any] | None = None, **kwargs: Any) -> _FakeResponse:
        self.calls.append((url, params or {}))
        if "esearch" in url:
            return _FakeResponse(200, "", ESEARCH_JSON)
        return _efetch_response()


def _client_with_fake_http(fake: Any) -> PubMedClient:
    client = PubMedClient(PubMedClientConfig(api_key="test"))
    client._client = fake  # type: ignore[assignment]
    client._rate_limit = lambda: None  # disable rate limiting in tests
    return client


def test_query_construction():
    client = PubMedClient(PubMedClientConfig(api_key="test"))
    query = client.build_query("Dietary Fiber and Gut Health")
    assert '"Dietary Fiber"[Title/Abstract]' in query
    assert '"Gut Health"[Title/Abstract]' in query
    assert '("humans"[MeSH Terms] OR "human"[Title/Abstract])' in query
    assert '"systematic review"[Title/Abstract]' in query
    assert '"meta-analysis"[Title/Abstract]' in query
    assert '"guideline"[Title/Abstract]' in query


def test_esearch_parsing():
    fake = _SearchThenFetch()
    client = _client_with_fake_http(fake)
    raw, pmids = client.search("test query", max_results=3)
    assert raw == ESEARCH_JSON
    assert pmids == ["29902436", "30638909", "30202317"]


def test_efetch_parsing():
    records = parse_efetch_xml(EFETCH_XML)
    assert len(records) == 3, "Duplicate PMID 29902436 should be deduplicated"

    by_pmid = {r.pmid: r for r in records}
    assert "29902436" in by_pmid
    assert "30638909" in by_pmid
    assert "30202317" in by_pmid

    makki = by_pmid["29902436"]
    assert "Impact of Dietary Fiber on Gut Microbiota" in makki.title
    assert makki.publication_year == 2018
    assert makki.doi == "10.1016/j.chom.2018.05.012"
    assert makki.abstract is not None
    assert "Conclusion:" in makki.abstract
    assert makki.authors is not None
    assert "Makki K" in makki.authors
    assert "Cell Host &amp; Microbe" not in makki.journal  # XML entities resolved
    assert "Dietary Fiber" in makki.mesh_terms


def test_missing_abstract():
    records = parse_efetch_xml(EFETCH_XML)
    by_pmid = {r.pmid: r for r in records}
    missing = by_pmid["30202317"]
    assert missing.abstract is None


def test_missing_doi():
    records = parse_efetch_xml(EFETCH_XML)
    by_pmid = {r.pmid: r for r in records}
    missing = by_pmid["30202317"]
    assert missing.doi is None


def test_duplicate_pmid_removal():
    records = parse_efetch_xml(EFETCH_XML)
    pmids = [r.pmid for r in records]
    assert len(pmids) == len(set(pmids))
    assert pmids.count("29902436") == 1


def test_normalized_record_validation():
    records = parse_efetch_xml(EFETCH_XML)
    for record in records:
        validated = PubMedRecord(**record.model_dump(mode="json"))
        assert validated.pmid == record.pmid


def test_inferred_evidence_levels():
    records = parse_efetch_xml(EFETCH_XML)
    by_pmid = {r.pmid: r for r in records}
    reynolds = by_pmid["30638909"]
    assert infer_study_type(reynolds.publication_types, reynolds.title) == "meta-analysis"
    assert infer_evidence_level(reynolds.publication_types, reynolds.title) == "systematic review / meta-analysis"

    makki = by_pmid["29902436"]
    assert infer_evidence_level(makki.publication_types, makki.title) == "review / nonsystematic"


def test_retry_on_rate_limit():
    calls: list[int] = []

    class FlakyGet:
        def get(self, url: str, **kwargs: Any) -> _FakeResponse:
            calls.append(1)
            if len(calls) == 1:
                return _FakeResponse(429, "rate limited")
            return _FakeResponse(200, "", ESEARCH_JSON)

    client = _client_with_fake_http(FlakyGet())
    raw, pmids = client.search("query", max_results=3)
    assert len(calls) == 2
    assert pmids == ["29902436", "30638909", "30202317"]


def test_retry_on_timeout():
    calls: list[int] = []

    class TimeoutThenOk:
        def get(self, url: str, **kwargs: Any) -> _FakeResponse:
            calls.append(1)
            if len(calls) == 1:
                raise httpx.TimeoutException("timeout")
            return _FakeResponse(200, "", ESEARCH_JSON)

    client = _client_with_fake_http(TimeoutThenOk())
    raw, pmids = client.search("query", max_results=3)
    assert len(calls) == 2
    assert pmids == ["29902436", "30638909", "30202317"]


def test_timeout_failure_after_retries():
    class AlwaysTimeout:
        def get(self, url: str, **kwargs: Any) -> _FakeResponse:
            raise httpx.TimeoutException("timeout")

    client = _client_with_fake_http(AlwaysTimeout())
    with pytest.raises(PubMedError, match="failed after"):
        client.search("query", max_results=3)


def test_complete_pubmed_pipeline_with_fixtures(tmp_path: Path):
    client = _client_with_fake_http(_SearchThenFetch())
    result = client.retrieve(
        topic="Dietary Fiber and Gut Health",
        max_results=3,
        output_dir=tmp_path,
    )

    assert len(result.records) == 3
    assert len(result.briefs) == 3
    assert result.query.topic == "Dietary Fiber and Gut Health"

    # Saved artifacts
    assert (tmp_path / "search_query.json").exists()
    assert (tmp_path / "pubmed_raw.json").exists()
    assert (tmp_path / "pubmed_records.json").exists()
    assert (tmp_path / "evidence_brief.json").exists()

    saved_records = json.loads((tmp_path / "pubmed_records.json").read_text())
    assert len(saved_records) == 3
    pmids = {r["pmid"] for r in saved_records}
    assert pmids == {"29902436", "30638909", "30202317"}


def test_evidence_briefs_from_records():
    records = parse_efetch_xml(EFETCH_XML)
    briefs = generate_evidence_briefs(records, topic="Dietary Fiber and Gut Health")
    assert len(briefs) == 3
    by_pmid = {b.pmid: b for b in briefs}
    reynolds = by_pmid["30638909"]
    assert reynolds.evidence_level == "systematic review / meta-analysis"
    # Abstract-only retrieval is reviewable evidence input, not automatically
    # cleared for public education without full-text professional review.
    assert reynolds.usable_for_public_education is False
    assert reynolds.key_findings.startswith("Abstract excerpt from PubMed")
    missing = by_pmid["30202317"]
    assert missing.usable_for_public_education is False
    assert missing.key_findings == "not_reported"
    assert "no abstract" in missing.limitations.lower()
