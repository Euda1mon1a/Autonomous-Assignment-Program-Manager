# API Documentation Index

**G2_RECON SEARCH_PARTY Operation - Complete API Documentation**

**Status:** Complete
**Generation Date:** 2025-12-30
**Operation:** Admin API Reconnaissance and Documentation

---

## Documentation Contents

This directory contains comprehensive API documentation for the Residency Scheduler backend.

### Available Documents

1. **[api-docs-admin.md](./api-docs-admin.md)** - 1,247 lines
   - Admin user management endpoints
   - Database administration and optimization
   - User CRUD operations (create, read, update, delete)
   - Account locking/unlocking
   - Bulk operations
   - Activity logging and audit trails
   - Database health monitoring
   - Index recommendations and optimization
   - Query statistics and analysis

2. **[api-docs-authentication.md](./api-docs-authentication.md)** - Companion document
   - Authentication model and JWT tokens
   - Login endpoints
   - Token refresh and validation
   - Session management

3. **[api-docs-people.md](./api-docs-people.md)** - Companion document
   - People/staff management
   - Role-based access control

---

## Quick Reference

### Admin User Management Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/admin/users/` | List all users with filters |
| POST | `/api/admin/users/` | Create new user |
| PUT | `/api/admin/users/{user_id}` | Update user |
| DELETE | `/api/admin/users/{user_id}` | Delete user |
| POST | `/api/admin/users/{user_id}/lock` | Lock/unlock account |
| POST | `/api/admin/users/{user_id}/resend-invite` | Resend invitation |
| POST | `/api/admin/users/bulk` | Bulk operations |
| GET | `/api/admin/users/activity-log` | View audit trail |

### Database Admin Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/db-admin/health` | Database health check |
| GET | `/api/db-admin/indexes/recommendations` | Index recommendations |
| GET | `/api/db-admin/indexes/unused` | Find unused indexes |
| GET | `/api/db-admin/indexes/usage` | Index usage statistics |
| GET | `/api/db-admin/tables/{table_name}/stats` | Table statistics |
| GET | `/api/db-admin/queries/stats` | Query performance stats |
| POST | `/api/db-admin/vacuum/{table_name}` | Run VACUUM on table |

---

## Authentication

All admin endpoints require:

```bash
Authorization: Bearer <jwt_token>
X-Required-Role: admin
```

---

## Key Features Documented

### 1. User Management
- Create users with 8 different roles
- Update users with change tracking
- Delete users with audit trails
- Lock accounts with reasons
- Bulk operations (up to 100 users)
- Invitation management

### 2. Database Administration
- Health monitoring (pools, size, connections)
- Index analysis and recommendations
- Table statistics and metrics
- Query performance analysis
- VACUUM and ANALYZE operations

### 3. Audit Logging
- All admin operations tracked
- Action types: USER_CREATED, USER_UPDATED, USER_DELETED, USER_LOCKED, INVITE_RESENT
- Full compliance audit trail

### 4. Bulk Operations
- Action types: activate, deactivate, delete
- Limits: 100 users per request
- Partial success allowed

---

## Common Use Cases

### Onboard New Coordinator
```bash
curl -X POST "http://localhost:8000/api/admin/users/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "coordinator@hospital.edu",
    "first_name": "Jane",
    "last_name": "Doe",
    "role": "coordinator",
    "send_invite": true
  }'
```

### Lock Suspicious Account
```bash
curl -X POST "http://localhost:8000/api/admin/users/{user_id}/lock" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "locked": true,
    "reason": "Failed login attempts"
  }'
```

### Check Database Health
```bash
curl -X GET "http://localhost:8000/api/db-admin/health" \
  -H "Authorization: Bearer $TOKEN"
```

---

## API Status

### Fully Implemented
- User CRUD operations
- Account locking/unlocking
- Invitation management
- Bulk operations
- Database health check
- Index recommendations
- Table statistics
- VACUUM operations

### Placeholder Implementation
- Activity log persistence (requires database table)
- Query statistics (requires QueryAnalyzer middleware)

---

## File Locations

- Main route handler: `/backend/app/api/routes/admin_users.py`
- Database admin routes: `/backend/app/api/routes/db_admin.py`
- Schemas: `/backend/app/schemas/admin_user.py`
- Tests: `/backend/tests/test_db_admin_routes.py`

---

## Security Features

- JWT token validation on all endpoints
- Role-based access control (ADMIN required)
- Self-operation prevention
- Complete audit trails
- SQL injection prevention
- Password hashing with bcrypt
- No sensitive data in error messages

---

**Version:** 1.0
**Created:** 2025-12-30
**By:** G2_RECON SEARCH_PARTY Operation
