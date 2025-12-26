# Swap Execution - [Swap ID]

**Date:** YYYY-MM-DD
**Swap ID:** [Unique identifier, e.g., S12345, CHAIN-C67890]
**Executed By:** [Agent name, e.g., SCHEDULER]
**Status:** [APPROVED | REJECTED | ROLLED_BACK | PENDING_APPROVAL]

---

## Summary

[One-sentence summary of swap request and outcome]

**Example:** "One-to-one swap between PGY2-01 and PGY2-03 for Aug 15 inpatient call - approved and executed after safety checks passed."

---

## Request Details

**Swap Type:**
- [ ] One-to-One (residents exchange shifts)
- [ ] Absorb (one resident takes shift, other drops)
- [ ] Chain (3+ residents involved in sequential swaps)
- [ ] Emergency Coverage (last-minute replacement)

**Requested By:**
- Initiator: [e.g., PGY2-01]
- Partner(s): [e.g., PGY2-03]
- Requested At: [YYYY-MM-DD HH:MM:SS]
- Request Method: [e.g., Web UI, Email, Phone call to coordinator]

**Request Reason:**
- [ ] Personal (family event, medical appointment)
- [ ] Educational (conference, lecture, board prep)
- [ ] Medical (illness, injury)
- [ ] Emergency (unexpected absence)
- [ ] Preference (schedule optimization)
- [ ] Other: ___________

**Urgency:**
- [ ] Routine (>7 days notice)
- [ ] Short Notice (2-7 days)
- [ ] Urgent (24-48 hours)
- [ ] Emergency (<24 hours)

---

## Shift Details

### Shift A (Given by Initiator)

**Original Assignment:**
- Person: [e.g., PGY2-01]
- Date: [YYYY-MM-DD]
- Session: [AM | PM]
- Rotation: [e.g., Inpatient Call]
- Duration: [e.g., 12 hours]
- Location: [e.g., Main Hospital]
- Credential Requirements: [e.g., BLS, N95 Fit, HIPAA current]

### Shift B (Received by Initiator)

**Original Assignment:**
- Person: [e.g., PGY2-03]
- Date: [YYYY-MM-DD]
- Session: [AM | PM]
- Rotation: [e.g., Inpatient Call]
- Duration: [e.g., 12 hours]
- Location: [e.g., Main Hospital]
- Credential Requirements: [e.g., BLS, N95 Fit, HIPAA current]

### Net Impact

**For Initiator (PGY2-01):**
- Hours change: [e.g., +0 hours (same duration)]
- Work hours this week: [e.g., 68 → 68 hours]
- Days since last off: [e.g., 4 → 4 days]

**For Partner (PGY2-03):**
- Hours change: [e.g., +0 hours (same duration)]
- Work hours this week: [e.g., 65 → 65 hours]
- Days since last off: [e.g., 3 → 3 days]

---

## Safety Check Results

### 1. Pre-Swap Compliance Check

**Initiator (PGY2-01):**
- Current ACGME status: [COMPLIANT | AT_RISK | VIOLATED]
  - 80-hour limit: [e.g., 68/80 hours this week] ✅
  - 1-in-7 day off: [e.g., Last off 4 days ago] ✅
  - Supervision ratio: [e.g., 1:1.5 (compliant)] ✅

**Partner (PGY2-03):**
- Current ACGME status: [COMPLIANT | AT_RISK | VIOLATED]
  - 80-hour limit: [e.g., 65/80 hours this week] ✅
  - 1-in-7 day off: [e.g., Last off 3 days ago] ✅
  - Supervision ratio: [e.g., 1:1.8 (compliant)] ✅

**Result:** [PASS | FAIL]
**Notes:** [Any observations or concerns]

### 2. Post-Swap Simulation

**ACGME Validation (±14 day window):**
- Initiator (PGY2-01) projected violations: [e.g., 0] ✅
- Partner (PGY2-03) projected violations: [e.g., 0] ✅
- Other residents affected by cascade: [e.g., 0]

**Work Hour Projection:**
- Initiator week of swap: [e.g., 68 hours → 68 hours] ✅
- Partner week of swap: [e.g., 65 hours → 65 hours] ✅
- Maximum weekly hours (either party): [e.g., 68/80] ✅

**1-in-7 Day Off Projection:**
- Initiator: [e.g., 1 day off in next 7 days] ✅
- Partner: [e.g., 1 day off in next 7 days] ✅

**Result:** [PASS | FAIL]
**Notes:** [e.g., "No ACGME violations projected in ±14 day window"]

### 3. Conflict Detection

