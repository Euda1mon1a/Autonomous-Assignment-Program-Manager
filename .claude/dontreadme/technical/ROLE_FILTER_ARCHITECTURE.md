# Role-Based Filtering System - Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT REQUEST (with JWT Token)                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Route Handler                           │
│  @router.get("/dashboard")                                              │
│  def get_dashboard(                                                     │
│      current_user: User = Depends(get_current_active_user),            │
│      _: None = Depends(require_resource_access(ResourceType.SCHEDULES))│
│  ):                                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                        │                              │
                        │                              ▼
                        │                   ┌─────────────────────────┐
                        │                   │ Role Filter Dependency  │
                        │                   │ - require_resource_...  │
                        │                   │ - require_admin()       │
                        │                   │ - check_endpoint_...    │
                        │                   └─────────────────────────┘
                        │                              │
                        │                              ▼
                        │                   ┌─────────────────────────┐
                        │                   │  Access Check           │
                        │                   │  (403 if denied)        │
                        │                   └─────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Build Raw Response Data                         │
│  data = {                                                               │
│      "schedules": [...],                                                │
│      "people": [...],                                                   │
│      "compliance": {...},                                               │
│      "users": [...],                                                    │
│      "manifest": [...],                                                 │
│      "call_roster": [...]                                               │
│  }                                                                      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      RoleFilterService.filter_for_role()                │
│  - Check user's role permissions                                        │
│  - Filter out unauthorized fields                                       │
│  - Apply role-specific logic                                            │
│  - Filter to own data if needed                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌───────────────┐ ┌─────────────┐ ┌──────────────────┐
        │  Admin Role   │ │Coordinator  │ │ Clinical Staff   │
        │  (see all)    │ │ (filtered)  │ │ (today only)     │
        └───────────────┘ └─────────────┘ └──────────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Filtered Response Data                          │
│  Role-appropriate subset of original data                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT RECEIVES RESPONSE                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Layers

### Layer 1: User Model & Database
```
User Model (models/user.py)
├── role: String (admin, coordinator, faculty, rn, lpn, msa, clinical_staff, resident)
├── is_admin: bool property
├── is_coordinator: bool property
├── is_clinical_staff: bool property
├── is_faculty: bool property
└── is_resident: bool property

Database Constraint (migration 012)
└── CHECK (role IN ('admin', 'coordinator', 'faculty', 'clinical_staff', 'rn', 'lpn', 'msa', 'resident'))
```

### Layer 2: Role Filter Service
```
RoleFilterService (services/role_filter_service.py)
│
├── UserRole Enum
│   ├── ADMIN
│   ├── COORDINATOR
│   ├── FACULTY
│   ├── RESIDENT
│   ├── CLINICAL_STAFF
│   ├── RN
│   ├── LPN
│   └── MSA
│
├── ResourceType Enum
│   ├── SCHEDULES
│   ├── PEOPLE
│   ├── CONFLICTS
│   ├── USERS
│   ├── COMPLIANCE
│   ├── AUDIT
│   ├── OWN_SCHEDULE
│   ├── SWAPS
│   ├── MANIFEST
│   ├── CALL_ROSTER
│   └── ACADEMIC_BLOCKS
│
└── Methods
    ├── can_access(resource, role) → bool
    ├── filter_for_role(data, role, user_id) → Dict
    ├── filter_schedule_list(schedules, role, user_id) → List
    ├── can_access_endpoint(role, category) → bool
    ├── get_permissions(role) → Set[ResourceType]
    ├── get_accessible_resources(role) → List[str]
    ├── is_admin(role) → bool
    ├── is_clinical_staff(role) → bool
    └── get_role_description(role) → Dict
```

### Layer 3: FastAPI Dependencies
```
Dependencies (api/dependencies/role_filter.py)
│
├── require_resource_access(resource: ResourceType)
│   └── Raises 403 if user lacks access
│
├── require_admin()
│   └── Raises 403 if user is not admin
│
├── check_endpoint_access(category: str)
│   └── Raises 403 if user lacks category access
│
├── get_current_user_role()
│   └── Returns user's role string
│
└── apply_role_filter(data, user)
    └── Applies filtering and returns filtered data
```

### Layer 4: API Routes
```
Route Handlers (api/routes/*.py)
│
├── Protected with dependencies
│   @router.get("/compliance")
│   def get_compliance(
│       _: None = Depends(require_resource_access(ResourceType.COMPLIANCE))
│   ):
│       return data
│
├── With manual filtering
│   @router.get("/dashboard")
│   def get_dashboard(current_user: User = Depends(get_current_active_user)):
│       data = {...}
│       return RoleFilterService.filter_for_role(data, current_user.role, user_id)
│
└── Admin-only endpoints
    @router.post("/users")
    def create_user(_: None = Depends(require_admin())):
        return user
```

## Permission Flow

### Admin User Request
```
Client → Route → Auth Check → RoleFilterService
                   ✓              ↓
                            All permissions granted
                                  ↓
                            Full data returned
```

### Coordinator User Request
```
Client → Route → Auth Check → RoleFilterService
                   ✓              ↓
                            Check permissions
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
              Allow: schedules            Deny: users
                    people                     compliance
                    conflicts                  audit
                    ↓
              Filtered data returned
```

<<<<<<< HEAD
### Faculty User Request
=======
##***REMOVED*** User Request
>>>>>>> origin/docs/session-14-summary
```
Client → Route → Auth Check → RoleFilterService
                   ✓              ↓
                            Check permissions
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
              Allow: own_schedule        Deny: schedules (all)
                    swaps                     people
                    ↓                         compliance
              Filter to own data               users
                    ↓
              Own data only returned
```

