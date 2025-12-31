# AUTH ROUTE TEST GAP ANALYSIS
## G2_RECON Intelligence Report
**Generated:** 2025-12-31
**Mission:** Map authentication route test coverage gaps

---

## EXECUTIVE SUMMARY

Authentication system has **3 route modules with 30 total endpoints**. Coverage analysis reveals:
- **16 endpoints with comprehensive integration tests** (53%)
- **14 endpoints with missing or partial integration tests** (47%)
- **Security-critical gaps identified** in audience token route management

---

## ROUTE INVENTORY & ENDPOINT MAPPING

### 1. AUTH ROUTES (`/api/auth`)
**File:** `backend/app/api/routes/auth.py`
**Endpoints:** 7

| Endpoint | HTTP Method | Security Level | Test Status | Notes |
|----------|------------|-----------------|-------------|-------|
| `/login` | POST | Critical | ✅ Tested | OAuth2 form-based (test_auth_routes.py: 15+ tests) |
| `/login/json` | POST | Critical | ✅ Tested | JSON alternative (test_auth_routes.py: 8+ tests) |
| `/logout` | POST | Critical | ✅ Tested | Token blacklisting (test_auth_routes.py: 8+ tests) |
| `/refresh` | POST | Critical | ✅ Tested | Token rotation security (test_auth_routes.py: 13+ tests) |
| `/me` | GET | High | ✅ Tested | Current user info (test_auth_routes.py: 8+ tests) |
| `/register` | POST | Critical | ✅ Tested | User creation (test_auth_routes.py: 12+ tests) |
| `/users` | GET | High | ✅ Tested | List users admin-only (test_auth_routes.py: 7+ tests) |

**Coverage:** 100% (7/7 endpoints)

---

### 2. SESSION ROUTES (`/api/sessions`)
**File:** `backend/app/api/routes/sessions.py`
**Endpoints:** 11

| Endpoint | HTTP Method | Security Level | Test Status | Notes |
|----------|------------|-----------------|-------------|-------|
| `/me` | GET | High | ⚠️ Partial | Mock-based tests only (test_sessions.py: basic auth test) |
| `/me/current` | GET | High | ⚠️ Partial | Mocked SessionState (test_sessions.py: 2 tests) |
| `/me/refresh` | POST | High | ⚠️ Partial | Mocked manager (test_sessions.py: 3 tests) |
| `/me/{session_id}` | DELETE | High | ⚠️ Partial | Ownership validation tested (test_sessions.py: 3 tests) |
| `/me/other` | DELETE | High | ⚠️ Partial | Logout others tested (test_sessions.py: 1 test) |
| `/me/all` | DELETE | High | ⚠️ Partial | Logout all tested (test_sessions.py: 1 test) |
| `/stats` | GET | Admin | ⚠️ Partial | Admin-only, mocked (test_sessions.py: incomplete) |
| `/user/{user_id}` | GET | Admin | ❌ Missing | **NO INTEGRATION TESTS** |
| `/user/{user_id}/force-logout` | DELETE | Admin | ⚠️ Partial | Basic auth test only (test_sessions.py: 1 test) |
| `/session/{session_id}` | DELETE | Admin | ⚠️ Partial | Basic auth test only (test_sessions.py: 1 test) |
| `/cleanup` | POST | Admin | ⚠️ Partial | No real session cleanup tested |

**Coverage:** ~45% (5/11 endpoints fully tested with real logic)

**Critical Gap:** Session manager is mocked throughout - tests don't verify actual session persistence, expiration, or concurrent session handling.

---

### 3. SSO ROUTES (`/api/sso`)
**File:** `backend/app/api/routes/sso.py`
**Endpoints:** 8

| Endpoint | HTTP Method | Security Level | Test Status | Notes |
|----------|------------|-----------------|-------------|-------|
| `/saml/metadata` | GET | Public | ✅ Tested | Config validation (test_sso.py: 1 test) |
| `/saml/login` | GET | Public | ❌ Missing | **NO INTEGRATION TESTS** |
| `/saml/acs` | POST | Critical | ❌ Missing | **NO INTEGRATION TESTS** (assertion consumer service) |
| `/saml/logout` | GET | High | ❌ Missing | **NO INTEGRATION TESTS** |
| `/oauth2/login` | GET | Public | ❌ Missing | **NO INTEGRATION TESTS** |
| `/oauth2/callback` | GET | Critical | ❌ Missing | **NO INTEGRATION TESTS** (code exchange vulnerable point) |
| `/providers` | GET | Public | ✅ Tested | Config validation (test_sso.py: 2 tests) |
| `/status` | GET | Public | ✅ Tested | Config validation (test_sso.py: 1 test) |

