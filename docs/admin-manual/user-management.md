# User and Permission Management

## Overview

This guide covers user account administration, role-based access control (RBAC), and permission management for the Residency Scheduler application.

## Table of Contents

1. [User Model Overview](#user-model-overview)
2. [Role-Based Access Control](#role-based-access-control)
3. [Creating Users](#creating-users)
4. [Managing Users](#managing-users)
5. [Permission Matrix](#permission-matrix)
6. [Authentication Configuration](#authentication-configuration)
7. [Session Management](#session-management)
8. [Audit Logging](#audit-logging)
9. [Troubleshooting](#troubleshooting)

---

## User Model Overview

### User vs Person Distinction

The application maintains two separate concepts:

| Concept | Purpose | Table |
|---------|---------|-------|
| **User** | System authentication and authorization | `users` |
| **Person** | Schedulable entities (residents, faculty) | `people` |

A User MAY be linked to a Person record (e.g., a faculty member who manages schedules), but this is not required (e.g., an admin who only manages the system).

### User Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `id` | UUID | Unique identifier |
| `username` | String | Login username (unique) |
| `email` | String | Email address (unique) |
| `hashed_password` | String | Bcrypt-hashed password |
| `full_name` | String | Display name |
| `role` | Enum | Permission role |
| `person_id` | UUID | Optional link to Person record |
| `is_active` | Boolean | Account status |
| `is_verified` | Boolean | Email verification status |
| `created_at` | DateTime | Account creation timestamp |
| `last_login_at` | DateTime | Last successful login |

---

## Role-Based Access Control

### Role Hierarchy

The system implements a hierarchical RBAC model:

```
              ADMIN
                |
                | (inherits all permissions)
                v
           COORDINATOR
                |
                | (inherits all permissions)
                v
            FACULTY
```

### Role Definitions

#### Admin Role

**Full system access.** Administrators can:

- Manage all users (create, modify, delete)
- Change user roles
- Access all schedules and data
- Modify system settings
- View audit logs
- Override ACGME compliance rules
- Manage rotation templates

#### Coordinator Role

**Schedule management access.** Coordinators can:

- Generate and modify schedules
- Manage people (residents, faculty)
- Create and manage absences
- Handle emergency coverage
- Export reports
- Override compliance (with justification)
- Manage most rotation templates

#### Faculty Role

**View access with limited actions.** Faculty can:

- View schedules
- View their own assignments
- Create absence requests for themselves
- Export schedules
- View compliance reports

---

## Creating Users

### Via API (Programmatic)

**Admin Only - POST /api/users**

```bash
curl -X POST https://api.your-domain.com/api/users \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "jsmith",
    "email": "jsmith@hospital.org",
    "password": "SecurePassword123!",
    "full_name": "Dr. John Smith",
    "role": "coordinator",
    "person_id": "optional-uuid-if-linking-to-person"
  }'
```

### Via Database (Initial Setup)

For initial admin user creation:

```bash
# Docker
docker compose exec backend python

# Manual deployment
cd /opt/residency-scheduler/backend
./venv/bin/python
```

```python
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()

# Create admin user
admin = User(
    username="admin",
    email="admin@your-domain.com",
    hashed_password=get_password_hash("SecureAdminPassword123!"),
    full_name="System Administrator",
    role="admin",
    is_active=True,
    is_verified=True
)
db.add(admin)
db.commit()
print(f"Created admin user with ID: {admin.id}")
db.close()
```

### Bulk User Import

For importing multiple users, create a Python script:

```python
import csv
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def import_users_from_csv(filepath: str):
    db = SessionLocal()

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            user = User(
                username=row['username'],
                email=row['email'],
                hashed_password=get_password_hash(row['temp_password']),
                full_name=row['full_name'],
                role=row['role'],
                is_active=True
            )
            db.add(user)

    db.commit()
    db.close()
    print("Users imported successfully")

# CSV format:
# username,email,temp_password,full_name,role
# jsmith,jsmith@hospital.org,TempPass123!,Dr. John Smith,coordinator
```

---

## Managing Users

### Listing Users

**Admin Only - GET /api/users**

```bash
# List all users
curl https://api.your-domain.com/api/users \
  -H "Authorization: Bearer <admin-token>"

# Filter by role
curl "https://api.your-domain.com/api/users?role=coordinator" \
  -H "Authorization: Bearer <admin-token>"

# Filter by status
curl "https://api.your-domain.com/api/users?is_active=true" \
  -H "Authorization: Bearer <admin-token>"
```

### Updating Users

**Admin Only - PATCH /api/users/{id}**

```bash
# Update user role
curl -X PATCH https://api.your-domain.com/api/users/<user-id> \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin"
  }'

# Deactivate user
curl -X PATCH https://api.your-domain.com/api/users/<user-id> \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'

# Link user to person record
curl -X PATCH https://api.your-domain.com/api/users/<user-id> \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "person_id": "<person-uuid>"
  }'
```

### Deleting Users

**Admin Only - DELETE /api/users/{id}**

```bash
curl -X DELETE https://api.your-domain.com/api/users/<user-id> \
  -H "Authorization: Bearer <admin-token>"
```

**Note:** User deletion is a soft operation. Consider deactivating users instead to preserve audit trails.

### Password Reset

**Admin-Initiated Reset:**

```python
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
user = db.query(User).filter(User.username == "jsmith").first()
user.hashed_password = get_password_hash("NewTempPassword123!")
db.commit()
db.close()
```

**User Self-Service (via API):**

```bash
# Change own password (authenticated user)
curl -X POST https://api.your-domain.com/api/auth/change-password \
  -H "Authorization: Bearer <user-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "OldPassword123!",
    "new_password": "NewPassword456!"
  }'
```

---

## Permission Matrix

### Resource Permissions

| Resource | Action | Admin | Coordinator | Faculty |
|----------|--------|:-----:|:-----------:|:-------:|
| **Users** | Create | Y | N | N |
| **Users** | Read (all) | Y | N | N |
| **Users** | Read (self) | Y | Y | Y |
| **Users** | Update (any) | Y | N | N |
| **Users** | Update (self) | Y | Y | Y |
| **Users** | Delete | Y | N | N |
| **Users** | Change role | Y | N | N |
| **People** | Create | Y | Y | N |
| **People** | Read | Y | Y | Y |
| **People** | Update | Y | Y | N |
| **People** | Delete | Y | Y | N |
| **Schedules** | Generate | Y | Y | N |
| **Schedules** | Read | Y | Y | Y |
| **Schedules** | Export | Y | Y | Y |
| **Assignments** | Create | Y | Y | N |
| **Assignments** | Update | Y | Y | N |
| **Assignments** | Delete | Y | Y | N |
| **Absences** | Create (any) | Y | Y | N |
| **Absences** | Create (self) | Y | Y | Y |
| **Absences** | Read | Y | Y | Y |
| **Absences** | Update (any) | Y | Y | N |
| **Absences** | Delete | Y | Y | N |
| **Templates** | Create | Y | Y | N |
| **Templates** | Read | Y | Y | Y |
| **Templates** | Update | Y | Y | N |
| **Templates** | Delete | Y | N | N |
| **Compliance** | View reports | Y | Y | Y |
| **Compliance** | Override | Y | Y | N |
| **Emergency** | Request coverage | Y | Y | N |
| **Settings** | View | Y | Y | Y |
| **Settings** | Modify | Y | N | N |
| **Audit Logs** | View | Y | N | N |

### API Permission Enforcement

Permissions are enforced at the API layer using FastAPI dependencies:

```python
from app.api.deps import require_permission
from app.core.permissions import Permission

@router.post("/people")
async def create_person(
    person: PersonCreate,
    current_user: User = Depends(require_permission(Permission.PEOPLE_CREATE))
):
    """Only users with PEOPLE_CREATE permission can access this endpoint."""
    pass
```

---

## Authentication Configuration

### JWT Token Settings

Configure in `.env` or `backend/app/core/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `SECRET_KEY` | Required | JWT signing key (min 64 chars) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 (24h) | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |

### Password Requirements

Default password policy:

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- Special characters recommended

### Account Lockout

The system implements account lockout after failed login attempts:

| Setting | Default |
|---------|---------|
| Max failed attempts | 5 |
| Lockout duration | 30 minutes |

---

## Session Management

### Token-Based Sessions

The application uses JWT tokens for authentication:

- **Access Token:** Short-lived (15 min recommended for production)
- **Refresh Token:** Longer-lived (7 days), used to obtain new access tokens

### Revoking Sessions

**Revoke All Sessions for a User (Admin):**

```bash
curl -X POST https://api.your-domain.com/api/users/<user-id>/revoke-sessions \
  -H "Authorization: Bearer <admin-token>"
```

**User Logout (Self):**

```bash
curl -X POST https://api.your-domain.com/api/auth/logout \
  -H "Authorization: Bearer <user-token>"
```

### Concurrent Sessions

By default, users can have multiple concurrent sessions (e.g., logged in on phone and desktop). All sessions are revoked when:

- Password is changed
- Admin revokes sessions
- Account is deactivated

---

## Audit Logging

### Audited Events

The following user-related events are logged:

| Event | Logged Data |
|-------|-------------|
| Login Success | User ID, IP, timestamp |
| Login Failure | Attempted username, IP, timestamp |
| Logout | User ID, timestamp |
| Password Change | User ID, timestamp |
| User Created | Creator ID, new user details |
| User Updated | Editor ID, changed fields |
| User Deleted | Deleter ID, deleted user ID |
| Role Changed | Changer ID, old role, new role |
| Session Revoked | Admin ID, target user ID |

### Viewing Audit Logs

**Admin Only - GET /api/audit-logs**

```bash
# Get recent audit logs
curl "https://api.your-domain.com/api/audit-logs?limit=100" \
  -H "Authorization: Bearer <admin-token>"

# Filter by user
curl "https://api.your-domain.com/api/audit-logs?user_id=<user-uuid>" \
  -H "Authorization: Bearer <admin-token>"

# Filter by action
curl "https://api.your-domain.com/api/audit-logs?action=login" \
  -H "Authorization: Bearer <admin-token>"

# Filter by date range
curl "https://api.your-domain.com/api/audit-logs?start_date=2024-01-01&end_date=2024-01-31" \
  -H "Authorization: Bearer <admin-token>"
```

### Audit Log Retention

Audit logs should be retained according to your organization's policy. For ACGME compliance, retain schedule-related audit logs for at least 7 years.

---

## Troubleshooting

### User Cannot Login

1. **Verify account is active:**
   ```sql
   SELECT username, is_active FROM users WHERE username = 'jsmith';
   ```

2. **Check for account lockout:**
   ```sql
   SELECT username, failed_login_attempts, locked_until
   FROM users WHERE username = 'jsmith';
   ```

3. **Reset lockout (if needed):**
   ```sql
   UPDATE users
   SET failed_login_attempts = 0, locked_until = NULL
   WHERE username = 'jsmith';
   ```

4. **Verify password:**
   ```python
   from app.core.security import verify_password
   # Test in Python shell
   verify_password("user_provided_password", user.hashed_password)
   ```

### Permission Denied Errors

1. **Verify user role:**
   ```bash
   curl https://api.your-domain.com/api/auth/me \
     -H "Authorization: Bearer <user-token>"
   ```

2. **Check required permission for endpoint in API documentation**

3. **Escalate role if necessary (Admin only)**

### Token Expired Errors

1. **Obtain new access token using refresh token:**
   ```bash
   curl -X POST https://api.your-domain.com/api/auth/refresh \
     -H "Cookie: refresh_token=<refresh-token>"
   ```

2. **If refresh token expired, user must login again**

### Database Queries for User Management

```sql
-- List all users with roles
SELECT id, username, email, role, is_active, created_at
FROM users ORDER BY created_at DESC;

-- Find users by role
SELECT * FROM users WHERE role = 'coordinator';

-- Find inactive users
SELECT * FROM users WHERE is_active = false;

-- Find users linked to people
SELECT u.username, u.role, p.name as person_name
FROM users u
LEFT JOIN people p ON u.person_id = p.id;

-- Recent login activity
SELECT username, last_login_at, failed_login_attempts
FROM users
ORDER BY last_login_at DESC
LIMIT 20;
```

---

## Best Practices

### User Administration

1. **Principle of Least Privilege:** Assign the minimum role necessary
2. **Regular Access Reviews:** Audit user roles quarterly
3. **Deactivate vs Delete:** Prefer deactivation to preserve audit trails
4. **Strong Passwords:** Enforce password policy and complexity
5. **Session Limits:** Configure appropriate token expiration

### Security Recommendations

1. **Unique Accounts:** No shared credentials
2. **MFA:** Consider implementing multi-factor authentication
3. **Password Rotation:** Encourage regular password changes
4. **Access Logging:** Monitor audit logs for suspicious activity
5. **Offboarding:** Immediately deactivate accounts when users leave

---

*Last Updated: December 2024*
