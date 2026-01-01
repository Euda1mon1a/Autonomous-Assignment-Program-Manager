# PHI Exposure Audit Report

> **Audit Date:** 2025-12-30
> **Auditor:** AI Security Analyst
> **Scope:** Backend API routes, schemas, error handling, and logging
> **Status:** Comprehensive review completed

---

## Executive Summary

This audit evaluated the Residency Scheduler application for Protected Health Information (PHI) exposure in API responses, error messages, logs, and exports. The system implements **strong authentication and authorization**, but **PHI is exposed in multiple API responses** without masking or field-level access control.

### Overall Risk Assessment

| Category | Risk Level | Notes |
|----------|-----------|-------|
| **API Responses** | HIGH | Person names and emails exposed in plain text |
| **Export Endpoints** | HIGH | Bulk PHI exports (admin-only, but unencrypted) |
| **Error Messages** | LOW | Generic messages in production mode |
| **Logging** | MEDIUM | Email addresses and names logged server-side |
| **Authentication** | LOW | Strong RBAC controls access |
| **OPSEC/PERSEC** | MEDIUM | Schedule patterns and TDY locations exposed |

**Overall HIPAA Compliance Status:** ⚠️ **PARTIAL COMPLIANCE** - Requires remediation

---

## 1. PHI Data Elements Identified

### 1.1 Person Data (Highest Risk)

**Schema:** `backend/app/schemas/person.py` → `PersonResponse`

| Field | PHI Classification | Exposure Level | HIPAA Category |
|-------|-------------------|----------------|----------------|
| `name` | **CLEAR PHI** | All authenticated users | Directly identifying |
| `email` | **CLEAR PHI** | All authenticated users | Directly identifying |
| `pgy_level` | Potentially identifying | All authenticated users | Demographic |
| `specialties` | Potentially identifying | All authenticated users | Demographic |
| `faculty_role` | Potentially identifying | All authenticated users | Demographic |
| `sunday_call_count` | Pattern revealing | All authenticated users | Operational |
| `weekday_call_count` | Pattern revealing | All authenticated users | Operational |
| `fmit_weeks_count` | Pattern revealing | All authenticated users | Operational |

**Affected Endpoints:**
- `GET /api/people` - Returns list of all people with names/emails
- `GET /api/people/residents` - Returns resident names/emails
- `GET /api/people/faculty` - Returns faculty names/emails
- `GET /api/people/{person_id}` - Returns individual person details

**Example Response (CURRENT):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "Dr. John Smith",  // CLEAR PHI
  "email": "john.smith@example.mil",  // CLEAR PHI
  "type": "faculty",
  "pgy_level": null,
  "specialties": ["Family Medicine"],
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### 1.2 Absence Data (OPSEC/PERSEC Risk)

**Schema:** `backend/app/schemas/absence.py` → `AbsenceResponse`

| Field | PHI Classification | Exposure Level | Military Risk |
|-------|-------------------|----------------|---------------|
| `person_id` | Links to PHI | All authenticated users | Identifies individual |
| `absence_type` | Potentially sensitive | All authenticated users | Medical = PHI |
| `deployment_orders` | **OPSEC CRITICAL** | All authenticated users | Reveals deployments |
| `tdy_location` | **OPSEC CRITICAL** | All authenticated users | Reveals movements |
| `notes` | **Could contain PHI** | All authenticated users | Free text risk |
| `start_date` / `end_date` | Movement patterns | All authenticated users | OPSEC |

**Affected Endpoints:**
- `GET /api/absences` - Returns list of absences with person linkage
- `GET /api/absences/{absence_id}` - Returns individual absence details

**OPSEC Concern:** Absence types like `deployment`, `tdy`, `medical`, `maternity_paternity`, `family_emergency` reveal sensitive information about military personnel.

---

### 1.3 Assignment/Schedule Data (Pattern Exposure)

**Schema:** `backend/app/schemas/assignment.py` → `AssignmentResponse`

| Field | PHI Classification | Exposure Level | OPSEC Risk |
|-------|-------------------|----------------|------------|
| `person_id` | Links to PHI | All authenticated users | Identifies individual |
| `block_id` + `person_id` | **Duty pattern** | All authenticated users | Reveals schedule |
| `notes` | **Could contain PHI** | All authenticated users | Free text risk |
| `override_reason` | **Could contain PHI** | All authenticated users | Free text risk |
| `rotation_template_id` | Reveals assignment type | All authenticated users | Operational pattern |

**Affected Endpoints:**
- `GET /api/assignments` - Returns assignments with person linkage
- `GET /api/schedule/{start_date}/{end_date}` - **Returns person names in schedule** (line 448-458)