### Clinical Staff (RN/LPN/MSA) Request
```
Client → Route → Auth Check → RoleFilterService
                   ✓              ↓
                            Normalize role
                            (rn/lpn/msa → clinical_staff)
                                  ↓
                            Check permissions
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
              Allow: manifest            Deny: schedules
                    call_roster               academic_blocks
                    ↓                         compliance
              Today's data only                people
                    ↓
              Manifest + roster returned
```

## Permission Matrix

| Resource | Admin | Coordinator | Faculty | Resident | Clinical Staff |
|----------|-------|-------------|---------|----------|----------------|
| schedules | ✓ | ✓ | ✗ | ✗ | ✗ |
| people | ✓ | ✓ | ✗ | ✗ | ✗ |
| conflicts | ✓ | ✓ | ✗ | ✓ | ✗ |
| users | ✓ | ✗ | ✗ | ✗ | ✗ |
| compliance | ✓ | ✗ | ✗ | ✗ | ✗ |
| audit | ✓ | ✗ | ✗ | ✗ | ✗ |
| own_schedule | ✓ | ✓ | ✓ | ✓ | ✗ |
| swaps | ✓ | ✓ | ✓ | ✓ | ✗ |
| manifest | ✓ | ✓ | ✗ | ✗ | ✓ |
| call_roster | ✓ | ✓ | ✗ | ✗ | ✓ |
| academic_blocks | ✓ | ✓ | ✗ | ✗ | ✗ |

## Data Flow Examples

### Example 1: Admin Dashboard Request
```
1. Request: GET /api/dashboard
   Headers: Authorization: Bearer <admin_jwt>

2. Auth: Extract user from JWT → User(role='admin')

3. Build data:
   {
     "schedules": [...],
     "compliance": {...},
     "users": [...],
     "manifest": [...]
   }

4. Filter: RoleFilterService.filter_for_role(data, 'admin')
   Result: All data passes through (no filtering)

5. Response: Complete data returned
```

### Example 2: Faculty Schedule Request
```
1. Request: GET /api/my-schedule
   Headers: Authorization: Bearer <faculty_jwt>

2. Auth: Extract user from JWT → User(id='user-123', role='faculty')

3. Build data:
   schedules = [
     {"id": 1, "person_id": "user-123", "date": "2025-01-15"},
     {"id": 2, "person_id": "user-456", "date": "2025-01-15"}
   ]

4. Filter: RoleFilterService.filter_schedule_list(schedules, 'faculty', 'user-123')
   Result: Only schedules with person_id='user-123'

5. Response: [{"id": 1, "person_id": "user-123", "date": "2025-01-15"}]
```

### Example 3: Clinical Staff Manifest Request
```
1. Request: GET /api/manifest
   Headers: Authorization: Bearer <rn_jwt>

2. Auth: Extract user from JWT → User(role='rn')

3. Normalize: 'rn' → 'clinical_staff'

4. Build data:
   schedules = [
     {"id": 1, "date": "2025-01-15"},  # today
     {"id": 2, "date": "2025-01-16"},  # tomorrow
   ]

5. Filter: RoleFilterService.filter_schedule_list(schedules, 'rn')
   Result: Only today's schedules (date='2025-01-15')

6. Response: [{"id": 1, "date": "2025-01-15"}]
```

### Example 4: Unauthorized Access Attempt
```
1. Request: GET /api/compliance
   Headers: Authorization: Bearer <coordinator_jwt>

2. Auth: Extract user from JWT → User(role='coordinator')

3. Dependency Check: require_resource_access(ResourceType.COMPLIANCE)
   → RoleFilterService.can_access(COMPLIANCE, 'coordinator')
   → Returns False

4. Raise HTTPException(403, "Access denied: Your role 'coordinator' cannot access compliance")

5. Response: 403 Forbidden
```

## Security Principles

1. **Default Deny**: If no explicit permission exists, access is denied
2. **Least Privilege**: Each role has minimum necessary permissions
3. **Data Isolation**: Faculty/residents only see their own data
4. **Temporal Filtering**: Clinical staff only see current day's data
5. **Role Normalization**: Clinical roles unified for consistent permissions
6. **Explicit Checks**: Access must be explicitly granted, never assumed

## Integration Points

### With Existing Auth System
- Uses existing `get_current_active_user` dependency
- Reads `User.role` from database
- Compatible with JWT token authentication
- No changes to auth flow required

### With Existing Routes
- Can protect entire endpoints with dependencies
- Can filter response data programmatically
- Can check access in business logic
- Backward compatible (no breaking changes)

### With Frontend
- Frontend can query `/api/example/permissions` to get user's permissions
- Frontend can hide/show UI elements based on role
- Frontend receives pre-filtered data from backend
- No sensitive data leaks even if frontend bypassed

## File Structure

```
backend/
├── alembic/versions/
│   └── 012_add_clinical_staff_roles.py        # Migration
├── app/
│   ├── api/
│   │   ├── dependencies/
│   │   │   ├── __init__.py                    # Dependency exports
│   │   │   └── role_filter.py                 # FastAPI dependencies
│   │   └── routes/
│   │       └── role_filter_example.py         # Example routes
│   ├── models/
│   │   └── user.py                            # User model (modified)
│   ├── schemas/
│   │   └── auth.py                            # Auth schemas (modified)
│   └── services/
│       ├── __init__.py                        # Service exports (modified)
│       ├── ROLE_FILTER_README.md              # Documentation
│       └── role_filter_service.py             # Core service
└── tests/
    └── services/
        └── test_role_filter_service.py        # Test suite

Documentation/
├── ROLE_FILTER_IMPLEMENTATION_SUMMARY.md      # Implementation summary
└── ROLE_FILTER_ARCHITECTURE.md                # This file
```

---

**Architecture Version**: 1.0
**Date**: 2025-12-17
**Status**: Production Ready
