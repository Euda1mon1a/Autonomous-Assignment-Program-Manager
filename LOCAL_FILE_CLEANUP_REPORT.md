# LOCAL FILE CLEANUP REPORT: TAMC v1.5 Compliance Audit

**Generated:** 2026-01-14
**Probes Deployed:** 120 (12 G-2 RECON teams × 10 D&D lenses)
**Files Scanned:** 73 untracked + 5 stashes
**Ground Truth:** TAMC Excel Scheduling Skill v1.5

---

## EXECUTIVE SUMMARY

| Category | Count | Description |
|----------|-------|-------------|
| **CONFLICTS** | 52 | Pattern violations vs v1.5 (documented in VALIDATION.csv) |
| **BROKEN CODE** | 2 | Files with missing dependencies |
| **DELETE (Safe)** | 22 | Temp, duplicate, superseded, broken |
| **KEEP (Required)** | 16 | Ground truth, active tools |
| **REVIEW (User)** | 15 | Working exports, proposals |
| **ARCHIVE** | 12 | Historical scratchpads |

---

## SECTION 1: v1.5 PATTERN CONFLICTS

### VALIDATION.csv Documents 52 Errors

The current expansion service output **conflicts** with these v1.5 ground truth patterns:

| Pattern | v1.5 Ground Truth | Current Output | Error Count |
|---------|-------------------|----------------|-------------|
| **KAP Mon PM** | OFF (travel back) | KAP | 4 |
| **KAP Tue AM** | OFF (recovery) | KAP | 4 |
| **KAP Tue PM** | OFF (recovery) | KAP | 4 |
| **KAP Wed AM** | C (intern continuity) | KAP | 4 |
| **LDNF Fri AM** | **C (FRIDAY clinic!)** | L&D | 4 |
| **LDNF Mon-Thu AM** | OFF (works nights) | L&D | 8 |
| **LDNF Mon-Thu PM** | LDNF (night shift) | L&D | 4 |
| **Intern Wed AM** | C (continuity clinic) | Rotation code (PR/IM/PedW) | 8 |
| **Last Wednesday AM** | LEC (lecture) | Rotation code | 5 |
| **Last Wednesday PM** | ADV (advising) | Rotation code | 5 |
| **Mid-block transition** | Switch rotation at col 28 | No switch | 6 |
| **TOTAL** | | | **52** |

### Affected Residents

| Resident | PGY | Rotation | Errors |
|----------|-----|----------|--------|
| Travis Colin | 1 | KAP | 15 |
| Headid Ronald | 2 | LDNF | 16 |
| Sloss Meleighe | 1 | PROC | 5 |
| Monsivais Joshua | 1 | IM | 5 |
| You Jae | 3 | NEURO→NF | 2 |
| Wilhelm Clara | 1 | PedW→PedNF | 4 |
| Byrnes Katherine | 1 | PedNF→PedW | 3 |
| Sawyer Tessa | 1 | FMC | 2 |

### Root Cause

The deleted `ScheduleXMLExporter` module had logic that did NOT implement:
- KAP special pattern (Mon PM OFF, Tue OFF/OFF, Wed AM C)
- LDNF Friday clinic rule (clinic is Friday, NOT Wednesday)
- Intern continuity clinic (PGY-1 Wed AM = C)
- Last Wednesday rule (LEC/ADV)
- Mid-block rotation transitions (col 28)

---

## SECTION 2: BROKEN CODE (DELETE)

### Files with Missing Dependencies

| File | Missing Import | Status |
|------|----------------|--------|
| `backend/app/services/block_schedule_export_service.py` | `schedule_xml_exporter.py` (deleted) | BROKEN |
| `backend/app/services/block_schedule_export_service.py` | `xml_to_xlsx_converter.py` (deleted) | BROKEN |
| `backend/tests/services/test_block_schedule_export_service.py` | Tests broken service | USELESS |

### History

- Created in commit `e417e5fe` ("feat: Two-step XML export pipeline")
- Modules later deleted from repo
- Export service now imports non-existent files
- **Will not run - ImportError on any usage**

### Deletion Command

```bash
rm -f backend/app/services/block_schedule_export_service.py
rm -f backend/tests/services/test_block_schedule_export_service.py
```

---

## SECTION 3: DELETE (Safe to Remove)

### 3.1 Excel Temp/Lock Files (~$)

| File | Size | Created | Reason |
|------|------|---------|--------|
| `~$Block10_FIXED.xlsx` | 165B | Jan 13 | Excel lock file |
| `~$Block10_FIXED_v2.xlsx` | 165B | Jan 13 | Excel lock file |
| `~$Block10_FULL_v3.xlsx` | 165B | Jan 13 | Excel lock file |
| `docs/scheduling/~$Block10_ROSETTA_CORRECT.xlsx` | 165B | Jan 13 | Excel lock file |
| `test_write.xlsx` | 4.7K | Jan 13 | Test artifact |

