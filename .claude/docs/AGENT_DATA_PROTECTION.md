***REMOVED*** AGENT DATA PROTECTION

**Version:** 1.0
**Last Updated:** 2025-12-31
**Purpose:** Define data retention policies, sensitive data handling, and cleanup procedures

---

***REMOVED******REMOVED*** 1. DATA CLASSIFICATION

***REMOVED******REMOVED******REMOVED*** Classification Levels

***REMOVED******REMOVED******REMOVED******REMOVED*** PUBLIC

```
Examples:
  - Project README content
  - General documentation
  - API endpoint descriptions
  - Architecture diagrams
  - Code structure information

Retention: No limit
Access: All agents, public
Cleanup: Not required
```

***REMOVED******REMOVED******REMOVED******REMOVED*** INTERNAL

```
Examples:
  - Database schema details
  - API implementation details
  - Security architecture (non-cryptographic)
  - Performance metrics
  - Build system details

Retention: Session duration only
Access: Authorized agents only
Cleanup: Sanitize before output
```

***REMOVED******REMOVED******REMOVED******REMOVED*** CONFIDENTIAL (PERSEC/OPSEC)

```
Examples:
  - Resident/faculty names
  - Email addresses
  - TDY/deployment schedules
  - Leave/absence records
  - Medical information
  - Schedule assignments
  - Coverage patterns

Retention: NEVER - ephemeral only
Access: LOCAL ONLY - never in AI context
Cleanup: Immediate after use
Destroy: Cryptographic overwrites
```

***REMOVED******REMOVED******REMOVED******REMOVED*** RESTRICTED (SECRETS)

```
Examples:
  - JWT_SECRET_KEY
  - DATABASE_PASSWORD
  - API keys and credentials
  - Encryption keys
  - OAuth tokens

Retention: Never in code/logs
Access: Application only
Cleanup: Cryptographic erasure
Destroy: Key rotation/archival
```

---

***REMOVED******REMOVED*** 2. SENSITIVE DATA HANDLING

***REMOVED******REMOVED******REMOVED*** PII/PHI Protection

***REMOVED******REMOVED******REMOVED******REMOVED*** Never Accept from Users

Agents MUST REFUSE missions containing:

```
✗ Resident full names
✗ Faculty full names
✗ Email addresses (personal)
✗ Phone numbers
✗ Medical conditions
✗ Psychiatric conditions
✗ Assignment histories (real)
✗ Actual TDY dates/locations
```

**Validation:**

```python
def reject_if_sensitive_data(task_description: str) -> None:
    """
    Reject mission if sensitive data detected.

    This is FIRST validation before any processing.
    """
    patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "name_pattern": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",  ***REMOVED*** First Last
    }

    for data_type, pattern in patterns.items():
        if re.search(pattern, task_description):
            raise SecurityError(
                f"Rejected: {data_type} detected in mission context. "
                "Use synthetic identifiers only."
            )
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Synthetic Identifiers

**Always Use:**

```
Instead of:                   Use:
─────────────────────────────────────────────────────
"John Smith"                  "PGY1-01"
"alice@hospital.edu"          "FAC-ATTENDING-01"
"2025-01-15 (TDY Japan)"      "BLOCK-Q1-WK3"
"Cardiac rotation"            "ROT-CARDIAC-01"
"12-hour night shift"         "SHIFT-NIGHT-12H"
"Appendectomy procedure"      "PROC-APPENDIX"
```

**Database References:**

```python
***REMOVED*** WRONG - stores real data
person = {
    "name": "John Smith",
    "email": "john@hospital.edu",
    "resident_id": "John_Smith_2022"
}

***REMOVED*** CORRECT - synthetic identifiers
person = {
    "synthetic_id": "PGY1-01",
    "role": "resident",
    "year": 1
}
```

***REMOVED******REMOVED******REMOVED*** OPSEC/PERSEC for Military Data

***REMOVED******REMOVED******REMOVED******REMOVED*** Schedule Information

**Forbidden in Logs/Output:**

```
✗ Resident assignments by date
  Shows duty patterns → Reveals deployment capabilities

