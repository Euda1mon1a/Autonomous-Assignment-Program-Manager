# PII Audit Findings — Comprehensive Scan Report

> **Date:** 2026-02-25
> **Status:** FINDINGS ONLY — No remediation performed
> **Branch:** `main` (HEAD `e36c5509`)
> **Prior Incidents:** #001 (Dec 2025), #002 (Feb 5), #003 (Feb 21 — catastrophic corruption)
> **Related Docs:** `PII_AUDIT_LOG.md`, `docs/planning/PII_HISTORY_PURGE_PLAN.md`

---

## Executive Summary

Real names of **30 people** (17 residents + 13 faculty) are present across **~50 tracked files** on HEAD with **~590 total occurrences**. An additional **12 PERSEC-critical items** combine names with deployment dates, TDY schedules, leave records, and military rank. PII is embedded in **143 of 2,445 git commits** (5.8%), spanning from 2025-12-16 through 2026-02-21. This data is currently live on GitHub (`origin/main`).

A purge plan was written on Feb 21 (`docs/planning/PII_HISTORY_PURGE_PLAN.md`) but has never been successfully executed. The one attempt on that date corrupted `origin/main` (Incident #003) and required a bundle restore.

---

## 1. Scope Summary

| Metric | Value |
|--------|-------|
| Unique real people identified | **30** (17 residents + 13 faculty) |
| Files on HEAD with PII | **~50** |
| Total name occurrences | **~590** |
| PERSEC-critical items | **12** |
| Git commits with PII in file content | **143** of 2,445 (5.8%) |
| Commit messages with real names | **25+** |
| Date range of contamination | 2025-12-16 to 2026-02-21 (67 days) |
| Alembic migrations with PII (Hard Boundary) | **4 files** |
| Replacement rules file status | 79 rules, covers 28 of 30 people (missing Lamoureux, Montgomery excluded) |
| `git-filter-repo` installed | Yes |
| Open PRs | 0 |

---

## 2. Complete Roster of Identified Individuals

### 2a. Residents (17)

| # | Last Name | First Name (Nicknames) | PGY | Files | Occurrences | Pseudonym |
|---|-----------|------------------------|-----|-------|-------------|-----------|
| 1 | Byrnes | Katherine (Katie) | 1 | 15 | 20 | PGY1-F |
| 2 | Cataquiz | Felipe | 2 | 7 | 10 | PGY2-C |
| 3 | Connolly | Laura | 3 | 8 | 8 | PGY3-E |
| 4 | Cook | Scott | 2 | 3 | 3 | PGY2-A |
| 5 | Gigon | Alaine | 2 | 7 | 7 | PGY2-D |
| 6 | Headid | Ronald (James) | 2 | 14 | 16 | PGY2-F |
| 7 | Hernandez | Christian | 2 | 6 | 6 | PGY3-D |
| 8 | Maher | Nicholas (Nick) | 2 | 8 | 8 | PGY2-B |
| 9 | Mayell | Cameron (Cam) | 3 | 9 | 9 | PGY3-C |
| 10 | Monsivais | Joshua (Josh) | 1 | 13 | 14 | PGY1-A |
| 11 | Petrie | William (Clay) | 3 | 11 | 14 | PGY3-B |
| 12 | Sawyer | Tessa | 1 | 11 | 15 | PGY1-B |
| 13 | Sloss | Meleighe (Meleigh) | 1 | 16 | 17 | PGY1-D |
| 14 | Thomas | Devin | 2 | 3 | 3 | PGY2-E |
| 15 | Travis | Colin | 1 | 8 | 8 | PGY1-E |
| 16 | Wilhelm | Clara | 1 | 16 | 22 | PGY1-C |
| 17 | You | Jae | 3 | 6 | 12 | PGY3-A |

### 2b. Faculty (13)

| # | Last Name | First Name | Files | Occurrences | Pseudonym |
|---|-----------|------------|-------|-------------|-----------|
| 1 | Bevis | Zach | 14 | 30 | Faculty-J |
| 2 | Chu | Jimmy | 10 | 17 | Faculty-G |
| 3 | Colgan | Bridget | 12 | 26 | Faculty-A |
| 4 | Dahl | Brian | 15 | 27 | Faculty-B |
| 5 | Kinkennon | Sarah | 14 | 27 | Faculty-I |
| 6 | LaBounty | Alex | 18 | 33 | Faculty-D |
| 7 | Lamoureux | Anne | 11 | 15 | **MISSING from replacements** |
| 8 | McGuire | Chris | 11 | 25 | Faculty-F |
| 9 | McRae | Zachery (Zach) | 12 | 22 | Faculty-K |
| 10 | Montgomery | Aaron | ~31 | ~79 | Excluded (developer + faculty dual role) |
| 11 | Napierala | Joseph (Joe) | 10 | 18 | Faculty-H |
| 12 | Tagawa | Chelsea | 18 | 51 | Faculty-C |
| 13 | Van Brunt | T. Blake | 10 | 19 | Faculty-E |

### 2c. Names NOT Found (From Prior Lists)

These 19 names appeared in earlier PII documentation but have **zero occurrences** in any tracked file on HEAD or in git history. They may be from a different academic year or were already fully scrubbed:

> Albers, Blanchard, Carpenter, Eaton, Gerber, Howerton, Keen, McClure, Moody, Phan, Simmons, Weiss, Bautista, Cannedy, Chamberlin, Czarnecki, Flint, McNamara, Shand

---

## 3. PERSEC-Critical Content

These 12 items combine real names with operationally sensitive military information. **Highest priority for removal.**

| # | File | Content Summary | Risk Category |
|---|------|-----------------|---------------|
| 1 | `.claude/Scratchpad/archive/session-111-db-xlsx-analysis.md:48` | `Bridget Colgan \| DEPLOYED Feb 21 - Jun 30` | **DEPLOYMENT DATES** |
| 2 | `.claude/Scratchpad/archive/session-111-db-xlsx-analysis.md:60` | `Colgan \| Feb 21 - Jun 30 \| DEPLOYED` | **DEPLOYMENT DATES** |
| 3 | `.claude/Scratchpad/archive/session-111-db-xlsx-analysis.md:58` | `Montgomery \| Mar 9-14 \| TDY/USAFP` | **TDY DATES** |
| 4 | `.claude/Scratchpad/archive/session-111-db-xlsx-analysis.md:62` | `McGuire \| Mar 6-14 \| Vacation/USAFP` | **TDY DATES** |
| 5 | `.claude/Scratchpad/archive/session-111-db-xlsx-analysis.md:64` | `Bevis \| Mar 9-14 \| USAFP/TDY` | **TDY DATES** |
| 6 | `.claude/Scratchpad/archive/session-111-db-xlsx-analysis.md:47-77` | Multiple `Name \| Date Range \| Vacation` entries | **LEAVE SCHEDULES** |
| 7 | `docs/TAMC_SCHEDULING_CONTEXT.md:126` | `Colgan, Bridget \| DEP (deployed)` | **DEPLOYMENT STATUS** |
| 8 | `backend/alembic/versions/20260114_half_day_tables.py:247` | `("%Colgan%", 0, 0, "GME"), # DEP` | **DEPLOYMENT STATUS** |
| 9 | `backend/alembic/versions/20260114_half_day_tables.py:252` | `("%Dahl%", 0, 0, "GME"), # OUT Dec-Jun` | **ABSENCE PERIOD** |
| 10 | `docs/TAMC_SCHEDULING_CONTEXT.md:158` | `Connolly, Laura \| Often Hilo (TDY)` | **TDY PATTERN** |
| 11 | `docs/scratchpad/block10-pre-regeneration-snapshot.md:49-68` | Call schedule with full names and dates | **DUTY SCHEDULES** |
| 12 | `frontend/src/features/synapse-monitor/constants.ts:12` | `name: "MAJ Montgomery"` | **MILITARY RANK** |

---

## 4. Files by Directory

### 4a. `.claude/` — Session Notes and Archives (35 files)

**`.claude/Scratchpad/` (3 active files)**
| File | Names Present |
|------|---------------|
| `session-103-db-alignment.md` | Tagawa |
| `session-104-half-day-model.md` | LaBounty, Tagawa |
| `session-106-color-scheme.md` | Lamoureux |

**`.claude/Scratchpad/archive/` (14 files)**
| File | Names Present | Notes |
|------|---------------|-------|
| `SESSION_075_CONTEXT.md` | Van Brunt, Dahl, Tagawa, McGuire, Kinkennon, Bevis, McRae, Colgan, Chu, Napierala, LaBounty | Full faculty roster |
| `session-095-seed-data.md` | All 17 residents | Full roster with PGY levels |
| `session-096-block-export-test.md` | Byrnes, Petrie, Headid, Maher, Monsivais, Sloss | Name format mismatches |
| `session-098-block10-v2.md` | Byrnes, Wilhelm, You | Secondary rotations |
| `session-099-completion.md` | Van Brunt, Lamoureux, Napierala | Adjunct status |
| `session-099-faculty-expansion.md` | All faculty | Call ranges |
| `session-101-backup-analysis.md` | Sloss, You | |
| `session-102-eod-handoff.md` | Wilhelm, Byrnes | Katie/Katherine mismatch |
| `session-107-font-colors-pii.md` | Lamoureux | HV visibility |
| `session-108-stealth-launch.md` | Connolly, Hernandez, Headid, Cook, Travis, Wilhelm, Byrnes | |
| `session-111-db-xlsx-analysis.md` | ALL faculty + call/leave/TDY dates | **PERSEC-CRITICAL** |
| `IG_AUDIT_SESSION_MCP_REFINEMENT.md` | Montgomery | Git author |
| `OPUS_REVIEW_PR497.md` | Montgomery | Git author + email |
| `ORCHESTRATOR_ADVISOR_NOTES.md` | Montgomery | User profile |

**`.claude/archive/` (6 files)**
| File | Names Present |
|------|---------------|
| `Missions/archive/DEBRIEF_20260109_063000.md` | Gigon, Mayell, Hernandez, Wilhelm |
| `agents/COORD_AAR.md` | Montgomery |
| `agents/DELEGATION_AUDITOR.md` | Montgomery |
| `agents/HISTORIAN.md` | Montgomery |
| `agents/MEDCOM.md` | Montgomery |
| `skills/historian/SKILL.md` | Montgomery |

**`.claude/dontreadme/` (7 files)**
| File | Names Present |
|------|---------------|
| `sessions/SESSION_2025-12-26_BLOCK_SCHEDULE_IMPORT.md` | Chu, Bevis, LaBounty |
| `sessions/SESSION_14_IDE_DEPLOYMENT.md` | Tagawa |
| `sessions/SESSION_078_HISTORIAN.md` | Montgomery |
| `reconnaissance/G2_RECON_REPORT.md` | Montgomery |
| Various OVERNIGHT_BURN session files (3) | Montgomery |

**`.claude/skills/` (1 file)**
| File | Names Present |
|------|---------------|
| `tamc-excel-scheduling/BLOCK_SCHEDULE_RULES.md` | Wilhelm, Byrnes, You |

### 4b. `backend/` — Source Code (14 files)

**Alembic Migrations (4 files — HARD BOUNDARY)**
| File | Names Present | Context |
|------|---------------|---------|
| `20260114_faculty_constraints.py` | Bevis, Kinkennon, LaBounty, McRae, Colgan, Chu, Montgomery, Dahl, McGuire, Tagawa | `%Name%` ILIKE patterns |
| `20260114_half_day_tables.py` | All 13 faculty | Clinic caps + DEP/OUT comments |
| `20260114_sm_constraints.py` | Tagawa | SM faculty |
| `20260129_link_activities_to_procedures.py` | Kinkennon, LaBounty, Tagawa | Procedure credentials |

**Application Code (4 files — comments only)**
| File | Names Present | Context |
|------|---------------|---------|
| `app/services/preload_service.py:26` | Petrie, Cataquiz | Comment: "FMIT Residents" |
| `app/services/tamc_color_scheme.py:189` | Lamoureux | Comment: "Visibility for Lamoureux - HV" |
| `app/services/block_assignment_expansion_service.py:664` | Montgomery | Comment: "APPROVED BY" |

**Scripts (2 files)**
| File | Names Present |
|------|---------------|
| `scripts/validate_rosetta_complete.py:44` | Connolly | Column name comment |
| `scripts/validate_xlsx_vs_rosetta.py` | 8 residents | Full names with PGY |

**Tests (2 files)**
| File | Names Present |
|------|---------------|
| `tests/scheduling/conftest.py` | Travis, Headid, Sloss, Monsivais, You, Wilhelm, Byrnes, Sawyer | Test fixture data |
| `tests/services/test_xml_to_xlsx_converter_diagnostics.py:327` | Bevis | Excel formula in test |

**Test Data Generator (1 file)**
| File | Names Present | Notes |
|------|---------------|-------|
| `generate_test_data.py` | Hernandez, Thomas | Generic surname lists (borderline) |

### 4c. `docs/` — Documentation (18 files)

**Core Reference**
| File | Names Present | Notes |
|------|---------------|-------|
| `TAMC_SCHEDULING_CONTEXT.md` | ALL 30 people | **Highest concentration file** — full roster, clinic caps, roles |

**Architecture Docs (5 files)**
| File | Names Present |
|------|---------------|
| `architecture/BLOCK10_CONSOLIDATED_REFERENCE.md` | All faculty with clinic caps |
| `architecture/BLOCK_SCHEDULE_PARSER.md` | Chu |
| `architecture/FACULTY_SCHEDULING_SPECIFICATION.md` | Kinkennon, LaBounty, Tagawa |
| `architecture/HALF_DAY_ASSIGNMENT_MODEL.md` | LaBounty |
| `architecture/bridges/CREEP_SPC_BRIDGE.md` | Montgomery |

**Scheduling Docs (3 files)**
| File | Names Present |
|------|---------------|
| `scheduling/CSV_BRIDGE_SPEC.md` | Connolly, Travis, Bevis, Headid, Sloss |
| `scheduling/README.md` | Travis, Headid, Sloss, Monsivais, Wilhelm, Byrnes, Sawyer |
| `scheduling/ROSETTA_PATTERNS.md` | Headid, Sloss, Monsivais, Wilhelm, Byrnes, You, Travis |

**Scratchpad Docs (3 files)**
| File | Names Present | Notes |
|------|---------------|-------|
| `scratchpad/block10-pre-regeneration-snapshot.md` | All 17 residents + faculty | **PERSEC-CRITICAL** — duty schedules |
| `scratchpad/session-143-faculty-clinic-cv-backfill.md` | McRae, LaBounty, Chu, Kinkennon, Dahl, McGuire, Bevis, Tagawa, Colgan | |
| `scratchpad/session-cpsat-phase2-20260128.md` | Chu, Lamoureux, Kinkennon, LaBounty, Tagawa | |

**Other Docs (6 files)**
| File | Names Present |
|------|---------------|
| `archived/reports/LOCAL_FILE_CLEANUP_REPORT.md` | 8 residents |
| `archived/sessions/session13/README.md` | Montgomery |
| `development/MERGE_ROADMAP.md` | Montgomery (first name only) |
| `development/SIDE_BY_SIDE_DEBUGGER.md` | Montgomery |
| `planning/PII_HISTORY_PURGE_PLAN.md` | All names (meta-reference) |
| `reports/GUI_WIRING_GAPS.md` | Montgomery |

### 4d. `frontend/` (2 files)

| File | Names Present | Context |
|------|---------------|---------|
| `src/features/synapse-monitor/constants.ts:12` | Montgomery | `"MAJ Montgomery"` with military rank |
| `src/types/api-generated-check.ts` | Chu, Bevis | OpenAPI spec examples |

### 4e. `scripts/` (5 files)

| File | Names Present |
|------|---------------|
| `csv_to_excel_direct.py` | Mayell, Petrie, Headid, Maher, Byrnes, Monsivais, Sloss, LaBounty, McRae, You |
| `csv_to_vba_format.py` | Mayell |
| `ops/learned_rules.py` | Petrie, Colgan, Hernandez |
| `pii-scan.sh` | All 30 names in KNOWN_NAMES variable |
| `seed_people.py` | Thomas (borderline) |

---

## 5. Git History Contamination

### 5a. Commits by Name (Top 20)

| Name | Commits | In Commit Messages? | Oldest Commit | Latest Commit |
|------|---------|---------------------|---------------|---------------|
| Tagawa | 32 | Yes (7) | `c34b29cc` 2025-12-16 | `e36c5509` 2026-02-21 |
| LaBounty | 27 | Yes (4) | 2025-12-21 | 2026-02-21 |
| Bevis | 26 | Yes (5) | 2025-12-21 | 2026-02-21 |
| Kinkennon | 25 | Yes (6) | 2025-12-21 | 2026-02-21 |
| Colgan | 23 | Yes (2) | 2025-12-21 | 2026-02-21 |
| Hernandez | 20 | Yes (1) | 2025-12-21 | 2026-02-21 |
| McGuire | 19 | Yes (2) | 2025-12-21 | 2026-02-21 |
| Dahl | 18 | Yes (1) | 2025-12-21 | 2026-02-21 |
| McRae | 18 | No | 2025-12-21 | 2026-02-21 |
| Petrie | 18 | No | 2025-12-21 | 2026-02-21 |
| Wilhelm | 17 | No | 2025-12-21 | 2026-02-21 |
| Sawyer | 17 | Yes (1) | 2025-12-21 | 2026-02-21 |
| Monsivais | 17 | Yes (1) | 2025-12-21 | 2026-02-21 |
| Travis | 17 | Yes (1) | 2025-12-21 | 2026-02-21 |
| Cataquiz | 16 | No | 2025-12-21 | 2026-02-21 |
| Headid | 16 | No | 2025-12-21 | 2026-02-21 |
| Sloss | 16 | No | 2025-12-21 | 2026-02-21 |
| Byrnes | 15 | No | 2025-12-21 | 2026-02-21 |
| Connolly | 15 | No | 2025-12-21 | 2026-02-21 |
| Gigon | 15 | No | 2025-12-21 | 2026-02-21 |

### 5b. Ambiguous Names (High False-Positive Rate)

| Name | Raw Hits | True PII Commits | False Positive Source |
|------|----------|------------------|----------------------|
| You | 348 | ~13 | English pronoun |
| Chu | 81 | ~20 | "Chunk", "Church", etc. |
| Cook | 45 | ~15 | Common English word |
| Montgomery | 48 | ~20 | Developer (dual role: git author + faculty) |
| Thomas | 20 | ~15 | Common surname in generic test data |

### 5c. Commit Messages with Real Names

At least **25 commit messages** contain real surnames. Notable examples:

| Commit | Message Excerpt | Names |
|--------|-----------------|-------|
| `cb4953ee` | "Update people seeder with real Airtable data" | Multiple residents |
| `d88a7952` | Explicitly lists faculty | Tagawa, Chu, Bevis, LaBounty, Kinkennon, Colgan |
| Various | Phase 7 calibration, faculty wiring | Bevis, Kinkennon, LaBounty, Chu |

**Note:** Commit messages can only be cleaned via history rewrite (`git-filter-repo`).

### 5d. Tags

One tag exists: `pre-sterile-reset-20260101` (lightweight, no annotation). No PII in tag metadata.

---

## 6. Replacements File Status (`/tmp/pii-replacements.txt`)

### Current Coverage

- **Total active rules:** 79 (across 3 tiers: "Last, First" / "First Last" / last-name-only)
- **People covered:** 28 of 30
- **Missing:** Lamoureux (Anne), Montgomery (intentionally excluded)

### Replacement Tiers

| Tier | Pattern | Example | Rules |
|------|---------|---------|-------|
| 1 | `literal:Last, First==>Pseudonym-Last, Pseudonym-First` | `literal:Colgan, Bridget==>Faculty-A-Last, Faculty-A-First` | 28 |
| 2 | `literal:First Last==>Pseudonym` | `literal:Bridget Colgan==>Faculty-A` | 28 |
| 3 | `literal:LastName==>Pseudonym-Last` | `literal:Colgan==>Faculty-A-Last` | 23 |

### Skipped Last-Name-Only Rules (Common Words)

These 5 last names are intentionally skipped at Tier 3 to avoid false-positive replacements:

| Name | Why Skipped |
|------|-------------|
| Travis | Common first name / place name |
| Cook | Common English word |
| Thomas | Common first name |
| You | English pronoun |
| Chu | Substring in common words |

These are still replaced at Tier 1 (full "Last, First") and Tier 2 (full "First Last").

### Required Additions

```
literal:Lamoureux, Anne==>Faculty-L-Last, Faculty-L-First
literal:Anne Lamoureux==>Faculty-L
literal:Lamoureux==>Faculty-L-Last
```

---

## 7. Hard Boundaries

### Alembic Migrations (Cannot Be Edited)

Per `CLAUDE.md` project rules: **"Never edit existing migrations — create new ones to fix issues."**

These 4 migration files contain real names in SQL ILIKE patterns and comments. They **cannot be modified** on HEAD without creating new migrations. `git-filter-repo` will rewrite them in history, but the HEAD versions will retain names unless superseded by a new migration.

| Migration | Names | Context |
|-----------|-------|---------|
| `20260114_faculty_constraints.py` | Bevis, Kinkennon, LaBounty, McRae, Colgan, Chu, Montgomery, Dahl, McGuire, Tagawa | `%Name%` ILIKE constraint patterns |
| `20260114_half_day_tables.py` | All 13 faculty | Clinic caps with DEP/OUT comments |
| `20260114_sm_constraints.py` | Tagawa | SM faculty constraint |
| `20260129_link_activities_to_procedures.py` | Kinkennon, LaBounty, Tagawa | Procedure credential links |

**Options (to be decided during remediation):**
1. Accept names in migrations (data migration necessary for the app to function)
2. Create new migration that replaces ILIKE patterns with person IDs (schema change)
3. Create new migration that just rewrites comments (minimal, but still editing migrations)

---

## 8. Confirmed False Positives (Excluded from Counts)

| Match | Appears In | Why Not PII |
|-------|-----------|-------------|
| "Herfindahl" | 4 files (workload optimizer, ecology docs) | Economist Orris Herfindahl, not "Dahl" |
| "Montgomery, D.C." | `backend/app/resilience/spc/README.md` | Academic citation (Douglas C. Montgomery, SQC textbook) |
| "toBeVisible" | ~59 test files | Playwright API, not "Bevis" |
| "Phan" (all hits) | 10 commits | All are "Phantom" substring |
| "Keen" (all hits) | 1 commit | "Keen Observations" in D&D gaming doc |
| Test data surnames | `generate_test_data.py`, `load-tests/` | Generic surnames (Hernandez, Thomas) that coincidentally match real people |
| `travisvn` | `docs/planning/ANTHROPIC_SKILLS_EXPLORATION.md` | GitHub username, not Colin Travis |

---

## 9. Prior Remediation Attempts

| Incident | Date | What Happened | Result |
|----------|------|---------------|--------|
| #001 | 2025-12-21 | PII in seed scripts/docstrings. History rewrite + force-push. | Diverged histories. Required `--allow-unrelated-histories` merge, creating duplicate SHAs. |
| #002 | 2026-02-05 | 28 people found across ~29 files. Scrubbed over 4 commits. | Partial success. 6 faculty names remained in migrations (Hard Boundary declared). |
| #003 | 2026-02-21 | PII wipe tool corrupted origin/main — all `#` replaced with `***REMOVED***` across 4,629 files. | **Catastrophic.** Restored from bundle backup. Plan never completed. |

**Current state:** All three incidents documented in `docs/security/PII_AUDIT_LOG.md`. The purge plan at `docs/planning/PII_HISTORY_PURGE_PLAN.md` remains unexecuted.

---

## 10. Existing Safeguards

| Safeguard | Status | Notes |
|-----------|--------|-------|
| Pre-commit hook (`scripts/pii-scan.sh`) | Active | Blocks commits with known names |
| GitHub Actions PII scan | Active | PR, push, weekly, manual triggers |
| `.gitignore` for data files | Active | `docs/data/*.json`, `*.dump`, `.env*` |
| Replacements file | Exists but incomplete | Missing Lamoureux; covers 28/30 people |
| `git-filter-repo` | Installed | Available for history rewrite |

---

## 11. Remediation Checklist (Not Yet Executed)

- [ ] Add Lamoureux to `/tmp/pii-replacements.txt` (3 rules)
- [ ] Delete `.claude/Scratchpad/archive/` session files (14 files)
- [ ] Delete `.claude/archive/Missions/archive/DEBRIEF_20260109_063000.md`
- [ ] Scrub ~32 remaining HEAD files (replace names with pseudonyms)
- [ ] Decide on migration strategy (Hard Boundary — accept, rewrite, or supersede)
- [ ] Commit HEAD cleanup
- [ ] `git clone --mirror` + `git filter-repo --replace-text` on fresh clone
- [ ] Re-add remotes, force-push to origin and mini
- [ ] Re-sync local repo (`git fetch origin && git reset --hard origin/main`)
- [ ] Verify: `git grep` and `git log -S` return no PII
- [ ] Verify: all tests pass post-rewrite
- [ ] Update `PII_AUDIT_LOG.md` with Incident #004

---

## Appendix A: Montgomery Dual-Role Analysis

Aaron Montgomery is both the **repository owner/developer** and a **faculty member in the scheduling data**. This creates ambiguity:

| Context | PII? | Action |
|---------|------|--------|
| Git author name/email | No | Normal git metadata |
| `APPROVED BY: Dr. Montgomery` in code comments | Borderline | Replace with role-based reference |
| `"MAJ Montgomery"` in frontend constants | **Yes** | Replace — combines name with military rank |
| Faculty scheduling data (clinic caps, call counts) | **Yes** | Replace with Faculty pseudonym |
| References as "Dr. Montgomery" in agent specs | Borderline | Low priority — developer identity |

**Recommendation:** Replace scheduling/military references. Leave git author metadata and developer identity references.

---

## Appendix B: PERSEC Risk Assessment

| Risk Level | Category | File Count | Examples |
|------------|----------|-----------|----------|
| **CRITICAL** | Deployment dates + names | 3 | Colgan DEP dates, USAFP TDY dates |
| **HIGH** | Leave/vacation schedules + names | 2 | Faculty vacation dates, absence periods |
| **HIGH** | Duty schedules + names | 1 | Block 10 call assignments with dates |
| **HIGH** | Military rank + names | 1 | "MAJ Montgomery" |
| **MEDIUM** | Full roster with PGY levels | 5 | TAMC_SCHEDULING_CONTEXT.md, seed data |
| **MEDIUM** | Faculty clinic assignments | 8 | Architecture docs, scratchpad |
| **LOW** | Name-only references | ~30 | Session notes, code comments |

**CRITICAL and HIGH items should be addressed first**, regardless of the broader purge timeline.