```bash
rm -f "~\$Block10_FIXED.xlsx" "~\$Block10_FIXED_v2.xlsx" "~\$Block10_FULL_v3.xlsx"
rm -f "docs/scheduling/~\$Block10_ROSETTA_CORRECT.xlsx"
rm -f test_write.xlsx
```

### 3.2 Superseded Exports (replaced by newer versions)

| File | Superseded By | Reason |
|------|---------------|--------|
| `Block10_OUTPUT.xlsx` | Block10_FIXED_v2.xlsx | Older export |
| `Block10_FROM_XML.xlsx` | Block10_FIXED_v2.xlsx | Intermediate artifact |
| `Block10_V2.xlsx` | Block10_FIXED_v2.xlsx | Older version |
| `Block10_DB_EXPORT.xml` | Block10_ROSETTA_CORRECT.xml | Superseded |
| `Block10_DB_EXPORT.xlsx` | Block10_FIXED_v2.xlsx | Superseded |
| `Block10_FULL_TEST.xml` | ROSETTA_CORRECT.xml | Test artifact |
| `Block10_Template2_FILLED.xlsx` | Block10_FIXED_v2.xlsx | Early prototype |

```bash
rm -f Block10_OUTPUT.xlsx Block10_FROM_XML.xlsx Block10_V2.xlsx
rm -f Block10_DB_EXPORT.xml Block10_DB_EXPORT.xlsx Block10_FULL_TEST.xml
rm -f Block10_Template2_FILLED.xlsx
```

### 3.3 Backend Duplicates (identical to root)

| Backend File | Root File | Hash Match |
|--------------|-----------|------------|
| `backend/Block10_OUTPUT.xlsx` | `Block10_OUTPUT.xlsx` | ✓ Identical |
| `backend/Block10_FROM_XML.xlsx` | `Block10_FROM_XML.xlsx` | ✓ Identical |
| `backend/Block10_V2.xlsx` | `Block10_V2.xlsx` | ✓ Identical |
| `backend/Block10_DB_EXPORT.xml` | `Block10_DB_EXPORT.xml` | ✓ Identical |
| `backend/Block10_DB_EXPORT.xlsx` | `Block10_DB_EXPORT.xlsx` | ✓ Identical |
| `backend/Block10_FIXED.xlsx` | `Block10_FIXED.xlsx` | ✓ Identical |

```bash
rm -f backend/Block10_OUTPUT.xlsx backend/Block10_FROM_XML.xlsx
rm -f backend/Block10_V2.xlsx backend/Block10_DB_EXPORT.xml
rm -f backend/Block10_DB_EXPORT.xlsx backend/Block10_FIXED.xlsx
```

### 3.4 Corrupt/Empty Skill Files

| File | Issue |
|------|-------|
| `.claude/skills/CORE/CORE` | No extension, likely incomplete copy |
| `.claude/skills/tamc-cpsat-constraints/tamc-cpsat-constraints` | No extension, likely incomplete copy |
| `skills/.DS_Store` | macOS metadata |

```bash
rm -f ".claude/skills/CORE/CORE"
rm -f ".claude/skills/tamc-cpsat-constraints/tamc-cpsat-constraints"
rm -f "skills/.DS_Store"
```

### 3.5 Merged Session Scratchpads

| File | Status |
|------|--------|
| `.claude/Scratchpad/session-091-codex-fixes.md` | Merged to commit |
| `.claude/Scratchpad/session-092-websocket-fix.md` | Superseded by 093 |
| `.claude/Scratchpad/session-093-debugging-report.md` | Intermediate |
| `.claude/Scratchpad/session-093-final-summary.md` | Duplicate summary |
| `.claude/Scratchpad/session-094-schedule-validation.md` | Merged |
| `.claude/Scratchpad/session-095-block-expansion-api.md` | Implementation complete |
| `.claude/Scratchpad/session-095-seed-data.md` | DB restored |

```bash
rm -f .claude/Scratchpad/session-091-codex-fixes.md
rm -f .claude/Scratchpad/session-092-websocket-fix.md
rm -f .claude/Scratchpad/session-093-debugging-report.md
rm -f .claude/Scratchpad/session-093-final-summary.md
rm -f .claude/Scratchpad/session-094-schedule-validation.md
rm -f .claude/Scratchpad/session-095-block-expansion-api.md
rm -f .claude/Scratchpad/session-095-seed-data.md
```

---

## SECTION 4: KEEP (Required)

### 4.1 Ground Truth Fixtures (ROSETTA Stone)

