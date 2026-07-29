# Nutrition Lesson Generator

An open-source toolkit for evidence-based nutrition education.

Turn a nutrition topic into a structured, evidence-informed lesson package with a real PowerPoint export — no paid API required. The default `mock` mode is fully offline; an optional `pubmed` mode retrieves real metadata from NCBI PubMed and links every claim to a PubMed identifier.

## Real output preview

![Real Nutrition Lesson Generator output showing all 12 generated artifacts, including nutrition_lesson.pptx](docs/images/real-output-preview.png)

*Actual v0.2.0 PubMed-mode run: the generated package contains 12 artifacts, including the editable `nutrition_lesson.pptx`, lesson specification, outline, speaker notes, references, evidence traceability, and quality report. The image preserves the real file names and byte sizes from the validated run.*

## Problem

Nutrition professionals and health educators repeatedly build slide decks, speaker notes, and reference lists from scratch. Generative AI can accelerate this, but nutrition content carries special risks: causal overstatement, fabricated citations, treatment promises, and unsupported numerical claims. This project provides a **structured, auditable pipeline** that keeps the human educator in control and makes evidence quality explicit.

## Why AI Assistance Helps

- **Consistency:** every lesson follows the same canonical schema.
- **Safety:** a built-in validator flags missing citations, causal overstatement, disease-treatment language, and unsupported numbers.
- **Transparency:** output includes a machine-readable spec, Markdown artifacts, a quality report, and — in PubMed mode — raw/normalized records plus claim-to-PMID traceability.
- **Extensibility:** provider interface lets future LLM or retrieval backends plug in without changing exporters.

## Features

- Typer-based Python CLI.
- Pydantic canonical schema (`lesson_spec.json`).
- Evidence/citation-aware lesson content.
- Markdown exports: outline, speaker notes, references, quality report.
- Real `.pptx` export via `python-pptx`.
- Fully offline `MockProvider` with a curated dietary-fiber evidence fixture (default).
- Optional PubMed evidence mode using official NCBI E-utilities via `httpx`.
- Retrieval-only `retrieve` command for inspection before lesson generation.
- Claim-to-PMID traceability report in PubMed mode.
- Pytest test suite covering schema validation, quality checks, PPT export, PubMed parsing, and end-to-end generation.

## Installation

Requires Python 3.11+.

```bash
cd nutrition-lesson-generator
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

No API key is required for the default `mock` mode or for public-rate PubMed access. For higher-rate PubMed access, request a free NCBI API key at https://www.ncbi.nlm.nih.gov/account/ and set it as `NCBI_API_KEY`. You may also set `NCBI_EMAIL` so the descriptive User-Agent includes a real contact; no placeholder contact is sent.

## Usage

### Mock mode (default — offline, deterministic)

Generate the canonical dietary-fiber example:

```bash
python -m src.main generate \
  --topic "Dietary Fiber and Gut Health" \
  --audience "general adults" \
  --language en \
  --duration 30
```

This writes six files to `output/`:

```text
output/
├── lesson_spec.json
├── lesson_outline.md
├── speaker_notes.md
├── references.md
├── quality_report.md
└── nutrition_lesson.pptx
```

### PubMed mode (live NCBI metadata retrieval)

Generate a lesson from real PubMed records:

```bash
python -m src.main generate \
  --topic "Dietary Fiber and Gut Health" \
  --audience "general adults" \
  --language en \
  --duration 10 \
  --evidence-source pubmed \
  --max-results 10 \
  --date-from 2010 \
  --date-to 2025 \
  --pubmed-timeout 30
```

The date options are optional and accept `YYYY` or `YYYY/MM/DD`. The timeout is configurable for live NCBI requests. PubMed mode has no silent fallback to mock evidence.

This writes the PubMed-mode output tree:

```text
output/<run>/
├── request.json
├── search_query.json
├── pubmed_raw.json
├── pubmed_records.json
├── evidence_brief.json
├── evidence_traceability.json
├── lesson_spec.json
├── lesson_outline.md
├── speaker_notes.md
├── references.md
├── quality_report.md
└── nutrition_lesson.pptx
```

### Retrieval-only mode

Inspect PubMed records without generating a lesson:

```bash
python -m src.main retrieve \
  --topic "Dietary Fiber and Gut Health" \
  --max-results 10 \
  --output output/pubmed-test
