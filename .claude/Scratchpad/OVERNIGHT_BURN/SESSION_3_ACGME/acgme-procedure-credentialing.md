***REMOVED*** ACGME Procedure Credentialing Requirements

**Document Type:** SEARCH_PARTY Reconnaissance Report
**Target:** ACGME procedure credentialing requirements & tracking systems
**Scope:** Backend implementation analysis (models, services, repositories)
**Status:** Reconnaissance Complete
**Date:** 2025-12-30

---

***REMOVED******REMOVED*** Executive Summary

The residency scheduler implements a comprehensive **procedure credentialing system** that tracks faculty qualifications to supervise medical procedures. The system enforces credential validity, manages competency levels, and integrates with slot-type invariants for assignment eligibility.

**Key Findings:**
- Dual-table architecture: `procedures` + `procedure_credentials`
- Four credential statuses with expiration tracking
- Four competency levels tied to supervision capacity
- Hard/soft constraint system for slot eligibility
- Complete audit trail with issued/verified/expiration dates

---

***REMOVED******REMOVED*** SEARCH_PARTY Probe Results

***REMOVED******REMOVED******REMOVED*** 1. PERCEPTION: Current Procedure Tracking

**Location:** `/backend/app/models/procedure.py`

***REMOVED******REMOVED******REMOVED******REMOVED*** Procedure Model Structure

```python
class Procedure(Base):
    """Represents a medical procedure requiring credentialed supervision."""

    __tablename__ = "procedures"

    ***REMOVED*** Core Fields
    id = GUID (PK)
    name: String(255) - unique, required
    description: Text (optional)

    ***REMOVED*** Categorization
    category: String(100)              ***REMOVED*** 'surgical', 'office', 'obstetric', 'clinic'
    specialty: String(100)             ***REMOVED*** 'Sports Medicine', 'OB/GYN', 'Dermatology'

    ***REMOVED*** Supervision Requirements
    supervision_ratio: Integer         ***REMOVED*** Max residents per faculty (default: 1)
    requires_certification: Boolean    ***REMOVED*** Must have explicit credential (default: True)

    ***REMOVED*** Complexity/Training
    complexity_level: String(50)       ***REMOVED*** 'basic', 'standard', 'advanced', 'complex'
    min_pgy_level: Integer             ***REMOVED*** Minimum PGY level to perform (default: 1)

    ***REMOVED*** Status
    is_active: Boolean                 ***REMOVED*** Soft-delete flag (default: True)

    ***REMOVED*** Timestamps
    created_at: DateTime (UTC)
    updated_at: DateTime (UTC)

    ***REMOVED*** Relationships
    credentials → ProcedureCredential[] (cascade delete)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Supported Procedure Categories

| Category | Examples | Supervision Ratio |
|----------|----------|-------------------|
| **surgical** | Mastectomy, Vasectomy, hysterectomy | 1:1 (faculty:resident) |
| **office** | Botox injection, IUD placement, joint injection | 1:2 to 1:1 |
| **obstetric** | Labor & delivery, cesarean section | 1:1 |
| **clinic** | Sports medicine clinic, peds clinic, general clinic | 1:2 to 1:4 |

***REMOVED******REMOVED******REMOVED******REMOVED*** Complexity Levels (Tied to Training)

| Level | Description | Min PGY | Supervision |
|-------|-------------|---------|-------------|
| **basic** | Simple, low-risk procedures | PGY-1 | Direct supervision |
| **standard** | Standard training procedures | PGY-1 | Direct/indirect supervision |
| **advanced** | Complex procedures requiring skill development | PGY-2 | Graduated responsibility |
| **complex** | High-risk, specialized procedures | PGY-3+ | Consultative/expert review |

---

***REMOVED******REMOVED******REMOVED*** 2. INVESTIGATION: Credential → Procedure Mapping

**Location:** `/backend/app/models/procedure_credential.py`

***REMOVED******REMOVED******REMOVED******REMOVED*** ProcedureCredential Model Structure

```python
class ProcedureCredential(Base):
    """Faculty credential to supervise a specific procedure."""

    __tablename__ = "procedure_credentials"
    __unique_constraint__ = (person_id, procedure_id)  ***REMOVED*** One credential per pair

    ***REMOVED*** Core Fields
    id = GUID (PK)
    person_id = GUID (FK → people.id, CASCADE)
    procedure_id = GUID (FK → procedures.id, CASCADE)

    ***REMOVED*** Credential Status (4-state machine)
    status: String(50)
        ├─ 'active'      ***REMOVED*** Currently valid and usable
        ├─ 'expired'     ***REMOVED*** Manually marked expired
        ├─ 'suspended'   ***REMOVED*** Temporarily revoked
        └─ 'pending'     ***REMOVED*** Awaiting verification

    ***REMOVED*** Competency Level (4-tier proficiency)
    competency_level: String(50)
        ├─ 'trainee'     ***REMOVED*** Learning/supervised practice
        ├─ 'qualified'   ***REMOVED*** Competent independent performance (default)
        ├─ 'expert'      ***REMOVED*** Advanced skill level
        └─ 'master'      ***REMOVED*** Mastery/teaching level

    ***REMOVED*** Credentialing Timeline
    issued_date: Date                  ***REMOVED*** When credential granted
    expiration_date: Date (nullable)   ***REMOVED*** NULL = no expiration
    last_verified_date: Date           ***REMOVED*** Most recent verification

    ***REMOVED*** Supervision Capacity (overrides procedure defaults)
    max_concurrent_residents: Integer (nullable)  ***REMOVED*** NULL = use procedure default
    max_per_week: Integer (nullable)   ***REMOVED*** NULL = unlimited
    max_per_academic_year: Integer (nullable)   ***REMOVED*** NULL = unlimited

    ***REMOVED*** Audit Trail
    notes: Text                        ***REMOVED*** Suspension reasons, renewal notes, etc.
    created_at: DateTime (UTC)
    updated_at: DateTime (UTC)

    ***REMOVED*** Relationships
    person → Person
    procedure → Procedure

    ***REMOVED*** Computed Properties
    @property is_valid: bool
        Returns: status == 'active' AND (expiration_date is None OR today < expiration_date)

    @property is_expired: bool
        Returns: expiration_date is not None AND today >= expiration_date
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Credential Status States & Transitions

