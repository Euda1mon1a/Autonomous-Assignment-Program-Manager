"""
Audit Log Archival Package.

This package provides comprehensive audit log archival functionality including:
- Automated archival with configurable retention policies
- Multiple storage backends (local filesystem, S3)
- Compressed archive storage
- Archive restoration
- Search and compliance reporting
- Enhanced audit logging with field-level tracking
- Integrity verification with checksums

Main Components:
--------------
- archiver.py: Core archival service
- storage.py: Storage backend implementations
- retention.py: Retention policy management
- restore.py: Archive restoration service
- enhanced_logging.py: Enhanced audit logging with integrity verification

Usage:
-----
    from app.audit.archiver import AuditArchiver
    from app.audit.retention import RetentionPolicy
    from app.audit.enhanced_logging import EnhancedAuditLogger

    # Create archiver with default retention policy
    archiver = AuditArchiver(db)

    # Archive logs older than 90 days
    result = await archiver.archive_old_logs(days=90)

    # Restore from archive
    from app.audit.restore import AuditRestorer
    restorer = AuditRestorer(db)
    logs = await restorer.restore_from_archive(archive_id="archive-2025-01")

    # Enhanced audit logging
    logger = EnhancedAuditLogger(db)
    await logger.log_change(
        entity_type="assignment",
        entity_id="123",
        action="update",
        user_id="user-456",
        old_values={"status": "pending"},
        new_values={"status": "approved"},
    )

Background Tasks:
---------------
Scheduled archival tasks are available in app.tasks.audit_tasks:
- Daily archival at 2 AM (configurable retention)
- Weekly compliance report generation
- Monthly archive cleanup

Configuration:
------------
Environment variables:
- AUDIT_ARCHIVE_STORAGE: 'local' or 's3' (default: local)
- AUDIT_ARCHIVE_PATH: Local archive directory
- AUDIT_ARCHIVE_S3_BUCKET: S3 bucket for archives
- AUDIT_ARCHIVE_S3_REGION: S3 region
- AUDIT_RETENTION_DAYS: Default retention period (default: 90)
- AUDIT_ARCHIVE_RETENTION_YEARS: Archive retention in years (default: 7)
"""

from app.audit.archiver import ArchiveResult, AuditArchiver
from app.audit.enhanced_logging import (
    AuditContext,
    AuditSearchFilter,
    ComplianceReport,
    EnhancedAuditLog,
    EnhancedAuditLogger,
    FieldChangeDetail,
    create_audit_log,
    generate_report,
    search_audit_logs,
)
from app.audit.restore import AuditRestorer, RestoreResult
from app.audit.retention import RetentionLevel, RetentionPolicy
from app.audit.storage import (
    ArchiveStorageBackend,
    LocalArchiveStorage,
    S3ArchiveStorage,
    get_storage_backend,
)

__all__ = [
    # Archiver
    "AuditArchiver",
    "ArchiveResult",
    # Restore
    "AuditRestorer",
    "RestoreResult",
    # Retention
    "RetentionPolicy",
    "RetentionLevel",
    # Storage
    "ArchiveStorageBackend",
    "LocalArchiveStorage",
    "S3ArchiveStorage",
    "get_storage_backend",
    # Enhanced Logging
    "AuditContext",
    "AuditSearchFilter",
    "ComplianceReport",
    "EnhancedAuditLog",
    "EnhancedAuditLogger",
    "FieldChangeDetail",
    "create_audit_log",
    "generate_report",
    "search_audit_logs",
]