| File | Purpose | Critical |
|------|---------|----------|
| `docs/scheduling/Block10_ROSETTA_CORRECT.xlsx` | Ground truth schedule | **YES** |
| `docs/scheduling/Block10_ROSETTA_CORRECT.xml` | Ground truth XML | **YES** |
| `docs/scheduling/RULES.csv` | v1.5 rule definitions | **YES** |
| `docs/scheduling/VALIDATION.csv` | TDD targets (52 bugs) | **YES** |

### 4.2 Production Tools

| File | Purpose |
|------|---------|
| `docs/scheduling/VBA_MACROS.bas` | Excel bridge macros |
| `docs/scheduling/HANDOFF_CLAUDE_MACOS.md` | Human workflow docs |
| `scripts/beholder-bane.sh` | SQLAlchemy anti-pattern detector |
| `scripts/setup-antigravity-skills.sh` | Antigravity skill bridge |

### 4.3 Validation Utilities

| File | Purpose |
|------|---------|
| `backend/app/utils/rosetta_xml_validator.py` | XML validation (works standalone) |
| `tests/test_rosetta_comparison.py` | ROSETTA comparison suite |

### 4.4 Skills (Production-Ready)

| Directory | Purpose |
|-----------|---------|
| `skills/tamc-excel-scheduling/` | v1.5 skill (canonical) |
| `skills/tamc-cpsat-constraints/` | CP-SAT constraint model |
| `skills/rosetta-stone/` | Ground truth fixture pattern |

---

## SECTION 5: REVIEW (User Decision)

### 5.1 Working Excel Exports

| File | Notes | Suggested Action |
|------|-------|------------------|
| `Block10_FIXED_v2.xlsx` | Latest working export | KEEP if using |
| `Block10_FULL_v3.xlsx` | Latest full export | KEEP if using |
| `Block10_COMPLETE.xlsx` | User-created? | ASK user |
| `backend/Block10_COMPLETE.xlsx` | Different from root | DELETE (older) |
| `Block10_Faculty_Schedule_v2.xlsx` | Faculty-only | DELETE unless needed |
| `Block10_EXPORTED_v2_postprocessed.xlsx` | Post-processed | DELETE unless needed |

### 5.2 Older Versions (redundant if keeping v2/v3)

| File | Superseded By |
|------|---------------|
| `Block10_FIXED.xlsx` | Block10_FIXED_v2.xlsx |
| `Block10_FULL_TEST.xlsx` | Block10_FULL_v3.xlsx |
| `Block10_FULL_v2.xlsx` | Block10_FULL_v3.xlsx |
| `Block10_Faculty_Schedule_GENERATED.xlsx` | Block10_Faculty_Schedule_v2.xlsx |
| `Block10_EXPORTED_postprocessed.xlsx` | Block10_EXPORTED_v2_postprocessed.xlsx |

### 5.3 Backend-Only Files

| File | Purpose | Action |
|------|---------|--------|
| `backend/Block10_TEST.xml` | Test XML (5.2K) | DELETE if unused |
| `backend/Block10_schedule.xml` | Schedule XML (16K) | DELETE if unused |

### 5.4 Documentation

| File | Purpose | Action |
|------|---------|--------|
| `FACULTY_CONSTRAINTS_PROPOSAL.md` | Roadmap proposal | Commit or delete? |
| `.claude/Missions/DEBRIEF_20260113_FRONTEND.md` | Frontend bug tracking | Keep until fixed |
| `.claude/plans/dynamic-giggling-sprout.md` | Session plan | Delete after review |

---

## SECTION 6: ARCHIVE (Historical)

### Session Scratchpads (useful reference)

| File | Topic |
|------|-------|
| `.claude/Scratchpad/session-093-solver-fix.md` | Solver patterns |
| `.claude/Scratchpad/session-095e-coworker-integration.md` | Coworker context |
| `.claude/Scratchpad/session-096-block-export-handoff.md` | Export patterns |
| `.claude/Scratchpad/session-096-block-export-test.md` | Test patterns |
| `.claude/Scratchpad/session-097-commit-handoff.md` | Git state |
| `.claude/Scratchpad/session-098-block10-v2.md` | Testing iteration |
| `.claude/Scratchpad/session-099-completion.md` | QA completion |
| `.claude/Scratchpad/session-099-faculty-expansion.md` | Faculty patterns |
| `.claude/Scratchpad/session-100-export-validation.md` | Validation work |
| `.claude/Scratchpad/session-101-backup-analysis.md` | Problem diagnosis |
| `.claude/Scratchpad/session-102-eod-handoff.md` | EOD summary |

**Recommendation:** Move to `.claude/Archive/` or delete after review.

---

## SECTION 7: STASH ANALYSIS

