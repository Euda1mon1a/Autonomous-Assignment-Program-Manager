# Faculty Bulk Endpoints Implementation

**Status:** Partially Complete
**Date:** 2026-01-04
**Mission:** Create batch operation endpoints for people (faculty/residents) management

## What Was Completed

### 1. Batch Schemas (/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/schemas/person.py) ✅

Added complete batch operation schemas following the rotation_templates.py pattern:

- `BatchPersonCreateRequest` - Create up to 100 people atomically
- `BatchPersonUpdateRequest` - Update up to 100 people atomically
- `BatchPersonDeleteRequest` - Delete up to 100 people atomically
- `BatchPersonResponse` - Unified response schema
- `BatchOperationResult` - Per-item result tracking
- `BatchPersonUpdateItem` - Single update item wrapper

All schemas include:
- max_length=100 limit on batch size
- dry_run support for validation
- Proper field validation via Pydantic

### 2. Reference Implementation (/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/services/person_service_batch.py) ✅

Created standalone reference file with complete batch methods:

- `batch_create()` - Atomic batch creation with duplicate email detection
- `batch_update()` - Atomic batch updates
- `batch_delete()` - Atomic batch deletions

All methods follow the pattern:
1. Phase 1: Validate all items (fail fast if any invalid)
2. Phase 2: Execute operations (only if dry_run=False)
3. Return detailed results with per-item success/error tracking

## What Needs to Be Done

### 1. Add Batch Methods to PersonService

Copy the three methods from `person_service_batch.py` into `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/services/person_service.py` after the `delete_person()` method.

Add this section marker:
```python
# =========================================================================
# Batch Operations
# =========================================================================
```

Then copy `batch_create()`, `batch_update()`, and `batch_delete()` methods.

### 2. Add Batch Methods to PersonController

Add to `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/controllers/person_controller.py` after the `delete_person()` method:

```python
# =========================================================================
# Batch Operations
# =========================================================================

def batch_create_people(self, people_data: list[dict], dry_run: bool = False) -> dict:
    """Batch create multiple people atomically."""
    try:
        result = self.service.batch_create(people_data, dry_run)

        if result["failed"] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Batch create operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

def batch_update_people(self, updates: list[dict], dry_run: bool = False) -> dict:
    """Batch update multiple people atomically."""
    try:
        result = self.service.batch_update(updates, dry_run)

        if result["failed"] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Batch update operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

def batch_delete_people(self, person_ids: list[UUID], dry_run: bool = False) -> dict:
    """Batch delete multiple people atomically."""
    try:
        result = self.service.batch_delete(person_ids, dry_run)

        if result["failed"] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Batch delete operation failed",
                    "failed": result["failed"],
                    "results": result["results"],
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
```

### 3. Add Batch Imports to Routes

Update `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/api/routes/people.py` imports:

```python
from app.schemas.person import (
    BatchPersonCreateRequest,
    BatchPersonDeleteRequest,
    BatchPersonResponse,
    BatchPersonUpdateRequest,
    PersonCreate,
    PersonListResponse,
    PersonResponse,
    PersonUpdate,
)
```

### 4. Add Batch Endpoints to Routes

Add to `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/backend/app/api/routes/people.py` at the end:

