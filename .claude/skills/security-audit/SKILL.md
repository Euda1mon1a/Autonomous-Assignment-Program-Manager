---
name: security-audit
description: Security-focused code audit for healthcare and military contexts. Use when reviewing authentication, authorization, data handling, HIPAA compliance, or OPSEC/PERSEC requirements. Essential for PHI handling and military medical residency schedules.
model_tier: opus
parallel_hints:
  can_parallel_with:
    - code-review
    - test-writer
    - lint-monorepo
  must_serialize_with: []
  preferred_batch_size: 3
---

# Security Audit Skill

Specialized security auditing for healthcare IT systems handling military medical residency data, with focus on HIPAA compliance and OPSEC/PERSEC requirements.

## When This Skill Activates

- Authentication or authorization code changes
- Code handling PHI (Protected Health Information)
- Military schedule or personnel data handling
- API endpoint security review
- File upload/download functionality
- Cryptographic operations
- Third-party integration reviews
- Pre-deployment security checks

## Security Domains

### 1. HIPAA Compliance

| Requirement | Implementation |
|-------------|----------------|
| Access Control | RBAC with 8 roles (Admin, Coordinator, Faculty, etc.) |
| Audit Logging | All data access logged with user, timestamp, action |
| Encryption at Rest | Database column encryption for PHI |
| Encryption in Transit | TLS 1.3 for all connections |
| Minimum Necessary | Query only required fields |

### 2. OPSEC/PERSEC (Military Data)

**NEVER commit or log:**

| Data Type | Risk | Handling |
|-----------|------|----------|
| Resident/Faculty Names | PERSEC | Sanitize for demos |
| Schedule Assignments | OPSEC | Reveals duty patterns |
| TDY/Deployment Data | OPSEC | Never in repo |
| Absence Records | OPSEC/PERSEC | Local only |

**Safe Identifiers for Demo/Test:**
```python
# Use synthetic identifiers
residents = ["PGY1-01", "PGY2-01"]  # Not real names
faculty = ["FAC-PD", "FAC-APD"]      # Role-based IDs
```

### 3. OWASP Top 10 Checklist

| Risk | Check | Status |
|------|-------|--------|
| A01:2021 Broken Access Control | RBAC + resource ownership | [ ] |
| A02:2021 Cryptographic Failures | TLS + proper key management | [ ] |
| A03:2021 Injection | SQLAlchemy ORM, no raw SQL | [ ] |
| A04:2021 Insecure Design | Layered architecture | [ ] |
| A05:2021 Security Misconfiguration | Secret validation on startup | [ ] |
| A06:2021 Vulnerable Components | Dependency scanning | [ ] |
| A07:2021 Auth Failures | Rate limiting, JWT httpOnly | [ ] |
| A08:2021 Data Integrity Failures | Signed updates, migrations | [ ] |
| A09:2021 Logging Failures | Audit trail, no sensitive data | [ ] |
| A10:2021 SSRF | URL validation, allowlists | [ ] |

## Security Audit Process

### Step 1: Threat Model Assessment

```
Data Flow:
Client → API Gateway → FastAPI → Service → Database
                ↓
          Rate Limiter
                ↓
          Auth Middleware (JWT in httpOnly cookie)
                ↓
          RBAC Check
                ↓
          Business Logic
```

### Step 2: Authentication Review

```python
# Verify proper auth checks
from app.api.deps import get_current_user, require_roles

@router.get("/schedules")
async def get_schedules(
    current_user: User = Depends(get_current_user),  # Auth required
    db: AsyncSession = Depends(get_db)
):
    # Business logic
    pass

# Role-based access
@router.post("/admin/users")
async def create_user(
    current_user: User = Depends(require_roles(["admin"]))  # Admin only
):
    pass
```

### Step 3: Input Validation

