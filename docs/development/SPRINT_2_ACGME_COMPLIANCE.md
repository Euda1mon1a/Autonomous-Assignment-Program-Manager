# Sprint 2 (Revised): ACGME Compliance Overhaul

## Overview

**Focus:** Fix critical ACGME duty hour validation issues identified by Gemini 3.0 review.

**Terminals:** 12 (not 25 - task doesn't warrant artificial splitting)

**Priority:** CRITICAL - Compliance errors have real-world consequences for medical residents and program accreditation.

---

## Executive Summary of Issues

| # | Issue | Current State | Required Fix |
|---|-------|---------------|--------------|
| 1 | 80-hour weekly limit | Broken averaging | Fixed rotation blocks |
| 2 | 1 day in 7 free | **Missing** | New validator |
| 3 | In-house call Q3 | **Missing** | New validator |
| 4 | 24+4 continuous duty | Broken logic | Rewrite + model changes |
| 5 | 8 hours between shifts | **Missing** | New validator |
| 6 | 14 hours after 24h call | **Missing** | New validator |

### Required Model Changes
```python
# Block model additions needed:
start_time: datetime.time    # e.g., 07:00:00
duration_hours: float        # e.g., 12.0
is_call_shift: bool          # True for 24h call shifts
is_night_float: bool         # True for night float rotations
```

---

## Terminal Assignments (12 Total)

### PHASE 1: Foundation (Must Complete First)

#### Terminal 1: Block Model Enhancement
**Files:**
- `backend/app/models/block.py` (MODIFY)
- `backend/app/schemas/block.py` (MODIFY)
- `backend/alembic/versions/xxx_add_block_time_fields.py` (CREATE)

**Scope:**
- Add `start_time`, `duration_hours`, `is_call_shift`, `is_night_float` to Block model
- Update Pydantic schemas with validation
- Create Alembic migration
- Add backward-compatible defaults for existing blocks

**Duration:** 45-60 min

**Dependencies:** None (Foundation)

---

#### Terminal 2: Rotation Period Configuration
**Files:**
- `backend/app/models/rotation_period.py` (CREATE)
- `backend/app/schemas/rotation_period.py` (CREATE)
- `backend/alembic/versions/xxx_add_rotation_periods.py` (CREATE)

**Scope:**
- Create RotationPeriod model for 4-week averaging blocks
- Fields: `start_date`, `end_date`, `name`, `academic_year`
- Link to schedule validation context
- Support variable-length rotations (2-4 weeks)

**Duration:** 45-60 min

**Dependencies:** None (Foundation)

---

### PHASE 2: Core Validators (Parallel After Phase 1)

#### Terminal 3: 80-Hour Rule Rewrite
**Files:**
- `backend/app/validators/acgme_80_hour.py` (CREATE)
- `backend/tests/test_acgme_80_hour.py` (CREATE)

**Scope:**
- Rewrite 80-hour validation with fixed rotation blocks
- Use RotationPeriod for averaging window
- Exclude vacation/sick days from denominator
- Include moonlighting hours in total
- Handle <4 week rotations correctly

**Key Rules:**
- 80 hours/week averaged over rotation period
- Vacation/sick days excluded from denominator
- All clinical + educational hours count

**Duration:** 60-90 min

**Dependencies:** Terminal 1, Terminal 2

---

#### Terminal 4: 1-in-7 Day Off Validator
**Files:**
- `backend/app/validators/acgme_day_off.py` (CREATE)
- `backend/tests/test_acgme_day_off.py` (CREATE)

**Scope:**
- New validator: 1 day free in 7 (averaged over 4 weeks)
- Define "free day" = no clinical work AND no required education
- Calculate using rotation period averaging
- Handle partial weeks at rotation boundaries

**Key Rules:**
- Minimum 1 day off per 7 days (averaged)
- Day = 24-hour period free of all duties
- Average over rotation period, not rolling

**Duration:** 60-90 min

**Dependencies:** Terminal 1, Terminal 2

---

#### Terminal 5: In-House Call Frequency (Q3)
**Files:**
- `backend/app/validators/acgme_call_frequency.py` (CREATE)
- `backend/tests/test_acgme_call_frequency.py` (CREATE)

**Scope:**
- New validator: No more than every 3rd night on call
- Uses `is_call_shift` from Block model
- Averaged over 4-week rotation period
- Distinct from night float (consecutive night) limits

**Key Rules:**
- Q3 = maximum 1 in-house call per 3 nights averaged
- Does NOT apply to night float rotations
- Average over rotation period

**Duration:** 45-60 min

**Dependencies:** Terminal 1, Terminal 2

---

#### Terminal 6: 24+4 Continuous Duty Rewrite
**Files:**
- `backend/app/validators/acgme_continuous_duty.py` (CREATE)
- `backend/tests/test_acgme_continuous_duty.py` (CREATE)

**Scope:**
- Complete rewrite of continuous duty calculation
- Use `start_time` and `duration_hours` from Block
- 8-hour gap breaks continuity
- Max 24 hours + 4 hours for transitions
- PGY-1 special case: 16-hour max

**Key Rules:**
- Gap < 8 hours = continuous duty period
- Max 24 hours clinical work
- +4 hours allowed for transitions/education only
- PGY-1: Max 16 hours (no +4)

**Duration:** 90-120 min

**Dependencies:** Terminal 1

---

#### Terminal 7: 8-Hour Rest Between Shifts
**Files:**
- `backend/app/validators/acgme_rest_between.py` (CREATE)
- `backend/tests/test_acgme_rest_between.py` (CREATE)

**Scope:**
- New validator: 8 hours off between scheduled work
- Calculate gap between shift end and next shift start
- Flag violations when gap < 8 hours

**Key Rules:**
- Minimum 8 hours between clinical work periods
- 10 hours "should" for intermediate residents (warning, not violation)
- Use Block `start_time` and `duration_hours`

**Duration:** 45-60 min

**Dependencies:** Terminal 1

---

#### Terminal 8: 14-Hour Post-Call Rest
**Files:**
- `backend/app/validators/acgme_post_call.py` (CREATE)
- `backend/tests/test_acgme_post_call.py` (CREATE)

**Scope:**
- New validator: 14 hours free after 24-hour call
- Only applies to shifts where `is_call_shift=True` AND duration >= 24
- Check next scheduled shift doesn't start within 14 hours

**Key Rules:**
- After 24h in-house call: 14 hours free required
- Free = no clinical work, no required education
- Clock starts when call shift ends

**Duration:** 45-60 min

**Dependencies:** Terminal 1

---

### PHASE 3: Integration & Edge Cases

#### Terminal 9: Edge Case Handling
**Files:**
- `backend/app/validators/acgme_edge_cases.py` (CREATE)
- `backend/tests/test_acgme_edge_cases.py` (CREATE)

**Scope:**
- Vacation/sick day exclusion logic
- Moonlighting hours integration
- Home call activation tracking (if Block is_call_shift + actually came in)
- Educational activities classification

**Key Rules:**
- Vacation/sick: Exclude from averaging denominator
- Moonlighting: Include in 80-hour total
- Home call: Only count time physically present
- Didactics/conferences: Count as duty hours

**Duration:** 60-90 min

**Dependencies:** Terminals 3-8

---

#### Terminal 10: Validator Orchestrator Update
**Files:**
- `backend/app/validators/advanced_acgme.py` (MODIFY)
- `backend/app/validators/__init__.py` (MODIFY)
- `backend/tests/test_acgme_integration.py` (CREATE)

**Scope:**
- Integrate all new validators into ACGMEValidator class
- Remove/deprecate old broken methods
- Add configuration for enabling/disabling rules
- Create integration tests for combined validation

**Duration:** 60-90 min

**Dependencies:** Terminals 3-9

---

### PHASE 4: Frontend & Documentation

#### Terminal 11: Frontend Block Editor Updates
**Files:**
- `frontend/src/components/forms/BlockForm.tsx` (MODIFY or CREATE)
- `frontend/src/components/schedule/BlockEditor.tsx` (MODIFY)
- `frontend/src/types/block.ts` (MODIFY)

**Scope:**
- Add time picker for `start_time`
- Add duration input for `duration_hours`
- Add checkboxes for `is_call_shift`, `is_night_float`
- Validate inputs client-side
- Update TypeScript types

**Duration:** 60-90 min

**Dependencies:** Terminal 1 (schema changes)

---

#### Terminal 12: Documentation & Compliance Guide
**Files:**
- `docs/compliance/ACGME_IMPLEMENTATION.md` (CREATE)
- `docs/compliance/DUTY_HOUR_RULES.md` (CREATE)
- `docs/compliance/VALIDATION_REFERENCE.md` (CREATE)
- `docs/api/endpoints/compliance.md` (CREATE)

**Scope:**
- Document all ACGME rules implemented
- Map code to ACGME Common Program Requirements VI
- Document edge case handling decisions
- API reference for compliance endpoints
- Troubleshooting guide for violations

**Duration:** 45-60 min

**Dependencies:** Terminals 3-9 (need final implementation details)

---

## Dependency Graph

```
Phase 1 (Foundation):
┌─────────────┐    ┌─────────────────────┐
│ Terminal 1  │    │ Terminal 2          │
│ Block Model │    │ Rotation Periods    │
└──────┬──────┘    └──────────┬──────────┘
       │                      │
       └──────────┬───────────┘
                  │
Phase 2 (Validators - Parallel):
                  ▼
    ┌─────────────────────────────────────────────┐
    │  T3: 80-Hour  │  T4: 1-in-7  │  T5: Q3 Call │
    │  T6: 24+4     │  T7: 8hr Rest│  T8: 14hr PC │
    └─────────────────────────────────────────────┘
                  │
Phase 3 (Integration):
                  ▼
    ┌─────────────────────────────────────────────┐
    │  T9: Edge Cases  │  T10: Orchestrator       │
    └─────────────────────────────────────────────┘
                  │
Phase 4 (Frontend & Docs):
                  ▼
    ┌─────────────────────────────────────────────┐
    │  T11: Frontend   │  T12: Documentation      │
    └─────────────────────────────────────────────┘
```

---

## File Ownership Matrix

| Terminal | Files Owned | Can Modify |
|----------|-------------|------------|
| T1 | `models/block.py`, `schemas/block.py`, migration | - |
| T2 | `models/rotation_period.py`, `schemas/rotation_period.py`, migration | - |
| T3 | `validators/acgme_80_hour.py`, `tests/test_acgme_80_hour.py` | - |
| T4 | `validators/acgme_day_off.py`, `tests/test_acgme_day_off.py` | - |
| T5 | `validators/acgme_call_frequency.py`, `tests/test_acgme_call_frequency.py` | - |
| T6 | `validators/acgme_continuous_duty.py`, `tests/test_acgme_continuous_duty.py` | - |
| T7 | `validators/acgme_rest_between.py`, `tests/test_acgme_rest_between.py` | - |
| T8 | `validators/acgme_post_call.py`, `tests/test_acgme_post_call.py` | - |
| T9 | `validators/acgme_edge_cases.py`, `tests/test_acgme_edge_cases.py` | - |
| T10 | `validators/advanced_acgme.py`, `validators/__init__.py`, `tests/test_acgme_integration.py` | - |
| T11 | `components/forms/BlockForm.tsx`, `components/schedule/BlockEditor.tsx`, `types/block.ts` | - |
| T12 | `docs/compliance/*` | - |

---

## Execution Plan

### Option A: Sequential (Safest)
1. Run T1 + T2 together (Phase 1)
2. Wait for completion
3. Run T3-T8 in parallel (Phase 2)
4. Wait for completion
5. Run T9-T10 (Phase 3)
6. Run T11-T12 in parallel (Phase 4)

**Total Time:** ~6-8 hours (with wait times)

### Option B: Staged Parallel (Recommended)
1. Run T1 + T2 (30-60 min)
2. Immediately run T3-T8 (validators can stub Block model imports)
3. Run T9-T12 once validators stabilize

**Total Time:** ~4-5 hours

---

## Success Criteria

- [ ] All 6 ACGME rules have dedicated validators
- [ ] All validators have >90% test coverage
- [ ] Block model supports time-based calculations
- [ ] Rotation periods support 4-week averaging
- [ ] No false positives for valid schedules
- [ ] No false negatives for violations
- [ ] Frontend can edit new Block fields
- [ ] Documentation maps code to ACGME requirements

---

## Post-Sprint Validation

After sprint completion, request Gemini 3.0 re-review:

```
Review the updated ACGME validators in backend/app/validators/acgme_*.py

Verify against ACGME Common Program Requirements Section VI:
1. 80-hour rule with rotation-based averaging
2. 1 day in 7 free
3. In-house call frequency (Q3)
4. 24+4 continuous duty with 8-hour gap rule
5. 8 hours between shifts
6. 14 hours free after 24h call

Confirm: No misinterpretations, no missing requirements.
```

---

## Gemini 3.0 Review Summary (Reference)

### Key Implementation Details from Gemini:

1. **8 hours** breaks continuity (not 10)
2. **Fixed rotation blocks** for averaging (not rolling windows)
3. **Vacation/sick excluded** from averaging denominator
4. **Educational activities count** as duty hours
5. **Moonlighting counts** toward 80-hour limit
6. **Home call** only counts time physically present
7. **Q3 call** = max every 3rd night, averaged over rotation
8. **PGY-1** = 16-hour max (no +4 transition time)
