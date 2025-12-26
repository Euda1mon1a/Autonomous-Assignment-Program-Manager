# Workflow: Historical Compliance Analysis

Analyze compliance trends across multiple academic blocks to identify patterns, recurring violations, and long-term compliance metrics.

## When to Use

- Quarterly ACGME reporting
- Annual program review preparation
- Identifying systemic compliance issues
- Trend analysis for process improvement
- Before ACGME site visits
- Evaluating constraint effectiveness

## Prerequisites

- Database access to historical schedules
- Date range spanning multiple blocks (recommend 3+ months)
- Sufficient historical data (minimum 1 complete block)
- Validator instances configured

## Step-by-Step Procedure

### Step 1: Define Analysis Period

```python
from datetime import date, timedelta
from collections import defaultdict

# Define historical period (e.g., last 6 blocks)
analysis_start = date(2025, 7, 1)   # Start of academic year
analysis_end = date(2025, 12, 31)    # End of analysis period

# Break into block periods (28-day blocks)
block_periods = []
current_date = analysis_start
block_num = 1

while current_date <= analysis_end:
    block_end = min(current_date + timedelta(days=27), analysis_end)
    block_periods.append({
        "block_number": block_num,
        "start_date": current_date,
        "end_date": block_end,
        "name": f"Block {block_num}"
    })
    current_date = block_end + timedelta(days=1)
    block_num += 1

print(f"Analyzing {len(block_periods)} blocks from {analysis_start} to {analysis_end}")
for period in block_periods:
    print(f"  - {period['name']}: {period['start_date']} to {period['end_date']}")
```

### Step 2: Load Historical Data

```python
from app.models.person import Person
from app.models.block import Block
from app.models.assignment import Assignment

db = SessionLocal()

try:
    # Load all residents and faculty (assume stable over period)
    residents = db.query(Person).filter(Person.role == "RESIDENT").all()
    faculty = db.query(Person).filter(Person.role == "FACULTY").all()

    # Load all blocks in analysis period
    all_blocks = db.query(Block).filter(
        Block.date >= analysis_start,
        Block.date <= analysis_end
    ).order_by(Block.date).all()

    # Load all assignments in analysis period
    all_assignments = db.query(Assignment).join(Block).filter(
        Block.date >= analysis_start,
        Block.date <= analysis_end
    ).all()

    print(f"\n✓ Loaded {len(residents)} residents")
    print(f"✓ Loaded {len(faculty)} faculty")
    print(f"✓ Loaded {len(all_blocks)} historical blocks")
    print(f"✓ Loaded {len(all_assignments)} historical assignments")

except Exception as e:
    db.rollback()
    print(f"❌ ERROR: Failed to load historical data: {e}")
    raise
```

### Step 3: Run Validation for Each Block

```python
from app.services.constraints.acgme import (
    ACGMEConstraintValidator,
    SchedulingContext
)
from app.validators.advanced_acgme import AdvancedACGMEValidator

validator = ACGMEConstraintValidator()
advanced_validator = AdvancedACGMEValidator(db)

# Store results by block
block_results = []

print("\n" + "="*70)
print("RUNNING HISTORICAL VALIDATION")
print("="*70)

for period in block_periods:
    print(f"\n[{period['name']}] Validating {period['start_date']} to {period['end_date']}...")

    # Filter data for this block
    block_blocks = [b for b in all_blocks
                    if period['start_date'] <= b.date <= period['end_date']]
    block_assignments = [a for a in all_assignments
                        if any(b.id == a.block_id for b in block_blocks)]

    # Build context
    context = SchedulingContext(
        residents=residents,
        faculty=faculty,
        blocks=block_blocks,
    )

    # Run all validators
    tier1_violations = []
    tier2_violations = []
    tier3_warnings = []

    # 80-Hour Rule
    result = validator.validate_80_hour_rule(block_assignments, context)
    tier1_violations.extend(result.violations)

    # 1-in-7 Rule
    result = validator.validate_1_in_7_rule(block_assignments, context)
    tier1_violations.extend(result.violations)

    # Supervision Ratios
    result = validator.validate_supervision(block_assignments, context)
    tier1_violations.extend(result.violations)

    # 24+4 Hour Rule
    for resident in residents:
        violations = advanced_validator.validate_24_plus_4_rule(
            resident.id, period['start_date'], period['end_date']
        )
        tier1_violations.extend(violations)

    # Night Float Limits
    for resident in residents:
        violations = advanced_validator.validate_night_float_limits(
            resident.id, period['start_date'], period['end_date']
        )
        tier1_violations.extend(violations)

    # Store results
    block_results.append({
        "block": period['name'],
        "start_date": period['start_date'],
        "end_date": period['end_date'],
        "tier1_count": len(tier1_violations),
        "tier2_count": len(tier2_violations),
        "tier3_count": len(tier3_warnings),
        "violations": tier1_violations + tier2_violations + tier3_warnings,
        "compliant": len(tier1_violations) == 0 and len(tier2_violations) == 0
    })

    status_icon = "✅" if block_results[-1]['compliant'] else "❌"
    print(f"  {status_icon} {period['name']}: {len(tier1_violations)} Tier 1, {len(tier2_violations)} Tier 2, {len(tier3_warnings)} Tier 3")
```

