# Authentication API Reference

**Endpoint Prefix:** `/api/auth`

## Overview

The Authentication API provides JWT-based authentication with secure token management, rate limiting, and XSS protection via httpOnly cookies.

### Key Features

- **OAuth2 Password Flow**: Standard username/password authentication
- **JWT Tokens**: Access and refresh tokens with configurable expiration
- **Token Rotation**: Optional refresh token rotation for enhanced security
- **Rate Limiting**: Brute force protection on login and registration
- **XSS Protection**: Access tokens stored in httpOnly cookies
- **Token Blacklisting**: Logout support via token blacklist

### Security Model

- **Access Token**: Short-lived token (default: 30 minutes), stored in httpOnly cookie
- **Refresh Token**: Long-lived token (default: 7 days), returned in response body
- **Token Rotation**: When enabled, old refresh tokens are immediately blacklisted on refresh
- **HTTP Only Cookies**: Access token cookies cannot be accessed by JavaScript (XSS protection)

---

## Endpoints

### POST /login

Authenticate user with OAuth2 password form and return JWT tokens.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourpassword"
```

**Form Data:**
- `username` (required): User email or username
- `password` (required): User password

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Cookies Set:**
```
Set-Cookie: access_token=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...; HttpOnly; Secure; SameSite=Lax; Max-Age=1800; Path=/
```

**Error Responses:**

- **401 Unauthorized**: Invalid credentials
  ```json
  {
    "detail": "Incorrect email or password"
  }
  ```

- **429 Too Many Requests**: Rate limit exceeded
  ```json
  {
    "detail": "Rate limit exceeded. Maximum 5 login attempts per 15 minutes"
  }
  ```

**Rate Limiting:**
- Max 5 attempts per 15 minutes per IP/username
- Configurable via `RATE_LIMIT_LOGIN_ATTEMPTS` and `RATE_LIMIT_LOGIN_WINDOW`

---

### POST /login/json

Authenticate user with JSON body (alternative to form-based login).

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/login/json \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "yourpassword"
  }'
```

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
Same as `/login` endpoint.

**Error Responses:**
Same as `/login` endpoint.

---

### POST /logout

Logout current user by blacklisting their token.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Cookie: access_token=Bearer <ACCESS_TOKEN>"
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

**Cookies Deleted:**
```
Set-Cookie: access_token=; Expires=Thu, 01 Jan 1970 00:00:00 UTC; Path=/
```

**Security Notes:**
- Token is added to blacklist and will be rejected on future requests
- httpOnly cookie is deleted from client
- User must login again to obtain new tokens

---

### POST /refresh

Exchange a refresh token for a new access token (and optionally a new refresh token).

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Request Body:**
```json
{
  "refresh_token": "string"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Cookies Set:**
```
Set-Cookie: access_token=Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...; HttpOnly; Secure; SameSite=Lax; Max-Age=1800; Path=/
```

**Token Rotation Behavior:**

When `REFRESH_TOKEN_ROTATE=true`:
1. Old refresh token is immediately blacklisted
2. New refresh token is returned
3. Old token cannot be reused (protects against token theft)

When `REFRESH_TOKEN_ROTATE=false`:
1. Same refresh token is returned
2. Token rotation is disabled

**Error Responses:**

- **401 Unauthorized**: Invalid or expired refresh token
  ```json
  {
    "detail": "Invalid or expired refresh token",
    "headers": {
      "WWW-Authenticate": "Bearer"
    }
  }
  ```

- **401 Unauthorized**: User inactive
  ```json
  {
    "detail": "User not found or inactive",
    "headers": {
      "WWW-Authenticate": "Bearer"
    }
  }
  ```

---

### GET /me

Get current authenticated user information.

**Request:**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "email": "user@example.com",
  "is_active": true,
  "created_at": "2025-12-31T12:00:00Z"
}
```

**Error Responses:**

- **401 Unauthorized**: Invalid or missing token
  ```json
  {
    "detail": "Not authenticated",
    "headers": {
      "WWW-Authenticate": "Bearer"
    }
  }
  ```

