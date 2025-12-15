# Authentication Guide

## Overview

The Residency Scheduler API uses **JWT (JSON Web Token)** authentication for securing endpoints. This guide covers the authentication flow, token management, and authorization levels.

## Authentication Flow

### 1. User Registration

The first user to register automatically becomes an administrator. Subsequent users must be created by an administrator.

**First User Registration (No Authentication Required):**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "SecurePassword123",
    "role": "coordinator"
  }'
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true
}
```

**Subsequent User Registration (Admin Authentication Required):**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "coordinator1",
    "email": "coordinator@example.com",
    "password": "SecurePassword123",
    "role": "coordinator"
  }'
```

### 2. Login

There are two login endpoints available:

#### Option 1: OAuth2 Form-Based Login

Uses OAuth2 password flow with form data (compatible with OAuth2 clients):

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=SecurePassword123"
```

#### Option 2: JSON-Based Login

Uses JSON request body (more convenient for modern applications):

```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SecurePassword123"
  }'
```

Both endpoints return the same response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjNlNDU2Ny1lODliLTEyZDMtYTQ1Ni00MjY2MTQxNzQwMDAiLCJ1c2VybmFtZSI6ImFkbWluIiwiZXhwIjoxNzA0MTUzNjAwfQ.signature",
  "token_type": "bearer"
}
```

### 3. Using the Token

Include the JWT token in the `Authorization` header for all authenticated requests:

```bash
curl -X GET http://localhost:8000/api/people \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

The header format is:
```
Authorization: Bearer <token>
```

### 4. Token Validation

The API automatically validates the token on each request:
- Checks token signature using the secret key
- Verifies token expiration
- Extracts user information (user ID and username)
- Loads user from database and checks if active

### 5. Get Current User Information

Retrieve information about the currently authenticated user:

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "username": "admin",
  "email": "admin@example.com",
  "role": "admin",
  "is_active": true
}
```

### 6. Logout

The logout endpoint is provided for client convenience:

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "message": "Successfully logged out"
}
```

**Important:** JWT tokens are stateless and cannot be invalidated on the server side. Clients should:
- Remove the token from local storage
- Clear any cached user data
- Redirect to the login page

For production systems requiring immediate token revocation, consider implementing a token blacklist.

## Token Management

### Token Expiration

JWT tokens expire after a configured time period:

**Default Expiration:** 24 hours (1440 minutes)

This is configured via the `ACCESS_TOKEN_EXPIRE_MINUTES` setting in the application configuration.

### Token Payload

The JWT token contains:
```json
{
  "sub": "123e4567-e89b-12d3-a456-426614174000",
  "username": "admin",
  "exp": 1704153600
}
```

Fields:
- `sub` - Subject (user ID)
- `username` - Username
- `exp` - Expiration timestamp (Unix timestamp)

### Handling Token Expiration

When a token expires, the API returns:

**Status:** 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

Clients should:
1. Detect 401 responses
2. Clear the expired token
3. Redirect user to login page
4. Prompt user to re-authenticate

### Token Refresh

Currently, the API does not support token refresh. Users must re-authenticate when their token expires.

**Future Enhancement:** A refresh token mechanism could be implemented for better UX.

## User Roles and Authorization

### Available Roles

The system supports three user roles:

1. **admin** - Full system access
2. **coordinator** - Scheduling and management access
3. **faculty** - Limited read access (planned for future)

### Role-Based Access Control

Different endpoints require different authorization levels:

#### Public Endpoints (No Authentication)

- `GET /` - Health check
- `GET /health` - Health check
- `POST /api/auth/register` - First user only; subsequent registrations require admin

#### Authenticated Endpoints (Any Active User)

- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout
- `GET /api/people` - List people (public read access)
- `GET /api/people/{id}` - Get person details
- `GET /api/blocks` - List blocks
- `GET /api/rotation-templates` - List templates
- `GET /api/schedule/validate` - Validate schedule
- `GET /api/schedule/{start_date}/{end_date}` - View schedule

#### Scheduler Endpoints (Admin or Coordinator Only)

- `POST /api/assignments` - Create assignment
- `PUT /api/assignments/{id}` - Update assignment
- `DELETE /api/assignments/{id}` - Delete assignment
- `DELETE /api/assignments` - Bulk delete assignments
- `POST /api/schedule/generate` - Generate schedule
- `POST /api/schedule/emergency-coverage` - Handle emergency coverage

#### Admin-Only Endpoints

- `GET /api/auth/users` - List all users
- `POST /api/auth/register` - Create new users (after first user)

### Protected vs Public Endpoints

#### Public Endpoints

These endpoints do not require authentication:
- Health check endpoints
- Initial user registration (when no users exist)

#### Protected Endpoints

All other endpoints require a valid JWT token:
- User management
- People (Create, Update, Delete)
- Blocks (Create, Delete)
- Rotation templates (Create, Update, Delete)
- Absences (all operations)
- Assignments (all operations)
- Schedule generation and validation
- Settings management
- Data export

### Authorization Implementation

The API uses FastAPI dependency injection for authorization:

```python
# Require any authenticated user
@router.get("/people")
def list_people(current_user: User = Depends(get_current_active_user)):
    ...

