***REMOVED*** ACGME Validator Implementation Guide

**Status:** Complete Implementation
**Version:** 1.0
**Last Updated:** 2025-12-31
**Scope:** 6 validator modules + orchestration engine

---

***REMOVED******REMOVED*** Overview

The ACGME Validation system consists of 5 specialized validators plus an orchestration engine:

```
┌─────────────────────────────────────────────────────┐
│       ACGMEComplianceEngine (Orchestrator)           │
└────┬────────┬────────┬────────┬────────┬────────────┘
     │        │        │        │        │
     ▼        ▼        ▼        ▼        ▼
  WorkHour  Supervision  Call   Leave  Rotation
  Validator Validator  Validator Validator Validator
```

***REMOVED******REMOVED*** 1. Work Hour Validator

**File:** `work_hour_validator.py`

***REMOVED******REMOVED******REMOVED*** Purpose
Enforces ACGME duty hour limits and work-life balance rules.

***REMOVED******REMOVED******REMOVED*** Implements
- **80-Hour Rule:** Maximum 80 hours/week (rolling 4-week average)
- **24+4 Rule:** Maximum 24 consecutive hours + 4 hours handoff (28 total)
- **10-Hour Rest:** Minimum 10 continuous hours off after 24-hour shift
- **Moonlighting Integration:** All moonlighting hours count toward 80-hour limit

***REMOVED******REMOVED******REMOVED*** Key Classes

***REMOVED******REMOVED******REMOVED******REMOVED*** `WorkHourValidator`
Main validator for duty hour compliance.

```python
from app.scheduling.validators import WorkHourValidator
from datetime import date, timedelta

validator = WorkHourValidator()

***REMOVED*** 80-hour rolling average validation
hours_by_date = {
    date(2025, 1, 1): 10.0,
    date(2025, 1, 2): 10.0,
    ***REMOVED*** ... 28 days of data
}
moonlighting_hours = {
    date(2025, 1, 1): 2.0,
}

violations, warnings = validator.validate_80_hour_rolling_average(
    person_id=resident_uuid,
    hours_by_date=hours_by_date,
    moonlighting_hours=moonlighting_hours
)

***REMOVED*** Check for violations
for v in violations:
    print(f"CRITICAL: {v.message}")

***REMOVED*** Check for warnings
for w in warnings:
    print(f"WARNING: {w.message}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** `BlockBasedWorkHourCalculator`
Converts block-based assignments to hour estimates.

```python
calculator = BlockBasedWorkHourCalculator()

assignments = [
    {'block_date': date(2025, 1, 1), 'rotation_id': 'fmit'},
    {'block_date': date(2025, 1, 1), 'rotation_id': 'clinic'},
]

rotation_intensity = {
    'fmit': 'intensive',  ***REMOVED*** 12 hours
    'clinic': 'standard',  ***REMOVED*** 6 hours
}

hours_by_date = calculator.calculate_hours_from_assignments(
    assignments,
    rotation_intensity_map=rotation_intensity
)
***REMOVED*** Result: {date(2025, 1, 1): 18.0}
```

***REMOVED******REMOVED******REMOVED*** Return Types

**WorkHourViolation:**
```python
@dataclass
class WorkHourViolation:
    person_id: UUID
    violation_type: str  ***REMOVED*** "80_hour", "24_plus_4", "rest_period", "moonlighting"
    severity: str  ***REMOVED*** "CRITICAL", "HIGH"
    message: str
    date_range: tuple[date, date]
    hours: float
    limit: float
    violation_percentage: float
```

**WorkHourWarning:**
```python
@dataclass
class WorkHourWarning:
    person_id: UUID
    warning_type: str  ***REMOVED*** "approaching_limit", "imbalance", "pattern"
    message: str
    current_hours: float
    warning_threshold: float
    days_remaining: int
```

---

***REMOVED******REMOVED*** 2. Supervision Validator

**File:** `supervision_validator.py`

***REMOVED******REMOVED******REMOVED*** Purpose
Ensures adequate faculty-to-resident ratios for patient safety and ACGME compliance.

***REMOVED******REMOVED******REMOVED*** Implements
- **PGY-1 Ratio:** 1 faculty per 2 residents (direct supervision)
- **PGY-2/3 Ratio:** 1 faculty per 4 residents (available supervision)
- **Fractional Load:** Accurate calculation for mixed PGY scenarios
- **Specialty Supervision:** Required specialty faculty for specialty rotations
- **Procedure Supervision:** Qualified faculty for procedure training

***REMOVED******REMOVED******REMOVED*** Key Classes

***REMOVED******REMOVED******REMOVED******REMOVED*** `SupervisionValidator`
Main validator for supervision ratios.

```python
from app.scheduling.validators import SupervisionValidator
from uuid import uuid4

