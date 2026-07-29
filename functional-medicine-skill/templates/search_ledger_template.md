# Template: Per-Source Search Ledger

> **Usage:** Record every search query executed for this formula. One row per query.
> **Governing contract:** `reference/citation_integrity_contract.md` (`citation-integrity-v1.0`) — whitelisted sources only; every citation must carry a locator and verification status.

## Metadata

| Field | Value |
|-------|-------|
| Formula ID | |
| Search Date | |
| Total Queries | |
| Live Retrieval Performed | yes / no (if no: all citations `unverified`, evidence capped at `weak`) |
| Citation Integrity Contract Version | citation-integrity-v1.0 |

## Search Ledger

| # | Ingredient | Track | Source ID | Source Name | Query String | Date Searched | Raw Results Count | Selected for Inclusion | Notes/Gaps |
|---|-----------|-------|-----------|------------|-------------|---------------|-------------------|----------------------|-----------|
| 1 | | T1: Human | | | | | | | |
| 2 | | T2: Animal | | | | | | | |
| 3 | | T3: TCM | | | | | | | |
| 4 | | T4: Mechanistic | | | | | | | |
| 5 | | Regulatory | | | | | | | |
| ... | | | | | | | | | |

## Citation Ledger (引用级台账 — MANDATORY)

> One row per citation RETRIEVED from a whitelisted source, whether or not it is selected for output.
> No locator, no citation: a row without `locator_value` + `locator_url` may never reach the output.
> `source_id` must exist in `reference/source_registry.md`; WeChat Official Accounts / self-media / blogs / marketing sites are prohibited and must be discarded on arrival.

| # | Ingredient | Track | Source ID | Full Citation (standard format: NLM/Vancouver for EN, GB/T 7714 for ZH) | Locator Type (pmid/doi/nct/cochrane_id/cnki_url/cbm_id) | Locator Value | Locator URL | Retrieved At | Verification Status (verified/partially_verified/unverified/rejected) | Verification Method | Rejection / Discrepancy Notes |
|---|-----------|-------|-----------|--------------------------------------------------------------------------|----------------------------------------------------------|---------------|-------------|--------------|------------------------------------------------------------------------|---------------------|-------------------------------|
| 1 | | | | | | | | | | | |
| 2 | | | | | | | | | | | |
| ... | | | | | | | | | | | |

### Absent Records (无证据可追溯声明)

> Every zero-result query must be recorded here with its scope — `absent` is a valid result and must never be filled with fabricated material.

| Ingredient | Track | Sources Searched (source_ids) | Query String(s) | Date | Eligible Records (=0) | Declared As |
|-----------|-------|-------------------------------|-----------------|------|-----------------------|-------------|
| | | | | | 0 | absent |
| | | | | | 0 | absent |

## Staged Discovery Summary

### Stage 1: Indication-Level Discovery (Pre-Formula)

| Search Round | Query | Source | Date | Results | New Candidates Found |
|-------------|-------|--------|------|---------|---------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

### Stage 2: Per-Ingredient Search (Post-Formula)

See main ledger above.

### Stage 3: Regulatory Assessment

| Ingredient | Jurisdiction | Category | Source | Date | Result |
|-----------|-------------|----------|--------|------|--------|
| | | | | | |

## Source Gaps

Record any sources that could NOT be accessed, had limited coverage, or showed gaps:

| Source | Gap Description | Impact |
|--------|----------------|--------|
| | | |