# Require scheduler role (admin or coordinator)
@router.post("/assignments")
def create_assignment(current_user: User = Depends(get_scheduler_user)):
    ...

# Require admin role
@router.get("/auth/users")
def list_users(current_user: User = Depends(get_admin_user)):
    ...
```

## Authorization Headers

### Standard Authorization Header

```
Authorization: Bearer <jwt_token>
```

Example:
```bash
curl -X GET http://localhost:8000/api/people \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Missing Authorization

If the `Authorization` header is missing:

**Status:** 401 Unauthorized

```json
{
  "detail": "Not authenticated"
}
```

### Invalid Token

If the token is invalid or malformed:

**Status:** 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

### Insufficient Permissions

If the user lacks required permissions:

**Status:** 403 Forbidden

```json
{
  "detail": "Admin access required to create users"
}
```

Or:

```json
{
  "detail": "Scheduler role (admin or coordinator) required"
}
```

## Session Expiration Handling

### Client-Side Handling

Recommended approach for handling session expiration:

```javascript
// Example: Axios interceptor for handling 401 responses
axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // Clear token from storage
      localStorage.removeItem('access_token');

      // Redirect to login
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### Proactive Token Checking

Check token expiration before making requests:

```javascript
function isTokenExpired(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expiry = payload.exp * 1000; // Convert to milliseconds
    return Date.now() >= expiry;
  } catch (e) {
    return true;
  }
}

function getToken() {
  const token = localStorage.getItem('access_token');

  if (!token || isTokenExpired(token)) {
    // Redirect to login
    window.location.href = '/login';
    return null;
  }

  return token;
}
```

### Auto-Renewal Strategy

Since the API doesn't support refresh tokens yet, consider:

1. **Short-lived tokens** - Keep tokens short-lived (e.g., 1 hour) for security
2. **Background renewal** - Have the client renew tokens periodically by re-authenticating
3. **Activity tracking** - Only renew if the user is active

## Security Best Practices

### Token Storage

**Browser Applications:**
- Store tokens in memory (React state, Vue store) for maximum security
- If persistence is needed, use `sessionStorage` (cleared on tab close)
- Avoid `localStorage` for sensitive applications
- Never store in cookies without `httpOnly` and `secure` flags

**Mobile Applications:**
- Use secure storage mechanisms (Keychain on iOS, KeyStore on Android)
- Never store in plain text files or shared preferences

### HTTPS Requirement

**Production Deployment:**
- Always use HTTPS to encrypt tokens in transit
- Configure HSTS (HTTP Strict Transport Security)
- Use certificate pinning for mobile apps

### Token Transmission

- Only send tokens in the `Authorization` header
- Never send tokens in URL query parameters
- Never log tokens in client-side code

### Password Requirements

When registering users, enforce strong passwords:
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, and special characters
- Not commonly used passwords

### CORS Configuration

The API is configured to accept requests from specific origins:

**Default:** `http://localhost:3000`

For production:
```python
CORS_ORIGINS=["https://yourapp.example.com"]
```

Configure via environment variables in `.env` file.

## Error Handling

### Common Authentication Errors

**401 Unauthorized - Missing Token:**
```json
{
  "detail": "Not authenticated"
}
```

**401 Unauthorized - Invalid Token:**
```json
{
  "detail": "Could not validate credentials"
}
```

**401 Unauthorized - Expired Token:**
```json
{
  "detail": "Could not validate credentials"
}
```

**401 Unauthorized - Inactive User:**
```json
{
  "detail": "Inactive user"
}
```

**403 Forbidden - Insufficient Permissions:**
```json
{
  "detail": "Admin access required to create users"
}
```