**Direct Conflicts:**
- [ ] Overlapping assignments on swap dates: [NONE | List conflicts]
- [ ] Pre-existing leave requests: [NONE | List conflicts]
- [ ] Mandatory conferences/training: [NONE | List conflicts]
- [ ] Other scheduled commitments: [NONE | List conflicts]

**Cascade Analysis:**
- Dependent swaps: [e.g., 0 (isolated swap)]
- Coverage domino effects: [NONE | Describe]
- Future conflicts (next 7 days): [NONE | List potential issues]

**Result:** [PASS | FAIL]
**Notes:** [e.g., "No conflicts detected - isolated swap with no cascading effects"]

### 4. Credential Verification

**Initiator → Partner's Shift:**
- Shift requirements: [e.g., BLS, N95 Fit, HIPAA]
- Initiator credentials:
  - BLS: [VALID until YYYY-MM-DD] ✅
  - N95 Fit: [VALID until YYYY-MM-DD] ✅
  - HIPAA: [VALID until YYYY-MM-DD] ✅
- Expiring soon (< 30 days): [NONE | List credentials]

**Partner → Initiator's Shift:**
- Shift requirements: [e.g., BLS, N95 Fit, HIPAA]
- Partner credentials:
  - BLS: [VALID until YYYY-MM-DD] ✅
  - N95 Fit: [VALID until YYYY-MM-DD] ✅
  - HIPAA: [VALID until YYYY-MM-DD] ✅
- Expiring soon (< 30 days): [NONE | List credentials]

**Result:** [PASS | FAIL]
**Notes:** [e.g., "Both parties meet credential requirements with >60 day validity"]

### 5. Coverage Impact Assessment

**Minimum Staffing Check:**
- Service affected: [e.g., Inpatient Call]
- Date(s) impacted: [e.g., Aug 15 PM]
- Minimum required: [e.g., 2 residents]
- Post-swap staffing: [e.g., 2 residents] ✅

**Specialty Coverage:**
- Critical services maintained: [YES | NO]
  - ER coverage: [MAINTAINED | IMPACTED]
  - ICU coverage: [MAINTAINED | IMPACTED]
  - Procedures coverage: [MAINTAINED | IMPACTED]
- Senior resident availability: [SUFFICIENT | INSUFFICIENT]

**Result:** [PASS | FAIL]
**Notes:** [e.g., "Minimum staffing maintained - no coverage gaps created"]

---

## Decision

**Overall Safety Assessment:** [PASS | FAIL]

**Decision Matrix:**

| Safety Check | Result | Weight | Score |
|--------------|--------|--------|-------|
| Pre-Swap Compliance | [PASS/FAIL] | Critical | [PASS=100, FAIL=0] |
| Post-Swap Simulation | [PASS/FAIL] | Critical | [PASS=100, FAIL=0] |
| Conflict Detection | [PASS/FAIL] | High | [PASS=80, FAIL=0] |
| Credential Verification | [PASS/FAIL] | Critical | [PASS=100, FAIL=0] |
| Coverage Impact | [PASS/FAIL] | High | [PASS=80, FAIL=0] |

**Total Score:** [e.g., 460/460 - all checks passed]

**Automated Decision:** [APPROVE | REJECT | FLAG_FOR_REVIEW]

**Reason:**
- [If APPROVE: "All safety checks passed. Swap meets ACGME compliance and maintains coverage."]
- [If REJECT: "Rejection reason (specific check failed)"]
- [If FLAG_FOR_REVIEW: "Flagged for manual review due to [specific concern]"]

### Manual Review (if required)

**Review Required:** [YES | NO]

**Trigger:**
- [ ] Critical service affected (ER, ICU)
- [ ] Short notice (<48 hours to shift start)
- [ ] Near-miss ACGME threshold (>75 hours/week)
- [ ] Chain swap (3+ residents)
- [ ] Previous swap reversal for this resident (within 30 days)

**Reviewed By:** [e.g., Faculty Coordinator, Program Director]
**Review Date:** [YYYY-MM-DD HH:MM:SS]
**Review Decision:** [APPROVED | REJECTED | CONDITIONAL]
**Review Notes:** [Comments from reviewer]

---

## Execution

**Execution Status:** [EXECUTED | REJECTED | PENDING | ROLLED_BACK]

**Execution Details:**

**Database Transaction:**
- Transaction ID: [e.g., TXN-123456]
- Started At: [YYYY-MM-DD HH:MM:SS]
- Completed At: [YYYY-MM-DD HH:MM:SS]
- Duration: [e.g., 0.42 seconds]
- Row Locking: [ENABLED | DISABLED]