```
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    v                                                 v
┌────────┐     verify()      ┌────────┐  suspend()  ┌──────────┐
│pending │ ──────────────→ │ active │ ──────────→ │suspended │
└────────┘                   └────────┘             └──────────┘
                               ^   │
                               │   └─────────────→ expired (manual)
                    activate() │   (by expiration_date)
                               │
                            (valid until expiration_date)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Competency Level Implications

| Level | Training Stage | Supervision Type | Capacity Impact |
|-------|---|---|---|
| **trainee** | Early learning | 1:1 direct supervision | 50% capacity |
| **qualified** | Independent | 1:1 or 1:2 (procedure-dependent) | Full capacity |
| **expert** | Advanced mastery | 1:2-1:4 (flexible) | 125% capacity (can teach) |
| **master** | Teaching/mentorship | Consultative only | 150% capacity (teaching focus) |

---

***REMOVED******REMOVED******REMOVED*** 3. ARCANA: Minimum Case Requirements

**Finding:** No explicit minimum case counting system currently implemented in procedure credentialing.

**However:** Slot-type invariant system provides implicit tracking through credential validity.

***REMOVED******REMOVED******REMOVED******REMOVED*** Credential Invariant Catalog (Proposed)

From `/backend/tests/integration/test_credential_invariants.py`:

```python
INVARIANT_CATALOG = {
    "inpatient_call": {
        "hard": [
            "HIPAA",           ***REMOVED*** Mandatory
            "Cyber_Training",  ***REMOVED*** Mandatory
            "AUP",             ***REMOVED*** Mandatory
            "Chaperone",       ***REMOVED*** Mandatory
            "N95_Fit"          ***REMOVED*** Mandatory
        ],
        "soft": [
            {
                "name": "expiring_soon",
                "window_days": 14,
                "penalty": 3
            }
        ]
    },
    "peds_clinic": {
        "hard": ["BLS", "HIPAA"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 3}]
    },
    "procedures_half_day": {
        "hard": ["BLS", "BBP_Module", "Sharps_Safety"],
        "soft": [{"name": "expiring_soon", "window_days": 30, "penalty": 5}]
    },
    "general_clinic": {
        "hard": ["HIPAA", "BLS"],
        "soft": [{"name": "expiring_soon", "window_days": 14, "penalty": 2}]
    },
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Eligibility Logic

