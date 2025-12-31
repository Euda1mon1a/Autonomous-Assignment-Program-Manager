# Admin API Documentation

**Status:** Complete API reconnaissance and comprehensive documentation
**Scope:** Admin user management, database administration, and system configuration
**Last Updated:** 2025-12-30

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication & Authorization](#authentication--authorization)
3. [Admin User Management](#admin-user-management)
4. [Database Administration](#database-administration)
5. [System Configuration & Monitoring](#system-configuration--monitoring)
6. [Error Handling](#error-handling)
7. [Audit Logging](#audit-logging)
8. [Bulk Operations](#bulk-operations)
9. [Best Practices](#best-practices)

---

## Overview

The Admin API provides a complete set of endpoints for system administrators to manage:

- **User Accounts**: Create, read, update, delete users; manage roles and permissions
- **Account Locking**: Lock/unlock accounts with audit trails
- **Database Optimization**: Monitor indexes, table statistics, query performance
- **Compliance Auditing**: Track all administrative actions for regulatory compliance

### Base URL

```
http://localhost:8000/api
```

### Authentication

All admin endpoints require:
- **Authentication**: JWT token in Authorization header
- **Authorization**: ADMIN role

```bash
Authorization: Bearer <jwt_token>
```

---

## Authentication & Authorization

### Access Control

Admin endpoints are protected by role-based access control:

| Endpoint | Minimum Role | Description |
|----------|-------------|-------------|
| `/api/admin/users/*` | ADMIN | User management operations |
| `/api/db-admin/*` | ADMIN | Database administration |
| `/api/*/admin/*` | ADMIN | System configuration |

### Getting an Admin Token

```bash
# Login endpoint
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin_user",
  "password": "secure_password"
}

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "refresh_token": "...",
  "user": {
    "id": "uuid",
    "username": "admin_user",
    "role": "admin",
    "email": "admin@example.com"
  }
}
```

### Token Refresh

Admin tokens can expire. Refresh using the refresh token:

```bash
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "..."
}
```

---

## Admin User Management

### User Management Endpoints

All user management endpoints are located at `/api/admin/users/`.

#### 1. List Users

**Endpoint:** `GET /api/admin/users/`

**Authentication:** ADMIN role required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-indexed) |
| `pageSize` | integer | 20 | Items per page (max 100) |
| `role` | string | None | Filter by role (admin, coordinator, faculty, resident, clinical_staff, rn, lpn, msa) |
| `status` | string | None | Filter by status (active, inactive, locked, pending) |
| `search` | string | None | Search by username or email (case-insensitive) |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/admin/users/?page=1&pageSize=20&role=faculty&status=active" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "drsmith",
      "email": "smith@hospital.edu",
      "first_name": "John",
      "last_name": "Smith",
      "role": "faculty",
      "is_active": true,
      "is_locked": false,
      "lock_reason": null,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-20T14:22:00Z",
      "last_login": "2025-01-20T09:15:00Z",
      "invite_sent_at": "2025-01-15T10:30:00Z",
      "invite_accepted_at": "2025-01-15T11:45:00Z"
    }
  ],
  "total": 127,
  "page": 1,
  "pageSize": 20,
  "totalPages": 7
}
```

**Use Cases:**

- Audit all active faculty accounts
- Find pending invitations (status=pending)
- Search for specific user by email
- Filter by role to see coordinator distribution

---

#### 2. Create User

**Endpoint:** `POST /api/admin/users/`

**Authentication:** ADMIN role required

**Request Body:**

```json
{
  "email": "newuser@hospital.edu",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "coordinator",
  "username": "janedoe",
  "send_invite": true
}
```

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `email` | string | Yes | Valid email format | Must be unique |
| `first_name` | string | Yes | 1-100 chars | |
| `last_name` | string | Yes | 1-100 chars | |
| `role` | enum | Yes | See roles below | Default: coordinator |
| `username` | string | No | 3-100 chars | Auto-generated from email if not provided |
| `send_invite` | boolean | No | Default: true | Send invitation email immediately |

**Available Roles:**

```
- admin            # Full system access
- coordinator      # Schedule management and monitoring
- faculty          # Faculty scheduling and swap requests
- resident         # Resident view and preferences
- clinical_staff   # Clinical operations
- rn               # Nursing staff
- lpn              # Licensed Practical Nurse
- msa              # Medical Support Assistant
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/admin/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@hospital.edu",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "coordinator",
    "send_invite": true
  }'
```

**Response: 201 Created**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "username": "newuser",
  "email": "newuser@hospital.edu",
  "first_name": "Jane",
  "last_name": "Doe",
  "role": "coordinator",
  "is_active": true,
  "is_locked": false,
  "lock_reason": null,
  "created_at": "2025-01-21T10:30:00Z",
  "updated_at": "2025-01-21T10:30:00Z",
  "last_login": null,
  "invite_sent_at": "2025-01-21T10:30:00Z",
  "invite_accepted_at": null
}
```

**Error Cases:**

- **409 Conflict** - Email already exists
- **400 Bad Request** - Invalid role or validation failure

**Activity Logged:** USER_CREATED action with send_invite details

---

#### 3. Update User

**Endpoint:** `PUT /api/admin/users/{user_id}`

**Authentication:** ADMIN role required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | User to update |

**Request Body (all fields optional):**

```json
{
  "email": "updated@hospital.edu",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": "faculty",
  "is_active": true
}
```

**Example Request:**

```bash
curl -X PUT "http://localhost:8000/api/admin/users/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "faculty",
    "is_active": true
  }'
```

**Response: 200 OK**

Returns updated user object (see Create User response format).

**Guardrails:**

- Cannot deactivate own account
- Cannot change own role
- Email must be unique (except current email)
- Tracks all changes for audit log

**Activity Logged:** USER_UPDATED action with change details

---

#### 4. Delete User

**Endpoint:** `DELETE /api/admin/users/{user_id}`

**Authentication:** ADMIN role required

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/api/admin/users/550e8400-e29b-41d4-a716-446655440001" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "message": "User deleted successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

**Guardrails:**

- Cannot delete own account
- All associated data will be cleaned up

**Activity Logged:** USER_DELETED action with email and username

---

#### 5. Lock/Unlock Account

**Endpoint:** `POST /api/admin/users/{user_id}/lock`

**Authentication:** ADMIN role required

**Request Body:**

```json
{
  "locked": true,
  "reason": "Suspicious activity detected"
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `locked` | boolean | Yes | true=lock, false=unlock |
| `reason` | string | No | Max 500 chars, required for locking |

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/admin/users/550e8400-e29b-41d4-a716-446655440001/lock" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "locked": true,
    "reason": "Failed login attempts - security breach"
  }'
```

**Response: 200 OK**

```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440001",
  "isLocked": true,
  "lockReason": "Failed login attempts - security breach",
  "lockedAt": "2025-01-21T15:30:00Z",
  "lockedBy": "admin@hospital.edu",
  "message": "Account locked successfully"
}
```

**Guardrails:**

- Cannot lock own account
- Locked users cannot login
- Lock reason recorded for audit trail

**Activity Logged:** USER_LOCKED or USER_UNLOCKED action

---

#### 6. Resend Invitation

**Endpoint:** `POST /api/admin/users/{user_id}/resend-invite`

**Authentication:** ADMIN role required

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/admin/users/550e8400-e29b-41d4-a716-446655440001/resend-invite" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "userId": "550e8400-e29b-41d4-a716-446655440001",
  "email": "newuser@hospital.edu",
  "sentAt": "2025-01-21T15:35:00Z",
  "message": "Invitation resent successfully"
}
```

**Constraints:**

- Only works for users who haven't accepted invite yet
- Updates invite_sent_at timestamp
- Sends invitation email to user

**Activity Logged:** INVITE_RESENT action

---

#### 7. Bulk User Actions

**Endpoint:** `POST /api/admin/users/bulk`

**Authentication:** ADMIN role required

**Request Body:**

```json
{
  "userIds": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "action": "activate"
}
```

| Field | Type | Required | Constraints | Notes |
|-------|------|----------|-------------|-------|
| `userIds` | array | Yes | 1-100 IDs | Cannot include own user |
| `action` | enum | Yes | activate, deactivate, delete | Bulk action type |

**Available Actions:**

- **activate** - Reactivate user, unlock if needed
- **deactivate** - Mark inactive (not deleted)
- **delete** - Permanently delete users

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/admin/users/bulk" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "userIds": [
      "550e8400-e29b-41d4-a716-446655440001",
      "550e8400-e29b-41d4-a716-446655440002"
    ],
    "action": "deactivate"
  }'
```

**Response: 200 OK**

```json
{
  "action": "deactivate",
  "affectedCount": 2,
  "successIds": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "failedIds": [],
  "errors": [],
  "message": "Successfully deactivated 2 user(s)"
}
```

**Response with Errors:**

```json
{
  "action": "delete",
  "affectedCount": 1,
  "successIds": [
    "550e8400-e29b-41d4-a716-446655440001"
  ],
  "failedIds": [
    "550e8400-e29b-41d4-a716-446655440002"
  ],
  "errors": [
    "Cannot perform action on your own account: 550e8400-e29b-41d4-a716-446655440002"
  ],
  "message": "Successfully deleted 1 user(s)"
}
```

**Constraints:**

- Cannot include own user ID
- Maximum 100 users per bulk operation
- Non-existent users in list generate errors
- Partial success is allowed

**Activity Logged:** USER_UPDATED or USER_DELETED with bulk operation details

---

#### 8. Activity Log

**Endpoint:** `GET /api/admin/users/activity-log`

**Authentication:** ADMIN role required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `pageSize` | integer | 20 | Items per page (max 100) |
| `userId` | UUID | None | Filter by user who performed action |
| `action` | string | None | Filter by action type (see below) |
| `dateFrom` | ISO datetime | None | Filter by start date |
| `dateTo` | ISO datetime | None | Filter by end date |

**Available Actions:**

```
USER_CREATED        # User account created
USER_UPDATED        # User account modified
USER_DELETED        # User account deleted
USER_LOCKED         # Account locked
USER_UNLOCKED       # Account unlocked
LOGIN_SUCCESS       # Successful login
LOGIN_FAILED        # Failed login attempt
PASSWORD_CHANGED    # Password changed
ROLE_CHANGED        # Role changed
INVITE_SENT         # Invitation sent
INVITE_RESENT       # Invitation resent
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/admin/users/activity-log?page=1&action=USER_CREATED&dateFrom=2025-01-01T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440010",
      "timestamp": "2025-01-21T10:30:00Z",
      "userId": "550e8400-e29b-41d4-a716-446655440099",
      "userEmail": "admin@hospital.edu",
      "action": "USER_CREATED",
      "targetUserId": "550e8400-e29b-41d4-a716-446655440001",
      "targetUserEmail": "newuser@hospital.edu",
      "details": {
        "send_invite": true,
        "role": "coordinator"
      },
      "ipAddress": "192.168.1.100",
      "userAgent": "Mozilla/5.0..."
    }
  ],
  "total": 47,
  "page": 1,
  "pageSize": 20,
  "totalPages": 3
}
```

**Current Status:**

The activity log endpoint is a placeholder. Full implementation requires:
- Activity log database table
- Middleware to capture IP and user agent
- Audit trail persistence layer

---

## Database Administration

### Database Admin Endpoints

All database administration endpoints are located at `/api/db-admin/`.

#### 1. Database Health Check

**Endpoint:** `GET /api/db-admin/health`

**Authentication:** ADMIN role required

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/db-admin/health" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "status": "healthy",
  "connection_pool": {
    "pool_size": 10,
    "max_overflow": 20,
    "checked_out": 5,
    "overflow": 0,
    "total_connections": 5,
    "utilization_percent": 33.33
  },
  "database_size_mb": 245.67,
  "active_connections": 8,
  "total_tables": 42,
  "total_indexes": 156,
  "recommendations": [
    "Consider running ANALYZE on frequently updated tables"
  ]
}
```

**Health Status Levels:**

| Status | Threshold | Action |
|--------|-----------|--------|
| healthy | Utilization < 80%, Connections < 50 | Normal operation |
| warning | Utilization 80-90%, Connections 50-100 | Monitor closely |
| critical | Utilization > 90%, Connections > 100 | Investigate immediately |

**Key Metrics:**

- **Pool Utilization**: % of available connections in use
- **Database Size**: Total size in MB including tables and indexes
- **Active Connections**: Currently executing queries
- **Table/Index Counts**: Schema complexity

---

#### 2. Index Recommendations

**Endpoint:** `GET /api/db-admin/indexes/recommendations`

**Authentication:** ADMIN role required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_table_size_mb` | float | 1.0 | Only analyze tables larger than this |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/db-admin/indexes/recommendations?min_table_size_mb=5.0" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
[
  {
    "table_name": "assignments",
    "columns": ["person_id", "rotation_id"],
    "index_type": "BTREE",
    "priority": "high",
    "reason": "Frequent join on person_id and rotation_id",
    "estimated_benefit": "25-40% query speedup",
    "create_statement": "CREATE INDEX idx_assignments_person_rotation ON assignments(person_id, rotation_id);"
  }
]
```

**How to Use:**

1. Review recommendations with priority ordering
2. Test CREATE INDEX statement in development
3. Apply to production during maintenance window
4. Monitor query execution times after deployment

---

#### 3. Unused Indexes

**Endpoint:** `GET /api/db-admin/indexes/unused`

**Authentication:** ADMIN role required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_age_days` | integer | 7 | Minimum index age to consider |
| `min_size_mb` | float | 10.0 | Minimum index size to consider |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/db-admin/indexes/unused?min_age_days=30&min_size_mb=10" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
[
  {
    "schema_name": "public",
    "table_name": "assignments_archive",
    "index_name": "idx_archive_person_old",
    "index_size_mb": 45.3,
    "scans": 0,
    "tuples_read": 0,
    "tuples_fetched": 0,
    "is_unique": false,
    "definition": "CREATE INDEX idx_archive_person_old ON assignments_archive(person_id) WHERE archived_at < NOW() - INTERVAL '1 year'"
  }
]
```

**Action Items:**

- High-size unused indexes (>100MB) should be evaluated for removal
- Before dropping, verify in application code that queries aren't using it
- Use `min_age_days` to avoid dropping recently created indexes

---

#### 4. Index Usage Statistics

**Endpoint:** `GET /api/db-admin/indexes/usage`

**Authentication:** ADMIN role required

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/db-admin/indexes/usage" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
[
  {
    "schema_name": "public",
    "table_name": "assignments",
    "index_name": "idx_assignments_person_id",
    "index_size_mb": 12.4,
    "scans": 15234,
    "tuples_read": 2456892,
    "tuples_fetched": 89234,
    "is_unique": false,
    "definition": "CREATE INDEX idx_assignments_person_id ON assignments(person_id)"
  }
]
```

**Interpretation:**

- **Scans**: How many times index was used
- **Tuples Read**: Total rows examined via index
- **Tuples Fetched**: Actual rows returned to client
- **Fetch Ratio**: tuples_fetched / tuples_read (lower = more selective index)

---

#### 5. Table Statistics

**Endpoint:** `GET /api/db-admin/tables/{table_name}/stats`

**Authentication:** ADMIN role required

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `table_name` | string | Table to analyze (alphanumeric + underscore only) |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/db-admin/tables/assignments/stats" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "schema": "public",
  "table": "assignments",
  "total_size": "125 MB",
  "table_size": "100 MB",
  "indexes_size": "25 MB",
  "sequential_scans": 234,
  "sequential_tuples_read": 4234234,
  "index_scans": 15234,
  "index_tuples_fetched": 89234,
  "inserts": 4523,
  "updates": 2341,
  "deletes": 234,
  "live_tuples": 89234,
  "dead_tuples": 1234,
  "scan_ratio": 0.0234,
  "last_vacuum": "2025-01-20T02:15:00Z",
  "last_autovacuum": "2025-01-20T15:30:00Z",
  "last_analyze": "2025-01-20T02:16:00Z",
  "last_autoanalyze": "2025-01-20T15:35:00Z"
}
```

**Key Indicators:**

| Metric | Good | Concerning | Critical |
|--------|------|------------|----------|
| Dead Tuples | < 1% of live | 5-10% | > 10% |
| Seq Scans | Minimal | > 100 | > 1000 |
| Scan Ratio | Near 0 | 0.1+ | 0.5+ |
| Last Vacuum | < 24h | > 1 week | > 1 month |

---

#### 6. Query Statistics

**Endpoint:** `GET /api/db-admin/queries/stats`

**Authentication:** ADMIN role required

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `request_id` | string | Yes | Request ID to analyze |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/db-admin/queries/stats?request_id=req-12345" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "request_id": "req-12345",
  "total_queries": 47,
  "total_duration_ms": 234.5,
  "avg_duration_ms": 4.99,
  "slow_queries": 2,
  "n_plus_one_warnings": 1,
  "query_types": {
    "SELECT": 42,
    "INSERT": 3,
    "UPDATE": 2
  },
  "recommendations": [
    "Query tracking not currently active - enable QueryAnalyzer to track queries"
  ]
}
```

