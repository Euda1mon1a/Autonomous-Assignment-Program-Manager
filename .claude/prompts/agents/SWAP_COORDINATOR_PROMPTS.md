# Swap Coordinator Agent - Prompt Templates

> **Role:** Swap request processing, matching, execution, rollback
> **Model:** Claude Opus 4.5
> **Mission:** Facilitate compliant schedule swaps

## 1. SWAP REQUEST PROCESSING TEMPLATE

```
**SWAP REQUEST PROCESSING**

**REQUEST ID:** ${REQUEST_ID}
**REQUEST DATE:** ${REQUEST_DATE}
**REQUESTER:** ${REQUESTER_ID}

**SWAP DETAILS:**
- Original assignment: ${ORIGINAL_ASSIGNMENT}
- Original date: ${ORIGINAL_DATE}
- Requested date: ${REQUESTED_DATE}
- Swap type: ${SWAP_TYPE} (one-to-one, absorb)

**REQUEST VALIDATION:**
- [ ] Requester is assigned to original slot
- [ ] Requested slot exists and is open
- [ ] Both slots same rotation type: ${SAME_ROTATION}
- [ ] Request within time window: ${WITHIN_WINDOW}
- [ ] Reason provided: ${REASON_PROVIDED}

**VALIDATION RESULT:** ${VALID}

**VALIDATION ERRORS:**
${VALIDATION_ERRORS}

**NEXT STEPS:**
- If valid: Proceed to matching
- If invalid: Notify requester of reason

Process swap request.
```

## 2. SWAP MATCHING TEMPLATE

```
**SWAP MATCHING ANALYSIS**

**SWAP REQUEST:** ${REQUEST_ID}

**MATCHING STRATEGY:**
For one-to-one swaps: Find compatible personnel who prefer to trade

**CRITERIA FOR MATCH:**
1. Person is assigned to requested date
2. Person wants to swap to original date
3. Both people have required credentials
4. Swap maintains ACGME compliance
5. Swap maintains coverage

**CANDIDATE POOL:**
- Total candidates searched: ${CANDIDATE_COUNT}
- Exact matches (mutual request): ${EXACT_MATCHES}
- Compatible matches: ${COMPATIBLE_MATCHES}

**MATCH RECOMMENDATIONS (Ranked):**

### Match 1: ${MATCH_1_ID}
- Confidence: ${CONF_1}%
- Reasons to accept: ${REASONS_1}
- Risks: ${RISKS_1}
- Coverage impact: ${COVERAGE_1}%

### Match 2: ${MATCH_2_ID}
- Confidence: ${CONF_2}%
- Reasons to accept: ${REASONS_2}
- Coverage impact: ${COVERAGE_2}%

### Match 3: ${MATCH_3_ID}
- Confidence: ${CONF_3}%

**RECOMMENDATION:** Match with ${RECOMMENDED_MATCH}

**AUTO-MATCH CRITERIA:**
- If confidence >= 95%: Auto-approve
- If confidence >= 80%: Require one approval
- If confidence < 80%: Require both approvals

Match compatible swap candidates.
```

## 3. COMPLIANCE VERIFICATION TEMPLATE

```
**SWAP COMPLIANCE VERIFICATION**

**SWAP:** ${SWAP_ID}

**PRE-SWAP STATE:**
- Person A hours/week: ${PERSON_A_HOURS}
- Person B hours/week: ${PERSON_B_HOURS}
- Coverage: ${CURRENT_COVERAGE}%

**POST-SWAP STATE (Projected):**
- Person A hours/week: ${PERSON_A_NEW_HOURS}
- Person B hours/week: ${PERSON_B_NEW_HOURS}
- Coverage: ${NEW_COVERAGE}%

**ACGME COMPLIANCE CHECK:**

### 80-Hour Rule
- Person A: ${RULE_A_PASS}
- Person B: ${RULE_B_PASS}
- Verdict: ${HOURS_VERDICT}

### 1-in-7 Rule
- Person A: ${RULE_A_PASS}
- Person B: ${RULE_B_PASS}
- Verdict: ${1IN7_VERDICT}

### Supervision Ratios
- Coverage maintained: ${COVERAGE_MAINTAINED}
- Ratio maintained: ${RATIO_MAINTAINED}
- Verdict: ${SUPERVISION_VERDICT}

### Credentials
- Both credentialed for assigned roles: ${CREDS_OK}
- Verdict: ${CREDS_VERDICT}

**OVERALL COMPLIANCE:** ${COMPLIANT}

**COMPLIANCE BLOCKERS:**
${BLOCKERS}

**REMEDIATION OPTIONS:**
${OPTIONS}

Verify swap compliance.
```

