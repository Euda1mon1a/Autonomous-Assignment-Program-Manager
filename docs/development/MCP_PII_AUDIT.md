# MCP PII Audit Report

> **Audit Date:** 2025-12-24
> **Scope:** mcp-server/src/**/*.py
> **Status:** REVIEW COMPLETE - Changes Required Before Production Use

---

## Executive Summary

The MCP tools contain **mock data with fake names** (Dr. Williams, Dr. Chen, etc.) that would be sent to Claude's API if used as-is. While these are not real PII, the **code patterns** would pull real PII if connected to the database.

**Recommendation:** Connect to FastAPI (not direct DB) and ensure API responses are sanitized.

---

## Findings

### 1. Mock Data with Fake Names (LOW RISK)

**Location:** `mcp-server/src/scheduler_mcp/tools.py`

```python
# Lines 252, 273, 295, 341, 850, 889, 928, 967, 1008
person_name="Dr. Williams"
person_name="Dr. Chen"
person_name="Dr. Patel"
person_name="Dr. Martinez"
candidate_name="Dr. Thompson"
candidate_name="Dr. Lee"
```

**Risk:** LOW - These are hardcoded mock data, not real PII
**Action:** Replace with anonymized IDs when connecting to real data

### 2. Schema Fields That Could Hold PII (MEDIUM RISK)

**Location:** `mcp-server/src/scheduler_mcp/tools.py:35`

```python
class ValidationIssue(BaseModel):
    person_id: str | None = None
    person_name: str | None = None  # ← PII RISK
```

**Risk:** MEDIUM - Schema allows PII, even if not currently populated
**Action:** Remove `person_name` field from schema

### 3. Resources with Direct Name Access (HIGH RISK if DB connected)

**Location:** `mcp-server/src/scheduler_mcp/resources.py`

```python
# Line 29, 71
person_name: str  # Required field in schema

# Line 217
person_name=person.name,  # Direct DB field access

# Lines 442, 479
person_name=resident.name,  # Direct DB field access
```

**Risk:** HIGH if connected to database - would pull real names
**Action:** Remove `person_name` from schemas, use `person_id` only

### 4. PII Detection in Error Handling (GOOD)

**Location:** `mcp-server/src/scheduler_mcp/error_handling.py:969`

```python
# Shows awareness of PII fields
"ssn"  # Listed in sensitive fields
```

**Risk:** N/A - This is protective code
**Action:** Ensure this is used consistently

### 5. Sanitization Script Exists (GOOD)

**Location:** `scripts/sanitize_pii.py`

Comprehensive sanitization that:
- Replaces names with synthetic IDs (PGY1-01, FAC-PD)
- Offsets dates
- Removes: deployment_orders, tdy_location, ssn, dod_id, etc.

**Risk:** N/A - This is protective infrastructure
**Action:** Ensure MCP uses sanitized data path

---

## Current Data Flow (Unsafe)

```
┌─────────────────────────────────────────────────────────┐
│  CURRENT: Direct DB Access (NOT RECOMMENDED)            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Database                                               │
│     │                                                   │
│     ├── person.name = "John Smith" (REAL NAME)         │
│     ├── person.email = "jsmith@mil.gov" (REAL EMAIL)   │
│     └── absence.tdy_location = "CENTCOM" (OPSEC)       │
│                                                         │
│     ↓ Direct access                                     │
│                                                         │
│  MCP Tool                                               │
│     │                                                   │
│     └── Returns: person_name="John Smith" ← PII LEAK!  │
│                                                         │
│     ↓ Tool result                                       │
│                                                         │
│  Claude API (Anthropic servers)                         │
│     │                                                   │
│     └── Receives real PII ← UNACCEPTABLE               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Recommended Data Flow (Safe)

```
┌─────────────────────────────────────────────────────────┐
│  RECOMMENDED: FastAPI with Sanitization                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Database                                               │
│     │                                                   │
│     ├── person.name = "John Smith"                     │
│     ├── person.email = "jsmith@mil.gov"                │
│     └── absence.tdy_location = "CENTCOM"               │
│                                                         │
│     ↓ SQLAlchemy ORM                                    │
│                                                         │
│  FastAPI Backend                                        │
│     │                                                   │
│     ├── Service layer (business logic)                 │
│     ├── ACGME validation                               │
│     └── Response sanitization ← CRITICAL               │
│           │                                            │
│           └── Removes: name, email, location           │
│               Returns: person_id="RES-001"             │
│                                                         │
│     ↓ Sanitized HTTP response                          │
│                                                         │
│  MCP Tool                                               │
│     │                                                   │
│     └── Returns: person_id="RES-001" ← SAFE            │
│                                                         │
│     ↓ Tool result                                       │
│                                                         │
│  Claude API (Anthropic servers)                         │
│     │                                                   │
│     └── Receives only anonymized IDs ← ACCEPTABLE      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Required Changes

### Phase 1: Schema Sanitization (MCP Layer)

| File | Change | Priority |
|------|--------|----------|
| `tools.py:35` | Remove `person_name` from `ValidationIssue` | HIGH |
| `tools.py:252-341` | Remove mock `person_name` values | MEDIUM |
| `tools.py:850-1008` | Remove `candidate_name` from swap tools | HIGH |
| `resources.py:29,71` | Remove `person_name` from schemas | HIGH |
| `resources.py:217,442,479` | Remove `.name` access patterns | HIGH |

### Phase 2: API Layer Sanitization (Backend)

| Endpoint | Change | Priority |
|----------|--------|----------|
| `/api/v1/schedules/validate` | Return `person_id` only | HIGH |
| `/api/v1/conflicts` | Return `person_id` only | HIGH |
| `/api/v1/swaps/candidates` | Return `person_id` only | HIGH |

### Phase 3: Verification

| Test | Expected Result |
|------|-----------------|
| Grep for `person_name` in MCP | 0 occurrences |
| Grep for `\.name` in MCP | 0 direct DB accesses |
| API response audit | No PII in any response |

---

## GitHub Protection (Already in Place)

Per user confirmation, the following protections exist:

1. **Local sanitization** - `scripts/sanitize_pii.py` before push
2. **GitHub checks** - Would flag PII if committed
3. **Gitignore** - `.sanitize/`, `docs/data/*.json` excluded

**Conclusion:** GitHub repo is clean. Risk is in MCP → Claude API path.

---

## Compliance Checklist

- [ ] Remove `person_name` from all MCP schemas
- [ ] Remove mock names from tool responses
- [ ] Connect MCP to FastAPI (not direct DB)
- [ ] Add sanitization to FastAPI response layer
- [ ] Test: No PII in MCP tool responses
- [ ] Document: ID → name mapping stays local only

---

*Audit Completed: 2025-12-24*
*Auditor: Claude Code*
