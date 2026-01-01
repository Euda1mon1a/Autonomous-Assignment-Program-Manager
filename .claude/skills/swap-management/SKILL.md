---
name: swap-management
description: Schedule swap workflow expertise for faculty and resident shift exchanges. Use when processing swap requests, finding compatible matches, or resolving scheduling conflicts. Integrates with swap auto-matcher and MCP tools.
model_tier: sonnet
parallel_hints:
  can_parallel_with: [swap-analyzer, schedule-validator]
  must_serialize_with: [SWAP_EXECUTION, safe-schedule-generation]
  preferred_batch_size: 3
context_hints:
  max_file_context: 40
  compression_level: 1
  requires_git_context: false
  requires_db_context: true
escalation_triggers:
  - pattern: "ACGME.*violation"
    reason: "Swaps causing compliance violations require human approval"
  - pattern: "emergency.*coverage"
    reason: "Emergency coverage requires human oversight"
  - keyword: ["rollback", "reverse", "undo"]
    reason: "Swap reversals may have cascade effects"
---

***REMOVED*** Swap Management Skill

Expert procedures for managing schedule swaps while maintaining compliance and fairness.

***REMOVED******REMOVED*** When This Skill Activates

- Processing swap requests
- Finding compatible swap partners
- Resolving scheduling conflicts
- Answering swap policy questions
- Validating proposed swaps
- Handling emergency coverage

***REMOVED******REMOVED*** Swap Types

***REMOVED******REMOVED******REMOVED*** 1. One-to-One Swap
**Definition:** Direct exchange between two people

```
Person A: Tuesday AM → Person B
Person B: Thursday PM → Person A
```

**Requirements:**
- Both parties consent
- Both qualified for swapped rotation
- Neither exceeds hour limits after swap
- Supervision ratios maintained

***REMOVED******REMOVED******REMOVED*** 2. Absorb (Give Away)
**Definition:** One person takes another's shift without exchange

```
Person A: Gives away Friday PM
Person B: Absorbs Friday PM (no return)
```

**Requirements:**
- Receiver doesn't exceed limits
- Receiver qualified for rotation
- Giver has legitimate reason (PTO, conference, etc.)

***REMOVED******REMOVED******REMOVED*** 3. Three-Way Swap
**Definition:** Circular exchange among three people

```
A → B's shift
B → C's shift
C → A's shift
```

**Requirements:**
- All three consent
- All compliance checks pass
- Tracked as linked transactions

***REMOVED******REMOVED*** Auto-Matching Algorithm

The system finds compatible swap partners using:

***REMOVED******REMOVED******REMOVED*** Match Criteria (Ranked)
1. **Qualification Match** - Same rotation certification
2. **Hour Balance** - Neither party exceeds limits
3. **Preference Alignment** - Historical preferences
4. **Fairness Score** - Workload distribution
5. **Proximity** - Schedule adjacency for handoffs

***REMOVED******REMOVED******REMOVED*** MCP Tool
```
Tool: analyze_swap_compatibility
Input: { requestor_id, target_shift, swap_type }
Output: { matches: [...], compatibility_scores: {...} }
```

***REMOVED******REMOVED*** Validation Checklist

Before approving any swap:

***REMOVED******REMOVED******REMOVED*** Pre-Swap Checks
- [ ] Both parties have consented
- [ ] Qualification/credentialing verified
- [ ] 80-hour limit maintained for both
- [ ] 1-in-7 day off preserved
- [ ] Supervision ratios still valid
- [ ] No double-booking created
- [ ] Handoff timing adequate

***REMOVED******REMOVED******REMOVED*** Post-Swap Verification
- [ ] Calendar updated for both parties
- [ ] Notifications sent
- [ ] Audit trail created
- [ ] Metrics recalculated

***REMOVED******REMOVED*** Swap Request Workflow

***REMOVED******REMOVED******REMOVED*** Step 1: Request Submission
```
POST /api/swap/request
{
  "requestor_id": "uuid",
  "target_shift": { "date": "2025-01-15", "session": "PM" },
  "swap_type": "one_to_one",
  "reason": "Conference attendance",
  "preferred_partners": ["uuid1", "uuid2"]  // optional
}
```

