"""Official NCBI E-utilities client for PubMed retrieval."""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from src import __version__
from src.providers.base import ProviderError
from src.pubmed.briefs import generate_evidence_briefs
from src.pubmed.models import EvidenceBrief, PubMedRecord, PubMedSearchQuery
from src.pubmed.normalizer import parse_efetch_xml


PMID_RE = re.compile(r"^[1-9]\d*$")
DATE_RE = re.compile(r"^\d{4}(?:/\d{2}/\d{2})?$")


class PubMedError(ProviderError):
    """Raised when PubMed retrieval cannot be completed safely."""


@dataclass
class PubMedRetrievalResult:
    """Container for all artifacts produced by a PubMed retrieval."""

    query: PubMedSearchQuery
    raw_esearch: dict[str, Any]
    raw_efetch: str
    records: list[PubMedRecord] = field(default_factory=list)
    briefs: list[EvidenceBrief] = field(default_factory=list)


def _default_user_agent() -> str:
    user_agent = (
        f"NutritionLessonGenerator/{__version__} "
        "(official NCBI E-utilities client)"
    )
    contact = os.getenv("NCBI_EMAIL", "").strip()
    if contact:
        user_agent += f"; mailto:{contact}"
    return user_agent


@dataclass
class PubMedClientConfig:
    """Runtime configuration for NCBI E-utilities requests."""

    base_url: str = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    timeout: float = 30.0
    max_retries: int = 3
    user_agent: str = field(default_factory=_default_user_agent)
    api_key: str | None = field(default_factory=lambda: os.getenv("NCBI_API_KEY"))

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")
        self.user_agent = self.user_agent.strip()
        if self.timeout <= 0:
            raise ValueError("PubMed timeout must be greater than zero seconds.")
        if self.max_retries < 1:
            raise ValueError("PubMed max_retries must be at least 1.")
        if not self.user_agent:
            raise ValueError("PubMed User-Agent must not be blank.")

    @property
    def rate_limit_delay(self) -> float:
        # NCBI allows about 3 requests/second without a key and 10/second with one.
        return 0.11 if self.api_key else 0.34


