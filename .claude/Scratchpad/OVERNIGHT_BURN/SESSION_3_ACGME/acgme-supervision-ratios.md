# ACGME Supervision Ratio Requirements
## Comprehensive Enforcement & Audit Documentation

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Target System:** Autonomous Assignment Program Manager (Residency Scheduler)

---

## Executive Summary

The ACGME supervision ratio constraint is a **HARD constraint** that ensures faculty-to-resident ratios meet regulatory requirements based on PGY level. Violations indicate inadequate patient safety oversight and regulatory non-compliance. This document provides the complete specification, calculation methodology, exception handling, and audit procedures.

---

## Table of Contents

1. [Ratio Requirements by PGY Level](#ratio-requirements-by-pgy-level)
2. [Calculation Algorithm](#calculation-algorithm)
3. [Exception Handling](#exception-handling)
4. [Audit Procedures](#audit-procedures)
5. [Implementation Details](#implementation-details)
6. [Violation Detection & Reporting](#violation-detection--reporting)
7. [Edge Cases & Gotchas](#edge-cases--gotchas)

---

## Ratio Requirements by PGY Level

### Primary Ratios

| PGY Level | Ratio | Max Residents per Faculty | Supervision Load |
|-----------|-------|--------------------------|------------------|
| **PGY-1** (Intern) | 1:2 | 2 residents | 0.5 per resident |
| **PGY-2/3** (Senior) | 1:4 | 4 residents | 0.25 per resident |

### ACGME Authority

**ACGME Reference:**
Common Program Requirements, Section VI.B:
> "The program must demonstrate that the appropriate level of supervision is in place for all residents who care for patients."

### Clinical Rationale

- **PGY-1 (Interns)**: First year of clinical training; require more direct oversight to ensure:
  - Safe patient care during early independent work
  - Educational assessment and feedback
  - Immediate faculty availability for clinical decisions

- **PGY-2/3 (Senior Residents)**: Established clinical competency; require oversight for:
  - Complex case management and escalation
  - Educational milestones and procedure credentialing
  - Program accreditation compliance

---

## Calculation Algorithm

### Step 1: Count Residents by PGY Level per Block

For each clinical block assignment set, count:
```
pgy1_count = number of residents with pgy_level == 1
other_count = total residents - pgy1_count
```

### Step 2: Calculate Required Faculty

The system uses a **fractional load approach** to avoid overcounting in mixed PGY scenarios:

#### Formula A: Fractional Load (Recommended)

```python
def calculate_required_faculty(pgy1_count: int, other_count: int) -> int:
    """
    Calculate required faculty using fractional supervision units.

    Algorithm:
    1. PGY-1 residents = 2 supervision units each (1:2 ratio)
    2. PGY-2/3 residents = 1 supervision unit each (1:4 ratio)
    3. Sum all units
    4. Apply ceiling division by 4
    5. Return max(1, result) if any residents, else 0
    """
    supervision_units = (pgy1_count * 2) + other_count
    return (supervision_units + 3) // 4 if supervision_units > 0 else 0
```

#### Formula B: Separate Ceiling (Legacy/Alternative)

```python
def calculate_required_faculty_separate(pgy1_count: int, other_count: int) -> int:
    """
    Alternative: Calculate each ratio separately, then sum.
    Results in same outcome but different implementation path.
    """
    from_pgy1 = (pgy1_count + 1) // 2  # Ceiling division
    from_other = (other_count + 3) // 4  # Ceiling division
    return max(1, from_pgy1 + from_other) if (pgy1_count + other_count) > 0 else 0
```

### Examples

| PGY-1 | PGY-2/3 | Calculation | Result | Verification |
|-------|---------|-------------|--------|--------------|
| 0 | 0 | No residents | 0 | No supervision required |
| 1 | 0 | 1×2=2 units, ⌈2/4⌉=1 | 1 faculty | 1 faculty : 1 PGY-1 ✓ |
| 2 | 0 | 2×2=4 units, ⌈4/4⌉=1 | 1 faculty | 1 faculty : 2 PGY-1 ✓ |
| 3 | 0 | 3×2=6 units, ⌈6/4⌉=2 | 2 faculty | 1 faculty : 1.5 PGY-1 (ceiling) ✓ |
| 4 | 0 | 4×2=8 units, ⌈8/4⌉=2 | 2 faculty | 1 faculty : 2 PGY-1 ✓ |
| 0 | 1 | 1 unit, ⌈1/4⌉=1 | 1 faculty | 1 faculty : 1 PGY-2 ✓ |
| 0 | 4 | 4 units, ⌈4/4⌉=1 | 1 faculty | 1 faculty : 4 PGY-2 ✓ |
| 0 | 5 | 5 units, ⌈5/4⌉=2 | 2 faculty | 1 faculty : 2.5 PGY-2 (ceiling) ✓ |
| **1** | **1** | 2+1=3 units, ⌈3/4⌉=1 | **1 faculty** | Mixed supervision (key case!) |
| **2** | **2** | 4+2=6 units, ⌈6/4⌉=2 | **2 faculty** | Adequate for both levels |
| **3** | **4** | 6+4=10 units, ⌈10/4⌉=3 | **3 faculty** | Complex scenario |

### Critical Case: Mixed PGY Levels

The fractional load approach prevents **supervision overcounting** in mixed scenarios:

**Incorrect approach (overcounting):**
```
3 PGY-1 alone needs ⌈3/2⌉ = 2 faculty
4 PGY-2 alone needs ⌈4/4⌉ = 1 faculty
Total: 2 + 1 = 3 (WRONG - allows one faculty to span both groups)
```

**Correct approach (fractional):**
```
3 PGY-1 = 6 supervision units
4 PGY-2 = 4 supervision units
Total = 10 units ÷ 4 = ⌈2.5⌉ = 3 faculty (CORRECT)
```

---

## Exception Handling

### Scenarios Requiring Special Treatment

#### 1. Zero Residents per Block

**Rule:** If a block has no residents, supervision requirement = 0

**Code:**
```python
if pgy1_count == 0 and other_count == 0:
    return 0  # No supervision needed
```

#### 2. No Faculty Available

**Rule:** Blocks with residents but zero faculty trigger **CRITICAL violation**

**Severity:** CRITICAL (Patient safety risk)

**Reporting:** Flag for immediate attention in compliance reports

#### 3. Partial Supervision Coverage

**Rule:** If actual faculty < required faculty, this is a violation

**Examples:**
- Block needs 2 faculty, has only 1 → **CRITICAL violation**
- Block needs 1 faculty, has only 0 → **CRITICAL violation**

#### 4. Excess Faculty (Over-staffing)

**Rule:** More faculty than required is **acceptable** (not a violation)

**Clinical Rationale:** Over-supervision improves patient safety and education

#### 5. Faculty Unable to Supervise (PGY-2/3 as Supervising Faculty)

**Current Implementation:** Any person with `type == "faculty"` is eligible to supervise

**Caveat:** PGY-2/3 residents can **supervise learners** (e.g., medical students) but are supervised by faculty

**Supervision Hierarchy:**
- Faculty supervises residents
- Residents (PGY-2/3) can supervise learners/students
- PGY-1 cannot supervise anyone

---

## Audit Procedures

### 1. Per-Block Audit

**Purpose:** Validate supervision ratios for each clinical block

**Procedure:**

```python
def audit_block_supervision(block_id: UUID, assignments: list[Assignment]) -> dict:
    """
    Audit a single block's supervision compliance.

    Returns:
        {
            'block_id': UUID,
            'block_date': date,
            'residents': [Assignment],
            'faculty': [Assignment],
            'pgy1_count': int,
            'pgy2_3_count': int,
            'required_faculty': int,
            'actual_faculty': int,
            'compliant': bool,
            'deficit': int,  # Required - Actual (0 if compliant)
        }
    """
    # 1. Separate residents from faculty
    residents = [a for a in assignments if a.person.type == 'resident']
    faculty = [a for a in assignments if a.person.type == 'faculty']

    # 2. Count PGY levels
    pgy1_residents = [r for r in residents if r.person.pgy_level == 1]
    other_residents = [r for r in residents if r.person.pgy_level > 1]

    # 3. Calculate requirement
    required = calculate_required_faculty(len(pgy1_residents), len(other_residents))
    actual = len(faculty)

    # 4. Determine compliance
    compliant = actual >= required
    deficit = max(0, required - actual)

    return {
        'block_id': block_id,
        'residents': len(residents),
        'pgy1_count': len(pgy1_residents),
        'pgy2_3_count': len(other_residents),
        'required_faculty': required,
        'actual_faculty': actual,
        'compliant': compliant,
        'deficit': deficit,
    }
```

### 2. Period-Wide Supervision Audit

**Purpose:** Calculate overall supervision compliance metrics

**Procedure:**

```python
def audit_period_supervision(
    start_date: date,
    end_date: date,
    db_session
) -> dict:
    """
    Audit supervision compliance across entire period.

    Returns:
        {
            'period': {'start': date, 'end': date},
            'total_blocks': int,
            'blocks_with_violations': int,
            'compliance_rate': float,  # % (0-100)
            'violations': [
                {
                    'block_id': UUID,
                    'block_date': date,
                    'residents': int,
                    'pgy1_count': int,
                    'faculty': int,
                    'required': int,
                    'deficit': int,
                }
            ]
        }
    """
    # 1. Get all assignments in period
    assignments = db_session.query(Assignment).filter(
        Assignment.block.has(Block.date >= start_date),
        Assignment.block.has(Block.date <= end_date),
    ).all()

    # 2. Group by block
    by_block = defaultdict(list)
    for assignment in assignments:
        by_block[assignment.block_id].append(assignment)

    # 3. Audit each block
    total_blocks = len(by_block)
    violations = []

    for block_id, block_assignments in by_block.items():
        audit_result = audit_block_supervision(block_id, block_assignments)

        if not audit_result['compliant']:
            violations.append(audit_result)

    # 4. Calculate metrics
    blocks_with_violations = len(violations)
    compliance_rate = (
        (total_blocks - blocks_with_violations) / total_blocks * 100
        if total_blocks > 0
        else 100.0
    )

    return {
        'period': {'start': start_date, 'end': end_date},
        'total_blocks': total_blocks,
        'blocks_with_violations': blocks_with_violations,
        'compliance_rate': compliance_rate,
        'violations': violations,
    }
```

### 3. Violation Severity Classification

| Scenario | Severity | Action Required |
|----------|----------|-----------------|
| Required faculty > Actual faculty | **CRITICAL** | Immediate correction required |
| Deficit = 1 faculty | HIGH | Must address within 24 hours |
| Deficit >= 2 faculty | CRITICAL | Halt assignments; escalate immediately |
| Excess faculty | ✓ ACCEPTABLE | No action needed |
| No residents in block | ✓ ACCEPTABLE | Supervision not applicable |

### 4. Audit Reporting Format

**Location:** `backend/app/compliance/reports.py` → `_calculate_supervision_summary()`

**Output Fields:**
```python
{
    'total_blocks': int,                    # Total blocks analyzed
    'blocks_with_violations': int,          # Blocks with inadequate supervision
    'supervision_violations': [             # Detailed violation list
        {
            'block_id': str,
            'block_date': str,              # ISO format
            'residents': int,               # Total residents
            'pgy1_count': int,              # PGY-1 residents
            'faculty': int,                 # Actual faculty
            'required_faculty': int,        # Minimum required
            'deficit': int,                 # Required - Actual
        }
    ],
    'compliance_rate': float,               # Percentage (0-100)
}
```

### 5. Automated Audit Triggers

The system audits supervision ratios:

1. **After Schedule Generation**: Validates initial compliance
2. **After Swap Execution**: Verifies swaps don't violate ratios
3. **After Absence Approval**: Recalculates with reduced faculty/residents
4. **During Conflict Resolution**: Checks proposed assignments
5. **Nightly Background Task**: Continuous compliance monitoring

---

## Implementation Details

### Code Locations

| Component | File Path |
|-----------|-----------|
| **Constraint Class** | `backend/app/scheduling/constraints.py` (lines 885-1022) |
| **Service Validator** | `backend/app/services/constraints/acgme.py` (lines 733-860) |
| **Compliance Reporter** | `backend/app/compliance/reports.py` (lines 434-508) |
| **Test Suite** | `backend/tests/test_constraints.py` (lines 299-381) |

### Constraint Registration

**In Scheduling Engine:**
```python
class ACGMEConstraintValidator:
    def __init__(self):
        self.constraints = [
            AvailabilityConstraint(),
            EightyHourRuleConstraint(),
            OneInSevenRuleConstraint(),
            SupervisionRatioConstraint(),  # ← Registered here
        ]
```

### Validation Entry Points

#### 1. Post-Generation Validation
```python
# After schedule generation completes
validator = ACGMEConstraintValidator()
result = validator.validate_supervision(assignments, context)
if not result.satisfied:
    log_violations(result.violations)
```

#### 2. Assignment Validation
```python
# Before committing new assignments
supervisor_ratio = SupervisionRatioConstraint()
result = supervisor_ratio.validate(proposed_assignments, context)
if len(result.violations) > 0:
    raise ComplianceError(f"Supervision violation: {result.violations[0]}")
```

#### 3. Swap Validation
```python
# After swap execution
existing_assignments = get_block_assignments(block_id)
proposed_assignments = existing_assignments + new_assignments - removed_assignments
result = SupervisionRatioConstraint().validate(proposed_assignments, context)
if not result.satisfied:
    rollback_swap()
```

---

## Violation Detection & Reporting

### Violation Structure

```python
@dataclass
class ConstraintViolation:
    constraint_name: str        # "SupervisionRatio"
    constraint_type: str        # "supervision"
    severity: str               # "CRITICAL"
    message: str                # "Block needs 2 faculty but has 1"
    block_id: UUID | None       # Block where violation occurs
    details: dict = {           # Rich context
        'residents': 2,
        'pgy1_count': 2,
        'faculty': 1,
        'required': 2,
    }
```

### Violation Message Examples

```
Block needs 2 faculty but has 1 (2 residents)
    → Block 2025-12-30-AM
    → Has: 2 PGY-1 residents
    → Has: 1 faculty member
    → Requires: 2 faculty minimum

Block needs 1 faculty but has 0 (1 resident)
    → Block 2025-12-31-PM
    → Has: 1 PGY-2 resident
    → Has: 0 faculty members
    → Requires: 1 faculty minimum
    → CRITICAL: Patient safety risk!
```

### Reporting Integration

**Compliance Report Sections:**
- `supervision_summary.compliance_rate` → Overall ratio compliance %
- `supervision_summary.blocks_with_violations` → Count of non-compliant blocks
- `supervision_summary.supervision_violations` → Detailed violation list

**MCP Tools Output:**
```python
# From scheduler_mcp/resources.py
{
    'supervision_violations': 5,
    'recommendations': [
        "Increase faculty coverage on 5 block(s) with inadequate supervision ratios"
    ]
}
```

---

## Edge Cases & Gotchas

### 1. Faculty Type Ambiguity

**Issue:** PGY-2/3 residents can supervise learners but are supervised by faculty

**Current Implementation:** Treats all `type == 'faculty'` as eligible to supervise

**Implication:** A PGY-3 resident in a block might be counted as both resident (requiring supervision) AND faculty (providing supervision)

**Mitigation:**
```python
def is_supervising_faculty(person):
    """Check if person is eligible to supervise residents."""
    return person.type == 'faculty' and person.role != 'learner'
```

### 2. Partial Blocks (Multiple Sessions)

**Issue:** Some blocks split into AM/PM sessions

**Current Behavior:** Each session audited independently for supervision ratios

**Example:**
```
Block 2025-12-30:
  - AM (Clinic): 2 PGY-1, 1 faculty ✓
  - PM (Procedure): 1 PGY-1, 1 faculty ✓
```

Both sessions compliant individually.

### 3. Shift Boundaries

**Issue:** Faculty may transition between blocks; ratio may appear violated at shift boundaries

**Current Handling:** Each block evaluated independently at time of audit

**Consideration:** May need overlap buffer for coverage continuity

### 4. Off-Service Rotations

**Issue:** Residents rotated off-service may not have designated supervising faculty in block

**Current Behavior:** These residents still counted in supervision requirements

**Recommendation:** Tag off-service assignments to exclude from supervision audits

### 5. Zero-Resident Blocks

**Issue:** Administrative blocks (faculty only) incorrectly audited

**Current Handling:** Skip supervision check if `residents` list empty

**Code:**
```python
if not residents:
    continue  # No supervision required for faculty-only blocks
```

### 6. Rounding & Ceiling Arithmetic

**Issue:** Integer ceiling division can be unintuitive

**Examples:**
```
⌈3/2⌉ = (3 + 1) // 2 = 2  ✓
⌈5/4⌉ = (5 + 3) // 4 = 2  ✓
⌈1/2⌉ = (1 + 1) // 2 = 1  ✓
```

**Ensure consistent use of `(n + divisor - 1) // divisor` pattern**

### 7. PGY Level == None

**Issue:** Faculty or unclassified personnel have `pgy_level = None`

**Current Handling:** Checked explicitly in ratio calculation

**Code:**
```python
pgy1_count = sum(1 for r in residents if pgy_levels.get(r) == 1)
```

---

## Test Coverage

### Unit Tests

Located: `backend/tests/test_constraints.py` (lines 299-381)

```python
class TestSupervisionRatioConstraint:

    def test_calculate_required_faculty():
        """Test faculty calculation for various scenarios."""
        assert constraint.calculate_required_faculty(0, 0) == 0
        assert constraint.calculate_required_faculty(1, 0) == 1
        assert constraint.calculate_required_faculty(2, 0) == 1
        assert constraint.calculate_required_faculty(3, 0) == 2

    def test_calculate_required_faculty_mixed():
        """Test fractional load approach (key fix)."""
        # 1 PGY-1 + 1 PGY-2 = 0.5 + 0.25 = 0.75 → ceil = 1
        assert constraint.calculate_required_faculty(1, 1) == 1

        # 3 PGY-1 + 4 PGY-2/3 = 6 + 4 = 10 units → 10/4 = 2.5 → 3
        assert constraint.calculate_required_faculty(3, 4) == 3

    def test_validate_adequate_supervision():
        """Test validation with adequate faculty."""
        # Block with 1 PGY-1 + 1 faculty → compliant
        assignments = [
            Assignment(person=pgy1_resident, block=block),
            Assignment(person=faculty, block=block),
        ]
        result = constraint.validate(assignments, context)
        assert result.satisfied is True
```

### Integration Tests

Covers:
- Schedule generation with supervision constraints
- Swap execution with re-validation
- Absence approval impact on ratios
- ACGME enforcement scenarios

---

## Enforcement Timeline

| Event | Action | Timing |
|-------|--------|--------|
| **Schedule Generation** | Validate supervision ratios | Before commit to DB |
| **Swap Request** | Re-validate all affected blocks | Before swap approval |
| **Absence Approval** | Recalculate with adjusted faculty/residents | Before absence effective |
| **Nightly Audit** | Generate compliance report | Celery background task |
| **Admin Dashboard** | Display supervision violations | Real-time refresh |
| **Compliance Report** | Include supervision metrics | Monthly/quarterly export |

---

## Regulatory Alignment

### ACGME CPR Reference

**Section VI.B - Supervision**

> The program must ensure that all residents have ready access to appropriate supervision. Faculty must be present and immediately available to residents to ensure patient safety and appropriate training. The number of residents under the supervision of each faculty member must be consistent with the level of training of the residents, the complexity of the patient population, and the structure of the rotation.

### Mapping to Implementation

| ACGME Requirement | Implementation | Validation |
|-------------------|---|---|
| "appropriate supervision" | PGY-1: 1:2, PGY-2/3: 1:4 | SupervisionRatioConstraint |
| "ready access" | Faculty in same block | Assignment validation |
| "patient safety" | CRITICAL severity on violation | Compliance reporting |
| "residents under supervision" | Count all residents per faculty per block | Per-block audit |
| "level of training" | Different ratios per PGY | Formula enforcement |

---

## Monitoring & Alerts

### Dashboard Metrics

```
Supervision Compliance: 94.2%
├── Blocks Analyzed: 1,456
├── Violations Found: 82
└── Blocks Needing Faculty: 82

Violation Breakdown:
├── Deficit = 1: 65 blocks
├── Deficit = 2: 12 blocks
└── Deficit >= 3: 5 blocks
```

### Alert Thresholds

| Condition | Threshold | Alert Type |
|-----------|-----------|-----------|
| Compliance < 95% | Daily | WARNING |
| Any CRITICAL violation | Real-time | CRITICAL |
| Deficit >= 2 on any block | Real-time | CRITICAL |
| Absence approval creates violation | Pre-approval | BLOCKING |

---

## Conclusion

The ACGME supervision ratio constraint is fundamental to patient safety and regulatory compliance. The **fractional load algorithm** ensures accurate calculations in mixed PGY scenarios, preventing both over- and under-staffing. Comprehensive audit procedures, integration with compliance reporting, and real-time violation detection maintain continuous oversight.

**Key Takeaways:**
1. Ratios are **HARD constraints** (violations = invalid schedule)
2. Use **fractional load formula** for mixed PGY calculations
3. Audit **per-block** and **period-wide** for comprehensive coverage
4. Report violations with **specific deficits** for remediation
5. Enforce immediately on schedule generation, swaps, and absences

---

## Appendix: Quick Reference

### Constants
```python
PGY1_RATIO = 2          # 1 faculty per 2 PGY-1
OTHER_RATIO = 4         # 1 faculty per 4 PGY-2/3
CRITICAL_SEVERITY = "CRITICAL"
CONSTRAINT_TYPE = "supervision"
```

### Calculation Formula (Single Line)
```python
required = (pgy1_count * 2 + other_count + 3) // 4 if (pgy1_count + other_count) > 0 else 0
```

### Violation Threshold
```python
if actual_faculty < required_faculty:
    # VIOLATION DETECTED
```

### Audit Query (SQL)
```sql
SELECT
    block_id,
    COUNT(CASE WHEN person.type='resident' AND person.pgy_level=1 THEN 1 END) as pgy1_count,
    COUNT(CASE WHEN person.type='resident' AND person.pgy_level>1 THEN 1 END) as other_count,
    COUNT(CASE WHEN person.type='faculty' THEN 1 END) as faculty_count,
    CEIL((COUNT(CASE WHEN person.pgy_level=1 THEN 1 END)*2 +
          COUNT(CASE WHEN person.pgy_level>1 THEN 1 END) + 3) / 4) as required_faculty
FROM assignments
JOIN person ON assignments.person_id = person.id
GROUP BY block_id
HAVING faculty_count < required_faculty;
```

---

**Document compiled by G2_RECON during SESSION 3 ACGME reconnaissance**
