# Generate Schedule Workflow

Step-by-step guide for generating a new medical residency schedule from requirements gathering through deployment.

---

## Overview

This workflow takes you through all five phases of schedule generation with specific tools, commands, and validation checkpoints.

**Time Required:** 2-4 hours (depending on complexity)
**Prerequisites:** Backend running, database healthy, backup available
**Roles Involved:** Scheduler Admin, Program Coordinator, Program Director (approval)

---

## Phase 1: Requirements Gathering

### Step 1.1: Define Scheduling Horizon

**Determine the time period to schedule:**

```bash
# For academic year (typical)
START_DATE="2026-07-01"
END_DATE="2027-06-30"

# For single block (4 weeks)
START_DATE="2026-07-01"
END_DATE="2026-07-28"

# For quarter (13 weeks)
START_DATE="2026-07-01"
END_DATE="2026-09-30"
```

**Calculate block count:**
```python
# Each block is 4 weeks (28 days)
from datetime import datetime
start = datetime.fromisoformat("2026-07-01")
end = datetime.fromisoformat("2027-06-30")
days = (end - start).days
blocks = days // 28  # Typically 13 blocks per year
```

**Validation Checkpoint:**
- [ ] Date range aligns with program calendar
- [ ] Block boundaries match 4-week intervals
- [ ] No partial blocks at edges

### Step 1.2: Gather Personnel Data

**Collect resident information:**

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | jq -r .access_token)

# List all residents
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/people?role=RESIDENT&limit=100" \
  | jq '.items[] | {id, name, pgy_level, status}'
```

**Expected Output:**
```json
{
  "id": "res-001",
  "name": "PGY1-01",
  "pgy_level": 1,
  "status": "active"
}
```

**Collect faculty information:**

```bash
# List all faculty
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/people?role=FACULTY&limit=100" \
  | jq '.items[] | {id, name, faculty_role}'
```

**Validation Checkpoint:**
- [ ] All active residents included
- [ ] PGY levels are current
- [ ] Faculty roles assigned (PD, APD, Core Faculty)
- [ ] Qualifications up to date

### Step 1.3: Collect Absence Data

**Get resident absences:**

```bash
# Absences in scheduling horizon
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/absences?start_date=${START_DATE}&end_date=${END_DATE}" \
  | jq '.items[] | {person_name, start_date, end_date, absence_type}'
```

**Absence types to capture:**
- `VACATION` - Pre-approved leave
- `CONFERENCE` - Educational conferences
- `SICK_LEAVE` - Medical leave
- `DEPLOYMENT` - Military TDY/deployment (blocks scheduling entirely)
- `PARENTAL_LEAVE` - Maternity/paternity leave

**Validation Checkpoint:**
- [ ] All approved leave entered
- [ ] Military deployments marked (critical for coverage)
- [ ] Conference dates confirmed
- [ ] Absence types correctly categorized

### Step 1.4: Document Rotation Requirements

**Get rotation templates:**

```bash
# List all rotation templates
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/rotation-templates" \
  | jq '.[] | {name, activity_type, required_pgy_levels, capacity}'
```

**Key rotation categories:**

| Activity Type | Templates | Scheduling Mode |
|---------------|-----------|-----------------|
| `inpatient` | FMIT, IM, EM, L&D | Block-assigned (NOT optimized) |
| `night_float` | NF, NICU+NF | Half-block mirrored pairs |
| `outpatient` | Neurology, ID, Palliative Care | Half-day optimized (AM/PM) |
| `clinic` | Family Medicine Clinic | Special capacity constraints |
| `procedure` | Procedures | Depends on configuration |

**Coverage requirements:**

```bash
# Check minimum coverage per rotation
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/rotation-templates" \
  | jq '.[] | {name, min_coverage, target_coverage, max_coverage}'
```

**Validation Checkpoint:**
- [ ] Templates match current curriculum
- [ ] Coverage levels realistic for available personnel
- [ ] Activity types correctly assigned
- [ ] Capacity limits set

### Step 1.5: Capture Preferences

**Collect preference data:**

```bash
# Get submitted preferences
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/preferences?academic_year=2026-2027" \
  | jq '.items[] | {person_name, preference_type, details}'