**Coverage:** 38% (3/8 endpoints tested, config-focused only)

**Critical Gaps:**
- No SAML assertion parsing/validation tests
- No OAuth2 code exchange tests
- No JIT user provisioning integration tests
- No open redirect vulnerability tests

---

### 4. AUDIENCE TOKEN ROUTES (`/api/audience-tokens`)
**File:** `backend/app/api/routes/audience_tokens.py`
**Endpoints:** 4

| Endpoint | HTTP Method | Security Level | Test Status | Notes |
|----------|------------|-----------------|-------------|-------|
| `/audiences` | GET | High | ❌ Missing | **NO ROUTE TESTS** (only core tests in test_audience_auth.py) |
| `/tokens` | POST | Critical | ❌ Missing | **NO ROUTE TESTS** (role-based permission check untested) |
| `/tokens/revoke` | POST | Critical | ❌ Missing | **NO ROUTE TESTS** (token ownership verification untested) |
| `/example/abort-job/{job_id}` | POST | Admin | ❌ Missing | **NO TESTS** (example endpoint, needs real endpoint) |

**Coverage:** 0% route integration tests

**Test Note:** `test_audience_auth.py` contains 70+ unit tests for core functions (`create_audience_token`, `verify_audience_token`, etc.) but **zero integration tests** for the HTTP API endpoints themselves.

**Critical Gaps:**
- RBAC enforcement not tested (can user with role X request audience Y?)
- Token ownership verification untested
- Concurrent token request handling not tested
- TTL boundary conditions (30-600s) at HTTP layer not tested

---

## SECURITY-PRIORITIZED TEST GAP RANKING

### TIER 1: CRITICAL SECURITY GAPS (Exploit-Ready Vulnerabilities)

| Gap | Risk | Impact | Priority |
|-----|------|--------|----------|
| **SSO SAML/OAuth2 callback validation** | JIT provisioning, privilege escalation | User creation bypass, unauthorized role assignment | **P0-CRITICAL** |
| **Audience token RBAC enforcement** | Privilege escalation | Resident could request coordinator tokens | **P0-CRITICAL** |
| **Session concurrent control** | Race conditions | Multiple simultaneous sessions not validated | **P0-CRITICAL** |
| **Open redirect in SSO** | Phishing | After auth, redirect to attacker site | **P0-CRITICAL** |

### TIER 2: HIGH PRIORITY GAPS (Missing Validation)

| Gap | Risk | Impact | Priority |
|-----|------|--------|----------|
| **Token ownership verification** | Authorization bypass | User revokes other users' tokens | **P1-HIGH** |
| **Session admin operations** | Missing coverage | Admin force-logout untested | **P1-HIGH** |
| **SAML signature validation** | XML signature bypass | Forged SAML assertions accepted | **P1-HIGH** |
| **OAuth2 state/PKCE validation** | CSRF/authorization code interception | Token exchange hijacked | **P1-HIGH** |

### TIER 3: MEDIUM PRIORITY GAPS (Incomplete Testing)

| Gap | Risk | Impact | Priority |
|-----|------|--------|----------|
| **Session persistence** | Logic errors | Sessions not properly stored/retrieved | **P2-MEDIUM** |
| **TTL boundary conditions** | Off-by-one errors | Token expiration at 29s or 601s accepted | **P2-MEDIUM** |
| **Error message leakage** | Information disclosure | User enumeration via detailed error messages | **P2-MEDIUM** |

---

## TEST FILE INVENTORY

