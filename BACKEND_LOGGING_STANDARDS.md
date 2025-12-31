***REMOVED*** Backend Logging Standards
***REMOVED******REMOVED*** SESSION 8 BURN: Structured Logging & PII Protection Requirements

**Generated:** 2025-12-31
**Based On:** SESSION_1_BACKEND/backend-logging-patterns.md
**Status:** IMPLEMENTATION GUIDE

---

***REMOVED******REMOVED*** Executive Summary

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

***REMOVED******REMOVED*** SECTION 1: LOGGING CONFIGURATION STANDARDS

***REMOVED******REMOVED******REMOVED*** Required Environment Variables

```bash
***REMOVED*** backend/.env

***REMOVED*** Log Configuration
LOG_LEVEL=INFO                    ***REMOVED*** DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                   ***REMOVED*** json (production) or text (development)
LOG_FILE=/var/log/app.log         ***REMOVED*** Optional file output (leave empty for stderr only)

***REMOVED*** Telemetry (Optional)
TELEMETRY_ENABLED=false           ***REMOVED*** Enable OpenTelemetry tracing
TELEMETRY_SERVICE_NAME=residency-scheduler
TELEMETRY_ENVIRONMENT=production
TELEMETRY_SAMPLING_RATE=0.1       ***REMOVED*** 10% sampling in production
TELEMETRY_EXPORTER_ENDPOINT=http://localhost:4317
```

***REMOVED******REMOVED******REMOVED*** Recommended Log Levels

| Environment | LOG_LEVEL | Rationale |
|-------------|-----------|-----------|
| Production | INFO | Reduces noise, captures important events |
| Staging | DEBUG | Detailed debugging while testing |
| Development | DEBUG | Maximum visibility for developers |

***REMOVED******REMOVED******REMOVED*** Log Rotation Configuration

```python
***REMOVED*** backend/app/core/logging.py

logger.add(
    log_file_path,
    rotation="100 MB",           ***REMOVED*** Rotate when file reaches 100 MB
    retention="7 days",          ***REMOVED*** Keep 7 days of logs
    compression="gz",            ***REMOVED*** Compress rotated files
    serialize=format_type == "json",  ***REMOVED*** JSON serialization in production
)
```

---

***REMOVED******REMOVED*** SECTION 2: STRUCTURED LOGGING PATTERNS

***REMOVED******REMOVED******REMOVED*** Pattern 1: Request Correlation

```python
***REMOVED*** All log entries include request_id automatically
from app.core.logging import set_request_id, get_request_id

@app.middleware("http")
async def correlation_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    set_request_id(request_id)

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

***REMOVED*** In service layer
from app.core.logging import get_logger
logger = get_logger(__name__)

def create_assignment(...):
    logger.info(
        "Creating assignment",
        person_id=person_id,          ***REMOVED*** Structured fields
        block_id=block_id,
        rotation_id=rotation_id,
        ***REMOVED*** request_id automatically included from context
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

***REMOVED******REMOVED******REMOVED*** Pattern 2: Error Logging with Context

```python
***REMOVED*** Always log exceptions with full context
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
        exc_info=True,  ***REMOVED*** Include stack trace
    )
    raise
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Audit Trail Logging

```python
***REMOVED*** For sensitive operations, log to audit trail
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

    ***REMOVED*** Also log to separate audit log if audit trail required
    audit_logger.info(
        "AUDIT: Assignment approved",
        user_id=current_user.id,
        action="APPROVE_ASSIGNMENT",
        resource_id=assignment.id,
        timestamp=datetime.utcnow().isoformat(),
    )
```

***REMOVED******REMOVED******REMOVED*** Pattern 4: Performance Monitoring

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
            duration = (time.time() - start) * 1000  ***REMOVED*** ms

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

***REMOVED*** Usage
@log_performance
async def generate_schedule(...):
    ...
```

---

***REMOVED******REMOVED*** SECTION 3: SENSITIVE DATA PROTECTION

***REMOVED******REMOVED******REMOVED*** PII That Must Be Redacted

```python
***REMOVED*** backend/app/core/logging/sanitizers.py

SENSITIVE_FIELDS = {
    ***REMOVED*** Authentication
    "password", "passwd", "pwd",
    "token", "access_token", "refresh_token",
    "api_key", "apikey", "api_secret",
    "secret", "credentials", "bearer",

    ***REMOVED*** Medical Records (PII)
    "ssn", "social_security_number",
    "passport", "driver_license",
    "mrn", "medical_record_number",

    ***REMOVED*** Personal Information
    "email", "phone", "phone_number", "mobile",
    "address", "zip_code", "date_of_birth",

    ***REMOVED*** Financial
    "credit_card", "card_number", "cvv", "cvn",
    "routing_number", "account_number",
}