```

**Preference types:**
- **Hard blocks** (must honor): Cannot work specific dates
- **Soft preferences** (best effort): Prefer AM shifts, prefer certain rotations
- **Continuity requests**: Prefer staying with same team

**Priority ranking:**
1. Hard blocks (vacation, family commitments) - Tier 2 constraint
2. Educational preferences (specific rotation timing) - Tier 3
3. Shift time preferences (AM/PM) - Tier 3
4. Team continuity - Tier 3

**Validation Checkpoint:**
- [ ] All submitted preferences recorded
- [ ] Hard blocks don't conflict with coverage requirements
- [ ] Preferences categorized by priority

### Step 1.6: Review Institutional Policies

**Tripler-specific rules to verify:**

1. **Military requirements:**
   - Deployments block all scheduling (absolute)
   - TDY assignments reduce availability
   - Duty restrictions for certain personnel

2. **Program-specific:**
   - PGY-1 must complete FMIT rotation first 6 months
   - Night Float rotation pattern (mirrored half-blocks)
   - Post-Call (PC) day required after NF
   - Continuity clinic weekly requirements

3. **Local policies:**
   - Holiday coverage rotation
   - Weekend coverage requirements
   - Call schedule equity

**See:** `Reference/institutional-rules.md` for complete policy list

**Validation Checkpoint:**
- [ ] Military constraints documented
- [ ] Program curriculum requirements listed
- [ ] Local policies incorporated

### Step 1.7: Create Scheduling Context

**Tool invocation:**

```bash
# MCP tool (if available)
mcp call create_scheduling_context \
  --start_date="${START_DATE}" \
  --end_date="${END_DATE}" \
  --include_absences=true \
  --include_preferences=true
```

**Or via API:**

```bash
curl -X POST http://localhost:8000/api/v1/schedule/context \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2026-07-01",
    "end_date": "2027-06-30",
    "include_residents": true,
    "include_faculty": true,
    "include_absences": true,
    "include_preferences": true,
    "include_rotation_templates": true
  }'
```

**Expected Output:**
```json
{
  "context_id": "ctx-2026-2027",
  "horizon": {
    "start_date": "2026-07-01",
    "end_date": "2027-06-30",
    "total_blocks": 13,
    "total_half_days": 182
  },
  "personnel": {
    "residents": 24,
    "faculty": 12,
    "pgy1_count": 8,
    "pgy2_count": 8,
    "pgy3_count": 8
  },
  "constraints": {
    "absences": 45,
    "hard_preferences": 12,
    "rotation_templates": 18
  },
  "status": "ready"
}
```

**Phase 1 Completion Checkpoint:**
- [ ] Scheduling horizon defined and validated
- [ ] All personnel data collected
- [ ] Absences captured and categorized
- [ ] Rotation requirements documented
- [ ] Preferences prioritized
- [ ] Institutional policies reviewed
- [ ] Scheduling context created and validated

---

## Phase 2: Constraint Propagation

**Purpose:** Apply constraints systematically to identify infeasibility early

**See:** `Workflows/constraint-propagation.md` for detailed constraint handling

### Step 2.1: Apply ACGME Constraints

**Run ACGME constraint check:**

```bash
# Pre-validate ACGME constraints with current data
curl -X POST http://localhost:8000/api/v1/schedule/validate-constraints \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "ctx-2026-2027",
    "constraint_types": ["acgme"]
  }'
```

**ACGME constraint categories:**
- 80-hour rule (weekly average over 4 weeks)
- 1-in-7 rule (24-hour off period)
- Supervision ratios (PGY-1: 2:1, PGY-2/3: 4:1)
- Duty period limits (24-hour max standard shift)

**Validation Checkpoint:**
- [ ] No structural ACGME violations
- [ ] Supervision ratios achievable with available faculty
- [ ] Work hour limits realistic for coverage needs

### Step 2.2: Apply Availability Constraints

**Check availability matrix:**

```bash
# Verify absences don't over-constrain
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/schedule/availability-matrix?context_id=ctx-2026-2027" \
  | jq '.conflicts'
```

**Look for:**
- Blocks where too many residents are unavailable
- Coverage gaps due to overlapping absences
- Critical rotations with insufficient available personnel

**Validation Checkpoint:**
- [ ] No blocks with zero available residents
- [ ] Critical rotations have minimum available coverage
- [ ] Deployment absences properly block scheduling

### Step 2.3: Apply Qualification Constraints

**Verify personnel qualifications:**

```bash
# Check qualification mapping
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/schedule/qualification-check?context_id=ctx-2026-2027" \
  | jq '.mismatches'