| Test File | Location | Endpoints Covered | Test Count | Status |
|-----------|----------|------------------|------------|--------|
| `test_auth_routes.py` | `backend/tests/` | `/api/auth/*` | 60+ | ✅ Comprehensive |
| `test_auth_workflow.py` | `backend/tests/integration/api/` | Auth flow scenarios | ~10 | ✅ Good |
| `test_sso.py` | `backend/tests/` | SSO config/providers | 18 | ⚠️ Config-only |
| `test_sessions.py` | `backend/tests/routes/` | Session routes | 20 | ⚠️ Mocked |
| `test_audience_auth.py` | `backend/tests/` | Audience token core | 70+ | ✅ Core logic only |
| `test_oauth2_pkce.py` | `backend/tests/` | PKCE flow | ~5 | ⚠️ Incomplete |
| `test_rbac_authorization.py` | `backend/tests/auth/` | RBAC logic | ~15 | ⚠️ Unit tests only |

**Total Tests:** ~200
**Gap:** Route-level integration tests missing for 18 endpoints

---

## MISSING INTEGRATION TEST TEMPLATES

### SSO ROUTES - MISSING (8 endpoints)

```python
# backend/tests/routes/test_sso_routes.py (NEW FILE)
# Needed tests:

class TestSAMLLogin:
    def test_saml_login_redirect_to_idp()
    def test_saml_acs_valid_assertion()
    def test_saml_acs_invalid_signature()
    def test_saml_acs_expired_assertion()
    def test_saml_acs_missing_required_attributes()
    def test_saml_acs_auto_provision_enabled()
    def test_saml_acs_auto_provision_disabled()
    def test_saml_acs_open_redirect_blocked()
    def test_saml_logout_initiation()

class TestOAuth2Flow:
    def test_oauth2_login_pkce_flow()
    def test_oauth2_callback_code_exchange()
    def test_oauth2_callback_state_mismatch()
    def test_oauth2_callback_invalid_code()
    def test_oauth2_id_token_validation()
    def test_oauth2_userinfo_endpoint()
    def test_oauth2_open_redirect_blocked()
    def test_oauth2_jit_provisioning()
```

### SESSION ROUTES - INCOMPLETE (6 endpoints need real tests)

```python
# backend/tests/routes/test_sessions.py (ENHANCE EXISTING)
# Convert mocks to real AsyncSessionManager tests:

class TestSessionRoutes:
    def test_get_my_sessions_real_sessions()
    def test_get_user_sessions_admin_real()
    def test_force_logout_user_admin_real()
    def test_revoke_session_admin_real()
    def test_cleanup_expired_sessions_real()
    def test_concurrent_session_limits()
    def test_session_expiration_cleanup()
```

### AUDIENCE TOKEN ROUTES - MISSING (4 endpoints)

```python
# backend/tests/routes/test_audience_tokens.py (NEW FILE)
# Needed tests:

class TestAudienceTokenRoutes:
    def test_list_audiences_authenticated()
    def test_list_audiences_unauthenticated()

    def test_request_audience_token_admin_success()
    def test_request_audience_token_coordinator_success()
    def test_request_audience_token_resident_forbidden()
    def test_request_audience_token_rbac_enforcement()
    def test_request_audience_token_ttl_validation()

    def test_revoke_own_token()
    def test_revoke_other_token_forbidden()
    def test_revoke_admin_override()
    def test_revoke_nonexistent_token()
    def test_revoke_already_revoked()
```

---

## ENDPOINTS BY CRITICALITY

### CRITICAL (Security-sensitive, high attack surface)

**Requires 100% integration test coverage:**

1. **`POST /api/auth/login`** - Credential validation, rate limiting
2. **`POST /api/auth/refresh`** - Token rotation, rotation timing attacks
3. **`POST /api/auth/logout`** - Token blacklist verification
4. **`POST /api/audience-tokens/tokens`** - RBAC privilege escalation
5. **`POST /api/audience-tokens/tokens/revoke`** - Ownership verification
6. **`POST /api/sso/saml/acs`** - Assertion validation, JIT provisioning
7. **`GET /api/sso/oauth2/callback`** - Code exchange, state/PKCE validation

### HIGH (Authorization/admin operations)

**Requires integration tests:**

1. **`GET /api/sessions/user/{user_id}`** - Admin viewing user sessions
2. **`DELETE /api/sessions/user/{user_id}/force-logout`** - Admin forced logout
3. **`DELETE /api/sessions/session/{session_id}`** - Admin session revocation
4. **`POST /api/sessions/cleanup`** - Admin maintenance