---

### POST /register

Register a new user account.

**Request:**
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser@example.com",
    "email": "newuser@example.com",
    "password": "SecurePassword123!"
  }'
```

**Request Body:**
```json
{
  "username": "string",
  "email": "string (valid email)",
  "password": "string (min 12 chars, with uppercase, lowercase, number, special char)"
}
```

**Response (201):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "newuser@example.com",
  "email": "newuser@example.com",
  "is_active": true,
  "created_at": "2025-12-31T12:00:00Z"
}
```

**Business Rules:**

- **First User Becomes Admin**: If no users exist, the first registered user is granted admin role
- **Admin-Only After First User**: After the first user, only admins can create new users
- **Password Requirements**:
  - Minimum 12 characters
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character (!@#$%^&*)

**Error Responses:**

- **400 Bad Request**: Password doesn't meet requirements
  ```json
  {
    "detail": "Password must be at least 12 characters with uppercase, lowercase, number, and special character"
  }
  ```

- **400 Bad Request**: User already exists
  ```json
  {
    "detail": "User with this email already exists"
  }
  ```

- **403 Forbidden**: User not admin (when trying to create user after first user)
  ```json
  {
    "detail": "Only administrators can create new users"
  }
  ```

- **429 Too Many Requests**: Rate limit exceeded
  ```json
  {
    "detail": "Rate limit exceeded. Maximum 10 registration attempts per hour"
  }
  ```

**Rate Limiting:**
- Max 10 registration attempts per hour per IP
- Configurable via `RATE_LIMIT_REGISTER_ATTEMPTS` and `RATE_LIMIT_REGISTER_WINDOW`

---

### GET /users

List all users (admin only).

**Request:**
```bash
curl -X GET http://localhost:8000/api/auth/users \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin@example.com",
    "email": "admin@example.com",
    "is_active": true,
    "created_at": "2025-12-31T12:00:00Z"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "username": "user@example.com",
    "email": "user@example.com",
    "is_active": true,
    "created_at": "2025-12-31T13:00:00Z"
  }
]
```

**Error Responses:**

- **401 Unauthorized**: Not authenticated
  ```json
  {
    "detail": "Not authenticated"
  }
  ```

- **403 Forbidden**: Not admin
  ```json
  {
    "detail": "Only administrators can list users"
  }
  ```

---

## Authentication Methods

### Cookie-Based Authentication

The API automatically sets and uses httpOnly cookies for access tokens:

```bash
# Login sets the cookie automatically
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=pass"

# Subsequent requests automatically include the cookie
curl -X GET http://localhost:8000/api/auth/me
```

### Bearer Token Authentication

Manually provide the access token in the Authorization header:

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| 400 | Bad Request | Invalid request format or validation error |
| 401 | Unauthorized | Authentication failed or invalid token |
| 403 | Forbidden | Insufficient permissions (e.g., not admin) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

---

## Configuration

Authentication behavior is configured via environment variables:

```env
# Token expiration (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Token rotation (security enhancement)
REFRESH_TOKEN_ROTATE=true

# Rate limiting
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW=900  # 15 minutes

RATE_LIMIT_REGISTER_ATTEMPTS=10
RATE_LIMIT_REGISTER_WINDOW=3600  # 1 hour

# Password requirements
PASSWORD_MIN_LENGTH=12
PASSWORD_REQUIRE_UPPERCASE=true
PASSWORD_REQUIRE_LOWERCASE=true
PASSWORD_REQUIRE_NUMBERS=true
PASSWORD_REQUIRE_SPECIAL_CHARS=true

# Security
SECRET_KEY=<generated-secret-key>  # Min 32 characters
DEBUG=false  # Must be false in production
```

---

## Token Structure

### Access Token (JWT)

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "jti": "550e8400-e29b-41d4-a716-446655440002",
  "exp": 1704067200,
  "iat": 1704063600
}
```

### Refresh Token (JWT)

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000",
  "username": "user@example.com",
  "jti": "550e8400-e29b-41d4-a716-446655440003",
  "exp": 1704672000,
  "iat": 1704063600
}
```