### Step 4: Aggregate Violation Statistics

```python
print("\n" + "="*70)
print("VIOLATION STATISTICS")
print("="*70)

# Overall metrics
total_violations = sum(r['tier1_count'] + r['tier2_count'] for r in block_results)
total_blocks = len(block_results)
compliant_blocks = sum(1 for r in block_results if r['compliant'])
compliance_rate = (compliant_blocks / total_blocks * 100) if total_blocks > 0 else 0

print(f"\nOverall Compliance Rate: {compliance_rate:.1f}% ({compliant_blocks}/{total_blocks} blocks)")
print(f"Total Violations: {total_violations}")
print(f"  - Tier 1 (ACGME): {sum(r['tier1_count'] for r in block_results)}")
print(f"  - Tier 2 (Institutional): {sum(r['tier2_count'] for r in block_results)}")
print(f"  - Tier 3 (Soft): {sum(r['tier3_count'] for r in block_results)}")

# Violation breakdown by type
violation_by_type = defaultdict(int)
violation_by_person = defaultdict(int)

for result in block_results:
    for violation in result['violations']:
        violation_by_type[violation.constraint_type] += 1
        if violation.person_id:
            violation_by_person[violation.person_name] += 1

print("\nViolations by Constraint Type:")
for vtype, count in sorted(violation_by_type.items(), key=lambda x: x[1], reverse=True):
    print(f"  - {vtype}: {count}")

print("\nTop 5 Personnel with Most Violations:")
top_5 = sorted(violation_by_person.items(), key=lambda x: x[1], reverse=True)[:5]
for person, count in top_5:
    print(f"  - {person}: {count} violations")
```

### Step 5: Identify Recurring Patterns

```python
print("\n" + "="*70)
print("PATTERN ANALYSIS")
print("="*70)

# Pattern 1: Consecutive Block Violations (same constraint)
consecutive_patterns = defaultdict(list)
for i in range(len(block_results) - 1):
    curr_types = set(v.constraint_type for v in block_results[i]['violations'])
    next_types = set(v.constraint_type for v in block_results[i+1]['violations'])
    common = curr_types & next_types
    if common:
        for ctype in common:
            consecutive_patterns[ctype].append(
                (block_results[i]['block'], block_results[i+1]['block'])
            )

if consecutive_patterns:
    print("\n⚠️  Recurring Violations (same constraint in consecutive blocks):")
    for ctype, blocks in consecutive_patterns.items():
        print(f"\n  {ctype}:")
        for b1, b2 in blocks:
            print(f"    - {b1} → {b2}")
else:
    print("\n✅ No recurring violations across consecutive blocks")

# Pattern 2: Seasonal Trends
print("\nSeasonal Trends:")
# Group by quarter
q1_violations = sum(r['tier1_count'] + r['tier2_count']
                   for r in block_results if r['start_date'].month in [1, 2, 3])
q2_violations = sum(r['tier1_count'] + r['tier2_count']
                   for r in block_results if r['start_date'].month in [4, 5, 6])
q3_violations = sum(r['tier1_count'] + r['tier2_count']
                   for r in block_results if r['start_date'].month in [7, 8, 9])
q4_violations = sum(r['tier1_count'] + r['tier2_count']
                   for r in block_results if r['start_date'].month in [10, 11, 12])

print(f"  Q1 (Jan-Mar): {q1_violations}")
print(f"  Q2 (Apr-Jun): {q2_violations}")
print(f"  Q3 (Jul-Sep): {q3_violations}")
print(f"  Q4 (Oct-Dec): {q4_violations}")

# Pattern 3: Improvement/Degradation Trend
if len(block_results) >= 3:
    first_half_avg = sum(r['tier1_count'] + r['tier2_count']
                        for r in block_results[:len(block_results)//2]) / (len(block_results)//2)
    second_half_avg = sum(r['tier1_count'] + r['tier2_count']
                         for r in block_results[len(block_results)//2:]) / (len(block_results) - len(block_results)//2)

    if second_half_avg < first_half_avg * 0.8:
        print(f"\n📈 IMPROVEMENT DETECTED: Violations decreased {((first_half_avg - second_half_avg) / first_half_avg * 100):.1f}%")
    elif second_half_avg > first_half_avg * 1.2:
        print(f"\n📉 DEGRADATION DETECTED: Violations increased {((second_half_avg - first_half_avg) / first_half_avg * 100):.1f}%")
    else:
        print(f"\n➡️  STABLE: Violations relatively consistent")
```

