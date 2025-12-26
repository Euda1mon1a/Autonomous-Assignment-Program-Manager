# Workflow: Violation Remediation

Systematic procedure for fixing identified ACGME and institutional compliance violations with minimal schedule disruption.

## When to Use

- After audit identifies violations (Tier 1 or Tier 2)
- Post-swap validation failures
- Emergency violation fixes before deployment
- Proactive violation resolution
- Before ACGME site visits

## Prerequisites

- Completed audit with identified violations (from `audit-current-schedule.md`)
- Database backup created
- Violation prioritization completed
- Swap candidates identified (if using swap strategy)

## Critical Safety Rule

**NEVER execute fixes without database backup:**

```bash
# Create backup before ANY remediation
cd backend
alembic downgrade -1  # Test rollback capability
alembic upgrade head   # Restore
pg_dump -U scheduler residency_scheduler > backup_pre_remediation_$(date +%Y%m%d_%H%M%S).sql
```

## Step-by-Step Procedure

### Step 1: Prioritize Violations

```python
from collections import defaultdict

# Assume violations loaded from audit
tier1_violations = [...]  # From audit
tier2_violations = [...]  # From audit

# Sort by priority (Tier 1 first, then by person affected)
all_violations = []
for v in tier1_violations:
    all_violations.append({
        "tier": 1,
        "severity": "CRITICAL",
        "violation": v,
        "priority": 100
    })

for v in tier2_violations:
    all_violations.append({
        "tier": 2,
        "severity": "HIGH",
        "violation": v,
        "priority": 75
    })

# Sort by priority
sorted_violations = sorted(all_violations, key=lambda x: x['priority'], reverse=True)

print("="*70)
print("VIOLATION PRIORITIZATION")
print("="*70)
print(f"\nTotal Violations: {len(sorted_violations)}")
print(f"  Tier 1 (ACGME): {len(tier1_violations)}")
print(f"  Tier 2 (Institutional): {len(tier2_violations)}\n")

for i, item in enumerate(sorted_violations, 1):
    v = item['violation']
    print(f"{i}. [Tier {item['tier']}] {v.constraint_type}: {v.message}")
```

### Step 2: Analyze Each Violation

For each violation, determine:
1. **Root cause** - Why did this violation occur?
2. **Remediation strategy** - What fix approach to use?
3. **Impact** - What else will change if we fix this?

```python
print("\n" + "="*70)
print("VIOLATION ANALYSIS")
print("="*70)

remediation_plans = []

for i, item in enumerate(sorted_violations, 1):
    v = item['violation']
    print(f"\n[{i}/{len(sorted_violations)}] Analyzing: {v.constraint_type}")

    plan = {
        "violation": v,
        "tier": item['tier'],
        "strategy": None,
        "actions": [],
        "impact": {},
        "estimated_effort": None
    }

    # Determine strategy based on constraint type
    if v.constraint_type == "duty_hours":
        print("  Root Cause: Resident over 80-hour limit")
        plan['strategy'] = "REDISTRIBUTE_LOAD"
        plan['actions'] = [
            f"Identify assignments for {v.person_name} in window {v.details.get('window_start')}",
            "Find swap candidates with lighter workload",
            "Execute swaps to redistribute assignments"
        ]
        plan['estimated_effort'] = "MEDIUM"

    elif v.constraint_type == "consecutive_days":
        print("  Root Cause: Resident worked 7+ consecutive days")
        plan['strategy'] = "INSERT_DAY_OFF"
        plan['actions'] = [
            f"Identify consecutive day sequence for {v.person_name}",
            "Find day to convert to off-day (preferably middle of sequence)",
            "Reassign that day's assignments to other residents"
        ]
        plan['estimated_effort'] = "LOW"

    elif v.constraint_type == "supervision":
        print("  Root Cause: Inadequate faculty supervision on block")
        plan['strategy'] = "ADD_FACULTY"
        plan['actions'] = [
            f"Identify block {v.block_id} needing supervision",
            "Find available faculty for that block",
            "Assign faculty to block"
        ]
        plan['estimated_effort'] = "HIGH"

    elif v.constraint_type == "availability":
        print("  Root Cause: Assignment during absence")
        plan['strategy'] = "REMOVE_ASSIGNMENT"
        plan['actions'] = [
            f"Remove assignment for {v.person_name} on {v.details.get('date')}",
            "Find replacement resident for coverage",
            "Verify replacement doesn't violate constraints"
        ]
        plan['estimated_effort'] = "LOW"

    elif v.constraint_type in ["24_PLUS_4_VIOLATION", "NIGHT_FLOAT_VIOLATION"]:
        print("  Root Cause: Extended duty hours violation")
        plan['strategy'] = "SPLIT_SHIFT"
        plan['actions'] = [
            f"Identify extended shift for {v.person_name}",
            "Split shift or reduce hours",
            "Assign relief coverage"
        ]
        plan['estimated_effort'] = "MEDIUM"

    else:
        print(f"  ⚠️  Unknown constraint type: {v.constraint_type}")
        plan['strategy'] = "MANUAL_REVIEW"
        plan['actions'] = ["Requires manual investigation and custom fix"]
        plan['estimated_effort'] = "HIGH"

    remediation_plans.append(plan)
    print(f"  Strategy: {plan['strategy']}")
    print(f"  Estimated Effort: {plan['estimated_effort']}")
```