***REMOVED******REMOVED******REMOVED*** Step 2: Auto-Match (if no partner specified)
System runs matching algorithm and returns:
- Top 5 compatible partners
- Compatibility scores
- Any warnings (approaching limits, etc.)

***REMOVED******REMOVED******REMOVED*** Step 3: Partner Response
Partner has 48 hours to:
- Accept → Proceeds to validation
- Decline → Returns to matching
- Counter-propose → New swap terms

***REMOVED******REMOVED******REMOVED*** Step 4: Validation
System performs full compliance check:
```
Tool: validate_swap
Returns: { valid: boolean, issues: [], warnings: [] }
```

***REMOVED******REMOVED******REMOVED*** Step 5: Execution
If valid:
1. Update assignments in database
2. Send calendar invites
3. Notify stakeholders
4. Log audit trail

***REMOVED******REMOVED******REMOVED*** Step 6: Rollback Window
24-hour window to reverse swap if issues discovered.

***REMOVED******REMOVED*** Emergency Coverage Protocol

When immediate coverage needed:

***REMOVED******REMOVED******REMOVED*** Tier 1: Available Pool
Check faculty/residents marked as backup:
```sql
SELECT * FROM persons
WHERE backup_available = true
  AND NOT EXISTS (shift on target date)
  AND weekly_hours < 75;
```

***REMOVED******REMOVED******REMOVED*** Tier 2: Swap Market
Broadcast need to all qualified personnel:
- Push notification
- Email alert
- Slack message (via n8n)

***REMOVED******REMOVED******REMOVED*** Tier 3: Absorb Request
Ask nearby shifts to extend coverage:
- Maximum 4-hour extension
- Must maintain 8-hour break

***REMOVED******REMOVED******REMOVED*** Tier 4: Escalation
If unfilled after 4 hours:
- Alert Program Director
- Consider schedule restructure
- Document coverage gap

***REMOVED******REMOVED*** Fairness Considerations

***REMOVED******REMOVED******REMOVED*** Swap Equity Tracking
Monitor swap patterns for fairness:

| Metric | Healthy | Warning | Action Needed |
|--------|---------|---------|---------------|
| Swap Balance | ±2 per quarter | ±4 | Review workload |
| Weekend Swaps | Even distribution | >2 std dev | Redistribute |
| Holiday Coverage | Rotating | Same person 2x | Force rotation |

***REMOVED******REMOVED******REMOVED*** Protected Categories
Extra scrutiny for swaps affecting:
- Residents on probation
- Faculty approaching burnout indicators
- Personnel with documented accommodations

***REMOVED******REMOVED*** Examples

***REMOVED******REMOVED******REMOVED*** Example 1: Conference Swap Request

**User Request:** "Dr. Smith needs to swap her Thursday March 24 PM shift because she has a required conference. Can you help find a match?"

**Claude Response:**

**Step 1: Verify shift eligibility**
```
Checking shift details...
- Person: Dr. Sarah Smith (FAC-CORE-02)
- Date: March 24, 2026 (Thursday PM)
- Current assignment: Outpatient Clinic
- Shift status: Active (not frozen) ✅
```

**Step 2: Run auto-matcher**
```bash
Calling analyze_swap_compatibility...

Top 5 compatible matches:
1. Dr. Johnson (FAC-CORE-05) - Score: 0.92
   - Available: Tuesday PM (clinic)
   - Current hours: 45/80 (safe buffer)
   - Historical preference: Prefers PM shifts ✅

2. Dr. Williams (FAC-CORE-01) - Score: 0.85
   - Available: Wednesday AM (clinic)
   - Current hours: 52/80
   - Note: Approaching preferred workload limit

3. Dr. Davis (FAC-CORE-07) - Score: 0.78
   - Available: Friday AM (procedures)
   - Current hours: 38/80
   - Note: Different rotation type (may need cross-training)
```

**Step 3: Validate top match**
```json
Validating swap: Smith ↔ Johnson...

{
  "valid": true,
  "compliance_check": {
    "smith_hours_post_swap": 47,
    "johnson_hours_post_swap": 47,
    "acgme_violations": 0,
    "supervision_ratios": "maintained"
  },
  "warnings": []
}
```

**Recommendation:**
> "✅ Dr. Johnson is the best match (92% compatibility). Both will remain well under work hour limits. Swap maintains all compliance requirements. Shall I notify Dr. Johnson and request consent?"