```python
# CHECK: All inputs use Pydantic schemas
from app.schemas.assignment import AssignmentCreate

@router.post("/assignments", response_model=AssignmentResponse)
async def create_assignment(
    assignment: AssignmentCreate,  # Validated by Pydantic
    db: AsyncSession = Depends(get_db)
):
    pass

# VERIFY: No raw SQL
# BAD
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# GOOD
result = await db.execute(
    select(User).where(User.id == user_id)
)
```

### Step 4: Secret Management

```bash
# Check for hardcoded secrets
cd /home/user/Autonomous-Assignment-Program-Manager

# Scan for patterns
grep -rn "password\s*=" --include="*.py" backend/
grep -rn "secret\s*=" --include="*.py" backend/
grep -rn "api_key\s*=" --include="*.py" backend/
grep -rn "Bearer " --include="*.py" backend/

# Verify .env is gitignored
cat .gitignore | grep -E "\.env"

# Check secret validation
cat backend/app/core/config.py | grep -A5 "SECRET_KEY"
```

### Step 5: File Security

```python
# Verify file path validation
from app.core.file_security import validate_path

# All file operations must use:
safe_path = validate_path(base_directory, user_filename)
```

### Step 6: Rate Limiting

```python
# Verify rate limiting on sensitive endpoints
from app.core.rate_limit import rate_limiter

@router.post("/auth/login")
@rate_limiter.limit("5/minute")  # Brute force protection
async def login():
    pass
```

## Vulnerability Patterns

### SQL Injection

```python
# VULNERABLE
query = f"SELECT * FROM persons WHERE name = '{user_input}'"

# SECURE
query = select(Person).where(Person.name == user_input)
```

### Path Traversal

```python
# VULNERABLE
file_path = f"/uploads/{filename}"

# SECURE
from app.core.file_security import validate_path
file_path = validate_path("/uploads", filename)
```

### XSS via API

```python
# VULNERABLE - returning raw user input
return {"message": f"Hello {user.name}"}

# SECURE - Pydantic escaping
from pydantic import BaseModel
class Response(BaseModel):
    message: str  # Auto-escaped in JSON serialization
```

### Insecure Direct Object Reference

```python
# VULNERABLE - No ownership check
@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    return await get_schedule_by_id(schedule_id)

# SECURE - Ownership verification
@router.get("/schedules/{schedule_id}")
async def get_schedule(
    schedule_id: str,
    current_user: User = Depends(get_current_user)
):
    schedule = await get_schedule_by_id(schedule_id)
    if not can_access(current_user, schedule):
        raise HTTPException(403, "Access denied")
    return schedule
```

### Sensitive Data Exposure

```python
# VULNERABLE - Full object returned
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    return await db.get(User, user_id)  # Includes password hash!

# SECURE - Schema controls response
@router.get("/users/{user_id}", response_model=UserPublic)
async def get_user(user_id: str):
    return await db.get(User, user_id)  # UserPublic excludes sensitive fields
```

## Security Scanning Commands

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Static security analysis
bandit -r app/ -ll -f json > bandit_report.json

# Dependency vulnerability check
pip-audit --format=json > pip_audit_report.json

# Check for secrets in code
pip install detect-secrets
detect-secrets scan app/ > .secrets.baseline

# SAST with ruff security rules
ruff check app/ --select S
```

## Audit Report Template

```markdown
## Security Audit Report

**Date:** YYYY-MM-DD
**Scope:** [Files/Features audited]
**Auditor:** [AI/Human]
**Risk Level:** [LOW/MEDIUM/HIGH/CRITICAL]

### Executive Summary
[One paragraph overview]

### Critical Findings
| ID | Finding | CVSS | Remediation |
|----|---------|------|-------------|
| C1 | [Description] | [Score] | [Fix] |

### High Findings
| ID | Finding | CVSS | Remediation |
|----|---------|------|-------------|
| H1 | [Description] | [Score] | [Fix] |

### Medium Findings
...

### Low Findings
...

### Compliance Status
- [ ] HIPAA: [Status]
- [ ] OPSEC/PERSEC: [Status]
- [ ] OWASP Top 10: [Status]

