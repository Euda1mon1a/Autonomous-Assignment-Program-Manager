# SEARCH_PARTY Operations Runbook

> **Purpose:** Operational procedures and troubleshooting guide for SEARCH_PARTY protocol execution
> **Status:** Active
> **Last Updated:** 2025-12-31
> **Audience:** G2_RECON operators, ORCHESTRATOR, technical staff

---

## Quick Start Checklist

Before deploying a SEARCH_PARTY mission, complete this checklist:

```
MISSION DEPLOYMENT CHECKLIST (5 minutes)

PRE-MISSION
□ Define target path (absolute, validated)
□ Identify mission questions (3-5 specific items)
□ Set priority level (P0/P1/P2/P3)
□ Select timeout profile (DASH/RECON/INVESTIGATION)
□ Verify context budget available (~150KB)

TARGET VALIDATION (2 minutes)
□ Path exists and is readable
□ Path is within repo boundaries
□ No secrets in target scope
□ Path is absolute (not relative)
□ Symlink resolution confirms no escapes

RESOURCE CHECK (1 minute)
□ Redis available
□ Agent pool healthy
□ No resource exhaustion warnings
□ Network connectivity confirmed

FINAL SIGN-OFF (1 minute)
□ All items above checked
□ Ready to deploy
□ Expected wall-clock time noted
□ Escalation path clear

STATUS: GREEN / YELLOW / RED
→ Proceed with deployment
```

---

## Timeout Profile Selection Guide

### Decision Tree

```
What's your mission priority and time budget?

P0 EMERGENCY (Must know NOW)
├─ Time available: 1-2 minutes
├─ Profile: DASH (60 seconds)
├─ Risk: HIGH (may miss findings)
├─ Best for: Critical production issues
└─ Accept: Partial intel, complete in shallow depth
    └─ Example: "Is the service down?" (baseline state check)

P1 CRITICAL (Need answer SOON)
├─ Time available: 5-10 minutes
├─ Profile: RECON (120 seconds)
├─ Risk: MEDIUM (balanced coverage)
├─ Best for: High-priority bugs, security reviews
└─ Accept: Full lens coverage with some depth limitations
    └─ Example: "Why did deployment fail?" (comprehensive recon)

P2 IMPORTANT (Need answer TODAY)
├─ Time available: 15+ minutes
├─ Profile: INVESTIGATION (300 seconds)
├─ Risk: LOW (near-complete coverage)
├─ Best for: Technical debt assessment, security audits
└─ Accept: Full depth analysis across all lenses
    └─ Example: "Is this architecture sustainable?" (deep analysis)

P3 ROUTINE (Can wait)
├─ Time available: Any (use INVESTIGATION)
├─ Profile: INVESTIGATION (300 seconds)
├─ Risk: LOW
├─ Best for: Documentation, learning, refactoring prep
└─ Accept: Complete deep analysis
```

### Override Scenarios

**Scenario 1: Target is unusually large**
```
Original Profile: RECON (120s)
Target Size: > 100 files or > 500 commits
Action: Upgrade to INVESTIGATION (300s)
Risk: +180 seconds wall-clock time
Benefit: Sufficient coverage for large targets
```

**Scenario 2: Critical probe needs extension**
```
Condition: INVESTIGATION probe at 50% complete at T=290s
Available Budget: 10 seconds
Decision: Extend 30 seconds (margin for phase 3/4 timeouts)
Risk: Total mission time ~330s instead of 300s
Benefit: INVESTIGATION probe completes (critical for dependencies)
```

**Scenario 3: Time-critical emergency with constrained resources**
```
Mission Priority: P0 (urgent)
Time Budget: 2 minutes
Circuit Breaker Status: HALF-OPEN (system recovering)
Profile: DASH (60 seconds)
Expected Outcome: 7-8 probes complete, minimal cross-reference
Fallback: If < 5 probes succeed, escalate to ORCHESTRATOR
```

