# Security Error Handling Audit Report
## G2_RECON SEARCH_PARTY Analysis

**Date:** 2025-12-30
**Target:** Error handling security in Residency Scheduler
**Scope:** Error response formatting, information disclosure, logging, and debug vs. production modes

---

## Executive Summary

The error handling system demonstrates **strong security posture** with comprehensive protections against information disclosure. The application implements RFC 7807 Problem Details formatting, context-aware error responses, and DEBUG-mode gating for sensitive information. However, **4 medium-severity findings** require attention.

**Risk Level:** MEDIUM (mostly mitigated by existing controls)

---

## 1. PERCEPTION: Current Error Response Architecture

### Error Handling Stack
The application implements a **3-layer error handling system**:

1. **Global Exception Handlers** (`backend/app/main.py:254-284`)
   - AppException: Custom exceptions with safe messages
   - Generic Exception: Catches all unhandled exceptions
   - DEBUG-aware response: Different payloads for dev vs. production

2. **Error Handler Middleware** (`backend/app/middleware/errors/handler.py`)
   - RFC 7807 Problem Details formatting
   - Error fingerprinting and rate limiting
   - Configurable stack trace inclusion
   - Error reporting integration

3. **Structured Logging** (`backend/app/core/logging.py`)
   - Loguru-based JSON output for production
   - Human-readable colored output for development
   - Request ID correlation
   - Exception context inclusion

### Current Flow
```
Exception Raised
    ↓
Global Handler (main.py)
    ↓
ErrorHandlerMiddleware (errors/handler.py)
    ↓
ErrorFormatter (errors/formatters.py)
    ↓
RFC 7807 Response or Simple JSON
```

---

## 2. INVESTIGATION: Error Information Flow Analysis

### Stack Trace Handling
**FINDING: Good - Stack traces properly gated**

