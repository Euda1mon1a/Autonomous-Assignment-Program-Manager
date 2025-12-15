# Sprint 2 ACGME Compliance - Terminal Prompts

## Execution Order

```
PHASE 1: T1 + T2 (Foundation) → Must complete first
PHASE 2: T3-T8 (Validators) → Parallel after Phase 1
PHASE 3: T9-T10 (Integration) → After Phase 2
PHASE 4: T11-T12 (Frontend/Docs) → After Phase 3
```

---

## PHASE 1 PROMPTS (Foundation)

### Terminal 1: Block Model Enhancement
```
Enhance the Block model with time-tracking fields for ACGME compliance.

FILES TO MODIFY:
- backend/app/models/block.py
- backend/app/schemas/block.py

FILE TO CREATE:
- backend/alembic/versions/[timestamp]_add_block_time_fields.py

ADD THESE FIELDS TO BLOCK MODEL:
- start_time: time (e.g., 07:00:00) - When the shift starts
- duration_hours: float (e.g., 12.0) - Length of shift in hours
- is_call_shift: bool (default False) - True for 24-hour call shifts
- is_night_float: bool (default False) - True for night float rotations

REQUIREMENTS:
- Add fields with backward-compatible defaults (start_time=07:00, duration_hours=8.0)
- Update Pydantic schema with Optional fields for creation, required for validation
- Create Alembic migration with proper upgrade/downgrade
- Add computed property: end_time = start_time + duration_hours
- Add validation: duration_hours must be 0.5-36 range

EXISTING BLOCK MODEL LOCATION: backend/app/models/block.py

DO NOT modify any validator files - those are handled by other terminals.
```

---

### Terminal 2: Rotation Period Configuration
```
Create a RotationPeriod model for ACGME 4-week averaging calculations.

FILES TO CREATE:
- backend/app/models/rotation_period.py
- backend/app/schemas/rotation_period.py
- backend/alembic/versions/[timestamp]_add_rotation_periods.py

MODEL FIELDS:
- id: UUID primary key
- name: str (e.g., "Block 1", "July Rotation")
- start_date: date
- end_date: date
- academic_year: str (e.g., "2024-2025")
- created_at: datetime
- updated_at: datetime

REQUIREMENTS:
- Validate end_date > start_date
- Validate duration between 14-35 days (2-5 weeks)
- Add computed property: duration_weeks = (end_date - start_date).days / 7
- Add method: contains_date(date) -> bool
- Create Alembic migration
- Export from models/__init__.py

SCHEMA REQUIREMENTS:
- RotationPeriodCreate: name, start_date, end_date, academic_year
- RotationPeriodUpdate: all optional
- RotationPeriodResponse: include id, computed duration_weeks

DO NOT create API routes - those may come later.
```

---

## PHASE 2 PROMPTS (Validators - Run in Parallel)

### Terminal 3: 80-Hour Rule Validator
```
Create ACGME 80-hour weekly limit validator with proper rotation-based averaging.

FILES TO CREATE:
- backend/app/validators/acgme_80_hour.py
- backend/tests/test_acgme_80_hour.py

VALIDATOR CLASS: EightyHourRuleValidator

METHODS:
- validate(assignments, rotation_period, person_id) -> ValidationResult
- calculate_weekly_hours(assignments, rotation_period) -> float
- get_excluded_days(person_id, rotation_period) -> list[date]  # vacation/sick

RULES TO IMPLEMENT (ACGME VI.F.1):
- Maximum 80 hours/week averaged over rotation period
- Include: clinical work, education, moonlighting
- Exclude: vacation and sick days from denominator
- Formula: total_hours / (rotation_weeks - excluded_weeks) <= 80

VALIDATION RESULT:
- valid: bool
- violation_type: "80_HOUR_VIOLATION" if invalid
- actual_hours: float
- allowed_hours: float
- message: descriptive string

TEST CASES:
- 79 hours/week = valid
- 81 hours in 1 week but 75 in others = valid (averaged)
- 85 hours/week averaged = violation
- Vacation week excluded from denominator
- Moonlighting hours included in total

REFERENCE: ACGME Common Program Requirements VI.F.1
```

---