```python
def is_eligible(person: Person, slot_type: str, assignment_date: date, db: Session) -> tuple[bool, int, list[str]]:
    """
    Check if person meets slot requirements.

    Returns:
        (eligible: bool, penalty: int, missing_credentials: list[str])

    Hard constraints: ALL must be present and valid
    Soft constraints: Missing = penalty score applied to slot preference
    """
    reqs = INVARIANT_CATALOG.get(slot_type, {})
    missing_credentials = []
    penalty = 0

    ***REMOVED*** Hard constraints - MUST PASS
    for req_cert_name in reqs.get("hard", []):
        cert = get_certification(person_id, req_cert_name)
        if not cert or not cert.is_valid or cert.expires_before(assignment_date):
            missing_credentials.append(req_cert_name)
            return (False, 0, missing_credentials)  ***REMOVED*** FAIL

    ***REMOVED*** Soft constraints - PENALTY if missing
    for soft in reqs.get("soft", []):
        if soft["name"] == "expiring_soon":
            if any_credential_expiring(person_id, soft["window_days"], assignment_date):
                penalty += soft["penalty"]

    return (True, penalty, [])  ***REMOVED*** SUCCESS
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Minimum Case Tracking Strategy

**Current:** Not implemented explicitly.

**Proposed** (to meet ACGME standards):

1. **Case Logging Table** (not yet created)
   - person_id, procedure_id, case_date, case_type, supervising_faculty
   - Allows: case counting, competency progression, minimum threshold enforcement

2. **Credential Milestone System** (not yet created)
   - Graduation criteria from trainee → qualified → expert
   - Example: "IUD placement: 20 supervised cases → qualified status"

3. **Dashboard Metrics** (planned)
   - "Resident X needs N more cases to graduate from trainee"
   - "Faculty Y has performed 150 cases this year (satisfies re-credentialing)"

---

***REMOVED******REMOVED******REMOVED*** 4. HISTORY: Credentialing Evolution

**Migration:** `/backend/alembic/versions/007_add_procedure_credentialing.py`

***REMOVED******REMOVED******REMOVED******REMOVED*** Schema Constraints

```sql
-- Status validation
CHECK (status IN ('active', 'expired', 'suspended', 'pending'))

-- Competency level validation
CHECK (competency_level IN ('trainee', 'qualified', 'expert', 'master'))

-- Supervision ratio validation
CHECK (supervision_ratio >= 1)

-- Procedure complexity validation
CHECK (complexity_level IN ('basic', 'standard', 'advanced', 'complex'))

-- PGY level validation
CHECK (min_pgy_level BETWEEN 1 AND 3)

-- Unique credential per person per procedure
UNIQUE CONSTRAINT (person_id, procedure_id)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Indexes for Performance

```sql
CREATE INDEX idx_credentials_person ON procedure_credentials(person_id)
CREATE INDEX idx_credentials_procedure ON procedure_credentials(procedure_id)
CREATE INDEX idx_credentials_status ON procedure_credentials(status)
CREATE INDEX idx_credentials_expiration ON procedure_credentials(expiration_date)

CREATE INDEX idx_procedures_name ON procedures(name)
CREATE INDEX idx_procedures_specialty ON procedures(specialty)
CREATE INDEX idx_procedures_category ON procedures(category)
CREATE INDEX idx_procedures_active ON procedures(is_active)
```

---

***REMOVED******REMOVED******REMOVED*** 5. INSIGHT: Competency Assessment

**Service Layer:** `/backend/app/services/credential_service.py`

***REMOVED******REMOVED******REMOVED******REMOVED*** Competency Assessment Methods

