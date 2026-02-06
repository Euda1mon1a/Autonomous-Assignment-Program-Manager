# Audit Trail Workflow

Phase 3 of swap execution: Log all swap decisions with complete audit trail for compliance and debugging.

## Purpose

Create **comprehensive, immutable audit logs** for:
- Compliance audits (ACGME, command)
- Dispute resolution
- Post-mortem analysis
- Security investigations
- Performance monitoring

## What to Log

Every swap action must record:

### 1. Request Metadata

```python
{
    "request_id": "uuid",
    "swap_type": "one_to_one",  # or "absorb"
    "requested_at": "2025-01-15T10:30:00Z",
    "requested_by_user_id": "uuid",
    "requested_by_name": "Dr. Jane Smith",
    "source_faculty_id": "uuid",
    "source_faculty_name": "Dr. John Doe",
    "source_week": "2025-02-03",
    "target_faculty_id": "uuid",
    "target_faculty_name": "Dr. Alice Johnson",
    "target_week": "2025-02-10",  # null for absorb
    "reason": "Conference attendance"
}
```

### 2. Safety Check Results

```python
{
    "validation_timestamp": "2025-01-15T10:30:05Z",
    "decision": "PROCEED",  # REJECT | FLAG | PROCEED
    "tier1_result": {
        "80_hour_rule": {"status": "PASS", "source_hours": 65.0, "target_hours": 72.5},
        "1_in_7_rule": {"status": "PASS"},
        "supervision_ratios": {"status": "PASS", "pgy1_ratio": 1.8},
        "past_date_check": {"status": "PASS"}
    },
    "tier2_result": {
        "back_to_back": {"status": "WARN", "message": "Would create consecutive weeks"},
        "external_conflicts": {"status": "PASS"},
        "coverage_gaps": {"status": "PASS"},
        "call_cascade": {"status": "WARN", "affected_dates": ["2025-02-07", "2025-02-08"]}
    },
    "tier3_result": {
        "utilization_before": 0.72,
        "utilization_after": 0.75,
        "n1_contingency": "PASS",
        "blast_radius": 3
    },
    "warnings": [
        {
            "code": "BACK_TO_BACK_FMIT",
            "severity": "warning",
            "message": "Dr. Alice Johnson would have back-to-back weeks"
        }
    ]
}
```

### 3. Execution Details

```python
{
    "execution_timestamp": "2025-01-15T10:30:10Z",
    "executed_by_user_id": "uuid",
    "executed_by_name": "Dr. Jane Smith",  # or "System (auto-approved)"
    "database_transaction_id": "db-txn-12345",
    "assignments_modified": [
        {
            "assignment_id": "uuid-1",
            "block_id": "uuid-block-1",
            "date": "2025-02-03",
            "session": "AM",
            "rotation": "FMIT",
            "changed_from_person_id": "uuid-john",
            "changed_to_person_id": "uuid-alice"
        },
        # ... 13 more assignments (7 days × 2 sessions/day)
    ],
    "call_assignments_modified": [
        {
            "call_assignment_id": "uuid-call-1",
            "date": "2025-02-07",  # Friday
            "changed_from_person_id": "uuid-john",
            "changed_to_person_id": "uuid-alice"
        },
        {
            "call_assignment_id": "uuid-call-2",
            "date": "2025-02-08",  # Saturday
            "changed_from_person_id": "uuid-john",
            "changed_to_person_id": "uuid-alice"
        }
    ]
}
```

### 4. Approval Chain (if escalated)

```python
{
    "approval_required": true,
    "approval_reason": "Back-to-back FMIT weeks flagged",
    "routed_to_user_id": "uuid-coordinator",
    "routed_to_name": "CPT Coordinator",
    "routed_at": "2025-01-15T10:30:06Z",
    "approved_by_user_id": "uuid-coordinator",
    "approved_by_name": "CPT Coordinator",
    "approved_at": "2025-01-15T14:22:00Z",
    "approval_notes": "Approved - target faculty confirmed availability"
}
```