---

## Common Mission Patterns

### Pattern 1: Bug Investigation (P1)

**Use Case:** Resident reports error, need root cause quickly

**Mission Setup:**
```
Target: /home/user/Autonomous-Assignment-Program-Manager/backend/app/services/
Profile: RECON (120s)
Questions:
1. What errors are visible in logs?
2. What changed recently that could cause this?
3. Are dependencies broken?
4. Is there a compliance violation?
5. What's the single most likely cause?

Expected Probes:
✓ PERCEPTION (current error state)
✓ HISTORY (recent changes)
✓ INVESTIGATION (dependencies)
✓ ARCANA (compliance check)
✓ SURVIVAL (edge case handling)
```

**Post-Mission Action:**
- Check PERCEPTION vs HISTORY discrepancy (regression detector)
- Follow root cause in INVESTIGATION findings
- If ARCANA flags violation, escalate immediately
- Run targeted fix based on 5-probe consensus

**Follow-up:** If < 5 probes succeed, extend to INVESTIGATION profile and re-run

---

### Pattern 2: Security Audit (P2)

**Use Case:** Compliance review or vulnerability assessment

**Mission Setup:**
```
Target: /home/user/Autonomous-Assignment-Program-Manager/backend/app/
Profile: INVESTIGATION (300s)
Questions:
1. What security vulnerabilities exist?
2. Are secrets exposed anywhere?
3. Is HIPAA/OPSEC properly handled?
4. What's the attack surface?
5. Are there hidden data flows?

Expected Probes:
✓ STEALTH (hidden vulnerabilities)
✓ ARCANA (compliance requirements)
✓ INVESTIGATION (data flow paths)
✓ PERCEPTION (obvious exposures)
✓ RELIGION (sacred law adherence)
```

**Post-Mission Action:**
- STEALTH findings are highest priority (security)
- ARCANA flags indicate regulatory risk
- INVESTIGATION data flows inform threat model
- Build mitigation plan from all findings

**Follow-up:** Critical findings (STEALTH) may require additional targeted probes

---

### Pattern 3: Architecture Review (P2)

**Use Case:** Evaluate technical debt or design soundness

**Mission Setup:**
```
Target: /home/user/Autonomous-Assignment-Program-Manager/backend/app/scheduling/
Profile: INVESTIGATION (300s)
Questions:
1. Is this design sustainable?
2. What technical debt exists?
3. Is the implementation matching design intent?
4. Are there performance issues?
5. How resilient is this to failures?

Expected Probes:
✓ INSIGHT (design intent)
✓ NATURE (ecosystem health)
✓ MEDICINE (performance vitals)
✓ SURVIVAL (resilience assessment)
✓ INVESTIGATION (architectural coupling)
```

**Post-Mission Action:**
- INSIGHT vs INVESTIGATION discrepancy = implementation drift
- NATURE findings drive refactoring priority
- MEDICINE identifies immediate bottlenecks
- SURVIVAL gaps drive resilience improvements

**Follow-up:** Use findings to scope refactoring work

---

## Troubleshooting Guide

### Symptom: Probe Timeout (All Probes Stalling)

**Diagnosis:**
```
Observation: All probes reach T=timeout_limit simultaneously
Likely Cause: Target scope too large, network latency spike, resource contention
Severity: MODERATE-HIGH
```

**Recovery Steps:**
```
Step 1: Check circuit breaker status
        └─ If OPEN: Wait 5 minutes, system recovering
           └─ Do NOT retry mission yet

Step 2: If CLOSED, check resource metrics
        ├─ Memory usage > 80%? → Free resources, retry
        ├─ CPU usage > 90%? → Wait for load to drop, retry
        ├─ Network latency > 500ms? → Extend timeout +60s
        └─ If none apply, proceed to Step 3

Step 3: Reduce target scope
        ├─ Instead of full directory: probe single file
        ├─ Reduce context size by filtering unnecessary info
        ├─ Use selective probes (5-6) instead of all 10
        └─ Retry with reduced scope

Step 4: If still timing out
        ├─ Escalate to INVESTIGATION profile (300s timeout)
        ├─ Or split into multiple focused missions
        └─ Last resort: Abort, escalate to ORCHESTRATOR
```

