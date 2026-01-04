# PHI Handling Guide for Developers

> **Document Classification:** INTERNAL USE ONLY
> **Last Updated:** 2026-01-04
> **Version:** 1.0
> **Audience:** Development Team

---

## Purpose

This guide provides practical guidance for developers working with Protected Health Information (PHI) in the Residency Scheduler application. It ensures HIPAA compliance and DoD OPSEC/PERSEC requirements are met during development, testing, and deployment.

---

## What is PHI in This Application?

### Clear PHI (HIPAA Protected)

| Data Element | Location | Risk Level |
|--------------|----------|------------|
| **Person Names** | `person.name` | HIGH |
| **Email Addresses** | `person.email` | HIGH |
| **Medical Absence Types** | `absence.absence_type = "medical"` | CRITICAL |
| **Free-Text Notes** | `assignment.notes`, `absence.notes`, `swap.reason` | HIGH |

### OPSEC/PERSEC Data (DoD Protected)

| Data Element | Location | Risk Level |
|--------------|----------|------------|
| **Deployment Orders** | `absence.deployment_orders` | CRITICAL |
| **TDY Locations** | `absence.tdy_location` | CRITICAL |
| **Duty Patterns** | `assignment` + `person_id` linkage | HIGH |
| **Schedule Patterns** | Aggregated assignments over time | MEDIUM |

### Non-PHI Data (Safe to Log/Display)

- UUIDs (person_id, block_id, assignment_id)
- Block names and rotation templates
- Dates without person linkage
- Aggregate statistics without identifiers

---

## API Development Guidelines

### 1. Adding X-Contains-PHI Headers

**REQUIREMENT:** All GET endpoints returning PHI must include `X-Contains-PHI` response header.

#### Good Example:

```python
from fastapi import APIRouter, Response

@router.get("/people", response_model=PersonListResponse)
async def list_people(
    response: Response,  # Inject Response object
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """List all people.

    PHI Warning:
        This endpoint returns Protected Health Information (PHI) including
        person names and email addresses. X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)
    return controller.list_people()
```

#### Bad Example (Missing Headers):

```python
# ❌ WRONG - No PHI headers
@router.get("/people", response_model=PersonListResponse)
async def list_people(
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    controller = PersonController(db)
    return controller.list_people()  # Returns PHI without warning!
```

#### When to Add Headers:

**YES - Add Headers:**
- Endpoints returning `person.name` or `person.email`
- Endpoints returning absences with medical types or TDY locations
- Endpoints returning assignments with person linkage
- Endpoints returning notes/free-text fields

**NO - Headers Not Required:**
- Endpoints returning only aggregated statistics
- Endpoints returning only UUIDs without names
- Health check endpoints
- Authentication endpoints (no PHI in payload)

### 2. Avoiding PHI in Error Messages

**REQUIREMENT:** Error messages must not reveal PHI, even for 404/validation errors.

#### Good Example:

```python
from fastapi import HTTPException

def get_person(person_id: UUID):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        # ✅ GOOD - Generic message
        raise HTTPException(
            status_code=404,
            detail="Person not found"
        )
    return person
```

#### Bad Example (Leaking PHI):

```python
def get_person(person_id: UUID):
    person = db.query(Person).filter(Person.id == person_id).first()
    if not person:
        # ❌ WRONG - Exposes person_id in error
        raise HTTPException(
            status_code=404,
            detail=f"Person {person_id} not found"  # Confirms existence!
        )
    return person
```

#### Validation Errors:

```python
# ✅ GOOD - No PHI echoed back
raise HTTPException(
    status_code=400,
    detail="Invalid absence type"
)

# ❌ WRONG - Echoes PHI from user input
raise HTTPException(
    status_code=400,
    detail=f"Invalid absence type: {user_input}"  # Could contain PHI!
)
```

### 3. Minimizing PHI in API Responses

**PRINCIPLE:** Return only the minimum necessary PHI for the use case.

#### Good Example (Minimal PHI):

```python
# For schedule view: Return person_id instead of full person object
{
    "date": "2025-01-15",
    "assignments": [
        {
            "person_id": "123e4567-e89b-12d3-a456-426614174000",
            "person_type": "faculty",
            "role": "supervising",
            "activity": "Inpatient"
            # Frontend can fetch full person details if needed
        }
    ]
}
```

#### Bad Example (Excessive PHI):

```python
# ❌ WRONG - Includes unnecessary PHI in every assignment
{
    "date": "2025-01-15",
    "assignments": [
        {
            "person": {
                "id": "123...",
                "name": "Dr. John Smith",  # Unnecessary PHI
                "email": "john.smith@example.mil",  # Unnecessary PHI
                "type": "faculty"
            },
            "role": "supervising",
            "activity": "Inpatient"
        }
    ]
}
```

---

## Logging Guidelines