validator = SupervisionValidator()

***REMOVED*** Calculate required faculty
pgy1_count = 3
other_count = 2

required = validator.calculate_required_faculty(pgy1_count, other_count)
***REMOVED*** (3*2 + 2 + 3) // 4 = ceil(11/4) = 3 faculty required

***REMOVED*** Validate single block
violation = validator.validate_block_supervision(
    block_id=uuid4(),
    block_date=date(2025, 1, 1),
    pgy1_residents=[uuid4(), uuid4(), uuid4()],
    other_residents=[uuid4(), uuid4()],
    faculty_assigned=[uuid4(), uuid4()],  ***REMOVED*** Only 2 faculty
)

if violation:
    print(f"CRITICAL: {violation.message}")
    print(f"Deficit: {violation.deficit} faculty")

***REMOVED*** Validate entire period
period_blocks = [
    {
        'block_id': uuid4(),
        'block_date': date(2025, 1, 1),
        'pgy1_residents': [...],
        'other_residents': [...],
        'faculty_assigned': [...]
    },
    ***REMOVED*** ... more blocks
]

violations, metrics = validator.validate_period_supervision(period_blocks)
print(f"Compliance: {metrics['compliance_rate']:.1f}%")
```

***REMOVED******REMOVED******REMOVED*** Faculty Calculation Formula

**Fractional Load Approach:**
```
supervision_units = (pgy1_count × 2) + (pgy2_3_count × 1)
required_faculty = ceil(supervision_units / 4)
```

**Examples:**
- 1 PGY-1 alone: (1×2 + 0) = 2 units → 1 faculty
- 2 PGY-1 together: (2×2 + 0) = 4 units → 1 faculty
- 3 PGY-1: (3×2 + 0) = 6 units → 2 faculty
- 1 PGY-1 + 1 PGY-2: (1×2 + 1) = 3 units → 1 faculty
- 4 PGY-2/3: (0 + 4) = 4 units → 1 faculty

***REMOVED******REMOVED******REMOVED*** Return Types

**SupervisionViolation:**
```python
@dataclass
class SupervisionViolation:
    block_id: Optional[UUID]
    block_date: date
    residents: int
    pgy1_count: int
    pgy2_3_count: int
    required_faculty: int
    actual_faculty: int
    deficit: int
    severity: str  ***REMOVED*** "CRITICAL", "HIGH"
    message: str
```

---

***REMOVED******REMOVED*** 3. Call Validator

**File:** `call_validator.py`

***REMOVED******REMOVED******REMOVED*** Purpose
Ensures fair and compliant call scheduling for faculty wellness.

***REMOVED******REMOVED******REMOVED*** Implements
- **Every-3rd-Night Rule:** Max ~10 calls per 28-day period
- **Consecutive Limits:** Max 2 consecutive overnight calls
- **Minimum Spacing:** At least 2 days between calls
- **Equity Tracking:** Fair distribution among faculty
- **Night Float Recovery:** Post-call day enforcement
- **Post-Call Rest:** 10-hour minimum after overnight call

***REMOVED******REMOVED******REMOVED*** Key Classes

***REMOVED******REMOVED******REMOVED******REMOVED*** `CallValidator`

```python
from app.scheduling.validators import CallValidator
from datetime import date, timedelta

validator = CallValidator()

***REMOVED*** Call frequency validation
faculty_id = uuid4()
call_dates = [
    date(2025, 1, 1),
    date(2025, 1, 4),
    date(2025, 1, 7),
    ***REMOVED*** ... more calls
]

violations, warnings = validator.validate_call_frequency(
    person_id=faculty_id,
    call_dates=call_dates
)

***REMOVED*** Call equity across faculty
faculty_calls = {
    uuid4(): [date(2025, 1, 1), date(2025, 1, 4), date(2025, 1, 7)],  ***REMOVED*** 3 calls
    uuid4(): [date(2025, 1, 2), date(2025, 1, 5)],  ***REMOVED*** 2 calls
    uuid4(): [date(2025, 1, 3), date(2025, 1, 6), date(2025, 1, 9)],  ***REMOVED*** 3 calls
}

warnings, metrics = validator.validate_call_equity(
    date(2025, 1, 1),
    date(2025, 1, 31),
    faculty_calls
)

