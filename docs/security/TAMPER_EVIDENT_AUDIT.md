# Tamper-Evident Audit Trail

## Overview

The Residency Scheduler implements a cryptographic audit trail for schedule changes using hash chains, providing tamper-evident properties similar to Certificate Transparency (RFC 6962) and AWS QLDB.

This document describes the security model, threat mitigation, and operational procedures.

---

## Security Model

### Hash Chain Structure

```
┌────────────────────────────────────────────────────────────────────┐
│ Record N                                                            │
├────────────────────────────────────────────────────────────────────┤
│ id:           UUID                                                  │
│ chain_id:     "global"                                              │
│ sequence_num: N                                                     │
│ prev_hash:    SHA256(Record N-1)                                    │
│ record_hash:  SHA256(prev_hash || payload || actor || timestamp)    │
│ action:       "SCHEDULE_APPROVED"                                   │
│ payload:      { schedule details }                                  │
│ actor_id:     UUID of approving user                                │
│ actor_type:   "human" | "system" | "ai"                             │
│ created_at:   Immutable timestamp                                   │
│ reason:       Justification text                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Hash Computation

```python
record_hash = SHA256(
    prev_hash       # Links to previous record (GENESIS for first)
    || payload      # JSON-serialized schedule change
    || actor_id     # Who performed the action
    || actor_type   # human/system/ai
    || action       # Action type (e.g., SCHEDULE_APPROVED)
    || timestamp    # ISO-8601 timestamp
    || reason       # Optional justification
)
```

The `||` operator represents JSON serialization with `sort_keys=True` for deterministic ordering.

### Security Properties

| Property | Guarantee |
|----------|-----------|
| **Integrity** | Any modification to payload, actor, or timestamp changes the hash |
| **Chain Integrity** | Modifying any record breaks all subsequent prev_hash links |
| **Non-repudiation** | Actor identity is cryptographically bound to the record |
| **Temporal Ordering** | Sequence numbers and timestamps provide ordering |
| **Append-only** | Design enforces INSERT-only operations |

---

## Threat Model

### Threats Mitigated

| Threat | Mitigation |
|--------|------------|
| **Silent modification** | Hash chain breaks, verification detects |
| **Record deletion** | Sequence gap detected during verification |
| **Record insertion** | Breaks hash chain at insertion point |
| **Timestamp manipulation** | Timestamp is part of hash computation |
| **Actor impersonation** | Actor ID captured from authenticated session |
| **Replay attacks** | Unique sequence numbers prevent replay |

### Threats NOT Mitigated

| Threat | Limitation | Mitigation Strategy |
|--------|------------|---------------------|
| **Genesis tampering** | First record has no predecessor | External seal of genesis hash |
| **Database admin access** | Can modify DB directly | Daily seals stored externally |
| **Compromised signing key** | N/A (no signatures currently) | Add Ed25519 signatures (future) |
| **Coerced user** | User forced to approve | Multi-party approval (future) |

---

## Chain Verification

### Verification Algorithm

```python
def verify_chain(chain_id: str) -> VerificationResult:
    records = get_all_records_ordered_by_sequence(chain_id)

    if not records:
        return VerificationResult(valid=False, error="Chain not found")

    prev_hash = None
    expected_seq = 0

    for record in records:
        # Check sequence continuity
        if record.sequence_num != expected_seq:
            return VerificationResult(
                valid=False,
                first_invalid_seq=record.sequence_num,
                error=f"Sequence gap: expected {expected_seq}"
            )

        # Check prev_hash link (skip genesis)
        if expected_seq > 0 and record.prev_hash != prev_hash:
            return VerificationResult(
                valid=False,
                first_invalid_seq=record.sequence_num,
                error="Chain broken: prev_hash mismatch"
            )

        # Verify record hash
        computed_hash = compute_hash(
            prev_hash=record.prev_hash,
            payload=record.payload,
            actor_id=record.actor_id,
            actor_type=record.actor_type,
            action=record.action,
            timestamp=record.created_at,
            reason=record.reason,
        )

        if record.record_hash != computed_hash:
            return VerificationResult(
                valid=False,
                first_invalid_seq=record.sequence_num,
                error="Hash mismatch: record tampered"
            )

        prev_hash = record.record_hash
        expected_seq += 1

    return VerificationResult(valid=True, verified_count=len(records))
```

### Verification Schedule

| Frequency | Scope | Trigger |
|-----------|-------|---------|
| On-demand | Full chain | Admin request via API |
| Daily | Full chain | Automated job before seal |
| On read | Single record | Optional integrity check |

---

## Daily Sealing

### Purpose

Daily seals create cryptographic checkpoints using Merkle trees, enabling:
- External storage of proof (email, notary, blockchain)
- Efficient verification without full chain traversal
- Snapshot-style integrity proofs

### Merkle Root Computation

```python
def compute_merkle_root(hashes: list[str]) -> str:
    """Binary Merkle tree from day's record hashes."""
    if not hashes:
        return SHA256("")

    # Pad to power of 2
    while len(hashes) & (len(hashes) - 1):
        hashes.append(SHA256(""))

    # Build tree bottom-up
    while len(hashes) > 1:
        new_level = []
        for i in range(0, len(hashes), 2):
            combined = hashes[i] + hashes[i + 1]
            new_level.append(SHA256(combined))
        hashes = new_level

    return hashes[0]
