---
name: swap-management
description: Schedule swap workflow expertise for faculty and resident shift exchanges. Use when processing swap requests, finding compatible matches, or resolving scheduling conflicts. Integrates with swap auto-matcher and MCP tools.
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

***REMOVED******REMOVED*** Common Scenarios

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
