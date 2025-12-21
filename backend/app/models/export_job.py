"""Export job models for scheduled data exports."""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY

from app.db.base import Base
from app.db.types import GUID, JSONType


class ExportFormat(str, Enum):
    """Export file formats."""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    XML = "xml"


class ExportDeliveryMethod(str, Enum):
    """Export delivery methods."""
    EMAIL = "email"
    S3 = "s3"
    BOTH = "both"


class ExportJobStatus(str, Enum):
    """Export job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportTemplate(str, Enum):
    """Predefined export templates."""
    FULL_SCHEDULE = "full_schedule"
    PERSONNEL = "personnel"
    ABSENCES = "absences"
    CERTIFICATIONS = "certifications"
    ACGME_COMPLIANCE = "acgme_compliance"
    SWAP_HISTORY = "swap_history"
    CUSTOM = "custom"


class ExportJob(Base):
    """
    Scheduled export job model.

    Attributes:
        id: Unique job identifier
        name: Human-readable job name
        description: Job description
        template: Export template to use
        format: Export file format (csv, json, xlsx, xml)
        delivery_method: How to deliver the export (email, s3, both)
        email_recipients: List of email addresses for delivery
        s3_bucket: S3 bucket name (if using S3 delivery)
        s3_key_prefix: S3 key prefix for files
        schedule_cron: Cron expression for scheduling (e.g., "0 8 * * 1")
        schedule_enabled: Whether scheduled execution is enabled
        filters: JSON filters to apply to export data
        columns: Specific columns to include (null = all)
        last_run_at: When the job was last executed
        next_run_at: When the job will next execute
        run_count: Number of times executed
        enabled: Whether the job is active
        created_at: Job creation timestamp
        updated_at: Job update timestamp
        created_by: User who created the job
    """

    __tablename__ = "export_jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    template = Column(String(50), nullable=False, default=ExportTemplate.CUSTOM.value)
    format = Column(String(20), nullable=False, default=ExportFormat.CSV.value)
    delivery_method = Column(String(20), nullable=False, default=ExportDeliveryMethod.EMAIL.value)

    # Email delivery settings
    email_recipients = Column(ARRAY(String), nullable=True)
    email_subject_template = Column(String(500), nullable=True)
    email_body_template = Column(Text, nullable=True)

    # S3 delivery settings
    s3_bucket = Column(String(255), nullable=True)
    s3_key_prefix = Column(String(500), nullable=True)
    s3_region = Column(String(50), nullable=True, default="us-east-1")

    # Scheduling
    schedule_cron = Column(String(100), nullable=True)
    schedule_enabled = Column(Boolean, default=False, index=True)

    # Export configuration
    filters = Column(JSONType, nullable=True, default=dict)
    columns = Column(ARRAY(String), nullable=True)
    include_headers = Column(Boolean, default=True)

    # Execution tracking
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    run_count = Column(Integer, default=0)

    # Status
    enabled = Column(Boolean, default=True, index=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<ExportJob(name='{self.name}', template='{self.template}', enabled={self.enabled})>"


class ExportJobExecution(Base):
    """
    Export job execution history.

    Tracks each execution of export jobs for auditing and debugging.

    Attributes:
        id: Unique execution identifier
        job_id: Reference to the export job
        job_name: Name of the job (denormalized)
        started_at: Execution start time
        finished_at: Execution finish time
        status: Execution status
        row_count: Number of rows exported
        file_size_bytes: Size of generated file
        file_path: Path to generated file (if stored locally)
        s3_url: S3 URL (if delivered to S3)
        email_sent: Whether email was sent successfully
        error_message: Error message if failed
        error_traceback: Full traceback if failed
        runtime_seconds: Execution duration
        scheduled_run_time: Originally scheduled time
        triggered_by: Who/what triggered the execution
    """

    __tablename__ = "export_job_executions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), nullable=False, index=True)
    job_name = Column(String(255), nullable=False, index=True)

    # Execution timing
    started_at = Column(DateTime, nullable=False, index=True)
    finished_at = Column(DateTime, nullable=True)
    runtime_seconds = Column(Integer, nullable=True)
    scheduled_run_time = Column(DateTime, nullable=True)

    # Status and results
    status = Column(String(50), nullable=False, index=True, default=ExportJobStatus.PENDING.value)
    row_count = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)

    # Delivery tracking
    file_path = Column(String(1000), nullable=True)
    s3_url = Column(String(1000), nullable=True)
    email_sent = Column(Boolean, default=False)
    email_recipients = Column(ARRAY(String), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)

    # Metadata
    triggered_by = Column(String(255), nullable=True)  # 'scheduled', 'manual', or username
    execution_metadata = Column(JSONType, nullable=True, default=dict)

    def __repr__(self):
        return f"<ExportJobExecution(job_name='{self.job_name}', status='{self.status}', started_at='{self.started_at}')>"