```python
class CredentialService:

    def get_faculty_credential_summary(person_id: UUID) -> dict:
        """
        Returns:
        {
            'person_id': UUID,
            'person_name': str,
            'total_credentials': int,          ***REMOVED*** All-time credential count
            'active_credentials': int,         ***REMOVED*** Currently valid
            'expiring_soon': int,              ***REMOVED*** Expiring within 30 days
            'procedures': list[Procedure],     ***REMOVED*** All qualified procedures
            'error': None | str
        }
        """

    def is_faculty_qualified(person_id: UUID, procedure_id: UUID) -> dict:
        """
        Quick qualification check before assignment.

        Returns: {'is_qualified': bool}
        Validation:
        - status == 'active'
        - expiration_date is None OR expiration_date >= today
        - person.type == 'faculty'
        """

    def list_qualified_faculty_for_procedure(procedure_id: UUID) -> dict:
        """
        Returns all faculty qualified to supervise a procedure.
        Filters: status='active', non-expired, person.type='faculty'
        """

    def list_procedures_for_faculty(person_id: UUID) -> list[Procedure]:
        """All procedures faculty is qualified to supervise."""
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Verification Workflow

```python
def verify_credential(credential_id: UUID) -> dict:
    """
    Mark credential as verified today.
    Updates: last_verified_date = date.today()

    ACGME compliance: Credentials should be re-verified periodically
    (typically annually for medical credentials)
    """
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Suspension Lifecycle

```python
def suspend_credential(credential_id: UUID, notes: str | None = None) -> dict:
    """
    Temporarily revoke credential.

    Updates:
    - status = 'suspended'
    - notes = suspension reason (e.g., "Failed competency assessment")

    Flow:
    suspended → (resolve issue) → activate_credential()
    """
```

---

***REMOVED******REMOVED******REMOVED*** 6. RELIGION: All Procedures Logged?

**Current Implementation:** YES - Procedure must be registered in database.

***REMOVED******REMOVED******REMOVED******REMOVED*** Procedure Registration Flow

```python
***REMOVED*** Routes: POST /api/procedures
def create_procedure(procedure_in: ProcedureCreate) -> ProcedureResponse:
    """
    Register new medical procedure.

    Required fields:
    - name: unique identifier
    - category: 'surgical' | 'office' | 'obstetric' | 'clinic'
    - specialty: 'OB/GYN' | 'Dermatology' | 'Urology' | etc.
    - complexity_level: 'basic' | 'standard' | 'advanced' | 'complex'
    - min_pgy_level: 1 | 2 | 3
    - supervision_ratio: integer >= 1
    """

    ***REMOVED*** Database constraint enforces unique procedure name
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Credential Assignment Flow

```
User creates Procedure → Faculty earns credential →
    Credential tracked with dates & competency →
        Used in assignment slot eligibility checks
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Audit Trail

All procedures and credentials have:
- `created_at`: When registered (UTC)
- `updated_at`: When last modified (UTC)
- For credentials: `last_verified_date` (re-certification tracking)

---

***REMOVED******REMOVED******REMOVED*** 7. NATURE: Over-Documentation?

**Analysis:** System is appropriately detailed, not over-documented.

***REMOVED******REMOVED******REMOVED******REMOVED*** What's Tracked

| Aspect | Tracked | Necessary |
|--------|---------|-----------|
| Credential issued date | Yes | For re-credentialing windows |
| Credential expiration | Yes | For compliance enforcement |
| Last verification date | Yes | For audit trail |
| Supervision capacity limits | Yes | For workload balancing |
| Competency level | Yes | For assignment appropriateness |
| Suspension notes | Yes | For compliance investigation |
| Procedure complexity | Yes | For resident progression |
| Procedure min PGY | Yes | For eligibility enforcement |

***REMOVED******REMOVED******REMOVED******REMOVED*** What's NOT Tracked (Could Be Considered)

- **Case counts**: No explicit minimum case logging → OPPORTUNITY
- **Remediation history**: Only current status stored → Could track suspension timeline
- **Competency assessment scores**: Boolean is_valid only → Could track numerical proficiency ratings
- **Re-credentialing deadlines**: Expiration tracked, but no pre-renewal warnings → Could add proactive alerts

---

***REMOVED******REMOVED******REMOVED*** 8. MEDICINE: Patient Safety Requirements

***REMOVED******REMOVED******REMOVED******REMOVED*** ACGME Standards Enforced

1. **Supervision Ratios** (Procedure-level)
   ```python
   supervision_ratio = 1  ***REMOVED*** 1:1 = one faculty per resident
   supervision_ratio = 2  ***REMOVED*** 1:2 = one faculty per two residents
   ```
   Enforced by: `Procedure.supervision_ratio` field