**Changes Made:**
1. Assignment for Shift A:
   - BEFORE: Person=[Initiator], Block=[Date+Session], Rotation=[Rotation A]
   - AFTER: Person=[Partner], Block=[Date+Session], Rotation=[Rotation A]

2. Assignment for Shift B:
   - BEFORE: Person=[Partner], Block=[Date+Session], Rotation=[Rotation B]
   - AFTER: Person=[Initiator], Block=[Date+Session], Rotation=[Rotation B]

**Audit Trail:**
- Audit Log ID: [e.g., AUDIT-789012]
- Operation: `swap_execution`
- User: [e.g., system (automated) or faculty_coordinator]
- Timestamp: [YYYY-MM-DD HH:MM:SS]
- IP Address: [If manual approval, log IP]

**Rollback Data Captured:**
- Rollback ID: [e.g., ROLLBACK-345678]
- Valid Until: [YYYY-MM-DD HH:MM:SS] (24-hour window)
- Original State Snapshot: [Database backup reference]
- Restore Procedure: [See rollback section below]

---

## Notifications

**Notification Status:** [SENT | PENDING | FAILED]

**Parties Notified:**

1. **Initiator (PGY2-01):**
   - Email: [SENT at HH:MM:SS]
   - Dashboard Alert: [UPDATED]
   - Calendar Sync: [UPDATED | PENDING]

2. **Partner (PGY2-03):**
   - Email: [SENT at HH:MM:SS]
   - Dashboard Alert: [UPDATED]
   - Calendar Sync: [UPDATED | PENDING]

3. **Affected Services:**
   - Clinic Coordinator: [NOTIFIED | NOT_REQUIRED]
   - ER Scheduler: [NOTIFIED | NOT_REQUIRED]
   - ICU Charge Nurse: [NOTIFIED | NOT_REQUIRED]
   - Faculty Supervisor: [NOTIFIED | NOT_REQUIRED]

**Notification Content:**
- Subject: [e.g., "Schedule Swap Confirmed - Aug 15 Inpatient Call"]
- Body: [Summary of swap, new assignments, contact info]
- Calendar Update: [ICS file attachment or calendar API sync]

---

## Rollback Procedure

**Rollback Window:** 24 hours from execution
**Valid Until:** [YYYY-MM-DD HH:MM:SS]
**Status:** [ACTIVE | EXPIRED | EXECUTED]

### If Rollback Needed

**Trigger Conditions:**
- [ ] No-show by resident (swap resulted in missed shift)
- [ ] Post-facto ACGME violation detected
- [ ] Coverage issue identified (unanticipated conflict)
- [ ] Resident requests reversal (within 24-hour window)
- [ ] System error detected (data integrity issue)

**Rollback Steps:**
```python
# Automated rollback procedure
rollback_swap(swap_id="S12345")

# This will:
# 1. Restore original assignments from snapshot
# 2. Update audit log with rollback event
# 3. Notify all parties of reversal
# 4. Invalidate calendar updates
# 5. Log rollback reason for review
```

**Manual Rollback:**
```bash
# For emergencies or after 24-hour window (requires faculty approval)
cd backend
python -m app.services.swap_executor rollback --swap-id S12345 --force
```

**Post-Rollback:**
- Notify all parties immediately
- Investigate root cause (why rollback needed)
- Document lessons learned
- Update swap validation logic if systemic issue

---

## Post-Execution Monitoring

**Monitoring Period:** 48 hours post-execution
**Monitor For:**
- [ ] No-shows or missed shifts
- [ ] Resident complaints or concerns
- [ ] ACGME compliance drift (real-time validation)
- [ ] Coverage issues or service disruptions
- [ ] Follow-on swap requests (indicates dissatisfaction)

**Monitoring Results (update after 48 hours):**
- Issues detected: [NONE | List issues]
- Resident feedback: [POSITIVE | NEUTRAL | NEGATIVE]
- Coverage maintained: [YES | NO]
- ACGME compliance: [MAINTAINED | DRIFTED]

**Sign-off (after monitoring period):**
- [ ] Swap successful - no issues detected
- [ ] Swap completed with minor issues (document below)
- [ ] Swap problematic - rollback or investigation required

---

## Impact & Metrics

**Workload Distribution Impact:**

| Resident | Call Shifts This Block | Variance from Average | Status |
|----------|------------------------|----------------------|--------|
| PGY2-01 | [e.g., 4 shifts] | [e.g., -0.2σ] | ✅ Within target |
| PGY2-03 | [e.g., 5 shifts] | [e.g., +0.3σ] | ✅ Within target |

