# ACGME Procedure Credentialing Requirements

**Document Type:** SEARCH_PARTY Reconnaissance Report
**Target:** ACGME procedure credentialing requirements & tracking systems
**Scope:** Backend implementation analysis (models, services, repositories)
**Status:** Reconnaissance Complete
**Date:** 2025-12-30

---

## Executive Summary

The residency scheduler implements a comprehensive **procedure credentialing system** that tracks faculty qualifications to supervise medical procedures. The system enforces credential validity, manages competency levels, and integrates with slot-type invariants for assignment eligibility.

**Key Findings:**
- Dual-table architecture: `procedures` + `procedure_credentials`
- Four credential statuses with expiration tracking
- Four competency levels tied to supervision capacity
- Hard/soft constraint system for slot eligibility
- Complete audit trail with issued/verified/expiration dates

---

## SEARCH_PARTY Probe Results

### 1. PERCEPTION: Current Procedure Tracking

**Location:** `/backend/app/models/procedure.py`

#### Procedure Model Structure

```python
class Procedure(Base):
    """Represents a medical procedure requiring credentialed supervision."""

    __tablename__ = "procedures"

    # Core Fields
    id = GUID (PK)
    name: String(255) - unique, required
    description: Text (optional)

    # Categorization
    category: String(100)              # 'surgical', 'office', 'obstetric', 'clinic'
    specialty: String(100)             # 'Sports Medicine', 'OB/GYN', 'Dermatology'

    # Supervision Requirements
    supervision_ratio: Integer         # Max residents per faculty (default: 1)
    requires_certification: Boolean    # Must have explicit credential (default: True)

    # Complexity/Training
    complexity_level: String(50)       # 'basic', 'standard', 'advanced', 'complex'
    min_pgy_level: Integer             # Minimum PGY level to perform (default: 1)

    # Status
    is_active: Boolean                 # Soft-delete flag (default: True)

    # Timestamps
    created_at: DateTime (UTC)
    updated_at: DateTime (UTC)

    # Relationships
    credentials → ProcedureCredential[] (cascade delete)
```

#### Supported Procedure Categories

| Category | Examples | Supervision Ratio |
|----------|----------|-------------------|
| **surgical** | Mastectomy, Vasectomy, hysterectomy | 1:1 (faculty:resident) |
| **office** | Botox injection, IUD placement, joint injection | 1:2 to 1:1 |
| **obstetric** | Labor & delivery, cesarean section | 1:1 |
| **clinic** | Sports medicine clinic, peds clinic, general clinic | 1:2 to 1:4 |

#### Complexity Levels (Tied to Training)

| Level | Description | Min PGY | Supervision |
|-------|-------------|---------|-------------|
| **basic** | Simple, low-risk procedures | PGY-1 | Direct supervision |
| **standard** | Standard training procedures | PGY-1 | Direct/indirect supervision |
| **advanced** | Complex procedures requiring skill development | PGY-2 | Graduated responsibility |
| **complex** | High-risk, specialized procedures | PGY-3+ | Consultative/expert review |

---

### 2. INVESTIGATION: Credential → Procedure Mapping

**Location:** `/backend/app/models/procedure_credential.py`

#### ProcedureCredential Model Structure

