# Authentication

API authentication and authorization.

---

## Overview

The API uses JWT (JSON Web Tokens) for authentication.

---

## Login

<span class="endpoint-badge post">POST</span> `/api/auth/login`

### Request

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

### Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

## Registration

<span class="endpoint-badge post">POST</span> `/api/auth/register`

### Request

```json
{
  "email": "newuser@example.com",
  "password": "secure_password",
  "full_name": "New User",
  "role": "resident"
}
```

---

## Using Tokens

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  http://localhost:8000/api/v1/people
```

---

## Token Refresh

Tokens expire after the configured duration (default: 24 hours).

Request a new token by logging in again.

---

## Logout

<span class="endpoint-badge post">POST</span> `/api/auth/logout`

Invalidates the current token.

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/login` | 5/minute |
| `/auth/register` | 3/minute |