**Prevention:**
- Pre-flight check: Is target > 50 files? → Use INVESTIGATION profile
- Monitor timeout frequency: If > 5% of missions timeout → platform issue
- Document consistently timing-out probes: May need override rules

---

### Symptom: Probe Crash (Specific Probe Fails)

**Diagnosis:**
```
Observation: Single probe returns null/error, others succeed
Likely Cause: Logic bug in probe, invalid input, unhandled exception
Severity: MODERATE
```

**Recovery Steps:**
```
Step 1: Identify crashed probe
        └─ Note probe name and error message

Step 2: Classify crash type
        ├─ Permission denied? → Check access control, retry with escalated permissions
        ├─ Timeout mid-execution? → Probe takes longer than expected
        ├─ Index/null pointer error? → Logic bug in probe
        ├─ Resource exhaustion? → Out of memory, file handles
        └─ Unknown error? → Escalate to developers

Step 3: Retry with exponential backoff
        ├─ Attempt 1: Retry immediately (same parameters)
        ├─ Attempt 2: Wait 5 seconds, retry
        ├─ Attempt 3: Failed after 2 retries
        │  └─ Mark probe as FAILED
        │  └─ Continue mission with 9 probes
        └─ If critical probe (PERCEPTION/INVESTIGATION): Flag mission DEGRADED

Step 4: Post-mission
        ├─ Log crash details for investigation
        ├─ If same probe crashes in next 3 missions: Escalate to developers
        └─ Consider using selective probe set (skip crashing probe temporarily)
```

**Prevention:**
- After probe crash, validate inputs were valid (scope, permissions)
- Check platform logs for system-level errors
- If recurring: File bug against probe logic

---

### Symptom: Low Confidence Findings (Most Probes Partial)

**Diagnosis:**
```
Observation: Most/all probes report LOW confidence, few high-signal findings
Likely Cause: Target scope unclear, mission questions ambiguous, insufficient depth
Severity: LOW
```

**Recovery Steps:**
```
Step 1: Review mission context
        ├─ Were questions clear and specific?
        ├─ Was scope boundary clearly communicated?
        ├─ Did probes have enough time (timeout exceeded)?
        └─ If any "no", re-run with clarified context

Step 2: Check completion %
        ├─ If < 50% probes marked COMPLETE: Extend timeout profile
        ├─ If most PARTIAL: Accept for now, schedule follow-up
        ├─ If all COMPLETE: Confidence downgrade is legitimate (ambiguous target)
        └─ Continue with available intel

Step 3: Schedule focused follow-up
        ├─ Deploy single probe with sharp focus on confidence gaps
        ├─ Example: If INVESTIGATION returns LOW, do targeted dependency probe
        └─ Use RECON or INVESTIGATION profile for follow-up

Step 4: Learn for next time
        ├─ What made context unclear?
        ├─ How could questions be more specific?
        ├─ Should timeout been extended?
        └─ Update mission templates if systematic issue
```

**Prevention:**
- Spend time on mission questions (clarity → signal)
- Keep scope narrow and bounded
- Use INVESTIGATION profile when uncertain

---

### Symptom: Circuit Breaker Tripped (OPEN State)

**Diagnosis:**
```
Observation: Circuit breaker state = OPEN
Condition: > 3 consecutive probe failures OR crash rate > 30%
Severity: CRITICAL
```

