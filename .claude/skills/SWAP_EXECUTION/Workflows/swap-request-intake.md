***REMOVED*** Swap Request Intake Workflow

Phase 1 of swap execution: Receive, parse, and normalize incoming swap requests.

***REMOVED******REMOVED*** Purpose

Transform raw API requests into structured, validated swap request objects ready for safety checks.

***REMOVED******REMOVED*** Inputs

Swap requests arrive via API endpoint:

```http
POST /api/swap/request
Content-Type: application/json
Authorization: Bearer {jwt_token}

{
  "source_faculty_id": "uuid-string",
  "source_week": "2025-02-03",
  "target_faculty_id": "uuid-string",
  "target_week": "2025-02-10",  // null for ABSORB swaps
  "swap_type": "one_to_one",    // or "absorb"
  "reason": "Conference attendance"
}
```

***REMOVED******REMOVED*** Intake Process

***REMOVED******REMOVED******REMOVED*** Step 1: Request Authentication

Verify the requestor has permission:

```python
***REMOVED*** Extract user from JWT token
current_user = get_current_user(token)

***REMOVED*** Verify authorization
if not (current_user.role in ["faculty", "admin", "coordinator"]):
    raise HTTPException(403, "Unauthorized to request swaps")

***REMOVED*** Verify source faculty matches requestor (unless admin)
if current_user.role != "admin":
    if str(current_user.person_id) != str(source_faculty_id):
        raise HTTPException(403, "Can only request swaps for yourself")
```

***REMOVED******REMOVED******REMOVED*** Step 2: Parse and Normalize

```python
from datetime import date
from uuid import UUID
from app.schemas.swap import SwapRequestCreate

***REMOVED*** Pydantic schema automatically validates:
***REMOVED*** - UUIDs are valid
***REMOVED*** - Dates are valid ISO format (YYYY-MM-DD)
***REMOVED*** - swap_type is valid enum
***REMOVED*** - Required fields are present

request_data = SwapRequestCreate(**request_json)
```

***REMOVED******REMOVED******REMOVED*** Step 3: Validate Request Components

Check basic data integrity:

```python
from app.services.swap_request_service import SwapRequestService

service = SwapRequestService(db)

***REMOVED*** 1. Verify source faculty exists and is active
source_faculty = service.get_faculty(request_data.source_faculty_id)
if not source_faculty:
    return {
        "valid": False,
        "error": "SOURCE_FACULTY_NOT_FOUND",
        "message": "Source faculty not found in system"
    }

***REMOVED*** 2. Verify target faculty exists and is active
target_faculty = service.get_faculty(request_data.target_faculty_id)
if not target_faculty:
    return {
        "valid": False,
        "error": "TARGET_FACULTY_NOT_FOUND",
        "message": "Target faculty not found in system"
    }

***REMOVED*** 3. Verify source and target are different people
if source_faculty.id == target_faculty.id:
    return {
        "valid": False,
        "error": "SELF_SWAP",
        "message": "Cannot swap with yourself"
    }

***REMOVED*** 4. Normalize week dates to Monday
source_week = normalize_to_monday(request_data.source_week)
if request_data.target_week:
    target_week = normalize_to_monday(request_data.target_week)
else:
    target_week = None

***REMOVED*** 5. Verify swap type matches week data
if request_data.swap_type == "one_to_one" and not target_week:
    return {
        "valid": False,
        "error": "INVALID_SWAP_TYPE",
        "message": "One-to-one swap requires target_week"
    }

if request_data.swap_type == "absorb" and target_week:
    return {
        "valid": False,
        "error": "INVALID_SWAP_TYPE",
        "message": "Absorb swap should not have target_week"
    }
```

***REMOVED******REMOVED******REMOVED*** Step 4: Record Request Metadata

Create a tracking record **before** validation:

```python
from datetime import datetime
from uuid import uuid4

***REMOVED*** Generate unique request ID
request_id = uuid4()

***REMOVED*** Record who requested and when
swap_request = SwapRecord(
    id=request_id,
    source_faculty_id=source_faculty.id,
    source_week=source_week,
    target_faculty_id=target_faculty.id,
    target_week=target_week,
    swap_type=request_data.swap_type,
    status=SwapStatus.PENDING,  ***REMOVED*** Not yet validated
    reason=request_data.reason,
    requested_at=datetime.utcnow(),
    requested_by_id=current_user.id,  ***REMOVED*** Who submitted the request
    notes=None
)

db.add(swap_request)
db.flush()  ***REMOVED*** Get ID without committing

logger.info(
    f"Swap request {request_id} created: "
    f"{source_faculty.name} week {source_week} → "
    f"{target_faculty.name} week {target_week or 'ABSORB'}"
)
```

***REMOVED******REMOVED******REMOVED*** Step 5: Create Structured Output

Return normalized request object:

```python
@dataclass
class StructuredSwapRequest:
    """Normalized swap request ready for validation."""

    request_id: UUID
    source_faculty: Person
    source_week: date
    target_faculty: Person
    target_week: date | None
    swap_type: SwapType
    reason: str | None
    requested_by: User
    requested_at: datetime

structured_request = StructuredSwapRequest(
    request_id=request_id,
    source_faculty=source_faculty,
    source_week=source_week,
    target_faculty=target_faculty,
    target_week=target_week,
    swap_type=SwapType(request_data.swap_type),
    reason=request_data.reason,
    requested_by=current_user,
    requested_at=swap_request.requested_at
)
```