### 1. Never Log PHI

**RULE:** Logs are not encrypted and may be retained indefinitely. Never log PHI.

#### Good Examples:

```python
import logging

logger = logging.getLogger(__name__)

# ✅ GOOD - Log using UUIDs
logger.info(f"Created person with ID {person.id}")

# ✅ GOOD - Log counts, not identifiers
logger.info(f"Email sent to {len(recipients)} recipients")

# ✅ GOOD - Log de-identified events
logger.info(f"Absence created for person_id={absence.person_id}")
```

#### Bad Examples (Leaking PHI):

```python
# ❌ WRONG - Logs full name (PHI)
logger.info(f"Created person: {person.name}")

# ❌ WRONG - Logs email address (PHI)
logger.warning(f"No email for {person.name}, skipping reminder")

# ❌ WRONG - Logs email recipients (PHI)
logger.info(f"Email sent to {to_email}: {subject}")

# ❌ WRONG - Logs potentially sensitive notes
logger.info(f"Absence reason: {absence.notes}")
```

### 2. Structured Logging for PHI Access

**REQUIREMENT:** Log all PHI access for audit purposes, but log only metadata.

#### Good Example:

```python
# ✅ GOOD - Audit log with metadata only
logger.info(
    "PHI_ACCESS",
    extra={
        "user_id": current_user.id,
        "user_role": current_user.role,
        "endpoint": "/api/people",
        "method": "GET",
        "person_count": len(results),
        "ip_address": request.client.host,
        "timestamp": datetime.utcnow().isoformat(),
    }
)
```

#### Bad Example:

```python
# ❌ WRONG - Includes actual PHI in logs
logger.info(
    "PHI_ACCESS",
    extra={
        "user": current_user.email,  # PHI!
        "accessed_names": [p.name for p in results],  # PHI!
    }
)
```

---

## Database Query Guidelines

### 1. Use ORM, Never Raw SQL

**REQUIREMENT:** Always use SQLAlchemy ORM to prevent SQL injection and ensure audit logging.

#### Good Example:

```python
from sqlalchemy import select

# ✅ GOOD - ORM query
stmt = select(Person).where(Person.type == person_type)
results = await db.execute(stmt)
people = results.scalars().all()
```

#### Bad Example (SQL Injection Risk):

```python
# ❌ WRONG - Raw SQL with user input
query = f"SELECT * FROM person WHERE type = '{person_type}'"  # VULNERABLE!
results = await db.execute(text(query))
```

### 2. Filter PHI by User Role

**REQUIREMENT:** Apply row-level and field-level access control based on user role.

#### Good Example:

```python
def list_people(self, current_user: User):
    """List people with role-based filtering."""
    stmt = select(Person)

    # Row-level filtering
    if current_user.role == "resident":
        # Residents can only see themselves
        stmt = stmt.where(Person.id == current_user.person_id)
    elif current_user.role in ["faculty", "clinical_staff"]:
        # Faculty/staff can see colleagues
        stmt = stmt.where(Person.type.in_(["faculty", "resident"]))
    # Admins/coordinators see all (no additional filter)

    results = await db.execute(stmt)
    people = results.scalars().all()

    # Field-level filtering (mask email for non-admins)
    if current_user.role != "admin":
        for person in people:
            person.email = None  # Mask email

    return people
```

---

## Testing Guidelines

### 1. Use Synthetic Data for Tests

**REQUIREMENT:** Never use real names, emails, or schedule data in tests.

#### Good Example:

```python
import pytest
from app.models.person import Person

@pytest.fixture
def sample_residents(db):
    """Create synthetic resident data for testing."""
    residents = [
        Person(
            id=uuid4(),
            name="Test Resident 1",  # ✅ Synthetic name
            email="test.resident1@example.com",  # ✅ .com domain
            type="resident",
            pgy_level=1
        ),
        Person(
            id=uuid4(),
            name="Test Resident 2",
            email="test.resident2@example.com",
            type="resident",
            pgy_level=2
        ),
    ]
    db.add_all(residents)
    db.commit()
    return residents
```

#### Bad Example:

```python
# ❌ WRONG - Uses real-sounding names
residents = [
    Person(
        name="John Smith",  # Could be real person!
        email="john.smith@example.mil",  # .mil TLD suggests real
        type="resident",
        pgy_level=1
    ),
]
```

### 2. Test PHI Header Presence

**REQUIREMENT:** All PHI-returning endpoints must have tests verifying X-Contains-PHI header.

#### Good Example:

```python
def test_list_people_has_phi_headers(client, auth_headers):
    """Test that people endpoint includes PHI warning headers."""
    response = client.get("/api/v1/people", headers=auth_headers)

    assert response.status_code == 200
    # ✅ Verify PHI headers present
    assert response.headers.get("X-Contains-PHI") == "true"
    assert "name" in response.headers.get("X-PHI-Fields", "")
    assert "email" in response.headers.get("X-PHI-Fields", "")
```