### Step 6: Generate Trend Chart (Text-Based)

```python
print("\n" + "="*70)
print("VIOLATION TREND CHART")
print("="*70)

max_violations = max((r['tier1_count'] + r['tier2_count']) for r in block_results)
if max_violations == 0:
    max_violations = 1  # Avoid division by zero

print(f"\nViolations per Block (max: {max_violations}):")
print("Block   |" + " " * 50 + "| Count")
print("-" * 70)

for result in block_results:
    total = result['tier1_count'] + result['tier2_count']
    bar_length = int((total / max_violations) * 50)
    bar = "█" * bar_length
    status = "✅" if result['compliant'] else "❌"
    print(f"{result['block']:8} {status} |{bar:<50}| {total}")
```

### Step 7: Root Cause Analysis

```python
print("\n" + "="*70)
print("ROOT CAUSE ANALYSIS")
print("="*70)

# Analyze most common violations
top_violations = sorted(violation_by_type.items(), key=lambda x: x[1], reverse=True)

print("\nTop 3 Violation Types and Probable Causes:")
for i, (vtype, count) in enumerate(top_violations[:3], 1):
    print(f"\n{i}. {vtype} ({count} occurrences)")

    # Provide context-specific root cause suggestions
    if vtype == "duty_hours":
        print("   Probable Causes:")
        print("   - Insufficient resident pool size")
        print("   - Holiday/deployment clustering")
        print("   - Inadequate post-call relief")
        print("   Recommendations:")
        print("   - Review call schedule distribution")
        print("   - Check for understaffing during high-coverage periods")
        print("   - Verify post-call blocking is enforced")

    elif vtype == "consecutive_days":
        print("   Probable Causes:")
        print("   - Weekend coverage gaps")
        print("   - Back-to-back call assignments")
        print("   - Insufficient coverage rotation")
        print("   Recommendations:")
        print("   - Review weekend coverage strategy")
        print("   - Implement call spacing constraints")
        print("   - Check for adequate off-days between rotations")

    elif vtype == "supervision":
        print("   Probable Causes:")
        print("   - Faculty absence not accounted for")
        print("   - Insufficient faculty pool")
        print("   - PGY-1 clustering on specific rotations")
        print("   Recommendations:")
        print("   - Review faculty availability matrix")
        print("   - Balance PGY-1 distribution across blocks")
        print("   - Verify supervision ratio calculations")

    elif vtype == "availability":
        print("   Probable Causes:")
        print("   - Absences not loaded into database")
        print("   - Late absence approvals after schedule generation")
        print("   - Absence preservation constraint disabled")
        print("   Recommendations:")
        print("   - Verify absence data completeness")
        print("   - Implement absence pre-validation")
        print("   - Check preserve_absence constraint weight")
```

### Step 8: Generate Recommendations