### 5. Rollback Information (if applicable)

```python
{
    "rolled_back_at": "2025-01-16T08:15:00Z",
    "rolled_back_by_user_id": "uuid",
    "rolled_back_by_name": "Dr. Jane Smith",
    "rollback_reason": "Resident reported schedule conflict",
    "rollback_eligible_until": "2025-01-16T10:30:10Z",  # executed_at + 24h
    "assignments_restored": 14,
    "call_assignments_restored": 2
}
```

---

## Storage Format and Location

### Primary Storage: `swap_records` Table

```sql
CREATE TABLE swap_records (
    id UUID PRIMARY KEY,
    source_faculty_id UUID NOT NULL REFERENCES people(id),
    source_week DATE NOT NULL,
    target_faculty_id UUID NOT NULL REFERENCES people(id),
    target_week DATE,  -- NULL for ABSORB swaps
    swap_type VARCHAR(20) NOT NULL,  -- 'one_to_one' or 'absorb'
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- Status enum

    -- Request tracking
    requested_at TIMESTAMP NOT NULL DEFAULT NOW(),
    requested_by_id UUID REFERENCES users(id),
    reason TEXT,

    -- Approval tracking
    approved_at TIMESTAMP,
    approved_by_id UUID REFERENCES users(id),

    -- Execution tracking
    executed_at TIMESTAMP,
    executed_by_id UUID REFERENCES users(id),

    -- Rollback tracking
    rolled_back_at TIMESTAMP,
    rolled_back_by_id UUID REFERENCES users(id),
    rollback_reason TEXT,

    -- Additional metadata
    notes TEXT,

    -- Versioning (SQLAlchemy-Continuum)
    transaction_id BIGINT
);

-- Indexes for common queries
CREATE INDEX idx_swap_records_status ON swap_records(status);
CREATE INDEX idx_swap_records_source_week ON swap_records(source_week);
CREATE INDEX idx_swap_records_requested_at ON swap_records(requested_at);
CREATE INDEX idx_swap_records_source_faculty ON swap_records(source_faculty_id);
CREATE INDEX idx_swap_records_target_faculty ON swap_records(target_faculty_id);
```

### Secondary Storage: Application Logs

**Structured JSON logs** for machine parsing:

```python
import logging
import json
from datetime import datetime

logger = logging.getLogger("swap_audit")

def log_swap_event(event_type: str, swap_id: UUID, details: dict) -> None:
    """
    Log swap event in structured format for parsing.

    Args:
        event_type: Event category (request|validation|execution|rollback)
        swap_id: Unique swap identifier
        details: Event-specific data
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "swap_id": str(swap_id),
        **details
    }

    logger.info(json.dumps(log_entry))

# Usage examples:

# 1. Request received
log_swap_event("request", swap_id, {
    "source_faculty": "Dr. John Doe",
    "target_faculty": "Dr. Alice Johnson",
    "source_week": "2025-02-03",
    "requested_by": "Dr. Jane Smith"
})

# 2. Validation complete
log_swap_event("validation", swap_id, {
    "decision": "PROCEED",
    "warnings": ["BACK_TO_BACK_FMIT", "IMMINENT_SWAP"],
    "tier1_pass": True,
    "tier2_pass": True,
    "tier3_pass": True
})

# 3. Execution complete
log_swap_event("execution", swap_id, {
    "executed_by": "System (auto-approved)",
    "assignments_modified": 14,
    "call_assignments_modified": 2,
    "transaction_id": "db-txn-12345"
})

# 4. Rollback executed
log_swap_event("rollback", swap_id, {
    "rolled_back_by": "Dr. Jane Smith",
    "reason": "Schedule conflict",
    "hours_since_execution": 18.5
})
```

**Log file location:** `/var/log/residency_scheduler/swap_audit.log`

---

## Unique ID Generation

Every swap gets a **globally unique identifier**:

