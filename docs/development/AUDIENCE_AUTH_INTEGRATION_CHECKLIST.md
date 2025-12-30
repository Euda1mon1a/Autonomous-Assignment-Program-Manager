# Audience-Scoped JWT Authentication - Integration Checklist

> **Status**: Ready for integration
> **Created**: 2025-12-29
> **Files Created**: 5 new files

---

## Files Created

### 1. Core Authentication Module
**File**: `/backend/app/core/audience_auth.py`

**Contains**:
- `create_audience_token()` - Generate audience-scoped tokens
- `verify_audience_token()` - Validate tokens with comprehensive checks
- `require_audience()` - FastAPI dependency for endpoint protection
- `get_audience_token()` - Manual token extraction for non-dependency use
- `revoke_audience_token()` - Blacklist tokens
- `AudienceTokenPayload` - Pydantic model for token data
- `VALID_AUDIENCES` - Registry of all available audiences

**Features**:
✅ Clock skew tolerance (30 seconds)
✅ Future-date rejection
✅ Blacklist integration
✅ Observability metrics integration
✅ Comprehensive logging
✅ TTL enforcement (30-600 seconds)

### 2. Pydantic Schemas
**File**: `/backend/app/schemas/audience_token.py`

**Contains**:
- `AudienceTokenRequest` - Request body for token creation
- `AudienceTokenResponse` - Response format
- `AudienceListResponse` - Available audiences listing
- `RevokeTokenRequest` - Token revocation request
- `RevokeTokenResponse` - Revocation response

### 3. API Routes
**File**: `/backend/app/api/routes/audience_tokens.py`

**Endpoints**:
- `GET /api/audience-tokens/audiences` - List available audiences
- `POST /api/audience-tokens/tokens` - Request audience token
- `POST /api/audience-tokens/revoke` - Revoke token
- `POST /api/audience-tokens/example/abort-job/{job_id}` - Example usage

### 4. Comprehensive Tests
**File**: `/backend/tests/test_audience_auth.py`

**Test Coverage**:
- ✅ Token creation and validation
- ✅ Audience validation
- ✅ Expiration handling
- ✅ Blacklist integration
- ✅ Clock skew tolerance
- ✅ Future-date rejection
- ✅ Wrong audience detection
- ✅ Token revocation
- ✅ FastAPI dependency usage
- ✅ Integration scenarios

**Run Tests**:
```bash
cd backend
pytest tests/test_audience_auth.py -v
```

### 5. Usage Documentation
**File**: `/docs/development/AUDIENCE_AUTH_USAGE.md`

**Contents**:
- Architecture overview
- Quick start guide
- API reference
- Backend integration examples
- Frontend integration examples
- Security best practices
- Troubleshooting guide
- Monitoring setup

---

## Integration Steps

### Step 1: Register API Routes

**File**: `backend/app/main.py`

```python
from app.api.routes import audience_tokens

# Add to route registration
app.include_router(
    audience_tokens.router,
    prefix="/api/audience-tokens",
    tags=["audience-tokens"],
)
```

### Step 2: Update Existing Endpoints

**Example**: Protect job abort endpoint

**File**: `backend/app/api/routes/jobs.py`

```python
from app.core.audience_auth import require_audience, AudienceTokenPayload

@router.post("/{job_id}/abort")
async def abort_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    audience_token: AudienceTokenPayload = Depends(require_audience("jobs.abort")),
):
    # Verify token belongs to user
    if audience_token.sub != str(current_user.id):
        raise HTTPException(403, "Token mismatch")

    # Execute operation
    await jobs_service.abort(job_id)
    return {"success": True}
```

### Step 3: Add New Audiences (If Needed)

**File**: `backend/app/core/audience_auth.py`

```python
VALID_AUDIENCES = {
    # Existing audiences...
    "your.new.operation": "Description of operation",
}
```

### Step 4: Database Migration (If Needed)

The implementation uses the existing `token_blacklist` table. No migration needed.

**Verify table exists**:
```sql
\dt token_blacklist
```

If missing, run migrations:
```bash
cd backend
alembic upgrade head
```

### Step 5: Frontend Integration

**Create API client**:

```typescript
// frontend/lib/audienceAuth.ts
export async function requestAudienceToken(
  audience: string,
  ttl_seconds: number = 120
) {
  const response = await api.post('/audience-tokens/tokens', {
    audience,
    ttl_seconds,
  });
  return response.data;
}

export async function performProtectedOperation(
  audience: string,
  operationFn: (token: string) => Promise<any>
) {
  const { token } = await requestAudienceToken(audience);
  return await operationFn(token);
}
```

**Usage in components**:

```typescript
import { performProtectedOperation } from '@/lib/audienceAuth';

async function handleAbortJob(jobId: string) {
  await performProtectedOperation('jobs.abort', async (token) => {
    return api.post(`/jobs/${jobId}/abort`, {}, {
      headers: { Authorization: `Bearer ${token}` }
    });
  });
}
```

