# Role-Based View Filtering System

This document describes the role-based filtering system that enables different user types to access only the data they are authorized to see.

## Overview

The role-based filtering system provides fine-grained access control for different user types in the Autonomous Assignment Program Manager. It implements the role definitions from `PROJECT_STATUS_ASSESSMENT.md`:

| Role | Sees | Hidden |
|------|------|--------|
| admin | Everything | - |
| coordinator | Schedules, people, conflicts | User management |
| faculty | Own schedule, swap requests | Other faculty details |
| rn/lpn/msa | Today's manifest, call roster | Academic blocks, compliance |

## Supported Roles

### Administrative Roles
- **admin**: Full system access including user management, compliance, and audit logs
- **coordinator**: Can manage schedules, people, and handle conflicts (no user management)

### Medical Staff Roles
- **faculty**: Can view their own schedule and participate in swap requests
- **resident**: Can view own schedule, manage swaps, and view conflicts

### Clinical Staff Roles
- **clinical_staff**: Unified role for clinical support staff
- **rn**: Registered Nurse (same permissions as clinical_staff)
- **lpn**: Licensed Practical Nurse (same permissions as clinical_staff)
- **msa**: Medical Support Assistant (same permissions as clinical_staff)

All clinical staff roles can view:
- Today's daily manifest
- Call roster

Clinical staff roles cannot view:
- Academic blocks
- Compliance data
- Other faculty details

## Components

### 1. RoleFilterService

Main service class providing role-based filtering capabilities.

**Location**: `backend/app/services/role_filter_service.py`

#### Key Methods

```python
# Check resource access
RoleFilterService.can_access(resource: ResourceType, role: str | UserRole) -> bool

# Filter response data
RoleFilterService.filter_for_role(
    data: Dict[str, Any],
    role: str | UserRole,
    user_id: Optional[str] = None
) -> Dict[str, Any]

# Filter schedule lists
RoleFilterService.filter_schedule_list(
    schedules: List[Dict[str, Any]],
    role: str | UserRole,
    user_id: Optional[str] = None,
    today_only: bool = False
) -> List[Dict[str, Any]]

# Check endpoint access
RoleFilterService.can_access_endpoint(
    role: str | UserRole,
    endpoint_category: str
) -> bool

# Get role information
RoleFilterService.get_role_description(role: str | UserRole) -> Dict[str, Any]
RoleFilterService.get_accessible_resources(role: str | UserRole) -> List[str]
```

### 2. FastAPI Dependencies

Dependency injection functions for use in route handlers.

**Location**: `backend/app/api/dependencies/role_filter.py`

#### Available Dependencies

```python
# Require access to specific resource
require_resource_access(ResourceType.SCHEDULES)

# Require admin role
require_admin()

# Check endpoint category access
check_endpoint_access("compliance")

# Get current user's role
get_current_user_role()
```

### 3. User Model Updates

The User model has been updated to support new clinical staff roles.

**Location**: `backend/app/models/user.py`

New properties:
- `is_clinical_staff`: Check if user is any clinical staff type
- `is_faculty`: Check if user is faculty
- `is_resident`: Check if user is resident

### 4. Database Migration

Migration to update the user role constraint.

**Location**: `backend/alembic/versions/012_add_clinical_staff_roles.py`

## Usage Examples

### Example 1: Filtering Dashboard Data

```python
from fastapi import APIRouter, Depends
from app.core.security import get_current_active_user
from app.models.user import User
from app.services.role_filter_service import RoleFilterService

router = APIRouter()

@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_active_user)
):
    # Build complete data
    raw_data = {
        "schedules": [...],
        "compliance": {...},
        "users": [...],
        "manifest": [...],
    }

    # Filter based on role
    filtered_data = RoleFilterService.filter_for_role(
        raw_data,
        current_user.role,
        str(current_user.id)
    )

    return filtered_data
```

### Example 2: Requiring Resource Access

```python
from fastapi import APIRouter, Depends
from app.api.dependencies.role_filter import require_resource_access
from app.services.role_filter_service import ResourceType

router = APIRouter()

@router.get("/compliance/report")
async def get_compliance(
    _: None = Depends(require_resource_access(ResourceType.COMPLIANCE))
):
    # Only admin can access this
    return {"compliance_data": "..."}
```

### Example 3: Admin-Only Endpoints

```python
from fastapi import APIRouter, Depends
from app.api.dependencies.role_filter import require_admin

router = APIRouter()

@router.post("/users")
async def create_user(
    username: str,
    email: str,
    _: None = Depends(require_admin())
):
    # Only admin can create users
    return {"user": "created"}
```

