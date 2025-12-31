***REMOVED*** RBAC Permission Matrix - Detailed Reference

**Generated:** 2025-12-30
**Purpose:** Complete role-permission mapping for authorization audit

---

***REMOVED******REMOVED*** 1. Complete Permission Matrix by Role

***REMOVED******REMOVED******REMOVED*** ADMIN Role

Full system access across all resources and actions.

| Resource | CREATE | READ | UPDATE | DELETE | LIST | APPROVE | REJECT | EXECUTE | MANAGE |
|----------|--------|------|--------|--------|------|---------|--------|---------|--------|
| SCHEDULE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ASSIGNMENT | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| BLOCK | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| ROTATION | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| PERSON | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| RESIDENT | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| FACULTY_MEMBER | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| ABSENCE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| LEAVE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| SWAP | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| SWAP_REQUEST | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| CONFLICT | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ |
| CONFLICT_ALERT | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ |
| PROCEDURE | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| CREDENTIAL | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| CERTIFICATION | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| USER | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| SETTINGS | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| FEATURE_FLAG | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| REPORT | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| ANALYTICS | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| AUDIT_LOG | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| NOTIFICATION | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| EMAIL_TEMPLATE | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| RESILIENCE_METRIC | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| CONTINGENCY_PLAN | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - |

**Total Permissions:** 26 resources × 9 actions = 234/234 possible

---

***REMOVED******REMOVED******REMOVED*** COORDINATOR Role

Schedule management, approval workflows, and people management.

| Resource | CREATE | READ | UPDATE | DELETE | LIST | APPROVE | REJECT | EXECUTE |
|----------|--------|------|--------|--------|------|---------|--------|---------|
| SCHEDULE | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | ✓ |
| ASSIGNMENT | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| BLOCK | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| ROTATION | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| PERSON | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| RESIDENT | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| FACULTY_MEMBER | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| ABSENCE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| LEAVE | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| SWAP | - | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ |
| SWAP_REQUEST | - | ✓ | ✓ | - | ✓ | ✓ | ✓ | - |
| CONFLICT | - | ✓ | ✓ | - | ✓ | - | - | - |
| CONFLICT_ALERT | - | ✓ | ✓ | - | ✓ | - | - | - |
| REPORT | - | ✓ | - | - | ✓ | - | - | ✓ |
| ANALYTICS | - | ✓ | - | - | ✓ | - | - | - |
| NOTIFICATION | ✓ | ✓ | - | - | ✓ | - | - | - |
| RESILIENCE_METRIC | - | ✓ | - | - | ✓ | - | - | - |
| CONTINGENCY_PLAN | - | ✓ | ✓ | - | ✓ | - | - | - |

**Risk Assessment:** COORDINATOR has CREATE/UPDATE on PERSON (can create fake identities)

---

***REMOVED******REMOVED******REMOVED*** FACULTY Role

View schedules, manage own availability, request and approve own swaps.

| Resource | CREATE | READ | UPDATE | LIST | APPROVE | REJECT |
|----------|--------|------|--------|------|---------|--------|
| SCHEDULE | - | ✓ | - | ✓ | - | - |
| ASSIGNMENT | - | ✓ | - | ✓ | - | - |
| BLOCK | - | ✓ | - | ✓ | - | - |
| ROTATION | - | ✓ | - | ✓ | - | - |
| PERSON | - | ✓ | ✓ | - | - | - |
| ABSENCE | ✓ | ✓ | ✓ | - | - | - |
| LEAVE | ✓ | ✓ | ✓ | - | - | - |
| SWAP | ✓ | ✓ | ✓ | ✓ | - | - |
| SWAP_REQUEST | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PROCEDURE | - | ✓ | - | ✓ | - | - |
| CREDENTIAL | - | ✓ | - | ✓ | - | - |
| CERTIFICATION | - | ✓ | - | ✓ | - | - |
| NOTIFICATION | - | ✓ | - | ✓ | - | - |

**Risk Assessment:** FACULTY can APPROVE/REJECT SWAP_REQUEST (should be limited to own swaps only)

---

***REMOVED******REMOVED******REMOVED*** RESIDENT Role