print(f"Mean calls: {metrics['mean_calls']:.1f}")
print(f"Imbalance ratio: {metrics['imbalance_ratio']:.2f}")
```

***REMOVED******REMOVED******REMOVED*** Return Types

**CallViolation:**
```python
@dataclass
class CallViolation:
    person_id: UUID
    violation_type: str  ***REMOVED*** "frequency", "spacing", "consecutive", "equity"
    severity: str  ***REMOVED*** "CRITICAL", "HIGH", "MEDIUM"
    message: str
    call_dates: list[date]
    violation_count: int
```

---

***REMOVED******REMOVED*** 4. Leave Validator

**File:** `leave_validator.py`

***REMOVED******REMOVED******REMOVED*** Purpose
Validates absence blocking and leave policy compliance.

***REMOVED******REMOVED******REMOVED*** Implements
- **Blocking Enforcement:** No assignments during blocking absences
- **Conditional Blocking:** Duration-based blocking (medical >7d, sick >3d)
- **Leave Types:** 11 absence types (vacation, medical, deployment, etc.)
- **TDY/Deployment:** Military-specific leave handling
- **Post-Deployment Recovery:** 7-day recovery period after deployment
- **Tentative Dates:** Follow-up on uncertain return dates

***REMOVED******REMOVED******REMOVED*** Key Classes

***REMOVED******REMOVED******REMOVED******REMOVED*** `LeaveValidator`

```python
from app.scheduling.validators import LeaveValidator
from datetime import date

validator = LeaveValidator()

***REMOVED*** Determine if absence should block assignments
should_block = validator.should_block_assignment(
    absence_type='deployment',
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 1),
    is_blocking_override=None
)
***REMOVED*** Returns: True (always blocks)

***REMOVED*** Check for assignments during blocking absence
assigned_dates = [date(2025, 1, 5), date(2025, 1, 10)]

violation = validator.validate_no_assignment_during_block(
    person_id=resident_uuid,
    absence_id=leave_uuid,
    absence_type='deployment',
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 1),
    assigned_dates=assigned_dates,
    is_blocking=None
)

if violation:
    print(f"ERROR: {len(violation.conflict_dates)} assignments during blocked absence")

***REMOVED*** Conditional blocking examples
***REMOVED*** Medical leave:
***REMOVED*** - ≤7 days: Does NOT block (minor procedure/illness)
***REMOVED*** - >7 days: Blocks (extended recovery)

***REMOVED*** Sick leave:
***REMOVED*** - ≤3 days: Does NOT block (minor illness, can work)
***REMOVED*** - >3 days: Blocks (extended illness)
```

***REMOVED******REMOVED******REMOVED*** Blocking Behavior

**Always Blocking:**
- `deployment`, `tdy`, `family_emergency`, `bereavement`
- `emergency_leave`, `maternity_paternity`, `convalescent`

**Non-Blocking:**
- `vacation`, `conference`

**Duration-Based:**
- `medical`: Blocks if > 7 days
- `sick`: Blocks if > 3 days

***REMOVED******REMOVED******REMOVED*** Return Types

**LeaveViolation:**
```python
@dataclass
class LeaveViolation:
    person_id: UUID
    violation_type: str  ***REMOVED*** "assignment_during_block", "expired_return_date"
    severity: str  ***REMOVED*** "CRITICAL", "HIGH"
    message: str
    absence_id: UUID
    conflict_dates: list[date]
```

---

***REMOVED******REMOVED*** 5. Rotation Validator

**File:** `rotation_validator.py`

***REMOVED******REMOVED******REMOVED*** Purpose
Validates rotation requirements and educational progression.

***REMOVED******REMOVED******REMOVED*** Implements
- **Minimum Length:** ≥7 days per rotation
- **PGY-Level Requirements:** Minimum clinic blocks per level
- **Specialty Rotations:** Required exposure for PGY-2/3
- **Procedure Volume:** Hands-on procedure tracking
- **Rotation Sequence:** Order and spacing of rotations
- **Educational Milestones:** Competency assessment

***REMOVED******REMOVED******REMOVED*** Key Classes

***REMOVED******REMOVED******REMOVED******REMOVED*** `RotationValidator`

```python
from app.scheduling.validators import RotationValidator

validator = RotationValidator()

***REMOVED*** Minimum rotation length
violation = validator.validate_minimum_rotation_length(
    person_id=resident_uuid,
    rotation_name='FMIT',
    start_date=date(2025, 1, 1),
    end_date=date(2025, 1, 5)  ***REMOVED*** Only 5 days - too short!
)
***REMOVED*** Returns: RotationViolation (minimum is 7 days)

***REMOVED*** PGY-level clinic requirements
***REMOVED*** PGY-1: Minimum 8 clinic blocks
***REMOVED*** PGY-2: Minimum 8 clinic blocks
***REMOVED*** PGY-3: Minimum 6 clinic blocks

