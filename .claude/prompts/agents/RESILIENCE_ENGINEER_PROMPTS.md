# Resilience Engineer Agent - Prompt Templates

> **Role:** System resilience, failure analysis, contingency planning, N-1/N-2 analysis
> **Model:** Claude Opus 4.5
> **Mission:** Ensure system survives disruptions

## 1. RESILIENCE ASSESSMENT TEMPLATE

```
**RESILIENCE ASSESSMENT**

**ASSESSMENT DATE:** ${TODAY}
**SCOPE:** ${SCOPE}

**RESILIENCE FRAMEWORK:**

### Defense Levels (GREEN to BLACK)
- **GREEN:** All systems nominal, no threats
- **YELLOW:** Warnings, minor degradation acceptable
- **ORANGE:** Major issues, contingency active
- **RED:** Critical condition, emergency response
- **BLACK:** System failure imminent, escalate immediately

**CURRENT DEFENSE LEVEL:** ${CURRENT_LEVEL}

**VULNERABILITY ASSESSMENT:**

### Single Point of Failures (SPOF)
- SPOF 1: ${SPOF_1} (Impact: ${IMPACT_1})
- SPOF 2: ${SPOF_2} (Impact: ${IMPACT_2})
- SPOF 3: ${SPOF_3} (Impact: ${IMPACT_3})

### Critical Resources
- Database: ${DB_REDUNDANCY}
- API servers: ${API_REDUNDANCY}
- Cache layer: ${CACHE_REDUNDANCY}
- Message queue: ${MQ_REDUNDANCY}

**RESILIENCE SCORE:** ${RESILIENCE_SCORE}/100

**GAPS:**
${GAPS}

**RECOMMENDATIONS:**
${RECOMMENDATIONS}

Assess system resilience.
```

## 2. N-1 CONTINGENCY TEMPLATE

```
**N-1 CONTINGENCY ANALYSIS**

**SCENARIO:** What if one critical resource fails?

**RESOURCE:** ${CRITICAL_RESOURCE}

**BASELINE STATE:**
- Current capacity: ${CURRENT_CAPACITY}%
- Utilization: ${CURRENT_UTIL}%
- Redundancy: ${REDUNDANCY_LEVEL}
- Failover time: ${FAILOVER_TIME}

**N-1 IMPACT:**
If ${CRITICAL_RESOURCE} fails:
- Remaining capacity: ${REMAINING_CAPACITY}%
- Utilization after failure: ${FAILURE_UTIL}%
- Service degradation: ${DEGRADATION}%
- Time to restore: ${RESTORE_TIME}

**FEASIBILITY:** ${N1_FEASIBLE}

**CONTINGENCY PLAN:**
1. Detect failure (automated in ${DETECTION_TIME}s)
2. Failover to backup (${FAILOVER_TIME}s)
3. Redirect traffic (automatic)
4. Restore original resource (${RESTORE_TIME} minutes)
5. Reintegrate (${REINTEGRATION_TIME} minutes)

**VALIDATION:**
- [ ] Failover tested monthly
- [ ] Capacity sufficient for N-1
- [ ] Alerts properly configured
- [ ] Team trained

Assess N-1 contingency capability.
```

## 3. N-2 CONTINGENCY TEMPLATE

```
**N-2 CONTINGENCY ANALYSIS**

**SCENARIO:** What if two critical resources fail simultaneously?

**RESOURCES AT RISK:**
1. ${RESOURCE_1}
2. ${RESOURCE_2}

**N-2 IMPACT:**
- Remaining capacity: ${REMAINING_CAPACITY}%
- Service operational: ${OPERATIONAL_STATUS}
- Estimated downtime: ${DOWNTIME}
- Data loss risk: ${DATA_LOSS_RISK}

**FEASIBILITY:** ${N2_FEASIBLE}

**N-2 STRATEGY:**
- Degraded service mode: ${DEGRADED_MODE_AVAILABLE}
- Reduced feature set: ${REDUCED_FEATURES}
- Batch job suspension: ${BATCH_SUSPENSION}
- Non-critical work: ${NONCRITICAL_SUSPENSION}

**RECOVERY SEQUENCE:**
1. Prioritize critical functions
2. Restore Resource 1 (${TIME_1})
3. Restore Resource 2 (${TIME_2})
4. Reintegrate systems
5. Resume normal operations

**PREPARATION:**
- Documented runbooks: ${RUNBOOKS_STATUS}
- Team training: ${TRAINING_STATUS}
- Communication plan: ${COMMS_PLAN_STATUS}

Assess N-2 contingency capability.
```

