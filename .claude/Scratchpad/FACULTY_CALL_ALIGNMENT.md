# Session 068-069 - Admin UI Improvements

**Branch:** `main` | **Date:** 2026-01-07

---

## COMPLETED THIS SESSION ✅

### 1. Real Personnel Data Restored
- Restored backup `backups/data/residency_scheduler_20260101_104047.sql.gz`
- Used test container (pgvector/pgvector:pg15) → ran migrations → swapped to dev
- **29 people** with real names now in DB (Aaron Montgomery, Zach Bevis, etc.)
- **60 rotation templates** (C-AM, FMIT, NF-*, PR-*, etc.)
- Alembic at: `20260105_add_import_staged_absences`

### 2. Immaculate Backup Created
**Name:** `immaculate_real_personnel_20260107` (2.5G)
```bash
./scripts/stack-backup.sh restore immaculate_real_personnel_20260107
```

### 3. RAG Updated
- Personnel roster ingested (29 names)
- Rotation templates ingested (60 templates)
- Backup reference added

### 4. People Toggle Bug Fixed ✅
**File:** `frontend/src/hooks/usePeople.ts:146`
- Changed `params.set('role', ...)` → `params.set('type', ...)`
- Backend expects `?type=resident`, frontend was sending `?role=resident`

---

## IN PROGRESS - Admin UI Plan

**Plan file:** `.claude/plans/merry-hatching-torvalds.md`

### Execution Order (remaining):
1. ~~Fix people toggle~~ ✅ DONE
2. Auto-save: queued edits + backup endpoint
3. Week-by-week pattern editing (add week_number to weekly_patterns)
4. Half-block rotation support (add block_duration to rotation_templates)
5. Admin people bulk edit page
6. Procedure credentialing matrix
7. Rename pages (templates→activities/rotations)
8. Navigation cleanup

### Key Domain Concepts
```
Block = 28 days (4 weeks) = 56 half-days
Rotation = Template assigned to a Block
Half-day activity = AM or PM slot within a week (14 slots/week)
Week-by-week = Some rotations vary pattern each week (W1≠W2)
Half-block = 14-day rotation (electives, splits)
```

### Existing Implementation Found
- `WeeklyGridEditor.tsx` - 7×2 grid editor exists
- `weekly_pattern.py` - Model exists
- `useWeeklyPattern.ts` - Hooks exist
- Docs: `docs/planning/ROTATION_TEMPLATE_GUI_PLAN.md`

### New Features Needed
1. **Week tabs** - Week 1/2/3/4 selector in grid editor
2. **Half-block** - Duration selector (full/half/quarter)
3. **Bulk operations** - Backup before bulk, copy patterns

---

## Key Files Reference

| Purpose | Path |
|---------|------|
| People hook (FIXED) | `frontend/src/hooks/usePeople.ts` |
| Weekly grid editor | `frontend/src/components/WeeklyGridEditor.tsx` |
| Weekly pattern model | `backend/app/models/weekly_pattern.py` |
| Rotation template model | `backend/app/models/rotation_template.py` |
| Admin templates page | `frontend/src/app/admin/templates/page.tsx` |
| Plan file | `.claude/plans/merry-hatching-torvalds.md` |

---

## Test Credentials
- Username: `admin`
- Password: `admin123`
