# Authentication

API authentication and authorization.

---

## Overview

The API uses JWT (JSON Web Tokens) for authentication with a dual-token system:

- **Access Token**: Short-lived (30 minutes), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

### Security Features

<<<<<<< HEAD
- **httpOnly Cookies**: Access tokens are stored in httpOnly cookies (XSS-resistant)
=======
- **httpOnly PGY2-01ies**: Access tokens are stored in httpOnly cookies (XSS-resistant)
>>>>>>> origin/docs/session-14-summary
- **Token Type Validation**: Refresh tokens cannot be used as access tokens (prevents privilege escalation)
- **Token Rotation**: Refresh tokens are rotated on use and old tokens are blacklisted
- **Token Blacklisting**: Logged out and rotated tokens are permanently invalidated
- **Rate Limiting**: Brute force protection on auth endpoints

---

## Login

<span class="endpoint-badge post">POST</span> `/api/auth/login`

Authenticate using OAuth2 form data.

### Request (Form Data)

```
username=user@example.com&password=your_password
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

The access token is also set as an httpOnly cookie for browser-based clients.

---

## Login (JSON)

<span class="endpoint-badge post">POST</span> `/api/auth/login/json`

Alternative JSON-based authentication.

### Request

```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## Registration

<span class="endpoint-badge post">POST</span> `/api/auth/register`

### Request

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password",
  "role": "coordinator"
}
```

### Notes

- First user automatically becomes admin
- Subsequent registrations require admin authentication

---

## Using Tokens

### Browser Clients

The access token is automatically sent via httpOnly cookie. No additional headers needed.

### API Clients

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/auth/me
```

---

## Token Refresh

<span class="endpoint-badge post">POST</span> `/api/auth/refresh`

Exchange a refresh token for a new access token.

### Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Security Behavior

When `REFRESH_TOKEN_ROTATE=true` (default):

1. A new refresh token is issued with each refresh
2. The old refresh token is **immediately blacklisted**
3. Reusing an old refresh token returns 401 Unauthorized

This prevents token theft attacks where an attacker tries to reuse a stolen refresh token.

---

## Get Current User

<span class="endpoint-badge get">GET</span> `/api/auth/me`

Returns the authenticated user's information.

### Response

```json
{
  "id": "uuid",
  "username": "user@example.com",
  "email": "user@example.com",
  "role": "coordinator",
  "is_active": true
}
```

---

## Logout

<span class="endpoint-badge post">POST</span> `/api/auth/logout`

Invalidates the current token by adding it to the blacklist.

### Response

```json
{
  "message": "Successfully logged out"
}
```

---

## List Users (Admin)

<span class="endpoint-badge get">GET</span> `/api/auth/users`

Returns all users. Requires admin role.

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5/minute |
| `/auth/login/json` | 5/minute |
| `/auth/register` | 3/minute |

---

## Token Structure

### Access Token Claims

| Claim | Description |
|-------|-------------|
| `sub` | User ID (UUID) |
| `username` | Username |
| `exp` | Expiration timestamp |
| `iat` | Issued at timestamp |
| `jti` | Unique token ID (for blacklisting) |

### Refresh Token Claims

| Claim | Description |
|-------|-------------|
| `sub` | User ID (UUID) |
| `username` | Username |
| `exp` | Expiration timestamp |
| `iat` | Issued at timestamp |
| `jti` | Unique token ID (for blacklisting) |
| `type` | Always `"refresh"` |

**Important**: The `type` field distinguishes refresh tokens from access tokens. Refresh tokens with `type="refresh"` are rejected when used to access protected endpoints.

---

## Security Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access token lifetime (minutes) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `REFRESH_TOKEN_ROTATE` | true | Enable refresh token rotation |

---

## Error Responses

| Status | Description |
|--------|-------------|
| 401 | Invalid credentials or token |
| 403 | Insufficient permissions |
| 422 | Validation error |
| 429 | Rate limit exceeded |