```

This saves `search_query.json`, `pubmed_raw.json`, `pubmed_records.json`, and `evidence_brief.json`.

### Run tests

```bash
python -m pytest -v
```

The default test suite uses local fixtures and does not call NCBI.

## Architecture

```text
src/
├── main.py                 # Typer CLI (generate, retrieve, version)
├── schemas/
│   └── lesson.py           # Canonical Pydantic models
├── pipeline/
│   ├── generator.py        # Orchestrates provider / PubMed retrieval + exports
│   └── validator.py        # Evidence/safety quality checks
├── exporters/
│   └── ppt.py              # python-pptx exporter
├── providers/
│   ├── base.py             # Abstract provider interface
│   └── mock_provider.py    # Offline deterministic provider
└── pubmed/
    ├── client.py           # NCBI E-utilities client
    ├── models.py           # PubMedRecord, EvidenceBrief, PubMedSearchQuery
    ├── normalizer.py       # EFetch XML → typed records
    ├── briefs.py           # EvidenceBrief generation
    ├── builder.py          # LessonPackage assembly from PubMed records
    └── traceability.py     # Claim-to-PMID traceability + integrity gates

templates/
└── ppt_template.py         # Slide styling helpers

examples/
└── dietary_fiber_evidence_fixture.json  # Verified offline evidence
```

## Evidence Contract

1. Every substantive health claim maps to one or more citations.
2. Observational associations are never turned into causal claims.
3. `evidence_statement`, `interpretation`, and `practical_advice` are kept separate.
4. No disease diagnosis, treatment, prescription, supplement dosing, or medication-change advice.
5. Limitations and population/applicability notes are included.
6. Unsupported numerical claims are flagged.
7. Verified development fixtures, PubMed-retrieved records, and provider-generated citations are clearly distinguished.
8. DOI/PMID/title/organization are not fabricated.
9. In PubMed mode, every cited PMID must exist in `pubmed_records.json`; invented or fallback citations are rejected.
10. Full references remain in `references.md` and the final reference slide; slide footers show compact `PMID: 12345678` citations.

## Traceability and Citation Integrity (PubMed Mode)

- `pubmed_records.json` contains the normalized NCBI records used by the lesson.
- `evidence_traceability.json` maps each claim to supporting PMIDs and the exact slides where the full claim text is visibly present with its citation.
- The fail-closed gate rejects missing/unknown citations, absent or duplicate PMIDs, reference metadata that does not match normalized records, and invalid claim-slide mappings.
- References are generated only from normalized retrieved records; duplicate PMIDs are deduplicated.
- A record without an abstract remains visible as insufficient evidence but produces no title-derived health claim or generated summary.

## Important Warnings

- **Retrieval does not guarantee evidence quality.** PubMed mode only proves that a record exists and was retrieved; it does not assess internal validity, risk of bias, or clinical relevance.
- **Abstracts are not full text.** The generated lesson is based on metadata and abstracts. A nutrition professional should review the full article before using any record in education or public-health messaging.
- **No medical advice.** All output is for educational purposes only and is not a substitute for professional diagnosis or treatment advice.
- **No silent fallback.** If PubMed retrieval fails, returns no results, or produces a quality-gate failure, the tool reports the error and does not silently substitute mock evidence.

## Limitations

- Only English (`en`) is supported in this version.
- PubMed mode is intentionally simple: it builds a conservative, template-based lesson from retrieved metadata without natural-language generation.
- The PubMed query is conservative and may return fewer records than a broad web search.
- One curated offline fixture is included (dietary fiber and gut health); arbitrary mock topics use a safe placeholder lesson.
- No LLM providers, RAG guideline database, web UI, video/voice/image generation, or clinical decision support.

## Roadmap (not implemented)

- Online LLM providers (OpenAI, Anthropic, local models) behind the provider interface.
- More sophisticated evidence extraction from full-text or structured abstracts.
- Additional curated offline evidence fixtures.
- Multi-language support.
- Optional web UI or API server.
- Video/voice/image generation remain out of scope.

## Author / 作者

**王润圆 (Wang Runyuan)**

昆明医科大学营养与食品卫生学硕士，中国注册营养师，云南天文爱好者协会秘书处干事。好奇心强，长期参与科普活动；正在学习并探索把 AI 与营养学科普和实际营养工作相结合，希望帮助更多人。

Wang Runyuan holds a master's degree in Nutrition and Food Hygiene from Kunming Medical University, is a Chinese Registered Dietitian, and serves on the secretariat of the Yunnan Astronomy Enthusiasts Association. Curious and active in science communication for many years, she is exploring how AI can support nutrition education and practical nutrition work to help more people.

- GitHub: [@9s5bz2jvd2-lang](https://github.com/9s5bz2jvd2-lang)
- Contact: [jykmsg@163.com](mailto:jykmsg@163.com)

## License

Apache-2.0. See [LICENSE](LICENSE).