**Recovery Steps:**
```
Step 1: STOP - Do not spawn new missions
        └─ System is recovering from cascade failure

Step 2: Investigate cause
        ├─ Check Redis availability
        ├─ Check agent execution environment
        ├─ Check network connectivity
        ├─ Check system resource metrics
        ├─ Check recent platform changes
        └─ Log findings

Step 3: Fix root cause
        ├─ If Redis down: Restart Redis service
        ├─ If agent pool exhausted: Scale resources
        ├─ If network issue: Resolve connectivity
        ├─ If recent code change broke probes: Rollback or fix
        └─ Once fixed, proceed to Step 4

Step 4: Reset circuit breaker
        └─ Location: Redis key `search_party:circuit_breaker`
        └─ Set state to HALF-OPEN (allows single test probe)
        └─ Circuit transitions to CLOSED if test succeeds

Step 5: Validate recovery
        ├─ Deploy test mission with single probe
        ├─ If successful: Circuit closes, resume normal operations
        ├─ If failed: Back to OPEN, investigate further
        └─ Monitor next 5 missions closely

Step 6: Post-incident
        ├─ Root cause analysis: Why did cascade happen?
        ├─ Preventive measures: What safeguards to add?
        ├─ Monitoring improvement: How to detect earlier?
        └─ Document incident for future reference
```

**Prevention:**
- Monitor circuit breaker status in real-time
- Alert when trips occur (automatic escalation to ORCHESTRATOR)
- Improve probe robustness (add error handling)
- Implement chaos testing to find failure modes

---

### Symptom: Discrepancies Not Detected (Cross-Reference Gap)

**Diagnosis:**
```
Observation: All probes return consistent findings
Condition: Expected at least 1-2 discrepancies (indicates shallow analysis)
Severity: LOW (informational)
```

**Recovery Steps:**
```
Step 1: Evaluate mission scope
        ├─ Is target too simple (single file)?
        ├─ Are all probes asking superficial questions?
        ├─ Is timeout cutting off deep analysis?
        └─ If any yes, consider deeper investigation

Step 2: Review probe findings for subtle discrepancies
        ├─ PERCEPTION: "Tests passing" vs HISTORY: "Major refactor 3 days ago"
        ├─ INVESTIGATION: "Highly coupled" vs INSIGHT: "Designed as modular"
        ├─ ARCANA: "Compliant" vs SURVIVAL: "No error handling in edge case"
        └─ Some discrepancies are subtle, may be valid

Step 3: Assess quality
        ├─ Do findings make sense together?
        ├─ Is consistency because scope is simple (OK)?
        ├─ Or is consistency because probes are shallow (NOT OK)?
        └─ Decision: Continue or escalate probe depth

Step 4: If legitimately no discrepancies
        ├─ Log as clean scan
        ├─ Can proceed with confidence
        └─ No action needed

Step 5: If probes seem shallow
        ├─ Extend timeout profile (RECON → INVESTIGATION)
        ├─ Clarify mission questions (more specific)
        ├─ Reduce scope (helps focus depth)
        └─ Retry
```

**Prevention:**
- Complexity of target determines expected discrepancies
- Simple targets = few discrepancies (OK)
- Complex targets = many discrepancies (expected)
- Track average discrepancies per target size

---

## Performance Tuning

### Context Overhead Reduction

**Problem:** Mission context takes 250KB for 10 probes (2x overhead)

**Solution 1: Compress Context**
```
BEFORE (verbose):
Mission context includes full file listings, complete git log, etc.
Size: ~125KB context → 250KB with 10 probes

AFTER (compressed):
Mission context includes only essential info, reference to external docs
Size: ~50KB context → 100KB with 10 probes
Savings: 60% reduction
```

**Solution 2: Use Selective Probes**
```
BEFORE:
Spawn all 10 probes for simple single-file target
Context overhead: 2x

AFTER:
Deploy 5 focused probes (PERCEPTION, INVESTIGATION, ARCANA, HISTORY, INSIGHT)
Context overhead: 1x
Tradeoff: Miss NATURE/MEDICINE/SURVIVAL/STEALTH insights (acceptable for simple targets)
```