class PubMedClient:
    """Retrieve and normalize PubMed records via official NCBI E-utilities.

    There is deliberately no fallback to MockProvider or generated evidence.
    """

    def __init__(self, config: PubMedClientConfig | None = None) -> None:
        self.config = config or PubMedClientConfig()
        self._client = httpx.Client(
            timeout=httpx.Timeout(self.config.timeout),
            headers={"User-Agent": self.config.user_agent},
        )
        self._last_request_at: float = 0.0

    def __enter__(self) -> "PubMedClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._client.close()

    def retrieve(
        self,
        topic: str,
        max_results: int = 10,
        date_range: tuple[str | None, str | None] = (None, None),
        output_dir: Path | str | None = None,
    ) -> PubMedRetrievalResult:
        """Run a full PubMed search, fetch, normalize, and validate cycle."""
        topic = topic.strip()
        if not topic:
            raise PubMedError("PubMed topic must not be blank.")
        _validate_max_results(max_results)
        normalized_range = _validate_date_range(date_range)

        query = self.build_query(topic, date_range=normalized_range)
        try:
            query_meta = PubMedSearchQuery(
                topic=topic,
                final_query=query,
                date_range=normalized_range,
                requested_max_count=max_results,
            )
        except ValueError as exc:
            raise PubMedError(f"Invalid PubMed search request: {exc}") from exc

        raw_esearch, pmids = self.search(query, max_results=max_results)
        if not pmids:
            raise PubMedError(
                f"No PubMed results for topic '{topic}'. Query: {query}"
            )

        raw_efetch = self.fetch(pmids)
        try:
            parsed_records = parse_efetch_xml(raw_efetch)
        except ValueError as exc:
            raise PubMedError(f"Malformed or invalid PubMed EFetch response: {exc}") from exc
        if not parsed_records:
            raise PubMedError(
                f"PubMed returned PMIDs {pmids} but EFetch produced no records."
            )

        parsed_by_pmid = {record.pmid: record for record in parsed_records}
        requested_set = set(pmids)
        unexpected = sorted(set(parsed_by_pmid) - requested_set)
        missing = [pmid for pmid in pmids if pmid not in parsed_by_pmid]
        if unexpected:
            raise PubMedError(
                "EFetch returned PMID(s) not requested by ESearch: "
                + ", ".join(unexpected)
            )
        if missing:
            raise PubMedError(
                "EFetch did not return all requested PMID(s): " + ", ".join(missing)
            )

        # Preserve ESearch order after XML-level deduplication.
        records = [parsed_by_pmid[pmid] for pmid in pmids]
        briefs = generate_evidence_briefs(records, topic)
        result = PubMedRetrievalResult(
            query=query_meta,
            raw_esearch=raw_esearch,
            raw_efetch=raw_efetch,
            records=records,
            briefs=briefs,
        )

        if output_dir is not None:
            self.save_outputs(result, Path(output_dir))
        return result

    def build_query(
        self,
        topic: str,
        date_range: tuple[str | None, str | None] = (None, None),
        include_human: bool = True,
        include_reviews: bool = True,
        include_guidelines: bool = True,
    ) -> str:
        """Build a conservative topic-focused PubMed query."""
        cleaned = topic.strip().replace('"', "")
        phrases = _topic_to_phrases(cleaned)
        if not phrases:
            raise PubMedError(f"Could not build a PubMed query from topic '{topic}'.")
        topic_clause = " AND ".join(
            f'"{phrase}"[Title/Abstract]' for phrase in phrases
        )
        clauses: list[str] = [f"({topic_clause})"]

        if include_human:
            clauses.append('("humans"[MeSH Terms] OR "human"[Title/Abstract])')

        evidence_clauses: list[str] = []
        if include_reviews:
            evidence_clauses.extend(
                [
                    '"systematic review"[Title/Abstract]',
                    '"meta-analysis"[Title/Abstract]',
                    '"review"[Title/Abstract]',
                ]
            )
        if include_guidelines:
            evidence_clauses.extend(
                [
                    '"guideline"[Title/Abstract]',
                    '"consensus"[Title/Abstract]',
                ]
            )
        if evidence_clauses:
            clauses.append(f"({' OR '.join(evidence_clauses)})")

        query = " AND ".join(clauses)
        start, end = _validate_date_range(date_range)
        if start or end:
            start_date = start or "1800/01/01"
            end_date = end or "2100/12/31"
            query += (
                f' AND ("{start_date}"[Date - Publication] : '
                f'"{end_date}"[Date - Publication])'
            )
        return query

    def search(
        self, query: str, max_results: int = 10
    ) -> tuple[dict[str, Any], list[str]]:
        """Call ESearch and strictly parse a deduplicated PMID list."""
        _validate_max_results(max_results)
        params: dict[str, Any] = {
            "db": "pubmed",
            "term": query,
            "retmode": "json",
            "retmax": max_results,
            "sort": "relevance",
        }
        if self.config.api_key:
            params["api_key"] = self.config.api_key

        response = self._request("/esearch.fcgi", params)
        try:
            data = response.json()
        except (ValueError, json.JSONDecodeError) as exc:
            raise PubMedError(f"Malformed non-JSON ESearch response: {exc}") from exc
        if not isinstance(data, dict):
            raise PubMedError("Malformed ESearch response: top-level JSON must be an object.")
        result = data.get("esearchresult")
        if not isinstance(result, dict):
            raise PubMedError("Malformed ESearch response: missing object 'esearchresult'.")
        idlist = result.get("idlist")
        if not isinstance(idlist, list):
            raise PubMedError("Malformed ESearch response: 'idlist' must be a list.")

        pmids: list[str] = []
        seen: set[str] = set()
        for raw_pmid in idlist:
            if isinstance(raw_pmid, bool) or not isinstance(raw_pmid, (str, int)):
                raise PubMedError(
                    f"Malformed ESearch response: invalid PMID value {raw_pmid!r}."
                )
            pmid = str(raw_pmid).strip()
            if not PMID_RE.fullmatch(pmid):
                raise PubMedError(f"Malformed ESearch response: invalid PMID {pmid!r}.")
            if pmid not in seen:
                seen.add(pmid)
                pmids.append(pmid)
        if len(pmids) > max_results:
            raise PubMedError(
                f"Malformed ESearch response: returned {len(pmids)} unique PMIDs "
                f"for retmax={max_results}."
            )
        return data, pmids

    def fetch(self, pmids: list[str]) -> str:
        """Call EFetch and return the raw XML response body."""
        normalized_pmids = _validate_pmids(pmids)
        if len(normalized_pmids) > 200:
            raise PubMedError(
                f"PubMed batch size {len(normalized_pmids)} exceeds limit 200."
            )

        params: dict[str, Any] = {
            "db": "pubmed",
            "id": ",".join(normalized_pmids),
            "retmode": "xml",
        }
        if self.config.api_key:
            params["api_key"] = self.config.api_key
        return self._request("/efetch.fcgi", params).text

    def save_outputs(
        self,
        result: PubMedRetrievalResult,
        output_dir: Path,
    ) -> None:
        """Save raw, normalized, and brief outputs to disk."""
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        (out / "search_query.json").write_text(
            result.query.model_dump_json(indent=2), encoding="utf-8"
        )
        raw_payload = {
            "esearch": result.raw_esearch,
            "efetch_xml": result.raw_efetch,
        }
        (out / "pubmed_raw.json").write_text(
            json.dumps(raw_payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out / "pubmed_records.json").write_text(
            json.dumps(
                [record.model_dump(mode="json") for record in result.records],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        (out / "evidence_brief.json").write_text(
            json.dumps(
                [brief.model_dump(mode="json") for brief in result.briefs],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    def _request(self, path: str, params: dict[str, Any]) -> httpx.Response:
        """Execute a rate-limited GET with only allowed transient retries."""
        url = f"{self.config.base_url}{path}"
        last_exception: Exception | None = None

        for _attempt in range(1, self.config.max_retries + 1):
            self._rate_limit()
            try:
                response = self._client.get(url, params=params)
            except httpx.TimeoutException as exc:
                # Timeouts are explicitly transient and retryable.
                last_exception = exc
                continue
            except httpx.RequestError as exc:
                # DNS, connection, TLS, and other request failures are surfaced
                # immediately; they are not in the authorized retry set.
                raise PubMedError(
                    f"Non-retryable NCBI network error for {url}: {exc}"
                ) from exc

            if response.status_code == 429 or response.status_code >= 500:
                last_exception = PubMedError(
                    f"NCBI returned transient HTTP {response.status_code} for {url}"
                )
                if response.status_code == 429:
                    time.sleep(self.config.rate_limit_delay * 2)
                continue
            if response.status_code >= 400:
                raise PubMedError(
                    f"NCBI returned HTTP {response.status_code} for {url}: "
                    f"{response.text[:500]}"
                )
            return response

        raise PubMedError(
            f"NCBI request failed after {self.config.max_retries} attempts: "
            f"{last_exception}"
        )

    def _rate_limit(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request_at
        delay = self.config.rate_limit_delay
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self._last_request_at = time.monotonic()


def _validate_max_results(max_results: int) -> None:
    if isinstance(max_results, bool) or not isinstance(max_results, int):
        raise PubMedError("max_results must be an integer.")
    if not 1 <= max_results <= 200:
        raise PubMedError("max_results must be between 1 and 200.")


def _validate_pmids(pmids: list[str]) -> list[str]:
    if not pmids:
        raise PubMedError("Cannot fetch PubMed records without PMIDs.")
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_pmid in pmids:
        pmid = str(raw_pmid).strip()
        if not PMID_RE.fullmatch(pmid):
            raise PubMedError(f"Invalid PMID for EFetch: {pmid!r}.")
        if pmid not in seen:
            seen.add(pmid)
            normalized.append(pmid)
    return normalized


def _validate_date_range(
    date_range: tuple[str | None, str | None]
) -> tuple[str | None, str | None]:
    try:
        validated = PubMedSearchQuery(
            topic="date-validation",
            final_query="date-validation",
            date_range=date_range,
            requested_max_count=1,
        ).date_range
    except ValueError as exc:
        raise PubMedError(f"Invalid PubMed publication date range: {exc}") from exc
    return validated


_STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}


def _topic_to_phrases(topic: str) -> list[str]:
    """Split a topic into consecutive non-stop-word phrases."""
    tokens = topic.split()
    phrases: list[str] = []
    current: list[str] = []
    for token in tokens:
        lowered = token.lower().strip(",.;:")
        if lowered in _STOP_WORDS:
            if current:
                phrases.append(" ".join(current))
                current = []
        else:
            current.append(token)
    if current:
        phrases.append(" ".join(current))
    return phrases
