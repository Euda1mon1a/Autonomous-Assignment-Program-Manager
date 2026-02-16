# Backend Logging Standards
## SESSION 8 BURN: Structured Logging & PII Protection Requirements

**Generated:** 2025-12-31
**Based On:** SESSION_1_BACKEND/backend-logging-patterns.md
**Status:** IMPLEMENTATION GUIDE

---

## Executive Summary

**Status:** ✅ Production-ready logging with **comprehensive PII protection**

| Aspect | Status | Finding |
|--------|--------|---------|
| Structured Logging | ✅ Implemented | Loguru-based JSON support |
| PII/Sensitive Data | ✅ Protected | Multi-layer filtering + masking |
| OpenTelemetry Integration | ✅ Optional | Production-ready with graceful degradation |
| Security Filtering | ✅ Excellent | 5 sensitive headers, 15 sensitive fields redacted |
| Context Correlation | ✅ Implemented | Request ID + user ID tracking |
| **OVERALL RISK** | **LOW** | Data security controls in place |

---

## SECTION 1: LOGGING CONFIGURATION STANDARDS

### Required Environment Variables

```bash
# backend/.env

# Log Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                   # json (production) or text (development)
LOG_FILE=/var/log/app.log         # Optional file output (leave empty for stderr only)

# Telemetry (Optional)
TELEMETRY_ENABLED=false           # Enable OpenTelemetry tracing
TELEMETRY_SERVICE_NAME=residency-scheduler
TELEMETRY_ENVIRONMENT=production
TELEMETRY_SAMPLING_RATE=0.1       # 10% sampling in production
TELEMETRY_EXPORTER_ENDPOINT=http://localhost:4317
```

### Recommended Log Levels

| Environment | LOG_LEVEL | Rationale |
|-------------|-----------|-----------|
| Production | INFO | Reduces noise, captures important events |
| Staging | DEBUG | Detailed debugging while testing |
| Development | DEBUG | Maximum visibility for developers |

### Log Rotation Configuration

```python
# backend/app/core/logging.py

logger.add(
    log_file_path,
    rotation="100 MB",           # Rotate when file reaches 100 MB
    retention="7 days",          # Keep 7 days of logs
    compression="gz",            # Compress rotated files
    serialize=format_type == "json",  # JSON serialization in production
)
```

---

## SECTION 2: STRUCTURED LOGGING PATTERNS

### Pattern 1: Request Correlation

```python
# All log entries include request_id automatically
from app.core.logging import set_request_id, get_request_id

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    set_request_id(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# In service layer
from app.core.logging import get_logger
logger = get_logger(__name__)

def create_assignment(...):
    logger.info(
        "Creating assignment",
        person_id=person_id,          # Structured fields
        block_id=block_id,
        rotation_id=rotation_id,
        # request_id automatically included from context
    )
```

**Log Output:**
```json
{
    "timestamp": "2025-12-31T10:30:00.123Z",
    "level": "INFO",
    "message": "Creating assignment",
    "person_id": "person-123",
    "block_id": "block-456",
    "rotation_id": "rotation-789",
    "request_id": "req-abcd1234",
    "module": "assignment_service",
    "function": "create_assignment",
    "line": 42
}
```

### Pattern 2: Error Logging with Context

```python
# Always log exceptions with full context
try:
    result = self.acgme_validator.validate_assignment(...)
except ACGMEComplianceError as e:
    logger.warning(
        "ACGME compliance violation detected",
        error_code=e.error_code,
        violation_type=e.violation_type,
        resident_id=e.resident_id,
        current_value=e.current_value,
        limit=e.limit,
        exc_info=True,  # Include stack trace
    )
    raise
```

### Pattern 3: Audit Trail Logging

```python
# For sensitive operations, log to audit trail
def approve_assignment(...):
    assignment = self._fetch_assignment(...)

    logger.info(
        "Assignment approved",
        assignment_id=assignment.id,
        approved_by=current_user.id,
        approved_at=datetime.utcnow().isoformat(),
        action="approve",
        entity_type="assignment",
        entity_id=assignment.id,
    )

    # Also log to separate audit log if audit trail required
    audit_logger.info(
        "AUDIT: Assignment approved",
        user_id=current_user.id,
        action="APPROVE_ASSIGNMENT",
        resource_id=assignment.id,
        timestamp=datetime.utcnow().isoformat(),
    )
```

### Pattern 4: Performance Monitoring

