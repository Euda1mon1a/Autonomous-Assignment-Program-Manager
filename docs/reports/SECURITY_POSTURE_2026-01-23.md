# Security Posture Report

> **Generated:** 2026-01-23 | **Session:** 136
> **Scope:** Full codebase security audit
> **Methodology:** Follow-up on Scratchpad Distillate Section 4 findings

---

## Executive Summary

| Severity | Count | Status |
|----------|-------|--------|
| **Critical** | 1 | PII exposure in burnout/resilience tools |
| **High** | 4 | DoS vectors, missing rate limits |
| **Medium** | 3 | Log injection, inconsistent validation |
| **Low** | 0 | - |
| **False Positives** | 2 | Hardcoded credentials (not found), auth bypass (not found) |

**Overall Risk: MODERATE** - Strong auth foundation, but PII exposure and DoS vectors need immediate attention.

---

## Critical Findings (Fix Now)

### C-1: PII Exposure in Resilience/Burnout Tools

**HIPAA/OPSEC Violation - Military Medical Data**

| Location | Class | Exposed Field |
|----------|-------|---------------|
| `backend/app/resilience/contagion_model.py:107-130` | `SuperspreaderProfile` | `provider_name` |
| `mcp-server/src/scheduler_mcp/resilience_integration.py:114-124` | `VulnerabilityInfo` | `faculty_name` |
| `mcp-server/src/scheduler_mcp/resilience_integration.py:126-135` | `FatalPairInfo` | `faculty_1_name`, `faculty_2_name` |

**Attack Vector:** API responses expose real names alongside burnout scores and vulnerability status.

**Fix Pattern:** Use existing anonymization function at `resilience_integration.py:27-45`:
```python
def _anonymize_id(identifier: str | None, prefix: str = "Provider") -> str:
    if not identifier:
        return f"{prefix}-unknown"
    import hashlib
    hash_suffix = hashlib.sha256(identifier.encode()).hexdigest()[:6]
    return f"{prefix}-{hash_suffix}"
```

**Effort:** 30 minutes per class (3 classes = 1.5 hours total)

---

## High Severity Findings

### H-1: Unbounded Date Range Queries (DoS)

| Endpoint | File:Line | Issue |
|----------|-----------|-------|
| `GET /analytics/export/research` | `analytics.py:769-959` | No max range, scans full table |
| `GET /analytics/metrics/history` | `analytics.py:185-312` | No limit clause |
| `GET /analytics/fairness/trend` | `analytics.py:314-457` | Same pattern |

**Attack:** `?start_date=1900-01-01&end_date=2100-12-31` forces full table scan.

**Fix:**
```python
from datetime import timedelta
MAX_RANGE = timedelta(days=365)
if (end_date - start_date) > MAX_RANGE:
    raise HTTPException(400, "Date range exceeds 365 days")
```

### H-2: Unbounded Count Query

| Endpoint | File:Line | Issue |
|----------|-----------|-------|
| `GET /schedule/runs` | `schedule.py:1369` | `.all()` loads entire table for count |

**Current (Bad):**
```python
total_result = db.execute(select(ScheduleRun)).all()  # Fetches ALL rows
total = len(total_result)
```

**Fix:**
```python
total = db.query(func.count(ScheduleRun.id)).scalar()
```

### H-3: Missing Rate Limits on Expensive Endpoints

| Endpoint | Impact |
|----------|--------|
| `POST /schedule/generate` | CPU exhaustion (schedule generation is expensive) |
| `POST /import/analyze` | File processing exhaustion |
| `POST /import/analyze-file` | Same |
| `POST /exports/{job_id}/run` | Celery task queue exhaustion |

**Fix:** Add `@limiter.limit("2/minute")` decorator from `app.core.slowapi_limiter`.

### H-4: Unlimited File Uploads

| Endpoint | File | Issue |
|----------|------|-------|
| `POST /upload` | `upload.py` | No rate limit, no per-user quota |

**Note:** File validation (extension, MIME, magic bytes) IS implemented in `file_security.py` - good.
**Missing:** Rate limiting and storage quota.

---

## Medium Severity Findings

### M-1: Log Injection Risk

| Location | Issue |
|----------|-------|
| `rate_limit.py:400-401` | User-controlled `request.user_id` in log string |
| `rate_limit.py:439-440` | Same pattern |

**Attack:** `user_id="\n2025-01-23 FAKE_ALERT: System compromised\n"` pollutes audit logs.