**Current Status:**

Query statistics endpoint requires QueryAnalyzer middleware to be enabled. Currently returns placeholder response.

---

#### 7. Run VACUUM on Table

**Endpoint:** `POST /api/db-admin/vacuum/{table_name}`

**Authentication:** ADMIN role required

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `analyze` | boolean | true | Also run ANALYZE (updates statistics) |

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/db-admin/vacuum/assignments?analyze=true" \
  -H "Authorization: Bearer $TOKEN"
```

**Response: 200 OK**

```json
{
  "message": "VACUUM ANALYZE completed successfully for assignments",
  "table": "assignments"
}
```

**What VACUUM Does:**

- **VACUUM**: Reclaims disk space from dead tuples
- **ANALYZE**: Updates table statistics for query planner
- **VACUUM ANALYZE**: Combination of both (recommended)

**Timing Considerations:**

- Use during low-traffic periods
- VACUUM FULL is more aggressive but locks table longer
- Run ANALYZE after bulk data loads
- Automatic autovacuum runs based on server settings

**Security:**

- Table name validated to prevent SQL injection
- Only allows alphanumeric names and underscores
- Checks table existence before execution

---

## System Configuration & Monitoring

### Configuration Endpoints

#### System Settings

**Endpoint:** `GET /api/settings/`

**Response:**

```json
{
  "app_name": "Residency Scheduler",
  "version": "1.0.0",
  "environment": "production",
  "debug_mode": false,
  "api_rate_limit": 1000,
  "max_file_upload_mb": 100,
  "session_timeout_minutes": 60
}
```

#### Health Check

**Endpoint:** `GET /api/health/ready`

**Response (healthy):**

```json
{
  "status": "ready",
  "timestamp": "2025-01-21T16:00:00Z",
  "services": {
    "database": "ok",
    "cache": "ok",
    "scheduler": "ok"
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Query returned data |
| 201 | Created | User successfully created |
| 204 | No Content | Resource deleted |
| 400 | Bad Request | Invalid input parameters |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | User/resource not found |
| 409 | Conflict | Email already exists |
| 422 | Validation Error | Pydantic validation failure |
| 500 | Server Error | Internal error |

### Error Response Format

```json
{
  "detail": "User not found",
  "status_code": 404,
  "timestamp": "2025-01-21T16:00:00Z"
}
```

### Common Error Scenarios

**Email Already Exists**

```
Status: 409 Conflict
Response: { "detail": "User with this email already exists" }
```

**Cannot Modify Own Account**

```
Status: 400 Bad Request
Response: { "detail": "Cannot deactivate your own account" }
```

**Insufficient Permissions**

```
Status: 403 Forbidden
Response: { "detail": "User does not have ADMIN role" }
```

---

## Audit Logging

### Audit Trail Implementation

All admin operations are logged through the `_log_activity()` function.

### Logged Activities

| Action | Trigger | Details Captured |
|--------|---------|------------------|
| USER_CREATED | Create user endpoint | send_invite flag |
| USER_UPDATED | Update user endpoint | Field changes (old/new) |
| USER_DELETED | Delete user endpoint | Email and username |
| USER_LOCKED | Lock account endpoint | Lock reason |
| USER_UNLOCKED | Unlock account endpoint | None |
| INVITE_RESENT | Resend invite endpoint | None |

### Audit Log Schema

Each log entry captures:

```python
{
  "id": "UUID",                    # Log entry ID
  "timestamp": "ISO datetime",     # When action occurred
  "user_id": "UUID",               # Who performed action
  "user_email": "string",          # Admin email
  "action": "string",              # Action type
  "target_user_id": "UUID",        # Who was affected
  "target_user_email": "string",   # Affected user email
  "details": "dict",               # Action-specific details
  "ip_address": "string",          # Requester IP
  "user_agent": "string"           # Browser user agent
}
```

### Accessing Audit Logs

**Activity Log Endpoint:** `GET /api/admin/users/activity-log`

See section 8 under Admin User Management for details.

---

## Bulk Operations

### Bulk User Action Request

**Endpoint:** `POST /api/admin/users/bulk`

### Bulk Operation Flow

```
1. Admin submits list of user IDs + action
2. System validates each user:
   - Check user exists
   - Check not own account
3. System applies action:
   - activate: Set is_active=true, unlock if needed
   - deactivate: Set is_active=false
   - delete: Remove from database
4. System returns summary:
   - Success count
   - Failed count with reasons
   - Partial success allowed
```

### Bulk Limits

- **Maximum users per request**: 100
- **Maximum concurrent bulk operations**: 10 (per admin)

### Error Handling in Bulk Operations

If some users fail, operation continues for others:

```json
{
  "action": "delete",
  "affectedCount": 8,
  "successIds": [
    "550e8400-e29b-41d4-a716-446655440001",
    "550e8400-e29b-41d4-a716-446655440002",
    // ... 6 more
  ],
  "failedIds": [
    "550e8400-e29b-41d4-a716-446655440010"
  ],
  "errors": [
    "Cannot perform action on your own account: 550e8400-e29b-41d4-a716-446655440010"
  ],
  "message": "Successfully deleted 8 user(s)"
}
```

---

## Best Practices

### Security Best Practices

1. **Always verify ADMIN role** before performing operations
2. **Use HTTPS** in production (never HTTP)
3. **Rotate tokens regularly** to prevent token theft
4. **Never log sensitive data** like passwords or emails in application logs
5. **Rate limit** admin endpoints to prevent abuse
6. **Audit all changes** for compliance

### User Management Best Practices

1. **Use meaningful usernames** based on institutional standards
2. **Always send invites** to new users to set their passwords
3. **Prefer deactivate over delete** to preserve audit trail
4. **Lock before deleting** suspicious accounts
5. **Verify role assignments** before granting admin access
6. **Bulk operations** - use for consistent changes across multiple users

### Database Maintenance Best Practices

1. **Run VACUUM ANALYZE** weekly on high-churn tables
2. **Monitor pool utilization** - keep below 80%
3. **Review index recommendations** monthly
4. **Remove unused indexes** to improve write performance
5. **Archive old data** when database exceeds 50GB
6. **Track table growth** with regular statistics checks

### Monitoring Checklist

**Daily:**
- [ ] Check database health status
- [ ] Review failed login attempts
- [ ] Scan active user sessions

**Weekly:**
- [ ] Review activity log for anomalies
- [ ] Run VACUUM ANALYZE on large tables
- [ ] Check connection pool utilization
- [ ] Verify backup completion

**Monthly:**
- [ ] Analyze index recommendations
- [ ] Review unused indexes
- [ ] Audit user roles and permissions
- [ ] Check database size trends

### Integration Examples

#### Monitoring Script

```bash
#!/bin/bash

TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Check health
curl -X GET "http://localhost:8000/api/db-admin/health" \
  -H "Authorization: Bearer $TOKEN"

# Check for unused indexes
curl -X GET "http://localhost:8000/api/db-admin/indexes/unused?min_age_days=30" \
  -H "Authorization: Bearer $TOKEN"
```

#### User Provisioning Script

```python
import requests
import json

TOKEN = "your_admin_token"
BASE_URL = "http://localhost:8000/api"

def create_users_from_csv(csv_file):
    """Create users from CSV file"""
    headers = {"Authorization": f"Bearer {TOKEN}"}

    with open(csv_file) as f:
        for line in f:
            email, first, last, role = line.strip().split(',')

            data = {
                "email": email,
                "first_name": first,
                "last_name": last,
                "role": role,
                "send_invite": True
            }

            resp = requests.post(
                f"{BASE_URL}/admin/users/",
                headers=headers,
                json=data
            )
            print(f"Created {email}: {resp.status_code}")
```

---

## Summary

The Admin API provides comprehensive capabilities for:

1. **User Management** - Complete CRUD with roles and locking
2. **Bulk Operations** - Efficient batch processing
3. **Database Optimization** - Index and table analysis
4. **Audit Trail** - Complete activity logging
5. **System Health** - Connection pool and performance monitoring

All endpoints require ADMIN authentication and maintain detailed audit logs for compliance.

For questions or issues, contact the system administrator.

---

**Document Version:** 1.0
**Last Updated:** 2025-12-30
**Created By:** G2_RECON SEARCH_PARTY Operation
