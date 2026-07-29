# Layer 8: Four-Track Evidence Discovery & Regulatory Gate

> **Schema version:** `layer8-evidence-v2.1`
> **Supersedes:** `layer8-evidence-v2.0` (adds Citation Integrity binding)
> **Purpose:** After draft generation, execute a traceable, non-silent four-track evidence workflow. Each component receives a result or a ledgered failure/blocked row; gaps block only finalization, efficacy promotion, or market claims, never the reviewable draft.
> **Related contract (MANDATORY):** `reference/citation_integrity_contract.md` — every citation produced by this workflow must satisfy its Iron Rules (no locator no citation; whitelisted sources only; absent is valid; standard format or nothing).

---

## Core Principle

The textbook corpus provides theoretical framework and classical formulation logic. Nutritional science and clinical research advance continuously. Every draft runs four traceable tracks—human, animal/in-vivo, TCM/material, and regulatory—plus a reminder/safety sidecar. A missing/blocked/zero-result attempt is recorded, not silently omitted.

---

## 1. Formula Context and Identity Eligibility

- Draft creation occurs before research eligibility decisions. Missing medication, pregnancy/lactation, allergy, target market/category, or other intake facts become `UNKNOWN` reminder/review fields.
- Botanical-specific search requires the identity tuple: common/local name, Latin species, plant part, preparation/extract, marker constituent, dose unit.
- An unresolved botanical becomes `BLOCKED_IDENTITY`: preserve its draft row; create a query-ledger row with `outcome=blocked`; do not issue falsely specific botanical queries; ask the reviewer for the identity tuple.
- Missing market/category produces T4 `not_assessed`/`unknown`, not an invented status.

## 2. Four Evidence Tracks

### Track 1: Human Clinical Evidence
Search verified SR/MA/RCT and human clinical records, using ONLY whitelisted `source_id`s from `reference/source_registry.md` (non-registered sources such as WeChat Official Accounts, self-media, blogs, and marketing sites are prohibited). For every selected source report locator, population, intervention/specification, dose, duration, outcome, limitations, query, source, and date. Snippets are not evidence; a scoped no-result is not proof of no evidence. Every citation must satisfy `reference/citation_integrity_contract.md`: complete minimum fields, standard citation format, canonical locator URL, and a recorded verification status.

### Track 2: Animal/In-vivo Evidence
For each selected source report species/model, route, animal dose/unit, duration, endpoints, locator, translation limits, and the mandatory warning that animal findings/doses do not establish human efficacy/dose.

### Track 3: TCM/Material Evidence
T1 classical material requires text title, edition/version, and exact entry/page/volume location; T2 official material requires a verifiable pharmacopeial/monograph identity record; T3 modern TCM clinical research is analysed under Track 1 standards. T1/T2 never prove efficacy.

### Track 4: Regulatory Evidence
Record ingredient identity × product category × declared target market using authoritative sources. Status vocabulary: `permitted`, `conditional`, `prohibited`, `unknown`, `not_assessed`. Missing market/category has status `not_assessed`; it blocks only market/clearance claims.

### Reminder/Safety Sidecar (not Track 4)
Record mechanism level, adverse-effect signals, interaction signals, medication/use-time questions, and red flags. Always set `mechanism_is_not_efficacy_proof=true`; no such signal can become human efficacy or regulatory evidence.

## 3. Evidence Discovery Query Plan

For each formula, produce a query plan record BEFORE executing searches:

| Field | Description |
|-------|-------------|
| `formula_id` | Formula identifier |
| `search_date` | ISO 8601 date |
| `tracks_executed` | List of tracks (T1-T4) |
| `sources_searched` | Per-track list of sources with query strings |
| `total_queries_executed` | Count |
| `queries_with_results` | Count |
| `queries_no_results` | Count |
| `coverage_notes` | Any source gaps, access limitations, or notes |

**Staged discovery requirement:**
1. **Stage 1 (Pre-formula, Step 0):** Indication-level discovery — search broadly for ALL nutrients/supplements with evidence for the target condition, not limited to textbook recommendations.
2. **Stage 2 (Post-formula):** Per-ingredient search — for each ingredient in the final formula, execute all four tracks.
3. **Stage 3 (Regulatory):** Per-ingredient × per-jurisdiction regulatory assessment per `regulatory_gate.md`.

---

## 4. Evidence Status Vocabulary

