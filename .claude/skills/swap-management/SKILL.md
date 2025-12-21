---
name: swap-management
description: Schedule swap workflow expertise for faculty and resident shift exchanges. Use when processing swap requests, finding compatible matches, or resolving scheduling conflicts. Integrates with swap auto-matcher and MCP tools.
---

# Swap Management Skill

Expert procedures for managing schedule swaps while maintaining compliance and fairness.

## When This Skill Activates

- Processing swap requests
- Finding compatible swap partners
- Resolving scheduling conflicts
- Answering swap policy questions
- Validating proposed swaps
- Handling emergency coverage

## Swap Types

### 1. One-to-One Swap
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

### 2. Absorb (Give Away)
**Definition:** One person takes another's shift without exchange

```
Person A: Gives away Friday PM
Person B: Absorbs Friday PM (no return)
```

**Requirements:**
- Receiver doesn't exceed limits
- Receiver qualified for rotation
- Giver has legitimate reason (PTO, conference, etc.)

### 3. Three-Way Swap
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

## Auto-Matching Algorithm

The system finds compatible swap partners using:

### Match Criteria (Ranked)
1. **Qualification Match** - Same rotation certification
2. **Hour Balance** - Neither party exceeds limits
3. **Preference Alignment** - Historical preferences
4. **Fairness Score** - Workload distribution
5. **Proximity** - Schedule adjacency for handoffs

### MCP Tool
```
Tool: analyze_swap_compatibility
Input: { requestor_id, target_shift, swap_type }
Output: { matches: [...], compatibility_scores: {...} }
```

## Validation Checklist

Before approving any swap:

### Pre-Swap Checks
- [ ] Both parties have consented
- [ ] Qualification/credentialing verified
- [ ] 80-hour limit maintained for both
- [ ] 1-in-7 day off preserved
- [ ] Supervision ratios still valid
- [ ] No double-booking created
- [ ] Handoff timing adequate

### Post-Swap Verification
- [ ] Calendar updated for both parties
- [ ] Notifications sent
- [ ] Audit trail created
- [ ] Metrics recalculated

## Swap Request Workflow

### Step 1: Request Submission
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

### Step 2: Auto-Match (if no partner specified)
System runs matching algorithm and returns:
- Top 5 compatible partners
- Compatibility scores
- Any warnings (approaching limits, etc.)

### Step 3: Partner Response
Partner has 48 hours to:
- Accept → Proceeds to validation
- Decline → Returns to matching
- Counter-propose → New swap terms

### Step 4: Validation
System performs full compliance check:
```
Tool: validate_swap
Returns: { valid: boolean, issues: [], warnings: [] }
```

### Step 5: Execution
If valid:
1. Update assignments in database
2. Send calendar invites
3. Notify stakeholders
4. Log audit trail

### Step 6: Rollback Window
24-hour window to reverse swap if issues discovered.

## Emergency Coverage Protocol

When immediate coverage needed:

### Tier 1: Available Pool
Check faculty/residents marked as backup:
```sql
SELECT * FROM persons
WHERE backup_available = true
  AND NOT EXISTS (shift on target date)
  AND weekly_hours < 75;
```

### Tier 2: Swap Market
Broadcast need to all qualified personnel:
- Push notification
- Email alert
- Slack message (via n8n)

### Tier 3: Absorb Request
Ask nearby shifts to extend coverage:
- Maximum 4-hour extension
- Must maintain 8-hour break

### Tier 4: Escalation
If unfilled after 4 hours:
- Alert Program Director
- Consider schedule restructure
- Document coverage gap

## Fairness Considerations

### Swap Equity Tracking
Monitor swap patterns for fairness:

| Metric | Healthy | Warning | Action Needed |
|--------|---------|---------|---------------|
| Swap Balance | ±2 per quarter | ±4 | Review workload |
| Weekend Swaps | Even distribution | >2 std dev | Redistribute |
| Holiday Coverage | Rotating | Same person 2x | Force rotation |

### Protected Categories
Extra scrutiny for swaps affecting:
- Residents on probation
- Faculty approaching burnout indicators
- Personnel with documented accommodations

## Common Scenarios

### Scenario: Conference Conflict
**Request:** Need Thursday off for required conference
**Process:**
1. Check if shift is swappable (not frozen)
2. Find partner with complementary availability
3. Validate both parties' compliance
4. Execute swap with "conference" reason code

### Scenario: Sick Coverage
**Request:** Called in sick, need immediate coverage
**Process:**
1. Skip consent (emergency protocol)
2. Query backup pool first
3. Broadcast if no backups available
4. Log as emergency absorb
5. Balance workload later

### Scenario: Preference Swap
**Request:** Want to swap AM for PM regularly
**Process:**
1. Check if standing swap arrangement possible
2. Validate long-term compliance
3. If approved, create recurring swap template
4. Review quarterly for fairness

## Escalation Triggers

**Escalate to Coordinator when:**
1. No compatible matches found
2. Swap would create compliance violation
3. Same person requesting >3 swaps/month
4. Pattern suggests scheduling problem
5. Conflict between swap participants

## Reporting Format

```markdown
## Swap Request Summary

**Request ID:** [ID]
**Type:** [One-to-One / Absorb / Three-Way]
**Status:** [Pending / Matched / Validated / Executed / Rejected]

### Parties
- Requestor: [Name] - [Current Hours: X/80]
- Partner: [Name] - [Current Hours: Y/80]

### Shifts Involved
- [Date] [Session] [Rotation] → From [A] to [B]
- [Date] [Session] [Rotation] → From [B] to [A]

### Validation Result
- Compliance: [PASS/FAIL]
- Warnings: [List any]
- Approval: [Auto/Manual Required]

### Next Steps
1. [Action item]
```

## MCP Tools Reference

| Tool | Purpose |
|------|---------|
| `analyze_swap_compatibility` | Find matching partners |
| `validate_swap` | Check compliance impact |
| `execute_swap` | Perform the swap |
| `rollback_swap` | Reverse within 24h window |
| `get_swap_history` | Audit trail query |
