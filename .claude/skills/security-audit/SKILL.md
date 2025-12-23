---
name: security-audit
description: Security-focused code audit for healthcare and military contexts. Use when reviewing authentication, authorization, data handling, HIPAA compliance, or OPSEC/PERSEC requirements. Essential for PHI handling and military medical residency schedules.
---

***REMOVED*** Security Audit Skill

Specialized security auditing for healthcare IT systems handling military medical residency data, with focus on HIPAA compliance and OPSEC/PERSEC requirements.

***REMOVED******REMOVED*** When This Skill Activates

- Authentication or authorization code changes
- Code handling PHI (Protected Health Information)
- Military schedule or personnel data handling
- API endpoint security review
- File upload/download functionality
- Cryptographic operations
- Third-party integration reviews
- Pre-deployment security checks

***REMOVED******REMOVED*** Security Domains

***REMOVED******REMOVED******REMOVED*** 1. HIPAA Compliance

| Requirement | Implementation |
|-------------|----------------|
| Access Control | RBAC with 8 roles (Admin, Coordinator, Faculty, etc.) |
| Audit Logging | All data access logged with user, timestamp, action |
| Encryption at Rest | Database column encryption for PHI |
| Encryption in Transit | TLS 1.3 for all connections |
| Minimum Necessary | Query only required fields |

***REMOVED******REMOVED******REMOVED*** 2. OPSEC/PERSEC (Military Data)

**NEVER commit or log:**

| Data Type | Risk | Handling |
|-----------|------|----------|
| Resident/Faculty Names | PERSEC | Sanitize for demos |
| Schedule Assignments | OPSEC | Reveals duty patterns |
| TDY/Deployment Data | OPSEC | Never in repo |
| Absence Records | OPSEC/PERSEC | Local only |

**Safe Identifiers for Demo/Test:**
```python
***REMOVED*** Use synthetic identifiers
residents = ["PGY1-01", "PGY2-01"]  ***REMOVED*** Not real names
faculty = ["FAC-PD", "FAC-APD"]      ***REMOVED*** Role-based IDs
```

***REMOVED******REMOVED******REMOVED*** 3. OWASP Top 10 Checklist

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

***REMOVED******REMOVED*** Security Audit Process

***REMOVED******REMOVED******REMOVED*** Step 1: Threat Model Assessment

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

***REMOVED******REMOVED******REMOVED*** Step 2: Authentication Review

```python
***REMOVED*** Verify proper auth checks
from app.api.deps import get_current_user, require_roles

@router.get("/schedules")
async def get_schedules(
    current_user: User = Depends(get_current_user),  ***REMOVED*** Auth required
    db: AsyncSession = Depends(get_db)
):
    ***REMOVED*** Business logic
    pass

***REMOVED*** Role-based access
@router.post("/admin/users")
async def create_user(
    current_user: User = Depends(require_roles(["admin"]))  ***REMOVED*** Admin only
):
    pass
```

***REMOVED******REMOVED******REMOVED*** Step 3: Input Validation

```python
***REMOVED*** CHECK: All inputs use Pydantic schemas
from app.schemas.assignment import AssignmentCreate

@router.post("/assignments", response_model=AssignmentResponse)
async def create_assignment(
    assignment: AssignmentCreate,  ***REMOVED*** Validated by Pydantic
    db: AsyncSession = Depends(get_db)
):
    pass

***REMOVED*** VERIFY: No raw SQL
***REMOVED*** BAD
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

***REMOVED*** GOOD
result = await db.execute(
    select(User).where(User.id == user_id)
)
```

***REMOVED******REMOVED******REMOVED*** Step 4: Secret Management

```bash
***REMOVED*** Check for hardcoded secrets
cd /home/user/Autonomous-Assignment-Program-Manager

***REMOVED*** Scan for patterns
grep -rn "password\s*=" --include="*.py" backend/
grep -rn "secret\s*=" --include="*.py" backend/
grep -rn "api_key\s*=" --include="*.py" backend/
grep -rn "Bearer " --include="*.py" backend/

***REMOVED*** Verify .env is gitignored
cat .gitignore | grep -E "\.env"

***REMOVED*** Check secret validation
cat backend/app/core/config.py | grep -A5 "SECRET_KEY"
```

***REMOVED******REMOVED******REMOVED*** Step 5: File Security

```python
***REMOVED*** Verify file path validation
from app.core.file_security import validate_path

***REMOVED*** All file operations must use:
safe_path = validate_path(base_directory, user_filename)
```

***REMOVED******REMOVED******REMOVED*** Step 6: Rate Limiting

```python
***REMOVED*** Verify rate limiting on sensitive endpoints
from app.core.rate_limit import rate_limiter

@router.post("/auth/login")
@rate_limiter.limit("5/minute")  ***REMOVED*** Brute force protection
async def login():
    pass
```