violation = validator.validate_pgy_level_clinic_requirements(
    person_id=resident_uuid,
    pgy_level=1,
    clinic_blocks_completed=6  ***REMOVED*** Only 6 of 8 required
)

***REMOVED*** Procedure volume tracking
violation, warning = validator.validate_procedure_volume(
    person_id=resident_uuid,
    pgy_level=2,
    procedures_completed=25  ***REMOVED*** Target is 30 for PGY-2
)
***REMOVED*** Returns: warning (approaching but not yet below 60% threshold)

***REMOVED*** Annual summary
summary = validator.get_annual_rotation_summary(
    person_id=resident_uuid,
    pgy_level=2,
    completed_rotations=[
        {'rotation_type': 'Clinic', 'blocks': 8},
        {'rotation_type': 'Specialty', 'blocks': 6},
        {'rotation_type': 'Inpatient', 'blocks': 8},
    ],
    total_blocks_available=26
)

print(f"Diversity score: {summary['diversity_score']}")  ***REMOVED*** Number of rotation types
print(f"Utilization: {summary['utilization_rate']:.1%}")
```

***REMOVED******REMOVED******REMOVED*** PGY-Level Requirements

| Requirement | PGY-1 | PGY-2 | PGY-3 |
|-------------|-------|-------|-------|
| Min Clinic Blocks | 8 | 8 | 6 |
| Min Specialty | N/A | 6 | 6 |
| Min Procedures | 20 | 30 | 50 |
| Min FMIT | Varies | Varies | Varies |

***REMOVED******REMOVED******REMOVED*** Return Types

**RotationViolation:**
```python
@dataclass
class RotationViolation:
    person_id: UUID
    violation_type: str  ***REMOVED*** "minimum_length", "missing_required", "volume_shortfall"
    severity: str  ***REMOVED*** "CRITICAL", "HIGH", "MEDIUM"
    message: str
    rotation_name: str
    actual_value: int | float
    required_value: int | float
```

---

***REMOVED******REMOVED*** 6. ACGME Compliance Engine

**File:** `acgme_compliance_engine.py`

***REMOVED******REMOVED******REMOVED*** Purpose
Orchestrates all validators into unified compliance system.

***REMOVED******REMOVED******REMOVED*** Key Classes

***REMOVED******REMOVED******REMOVED******REMOVED*** `ACGMEComplianceEngine`

```python
from app.scheduling.acgme_compliance_engine import ACGMEComplianceEngine
from datetime import date

engine = ACGMEComplianceEngine()

***REMOVED*** Validate entire schedule
schedule_data = {
    'residents': [
        {'id': uuid4(), 'pgy_level': 1, 'type': 'resident'},
        {'id': uuid4(), 'pgy_level': 2, 'type': 'resident'},
    ],
    'assignments': [
        {'person_id': ..., 'block_id': ..., 'rotation_name': 'FMIT'},
        ***REMOVED*** ... more assignments
    ],
    'blocks': [
        {'id': uuid4(), 'date': date(2025, 1, 1)},
        ***REMOVED*** ... more blocks
    ],
    'call_assignments': {
        resident_uuid: [{'date': date(2025, 1, 1)}],
        ***REMOVED*** ... more calls
    },
    'leave_records': {
        resident_uuid: [
            {
                'id': uuid4(),
                'type': 'vacation',
                'start_date': date(2025, 1, 15),
                'end_date': date(2025, 1, 22),
                'is_blocking': False,
            }
        ],
        ***REMOVED*** ... more leave
    }
}

report = engine.validate_complete_schedule(
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31),
    schedule_data=schedule_data
)

***REMOVED*** Access results
print(f"Compliance: {report.compliance_percentage:.1f}%")
print(f"Critical violations: {report.critical_violations_count}")
print(f"High violations: {report.high_violations_count}")

***REMOVED*** By resident
for resident_id, result in report.by_resident.items():
    if not result.is_compliant:
        print(f"Resident {resident_id}:")
        for suggestion in result.remediation_suggestions:
            print(f"  - {suggestion}")

***REMOVED*** Generate dashboard data
dashboard = engine.generate_compliance_dashboard_data(report)
```

***REMOVED******REMOVED******REMOVED*** Return Types

**ComplianceCheckResult:**
```python
@dataclass
class ComplianceCheckResult:
    person_id: UUID
    check_date: date
    is_compliant: bool
    critical_violations: int
    high_violations: int
    medium_violations: int
    warnings: int
    violations_by_domain: dict
    warnings_by_domain: dict
    remediation_suggestions: list[str]
    last_updated: Optional[date]
