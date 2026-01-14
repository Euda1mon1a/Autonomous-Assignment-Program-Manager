# Approval Chain API Reference

**Endpoint Prefix:** `/api/approval-chain`

## Overview

The Approval Chain API provides a tamper-evident audit trail for schedule changes using cryptographic hash chains. Each approval record links to its predecessor via SHA-256, making any tampering instantly detectable.

### Key Features

- **Hash Chain Integrity**: Each record includes hash of previous record
- **Chain Verification**: Endpoint to verify entire chain integrity
- **Daily Sealing**: Merkle root checkpoints for external verification
- **ACGME Override Tracking**: Dedicated action types for compliance
- **Non-repudiation**: Actor identity, timestamp, and IP captured in hash

### Security Properties

| Property | Implementation |
|----------|----------------|
| **Append-only** | Records should never be modified or deleted |
| **Tamper-evident** | Any modification breaks the hash chain |
| **Non-repudiation** | Actor identity and timestamp are hashed |
| **Verifiable** | Chain can be verified from genesis to head |

### How It Works

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Genesis    │───▶│  Record 1   │───▶│  Record 2   │
│  (seq: 0)   │    │  (seq: 1)   │    │  (seq: 2)   │
│             │    │             │    │             │
│ hash: abc.. │    │ prev: abc.. │    │ prev: def.. │
│             │    │ hash: def.. │    │ hash: ghi.. │
└─────────────┘    └─────────────┘    └─────────────┘
```

Each record's hash is computed as:
```
SHA256(prev_hash || payload || actor_id || actor_type || action || timestamp || reason)
```

If anyone edits Record 1, its hash changes from `def..` to something else, breaking the link in Record 2.

---

## Endpoints

### GET /verify

Verify the cryptographic integrity of an approval chain.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/approval-chain/verify?chainId=global" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chainId` | string | `global` | Chain identifier to verify |

**Response (200 - Valid Chain):**
```json
{
  "valid": true,
  "chainId": "global",
  "totalRecords": 42,
  "verifiedCount": 42,
  "headHash": "a3f2...8c91",
  "genesisHash": "7b4e...2d3f",
  "verifiedAt": "2026-01-13T14:30:00Z"
}
```

**Response (200 - Tampered Chain):**
```json
{
  "valid": false,
  "chainId": "global",
  "totalRecords": 42,
  "verifiedCount": 15,
  "firstInvalidSeq": 16,
  "firstInvalidId": "550e8400-e29b-41d4-a716-446655440016",
  "errorMessage": "Hash mismatch at seq 16: record has been tampered with",
  "verifiedAt": "2026-01-13T14:30:00Z"
}
```

---

### POST /verify

Verify chain with additional options (POST version).

**Request:**
```bash
curl -X POST http://localhost:8000/api/approval-chain/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "chainId": "global",
    "stopOnFirstError": true
  }'
```

**Request Body:**
```json
{
  "chainId": "string (default: global)",
  "stopOnFirstError": "boolean (default: true)"
}
```

---

### GET /stats

Get statistics about an approval chain.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/approval-chain/stats?chainId=global" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Response (200):**
```json
{
  "chainId": "global",
  "totalRecords": 42,
  "headSequence": 41,
  "headHash": "a3f2...8c91",
  "genesisHash": "7b4e...2d3f",
  "firstRecordAt": "2026-01-01T00:00:00Z",
  "lastRecordAt": "2026-01-13T14:25:00Z",
  "actionsByType": {
    "GENESIS": 1,
    "SCHEDULE_APPROVED": 15,
    "ASSIGNMENT_CREATED": 20,
    "ACGME_OVERRIDE_APPROVED": 3,
    "DAY_SEALED": 3
  }
}
```

**Error Response (404):**
```json
{
  "detail": "Chain 'nonexistent' not found"
}
```

---

### POST /records

Append a new approval record to the chain. **Requires Coordinator role or above.**

**Request:**
```bash
curl -X POST http://localhost:8000/api/approval-chain/records \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "action": "SCHEDULE_APPROVED",
    "payload": {
      "scheduleRunId": "550e8400-e29b-41d4-a716-446655440001",
      "blockNumber": 10,
      "totalAssignments": 156
    },
    "reason": "Block 10 schedule approved after faculty review",
    "targetEntityType": "ScheduleRun",
    "targetEntityId": "550e8400-e29b-41d4-a716-446655440001"
  }'
```