2. **Credential Validity** (Assignment-level)
   ```python
   ***REMOVED*** Before assigning to procedure:
   credential = db.query(ProcedureCredential).filter(
       person_id == resident_id,
       procedure_id == procedure_id,
       status == 'active',
       (expiration_date IS NULL OR expiration_date >= today)
   )
   ```

3. **Minimum Competency** (Slot-type invariants)
   ```python
   ***REMOVED*** Hard constraints ensure minimum training
   "inpatient_call": {
       "hard": ["HIPAA", "Cyber_Training", "AUP", "Chaperone", "N95_Fit"]
   }
   ***REMOVED*** ALL must be valid for assignment
   ```

4. **Faculty Qualification** (Pre-assignment check)
   ```python
   is_qualified = credential_repo.is_faculty_qualified_for_procedure(
       person_id=faculty_id,
       procedure_id=procedure_id
   )
   ***REMOVED*** Returns: bool (True only if active + non-expired)
   ```

---

***REMOVED******REMOVED******REMOVED*** 9. SURVIVAL: Emergency Procedure Coverage

***REMOVED******REMOVED******REMOVED******REMOVED*** N-1 Contingency Coverage

**Current System:** Qualified faculty lookup supports emergency reassignment.

```python
def list_qualified_faculty_for_procedure(procedure_id: UUID) -> list[Person]:
    """
    Get all faculty qualified to supervise if primary faculty unavailable.

    Returns: Ordered list of faculty by competency
    - Filter: status='active', non-expired, person.type='faculty'
    """
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Emergency Assignment Logic (To Be Implemented)

```python
def get_emergency_supervisor_for_procedure(procedure_id: UUID) -> Person | None:
    """
    Find replacement supervisor if primary unavailable.

    Priority:
    1. 'master' competency level
    2. 'expert' competency level
    3. 'qualified' with most recent verification
    4. 'trainee' with explicit override flag
    """
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Coverage Gaps

| Gap | Mitigation |
|-----|-----------|
| All faculty on leave | Escalation to department head |
| No one with procedure credential | Cross-training or external consultant |
| Faculty suspended mid-procedure | Immediate supervisor notification |
| Expired credential during shift | Emergency credentialing protocol |

---

***REMOVED******REMOVED******REMOVED*** 10. STEALTH: Procedure Log Manipulation?

***REMOVED******REMOVED******REMOVED******REMOVED*** Security Controls

1. **Immutable Audit Trail**
   - `created_at`: Auto-set on insert, never updated
   - `updated_at`: Auto-updated by database trigger
   - All timestamps in UTC (not modifiable from application)

2. **Unique Constraints**
   ```sql
   UNIQUE (person_id, procedure_id)  -- Prevent duplicate credentials
   ```

3. **Foreign Key Integrity**
   ```sql
   FOREIGN KEY (person_id) REFERENCES people(id) ON DELETE CASCADE
   FOREIGN KEY (procedure_id) REFERENCES procedures(id) ON DELETE CASCADE
   -- Prevents orphaned credentials
   ```

4. **Status Validation**
   ```sql
   CHECK (status IN ('active', 'expired', 'suspended', 'pending'))
   -- Only valid states allowed
   ```

5. **Date Validation**
   ```python
   ***REMOVED*** Schema validation
   if expiration_date <= issued_date:
       raise ValueError("expiration_date must be after issued_date")
   ```

6. **Role-Based Access Control (RBAC)**
   - Only authenticated users can create/modify credentials
   - Coordinator role: Full credential management
   - Faculty role: View own credentials only
   - Admin role: Full audit access

***REMOVED******REMOVED******REMOVED******REMOVED*** Audit Logging (To Be Enhanced)

**Current:** created_at, updated_at timestamps
**Recommended Additions:**
- Who modified the credential (created_by, updated_by user IDs)
- Why suspension occurred (suspend_reason field)
- Audit event logging table with full change history

---

***REMOVED******REMOVED*** Procedure Category Reference

***REMOVED******REMOVED******REMOVED*** Surgical Procedures

| Procedure | Category | Specialty | Min PGY | Supervision |
|-----------|----------|-----------|---------|-------------|
| Mastectomy | surgical | Surgery | 2 | 1:1 |
| Vasectomy | surgical | Urology | 2 | 1:1 |
| Hysterectomy | surgical | OB/GYN | 2 | 1:1 |
| Cesarean section | surgical | OB/GYN | 2 | 1:1 |