### Terminal 4: 1-in-7 Day Off Validator
```
Create ACGME 1 day in 7 free validator.

FILES TO CREATE:
- backend/app/validators/acgme_day_off.py
- backend/tests/test_acgme_day_off.py

VALIDATOR CLASS: DayOffRuleValidator

METHODS:
- validate(assignments, rotation_period, person_id) -> ValidationResult
- count_days_off(assignments, rotation_period) -> int
- is_day_free(date, assignments) -> bool

RULES TO IMPLEMENT (ACGME VI.F.2.d):
- Minimum 1 day off per 7 days, averaged over rotation period
- "Day off" = 24 continuous hours free of clinical work AND education
- Average calculation: days_off / rotation_weeks >= 1

DEFINITION OF FREE DAY:
- No assignments on that calendar date
- AND no assignment ending on that date (post-call doesn't count)
- AND no assignment starting on that date

TEST CASES:
- 4 days off in 4 weeks = valid (1/week average)
- 3 days off in 4 weeks = violation
- 2-week rotation with 2 days off = valid
- Day with only educational conference = NOT a free day

REFERENCE: ACGME Common Program Requirements VI.F.2.d
```

---

### Terminal 5: In-House Call Frequency (Q3)
```
Create ACGME in-house call frequency validator (every 3rd night max).

FILES TO CREATE:
- backend/app/validators/acgme_call_frequency.py
- backend/tests/test_acgme_call_frequency.py

VALIDATOR CLASS: CallFrequencyValidator

METHODS:
- validate(assignments, rotation_period, person_id) -> ValidationResult
- count_call_nights(assignments, rotation_period) -> int
- calculate_call_frequency(call_count, total_nights) -> float

RULES TO IMPLEMENT (ACGME VI.F.7):
- In-house call no more frequent than every 3rd night (Q3)
- Averaged over 4-week rotation period
- Does NOT apply to night float rotations
- Formula: call_nights / total_nights <= 1/3

IDENTIFYING CALL SHIFTS:
- Use Block.is_call_shift == True
- Exclude night float (Block.is_night_float == True)

TEST CASES:
- 10 call nights in 30 days = valid (1/3)
- 12 call nights in 30 days = violation (>1/3)
- Night float rotation = skip this validation
- Mixed call + night float = only count call shifts

REFERENCE: ACGME Common Program Requirements VI.F.7
```

---

### Terminal 6: 24+4 Continuous Duty Rewrite
```
Rewrite ACGME continuous duty validator with correct gap-based logic.

FILES TO CREATE:
- backend/app/validators/acgme_continuous_duty.py
- backend/tests/test_acgme_continuous_duty.py

VALIDATOR CLASS: ContinuousDutyValidator

METHODS:
- validate(assignments, person_id) -> ValidationResult
- find_continuous_periods(assignments) -> list[ContinuousPeriod]
- calculate_gap_hours(assignment1, assignment2) -> float
- merge_if_continuous(period1, period2, gap_threshold=8) -> ContinuousPeriod

RULES TO IMPLEMENT (ACGME VI.F.3):
- Maximum 24 hours of continuous clinical work
- +4 hours allowed for transitions and education ONLY
- Gap < 8 hours = shifts are considered continuous
- PGY-1 special rule: Maximum 16 hours, no +4 extension

CONTINUOUS PERIOD CALCULATION:
1. Sort assignments by start_time
2. For each pair: gap = next_start - (prev_start + prev_duration)
3. If gap < 8 hours: merge into single continuous period
4. Sum total hours of merged period

TEST CASES:
- Single 12-hour shift = valid
- Two 12-hour shifts with 4-hour gap = 24hr continuous = valid
- Two 12-hour shifts with 6-hour gap = 24hr continuous = valid
- Three 12-hour shifts with <8hr gaps = 36hr violation
- 24hr call + 4hr rounds = valid (24+4)
- 24hr call + 6hr clinic = violation (30hr total)
- PGY-1 with 18-hour shift = violation (16hr max)

REFERENCE: ACGME Common Program Requirements VI.F.3
```

---