***REMOVED******REMOVED*** Vulnerability Patterns

***REMOVED******REMOVED******REMOVED*** SQL Injection

```python
***REMOVED*** VULNERABLE
query = f"SELECT * FROM persons WHERE name = '{user_input}'"

***REMOVED*** SECURE
query = select(Person).where(Person.name == user_input)
```

***REMOVED******REMOVED******REMOVED*** Path Traversal

```python
***REMOVED*** VULNERABLE
file_path = f"/uploads/{filename}"

***REMOVED*** SECURE
from app.core.file_security import validate_path
file_path = validate_path("/uploads", filename)
```

***REMOVED******REMOVED******REMOVED*** XSS via API

```python
***REMOVED*** VULNERABLE - returning raw user input
return {"message": f"Hello {user.name}"}

***REMOVED*** SECURE - Pydantic escaping
from pydantic import BaseModel
class Response(BaseModel):
    message: str  ***REMOVED*** Auto-escaped in JSON serialization
```

***REMOVED******REMOVED******REMOVED*** Insecure Direct Object Reference

```python
***REMOVED*** VULNERABLE - No ownership check
@router.get("/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    return await get_schedule_by_id(schedule_id)

***REMOVED*** SECURE - Ownership verification
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

***REMOVED******REMOVED******REMOVED*** Sensitive Data Exposure

```python
***REMOVED*** VULNERABLE - Full object returned
@router.get("/users/{user_id}")
async def get_user(user_id: str):
    return await db.get(User, user_id)  ***REMOVED*** Includes password hash!

***REMOVED*** SECURE - Schema controls response
@router.get("/users/{user_id}", response_model=UserPublic)
async def get_user(user_id: str):
    return await db.get(User, user_id)  ***REMOVED*** UserPublic excludes sensitive fields
```

***REMOVED******REMOVED*** Security Scanning Commands

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

***REMOVED*** Static security analysis
bandit -r app/ -ll -f json > bandit_report.json

***REMOVED*** Dependency vulnerability check
pip-audit --format=json > pip_audit_report.json

***REMOVED*** Check for secrets in code
pip install detect-secrets
detect-secrets scan app/ > .secrets.baseline

***REMOVED*** SAST with ruff security rules
ruff check app/ --select S
```

***REMOVED******REMOVED*** Audit Report Template

```markdown
***REMOVED******REMOVED*** Security Audit Report

**Date:** YYYY-MM-DD
**Scope:** [Files/Features audited]
**Auditor:** [AI/Human]
**Risk Level:** [LOW/MEDIUM/HIGH/CRITICAL]

***REMOVED******REMOVED******REMOVED*** Executive Summary
[One paragraph overview]

***REMOVED******REMOVED******REMOVED*** Critical Findings
| ID | Finding | CVSS | Remediation |
|----|---------|------|-------------|
| C1 | [Description] | [Score] | [Fix] |

***REMOVED******REMOVED******REMOVED*** High Findings
| ID | Finding | CVSS | Remediation |
|----|---------|------|-------------|
| H1 | [Description] | [Score] | [Fix] |

***REMOVED******REMOVED******REMOVED*** Medium Findings
...

***REMOVED******REMOVED******REMOVED*** Low Findings
...

***REMOVED******REMOVED******REMOVED*** Compliance Status
- [ ] HIPAA: [Status]
- [ ] OPSEC/PERSEC: [Status]
- [ ] OWASP Top 10: [Status]

***REMOVED******REMOVED******REMOVED*** Recommendations
1. [Priority recommendation]
2. [Secondary recommendation]

***REMOVED******REMOVED******REMOVED*** Files Requiring Attention
- `path/to/file.py:line` - [Issue]
```

***REMOVED******REMOVED*** Escalation Rules

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

***REMOVED******REMOVED*** Integration with Other Skills

***REMOVED******REMOVED******REMOVED*** With code-review
When security issues detected during code review:
1. Flag immediately with CRITICAL level
2. Defer to security-audit skill for full analysis
3. Block merge until resolved

***REMOVED******REMOVED******REMOVED*** With automated-code-fixer
For auto-remediable issues:
1. Apply fix through quality gates
2. Re-run security scan
3. Document remediation

***REMOVED******REMOVED******REMOVED*** With production-incident-responder
If security incident detected:
1. Escalate immediately
2. Activate incident response
3. Generate MFR documentation if required

***REMOVED******REMOVED*** References

- `docs/security/DATA_SECURITY_POLICY.md` - Full security policy
- `backend/app/core/security.py` - Auth implementation
- `backend/app/core/file_security.py` - File validation
- `backend/app/core/rate_limit.py` - Rate limiting