***REMOVED******REMOVED******REMOVED*** Office Procedures

| Procedure | Category | Specialty | Min PGY | Supervision |
|-----------|----------|-----------|---------|-------------|
| Botox injection | office | Dermatology | 1 | 1:2 |
| IUD placement | office | Women's Health | 1 | 1:1 |
| Joint injection | office | Sports Medicine | 1 | 1:2 |
| Colposcopy | office | OB/GYN | 1 | 1:2 |

***REMOVED******REMOVED******REMOVED*** Obstetric Procedures

| Procedure | Category | Specialty | Min PGY | Supervision |
|-----------|----------|-----------|---------|-------------|
| Labor & delivery | obstetric | OB/GYN | 1 | 1:1 |
| Delivery (assisted) | obstetric | OB/GYN | 2 | 1:1 |
| Vacuum extraction | obstetric | OB/GYN | 2 | 1:1 |

***REMOVED******REMOVED******REMOVED*** Clinic Rotations

| Rotation | Category | Specialty | Min PGY | Supervision |
|----------|----------|-----------|---------|-------------|
| Sports medicine clinic | clinic | Sports Medicine | 1 | 1:2 |
| Pediatrics clinic | clinic | Pediatrics | 1 | 1:4 |
| General clinic | clinic | Internal Medicine | 1 | 1:3 |
| Women's health clinic | clinic | OB/GYN | 1 | 1:2 |

---

***REMOVED******REMOVED*** API Endpoints Summary

***REMOVED******REMOVED******REMOVED*** Credential Management

```
GET     /credentials/{credential_id}                 → Get credential by ID
GET     /credentials/by-person/{person_id}          → List person's credentials
GET     /credentials/by-procedure/{procedure_id}    → List procedure supervisors
GET     /credentials/qualified-faculty/{procedure_id} → Get qualified faculty
GET     /credentials/check/{person_id}/{procedure_id} → Check qualification
GET     /credentials/summary/{person_id}            → Faculty credential summary
GET     /credentials/expiring?days=30                → List expiring soon

POST    /credentials/                               → Create credential
POST    /credentials/{credential_id}/suspend        → Suspend credential
POST    /credentials/{credential_id}/activate       → Activate credential
POST    /credentials/{credential_id}/verify         → Verify credential

PUT     /credentials/{credential_id}                → Update credential
DELETE  /credentials/{credential_id}                → Delete credential
```

***REMOVED******REMOVED******REMOVED*** Procedure Management

```
GET     /procedures/{procedure_id}                  → Get procedure by ID
GET     /procedures?category=surgical               → List procedures
GET     /procedures?specialty=OB/GYN                → Filter by specialty
POST    /procedures/                               → Create procedure
PUT     /procedures/{procedure_id}                  → Update procedure
DELETE  /procedures/{procedure_id}                  → Deactivate procedure
```

---

***REMOVED******REMOVED*** Database Schema (Key Tables)

***REMOVED******REMOVED******REMOVED*** procedures Table

```sql
CREATE TABLE procedures (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    category VARCHAR(100),
    specialty VARCHAR(100),
    supervision_ratio INTEGER DEFAULT 1 CHECK (supervision_ratio >= 1),
    requires_certification BOOLEAN DEFAULT true,
    complexity_level VARCHAR(50) DEFAULT 'standard'
        CHECK (complexity_level IN ('basic', 'standard', 'advanced', 'complex')),
    min_pgy_level INTEGER DEFAULT 1 CHECK (min_pgy_level BETWEEN 1 AND 3),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_procedures_name ON procedures(name);
CREATE INDEX idx_procedures_specialty ON procedures(specialty);
CREATE INDEX idx_procedures_category ON procedures(category);
CREATE INDEX idx_procedures_active ON procedures(is_active);
```

***REMOVED******REMOVED******REMOVED*** procedure_credentials Table

