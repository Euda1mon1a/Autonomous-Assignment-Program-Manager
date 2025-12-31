# Swap Processing Playbook

**Purpose:** Step-by-step operational guide for managing resident and faculty schedule swaps while maintaining ACGME compliance.

**Target Audience:** Scheduling Coordinators, Program Directors, Faculty

**Last Updated:** 2025-12-31

---

## Table of Contents

1. [Overview](#overview)
2. [Swap Request Intake](#swap-request-intake)
3. [Compatibility Analysis](#compatibility-analysis)
4. [Approval Workflow](#approval-workflow)
5. [Execution Steps](#execution-steps)
6. [Rollback Procedures](#rollback-procedures)
7. [Compliance Verification](#compliance-verification)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Swap Types Supported

| Swap Type | Description | Parties | Approval |
|-----------|-------------|---------|----------|
| **1:1 Swap** | Two residents exchange single blocks | 2 residents | Faculty approval |
| **Multi-Block** | Resident swaps multiple consecutive blocks | 2 residents | Faculty approval |
| **Faculty Swap** | Faculty exchange call/clinic duties | 2 faculty | PD approval |
| **Absorb** | Resident gives away shift (no swap) | 1 resident, faculty | PD approval |
| **Complex Swap** | 3+ residents or multi-day chains | Multi-party | Committee review |

### Key Policies

- **Swap Window:** Available after schedule published + 30 days
- **Processing Time:** 24-48 hours typical
- **Reversal Window:** 24 hours after execution
- **Approval Depth:** Based on participant roles and schedule impact
- **Compliance Check:** ACGME rules verified before execution

---

## Swap Request Intake

### Step 1: Request Submission

Residents/faculty submit requests via web portal or email.

#### Web Portal Submission

```bash
# POST: Submit swap request
curl -X POST http://localhost:8000/api/swaps/request \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_type": "one_to_one",
    "initiator_id": "PGY1-001",
    "participants": ["PGY1-002"],
    "blocks": [
      {
        "initiator_block_date": "2026-02-15",
        "initiator_rotation": "inpatient_call",
        "target_block_date": "2026-03-15",
        "target_rotation": "clinic"
      }
    ],
    "reason": "Personal conflict on 2026-02-15",
    "requested_approval_date": "2026-02-05"
  }'

# Response:
# {
#   "swap_id": "SWAP_20251231_001",
#   "status": "pending_initiator_confirmation",
#   "created_at": "2025-12-31T10:00:00Z"
# }
```

#### Email Submission

```
SWAP REQUEST EMAIL TEMPLATE

To: schedule-admin@program.edu
Subject: Swap Request - [Your Name] - [Dates]

Name: [Full Name]
Role: [Resident/Faculty]
ID: [ID Number]

SWAP TYPE:
☐ 1:1 Swap
☐ Multi-block Swap
☐ Faculty Swap
☐ Absorb
☐ Other: ___________

DATES INVOLVED:
From: [Block Date 1]
To: [Block Date 2]

ROTATION DETAILS:
Current Rotation: [Rotation Name]
Desired Rotation: [Rotation Name if applicable]

SWAP PARTNER (if applicable):
Name: [Name]
ID: [ID]

REASON:
[Brief explanation]

PREFERRED APPROVAL DATE:
[Date if specific deadline]

REQUESTED ACCOMMODATIONS:
[Any special requests]
```

### Step 2: Initial Validation

```bash
# POST: Validate swap request feasibility
curl -X POST http://localhost:8000/api/swaps/validate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001"
  }'

# Response includes:
# - Structural validity (dates, ids valid)
# - Timing validity (within swap window)
# - Participant eligibility
# - Initial compliance check
```

**Validation Checklist:**

```
SWAP REQUEST VALIDATION

Request ID: _________________
Received: _________________

STRUCTURAL CHECKS:
☐ All required fields provided
☐ Dates are valid calendar dates
☐ Block dates exist in current schedule
☐ Participant IDs are valid in system
☐ Rotation types are valid

TIMING CHECKS:
☐ Schedule published > 30 days ago
☐ Swap request is before affected blocks
☐ Approval deadline is reasonable (5+ days out)
☐ No past dates (swap_date > today)

PARTICIPANT CHECKS:
☐ All participants still in program
☐ All participants have access to swaps feature
☐ No duplicate participants
☐ Participants from same category (residents) or compatible (faculty-resident)

STATUS:
☐ PASS: Proceed to compatibility analysis
☐ FAIL: Contact requester for corrections
☐ REJECT: Not eligible for swap system
```

### Step 3: Confirm All Participants

```bash
# Notify all non-initiating participants
cat > swap_confirmation_email.txt << 'EOF'
SWAP REQUEST CONFIRMATION NEEDED

You have been identified as a participant in a proposed schedule swap:

Swap ID: SWAP_20251231_001
Initiator: [Name]

PROPOSED EXCHANGE:
[Details of blocks to be swapped]

TO CONFIRM YOUR PARTICIPATION:
1. Review the swap details
2. Click confirmation link: [URL]
3. OR reply with "I confirm" to this email

DEADLINE: 48 hours from this email

If you do not confirm or explicitly decline, this swap will be marked as unconfirmed.

Questions? Contact: schedule-admin@program.edu
EOF

# Send confirmations
curl -X POST http://localhost:8000/api/swaps/send-confirmations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001"
  }'
```

### Step 4: Receive Confirmations

```bash
# GET: Check confirmation status
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/confirmations \
  -H "Authorization: Bearer $TOKEN"

# Response:
# {
#   "swap_id": "SWAP_20251231_001",
#   "confirmations": {
#     "PGY1-001": {"status": "confirmed", "confirmed_at": "..."},
#     "PGY1-002": {"status": "pending", "deadline": "..."}
#   }
# }
```

**Manual Confirmation Log:**

```
SWAP CONFIRMATION LOG

Swap ID: _________________

PARTICIPANTS:
Name: _________________ Status: ☐ Confirmed ☐ Pending ☐ Declined Date: _____
Name: _________________ Status: ☐ Confirmed ☐ Pending ☐ Declined Date: _____

ALL CONFIRMED BY: ___________ Date: ___________
REASON FOR DECLINE (if any): ________________________
```

---

## Compatibility Analysis

### Step 1: Check Rotation Compatibility

```bash
# POST: Analyze rotation compatibility
curl -X POST http://localhost:8000/api/swaps/analyze/rotations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001"
  }'

# Response includes:
# - Rotation type compatibility
# - Credential requirements for each rotation
# - Faculty coverage implications
```

**Rotation Compatibility Matrix:**

```
ROTATION COMPATIBILITY ANALYSIS

Swap Participants: [Names]
Block Dates: [Dates]

ROTATION COMPARISON:

Initiator's Current:    [Rotation A]
Initiator's Desired:    [Rotation B]
Compatibility:          ☐ High ☐ Moderate ☐ Low
Notes:                  _________________________

Target Participant's Current:  [Rotation B]
Target Participant's Desired:  [Rotation A]
Compatibility:                 ☐ High ☐ Moderate ☐ Low
Notes:                        _________________________

OVERALL ROTATION COMPATIBILITY: ___________
```

### Step 2: Credential Requirements Check

```bash
# POST: Verify credentials for swapped rotations
curl -X POST http://localhost:8000/api/swaps/analyze/credentials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001"
  }'

# Response includes:
# - Each participant's current credentials
# - Credentials required for proposed rotation
# - Any missing credentials
```

**Credential Verification Checklist:**

```
CREDENTIAL VERIFICATION

Swap ID: _________________

INITIATOR: [Name] - [ID]
Current Credentials for Current Rotation:
☐ [Credential 1]: _______ (Expires: ____)
☐ [Credential 2]: _______ (Expires: ____)

Required Credentials for Proposed Rotation:
☐ [Credential 1]: Status ☐ Has ☐ Missing ☐ Expired
☐ [Credential 2]: Status ☐ Has ☐ Missing ☐ Expired

TARGET: [Name] - [ID]
Current Credentials for Current Rotation:
☐ [Credential 1]: _______ (Expires: ____)
☐ [Credential 2]: _______ (Expires: ____)

Required Credentials for Proposed Rotation:
☐ [Credential 1]: Status ☐ Has ☐ Missing ☐ Expired
☐ [Credential 2]: Status ☐ Has ☐ Missing ☐ Expired

CREDENTIAL ASSESSMENT:
☐ PASS: All required credentials present and valid
☐ CONDITIONAL: Some credentials can be obtained before swap date
☐ FAIL: Missing required credentials (swap cannot proceed)
```

### Step 3: Coverage Impact Analysis

```bash
# POST: Analyze impact on coverage
curl -X POST http://localhost:8000/api/swaps/analyze/coverage \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001",
    "include_alternatives": true
  }'

# Response:
# - Impact on rotation coverage
# - Impact on faculty supervision ratios
# - Alternative swap suggestions if coverage affected
```

**Coverage Impact Report Template:**

```
COVERAGE IMPACT ANALYSIS

Swap ID: _________________
Affected Blocks: [Dates]
Affected Rotations: [List]

CURRENT COVERAGE STATE:
[Rotation A] on [Date]: [X] residents scheduled
[Rotation B] on [Date]: [Y] residents scheduled

AFTER SWAP:
[Rotation A] on [Date]: [X-1] residents scheduled ← IMPACT
[Rotation B] on [Date]: [Y+1] residents scheduled ← IMPACT

COVERAGE ASSESSMENT:
☐ ACCEPTABLE: Coverage remains adequate
☐ MARGINAL: Coverage at minimum acceptable level
☐ INADEQUATE: Coverage falls below required minimum
  Mitigation: ____________________________

FACULTY SUPERVISION IMPACT:
Current Ratio: [X:Y]
After Swap: [X:Y]
☐ Ratio maintained ☐ Ratio affected
Status: ____________________________

FINAL ASSESSMENT:
☐ APPROVE: Swap maintains coverage
☐ CONDITIONAL: Swap acceptable with coverage mitigation
☐ REJECT: Swap would create coverage gap
```

### Step 4: Generate Compatibility Report

```bash
# GET: Complete compatibility analysis
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/compatibility-report \
  -H "Authorization: Bearer $TOKEN"

# Export for review
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/compatibility-report \
  -H "Authorization: Bearer $TOKEN" \
  -H "Accept: application/pdf" > compatibility_report.pdf
```

---

## Approval Workflow

### Step 1: Route to Appropriate Approvers

Approval required based on participant roles:

```
APPROVAL ROUTING LOGIC

Swap Type: [1:1 Resident Swap]
Participants: [2 Residents]
↓
Route to: Supervising Faculty
Faculty Approval Required: YES
PD Approval Required: NO
↓
Approval Request Sent

---

Swap Type: [Faculty Swap]
Participants: [2 Faculty]
↓
Route to: Program Director
PD Approval Required: YES
Associate PD: Notify
↓
Approval Request Sent

---

Swap Type: [Complex Swap]
Participants: [3+ participants or cross-training]
↓
Route to: Committee Review
Members: PD, Associate PD, Chief Resident
Additional Review: Feasibility committee
↓
Committee Review Initiated
```

### Step 2: Send Approval Requests

```bash
# POST: Request approval from faculty member
curl -X POST http://localhost:8000/api/swaps/request-approval \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001",
    "approvers": ["FAC-001"],  # Supervising faculty
    "due_date": "2026-01-05",
    "priority": "standard"
  }'

# Send approval request email
cat > approval_request_email.txt << 'EOF'
SWAP REQUEST APPROVAL NEEDED

Swap ID: SWAP_20251231_001
Submitted By: [Initiator Name]

SWAP DETAILS:
Participants: [Names and IDs]
Block Dates: [Dates]
Rotations: [Current → Proposed]

ANALYSIS SUMMARY:
- Rotation Compatibility: [Assessment]
- Credentials: [Status]
- Coverage Impact: [Status]
- Compliance: [Status]

REQUEST:
Please review and approve/deny by [Date].

ACTION LINKS:
- APPROVE: [Link]
- REQUEST MORE INFO: [Link]
- DENY: [Link]

Questions? Reply to this email.
EOF
```

### Step 3: Review and Decision

```bash
# GET: Pull up swap details for review
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/full-review \
  -H "Authorization: Bearer $TOKEN"

# This includes:
# - All compatibility analyses
# - Participant credentials
# - Coverage impact
# - Historical pattern (if resident has had swaps before)
# - ACGME compliance check
```

**Approval Decision Checklist:**

```
SWAP APPROVAL DECISION FORM

Swap ID: _________________
Reviewed By: _________________ Date: __________

REVIEW ITEMS:
☐ Participants confirmed the request
☐ Credentials verified and valid
☐ Coverage impact acceptable
☐ ACGME compliance assured
☐ No conflicts identified

DECISION:
☐ APPROVED: Swap may proceed
☐ APPROVED WITH CONDITIONS: [Specify conditions]
☐ REQUEST MORE INFO: [Specify information needed]
☐ DENIED: [Specify reason]

COMMENTS:
_________________________________________________________________
_________________________________________________________________

Signature: _______________________ Date: ____________
```

### Step 4: Record Decision

```bash
# POST: Submit approval decision
curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approved",
    "approver_id": "FAC-001",
    "comments": "Swap approved. Coverage maintained, all credentials valid.",
    "approved_at": "2025-12-31T14:30:00Z"
  }'

# Response:
# {
#   "swap_id": "SWAP_20251231_001",
#   "status": "approved",
#   "next_step": "Awaiting coordinator execution"
# }
```

### Step 5: Notify Participants

```bash
# POST: Send approval notification
curl -X POST http://localhost:8000/api/swaps/notify-participants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001",
    "notification_type": "approved"
  }'

# Approval notification email
cat > approval_notification.txt << 'EOF'
SWAP REQUEST APPROVED

Swap ID: SWAP_20251231_001
Approved By: [Faculty/PD Name]
Approval Date: [Date]

Your swap request has been APPROVED.

SWAP DETAILS:
Effective Blocks: [Dates]
Your Assignment: [Changed from X to Y]

NEXT STEPS:
Your schedule will be updated within 24 hours.
Check your portal for updated assignments.

If you have questions, contact: schedule-admin@program.edu
EOF
```

---

## Execution Steps

### Step 1: Pre-Execution Verification

```bash
# POST: Final verification before execution
curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/pre-execution-check \
  -H "Authorization: Bearer $TOKEN"

# Verifies:
# - Schedule still contains both blocks
# - No conflicting changes since approval
# - Database integrity
# - Backup exists
```

**Pre-Execution Checklist:**

```
PRE-EXECUTION CHECKLIST

Swap ID: _________________
Executor: _________________ Date: __________

VERIFICATION ITEMS:
☐ Swap approval still valid
☐ Both blocks still exist in schedule
☐ No conflicting swaps in progress
☐ All participants still eligible
☐ ACGME compliance still verified
☐ Database backup created
☐ System healthy

CONDITIONS:
☐ All conditions met - PROCEED with execution
☐ Issues detected - PAUSE and resolve
☐ Conditions still apply - [List any]

Approved for Execution By: ______________________
```

### Step 2: Create Database Backup

```bash
# MANDATORY: Backup before swap execution
docker-compose exec db pg_dump -U scheduler residency_scheduler > \
  backups/swap_execution_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backups/swap_execution_*.sql | tail -1
```

### Step 3: Execute Swap

```bash
# POST: Execute the swap
curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "executed_by": "coordinator-001",
    "execution_time": "2026-01-02T09:00:00Z",
    "audit_note": "Standard 1:1 resident swap - PGY1-001 and PGY1-002"
  }'

# Response:
# {
#   "swap_id": "SWAP_20251231_001",
#   "status": "executed",
#   "executed_at": "2026-01-02T09:00:00Z",
#   "transaction_id": "TXN_20260102_001",
#   "assignments_modified": 2,
#   "assignments_created": 0
# }
```

### Step 4: Verify Execution

```bash
# GET: Verify both assignments were updated
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/execution-result \
  -H "Authorization: Bearer $TOKEN"

# Manually verify
curl -X GET http://localhost:8000/api/assignments/PGY1-001 \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.assignments[] | select(.date == "2026-02-15")'

# Should show new rotation assignment
```

**Execution Verification Template:**

```
SWAP EXECUTION VERIFICATION

Swap ID: _________________
Executed: _________________

ASSIGNMENTS BEFORE:
PGY1-001 on 2026-02-15: [Rotation A] ✓
PGY1-002 on 2026-03-15: [Rotation B] ✓

ASSIGNMENTS AFTER:
PGY1-001 on 2026-02-15: [Rotation B] ✓ CHANGED
PGY1-002 on 2026-03-15: [Rotation A] ✓ CHANGED

VERIFICATION:
☐ Both assignments modified
☐ Correct rotations assigned
☐ All other assignments unchanged
☐ Database integrity verified
☐ ACGME compliance maintained

Verified By: ______________________
```

### Step 5: Update Schedules and Notifications

```bash
# POST: Update participant schedules
curl -X POST http://localhost:8000/api/scheduler/update-assignments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001",
    "action": "refresh_schedules"
  }'

# Send execution confirmation
cat > execution_confirmation.txt << 'EOF'
SWAP EXECUTED SUCCESSFULLY

Swap ID: SWAP_20251231_001
Execution Date: 2026-01-02

Your schedule has been updated with the approved swap.

YOUR NEW ASSIGNMENTS:
[New schedule details for affected blocks]

The changes are now visible in your portal.

24-HOUR REVERSAL AVAILABLE:
If this was executed in error, contact admin within 24 hours to reverse.

Questions? Contact: schedule-admin@program.edu
EOF

# Send to all participants
curl -X POST http://localhost:8000/api/notifications/send-bulk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "notification_type": "swap_executed",
    "recipients": ["PGY1-001", "PGY1-002"],
    "swap_id": "SWAP_20251231_001"
  }'
```

---

## Rollback Procedures

### Decision Tree

```
Must Rollback?
├─ YES: Swap executed in error
│   ├─ Within 24 hours: IMMEDIATE ROLLBACK
│   ├─ After 24 hours: REQUEST REVERSAL SWAP
├─ YES: Swap created compliance violation
│   ├─ Immediately detected: IMMEDIATE ROLLBACK
│   ├─ Later detected: ESCALATE TO PD & LEGAL
├─ NO: Swap valid and appropriate
│   ├─ Monitor for issues
```

### Step 1: Initiate Rollback

```bash
# POST: Initiate swap rollback (within 24 hours)
curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/rollback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Executed in error - participant request",
    "initiated_by": "coordinator-001",
    "restore_from_backup": true
  }'

# Response:
# {
#   "swap_id": "SWAP_20251231_001",
#   "status": "rollback_initiated",
#   "rollback_job_id": "RB_20260102_001",
#   "estimated_completion": "2026-01-02T10:00:00Z"
# }
```

### Step 2: Verify Rollback

```bash
# GET: Check rollback status
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/rollback-status \
  -H "Authorization: Bearer $TOKEN"

# Verify assignments restored
curl -X GET http://localhost:8000/api/assignments/PGY1-001 \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.assignments[] | select(.date == "2026-02-15")'

# Should show original rotation assignment
```

### Step 3: Notify Participants

```bash
# Send rollback notification
cat > rollback_notification.txt << 'EOF'
SWAP ROLLBACK COMPLETED

Swap ID: SWAP_20251231_001

This swap has been rolled back and your original schedule has been restored.

RESTORED ASSIGNMENTS:
[Original schedule details]

REASON: [Rollback reason]

If you have questions, contact: schedule-admin@program.edu
EOF
```

**Rollback Verification Checklist:**

```
ROLLBACK VERIFICATION

Swap ID: _________________
Rollback Initiated: _________________ Date: __________

RESTORATION ITEMS:
☐ Original assignments restored
☐ Modified dates match
☐ Rotation assignments correct
☐ Database transaction logged
☐ All related records updated

VERIFICATION:
☐ All rollback items verified
☐ No residual swap data remaining
☐ System integrity confirmed
☐ Participants notified

Verified By: ______________________
```

---

## Compliance Verification

### Step 1: ACGME Rule Check

```bash
# POST: Verify ACGME rules still satisfied after swap
curl -X POST http://localhost:8000/api/scheduler/validate/acgme \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "check_residents": ["PGY1-001", "PGY1-002"],
    "check_period": "rolling_month",
    "date_range": "2026-01-01:2026-03-31"
  }'

# Response should show zero violations
# {
#   "residents_checked": 2,
#   "violations_found": 0,
#   "compliance_status": "PASS"
# }
```

### Step 2: Work Hour Verification

```bash
# POST: Verify work hours still compliant
curl -X POST http://localhost:8000/api/scheduler/validate/work-hours \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "residents": ["PGY1-001", "PGY1-002"],
    "weeks": 4,
    "starting": "2026-01-15"
  }'

# Should show all residents within 80 hours/week average
```

### Step 3: Supervision Ratio Check

```bash
# POST: Verify supervision ratios maintained
curl -X POST http://localhost:8000/api/scheduler/validate/supervision \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "affected_rotations": ["inpatient_call"],
    "affected_dates": ["2026-02-15"]
  }'

# Response: All supervision ratios within acceptable range
```

**Post-Swap Compliance Report:**

```
POST-SWAP COMPLIANCE VERIFICATION

Swap ID: _________________
Verification Date: _________________

ACGME RULE COMPLIANCE:
80-Hour Rule:
  PGY1-001: [XX hours/week] ☐ Compliant ☐ Violation
  PGY1-002: [XX hours/week] ☐ Compliant ☐ Violation

1-in-7 Rule:
  PGY1-001: [Rest pattern] ☐ Compliant ☐ Violation
  PGY1-002: [Rest pattern] ☐ Compliant ☐ Violation

Supervision Ratios:
  [Rotation]: [Ratio] ☐ Compliant ☐ Violation

OVERALL COMPLIANCE STATUS:
☐ COMPLIANT: All rules satisfied
☐ NON-COMPLIANT: Violations detected

If violations, escalate to: Program Director

Verified By: ______________________
```

---

## Troubleshooting

### Issue: "Swap Participants Not Confirmed"

**Cause:** One or more participants haven't confirmed the swap

**Solution:**

```bash
# Check confirmation status
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/confirmations \
  -H "Authorization: Bearer $TOKEN"

# Send reminder to pending participants
curl -X POST http://localhost:8000/api/swaps/send-reminders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001",
    "recipient_status": "pending"
  }'

# If no confirmation after deadline, reject swap
curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/reject \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Confirmation deadline passed without all participants confirming"
  }'
```

### Issue: "Credential Missing for Swapped Rotation"

**Cause:** Participant lacks required credential for new rotation

**Solution:**

```bash
# Check credential gap
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/credential-gaps \
  -H "Authorization: Bearer $TOKEN"

# Option 1: Obtain credential before swap date
# Have participant complete training by swap date

# Option 2: Grant temporary waiver (requires PD approval)
curl -X POST http://localhost:8000/api/admin/waivers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "PGY1-001",
    "credential": "procedure_training",
    "waiver_type": "temporary",
    "duration_days": 14,
    "approved_by": "PD-001"
  }'

# Option 3: Cancel swap if credential cannot be obtained
curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/cancel \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Required credential unavailable before swap date"
  }'
```

### Issue: "Coverage Gap After Swap"

**Cause:** Rotation would have insufficient coverage after swap

**Solution:**

```bash
# Get coverage analysis
curl -X GET http://localhost:8000/api/swaps/SWAP_20251231_001/coverage-gaps \
  -H "Authorization: Bearer $TOKEN"

# Option 1: Find alternative swap partner
curl -X POST http://localhost:8000/api/swaps/find-alternatives \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "swap_id": "SWAP_20251231_001",
    "strategy": "coverage-preserving"
  }'

# Option 2: Deny swap due to coverage issues
curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/deny \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Swap would create coverage gap in inpatient rotation"
  }'

# Option 3: Conditional approval with coverage mitigation
# Approve if additional coverage can be assigned
```

### Issue: "ACGME Violation After Swap Execution"

**Cause:** Swap created ACGME compliance violation

**Solution:**

```bash
# Immediately identify violation
curl -X GET http://localhost:8000/api/scheduler/compliance-violations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"after_swap_id": "SWAP_20251231_001"}'

# If within 24 hours: ROLLBACK
if [ $(echo "$(date) - swap_execution_time" | bc) -lt 86400 ]; then
  curl -X POST http://localhost:8000/api/swaps/SWAP_20251231_001/rollback \
    -H "Authorization: Bearer $TOKEN"
fi

# If after 24 hours: ESCALATE
curl -X POST http://localhost:8000/api/incidents/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "severity": "high",
    "category": "compliance_violation",
    "description": "Swap SWAP_20251231_001 created ACGME violation",
    "escalate_to": "PD,GME"
  }'
```

---

**Document Version:** 1.0
**Last Updated:** 2025-12-31
**Owner:** Scheduling Administration
**Review Cycle:** Quarterly or as needed