**Fix:** Use structured logging:
```python
logger.info("rate_limit_updated", extra={
    "admin": current_user.username,
    "target_user_id": request.user_id  # Separate context field
})
```

### M-2: Inconsistent Date Parameter Types

| Endpoint | Type | Should Be |
|----------|------|-----------|
| `GET /validate` | `str` | `datetime` |
| Other endpoints | `datetime` | ✓ |

**Issue:** `/validate` uses `strptime()` parsing instead of FastAPI's native datetime type.

### M-3: Potential PII in Unified Index (Needs Verification)

| Location | Field | Status |
|----------|-------|--------|
| `composite_resilience_tools.py:102-126` | `faculty_name` | Labeled "(anonymized)" but needs runtime check |

---

## Verified Secure (False Positives from Distillate)

### FP-1: Hardcoded Credentials - NOT FOUND

The distillate mentioned `api_client.py:24-25` having hardcoded defaults. **Investigation found:**

```python
# Actual code (lines 30-31, 38-46):
username: str = ""  # REQUIRED via API_USERNAME env var
password: str = ""  # REQUIRED via API_PASSWORD env var

if not self.config.username or not self.config.password:
    raise ValueError("API_USERNAME and API_PASSWORD environment variables are required.")
```

**Status:** ✓ SECURE - App refuses to start without credentials.

### FP-2: Auth Implementation - EXCELLENT

| Component | Status |
|-----------|--------|
| SECRET_KEY generation | 64 chars, cryptographically secure |
| Weak password blocking | 44 known weak values rejected |
| Database password | Min 12 chars required in production |
| JWT tokens | HS256, rotation enabled, type validation |
| Login rate limiting | 5 attempts/60 seconds |
| Cookie security | httpOnly, secure, samesite |
| Impersonation audit | Full trail with original_admin_id |

---

## Remediation Plan

### Phase 1: Critical (Do Now - 2 hours)

| Task | File | Change |
|------|------|--------|
| Anonymize `SuperspreaderProfile.provider_name` | `contagion_model.py:530` | Use `_anonymize_id()` |
| Anonymize `VulnerabilityInfo.faculty_name` | `resilience_integration.py:114` | Same |
| Anonymize `FatalPairInfo.faculty_*_name` | `resilience_integration.py:126` | Same |

### Phase 2: High (This Week - 4 hours)

| Task | File | Change |
|------|------|--------|
| Add date range validation | `analytics.py` | Max 365 days |
| Fix count query | `schedule.py:1369` | Use `func.count()` |
| Add rate limits | `schedule.py`, `exports.py` | `@limiter.limit()` decorator |
| Add upload rate limit | `upload.py` | Same |

### Phase 3: Medium (Pre-Production - 2 hours)

| Task | File | Change |
|------|------|--------|
| Structured logging | `rate_limit.py` | Use `extra={}` dict |
| Standardize date params | `schedule.py:366` | Change `str` to `datetime` |
| Verify faculty_name anonymization | `composite_resilience_tools.py` | Runtime inspection |

---

## Test Verification

```bash
# After fixes, verify:

# 1. PII anonymization
curl /api/resilience/contingency-analysis | jq '.n1_vulnerabilities[].faculty_name'
# Should return: "Faculty-a1b2c3" (hashed), not real names

# 2. Date range validation
curl "/api/analytics/export/research?start_date=1900-01-01&end_date=2100-12-31"
# Should return: 400 "Date range exceeds 365 days"

# 3. Rate limiting
for i in {1..10}; do curl -X POST /api/schedule/generate; done
# Should return: 429 Too Many Requests after 2 attempts

# 4. Log injection
# Check logs for sanitized output, no newlines in log messages
```

---

## Cross-References

| Finding | Related Report | Priority |
|---------|----------------|----------|
| Resilience endpoints untested | API Coverage Matrix | P0 |
| 59 resilience endpoints | MCP Tools Audit | Same gap |
| Burnout tools placeholder | PLACEHOLDER_IMPLEMENTATIONS.md | Backend needed first |

---

## Summary

**Good News:**
- Auth system is rock-solid (no action needed)
- No hardcoded credentials
- File validation is comprehensive
- Login rate limiting works

**Action Required:**
- 3 PII exposures (CRITICAL - fix now)
- 4 DoS vectors (HIGH - fix this week)
- 3 minor issues (MEDIUM - pre-production)

**Estimated Total Effort:** 8 hours

---

*Security audit based on Scratchpad Distillate Section 4 + fresh codebase analysis.*