**User:** "Yes, please proceed"

**Step 4: Execute swap**
```
Sending swap request to Dr. Johnson...
- Notification sent via email + app
- Awaiting response (48-hour window)
- Swap ID: SWAP-20260312-001

I'll notify you when Dr. Johnson responds.
```

***REMOVED******REMOVED******REMOVED*** Example 2: Emergency Sick Coverage

**User Request:** "URGENT: Dr. Martinez just called in sick for her Sunday call shift. We need immediate coverage."

**Claude Response:**

**🚨 Emergency coverage protocol activated**

**Step 1: Check backup pool**
```sql
Querying available backup faculty...

Backup pool found: 3 available
1. Dr. Chen (FAC-CORE-08) - No assignments Sunday
   - Current hours: 42/80 ✅
   - Qualified for call ✅
   - Marked as backup_available ✅

2. Dr. Patel (FAC-CORE-11) - Has AM shift only
   - Could extend to cover PM call
   - Current hours: 38/80 ✅

3. Dr. Kim (FAC-CORE-03) - Weekend off
   - In backup pool but hours: 68/80 ⚠️
```

**Step 2: Validate emergency absorb**
```
Checking Dr. Chen for emergency coverage...

Compliance check:
- Post-absorb hours: 42 + 12 = 54/80 ✅
- 1-in-7 day off: Preserved ✅
- No double-booking: ✅
- Recent call: Last call 9 days ago ✅

✅ Dr. Chen is safe to absorb the shift
```

**Step 3: Execute without consent (emergency)**
```bash
Executing emergency absorb...

POST /api/swap/emergency-absorb
{
  "original_person_id": "FAC-MARTINEZ",
  "replacement_person_id": "FAC-CHEN",
  "shift": "2026-03-27 PM (Sunday Call)",
  "reason": "sick_call",
  "emergency": true,
  "skip_consent": true
}

✅ Assignment updated
✅ Dr. Chen notified (SMS + email + app)
✅ Calendar invite sent
✅ Program Director notified of emergency swap
```

**Step 4: Workload balancing note**
```
Emergency swap logged for fairness tracking:
- Dr. Chen: +1 emergency absorb (total this quarter: 2)
- Dr. Martinez: Sick day recorded

Recommendation: Offer Dr. Chen compensatory time off or first pick
on next swap request to maintain equity.
```

**Summary:**
> "✅ Emergency coverage secured. Dr. Chen will cover Sunday call. All compliance requirements maintained. Dr. Martinez can focus on recovery."

***REMOVED******REMOVED******REMOVED*** Example 3: Standing Preference Swap

**User Request:** "Two residents want to permanently swap their clinic days - PGY-2 resident wants Mondays instead of Tuesdays. Is this possible?"

**Claude Response:**

**Step 1: Identify swap scope**
```
Request: Standing swap arrangement
- Resident A (PGY-2): Currently Tuesday PM clinic
- Resident B (PGY-2): Currently Monday PM clinic
- Duration: Remainder of academic year (6 months)
```

**Step 2: Check long-term compliance**
```bash
Validating standing swap arrangement...

Checking 24-week projection:
✅ Week 1-4: Both residents maintain <80hr limit
✅ Week 5-8: Both residents maintain <80hr limit
...
✅ Week 21-24: Both residents maintain <80hr limit

⚠️  Warning: Resident A has scheduled conference March 30 (Monday)
    - Will need one-time exception that week

Long-term ACGME compliance: ✅ PASS
```

**Step 3: Create recurring swap template**
```json
Creating standing swap template...

{
  "template_id": "SWAP-TEMPLATE-001",
  "type": "recurring_weekly",
  "participant_a": "RES-PGY2-03",
  "participant_b": "RES-PGY2-07",
  "swap_pattern": {
    "a_gives": "Tuesday PM Clinic",
    "a_receives": "Monday PM Clinic",
    "b_gives": "Monday PM Clinic",
    "b_receives": "Tuesday PM Clinic"
  },
  "duration": "2026-03-12 to 2026-09-30",
  "exceptions": ["2026-03-30 (Resident A conference)"],
  "review_frequency": "quarterly"
}

✅ Template created
✅ Next 24 swaps auto-scheduled
```