**Example Response from `/api/schedule/{start_date}/{end_date}`:**
```json
{
  "2025-01-15": {
    "AM": [
      {
        "person": {
          "id": "123...",
          "name": "Dr. John Smith",  // CLEAR PHI
          "type": "faculty",
          "pgy_level": null
        },
        "role": "supervising",
        "activity": "Inpatient"
      }
    ]
  }
}
```

**OPSEC Risk:** Combining schedule data reveals duty patterns, which is classified as OPSEC-sensitive for military medical personnel.

---

### 1.4 Swap Request Data (Faculty PHI)

**Schema:** `backend/app/schemas/swap.py` → `SwapRecordResponse`

| Field | PHI Classification | Exposure Level | Risk |
|-------|-------------------|----------------|------|
| `source_faculty_name` | **CLEAR PHI** | All authenticated users | Directly identifying |
| `target_faculty_name` | **CLEAR PHI** | All authenticated users | Directly identifying |
| `source_week` / `target_week` | Schedule pattern | All authenticated users | OPSEC |
| `reason` | **Could contain PHI** | All authenticated users | Free text risk |

**Affected Endpoints:**
- `GET /api/swaps/history` - Returns swap records with faculty names
- `POST /api/schedule/swaps/find` - Returns candidate names (line 1166-1167)

---

## 2. Bulk Export Endpoints (HIGH RISK)

**File:** `backend/app/api/routes/export.py`

All export endpoints require **admin authentication** (good), but export **unencrypted PHI** in bulk.

### 2.1 People Export

**Endpoint:** `GET /api/export/people`

**Exports (CSV/JSON):**
- Full names
- Email addresses
- PGY levels
- Specialties

**Risk:** Bulk PHI exposure if admin account compromised or export file leaked.

### 2.2 Absence Export

**Endpoint:** `GET /api/export/absences`

**Exports (CSV/JSON):**
- Person names
- Absence types (including medical)
- Start/end dates
- TDY locations (OPSEC)
- Notes (could contain PHI)

**Risk:** HIPAA violation if medical absence details exported without encryption.

### 2.3 Schedule Export

**Endpoint:** `GET /api/export/schedule`

**Exports (CSV/JSON/XLSX):**
- Person names
- PGY levels
- Daily assignments
- Role assignments

**Risk:** Reveals complete duty patterns for all personnel (OPSEC).

---

## 3. Error Messages (LOW RISK)

### 3.1 Global Exception Handler

**File:** `backend/app/main.py` (lines 260-284)

**Good Pattern:**
```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if settings.DEBUG:
        # Development: includes details
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    else:
        # Production: generic message (GOOD)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please try again later."}
        )
```

**Status:** ✅ **COMPLIANT** - Production mode hides implementation details.

### 3.2 Specific Error Messages

**Minor Concern:** `backend/app/api/routes/schedule.py` line 1029

```python
raise HTTPException(
    status_code=404,
    detail=f"Person {request.person_id} not found"  # Exposes person ID
)
```

**Risk:** Low - person ID is a UUID (not directly identifying), but confirms existence/non-existence.

**Recommendation:** Change to generic "Person not found" without ID.

---

## 4. Logging (MEDIUM RISK)

### 4.1 Email Address Logging

**File:** `backend/app/services/email_service.py`

**Lines 88, 92, 114, 118:**
```python
logger.info(f"Email sent to {to_email}: {subject}")
logger.warning(f"No email for {person.name}, skipping reminder")
```

**Risk:** Email addresses and person names logged server-side.

**HIPAA Compliance:** Logs are considered PHI if they contain identifiable information.

### 4.2 Certification Scheduler Logging

**File:** `backend/app/services/certification_scheduler.py` line 129

```python
logger.warning(f"No email for {person.name}, skipping reminder")
```

**Risk:** Person names logged during batch operations.

### 4.3 Compliance Report Logging

**File:** `backend/app/tasks/compliance_report_tasks.py` lines 119, 248, 368

```python
logger.info(f"Found {len(emails)} program director email(s)")
logger.info(f"Violation alert email queued for {email}")
```

**Risk:** Email addresses logged during report generation.

---

## 5. HIPAA Compliance Analysis

### 5.1 HIPAA Requirements

| Requirement | Status | Notes |
|-------------|--------|-------|
| **Minimum Necessary** | ❌ VIOLATION | All authenticated users see full PHI |
| **Access Controls** | ✅ PARTIAL | RBAC implemented, but no field-level controls |
| **Encryption at Rest** | ✅ COMPLIANT | Database encrypted (assumed) |
| **Encryption in Transit** | ✅ COMPLIANT | HTTPS enforced (HSTS enabled) |
| **Audit Trails** | ✅ PARTIAL | Auth logged, but no PHI access logging |
| **Data Minimization** | ❌ VIOLATION | API responses include all PHI fields |
| **Breach Notification** | ⚠️ UNKNOWN | No documented breach response plan |