**Fairness Metrics:**
- Call distribution variance (before): [e.g., 0.7σ]
- Call distribution variance (after): [e.g., 0.8σ]
- Change: [e.g., +0.1σ] (Target: < 1σ) ✅

**Resilience Impact:**
- Overall health score: [e.g., 0.83 → 0.82] (minimal change)
- Utilization (Initiator): [e.g., 72% → 72%] (no change)
- Utilization (Partner): [e.g., 68% → 68%] (no change)

**Preference Satisfaction:**
- Initiator preference honored: [YES | NO]
- Partner preference honored: [YES | NO | N/A (absorb swap)]

---

## Lessons Learned

**What Went Well:**
- [e.g., "Automated safety checks caught potential supervision ratio issue and adjusted coverage preemptively."]
- [e.g., "Swap executed in <2 seconds with no manual intervention required."]

**What Could Be Improved:**
- [e.g., "Notification delay (5 minutes) due to email server lag. Consider SMS fallback for urgent swaps."]
- [e.g., "Calendar sync failed for Initiator - manual intervention required. Investigate API timeout."]

**Pattern Detection:**
- [e.g., "This is the 3rd swap between PGY2-01 and PGY2-03 this block. Suggest auto-match for future requests."]
- [e.g., "Aug 15 is a popular swap target date (5th request). Consider proactive schedule adjustment."]

**MetaUpdater Notes:**
- [Insights for continuous improvement]
- [e.g., "Credential expiration warnings (30-day) reduced last-minute swap rejections by 40%. Continue this practice."]

---

## Related Records

**References:**
- Schedule: [e.g., `.claude/History/scheduling/2025-07-15_block10_gen001.md`]
- Compliance Audit: [e.g., `.claude/History/compliance/2025-08-01_weekly_check.md`]
- Previous Swap (if chain): [e.g., `.claude/History/swaps/2025-08-10_swap_s12344.md`]
- Rollback (if executed): [e.g., `.claude/History/swaps/2025-08-16_rollback_s12345.md`]

**Linked Issues:**
- [Any related incidents or bugs]
- [e.g., "See incident: `.claude/History/incidents/2025-08-05_calendar_sync_failure.md`"]

---

## Approval Chain

**Automated Approval:**
- Safety Checks: [PASS at YYYY-MM-DD HH:MM:SS]
- ACGME Validator: [PASS at YYYY-MM-DD HH:MM:SS]
- Coverage Checker: [PASS at YYYY-MM-DD HH:MM:SS]
- Auto-Approve Threshold: [MET | NOT_MET]

**Manual Approval (if required):**
- Requested From: [e.g., Faculty Coordinator]
- Requested At: [YYYY-MM-DD HH:MM:SS]
- Approved By: [Name/Role]
- Approved At: [YYYY-MM-DD HH:MM:SS]
- Approval Method: [e.g., Email, Web UI, Phone]
- Comments: [Any notes from approver]

**Final Authorization:**
- Authorized By: [SCHEDULER (automated) | Faculty Name]
- Authorized At: [YYYY-MM-DD HH:MM:SS]
- Authorization Level: [AUTOMATIC | MANUAL_REVIEW | FACULTY_OVERRIDE]

---

## Statistics

**Swap Request Metrics:**
- Request submitted: [YYYY-MM-DD HH:MM:SS]
- Validation completed: [YYYY-MM-DD HH:MM:SS]
- Approval obtained: [YYYY-MM-DD HH:MM:SS]
- Execution completed: [YYYY-MM-DD HH:MM:SS]
- **Total Time:** [e.g., 1.8 seconds] (Target: < 2s for simple swaps)

**Safety Check Performance:**
- Pre-swap compliance: [e.g., 0.12s]
- Post-swap simulation: [e.g., 0.35s]
- Conflict detection: [e.g., 0.28s]
- Credential verification: [e.g., 0.08s]
- Coverage assessment: [e.g., 0.15s]
- **Total Validation Time:** [e.g., 0.98s]

**System Performance:**
- Database query time: [e.g., 0.05s]
- Transaction commit time: [e.g., 0.02s]
- Notification send time: [e.g., 0.30s]
- Calendar sync time: [e.g., 0.42s]

---

**Entry Created:** YYYY-MM-DD HH:MM:SS
**Created By:** [Agent name]
**Committed To Git:** [YES | NO]
**Commit Hash:** [Git commit hash, if applicable]

---

## Notes

[Any additional context, observations, or special circumstances]

**Example:**
- "First swap processed with new credential expiration warning system. Warning successfully notified both parties 30 days before expiration."
- "Partner (PGY2-03) requested this swap to attend family wedding. Preference noted for future scheduling."