**Step 4: Fairness review schedule**
```
Standing swap approved with quarterly review:
- First review: June 15, 2026
- Review criteria:
  * Both residents satisfied with arrangement
  * No negative impact on team dynamics
  * Work hour compliance maintained
  * Fair distribution of weekend coverage

I'll remind you 1 week before each quarterly review.
```

**Recommendation:**
> "✅ Standing swap approved for 6 months. Both residents will swap clinic days weekly (with 1 exception for conference). Quarterly fairness reviews scheduled. Both residents notified of approval."

---

***REMOVED******REMOVED*** Common CLI Scenarios

***REMOVED******REMOVED******REMOVED*** Scenario: Conference Conflict
**Request:** Need Thursday off for required conference
**Process:**
1. Check if shift is swappable (not frozen)
2. Find partner with complementary availability
3. Validate both parties' compliance
4. Execute swap with "conference" reason code

***REMOVED******REMOVED******REMOVED*** Scenario: Sick Coverage
**Request:** Called in sick, need immediate coverage
**Process:**
1. Skip consent (emergency protocol)
2. Query backup pool first
3. Broadcast if no backups available
4. Log as emergency absorb
5. Balance workload later

***REMOVED******REMOVED******REMOVED*** Scenario: Preference Swap
**Request:** Want to swap AM for PM regularly
**Process:**
1. Check if standing swap arrangement possible
2. Validate long-term compliance
3. If approved, create recurring swap template
4. Review quarterly for fairness

***REMOVED******REMOVED*** Escalation Triggers

**Escalate to Coordinator when:**
1. No compatible matches found
2. Swap would create compliance violation
3. Same person requesting >3 swaps/month
4. Pattern suggests scheduling problem
5. Conflict between swap participants

***REMOVED******REMOVED*** Reporting Format

```markdown
***REMOVED******REMOVED*** Swap Request Summary

**Request ID:** [ID]
**Type:** [One-to-One / Absorb / Three-Way]
**Status:** [Pending / Matched / Validated / Executed / Rejected]

***REMOVED******REMOVED******REMOVED*** Parties
- Requestor: [Name] - [Current Hours: X/80]
- Partner: [Name] - [Current Hours: Y/80]

***REMOVED******REMOVED******REMOVED*** Shifts Involved
- [Date] [Session] [Rotation] → From [A] to [B]
- [Date] [Session] [Rotation] → From [B] to [A]

***REMOVED******REMOVED******REMOVED*** Validation Result
- Compliance: [PASS/FAIL]
- Warnings: [List any]
- Approval: [Auto/Manual Required]

***REMOVED******REMOVED******REMOVED*** Next Steps
1. [Action item]
```

***REMOVED******REMOVED*** MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `analyze_swap_compatibility` | Find matching partners |
| `validate_swap` | Check compliance impact |
| `execute_swap` | Perform the swap |
| `rollback_swap` | Reverse within 24h window |
| `get_swap_history` | Audit trail query |

***REMOVED******REMOVED*** Concrete Usage Example

***REMOVED******REMOVED******REMOVED*** End-to-End: Processing a Conference Swap Request

**Scenario:** Dr. Smith needs Thursday PM off for a required conference. Find a compatible swap partner and execute the swap safely.

**Step 1: Receive Swap Request**
```python
***REMOVED*** Via API or admin interface
from app.models import SwapRequest
from datetime import date

swap_request = SwapRequest(
    requestor_id="person-001",  ***REMOVED*** Dr. Smith
    target_date=date(2025, 2, 13),  ***REMOVED*** Thursday
    target_session="PM",
    swap_type="one_to_one",
    reason="ACFP Conference (required)",
    preferred_partners=[]  ***REMOVED*** Will auto-match
)
```

**Step 2: Find Compatible Partners**
```python
from app.services.swap_matcher import SwapMatcher

matcher = SwapMatcher(db)
matches = await matcher.find_compatible_partners(
    requestor_id="person-001",
    target_shift={
        "date": date(2025, 2, 13),
        "session": "PM",
        "rotation": "FM Clinic"
    },
    max_matches=5
)

print(f"Found {len(matches)} compatible partners:")
for match in matches:
    print(f"  {match.person_id}: {match.compatibility_score:.2f}")
    print(f"    - Current hours: {match.current_weekly_hours}/80")
    print(f"    - Qualified: {match.is_qualified}")
    print(f"    - Suggested return shift: {match.suggested_return_shift}")
```