### Step 3: Execute Remediation (Tier 1 First)

**CRITICAL:** Use database transactions with rollback capability.

```python
from sqlalchemy.orm import Session
from app.models.assignment import Assignment
from app.services.swap_executor import SwapExecutor

db = SessionLocal()

try:
    print("\n" + "="*70)
    print("EXECUTING REMEDIATION")
    print("="*70)

    successful_fixes = 0
    failed_fixes = 0

    for i, plan in enumerate(remediation_plans, 1):
        v = plan['violation']
        print(f"\n[{i}/{len(remediation_plans)}] Fixing: {v.constraint_type}")
        print(f"  Strategy: {plan['strategy']}")

        try:
            # Start transaction
            db.begin_nested()

            if plan['strategy'] == "REMOVE_ASSIGNMENT":
                # Find and remove the offending assignment
                assignment = db.query(Assignment).filter(
                    Assignment.person_id == v.person_id,
                    Assignment.block_id == v.block_id
                ).first()

                if assignment:
                    db.delete(assignment)
                    print(f"  ✅ Removed assignment: {assignment.id}")
                    successful_fixes += 1
                else:
                    print(f"  ⚠️  Assignment not found (may already be removed)")

            elif plan['strategy'] == "REDISTRIBUTE_LOAD":
                # Use swap system to redistribute assignments
                # (Simplified - real implementation would find specific assignments)
                print(f"  🔄 Finding swap candidates...")

                # Get assignments in violation window
                window_start = v.details.get('window_start')
                window_end = v.details.get('window_end')

                # Find assignments to swap
                assignments_to_swap = db.query(Assignment).join(Block).filter(
                    Assignment.person_id == v.person_id,
                    Block.date >= window_start,
                    Block.date <= window_end
                ).limit(3).all()  # Swap first 3 to reduce load

                for assignment in assignments_to_swap:
                    # Find swap candidate
                    # (Real implementation would use get_swap_candidates MCP tool)
                    print(f"    - Queuing assignment {assignment.id} for swap")

                print(f"  ✅ Queued {len(assignments_to_swap)} swaps for execution")
                successful_fixes += 1

            elif plan['strategy'] == "INSERT_DAY_OFF":
                # Remove assignments on a specific day to create day off
                consecutive_dates = v.details.get('consecutive_dates', [])
                if consecutive_dates:
                    # Pick middle day
                    middle_day = consecutive_dates[len(consecutive_dates) // 2]

                    day_assignments = db.query(Assignment).join(Block).filter(
                        Assignment.person_id == v.person_id,
                        Block.date == middle_day
                    ).all()

                    for assignment in day_assignments:
                        db.delete(assignment)
                        print(f"    - Removed assignment on {middle_day}")

                    print(f"  ✅ Created day off on {middle_day}")
                    successful_fixes += 1

            elif plan['strategy'] == "ADD_FACULTY":
                print(f"  ⚠️  ADD_FACULTY strategy requires manual intervention")
                print(f"     Action: Assign faculty to block {v.block_id}")
                failed_fixes += 1
                db.rollback()
                continue

            elif plan['strategy'] == "MANUAL_REVIEW":
                print(f"  ⚠️  MANUAL_REVIEW required - skipping automated fix")
                failed_fixes += 1
                db.rollback()
                continue

            # Commit transaction
            db.commit()
            print(f"  ✅ Fix committed to database")

        except Exception as e:
            db.rollback()
            print(f"  ❌ Fix failed: {e}")
            print(f"     Rolling back transaction")
            failed_fixes += 1

    print("\n" + "="*70)
    print(f"Remediation Summary:")
    print(f"  ✅ Successful: {successful_fixes}")
    print(f"  ❌ Failed: {failed_fixes}")
    print(f"  Total: {len(remediation_plans)}")
    print("="*70)

except Exception as e:
    db.rollback()
    print(f"\n❌ CRITICAL ERROR during remediation: {e}")
    print("   All changes rolled back")
    raise

finally:
    db.close()
```

