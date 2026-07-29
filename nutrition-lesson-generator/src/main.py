"""Typer CLI for the Nutrition Lesson Generator."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from src.pipeline.generator import LessonGenerator
from src.providers.base import ProviderError
from src.providers.mock_provider import MockProvider
from src.pubmed.client import PubMedClient, PubMedClientConfig, PubMedError
from src.schemas.lesson import Language


class EvidenceSource(str, Enum):
    """Supported evidence backends."""

    MOCK = "mock"
    PUBMED = "pubmed"


app = typer.Typer(
    name="nutrition-lesson",
    help="Generate evidence-informed nutrition lesson packages.",
    no_args_is_help=True,
)
console = Console()


def _get_provider(provider_name: str):
    if provider_name.lower() == "mock":
        return MockProvider()
    raise typer.BadParameter(
        f"Unknown provider '{provider_name}'. MVP supports 'mock' only."
    )


@app.command()
def generate(
    topic: str = typer.Option(
        ...,
        "--topic",
        "-t",
        help="Nutrition topic for the lesson.",
    ),
    audience: str = typer.Option(
        "general adults",
        "--audience",
        "-a",
        help="Target audience (e.g., 'general adults', 'health educators').",
    ),
    language: str = typer.Option(
        "en",
        "--language",
        "-l",
        help="Output language code (MVP supports 'en').",
    ),
    duration: int = typer.Option(
        30,
        "--duration",
        "-d",
        help="Target lesson duration in minutes.",
        min=5,
        max=180,
    ),
    output_dir: Path = typer.Option(
        Path("output"),
        "--output-dir",
        "-o",
        help="Directory where outputs are written.",
    ),
    provider: str = typer.Option(
        "mock",
        "--provider",
        "-p",
        help="Provider to use (MVP supports 'mock' only).",
    ),
    evidence_source: EvidenceSource = typer.Option(
        EvidenceSource.MOCK,
        "--evidence-source",
        "-e",
        help="Evidence source: mock (offline default) or pubmed (live NCBI).",
        case_sensitive=False,
    ),
    max_results: int = typer.Option(
        10,
        "--max-results",
        "-m",
        help="Maximum PubMed records when --evidence-source=pubmed.",
        min=1,
        max=100,
    ),
    date_from: Optional[str] = typer.Option(
        None,
        "--date-from",
        help="Optional PubMed publication-date start (YYYY or YYYY/MM/DD).",
    ),
    date_to: Optional[str] = typer.Option(
        None,
        "--date-to",
        help="Optional PubMed publication-date end (YYYY or YYYY/MM/DD).",
    ),
    pubmed_timeout: float = typer.Option(
        30.0,
        "--pubmed-timeout",
        help="NCBI request timeout in seconds for PubMed mode.",
        min=0.1,
        max=300.0,
    ),
    skip_quality_gate: bool = typer.Option(
        False,
        "--skip-quality-gate",
        help="Export despite the general quality gate; PubMed integrity never skips.",
    ),
) -> None:
    """Generate a complete lesson package for TOPIC."""
    try:
        lang = Language(language.lower())
    except ValueError as exc:
        raise typer.BadParameter(f"Unsupported language '{language}'.") from exc

    if evidence_source == EvidenceSource.MOCK and (date_from or date_to):
        raise typer.BadParameter(
            "--date-from/--date-to require --evidence-source pubmed."
        )

    prov = _get_provider(provider)
    generator = LessonGenerator(provider=prov, output_dir=output_dir)

    console.print(f"[bold blue]Generating lesson:[/bold blue] {topic}")
    console.print(
        f"[blue]Audience:[/blue] {audience} | "
        f"[blue]Language:[/blue] {language} | "
        f"[blue]Duration:[/blue] {duration} min | "
        f"[blue]Evidence source:[/blue] {evidence_source.value}"
    )

    try:
        package = generator.generate(
            topic=topic,
            audience=audience,
            language=lang,
            duration_minutes=duration,
            evidence_source=evidence_source.value,
            max_pubmed_results=max_results,
            pubmed_date_range=(date_from, date_to),
            pubmed_timeout=pubmed_timeout,
        )

        report = generator.validator.validate(package)
        if not report.pass_quality_gate:
            console.print(
                f"[yellow]Quality gate failed with {len(report.issues)} issue(s).[/yellow]"
            )
            for issue in report.issues:
                if issue.severity == "error":
                    console.print(
                        f"  [red]ERROR[/red] {issue.rule}: {issue.message}"
                    )
                elif issue.severity == "warning":
                    console.print(
                        f"  [yellow]WARN[/yellow] {issue.rule}: {issue.message}"
                    )
            if not skip_quality_gate:
                console.print(
                    "[red]Export aborted. Use --skip-quality-gate to override.[/red]"
                )
                raise typer.Exit(code=2)
            console.print(
                "[yellow]Exporting anyway because --skip-quality-gate was set.[/yellow]"
            )
        else:
            console.print(
                f"[green]Quality gate passed[/green] "
                f"({len(report.issues)} info/warning issue(s))."
            )

        # PubMed request metadata is attached during generation. export_package
        # refuses to omit it and revalidates all claim-slide-PMID links.
        out = generator.export_package(package, output_dir)
    except ProviderError as exc:
        console.print(f"[red]Generation/export failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    except (OSError, ValueError) as exc:
        console.print(f"[red]Output validation failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Exported package to:[/green] {out.resolve()}")
    for artifact in sorted(out.iterdir()):
        console.print(f"  - {artifact.name}")


@app.command()
def retrieve(
    topic: str = typer.Option(
        ...,
        "--topic",
        "-t",
        help="Nutrition topic to search PubMed.",
    ),
    max_results: int = typer.Option(
        10,
        "--max-results",
        "-m",
        help="Maximum records to retrieve.",
        min=1,
        max=100,
    ),
    output: Path = typer.Option(
        Path("output/pubmed-retrieval"),
        "--output",
        "-o",
        help="Directory where PubMed retrieval artifacts are written.",
    ),
    date_from: Optional[str] = typer.Option(
        None,
        "--date-from",
        help="Optional publication-date start (YYYY or YYYY/MM/DD).",
    ),
    date_to: Optional[str] = typer.Option(
        None,
        "--date-to",
        help="Optional publication-date end (YYYY or YYYY/MM/DD).",
    ),
    timeout: float = typer.Option(
        30.0,
        "--timeout",
        help="NCBI request timeout in seconds.",
        min=0.1,
        max=300.0,
    ),
) -> None:
    """Retrieve PubMed records for TOPIC without generating a lesson."""
    console.print(f"[bold blue]Retrieving PubMed evidence for:[/bold blue] {topic}")

    try:
        config = PubMedClientConfig(timeout=timeout)
        with PubMedClient(config) as client:
            client.retrieve(
                topic=topic,
                max_results=max_results,
                date_range=(date_from, date_to),
                output_dir=output,
            )
    except (PubMedError, OSError, ValueError) as exc:
        console.print(f"[red]PubMed retrieval failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[green]Saved PubMed artifacts to:[/green] {output.resolve()}")
    for artifact in sorted(output.iterdir()):
        console.print(f"  - {artifact.name}")


@app.command()
def version() -> None:
    """Show version information."""
    from src import __version__

    console.print(f"Nutrition Lesson Generator v{__version__}")


if __name__ == "__main__":
    app()
