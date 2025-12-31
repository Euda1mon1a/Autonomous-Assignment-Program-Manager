# Backend Authentication & Authorization - Quick Reference

**Deliverable:** `backend-auth-patterns.md` (1,186 lines)

## Document Structure

### Part 1: Authentication Flow (Endpoints & Tokens)
- High-level authentication flow diagram
- 5 main endpoints: login, login/json, logout, refresh, me
- Token structure and lifecycle
- Rate limiting and account lockout mechanics

### Part 2: Token Architecture
- JWT payload structure (access vs refresh tokens)
- Token verification logic with security rules
- Token blacklisting system (Redis-backed)
- Security implications of token theft

### Part 3: Rate Limiting & Account Lockout
- IP-based sliding window rate limiter (Redis)
- Per-username account lockout with exponential backoff
- Trusted proxy support to prevent bypass
- Configuration options and tuning

### Part 4: Role-Based Access Control (RBAC)
- 8 user roles with hierarchical structure
- User model with permission properties
- Access Control Matrix: 20 resources × 11 actions
- Role hierarchy inheritance
- Context-aware permissions (own resource checks)

### Part 5: Security Implementation Details
- Password hashing (bcrypt) and validation rules
- JWT configuration and secret key validation
- httpOnly cookie security
- Error handling to prevent information leakage
- Permission audit logging system

### Part 6-10: Integration, Testing, Configuration

## Key Findings

### Strengths
1. **JWT + Blacklist hybrid** - Stateless JWT with stateful logout
2. **Token rotation** - Old refresh tokens immediately blacklisted
3. **Dual authentication** - IP-based rate limiting + username lockout
4. **Comprehensive matrix** - 20 resources × 8 roles × context-aware
5. **httpOnly cookies** - XSS-resistant token storage
6. **Audit trails** - All permission checks logged
7. **Graceful degradation** - Works if Redis unavailable

### Security Checklist (All Implemented)
- ✅ Password hashing (bcrypt)
- ✅ Rate limiting (IP-based)
- ✅ Account lockout (exponential backoff)
- ✅ XSS protection (httpOnly)
- ✅ CSRF protection (SameSite)
- ✅ Token blacklisting (Redis)
- ✅ Audit logging (all checks)
- ✅ Generic error messages (no info leakage)
- ✅ Role-based access control (hierarchical)
- ✅ Context-aware permissions (ownership)

## Critical Security Rules

1. **Refresh tokens CANNOT be used as access tokens**
   - Access tokens have no `type` field
   - Refresh tokens have `type="refresh"`
   - verify_token() explicitly rejects refresh tokens

2. **Access tokens in httpOnly cookies only**
   - Prevents XSS attacks
   - Refresh tokens in response body only (client controls storage)

3. **Token rotation blacklists immediately**
   - When REFRESH_TOKEN_ROTATE=true
   - Old token blacklisted before new one issued
   - Prevents token theft window exploitation

4. **Two-layer rate limiting**
   - IP-based: Sliding window via Redis
   - Username-based: Exponential backoff after 5 failures
   - Prevents distributed attacks + credential enumeration

## File Locations (Explored)

### Core Auth Files
- `backend/app/core/security.py` - Token operations, password hashing, user extraction
- `backend/app/api/routes/auth.py` - Login, logout, refresh endpoints
- `backend/app/controllers/auth_controller.py` - Request validation, lockout tracking
- `backend/app/services/auth_service.py` - Authentication business logic
- `backend/app/models/user.py` - User model with permission properties
- `backend/app/models/token_blacklist.py` - Logout token storage

### RBAC & Authorization
- `backend/app/auth/access_matrix.py` - Complete RBAC matrix system (934 lines)
- `backend/app/api/dependencies/role_filter.py` - Dependency injection helpers

### Rate Limiting & Security
- `backend/app/core/rate_limit.py` - Rate limiter + account lockout (546 lines)
- `backend/app/schemas/auth.py` - Request/response schemas with validation

### Testing
- `backend/tests/test_auth_routes.py`
- `backend/tests/test_access_matrix.py`
- `backend/tests/auth/test_rbac_authorization.py`
- `backend/tests/integration/api/test_auth_workflow.py`

## RBAC Matrix Summary

| Role | Permissions | Common Use Case |
|------|-------------|-----------------|
| **ADMIN** | All CRUD on all resources | System administrator |
| **COORDINATOR** | Schedule management, user oversight | Scheduling manager |
| **FACULTY** | View schedules, manage own swaps/absence | Attending physician |
| **CLINICAL_STAFF** | Read-only access to schedules/roster | Nursing staff |
| **RN/LPN/MSA** | Same as CLINICAL_STAFF | Specific clinical roles |
| **RESIDENT** | View own schedule, create swaps | Resident physician |

## Configuration Reference

```bash
SECRET_KEY=<32+ chars random>           # REQUIRED
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
REFRESH_TOKEN_ROTATE=true
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_ATTEMPTS=5
REDIS_URL=redis://localhost:6379/0
```

## Recommendations

**Priority 1 - Security:**
1. Add MFA (TOTP) for admin operations
2. Document refresh token secure storage patterns
3. Add session management (list/revoke active sessions)

**Priority 2 - Operations:**
1. Permission matrix visualization UI
2. Audit log export (CSV/JSON)
3. Failed login attempt dashboard

**Priority 3 - Advanced:**
1. API keys for service accounts
2. IP whitelisting per user
3. Risk-based adaptive authentication

---

**Generated:** 2025-12-30
**Operation:** SEARCH_PARTY G2_RECON (Authentication & Authorization Patterns)
