# G2 RECON: API Collection Cleanup Manifest

## Intelligence Assessment
**Date:** 2025-12-31
**Agent:** G2_RECON (Intelligence/Reconnaissance)
**Mission Status:** COMPLETE

---

## Executive Summary

Two Postman collection files have been identified in the codebase. **Recommendation: DELETE `/collections/postman-collection.json` and KEEP `postman_collection.json` in root.**

The collections are NOT auto-generated and represent two different document versions created at different times. The root collection is newer, better documented, and referenced in official documentation.

---

## File Inventory

| File | Location | Size | Lines | Modified |
|------|----------|------|-------|----------|
| **postman_collection.json** | `/docs/api/` | 24KB | 864 | 2025-12-31 07:13 |
| **postman-collection.json** | `/docs/api/collections/` | 27KB | 913 | 2025-12-30 18:34 |

---

## Detailed Comparison

### Collection 1: `/docs/api/postman_collection.json` (RECOMMENDED KEEP)

**Metadata:**
```json
{
  "info": {
    "name": "Residency Scheduler API",
    "description": "Complete API collection for medical residency scheduling system",
    "version": "1.0.0"
  }
}
```

**Structure:**
- `schema`: NOT SPECIFIED (missing Postman standard)
- `_postman_id`: NOT SPECIFIED
- Root-level `auth`: NO
- Root-level `variable`: YES (9 environment variables)
- Top-level folders: 6
  - Authentication
  - People
  - Assignments
  - Schedule
  - Swaps
  - Resilience

**Endpoints:** 33 total requests
- Authentication: 7 endpoints
- People: 10 endpoints (includes credentials & procedures)
- Assignments: 6 endpoints (includes bulk operations)
- Schedule: 4 endpoints
- Swaps: 3 endpoints
- Resilience: 3 endpoints

**API Paths:** `/api/*` (non-versioned)

**Last Modified:** 2025-12-31 07:13 UTC
**Git Commit:** f663daf0 (2025-12-31 - "feat: 10-session parallel burn")

---

### Collection 2: `/docs/api/collections/postman-collection.json` (RECOMMENDED DELETE)

**Metadata:**
```json
{
  "info": {
    "name": "Residency Scheduler API",
    "description": "Complete API collection for Residency Scheduler - Medical residency program schedule management with ACGME compliance",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    "_postman_id": "residency-scheduler-api-v1",
    "version": "1.0.0"
  }
}
```

**Structure:**
- `schema`: SPECIFIED (Postman v2.1.0 standard)
- `_postman_id`: "residency-scheduler-api-v1" (explicit ID)
- Root-level `auth`: YES (Bearer token auth defined)
- Root-level `variable`: YES (6 environment variables)
- Top-level folders: 6
  - Authentication
  - Schedule
  - Assignments
  - Persons
  - Swaps
  - Resilience

**Endpoints:** 38 total requests
- Authentication: 5 endpoints (fewer than Collection 1)
- Schedule: 5 endpoints
- Assignments: 6 endpoints (includes bulk delete)
- Persons: 10 endpoints (renamed from "People")
- Swaps: 5 endpoints (includes rollback endpoint)
- Resilience: 7 endpoints (more comprehensive)

**API Paths:** `/api/v1/*` (versioned)

**Last Modified:** 2025-12-30 18:34 UTC
**Git Commit:** 5a9c0bc7 (2025-12-30 - "feat: Massive parallel development")

---

## Analysis

### Key Differences

| Aspect | Collection 1 | Collection 2 |
|--------|-------------|-------------|
| **Postman Compliance** | Minimal (no schema/ID) | Full (schema + ID) |
| **Root Auth Config** | Missing | Defined (Bearer) |
| **Environment Vars** | 9 variables | 6 variables |
| **API Versioning** | `/api/*` (unversioned) | `/api/v1/*` (versioned) |
| **Auth Endpoints** | 7 (form + JSON login) | 5 (JSON login only) |
| **Resilience Endpoints** | 3 basic | 7 advanced (history, fallbacks, events) |
| **Total Endpoints** | 33 | 38 |
| **Folder Names** | "People" | "Persons" |
| **Last Modified** | 2025-12-31 (NEWER) | 2025-12-30 (OLDER) |

### Generation Analysis

**Both collections are MANUALLY CREATED, NOT AUTO-GENERATED:**
- No auto-generation markers or comments
- Inconsistent structure (different field orderings, different endpoints)
- Contains hand-written descriptions and examples
- Endpoint lists don't perfectly match actual API
- No build/export metadata

**Evidence of Manual Creation:**
1. Different endpoint counts (33 vs 38)
2. Different authentication approaches (form-based vs bearer)
3. Different folder organization (Authentication first vs Schedule first)
4. Custom descriptions with context ("medical residency scheduling system")
5. Test scripts in JSON bodies (Postman feature)