View own schedule, request swaps and leave.

| Resource | CREATE | READ | UPDATE | LIST | APPROVE | REJECT |
|----------|--------|------|--------|------|---------|--------|
| SCHEDULE | - | ✓ | - | ✓ | - | - |
| ASSIGNMENT | - | ✓ | - | ✓ | - | - |
| BLOCK | - | ✓ | - | ✓ | - | - |
| ROTATION | - | ✓ | - | ✓ | - | - |
| PERSON | - | ✓ | - | - | - | - |
| ABSENCE | ✓ | ✓ | - | - | - | - |
| LEAVE | ✓ | ✓ | - | - | - | - |
| SWAP | ✓ | ✓ | ✓ | ✓ | - | - |
| SWAP_REQUEST | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| CONFLICT | - | ✓ | - | ✓ | - | - |
| NOTIFICATION | - | ✓ | - | ✓ | - | - |

**Risk Assessment:** RESIDENT can APPROVE/REJECT SWAP_REQUEST (semantically wrong - should COORDINATOR do this?)

---

***REMOVED******REMOVED******REMOVED*** CLINICAL_STAFF Role

Read-only access to schedules for operational use.

| Resource | READ | LIST |
|----------|------|------|
| SCHEDULE | ✓ | ✓ |
| ASSIGNMENT | ✓ | ✓ |
| BLOCK | ✓ | ✓ |
| ROTATION | ✓ | ✓ |
| PERSON | ✓ | ✓ |
| NOTIFICATION | ✓ | ✓ |

---

***REMOVED******REMOVED******REMOVED*** RN, LPN, MSA Roles

Same as CLINICAL_STAFF with optional role-specific additions.

**RN-specific additions:**
- PROCEDURE: READ, LIST

**LPN-specific additions:**
- (None currently)

**MSA-specific additions:**
- (None currently)

---

***REMOVED******REMOVED*** 2. Risk-Ranked Permission Violations

***REMOVED******REMOVED******REMOVED*** Critical Risk Issues

**Issue ***REMOVED***1: FACULTY Can Approve Swaps They're Not In**
```
Current: FACULTY has SWAP_REQUEST {APPROVE, REJECT}
Problem: No context check - can approve any swap
Real-world: Faculty should only approve swaps involving themselves

Impact: Faculty could:
- Approve resident's swap without their participation
- Reject resident's swap out of spite
- Bypass coordinator approval workflow

Example Attack:
  1. Faculty-A sees Resident-B wants to swap with Resident-C
  2. Faculty-A doesn't like Resident-C
  3. Faculty-A clicks "REJECT" on swap
  4. Swap disappears without coordinator knowing
```

**Issue ***REMOVED***2: RESIDENT Can Approve Swaps**
```
Current: RESIDENT has SWAP_REQUEST {APPROVE, REJECT}
Problem: Makes no sense semantically
Real-world: Residents cannot approve anything (no authority)

Impact: Resident could:
- Create their own swap request
- Immediately approve it (bypass coordinator)
- Change swap status unilaterally

Example Attack:
  1. Resident creates SWAP_REQUEST (request_swap)
  2. Same resident changes to SWAP_REQUEST (approve)
  3. Swap treated as approved without coordinator review
```

**Issue ***REMOVED***3: COORDINATOR Can Delete People**
```
Current: COORDINATOR has PERSON {CREATE, UPDATE, DELETE}
Problem: Destroys audit trail in medical system
Real-world: HIPAA requires retaining medical records

Impact: Coordinator could:
- Delete resident's person record
- Resident assignments disappear
- No audit trail of who worked what shifts
- HIPAA violation

Real Requirement: Only admins with dual approval can "delete"
  (Actually archive, not true delete)
```

**Issue ***REMOVED***4: FACULTY Inherits COORDINATOR Permissions**
```
Current Role Hierarchy:
  FACULTY → [ADMIN, COORDINATOR]

Problem: FACULTY inherits all COORDINATOR permissions

Impact: Faculty can:
- Create new residents (PERSON create)
- Delete existing residents (PERSON delete)
- Modify other faculty assignments
- Execute (publish) schedules

Real-world: Faculty should be read-only + own profile management
```