### MEDIUM (User-facing, less risky)

**Partial coverage acceptable, but recommend:**

1. **`GET /api/sessions/me`** - Current user sessions (use real manager)
2. **`GET /api/auth/me`** - Current user info (covered)
3. **`POST /api/auth/register`** - User creation (covered)

---

## TESTING BLOCKERS & DEPENDENCIES

| Blocker | Status | Impact |
|---------|--------|--------|
| SessionManager async mock (needs real integration) | Blocking | Can't test session persistence |
| SAML/OAuth2 IdP mock not realistic | Blocking | SAML assertion parsing untested |
| Open redirect allowlist not tested | Blocking | OWASP A01 vulnerability |
| RBAC permission matrix not validated at HTTP layer | Blocking | Privilege escalation untested |
| Concurrent request handling | Blocking | Race conditions untested |

---

## RECOMMENDED TEST EXECUTION PLAN

### Phase 1: CRITICAL (Week 1)
- [ ] SSO SAML/OAuth2 callback validation (P0)
- [ ] Audience token RBAC enforcement (P0)
- [ ] Open redirect vulnerability tests (P0)
- **Estimated:** 25-30 new tests

### Phase 2: HIGH (Week 2)
- [ ] Session admin operations (P1)
- [ ] Token ownership verification (P1)
- [ ] Real SessionManager integration (P1)
- **Estimated:** 20-25 new tests

### Phase 3: MEDIUM (Week 3)
- [ ] TTL boundary conditions (P2)
- [ ] Error message leakage audit (P2)
- [ ] Concurrent session scenarios (P2)
- **Estimated:** 15-20 new tests

---

## COMPLIANCE IMPLICATIONS

| Standard | Gap | Severity |
|----------|-----|----------|
| **OWASP Top 10** | A01 (Broken Access Control) - No RBAC HTTP tests | Critical |
| **OWASP Top 10** | A05 (Broken Access Control) - Open redirect untested | Critical |
| **OWASP Top 10** | A07 (Identification/Auth) - SSO flows untested | High |
| **HIPAA** | Audit trail (no test for session forced logout logging) | Medium |
| **ACGME** | User access control verification | High |

---

## FILES REQUIRING UPDATES

### New Test Files
- `backend/tests/routes/test_sso_routes.py` (70+ tests)
- `backend/tests/routes/test_audience_tokens.py` (25+ tests)

### Files Requiring Enhancement
- `backend/tests/routes/test_sessions.py` (Replace mocks with real manager: 15-20 tests)
- `backend/tests/test_audience_auth.py` (Add route-level tests alongside unit tests)

### Files to Review/Audit
- `backend/app/api/routes/sso.py` (Open redirect validation)
- `backend/app/api/routes/audience_tokens.py` (RBAC enforcement)
- `backend/app/api/routes/sessions.py` (Admin operation logging)

---

## SUMMARY TABLE

| Route Module | Total Endpoints | Tested | Gaps | Coverage % | Priority |
|--------------|-----------------|--------|------|------------|----------|
| Auth (`/api/auth`) | 7 | 7 | 0 | 100% | ✅ Complete |
| Sessions (`/api/sessions`) | 11 | 5 | 6 | 45% | 🔴 P1-HIGH |
| SSO (`/api/sso`) | 8 | 3 | 5 | 38% | 🔴 P0-CRITICAL |
| Audience Tokens (`/api/audience-tokens`) | 4 | 0 | 4 | 0% | 🔴 P0-CRITICAL |
| **TOTAL** | **30** | **15** | **15** | **50%** | **P0+P1** |

---

## INTELLIGENCE ASSESSMENT

**Reconnaissance Status:** COMPLETE ✅

**Threat Level:** 🔴 **CRITICAL**
- 14/30 endpoints lack security-critical integration tests
- SSO and Audience Token routes entirely untested at HTTP layer
- RBAC enforcement not validated in production-like scenario
- Open redirect vulnerability not tested

**Recommendation:** Prioritize P0 gaps immediately before production deployment.

---

*Report compiled by G2_RECON*
*Mission Status: COMPLETE*
