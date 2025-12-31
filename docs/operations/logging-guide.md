***REMOVED*** Logging Guide

Comprehensive guide to logging in the Residency Scheduler application.

***REMOVED******REMOVED*** Overview

The application uses a multi-layered logging infrastructure with:
- **Structured Logging**: JSON and text formats using Loguru
- **Specialized Loggers**: Performance, security, and compliance logging
- **Context Tracking**: Request correlation and distributed tracing
- **Data Sanitization**: PII and sensitive data redaction

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Basic Logging

```python
from loguru import logger

***REMOVED*** Simple logging
logger.info("Processing schedule generation")
logger.warning("Low cache hit rate: {rate}%", rate=65)
logger.error("Failed to validate schedule", error=str(e))
```

***REMOVED******REMOVED******REMOVED*** Structured Logging with Context

```python
from app.core.logging.context import create_request_context, LogContextManager

***REMOVED*** Create context for request
context = create_request_context(
    user_id="user-123",
    session_id="session-456"
)

with LogContextManager(context):
    logger.info("Processing request")  ***REMOVED*** Will include user_id and session_id
```

***REMOVED******REMOVED******REMOVED*** Performance Logging

```python
from app.logging.performance_logger import time_operation, log_api_request

***REMOVED*** Time an operation
with time_operation("schedule_generation"):
    schedule = generate_schedule()

***REMOVED*** Log API request performance
log_api_request(
    method="POST",
    path="/api/v1/schedules",
    status_code=200,
    duration_ms=1234.56
)
```

***REMOVED******REMOVED******REMOVED*** Security Logging

```python
from app.logging.security_logger import log_auth_success, log_authz_failure

***REMOVED*** Log successful authentication
log_auth_success(
    user_id="user-123",
    username="johndoe",
    ip_address="192.168.1.100"
)

***REMOVED*** Log authorization failure
log_authz_failure(
    user_id="user-123",
    resource="schedules",
    action="delete",
    reason="insufficient_permissions"
)
```

***REMOVED******REMOVED******REMOVED*** Compliance Logging

```python
from app.logging.compliance_logger import log_acgme_violation, log_schedule_change

***REMOVED*** Log ACGME violation
log_acgme_violation(
    rule="80_hour",
    affected_person="resident-456",
    affected_person_role="RESIDENT",
    violation_details="Worked 85 hours in week",
    user_id="coordinator-789"
)

***REMOVED*** Log schedule change
log_schedule_change(
    affected_person="resident-456",
    change_type="assignment",
    old_value="Clinic AM",
    new_value="Call PM",
    user_id="coordinator-789",
    reason="Emergency coverage needed"
)
```

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** Environment Variables

```bash
***REMOVED*** Log level
LOG_LEVEL=INFO  ***REMOVED*** DEBUG, INFO, WARNING, ERROR, CRITICAL

***REMOVED*** Log format
LOG_FORMAT=json  ***REMOVED*** json, text, gelf, logfmt

***REMOVED*** Log file (optional)
LOG_FILE=/var/log/app/scheduler.log
LOG_MAX_FILE_SIZE=100  ***REMOVED*** MB
LOG_BACKUP_COUNT=7

***REMOVED*** Features
LOG_CORRELATION=true
LOG_PERFORMANCE=true
LOG_AUDIT=true
```

***REMOVED******REMOVED******REMOVED*** Programmatic Configuration

```python
from app.core.logging.config import LoggingConfig, set_logging_config, LogLevel, LogFormat

config = LoggingConfig(
    level=LogLevel.DEBUG,
    format=LogFormat.JSON,
    log_file="/var/log/app/scheduler.log",
    enable_backtrace=True,
    enable_diagnose=False,  ***REMOVED*** Disable in production
)

set_logging_config(config)
```

***REMOVED******REMOVED*** Log Formats

***REMOVED******REMOVED******REMOVED*** JSON Format (Production)

```json
{
  "timestamp": "2025-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "app.api.routes.schedules",
  "message": "Schedule generated successfully",
  "module": "schedules",
  "function": "generate_schedule",
  "line": 142,
  "request_id": "req-abc123",
  "user_id": "user-456",
  "duration_ms": 234.56
}
```

***REMOVED******REMOVED******REMOVED*** Text Format (Development)

```
2025-01-15 10:30:45.123 | INFO     | schedules:generate_schedule:142 | [req-abc1] Schedule generated successfully | duration_ms=234.56
```

***REMOVED******REMOVED******REMOVED*** GELF Format (Graylog)

