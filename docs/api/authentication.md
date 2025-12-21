***REMOVED*** Authentication

API authentication and authorization.

---

***REMOVED******REMOVED*** Overview

The API uses JWT (JSON Web Tokens) for authentication with a dual-token system:

- **Access Token**: Short-lived (30 minutes), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

***REMOVED******REMOVED******REMOVED*** Security Features

- **httpOnly PGY2-01ies**: Access tokens are stored in httpOnly cookies (XSS-resistant)
- **Token Type Validation**: Refresh tokens cannot be used as access tokens (prevents privilege escalation)
- **Token Rotation**: Refresh tokens are rotated on use and old tokens are blacklisted
- **Token Blacklisting**: Logged out and rotated tokens are permanently invalidated
- **Rate Limiting**: Brute force protection on auth endpoints

---

***REMOVED******REMOVED*** Login

<span class="endpoint-badge post">POST</span> `/api/auth/login`

Authenticate using OAuth2 form data.

***REMOVED******REMOVED******REMOVED*** Request (Form Data)

```
username=user@example.com&password=your_password
```

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

The access token is also set as an httpOnly cookie for browser-based clients.

---

***REMOVED******REMOVED*** Login (JSON)

<span class="endpoint-badge post">POST</span> `/api/auth/login/json`

Alternative JSON-based authentication.

***REMOVED******REMOVED******REMOVED*** Request

```json
{
  "username": "user@example.com",
  "password": "your_password"
}
```

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

***REMOVED******REMOVED*** Registration

<span class="endpoint-badge post">POST</span> `/api/auth/register`

***REMOVED******REMOVED******REMOVED*** Request

```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password",
  "role": "coordinator"
}
```

***REMOVED******REMOVED******REMOVED*** Notes

- First user automatically becomes admin
- Subsequent registrations require admin authentication

---

***REMOVED******REMOVED*** Using Tokens

***REMOVED******REMOVED******REMOVED*** Browser Clients

The access token is automatically sent via httpOnly cookie. No additional headers needed.

***REMOVED******REMOVED******REMOVED*** API Clients

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/auth/me
```

---

***REMOVED******REMOVED*** Token Refresh

<span class="endpoint-badge post">POST</span> `/api/auth/refresh`

Exchange a refresh token for a new access token.

***REMOVED******REMOVED******REMOVED*** Request

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

***REMOVED******REMOVED******REMOVED*** Security Behavior

When `REFRESH_TOKEN_ROTATE=true` (default):

1. A new refresh token is issued with each refresh
2. The old refresh token is **immediately blacklisted**
3. Reusing an old refresh token returns 401 Unauthorized

This prevents token theft attacks where an attacker tries to reuse a stolen refresh token.

---

***REMOVED******REMOVED*** Get Current User

<span class="endpoint-badge get">GET</span> `/api/auth/me`

Returns the authenticated user's information.

***REMOVED******REMOVED******REMOVED*** Response

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

***REMOVED******REMOVED*** Logout

<span class="endpoint-badge post">POST</span> `/api/auth/logout`

Invalidates the current token by adding it to the blacklist.

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "message": "Successfully logged out"
}
```

---

***REMOVED******REMOVED*** List Users (Admin)

<span class="endpoint-badge get">GET</span> `/api/auth/users`

Returns all users. Requires admin role.

---

***REMOVED******REMOVED*** Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5/minute |
| `/auth/login/json` | 5/minute |
| `/auth/register` | 3/minute |

---

***REMOVED******REMOVED*** Token Structure

***REMOVED******REMOVED******REMOVED*** Access Token Claims

| Claim | Description |
|-------|-------------|
| `sub` | User ID (UUID) |
| `username` | Username |
| `exp` | Expiration timestamp |
| `iat` | Issued at timestamp |
| `jti` | Unique token ID (for blacklisting) |

***REMOVED******REMOVED******REMOVED*** Refresh Token Claims

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

***REMOVED******REMOVED*** Security Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access token lifetime (minutes) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token lifetime |
| `REFRESH_TOKEN_ROTATE` | true | Enable refresh token rotation |

---

***REMOVED******REMOVED*** Error Responses

| Status | Description |
|--------|-------------|
| 401 | Invalid credentials or token |
| 403 | Insufficient permissions |
| 422 | Validation error |
| 429 | Rate limit exceeded |