**Expected Output:**
```
Found 3 compatible partners:
  person-002: 0.92
    - Current hours: 68/80
    - Qualified: True
    - Suggested return shift: 2025-02-18 AM (Tuesday)

  person-005: 0.87
    - Current hours: 65/80
    - Qualified: True
    - Suggested return shift: 2025-02-19 PM (Wednesday)

  person-003: 0.75
    - Current hours: 72/80
    - Qualified: True
    - Suggested return shift: 2025-02-20 AM (Thursday)
```

**Step 3: Present Options to Requestor**
```python
***REMOVED*** Dr. Smith reviews matches and selects person-002
swap_request.partner_id = "person-002"
swap_request.return_shift = {
    "date": date(2025, 2, 18),
    "session": "AM"
}
```

**Step 4: Validate Swap**
```python
from app.services.swap_validator import SwapValidator

validator = SwapValidator(db)
validation_result = await validator.validate_swap(swap_request)

if validation_result.is_valid:
    print("✅ Swap validation: PASS")
else:
    print("❌ Swap validation: FAIL")
    for issue in validation_result.issues:
        print(f"   - {issue.severity}: {issue.description}")

***REMOVED*** Check warnings even if valid
if validation_result.warnings:
    print("⚠️ Warnings:")
    for warning in validation_result.warnings:
        print(f"   - {warning}")
```

**Expected Output:**
```
✅ Swap validation: PASS

⚠️ Warnings:
   - person-002 will have 3 swaps this month (approaching limit of 4)
```

**Step 5: Get Partner Consent**
```python
***REMOVED*** Send notification to partner
from app.notifications import send_swap_request_notification

await send_swap_request_notification(
    to_person_id="person-002",
    swap_request=swap_request,
    expiration_hours=48
)

print("Notification sent. Waiting for response...")

***REMOVED*** Partner responds (via API or UI)
***REMOVED*** Assume they accept
swap_request.partner_status = "accepted"
swap_request.partner_accepted_at = datetime.now()
```

**Step 6: Execute Swap**
```python
from app.services.swap_executor import SwapExecutor

executor = SwapExecutor(db)
result = await executor.execute_swap(swap_request)

if result.success:
    print(f"✅ Swap executed successfully!")
    print(f"   Swap ID: {result.swap_id}")
    print(f"   Audit trail: {result.audit_trail_id}")

    ***REMOVED*** What changed:
    for change in result.changes:
        print(f"   - {change.person_id}: {change.from_assignment} → {change.to_assignment}")
else:
    print(f"❌ Swap failed: {result.error}")
```

**Expected Output:**
```
✅ Swap executed successfully!
   Swap ID: swap-12345
   Audit trail: audit-67890

   Changes:
   - person-001: 2025-02-13 PM FM Clinic → [unassigned]
   - person-002: 2025-02-13 PM [unassigned] → 2025-02-13 PM FM Clinic
   - person-001: 2025-02-18 AM [unassigned] → 2025-02-18 AM FM Clinic
   - person-002: 2025-02-18 AM FM Clinic → [unassigned]
```

**Step 7: Post-Execution Verification**
```python
***REMOVED*** Re-validate ACGME compliance for both parties
from app.scheduling.acgme_validator import ACGMEValidator

acgme_validator = ACGMEValidator()

for person_id in ["person-001", "person-002"]:
    assignments = await db.get_assignments_for_person(
        person_id,
        start_date=date(2025, 2, 1),
        end_date=date(2025, 2, 28)
    )

    compliance_result = acgme_validator.validate_person_schedule(
        person_id=person_id,
        assignments=assignments
    )

    if compliance_result.is_compliant:
        print(f"✅ {person_id}: ACGME compliant")
    else:
        print(f"❌ {person_id}: VIOLATIONS DETECTED - ROLLBACK NEEDED!")
        await executor.rollback_swap(result.swap_id)
        break
```

**Expected Output:**
```
✅ person-001: ACGME compliant
✅ person-002: ACGME compliant
```

**Step 8: Send Confirmations**
```python
***REMOVED*** Notify both parties
await send_swap_confirmation_notification(
    swap_id=result.swap_id,
    participants=["person-001", "person-002"],
    calendar_updates=True  ***REMOVED*** Send updated calendar invites
)

print("Swap complete! Confirmations sent.")
```

