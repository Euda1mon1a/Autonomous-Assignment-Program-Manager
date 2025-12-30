# Audience-Scoped JWT Authentication Usage Guide

> **Purpose**: Documentation for using audience-scoped JWT tokens for elevated agent operations
> **Created**: 2025-12-29
> **Security Level**: Confidential - Contains authentication patterns

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [API Reference](#api-reference)
5. [Backend Integration](#backend-integration)
6. [Frontend Integration](#frontend-integration)
7. [Security Considerations](#security-considerations)
8. [Testing](#testing)
9. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Audience-Scoped Authentication?

Audience-scoped JWT tokens are **short-lived, operation-specific tokens** that grant elevated permissions for sensitive operations. Unlike regular access tokens which grant general API access, audience tokens are scoped to a specific operation type (audience).

### Why Use Audience Tokens?

**Problem**: Normal access tokens are long-lived (15 minutes) and grant broad permissions. For AI agents performing sensitive operations (schedule generation, job abortion, database backups), this creates unnecessary risk.

**Solution**: Audience tokens are:
- **Short-lived**: 30 seconds to 10 minutes (default: 2 minutes)
- **Operation-scoped**: Only valid for specific operation type
- **Immediately revocable**: Can be blacklisted if compromised
- **Fully audited**: All creation and usage logged

### Use Cases

| Operation | Audience | Why Needed |
|-----------|----------|------------|
| Abort running solver | `jobs.abort` | Prevents accidental termination |
| Generate schedules | `schedule.generate` | Resource-intensive operation |
| Execute swaps | `swap.execute` | Modifies production data |
| Database backup | `database.backup` | High-privilege operation |
| Admin impersonation | `admin.impersonate` | Security-critical |

---

## Architecture

### Token Structure

```json
{
  "sub": "user-uuid",           // User ID
  "aud": "jobs.abort",          // Audience (operation scope)
  "exp": 1735489800,            // Expiration timestamp
  "iat": 1735489680,            // Issued at timestamp
  "jti": "unique-token-id",     // JWT ID for revocation
  "type": "audience"            // Token type
}
```

### Security Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant AuthAPI
    participant OperationAPI
    participant Database

    User->>Frontend: Initiate sensitive operation
    Frontend->>AuthAPI: POST /api/audience-tokens/tokens
    Note right of AuthAPI: Validates user<br/>access token
    AuthAPI->>Database: Log token creation
    AuthAPI-->>Frontend: Audience token (2 min TTL)
    Frontend->>OperationAPI: POST /jobs/{id}/abort<br/>(with audience token)
    Note right of OperationAPI: Validates audience<br/>matches operation
    OperationAPI->>Database: Check blacklist
    OperationAPI->>Database: Execute operation
    OperationAPI->>Database: Log operation
    OperationAPI-->>Frontend: Success
    Frontend->>AuthAPI: POST /api/audience-tokens/revoke
    AuthAPI->>Database: Blacklist token
```

### Available Audiences

```python
VALID_AUDIENCES = {
    "jobs.abort": "Abort running background jobs",
    "jobs.kill": "Force-kill stuck background jobs",
    "schedule.generate": "Generate new schedules",
    "schedule.regenerate": "Regenerate existing schedules",
    "schedule.delete": "Delete schedules",
    "swap.execute": "Execute schedule swaps",
    "swap.rollback": "Rollback schedule swaps",
    "solver.abort": "Abort running solver operations",
    "database.backup": "Create database backups",
    "database.restore": "Restore from database backups",
    "resilience.override": "Override resilience framework limits",
    "admin.impersonate": "Impersonate other users (admin)",
    "audit.export": "Export audit logs",
}
```

---

## Quick Start

### 1. Backend: Protect an Endpoint

```python
# backend/app/api/routes/jobs.py
from fastapi import APIRouter, Depends
from app.core.audience_auth import require_audience, AudienceTokenPayload
from app.core.security import get_current_active_user
from app.models.user import User

router = APIRouter()

@router.post("/jobs/{job_id}/abort")
async def abort_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    audience_token: AudienceTokenPayload = Depends(require_audience("jobs.abort")),
):
    """Abort a running job (requires audience token)."""

    # Verify token belongs to authenticated user
    if audience_token.sub != str(current_user.id):
        raise HTTPException(403, "Token mismatch")

    # Execute operation
    await abort_job_by_id(job_id)

    return {"success": True, "job_id": job_id}
```

### 2. Frontend: Request and Use Token

```typescript
// frontend/lib/audienceAuth.ts
import { api } from './api';

interface AudienceToken {
  token: string;
  audience: string;
  expires_at: string;
  ttl_seconds: number;
}

export async function requestAudienceToken(
  audience: string,
  ttl_seconds: number = 120
): Promise<AudienceToken> {
  const response = await api.post('/audience-tokens/tokens', {
    audience,
    ttl_seconds,
  });
  return response.data;
}

export async function abortJobWithToken(jobId: string) {
  // Step 1: Request audience token
  const { token } = await requestAudienceToken('jobs.abort', 120);

  try {
    // Step 2: Use token for operation
    const response = await api.post(
      `/jobs/${jobId}/abort`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } finally {
    // Step 3: Token is short-lived, but can be explicitly revoked
    // (Optional - token expires in 2 minutes anyway)
  }
}
```

### 3. Test the Integration

```bash
# 1. Authenticate and get access token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}' \
  -c cookies.txt

# 2. Request audience token
curl -X POST http://localhost:8000/api/audience-tokens/tokens \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{"audience": "jobs.abort", "ttl_seconds": 120}'

# Response:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "audience": "jobs.abort",
#   "expires_at": "2025-12-29T15:30:00Z",
#   "ttl_seconds": 120
# }

# 3. Use audience token for operation
curl -X POST http://localhost:8000/api/jobs/job-123/abort \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

---

## API Reference

### List Available Audiences

```http
GET /api/audience-tokens/audiences
```

**Authentication**: Required (access token)

**Response**:
```json
{
  "audiences": {
    "jobs.abort": "Abort running background jobs",
    "schedule.generate": "Generate new schedules",
    "swap.execute": "Execute schedule swaps"
  }
}
```

### Request Audience Token

```http
POST /api/audience-tokens/tokens
```

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "audience": "jobs.abort",
  "ttl_seconds": 120
}
```

**Response**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "audience": "jobs.abort",
  "expires_at": "2025-12-29T15:30:00Z",
  "ttl_seconds": 120
}
```

**Errors**:
- `400`: Invalid audience or TTL out of range (30-600 seconds)
- `401`: Not authenticated
- `500`: Token creation failed

### Revoke Audience Token

```http
POST /api/audience-tokens/revoke
```

**Authentication**: Required (access token)

**Request Body**:
```json
{
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "reason": "operation_completed"
}
```

**Response**:
```json
{
  "success": true,
  "jti": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "message": "Token successfully revoked"
}
```

---

## Backend Integration

### Protecting Endpoints

#### Option 1: Using Dependency (Recommended)

```python
from fastapi import Depends
from app.core.audience_auth import require_audience, AudienceTokenPayload

@router.post("/schedule/generate")
async def generate_schedule(
    audience_token: AudienceTokenPayload = Depends(require_audience("schedule.generate"))
):
    user_id = audience_token.sub  # Access user ID
    # Execute operation
    ...
```

#### Option 2: Manual Validation

```python
from app.core.audience_auth import get_audience_token
from fastapi import Header

@router.post("/schedule/generate")
async def generate_schedule(
    authorization: str = Header(...),
    db: Session = Depends(get_db),
):
    payload = get_audience_token(authorization, "schedule.generate", db)
    user_id = payload.sub
    # Execute operation
    ...
```

### Creating Tokens Programmatically

```python
from app.core.audience_auth import create_audience_token

# In a service or route
def request_elevated_permission(user_id: str, operation: str):
    token_response = create_audience_token(
        user_id=user_id,
        audience=operation,
        ttl_seconds=180,  # 3 minutes
    )
    return token_response.token
```

### Revoking Tokens

```python
from app.core.audience_auth import revoke_audience_token
from datetime import datetime

def cleanup_after_operation(db, jti: str, user_id: str):
    revoke_audience_token(
        db=db,
        jti=jti,
        expires_at=datetime.utcnow(),
        user_id=user_id,
        reason="operation_completed",
    )
```

---

## Frontend Integration

### React Hook for Audience Tokens

```typescript
// hooks/useAudienceToken.ts
import { useState } from 'react';
import { requestAudienceToken } from '@/lib/audienceAuth';

export function useAudienceToken() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const requestToken = async (audience: string, ttl: number = 120) => {
    setLoading(true);
    setError(null);
    try {
      const response = await requestAudienceToken(audience, ttl);
      setToken(response.token);
      return response.token;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return { token, loading, error, requestToken };
}
```

### Usage in Components

```typescript
// components/JobAbortButton.tsx
import { useAudienceToken } from '@/hooks/useAudienceToken';
import { api } from '@/lib/api';

export function JobAbortButton({ jobId }: { jobId: string }) {
  const { requestToken, loading } = useAudienceToken();

  const handleAbort = async () => {
    try {
      // Request audience token
      const token = await requestToken('jobs.abort', 120);

      // Use token for operation
      await api.post(
        `/jobs/${jobId}/abort`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      alert('Job aborted successfully');
    } catch (err) {
      alert(`Failed to abort job: ${err.message}`);
    }
  };

  return (
    <button onClick={handleAbort} disabled={loading}>
      {loading ? 'Aborting...' : 'Abort Job'}
    </button>
  );
}
```

---

## Security Considerations

### Best Practices

1. **Store Tokens in Memory Only**
   - ❌ Don't store in localStorage (XSS risk)
   - ❌ Don't store in cookies (CSRF risk for audience tokens)
   - ✅ Store in component state or memory

2. **Use Shortest Necessary TTL**
   ```python
   # Good: 2 minutes for quick operation
   create_audience_token(user_id, "jobs.abort", ttl_seconds=120)

   # Bad: 10 minutes for operation that takes 30 seconds
   create_audience_token(user_id, "jobs.abort", ttl_seconds=600)
   ```

3. **Verify Token Ownership**
   ```python
   # Always verify audience token belongs to authenticated user
   if audience_token.sub != str(current_user.id):
       raise HTTPException(403, "Token mismatch")
   ```

4. **Log All Operations**
   ```python
   logger.info(
       f"Sensitive operation: user={current_user.id}, "
       f"audience={audience_token.aud}, jti={audience_token.jti}"
   )
   ```

5. **Revoke After Use (Optional)**
   ```python
   # For maximum security, revoke immediately after operation
   revoke_audience_token(db, jti, expires_at, user_id, "completed")
   ```

### Attack Scenarios and Mitigations

| Attack | Mitigation |
|--------|------------|
| **Token theft** | Short TTL (2 min), blacklist on compromise |
| **Replay attack** | JTI tracking, single-use enforcement (if implemented) |
| **Privilege escalation** | Audience validation, role checking |
| **Clock manipulation** | Clock skew tolerance (30s), future-date rejection |
| **Token reuse** | Blacklist after use, expiration enforcement |

### Role-Based Audience Restrictions (TODO)

```python
# Future enhancement: Restrict audiences by role
ROLE_AUDIENCE_MAP = {
    "admin": ["*"],  # All audiences
    "coordinator": ["schedule.generate", "swap.execute"],
    "faculty": ["swap.execute"],
    "resident": [],  # No elevated permissions
}

def validate_user_can_request_audience(user: User, audience: str):
    allowed = ROLE_AUDIENCE_MAP.get(user.role, [])
    if "*" not in allowed and audience not in allowed:
        raise HTTPException(403, f"Role {user.role} cannot request {audience}")
```

---

## Testing

### Unit Tests

```python
# tests/test_audience_auth.py
import pytest
from app.core.audience_auth import create_audience_token, verify_audience_token

def test_create_and_verify_token(db):
    """Test token creation and verification."""
    user_id = "test-user-123"
    audience = "jobs.abort"

    # Create token
    response = create_audience_token(user_id, audience, ttl_seconds=120)

    # Verify token
    payload = verify_audience_token(response.token, audience, db)
    assert payload.sub == user_id
    assert payload.aud == audience

def test_wrong_audience_fails(db):
    """Test token fails for wrong audience."""
    user_id = "test-user-123"

    # Create token for jobs.abort
    response = create_audience_token(user_id, "jobs.abort", ttl_seconds=120)

    # Try to use for schedule.generate
    with pytest.raises(HTTPException) as exc:
        verify_audience_token(response.token, "schedule.generate", db)

    assert exc.value.status_code == 403
```

### Integration Tests

```python
# tests/integration/test_audience_endpoints.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_abort_job_workflow(client: AsyncClient, auth_headers):
    """Test complete abort job workflow with audience token."""

    # Step 1: Request audience token
    response = await client.post(
        "/api/audience-tokens/tokens",
        json={"audience": "jobs.abort", "ttl_seconds": 120},
        headers=auth_headers,
    )
    assert response.status_code == 200
    token = response.json()["token"]

    # Step 2: Use token to abort job
    response = await client.post(
        "/api/jobs/job-123/abort",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    # Step 3: Verify token cannot be reused after revocation
    # (if single-use enforcement is implemented)
```

### Load Tests

```bash
# k6 load test for audience token endpoint
k6 run - <<EOF
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  vus: 10,
  duration: '30s',
};

export default function () {
  const payload = JSON.stringify({
    audience: 'jobs.abort',
    ttl_seconds: 120,
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer <access-token>',
    },
  };

  const res = http.post(
    'http://localhost:8000/api/audience-tokens/tokens',
    payload,
    params
  );

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has token': (r) => JSON.parse(r.body).token !== undefined,
  });
}
EOF
```

---

## Troubleshooting

### Common Issues

#### 1. "Token has expired"

**Cause**: Token TTL elapsed before use

**Solution**:
- Use shorter operation execution time
- Request token immediately before operation
- Increase TTL if legitimate (max 600s)

```python
# Before: Request token, then wait 5 minutes
token = create_audience_token(user_id, "jobs.abort", 120)
time.sleep(300)  # ❌ Token expired
abort_job(token)

# After: Request token immediately before use
token = create_audience_token(user_id, "jobs.abort", 120)
abort_job(token)  # ✅ Token still valid
```

#### 2. "Token not valid for this operation"

**Cause**: Audience mismatch between token and endpoint

**Solution**: Ensure audience in request matches endpoint requirement

```python
# Wrong: Request jobs.abort token for schedule.generate endpoint
token = create_audience_token(user_id, "jobs.abort")
generate_schedule(token)  # ❌ Audience mismatch

# Right: Match audience to operation
token = create_audience_token(user_id, "schedule.generate")
generate_schedule(token)  # ✅ Correct audience
```

#### 3. "Token has been revoked"

**Cause**: Token is in blacklist

**Solution**:
- Request new token
- Check if token was revoked prematurely
- Verify blacklist cleanup job is running

#### 4. "Invalid token timestamp"

**Cause**: Future-dated token (clock skew or attack)

**Solution**:
- Verify server clocks are synchronized (NTP)
- Check for timezone issues (all times should be UTC)
- Investigate potential security incident

#### 5. "Authorization header required"

**Cause**: Missing or malformed Authorization header

**Solution**:
```javascript
// Wrong
fetch('/api/jobs/123/abort', {
  headers: { 'Token': token }  // ❌ Wrong header name
})

// Right
fetch('/api/jobs/123/abort', {
  headers: { 'Authorization': `Bearer ${token}` }  // ✅ Correct format
})
```

### Debugging

Enable debug logging:

```python
# backend/app/core/config.py
LOG_LEVEL="DEBUG"

# View detailed token validation logs
docker-compose logs -f backend | grep "audience"
```

Check token contents:

```python
from jose import jwt
from app.core.config import get_settings

settings = get_settings()
payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
print(payload)
# {
#   'sub': 'user-id',
#   'aud': 'jobs.abort',
#   'exp': 1735489800,
#   'iat': 1735489680,
#   'jti': '...',
#   'type': 'audience'
# }
```

Verify blacklist status:

```python
from app.models.token_blacklist import TokenBlacklist

is_blacklisted = TokenBlacklist.is_blacklisted(db, jti)
print(f"Token {jti} blacklisted: {is_blacklisted}")
```

---

## Monitoring and Observability

### Metrics to Track

```python
# Using observability metrics (if configured)
obs_metrics.record_token_issued("audience_jobs.abort")
obs_metrics.record_auth_failure("audience_mismatch")
obs_metrics.record_token_blacklisted("audience_completed")
```

### Dashboard Queries

**Prometheus**:
```promql
# Audience tokens issued per minute
rate(tokens_issued{type="audience_jobs.abort"}[1m])

# Authentication failures by reason
sum by (reason) (auth_failures{type=~"audience_.*"})

# Token blacklist operations
rate(tokens_blacklisted{reason=~"audience_.*"}[5m])
```

**Grafana Dashboard Panels**:
- Audience token creation rate (by audience)
- Token validation success/failure ratio
- Average token TTL
- Blacklisted tokens over time
- Top audiences by usage

---

## References

- [JWT Specification (RFC 7519)](https://datatracker.ietf.org/doc/html/rfc7519)
- [OAuth 2.0 Token Introspection (RFC 7662)](https://datatracker.ietf.org/doc/html/rfc7662)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)
- [Security Pattern Audit](../security/SECURITY_PATTERN_AUDIT.md)
- [AI Rules of Engagement](./AI_RULES_OF_ENGAGEMENT.md)

---

**Last Updated**: 2025-12-29
**Maintainer**: Development Team
**Review Cycle**: Quarterly
