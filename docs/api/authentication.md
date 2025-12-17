***REMOVED*** Authentication

API authentication and authorization.

---

***REMOVED******REMOVED*** Overview

The API uses JWT (JSON Web Tokens) for authentication.

---

***REMOVED******REMOVED*** Login

<span class="endpoint-badge post">POST</span> `/api/auth/login`

***REMOVED******REMOVED******REMOVED*** Request

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

***REMOVED******REMOVED******REMOVED*** Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

***REMOVED******REMOVED*** Registration

<span class="endpoint-badge post">POST</span> `/api/auth/register`

***REMOVED******REMOVED******REMOVED*** Request

```json
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "full_name": "New User",
  "role": "resident"
}
```

---

***REMOVED******REMOVED*** Using Tokens

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/v1/people
```

---

***REMOVED******REMOVED*** Token Refresh

Tokens expire after the configured duration (default: 24 hours).

Request a new token by logging in again.

---

***REMOVED******REMOVED*** Logout

<span class="endpoint-badge post">POST</span> `/api/auth/logout`

Invalidates the current token.

---

***REMOVED******REMOVED*** Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5/minute |
| `/auth/register` | 3/minute |
