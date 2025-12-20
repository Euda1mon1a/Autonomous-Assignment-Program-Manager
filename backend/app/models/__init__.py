"""Database models."""
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.idempotency import IdempotencyRequest, IdempotencyStatus
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.certification import CertificationType, PersonCertification
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.email_log import EmailLog, EmailStatus
from app.models.email_template import EmailTemplate, EmailTemplateType
from app.models.faculty_preference import FacultyPreference
from app.models.notification import (
    Notification,
    NotificationPreferenceRecord,
    ScheduledNotificationRecord,
)
from app.models.person import Person
from app.models.procedure import Procedure
from app.models.procedure_credential import ProcedureCredential
from app.models.resilience import (
    AllostasisRecord,
    # Tier 2 models
    AllostasisState,
    CognitiveDecisionRecord,
    CognitiveSessionRecord,
    # Tier 3 models
    CognitiveState,
    CompensationRecord,
    ContainmentLevel,
    CrossTrainingPriority,
    CrossTrainingRecommendationRecord,
    DecisionCategory,
    DecisionComplexity,
    DecisionOutcome,
    EquilibriumShiftRecord,
    EquilibriumState,
    FacultyCentralityRecord,
    FallbackActivation,
    FeedbackLoopState,
    HubProtectionPlanRecord,
    HubRiskLevel,
    OverallStatus,
    PositiveFeedbackAlert,
    PreferenceTrailRecord,
    ResilienceEvent,
    ResilienceEventType,
    # Tier 1 models
    ResilienceHealthCheck,
    SacrificeDecision,
    SchedulingZoneRecord,
    SystemStressRecord,
    TrailSignalRecord,
    TrailType,
    VulnerabilityRecord,
    ZoneBorrowingRecord,
    ZoneFacultyAssignmentRecord,
    ZoneIncidentRecord,
    ZoneStatus,
)
from app.models.rotation_template import RotationTemplate
from app.models.schedule_run import ScheduleRun
from app.models.settings import ApplicationSettings
from app.models.swap import SwapApproval, SwapRecord, SwapStatus, SwapType
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.models.calendar_subscription import CalendarSubscription
from app.models.feature_flag import (
    FeatureFlag,
    FeatureFlagAudit,
    FeatureFlagEvaluation,
)
from app.models.scheduled_job import JobExecution, ScheduledJob
from app.models.export_job import (
    ExportJob,
    ExportJobExecution,
    ExportFormat,
    ExportDeliveryMethod,
    ExportJobStatus,
    ExportTemplate,
)
from app.webhooks.models import (
    Webhook,
    WebhookDeadLetter,
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEventType,
    WebhookStatus,
)

__all__ = [
    "Person",
    "Block",
    "RotationTemplate",
    "Assignment",
    "Absence",
    "CallAssignment",
    "ScheduleRun",
    "User",
    # Idempotency models
    "IdempotencyRequest",
    "IdempotencyStatus",
    # Credentialing models
    "Procedure",
    "ProcedureCredential",
    # Certification models
    "CertificationType",
    "PersonCertification",
    # Settings model
    "ApplicationSettings",
    # Notification models
    "Notification",
    "ScheduledNotificationRecord",
    "NotificationPreferenceRecord",
    # Email notification models
    "EmailLog",
    "EmailStatus",
    "EmailTemplate",
    "EmailTemplateType",
    # Token blacklist
    "TokenBlacklist",
    # FMIT Swap models
    "SwapRecord",
    "SwapApproval",
    "SwapStatus",
    "SwapType",
    # Conflict Alert models
    "ConflictAlert",
    "ConflictAlertStatus",
    "ConflictSeverity",
    "ConflictType",
    ***REMOVED*** Preference model
    "FacultyPreference",
    # Tier 1 Resilience models
    "ResilienceHealthCheck",
    "ResilienceEvent",
    "SacrificeDecision",
    "FallbackActivation",
    "VulnerabilityRecord",
    "ResilienceEventType",
    "OverallStatus",
    # Tier 2 Resilience models
    "AllostasisState",
    "ZoneStatus",
    "ContainmentLevel",
    "EquilibriumState",
    "FeedbackLoopState",
    "AllostasisRecord",
    "PositiveFeedbackAlert",
    "SchedulingZoneRecord",
    "ZoneFacultyAssignmentRecord",
    "ZoneBorrowingRecord",
    "ZoneIncidentRecord",
    "EquilibriumShiftRecord",
    "SystemStressRecord",
    "CompensationRecord",
    # Tier 3 Resilience models
    "CognitiveState",
    "DecisionComplexity",
    "DecisionCategory",
    "DecisionOutcome",
    "TrailType",
    "HubRiskLevel",
    "CrossTrainingPriority",
    "CognitiveSessionRecord",
    "CognitiveDecisionRecord",
    "PreferenceTrailRecord",
    "TrailSignalRecord",
    "FacultyCentralityRecord",
    "HubProtectionPlanRecord",
    "CrossTrainingRecommendationRecord",
    # Calendar Subscription model
    "CalendarSubscription",
    # Feature Flag models
    "FeatureFlag",
    "FeatureFlagEvaluation",
    "FeatureFlagAudit",
    # Scheduled Job models
    "ScheduledJob",
    "JobExecution",
    # Export Job models
    "ExportJob",
    "ExportJobExecution",
    "ExportFormat",
    "ExportDeliveryMethod",
    "ExportJobStatus",
    "ExportTemplate",
    # Webhook models
    "Webhook",
    "WebhookDelivery",
    "WebhookDeadLetter",
    "WebhookEventType",
    "WebhookStatus",
    "WebhookDeliveryStatus",
]