***REMOVED******REMOVED*** Output Format

The structured request object contains:

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | UUID | Unique identifier for tracking |
| `source_faculty` | Person | Full Person object (eager loaded) |
| `source_week` | date | Monday of source week (normalized) |
| `target_faculty` | Person | Full Person object (eager loaded) |
| `target_week` | date \| None | Monday of target week, or None for ABSORB |
| `swap_type` | SwapType | ONE_TO_ONE or ABSORB enum |
| `reason` | str \| None | Requestor's explanation |
| `requested_by` | User | User object who submitted request |
| `requested_at` | datetime | UTC timestamp of request |

***REMOVED******REMOVED*** Common Validation Errors

***REMOVED******REMOVED******REMOVED*** Invalid UUIDs

**Input:**
```json
{"source_faculty_id": "not-a-uuid"}
```

**Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "source_faculty_id"],
      "msg": "value is not a valid uuid",
      "type": "type_error.uuid"
    }
  ]
}
```

***REMOVED******REMOVED******REMOVED*** Invalid Date Format

**Input:**
```json
{"source_week": "02/03/2025"}
```

**Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "source_week"],
      "msg": "invalid date format",
      "type": "value_error.date"
    }
  ]
}
```

***REMOVED******REMOVED******REMOVED*** Missing Required Fields

**Input:**
```json
{
  "source_faculty_id": "uuid-a"
  // Missing other required fields
}
```

**Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "source_week"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    ...
  ]
}
```

***REMOVED******REMOVED*** Week Normalization

**Always normalize week dates to Monday:**

```python
def normalize_to_monday(input_date: date) -> date:
    """
    Normalize any date within a week to the Monday of that week.

    Args:
        input_date: Any date within the target week

    Returns:
        Monday of the week containing input_date

    Example:
        normalize_to_monday(date(2025, 2, 5))  ***REMOVED*** Wednesday
        ***REMOVED*** Returns: date(2025, 2, 3)  ***REMOVED*** Monday
    """
    ***REMOVED*** weekday(): Mon=0, Tue=1, ..., Sun=6
    days_since_monday = input_date.weekday()
    monday = input_date - timedelta(days=days_since_monday)
    return monday
```

**Why normalize?**
- Consistent week identification
- Prevents ambiguity (which week is "Feb 5"?)
- Simplifies database queries
- Matches FMIT rotation structure (week-based)

***REMOVED******REMOVED*** Data Sanitization

Protect against injection and leaks:

```python
***REMOVED*** 1. Sanitize reason field (free text)
MAX_REASON_LENGTH = 500
reason = request_data.reason[:MAX_REASON_LENGTH] if request_data.reason else None

***REMOVED*** 2. Strip sensitive patterns
SENSITIVE_PATTERNS = [
    r'\b\d{3}-\d{2}-\d{4}\b',  ***REMOVED*** SSN
    r'\b[A-Z]\d{10}\b',         ***REMOVED*** Military ID
]
for pattern in SENSITIVE_PATTERNS:
    if reason and re.search(pattern, reason):
        logger.warning(f"Swap request {request_id} reason contains sensitive data")
        reason = "[REDACTED - contains sensitive information]"

***REMOVED*** 3. HTML escape to prevent XSS
from html import escape
reason = escape(reason) if reason else None
```

***REMOVED******REMOVED*** Logging Requirements

Log at each stage for audit trail:

```python
import logging
logger = logging.getLogger(__name__)

***REMOVED*** 1. Request received
logger.info(
    f"Swap request received from user {current_user.id} "
    f"for {source_faculty_id} week {source_week}"
)

***REMOVED*** 2. Validation passed
logger.info(
    f"Swap request {request_id} validated successfully"
)

***REMOVED*** 3. Proceeding to safety checks
logger.info(
    f"Swap request {request_id} entering safety check phase"
)

***REMOVED*** 4. Validation failed (WARNING level)
logger.warning(
    f"Swap request rejected: {error_code} - {error_message}",
    extra={
        "request_id": request_id,
        "source_faculty": source_faculty_id,
        "error_code": error_code
    }
)
```

**Do NOT log:**
- Full reason text (may contain sensitive info)
- User personal details beyond ID
- Target faculty details if request failed early

***REMOVED******REMOVED*** Next Phase

On successful intake, proceed to:
**[safety-checks.md](safety-checks.md)** - Validate swap against constraints

On intake failure, respond immediately:

```json
{
  "success": false,
  "request_id": "uuid",
  "error_code": "SOURCE_FACULTY_NOT_FOUND",
  "message": "Source faculty not found in system",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Key Functions

| Function | Purpose | Location |
|----------|---------|----------|
| `normalize_to_monday()` | Week normalization | `app/services/swap_request_service.py` |
| `get_faculty()` | Fetch and validate faculty | `app/services/swap_request_service.py` |
| `SwapRequestCreate` | Pydantic validation schema | `app/schemas/swap.py` |

***REMOVED******REMOVED******REMOVED*** Status Flow

```
[API Request]
    → Pydantic Validation
    → Entity Verification
    → PENDING SwapRecord Created
    → [Proceed to Safety Checks]
```
