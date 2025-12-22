# Faculty Scheduling Integration

## Current Architecture ✅

**This is by design:**
1. Solver schedules residents → template half-day activities
2. Faculty assignments built around resident needs (post-processing)
3. `engine.py:701-780` handles faculty via `_assign_faculty()`

## What's Working
- Supervision ratio enforcement
- Basic faculty coverage

## What's Missing (Wednesday Rules)

The post-processing step (`_assign_faculty`) needs enhancement:

| Rule | Status |
|------|--------|
| Regular Wed PM: 1 faculty in clinic | ❌ Not enforced |
| 4th Wed AM: 1 faculty in clinic | ❌ Not enforced |
| 4th Wed PM: 1 different faculty | ❌ Not enforced |
| 4th Wed faculty equity | ❌ Not enforced |

## Implementation Options

### Option A: Enhance Post-Processing (Recommended)
Extend `engine.py:_assign_faculty()` to:
1. Identify Wednesday blocks in resident schedule
2. Assign exactly 1 faculty on Wed PM (1st-3rd)
3. Assign 2 different faculty on 4th Wed (AM/PM)
4. Track 4th Wed assignments for equity

**Pros:** Minimal change, preserves design intent  
**Cons:** No solver optimization for faculty

### Option B: Model Faculty in Solver
Add faculty decision variables to solver.

**Warning:** Codex found issues with current doc:
- Shape mismatch (3D proposed, 2D in existing constraints)
- Missing PuLP implementation
- Missing solution extraction
- Other constraints need updates (`FacultyRoleClinicConstraint`, etc.)

**Pros:** Full optimization  
**Cons:** Major architectural change (~8-10 hours)

---

## Recommendation

**Start with Option A** - enhance `_assign_faculty()` to handle Wednesday rules. This:
- Matches original n8n/Airtable design
- Is lower risk
- Delivers value faster

Faculty decision variables can be added later if optimization is needed.

## Files to Modify (Option A)
- `backend/app/scheduling/engine.py` - `_assign_faculty()` method
- Add Wednesday detection helpers
- Add equity tracking for 4th Wed