---

***REMOVED******REMOVED*** 3. Permission Scope Analysis

***REMOVED******REMOVED******REMOVED*** By Operation Type

***REMOVED******REMOVED******REMOVED******REMOVED*** Schedule Operations
| Role | Generate | Approve | Publish | Modify | View |
|------|----------|---------|---------|--------|------|
| ADMIN | ✓ | ✓ | ✓ | ✓ | ✓ |
| COORDINATOR | ✓ | ✓ | ✓ | ✓ | ✓ |
| FACULTY | - | - | - | - | ✓ |
| RESIDENT | - | - | - | - | ✓ |
| CLINICAL_STAFF | - | - | - | - | ✓ |

**Assessment:** Correct - only ADMIN/COORDINATOR should modify

***REMOVED******REMOVED******REMOVED******REMOVED*** Assignment Operations
| Role | Create | Modify | Delete | View | Reassign |
|------|--------|--------|--------|------|----------|
| ADMIN | ✓ | ✓ | ✓ | ✓ | ✓ |
| COORDINATOR | ✓ | ✓ | ✓ | ✓ | ✓ |
| FACULTY | - | - | - | ✓ | - |
| RESIDENT | - | - | - | ✓ | - |
| CLINICAL_STAFF | - | - | - | ✓ | - |

**Assessment:** Correct - only COORDINATOR should assign

***REMOVED******REMOVED******REMOVED******REMOVED*** Person Management
| Role | Create | Modify | Delete | View |
|------|--------|--------|--------|------|
| ADMIN | ✓ | ✓ | ✓ | ✓ |
| COORDINATOR | ✓ | ✓ | ✓ | ✓ |
| FACULTY | - | ✓* | - | ✓ |
| RESIDENT | - | - | - | ✓ |
| CLINICAL_STAFF | - | - | - | ✓ |

**Assessment:** FACULTY can MODIFY is fine (own profile). But COORDINATOR DELETE is risky.

---

***REMOVED******REMOVED*** 4. Data Flow Permission Checks

***REMOVED******REMOVED******REMOVED*** Schedule Publication Workflow

```
1. COORDINATOR generates schedule
   └─ Requires: SCHEDULE.CREATE (✓ COORDINATOR has this)

2. COORDINATOR approves blocks
   └─ Requires: SCHEDULE.APPROVE (✓ COORDINATOR has this)

3. COORDINATOR publishes
   └─ Requires: SCHEDULE.PUBLISH (✓ COORDINATOR has this)
              or SCHEDULE.EXECUTE (✓ COORDINATOR has this)

4. FACULTY views schedule
   └─ Requires: SCHEDULE.READ (✓ FACULTY has this)

5. RESIDENT requests swap
   └─ Requires: SWAP.CREATE (✓ RESIDENT has this)

6. FACULTY approves swap ???
   └─ Current: SWAP_REQUEST.APPROVE (✓ FACULTY has this)
   └─ Real-world: Should be COORDINATOR.APPROVE
   └─ PROBLEM: Context check missing!

7. COORDINATOR finalizes swap
   └─ Requires: SWAP.EXECUTE (✓ COORDINATOR has this)
```

**Gap:** Step 6 - FACULTY approval shouldn't exist

---

***REMOVED******REMOVED*** 5. Context-Aware Permission Evaluation

***REMOVED******REMOVED******REMOVED*** Current Implementation

```python
***REMOVED*** From access_matrix.py

***REMOVED*** Own resource context:
if role in {RESIDENT, FACULTY}:
    if action in {UPDATE, DELETE}:
        if resource in {ABSENCE, LEAVE, SWAP_REQUEST, PERSON}:
            ***REMOVED*** Check: user_id == resource.owner_id
            return is_own_resource(context)

***REMOVED*** Supervisor context:
if role in {ADMIN, COORDINATOR}:
    return True  ***REMOVED*** Supervisors can do anything
```

***REMOVED******REMOVED******REMOVED*** Missing Context Evaluators

