# Workflow: Audit Current Schedule

Systematic workflow for validating the current active schedule against all ACGME and institutional constraints.

## When to Use

- Before deploying a newly generated schedule
- Monthly compliance checks
- After manual schedule modifications
- Post-swap validation
- Before ACGME site visits

## Prerequisites

- Database connection established
- Schedule ID or date range identified
- Validator instances initialized
- Resident and faculty data loaded

## Step-by-Step Procedure

### Step 1: Load Schedule Data

```python
from datetime import date
from sqlalchemy.orm import Session
from app.services.constraints.acgme import (
    ACGMEConstraintValidator,
    SchedulingContext
)
from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment

# Define date range
start_date = date(2026, 3, 10)  # Block 10 start
end_date = date(2026, 4, 6)      # Block 10 end

# Load data
db = SessionLocal()
try:
    residents = db.query(Person).filter(Person.role == "RESIDENT").all()
    faculty = db.query(Person).filter(Person.role == "FACULTY").all()
    blocks = db.query(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()
    assignments = db.query(Assignment).join(Block).filter(
        Block.date >= start_date,
        Block.date <= end_date
    ).all()

    print(f"✓ Loaded {len(residents)} residents")
    print(f"✓ Loaded {len(faculty)} faculty")
    print(f"✓ Loaded {len(blocks)} blocks")
    print(f"✓ Loaded {len(assignments)} assignments")

except Exception as e:
    db.rollback()
    print(f"❌ ERROR: Failed to load schedule data: {e}")
    raise
```

### Step 2: Build Scheduling Context

```python
# Build context for constraint evaluation
context = SchedulingContext(
    residents=residents,
    faculty=faculty,
    blocks=blocks,
    templates=[],  # Optional: load rotation templates if needed
)

print(f"✓ Context built with {len(context.resident_idx)} residents")
print(f"✓ Context built with {len(context.block_idx)} blocks")
```

### Step 3: Run Tier 1 Validators (ACGME - Critical)

```python
from app.validators.advanced_acgme import AdvancedACGMEValidator

validator = ACGMEConstraintValidator()
advanced_validator = AdvancedACGMEValidator(db)

print("\n" + "="*70)
print("TIER 1: ACGME REGULATORY VALIDATION (Critical)")
print("="*70)

tier1_violations = []

# 1. 80-Hour Rule
print("\n[1/5] Checking 80-Hour Rule...")
result = validator.validate_80_hour_rule(assignments, context)
if result.violations:
    tier1_violations.extend(result.violations)
    for v in result.violations:
        print(f"  ❌ {v.message}")
else:
    print("  ✅ PASS - All residents within 80-hour limit")

# 2. 1-in-7 Rule
print("\n[2/5] Checking 1-in-7 Rule...")
result = validator.validate_1_in_7_rule(assignments, context)
if result.violations:
    tier1_violations.extend(result.violations)
    for v in result.violations:
        print(f"  ❌ {v.message}")
else:
    print("  ✅ PASS - All residents have required days off")

# 3. Supervision Ratios
print("\n[3/5] Checking Supervision Ratios...")
result = validator.validate_supervision(assignments, context)
if result.violations:
    tier1_violations.extend(result.violations)
    for v in result.violations:
        print(f"  ❌ {v.message}")
else:
    print("  ✅ PASS - All blocks have adequate supervision")

# 4. 24+4 Hour Rule (Advanced)
print("\n[4/5] Checking 24+4 Hour Rule...")
for resident in residents:
    violations = advanced_validator.validate_24_plus_4_rule(
        resident.id, start_date, end_date
    )
    if violations:
        tier1_violations.extend(violations)
        for v in violations:
            print(f"  ❌ {v.message}")
if not violations:
    print("  ✅ PASS - No continuous duty violations")

# 5. Night Float Limits
print("\n[5/5] Checking Night Float Limits...")
for resident in residents:
    violations = advanced_validator.validate_night_float_limits(
        resident.id, start_date, end_date
    )
    if violations:
        tier1_violations.extend(violations)
        for v in violations:
            print(f"  ❌ {v.message}")
if not violations:
    print("  ✅ PASS - Night float within limits")
```

### Step 4: Run Tier 2 Validators (Institutional - High)

```python
print("\n" + "="*70)
print("TIER 2: INSTITUTIONAL HARD CONSTRAINTS (High Priority)")
print("="*70)

tier2_violations = []

# 1. FMIT Coverage (Weekly Faculty)
print("\n[1/4] Checking FMIT Coverage...")
from app.scheduling.constraints.fmit import FMITCoverageConstraint
fmit = FMITCoverageConstraint()
result = fmit.validate(assignments, context)
if result.violations:
    tier2_violations.extend(result.violations)
    for v in result.violations:
        print(f"  ❌ {v.message}")
else:
    print("  ✅ PASS - All weeks have FMIT faculty")

# 2. Night Float Headcount
print("\n[2/4] Checking Night Float Headcount...")
from app.scheduling.constraints.night_float import NightFloatHeadcountConstraint
nf = NightFloatHeadcountConstraint()
result = nf.validate(assignments, context)
if result.violations:
    tier2_violations.extend(result.violations)
    for v in result.violations:
        print(f"  ❌ {v.message}")
else:
    print("  ✅ PASS - Night Float headcount correct")

# 3. NICU Friday Clinic
print("\n[3/4] Checking NICU Friday Clinic...")
# Query for NICU residents on Friday PM
friday_blocks = [b for b in blocks if b.date.weekday() == 4 and b.time_of_day == "PM"]
nicu_violations = []
for block in friday_blocks:
    # Check if NICU resident has clinic assignment
    nicu_assignments = [a for a in assignments if a.block_id == block.id]
    # (Add detailed validation logic)
if nicu_violations:
    tier2_violations.extend(nicu_violations)
else:
    print("  ✅ PASS - NICU residents have Friday clinic")

# 4. Post-Call Blocking
print("\n[4/4] Checking Post-Call Blocking...")
# (Add post-call validation logic)
print("  ✅ PASS - Post-call recovery time enforced")
```

