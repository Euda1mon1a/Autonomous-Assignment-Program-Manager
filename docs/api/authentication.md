# Authentication

The Residency Scheduler API uses JWT (JSON Web Token) authentication with Bearer token authorization.

## Overview

- **Authentication Type**: JWT Bearer Token
- **Token Algorithm**: HS256
- **Token Expiration**: 24 hours (configurable)
- **Password Hashing**: bcrypt

## Authentication Flow

```
┌──────────┐          ┌──────────┐          ┌──────────┐
│  Client  │          │   API    │          │ Database │
└────┬─────┘          └────┬─────┘          └────┬─────┘
     │                     │                     │
     │  POST /auth/login   │                     │
     │────────────────────>│                     │
     │                     │  Verify credentials │
     │                     │────────────────────>│
     │                     │<────────────────────│
     │                     │                     │
     │  JWT access_token   │                     │
     │<────────────────────│                     │
     │                     │                     │
     │  GET /api/resource  │                     │
     │  Authorization:     │                     │
     │  Bearer <token>     │                     │
     │────────────────────>│                     │
     │                     │  Validate token     │
     │                     │  Query data         │
     │                     │────────────────────>│
     │                     │<────────────────────│
     │  Resource data      │                     │
     │<────────────────────│                     │
     │                     │                     │
```

## Obtaining a Token

### Method 1: OAuth2 Form Data

Use `application/x-www-form-urlencoded` content type:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=john.doe&password=SecurePassword123!"
```

### Method 2: JSON Request

Use `application/json` content type:

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "password": "SecurePassword123!"
  }'
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJ1c2VybmFtZSI6ImpvaG4uZG9lIiwiZXhwIjoxNzA0MDY3MjAwfQ.signature",
  "token_type": "bearer"
}
```

## Using the Token

Include the token in the `Authorization` header with the `Bearer` prefix:

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Token Structure

The JWT token contains the following claims:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "exp": 1704067200,
  "iat": 1703980800
}
```

| Claim | Description |
|-------|-------------|
| `sub` | Subject - User's UUID |
| `username` | User's username |
| `exp` | Expiration timestamp (Unix epoch) |
| `iat` | Issued at timestamp (Unix epoch) |

## User Registration

Register a new user account:

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john.doe",
    "email": "john.doe@hospital.org",
    "password": "SecurePassword123!",
    "role": "coordinator"
  }'
```

**Note**: The first user registered automatically becomes an admin.

### Registration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Unique username |
| `email` | string | Yes | Valid email address (unique) |
| `password` | string | Yes | User password |
| `role` | string | No | User role (default: `coordinator`) |

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "email": "john.doe@hospital.org",
  "role": "coordinator",
  "is_active": true
}
```

## Role-Based Access Control (RBAC)

The API implements role-based access control with three roles:

### Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| `admin` | System administrator | Full access to all endpoints |
| `coordinator` | Schedule coordinator | Schedule management, people management |
| `faculty` | Faculty member | View-only access to schedules |

### Permission Matrix

| Endpoint | Admin | Coordinator | Faculty | Public |
|----------|-------|-------------|---------|--------|
| `GET /api/people` | ✓ | ✓ | ✓ | ✓ |
| `POST /api/people` | ✓ | ✓ | - | - |
| `PUT /api/people/{id}` | ✓ | ✓ | - | - |
| `DELETE /api/people/{id}` | ✓ | ✓ | - | - |
| `GET /api/assignments` | ✓ | ✓ | ✓ | - |
| `POST /api/assignments` | ✓ | ✓ | - | - |
| `POST /api/schedule/generate` | ✓ | ✓ | - | - |
| `GET /api/auth/users` | ✓ | - | - | - |

### Protected vs Public Endpoints

**Public Endpoints** (no authentication required):
- `GET /` - Health check
- `GET /health` - Detailed health status
- `GET /api/people` - List people
- `GET /api/blocks` - List blocks
- `GET /api/rotation-templates` - List templates
- `GET /api/absences` - List absences
- `GET /api/schedule/{start}/{end}` - View schedule
- `GET /api/schedule/validate` - Validate schedule
- `GET /api/settings` - View settings

**Protected Endpoints** (authentication required):
- `POST /api/auth/logout` - Logout
- `GET /api/auth/me` - Current user info
- `POST /api/people` - Create person
- `PUT /api/people/{id}` - Update person
- `DELETE /api/people/{id}` - Delete person
- All `/api/assignments` endpoints
- `POST /api/schedule/generate` - Generate schedule
- `POST /api/schedule/emergency-coverage` - Emergency coverage

**Admin-Only Endpoints**:
- `GET /api/auth/users` - List all users

## Token Refresh

The current implementation does not include refresh tokens. When a token expires, the user must re-authenticate using the login endpoint.

**Token Lifecycle:**

1. User logs in and receives access token
2. Token is valid for 24 hours
3. After expiration, user must log in again

## Logout

To logout and invalidate the session:

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Response

```json
{
  "message": "Successfully logged out"
}
```

## Get Current User

Retrieve the authenticated user's information:

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <your_jwt_token>"
```

### Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john.doe",
  "email": "john.doe@hospital.org",
  "role": "coordinator",
  "is_active": true
}
```

## Authentication Errors

### Invalid Credentials (401)

```json
{
  "detail": "Incorrect username or password"
}
```

### Missing Token (401)

```json
{
  "detail": "Not authenticated"
}
```

### Invalid Token (401)

```json
{
  "detail": "Could not validate credentials"
}
```

### Expired Token (401)

```json
{
  "detail": "Token has expired"
}
```

### Insufficient Permissions (403)

```json
{
  "detail": "Not authorized to access this resource"
}
```

## Security Best Practices

1. **Store tokens securely**: Use secure storage mechanisms (e.g., HttpOnly cookies, secure local storage)
2. **Use HTTPS**: Always use HTTPS in production to protect tokens in transit
3. **Don't expose tokens**: Never include tokens in URLs or client-side logs
4. **Handle expiration gracefully**: Implement token expiration handling in your client
5. **Use strong passwords**: Enforce password complexity requirements

## Configuration

The following environment variables control authentication behavior:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | 1440 (24 hours) |
| `ALGORITHM` | JWT algorithm | HS256 |

## Example: Complete Authentication Flow

```bash
# 1. Register a new user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "scheduler",
    "email": "scheduler@hospital.org",
    "password": "SecurePass123!",
    "role": "coordinator"
  }'

# 2. Login to get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "scheduler",
    "password": "SecurePass123!"
  }' | jq -r '.access_token')

# 3. Use token for authenticated requests
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Create a person (requires authentication)
curl -X POST http://localhost:8000/api/people \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dr. Jane Smith",
    "type": "resident",
    "pgy_level": 2
  }'

# 5. Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer $TOKEN"
```

---

*See also: [Error Handling](./errors.md) for authentication error details*