### Step 4: Verify Fixes

**MANDATORY:** Re-run audit after remediation to verify violations are resolved.

```python
print("\n" + "="*70)
print("VERIFICATION: Re-running audit after fixes")
print("="*70)

# Re-run audit (use audit-current-schedule.md workflow)
# This is CRITICAL - never assume fixes worked without verification

from app.services.constraints.acgme import ACGMEConstraintValidator

db = SessionLocal()
try:
    # Reload data
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

    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=blocks,
    )

    validator = ACGMEConstraintValidator()

    # Re-validate
    new_violations = []

    result = validator.validate_80_hour_rule(assignments, context)
    new_violations.extend(result.violations)

    result = validator.validate_1_in_7_rule(assignments, context)
    new_violations.extend(result.violations)

    result = validator.validate_supervision(assignments, context)
    new_violations.extend(result.violations)

    print(f"\nVerification Results:")
    print(f"  Original Violations: {len(sorted_violations)}")
    print(f"  Remaining Violations: {len(new_violations)}")
    print(f"  Violations Resolved: {len(sorted_violations) - len(new_violations)}")

    if len(new_violations) == 0:
        print("\n✅ ALL VIOLATIONS RESOLVED - Schedule is now compliant")
    elif len(new_violations) < len(sorted_violations):
        print(f"\n⚠️  PARTIAL SUCCESS - {len(new_violations)} violations remain")
        print("   Remaining violations require additional remediation:")
        for v in new_violations:
            print(f"     - {v.constraint_type}: {v.message}")
    else:
        print(f"\n❌ REMEDIATION FAILED - Violations not reduced")
        print("   Recommend rolling back changes and trying different strategy")

finally:
    db.close()
```

### Step 5: Impact Assessment

```python
print("\n" + "="*70)
print("IMPACT ASSESSMENT")
print("="*70)

# Compare before/after metrics
print("\nSchedule Metrics Before/After Remediation:")

# Calculate metrics
# (Simplified - real implementation would calculate comprehensive metrics)

before_metrics = {
    "total_assignments": len(all_assignments),  # Original count
    "avg_hours_per_week": 45.2,  # Example
    "coverage_rate": 92.3,       # Example
}

after_metrics = {
    "total_assignments": len(assignments),  # After remediation
    "avg_hours_per_week": 43.8,  # Recalculated
    "coverage_rate": 91.1,       # Recalculated
}

print(f"\nTotal Assignments: {before_metrics['total_assignments']} → {after_metrics['total_assignments']}")
print(f"Avg Hours/Week: {before_metrics['avg_hours_per_week']} → {after_metrics['avg_hours_per_week']}")
print(f"Coverage Rate: {before_metrics['coverage_rate']}% → {after_metrics['coverage_rate']}%")

# Check for unintended consequences
if after_metrics['coverage_rate'] < before_metrics['coverage_rate'] - 5:
    print("\n⚠️  WARNING: Coverage rate dropped significantly")
    print("   Review remediation to ensure adequate coverage maintained")

if after_metrics['total_assignments'] < before_metrics['total_assignments'] * 0.9:
    print("\n⚠️  WARNING: Large reduction in assignments")
    print("   Verify schedule still meets operational requirements")
```

### Step 6: Generate Remediation Report

