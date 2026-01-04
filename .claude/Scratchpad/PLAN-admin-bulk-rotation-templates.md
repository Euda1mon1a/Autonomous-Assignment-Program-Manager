# P0: Admin GUI for Bulk Rotation Template Changes

**Branch:** `feat/admin-bulk-rotation-templates`
**Priority:** P0
**Created:** 2026-01-04

---

## Objective

Build admin interface for bulk viewing/editing rotation templates with:
- Grid view of all templates
- Bulk edit capabilities (select multiple → change properties)
- Weekly pattern editor (7×2 visual grid)
- Preference management
- DB backup/restore integration

---

## Pre-Implementation Setup

### 1. Database Backup
```bash
# Backup current DB before changes
docker exec scheduler-db pg_dump -U scheduler scheduler > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. Fresh DB (if needed)
```bash
# Warning: Destroys data
docker-compose down -v
docker-compose up -d db
alembic upgrade head
python -m app.scripts.seed_all  # or appropriate seed
```

### 3. Container Restart Protocol
- MCP server will show "rebuilding" status
- Frontend hot-reload should handle changes
- If full restart needed: `docker-compose restart`

---

## Implementation Phases

### Phase 1: Admin Page Shell
**Route:** `/admin/templates`

**Files to create:**
- `frontend/src/app/admin/templates/page.tsx` - Main page
- `frontend/src/app/admin/templates/components/` - Components dir

**Features:**
- List all rotation templates in table/grid
- Filter by activity_type
- Sort by name, created_at
- Select multiple rows

### Phase 2: Template CRUD UI
**Components:**
- `TemplateTable.tsx` - Sortable, selectable table
- `TemplateForm.tsx` - Create/edit single template
- `TemplateCard.tsx` - Card view option

**Bulk Actions Toolbar:**
- Delete selected
- Change activity_type
- Update leave_eligible
- Update supervision settings

### Phase 3: Weekly Pattern Grid Editor
**Component:** `WeeklyGridEditor.tsx`

**Layout:**
```
        Mon  Tue  Wed  Thu  Fri  Sat  Sun
  AM   [ ]  [ ]  [P]  [ ]  [ ]  [ ]  [ ]
  PM   [ ]  [ ]  [ ]  [ ]  [ ]  [ ]  [ ]
```
- [P] = Protected slot (e.g., Wed AM conference)
- Click to edit activity_type
- Color coding by activity
- Drag to select multiple slots

### Phase 4: Preference Manager
**Component:** `PreferenceEditor.tsx`

**Features:**
- Add/remove preferences
- Set weight (low/medium/high/required)
- Configure type-specific options
- Preview impact on scheduling

### Phase 5: Bulk Operations
**Components:**
- `BulkEditModal.tsx` - Edit multiple templates
- `BulkPatternModal.tsx` - Apply pattern to multiple templates

**API Integration:**
- Use existing bulk schemas
- Implement missing bulk routes if needed

---

## API Verification Needed

Check if these routes are implemented:
- [ ] `GET /api/rotation-templates/{id}/patterns`
- [ ] `PUT /api/rotation-templates/{id}/patterns`
- [ ] `GET /api/rotation-templates/{id}/preferences`
- [ ] `PUT /api/rotation-templates/{id}/preferences`

If missing, add to backend first.

---

## Testing Strategy

1. **Unit Tests:** Component rendering, form validation
2. **Integration Tests:** API calls, state management
3. **E2E Tests:** Full CRUD workflow
4. **Visual Tests:** Grid editor interactions

---

## Delegation

| Phase | Agent | Notes |
|-------|-------|-------|
| 1-2 | FRONTEND_ENGINEER | Page structure, table |
| 3 | FRONTEND_ENGINEER + UX | Grid editor complexity |
| 4-5 | FRONTEND_ENGINEER | Forms, modals |
| API gaps | BACKEND_ENGINEER | If routes missing |
| Tests | QA_TESTER | All phases |

---

## Risk Factors

- Weekly grid editor is complex UI
- Bulk operations need transaction safety
- Pattern validation (no duplicate day/time)
- Mobile responsiveness

---

## Success Criteria

- [ ] Admin can view all templates in sortable table
- [ ] Admin can bulk-select and modify properties
- [ ] Admin can edit 7×2 weekly pattern visually
- [ ] Admin can manage scheduling preferences
- [ ] All operations have undo/confirmation
- [ ] Tests pass