```sql
CREATE TABLE procedure_credentials (
    id UUID PRIMARY KEY,
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    procedure_id UUID NOT NULL REFERENCES procedures(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'expired', 'suspended', 'pending')),
    competency_level VARCHAR(50) DEFAULT 'qualified'
        CHECK (competency_level IN ('trainee', 'qualified', 'expert', 'master')),
    issued_date DATE DEFAULT CURRENT_DATE,
    expiration_date DATE,
    last_verified_date DATE,
    max_concurrent_residents INTEGER,
    max_per_week INTEGER,
    max_per_academic_year INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    UNIQUE (person_id, procedure_id)
);

CREATE INDEX idx_credentials_person ON procedure_credentials(person_id);
CREATE INDEX idx_credentials_procedure ON procedure_credentials(procedure_id);
CREATE INDEX idx_credentials_status ON procedure_credentials(status);
CREATE INDEX idx_credentials_expiration ON procedure_credentials(expiration_date);
```

---

***REMOVED******REMOVED*** Audit Procedures & Compliance Checks

***REMOVED******REMOVED******REMOVED*** Monthly Credential Audit

```python
def audit_credentials(month: int, year: int) -> dict:
    """Generate monthly credential compliance report."""
    return {
        'total_credentials': count_all_active(),
        'expiring_this_month': count_expiring(month, year),
        'suspended': count_suspended(),
        'pending_verification': count_pending(),
        'faculty_without_required_credentials': find_gaps(),
        'overdue_verifications': list_unverified(days=365)
    }
```

***REMOVED******REMOVED******REMOVED*** Faculty Credential Validation

```python
def validate_faculty_credentials(person_id: UUID) -> dict:
    """
    Pre-assignment validation checklist.

    Returns:
    {
        'person_id': UUID,
        'can_work_inpatient_call': bool,        ***REMOVED*** Has all required credentials
        'can_work_procedures': bool,             ***REMOVED*** Has procedure credentials
        'expiring_soon': list[Procedure],        ***REMOVED*** Renewal needed
        'missing_required': list[str],           ***REMOVED*** ACGME gaps
        'recommendations': list[str]             ***REMOVED*** Remediation actions
    }
    """
```

***REMOVED******REMOVED******REMOVED*** ACGME Compliance Report

```python
def generate_acgme_compliance_report() -> dict:
    """Quarterly ACGME compliance verification."""
    return {
        'period': 'Q4 2025',
        'supervision_ratios_met': bool,
        'all_faculty_credentialed': bool,
        'no_suspended_supervisors': bool,
        'procedure_coverage': dict[procedure_id, faculty_count],
        'violations': list[str],
        'remediation_plan': str
    }
```

---

***REMOVED******REMOVED*** Key Takeaways

1. **Two-Table Architecture**
   - Procedures: What can be done
   - Credentials: Who can supervise

2. **Four Credential States**
   - active, expired, suspended, pending
   - Transitions managed through service layer

3. **Competency Progression**
   - trainee → qualified → expert → master
   - Tied to supervision capacity

4. **Slot-Type Invariants**
   - Hard constraints (must have)
   - Soft constraints (preferred, with penalties)
   - Enable dynamic eligibility assessment

5. **Audit Trail**
   - issued_date, last_verified_date, expiration_date
   - created_at, updated_at (immutable)
   - suspension_notes (why)

6. **Missing Pieces**
   - No explicit minimum case counting (opportunity)
   - No competency assessment scores
   - No proactive re-credentialing alerts (could add)

---

***REMOVED******REMOVED*** Next Steps for Implementation

***REMOVED******REMOVED******REMOVED*** Priority 1: Case Logging
- Create `procedure_case_logs` table
- Track: performed by, supervised by, case date, outcome
- Enable: minimum case enforcement, competency progression

***REMOVED******REMOVED******REMOVED*** Priority 2: Enhanced Auditing
- Add `created_by`, `updated_by` user IDs
- Implement audit event stream
- Enable: compliance investigation, change tracking

***REMOVED******REMOVED******REMOVED*** Priority 3: Proactive Alerts
- Dashboard: "Credentials expiring in 30/60/90 days"
- Email: Re-credentialing deadline reminders
- Escalation: Automatic supervisor notification if expired

***REMOVED******REMOVED******REMOVED*** Priority 4: Competency Scoring
- Numeric competency ratings (1-10 scale)
- Case-based progression milestones
- Automated graduation from trainee → qualified

---

**Document Prepared By:** G2_RECON (SEARCH_PARTY Operation)
**Completion Time:** 2025-12-30
**Codebase Scope:** Backend only (frontend integration TBD)