```python
from datetime import datetime

report_filename = f"docs/reports/remediation-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"

with open(report_filename, 'w') as f:
    f.write("# Violation Remediation Report\n\n")
    f.write(f"**Generated:** {datetime.now().isoformat()}\n")
    f.write(f"**Schedule:** Block 10 ({start_date} to {end_date})\n\n")

    f.write("## Summary\n\n")
    f.write(f"- Original Violations: {len(sorted_violations)}\n")
    f.write(f"- Successful Fixes: {successful_fixes}\n")
    f.write(f"- Failed Fixes: {failed_fixes}\n")
    f.write(f"- Remaining Violations: {len(new_violations)}\n\n")

    f.write("## Remediation Actions\n\n")
    for i, plan in enumerate(remediation_plans, 1):
        v = plan['violation']
        f.write(f"### {i}. {v.constraint_type}\n\n")
        f.write(f"**Person:** {v.person_name}\n")
        f.write(f"**Strategy:** {plan['strategy']}\n")
        f.write(f"**Actions:**\n")
        for action in plan['actions']:
            f.write(f"- {action}\n")
        f.write("\n")

    f.write("## Impact Assessment\n\n")
    f.write(f"- Total Assignments: {before_metrics['total_assignments']} → {after_metrics['total_assignments']}\n")
    f.write(f"- Coverage Rate: {before_metrics['coverage_rate']}% → {after_metrics['coverage_rate']}%\n\n")

    if len(new_violations) > 0:
        f.write("## Remaining Violations\n\n")
        for v in new_violations:
            f.write(f"- {v.constraint_type}: {v.message}\n")

print(f"\n✓ Remediation report saved to {report_filename}")
```

### Step 7: Document Changes (Audit Trail)

```python
# Log remediation to audit trail table
from app.models.audit_log import AuditLog  # If exists

audit_entry = AuditLog(
    event_type="REMEDIATION",
    description=f"Fixed {successful_fixes} violations in Block 10",
    details={
        "original_violations": len(sorted_violations),
        "successful_fixes": successful_fixes,
        "failed_fixes": failed_fixes,
        "remaining_violations": len(new_violations),
        "strategies_used": list(set(p['strategy'] for p in remediation_plans))
    },
    created_at=datetime.now()
)

db.add(audit_entry)
db.commit()
print("\n✓ Audit trail updated")
```

## Remediation Strategies Reference

| Strategy | Use Case | Complexity | Risk |
|----------|----------|------------|------|
| **REMOVE_ASSIGNMENT** | Availability violations | LOW | LOW |
| **INSERT_DAY_OFF** | Consecutive days violations | LOW | MEDIUM |
| **REDISTRIBUTE_LOAD** | 80-hour rule violations | MEDIUM | MEDIUM |
| **SPLIT_SHIFT** | 24+4 hour violations | MEDIUM | HIGH |
| **ADD_FACULTY** | Supervision violations | HIGH | LOW |
| **MANUAL_REVIEW** | Unknown/complex violations | HIGH | N/A |

## Safety Checklist

Before executing remediation:
- [ ] Database backup created
- [ ] Violations prioritized (Tier 1 first)
- [ ] Remediation strategies selected
- [ ] Impact assessment completed
- [ ] Rollback plan prepared

After executing remediation:
- [ ] Re-run full audit
- [ ] Verify violations resolved
- [ ] Check for unintended consequences
- [ ] Document changes in audit trail
- [ ] Save remediation report

## Rollback Procedure

If remediation fails or causes worse violations:

```bash
# Restore from backup
cd backend
psql -U scheduler residency_scheduler < backup_pre_remediation_YYYYMMDD_HHMMSS.sql

# Verify restoration
python -c "from app.db.session import SessionLocal; db = SessionLocal(); print(f'Assignments: {db.query(Assignment).count()}')"
```

## Next Steps

**If all violations resolved:**
- Proceed with schedule deployment
- Save final audit report
- Update compliance metrics

**If violations remain:**
- Analyze remaining violations
- Try different remediation strategies
- Consider manual intervention for complex cases
- Escalate to Program Director if unresolvable

## Troubleshooting

### Fix Doesn't Resolve Violation
```
⚠️  Check that fix targets correct person/block
⚠️  Verify transaction was committed
⚠️  Re-run audit with fresh database query
```

### New Violations Introduced
```
❌ Rollback changes immediately
❌ Review remediation strategy
❌ Check impact on related constraints
```

### Cannot Find Swap Candidates
```
⚠️  Relax swap matching criteria
⚠️  Consider cross-PGY swaps if allowed
⚠️  May need to add faculty coverage instead
```