```python
***REMOVED*** Not implemented:

***REMOVED*** Swap participant context
def is_swap_participant(context):
    """Check if user is one of the swap participants."""
    ***REMOVED*** For SWAP.APPROVE:
    ***REMOVED*** Should check if user is resident A or resident B

***REMOVED*** Temporal context
def is_recent_request(context):
    """Check if request was created recently."""
    ***REMOVED*** For SWAP_REQUEST.REJECT:
    ***REMOVED*** Should not allow rejecting old requests

***REMOVED*** Approval chain context
def is_in_approval_chain(context):
    """Check if user is authorized to approve this resource."""
    ***REMOVED*** For ABSENCE.APPROVE:
    ***REMOVED*** Check supervisor chain

***REMOVED*** Cross-team context
def is_same_team(context):
    """Check if user and target are in same team."""
    ***REMOVED*** For PERSON.UPDATE:
    ***REMOVED*** Should not allow modifying other teams' people
```

---

***REMOVED******REMOVED*** 6. Recommended Fixes (Priority Order)

***REMOVED******REMOVED******REMOVED*** P1 - Must Fix Before Release

1. **Remove FACULTY APPROVE/REJECT for swaps not involving them**
   ```python
   ***REMOVED*** Current: FACULTY can APPROVE any SWAP_REQUEST
   ***REMOVED*** Fixed: FACULTY can only APPROVE own swap_requests

   ***REMOVED*** Requires context check:
   is_faculty_participant_in_swap(context)
   ```

2. **Remove RESIDENT APPROVE/REJECT entirely**
   ```python
   ***REMOVED*** Current: RESIDENT can APPROVE any SWAP_REQUEST
   ***REMOVED*** Fixed: Remove approval permission from RESIDENT

   UserRole.RESIDENT: {
       ResourceType.SWAP_REQUEST: {
           PermissionAction.CREATE,
           PermissionAction.READ,
           PermissionAction.UPDATE,
           PermissionAction.LIST,
           ***REMOVED*** REMOVE: APPROVE, REJECT
       }
   }
   ```

3. **Remove COORDINATOR DELETE on PERSON**
   ```python
   ***REMOVED*** Current: COORDINATOR can DELETE people
   ***REMOVED*** Fixed: Only ADMIN can "delete" (really archive)

   UserRole.COORDINATOR: {
       ResourceType.PERSON: {
           PermissionAction.CREATE,
           PermissionAction.READ,
           PermissionAction.UPDATE,
           ***REMOVED*** REMOVE: DELETE
       }
   }
   ```

4. **Fix FACULTY role hierarchy**
   ```python
   ***REMOVED*** Current hierarchy (WRONG):
   FACULTY: [ADMIN, COORDINATOR]

   ***REMOVED*** Fixed hierarchy:
   FACULTY: [ADMIN]  ***REMOVED*** Only inherit from ADMIN, not COORDINATOR
   ```

***REMOVED******REMOVED******REMOVED*** P2 - Should Fix This Sprint

5. **Implement context validators**
   ```python
   def _register_context_evaluators(self):
       self._context_evaluators["is_swap_participant"] = ...
       self._context_evaluators["is_same_supervisor"] = ...
       self._context_evaluators["is_approval_authorized"] = ...
   ```

6. **Enforce context checks in permission evaluation**
   ```python
   ***REMOVED*** For every permission check, verify context is evaluated
   if resource == SWAP_REQUEST and action in {APPROVE, REJECT}:
       if not context:
           raise ValueError("Context required for swap approval")
       if not self._context_evaluators["is_swap_participant"](context):
           return False
   ```

---

***REMOVED******REMOVED*** Conclusion

**Current Matrix Assessment:**
- ✓ Structure is well-organized
- ✗ Multiple violations of least privilege
- ✗ Missing context checks for critical operations
- ✗ Inconsistent role hierarchy

**Security Impact:** Medium - Exploitable if user gains FACULTY or RESIDENT access

**Recommended Action:** Implement all P1 fixes before system goes live with real data

---

**Last Updated:** 2025-12-30
**Review Cycle:** Quarterly (Every 3 months)
**Maintainer:** Security Team