```python
from uuid import uuid4
from datetime import datetime

def generate_swap_id() -> UUID:
    """
    Generate UUID v4 for swap request.

    Returns:
        UUID: Globally unique identifier
    """
    return uuid4()

# Example usage:
swap_id = generate_swap_id()
# Result: UUID('550e8400-e29b-41d4-a716-446655440000')
```

**Why UUIDs?**
- Globally unique (no collisions)
- Indexable in PostgreSQL
- Can be generated client-side if needed
- URL-safe for API endpoints
- Non-sequential (no information leakage)

---

## Searchability Requirements

Audit logs must be searchable by:

### 1. Time Range

```sql
-- All swaps in January 2025
SELECT * FROM swap_records
WHERE requested_at >= '2025-01-01'
  AND requested_at < '2025-02-01'
ORDER BY requested_at DESC;
```

### 2. Person Involved (Source or Target)

```sql
-- All swaps involving Dr. John Doe
SELECT * FROM swap_records
WHERE source_faculty_id = 'uuid-john'
   OR target_faculty_id = 'uuid-john'
ORDER BY requested_at DESC;
```

### 3. Status

```sql
-- All pending swaps awaiting approval
SELECT * FROM swap_records
WHERE status = 'pending'
ORDER BY requested_at ASC;

-- All rolled-back swaps (for investigation)
SELECT * FROM swap_records
WHERE status = 'rolled_back'
ORDER BY rolled_back_at DESC;
```

### 4. Week Affected

```sql
-- All swaps affecting week of 2025-02-03
SELECT * FROM swap_records
WHERE source_week = '2025-02-03'
   OR target_week = '2025-02-03'
ORDER BY requested_at DESC;
```

### 5. Requestor

```sql
-- All swaps requested by Dr. Jane Smith
SELECT * FROM swap_records
WHERE requested_by_id = 'uuid-jane'
ORDER BY requested_at DESC;
```

### 6. Full-Text Search on Reason

```sql
-- Find swaps related to "conference"
SELECT * FROM swap_records
WHERE reason ILIKE '%conference%'
ORDER BY requested_at DESC;
```

### 7. Application Log Queries (via grep/jq)

```bash
# Find all swap executions in last 24 hours
grep '"event_type": "execution"' /var/log/residency_scheduler/swap_audit.log \
    | jq 'select(.timestamp > "2025-01-14T00:00:00Z")'

# Find all rejected swaps
grep '"decision": "REJECT"' /var/log/residency_scheduler/swap_audit.log \
    | jq '{swap_id, timestamp, reason}'

# Find swaps with specific warning
grep 'BACK_TO_BACK_FMIT' /var/log/residency_scheduler/swap_audit.log \
    | jq .swap_id
```

---

## Immutability Guarantees

Audit logs must be **append-only** to prevent tampering:

### Database Versioning (SQLAlchemy-Continuum)

```python
from sqlalchemy_continuum import make_versioned

# Enable versioning for SwapRecord model
make_versioned(user_cls=None)

class SwapRecord(Base):
    __tablename__ = 'swap_records'
    __versioned__ = {}  # Enable versioning

    # ... model definition ...

# Every UPDATE creates a new version in swap_records_version table
# Query history:
from sqlalchemy_continuum import version_class

SwapRecordVersion = version_class(SwapRecord)

# Get all versions of a swap
versions = db.query(SwapRecordVersion).filter(
    SwapRecordVersion.id == swap_id
).order_by(SwapRecordVersion.transaction_id).all()

for version in versions:
    print(f"Transaction {version.transaction_id}: {version.status}")
```

### Application Log Rotation (Immutable Archives)

```bash
# /etc/logrotate.d/swap_audit
/var/log/residency_scheduler/swap_audit.log {
    daily
    rotate 365
    compress
    delaycompress
    notifempty
    create 0640 scheduler scheduler
    sharedscripts
    postrotate
        # Archive to immutable storage (S3, etc.)
        aws s3 cp /var/log/residency_scheduler/swap_audit.log.1.gz \
            s3://residency-audit-logs/swap_audit/$(date +%Y-%m-%d).log.gz
    endscript
}
```

---

## Compliance Reporting

