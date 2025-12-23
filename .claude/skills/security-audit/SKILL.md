---
name: security-audit
description: Security-focused code audit for healthcare and military contexts. Use when reviewing authentication, authorization, data handling, HIPAA compliance, or OPSEC/PERSEC requirements. Essential for PHI handling and military medical residency schedules.
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

## References

- `docs/security/DATA_SECURITY_POLICY.md` - Full security policy
- `backend/app/core/security.py` - Auth implementation
- `backend/app/core/file_security.py` - File validation
- `backend/app/core/rate_limit.py` - Rate limiting
