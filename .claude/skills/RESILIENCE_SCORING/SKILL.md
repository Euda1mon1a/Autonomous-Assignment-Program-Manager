***REMOVED*** RESILIENCE_SCORING Skill

***REMOVED******REMOVED*** Metadata

- **Name**: RESILIENCE_SCORING
- **Version**: 1.0.0
- **Category**: Schedule Analysis
- **Dependencies**: Backend resilience framework (`backend/app/resilience/`)

***REMOVED******REMOVED*** Description

Health metrics calculation and robustness testing under failure scenarios. Quantifies schedule resilience through coverage margins, constraint slack, and failure simulation.

***REMOVED******REMOVED*** Purpose

Proactively identify schedule vulnerabilities before real-world failures occur. Answer critical questions:
- How healthy is the current schedule?
- What happens if one resident is suddenly absent?
- Which rotations are most fragile?
- How quickly can we recover from disruptions?
- Who are the "critical" residents we can't afford to lose?

***REMOVED******REMOVED*** When to Use This Skill

Invoke this skill when:
- ✅ Evaluating a newly generated schedule before deployment
- ✅ Conducting monthly resilience health checks
- ✅ Investigating schedule weaknesses after an incident
- ✅ Comparing resilience across multiple schedule candidates
- ✅ Planning for high-risk periods (deployment season, flu season)
- ✅ Validating that schedule changes improved robustness

Do NOT use for:
- ❌ Real-time failure response (use `production-incident-responder` skill)
- ❌ ACGME compliance validation (use `acgme-compliance` skill)
- ❌ Schedule generation (use `schedule-optimization` skill)

***REMOVED******REMOVED*** Core Metrics

***REMOVED******REMOVED******REMOVED*** Health Score Formula

**Overall Health Score = 0.4×Coverage + 0.3×Margin + 0.3×Continuity**

Where:
- **Coverage (0-1)**: Rotation staffing adequacy vs minimum requirements
- **Margin (0-1)**: Constraint slack (how close to ACGME limits)
- **Continuity (0-1)**: Rotation stability (minimize mid-block switches)

***REMOVED******REMOVED******REMOVED*** Health Score Interpretation

| Score | Status | Meaning | Action |
|-------|--------|---------|--------|
| 0.85-1.0 | EXCELLENT | Robust, high margin | Monitor quarterly |
| 0.70-0.84 | GOOD | Acceptable, some slack | Monitor monthly |
| 0.50-0.69 | FAIR | Tight margins | Weekly monitoring |
| 0.30-0.49 | POOR | Vulnerable to failures | Daily monitoring + mitigation |
| 0.0-0.29 | CRITICAL | Collapse imminent | Emergency intervention |

***REMOVED******REMOVED*** Failure Modes Analyzed

***REMOVED******REMOVED******REMOVED*** 1. N-1 Failure (Single Absence)
- Simulate each resident absent for 1 week
- Identify "critical" residents (absence causes coverage failure)
- Quantify impact: hours of understaffing, rotations affected

***REMOVED******REMOVED******REMOVED*** 2. N-2 Failure (Double Absence)
- Simultaneous absence of 2 residents
- Worst-case pair identification
- Cascading failure probability

***REMOVED******REMOVED******REMOVED*** 3. Multi-Failure Scenarios
- Monte Carlo simulation (random 2-3 absences)
- Median time-to-failure
- 95th percentile worst-case

***REMOVED******REMOVED******REMOVED*** 4. Recovery Analysis
- Time to restore coverage after disruption
- Bottleneck identification (which rotations delay recovery)
- Supplemental staff effectiveness

***REMOVED******REMOVED*** Skill Phases

***REMOVED******REMOVED******REMOVED*** Phase 1: Baseline Health Assessment
**Input**: Current schedule (block assignments)
**Output**: Health score, component breakdown, flagged weaknesses
**Workflow**: `Workflows/compute-health-score.md`

***REMOVED******REMOVED******REMOVED*** Phase 2: Single-Point Failure Analysis
**Input**: Schedule + resident roster
**Output**: Critical resident list, N-1 vulnerability matrix
**Workflow**: `Workflows/n1-failure-simulation.md`

***REMOVED******REMOVED******REMOVED*** Phase 3: Multi-Failure Stress Testing
**Input**: Schedule + failure scenarios (2-3 simultaneous absences)
**Output**: Collapse probability, fragile rotation ranking
**Workflow**: `Workflows/multi-failure-scenarios.md`

***REMOVED******REMOVED******REMOVED*** Phase 4: Recovery Time Modeling
**Input**: Disruption scenario + available mitigation options
**Output**: Time-to-recovery estimate, optimal response strategy
**Workflow**: `Workflows/recovery-time-analysis.md`