Generate reports from audit trail:

### Monthly Swap Summary

```sql
-- Swap statistics for January 2025
SELECT
    COUNT(*) AS total_swaps,
    COUNT(*) FILTER (WHERE status = 'executed') AS executed,
    COUNT(*) FILTER (WHERE status = 'rejected') AS rejected,
    COUNT(*) FILTER (WHERE status = 'rolled_back') AS rolled_back,
    AVG(EXTRACT(EPOCH FROM (executed_at - requested_at))) AS avg_approval_time_seconds
FROM swap_records
WHERE requested_at >= '2025-01-01'
  AND requested_at < '2025-02-01';
```

### Per-Faculty Swap Activity

```sql
-- Swap activity by faculty (source and target combined)
WITH swap_activity AS (
    SELECT source_faculty_id AS faculty_id FROM swap_records
    WHERE status = 'executed'
      AND requested_at >= '2025-01-01'
    UNION ALL
    SELECT target_faculty_id AS faculty_id FROM swap_records
    WHERE status = 'executed'
      AND requested_at >= '2025-01-01'
      AND target_week IS NOT NULL  -- Exclude absorbs (target doesn't give anything)
)
SELECT
    p.name,
    COUNT(*) AS swap_count
FROM swap_activity sa
JOIN people p ON p.id = sa.faculty_id
GROUP BY p.name
ORDER BY swap_count DESC;
```

### Rollback Rate

```sql
-- Rollback rate (quality metric)
SELECT
    COUNT(*) FILTER (WHERE status = 'rolled_back') AS rolled_back,
    COUNT(*) FILTER (WHERE status = 'executed') +
        COUNT(*) FILTER (WHERE status = 'rolled_back') AS total_executed,
    (COUNT(*) FILTER (WHERE status = 'rolled_back')::FLOAT /
        NULLIF(COUNT(*) FILTER (WHERE status IN ('executed', 'rolled_back')), 0)) * 100
        AS rollback_percentage
FROM swap_records
WHERE requested_at >= '2025-01-01'
  AND requested_at < '2025-02-01';
```

---

## Performance Considerations

### Index Optimization

```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_swap_records_status_requested_at
    ON swap_records(status, requested_at DESC);

CREATE INDEX idx_swap_records_faculty_week
    ON swap_records(source_faculty_id, source_week);

-- GIN index for full-text search on reason
CREATE INDEX idx_swap_records_reason_gin
    ON swap_records USING GIN(to_tsvector('english', reason));
```

### Log Volume Management

**Expected volume:**
- ~50 swaps/month
- ~4 log entries per swap (request, validation, execution, optional rollback)
- ~200 log entries/month
- ~2,400 entries/year

**Storage requirements:**
- Average log entry: ~2 KB
- Monthly: 400 KB
- Yearly: ~5 MB (negligible)

**Retention policy:**
- Database: Keep all records indefinitely (versioned)
- Application logs: Rotate daily, archive for 1 year, then compress to cold storage

---

## Next Phase

After audit trail is logged, proceed to:

- **[rollback-procedures.md](rollback-procedures.md)** - Monitor for 24h rollback window
- **Notification delivery** - Alert affected parties via email/Slack

---

## Quick Reference

### Key Functions

| Function | Purpose | Location |
|----------|---------|----------|
| `log_swap_event()` | Structured logging | `app/services/swap_audit.py` |
| `generate_swap_id()` | UUID generation | `app/services/swap_request_service.py` |
| `get_swap_history()` | Query audit trail | `app/services/swap_audit.py` |

### Log Event Types

```python
EVENT_TYPES = [
    "request",      # Swap request received
    "validation",   # Safety checks completed
    "approval",     # Manual approval granted
    "rejection",    # Request rejected
    "execution",    # Swap executed
    "rollback",     # Swap rolled back
    "notification"  # Party notified
]
```

### Status State Machine

```
PENDING → APPROVED → EXECUTED → ROLLED_BACK
   ↓
REJECTED
   ↓
CANCELLED
```
