# Citation Integrity Contract

> **Schema version:** `citation-integrity-v1.0`
> **Status:** MANDATORY for all modes (A / B / C) and all evidence tracks (T1–T4)
> **Referenced by:** `layer8_evidence_query.md` gates E6a–E6d, `SKILL.md` safety red lines, `safety_red_lines.md`, `ROUTING.yaml` (`citation_verifiability`)
> **Purpose:** Guarantee that every literature citation in any output is real, complete, formatted to a standard, and traceable to its original record — and that fabrication is structurally impossible, not merely discouraged.

---

## 0. Iron Rules (不可协商的铁律)

| # | Rule | Meaning |
|---|------|---------|
| R1 | **No locator, no citation.** | A reference may appear in output ONLY if it maps 1:1 to a Citation Ledger row carrying a resolvable locator (PMID / DOI / NCT / Cochrane ID / CNKI accession URL). |
| R2 | **Whitelisted sources only.** | Evidence may be retrieved ONLY from sources registered in `reference/source_registry.md`. Anything else is discarded on arrival. |
| R3 | **Absent is a valid result.** | A scoped zero-result is reported honestly as `absent`. It must NEVER be filled with fabricated, memory-generated, or non-whitelisted material. |
| R4 | **Standard format or nothing.** | Every output citation follows the standard format in §3 and ends with its canonical locator URL. Non-standard citations are removed before delivery. |

---

## 1. Source Whitelist (来源白名单)

### 1.1 ALLOWED sources

Only `source_id` values registered in `reference/source_registry.md`, e.g.:

- Human clinical: `pubmed`, `cochrane`, `embase`, `clinicaltrials_gov`, `who_ictrp`, `cnki`, `cbm`, `who_itrp`
- TCM / official material: `cp2020`, `cp_previous`, `tcm_classics`, `who_mong`, `escop`, `hmpdc`
- Mechanistic / safety: `nih_ods`, `examine`, `naturalmedicines`, `pubchem`, `lactmed`
- Regulatory authorities listed in the registry (NMPA, FDA, EFSA, …) — for the regulatory track only, never as efficacy evidence.

### 1.2 PROHIBITED sources (禁止作为证据来源)

The following must NEVER enter the Search Ledger, Citation Ledger, or any output as evidence:

- WeChat Official Accounts (微信公众号) and any self-media / content-farm articles (自媒体、营销号)
- Blogs, forums, Q&A sites, social media posts
- Marketing, e-commerce, or vendor promotional pages (产品宣传页、电商详情页)
- Wikipedia or any crowd-sourced encyclopedia (as efficacy evidence)
- Any website not registered in `source_registry.md`

If a retrieval tool returns such sources, they are **discarded on arrival** — not quoted, not paraphrased, not "used for inspiration". Discovery of candidate topics from non-whitelisted material is permitted only if every resulting citation is independently re-retrieved from a whitelisted source before use.

---

## 2. Minimum Citation Fields (最小完整字段集)

A citation is COMPLETE only when ALL of the following are present in its Citation Ledger row:

| Field | Requirement |
|-------|-------------|
| `title` | Original-language title, verbatim from the source record |
| `authors` | At least first author (+ `et al.` where applicable) |
| `journal` | Full or NLM-abbreviated journal name — never an invented abbreviation |
| `year` | Publication year |
| `volume_pages` | Volume / issue / pages or article number (when applicable) |
| `study_type` | One of: `meta_analysis`, `systematic_review`, `large_rct`, `small_rct`, `controlled_trial`, `case_report`, `none_found` |
| `source_id` | A registered ID from `source_registry.md` |
| `locator_type` | One of: `pmid`, `doi`, `nct`, `cochrane_id`, `cnki_url`, `cbm_id` |
| `locator_value` | The identifier itself (e.g. `PMID: 38012345`) |
| `locator_url` | Canonical URL resolving to the original record (see §3.3) |
| `retrieved_at` | ISO 8601 date of retrieval in the current session |

A citation missing ANY field is INCOMPLETE: it must not support any efficacy claim, and the gap is recorded in the ledger.

---

## 3. Standard Citation Format (标准引用格式)

### 3.1 English-language references — NLM / Vancouver style

```
Author AA, Author BB, Author CC, et al. Article title in sentence case. J Abbrev. Year;Volume(Issue):Pages. doi:10.xxxx/xxxxx. PMID: xxxxxxxx.
```

Example:

```
Smith J, Wang L, Chen Y, et al. Vitamin D supplementation and upper respiratory infections: a randomized controlled trial. J Nutr. 2023;153(4):1023-35. doi:10.1016/j.jnut.2023.01.012. PMID: 38012345.
```

### 3.2 Chinese-language references — GB/T 7714-2015

```
第一作者, 第二作者, 等. 文献题名[J]. 刊名, 年, 卷(期): 起-止页码. DOI 或 CNKI 链接.
```

### 3.3 Canonical locator URLs (原文可追溯链接)

