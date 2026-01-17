# Session: Schema Visualizer + Block Explorer Phase 2

**Date:** 2026-01-16
**Branch:** `chore/branch-pruning`
**Status:** Implementation complete, uncommitted

---

## Work Completed

### 1. Schema Export CLI (backend)
- Added `export` command to `backend/app/cli/schema_commands.py`
- Extracts tables, columns, FKs from SQLAlchemy models
- Maps 102 tables to 30 domains with color coding
- Output: `frontend/public/data/schema.json` (85KB)

### 2. Interactive Visualizer (standalone)
- Created `frontend/public/schema-visualizer.html`
- SVG-based rendering with radial domain clustering
- Features: click expand/collapse, FK line highlighting, pan/zoom, search, domain filters
- Glassmorphism styling consistent with other visualizers

### 3. Admin GUI Integration
- Added nav item to `Navigation.tsx` and `MobileNav.tsx`
- Created `frontend/src/app/admin/schema/page.tsx` (iframe wrapper)
- Protected with `<ProtectedRoute requireAdmin={true}>`
- Access via `/admin/schema` (admin-only)

---

## Files Modified/Created

| File | Action |
|------|--------|
| `backend/app/cli/schema_commands.py` | Modified - added export command |
| `frontend/public/data/schema.json` | Created - 102 tables, 77 FKs |
| `frontend/public/schema-visualizer.html` | Created - SVG visualizer |
| `frontend/src/components/Navigation.tsx` | Modified - added Schema nav item |
| `frontend/src/components/MobileNav.tsx` | Modified - added Schema nav item |
| `frontend/src/app/admin/schema/page.tsx` | Created - admin page wrapper |

---

## Verification Steps

1. Start frontend: `cd frontend && npm run dev`
2. Login as admin
3. Navigate to `/admin/schema` or click "Schema" in black admin bar
4. Verify visualizer loads with all 102 tables
5. Test: click tables, search, filter domains, pan/zoom

---

## Notes

- Linter passes (only pre-existing warnings)
- Schema data generated manually (Python env not available in session)
- To regenerate schema.json: `python -m app.cli schema export`

---

## Block Explorer Phase 2: Pre-Launch Verification Features

### Context
Three exploration agents completed prior to implementation:
1. **Excel Export Workflow** - Found verification gaps in legacy export pipeline
2. **MCP Validation Tools** - Cataloged 20 verification tools for pre-launch checks
3. **Schedule Generation Prerequisites** - Documented entity/config requirements

### Implementation Completed

#### 1. JSON Schema Updates (`frontend/public/data/block-10-explorer.json`)
Added two new data sections:

```json
"completeness": {
  "residents": { "assigned": 14, "total": 14, "status": "pass" },
  "faculty": { "active": 8, "total": 8, "status": "pass" },
  "rotations": { "defined": 6, "total": 6, "status": "pass" },
  "absences": { "recorded": 3, "pending": 0, "status": "pass" },
  "callRoster": { "filled": 28, "total": 28, "status": "pass" },
  "coverage": { "filled": 784, "total": 784, "gaps": 0, "status": "pass" }
},
"acgmeCompliance": {
  "overallStatus": "pass",
  "lastChecked": "2026-01-16T10:30:00Z",
  "rules": [
    { "id": "80-hour", "name": "80-Hour Rule", "status": "pass", ... },
    { "id": "1-in-7", "name": "1-in-7 Day Off", "status": "pass", ... },
    { "id": "supervision", "name": "Supervision Ratios", "status": "pass", ... }
  ]
}
```

#### 2. Data Completeness Panel (Left Sidebar)
- Collapsible panel above filters
- Shows 6 items: Residents, Faculty, Rotations, Absences, Call Roster, Coverage
- Color-coded status icons (green/amber/red)
- Summary badge in header ("6/6 Complete")

#### 3. ACGME Compliance Widget (Right Sidebar)
- New section above Validation Checks
- Displays 3 rules with PASS/WARN/FAIL badges
- Overall compliance status box (COMPLIANT/VIOLATIONS)
- Refresh button (ready for future API integration)

