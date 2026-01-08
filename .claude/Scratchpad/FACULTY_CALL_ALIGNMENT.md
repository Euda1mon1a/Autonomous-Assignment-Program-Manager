# Session 068-070 - Admin UI Improvements

**Branch:** `main` | **Date:** 2026-01-07

---

## COMPLETED THIS SESSION ✅

### 1. Real Personnel Data Restored (Session 068-069)
- Restored backup `backups/data/residency_scheduler_20260101_104047.sql.gz`
- Used test container (pgvector/pgvector:pg15) → ran migrations → swapped to dev
- **29 people** with real names now in DB (Aaron Montgomery, Zach Bevis, etc.)
- **60 rotation templates** (C-AM, FMIT, NF-*, PR-*, etc.)
- Alembic at: `20260105_add_import_staged_absences`

### 2. Immaculate Backup Created (Session 068-069)
**Name:** `immaculate_real_personnel_20260107` (2.5G)
```bash
./scripts/stack-backup.sh restore immaculate_real_personnel_20260107
```

### 3. RAG Updated (Session 068-069)
- Personnel roster ingested (29 names)
- Rotation templates ingested (60 templates)
- Backup reference added

### 4. People Toggle Bug Fixed ✅ (Session 068-069)
**File:** `frontend/src/hooks/usePeople.ts:146`
- Changed `params.set('role', ...)` → `params.set('type', ...)`
- Backend expects `?type=resident`, frontend was sending `?role=resident`

### 5. Auto-save with Backup Endpoint ✅ (Session 070)
**Files:**
- `backend/app/api/routes/backup.py` - New snapshot/restore API
- `frontend/src/hooks/useBackup.ts` - TanStack Query hooks
- `frontend/src/app/admin/templates/page.tsx` - Queued edits with debounced save

**Features:**
- Table snapshots before bulk operations (pg_dump single table)
- Restore capability with dry-run preview
- Auto-save: field edits queue → debounced flush (1.5s)
- Unsaved changes indicator in header

### 6. Week-by-week Pattern Editing ✅ (Session 070)
**Files:**
- `backend/app/models/weekly_pattern.py` - Added `week_number` column
- `backend/app/schemas/rotation_template_gui.py` - Updated schemas
- `backend/alembic/versions/20260107_add_week_num_weekly_patterns.py` - Migration
- `frontend/src/types/weekly-pattern.ts` - Added `WeekNumber` type
- `frontend/src/components/scheduling/WeeklyGridEditor.tsx` - Added week tabs

**Features:**
- Week 1/2/3/4 tabs for week-specific patterns
- "Same pattern all weeks" toggle
- Up to 56 slots (14 per week × 4 weeks)

### 7. Half-block Rotation Support ✅ (Session 070)
**Files:**
- `backend/app/models/rotation_template.py` - Added `is_block_half_rotation`
- `frontend/src/types/admin-templates.ts` - Updated types

**Note:** Migration already existed: `9d38e1388001_add_is_block_half_rotation`

---

## REMAINING TASKS (Session 070 Continuation)

**Plan file:** `.claude/plans/merry-hatching-torvalds.md`

### Execution Order:
1. ~~Fix people toggle~~ ✅
2. ~~Auto-save: queued edits + backup endpoint~~ ✅
3. ~~Week-by-week pattern editing~~ ✅
4. ~~Half-block rotation support~~ ✅
5. **Admin people bulk edit page** ← IN PROGRESS
6. Procedure credentialing matrix
7. Rename pages (templates→activities/rotations) - Frontend-only
8. Navigation cleanup

### Phase 1: Admin People Bulk Edit - Implementation Status

**Backend:** 100% ready
- `POST /people/batch` - Batch create
- `PUT /people/batch` - Batch update
- `DELETE /people/batch` - Batch delete

**Frontend (to create):**
1. `frontend/src/hooks/usePeople.ts` - Add batch hooks (follow useAdminTemplates.ts:193-260 pattern)
2. `frontend/src/app/admin/people/page.tsx` - New admin page (copy admin/templates/page.tsx structure)
3. `frontend/src/components/admin/PeopleTable.tsx` - Table with selection
4. `frontend/src/components/admin/PeopleBulkActionsToolbar.tsx` - Bulk action toolbar

### Reference Files
- Pattern to follow: `frontend/src/hooks/useAdminTemplates.ts:193-260` (batch mutations)
- Page structure: `frontend/src/app/admin/templates/page.tsx` (dark theme admin page)
- Table component: `frontend/src/components/admin/TemplateTable.tsx`
- Toolbar component: `frontend/src/components/admin/BulkActionsToolbar.tsx`

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
