"""
Structured logging modules.

Provides specialized loggers for:
- Performance monitoring
- Security events
- Compliance tracking
"""

from app.logging.compliance_logger import (
    ComplianceEvent,
    ComplianceEventType,
    ComplianceLogger,
    ComplianceSeverity,
    get_compliance_logger,
    log_acgme_override,
    log_acgme_violation,
    log_schedule_change,
    set_compliance_logger,
)
from app.logging.performance_logger import (
    PerformanceLogger,
    PerformanceMetric,
    PerformanceTimer,
    get_performance_logger,
    log_api_request,
    log_cache_access,
    log_database_query,
    set_performance_logger,
    time_async_function,
    time_function,
    time_operation,
)
from app.logging.security_logger import (
    SecurityEvent,
    SecurityEventType,
    SecurityLogger,
    SecuritySeverity,
    get_security_logger,
    log_auth_failure,
    log_auth_success,
    log_authz_failure,
    log_data_access,
    log_suspicious_activity,
    set_security_logger,
)

__all__ = [
    # Performance logging
    "PerformanceLogger",
    "PerformanceMetric",
    "PerformanceTimer",
    "get_performance_logger",
    "set_performance_logger",
    "time_operation",
    "time_function",
    "time_async_function",
    "log_api_request",
    "log_database_query",
    "log_cache_access",
    # Security logging
    "SecurityLogger",
    "SecurityEvent",
    "SecurityEventType",
    "SecuritySeverity",
    "get_security_logger",
    "set_security_logger",
    "log_auth_success",
    "log_auth_failure",
    "log_authz_failure",
    "log_data_access",
    "log_suspicious_activity",
    # Compliance logging
    "ComplianceLogger",
    "ComplianceEvent",
    "ComplianceEventType",
    "ComplianceSeverity",
    "get_compliance_logger",
    "set_compliance_logger",
    "log_acgme_violation",
    "log_acgme_override",
    "log_schedule_change",
]