***REMOVED******REMOVED*** Key Files and Integration Points

***REMOVED******REMOVED******REMOVED*** Backend Resilience Framework
```
backend/app/resilience/
├── health_metrics.py          ***REMOVED*** Health score calculation
├── n_minus_analysis.py        ***REMOVED*** N-1/N-2 contingency testing
├── monte_carlo_sim.py         ***REMOVED*** Multi-failure simulation
├── recovery_planner.py        ***REMOVED*** Recovery time estimation
└── thresholds.py              ***REMOVED*** Alert thresholds
```

***REMOVED******REMOVED******REMOVED*** Database Tables Used
- `assignments` - Current schedule state
- `persons` - Resident/faculty roster
- `rotations` - Coverage requirements
- `resilience_health_checks` - Historical health scores
- `resilience_alerts` - Triggered warnings

***REMOVED******REMOVED******REMOVED*** MCP Tools (if available)
- `mcp__resilience_check_health` - Compute current health score
- `mcp__resilience_n1_simulation` - Run N-1 failure test
- `mcp__resilience_recovery_plan` - Generate recovery options

***REMOVED******REMOVED******REMOVED*** Metrics Endpoints
- `GET /api/resilience/health` - Current health score
- `GET /api/resilience/n-minus-analysis` - N-1/N-2 results
- `POST /api/resilience/simulate-failure` - Run custom scenario
- `GET /api/resilience/historical` - Past health trends

***REMOVED******REMOVED*** Output Formats

***REMOVED******REMOVED******REMOVED*** Health Score Report
```json
{
  "overall_health": 0.78,
  "timestamp": "2025-12-26T10:00:00Z",
  "components": {
    "coverage": 0.85,
    "margin": 0.72,
    "continuity": 0.76
  },
  "status": "GOOD",
  "warnings": [
    "Peds rotation coverage at 1.1x minimum (tight margin)",
    "PGY-2 cohort at 75/80 work hours (low slack)"
  ],
  "recommendations": [
    "Add 1 supplemental faculty for Peds clinic",
    "Reduce PGY-2 call frequency by 10%"
  ]
}
```

***REMOVED******REMOVED******REMOVED*** N-1 Failure Matrix
```
Critical Residents (absence causes coverage failure):
  - PGY2-03: Coverage loss in EM (2.3 days understaffed)
  - PGY3-01: Coverage loss in Peds (1.8 days understaffed)

High-Impact Residents (significant degradation):
  - PGY2-05: Margin drops from 0.72 → 0.58
  - PGY3-04: Continuity loss (4 residents need rotation switch)

Low-Impact Residents (absorbable):
  - PGY1-02, PGY1-07, PGY2-08 (can cover via existing slack)
```

***REMOVED******REMOVED******REMOVED*** Multi-Failure Scenario Results
```
Monte Carlo Simulation (10,000 trials, 2-3 simultaneous absences):
  - Median time-to-failure: 4.2 days
  - 95th percentile: 1.1 days (worst-case collapse)
  - Collapse probability: 12.3% (unacceptable)

Fragile Rotations:
  1. EM Night Shift (fails in 78% of scenarios)
  2. Peds Clinic (fails in 45% of scenarios)
  3. OB/GYN Call (fails in 31% of scenarios)

Recommended Mitigations:
  - Add 1 supplemental EM night resident (→ 3.8% collapse prob)
  - Cross-train 2 residents for Peds backup
```

***REMOVED******REMOVED*** Error Handling

***REMOVED******REMOVED******REMOVED*** Common Errors

**Error: Insufficient historical data**
```
Cause: Less than 1 month of resilience checks in database
Fix: Run daily health checks for 30 days to establish baseline
Command: celery -A app.core.celery_app worker --loglevel=info
```

**Error: Monte Carlo simulation timeout**
```
Cause: Too many trials or complex schedule
Fix: Reduce trial count from 10,000 → 1,000 for initial analysis
Parameter: POST /api/resilience/simulate-failure {"trials": 1000}
```

**Error: N-1 analysis incomplete**
```
Cause: Missing rotation coverage requirements in database
Fix: Verify all rotations have `min_residents` field populated
SQL: SELECT * FROM rotations WHERE min_residents IS NULL;
```

**Error: Health score = NULL**
```
Cause: No active assignments in schedule
Fix: Verify schedule has been generated and is not in draft state
Check: SELECT COUNT(*) FROM assignments WHERE status = 'active';
```

***REMOVED******REMOVED******REMOVED*** Recovery Procedures