### Step 6: Update API Documentation

**File**: `docs/api/README.md`

Add section:
```markdown
## Audience-Scoped Authentication

For elevated operations, use audience-scoped tokens. See:
- [Usage Guide](../development/AUDIENCE_AUTH_USAGE.md)
- [Integration Checklist](../development/AUDIENCE_AUTH_INTEGRATION_CHECKLIST.md)
```

---

## Testing Checklist

- [ ] Unit tests pass: `pytest tests/test_audience_auth.py`
- [ ] Integration tests pass: `pytest tests/integration/`
- [ ] Manual testing:
  - [ ] Request audience token via API
  - [ ] Use token for protected operation
  - [ ] Verify token expiration
  - [ ] Verify wrong audience rejection
  - [ ] Verify token revocation
- [ ] Load testing (optional): `k6 run load-tests/audience-tokens.js`

---

## Security Review Checklist

- [ ] Tokens are short-lived (max 10 minutes)
- [ ] All operations logged with user_id and jti
- [ ] Blacklist integration working
- [ ] Clock skew tolerance tested
- [ ] Future-date rejection working
- [ ] Audience validation enforced
- [ ] Token ownership verified in endpoints
- [ ] No sensitive data in error messages
- [ ] HTTPS enforced in production
- [ ] Rate limiting configured for token endpoint

---

## Deployment Checklist

### Development
- [ ] Update `.env` with `LOG_LEVEL=DEBUG` for testing
- [ ] Restart backend: `docker-compose restart backend`
- [ ] Verify endpoint: `curl http://localhost:8000/api/audience-tokens/audiences`

### Staging
- [ ] Run full test suite
- [ ] Monitor logs for errors
- [ ] Test with real user accounts
- [ ] Verify observability metrics
- [ ] Load test token endpoint

### Production
- [ ] Review security configuration
- [ ] Set `LOG_LEVEL=INFO` or `WARNING`
- [ ] Configure rate limiting
- [ ] Set up alerts for:
  - High token validation failure rate
  - Unusual audience requests
  - Blacklist growth rate
- [ ] Update runbook with new endpoints

---

## Monitoring Setup

### Prometheus Metrics

The implementation automatically records metrics via `app.core.observability`:

```python
obs_metrics.record_token_issued("audience_jobs.abort")
obs_metrics.record_auth_failure("audience_mismatch")
obs_metrics.record_token_blacklisted("audience_completed")
```

### Grafana Dashboard

Create panels for:
- Audience token creation rate (by audience)
- Token validation success/failure ratio
- Blacklist operations per minute
- Average token TTL
- Top users by token requests

**Query Examples**:
```promql
# Tokens issued per minute
rate(tokens_issued{type=~"audience_.*"}[1m])

# Validation failures
sum by (reason) (auth_failures{type=~"audience_.*"})
```

### Logging

All operations logged with structured data:

```python
logger.info(
    f"Audience token created: user_id={user_id}, audience={audience}, "
    f"jti={jti}, ttl={ttl_seconds}s"
)
```

Search logs:
```bash
# View all audience token operations
docker-compose logs backend | grep "Audience token"

# View validation failures
docker-compose logs backend | grep "audience_mismatch"
```

---

## Rollback Plan

If issues arise, rollback is straightforward:

### Step 1: Remove Route Registration
```python
# backend/app/main.py
# Comment out:
# app.include_router(audience_tokens.router, ...)
```

### Step 2: Restart Services
```bash
docker-compose restart backend
```

### Step 3: Revert Frontend Changes
```bash
git checkout main -- frontend/lib/audienceAuth.ts
git checkout main -- frontend/components/JobAbortButton.tsx
```

**Note**: Database tables are not affected (uses existing `token_blacklist`).

---

## Next Steps

### Immediate (Required for MVP)
1. [ ] Register routes in `main.py`
2. [ ] Protect at least one endpoint (e.g., job abort)
3. [ ] Test token flow end-to-end
4. [ ] Deploy to development environment

### Short-term (1-2 weeks)
1. [ ] Implement role-based audience restrictions
2. [ ] Add frontend UI for token management
3. [ ] Set up monitoring dashboards
4. [ ] Write operational runbook

### Long-term (Future Enhancements)
1. [ ] Single-use token enforcement
2. [ ] Token usage analytics
3. [ ] Automated token rotation
4. [ ] Multi-factor authentication for sensitive audiences
5. [ ] Token delegation (allow AI agents to create tokens)

---

## Support and Questions

- **Documentation**: `/docs/development/AUDIENCE_AUTH_USAGE.md`
- **Code Reference**: `/backend/app/core/audience_auth.py`
- **Tests**: `/backend/tests/test_audience_auth.py`
- **Security Review**: `/docs/security/SECURITY_PATTERN_AUDIT.md`

---

**Status**: ✅ Ready for integration
**Last Updated**: 2025-12-29
**Reviewed By**: AI Development Team