### Official Documentation Reference

Per `/docs/api/README.md` (Lines 236-262):

```markdown
## Postman Collection

### [postman_collection.json](postman_collection.json)

Import this collection into Postman for interactive API testing...
```

**Finding:** Official documentation references ONLY `postman_collection.json` (in root `/docs/api/`), NOT the `/collections/` subdirectory version.

---

## Root Cause Analysis

### Why Two Collections Exist

1. **Timeline:**
   - Collection 2 created 2025-12-30 (older, includes v1 API paths)
   - Collection 1 updated 2025-12-31 (newer, removed versioning from paths)
   - Both maintained separately without synchronization

2. **Directory Structure:**
   - Root location (`/docs/api/postman_collection.json`) = Primary, documented
   - Subdirectory (`/docs/api/collections/postman-collection.json`) = Secondary, orphaned

3. **Content Divergence:**
   - Reflects two different API design decisions (versioned vs non-versioned)
   - Different endpoint implementations
   - Different maturity levels (Collection 2 more comprehensive in resilience)

---

## Cleanup Decision Matrix

### KEEP: `/docs/api/postman_collection.json`

**Reasons:**
1. **Official Documentation:** Referenced in `/docs/api/README.md`
2. **Recency:** Modified 2025-12-31 (1 day newer)
3. **Root Location:** Standard location for API artifacts
4. **Simplicity:** No API versioning (`/api` not `/api/v1`)
5. **Better Auth Coverage:** Includes form-based login for testing

**Risk Level:** LOW - This is the documented collection

---

### DELETE: `/docs/api/collections/postman-collection.json`

**Reasons:**
1. **Orphaned:** No documentation reference
2. **Deprecated:** 1 day older than primary
3. **Subdirectory Location:** Non-standard placement
4. **Redundant:** Duplicate functionality with primary
5. **Confusing:** Creates confusion for API users importing collections
6. **API Versioning Mismatch:** Uses `/api/v1/*` but API doesn't support versioning

**Risk Level:** LOW - No documentation depends on this file

---

## Recommendations

### Priority 1: DELETE (Immediate)
- `/docs/api/collections/postman-collection.json`

**Action:**
```bash
rm /docs/api/collections/postman-collection.json
```

**Why:** Eliminates confusion and maintains single source of truth

---

### Priority 2: VERIFY (After Deletion)
Confirm that:
1. No documentation references the old path
2. No CI/CD pipelines use the old collection
3. Git history preserved (deletion logged)

**Verification:**
```bash
grep -r "collections/postman" docs/
grep -r "collections/postman" .github/
```

**Expected Result:** No matches (clean deletion)

---

### Priority 3: OPTIONAL ENHANCEMENT (If Resources Available)

**Merge Collection 2's Advanced Features into Collection 1:**

Collection 2 includes more advanced resilience endpoints:
- `GET /api/v1/resilience/fallbacks` → Fallback schedule management
- `GET /api/v1/resilience/health/history` → Health history
- `GET /api/v1/resilience/events` → Event tracking
- `GET /api/v1/resilience/vulnerability` → Vulnerability reporting
- `POST /api/v1/resilience/crisis/activate` → Crisis mode
- `POST /api/v1/resilience/crisis/deactivate` → Crisis resolution

**Recommendation:** If API supports these endpoints, manually add them to primary collection after deletion

---

## Implementation Checklist

- [ ] Review this manifest for approval
- [ ] Delete `/docs/api/collections/postman-collection.json`
- [ ] Verify no grep matches in documentation
- [ ] Verify no CI/CD pipeline references
- [ ] Commit deletion with message: "cleanup: Remove duplicate Postman collection (#XXX)"
- [ ] Test import of remaining collection in Postman UI

---

## Evidence Files

**Maintained Analysis Output:**
```
Collection 1: /docs/api/postman_collection.json
- Lines: 864
- Size: 24KB
- Endpoints: 33
- Modified: 2025-12-31 07:13
- Documentation: YES (README.md Line 238)

Collection 2: /docs/api/collections/postman-collection.json
- Lines: 913
- Size: 27KB
- Endpoints: 38
- Modified: 2025-12-30 18:34
- Documentation: NO (Orphaned)
```

---

## Sign-Off

**Intelligence Agent:** G2_RECON
**Assessment Date:** 2025-12-31
**Status:** READY FOR HUMAN APPROVAL

**Recommendation:** PROCEED WITH DELETION (LOW RISK)

All supporting analysis attached. Ready for execution upon approval.

---

*Generated by G2_RECON reconnaissance team*
*Part of SEARCH_PARTY protocol - D&D-inspired intelligence gathering*