```

**ScheduleValidationReport:**
```python
@dataclass
class ScheduleValidationReport:
    period_start: date
    period_end: date
    total_residents: int
    residents_compliant: int
    compliance_percentage: float
    critical_violations_count: int
    high_violations_count: int
    by_resident: dict
    by_domain: dict
    executive_summary: str
```

---

***REMOVED******REMOVED*** Usage Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Validate New Assignment

```python
from app.scheduling.validators import LeaveValidator

validator = LeaveValidator()

***REMOVED*** Before committing new assignment
is_valid, reasons = engine.validate_single_assignment(
    assignment_data={'block_date': date(2025, 1, 15)},
    person_id=resident_uuid,
    pgy_level=2,
    existing_assignments=[...],
    leave_records=[...]
)

if is_valid:
    ***REMOVED*** Commit assignment to database
    pass
else:
    for reason in reasons:
        print(f"Cannot assign: {reason}")
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Post-Schedule Validation

```python
from app.scheduling.acgme_compliance_engine import ACGMEComplianceEngine

engine = ACGMEComplianceEngine()

report = engine.validate_complete_schedule(
    period_start=date(2025, 1, 1),
    period_end=date(2025, 1, 31),
    schedule_data=schedule_data
)

***REMOVED*** Generate reports
if report.compliance_percentage < 95:
    print(f"WARNING: {100 - report.compliance_percentage:.1f}% of residents "
          f"have compliance issues")

    ***REMOVED*** Export to database
    compliance_report = ComplianceReport(
        schedule_id=...,
        period_start=report.period_start,
        period_end=report.period_end,
        compliance_percentage=report.compliance_percentage,
        critical_violations=report.critical_violations_count,
        report_json=json.dumps(report.by_resident),
        created_at=datetime.now(),
    )
    db.add(compliance_report)
    db.commit()
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Real-Time Monitoring

```python
from app.scheduling.validators import WorkHourValidator

validator = WorkHourValidator()

***REMOVED*** Check resident's current hours status
violations, warnings = validator.validate_80_hour_rolling_average(
    person_id=resident_uuid,
    hours_by_date=hours_dict
)

***REMOVED*** Determine alert level
level = validator.create_violation_notification_level(current_average_hours)

if level == 'red':
    ***REMOVED*** Send critical alert
    send_alert(f"Resident {resident_id} at 80-hour limit")
elif level == 'orange':
    ***REMOVED*** Send warning
    send_alert(f"Resident {resident_id} at 78 hours")
elif level == 'yellow':
    ***REMOVED*** Send info
    send_alert(f"Resident {resident_id} at 75 hours")
```

---

***REMOVED******REMOVED*** Testing

All validators have comprehensive unit tests in:
```
backend/tests/validators/test_acgme_validators_comprehensive.py
```

**Run tests:**
```bash
cd backend
pytest tests/validators/test_acgme_validators_comprehensive.py -v
```

**Test coverage includes:**
- Core compliance rule validation
- Edge cases and boundary conditions
- Data validation
- Violation severity classification
- Integration scenarios

---

***REMOVED******REMOVED*** Integration with Scheduling Engine

The validators integrate with the schedule generation/validation workflow:

```
Schedule Generation
        ↓
   Solver Creates Assignments
        ↓
   Pre-Commit Validation (validate_single_assignment)
        ↓
   Post-Schedule Validation (validate_complete_schedule)
        ↓
   Generate Compliance Report
        ↓
   Export to Dashboard
```

---

***REMOVED******REMOVED*** Performance Considerations

- **80-hour rolling average:** O(N²) where N = days in period (28-365)
- **Supervision validation:** O(B) where B = number of blocks
- **Call equity:** O(F²) where F = number of faculty
- **Leave checking:** O(A) where A = number of absences

**Optimization:**
- Cache blocking leave dates
- Pre-index assignments by person/block
- Use window-based calculations for rolling averages

---

***REMOVED******REMOVED*** Future Enhancements

1. **Machine Learning:** Predict compliance issues from historical patterns
2. **Optimization:** Suggest swap candidates to fix violations
3. **Alerts:** Proactive notifications when approaching limits
4. **Reporting:** Export compliance evidence for ACGME audits
5. **Analytics:** Track compliance trends over time

---

***REMOVED******REMOVED*** References

- **ACGME Common Program Requirements:** Section VI (Fatigue Mitigation and Duty Hours)
- **Existing Constraints:** `/backend/app/services/constraints/acgme.py`
- **Database Models:** `/backend/app/models/`
- **API Integration:** `/backend/app/api/routes/schedules.py`

---

**Validation System Status:** ✅ Production Ready