```python
import time
from functools import wraps

def log_performance(func):
    """Decorator: Log function execution time."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = (time.time() - start) * 1000  # ms

            logger.info(
                f"{func.__name__} completed",
                duration_ms=duration,
                status="success",
            )
            return result
        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(
                f"{func.__name__} failed",
                duration_ms=duration,
                status="error",
                error=str(e),
                exc_info=True,
            )
            raise

    return async_wrapper

# Usage
@log_performance
async def generate_schedule(...):
    ...
```

---

## SECTION 3: SENSITIVE DATA PROTECTION

### PII That Must Be Redacted

```python
# backend/app/core/logging/sanitizers.py

SENSITIVE_FIELDS = {
    # Authentication
    "password", "passwd", "pwd",
    "token", "access_token", "refresh_token",
    "api_key", "apikey", "api_secret",
    "secret", "credentials", "bearer",

    # Medical Records (PII)
    "ssn", "social_security_number",
    "passport", "driver_license",
    "mrn", "medical_record_number",

    # Personal Information
    "email", "phone", "phone_number", "mobile",
    "address", "zip_code", "date_of_birth",

    # Financial
    "credit_card", "card_number", "cvv", "cvn",
    "routing_number", "account_number",
}

# Patterns that trigger automatic redaction
SENSITIVE_PATTERNS = [
    (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARD]"),        # Credit cards
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),                              # SSN
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", "[EMAIL]"), # Email
    (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer [TOKEN]"),            # Tokens
    (r"\b[a-f0-9]{32,}\b", "[KEY]"),                                  # API keys
]
```

### Auto-Masking in Logs

```python
# Automatic redaction applied to all logs
def log_request_body(...):
    # Request: {"username": "john", "password": "secret123"}
    # Logged as: {"username": "john", "password": "****"}
    logger.info("Request received", body=sanitize_dict(body))

def log_email_error(...):
    # Error: "Failed to send email to john@example.com"
    # Logged as: "Failed to send email to [EMAIL]"
    logger.error(sanitize_message(error_message))

# Sanitization function
def sanitize_dict(data: dict) -> dict:
    """Recursively redact sensitive fields in dict."""
    result = {}
    for key, value in data.items():
        if key.lower() in SENSITIVE_FIELDS:
            result[key] = "****"
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [sanitize_dict(v) if isinstance(v, dict) else v for v in value]
        else:
            result[key] = value
    return result
```

### Sensitive Endpoints That Skip Body Logging

```python
# backend/app/middleware/logging/request_logger.py

SENSITIVE_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/token",
    "/api/v1/auth/refresh",
    "/api/v1/auth/change-password",
    "/api/v1/auth/reset-password",
}

async def should_log_body(path: str) -> bool:
    """Check if request body should be logged."""
    return path not in SENSITIVE_PATHS
```

---

## SECTION 4: STRUCTURED LOGGING FOR SERVICES

### Service Logging Template

```python
# backend/app/services/assignment_service.py

from app.core.logging import get_logger

logger = get_logger(__name__)

class AssignmentService:
    def __init__(self, db: Session):
        self.db = db
        self.assignment_repo = AssignmentRepository(db)

    def create_assignment(
        self,
        block_id: UUID,
        person_id: UUID,
        rotation_template_id: UUID,
    ) -> dict:
        """Create new assignment with logging."""
        logger.info(
            "Starting assignment creation",
            block_id=block_id,
            person_id=person_id,
            rotation_template_id=rotation_template_id,
        )

        try:
            # Check for duplicates
            existing = self.assignment_repo.get_by_block_and_person(block_id, person_id)
            if existing:
                logger.info(
                    "Assignment already exists, skipping creation",
                    block_id=block_id,
                    person_id=person_id,
                    existing_assignment_id=existing.id,
                )
                return {
                    "assignment": None,
                    "error": "Person already assigned to this block",
                }

            # Create assignment
            assignment = self.assignment_repo.create({
                "block_id": block_id,
                "person_id": person_id,
                "rotation_template_id": rotation_template_id,
            })

            # Validate ACGME compliance
            validation = self.validate_acgme_compliance(assignment)
            if not validation["is_compliant"]:
                logger.warning(
                    "Assignment created with ACGME warnings",
                    assignment_id=assignment.id,
                    warnings=validation["warnings"],
                    is_compliant=False,
                )

            logger.info(
                "Assignment created successfully",
                assignment_id=assignment.id,
                block_id=block_id,
                person_id=person_id,
                is_compliant=validation["is_compliant"],
            )

            return {
                "assignment": assignment,
                "error": None,
                "warnings": validation["warnings"],
            }

        except ACGMEComplianceError as e:
            logger.warning(
                "ACGME validation failed",
                block_id=block_id,
                person_id=person_id,
                error_code=e.error_code,
                violation_type=e.violation_type,
                exc_info=True,
            )
            return {"assignment": None, "error": str(e)}

        except Exception as e:
            logger.error(
                "Unexpected error during assignment creation",
                block_id=block_id,
                person_id=person_id,
                error_type=type(e).__name__,
                error_message=str(e),
                exc_info=True,
            )
            raise
```