### Terminal 7: 8-Hour Rest Between Shifts
```
Create ACGME 8-hour rest between shifts validator.

FILES TO CREATE:
- backend/app/validators/acgme_rest_between.py
- backend/tests/test_acgme_rest_between.py

VALIDATOR CLASS: RestBetweenShiftsValidator

METHODS:
- validate(assignments, person_id) -> ValidationResult
- calculate_rest_period(assignment1, assignment2) -> float
- find_short_rest_violations(assignments) -> list[Violation]

RULES TO IMPLEMENT (ACGME VI.F.2.b):
- Minimum 8 hours off between scheduled clinical work periods
- 10 hours recommended for intermediate residents (warning only)

CALCULATION:
- rest_hours = next_start_time - (prev_start_time + prev_duration)
- If rest_hours < 8: violation
- If rest_hours < 10 and PGY2-3: warning

TEST CASES:
- 12-hour gap between shifts = valid
- 8-hour gap = valid (minimum)
- 6-hour gap = violation
- 9-hour gap for PGY-2 = warning (not violation)
- Overnight shift ending 7am, next shift 3pm = 8hr = valid

REFERENCE: ACGME Common Program Requirements VI.F.2.b
```

---

### Terminal 8: 14-Hour Post-Call Rest
```
Create ACGME 14-hour post-call rest validator.

FILES TO CREATE:
- backend/app/validators/acgme_post_call.py
- backend/tests/test_acgme_post_call.py

VALIDATOR CLASS: PostCallRestValidator

METHODS:
- validate(assignments, person_id) -> ValidationResult
- is_24_hour_call(assignment) -> bool
- find_next_assignment(call_assignment, all_assignments) -> Assignment
- calculate_post_call_rest(call_end, next_start) -> float

RULES TO IMPLEMENT (ACGME VI.F.2.c):
- After 24 hours of in-house call: minimum 14 hours free
- "Free" = no clinical work and no required education
- Clock starts when call shift ends

IDENTIFYING 24-HOUR CALL:
- Block.is_call_shift == True AND Block.duration_hours >= 24

TEST CASES:
- 24hr call ends 7am, next shift 9pm = 14hr rest = valid
- 24hr call ends 7am, next shift 5pm = 10hr rest = violation
- 24hr call ends 7am, next shift 10pm = 15hr rest = valid
- 16hr shift (not call) = this rule doesn't apply
- 24hr call followed by vacation day = valid

REFERENCE: ACGME Common Program Requirements VI.F.2.c
```

---

## PHASE 3 PROMPTS (Integration)

### Terminal 9: Edge Case Handler
```
Create edge case handling module for ACGME validators.

FILES TO CREATE:
- backend/app/validators/acgme_edge_cases.py
- backend/tests/test_acgme_edge_cases.py

CLASS: ACGMEEdgeCaseHandler

METHODS:
- exclude_vacation_days(assignments, person_id, date_range) -> list[Assignment]
- exclude_sick_days(assignments, person_id, date_range) -> list[Assignment]
- get_averaging_denominator(rotation_period, excluded_days) -> float
- include_moonlighting_hours(base_hours, moonlighting_assignments) -> float
- is_educational_activity(assignment) -> bool
- calculate_home_call_hours(home_call_activations) -> float

EDGE CASE RULES:
1. Vacation/sick: Exclude from averaging denominator, not numerator
2. Moonlighting: Add to total hours for 80-hour calculation
3. Educational activities: Count as duty hours (didactics, conferences)
4. Home call: Only count time physically at hospital

DATA REQUIREMENTS:
- Absence model with type field (vacation, sick, etc.)
- Moonlighting flag on assignments or separate tracking
- Home call activation log (future enhancement)

TEST CASES:
- 4-week rotation with 1 week vacation = average over 3 weeks
- 80 clinical + 5 moonlighting = 85 total (check against 80)
- Conference day = counts as duty hours
- Home call with no activation = 0 hours
- Home call with 4-hour activation = 4 hours

REFERENCE: ACGME Common Program Requirements VI.F
```

---

