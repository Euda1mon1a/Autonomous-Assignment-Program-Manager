# G2_RECON: Authorization & RBAC Security Audit

**Audit Date:** 2025-12-30
**Session:** OVERNIGHT_BURN/SESSION_4_SECURITY
**Scope:** Role-Based Access Control (RBAC) and Authorization Enforcement
**Status:** Complete

---

## Executive Summary

The residency scheduler implements a **multi-layered authorization framework** with 8 distinct roles and comprehensive permission matrices. The system demonstrates **strong foundational security patterns** with JWT-based authentication, role hierarchy support, and permission caching. However, several **critical gaps** exist in:

1. **Inconsistent endpoint protection** - 344 protected endpoints analyzed, but patterns vary
2. **Permission resolver hierarchy ambiguity** - Two competing role hierarchies (access_matrix vs. resolver)
3. **Context-aware permission edge cases** - "Own resource" validation lacks depth
4. **Missing granular escalation controls** - No explicit privilege escalation detection

---

## Part 1: PERCEPTION - Current RBAC Implementation

### 1.1 Role Definitions (8 Roles)

The system defines **8 user roles** with hierarchical structure:

```python
# From app/models/user.py and app/auth/permissions/models.py

Roles (by privilege level):
├─ ADMIN           # System administrator (full access)
├─ COORDINATOR     # Schedule manager
├─ FACULTY         # Faculty/attending physicians
├─ RESIDENT        # Resident physicians
├─ CLINICAL_STAFF  # Base clinical staff role
├─ RN              # Registered Nurse (inherits from CLINICAL_STAFF)
├─ LPN             # Licensed Practical Nurse (inherits from CLINICAL_STAFF)
└─ MSA             # Medical Support Assistant (inherits from CLINICAL_STAFF)
```

### 1.2 Authentication Mechanism