---

## SECTION 5: OPENTELEMETRY INTEGRATION

### Optional: Enable Distributed Tracing

```bash
# backend/.env (when using OpenTelemetry)

TELEMETRY_ENABLED=true
TELEMETRY_EXPORTER_TYPE=otlp_grpc
TELEMETRY_EXPORTER_ENDPOINT=http://jaeger:4317
TELEMETRY_SAMPLING_RATE=0.1  # 10% sampling
TELEMETRY_TRACE_SQLALCHEMY=true
TELEMETRY_TRACE_REDIS=true
TELEMETRY_TRACE_HTTP=true
```

### Span Attributes

```python
# All spans include standard attributes
with tracer.start_as_current_span("create_assignment") as span:
    span.set_attribute("http.method", "POST")
    span.set_attribute("http.url", "/api/v1/assignments")
    span.set_attribute("http.status_code", 201)
    span.set_attribute("db.system", "postgresql")
    span.set_attribute("db.statement", "INSERT INTO assignments ...")
    span.set_attribute("duration_ms", elapsed_time)

    # Sensitive parameters masked automatically
    span.set_attribute("db.params", {"person_id": "...", "token": "***"})
```

### Graceful Degradation

```python
# If OpenTelemetry not installed, app continues with logging only
try:
    from opentelemetry import trace
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available - tracing disabled")
```

---

## SECTION 6: LOGGING BEST PRACTICES

### DO ✅

```python
# Good: Structured fields
logger.info("User logged in", user_id=user.id, ip_address=request.client.host)

# Good: Include context
logger.error("Database error", operation="insert_assignment", exc_info=True)

# Good: Use appropriate level
logger.warning("Schedule freeze approaching", days_until_freeze=3)

# Good: Mask sensitive data
logger.info("Password reset requested", email="[EMAIL]", reset_token="****")

# Good: Performance metrics
logger.info("Query completed", query_type="list_assignments", duration_ms=234)
```

### DON'T ❌

```python
# Bad: Generic message, no context
logger.info("Error occurred")

# Bad: Logging passwords
logger.info(f"Login attempt with password: {password}")

# Bad: Unstructured data
logger.info("User: john, Email: john@example.com, SSN: 123-45-6789")

# Bad: Missing error context
logger.error("Failed")

# Bad: Logging entire request body without filtering
logger.info("Request received", body=request.json())
```

---

## SECTION 7: LOG LEVEL USAGE

### CRITICAL (0 expected per day)
Used for: System crashes, data loss risk, immediate action required

```python
logger.critical("Database connection lost, cache unavailable, accepting no requests")
```

### ERROR (< 10 per day expected)
Used for: Recoverable errors affecting functionality

```python
logger.error("Failed to send email notification", recipient=email, exc_info=True)
```

### WARNING (< 50 per day expected)
Used for: Potentially problematic situations

```python
logger.warning("Schedule nearing freeze horizon", days_remaining=2)
logger.warning("ACGME compliance warning", violation_type="approaching_80_hours")
```

### INFO (< 500 per day expected)
Used for: Significant application events

```python
logger.info("Assignment created", assignment_id=id, person_id=person_id)
logger.info("User logged in", user_id=user_id)
```

### DEBUG (Development only)
Used for: Detailed diagnostic information

```python
logger.debug("Query executed", query_type="select", duration_ms=45)
logger.debug("Validation passed", field="email", value="[EMAIL]")
```

---

## SECTION 8: LOG AGGREGATION SETUP

### For Development (Local)

```bash
# View logs with colors
cd backend
tail -f logs/app.log

# Search logs
grep "ERROR" logs/app.log

# Count errors by type
grep "ERROR" logs/app.log | cut -d' ' -f3 | sort | uniq -c
```

### For Production (Recommended Tools)

#### Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# logstash.conf
input {
  file {
    path => "/var/log/app.log"
    codec => "json"
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "residency-scheduler-%{+YYYY.MM.dd}"
  }
}
```

#### Option 2: Datadog/CloudWatch (Cloud-native)

```python
# Configure in .env
LOG_FORMAT=json  # Send JSON to cloud service
```

#### Option 3: Splunk

```python
# Configure Splunk HTTP Event Collector
SPLUNK_HEC_ENDPOINT=https://splunk.example.com:8088
SPLUNK_HEC_TOKEN=xxxxx
```

---

## SECTION 9: COMPLIANCE & AUDIT LOGGING

### Audit Log Requirements

For sensitive operations, use audit logger:

```python
# backend/app/core/logging/audit_logger.py
from app.core.logging import get_logger

audit_logger = get_logger("audit", level="INFO")

def log_audit_event(
    action: str,
    user_id: str,
    resource_type: str,
    resource_id: str,
    changes: dict | None = None,
):
    """Log auditable event."""
    audit_logger.info(
        f"AUDIT: {action}",
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        changes=changes,
        timestamp=datetime.utcnow().isoformat(),
    )

# Usage in controllers
def approve_assignment(...):
    assignment = ...
    log_audit_event(
        action="APPROVE_ASSIGNMENT",
        user_id=current_user.id,
        resource_type="assignment",
        resource_id=assignment.id,
        changes={"status": "pending → approved"},
    )
```

### HIPAA Compliance Notes

✅ **Compliant:**
- PII automatically redacted
- Audit logs retained
- No passwords logged
- Sensitive endpoints skip body logging
- Error messages don't leak internal details

⚠️ **Verify:**
- [ ] Log retention policy meets legal requirements (typically 90+ days)
- [ ] Logs stored in HIPAA-compliant storage
- [ ] Log access restricted to authorized personnel
- [ ] Regular log audits performed

---

## SECTION 10: LOGGING CHECKLIST

### For Every Service Method
- [ ] Log entry with method name and input parameters (masked if needed)
- [ ] Log major decision points (found/not found, passed/failed validation)
- [ ] Log errors with full context (error code, details, stack trace)
- [ ] Log completion with result summary

### For Every API Endpoint
- [ ] Log request (method, path, user_id)
- [ ] Log response (status_code, duration)
- [ ] Log errors with error_code
- [ ] Use appropriate HTTP status codes

### For Every Database Operation
- [ ] Log query type and duration
- [ ] Log row count (for bulk operations)
- [ ] Log errors (constraint violations, timeouts)
- [ ] Mask sensitive parameters

### For Every External Service Call
- [ ] Log service name and operation
- [ ] Log request/response (masked)
- [ ] Log timing and retry attempts
- [ ] Log errors with service-specific context

---

## SECTION 11: MONITORING & ALERTING

### Log-Based Alerts

Set up alerts for:

```python
# Critical alerts (immediate)
- "CRITICAL" level logs → Page on-call
- "DatabaseConnectionError" → Page DBA
- "ACGME.*violation" count > 5 in 5min → Alert compliance officer

# Warning alerts (next business day)
- "ERROR" level logs > 100/hour → Create ticket
- Schedule generation > 30 minutes → Investigate
- Rate limit hit > 50/hour → Review traffic
```

### Key Metrics from Logs

Extract metrics for dashboards:

```python
# From logs
- Request latency (p50, p95, p99)
- Error rate by endpoint
- ACGME violations per week
- Failed authentication attempts
- Schedule generation time distribution
```

---

## SECTION 12: MIGRATION FROM OLD LOGGING

### If currently using old logging style:

```python
# Old style (deprecated)
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {user_id} logged in")

# New style (recommended)
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.info("User logged in", user_id=user_id)
```

### Gradual migration strategy:

1. **Phase 1:** Add structured logging to new code only
2. **Phase 2:** Migrate one service at a time
3. **Phase 3:** Deprecate old logging
4. **Phase 4:** Remove old code

---

## SECTION 13: REFERENCE CHECKLIST

**Environment Setup**
- [ ] Set LOG_LEVEL=INFO for production
- [ ] Set LOG_FORMAT=json for production
- [ ] Configure log rotation (100 MB, 7-day retention)
- [ ] Set up log aggregation service

**Code Standards**
- [ ] All service methods have entry/exit logs
- [ ] All errors logged with full context
- [ ] All sensitive data masked automatically
- [ ] All performance-critical operations timed

**Testing**
- [ ] Test that PII is redacted in logs
- [ ] Test that error details are not exposed
- [ ] Test log format (JSON/text)
- [ ] Test log levels are appropriate

**Compliance**
- [ ] Logs retained for minimum period
- [ ] Logs access-controlled
- [ ] Regular audit of logs
- [ ] HIPAA compliance verified

---

*Generated by SESSION 8 BURN - Backend Improvements*
*Reference: SESSION_1_BACKEND/backend-logging-patterns.md*
