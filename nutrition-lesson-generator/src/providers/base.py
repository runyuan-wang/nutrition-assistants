"""Abstract provider interface for lesson generation.

A provider turns a user request (topic, audience, language) into a canonical
LessonPackage. The interface is provider-agnostic so that future LLM-backed
providers can be swapped in without changing the pipeline.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.schemas.lesson import LessonPackage, Language


class ProviderError(Exception):
    """Raised when a provider cannot generate a lesson."""

    pass


class LessonProvider(ABC):
    """Abstract base class for lesson providers."""

    name: str = "abstract"
    version: str = "0.0.0"
    requires_api_key: bool = False

    @abstractmethod
    def generate(
        self,
        topic: str,
        audience: str,
        language: Language,
        duration_minutes: int = 30,
    ) -> LessonPackage:
        """Generate a canonical lesson package.

        Args:
            topic: The nutrition topic requested by the user.
            audience: Intended audience string.
            language: Output language (MVP supports English).
            duration_minutes: Target lesson length.

        Returns:
            A validated LessonPackage.

        Raises:
            ProviderError: If generation cannot be completed safely.
        """
        ...

    def is_available(self) -> bool:
        """Return True if the provider can be used right now."""
        return True