### Terminal 10: Validator Orchestrator Update
```
Update the main ACGME validator to use all new rule validators.

FILES TO MODIFY:
- backend/app/validators/advanced_acgme.py
- backend/app/validators/__init__.py

FILE TO CREATE:
- backend/tests/test_acgme_integration.py

CHANGES TO advanced_acgme.py:
1. Import all new validators (acgme_80_hour, acgme_day_off, etc.)
2. Remove/deprecate old broken methods
3. Create ACGMEValidatorSuite class that orchestrates all validators
4. Add configuration for enabling/disabling specific rules
5. Aggregate results from all validators

NEW CLASS: ACGMEValidatorSuite

METHODS:
- validate_all(assignments, rotation_period, person_id) -> ComprehensiveResult
- validate_rule(rule_name, ...) -> ValidationResult
- get_enabled_rules() -> list[str]
- enable_rule(rule_name) / disable_rule(rule_name)

COMPREHENSIVE RESULT:
- overall_valid: bool
- violations: list[Violation]
- warnings: list[Warning]
- by_rule: dict[rule_name, ValidationResult]

INTEGRATION TESTS:
- Valid schedule passes all rules
- Schedule with one violation correctly identified
- Multiple violations all reported
- Disabled rule not checked
- PGY-1 gets stricter validation

UPDATE __init__.py:
- Export ACGMEValidatorSuite
- Export individual validators for direct use
- Deprecation warning on old ACGMEValidator class
```

---

## PHASE 4 PROMPTS (Frontend & Docs)

### Terminal 11: Frontend Block Editor Updates
```
Update frontend Block editor to support new time fields.

FILES TO MODIFY:
- frontend/src/types/block.ts
- frontend/src/components/schedule/BlockEditor.tsx (or similar)

FILES TO CREATE (if needed):
- frontend/src/components/forms/BlockTimeFields.tsx

TYPE UPDATES (block.ts):
```typescript
interface Block {
  // ... existing fields
  start_time?: string;        // "HH:MM:SS" format
  duration_hours?: number;    // 0.5 - 36
  is_call_shift?: boolean;
  is_night_float?: boolean;
}
```

NEW COMPONENT: BlockTimeFields
- Time picker for start_time (use HTML time input or library)
- Number input for duration_hours with validation
- Checkbox for is_call_shift with label "24-hour call shift"
- Checkbox for is_night_float with label "Night float rotation"

UI REQUIREMENTS:
- Show computed end_time based on start + duration
- Validate duration is between 0.5 and 36 hours
- Show warning if duration > 24 and is_call_shift is false
- Conditionally show fields only when editing (not in list view)

INTEGRATION:
- Add BlockTimeFields to existing block creation/edit forms
- Update API calls to include new fields
- Handle backward compatibility (fields may be null for old blocks)

DO NOT modify backend code - that's handled by Terminal 1.
```

---

### Terminal 12: ACGME Compliance Documentation
```
Create comprehensive ACGME compliance documentation.

FILES TO CREATE:
- docs/compliance/README.md
- docs/compliance/ACGME_IMPLEMENTATION.md
- docs/compliance/DUTY_HOUR_RULES.md
- docs/compliance/VALIDATION_REFERENCE.md

README.md:
- Overview of ACGME compliance features
- Quick reference table of all rules
- Link to official ACGME requirements

ACGME_IMPLEMENTATION.md:
- How each rule is implemented in code
- Map validator classes to ACGME sections
- Design decisions and rationale
- Known limitations

DUTY_HOUR_RULES.md:
- Plain-English explanation of each rule
- Examples of valid vs. invalid scenarios
- PGY-level differences
- Edge cases and how they're handled

VALIDATION_REFERENCE.md:
- API reference for validation endpoints
- Request/response formats
- Error codes and messages
- Troubleshooting common violations

REQUIREMENTS:
- Use clear language for non-technical readers
- Include diagrams where helpful (mermaid)
- Cross-reference ACGME Common Program Requirements
- Include version/date for compliance tracking

REFERENCE SOURCE:
ACGME Common Program Requirements (Residency), Section VI
https://www.acgme.org/globalassets/pfassets/programrequirements/cprresidency_2022v3.pdf
```

---

## Execution Checklist

### Before Starting
- [ ] Phase 1 (T1, T2) runs first - others depend on model changes
- [ ] Confirm no file overlaps between terminals
- [ ] Each terminal has clear scope boundaries

### During Execution
- [ ] Phase 2 can start once Phase 1 model files are committed
- [ ] Validators can stub Block model imports initially
- [ ] Monitor for merge conflicts on validators/__init__.py

### After Completion
- [ ] Run full test suite
- [ ] Request Gemini re-review of final validators
- [ ] Verify no regressions in existing functionality
- [ ] Update CHANGELOG with compliance improvements
