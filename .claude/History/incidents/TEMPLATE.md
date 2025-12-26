# Incident Report - [Incident Title]

**Date:** YYYY-MM-DD
**Incident ID:** [Unique identifier, e.g., INC-042, CRITICAL-2025-08-05]
**Reported By:** [Agent or person name]
**Severity:** [CRITICAL | HIGH | MEDIUM | LOW]
**Status:** [INVESTIGATING | MITIGATED | RESOLVED | CLOSED]

---

## Summary

[One-sentence summary of incident and impact]

**Example:** "Solver timeout during Block 11 generation caused 45-minute delay in schedule release and required constraint relaxation to complete."

---

## Classification

**Incident Type:**
- [ ] System Failure (service down, database crash)
- [ ] Performance Degradation (slow response, timeout)
- [ ] Data Integrity (corrupted data, inconsistent state)
- [ ] Security Event (unauthorized access, breach attempt)
- [ ] ACGME Compliance (violation detected in production)
- [ ] User Error (misconfiguration, incorrect input)
- [ ] Integration Failure (API down, third-party service)
- [ ] Other: ___________

**Severity Level:**

| Level | Definition | Response Time | Escalation |
|-------|------------|---------------|------------|
| **CRITICAL** | Service outage, data loss, compliance violation | Immediate | Faculty + ARCHITECT |
| **HIGH** | Degraded service, significant delay, security concern | < 1 hour | ARCHITECT or ORCHESTRATOR |
| **MEDIUM** | Minor degradation, workaround available | < 4 hours | ORCHESTRATOR |
| **LOW** | Cosmetic issue, minimal impact | < 24 hours | Log only |

**This Incident:** [CRITICAL | HIGH | MEDIUM | LOW]

**Justification:** [Why this severity level?]

---

## Timeline of Events

**All times in [Timezone, e.g., HST (UTC-10)]**

### Detection

**Incident Detected:** [YYYY-MM-DD HH:MM:SS]
**Detected By:** [Agent name, monitoring system, or user report]
**Detection Method:**
- [ ] Automated monitoring (health check, alert)
- [ ] User complaint (email, phone call)
- [ ] Agent self-reported (error during operation)
- [ ] Routine audit (discovered during review)
- [ ] Other: ___________

**Initial Symptoms:**
- [e.g., "Solver timeout after 30 minutes during Block 11 schedule generation"]
- [e.g., "ACGME compliance alert: PGY2-01 projected to exceed 80-hour limit"]
- [e.g., "Database connection pool exhausted, API requests timing out"]

### Response Timeline

| Time | Event | Actor | Action Taken |
|------|-------|-------|--------------|
| HH:MM:SS | Incident detected | [Who] | [What happened] |
| HH:MM:SS | Initial triage | [Who] | [Assessment performed] |
| HH:MM:SS | Escalation | [Who] | [Escalated to whom] |
| HH:MM:SS | Mitigation started | [Who] | [What was done] |
| HH:MM:SS | Service restored | [Who] | [How service recovered] |
| HH:MM:SS | Root cause identified | [Who] | [Finding] |
| HH:MM:SS | Permanent fix applied | [Who] | [Solution implemented] |
| HH:MM:SS | Incident closed | [Who] | [Verification completed] |

**Total Duration:**
- Detection → Mitigation: [e.g., 5 minutes]
- Detection → Resolution: [e.g., 45 minutes]
- Detection → Closure: [e.g., 2 hours]

---

## Impact Assessment

### User Impact

**Affected Users:**
- Residents: [Count, e.g., 12 residents]
- Faculty: [Count, e.g., 3 faculty]
- Administrators: [Count, e.g., 1 coordinator]
- External Services: [e.g., Calendar integration, email notifications]

**Service Availability:**
- Service uptime: [e.g., 99.2% (45 min downtime in 30 days)]
- Features affected: [List features unavailable or degraded]
- Duration of impact: [e.g., 45 minutes]

**User Actions Required:**
- [ ] None (transparent recovery)
- [ ] Retry operation (e.g., re-submit swap request)
- [ ] Manual workaround (e.g., contact coordinator)
- [ ] Data re-entry (e.g., re-input schedule preferences)