```

### Seal Record Payload

```json
{
  "seal_date": "2026-01-13",
  "records_sealed": 15,
  "merkle_root": "b7c4...9e2a",
  "head_hash_at_seal": "a3f2...8c91",
  "first_seq_of_day": 28,
  "last_seq_of_day": 42
}
```

### External Storage Options

| Option | Pros | Cons |
|--------|------|------|
| **Email to admin** | Simple, timestamped | Email can be deleted |
| **Timestamping service** | RFC 3161 compliant | External dependency |
| **Public blockchain** | Immutable, public | Cost, latency |
| **Internal backup** | Controlled | Same attack surface |

**Recommendation**: Email daily Merkle roots to a distribution list (admin + legal).

---

## Operational Procedures

### Incident Response: Tampering Detected

```
┌─────────────────────────────────────────────────────────────────┐
│ TAMPERING DETECTED                                               │
├─────────────────────────────────────────────────────────────────┤
│ 1. ISOLATE: Disable write access to approval_record table        │
│ 2. PRESERVE: Snapshot current database state                     │
│ 3. NOTIFY: Alert security team and program leadership            │
│ 4. INVESTIGATE:                                                   │
│    - Identify first invalid record (verification result)         │
│    - Review database access logs                                  │
│    - Check for application bugs vs. malicious access             │
│ 5. RESTORE: If backup available, restore from last valid seal    │
│ 6. DOCUMENT: Create incident report with timeline                 │
│ 7. REMEDIATE: Address root cause (access controls, monitoring)   │
└─────────────────────────────────────────────────────────────────┘
```

### Regular Verification

```bash
# Add to daily cron/celery beat
0 1 * * * curl -X GET "http://localhost:8000/api/approval-chain/verify" \
  -H "Authorization: Bearer $SERVICE_TOKEN" \
  | jq '.valid' | grep -q "true" || alert_security_team
```

### Backup Considerations

1. **Include in regular DB backups** - approval_record table is critical
2. **Store daily seals externally** - independent of DB backup
3. **Test restoration** - verify chain after restore

---

## ACGME Compliance Integration

### Override Tracking

All ACGME overrides are recorded with dedicated action types:

```python
# When approving an ACGME override
service.append_record(
    action=ApprovalAction.ACGME_OVERRIDE_APPROVED,
    payload={
        "assignment_id": str(assignment.id),
        "resident_id": str(resident.id),
        "rule_violated": "max_weekly_hours",
        "original_limit": 80,
        "actual_value": 84,
        "educational_justification": True,
    },
    reason="Resident requested to complete complex surgical case",
    actor_id=program_director.id,
)
```

### Compliance Audit Query

```sql
-- Find all ACGME overrides in date range
SELECT
    ar.created_at,
    ar.action,
    ar.payload->>'rule_violated' as rule,
    ar.reason,
    u.name as approved_by
FROM approval_record ar
LEFT JOIN users u ON ar.actor_id = u.id
WHERE ar.action LIKE 'ACGME_OVERRIDE%'
  AND ar.created_at BETWEEN '2026-01-01' AND '2026-06-30'
ORDER BY ar.created_at;
```

---

## Database Schema

```sql
CREATE TABLE approval_record (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chain_id VARCHAR(100) NOT NULL,
    sequence_num INTEGER NOT NULL,

    -- Hash chain links
    prev_record_id UUID REFERENCES approval_record(id),
    prev_hash VARCHAR(64),  -- SHA-256, null for genesis
    record_hash VARCHAR(64) NOT NULL,

    -- Action and payload
    action VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',

    -- Actor information
    actor_id UUID REFERENCES users(id) ON DELETE SET NULL,
    actor_type VARCHAR(20) NOT NULL DEFAULT 'human',

    -- Justification
    reason TEXT,

    -- Target entity
    target_entity_type VARCHAR(50),
    target_entity_id VARCHAR(100),

    -- Immutable timestamp (no updated_at!)
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Request metadata
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),

    CONSTRAINT uq_approval_record_chain_seq
        UNIQUE (chain_id, sequence_num)
);

-- Optimized indexes
CREATE INDEX ix_approval_record_chain_seq
    ON approval_record (chain_id, sequence_num);
CREATE INDEX ix_approval_record_acgme_overrides
    ON approval_record (created_at DESC)
    WHERE action LIKE 'ACGME_OVERRIDE%';
CREATE INDEX ix_approval_record_seals
    ON approval_record (chain_id, sequence_num DESC)
    WHERE action = 'DAY_SEALED';
```

---

## Future Enhancements

### 1. Ed25519 Digital Signatures

Add cryptographic signatures for stronger non-repudiation:

```python
# Each record would include
signature = Ed25519.sign(private_key, record_hash)
```

This requires key management infrastructure.

### 2. Multi-Party Approval

Require multiple signatures for high-risk actions:

```python
if action == "ACGME_OVERRIDE_APPROVED":
    require_signatures = ["program_director", "chief_resident"]
```

### 3. Hardware Security Module (HSM)

Store signing keys in HSM for tamper-resistant key protection.

### 4. Blockchain Anchoring

Periodically anchor Merkle roots to a public blockchain for maximum immutability.

---

## References

- [RFC 6962 - Certificate Transparency](https://tools.ietf.org/html/rfc6962)
- [AWS QLDB Documentation](https://docs.aws.amazon.com/qldb/)
- [Merkle Trees (Wikipedia)](https://en.wikipedia.org/wiki/Merkle_tree)
- [ACGME Work Hour Requirements](https://www.acgme.org/what-we-do/accreditation/common-program-requirements/)

---

## Related Documentation

- [Approval Chain API Reference](../api/APPROVAL_CHAIN_API.md)
- [Audit API Reference](../api/audit.md)
- [Data Security Policy](./DATA_SECURITY_POLICY.md)