## 4. SWAP EXECUTION TEMPLATE

```
**SWAP EXECUTION**

**SWAP ID:** ${SWAP_ID}
**EXECUTION DATE:** ${TODAY}
**EXECUTED BY:** ${EXECUTOR}

**EXECUTION WORKFLOW:**

### Phase 1: Pre-Execution (${TIME_1}min)
- [ ] Final compliance verification
- [ ] Both parties confirmed
- [ ] Backup schedule ready
- [ ] Rollback plan documented

### Phase 2: Transaction (${TIME_2}min)
- [ ] Begin database transaction
- [ ] Swap assignment A
- [ ] Swap assignment B
- [ ] Update audit log
- [ ] Commit transaction

### Phase 3: Notification (${TIME_3}min)
- [ ] Notify Person A
- [ ] Notify Person B
- [ ] Notify coordinators
- [ ] Update schedule display

### Phase 4: Validation (${TIME_4}min)
- [ ] Schedule consistency verified
- [ ] ACGME rules still satisfied
- [ ] Coverage maintained

**EXECUTION RESULT:** ${RESULT}

**AUDIT TRAIL:**
- Initiated by: ${INITIATED_BY}
- Approved by: ${APPROVED_BY}
- Executed at: ${EXECUTION_TIME}
- Duration: ${DURATION}

**ROLLBACK AVAILABLE:** YES (24 hours)

Execute swap transaction safely.
```

## 5. SWAP WITHDRAWAL TEMPLATE

```
**SWAP WITHDRAWAL/CANCELLATION**

**SWAP ID:** ${SWAP_ID}
**WITHDRAWAL DATE:** ${TODAY}
**WITHDRAWN BY:** ${WITHDRAWN_BY}

**SWAP STATUS BEFORE WITHDRAWAL:**
${SWAP_STATUS}

**REASON FOR WITHDRAWAL:**
${REASON}

**IMPACT OF WITHDRAWAL:**
- Person A reverts to: ${REVERTED_A}
- Person B reverts to: ${REVERTED_B}
- Coverage impact: ${COVERAGE_IMPACT}

**WORKFLOW:**
1. Cancel pending swap requests
2. Revert assignments to pre-swap state
3. Notify all parties
4. Update schedule display
5. Log withdrawal

**NOTIFICATIONS SENT:**
- Person A: Notified
- Person B: Notified
- Coordinators: Notified

**WITHDRAWAL RESULT:** SUCCESS

Process swap withdrawal.
```

## 6. ROLLBACK CAPABILITY TEMPLATE

```
**SWAP ROLLBACK WINDOW**

**SWAP ID:** ${SWAP_ID}
**EXECUTED:** ${EXECUTION_DATE}
**ROLLBACK WINDOW:** 24 hours
**ROLLBACK EXPIRES:** ${EXPIRATION_TIME}

**ROLLBACK PROCEDURE:**
1. Verify swap within rollback window
2. Check for dependent changes
3. Revert to pre-swap state
4. Validate compliance
5. Notify parties
6. Update schedule

**DEPENDENCIES:**
- Subsequent changes: ${DEPENDENT_SWAPS}
- If present: Must handle cascading rollback

**ROLLBACK VALIDATION:**
- Original schedule state recoverable: YES
- Audit trail preserved: YES
- Notification completed: YES

**ROLLBACK RESULT:** ${RESULT}

Execute swap rollback safely.
```

## 7. APPROVAL WORKFLOW TEMPLATE

```
**SWAP APPROVAL WORKFLOW**

**SWAP ID:** ${SWAP_ID}

**APPROVAL LEVELS:**

### Level 1: Requester Confirmation
- Status: ${REQUESTER_CONFIRMED}
- Confirmed by: ${REQUESTER}
- Date: ${REQUESTER_DATE}

### Level 2: Partner Confirmation (if new match)
- Status: ${PARTNER_CONFIRMED}
- Confirmed by: ${PARTNER_ID}
- Date: ${PARTNER_DATE}

### Level 3: Compliance Check (Automatic)
- Status: ${COMPLIANCE_PASSED}
- Checked by: Compliance Engine
- Date: ${COMPLIANCE_DATE}

### Level 4: Coordinator Approval (if needed)
- Status: ${COORD_APPROVED}
- Approved by: ${COORDINATOR}
- Date: ${COORD_DATE}
- Reason: ${COORD_REASON}

**APPROVAL DECISION FLOW:**
- Mutual + Compliant + Auto-eligible → Instant approval
- Mutual + Compliant + Coordinator discretion → Pending approval
- Non-compliant → Rejection with remediation options
- Blocked dependencies → Queued for retry

**CURRENT STATUS:** ${CURRENT_STATUS}

**NEXT ACTION:** ${NEXT_ACTION}

Manage approval workflow.
```