✗ Unit composition
  Shows staffing → Reveals force structure

✗ Absence patterns
  Shows movements → Reveals operations tempo

✗ TDY schedules
  Shows redeployment → Reveals operational planning
```

**Allowed (Generic):**

```
✓ "System manages 10 residents"
✓ "Schedule covers Q1-Q4"
✓ "Rotation types: inpatient, clinic, procedures"
✓ "Duty periods average 12 hours"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Deployment Data

**Never Log:**

```
✗ Specific deployment locations
✗ Deployment dates/durations
✗ Unit movements
✗ Training locations
✗ Exercise participation
✗ Real TDY data
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Coverage Patterns

**Reveal Information:**

```
If this:                    It reveals:
─────────────────────────────────────────
"2x duty officers on Jan 5" "Planning high-risk event"
"100% attendance required"  "Operation critical timing"
"Night float rotation"      "24/7 operational status"
"Limited leave approval"    "Surge period expected"
```

**Safe Abstraction:**

```
✓ "System ensures coverage compliance"
✓ "Scheduling algorithm optimizes availability"
✓ "Leave requests evaluated against ACGME rules"
```

---

***REMOVED******REMOVED*** 3. SCRATCHPAD DATA RETENTION

***REMOVED******REMOVED******REMOVED*** Scratchpad Purpose

```
Scratchpad = Temporary working space for agent execution
├── Read input files
├── Process data
├── Create intermediate results
├── Write final output
└── Schedule for cleanup
```

***REMOVED******REMOVED******REMOVED*** Data Retention Policies

***REMOVED******REMOVED******REMOVED******REMOVED*** During Execution

```
Timeline: [Agent Start] → [Agent Working] → [Agent Complete]
                          ↓
                    Scratchpad active
                    ├── Read cache: 15 min TTL
                    ├── Process results: Live
                    ├── Intermediate files: Temp storage
                    └── Session context: Memory (RAM)
```

**What's in Scratchpad During Execution:**

```
✓ File contents (from reads)
✓ Computation results
✓ Test execution output
✓ Lint/format findings
✓ Process logs

✗ NEVER: Secrets/credentials
✗ NEVER: PII/PHI data
✗ NEVER: OPSEC data
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Post-Execution Cleanup

**Immediate (Within 1 minute):**

```
1. Archive execution logs
   └─ .claude/archives/[timestamp]/execution-log.json

2. Archive scratchpad
   └─ .claude/archives/[timestamp]/scratchpad.md

3. Clear runtime memory
   └─ All variables cleared
   └─ Caches flushed
   └─ Connections closed

4. Verify cleanup
   └─ Confirm no sensitive data leaked
   └─ No temp files left
   └─ No cache entries remaining
```

**Timing Example:**

```
14:30:00 - Agent starts
14:30:05 - Read file: backend/app/services/swap.py (cached)
14:30:30 - Analyze and generate output
14:31:15 - Write final results to output.md
14:31:20 - ← CLEANUP BEGINS
14:31:22 - Archive scratchpad
14:31:23 - Clear caches
14:31:24 - Verify cleanup complete
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Archive Retention

**Archival Structure:**

```
.claude/archives/
└── 2025-12-31-14-30-45/
    ├── agent-context.json
    │   ├── agent_id
    │   ├── mission_type
    │   ├── timestamp_start
    │   └── timestamp_end
    │
    ├── execution-log.json
    │   ├── file_reads: []
    │   ├── file_writes: []
    │   ├── commands_executed: []
    │   └── errors: []
    │
    ├── scratchpad.md
    │   ├── Working notes
    │   ├── Analysis results
    │   └── Process logs
    │
    ├── output.md
    │   └── Final deliverable
    │
    └── cleanup-log.json
        ├── items_deleted: []
        ├── items_archived: []
        ├── verification: "passed"
        └── timestamp: "2025-12-31T14:31:24Z"
```

**Archival Retention Policy:**

```
Archive Age        Action
────────────────────────────────
< 7 days          Keep locally (debuggability)
7-30 days         Keep locally (reference)
30-90 days        Archive to cold storage
> 90 days         Evaluate for deletion