```python
class ProcedureCredential(Base):
    """Faculty credential to supervise a specific procedure."""

    __tablename__ = "procedure_credentials"
    __unique_constraint__ = (person_id, procedure_id)  # One credential per pair

    # Core Fields
    id = GUID (PK)
    person_id = GUID (FK → people.id, CASCADE)
    procedure_id = GUID (FK → procedures.id, CASCADE)

    # Credential Status (4-state machine)
    status: String(50)
        ├─ 'active'      # Currently valid and usable
        ├─ 'expired'     # Manually marked expired
        ├─ 'suspended'   # Temporarily revoked
        └─ 'pending'     # Awaiting verification

    # Competency Level (4-tier proficiency)
    competency_level: String(50)
        ├─ 'trainee'     # Learning/supervised practice
        ├─ 'qualified'   # Competent independent performance (default)
        ├─ 'expert'      # Advanced skill level
        └─ 'master'      # Mastery/teaching level

    # Credentialing Timeline
    issued_date: Date                  # When credential granted
    expiration_date: Date (nullable)   # NULL = no expiration
    last_verified_date: Date           # Most recent verification

    # Supervision Capacity (overrides procedure defaults)
    max_concurrent_residents: Integer (nullable)  # NULL = use procedure default
    max_per_week: Integer (nullable)   # NULL = unlimited
    max_per_academic_year: Integer (nullable)   # NULL = unlimited

    # Audit Trail
    notes: Text                        # Suspension reasons, renewal notes, etc.
    created_at: DateTime (UTC)
    updated_at: DateTime (UTC)

    # Relationships
    person → Person
    procedure → Procedure

    # Computed Properties
    @property is_valid: bool
        Returns: status == 'active' AND (expiration_date is None OR today < expiration_date)

    @property is_expired: bool
        Returns: expiration_date is not None AND today >= expiration_date
```

#### Credential Status States & Transitions

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

#### Competency Level Implications

| Level | Training Stage | Supervision Type | Capacity Impact |
|-------|---|---|---|
| **trainee** | Early learning | 1:1 direct supervision | 50% capacity |
| **qualified** | Independent | 1:1 or 1:2 (procedure-dependent) | Full capacity |
| **expert** | Advanced mastery | 1:2-1:4 (flexible) | 125% capacity (can teach) |
| **master** | Teaching/mentorship | Consultative only | 150% capacity (teaching focus) |

---

### 3. ARCANA: Minimum Case Requirements

**Finding:** No explicit minimum case counting system currently implemented in procedure credentialing.

**However:** Slot-type invariant system provides implicit tracking through credential validity.

#### Credential Invariant Catalog (Proposed)

From `/backend/tests/integration/test_credential_invariants.py`:

```python
INVARIANT_CATALOG = {
    "inpatient_call": {
        "hard": [
            "HIPAA",           # Mandatory
            "Cyber_Training",  # Mandatory
            "AUP",             # Mandatory
            "Chaperone",       # Mandatory
            "N95_Fit"          # Mandatory
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

#### Eligibility Logic

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

    # Hard constraints - MUST PASS
    for req_cert_name in reqs.get("hard", []):
        cert = get_certification(person_id, req_cert_name)
        if not cert or not cert.is_valid or cert.expires_before(assignment_date):
            missing_credentials.append(req_cert_name)
            return (False, 0, missing_credentials)  # FAIL

    # Soft constraints - PENALTY if missing
    for soft in reqs.get("soft", []):
        if soft["name"] == "expiring_soon":
            if any_credential_expiring(person_id, soft["window_days"], assignment_date):
                penalty += soft["penalty"]

    return (True, penalty, [])  # SUCCESS
```

#### Minimum Case Tracking Strategy

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

### 4. HISTORY: Credentialing Evolution

**Migration:** `/backend/alembic/versions/007_add_procedure_credentialing.py`

#### Schema Constraints

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

#### Indexes for Performance

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

### 5. INSIGHT: Competency Assessment

**Service Layer:** `/backend/app/services/credential_service.py`

#### Competency Assessment Methods

```python
class CredentialService:

    def get_faculty_credential_summary(person_id: UUID) -> dict:
        """
        Returns:
        {
            'person_id': UUID,
            'person_name': str,
            'total_credentials': int,          # All-time credential count
            'active_credentials': int,         # Currently valid
            'expiring_soon': int,              # Expiring within 30 days
            'procedures': list[Procedure],     # All qualified procedures
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

#### Verification Workflow

```python
def verify_credential(credential_id: UUID) -> dict:
    """
    Mark credential as verified today.
    Updates: last_verified_date = date.today()

    ACGME compliance: Credentials should be re-verified periodically
    (typically annually for medical credentials)
    """