### Recommendations
1. [Priority recommendation]
2. [Secondary recommendation]

### Files Requiring Attention
- `path/to/file.py:line` - [Issue]
```

## Escalation Rules

**ALWAYS escalate to human when:**

1. Critical vulnerability discovered (CVSS >= 9.0)
2. PHI exposure risk detected
3. Authentication bypass possible
4. Cryptographic weakness found
5. OPSEC/PERSEC violation
6. Third-party credential exposure
7. Active exploitation suspected

**Can remediate automatically:**

1. Missing input validation (add Pydantic schema)
2. Hardcoded non-secret values
3. Missing type hints on security functions
4. Outdated dependencies (if minor version)
5. Missing rate limiting on non-auth endpoints

## Examples

### Example 1: OPSEC/PERSEC Data Leak Detection

**Context:** Reviewing PR that adds schedule export feature

**Input:**
```python
# backend/app/api/routes/export.py
@router.get("/export/schedule")
async def export_schedule(db: AsyncSession = Depends(get_db)):
    """Export full schedule to JSON."""
    assignments = await db.execute(select(Assignment))

    return {
        "schedule": [
            {
                "resident_name": a.person.name,  # PERSEC VIOLATION
                "rotation": a.rotation.name,
                "date": a.date,
                "deployment_status": a.person.deployment_status  # OPSEC VIOLATION
            }
            for a in assignments.scalars()
        ]
    }
```

**Process:**
1. Scan for PERSEC data: `resident_name` exposes real names
2. Scan for OPSEC data: `deployment_status` reveals military movements
3. Check gitignore patterns: Export endpoint could log to files
4. Assess severity: HIGH - violates military data security policy

**Output:**
```markdown
## Security Audit Finding

**Severity:** :red_circle: CRITICAL
**Category:** OPSEC/PERSEC Violation
**File:** `backend/app/api/routes/export.py:12`

**Issue:** Sensitive Military Data Exposure

This endpoint exposes PERSEC (personally identifiable) and OPSEC (operational security)
data that must never leave the local system.

**Violations Detected:**
1. **PERSEC:** Real resident names in export (`resident_name`)
2. **OPSEC:** Deployment status reveals military movements
3. **Data Leak Risk:** Export could be committed to repo or logged

**Security Impact:**
- Compromises resident privacy (PERSEC)
- Reveals duty patterns and movements (OPSEC)
- Could violate HIPAA if PHI included
- Non-compliance with military data handling requirements

**Required Fix:**
```python
@router.get("/export/schedule", response_model=ScheduleExportResponse)
async def export_schedule(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"]))  # Auth required
):
    """Export sanitized schedule (admin only)."""
    assignments = await db.execute(select(Assignment))

    return {
        "schedule": [
            {
                "resident_id": a.person.id,  # Use ID, not name
                "rotation": a.rotation.name,
                "date": a.date,
                # DO NOT include deployment_status
            }
            for a in assignments.scalars()
        ]
    }
```

**Additional Recommendations:**
1. Add audit log: Track who exported schedule and when
2. Rate limit: Prevent bulk data exfiltration
3. Document: Add warning comment about OPSEC/PERSEC
4. Review: Any export feature requires security team approval

**Action Required:** BLOCK MERGE until fixed
```

### Example 2: SQL Injection Vulnerability

**Context:** Security scan finds raw SQL in search endpoint

**Input:**
```python
# backend/app/api/routes/search.py
@router.get("/search/residents")
async def search_residents(name: str, db: AsyncSession = Depends(get_db)):
    """Search residents by name."""
    # VULNERABLE: Using raw SQL with user input
    query = f"SELECT * FROM persons WHERE name LIKE '%{name}%'"
    result = await db.execute(text(query))
    return result.fetchall()
```

**Process:**
1. Detect raw SQL: `text(query)` with f-string interpolation
2. Identify user input: `name` parameter not sanitized
3. Test exploit: `name = "'; DROP TABLE persons; --"`
4. Assess severity: CRITICAL - SQL injection vulnerability

**Output:**
```markdown
## Security Audit Finding