Confidential data always purged immediately
after archival to cold storage
```

---

***REMOVED******REMOVED*** 4. SENSITIVE DATA CLEANUP

***REMOVED******REMOVED******REMOVED*** Detection & Sanitization

***REMOVED******REMOVED******REMOVED******REMOVED*** Pre-Output Validation

Before agent outputs any file:

```python
def sanitize_output_file(filepath: str) -> None:
    """
    Scan output file for sensitive data.
    Reject if found, sanitize if possible.
    """
    with open(filepath, 'r') as f:
        content = f.read()

    ***REMOVED*** Scan for sensitive patterns
    threats = {
        "emails": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "names": r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    }

    violations = {}
    for threat_type, pattern in threats.items():
        matches = re.findall(pattern, content)
        if matches:
            violations[threat_type] = matches[:3]  ***REMOVED*** Show first 3

    if violations:
        raise SensitiveDataError(
            f"Output contains sensitive data: {violations}. "
            "Use synthetic identifiers only."
        )

    logger.info(f"Sanitization passed for {filepath}")
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Log Sanitization

**Automatic Log Filtering:**

```python
***REMOVED*** Before logging any message:
def sanitize_log_message(message: str) -> str:
    """Remove sensitive data from log messages."""

    ***REMOVED*** Replace email addresses
    message = re.sub(
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "[EMAIL]",
        message
    )

    ***REMOVED*** Replace phone numbers
    message = re.sub(
        r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "[PHONE]",
        message
    )

    ***REMOVED*** Replace full names
    message = re.sub(
        r"\b[A-Z][a-z]+ [A-Z][a-z]+\b",
        "[NAME]",
        message
    )

    ***REMOVED*** Replace SSN
    message = re.sub(
        r"\b\d{3}-\d{2}-\d{4}\b",
        "[SSN]",
        message
    )

    return message
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Access Patterns

**Safe Pattern (Synthetic IDs):**

```python
***REMOVED*** CORRECT - Uses synthetic ID, never logs PII
async def get_resident_schedule(db: AsyncSession, resident_id: str):
    """Get schedule for resident (using synthetic ID)."""
    ***REMOVED*** resident_id = "PGY1-01" (synthetic)

    result = await db.execute(
        select(Assignment)
        .where(Assignment.person_id == resident_id)
    )

    ***REMOVED*** Log only synthetic ID
    logger.info(f"Schedule retrieved for {resident_id}")

    return result.scalars().all()
```

**Unsafe Pattern (Names/PII):**

```python
***REMOVED*** WRONG - Never do this
def get_resident_schedule_unsafe(name: str):
    """⚠️ DON'T USE - Gets schedule by resident name."""
    ***REMOVED*** name = "John Smith" (PII!)

    ***REMOVED*** Searching by name
    result = db.query(Person).filter_by(name=name).first()

    ***REMOVED*** Logging PII
    logger.info(f"Schedule for {name}: {result.schedule}")

    return result
```

---

***REMOVED******REMOVED*** 5. CLEANUP PROCEDURES

***REMOVED******REMOVED******REMOVED*** Automated Cleanup

**Scheduled Cleanup Tasks:**

```
Every 1 minute:
  ├─ Check for completed agents
  ├─ Archive their scratchpads
  ├─ Clear runtime caches
  └─ Verify no sensitive data

Every 1 hour:
  ├─ Scan logs for sensitive patterns
  ├─ Sanitize if found
  ├─ Alert if major leak detected
  └─ Archive if clean

Every 24 hours:
  ├─ Archive old session data
  ├─ Verify retention policy
  ├─ Identify confidential data for purge
  └─ Schedule cold storage archive
```

***REMOVED******REMOVED******REMOVED*** Manual Cleanup

**User-Initiated Cleanup:**

```bash
***REMOVED*** Clean current session scratchpad
claude cleanup --scope session

***REMOVED*** Clean all scratchpad data
claude cleanup --scope all