```

**Common qualification requirements:**
- PGY level (e.g., PGY-3 for senior resident clinics)
- Procedure credentialing (e.g., ACLS for EM rotation)
- Specialty training (e.g., OB training for L&D)

**Validation Checkpoint:**
- [ ] All residents qualified for assigned rotations
- [ ] No impossible assignments (e.g., PGY-1 to senior-only rotation)

### Step 2.4: Identify Early Conflicts

**Run feasibility analysis:**

```bash
# Check if problem is solvable
curl -X POST http://localhost:8000/api/v1/schedule/feasibility \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"context_id": "ctx-2026-2027"}'
```

**Expected Output:**
```json
{
  "feasible": true,
  "confidence": 0.85,
  "tight_constraints": [
    "Block 5: Night Float coverage (only 2 available PGY-2/3)",
    "Week 12: Three residents on leave simultaneously"
  ],
  "recommendations": [
    "Consider staggering leave in Week 12",
    "Add backup faculty for Block 5 NF"
  ]
}
```

**If infeasible:**
- Review tight constraints
- Relax Tier 3 preferences
- Adjust coverage requirements
- Add personnel or reduce rotations

**Phase 2 Completion Checkpoint:**
- [ ] ACGME constraints validated
- [ ] Availability matrix checked
- [ ] Qualifications verified
- [ ] Feasibility confirmed or conflicts identified

---

## Phase 3: Optimization

**Purpose:** Generate high-quality schedules using solver algorithms

### Step 3.1: Select Solver Algorithm

**Algorithm selection guide:**

```python
# Calculate problem complexity score
residents = 24
blocks = 13
rotations = 18
absences = 45
complexity = (residents * blocks * rotations) / (1000 + absences)

if complexity < 20:
    solver = "greedy"  # Fast, explainable
elif complexity < 50:
    solver = "pulp"    # Fast, scalable
elif complexity < 75:
    solver = "cp_sat"  # Optimal, moderate time
else:
    solver = "hybrid"  # Reliable, longer time
```

**For this workflow (24 residents, 13 blocks):**
- Recommended: `cp_sat` (optimal solutions, 1-5 minutes)
- Fallback: `hybrid` (if cp_sat times out)

### Step 3.2: Configure Optimization Objectives

**Define objective weights:**

```json
{
  "objectives": {
    "acgme_compliance": 1.0,    // Always 1.0 (hard constraint)
    "fairness": 0.25,            // Even workload distribution
    "preferences": 0.20,         // Honor preferences
    "efficiency": 0.15,          // Minimize gaps/fragmentation
    "resilience": 0.20          // Maintain backup capacity
  }
}
```

**Adjust weights based on priorities:**
- High preference satisfaction needed? Increase `preferences` to 0.30
- Fairness concerns? Increase `fairness` to 0.30
- Coverage gaps frequent? Increase `resilience` to 0.25

### Step 3.3: Run Solver with Monitoring

**Create backup FIRST (MANDATORY):**

```bash
./scripts/backup-db.sh --docker
```

**Execute schedule generation:**

```bash
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "ctx-2026-2027",
    "start_date": "2026-07-01",
    "end_date": "2027-06-30",
    "algorithm": "cp_sat",
    "timeout_seconds": 300,
    "objectives": {
      "acgme_compliance": 1.0,
      "fairness": 0.25,
      "preferences": 0.20,
      "efficiency": 0.15,
      "resilience": 0.20
    },
    "generate_alternatives": true
  }' \
  | tee schedule_generation_result.json