***REMOVED*** Patterns that trigger automatic redaction
SENSITIVE_PATTERNS = [
    (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "[CARD]"),        ***REMOVED*** Credit cards
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN]"),                              ***REMOVED*** SSN
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}", "[EMAIL]"), ***REMOVED*** Email
    (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", "Bearer [TOKEN]"),            ***REMOVED*** Tokens
    (r"\b[a-f0-9]{32,}\b", "[KEY]"),                                  ***REMOVED*** API keys
]
```

***REMOVED******REMOVED******REMOVED*** Auto-Masking in Logs

```python
***REMOVED*** Automatic redaction applied to all logs
def log_request_body(...):
    ***REMOVED*** Request: {"username": "john", "password": "secret123"}
    ***REMOVED*** Logged as: {"username": "john", "password": "****"}
    logger.info("Request received", body=sanitize_dict(body))

def log_email_error(...):
    ***REMOVED*** Error: "Failed to send email to john@example.com"
    ***REMOVED*** Logged as: "Failed to send email to [EMAIL]"
    logger.error(sanitize_message(error_message))

***REMOVED*** Sanitization function
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

***REMOVED******REMOVED******REMOVED*** Sensitive Endpoints That Skip Body Logging

```python
***REMOVED*** backend/app/middleware/logging/request_logger.py

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

***REMOVED******REMOVED*** SECTION 4: STRUCTURED LOGGING FOR SERVICES

***REMOVED******REMOVED******REMOVED*** Service Logging Template

```python
***REMOVED*** backend/app/services/assignment_service.py

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
            ***REMOVED*** Check for duplicates
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

            ***REMOVED*** Create assignment
            assignment = self.assignment_repo.create({
                "block_id": block_id,
                "person_id": person_id,
                "rotation_template_id": rotation_template_id,
            })

            ***REMOVED*** Validate ACGME compliance
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

***REMOVED******REMOVED*** SECTION 5: OPENTELEMETRY INTEGRATION

***REMOVED******REMOVED******REMOVED*** Optional: Enable Distributed Tracing

```bash
***REMOVED*** backend/.env (when using OpenTelemetry)

TELEMETRY_ENABLED=true
TELEMETRY_EXPORTER_TYPE=otlp_grpc
TELEMETRY_EXPORTER_ENDPOINT=http://jaeger:4317
TELEMETRY_SAMPLING_RATE=0.1  ***REMOVED*** 10% sampling
TELEMETRY_TRACE_SQLALCHEMY=true
TELEMETRY_TRACE_REDIS=true
TELEMETRY_TRACE_HTTP=true
```

***REMOVED******REMOVED******REMOVED*** Span Attributes

```python
***REMOVED*** All spans include standard attributes
with tracer.start_as_current_span("create_assignment") as span:
    span.set_attribute("http.method", "POST")
    span.set_attribute("http.url", "/api/v1/assignments")
    span.set_attribute("http.status_code", 201)
    span.set_attribute("db.system", "postgresql")
    span.set_attribute("db.statement", "INSERT INTO assignments ...")
    span.set_attribute("duration_ms", elapsed_time)

    ***REMOVED*** Sensitive parameters masked automatically
    span.set_attribute("db.params", {"person_id": "...", "token": "***"})
```

***REMOVED******REMOVED******REMOVED*** Graceful Degradation

```python
***REMOVED*** If OpenTelemetry not installed, app continues with logging only
try:
    from opentelemetry import trace
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available - tracing disabled")
```

---

***REMOVED******REMOVED*** SECTION 6: LOGGING BEST PRACTICES

***REMOVED******REMOVED******REMOVED*** DO ✅

```python
***REMOVED*** Good: Structured fields
logger.info("User logged in", user_id=user.id, ip_address=request.client.host)

***REMOVED*** Good: Include context
logger.error("Database error", operation="insert_assignment", exc_info=True)

***REMOVED*** Good: Use appropriate level
logger.warning("Schedule freeze approaching", days_until_freeze=3)

***REMOVED*** Good: Mask sensitive data
logger.info("Password reset requested", email="[EMAIL]", reset_token="****")

***REMOVED*** Good: Performance metrics
logger.info("Query completed", query_type="list_assignments", duration_ms=234)
```

***REMOVED******REMOVED******REMOVED*** DON'T ❌

```python
***REMOVED*** Bad: Generic message, no context
logger.info("Error occurred")

***REMOVED*** Bad: Logging passwords
logger.info(f"Login attempt with password: {password}")

***REMOVED*** Bad: Unstructured data
logger.info("User: john, Email: john@example.com, SSN: 123-45-6789")

***REMOVED*** Bad: Missing error context
logger.error("Failed")

***REMOVED*** Bad: Logging entire request body without filtering
logger.info("Request received", body=request.json())
```

---

***REMOVED******REMOVED*** SECTION 7: LOG LEVEL USAGE

***REMOVED******REMOVED******REMOVED*** CRITICAL (0 expected per day)
Used for: System crashes, data loss risk, immediate action required

```python
logger.critical("Database connection lost, cache unavailable, accepting no requests")
```

***REMOVED******REMOVED******REMOVED*** ERROR (< 10 per day expected)
Used for: Recoverable errors affecting functionality

```python
logger.error("Failed to send email notification", recipient=email, exc_info=True)
```