**Total Time:** ~5-10 minutes (most is waiting for partner response)

***REMOVED******REMOVED*** Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ SWAP REQUEST WORKFLOW                                       │
└─────────────────────────────────────────────────────────────┘

1. REQUEST SUBMISSION
   ├─ Requestor specifies shift to give away
   ├─ Optional: Suggest preferred partners
   └─ Provide reason/justification
              ↓
2. AUTO-MATCHING (if no partner specified)
   ├─ Find qualified personnel
   ├─ Check hour limits
   ├─ Score compatibility
   └─ Return top 5 matches
              ↓
3. PARTNER SELECTION
   ├─ Requestor reviews matches
   ├─ Selects preferred partner
   └─ Proposes return shift
              ↓
4. VALIDATION
   ├─ Check qualifications
   ├─ Verify ACGME compliance impact
   ├─ Confirm no double-booking
   └─ Generate warnings if any
              ↓
5. PARTNER CONSENT
   ├─ Send notification to partner
   ├─ 48-hour response window
   ├─ Partner accepts/declines/counters
   └─ If declined, return to step 2
              ↓
6. EXECUTION
   ├─ Begin database transaction
   ├─ Update assignments for both parties
   ├─ Create audit trail
   └─ Commit or rollback on error
              ↓
7. POST-EXECUTION VERIFICATION
   ├─ Re-validate ACGME compliance
   ├─ Check coverage maintained
   ├─ Update metrics
   └─ If issues, rollback immediately
              ↓
8. NOTIFICATIONS
   ├─ Send confirmations to both parties
   ├─ Update calendar invites
   ├─ Log in swap history
   └─ 24-hour rollback window begins
```

***REMOVED******REMOVED*** Common Failure Modes

***REMOVED******REMOVED******REMOVED*** Failure Mode 1: No Compatible Matches Found
**Symptom:** Auto-matcher returns empty list or very low compatibility scores

**Cause:** Shift is highly specialized, everyone at hour limits, or unusual constraints

**Example:**
```python
matches = await matcher.find_compatible_partners(...)
***REMOVED*** Returns: []
```

**Resolution:**
1. **Relax constraints temporarily:**
   ```python
   matches = await matcher.find_compatible_partners(
       ...,
       allow_near_limit=True,  ***REMOVED*** Include people at 75+ hours
       extend_search_window=True  ***REMOVED*** Look 2 weeks out instead of 1
   )
   ```

2. **Emergency protocol:**
   ```python
   ***REMOVED*** Broadcast to all qualified faculty
   await broadcast_emergency_coverage_request(
       shift=target_shift,
       reason="No matches found via auto-matcher"
   )
   ```

3. **Escalate to coordinator:**
   ```python
   await create_coordinator_intervention_ticket(
       swap_request_id=swap_request.id,
       reason="No compatible partners available"
   )
   ```

***REMOVED******REMOVED******REMOVED*** Failure Mode 2: Partner Declines After Validation
**Symptom:** Swap validated successfully but partner says no

**Cause:** Personal reasons, schedule preference, or found better alternative

**Example:**
```python
swap_request.partner_status = "declined"
swap_request.partner_decline_reason = "Prefer not to work that day"
```

**Resolution:**
1. **Return to matching:**
   ```python
   ***REMOVED*** Exclude declined partner
   matches = await matcher.find_compatible_partners(
       ...,
       exclude_person_ids=["person-002"]  ***REMOVED*** They already declined
   )
   ```

2. **Counter-proposal:**
   ```python
   ***REMOVED*** Partner might propose different return shift
   if swap_request.partner_counter_proposal:
       print(f"Partner proposes: {swap_request.partner_counter_proposal}")
       ***REMOVED*** Requestor can accept or decline
   ```

***REMOVED******REMOVED******REMOVED*** Failure Mode 3: ACGME Violation After Execution
**Symptom:** Swap executes but post-validation finds compliance issue

**Cause:** Validation logic bug, edge case, or cascading effect on other assignments

**Example:**
```python
***REMOVED*** Swap executes
result = await executor.execute_swap(swap_request)