### Business Impact

**ACGME Compliance:**
- Compliance status: [MAINTAINED | VIOLATED | AT_RISK]
- Violations introduced: [Count, e.g., 0]
- Violations prevented: [Count, if applicable]

**Schedule Operations:**
- Schedule generation: [DELAYED | FAILED | COMPLETED]
- Swaps processed: [Count affected, e.g., 3 swaps delayed]
- Coverage gaps: [YES | NO] - If YES, describe mitigation

**Data Integrity:**
- Data loss: [YES | NO] - If YES, quantify (e.g., "5 swap requests lost")
- Data corruption: [YES | NO] - If YES, describe extent
- Recovery successful: [YES | PARTIAL | NO]

### Financial/Operational Impact

**Estimated Impact:**
- Manual intervention hours: [e.g., 2 person-hours]
- Delayed operations: [e.g., Schedule release delayed 45 minutes]
- Opportunity cost: [e.g., Coordinator unable to process 3 urgent swaps]
- Recovery cost: [e.g., Developer time: 4 hours]

---

## Root Cause Analysis

### Investigation Methodology

**Tools Used:**
- [ ] Log analysis (application logs, system logs)
- [ ] Database query (transaction logs, slow query log)
- [ ] Code review (recent commits, related PRs)
- [ ] Profiling (CPU, memory, I/O analysis)
- [ ] Reproduction (test environment recreation)
- [ ] 5 Whys technique
- [ ] Fishbone diagram (Ishikawa)

**Investigation Timeline:**
- Started: [YYYY-MM-DD HH:MM:SS]
- Completed: [YYYY-MM-DD HH:MM:SS]
- Duration: [e.g., 1.5 hours]

### Symptoms Observed

**System Behavior:**
- [e.g., "Solver process CPU usage 100% for 30 minutes"]
- [e.g., "Memory consumption grew to 8GB (4x normal)"]
- [e.g., "Database connection pool saturated (100/100 connections)"]

**Error Messages:**
```
[Paste relevant error messages, stack traces, or log excerpts]

Example:
ERROR 2025-08-05 14:32:01 - Solver timeout after 1800 seconds
  File: backend/app/scheduling/engine.py, line 247
  Solver status: UNKNOWN (time limit exceeded)
  Constraints: 1247 hard, 358 soft
  Variables: 3650 (unassigned: 1200)
```

**Affected Components:**
- Primary: [e.g., Scheduling Engine (backend/app/scheduling/engine.py)]
- Secondary: [e.g., Database (assignment table row locking)]
- Related: [e.g., API endpoints (schedule generation endpoint timed out)]

### Root Cause

**Primary Cause:**
[Detailed explanation of the fundamental reason the incident occurred]

**Example:**
"Over-constrained scheduling problem for Block 11. Constraint catalog included 1247 hard constraints (35% increase from Block 10) due to:
1. 5 leave requests (vs. 3 in Block 10)
2. 2 new credential requirements (N95 Fit, Flu Vax added mid-year)
3. 3 pre-assigned TDY blocks
4. Redundant continuity constraints (should have been Tier 3, were Tier 2)

Solver unable to find feasible solution within 30-minute timeout. Exponential search space explosion due to constraint interdependencies."

**Contributing Factors:**
1. [Factor 1: e.g., "Constraint catalog not pruned for obsolete rules"]
2. [Factor 2: e.g., "No early feasibility detection (fail-fast logic)"]
3. [Factor 3: e.g., "Solver timeout increased from 15min → 30min (masked problem)"]

**Why It Wasn't Caught Earlier:**
- [ ] No test case covering this scenario
- [ ] Monitoring alert threshold too high
- [ ] Edge case not anticipated in design
- [ ] Recent code change introduced regression
- [ ] External factor (e.g., database performance degraded)

### 5 Whys Analysis

1. **Why did the schedule generation fail?**
   - [e.g., "Solver timed out after 30 minutes without finding feasible solution."]

2. **Why did the solver timeout?**
   - [e.g., "Over-constrained problem: 1247 constraints for 60 blocks (20:1 ratio)."]