**If health score drops suddenly:**
1. Check recent schedule changes: `git log --since="1 week ago" -- backend/app/scheduling/`
2. Review recent leave approvals: `SELECT * FROM leave_requests WHERE approved_at > NOW() - INTERVAL '1 week';`
3. Run N-1 analysis to identify new critical residents
4. Generate mitigation options via recovery planner

**If N-1 analysis shows too many critical residents (>3):**
1. Examine rotation coverage requirements (may be over-constrained)
2. Consider cross-training residents for backup roles
3. Evaluate adding supplemental staff
4. Review historical data - is this seasonal (deployment season, flu season)?

**If Monte Carlo shows high collapse probability (>10%):**
1. Immediate: Flag schedule as high-risk, do not deploy
2. Short-term: Run recovery planner for contingency options
3. Long-term: Increase staffing or reduce rotation requirements

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** Workflow: Complete Schedule Validation
```
1. Generate schedule: schedule-optimization skill
2. ACGME validation: acgme-compliance skill
3. Resilience scoring: RESILIENCE_SCORING skill (this skill)
4. Security audit: security-audit skill
5. Deployment: safe-schedule-generation skill
```

***REMOVED******REMOVED******REMOVED*** Workflow: Post-Incident Analysis
```
1. Immediate response: production-incident-responder skill
2. Root cause: systematic-debugger skill
3. Resilience assessment: RESILIENCE_SCORING skill (this skill)
4. Long-term fix: constraint-preflight skill
```

***REMOVED******REMOVED******REMOVED*** Workflow: Monthly Health Check
```
1. Compute health score: RESILIENCE_SCORING skill
2. If score < 0.7: Run N-1 + multi-failure analysis
3. Document findings: Update Reference/historical-resilience.md
4. Track trends: Plot health score over time
```

***REMOVED******REMOVED*** Reference Documents

- **metric-definitions.md**: What each metric means (coverage, margin, continuity formulas)
- **thresholds.md**: When to escalate (health < 0.7, critical count > 2)
- **historical-resilience.md**: Past benchmark data, seasonal patterns

***REMOVED******REMOVED*** Quick Start Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Check Current Schedule Health
```bash
***REMOVED*** Via MCP tool (if available)
mcp__resilience_check_health

***REMOVED*** Via API
curl http://localhost:8000/api/resilience/health

***REMOVED*** Expected output: Health score + component breakdown + warnings
```

***REMOVED******REMOVED******REMOVED*** Example 2: Identify Critical Residents
```bash
***REMOVED*** Run N-1 analysis
curl -X POST http://localhost:8000/api/resilience/n-minus-analysis \
  -H "Content-Type: application/json" \
  -d '{"scenario": "n1", "duration_days": 7}'

***REMOVED*** Review output for "critical" residents (absence causes coverage failure)
```

***REMOVED******REMOVED******REMOVED*** Example 3: Stress Test Schedule
```bash
***REMOVED*** Monte Carlo simulation (1000 trials, 2-3 simultaneous absences)
curl -X POST http://localhost:8000/api/resilience/simulate-failure \
  -H "Content-Type: application/json" \
  -d '{
    "trials": 1000,
    "min_failures": 2,
    "max_failures": 3,
    "duration_days": 7
  }'

***REMOVED*** Review collapse probability and fragile rotations
```

***REMOVED******REMOVED******REMOVED*** Example 4: Recovery Planning
```bash
***REMOVED*** Generate recovery options for specific disruption
curl -X POST http://localhost:8000/api/resilience/recovery-plan \
  -H "Content-Type: application/json" \
  -d '{
    "absent_residents": ["PGY2-03", "PGY3-01"],
    "duration_days": 14,
    "available_supplemental_staff": ["FAC-TEMP-01"]
  }'

***REMOVED*** Expected output: Time-to-recovery, optimal strategy, bottlenecks
```

***REMOVED******REMOVED*** Success Criteria

This skill is successfully applied when:
- ✅ Health score is computed with all 3 components (coverage, margin, continuity)
- ✅ Critical residents are identified (if any)
- ✅ Fragile rotations are ranked by failure probability
- ✅ Recovery time estimates are generated for key scenarios
- ✅ Findings are documented in historical-resilience.md
- ✅ Actionable recommendations are provided (not just raw numbers)

***REMOVED******REMOVED*** Notes

- **Run monthly**: Schedule regular resilience health checks (via Celery beat)
- **Seasonal awareness**: Deployment season (Jun-Aug) and flu season (Nov-Feb) typically show lower scores
- **Trend analysis**: Single health score is less useful than 3-month trend
- **Mitigation tracking**: Document whether recommended mitigations were implemented and their effect
- **Cross-training**: Most effective long-term resilience improvement (train residents for backup rotations)

---

*This skill complements the existing resilience framework in `backend/app/resilience/` by providing systematic workflows for health assessment and failure testing.*
