# Activity Assignment Architecture

> **Created:** 2026-01-19
> **Purpose:** Document the full-stack flow for assigning activities (C, LEC, ADV) to half-day slots

## Architecture Flow

```
BlockAssignment (manual)
       ↓
Expansion Service (creates 56 slots/person, activity_id=NULL)
       ↓
SyncPreloadService (locks FMIT, call, absences with activity_id)
       ↓
CPSATActivitySolver (assigns C, LEC, ADV to remaining slots)
       ↓
half_day_assignments (all slots have activity_id)
       ↓
Frontend (displays activities via /api/half-day-assignments)
```

## Key Files

| File | Purpose |
|------|---------|
| `backend/app/scheduling/engine.py` | Orchestrates the flow |
| `backend/app/services/sync_preload_service.py` | Loads locked assignments (sync version) |
| `backend/app/services/preload_service.py` | Async version (for API use) |
| `backend/app/scheduling/activity_solver.py` | CP-SAT solver for activity assignment |
| `backend/app/services/block_assignment_expansion_service.py` | Expands block → daily slots |

## Business Rules

### Activity Distribution
| Week | Wednesday AM | Wednesday PM | Other Slots |
|------|--------------|--------------|-------------|
| 1-3  | Primary (C) | **LEC** | Primary (C) |
| 4    | **LEC** | **ADV** | Primary (C) |

### Source Priority
| Source | Can Overwrite | Description |
|--------|--------------|-------------|
| preload | Nothing | FMIT, call, absences - locked |
| manual | Nothing | Human overrides - locked |
| solver | template | Activity solver output |
| template | All | Default from expansion |

## Engine Integration (engine.py)

```python
# Step 1.5g: Expand block_assignments
expansion_service = BlockAssignmentExpansionService(self.db)
expanded_assignments = expansion_service.expand_block_assignments(...)

# Step 1.5h: Load preloads (FMIT, call, absences)
preload_service = SyncPreloadService(self.db)
preload_count = preload_service.load_all_preloads(block_number, academic_year)

# Step 1.5i: Run activity solver
activity_solver = CPSATActivitySolver(self.db, timeout_seconds=30.0)
activity_result = activity_solver.solve(block_number, academic_year)
```

## HUMAN TODOs

1. Fork greedy, pulp, hybrid solvers for activity assignment
2. Add rotation_activity_requirements constraints to activity solver
3. Add tests for activity solver

## Verification SQL

```sql
-- Check activity distribution after generation
SELECT a.display_abbreviation, hda.source, COUNT(*)
FROM half_day_assignments hda
LEFT JOIN activities a ON hda.activity_id = a.id
WHERE hda.date BETWEEN '2026-03-12' AND '2026-04-08'
GROUP BY a.display_abbreviation, hda.source
ORDER BY COUNT(*) DESC;
```