## 4. FAILURE MODE ANALYSIS TEMPLATE

```
**FAILURE MODE AND EFFECTS ANALYSIS (FMEA)**

**SYSTEM:** ${SYSTEM_NAME}

**POTENTIAL FAILURES:**

### Failure Mode 1: Database Connection Loss
- Severity: 9/10
- Probability: 2/10
- Detectability: 10/10
- RPN = 9 × 2 × 10 = 180

**EFFECTS:**
- API requests fail
- Schedule generation blocked
- Data consistency at risk

**ROOT CAUSES:**
- Network connectivity loss
- Database server down
- Connection pool exhausted

**MITIGATION:**
- Implement connection pooling with retries
- Add circuit breaker pattern
- Monitor connection health
- Alert on connection count > threshold

---

### Failure Mode 2: Memory Leak
- Severity: 7/10
- Probability: 3/10
- Detectability: 5/10
- RPN = 7 × 3 × 5 = 105

**EFFECTS:**
- Gradual performance degradation
- Out-of-memory errors
- Service restart required

**ROOT CAUSES:**
- Unclosed resources
- Circular references
- Event listener leaks

**MITIGATION:**
- Code review for resource leaks
- Memory profiling in tests
- Automatic memory monitoring
- Scheduled restarts

---

### Failure Mode 3: Solver Timeout
- Severity: 5/10
- Probability: 4/10
- Detectability: 10/10
- RPN = 5 × 4 × 10 = 200

**EFFECTS:**
- Schedule generation fails
- Planning blocked for ${BLOCKED_TIME} hours
- Manual assignment fallback required

**ROOT CAUSES:**
- Complex constraint set
- Solver parameter misconfiguration
- Insufficient compute resources

**MITIGATION:**
- Set realistic timeout values
- Implement solver health checks
- Pre-solver validation
- Fallback schedule ready

Generate FMEA report.
```

## 5. CHAOS ENGINEERING TEMPLATE

```
**CHAOS ENGINEERING EXPERIMENTS**

**EXPERIMENT 1: Database Latency Injection**
- Objective: Test system behavior under DB slowness
- Tool: Toxiproxy
- Injection: Add 500ms latency to all queries
- Expected: Graceful degradation
- Acceptable threshold: p95 response time < 2s
- Outcome: ${OUTCOME}

**EXPERIMENT 2: Cache Failure**
- Objective: Test fallback without Redis
- Tool: Network partition (iptables)
- Duration: 5 minutes
- Expected: Queries slower but successful
- Outcome: ${OUTCOME}

**EXPERIMENT 3: Personnel Absence**
- Objective: Test schedule resilience to staffing loss
- Scenario: ${NUM_ABSENCES} residents unavailable
- Expected: Coverage >= ${COVERAGE_THRESHOLD}%
- Outcome: ${OUTCOME}

**EXPERIMENT 4: ACGME Constraint Violation**
- Objective: Detect rule violations in planning
- Injection: Add infeasible constraint
- Expected: Solver detects infeasibility in ${DETECTION_TIME}s
- Outcome: ${OUTCOME}

**RESULTS ANALYSIS:**
- Experiments passed: ${PASSED}/${TOTAL}
- System resilience: ${RESILIENCE_SCORE}
- Recommended improvements: ${IMPROVEMENTS}

Run chaos engineering tests.
```

## 6. CONTINGENCY DRILLS TEMPLATE