```python
print("\n" + "="*70)
print("RECOMMENDATIONS")
print("="*70)

recommendations = []

# Recommendation 1: Based on compliance rate
if compliance_rate < 80:
    recommendations.append({
        "priority": "HIGH",
        "issue": f"Low compliance rate ({compliance_rate:.1f}%)",
        "action": "Review constraint configuration and resident staffing levels",
        "timeline": "Within 1 week"
    })
elif compliance_rate < 95:
    recommendations.append({
        "priority": "MEDIUM",
        "issue": f"Moderate compliance rate ({compliance_rate:.1f}%)",
        "action": "Fine-tune constraint weights and investigate recurring violations",
        "timeline": "Within 2 weeks"
    })

# Recommendation 2: Based on recurring patterns
if consecutive_patterns:
    recommendations.append({
        "priority": "HIGH",
        "issue": "Recurring violations across consecutive blocks",
        "action": f"Investigate {', '.join(consecutive_patterns.keys())} constraints for systemic issues",
        "timeline": "Immediate"
    })

# Recommendation 3: Based on personnel violations
if top_5 and top_5[0][1] > 5:
    recommendations.append({
        "priority": "MEDIUM",
        "issue": f"{top_5[0][0]} has {top_5[0][1]} violations",
        "action": "Review workload distribution and investigate if specific personnel are overburdened",
        "timeline": "Within 1 week"
    })

# Recommendation 4: Based on trend
if len(block_results) >= 3 and second_half_avg > first_half_avg * 1.2:
    recommendations.append({
        "priority": "HIGH",
        "issue": "Violations increasing over time",
        "action": "Urgent review of recent process changes, staffing, or constraint modifications",
        "timeline": "Immediate"
    })

# Print recommendations
for i, rec in enumerate(recommendations, 1):
    print(f"\n[{rec['priority']}] Recommendation {i}:")
    print(f"  Issue: {rec['issue']}")
    print(f"  Action: {rec['action']}")
    print(f"  Timeline: {rec['timeline']}")

if not recommendations:
    print("\n✅ No immediate recommendations - compliance is strong")
```

### Step 9: Save Historical Report

```python
from datetime import datetime

report_filename = f"docs/reports/historical-compliance-{analysis_start.isoformat()}-to-{analysis_end.isoformat()}.md"

with open(report_filename, 'w') as f:
    f.write("# Historical Compliance Analysis Report\n\n")
    f.write(f"**Analysis Period:** {analysis_start} to {analysis_end}\n")
    f.write(f"**Total Blocks Analyzed:** {len(block_results)}\n")
    f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")

    f.write("## Summary\n\n")
    f.write(f"- Overall Compliance Rate: {compliance_rate:.1f}%\n")
    f.write(f"- Compliant Blocks: {compliant_blocks}/{total_blocks}\n")
    f.write(f"- Total Violations: {total_violations}\n\n")

    f.write("## Violations by Block\n\n")
    f.write("| Block | Start Date | End Date | Tier 1 | Tier 2 | Tier 3 | Status |\n")
    f.write("|-------|-----------|----------|--------|--------|--------|--------|\n")
    for result in block_results:
        status = "✅ Compliant" if result['compliant'] else "❌ Violations"
        f.write(f"| {result['block']} | {result['start_date']} | {result['end_date']} | "
               f"{result['tier1_count']} | {result['tier2_count']} | {result['tier3_count']} | {status} |\n")

    f.write("\n## Top Violations\n\n")
    for vtype, count in top_violations[:5]:
        f.write(f"- **{vtype}**: {count} occurrences\n")

    f.write("\n## Recommendations\n\n")
    for i, rec in enumerate(recommendations, 1):
        f.write(f"{i}. **[{rec['priority']}]** {rec['issue']}\n")
        f.write(f"   - Action: {rec['action']}\n")
        f.write(f"   - Timeline: {rec['timeline']}\n\n")

print(f"\n✓ Historical report saved to {report_filename}")
```

### Step 10: Cleanup

```python
finally:
    db.close()
    print("\n✓ Database connection closed")
```

## Success Criteria

- ✅ All blocks in period analyzed
- ✅ Trend analysis completed
- ✅ Pattern identification performed
- ✅ Root cause analysis provided
- ✅ Recommendations generated
- ✅ Report saved to file

## Metrics to Track

| Metric | Calculation | Target |
|--------|-------------|--------|
| Compliance Rate | `(compliant_blocks / total_blocks) * 100` | > 95% |
| Violation Density | `total_violations / total_blocks` | < 2 per block |
| Recurring Pattern Rate | `blocks_with_recurring / total_blocks` | < 20% |
| Improvement Trend | `(recent_avg - early_avg) / early_avg` | Negative (improving) |

## Next Steps

**If trends are positive:**
- Continue current practices
- Document successful strategies
- Schedule next quarterly review

**If trends are negative:**
- Proceed to `violation-remediation.md` for systemic fixes
- Review constraint configuration
- Investigate staffing or process changes