***REMOVED*** Purge archives older than 30 days
claude cleanup --purge-archives --older-than 30d

***REMOVED*** Verify cleanup
claude cleanup --verify
```

***REMOVED******REMOVED******REMOVED*** Emergency Data Destruction

**If Sensitive Data Leaked:**

```
1. Immediate:
   └─ Isolate compromised files
   └─ Log incident with timestamp
   └─ Alert user

2. Within 1 hour:
   └─ Cryptographic overwrite of file
   └─ Remove from version control
   └─ Purge from backups/archives

3. Within 24 hours:
   └─ Audit how data leaked
   └─ Implement prevention
   └─ Document incident
   └─ Report to compliance
```

**Cryptographic Overwrite:**

```python
def secure_delete(filepath: str) -> None:
    """
    Securely delete file using cryptographic overwriting.
    Overwrites with random data 3 times to prevent recovery.
    """
    import os
    import secrets

    file_size = os.path.getsize(filepath)

    ***REMOVED*** 3-pass overwrite
    for pass_num in range(3):
        with open(filepath, 'wb') as f:
            f.write(secrets.token_bytes(file_size))
        os.fsync(filepath)

    ***REMOVED*** Remove file
    os.remove(filepath)

    logger.info(f"Securely deleted: {filepath}")
```

---

***REMOVED******REMOVED*** 6. COMPLIANCE & AUDIT

***REMOVED******REMOVED******REMOVED*** Data Protection Audit Trail

**Every Data Operation Logged:**

```json
{
  "timestamp": "2025-12-31T14:30:45Z",
  "operation": "FILE_READ",
  "agent_id": "code_reviewer_001",
  "filepath": "backend/app/services/swap.py",
  "contains_sensitive": false,
  "sanitized": false,
  "audit_id": "aud_12345"
}
```

***REMOVED******REMOVED******REMOVED*** Compliance Checklist

Before deployment:

- [ ] All PII sanitization functions tested
- [ ] Log sanitization enabled
- [ ] Output validation enforced
- [ ] Cleanup procedures automated
- [ ] Retention policies documented
- [ ] Archive process verified
- [ ] Secure delete tested
- [ ] Audit logging working
- [ ] No sensitive data in codebase
- [ ] No secrets in documentation

---

***REMOVED******REMOVED*** 7. DATA BREACH RESPONSE

***REMOVED******REMOVED******REMOVED*** Detection

```
Alert Triggers:
├─ PII pattern found in output
├─ Secret found in logs
├─ Unauthorized file access
├─ Data exfiltration attempt
└─ Compliance violation detected
```

***REMOVED******REMOVED******REMOVED*** Response Protocol

**Tier 1 (Minor):**
```
1. Log incident
2. Sanitize data
3. Alert user
4. Archive for audit
```

**Tier 2 (Significant):**
```
1. Isolate agent
2. Secure delete leaked data
3. Alert user immediately
4. Audit how it happened
5. Implement prevention
6. Compliance review
```

**Tier 3 (Critical):**
```
1. Emergency isolation
2. Cryptographic overwrite
3. Revoke credentials
4. Incident command activated
5. External notification (if required)
6. Legal review
7. Remediation plan
```

---

***REMOVED******REMOVED*** 8. VALIDATION CHECKLIST

**Data Protection Validation:**

- [ ] No PII in mission context
- [ ] No secrets in task description
- [ ] Synthetic IDs used throughout
- [ ] Output scanned before write
- [ ] Logs sanitized automatically
- [ ] Cleanup scheduled
- [ ] Sensitive data purged
- [ ] Archive retention compliant
- [ ] Audit trail maintained
- [ ] Compliance verified

---

***REMOVED******REMOVED*** References

- [Access Control Model](AGENT_ACCESS_CONTROL.md)
- [Isolation Model](AGENT_ISOLATION_MODEL.md)
- [Input Validation](AGENT_INPUT_VALIDATION.md)
- [Security Audit Framework](AGENT_SECURITY_AUDIT.md)
- Project Security Policy: `docs/security/DATA_SECURITY_POLICY.md`