3. **Why was the problem over-constrained?**
   - [e.g., "Redundant continuity constraints + new credential requirements + increased leave requests."]

4. **Why were redundant constraints not detected?**
   - [e.g., "No automated constraint pruning or conflict detection during pre-flight."]

5. **Why is there no constraint pruning?**
   - [e.g., "Constraint catalog assumed to be manually curated. No validation in CI/CD pipeline."]

**Root Cause:** [Fundamental issue identified]

---

## Immediate Mitigation

**Actions Taken During Incident:**

### Step 1: [Action Name]
- **Time:** [HH:MM:SS]
- **Action:** [What was done]
- **Performed By:** [Who did it]
- **Result:** [Outcome - successful/failed]
- **Rationale:** [Why this action]

**Example:**
- **Time:** 14:35:00
- **Action:** Activated solver kill-switch to abort runaway process
- **Performed By:** SCHEDULER agent (automated)
- **Result:** Successful - solver process terminated gracefully
- **Rationale:** Prevent resource exhaustion, allow diagnosis

### Step 2: [Action Name]
- **Time:** [HH:MM:SS]
- **Action:** [What was done]
- **Performed By:** [Who did it]
- **Result:** [Outcome]
- **Rationale:** [Why this action]

### Step 3: [Action Name]
- **Time:** [HH:MM:SS]
- **Action:** [What was done]
- **Performed By:** [Who did it]
- **Result:** [Outcome]
- **Rationale:** [Why this action]

**Temporary Workaround:**
- [Describe interim solution used to restore service]
- [e.g., "Relaxed Soft-2 continuity constraints, regenerated schedule successfully in 8m 12s."]

**Service Restoration:**
- Service restored at: [HH:MM:SS]
- Method: [e.g., "Schedule published with relaxed constraints, notified residents of delayed release"]
- Verification: [e.g., "ACGME compliance validated - 0 violations post-mitigation"]

---

## Permanent Remediation

**Long-Term Fixes Applied:**

### Fix 1: [Fix Name]
- **Problem Addressed:** [Specific root cause or contributing factor]
- **Solution:** [Technical implementation]
- **Code Changes:**
  - Files modified: [List files]
  - PR: [Link to pull request or commit hash]
  - Deployed: [YYYY-MM-DD]
- **Testing:** [How verified]
- **Validation:** [Success criteria met]

**Example:**
- **Problem Addressed:** No automated constraint pruning before generation
- **Solution:** Implemented constraint conflict detector in pre-flight checks
- **Code Changes:**
  - Files: `backend/app/scheduling/constraint_validator.py` (new)
  - PR: #347 "Add constraint conflict detection to pre-flight"
  - Deployed: 2025-08-07
- **Testing:** Unit tests + integration test with Block 11 scenario
- **Validation:** Block 12 generation completed in 5m 02s (baseline: 4m 30s) ✅

### Fix 2: [Fix Name]
- **Problem Addressed:** [Issue]
- **Solution:** [Implementation]
- **Code Changes:** [Details]
- **Testing:** [How verified]
- **Validation:** [Results]

### Fix 3: [Fix Name]
- **Problem Addressed:** [Issue]
- **Solution:** [Implementation]
- **Code Changes:** [Details]
- **Testing:** [How verified]
- **Validation:** [Results]

**Infrastructure Changes:**
- [Any monitoring, alerting, or system configuration updates]
- [e.g., "Added solver progress monitoring: alert if >50% timeout elapsed without progress."]

**Process Changes:**
- [Any workflow or procedure updates]
- [e.g., "Updated schedule generation checklist: constraint count must be ≤ 15:1 ratio to blocks."]

---

## Prevention Measures

**To Prevent Recurrence:**

### Technical Safeguards
1. [e.g., "Constraint catalog size limit: max 800 hard constraints for 60-block period"]
2. [e.g., "Early feasibility detection: abort if no solution found in first 5 minutes"]
3. [e.g., "Solver progress monitoring: alert if convergence rate drops below threshold"]