**Severity:** :red_circle: CRITICAL
**Category:** SQL Injection (OWASP A03:2021)
**File:** `backend/app/api/routes/search.py:8`

**Issue:** SQL Injection Vulnerability

User input is directly interpolated into SQL query without sanitization,
allowing arbitrary SQL execution.

**Vulnerability:**
```python
query = f"SELECT * FROM persons WHERE name LIKE '%{name}%'"
```

**Exploit Example:**
```
GET /search/residents?name='; DROP TABLE persons; --
```
This would execute:
```sql
SELECT * FROM persons WHERE name LIKE '%'; DROP TABLE persons; --%'
```

**Security Impact:**
- **Data Breach:** Attacker can read entire database
- **Data Loss:** Attacker can delete or modify data
- **Privilege Escalation:** Attacker can create admin accounts
- **Compliance Violation:** Fails HIPAA security requirements

**Required Fix - Use SQLAlchemy ORM:**
```python
from sqlalchemy import select
from app.models.person import Person

@router.get("/search/residents", response_model=list[PersonPublic])
async def search_residents(
    name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Add auth
):
    """Search residents by name."""
    result = await db.execute(
        select(Person)
        .where(Person.name.ilike(f"%{name}%"))  # Safe - parameterized
        .where(Person.role == "RESIDENT")
    )
    return result.scalars().all()
```

**Why This is Safe:**
- SQLAlchemy uses parameterized queries
- User input is escaped automatically
- SQL and data are separated

**Testing:**
```python
# Add test to verify exploit is blocked
def test_sql_injection_blocked():
    response = client.get("/search/residents?name='; DROP TABLE persons; --")
    # Should return empty list, not execute DROP
    assert response.status_code == 200
    assert len(response.json()) == 0
```

**Action Required:** BLOCK MERGE - Fix immediately before deployment
```

### Example 3: Missing Authentication Check

**Context:** Routine security audit of API endpoints

**Input:**
```python
# backend/app/api/routes/schedules.py
@router.get("/schedules/all")
async def get_all_schedules(db: AsyncSession = Depends(get_db)):
    """Get all schedules."""
    schedules = await db.execute(select(Schedule))
    return schedules.scalars().all()
```

**Process:**
1. Check for authentication: Missing `Depends(get_current_user)`
2. Check for authorization: No role check
3. Assess data sensitivity: Schedules contain PII and scheduling patterns
4. Scan codebase for pattern: Find 3 other endpoints with same issue

**Output:**
```markdown
## Security Audit Finding

**Severity:** :yellow_circle: HIGH
**Category:** Broken Access Control (OWASP A01:2021)
**File:** `backend/app/api/routes/schedules.py:15`

**Issue:** Missing Authentication on Sensitive Endpoint

This endpoint exposes all schedules without requiring authentication.

**Security Impact:**
- Unauthenticated access to resident schedules
- Potential PHI exposure if schedules include medical assignments
- OPSEC risk if schedules reveal military duty patterns
- No audit trail of who accessed data

**Current Code:**
```python
@router.get("/schedules/all")
async def get_all_schedules(db: AsyncSession = Depends(get_db)):
```

**Required Fix:**
```python
from app.api.deps import get_current_user
from app.models.user import User

@router.get("/schedules/all", response_model=list[SchedulePublic])
async def get_all_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Require auth
):
    """Get all schedules (authenticated users only)."""
    # Filter based on user role
    if current_user.role not in ["admin", "coordinator"]:
        raise HTTPException(403, "Insufficient permissions")

    schedules = await db.execute(select(Schedule))
    return schedules.scalars().all()
```

**Pattern Found in Other Endpoints:**
- `GET /residents/all` - Missing auth
- `GET /faculty/all` - Missing auth
- `GET /rotations/all` - Missing auth

