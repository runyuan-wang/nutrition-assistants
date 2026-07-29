"""High-level lesson generator orchestrating provider -> package -> exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.exporters.ppt import PptxExporter
from src.providers.base import LessonProvider, ProviderError
from src.providers.mock_provider import MockProvider
from src.pubmed.builder import PubMedLessonBuilder
from src.pubmed.client import (
    PubMedClient,
    PubMedClientConfig,
    PubMedRetrievalResult,
)
from src.pubmed.traceability import (
    build_traceability_report,
    validate_pubmed_traceability,
)
from src.schemas.lesson import Language, LessonPackage, QualityReport
from src.pipeline.validator import QualityValidator


class LessonGenerator:
    """Generate and export a complete lesson package."""

    def __init__(
        self,
        provider: LessonProvider | None = None,
        output_dir: Path | str = "output",
    ) -> None:
        self.provider = provider or MockProvider()
        self.output_dir = Path(output_dir)
        self.validator = QualityValidator()
        self.ppt_exporter = PptxExporter()

    def generate(
        self,
        topic: str,
        audience: str,
        language: Language = Language.EN,
        duration_minutes: int = 30,
        evidence_source: str = "mock",
        max_pubmed_results: int = 10,
        pubmed_date_range: tuple[str | None, str | None] = (None, None),
        pubmed_timeout: float = 30.0,
    ) -> LessonPackage:
        if evidence_source.lower() == "mock":
            if not self.provider.is_available():
                raise ProviderError(f"Provider '{self.provider.name}' is not available.")
            package = self.provider.generate(
                topic=topic,
                audience=audience,
                language=language,
                duration_minutes=duration_minutes,
            )
        elif evidence_source.lower() == "pubmed":
            if language != Language.EN:
                raise ProviderError("PubMed evidence mode only supports English (en).")
            package = self._generate_from_pubmed(
                topic=topic,
                audience=audience,
                language=language,
                duration_minutes=duration_minutes,
                max_results=max_pubmed_results,
                date_range=pubmed_date_range,
                timeout=pubmed_timeout,
            )
        else:
            raise ProviderError(
                f"Unknown evidence source '{evidence_source}'. Supported: mock, pubmed."
            )

        report = self.validator.validate(package)
        if report.issues:
            # Attach report in memory only; exporters write it to disk.
            pass

        return package

    def _generate_from_pubmed(
        self,
        topic: str,
        audience: str,
        language: Language,
        duration_minutes: int,
        max_results: int,
        date_range: tuple[str | None, str | None],
        timeout: float,
    ) -> LessonPackage:
        try:
            config = PubMedClientConfig(timeout=timeout)
            with PubMedClient(config) as client:
                result = client.retrieve(
                    topic,
                    max_results=max_results,
                    date_range=date_range,
                )

            package = PubMedLessonBuilder(
                topic=topic,
                audience=audience,
                language=language,
                duration_minutes=duration_minutes,
                records=result.records,
            ).build()

            # Fail closed on invented references, metadata drift, unlinked claims,
            # and incorrect slide mappings before any export is possible.
            validate_pubmed_traceability(package, result.records)
        except ProviderError:
            raise
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"PubMed generation validation failed: {exc}") from exc

        report = self.validator.validate(package)
        if not report.pass_quality_gate:
            issues = [
                f"{issue.rule}: {issue.message}"
                for issue in report.issues
                if issue.severity == "error"
            ]
            raise ProviderError(
                f"PubMed lesson failed quality gate: {'; '.join(issues)}"
            )

        canonical_request = {
            "topic": topic,
            "audience": audience,
            "language": language.value,
            "duration_minutes": duration_minutes,
            "evidence_source": "pubmed",
            "max_pubmed_results": max_results,
            "date_from": result.query.date_range[0],
            "date_to": result.query.date_range[1],
            "pubmed_timeout_seconds": timeout,
        }
        # These private run artifacts intentionally do not enter lesson_spec.json,
        # but a PubMed package cannot be exported successfully without them.
        object.__setattr__(package, "_pubmed_result", result)
        object.__setattr__(package, "_pubmed_request", canonical_request)
        return package

    def export_package(
        self,
        package: LessonPackage,
        output_dir: Path | str | None = None,
        pubmed_request: dict[str, Any] | None = None,
    ) -> Path:
        out = Path(output_dir) if output_dir else self.output_dir
        out.mkdir(parents=True, exist_ok=True)

        is_pubmed = package.generation.provider_name.lower() == "pubmed"
        pubmed_result: PubMedRetrievalResult | None = getattr(
            package, "_pubmed_result", None
        )
        if is_pubmed:
            if pubmed_result is None:
                raise ProviderError(
                    "PubMed export requires the original validated retrieval result; "
                    "refusing to write an incomplete output tree."
                )
            attached_request: dict[str, Any] | None = getattr(
                package, "_pubmed_request", None
            )
            if attached_request is None:
                raise ProviderError(
                    "PubMed export is missing canonical request metadata; refusing "
                    "to omit request.json."
                )
            request = dict(attached_request)
            if pubmed_request:
                for key, value in pubmed_request.items():
                    if key in request and request[key] != value:
                        raise ProviderError(
                            f"PubMed request metadata mismatch for '{key}': "
                            f"generated={request[key]!r}, supplied={value!r}."
                        )
                    request[key] = value
            self._export_pubmed_artifacts(out, package, pubmed_result, request)

        # 1. Canonical spec
        spec_path = out / "lesson_spec.json"
        spec_path.write_text(package.to_canonical_dict(), encoding="utf-8")

        # 2. Markdown lesson outline
        outline_path = out / "lesson_outline.md"
        outline_path.write_text(self._render_outline(package), encoding="utf-8")

        # 3. Speaker notes
        notes_path = out / "speaker_notes.md"
        notes_path.write_text(self._render_speaker_notes(package), encoding="utf-8")

        # 4. References
        refs_path = out / "references.md"
        refs_path.write_text(self._render_references(package), encoding="utf-8")

        # 5. Quality report
        report = self.validator.validate(package)
        report_path = out / "quality_report.md"
        report_path.write_text(self._render_quality_report(report), encoding="utf-8")

        # 6. PowerPoint
        ppt_path = out / "nutrition_lesson.pptx"
        self.ppt_exporter.export(package, ppt_path)

        return out

    def _export_pubmed_artifacts(
        self,
        out: Path,
        package: LessonPackage,
        result: PubMedRetrievalResult,
        request: dict[str, Any],
    ) -> None:
        try:
            validate_pubmed_traceability(package, result.records)
        except ValueError as exc:
            raise ProviderError(f"PubMed export validation failed: {exc}") from exc

        (out / "request.json").write_text(
            json.dumps(request, indent=2, ensure_ascii=False), encoding="utf-8"
        )

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
                [r.model_dump(mode="json") for r in result.records],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        (out / "evidence_brief.json").write_text(
            json.dumps(
                [b.model_dump(mode="json") for b in result.briefs],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8"
        )

        trace_report = build_traceability_report(package, result.records)
        (out / "evidence_traceability.json").write_text(
            trace_report.model_dump_json(indent=2), encoding="utf-8"
        )

    @staticmethod
    def _render_outline(package: LessonPackage) -> str:
        lines = [
            f"# {package.metadata.title}",
            "",
            f"**Topic:** {package.metadata.topic}",
            f"**Audience:** {package.metadata.audience}",
            f"**Duration:** {package.metadata.duration_minutes} minutes",
            f"**Language:** {package.metadata.language.value}",
            f"**Provider:** {package.generation.provider_name} ({package.generation.provider_version})",
            "",
            "## Disclaimer",
            "",
            package.metadata.disclaimer,
            "",
            "## Learning Objectives",
            "",
        ]
        for obj in package.metadata.learning_objectives:
            lines.append(f"- {obj}")
        lines.append("")
        lines.append("## Slide Outline")
        lines.append("")
        for slide in package.slides:
            lines.append(f"### Slide {slide.slide_number}: {slide.title}")
            for point in slide.key_points:
                lines.append(f"- {point}")
            if slide.citation_ids:
                lines.append(
                    "\n*Citations:* " + ", ".join(slide.citation_ids)
                )
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _render_speaker_notes(package: LessonPackage) -> str:
        lines = [
            f"# Speaker Notes: {package.metadata.title}",
            "",
        ]
        for slide in package.slides:
            lines.append(f"## Slide {slide.slide_number}: {slide.title}")
            if slide.speaker_notes:
                lines.append(slide.speaker_notes)
            if slide.notes_for_educator:
                lines.append("")
                lines.append(f"**Educator note:** {slide.notes_for_educator}")
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _render_references(package: LessonPackage) -> str:
        lines = [
            f"# References: {package.metadata.title}",
            "",
        ]
        for ref in package.references:
            parts = [f"## {ref.citation_id}"]
            if ref.title:
                parts.append(f"**Title:** {ref.title}")
            if ref.authors:
                parts.append(f"**Authors:** {ref.authors}")
            if ref.year:
                parts.append(f"**Year:** {ref.year}")
            if ref.journal_or_org:
                parts.append(f"**Journal/Organization:** {ref.journal_or_org}")
            if ref.doi:
                parts.append(f"**DOI:** {ref.doi}")
            if ref.pmid:
                parts.append(f"**PMID:** {ref.pmid}")
            if ref.url:
                parts.append(f"**URL:** {ref.url}")
            parts.append(f"**Evidence level:** {ref.evidence_level.value}")
            parts.append(f"**Reference type:** {ref.reference_type.value}")
            if ref.provenance_note:
                parts.append(f"**Provenance:** {ref.provenance_note}")
            if ref.population:
                parts.append(f"**Population:** {ref.population}")
            if ref.limitations:
                parts.append(f"**Limitations:** {ref.limitations}")
            lines.extend(parts)
            lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _render_quality_report(report: QualityReport) -> str:
        r = report
        lines = [
            f"# Quality Report: {r.package_title}",
            "",
            f"**Generated at:** {r.generated_at.isoformat()}",
            f"**Quality gate:** {'PASS' if r.pass_quality_gate else 'FAIL'}",
            "",
            "## Summary",
            "",
            f"- Total slides: {r.total_slides}",
            f"- Total claims: {r.total_claims}",
            f"- Total citations: {r.total_citations}",
            f"- Claims with citations: {r.claims_with_citations}",
            f"- Causal claims: {r.causal_claims}",
            f"- Disease/treatment claims: {r.disease_treatment_claims}",
            f"- Unsupported numerical claims: {r.unsupported_numerical_claims}",
            f"- Unverified/provider-generated citations: {r.unverified_citations}",
            "",
            "## Issues",
            "",
        ]
        if not r.issues:
            lines.append("No issues detected.")
        else:
            for issue in r.issues:
                lines.append(f"### {issue.severity.upper()}: {issue.rule}")
                lines.append(issue.message)
                if issue.claim_id:
                    lines.append(f"*Claim:* {issue.claim_id}")
                if issue.slide_number:
                    lines.append(f"*Slide:* {issue.slide_number}")
                if issue.suggestion:
                    lines.append(f"*Suggestion:* {issue.suggestion}")
                lines.append("")
        lines.append("")
        lines.append("## Summary Text")
        lines.append("")
        lines.append(r.summary)
        return "\n".join(lines)