### 3. Test Error Messages Don't Leak PHI

```python
def test_404_errors_dont_leak_phi(client, auth_headers):
    """Test that 404 errors use generic messages."""
    fake_id = str(uuid4())
    response = client.get(f"/api/v1/people/{fake_id}", headers=auth_headers)

    assert response.status_code == 404
    error_detail = response.json()["detail"]

    # ✅ Verify error doesn't include person_id
    assert fake_id not in error_detail
    assert error_detail == "Person not found"
```

---

## Frontend Development Guidelines

### 1. Display PHI Only When Necessary

**PRINCIPLE:** Show person_id instead of names when possible.

#### Good Example (Schedule View):

```tsx
// ✅ GOOD - Shows role without name
<AssignmentCard>
  <p>Role: Supervising</p>
  <p>Person ID: {assignment.person_id.slice(0, 8)}</p>
  <button onClick={() => fetchPersonDetails(assignment.person_id)}>
    View Details
  </button>
</AssignmentCard>
```

#### Bad Example:

```tsx
// ❌ WRONG - Always fetches and displays full name
<AssignmentCard>
  <p>Person: Dr. {person.name}</p>
  <p>Email: {person.email}</p>
</AssignmentCard>
```

### 2. Mask PHI in URLs and Browser History

```tsx
// ✅ GOOD - Use IDs in URLs, not names
<Link href={`/people/${person.id}`}>View Person</Link>

// ❌ WRONG - Name in URL (PHI in browser history!)
<Link href={`/people/${person.name}`}>View Person</Link>
```

---

## Common Pitfalls and How to Avoid Them

### Pitfall 1: Logging Email Addresses

```python
# ❌ WRONG
logger.info(f"Sending reminder to {person.email}")

# ✅ CORRECT
logger.info(f"Sending reminder to person_id={person.id}")
```

### Pitfall 2: Including PHI in Exception Messages

```python
# ❌ WRONG
raise ValueError(f"Invalid email: {email}")

# ✅ CORRECT
raise ValueError("Invalid email format")
```

### Pitfall 3: Exposing PHI in Debug Mode

```python
# ❌ WRONG - PHI in debug output
if settings.DEBUG:
    print(f"Person data: {person.name}, {person.email}")

# ✅ CORRECT - Use UUIDs even in debug
if settings.DEBUG:
    print(f"Person data: id={person.id}, type={person.type}")
```

### Pitfall 4: Unencrypted Exports

```python
# ❌ WRONG - Plaintext CSV with PHI
with open("export.csv", "w") as f:
    for person in people:
        f.write(f"{person.name},{person.email}\n")

# ✅ CORRECT - Encrypted export
encrypted_data = encrypt_data(csv_content)
return Response(
    content=encrypted_data,
    media_type="application/octet-stream",
    headers={"X-Encryption": "AES-256-GCM"}
)
```

### Pitfall 5: PHI in Git Commits

```bash
# ❌ WRONG - Committing test data with real names
git add data/test_residents.json  # Contains real names!

# ✅ CORRECT - Use .gitignore
echo "data/*.json" >> .gitignore
# Use synthetic data only in committed test files
```

---

## Pre-Deployment Checklist

Before creating a pull request or deploying code that handles PHI, verify:

- [ ] All PHI-returning GET endpoints include `X-Contains-PHI` header
- [ ] Error messages do not reveal PHI
- [ ] Logging statements use UUIDs, not names/emails
- [ ] Tests use synthetic data only (no real names/emails)
- [ ] Tests verify PHI headers are present
- [ ] API responses return minimum necessary PHI
- [ ] Free-text fields are sanitized before logging
- [ ] Database queries use ORM (no raw SQL)
- [ ] Frontend masks PHI in URLs and browser history
- [ ] Exports are encrypted if containing bulk PHI

---

## Resources

- **PHI Exposure Audit:** `docs/security/PHI_EXPOSURE_AUDIT.md`
- **Breach Response Plan:** `docs/security/BREACH_RESPONSE_PLAN.md`
- **Data Security Policy:** `docs/security/DATA_SECURITY_POLICY.md`
- **HIPAA Privacy Rule:** 45 CFR Part 164, Subpart E
- **DoD OPSEC Guide:** AR 530-1

---

## Questions?

If you're unsure whether something is PHI or how to handle it securely:

1. **Check this guide** for similar examples
2. **Ask the Security Lead** before committing code
3. **Use the checklist above** before creating a PR
4. **When in doubt, treat it as PHI** and apply strictest protections

---

**Document Control:**
- Review: Quarterly or when HIPAA regulations change
- Owner: Security Lead + Privacy Officer
- Next Review: 2026-04-04