### Process Improvements
1. [e.g., "Quarterly constraint audit: review and prune obsolete rules"]
2. [e.g., "Pre-flight validation: simulate 10% sample before full generation"]
3. [e.g., "Constraint impact analysis: measure how each constraint affects solve time"]

### Monitoring & Alerting
1. [e.g., "Alert if solver time >10 minutes (75% of baseline)"]
2. [e.g., "Daily constraint count trend: flag >10% week-over-week increase"]
3. [e.g., "Dashboard widget: constraint-to-block ratio visualization"]

### Documentation Updates
1. [e.g., "Updated `docs/architecture/SOLVER_ALGORITHM.md` with constraint limits"]
2. [e.g., "Added constraint pruning guide to `docs/development/DEBUGGING_WORKFLOW.md`"]
3. [e.g., "Updated CONSTITUTION.md: max constraint density rule"]

### Testing Enhancements
1. [e.g., "Added stress test: 1000-constraint scenario (expected to fail gracefully)"]
2. [e.g., "Created regression test for Block 11 exact scenario"]
3. [e.g., "Parameterized constraint tests: vary constraint count, measure solve time"]

---

## Lessons Learned

**What Went Well:**
- [e.g., "Solver kill-switch worked perfectly - prevented resource exhaustion"]
- [e.g., "Automated backup before generation prevented data loss"]
- [e.g., "Incident detection was immediate via monitoring alert"]

**What Went Poorly:**
- [e.g., "No early warning that constraint catalog was growing unsustainably"]
- [e.g., "Solver timeout too long (30 min) - should have failed faster"]
- [e.g., "No visibility into solver progress during long runs"]

**What We Learned:**
- [e.g., "Constraint complexity is non-linear - small increases can cause exponential solve time"]
- [e.g., "Manual constraint curation doesn't scale - need automated validation"]
- [e.g., "Timeout is not a substitute for feasibility detection"]

**Surprising Insights:**
- [e.g., "Redundant constraints don't just slow solver - they can make problems unsolvable"]
- [e.g., "Solver progress monitoring would have detected stalled convergence 15 minutes earlier"]

---

## Follow-Up Actions

**Immediate (within 24 hours):**
- [X] Service restored
- [X] Root cause identified
- [X] Temporary fix deployed
- [ ] Affected users notified
- [ ] Post-incident review scheduled

**Short-Term (within 1 week):**
- [ ] Permanent fix implemented
- [ ] Tests added for this scenario
- [ ] Monitoring enhanced (solver progress alerts)
- [ ] Documentation updated (constraint limits)
- [ ] Post-mortem shared with team

**Long-Term (within 1 month):**
- [ ] Quarterly constraint audit process established
- [ ] Automated constraint pruning implemented
- [ ] Early feasibility detection added
- [ ] Stress testing for constraint complexity
- [ ] CONSTITUTION amendment (constraint density rule)

**Verification:**
- [ ] Block 12 generation successful (validate fix)
- [ ] Monitoring alerts functional (test with synthetic load)
- [ ] Team training on new constraint validation process
- [ ] MetaUpdater review (ensure pattern detection active)

---

## Related Incidents

**Similar Incidents:**
- [e.g., "INC-028 (2025-06-12): Solver timeout during academic year generation"]
- [e.g., "INC-015 (2025-04-03): Over-constrained problem for specialty clinic scheduling"]

**Pattern Analysis:**
- Recurrence: [e.g., "3rd solver timeout incident in 90 days - escalating pattern"]
- Common factor: [e.g., "All incidents involved >1000 constraints and <100 blocks"]
- Trend: [e.g., "Constraint catalog growing 15% per block (unsustainable)"]

**MetaUpdater Action:**
- [e.g., "MetaUpdater flagged recurring solver timeout pattern. Recommend systematic constraint reduction."]
- [e.g., "Propose: Add constraint budget per block (max 15:1 ratio) as hard limit in CONSTITUTION."]

---

## Stakeholder Communication

**Internal Communication:**