### 5.2 HIPAA Privacy Rule Violations

1. **Minimum Necessary Standard (45 CFR 164.502(b)):**
   - ❌ API responses return full person records when only IDs are needed
   - ❌ Non-admin users can access names/emails of all personnel

2. **Administrative Safeguards (45 CFR 164.308):**
   - ❌ No documented PHI access policies
   - ❌ No training documentation for PHI handling

3. **Technical Safeguards (45 CFR 164.312):**
   - ❌ No access controls limiting PHI to authorized users only
   - ❌ No audit controls tracking PHI access
   - ✅ Encryption in transit (HTTPS)
   - ⚠️ Encryption at rest (assumed but not verified)

---

## 6. OPSEC/PERSEC Compliance (Military Context)

### 6.1 PERSEC Violations

| Data Type | Exposure | Risk Level | DoD Policy |
|-----------|----------|------------|------------|
| **Military Personnel Names** | All API responses | HIGH | AR 530-1 |
| **Email Addresses (.mil)** | All API responses | HIGH | AR 530-1 |
| **Assignment Patterns** | Schedule endpoints | HIGH | OPSEC Critical |
| **Deployment Status** | Absence records | CRITICAL | OPSEC Critical |
| **TDY Locations** | Absence records | CRITICAL | OPSEC Critical |

### 6.2 Data Security Policy Alignment

**Reference:** `docs/security/DATA_SECURITY_POLICY.md`

| Policy Requirement | Status | Notes |
|-------------------|--------|-------|
| No real names in repo | ✅ COMPLIANT | Code uses generic examples |
| No real names in API | ❌ VIOLATION | API returns actual names |
| No schedule assignments in repo | ✅ COMPLIANT | Data gitignored |
| No TDY/deployment data in repo | ✅ COMPLIANT | Data gitignored |
| Use role-based IDs for demo | ⚠️ PARTIAL | Demo data exists, but API exposes real data |

**Gap:** Policy covers repository hygiene but not runtime API exposure.

---

## 7. Recommendations

### 7.1 CRITICAL (Implement Within 30 Days)

**1. Implement PHI Masking for Non-Admin Users**

Add role-based field filtering to Pydantic schemas:

```python
class PersonResponse(PersonBase):
    id: UUID
    name: str
    email: EmailStr | None = None  # Only for admins

    @classmethod
    def from_orm_masked(cls, person: Person, user_role: str):
        """Return masked version for non-admin users."""
        data = {
            "id": person.id,
            "name": person.name if user_role == "admin" else f"Person-{str(person.id)[:8]}",
            "email": person.email if user_role == "admin" else None,
            "type": person.type,
            "pgy_level": person.pgy_level,
        }
        return cls(**data)
```

**2. Add PHI Access Audit Logging**

Create audit middleware to log all PHI access:

```python
@app.middleware("http")
async def audit_phi_access(request: Request, call_next):
    """Log access to PHI-containing endpoints."""
    phi_endpoints = ["/api/people", "/api/export", "/api/schedule"]

    if any(request.url.path.startswith(ep) for ep in phi_endpoints):
        logger.info(
            "PHI_ACCESS",
            extra={
                "user": request.state.user.username,
                "endpoint": request.url.path,
                "method": request.method,
                "ip": request.client.host,
            }
        )

    return await call_next(request)
```

**3. Encrypt Bulk Exports**

Add AES-256 encryption to export endpoints:

```python
from app.security.key_management import KeyManagementService

def create_encrypted_export(content: str, filename: str):
    kms = KeyManagementService()
    encrypted = kms.encrypt(content.encode(), key_name="export-key")

    return StreamingResponse(
        iter([encrypted]),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}.enc",
            "X-Encryption": "AES-256-GCM",
        }
    )
```

### 7.2 HIGH PRIORITY (Implement Within 60 Days)

**4. Sanitize Logging to Exclude PHI**

Replace email addresses and names with IDs in logs:

```python
# Before (CURRENT):
logger.info(f"Email sent to {to_email}: {subject}")

# After (RECOMMENDED):
logger.info(f"Email sent to user {user_id}: {subject}")
```

**5. Implement Field-Level Access Control**

Add Pydantic schema transformers based on user role:

```python
def filter_response_fields(
    response: BaseModel,
    user_role: str,
    field_permissions: dict
) -> dict:
    """Filter response fields based on role permissions."""
    response_dict = response.model_dump()
    allowed_fields = field_permissions.get(user_role, [])

    return {
        k: v for k, v in response_dict.items()
        if k in allowed_fields or k == "id"
    }
```