```

**Monitor progress:**

```bash
# Watch backend logs for solver progress
docker-compose logs -f backend | grep -i "solver\|schedule"
```

**Expected log output:**
```
INFO: CP-SAT solver starting...
INFO: Variables created: 5616
INFO: Constraints applied: 1234
INFO: Solving... (timeout: 300s)
INFO: Solution found at 45s (objective: 0.87)
INFO: Improving... (current best: 0.91)
INFO: Optimal solution found at 127s (objective: 0.94)
```

### Step 3.4: Evaluate Solution Quality

**Check generation results:**

```bash
cat schedule_generation_result.json | jq '{
  status,
  assignments_created,
  solve_time_seconds,
  acgme_compliant: .validation.acgme_compliant,
  coverage_rate: .metrics.coverage_rate,
  fairness_gini: .metrics.fairness_gini,
  preference_satisfaction: .metrics.preference_satisfaction
}'
```

**Quality thresholds:**

| Metric | Excellent | Good | Acceptable | Poor |
|--------|-----------|------|------------|------|
| Coverage Rate | >98% | >95% | >90% | <90% |
| Fairness (Gini) | <0.10 | <0.15 | <0.20 | >0.20 |
| Preference Match | >85% | >80% | >75% | <75% |
| Solve Time | <60s | <180s | <300s | Timeout |

### Step 3.5: Review Alternative Solutions

**If `generate_alternatives: true`, compare options:**

```bash
cat schedule_generation_result.json | jq '.alternatives[]'
```

**Expected alternatives:**
```json
[
  {
    "id": "alt-1",
    "description": "Maximizes fairness (Gini=0.08)",
    "metrics": {
      "fairness_gini": 0.08,
      "preference_satisfaction": 0.78,
      "efficiency_score": 0.85
    },
    "trade_offs": "Lower preference satisfaction"
  },
  {
    "id": "alt-2",
    "description": "Maximizes preferences (satisfaction=0.89)",
    "metrics": {
      "fairness_gini": 0.13,
      "preference_satisfaction": 0.89,
      "efficiency_score": 0.82
    },
    "trade_offs": "Moderate fairness impact"
  }
]
```

**Select best option:**
- Present to Program Director for review
- Consider program priorities
- Document selection rationale

**Phase 3 Completion Checkpoint:**
- [ ] Solver completed successfully
- [ ] Solution quality meets thresholds
- [ ] Alternatives evaluated
- [ ] Primary solution selected

---

## Phase 4: Conflict Resolution

**Purpose:** Handle unavoidable conflicts and trade-offs

**See:** `Workflows/conflict-resolution.md` for detailed conflict handling

### Step 4.1: Identify Remaining Violations

**Check validation report:**

```bash
cat schedule_generation_result.json | jq '.validation.violations'
```

**Violation categories:**
- **Hard violations** (Tier 1): ACGME rule breaks
- **Soft violations** (Tier 2): Institutional policy overrides
- **Warnings** (Tier 3): Sub-optimal but acceptable

### Step 4.2: Attempt Automated Resolution

**For soft violations, try constraint relaxation:**

```bash
# If fairness slightly violated, regenerate with relaxed fairness
curl -X POST http://localhost:8000/api/v1/schedule/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "ctx-2026-2027",
    "algorithm": "cp_sat",
    "objectives": {
      "acgme_compliance": 1.0,
      "fairness": 0.20,    // Reduced from 0.25
      "preferences": 0.25  // Increased from 0.20
    }
  }'
```

### Step 4.3: Manual Conflict Resolution

**For hard violations requiring human decision:**

1. Document the conflict
2. Propose trade-off options
3. Get Program Director approval
4. Document exception

**See:** `Workflows/conflict-resolution.md` for conflict resolution protocol

**Phase 4 Completion Checkpoint:**
- [ ] All hard violations resolved
- [ ] Soft violations documented and approved
- [ ] Exceptions recorded with rationale

---

## Phase 5: Validation & Deployment

**Purpose:** Final verification and safe deployment

### Step 5.1: Comprehensive ACGME Validation

**Run full compliance check:**

```bash
# MCP tool
mcp call validate_acgme_compliance --schedule_id="2026-2027-academic-year"

# Or API
curl -X POST http://localhost:8000/api/v1/schedule/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": "2026-2027-academic-year", "strict": true}'
```

**Must be 100% compliant (zero violations).**

### Step 5.2: Verify Coverage Requirements

**Check all rotations have minimum coverage:**

```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/schedule/coverage-report?schedule_id=2026-2027-academic-year" \
  | jq '.gaps'
```

**Expected:** `gaps: []`

### Step 5.3: Run Resilience Checks

**N-1 Contingency Analysis:**

```bash
# MCP tool
mcp call run_contingency_analysis_resilience_tool \
  --schedule_id="2026-2027-academic-year"
```

**Must pass:** Schedule remains valid if any one person becomes unavailable

**80% Utilization Check:**

```bash
mcp call check_utilization_threshold_tool \
  --schedule_id="2026-2027-academic-year"
```

**Must pass:** No person scheduled above 80% of maximum capacity

### Step 5.4: Create Final Backup

**Mandatory before deployment:**

```bash
# Create pre-deployment backup
./scripts/backup-db.sh --docker