**Solution 3: Batch Related Missions**
```
BEFORE:
Mission A (target X) - 120s
Mission B (target Y) - 120s
Total: 240s wall-clock

AFTER:
Batch A+B with shared context framework
├─ Common probe pool reused
├─ Context sharing between missions
└─ Total: 180s wall-clock (20% faster)
```

---

### Wall-Clock Time Optimization

**Baseline:** 1 probe with 120s timeout = 120s wall-clock

**Optimization Strategies:**

| Strategy | Time Impact | Complexity | Recommendation |
|----------|-------------|-----------|---|
| Run 1 probe (sequential) | 120s | Simple | Good for urgent quick-checks |
| Run 10 probes (parallel) | 120s (no penalty!) | Moderate | Standard SEARCH_PARTY |
| Run 10 + follow-up probe | 240s | Complex | Use when gaps detected |
| Reduce timeout to DASH | 60s | Simple | Emergency missions only |
| Use selective probes (5) | 120s (+ 2x context saved) | Moderate | Good for simple targets |
| Cache results between runs | -30-50% repeat time | Complex | Enterprise deployments |

**Optimal Strategy by Scenario:**

```
Scenario: Need baseline state NOW (< 1 min)
└─ DASH profile + PERCEPTION probe only
   └─ 60s wall-clock, minimal context
   └─ Sacrifice: 9 lenses, deep analysis

Scenario: Bug investigation (5-10 min available)
└─ RECON profile + all 10 probes
   └─ 120s wall-clock, balanced coverage
   └─ Sweet spot: Context cost acceptable, time budget works

Scenario: Deep security audit (unlimited time)
└─ INVESTIGATION profile + all 10 probes
   └─ 300s wall-clock, maximum depth
   └─ Tradeoff: 3x slower but near-complete coverage

Scenario: Simple targeted check (5 min available)
└─ RECON profile + 5 selective probes
   └─ 120s wall-clock, 1x context overhead
   └─ Good balance: Speed + enough lenses
```

---

## Monitoring Dashboard Template

Use this template to monitor SEARCH_PARTY health:

```
SEARCH_PARTY OPERATIONS DASHBOARD

REAL-TIME STATUS
├─ Circuit Breaker State: CLOSED / HALF-OPEN / OPEN
├─ Active Missions: N running, last completed T ago
├─ Agent Pool Health: M agents available, X% utilized
└─ Platform Status: GREEN / YELLOW / RED

METRICS (LAST 24 HOURS)
├─ Total Missions Executed: 47
├─ Probe Completion Rate: 99.2% (target > 99%)
├─ Timeout Frequency: 2.1% (target < 5%)
├─ Average Probe Crash Rate: 0.3% (target 0%)
├─ Average Context Overhead: 2.1x (target ~2x)
├─ Intel Actionability: 87% (target > 80%)
└─ Average Synthesis Time: 3.5m (target < 5m)

TOP ISSUES (LAST 7 DAYS)
├─ 3 timeouts on large scheduling targets
├─ 1 circuit breaker trip (database unavailability)
├─ High context overhead on system-wide audits (2.8x)
└─ 2 probes consistently slower than others

TREND ANALYSIS
├─ Completion rate: STABLE (no drift)
├─ Timeout rate: UP 0.5% (monitor)
├─ Context overhead: STABLE
├─ Crash rate: DOWN (recent robustness fixes)
└─ Actionability: UP 2% (better questions)

ALERTS
├─ ⚠️ WARNING: Timeout rate 2.1% (threshold 5%) - monitor
├─ ℹ️ INFO: Context overhead 2.1x (slightly above target)
└─ ✓ OK: No critical issues
```

---

## Escalation Path

### Decision Tree