**6. Add Data Minimization to Schedule Endpoints**

Return person IDs instead of full person objects:

```python
# Before (CURRENT):
"person": {
    "id": "123...",
    "name": "Dr. John Smith",  # PHI
    "email": "john.smith@example.mil",  # PHI
    "type": "faculty"
}

# After (RECOMMENDED):
"person_id": "123...",
"person_type": "faculty",
"person_pgy_level": null
```

Frontend can fetch full details only when needed (with proper authorization).

### 7.3 MEDIUM PRIORITY (Implement Within 90 Days)

**7. Add PHI Warning Headers to Sensitive Endpoints**

```python
@router.get("/people")
def list_people(...):
    """List all people. Contains PHI."""
    response = controller.list_people(...)
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"
    return response
```

**8. Implement Breach Notification Procedures**

Document breach response plan in `docs/security/BREACH_RESPONSE_PLAN.md`.

**9. Create PHI Access Training Documentation**

Add developer training guide for PHI handling in `docs/security/PHI_HANDLING_GUIDE.md`.

**10. Add Automated PHI Detection Tests**

```python
def test_no_phi_in_public_endpoints():
    """Ensure public endpoints don't leak PHI."""
    response = client.get("/api/health")
    assert "email" not in response.text
    assert "name" not in response.text
```

### 7.4 LOW PRIORITY (Implement Within 6 Months)

**11. Implement Differential Privacy for Analytics**

Add noise to aggregate statistics to prevent re-identification.

**12. Add Data Loss Prevention (DLP) Rules**

Integrate with DLP tools to detect PHI exfiltration attempts.

**13. Conduct Annual PHI Exposure Audits**

Schedule quarterly reviews of API responses and logs.

---

## 8. Immediate Actions Checklist

> **Status Update (2026-01-01):** PHI exposure documented in HUMAN_TODO.md. See "Security & Compliance" section.

- [x] **CRITICAL:** Document current PHI exposure in HUMAN_TODO.md
- [ ] **CRITICAL:** Add "X-Contains-PHI" warning headers to affected endpoints
- [ ] **CRITICAL:** Implement PHI access audit logging
- [ ] **HIGH:** Sanitize logging to remove email addresses and names
- [ ] **HIGH:** Add field-level access control to PersonResponse schema
- [ ] **HIGH:** Encrypt bulk export downloads
- [ ] **MEDIUM:** Create BREACH_RESPONSE_PLAN.md
- [ ] **MEDIUM:** Create PHI_HANDLING_GUIDE.md for developers
- [ ] **MEDIUM:** Add automated tests for PHI exposure
- [ ] **LOW:** Review frontend PHI handling
- [ ] **LOW:** Conduct penetration test focused on PHI exfiltration

---

## 9. Compliance Summary

### 9.1 HIPAA Compliance Score: 6/10

**Strengths:**
- Strong authentication and authorization (RBAC)
- Encryption in transit (HTTPS/HSTS)
- Generic error messages in production
- Admin-only access to bulk exports

**Weaknesses:**
- No minimum necessary controls (all users see all PHI)
- No audit trails for PHI access
- Logging contains PHI (email addresses, names)
- No encryption for bulk exports
- Free text fields (notes, reasons) not sanitized

### 9.2 OPSEC/PERSEC Compliance Score: 5/10

**Strengths:**
- Real data gitignored (not in repository)
- Authentication required for all endpoints

**Weaknesses:**
- Military personnel names exposed via API
- Deployment and TDY data exposed via absences
- Schedule patterns reveal duty assignments
- No data minimization for operational patterns

---

## 10. References

### Regulatory References

- **HIPAA Privacy Rule:** 45 CFR Part 160 and Part 164, Subparts A and E
- **HIPAA Security Rule:** 45 CFR Part 164, Subpart C
- **DoD AR 530-1:** Operations Security (OPSEC)
- **DoD 5400.11-R:** Department of Defense Privacy Program

### Internal References

- `docs/security/DATA_SECURITY_POLICY.md` - Data security policy
- `docs/security/SECURITY_PATTERN_AUDIT.md` - Security architecture review
- `CLAUDE.md` - Security requirements and best practices
- `backend/app/core/security.py` - Authentication implementation
- `backend/app/schemas/person.py` - Person schema (PHI exposure)
- `backend/app/api/routes/export.py` - Bulk export endpoints (PHI exposure)

---

**End of Audit Report**

*Next Review Date: 2026-01-30*
*Auditor Signature: AI Security Analyst*
*Classification: INTERNAL USE ONLY - Contains security findings*
