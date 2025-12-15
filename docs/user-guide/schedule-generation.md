# Schedule Generation

Schedule Generation is the core function of the Residency Scheduler. This guide explains how to create, configure, and optimize schedules.

---

## Accessing Schedule Generation

### From Dashboard

Click **Generate Schedule** in Quick Actions.

### From Navigation

The schedule generation dialog can be accessed from multiple locations.

**Required Role**: Coordinator or Admin

---

## Generate Schedule Dialog

```
+------------------------------------------+
|          Generate Schedule               |
+------------------------------------------+
|                                          |
|  Start Date *                            |
|  [____/____/________]  [Calendar Icon]   |
|                                          |
|  End Date *                              |
|  [____/____/________]  [Calendar Icon]   |
|                                          |
|  Algorithm                               |
|  [Greedy (Fast)            v]            |
|                                          |
|  PGY Levels to Include                   |
|  [x] PGY-1                               |
|  [x] PGY-2                               |
|  [x] PGY-3                               |
|                                          |
|  Advanced Options [+]                    |
|                                          |
|  [Cancel]              [Generate]        |
+------------------------------------------+
```

---

## Basic Schedule Generation

### Step-by-Step Guide

1. Click **Generate Schedule** from Dashboard
2. Set **Start Date** (first day of schedule)
3. Set **End Date** (last day of schedule)
4. Select **Algorithm** (start with Greedy)
5. Verify **PGY Levels** are checked
6. Click **Generate**

### Typical Date Ranges

| Period Type | Duration | Example |
|-------------|----------|---------|
| One Block | 4 weeks | Jan 1 - Jan 28 |
| One Month | ~30 days | Jan 1 - Jan 31 |
| One Quarter | 13 weeks | Jan 1 - Mar 31 |
| Academic Year | 52 weeks | Jul 1 - Jun 30 |

**Recommendation**: Generate one block (4 weeks) at a time for best results.

---

## Scheduling Algorithms

### Greedy (Fast)

```
Speed:     [=====-----]  Fast
Quality:   [====------]  Good
Best For:  Quick drafts, simple schedules
```

**How it works**:
1. Sorts blocks by difficulty (hardest first)
2. Assigns least-loaded available resident
3. Continues until all blocks filled

**Use when**:
- You need quick results
- Making initial drafts
- Simple scheduling needs

### Min Conflicts (Balanced)

```
Speed:     [===-------]  Moderate
Quality:   [======----]  Better
Best For:  Most schedules
```

**How it works**:
1. Initial greedy assignment
2. Identifies conflicts
3. Iteratively resolves by swapping assignments
4. Stops when no improvement possible

**Use when**:
- Standard scheduling
- Balance of speed and quality
- Moderate complexity

### CP-SAT (Optimal)

```
Speed:     [==--------]  Slower
Quality:   [==========-]  Optimal
Best For:  Final schedules, complex constraints
```

**How it works**:
1. Models as constraint satisfaction problem
2. Uses Google OR-Tools solver
3. Guarantees ACGME compliance if possible
4. Finds mathematically optimal solution

**Use when**:
- Final schedule generation
- Complex constraint scenarios
- ACGME compliance is critical
- You have time to wait

### Algorithm Comparison

| Factor | Greedy | Min Conflicts | CP-SAT |
|--------|--------|---------------|--------|
| Speed | Seconds | Minutes | Minutes-Hours |
| ACGME Compliance | Not guaranteed | Usually good | Guaranteed* |
| Coverage | Good | Better | Optimal |
| Fairness | Basic | Improved | Optimal |

*If a compliant solution exists

---

## Generation Process

### What Happens During Generation

```
Step 1: Data Loading
├── Load all people (residents, faculty)
├── Load rotation templates
├── Load absence records
└── Build availability matrix

Step 2: Block Analysis
├── Identify all schedulable blocks
├── Determine requirements per block
└── Calculate difficulty scores

Step 3: Assignment
├── Run selected algorithm
├── Assign residents to rotations
├── Assign supervising faculty
└── Track constraint satisfaction

Step 4: Validation
├── Check 80-hour rule
├── Check 1-in-7 rule
├── Verify supervision ratios
└── Calculate coverage rate

Step 5: Results
├── Save assignments to database
├── Generate summary report
└── Flag any violations
```

### Progress Indicators

During generation, you'll see:
- Progress bar
- Current step description
- Estimated time remaining (for longer runs)

---

## Generation Results

### Success

```
+------------------------------------------+
|          Schedule Generated!             |
+------------------------------------------+
|                                          |
|  [Green Checkmark] Success!              |
|                                          |
|  Assignments Created: 156                |
|  Coverage Rate: 94%                      |
|  ACGME Compliant: Yes                    |
|                                          |
|  [View Schedule]    [Generate Another]   |
+------------------------------------------+
```

