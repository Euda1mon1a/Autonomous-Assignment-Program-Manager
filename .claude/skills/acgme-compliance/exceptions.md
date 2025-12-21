# ACGME Exception Documentation

Procedures for documenting and approving exceptions to standard ACGME limits.

## When Exceptions Apply

ACGME allows limited exceptions with proper documentation:

1. **Continuity of Care**: Completing critical patient care
2. **Educational Value**: Rare learning opportunity
3. **Emergency Coverage**: Unforeseen circumstances
4. **Moonlighting**: Pre-approved external work

## Exception Request Process

### Step 1: Document Justification
```markdown
## Exception Request

**Date:** [Date]
**Resident:** [Name]
**Rule Affected:** [80-hour / 1-in-7 / Supervision]
**Requested Exception:** [Specific deviation]
**Justification:** [Detailed reason]
**Duration:** [One-time / Recurring]
**Mitigation:** [How harm will be minimized]
```

### Step 2: Approval Chain
1. Attending Physician (for continuity of care)
2. Chief Resident (for scheduling conflicts)
3. Program Director (for recurring or significant exceptions)
4. DIO (for program-wide policy exceptions)

### Step 3: Documentation
- Log in resident's duty hour tracking
- Note in schedule system with reason code
- Include in monthly compliance report

## Exception Categories

### Category A: Continuity of Care (Auto-Approved)
- Patient in active crisis
- Procedure cannot be handed off
- Maximum additional: 4 hours
- **Must document in patient chart**

### Category B: Educational (PD Approval)
- Rare surgical case
- Unique learning opportunity
- Maximum: Once per block
- **Resident must request**

### Category C: Emergency (Retrospective)
- Unforeseen mass casualty
- Natural disaster response
- System failure requiring all-hands
- **Document within 24 hours**

### Category D: Moonlighting (Pre-Approved)
- Must not exceed 80-hour total
- Must maintain performance standards
- Requires written agreement
- **Count toward duty hours**

## Exception Limits

| Exception Type | Max Per Month | Max Per Year |
|----------------|---------------|--------------|
| Continuity of Care | 4 | 24 |
| Educational | 2 | 12 |
| Emergency | As needed | Document all |
| Moonlighting | Per agreement | Per agreement |

## Red Flags (No Exceptions)

These situations require immediate correction, no exceptions:
- Resident impairment due to fatigue
- Pattern of repeated exceptions for same person
- Supervision gap during high-risk procedure
- Falsification of duty hour logs

## Audit Trail

All exceptions tracked in:
```
backend/app/models/compliance_exception.py
```

Query exceptions:
```sql
SELECT * FROM compliance_exceptions
WHERE created_at > NOW() - INTERVAL '30 days'
ORDER BY resident_id, created_at;
```