### Error Response Format

All authentication errors follow the FastAPI standard error format:

```json
{
  "detail": "Error message string"
}
```

For validation errors:
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## User Management

### List All Users (Admin Only)

```bash
curl -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

Response:
```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "admin",
    "email": "admin@example.com",
    "role": "admin",
    "is_active": true
  },
  {
    "id": "456e7890-e89b-12d3-a456-426614174000",
    "username": "coordinator1",
    "email": "coordinator@example.com",
    "role": "coordinator",
    "is_active": true
  }
]
```

### User Account States

- **Active** (`is_active: true`) - User can authenticate and access the system
- **Inactive** (`is_active: false`) - User cannot authenticate (planned feature)

Currently, all users are active by default. Future enhancements will add:
- User deactivation
- Password reset
- Email verification
- Multi-factor authentication

## Integration Examples

### JavaScript/TypeScript (Fetch API)

```typescript
// Login
async function login(username: string, password: string): Promise<string> {
  const response = await fetch('http://localhost:8000/api/auth/login/json', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ username, password }),
  });

  if (!response.ok) {
    throw new Error('Login failed');
  }

  const data = await response.json();
  return data.access_token;
}

// Make authenticated request
async function fetchPeople(token: string) {
  const response = await fetch('http://localhost:8000/api/people', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (response.status === 401) {
    // Token expired, redirect to login
    window.location.href = '/login';
    return;
  }

  return response.json();
}
```

### Python (Requests)

```python
import requests

# Login
def login(username: str, password: str) -> str:
    response = requests.post(
        'http://localhost:8000/api/auth/login/json',
        json={'username': username, 'password': password}
    )
    response.raise_for_status()
    return response.json()['access_token']

# Make authenticated request
def get_people(token: str):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        'http://localhost:8000/api/people',
        headers=headers
    )

    if response.status_code == 401:
        # Token expired
        raise Exception('Authentication required')

    response.raise_for_status()
    return response.json()
```

### cURL

```bash
# Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}' \
  | jq -r '.access_token')

# Use token for authenticated requests
curl -X GET http://localhost:8000/api/people \
  -H "Authorization: Bearer $TOKEN"
```

## Testing Authentication

### Swagger UI

The API includes interactive documentation with built-in authentication:

1. Navigate to http://localhost:8000/docs
2. Click the "Authorize" button (lock icon)
3. Enter your credentials in the OAuth2 form
4. Click "Authorize"
5. Try out endpoints with automatic token injection

### Postman

1. Create a new request
2. Go to the "Authorization" tab
3. Select "Bearer Token" type
4. Paste your JWT token
5. Send the request

Or use Postman's OAuth2 feature:
1. Authorization type: OAuth 2.0
2. Grant type: Password Credentials
3. Access Token URL: http://localhost:8000/api/auth/login
4. Username: your-username
5. Password: your-password
6. Client ID: (leave empty)
7. Client Secret: (leave empty)

## Future Enhancements

Planned authentication improvements:

1. **Refresh Tokens** - Long-lived tokens for renewing access tokens
2. **Password Reset** - Email-based password reset flow
3. **Email Verification** - Verify user email addresses
4. **Multi-Factor Authentication (MFA)** - TOTP-based 2FA
5. **OAuth2 Integration** - Login with Google, Microsoft, etc.
6. **API Keys** - Long-lived API keys for service accounts
7. **Token Blacklist** - Revoke tokens before expiration
8. **Audit Logging** - Track authentication events
9. **Rate Limiting** - Prevent brute force attacks
10. **Password Policies** - Enforce complexity and rotation

## Troubleshooting

### "Not authenticated" Error

**Cause:** Missing or malformed Authorization header

**Solution:**
- Ensure the Authorization header is present
- Check the format: `Authorization: Bearer <token>`
- Verify no extra spaces or characters

### "Could not validate credentials" Error

**Cause:** Invalid, expired, or tampered token

**Solution:**
- Check if token has expired
- Try logging in again to get a new token
- Verify the SECRET_KEY matches between requests

### "Inactive user" Error

**Cause:** User account is deactivated

**Solution:**
- Contact administrator to reactivate account
- Check user status in database

### "Admin access required" Error

**Cause:** Insufficient permissions for the operation

**Solution:**
- Verify your user role (admin, coordinator, faculty)
- Contact administrator for role upgrade if needed
- Use an admin account for admin-only operations