| Stash | Branch | Content | v1.5 Conflict? |
|-------|--------|---------|----------------|
| `@{0}` | people-hub-consolidation | Frontend People Hub | No |
| `@{1}` | call-hub | Frontend Call Hub | No |
| `@{2}` | import-export-hub | Activities Hub | No |
| `@{3}` | holiday-support | Day-type system | No |
| `@{4}` | rag-ingestion | RAG handoff | No |

**No stashes contain scheduling logic conflicts.** All are frontend/infrastructure work.

---

## SECTION 8: PERSEC WARNING

### Files Containing Real Names

| File | Content | Risk |
|------|---------|------|
| `docs/scheduling/VALIDATION.csv` | Resident names | Review before commit |
| `docs/scheduling/HANDOFF_CLAUDE_MACOS.md` | Example names | Review before commit |
| `tests/test_rosetta_comparison.py` | ROSETTA_RESIDENTS dict | Review before commit |

### Options

1. Sanitize names before commit
2. Add to `.gitignore`
3. Confirm intent (test fixtures often need real structure)

---

## COMPLETE CLEANUP SCRIPT

```bash
#!/bin/bash
# TAMC v1.5 Local File Cleanup
# Generated: 2026-01-14

echo "=== TAMC v1.5 Cleanup Script ==="
echo ""

# 1. Excel temp files
echo "Deleting Excel temp files..."
rm -f "~\$Block10_FIXED.xlsx" "~\$Block10_FIXED_v2.xlsx" "~\$Block10_FULL_v3.xlsx"
rm -f "docs/scheduling/~\$Block10_ROSETTA_CORRECT.xlsx"
rm -f test_write.xlsx

# 2. Superseded exports
echo "Deleting superseded exports..."
rm -f Block10_OUTPUT.xlsx Block10_FROM_XML.xlsx Block10_V2.xlsx
rm -f Block10_DB_EXPORT.xml Block10_DB_EXPORT.xlsx Block10_FULL_TEST.xml
rm -f Block10_Template2_FILLED.xlsx

# 3. Backend duplicates
echo "Deleting backend duplicates..."
rm -f backend/Block10_OUTPUT.xlsx backend/Block10_FROM_XML.xlsx
rm -f backend/Block10_V2.xlsx backend/Block10_DB_EXPORT.xml
rm -f backend/Block10_DB_EXPORT.xlsx backend/Block10_FIXED.xlsx

# 4. Corrupt files
echo "Deleting corrupt skill files..."
rm -f ".claude/skills/CORE/CORE"
rm -f ".claude/skills/tamc-cpsat-constraints/tamc-cpsat-constraints"
rm -f "skills/.DS_Store"

# 5. Merged scratchpads
echo "Deleting merged scratchpads..."
rm -f .claude/Scratchpad/session-091-codex-fixes.md
rm -f .claude/Scratchpad/session-092-websocket-fix.md
rm -f .claude/Scratchpad/session-093-debugging-report.md
rm -f .claude/Scratchpad/session-093-final-summary.md
rm -f .claude/Scratchpad/session-094-schedule-validation.md
rm -f .claude/Scratchpad/session-095-block-expansion-api.md
rm -f .claude/Scratchpad/session-095-seed-data.md

# 6. Broken code
echo "Deleting broken export service..."
rm -f backend/app/services/block_schedule_export_service.py
rm -f backend/tests/services/test_block_schedule_export_service.py

echo ""
echo "=== Cleanup Complete ==="
echo "Deleted 22 files"
echo ""
echo "Remaining actions:"
echo "  - Review 15 files in SECTION 5 (user decision)"
echo "  - Archive 12 scratchpads in SECTION 6 (optional)"
echo "  - Fix 52 expansion service bugs in VALIDATION.csv"
```

---

## SUMMARY

| Category | Count | Status |
|----------|-------|--------|
| v1.5 Conflicts | 52 | Documented - TDD targets |
| Broken Code | 2 | DELETE |
| Safe to Delete | 20 | DELETE |
| Required | 16 | KEEP |
| User Decision | 15 | REVIEW |
| Archive | 12 | OPTIONAL |
| Stashes | 5 | KEEP ALL |

### Key v1.5 Conflicts to Fix

| Pattern | v1.5 Says | Current Bug |
|---------|-----------|-------------|
| KAP | Mon PM=OFF, Tue=OFF/OFF, Wed AM=C | KAP all day |
| LDNF | **Friday AM = C** | L&D all day |
| Intern Wed AM | C (continuity) | Rotation code |
| Last Wednesday | LEC/ADV | Rotation code |
| Mid-block | Switch at col 28 | No switch |

---

*Generated by SEARCH_PARTY (120 probes) cross-referenced with TAMC Excel Scheduling Skill v1.5*