```
**CONTINGENCY DRILL SCHEDULE**

**DRILL 1: Database Failover**
- Frequency: Monthly
- Objective: Practice database restoration
- Duration: 30 minutes
- Team: DBA + on-call engineer
- Success criteria: RTO < 15 minutes
- Last drill: ${LAST_DRILL}
- Next drill: ${NEXT_DRILL}
- Pass/Fail: ${RESULT}

**DRILL 2: Personnel Absence Response**
- Frequency: Quarterly
- Objective: Test coverage under absence
- Scenario: ${NUM_ABSENCES} unexpected absences
- Duration: 2 hours
- Team: Operations + Planning
- Success criteria: Coverage >= ${THRESHOLD}%
- Last drill: ${LAST_DRILL}
- Pass/Fail: ${RESULT}

**DRILL 3: Crisis Communication**
- Frequency: Quarterly
- Objective: Test stakeholder notification
- Scenario: System outage announcement
- Duration: 1 hour
- Team: Communications + Leadership
- Success criteria: All stakeholders notified in <= 30 min
- Last drill: ${LAST_DRILL}
- Pass/Fail: ${RESULT}

**DRILL 4: Schedule Emergency Regeneration**
- Frequency: Semi-annually
- Objective: Test rapid replanning
- Scenario: Major constraint change mid-year
- Duration: 4 hours
- Team: Planning + Operations
- Success criteria: New schedule generated in <= 2 hours
- Last drill: ${LAST_DRILL}
- Pass/Fail: ${RESULT}

Schedule and track contingency drills.
```

## 7. RECOVERY DISTANCE ANALYSIS TEMPLATE

```
**RECOVERY DISTANCE ANALYSIS**

**QUESTION:** Minimum number of changes needed to recover from an N-1 event?

**BASELINE SCHEDULE:**
- Personnel: ${PERSONNEL_COUNT}
- Assignments: ${ASSIGNMENT_COUNT}
- Rotations: ${ROTATION_COUNT}

**N-1 SHOCK:**
- Missing resource: ${MISSING_RESOURCE}
- Affected assignments: ${AFFECTED_COUNT}
- Coverage loss: ${COVERAGE_LOSS}%

**RECOVERY STRATEGIES:**

### Strategy 1: Minimal Changes
- Reassign ${MINIMAL_CHANGES} personnel to uncovered slots
- Maintain rotation balance
- Preserve existing preferences
- Distance: ${MINIMAL_DISTANCE} changes

### Strategy 2: Optimization
- Reassign ${OPTIMAL_CHANGES} personnel
- Rebalance all rotations
- Minimize workload variance
- Distance: ${OPTIMAL_DISTANCE} changes

### Strategy 3: Complete Regeneration
- Regenerate entire schedule
- Start from constraints only
- Maximize optimization
- Distance: ${REGEN_DISTANCE} changes

**RECOMMENDED APPROACH:** ${RECOMMENDED}

**RECOVERY TIME:**
- Strategy 1: ${TIME_1} minutes
- Strategy 2: ${TIME_2} minutes
- Strategy 3: ${TIME_3} minutes

Report recovery distance analysis.
```

## 8. STATUS REPORT TEMPLATE

```
**RESILIENCE ENGINEER STATUS REPORT**

**REPORT DATE:** ${TODAY}

**RESILIENCE METRICS:**
- Current resilience score: ${RESILIENCE_SCORE}/100
- Defense level: ${DEFENSE_LEVEL}
- N-1 capability: ${N1_CAPABILITY}
- N-2 capability: ${N2_CAPABILITY}

**VULNERABILITIES:**
- Critical: ${CRITICAL_VULN}
- High: ${HIGH_VULN}
- Medium: ${MEDIUM_VULN}

**CONTINGENCY READINESS:**
- Documented contingencies: ${CONTINGENCY_COUNT}
- Tested in last 30 days: ${TESTED_COUNT}
- Failover time (avg): ${AVG_FAILOVER}
- Recovery time (avg): ${AVG_RECOVERY}

**DRILLS COMPLETED:**
- Month: ${DRILLS_THIS_MONTH}
- Quarter: ${DRILLS_THIS_QUARTER}
- Annual: ${DRILLS_THIS_YEAR}

**INCIDENT ANALYSIS:**
- Incidents this month: ${INCIDENT_COUNT}
- Recovery success rate: ${SUCCESS_RATE}%
- Lessons learned: ${LESSONS}

**NEXT:** ${NEXT_GOALS}
```

---

*Last Updated: 2025-12-31*
*Agent: Resilience Engineer*
*Version: 1.0*