**Incident Notification (sent at HH:MM:SS):**
- **To:** [e.g., Faculty, Coordinators, ARCHITECT]
- **Subject:** [e.g., "INCIDENT: Schedule generation delayed - mitigation in progress"]
- **Content:** [Brief summary, impact, ETA for resolution]

**Resolution Notification (sent at HH:MM:SS):**
- **To:** [e.g., All affected users]
- **Subject:** [e.g., "RESOLVED: Block 11 schedule published (45-min delay)"]
- **Content:** [Summary of incident, resolution, apology if needed]

**Post-Mortem Report:**
- **To:** [e.g., Program Director, Faculty]
- **Date:** [YYYY-MM-DD]
- **Format:** [e.g., Email summary + detailed document link]
- **Key Messages:**
  1. [What happened]
  2. [Why it happened]
  3. [How we fixed it]
  4. [How we prevent it]

**External Communication (if required):**
- [ ] ACGME notification required: [YES | NO]
- [ ] Institutional reporting: [YES | NO]
- [ ] User apology/explanation: [YES | NO]

---

## Metrics & Analytics

**Incident Metrics:**
- Detection time: [e.g., < 1 minute (automated alert)]
- Response time: [e.g., 3 minutes (human engagement)]
- Mitigation time: [e.g., 5 minutes (service degraded → restored)]
- Resolution time: [e.g., 45 minutes (temporary → permanent fix)]

**Service Level Impact:**
- Uptime this month: [e.g., 99.2% (45 min downtime)]
- Target SLA: [e.g., 99.9%]
- SLA breach: [YES | NO]

**Performance Degradation:**
- Baseline solve time: [e.g., 4m 30s]
- Incident solve time: [e.g., TIMEOUT at 30m]
- Post-fix solve time: [e.g., 5m 02s]

**User Satisfaction:**
- Complaints received: [Count]
- Satisfaction survey (if conducted): [e.g., 3.8/5.0]
- Net Promoter Score impact: [e.g., -2 points]

---

## Review & Sign-Off

**Incident Review:**
- Review Date: [YYYY-MM-DD]
- Reviewed By: [Names/Roles]
- Review Method: [e.g., Post-mortem meeting, async document review]

**Key Takeaways (from review):**
1. [e.g., "Constraint complexity is a critical risk - needs proactive management"]
2. [e.g., "Solver progress visibility is essential for long-running operations"]
3. [e.g., "Automated safeguards (kill-switch, backup) prevented worse outcomes"]

**Action Items Assigned:**
- [ ] [Action 1] - Owner: [Name] - Due: [Date]
- [ ] [Action 2] - Owner: [Name] - Due: [Date]
- [ ] [Action 3] - Owner: [Name] - Due: [Date]

**Incident Closure:**
- [ ] Root cause identified and documented
- [ ] Permanent fix deployed and validated
- [ ] Prevention measures implemented
- [ ] Documentation updated
- [ ] Team notified and trained
- [ ] MetaUpdater reviewed and integrated learnings

**Closed By:** [Name/Agent]
**Closed At:** [YYYY-MM-DD HH:MM:SS]
**Final Status:** [RESOLVED | RESOLVED_WITH_WORKAROUND]

---

## Attachments

**Related Files:**
- [ ] Error logs: [Path or link]
- [ ] Database dump (if applicable): [Path - NEVER commit to git]
- [ ] Profiling data: [Path]
- [ ] Code fix PR: [GitHub PR link]
- [ ] Post-mortem slides: [Path or link]

**Code References:**
- Affected components: [File paths + commit hashes]
- Fix implementation: [PR #XXX or commit hash]
- Tests added: [Test file paths]

---

**Entry Created:** YYYY-MM-DD HH:MM:SS
**Created By:** [Agent or person name]
**Committed To Git:** [YES | NO]
**Commit Hash:** [Git commit hash, if applicable]

---

## Notes

[Any additional context, observations, or special circumstances]

**Example:**
- "First production incident with new solver kill-switch. Kill-switch performed exactly as designed - graceful termination with full state preservation."
- "This incident highlighted the need for constraint management tooling. Consider building constraint catalog dashboard for visibility."
- "Faculty were understanding of delay - appreciated transparent communication and rapid resolution."