**Recommendation:**
Run security audit script to identify all unprotected endpoints:
```bash
# Find all routes missing authentication
grep -rn "@router" backend/app/api/routes/ | \
  grep -v "get_current_user" | \
  grep -v "require_roles"
```

**Action Required:** Fix all unprotected endpoints before next deployment
```

## Common Failure Modes

| Failure Mode | Symptom | Root Cause | Recovery Steps |
|--------------|---------|------------|----------------|
| **Bandit False Positive** | Security scan flags safe code | Static analysis can't understand context | 1. Manual review confirms safety<br>2. Add `# nosec` with justification<br>3. Document in security log |
| **Hardcoded Secret Not Detected** | Secret committed to repo | Tool doesn't recognize custom secret format | 1. Manually scan for patterns: API keys, tokens<br>2. Use `detect-secrets` with custom patterns<br>3. Rotate compromised secret immediately |
| **Authentication Bypass Not Found** | Endpoint accessible without auth | No automated test for auth enforcement | 1. Manual endpoint inventory<br>2. Test each endpoint without credentials<br>3. Add authentication test suite |
| **OPSEC Data in Logs** | Logs contain sensitive military data | Logging statement added without review | 1. Search logs for PII/OPSEC patterns<br>2. Redact existing logs<br>3. Add log sanitization middleware |
| **Rate Limit Not Applied** | Endpoint vulnerable to brute force | Rate limiter decorator forgotten | 1. Check all auth endpoints for `@rate_limiter.limit()`<br>2. Add rate limiting<br>3. Test with rate limit attack script |
| **HIPAA Audit Trail Missing** | No record of data access | Audit logging not implemented | 1. Add audit middleware to all data access routes<br>2. Log user, timestamp, action, resource<br>3. Verify audit logs are tamper-proof |

## Validation Checklist

After completing security audit, verify:

- [ ] **Authentication:** All sensitive endpoints require `Depends(get_current_user)`
- [ ] **Authorization:** Role checks present where needed (`require_roles()`)
- [ ] **Input Validation:** All inputs use Pydantic schemas
- [ ] **SQL Injection:** No raw SQL with user input (use SQLAlchemy ORM)
- [ ] **Path Traversal:** File paths validated with `validate_path()`
- [ ] **XSS Prevention:** API returns JSON (not HTML), Pydantic auto-escapes
- [ ] **CSRF Protection:** State-changing endpoints use POST/PUT/DELETE
- [ ] **Rate Limiting:** Auth endpoints have rate limits
- [ ] **Secret Management:** No hardcoded secrets, use environment variables
- [ ] **OPSEC/PERSEC:** No real names, deployment data, or PII in code/logs
- [ ] **HIPAA Compliance:** PHI encrypted, access logged, minimum necessary
- [ ] **Audit Logging:** All data access logged with user/timestamp/action
- [ ] **Error Handling:** No sensitive data in error messages
- [ ] **TLS/HTTPS:** All connections encrypted in transit
- [ ] **Dependency Scan:** No known vulnerabilities in `requirements.txt`

## Integration with Other Skills

### With code-review
When security issues detected during code review:
1. Flag immediately with CRITICAL level
2. Defer to security-audit skill for full analysis
3. Block merge until resolved

### With automated-code-fixer
For auto-remediable issues:
1. Apply fix through quality gates
2. Re-run security scan
3. Document remediation

### With production-incident-responder
If security incident detected:
1. Escalate immediately
2. Activate incident response
3. Generate MFR documentation if required

### With pr-reviewer
**Coordination:** Security review integrated into PR workflow
```
1. pr-reviewer detects security-sensitive file (auth, crypto)
2. Trigger security-audit skill for deep analysis
3. Include security findings in PR review
4. Block merge if critical issues found
```

## References

- `docs/security/DATA_SECURITY_POLICY.md` - Full security policy
- `backend/app/core/security.py` - Auth implementation
- `backend/app/core/file_security.py` - File validation
- `backend/app/core/rate_limit.py` - Rate limiting
