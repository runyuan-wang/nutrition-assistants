---
name: nutrition-lesson-generator
version: 0.2.0
last_changed_at: 2026-07-17T18:36:30-07:00
description: Generate evidence-informed nutrition lesson packages with PowerPoint export and optional PubMed retrieval.
triggers:
  - nutrition lesson generator
  - generate nutrition lesson
  - nutrition education pptx
  - dietary fiber lesson
  - evidence based nutrition lesson
  - create nutrition slides
non_triggers:
  - video generation
  - voice generation
  - image generation
  - web app
  - medical diagnosis
  - prescription
  - supplement dosing
inputs:
  topic:
    type: string
    required: true
    description: Nutrition topic to teach.
  audience:
    type: string
    required: false
    default: general adults
    description: Target audience for the lesson.
  language:
    type: string
    required: false
    default: en
    description: Output language (MVP supports en only).
  duration:
    type: integer
    required: false
    default: 30
    description: Target lesson duration in minutes.
  output_dir:
    type: string
    required: false
    default: output
    description: Directory for generated artifacts.
  evidence_source:
    type: string
    required: false
    default: mock
    description: Evidence source — 'mock' (offline) or 'pubmed' (live NCBI retrieval).
---

# Nutrition Lesson Generator — Skill

Use this project when a user asks for a nutrition education lesson, slide deck, speaker notes, or evidence-based teaching materials.

## When to invoke

- User wants a lesson on a nutrition topic (e.g., dietary fiber, hydration, macronutrients).
- User wants a PowerPoint for health educators, dietitians, or general adults.
- User wants structured speaker notes and references alongside slides.
- User explicitly asks for PubMed-backed evidence retrieval for a nutrition topic.

## When NOT to invoke

- User asks for medical diagnosis, treatment plans, prescription changes, or supplement dosing.
- User asks for video/voice/image generation, or a web app.
- User asks for arbitrary health advice for a specific individual.

## Safe evidence rules

1. Every substantive health claim must cite a reference.
2. Never turn observational associations into causal claims.
3. Keep `evidence`, `interpretation`, and `practical_advice` separate.
4. Never include disease treatment promises, diagnosis, prescription, supplement dosing, or medication-change advice.
5. Always include limitations and population/applicability notes.
6. Flag unsupported numerical claims.
7. Use only verified citations; PubMed mode uses records retrieved live from NCBI, while mock mode uses the bundled development fixture.
8. Never fabricate PMIDs, DOIs, titles, or authors. If PubMed retrieval fails, report the failure instead of falling back to mock data.

## CLI

Run from the project root `nutrition-lesson-generator/`.

Default offline mock mode:

```bash
python -m src.main generate \
  --topic "Dietary Fiber and Gut Health" \
  --audience "general adults" \
  --language en \
  --duration 30 \
  --output-dir output
```

Optional PubMed evidence mode (requires network access to NCBI E-utilities):

```bash
python -m src.main generate \
  --topic "Dietary Fiber and Gut Health" \
  --audience "general adults" \
  --language en \
  --duration 10 \
  --evidence-source pubmed \
  --max-results 10 \
  --output-dir output/pubmed-lesson
```

Retrieval-only mode (inspect PubMed records without generating a lesson):

```bash
python -m src.main retrieve \
  --topic "Dietary Fiber and Gut Health" \
  --max-results 10 \
  --output output/pubmed-test
```

## Expected outputs

### Mock mode

- `lesson_spec.json` — canonical Pydantic-serialized package.
- `lesson_outline.md` — slide-by-slide outline.
- `speaker_notes.md` — notes for each slide.
- `references.md` — full citations with provenance and limitations.
- `quality_report.md` — structured validation report.
- `nutrition_lesson.pptx` — real PowerPoint.

### PubMed mode

All mock-mode files plus:

- `request.json` — generation request parameters.
- `search_query.json` — final PubMed query and request metadata.
- `pubmed_raw.json` — raw ESearch/EFetch responses for debugging.
- `pubmed_records.json` — normalized PubMed records.
- `evidence_brief.json` — conservative summaries of each record.
- `evidence_traceability.json` — claim-to-PMID/slide traceability.

## Validation gates

Do not present results as final until:

1. `lesson_spec.json` validates against the canonical Pydantic model.
2. `nutrition_lesson.pptx` is non-empty, reopens with `pptx.Presentation`, and is a valid OOXML ZIP.
3. All expected outputs exist for the selected evidence mode.
4. The quality report is derived from actual structured claims and citations (not hard-coded).
5. No disease-treatment or causal-overstatement issues are present.
6. In PubMed mode, every cited PMID is present in `pubmed_records.json` and `evidence_traceability.json` is complete.

## Architecture summary

- `src/schemas/lesson.py` — canonical models.
- `src/providers/` — provider interface + offline `MockProvider`.
- `src/pubmed/` — NCBI E-utilities client, normalizer, evidence briefs, lesson builder, traceability.
- `src/pipeline/generator.py` — orchestrates generation, retrieval, and exports.
- `src/pipeline/validator.py` — evidence/safety quality checks.
- `src/exporters/ppt.py` — PowerPoint export.
- `examples/dietary_fiber_evidence_fixture.json` — verified offline fixture.

## Limitations

- English only.
- One curated offline fixture (dietary fiber and gut health); arbitrary mock topics use a safe placeholder lesson.
- PubMed mode is retrieval-only and template-based; it does not perform full-text analysis or clinical appraisal.
- No LLM providers, RAG guideline database, web UI, or video/voice/image generation.