```

#### Suspension Lifecycle

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

### 6. RELIGION: All Procedures Logged?

**Current Implementation:** YES - Procedure must be registered in database.

#### Procedure Registration Flow

```python
# Routes: POST /api/procedures
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

    # Database constraint enforces unique procedure name
```

#### Credential Assignment Flow

```
User creates Procedure → Faculty earns credential →
    Credential tracked with dates & competency →
        Used in assignment slot eligibility checks
```

#### Audit Trail

All procedures and credentials have:
- `created_at`: When registered (UTC)
- `updated_at`: When last modified (UTC)
- For credentials: `last_verified_date` (re-certification tracking)

---

### 7. NATURE: Over-Documentation?

**Analysis:** System is appropriately detailed, not over-documented.

#### What's Tracked

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

#### What's NOT Tracked (Could Be Considered)

- **Case counts**: No explicit minimum case logging → OPPORTUNITY
- **Remediation history**: Only current status stored → Could track suspension timeline
- **Competency assessment scores**: Boolean is_valid only → Could track numerical proficiency ratings
- **Re-credentialing deadlines**: Expiration tracked, but no pre-renewal warnings → Could add proactive alerts

---

### 8. MEDICINE: Patient Safety Requirements

#### ACGME Standards Enforced

1. **Supervision Ratios** (Procedure-level)
   ```python
   supervision_ratio = 1  # 1:1 = one faculty per resident
   supervision_ratio = 2  # 1:2 = one faculty per two residents
   ```
   Enforced by: `Procedure.supervision_ratio` field

2. **Credential Validity** (Assignment-level)
   ```python
   # Before assigning to procedure:
   credential = db.query(ProcedureCredential).filter(
       person_id == resident_id,
       procedure_id == procedure_id,
       status == 'active',
       (expiration_date IS NULL OR expiration_date >= today)
   )
   ```

3. **Minimum Competency** (Slot-type invariants)
   ```python
   # Hard constraints ensure minimum training
   "inpatient_call": {
       "hard": ["HIPAA", "Cyber_Training", "AUP", "Chaperone", "N95_Fit"]
   }
   # ALL must be valid for assignment
   ```

4. **Faculty Qualification** (Pre-assignment check)
   ```python
   is_qualified = credential_repo.is_faculty_qualified_for_procedure(
       person_id=faculty_id,
       procedure_id=procedure_id
   )
   # Returns: bool (True only if active + non-expired)
   ```

---

### 9. SURVIVAL: Emergency Procedure Coverage

#### N-1 Contingency Coverage

**Current System:** Qualified faculty lookup supports emergency reassignment.

```python
def list_qualified_faculty_for_procedure(procedure_id: UUID) -> list[Person]:
    """
    Get all faculty qualified to supervise if primary faculty unavailable.

    Returns: Ordered list of faculty by competency
    - Filter: status='active', non-expired, person.type='faculty'
    """
```

#### Emergency Assignment Logic (To Be Implemented)

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

#### Coverage Gaps

| Gap | Mitigation |
|-----|-----------|
| All faculty on leave | Escalation to department head |
| No one with procedure credential | Cross-training or external consultant |
| Faculty suspended mid-procedure | Immediate supervisor notification |
| Expired credential during shift | Emergency credentialing protocol |

---

### 10. STEALTH: Procedure Log Manipulation?

#### Security Controls

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
   # Schema validation
   if expiration_date <= issued_date:
       raise ValueError("expiration_date must be after issued_date")
   ```

6. **Role-Based Access Control (RBAC)**
   - Only authenticated users can create/modify credentials
   - Coordinator role: Full credential management
   - Faculty role: View own credentials only
   - Admin role: Full audit access

#### Audit Logging (To Be Enhanced)

**Current:** created_at, updated_at timestamps
**Recommended Additions:**
- Who modified the credential (created_by, updated_by user IDs)
- Why suspension occurred (suspend_reason field)
- Audit event logging table with full change history