---

## Best Practices

### For Frontend Applications

1. **Login Flow**:
   ```javascript
   const response = await fetch('/api/auth/login/json', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     credentials: 'include',  // Include cookies
     body: JSON.stringify({
       username: 'user@example.com',
       password: 'password'
     })
   });

   const data = await response.json();
   // Store refresh_token in secure storage (localStorage, sessionStorage, etc.)
   localStorage.setItem('refresh_token', data.refresh_token);
   ```

2. **Authenticated Requests**:
   ```javascript
   const response = await fetch('/api/auth/me', {
     credentials: 'include'  // Include httpOnly cookie
   });
   ```

3. **Token Refresh**:
   ```javascript
   const refreshResponse = await fetch('/api/auth/refresh', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({
       refresh_token: localStorage.getItem('refresh_token')
     })
   });

   const newData = await refreshResponse.json();
   localStorage.setItem('refresh_token', newData.refresh_token);
   ```

4. **Logout Flow**:
   ```javascript
   await fetch('/api/auth/logout', {
     method: 'POST',
     credentials: 'include'
   });
   localStorage.removeItem('refresh_token');
   ```

### For CLI/Scripts

1. **Get Tokens**:
   ```bash
   RESPONSE=$(curl -X POST http://localhost:8000/api/auth/login/json \
     -H "Content-Type: application/json" \
     -d '{"username":"user@example.com","password":"pass"}')

   ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')
   REFRESH_TOKEN=$(echo $RESPONSE | jq -r '.refresh_token')
   ```

2. **Use Access Token**:
   ```bash
   curl -X GET http://localhost:8000/api/auth/me \
     -H "Authorization: Bearer $ACCESS_TOKEN"
   ```

3. **Refresh Token**:
   ```bash
   RESPONSE=$(curl -X POST http://localhost:8000/api/auth/refresh \
     -H "Content-Type: application/json" \
     -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}")

   ACCESS_TOKEN=$(echo $RESPONSE | jq -r '.access_token')
   REFRESH_TOKEN=$(echo $RESPONSE | jq -r '.refresh_token')
   ```

---

## Troubleshooting

### "Invalid or expired refresh token"

**Cause:** Refresh token has expired (default: 7 days) or was blacklisted

**Solution:** Login again to get new tokens

### "Rate limit exceeded"

**Cause:** Too many login attempts from your IP

**Solution:** Wait 15 minutes and try again, or check if credentials are correct

### "Only administrators can create new users"

**Cause:** You don't have admin role

**Solution:** Ask an admin to create the account, or register if you're the first user

### "Not authenticated"

**Cause:** Missing or invalid access token

**Solution:**
1. Check that the token is in the Authorization header or cookie
2. Verify the token hasn't expired
3. Try refreshing the token
4. Login again if all else fails

---

## Security Considerations

### XSS Protection

- **httpOnly Cookies**: Access token is stored in an httpOnly cookie that JavaScript cannot access
- **CORS**: Proper CORS configuration prevents cross-origin token theft
- **SameSite=Lax**: Cookies are only sent with same-site and top-level navigation requests

### CSRF Protection

- **POST Requests**: Use standard CSRF protection headers
- **Cookie Attributes**: SameSite=Lax mitigates CSRF attacks

### Token Theft Prevention

1. **Token Rotation**: Enable `REFRESH_TOKEN_ROTATE=true` to rotate refresh tokens on use
2. **Short Expiration**: Use short access token expiration (default: 30 minutes)
3. **Secure Transport**: Always use HTTPS in production

### Password Security

- **Minimum Length**: 12 characters required
- **Complexity Requirements**: Mix of uppercase, lowercase, numbers, special characters
- **Hashing**: Passwords hashed with bcrypt
- **Never Logged**: Passwords never appear in logs

---

## Related Documentation

- [Authentication Security Best Practices](../security/AUTHENTICATION_SECURITY.md)
- [Rate Limiting Configuration](../admin-manual/rate-limiting.md)
- [JWT Token Management](../development/JWT_MANAGEMENT.md)