```python
# ============================================================================
# Batch operations for people
# ============================================================================


@router.post("/batch", response_model=BatchPersonResponse, status_code=201)
async def batch_create_people(
    request: BatchPersonCreateRequest,
    response: Response,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch create multiple people atomically.

    Features:
    - Create up to 100 people at once
    - Dry-run mode for validation without creating
    - Atomic operation (all or nothing)
    - Duplicate email detection within batch and database
    - Validates resident PGY level requirements

    Args:
        request: BatchPersonCreateRequest with list of people to create
        response: FastAPI Response object for adding headers
        db: Database session
        current_user: Authenticated user

    Returns:
        BatchPersonResponse with operation results

    Security:
        Requires authentication

    PHI Warning:
        This endpoint creates Protected Health Information (PHI).
        X-Contains-PHI header is set.
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)

    # Convert Pydantic models to dicts
    people_data = [person.model_dump() for person in request.people]

    return controller.batch_create_people(people_data, request.dry_run)


@router.put("/batch", response_model=BatchPersonResponse)
async def batch_update_people(
    request: BatchPersonUpdateRequest,
    response: Response,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch update multiple people atomically.

    Features:
    - Update up to 100 people at once
    - Dry-run mode for validation without updating
    - Atomic operation (all or nothing)
    - Per-person update tracking
    """
    # Add PHI warning headers
    response.headers["X-Contains-PHI"] = "true"
    response.headers["X-PHI-Fields"] = "name,email"

    controller = PersonController(db)

    # Convert Pydantic models to dicts
    updates = [
        {
            "person_id": item.person_id,
            "updates": item.updates.model_dump(exclude_unset=True),
        }
        for item in request.people
    ]

    return controller.batch_update_people(updates, request.dry_run)


@router.delete("/batch", response_model=BatchPersonResponse)
async def batch_delete_people(
    request: BatchPersonDeleteRequest,
    db=Depends(get_async_db),
    current_user: User = Depends(get_current_active_user),
):
    """Batch delete multiple people atomically.

    Features:
    - Delete up to 100 people at once
    - Dry-run mode for validation without deleting
    - Atomic operation (all or nothing)
    - Validates all people exist before deletion
    """
    controller = PersonController(db)
    return controller.batch_delete_people(request.person_ids, request.dry_run)
```

## API Endpoints Created

Once implementation is complete, these endpoints will be available:

- `POST /api/people/batch` - Batch create people
- `PUT /api/people/batch` - Batch update people
- `DELETE /api/people/batch` - Batch delete people

All endpoints support:
- Batch size: 1-100 items
- Dry-run mode
- Atomic transactions
- PHI warning headers
- Authentication required

## Example Usage

### Batch Create
```json
POST /api/people/batch
{
    "people": [
        {
            "name": "Dr. John Smith",
            "type": "faculty",
            "email": "john.smith@example.com",
            "specialties": ["Family Medicine"]
        },
        {
            "name": "Jane Doe",
            "type": "resident",
            "pgy_level": 1,
            "email": "jane.doe@example.com"
        }
    ],
    "dry_run": false
}
```

### Batch Update
```json
PUT /api/people/batch
{
    "people": [
        {
            "person_id": "550e8400-e29b-41d4-a716-446655440000",
            "updates": {
                "email": "newemail@example.com",
                "specialties": ["Family Medicine", "Sports Medicine"]
            }
        }
    ],
    "dry_run": false
}
```

### Batch Delete
```json
DELETE /api/people/batch
{
    "person_ids": [
        "550e8400-e29b-41d4-a716-446655440000",
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    ],
    "dry_run": false
}
```

## Files Modified

1. `/backend/app/schemas/person.py` - Added batch schemas (COMPLETE)
2. `/backend/app/services/person_service_batch.py` - Reference implementation (COMPLETE)
3. `/backend/app/services/person_service.py` - Needs batch methods added
4. `/backend/app/controllers/person_controller.py` - Needs batch methods added
5. `/backend/app/api/routes/people.py` - Needs batch endpoints added

## Testing

Once complete, test with:

```bash
# Run person-related tests
docker exec residency-scheduler-backend pytest tests/ -k "person" -v

# Test batch schemas
docker exec residency-scheduler-backend python -c "
from app.schemas.person import BatchPersonCreateRequest, PersonCreate
batch = BatchPersonCreateRequest(
    people=[PersonCreate(name='Test', type='faculty')],
    dry_run=True
)
print('Schemas work!')
"
```

## Architecture Followed

This implementation follows the established layered architecture pattern from `rotation_templates.py`:

1. **Schemas (Pydantic)** - Request/response validation
2. **Service Layer** - Business logic, atomic transactions
3. **Controller Layer** - HTTP exception handling
4. **Route Layer** - Thin routing, PHI headers, auth

All batch operations are:
- Atomic (all-or-nothing)
- Support dry-run mode
- Provide per-item result tracking
- Follow the 100-item batch limit
- Include duplicate detection (for creates)