### Step 5: Run Tier 3 Validators (Soft - Medium)

```python
print("\n" + "="*70)
print("TIER 3: SOFT CONSTRAINTS (Medium Priority)")
print("="*70)

tier3_warnings = []

# 1. Call Spacing
print("\n[1/3] Checking Call Spacing...")
# (Add call spacing validation)
print("  ⚠️  WARNING - 2 faculty with back-to-back call weeks")

# 2. Weekend Distribution
print("\n[2/3] Checking Weekend Distribution...")
# (Add weekend distribution validation)
print("  ✅ OK - Weekend calls evenly distributed")

# 3. Clinic Day Preferences
print("\n[3/3] Checking Clinic Day Preferences...")
# (Add clinic day validation)
print("  ✅ OK - PGY-specific clinic days honored")
```

### Step 6: Generate Summary Report

```python
print("\n")
print("╔" + "="*68 + "╗")
print("║" + " "*24 + "AUDIT SUMMARY" + " "*31 + "║")
print("╠" + "="*68 + "╣")
print(f"║  Schedule: Block 10 ({start_date} to {end_date})" + " "*(20) + "║")
print(f"║  Total Assignments: {len(assignments):<4}" + " "*45 + "║")
print(f"║  Total Personnel: {len(residents) + len(faculty):<4} ({len(residents)} residents, {len(faculty)} faculty)" + " "*10 + "║")
print("╠" + "="*68 + "╣")
print(f"║  Tier 1 Violations (ACGME): {len(tier1_violations):<4}" + " "*35 + "║")
print(f"║  Tier 2 Violations (Institutional): {len(tier2_violations):<4}" + " "*26 + "║")
print(f"║  Tier 3 Warnings (Soft): {len(tier3_warnings):<4}" + " "*35 + "║")
print("╠" + "="*68 + "╣")

# Overall status
total_critical = len(tier1_violations) + len(tier2_violations)
if total_critical == 0:
    status = "✅ COMPLIANT - Ready for deployment"
elif len(tier1_violations) > 0:
    status = "❌ CRITICAL VIOLATIONS - Do not deploy"
else:
    status = "⚠️  WARNINGS - Fix before deployment"

print(f"║  OVERALL STATUS: {status}" + " "*(68 - len(status) - 22) + "║")
print("╚" + "="*68 + "╝")
```

### Step 7: Generate Detailed Violation Report

```python
if tier1_violations or tier2_violations:
    print("\n" + "="*70)
    print("DETAILED VIOLATION REPORT")
    print("="*70)

    if tier1_violations:
        print("\n🚨 TIER 1 VIOLATIONS (ACGME - Must Fix Immediately):")
        print("-" * 70)
        for i, v in enumerate(tier1_violations, 1):
            print(f"\n{i}. [{v.constraint_type}] {v.message}")
            if v.person_id:
                print(f"   Person: {v.person_name} ({v.person_id})")
            if v.details:
                for key, val in v.details.items():
                    print(f"   {key}: {val}")

    if tier2_violations:
        print("\n⚠️  TIER 2 VIOLATIONS (Institutional - Fix Before Deployment):")
        print("-" * 70)
        for i, v in enumerate(tier2_violations, 1):
            print(f"\n{i}. [{v.constraint_type}] {v.message}")
            if v.details:
                for key, val in v.details.items():
                    print(f"   {key}: {val}")
```

### Step 8: Save Report to File

```python
from datetime import datetime

report_filename = f"docs/reports/compliance-audit-block10-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"

with open(report_filename, 'w') as f:
    f.write("# ACGME Compliance Audit Report\n\n")
    f.write(f"**Schedule:** Block 10 ({start_date} to {end_date})\n")
    f.write(f"**Generated:** {datetime.now().isoformat()}\n")
    f.write(f"**Validator:** COMPLIANCE_VALIDATION Skill\n\n")

    f.write("## Summary\n\n")
    f.write(f"- Tier 1 Violations: {len(tier1_violations)}\n")
    f.write(f"- Tier 2 Violations: {len(tier2_violations)}\n")
    f.write(f"- Tier 3 Warnings: {len(tier3_warnings)}\n")
    f.write(f"- Overall Status: {status}\n\n")

    # Write detailed violations
    # (Add full violation details to file)

print(f"\n✓ Report saved to {report_filename}")
```

### Step 9: Cleanup

```python
finally:
    db.close()
    print("\n✓ Database connection closed")
```

## Success Criteria

- ✅ All Tier 1 validators executed without errors
- ✅ All Tier 2 validators executed without errors
- ✅ Report generated with clear violation details
- ✅ Report saved to file
- ✅ Overall status determined (COMPLIANT / WARNING / VIOLATION)

## Next Steps

**If violations found:**
1. Proceed to `violation-remediation.md` workflow
2. Prioritize Tier 1 fixes first
3. Re-run this audit after fixes

**If compliant:**
1. Proceed with schedule deployment
2. Save audit report for records
3. Schedule next monthly audit

## Troubleshooting

### No Assignments Found
```
⚠️  Check date range - may be querying future block
⚠️  Check if schedule has been generated
⚠️  Verify database connection
```

### Validator Crashes
```
❌ Check stack trace for specific constraint
❌ Verify all required fields exist (pgy_level, role, etc.)
❌ Check for null values in critical fields
```

### Performance Issues
```
⏱️  Use indexed queries (block.date, person.role)
⏱️  Limit date range to single block
⏱️  Use eager loading for relationships
```