Every output citation MUST end with a clickable canonical URL built from its locator:

| Locator | Canonical URL template |
|---------|------------------------|
| PMID | `https://pubmed.ncbi.nlm.nih.gov/{PMID}/` |
| DOI | `https://doi.org/{DOI}` |
| NCT number | `https://clinicaltrials.gov/study/{NCT}` |
| Cochrane review | `https://www.cochranelibrary.com/cdsr/doi/{DOI}/full` |
| CNKI record | The record's detail-page URL on `cnki.net` |
| CBM record | The record's detail-page URL on `sinomed.ac.cn` |

A locator that cannot be expanded into a canonical URL is not a valid locator.

---

## 4. Verification Status Vocabulary (验证状态)

| Status | Meaning | Output effect |
|--------|---------|---------------|
| `verified` | Locator re-checked against the source record in the current session; all Minimum Citation Fields consistent | May support claims at its own evidence tier |
| `partially_verified` | Record located, but ≥1 field inconsistent (e.g. page range, year) | Discrepancy must be flagged; evidence downgraded one tier |
| `unverified` | No live re-check possible (no retrieval tool, or citation originates from the textbook corpus) | Must be labeled `待核验 / unverified`; cannot support efficacy claims on its own |
| `rejected` | Locator does not resolve, or fields contradict the source record | REMOVE from output; log the rejection reason in the ledger |

---

## 5. Prohibited Patterns (禁止行为清单)

1. Generating any citation from model memory in a session without an actual retrieval call returning that record.
2. Inventing, "repairing", or guessing PMIDs, DOIs, NCT numbers, trial registrations, page ranges, or years.
3. Combining a real journal name with an unverified or fabricated title.
4. Writing "studies show…" / "有研究表明…" without a ledger-backed standard citation and locator URL.
5. Treating search-result snippets or abstracts as full-text conclusions.
6. Using any §1.2 prohibited source as evidence (公众号、自媒体、营销网站等).
7. Upgrading `unverified` citations into efficacy evidence.
8. Filling a zero-result gap with fabricated or non-whitelisted material instead of reporting `absent` per §7.
9. Claiming "searched the whole internet" or "covered all databases".

---

## 6. Verification Workflow (按 agent 能力分级执行)

### 6.1 Agent WITH live retrieval tools

1. Execute track queries per `layer8_evidence_query.md`, using whitelisted `source_id`s only.
2. Record EVERY retrieved candidate citation in the Citation Ledger with all Minimum Citation Fields.
3. For each citation selected for output, re-resolve its locator (PMID/DOI/NCT lookup) and compare fields → set `verified` / `partially_verified` / `rejected`.
4. Output may cite ONLY `verified` entries, or `partially_verified` entries with the discrepancy explicitly flagged.

### 6.2 Agent WITHOUT live retrieval tools

1. MUST state in the output: `本会话未执行实时文献检索 / No live literature retrieval was performed in this session.`
2. May cite ONLY citations already present in the textbook corpus, every one marked `unverified`.
3. Evidence status is capped at `weak`; efficacy claims are prohibited.
4. Recommend re-running the query with a retrieval-enabled agent.

---

## 7. Absent Reporting Standard (无证据的可追溯声明)

A claim of "no evidence found" must itself be traceable. Every `absent` result carries its search scope:

```
absent — searched: pubmed, cochrane, embase (2026-07-29);
queries: "magnesium glycinate AND insomnia randomized";
eligible records: 0.
```

`absent` means "not detected within this scoped search". It never means "proven not to exist", and it never authorizes filling the gap by other means.

---

## 8. Binding & Fail-Closed Gates (绑定与门控)

| Gate | Rule | Violation consequence |
|------|------|----------------------|
| C1 | Every output citation maps 1:1 to a Citation Ledger row with a valid locator and canonical URL | Orphan citation → removed before delivery |
| C2 | Citation Ledger row count ≥ output citation count | Missing ledger rows → abort finalization |
| C3 | Every efficacy-supporting citation is `verified` | `unverified` support → claim downgraded to `weak`/`absent` |
| C4 | Every zero-result query is ledgered as `absent` per §7, never fabricated | Fabricated filler → abort finalization |
| C5 | Every citation follows §3 standard format with a canonical locator URL | Non-standard citation → removed before delivery |
| C6 | Every cited `source_id` exists in `source_registry.md` | Non-whitelisted source → citation removed; if intentional, abort finalization |

---

## 9. Relationship to Existing Contracts

- This contract REFINES gate (E6) of `layer8_evidence_query.md` into executable gates E6a–E6d.
- It does NOT relax any existing gate: identity gating (`BLOCKED_IDENTITY`), regulatory gating, corpus two-pass coverage, and human-review finalization remain fully in force.
- Ledger implementations: `templates/search_ledger_template.md` (Citation Ledger section) and `reference/evidence_ledger_template.json` (`citations[]` arrays with verification fields).