***REMOVED******REMOVED******REMOVED*** WARNING (< 50 per day expected)
Used for: Potentially problematic situations

```python
logger.warning("Schedule nearing freeze horizon", days_remaining=2)
logger.warning("ACGME compliance warning", violation_type="approaching_80_hours")
```

***REMOVED******REMOVED******REMOVED*** INFO (< 500 per day expected)
Used for: Significant application events

```python
logger.info("Assignment created", assignment_id=id, person_id=person_id)
logger.info("User logged in", user_id=user_id)
```

***REMOVED******REMOVED******REMOVED*** DEBUG (Development only)
Used for: Detailed diagnostic information

```python
logger.debug("Query executed", query_type="select", duration_ms=45)
logger.debug("Validation passed", field="email", value="[EMAIL]")
```

---

***REMOVED******REMOVED*** SECTION 8: LOG AGGREGATION SETUP

***REMOVED******REMOVED******REMOVED*** For Development (Local)

```bash
***REMOVED*** View logs with colors
cd backend
tail -f logs/app.log

***REMOVED*** Search logs
grep "ERROR" logs/app.log

***REMOVED*** Count errors by type
grep "ERROR" logs/app.log | cut -d' ' -f3 | sort | uniq -c
```

***REMOVED******REMOVED******REMOVED*** For Production (Recommended Tools)

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 1: ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
***REMOVED*** logstash.conf
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

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 2: Datadog/CloudWatch (Cloud-native)

```python
***REMOVED*** Configure in .env
LOG_FORMAT=json  ***REMOVED*** Send JSON to cloud service
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Option 3: Splunk

```python
***REMOVED*** Configure Splunk HTTP Event Collector
SPLUNK_HEC_ENDPOINT=https://splunk.example.com:8088
SPLUNK_HEC_TOKEN=xxxxx
```

---

***REMOVED******REMOVED*** SECTION 9: COMPLIANCE & AUDIT LOGGING

***REMOVED******REMOVED******REMOVED*** Audit Log Requirements

For sensitive operations, use audit logger:

```python
***REMOVED*** backend/app/core/logging/audit_logger.py
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

***REMOVED*** Usage in controllers
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

***REMOVED******REMOVED******REMOVED*** HIPAA Compliance Notes

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

***REMOVED******REMOVED*** SECTION 10: LOGGING CHECKLIST

***REMOVED******REMOVED******REMOVED*** For Every Service Method
- [ ] Log entry with method name and input parameters (masked if needed)
- [ ] Log major decision points (found/not found, passed/failed validation)
- [ ] Log errors with full context (error code, details, stack trace)
- [ ] Log completion with result summary

***REMOVED******REMOVED******REMOVED*** For Every API Endpoint
- [ ] Log request (method, path, user_id)
- [ ] Log response (status_code, duration)
- [ ] Log errors with error_code
- [ ] Use appropriate HTTP status codes

***REMOVED******REMOVED******REMOVED*** For Every Database Operation
- [ ] Log query type and duration
- [ ] Log row count (for bulk operations)
- [ ] Log errors (constraint violations, timeouts)
- [ ] Mask sensitive parameters

***REMOVED******REMOVED******REMOVED*** For Every External Service Call
- [ ] Log service name and operation
- [ ] Log request/response (masked)
- [ ] Log timing and retry attempts
- [ ] Log errors with service-specific context

---

***REMOVED******REMOVED*** SECTION 11: MONITORING & ALERTING

***REMOVED******REMOVED******REMOVED*** Log-Based Alerts

Set up alerts for:

```python
***REMOVED*** Critical alerts (immediate)
- "CRITICAL" level logs → Page on-call
- "DatabaseConnectionError" → Page DBA
- "ACGME.*violation" count > 5 in 5min → Alert compliance officer

***REMOVED*** Warning alerts (next business day)
- "ERROR" level logs > 100/hour → Create ticket
- Schedule generation > 30 minutes → Investigate
- Rate limit hit > 50/hour → Review traffic
```

***REMOVED******REMOVED******REMOVED*** Key Metrics from Logs

Extract metrics for dashboards:

```python
***REMOVED*** From logs
- Request latency (p50, p95, p99)
- Error rate by endpoint
- ACGME violations per week
- Failed authentication attempts
- Schedule generation time distribution
```

---

***REMOVED******REMOVED*** SECTION 12: MIGRATION FROM OLD LOGGING

***REMOVED******REMOVED******REMOVED*** If currently using old logging style:

```python
***REMOVED*** Old style (deprecated)
import logging
logger = logging.getLogger(__name__)
logger.info(f"User {user_id} logged in")

***REMOVED*** New style (recommended)
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.info("User logged in", user_id=user_id)
```

***REMOVED******REMOVED******REMOVED*** Gradual migration strategy:

1. **Phase 1:** Add structured logging to new code only
2. **Phase 2:** Migrate one service at a time
3. **Phase 3:** Deprecate old logging
4. **Phase 4:** Remove old code

---

***REMOVED******REMOVED*** SECTION 13: REFERENCE CHECKLIST

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