#### 4. Pre-Export Checklist Footer (Fixed Bottom)
- 3 checklist items:
  - Data Complete (X/6)
  - ACGME Compliant
  - All Reviewed (X/14)
- Export Excel button (disabled until all pass)
- Download JSON button (always available)
- READY badge animation when all checks pass

#### 5. JavaScript Functions Added
- `renderCompletenessPanel()` - Renders data completeness items
- `toggleCompletenessPanel()` - Collapse/expand toggle
- `renderACGMEComplianceWidget()` - Renders ACGME rules
- `updateExportChecklist()` - Updates checklist state
- `updateChecklistItem()` - Helper for styling
- `downloadJSON()` - Downloads block data as JSON
- `exportToExcel()` - Placeholder for future API integration

### Export Gate Logic
Export button enabled ONLY when:
1. All 6 data completeness items have status "pass"
2. ACGME compliance overallStatus is "pass"
3. All 14 residents are marked as reviewed (localStorage)

---

## Files Modified (Block Explorer Phase 2)

| File | Changes |
|------|---------|
| `frontend/public/data/block-10-explorer.json` | +38 lines - completeness + acgmeCompliance |
| `frontend/public/block-explorer.html` | +200 lines - CSS, HTML sections, JS functions |

---

## Future API Integration (Not This PR)

When ready to connect to live data:
1. Replace static JSON with API fetch to `/api/v1/block-scheduler/{block_id}/dashboard`
2. Wire ACGME Refresh button to `/api/v1/compliance/validate`
3. Wire Export Excel button to `/api/v1/export/schedule/xlsx`
4. Add loading states and error handling

---

## Verification Steps (Block Explorer)

1. Open `http://localhost:3000/admin/block-explorer` (or static HTML)
2. Verify Data Completeness panel shows 6/6 complete
3. Verify ACGME Compliance widget shows 3 rules + COMPLIANT status
4. Verify Pre-Export Checklist footer at bottom
5. Mark all 14 residents as reviewed
6. Verify "READY" badge appears and Export Excel enables
7. Click Export Excel (currently downloads JSON with message)
8. Click Download JSON (saves block data)

---

## Phase 3: Full-Stack Integration (COMPLETED)

### Objective
Wire up Block Explorer to live backend APIs instead of static JSON.

### Backend Implementation

#### 1. New Pydantic Schemas (`backend/app/schemas/block_explorer.py`)
Created ~180 lines of schema definitions:
- `BlockMeta` - Block metadata
- `CompletenessItem` / `CompletenessData` - Data completeness tracking
- `ACGMERule` / `ACGMEComplianceData` - ACGME compliance status
- `HealthData` - Schedule health metrics
- `CalendarWeek` / `CalendarData` - Calendar structure
- `ResidentHalfDay` / `ResidentExplorerData` - Resident data with half-days
- `RotationExplorerData` - Rotation info
- `ValidationCheck` - Validation check results
- `SourceInfo` - Assignment source metadata
- `BlockExplorerResponse` - Main response model

#### 2. Service Method (`backend/app/services/block_scheduler_service.py`)
Added `get_explorer_data(block_number, academic_year)` method (~340 lines):
- Aggregates data from dashboard + ACGME validator
- Builds completeness data from dashboard counts
- Transforms validation violations to ACGME compliance format
- Generates calendar structure with 28-day weeks
- Builds resident list with half-day placeholders
- Computes validation checks from violation types
- Returns dict matching `BlockExplorerResponse` schema

#### 3. API Endpoint (`backend/app/api/routes/block_scheduler.py`)
Added `GET /{block_number}/explorer`:
- Path: `/api/v1/block-scheduler/{block_number}/explorer?academic_year=YYYY`
- Requires authentication
- Returns complete Block Explorer data

#### 4. Controller Method (`backend/app/controllers/block_scheduler_controller.py`)
Added `get_explorer_data()` - delegates to service

### Frontend Implementation

#### 1. State Management Updates
- Added `currentBlock = 10` (selected block)
- Added `currentAcademicYear = getCurrentAcademicYear()`
- Added `isAuthenticated = false`
- localStorage key now uses block number: `block${currentBlock}-reviewed`

#### 2. Block Selector Dropdown
- Added `<select id="block-selector">` with options 1-13
- Event listener updates `currentBlock` and reloads data

