"""PubMed evidence retrieval layer for the Nutrition Lesson Generator."""

from __future__ import annotations

from src.pubmed.client import PubMedClient, PubMedError, PubMedRetrievalResult
from src.pubmed.models import EvidenceBrief, PubMedRecord, PubMedSearchQuery

__all__ = [
    "PubMedClient",
    "PubMedError",
    "PubMedRetrievalResult",
    "PubMedRecord",
    "EvidenceBrief",
    "PubMedSearchQuery",
]