**Request Body:**
```json
{
  "action": "string (required, see Action Types below)",
  "payload": "object (required, schedule change details)",
  "chainId": "string (default: global)",
  "actorType": "human | system | ai (default: human)",
  "reason": "string (optional, justification)",
  "targetEntityType": "string (optional, e.g., 'ScheduleRun', 'Assignment')",
  "targetEntityId": "string (optional, entity UUID)"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440042",
  "chainId": "global",
  "sequenceNum": 42,
  "prevHash": "def1...2345",
  "recordHash": "a3f2...8c91",
  "action": "SCHEDULE_APPROVED",
  "payload": {
    "scheduleRunId": "550e8400-e29b-41d4-a716-446655440001",
    "blockNumber": 10,
    "totalAssignments": 156
  },
  "reason": "Block 10 schedule approved after faculty review",
  "targetEntityType": "ScheduleRun",
  "targetEntityId": "550e8400-e29b-41d4-a716-446655440001",
  "actorId": "550e8400-e29b-41d4-a716-446655440099",
  "actorType": "human",
  "createdAt": "2026-01-13T14:30:00Z",
  "ipAddress": "10.0.1.45"
}
```

---

### GET /records

Query approval records with optional filters.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/approval-chain/records?chainId=global&action=ACGME_OVERRIDE_APPROVED&limit=10" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `chainId` | string | `global` | Chain to query |
| `action` | string | - | Filter by action type |
| `targetEntityType` | string | - | Filter by entity type |
| `targetEntityId` | string | - | Filter by entity ID |
| `limit` | int | 100 | Max records (1-1000) |
| `offset` | int | 0 | Records to skip |

**Response (200):**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440042",
      "chainId": "global",
      "sequenceNum": 42,
      "prevHash": "def1...2345",
      "recordHash": "a3f2...8c91",
      "action": "ACGME_OVERRIDE_APPROVED",
      "payload": { ... },
      "reason": "Educational opportunity - resident requested continuation",
      "actorId": "...",
      "actorType": "human",
      "createdAt": "2026-01-13T14:30:00Z"
    }
  ],
  "total": 3,
  "limit": 10,
  "offset": 0,
  "chainId": "global"
}
```

---

### GET /records/{record_id}

Get a specific approval record by ID.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/approval-chain/records/550e8400-e29b-41d4-a716-446655440042" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440042",
  "chainId": "global",
  "sequenceNum": 42,
  "prevHash": "def1...2345",
  "recordHash": "a3f2...8c91",
  "action": "SCHEDULE_APPROVED",
  "payload": { ... },
  ...
}
```

---

### POST /seal

Create a daily seal with Merkle root for external verification. **Requires Admin role.**

Daily seals create cryptographic checkpoints that can be stored externally (email, notary service, etc.) for stronger, snapshot-style proofs.

**Request:**
```bash
curl -X POST http://localhost:8000/api/approval-chain/seal \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "chainId": "global",
    "sealDate": "2026-01-13T00:00:00Z"
  }'
```

**Request Body:**
```json
{
  "chainId": "string (default: global)",
  "sealDate": "datetime (default: today)"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440043",
  "chainId": "global",
  "sequenceNum": 43,
  "sealDate": "2026-01-13",
  "recordsSealed": 15,
  "merkleRoot": "b7c4...9e2a",
  "recordHash": "f1d2...3c4b"
}
```

The `merkleRoot` can be stored externally. To verify, recompute the Merkle root from the day's records and compare.

---

### GET /actions

List all valid approval action types.

**Request:**
```bash
curl -X GET "http://localhost:8000/api/approval-chain/actions"
```

**Response (200):**
```json
[
  "SCHEDULE_GENERATED",
  "SCHEDULE_APPROVED",
  "SCHEDULE_PUBLISHED",
  "SCHEDULE_REJECTED",
  "ASSIGNMENT_CREATED",
  "ASSIGNMENT_MODIFIED",
  "ASSIGNMENT_DELETED",
  "ACGME_OVERRIDE_REQUESTED",
  "ACGME_OVERRIDE_APPROVED",
  "ACGME_OVERRIDE_DENIED",
  "SWAP_REQUESTED",
  "SWAP_APPROVED",
  "SWAP_EXECUTED",
  "SWAP_ROLLED_BACK",
  "GENESIS",
  "DAY_SEALED"
]
```