# Verify backup
ls -lah backups/postgres/ | tail -1
```

### Step 5.5: Deploy Schedule

**Publish to production:**

```bash
curl -X POST http://localhost:8000/api/v1/schedule/publish \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"schedule_id": "2026-2027-academic-year", "notify_users": true}'
```

**Expected actions:**
- Schedule assignments written to database
- Users notified via email
- Calendar integrations updated
- Audit log created

### Step 5.6: Generate Reports

**Create summary reports:**

```bash
# Coverage report
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/reports/coverage?schedule_id=2026-2027-academic-year" \
  > coverage_report.pdf

# Fairness analysis
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/reports/fairness?schedule_id=2026-2027-academic-year" \
  > fairness_report.pdf

# Individual schedules
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/reports/individual-schedules?schedule_id=2026-2027-academic-year" \
  > individual_schedules.pdf
```

**Phase 5 Completion Checkpoint:**
- [ ] 100% ACGME compliant
- [ ] All coverage requirements met
- [ ] N-1 contingency passes
- [ ] 80% utilization respected
- [ ] Backup created
- [ ] Schedule deployed
- [ ] Reports generated and distributed

---

## Post-Deployment

### Monitoring

**First 48 hours after deployment:**
- Monitor for user-reported conflicts
- Check swap request volume
- Review complaint patterns

**First week:**
- Run daily compliance check
- Monitor coverage gaps
- Collect feedback from residents/faculty

### Adjustments

**Minor adjustments (via swap system):**
- Individual preference issues
- One-off conflicts
- Personal emergencies

**Major adjustments (requires regeneration):**
- Systemic coverage problems
- Multiple ACGME violations discovered
- Policy changes mid-year

---

## Troubleshooting

### Solver Times Out

**Problem:** Solver exceeds 300 second timeout

**Solutions:**
1. Increase timeout to 600 seconds
2. Switch to `hybrid` solver (tries multiple algorithms)
3. Decompose problem (generate quarters separately)
4. Reduce objective complexity (fewer weighted objectives)

### No Feasible Solution

**Problem:** Solver reports no valid schedule exists

**Solutions:**
1. Review tight constraints (see feasibility report)
2. Check for impossible configurations (e.g., all residents on leave same day)
3. Relax Tier 3 preferences
4. Reduce coverage requirements temporarily
5. Add backup personnel or reduce rotations

### Poor Quality Score

**Problem:** Solution quality below acceptable thresholds

**Solutions:**
1. Increase solver timeout (allow more time to optimize)
2. Adjust objective weights (favor problematic metric)
3. Generate alternatives and compare
4. Use `cp_sat` for better optimality (if using greedy/pulp)

### ACGME Violations in Result

**Problem:** Generated schedule has compliance violations

**Solutions:**
1. **NEVER deploy** - must be 100% compliant
2. Review which rule violated (80-hour, 1-in-7, supervision)
3. Check constraint configuration in code
4. Report as bug if solver should have prevented
5. Regenerate with stricter ACGME weight

---

## Checklist Summary

**Before Starting:**
- [ ] Backend healthy and accessible
- [ ] Database backup exists and is recent
- [ ] Auth token obtained
- [ ] Personnel data is current

**Phase 1 - Requirements:**
- [ ] Scheduling horizon defined
- [ ] Personnel data collected
- [ ] Absences captured
- [ ] Rotation requirements documented
- [ ] Preferences prioritized
- [ ] Institutional policies reviewed
- [ ] Scheduling context validated

**Phase 2 - Constraints:**
- [ ] ACGME constraints validated
- [ ] Availability matrix checked
- [ ] Qualifications verified
- [ ] Feasibility confirmed

**Phase 3 - Optimization:**
- [ ] Solver selected
- [ ] Objectives configured
- [ ] Backup created
- [ ] Solver executed successfully
- [ ] Solution quality acceptable
- [ ] Alternatives evaluated

**Phase 4 - Conflicts:**
- [ ] Violations identified
- [ ] Automated resolution attempted
- [ ] Manual conflicts resolved
- [ ] Exceptions documented

**Phase 5 - Deployment:**
- [ ] ACGME validation passes (100%)
- [ ] Coverage complete
- [ ] Resilience checks pass
- [ ] Final backup created
- [ ] Schedule deployed
- [ ] Reports generated
- [ ] Users notified

**Post-Deployment:**
- [ ] Monitoring active for 48 hours
- [ ] Feedback collection started
- [ ] Adjustment process ready
