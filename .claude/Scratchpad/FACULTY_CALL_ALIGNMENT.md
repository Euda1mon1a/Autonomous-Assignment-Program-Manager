# Session 075 Handoff

**Branch:** `session/075-continued-work` | **Date:** 2026-01-08
**Base:** `main @ 97356688` (PR #664 merged)

---

## SESSIONS 067-074 COMPLETE ✅

### PRs Merged to Main
- **PR #662** - Sessions 067-072: Admin UI, Faculty Call, Schedule Views
- **PR #663** - Rotation templates documentation
- **PR #664** - Greedy solver call generation + full year import + PII sanitization

### Key Accomplishments
1. **Greedy solver generates faculty call** - 20 overnight call assignments (Sun-Thu)
2. **221 block assignments imported** - Full AY 2025 (17 residents × 13 blocks)
3. **24 new rotation templates** - 7 in session 073, 17 in session 074
4. **Import script** - `backend/scripts/import_block_assignments.py`
5. **Admin UI** - People bulk edit, Credentials matrix, Rotations auto-save
6. **Schedule Views** - Block Annual View, Block Week View, Daily Manifest V2
7. **PII Sanitized** - Removed from PR branch history + deleted files from main HEAD

### Backup Location
```
~/backups/scheduler-20260108-session074/
├── MANIFEST.md
├── repo.bundle (21MB)
├── db.sql.gz (772KB)
├── rag_documents.sql (1.2MB)
├── block_assignments.sql.gz (10KB)
└── rotation_templates.sql.gz (4.6KB)
```

---

## CRITICAL TODO (Human Required)

**PERSEC: Remove PII from git history**
- Files deleted from HEAD but still in main branch history
- Affected: BLOCK_10_SUMMARY.md, AIRTABLE_EXPORT_SUMMARY.md, SESSION_2025-12-26_COLORS_AND_SPLITS.md, block10_extracted_26dec2025.json
- Requires: `git filter-repo` + force push to main
- Impact: All collaborators must re-clone after
- Tracked in: `docs/TODO_INVENTORY.md` (Critical section)

---

## Database State

```
block_assignments: 221 rows (AY 2025, 17 residents × 13 blocks)
rotation_templates: 84 total
call_assignments: 365 (full academic year)
```

**Academic Year Note:** Data uses `academic_year=2025` which represents AY 2025-2026 (July 2025 - June 2026). Frontend `getCurrentAcademicYear()` correctly returns 2025 for dates Jan-June 2026.

---

## GUI Status

- **Block Annual View** (`/schedule`): Shows 221 assignments across 13 blocks
- **Block assignments visible**: Verified via API and GUI
- **Import script working**: CLI tool for future bulk imports

---

## Next Steps (Potential)

1. GUI import feature for block assignments (lessons in `docs/planning/GUI_IMPORT_LESSONS.md`)
2. Solver constraint improvements (template max_residents, PGY requirements)
3. rotation_halfday_requirements table population
4. CP-SAT solver debugging (currently generates violations)

---

## Test Credentials
- Username: `admin`
- Password: `admin123`