```json
{
  "version": "1.1",
  "host": "scheduler-prod-01",
  "timestamp": 1642246245.123,
  "level": 6,
  "short_message": "Schedule generated successfully",
  "facility": "app",
  "_logger": "app.api.routes.schedules",
  "_request_id": "req-abc123",
  "_user_id": "user-456"
}
```

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Use Appropriate Log Levels

```python
***REMOVED*** DEBUG: Detailed diagnostic information
logger.debug("Calculated work hours: {hours}", hours=schedule.hours)

***REMOVED*** INFO: General informational messages
logger.info("Schedule generation completed for {count} residents", count=len(residents))

***REMOVED*** WARNING: Warning messages for potentially harmful situations
logger.warning("Cache miss rate high: {rate}%", rate=cache_miss_rate)

***REMOVED*** ERROR: Error events that might still allow the application to continue
logger.error("Failed to send notification", error=str(e))

***REMOVED*** CRITICAL: Critical events that cause application failure
logger.critical("Database connection lost", error=str(e))
```

***REMOVED******REMOVED******REMOVED*** 2. Include Context

```python
***REMOVED*** Good: Include context
logger.info(
    "Schedule generated",
    user_id=user.id,
    schedule_id=schedule.id,
    resident_count=len(residents),
    duration_ms=elapsed_ms
)

***REMOVED*** Bad: Missing context
logger.info("Schedule generated")
```

***REMOVED******REMOVED******REMOVED*** 3. Sanitize Sensitive Data

```python
from app.core.logging.sanitizers import sanitize

***REMOVED*** Sanitize before logging
user_data = {
    "email": "user@example.com",
    "password": "secret123"
}

logger.info("User data", data=sanitize(user_data))
***REMOVED*** Output: {"email": "[REDACTED-EMAIL]", "password": "[REDACTED]"}
```

***REMOVED******REMOVED******REMOVED*** 4. Use Structured Fields

```python
***REMOVED*** Good: Structured fields
logger.info(
    "API request completed",
    method="POST",
    path="/api/v1/schedules",
    status_code=200,
    duration_ms=123.45
)

***REMOVED*** Bad: String interpolation
logger.info(f"API POST /api/v1/schedules returned 200 in 123.45ms")
```

***REMOVED******REMOVED******REMOVED*** 5. Log Exceptions Properly

```python
try:
    result = risky_operation()
except Exception as e:
    ***REMOVED*** Log with exception context
    logger.exception("Operation failed")
    ***REMOVED*** Or manually record exception
    logger.error("Operation failed", exc_info=True)
```

***REMOVED******REMOVED*** Log Analysis

***REMOVED******REMOVED******REMOVED*** Using Log Parser

```bash
***REMOVED*** Parse and filter logs
python scripts/logs/log_parser.py app.log --level ERROR --module schedules

***REMOVED*** Analyze errors
python scripts/logs/log_parser.py app.log --errors

***REMOVED*** Export to CSV
python scripts/logs/log_parser.py app.log --export-csv errors.csv --fields timestamp,level,module,message
```

***REMOVED******REMOVED******REMOVED*** Using Error Aggregator

```bash
***REMOVED*** Aggregate errors
python scripts/logs/error_aggregator.py app.log --output error-report.json
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Logs Not Appearing

1. Check log level configuration
2. Verify logging is enabled
3. Check file permissions for log files
4. Review excluded paths in middleware

***REMOVED******REMOVED******REMOVED*** Performance Impact

- Use JSON format for high-volume production
- Disable diagnose mode in production
- Adjust log levels (INFO in prod, DEBUG in dev)
- Use async logging for high throughput

***REMOVED******REMOVED******REMOVED*** Sensitive Data Leakage

- Enable data sanitization
- Review custom sensitive field patterns
- Audit logs for PII before sharing
- Use `[REDACTED]` placeholders

***REMOVED******REMOVED*** Integration

***REMOVED******REMOVED******REMOVED*** With Monitoring Systems

```python
***REMOVED*** Export to Prometheus
from app.core.logging.handlers import create_webhook_handler

webhook_handler = create_webhook_handler(
    webhook_url="https://monitoring.example.com/logs",
    min_level="WARNING"
)
```

***REMOVED******REMOVED******REMOVED*** With Distributed Tracing

```python
from app.tracing import trace_function, add_span_attributes

@trace_function("schedule_generation")
def generate_schedule():
    add_span_attributes(user_id="123", operation="schedule")
    logger.info("Generating schedule")  ***REMOVED*** Will include trace context
```

***REMOVED******REMOVED*** See Also

- [Observability Setup Guide](observability-setup.md)
- [Alert Runbook](alert-runbook.md)
- [Security Logging Policy](../security/SECURITY_PATTERN_AUDIT.md)