### Partial Success

```
+------------------------------------------+
|          Schedule Generated              |
+------------------------------------------+
|                                          |
|  [Yellow Warning] Completed with issues  |
|                                          |
|  Assignments Created: 148                |
|  Coverage Rate: 86%                      |
|  ACGME Compliant: No (2 violations)      |
|                                          |
|  Issues:                                 |
|  - Dr. Smith: 1-in-7 violation           |
|  - Coverage gap: Jan 15 PM               |
|                                          |
|  [View Schedule]    [View Compliance]    |
+------------------------------------------+
```

### Failure

```
+------------------------------------------+
|          Generation Failed               |
+------------------------------------------+
|                                          |
|  [Red X] Could not generate schedule     |
|                                          |
|  Reason: Insufficient residents          |
|  available for required coverage.        |
|                                          |
|  Suggestions:                            |
|  - Check absence records                 |
|  - Reduce rotation requirements          |
|  - Add more residents                    |
|                                          |
|  [Retry]              [Cancel]           |
+------------------------------------------+
```

---

## Advanced Options

### PGY Level Selection

Control which residents to include:

```
PGY Levels to Include
[x] PGY-1   (12 residents)
[x] PGY-2   (10 residents)
[ ] PGY-3   (8 residents - excluded)
```

**Use cases**:
- Generate PGY-specific schedules
- Test capacity with subset
- Handle staggered onboarding

### Override Settings (Admin)

```
Advanced Options
[x] Allow overtime (exceed 80 hours)
[x] Allow supervision flex
[ ] Force regenerate (clear existing)
```

**Caution**: Override options may create non-compliant schedules.

---

## Post-Generation Tasks

### 1. Review the Schedule

- Check Dashboard for overview
- Look for gaps or issues
- Verify key assignments

### 2. Check Compliance

- Go to Compliance page
- Review all three rules
- Address any violations

### 3. Make Manual Adjustments

If needed:
- Swap assignments
- Add coverage
- Adjust for preferences

### 4. Export and Distribute

- Export to Excel
- Review with chief residents
- Distribute to program

---

## Scheduling Tips

### Before Generating

1. **Update all absences** - Ensure vacation, TDY, deployments are recorded
2. **Verify people list** - All residents and faculty should be current
3. **Review templates** - Capacity and requirements should be accurate

### Choosing Algorithm

| Situation | Recommended Algorithm |
|-----------|----------------------|
| First draft | Greedy |
| Standard block | Min Conflicts |
| Final schedule | CP-SAT |
| Large program (>30 residents) | Min Conflicts or CP-SAT |
| Simple program | Greedy |

### Handling Failures

If generation fails:
1. Check error message for cause
2. Common fixes:
   - Add missing absences
   - Increase template capacity
   - Adjust date range
3. Try different algorithm
4. Contact admin if persistent

---

## Common Scenarios

### Generating Monthly Schedule

1. **Date Range**: First to last day of month
2. **Algorithm**: Min Conflicts
3. **Generate**
4. **Review** compliance
5. **Export** for distribution

### Generating After New Absence

When someone calls in sick:
1. Add the absence
2. Generate for affected dates only
3. Review changes
4. Notify affected parties

### Generating New Academic Year

1. **Verify** all PGY levels updated
2. **Add** new interns
3. **Generate** first block (July 1-28)
4. **Check** compliance carefully
5. **Iterate** as needed

### Regenerating Specific Period

When changes require regeneration:
1. Generate with same date range
2. New schedule replaces old
3. Review all assignments
4. Check compliance

---

## Performance Considerations

### Large Date Ranges

| Range | Greedy | Min Conflicts | CP-SAT |
|-------|--------|---------------|--------|
| 1 week | <1 sec | <5 sec | <30 sec |
| 1 month | <5 sec | <30 sec | 2-5 min |
| 3 months | <15 sec | 2-3 min | 10-30 min |
| 1 year | <1 min | 10-15 min | May timeout |

### Recommendations

- Generate one block (4 weeks) at a time for CP-SAT
- Use Greedy for full-year planning
- Min Conflicts for monthly schedules

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Generation times out | Too large range + CP-SAT | Use smaller range or different algorithm |
| Low coverage rate | Not enough available residents | Check absences; add residents |
| Many violations | Insufficient resources | Adjust templates; reduce requirements |
| Same person always assigned | Uneven workload | Use CP-SAT for fairness |
| Algorithm fails immediately | Invalid data | Check people, templates, blocks |

---

## Related Guides

- [Dashboard](dashboard.md) - Quick Actions
- [Compliance](compliance.md) - Understanding violations
- [Templates](templates.md) - Rotation setup
- [Absences](absences.md) - Availability management
- [Settings](settings.md) - Algorithm configuration

---

*Effective schedule generation combines good data with the right algorithm choice.*