- `backend/app/middleware/errors/handler.py:120` - Stack trace only included when `settings.DEBUG=true`
- `backend/app/core/logging.py:196` - Production logging uses `diagnose=False` (doesn't include variable values)
- `backend/app/main.py:274-284` - DEBUG conditional response formatting

**Evidence:**
```python
# Line 120 in handler.py
include_stack_trace = settings.DEBUG

# Lines 274-284 in main.py
if settings.DEBUG:
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "type": type(exc).__name__}
    )
else:
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )
```

### Exception Message Exposure
**FINDING: Good - Custom exceptions use safe messages**

All custom exceptions inherit from `AppException` (`backend/app/core/exceptions.py:8`):
- NotFoundError, ValidationError, ConflictError, etc.
- All have `message` attribute intended for safe exposure
- Used in global handler: `{"detail": exc.message}`

**Evidence:**
```python
# exceptions.py
class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message  # Safe to expose
        self.status_code = status_code
```

### Headers Sanitization
**FINDING: Good - Sensitive headers redacted**

- `backend/app/middleware/errors/context.py:82-98` implements header sanitization
- Redacts: authorization, cookie, x-api-key, x-auth-token, proxy-authorization
- Used in error context collection for logging

**Evidence:**
```python
sensitive_headers = {
    "authorization", "cookie", "x-api-key",
    "x-auth-token", "proxy-authorization"
}
sanitized[key] = "[REDACTED]"
```

### Pydantic Validation Error Handling
**FINDING: Good - Input values sanitized in validation errors**

- `backend/app/middleware/errors/formatters.py:206-238` formats validation errors
- Sanitizes sensitive field values (lines 228-234)
- Excludes values for fields containing: password, secret, token, key

**Evidence:**
```python
field_name = formatted_error["field"].lower()
if not any(
    sensitive in field_name
    for sensitive in ["password", "secret", "token", "key"]
):
    formatted_error["input"] = str(error["input"])[:100]
```

---

## 3. ARCANA: Information Disclosure Risk Assessment

### FINDING 1: DEBUG Mode Exception Details in Responses
**Severity:** MEDIUM
**Status:** Known and Documented
**File:** `backend/app/main.py:277`

In DEBUG mode, the global exception handler returns:
```json
{
  "detail": "str(exc)",
  "type": "type(exc).__name__"
}
```

This exposes:
- Exception message (may contain implementation details)
- Exception type name (reveals internal class hierarchy)

**Risk:** If DEBUG is accidentally left true in staging/production, sensitive details leak.

**Recommendations:**
1. Add startup validation: ENFORCE `DEBUG=false` in production
2. Current: `_validate_security_config()` only checks secrets
3. Suggested addition:
   ```python
   if not settings.DEBUG and os.getenv("ENVIRONMENT") == "production":
       raise ValueError("DEBUG must be False in production")
   ```

**Current Status:** Documented in CLAUDE.md as acceptable for development only.

---

### FINDING 2: Exception str() Conversion in Telemetry
**Severity:** MEDIUM
**Status:** Partially Mitigated
**Files:**
- `backend/app/telemetry/middleware.py` - Sets error message as span attribute
- `backend/app/telemetry/decorators.py` - Same pattern in decorator spans

**Code:**
```python
span.set_status(Status(StatusCode.ERROR, str(exc)))
span.set_attribute("error.message", str(exc))
```

**Risk:** Telemetry spans are exported to external services (Jaeger, Zipkin). Raw exception strings may contain sensitive information depending on exception type.

**Example Vulnerabilities:**
- Database exceptions: `"Integrity constraint violation: unique constraint 'user_email_idx' violated with value 'secret@example.com'"`
- Business logic exceptions: `"Cannot swap shifts for PGY3-001 due to deployment at location X"`

**Recommendations:**
1. Sanitize exception messages before adding to spans
2. Use custom exception attributes instead of str(exc)
3. Filter based on exception type hierarchy (AppException vs. generic)

**Current Status:** Not yet implemented. Low likelihood in production since DEBUG=false filters most.

---

### FINDING 3: str(exc) in Database/Outbox Tasks
**Severity:** LOW-MEDIUM
**Status:** Partially Logged
**Files:**
- `backend/app/outbox/tasks.py` - Stores exception in task record
- `backend/app/queue/tasks.py` - Logs error as string

**Code:**
```python
# outbox/tasks.py
"exception": str(exc)

# queue/tasks.py
error=str(exc)
```

**Risk:** Exception details stored in database/log records where they may be:
- Exposed via admin interfaces
- Included in database backups
- Visible in monitoring/alerting systems

**Recommendations:**
1. Use custom exception handling for task failures
2. Store exception type + fingerprint instead of message
3. Log detailed message only in structured logs (already santized by loguru)

**Current Status:** Partially mitigated by loguru sanitization, but direct str(exc) bypasses sanitizers.

---

### FINDING 4: Over-Generic Error Messages May Hide Real Issues
**Severity:** LOW
**Status:** Design Choice - Trade-off Accepted
**File:** `backend/app/main.py:283`

Production response:
```python
{"detail": "An internal error occurred. Please try again later."}
```

**Risk:** Operations team loses visibility into actual failures. Error fingerprinting helps, but may not be sufficient for on-call debugging.

**Current Mitigations:**
- Error fingerprinting: `backend/app/middleware/errors/context.py:ErrorFingerprinter`
- Request ID correlation for log lookups
- Structured logging with full context server-side
- Error reporting to LoggingReporter

**Recommendations:**
1. Return error_id in production response for correlation:
   ```json
   {
     "detail": "An internal error occurred. Please try again later.",
     "error_id": "550e8400-e29b-41d4-a716-446655440000"
   }
   ```
2. This is already generated in ErrorFormatter - should expose to client

**Current Status:** Already partially implemented (error_id is generated). Consider exposing to client in production.

---

## 4. HISTORY: Error Handling Evolution

### Version Timeline
1. **Legacy Handler** (main.py:327-346) - Backward compatibility wrapper
   - Delegates to new ErrorHandlerMiddleware
   - Maintains old behavior while allowing migration

2. **New Middleware** (errors/handler.py) - Introduced recently
   - RFC 7807 Problem Details
   - Error fingerprinting
   - Rate limiting
   - Reporter integration

3. **Structured Logging** (core/logging.py) - Comprehensive setup
   - Loguru integration
   - JSON output for production
   - Request ID context

### No Breaking Changes
Old and new systems coexist:
- `install_error_handlers()` provides backward-compatible setup
- Both middleware and exception handlers work together
- Gradual migration path for existing code

---

## 5. INSIGHT: Debug vs. Production Mode Behavior

### Conditional Behavior Matrix

| Aspect | Debug Mode | Production Mode |
|--------|-----------|-----------------|
| **Stack Traces** | Included in response | Excluded |
| **Exception Details** | Full message + type | Generic message |
| **Log Verbosity** | Colorized, detailed | JSON, structured |
| **Log Level** | DEBUG (verbose) | INFO (normal) |
| **Diagnose Flag** | True (variable values) | False (no values) |
| **Documentation** | Enabled (/docs, /redoc) | Disabled |
| **Cookie Secure** | False (http ok) | True (https required) |

### Enforcement Mechanisms

1. **at-startup validation** (`main.py:37-88`)
   - Warns if DEBUG=true in development
   - Fails fast if secrets are weak

2. **runtime conditionals**
   - ErrorHandlerMiddleware checks `settings.DEBUG` at line 120
   - Main.py checks at line 274
   - Logging setup checks at line 196

3. **environment variable validation**
   - `backend/app/core/config.py` (not shown, but referenced)
   - Should validate DEBUG is false in production

**Risk:** DEBUG mode controlled by environment variable, not configuration management.

---

## 6. RELIGION: Stack Trace Compliance Check

### CLAUDE.md Requirement
From project guidelines:
> **No stack traces in responses per CLAUDE.md**

### Implementation Status: COMPLIANT

Checking `backend/app/middleware/errors/handler.py`:
```python
# Line 120 - Only in DEBUG mode
include_stack_trace = settings.DEBUG

# Line 179-180 - Only added if flag is true
if include_stack_trace:
    problem.stack_trace = self._format_stack_trace(exc)
```

### Verification
- Stack traces only included when `include_stack_trace=True`
- This flag is set to `settings.DEBUG` (line 120)
- In production (DEBUG=false), stack traces excluded from response
- Line 182: `return problem.model_dump(exclude_none=True)` excludes None fields

**Status:** COMPLIANT - Stack traces not included in production responses

---

## 7. NATURE: Generic vs. Specific Error Messages

### Classification

**Good: Appropriately Generic**
- `main.py:283` - "An internal error occurred. Please try again later."
- `error_codes.py:193` - "An internal error occurred" (fallback)
- Database constraint violations: "Resource Conflict" (doesn't leak schema)

**Good: Appropriately Specific**
- Application exceptions: "Person not found" (safe to expose)
- Validation errors: Field name + validation rule (user-facing)
- ACGME violations: "80-hour work week limit was violated" (business logic)

**Needs Review: Route-Level Messages**
From `backend/app/api/routes/academic_blocks.py`:
- "Invalid request parameters" - good, generic
- "An error occurred generating the block matrix" - acceptable
- Similar pattern throughout routes

**Assessment:** Balance is appropriate for healthcare context.

---

## 8. MEDICINE: Error Logging Completeness

### Logging Coverage

**Implemented:**
1. **Access Logging** - uvicorn.access (suppressed at WARNING level)
2. **Application Errors** - loguru with structured JSON
3. **Exception Details** - Full traceback logged server-side
4. **Request Context** - Method, path, query params, user ID
5. **Correlation IDs** - X-Request-ID support (core/observability.py)
6. **Performance** - Telemetry spans with error attributes
7. **Rate Limiting** - Error reporting rate limits (errors/context.py)

**Not Found:**
1. **Audit Trail for Sensitive Operations** - May exist elsewhere (audit/ module)
2. **Error Aggregation Metrics** - Fingerprinting done, but no dashboard
3. **PII Detection in Logs** - Patterns defined in sanitizers.py but not actively used

### Structured Logging Quality
From `core/logging.py:79-121`:
```json
{
  "timestamp": "2025-12-30T10:30:00.000000Z",
  "level": "ERROR",
  "message": "Unhandled exception",
  "module": "app.api.routes.schedule",
  "function": "create_schedule",
  "line": 42,
  "request_id": "550e8400...",
  "exception": {
    "type": "ValueError",
    "value": "Invalid input",
    "traceback": true
  }
}
```

**Quality:** Excellent - includes context, request correlation, exception details

---

## 9. SURVIVAL: Error Recovery Procedures

### Recovery Mechanisms

1. **Circuit Breaker** (`health/checks/circuit_breaker.py`)
   - Prevents cascade failures
   - Monitored in /health endpoint
   - Integrated with resilience framework

2. **Rate Limiting on Error Reporting** (`middleware/errors/context.py`)
   - Prevents error reporting storms
   - Uses fingerprinting to group similar errors
   - Configurable thresholds

3. **Rollback Capability** (`rollback/manager.py`)
   - Not directly error handling but complements it
   - Allows recovery from invalid state

4. **Transaction Handling** (implicit via SQLAlchemy async)
   - Errors trigger rollbacks
   - Consistency maintained

### Database Error Handling
From `middleware/errors/mappings.py:108-131`:
```python
# IntegrityError → 409 Conflict (don't leak schema)
# DataError → 422 Validation Error (don't leak format)
# OperationalError → 503 Service Unavailable (safe)
# DatabaseError → 500 Internal Server Error
```

All with `include_details=False` to prevent schema information leakage.

---

## 10. STEALTH: Verbose Errors in Logs

### Analysis

**Potentially Verbose Locations:**

1. **Telemetry Middleware** (`telemetry/middleware.py`)
   - Exports `str(exc)` to span attributes
   - Exported to external tracing services
   - Risk: Zipkin/Jaeger may expose details in UI

2. **Outbox Task Storage** (`outbox/tasks.py`)
   - Stores full exception string
   - May be visible in admin interface
   - Risk: Readable by non-technical staff

3. **Task Queue** (`queue/tasks.py`)
   - Logs error as string
   - Risk: Visible in monitoring systems

4. **Correlation Middleware** (`correlation/middleware.py`)
   - Includes `str(exc)` in correlation tracking
   - Risk: May be indexed by observability tools

### Log Sanitization Status

**Active Sanitizers:**
- `backend/app/core/logging/sanitizers.py` - Defines patterns for PII
- EMAIL_PATTERN, PHONE_PATTERN, SSN_PATTERN, CREDIT_CARD_PATTERN, IP_ADDRESS_PATTERN
- SENSITIVE_FIELDS list (passwords, tokens, etc.)

**Usage Status:** PATTERNS DEFINED BUT NOT ACTIVELY USED
- No automatic sanitization in logging pipeline
- Patterns available for custom use
- Recommendation: Integrate into loguru serializer

---

## Summary of Findings

### Security Posture
| Category | Status | Risk | Priority |
|----------|--------|------|----------|
| Stack Traces in Responses | COMPLIANT | None | - |
| Debug/Prod Differentiation | STRONG | Low | Medium |
| Sensitive Header Sanitization | GOOD | Low | Low |
| Exception Message Exposure | GOOD | Medium | Medium |
| Validation Error Handling | GOOD | Low | Low |
| Telemetry Data Exposure | MEDIUM | Medium | Medium |
| Task Queue Error Storage | MEDIUM | Low-Medium | Low |
| Logging Completeness | EXCELLENT | None | - |

---

## Recommendations (Priority Order)

### HIGH PRIORITY

1. **Expose error_id to Production Responses**
   - Currently generated but not exposed
   - Needed for client-side error correlation
   - File: `backend/app/main.py` (global_exception_handler)
   - Add: Include error_id from ErrorFormatter in response

2. **Enforce DEBUG=False in Production**
   - Add startup validation
   - File: `backend/app/main.py` (_validate_security_config)
   - Check: `if not settings.DEBUG and ENVIRONMENT=="production"`

### MEDIUM PRIORITY

3. **Sanitize Telemetry Span Attributes**
   - Create sanitized exception message
   - File: `backend/app/telemetry/middleware.py` and decorators.py
   - Use: Custom exception attribute (exc.safe_message) instead of str(exc)

4. **Integrate PII Sanitizers into Logging Pipeline**
   - Currently defined but not used
   - File: `backend/app/core/logging/sanitizers.py`
   - Hook into loguru's filter or serializer

5. **Sanitize Task Exception Storage**
   - Don't store full str(exc)
   - File: `backend/app/outbox/tasks.py`, `backend/app/queue/tasks.py`
   - Store: Exception type + fingerprint instead

### LOW PRIORITY

6. **Add Error Aggregation Dashboard**
   - Use error fingerprints for grouping
   - File: New API endpoint or admin interface
   - Benefits: Visibility into top errors

7. **Audit Log Error Handling**
   - Ensure sensitive operations log errors to audit trail
   - File: `backend/app/audit/` module
   - Check: Audit trail captures errors in critical paths

---

## Appendix: Files Analyzed

### Core Error Handling
- `backend/app/main.py` - Global exception handlers
- `backend/app/core/exceptions.py` - Custom exception hierarchy
- `backend/app/core/error_codes.py` - Structured error codes

### Middleware
- `backend/app/middleware/errors/handler.py` - RFC 7807 formatting
- `backend/app/middleware/errors/formatters.py` - Error response formatting
- `backend/app/middleware/errors/mappings.py` - Exception to HTTP mapping
- `backend/app/middleware/errors/context.py` - Error context collection
- `backend/app/middleware/errors/reporters.py` - Error reporting

### Logging
- `backend/app/core/logging.py` - Structured logging configuration
- `backend/app/core/logging/sanitizers.py` - PII sanitization patterns

### Telemetry
- `backend/app/telemetry/middleware.py` - Traces errors to spans
- `backend/app/telemetry/decorators.py` - Decorator-based error tracing

### Related Systems
- `backend/app/middleware/errors/reporters.py` - Error reporting integration
- `backend/app/health/checks/circuit_breaker.py` - Failure handling
- `backend/app/api/routes/academic_blocks.py` - Example route error handling

---

## Conclusion

The error handling system implements **strong security controls** with RFC 7807 compliance, DEBUG-mode gating, and comprehensive logging. Most findings are **low to medium severity** and relate to edge cases or missing enhancements rather than fundamental flaws.

**Recommended Action:**
1. Address HIGH priority findings immediately (error_id exposure, DEBUG enforcement)
2. Schedule MEDIUM findings for next sprint
3. Document LOW priority items for future improvement

The system follows CLAUDE.md requirements and provides good protection against information disclosure in production.