## 8. SWAP HISTORY & ANALYTICS TEMPLATE

```
**SWAP ANALYTICS & HISTORY**

**REPORTING PERIOD:** ${PERIOD}
**REPORT DATE:** ${TODAY}

**VOLUME METRICS:**
- Total requests: ${REQUEST_COUNT}
- Executed swaps: ${EXECUTED_COUNT}
- Successful rate: ${SUCCESS_RATE}%
- Average processing time: ${AVG_TIME}min

**SWAP REASONS:**
- Personal: ${PERSONAL_REASON_PCT}%
- Clinical: ${CLINICAL_REASON_PCT}%
- Family: ${FAMILY_REASON_PCT}%
- Other: ${OTHER_REASON_PCT}%

**MATCH STATISTICS:**
- Mutual matches: ${MUTUAL_COUNT}
- Auto-matched: ${AUTO_MATCHED}
- Manual approved: ${MANUAL_APPROVED}
- Pending: ${PENDING_COUNT}
- Rejected: ${REJECTED_COUNT}

**COMPLIANCE IMPACT:**
- Swaps that maintained compliance: ${MAINTAINED}%
- Swaps that improved compliance: ${IMPROVED}%
- Swaps that reduced compliance: ${REDUCED}%

**MOST ACTIVE SWAPPERS:**
- ${PERSON_1}: ${SWAP_COUNT_1} swaps
- ${PERSON_2}: ${SWAP_COUNT_2} swaps
- ${PERSON_3}: ${SWAP_COUNT_3} swaps

**TRENDS:**
- Swap requests trending: ${TREND}
- Most common rotation swap: ${COMMON_ROTATION}
- Peak swap time: ${PEAK_TIME}

Report swap analytics.
```

## 9. STATUS REPORT TEMPLATE

```
**SWAP COORDINATOR STATUS REPORT**

**REPORT DATE:** ${TODAY}

**ACTIVE SWAPS:**
- Pending requests: ${PENDING}
- In approval: ${APPROVAL}
- Executed (24h window): ${EXECUTED_24H}
- Rollback eligible: ${ROLLBACK_ELIGIBLE}

**PROCESSING METRICS:**
- Avg processing time: ${AVG_TIME}min
- Compliance validation: 100%
- Partner match success: ${MATCH_SUCCESS}%
- Auto-approval rate: ${AUTO_APPROVAL}%

**ISSUES:**
- Deadlocked swaps: ${DEADLOCKED}
- High-risk swaps: ${HIGH_RISK}
- Escalations: ${ESCALATIONS}

**NEXT:** ${NEXT_GOALS}
```

## 10. ESCALATION TEMPLATE

```
**SWAP ESCALATION**

**SWAP ID:** ${SWAP_ID}
**ISSUE:** ${ISSUE_TYPE}
**PRIORITY:** ${PRIORITY}

**SITUATION:**
${SITUATION}

**BLOCKER:**
${BLOCKER}

**IMPACT:**
- Swap execution blocked: ${BLOCKED}
- Time pending: ${TIME_PENDING}
- Personnel affected: ${AFFECTED_COUNT}

**REQUESTED AUTHORITY:**
${AUTHORITY}

**ESCALATION DEADLINE:** ${DEADLINE}

Escalate swap issue.
```

## 11. HANDOFF TEMPLATE

```
**SWAP COORDINATOR HANDOFF**

**FROM:** ${FROM_AGENT}
**TO:** ${TO_AGENT}

**PENDING SWAPS:**
- Awaiting approval: ${AWAITING_APPROVAL}
- Ready to execute: ${READY_TO_EXECUTE}
- Waiting for callback: ${WAITING_CALLBACK}

**ESCALATIONS:**
${ESCALATIONS}

**NEXT ACTIONS:**
${NEXT_ACTIONS}

Acknowledge and continue.
```

## 12. DELEGATION TEMPLATE

```
**SWAP TASK DELEGATION**

**DELEGATEE:** ${DELEGATEE}
**TASK:** ${TASK}

**SCOPE:**
${SCOPE}

**EXPECTED OUTPUT:**
${OUTPUT}

**SUCCESS CRITERIA:**
- [ ] All swaps processed
- [ ] 100% ACGME compliant
- [ ] Notifications sent
- [ ] Audit log complete

Confirm acceptance.
```

---

*Last Updated: 2025-12-31*
*Agent: Swap Coordinator*
*Version: 1.0*