***REMOVED*** But post-validation fails
compliance_result = acgme_validator.validate_person_schedule(person_id)
***REMOVED*** Returns: violations found - 81 hours in week of 2025-02-17
```

**Resolution:**
```python
***REMOVED*** Immediate rollback
await executor.rollback_swap(result.swap_id, reason="ACGME violation detected")

***REMOVED*** Investigate why validation passed initially
await log_validation_discrepancy(
    swap_id=result.swap_id,
    pre_validation=validation_result,
    post_validation=compliance_result
)

***REMOVED*** Fix validation logic before allowing future swaps
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 4: Double-Booking Created
**Symptom:** After swap, person assigned to two shifts at same time

**Cause:** Race condition, concurrent swap execution, or validation bug

**Example:**
```python
***REMOVED*** Person-002 now has:
***REMOVED*** 2025-02-13 PM: FM Clinic (from swap)
***REMOVED*** 2025-02-13 PM: Procedures (existing assignment not caught)
```

**Detection:**
```python
***REMOVED*** Check for overlaps
overlaps = await db.check_person_overlaps(person_id="person-002")
if overlaps:
    print(f"❌ CRITICAL: Double-booking detected!")
    for overlap in overlaps:
        print(f"   {overlap.date} {overlap.session}: {overlap.assignments}")
```

**Resolution:**
```python
***REMOVED*** Rollback immediately
await executor.rollback_swap(result.swap_id, reason="Double-booking detected")

***REMOVED*** Implement locking to prevent concurrent swaps
***REMOVED*** Add database-level unique constraint on (person_id, date, session)
```

***REMOVED******REMOVED******REMOVED*** Failure Mode 5: Swap Imbalance Tracking
**Symptom:** Person requests many swaps, always giving away shifts, never taking them

**Cause:** Gaming the system, burnout avoidance, or workload inequity

**Example:**
```python
swap_history = await db.get_swap_history(person_id="person-001")

***REMOVED*** Output:
***REMOVED*** Swaps requested: 12
***REMOVED*** Swaps given: 12 (always giving away shifts)
***REMOVED*** Swaps taken: 0 (never absorbing others' shifts)
```

**Detection:**
```python
***REMOVED*** Calculate swap balance
balance = swap_history.swaps_taken - swap_history.swaps_given
if abs(balance) > 4:
    print(f"⚠️ Swap imbalance: {balance}")
```

**Resolution:**
```python
***REMOVED*** Enforce balance requirement
if balance < -3:
    raise ValidationError(
        "You must accept incoming swaps before requesting more. "
        "Current balance: -3 (you've given 3 more than taken)"
    )

***REMOVED*** Or implement points system
***REMOVED*** Each swap given = -1 point
***REMOVED*** Each swap taken = +1 point
***REMOVED*** Require points >= -2 to request new swap
```

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** With `schedule-optimization`
**When:** Swaps have degraded schedule fairness
**Workflow:**
1. Execute swaps via swap-management
2. Check fairness metrics (Gini coefficient)
3. If fairness degraded significantly, invoke schedule-optimization
4. Generate minimal-change rebalancing adjustments
5. Execute as coordinated swaps

***REMOVED******REMOVED******REMOVED*** With `acgme-compliance`
**When:** Every swap execution
**Workflow:**
1. Before swap: Invoke acgme-compliance to validate
2. After swap: Invoke acgme-compliance to verify
3. If violations detected, rollback immediately
4. Document in audit trail

***REMOVED******REMOVED******REMOVED*** With `resilience-dashboard`
**When:** Checking if swaps maintain backup capacity
**Workflow:**
1. Before executing swap, check current resilience status
2. Model impact of swap on N-1 contingency
3. If swap would degrade resilience below threshold, warn or block
4. Document resilience impact in swap audit trail

***REMOVED******REMOVED******REMOVED*** With `swap-analyzer`
**When:** Analyzing patterns for fairness or abuse detection
**Workflow:**
1. Monthly: Invoke swap-analyzer to review all swaps
2. Identify imbalances, clustering, or suspicious patterns
3. Generate reports for program coordinator
4. Recommend policy adjustments if needed

***REMOVED******REMOVED******REMOVED*** With `security-audit`
**When:** Suspicious swap patterns detected
**Workflow:**
1. swap-management detects unusual pattern (e.g., circular swaps)
2. Invoke security-audit to investigate
3. Check for collusion, manipulation, or system abuse
4. Escalate to human if fraud suspected