### Example 4: Filtering Schedule Lists

```python
from app.services.role_filter_service import RoleFilterService

# Get all schedules from database
all_schedules = [...]

# Filter based on user role
filtered_schedules = RoleFilterService.filter_schedule_list(
    all_schedules,
    current_user.role,
    str(current_user.id),
    today_only=False  # Set to True for clinical staff view
)
```

### Example 5: Checking Access Programmatically

```python
from app.services.role_filter_service import RoleFilterService, ResourceType

# Check if user can access a resource
if RoleFilterService.can_access(ResourceType.COMPLIANCE, user.role):
    # Show compliance data
    pass

# Check if user can access an endpoint category
if RoleFilterService.can_access_endpoint(user.role, "schedules"):
    # Allow access
    pass

# Check if user is admin
if RoleFilterService.is_admin(user.role):
    # Admin-only functionality
    pass

# Check if user is clinical staff
if RoleFilterService.is_clinical_staff(user.role):
    # Show today's manifest
    pass
```

### Example 6: Getting Role Information

```python
from app.services.role_filter_service import RoleFilterService

# Get role description
description = RoleFilterService.get_role_description("rn")
# Returns:
# {
#     "role": "rn",
#     "title": "Registered Nurse",
#     "sees": "Today's manifest, call roster",
#     "hidden": "Academic blocks, compliance",
#     "description": "...",
#     "permissions": ["manifest", "call_roster"]
# }

# Get accessible resources for a role
resources = RoleFilterService.get_accessible_resources("coordinator")
# Returns: ["schedules", "people", "conflicts", "own_schedule", ...]
```

## Resource Types

The following resource types are defined in `ResourceType` enum:

- `SCHEDULES`: Full schedule access (admin, coordinator)
- `PEOPLE`: People/faculty management
- `CONFLICTS`: Conflict viewing and management
- `USERS`: User management (admin only)
- `COMPLIANCE`: Compliance data (admin only)
- `AUDIT`: Audit logs (admin only)
- `OWN_SCHEDULE`: User's own schedule (faculty, resident)
- `SWAPS`: Swap management (faculty, resident)
- `MANIFEST`: Daily manifest (clinical staff)
- `CALL_ROSTER`: Call roster (clinical staff)
- `ACADEMIC_BLOCKS`: Academic block planning

## Permission Matrix

| Role | Schedules | People | Conflicts | Users | Compliance | Audit | Own Schedule | Swaps | Manifest | Call Roster | Academic Blocks |
|------|-----------|--------|-----------|-------|------------|-------|--------------|-------|----------|-------------|-----------------|
| admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| coordinator | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| faculty | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |
| resident | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |
| rn/lpn/msa | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ |

## Testing

Comprehensive test suite available at:
`backend/tests/services/test_role_filter_service.py`

Run tests:
```bash
pytest backend/tests/services/test_role_filter_service.py -v
```

## Database Migration

To apply the new role constraints to the database:

```bash
cd backend
alembic upgrade head
```

This will run migration `012_add_clinical_staff_roles` which updates the user role check constraint.

## Integration with Existing Code

The RoleFilterService can be integrated with existing route handlers:

1. Import the service or dependencies:
   ```python
   from app.services.role_filter_service import RoleFilterService
   from app.api.dependencies.role_filter import require_resource_access
   ```

2. Apply filtering to responses:
   ```python
   filtered_data = RoleFilterService.filter_for_role(data, user.role, user_id)
   ```

3. Add access control to routes:
   ```python
   @router.get("/protected")
   async def protected_route(
       _: None = Depends(require_resource_access(ResourceType.COMPLIANCE))
   ):
       pass
   ```

## API Examples

See `backend/app/api/routes/role_filter_example.py` for complete working examples of:
- Dashboard filtering
- Schedule access control
- Manifest endpoints
- Compliance reports
- User management
- Access checking

## Security Considerations

1. **Default Deny**: If a role is not explicitly granted access, it is denied
2. **User ID Required**: For "own schedule" filtering, user ID must be provided
3. **Clinical Staff Normalization**: RN/LPN/MSA roles are normalized to clinical_staff for permission checks
4. **String Safety**: Invalid role strings return empty permissions rather than errors

## Future Enhancements

Potential future additions:
- Row-level security (RLS) integration with PostgreSQL
- Fine-grained permission system (beyond role-based)
- Time-based access restrictions
- Audit logging for access attempts
- Dynamic permission management via database

## Support

For questions or issues:
1. Check the test file for usage examples
2. Review the example routes file
3. Consult PROJECT_STATUS_ASSESSMENT.md for role definitions