#### 3. Authentication Check
- Added `checkAuth()` function
- Attempts `/api/v1/users/me` fetch
- Redirects to login on 401, continues in demo mode on network error

#### 4. API Data Fetching
- `loadBlockData()` now tries API first: `/api/v1/block-scheduler/{block}/explorer`
- Falls back to static JSON on API failure
- Logs source of data for debugging

#### 5. ACGME Refresh Button
- Now calls `/api/v1/schedule/validate` with date range
- Transforms `ValidationResult` to compliance format
- Updates widget and checklist on success

#### 6. Excel Export Button
- Now calls `/api/v1/export/schedule/xlsx` with params
- Downloads blob as `.xlsx` file
- Shows loading spinner during export
- Falls back to JSON download on failure

### Files Modified (Phase 3)

| File | Action | Lines |
|------|--------|-------|
| `backend/app/schemas/block_explorer.py` | CREATE | ~180 |
| `backend/app/services/block_scheduler_service.py` | ADD | ~340 |
| `backend/app/api/routes/block_scheduler.py` | ADD | ~25 |
| `backend/app/controllers/block_scheduler_controller.py` | ADD | ~10 |
| `frontend/public/block-explorer.html` | MODIFY | ~150 |

**Total:** ~705 lines

### Verification Steps (Phase 3)

1. **Backend API test:**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/block-scheduler/10/explorer?academic_year=2026" \
        -H "Authorization: Bearer $TOKEN"
   ```

2. **Frontend integration:**
   - Open Block Explorer
   - Check Network tab for API calls
   - Select different blocks from dropdown
   - Verify data updates

3. **ACGME refresh:**
   - Click Refresh button on ACGME widget
   - Verify API call and widget update

4. **Excel export:**
   - Complete checklist (mark all reviewed)
   - Click Export Excel
   - Verify `.xlsx` downloads

5. **Fallback mode:**
   - Stop backend, refresh page
   - Verify static JSON loads with warning

### Design Decisions

- **Block selection:** Dropdown for blocks 1-13
- **Academic year:** Derived from current date (July = new AY)
- **Authentication:** Required, redirects to login
- **Fallback:** Static JSON for development/demo mode

---

## Phase 4: Real Half-Day Data Wiring (COMPLETED)

### Objective
Replace placeholder half-day data in `get_explorer_data()` with real queries to existing tables.

### Changes Made

#### File: `backend/app/services/block_scheduler_service.py`

**1. Added Imports:**
```python
from sqlalchemy.orm import Session, joinedload
from app.models.activity import Activity
from app.models.call_assignment import CallAssignment
from app.models.half_day_assignment import HalfDayAssignment
```

**2. Added Bulk Queries (after line 696):**
- `HalfDayAssignment` query with `joinedload(activity)` for date range
- Index by `(person_id, date, time_of_day)` for O(1) lookup
- `CallAssignment` query for call roster completeness
- `Activity` query for color mapping

**3. Updated Completeness Counts:**
- `callRoster.filled` now uses actual `CallAssignment` count
- `coverage.filled` now uses actual `HalfDayAssignment` count

**4. Replaced Placeholder Half-Day Loop:**
- Real data from `hda_index` lookup
- Shows actual activity abbreviations per slot
- Shows actual source per slot (preload, manual, solver, template)
- Calculates `completeAssignments` from actual half-day records
- Flags residents with missing assignments

**5. Activity Colors:**
- Queried from `Activity.background_color`
- Fallback defaults for common codes (FMIT, NF, C, etc.)
- Used for rotation colors in rotations_data

### DB Changes Required
**NONE** - Query-only against existing tables:
- `half_day_assignments`
- `call_assignments`
- `activities`

### Lines Changed
~60 lines modified in `block_scheduler_service.py`

### Verification
1. Linter passes: `ruff check` ✓
2. Formatter applied: `ruff format` ✓

### Data Flow
```
HalfDayAssignment table
  ↓ bulk query + joinedload(activity)
hda_index dict (person_id, date, time_of_day) → HalfDayAssignment
  ↓ O(1) lookup per resident per day
Real half-day grid with actual activities/sources
```