---

## Action Types Reference

### Schedule Actions

| Action | Description | Typical Actor |
|--------|-------------|---------------|
| `SCHEDULE_GENERATED` | AI/solver generated a schedule | system |
| `SCHEDULE_APPROVED` | Human approved generated schedule | human |
| `SCHEDULE_PUBLISHED` | Schedule made visible to residents | human |
| `SCHEDULE_REJECTED` | Schedule rejected, needs regeneration | human |

### Assignment Actions

| Action | Description | Typical Actor |
|--------|-------------|---------------|
| `ASSIGNMENT_CREATED` | New assignment added | human/system |
| `ASSIGNMENT_MODIFIED` | Assignment changed | human |
| `ASSIGNMENT_DELETED` | Assignment removed | human |

### ACGME Override Actions

| Action | Description | Typical Actor |
|--------|-------------|---------------|
| `ACGME_OVERRIDE_REQUESTED` | Request to exceed ACGME limits | human |
| `ACGME_OVERRIDE_APPROVED` | Override approved with justification | human |
| `ACGME_OVERRIDE_DENIED` | Override request denied | human |

### Swap Actions

| Action | Description | Typical Actor |
|--------|-------------|---------------|
| `SWAP_REQUESTED` | Faculty requested a swap | human |
| `SWAP_APPROVED` | Swap approved by coordinator | human |
| `SWAP_EXECUTED` | Swap completed in system | system |
| `SWAP_ROLLED_BACK` | Swap reverted | human |

### System Actions

| Action | Description | Typical Actor |
|--------|-------------|---------------|
| `GENESIS` | First record in a chain | system |
| `DAY_SEALED` | Daily Merkle root seal | system |

---

## Usage Examples

### Record a Schedule Approval

```python
from app.services.approval_chain_service import ApprovalChainService
from app.models.approval_record import ApprovalAction

service = ApprovalChainService(db)
record = service.append_record(
    action=ApprovalAction.SCHEDULE_APPROVED,
    payload={
        "schedule_run_id": str(schedule_run.id),
        "block_number": 10,
        "total_assignments": 156,
        "acgme_violations": 0,
    },
    actor_id=current_user.id,
    reason="Block 10 schedule reviewed and approved by program director",
    target_entity_type="ScheduleRun",
    target_entity_id=str(schedule_run.id),
)
db.commit()
```

### Record an ACGME Override

```python
record = service.append_record(
    action=ApprovalAction.ACGME_OVERRIDE_APPROVED,
    payload={
        "assignment_id": str(assignment.id),
        "rule_violated": "max_consecutive_days",
        "original_limit": 6,
        "approved_value": 8,
    },
    actor_id=current_user.id,
    reason="Educational opportunity - resident requested to continue for critical surgical case",
    target_entity_type="Assignment",
    target_entity_id=str(assignment.id),
)
```

### Verify Chain Integrity

```python
from app.services.approval_chain_service import verify_chain

result = verify_chain(db, chain_id="global")
if not result.valid:
    logger.critical(
        f"TAMPERING DETECTED at sequence {result.first_invalid_seq}: "
        f"{result.error_message}"
    )
    # Alert security team
```

### Automated Daily Sealing (Celery Task)

```python
@celery_app.task
def seal_approval_chains():
    """Run nightly to create verifiable checkpoints."""
    with get_db_session() as db:
        service = ApprovalChainService(db)
        seal = service.seal_day(chain_id="global")
        db.commit()

        # Store merkle root externally
        notify_admin(
            subject=f"Daily Approval Seal - {seal.payload['seal_date']}",
            body=f"Merkle Root: {seal.payload['merkle_root']}\n"
                 f"Records Sealed: {seal.payload['records_sealed']}"
        )
```

---

## Error Handling

| Status | Error | Description |
|--------|-------|-------------|
| 400 | Invalid action type | Action not in allowed list |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient role (need Coordinator+) |
| 404 | Chain not found | Specified chain_id doesn't exist |
| 409 | Sequence conflict | Concurrent append (auto-retried) |

---

## Related Documentation

- [Tamper-Evident Audit Security Model](../security/TAMPER_EVIDENT_AUDIT.md)
- [Audit API Reference](./audit.md)
- [ACGME Compliance](../constraints/CONSTRAINT_CATALOG.md)