---

## Procedure Category Reference

### Surgical Procedures

| Procedure | Category | Specialty | Min PGY | Supervision |
|-----------|----------|-----------|---------|-------------|
| Mastectomy | surgical | Surgery | 2 | 1:1 |
| Vasectomy | surgical | Urology | 2 | 1:1 |
| Hysterectomy | surgical | OB/GYN | 2 | 1:1 |
| Cesarean section | surgical | OB/GYN | 2 | 1:1 |

### Office Procedures

| Procedure | Category | Specialty | Min PGY | Supervision |
|-----------|----------|-----------|---------|-------------|
| Botox injection | office | Dermatology | 1 | 1:2 |
| IUD placement | office | Women's Health | 1 | 1:1 |
| Joint injection | office | Sports Medicine | 1 | 1:2 |
| Colposcopy | office | OB/GYN | 1 | 1:2 |

### Obstetric Procedures

| Procedure | Category | Specialty | Min PGY | Supervision |
|-----------|----------|-----------|---------|-------------|
| Labor & delivery | obstetric | OB/GYN | 1 | 1:1 |
| Delivery (assisted) | obstetric | OB/GYN | 2 | 1:1 |
| Vacuum extraction | obstetric | OB/GYN | 2 | 1:1 |

### Clinic Rotations

| Rotation | Category | Specialty | Min PGY | Supervision |
|----------|----------|-----------|---------|-------------|
| Sports medicine clinic | clinic | Sports Medicine | 1 | 1:2 |
| Pediatrics clinic | clinic | Pediatrics | 1 | 1:4 |
| General clinic | clinic | Internal Medicine | 1 | 1:3 |
| Women's health clinic | clinic | OB/GYN | 1 | 1:2 |

---

## API Endpoints Summary

### Credential Management

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

### Procedure Management

```
GET     /procedures/{procedure_id}                  → Get procedure by ID
GET     /procedures?category=surgical               → List procedures
GET     /procedures?specialty=OB/GYN                → Filter by specialty
POST    /procedures/                               → Create procedure
PUT     /procedures/{procedure_id}                  → Update procedure
DELETE  /procedures/{procedure_id}                  → Deactivate procedure
```

---

## Database Schema (Key Tables)

### procedures Table

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

### procedure_credentials Table

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

## Audit Procedures & Compliance Checks

### Monthly Credential Audit

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

### Faculty Credential Validation

```python
def validate_faculty_credentials(person_id: UUID) -> dict:
    """
    Pre-assignment validation checklist.

    Returns:
    {
        'person_id': UUID,
        'can_work_inpatient_call': bool,        # Has all required credentials
        'can_work_procedures': bool,             # Has procedure credentials
        'expiring_soon': list[Procedure],        # Renewal needed
        'missing_required': list[str],           # ACGME gaps
        'recommendations': list[str]             # Remediation actions
    }
    """
```

### ACGME Compliance Report

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

## Key Takeaways

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

## Next Steps for Implementation

### Priority 1: Case Logging
- Create `procedure_case_logs` table
- Track: performed by, supervised by, case date, outcome
- Enable: minimum case enforcement, competency progression

### Priority 2: Enhanced Auditing
- Add `created_by`, `updated_by` user IDs
- Implement audit event stream
- Enable: compliance investigation, change tracking

### Priority 3: Proactive Alerts
- Dashboard: "Credentials expiring in 30/60/90 days"
- Email: Re-credentialing deadline reminders
- Escalation: Automatic supervisor notification if expired

### Priority 4: Competency Scoring
- Numeric competency ratings (1-10 scale)
- Case-based progression milestones
- Automated graduation from trainee → qualified

---

**Document Prepared By:** G2_RECON (SEARCH_PARTY Operation)
**Completion Time:** 2025-12-30
**Codebase Scope:** Backend only (frontend integration TBD)