```
Something went wrong during mission execution

Critical Failure (circuit breaker tripped, 0 probes completed)
├─ Action: STOP immediately
├─ Notify: ORCHESTRATOR
├─ Investigation: System-level (Redis, network, resources)
├─ Resolution: Fix platform issue, reset circuit breaker
└─ Follow-up: Root cause analysis + preventive measures

Major Failure (< 5 probes complete)
├─ Action: Abort mission
├─ Notify: ORCHESTRATOR
├─ Investigation: Scope too large? Security breach?
├─ Resolution: Reduce scope or escalate security review
└─ Follow-up: Re-run with corrected parameters

Moderate Failure (5-9 probes complete)
├─ Action: Accept partial intel, flag as DEGRADED
├─ Notify: Requesting agent (G2_RECON or ORCHESTRATOR)
├─ Investigation: Which probes failed? Why?
├─ Resolution: Identify gaps, schedule follow-up
└─ Follow-up: Targeted probes for missing lenses

Minor Failure (all probes complete, low confidence)
├─ Action: Deliver intel, note confidence levels
├─ Notify: Requesting agent
├─ Investigation: Were questions clear enough?
├─ Resolution: Schedule focused follow-up
└─ Follow-up: Second mission with refined questions

No Failure (all probes complete, high confidence)
├─ Action: Deliver full intel brief
├─ Notify: Requesting agent
└─ Follow-up: None needed (close mission)
```

### Contact List

```
ESCALATION CONTACTS:

ORCHESTRATOR (All escalations)
├─ Role: Mission approval, resource decisions
├─ Threshold: Major/Critical failures
├─ Action: Approve retry, investigate platform
└─ Response: Within 5 minutes

G2_RECON (Mission owner)
├─ Role: Validate mission parameters, accept partial results
├─ Threshold: Moderate/Minor failures
├─ Action: Decide retry vs accept
└─ Response: Within 2 minutes

SECURITY TEAM (Isolation breach only)
├─ Role: Investigate potential security incidents
├─ Threshold: Probe attempts access outside scope
├─ Action: Security review, scope validation
└─ Response: Immediate escalation

DEVELOPERS (Probe crashes)
├─ Role: Debug logic errors in probe code
├─ Threshold: Same probe crashes in > 3 missions
├─ Action: File bug, implement fix
└─ Response: Within 1 sprint cycle
```

---

## Post-Incident Review Template

After significant incident (circuit breaker trip, multiple crashes, etc.):

```
SEARCH_PARTY INCIDENT REVIEW

INCIDENT SUMMARY
Date: [date]
Severity: [CRITICAL/MAJOR/MODERATE]
Duration: [T minutes]
Impact: [N missions affected]

TIMELINE
T+0m: [What happened]
T+5m: [Initial response]
T+15m: [Escalation to ORCHESTRATOR]
T+30m: [Remediation started]
T+60m: [System recovered]

ROOT CAUSE
Primary: [e.g., "Redis connection pool exhausted"]
Contributing: [e.g., "Large missions with 10 probes each"]
Detection: [How did we notice?]

IMPACT ASSESSMENT
├─ Missions affected: N
├─ Data loss: None / [describe]
├─ Mean time to recovery: M minutes
└─ SLA impact: Yes/No

PREVENTIVE MEASURES
├─ Action 1: [Implement rate limiting on large missions]
├─ Action 2: [Improve circuit breaker thresholds]
├─ Action 3: [Add monitoring for resource exhaustion]
└─ Assigned to: [Owner] by [Date]

LESSONS LEARNED
├─ What should we have caught earlier?
├─ What process gap exists?
├─ How do we prevent recurrence?
└─ What did we learn?

FOLLOW-UP
├─ Preventive measures status: [In progress/Complete/Blocked]
├─ Monitoring improvements: [Implemented/Pending]
└─ Next review: [Date]
```

---

*This runbook is a living document. Update procedures as operational experience grows.*
