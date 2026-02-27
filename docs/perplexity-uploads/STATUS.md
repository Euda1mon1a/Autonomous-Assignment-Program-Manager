# Perplexity Computer Research Sessions

> **Platform:** Perplexity Max ($200/mo) — 40MB/file, 100+ files/upload, 10K credits/month
> **Last Updated:** 2026-02-26

## Session Status

| # | Session | Status | Upload Size | Results Filed | Key Findings |
|---|---------|--------|-------------|---------------|--------------|
| 1 | `full-stack` | Done | ~5MB | `RESULTS.md` | CP-SAT weight sweep (2,100 configs), 35 security findings (10 critical), 65 API mismatches, 3 Excel import bugs |
| 2 | `exotic-research` | Done | ~3MB | `RESULTS.md` | Betweenness centrality, burstiness B parameter, ACO warm-start, CMA-ES bilevel weight optimization |
| 3 | `ortools-upgrade` | Done | ~2MB | `RESULTS.md` | OR-Tools 9.8-9.12 changelog, PEP 8 rename, hint system rewrite in v9.12, migration checklist |
| 4 | `accessibility-508` | Done | ~1MB | `RESULTS.md` | Landmarks/headings, keyboard nav, ARIA patterns, drag-and-drop, color contrast, remediation priority |
| 5 | `competitive-intel` | Done | ~500KB | `RESULTS.md` | 13,762 ACGME programs, 167K trainees, $1.3B TAM, no competitor does cross-block optimization |
| 6 | `postgres-tuning` | Done | ~1MB | `RESULTS.md` | 76 query patterns, 24 new indexes, connection pool tuning, materialized views, monitoring config |
| 7 | `annual-leap` | Done | 404KB (19 files) | `RESULTS.md` | 4,036-line reference: ACGME longitudinal validation (1-in-7 sliding window, 14-hr post-call), PGY SCD2 model (admin-triggered advancement), CP-SAT equity injection (MAD via add_abs_equality, gamma=1 adaptive), leave hybrid model (NOT event sourcing), YTD_SUMMARY chained SUMIF, 10-step migration sequence |
| 8 | `full-codebase` | Done | 39MB (7 files) | `RESULTS.md` | 51 unmigrated models, 20 SQL injection vectors, `prior_calls` never hydrated (call equity no-op), 8 untested edge cases, 1,096 unbounded queries, 38 untested services, 331 secret exposure points |

## Folder Convention

```
docs/perplexity-uploads/
├── STATUS.md              ← this file
└── started/
    ├── {session-name}/
    │   ├── README.md      ← upload manifest + research sections
    │   ├── PROMPT.md      ← the prompt sent to Perplexity
    │   ├── RESULTS.md     ← research output (filed when complete)
    │   └── {source files} ← uploaded files
    └── ...
```

## Cross-Session Dependencies

Sessions 7 and 8 were designed to run in parallel:

- **`annual-leap`** (19 files, deep) — sees constraint internals, CP-SAT injection patterns, engine structure
- **`full-codebase`** (39MB, wide) — sees every file, every import chain, every test gap

Where they agree: high confidence. Where they disagree: investigate. Where one finds something the other missed: that's the value of running both.

Sessions 1-6 results are embedded in `full-codebase/prior_research_results.md` so session 8 builds on them rather than re-deriving.

## Resolved Findings (Feb 26, 2026 Sprint)

7 PRs merged (#1196–#1202) addressing findings from sessions 7 and 8:

| Finding | Session | Status | Resolution |
|---------|---------|--------|------------|
| 4.2: `prior_calls` never hydrated | #8 | **FIXED** (PR #1199) | GROUP BY query in `_build_context()` with CASE expression for `effective_type` |
| 5.2.1: 20 SQL injection vectors | #8 | **FIXED** (PRs #1197, #1200, #1201) | `validate_identifier()` + `validate_search_path()` in `sql_identifiers.py` |
| Dead scaffolding modules | #8 (1.1.1) | **FIXED** (PR #1198) | 27,598 lines removed (~19 modules: CQRS, event sourcing, SAML, sharding, etc.) |
| Call equity Min-Max incompatible | #7 | **FIXED** (PR #1199) | MAD via `AddAbsEquality`, F-multiplied integers for CP-SAT |
| FMIT weekend calls misclassified | Codex review | **FIXED** (PR #1202) | `is_weekend` CASE expression reclassifies overnight+weekend as sunday equity |
| Alembic chain divergence | #8 (4.1) | **FIXED** (PR #1196) | Heads merged, chain linearized |
| Stroboscopic ImportError fallback | Codex review | **FIXED** (PR #1201) | Removed broken fallback, event_bus made optional |

**Still open from session 8:**
- Finding 1.1.1: Remaining unmigrated models (after ~19 dead modules removed)
- Finding 3.3.1: 8 untested scheduling edge cases
- Finding 4.5: YTD_SUMMARY hardcoded column positions

## What to Do When Results Come Back

1. Save output to `started/{session-name}/RESULTS.md`
2. Update this table (Status → Done, fill Key Findings)
3. Cross-reference with other session results
4. Create implementation tasks from actionable findings