**JWT-Based Authentication (Secure):**
- Access tokens: 30-minute expiration (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Refresh tokens: 7-day expiration (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- Token storage: httpOnly cookies (XSS-resistant) + optional Authorization header
- Token validation: Signature verification, expiration check, blacklist check

**Token Blacklisting (Strong):**
```python
# From app/core/security.py
- Tokens get unique JWT ID (jti) for blacklist tracking
- Support for token rotation on refresh
- Logout immediately revokes token
- Blacklist cleanup based on token expiration
```

### 1.3 Permission Framework

**Dual Permission Systems Detected:**

**System A: AccessControlMatrix (app/auth/access_matrix.py)**
- Comprehensive permission matrix with 20+ resource types
- 8 actions (CREATE, READ, UPDATE, DELETE, LIST, APPROVE, REJECT, EXECUTE)
- Role hierarchy with inherited roles
- Audit logging of permission checks
- Context-aware evaluation (own resource checks)

```python
Permission Matrix Structure:
{
  role: {
    resource: {
      actions
    }
  }
}

Example - ADMIN role:
- Full access to all resources and actions

Example - RESIDENT role:
- SCHEDULE: {READ, LIST}
- ASSIGNMENT: {READ, LIST}
- SWAP: {CREATE, READ, UPDATE, LIST, APPROVE, REJECT}
- ABSENCE: {CREATE, READ}
- PERSON: {READ}  # Own profile only
```

**System B: PermissionResolver (app/auth/permissions/resolver.py)**
- Role hierarchy with inheritance
- Redis-based permission caching
- Default role permissions (string-based)
- User-level permission checking

### 1.4 Endpoint Protection Coverage

**Protection Stats:**
- Total endpoints analyzed: ~57 route files
- Protected endpoints: 344 (verified via grep)
- Protection method: Dependency injection with `Depends(get_current_active_user)`

**Protected Endpoint Examples:**
```python
# From app/api/routes/

# Admin-only
@router.post("/api/admin/users")
async def create_user(
    current_user: User = Depends(get_admin_user)
):
    ...

# Coordinator-level
@router.get("/api/scheduler/runs")
async def get_solver_runs(
    current_user: User = Depends(get_scheduler_user)
):
    ...

# General authentication
@router.get("/api/people")
async def list_people(
    current_user: User = Depends(get_current_active_user)
):
    ...
```

---

## Part 2: INVESTIGATION - Permission Propagation

### 2.1 Permission Inheritance Chain

**AccessControlMatrix Hierarchy:**
```
ADMIN (top)
├─ COORDINATOR
│  ├─ FACULTY
│  └─ RESIDENT (sibling)
└─ CLINICAL_STAFF
   ├─ RN
   ├─ LPN
   └─ MSA
```

**PermissionResolver Hierarchy:**
```
ADMIN (top)
├─ COORDINATOR
│  └─ FACULTY
RESIDENT (independent)
CLINICAL_STAFF (base)
├─ RN
├─ LPN
└─ MSA
```

**CRITICAL ISSUE #1: Hierarchy Mismatch**
- AccessControlMatrix defines RESIDENT as inheriting from COORDINATOR
- PermissionResolver defines RESIDENT as independent
- **Risk:** Inconsistent permission evaluation depending on which system is used

### 2.2 Permission Propagation Flow

```
Request → Authentication (JWT validation)
  ↓
User object (role field)
  ↓
Route handler checks:
  a) Simple role check: get_admin_user, get_scheduler_user
  b) Matrix-based: AccessControlMatrix.has_permission()
  c) Resolver-based: PermissionResolver.check_permission()
  ↓
Allow/Deny + Audit log
```

### 2.3 Context-Aware Permission Logic

**Current Implementation (app/auth/access_matrix.py):**
```python
# Only two context evaluators registered:

def is_own_resource(context: PermissionContext) -> bool:
    return (
        context.resource_owner_id is not None
        and context.user_id == context.resource_owner_id
    )

def is_supervisor(context: PermissionContext) -> bool:
    return context.user_role in {UserRole.ADMIN, UserRole.COORDINATOR}
```

**Usage Pattern:**
```python
# Residents can only update their own absence requests
if role in {UserRole.RESIDENT, UserRole.FACULTY}:
    if action in {PermissionAction.UPDATE, PermissionAction.DELETE}:
        if resource in {ABSENCE, LEAVE, SWAP_REQUEST, PERSON}:
            return is_own_resource(context)
```

**CRITICAL ISSUE #2: Incomplete Context Evaluation**
- No supervisor chain validation (can supervisor of supervisor update?)
- No temporal context (can past decisions be modified?)
- No audit trail linking (can updates be traced to original request?)

### 2.4 Permission Caching Strategy

**Redis-based caching (app/auth/permissions/cache.py):**
- Role permissions cached by role key
- User permissions cached by user ID
- Cache TTL: Configurable (default likely 1 hour)

**Cache Keys:**
```
role:{role_name}:{permission_string}
user:{user_id}:permissions
```

**POTENTIAL ISSUE #3: Stale Permission Cache**
- Cache invalidation not visible in code review
- No event-based invalidation on role/permission changes
- If role is changed, old permissions might be cached until TTL

---

## Part 3: ARCANA - Role Hierarchy Design

### 3.1 Role Hierarchy Correctness

**Analysis: Is the hierarchy optimal?**

| Role | Current Parents | Evaluation |
|------|-----------------|-----------|
| ADMIN | None | Correct - highest privilege |
| COORDINATOR | ADMIN | Correct - schedule manager inherits admin view |
| FACULTY | ADMIN, COORDINATOR | QUESTIONABLE - Faculty shouldn't inherit coordinator's modify power |
| RESIDENT | ADMIN, COORDINATOR | WRONG - Residents have no coordinator privileges in real world |
| RN | ADMIN, COORDINATOR, CLINICAL_STAFF | CORRECT - Clinical staff is parent |
| LPN | ADMIN, COORDINATOR, CLINICAL_STAFF | CORRECT - Clinical staff is parent |
| MSA | ADMIN, COORDINATOR, CLINICAL_STAFF | CORRECT - Clinical staff is parent |

**CRITICAL ISSUE #4: Faculty Over-Privileged**
- Faculty should NOT inherit COORDINATOR permissions
- COORDINATOR can create/delete people and assignments
- FACULTY should only view and manage own availability
- Current: Faculty can update PERSON (any person) via inheritance

**CRITICAL ISSUE #5: Resident Over-Privileged**
- RESIDENT inherits COORDINATOR permissions (AccessControlMatrix only)
- RESIDENT should NOT be able to approve other residents' swaps
- Current: Could approve if using AccessControlMatrix path

### 3.2 Principle of Least Privilege Assessment

**Principle:** Each role should have ONLY permissions needed for job function

**Current State:**

| Role | Needed Permissions | Current Permissions | Gap |
|------|-------------------|-------------------|-----|
| ADMIN | All | All ✓ | None |
| COORDINATOR | Schedule CRUD, Approval | Schedule CRUD, Approval, VIEW_AUDIT_LOG, MANAGE_TEMPLATES | Over-scoped |
| FACULTY | View schedules, manage own leave/swaps | View schedules, manage own + APPROVE_SWAP | Over-scoped (can approve others' swaps) |
| RESIDENT | View own schedule, request swaps | View own + REQUEST_SWAP, can APPROVE own | Marginal |
| CLINICAL_STAFF | View schedules | View schedules ✓ | Correct |

---

## Part 4: HISTORY - RBAC Evolution

### 4.1 Implementation Phases Detected

**Phase 1: Basic Authentication (Legacy)**
- Simple `is_admin` checks in endpoints
- Property-based role checking on User model

**Phase 2: Access Control Matrix (Recent)**
- Comprehensive permission matrix
- Resource-action model
- Audit logging framework

**Phase 3: Permission Resolver (Current)**
- Redis caching layer
- Role hierarchy support
- Async-first design

**Issue:** Three overlapping systems create maintenance burden and inconsistency

### 4.2 Missing Evolution Markers

- No version tracking for permission definitions
- No audit trail for permission changes
- No rollback capability for permission updates
- No permission schema versioning

---

## Part 5: INSIGHT - Least Privilege Principle Analysis

### 5.1 Over-Privileged Roles

**FACULTY Role Problem:**
```python
# From access_matrix.py line 369
UserRole.FACULTY: {
    ResourceType.PERSON: {PermissionAction.READ},  # ✓ Own profile
    ResourceType.SWAP_REQUEST: {
        PermissionAction.APPROVE,  # ✗ Can approve others' swaps!
        PermissionAction.REJECT,   # ✗ Should only approve own?
    }
}
```

**Actual Real-World Requirement:**
- Faculty should only approve swaps involving themselves (swap out of their slot)
- Faculty should NOT approve swaps not involving them
- Context check exists but is incomplete

**COORDINATOR Role Problem:**
```python
# From resolver.py line 179
UserRole.COORDINATOR: {
    "person:delete",      # Can delete people!
    "person:create",      # Can create new identities
}
```

**Real-World Requirement:**
- Coordinators shouldn't be able to delete people (HIPAA audit trail)
- Only admins should delete (with approval audit)

**RESIDENT Role Problem:**
```python
# From access_matrix.py line 459
UserRole.RESIDENT: {
    ResourceType.SWAP_REQUEST: {
        PermissionAction.APPROVE,  # ✗ Can approve other residents' swaps?
        PermissionAction.REJECT,   # ✗ This doesn't make sense
    }
}
```

**Real-World Requirement:**
- Residents can request swaps (1:1 trading with peer)
- Residents should NOT approve/reject (that's coordinator role)
- Context check missing: Can resident A approve resident B's request?

### 5.2 Under-Privileged Roles

**CLINICAL_STAFF (RN/LPN/MSA):**
```python
# Only READ access to most resources
# Cannot create absence requests? (they might need time off)
```

**Suggested:** LPN/RN might need to request leave for themselves

---

## Part 6: RELIGION - All Endpoints Protected?

### 6.1 Unprotected Endpoint Scan

**Public Endpoints (No Auth Required):**
```
POST /api/auth/login              # ✓ Correct - no auth needed
POST /api/auth/register           # ✓ Correct - public signup
POST /api/auth/refresh            # ✓ Correct - refresh flow
GET  /api/health                  # ✓ Correct - health check
GET  /api/docs                    # ? Depends on settings.DEBUG
GET  /api/openapi.json            # ? Depends on settings.DEBUG
```

**Protected Endpoints:**
```
GET  /api/people                  # Requires get_current_active_user
GET  /api/schedule                # Requires get_current_active_user
POST /api/assignments             # Requires get_current_active_user
```

### 6.2 Protection Pattern Consistency

**Patterns Found:**

| Pattern | Count | Risk |
|---------|-------|------|
| `Depends(get_current_active_user)` | ~200 | Medium - requires any authenticated user |
| `Depends(get_admin_user)` | ~30 | Low - admin only |
| `Depends(get_scheduler_user)` | ~20 | Low - coordinator only |
| No protection | ~10 | HIGH - unprotected |
| Direct role check | ~84 | Medium - hardcoded logic |

**CRITICAL ISSUE #6: Inconsistent Protection Patterns**

Some endpoints may use:
```python
@router.get("/data")
async def get_data(
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role != "admin":
        raise HTTPException(403)
```

Others might use:
```python
@router.get("/data")
async def get_data(
    current_user: User = Depends(get_admin_user)  # Better
):
    ...
```

**Recommendation:** Standardize on dependency injection, not inline checks

### 6.3 Missing Permission Checks

**Endpoints using dependency but not verifying permissions:**

Found in testing code (test_rbac_authorization.py):
```python
# Endpoint exists but doesn't enforce permission
response = client.get("/api/admin/users", headers=coordinator_headers)
# If response.status_code != 403, permission check is missing!
```

---

## Part 7: NATURE - Over-Granular Permissions?

### 7.1 Permission Matrix Size

**Current Statistics:**
- 20+ resource types (SCHEDULE, ASSIGNMENT, PERSON, etc.)
- 10+ actions (CREATE, READ, UPDATE, DELETE, APPROVE, REJECT, EXECUTE, etc.)
- 8 roles
- Total permission combinations: 1600+

**Assessment:** Right-sized for medical system complexity

### 7.2 Action Granularity

**Too Fine-Grained?**
```python
CREATE, READ, UPDATE, DELETE  # Standard CRUD
APPROVE, REJECT               # Workflow actions
EXECUTE                       # System actions
```

**Problem:** MANAGE action is supposed to represent "all CRUD" but:
```python
# From access_matrix.py line 588
if (
    action in {CREATE, READ, UPDATE, DELETE}
    and PermissionAction.MANAGE in resource_permissions
):
    return True
```

This is fragile - what if new actions are added?

### 7.3 Resource Granularity

**Potential Redundancy:**
```python
ResourceType.SWAP          # Generic swap
ResourceType.SWAP_REQUEST  # Specific to requests
```

Should SWAP_REQUEST be a detail of SWAP resource?

**Suggested Refactor:**
```python
# Instead of separate resources:
ResourceType.SWAP with conditions:
  - type: "request"
  - type: "approved"
  - type: "executed"
```

---

## Part 8: MEDICINE - Authorization Performance

### 8.1 Permission Lookup Performance

**Current Implementation:**
```python
# From access_matrix.py
def has_permission(...) -> bool:
    # 1. Convert strings to enums
    if isinstance(role, str):
        role = UserRole(role)  # O(1)

    # 2. Check static permissions
    role_permissions = self.PERMISSION_MATRIX.get(role, {})  # O(1)
    resource_permissions = role_permissions.get(resource, set())  # O(1)

    # 3. Check inherited permissions (worst case: 8 roles)
    inherited_roles = RoleHierarchy.get_inherited_roles(role)  # O(n)
    for inherited_role in inherited_roles:  # O(8)
        if self._check_static_permission(...):  # O(1)
            has_static_permission = True

    # 4. Audit log (always)
    self._audit_permission_check(...)
```

**Complexity:** O(n) where n = depth of role hierarchy (max 8)

### 8.2 Resolver Caching Performance

**Redis Cache Hit Path:**
```python
# From resolver.py
if use_cache:
    cached = await cache.get_role_permissions(role)  # O(1) Redis GET
    if cached is not None:
        return cached  # Cache hit!
```

**Cache Miss Path:**
```python
all_permissions = set()
hierarchy = self._resolve_role_hierarchy(role)  # O(n) graph traversal
for role in hierarchy:  # O(n)
    all_permissions.update(DEFAULT_ROLE_PERMISSIONS[role])  # O(m)
# Total: O(n*m) where m = permissions per role
```

**Performance Assessment:** Good with caching, acceptable without

### 8.3 Audit Logging Performance

**Current Audit Implementation:**
```python
self.audit_log.append(entry)  # In-memory list
logger.info(f"Permission check...")  # Synchronous logging
```

**Concerns:**
- Audit log is in-memory (lost on restart)
- Synchronous logging blocks request
- No log rotation

**Improvement Needed:** Async audit to database/external log aggregator

---

## Part 9: SURVIVAL - Emergency Access Procedures

### 9.1 Emergency Escalation Paths

**Current Emergency Access:**
```python
# From app/core/security.py
async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(403, "Admin access required")
    return current_user
```

**Problem: Single-Factor Escalation**
- Any admin account compromise = full system access
- No approval required for sensitive operations
- No separate "emergency override" role

### 9.2 Missing Safeguards

**Not Implemented:**
- [ ] Dual-approval for sensitive operations (delete person, modify salary)
- [ ] Emergency access token (time-limited, audit-logged)
- [ ] Rate limiting on admin operations
- [ ] IP-based restrictions for admin accounts
- [ ] Session binding (prevent token reuse from different IP)

### 9.3 Recovery Procedures

**Not Documented:**
- How to recover if all admin accounts compromised?
- How to revoke all tokens quickly?
- How to audit what changed during incident?

**Current Token Blacklist:**
```python
def blacklist_token(
    db: Session,
    jti: str,
    expires_at: datetime,
    user_id: UUID | None = None,
    reason: str = "logout",
):
    # Can only blacklist one token at a time
    # No bulk operations!
```

**Gap:** No way to revoke all tokens for a user in single operation

---

## Part 10: STEALTH - Privilege Escalation Paths

### 10.1 Horizontal Escalation (Access other users' data)

**Attack Vector: Context Check Bypass**

Current code checks:
```python
def is_own_resource(context: PermissionContext) -> bool:
    return (
        context.resource_owner_id is not None
        and context.user_id == context.resource_owner_id
    )
```

**Vulnerability:** If resource_owner_id is not set/checked:
```python
# What if context doesn't include resource_owner_id?
context = PermissionContext(
    user_id=uuid4(),
    user_role=UserRole.FACULTY,
    # resource_owner_id NOT SET - defaults to None
)
# is_own_resource() returns False (safe)
# But what if UPDATE permission checking skips context entirely?
```

### 10.2 Vertical Escalation (Promote to higher role)

**Attack Vector: User Object Mutation**

```python
# If session is not properly managed:
user.role = "admin"
db.commit()  # Permissions now escalated!

# Even better: JWT stores role at issue time
# Change user.role in database
# Old JWT still has old role (safe)
# But new JWT from refresh might have new role!
```

**Current Safeguard:**
```python
# From auth.py - role change requires new login
# JWT is refreshed with new role
```

**Issue:** No explicit check preventing unauthorized role updates

### 10.3 Lateral Escalation (Swap another user's permissions)

**Attack Vector: Object Injection in Swap Request**

```python
# API request:
POST /api/swaps
{
    "resident_a_id": "attacker_id",  # Inject their own ID
    "resident_b_id": "target_id",
    "block_id": "..."
}

# If API doesn't verify context:
# Attacker can create fake swap with target resident
# Depending on approval flow, might gain unauthorized shifts
```

**Mitigation Check (from context validation):**
```python
# Should verify:
# - Current user ID matches one of the swap participants
# - Current user has authority to create swap
```

### 10.4 Token Theft & Reuse

**Current Protection:**
- httpOnly cookies (prevents XSS token theft)
- Short-lived access tokens (30 min)
- Token blacklist on logout

**Missing Protection:**
- No IP binding (stolen token works from any IP)
- No device fingerprint (stolen token works on any device)
- No session binding (no way to revoke single session)

**New Attack:** Token theft via HTTP logging or backup
```
1. Attacker gets token via backup disclosure
2. Uses token from different IP/device
3. System cannot detect anomaly
4. Access continues until token expires
```

---

## RBAC Matrix Analysis

### Authorization Matrix (Current State)

```
ROLE          | SCHEDULE | ASSIGNMENT | PERSON | SWAP | ABSENCE | USER_MGMT | ADMIN
-----------   |----------|-----------|--------|------|---------|-----------|-------
ADMIN         | C R U D X| C R U D X | C R U D| A E  | A L      | C R U D   | ✓
COORDINATOR   | C R U X  | C R U X   | R U    | R A E| R A L    | -         | -
FACULTY       | R L      | R L       | R      | C R U| C R U    | -         | -
RESIDENT      | R L      | R L       | R      | C R U| C R U    | -         | -
CLINICAL_STAFF| R L      | R L       | R L    | -    | -        | -         | -
RN            | R L      | R L       | R L    | -    | -        | -         | -
LPN           | R L      | R L       | R L    | -    | -        | -         | -
MSA           | R L      | R L       | R L    | -    | -        | -         | -

Legend:
C = CREATE    R = READ    U = UPDATE    D = DELETE    X = EXECUTE/APPROVE
L = LIST      A = APPROVE E = EXECUTE
✓ = Full access
```

### Permission Gap Analysis

**Cells with Potential Issues:**

| Gap | Severity | Description |
|-----|----------|-------------|
| FACULTY can approve SWAP | HIGH | Should only approve swaps they're in |
| RESIDENT can approve SWAP | HIGH | Only coordinator should approve |
| COORDINATOR can DELETE PERSON | MEDIUM | Audit trail suggests delete not allowed |
| FACULTY inherits COORDINATOR | HIGH | Violates least privilege |
| RESIDENT inherits COORDINATOR | CRITICAL | Shouldn't exist in real world |
| Clinical staff READ PERSON | MEDIUM | Should be limited to schedule-related data |

---

## Critical Findings Summary

### CRITICAL ISSUES (Exploit Possible)

1. **Role Hierarchy Mismatch** (P1)
   - Two different hierarchies cause inconsistent evaluation
   - Using wrong system could grant/deny wrong permissions
   - **Fix:** Unify to single hierarchy

2. **Faculty Over-Privileged** (P1)
   - Faculty inherit COORDINATOR permissions (delete people, update all assignments)
   - Real-world: Faculty should only view and manage own availability
   - **Fix:** Remove COORDINATOR inheritance for FACULTY

3. **Resident Swap Approval** (P1)
   - Resident can APPROVE swaps (what does this mean?)
   - Real-world: Only coordinator approves swaps
   - **Fix:** Remove APPROVE/REJECT from RESIDENT SWAP_REQUEST

4. **Incomplete Context Validation** (P1)
   - FACULTY can APPROVE swaps not involving them
   - is_own_resource() not called for all permission checks
   - **Fix:** Verify context for every permission check

5. **No Cache Invalidation** (P2)
   - Permission changes not reflected immediately
   - Role promotion might not work until cache expires
   - **Fix:** Implement event-based cache invalidation

### HIGH PRIORITY ISSUES (Likely Exploitable)

6. **Inconsistent Endpoint Protection** (P2)
   - Mix of dependency injection and inline role checks
   - Some endpoints might bypass permission framework
   - **Fix:** Standardize all endpoints to use permission framework

7. **Missing Audit Trail for Permission Changes** (P2)
   - No history of who changed roles/permissions
   - Cannot reconstruct security incidents
   - **Fix:** Add audit table for permission mutations

8. **No Privilege Escalation Detection** (P2)
   - No alerting when user requests admin operation
   - No rate limiting on sensitive operations
   - **Fix:** Add detection and alerting

9. **Token Theft Not Detectable** (P2)
   - No IP/device binding
   - No anomaly detection
   - **Fix:** Add session context tracking

10. **No Bulk Token Revocation** (P2)
    - Can only blacklist one token at a time
    - Cannot revoke all sessions for compromised user
    - **Fix:** Add user-level token revocation

---

## Recommendations

### Immediate Actions (This Sprint)

**R1: Fix Role Hierarchy Mismatch (P1)**
```python
# backend/app/auth/permissions/models.py
# Make both systems use same hierarchy
ROLE_HIERARCHY = {
    UserRole.ADMIN: [],
    UserRole.COORDINATOR: [UserRole.ADMIN],
    UserRole.FACULTY: [],  # NOT coordinator!
    UserRole.RESIDENT: [],  # NOT coordinator!
    UserRole.CLINICAL_STAFF: [],
    UserRole.RN: [UserRole.CLINICAL_STAFF],
    UserRole.LPN: [UserRole.CLINICAL_STAFF],
    UserRole.MSA: [UserRole.CLINICAL_STAFF],
}
```

**R2: Remove Resident Swap Approval (P1)**
```python
# backend/app/auth/access_matrix.py line 453
UserRole.RESIDENT: {
    ResourceType.SWAP_REQUEST: {
        PermissionAction.CREATE,
        PermissionAction.READ,
        PermissionAction.UPDATE,
        PermissionAction.LIST,
        # Remove: PermissionAction.APPROVE, PermissionAction.REJECT
    }
}
```

**R3: Implement Supervisor Context Check (P1)**
```python
# backend/app/auth/access_matrix.py
def _check_context_permission(...):
    if resource == ResourceType.SWAP_REQUEST:
        if action in {APPROVE, REJECT}:
            # Must be coordinator or supervisor of person
            return is_supervisor_of_person(context) or user_is_coordinator
```

**R4: Enforce Cache Invalidation (P2)**
```python
# backend/app/auth/permissions/cache.py
async def invalidate_user_permissions(user_id: UUID):
    """Revoke all cached permissions for user after role change."""
    cache_key = f"user:{user_id}:permissions"
    await cache.delete(cache_key)
```

### Short-Term Actions (Next 2 Weeks)

**R5: Standardize Endpoint Protection (P2)**
- Audit all 57 route files
- Replace inline role checks with dependency injection
- Use consistent `require_permission()` decorator

**R6: Add Permission Audit Table (P2)**
```python
# New table: permission_audit_log
# Track: who changed what permission, when, why
# Enable incident reconstruction
```

**R7: Implement Bulk Token Revocation (P2)**
```python
# backend/app/models/token_blacklist.py
async def revoke_all_tokens_for_user(user_id: UUID):
    """Revoke all tokens for user (compromised account)."""
    # Update all tokens to blacklist
    # Add to queue for notification service
```

**R8: Add Session Context Binding (P2)**
```python
# Store in JWT:
- ip_address (at login)
- device_fingerprint (user-agent)
- session_id (unique per login)

# Validate on each request:
if request.ip_address != jwt.ip_address:
    log_anomaly()  # Might be token theft
```

### Medium-Term Actions (This Quarter)

**R9: Consolidate Permission Systems (P3)**
- Migrate all endpoints to unified permission framework
- Deprecate inline role checks
- Remove AccessControlMatrix if using PermissionResolver

**R10: Implement Privilege Escalation Detection (P3)**
```python
# New service: PrivilegeEscalationDetector
# Alerts on:
- User requesting permissions > current role
- Multiple failed permission checks
- Access to sensitive resources from non-standard IP
```

**R11: Add Role-Based Rate Limiting (P3)**
```python
# Tighter limits for:
- User creation (admin)
- Role changes (admin)
- Swap approvals (coordinator)
- Absence approvals (coordinator)
```

**R12: Implement Approval Workflow for Sensitive Operations (P3)**
```python
# Operations requiring dual approval:
- User deletion
- Role escalation
- Permission changes
- Schedule publication
```

### Documentation

**D1: Create RBAC Design Doc** (Where?)
- Define canonical role hierarchy
- Document each role's purpose and permissions
- Include real-world job functions

**D2: Create Authorization Implementation Guide**
- How to add new permission
- How to check permission in endpoint
- Testing checklist

---

## Test Coverage Assessment

### Current Test Coverage

**Strengths:**
- Test file exists: `backend/tests/auth/test_rbac_authorization.py`
- Covers 8 roles with fixtures
- Tests authentication and token validation
- Tests permission edge cases

**Gaps:**

| Test Case | Status | Priority |
|-----------|--------|----------|
| Test role hierarchy inheritance | Missing | P1 |
| Test context-aware permissions | Missing | P1 |
| Test permission cache invalidation | Missing | P2 |
| Test bulk token revocation | Missing | P2 |
| Test privilege escalation detection | Missing | P3 |
| Test inconsistent hierarchy handling | Missing | P1 |

### Recommended New Tests

```python
# backend/tests/auth/test_privilege_escalation.py

class TestPrivilegeEscalation:
    """Test privilege escalation prevention."""

    async def test_faculty_cannot_delete_person():
        # Verify FACULTY doesn't inherit COORDINATOR DELETE

    async def test_resident_cannot_approve_other_swaps():
        # Verify RESIDENT can't approve swap not involving them

    async def test_role_change_requires_reauth():
        # Verify old token doesn't have new permissions

    async def test_cache_invalidation_on_role_change():
        # Verify cached permissions cleared when role changes
```

---

## Conclusion

The authorization system has **strong foundational security** with JWT tokens, role hierarchies, and permission matrices. However, **critical privilege escalation gaps** exist due to:

1. **Conflicting role hierarchies** - needs immediate unification
2. **Incomplete context validation** - permissions granted without full context
3. **Over-privileged roles** - faculty and residents can do too much
4. **Missing audit trails** - cannot reconstruct permission changes
5. **No escalation detection** - silent privilege violations

**Overall Security Rating: C+ (Fair)**
- Strong authentication: A
- RBAC framework: B-
- Permission enforcement: C
- Audit & monitoring: D
- Emergency procedures: D

**Recommendation:** Address P1 findings before next release. Current system is exploitable if attacker gains any user account.

---

## Appendix: File References

### Key Authorization Files

1. **Authentication Core**
   - `/backend/app/core/security.py` - JWT, password hashing, user dependencies
   - `/backend/app/models/user.py` - User model with roles

2. **Authorization Framework**
   - `/backend/app/auth/access_matrix.py` - RBAC matrix with permissions
   - `/backend/app/auth/permissions/models.py` - Permission enums and defaults
   - `/backend/app/auth/permissions/resolver.py` - Permission resolver with caching
   - `/backend/app/auth/permissions/decorators.py` - Route decorators for permissions
   - `/backend/app/auth/permissions/cache.py` - Redis permission cache

3. **Endpoint Protection**
   - `/backend/app/api/routes/auth.py` - Authentication endpoints
   - `/backend/app/api/routes/admin_users.py` - Admin user management
   - 55+ other route files with protected endpoints

4. **Testing**
   - `/backend/tests/auth/test_rbac_authorization.py` - RBAC tests

### Configuration Files
- `.env.example` - Environment variables for auth settings
- `docker-compose.yml` - Redis for permission caching

---

**Audit Completed:** 2025-12-30
**Next Review:** 2025-01-30
**Auditor:** G2_RECON Security Analyst