| Status | Meaning | Gate Effect |
|--------|---------|-------------|
| `supported` | Adequate human clinical evidence found from authoritative sources | Passes evidence gate |
| `weak` | Some evidence found but of low quality, small sample, or limited applicability | Passes with caveats; must state limitations |
| `absent` | No human clinical evidence found in searched sources | Does NOT imply safety; blocks efficacy claims |
| `conflicting` | Evidence found but results are contradictory | Must present both sides; blocks definitive claims |
| `animal_only` | Only animal evidence available | Human efficacy claim prohibited; translation limits mandatory |
| `traditional_only` | Only traditional/classical record | Clinical efficacy claim prohibited |
| `mechanistic_only` | Only mechanistic/in vitro evidence | Clinical efficacy claim prohibited |

---

## 5. Evidence × Regulatory Independence

The evidence gate and regulatory gate are **independent, parallel gates**:

- A formula with strong clinical evidence but no regulatory authorization → CANNOT be marketed.
- A formula with regulatory authorization but no clinical evidence → CANNOT claim efficacy.
- A formula must pass BOTH gates to be both evidence-supported and market-authorized.
- Failure of either gate independently blocks the respective claim.

---

## 6. Updated Output Tables

### Table 1: Four-Track Evidence Matrix

| Ingredient | Dose | Track 1: Human Clinical | Track 2: Animal | Track 3: TCM Material | Track 4: Mechanistic/Safety |
|------------|------|------------------------|-----------------|----------------------|---------------------------|
| [name] | [dose] | [study_type: details, locator, limitations] | [species/model: findings, locator, translation limits] | [T1: classical record / T2: pharmacopoeia / T3: modern clinical] | [pathways, adverse effects, interactions] |

### Table 2: Regulatory Coverage Matrix

| Ingredient | Dose | Jurisdiction | Category | Authority | Status | Max Level | Source/Doc | Checked | Limitations |
|------------|------|-------------|----------|-----------|--------|-----------|------------|---------|-------------|
| [name] | [dose] | [market] | [cat] | [auth] | [status] | [level] | [ref] | [date] | [limits] |

### Table 3: Search Ledger

| Ingredient | Track | Source | Query String | Date | Results | Selected | Notes |
|------------|-------|--------|-------------|------|---------|----------|-------|
| [name] | [T1/T2/T3/T4/REG] | [source_id] | [query] | [date] | [count] | [count] | [notes] |

---

## 7. Fail-Closed Finalization Gates (Updated)

| Gate | Condition | Fail-Closed Rule |
|------|-----------|------------------|
| (E1) | Formula context and identity fully resolved | Missing/ambiguous context or identity → abort |
| (E2) | All four evidence tracks executed for every ingredient | Any unexecuted track → abort |
| (E3) | Human evidence status does not imply efficacy when absent | Text implies efficacy but `evidence_status=absent` → abort |
| (E4) | Animal/traditional/mechanistic evidence not promoted to clinical proof | Cross-tier promotion detected → abort |
| (E5) | Regulatory assessment completed for every ingredient × every declared jurisdiction × every category | Any `unknown` or `not_assessed` → blocks "market-ready" claim |
| (E6a) | Every output citation complies with `citation_integrity_contract.md` Iron Rules R1–R4: ledger-backed locator with canonical URL, whitelisted `source_id`, standard citation format | Orphan / non-standard / non-whitelisted citation → removed; intentional fabrication → abort |
| (E6b) | Citation gates C1–C6 of `citation_integrity_contract.md` all pass (1:1 binding, ledger coverage, verified-for-efficacy, absent-never-filled, standard format, whitelist) | Any C-gate failed → abort finalization |
| (E6c) | Sessions without live retrieval declare "No live literature retrieval was performed", mark all citations `unverified`, and cap evidence at `weak` | Undeclared memory-based citation → abort |
| (E6d) | Every zero-result query is ledgered as `absent` with its search scope per contract §7; rejected citations removed and logged | Fabricated filler or silent zero-result → abort |
| (E7) | Search ledger AND citation ledger recorded for all queries and citations | Missing search or citation record → abort |
| (E8) | Retains existing two-pass textbook corpus safety contract (Phase A/B) | Phase A/B coverage incomplete → abort |

---

## 8. Retained Baseline Elements

The following baseline elements are RETAINED and remain mandatory:
- Step 0 (pre-formula indication-level literature discovery)
- Step 1-6 formula design workflow
- Two-pass corpus retrieval contract (Phase A targeted + Phase B sweep)
- Coverage ledger with SHA-256 verification
- Finalization gates (A-D) from `formula_full_scan_contract.md`
- All safety red lines from `safety_red_lines.md`
- Special population safety gates
- Anti-hallucination citation rules

This document ADDS four evidence tracks, a regulatory gate, and a search ledger ON TOP of the existing contract.
