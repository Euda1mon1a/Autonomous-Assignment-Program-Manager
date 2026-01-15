"""Database models."""

from app.models.absence import Absence
from app.models.activity import Activity, ActivityCategory
from app.models.activity_log import ActivityActionType, ActivityLog
from app.models.approval_record import ApprovalAction, ApprovalRecord
from app.models.agent_memory import AgentEmbedding, ModelTier, TaskHistory
from app.models.assignment import Assignment
from app.models.block_assignment import AssignmentReason, BlockAssignment
from app.models.rag_document import RAGDocument
from app.models.block import Block
from app.models.calendar_subscription import CalendarSubscription
from app.models.call_assignment import CallAssignment
from app.models.certification import CertificationType, PersonCertification
from app.models.clinic_session import (
    ClinicSession,
    ClinicType,
    SessionType,
    StaffingStatus,
)
from app.models.conflict_alert import (
    ConflictAlert,
    ConflictAlertStatus,
    ConflictSeverity,
    ConflictType,
)
from app.models.email_log import EmailLog, EmailStatus
from app.models.email_template import EmailTemplate, EmailTemplateType
from app.models.export_job import (
    ExportDeliveryMethod,
    ExportFormat,
    ExportJob,
    ExportJobExecution,
    ExportJobStatus,
    ExportTemplate,
)
from app.models.faculty_preference import FacultyPreference
from app.models.faculty_weekly_template import FacultyWeeklyTemplate
from app.models.faculty_weekly_override import FacultyWeeklyOverride
from app.models.feature_flag import (
    FeatureFlag,
    FeatureFlagAudit,
    FeatureFlagEvaluation,
)
from app.models.gateway_auth import (
    APIKey,
    IPBlacklist,
    IPWhitelist,
    OAuth2Client,
    RequestSignature,
)
from app.models.half_day_assignment import (
    AssignmentSource,
    HalfDayAssignment,
)
from app.models.inpatient_preload import (
    InpatientPreload,
    InpatientRotationType,
    PreloadAssignedBy,
)
from app.models.resident_call_preload import (
    ResidentCallPreload,
    ResidentCallType,
)
from app.models.idempotency import IdempotencyRequest, IdempotencyStatus
from app.models.import_staging import (
    ConflictResolutionMode,
    ImportBatch,
    ImportBatchStatus,
    ImportStagedAssignment,
    StagedAssignmentStatus,
)
from app.models.intern_stagger import InternStaggerPattern
from app.models.notification import (
    Notification,
    NotificationPreferenceRecord,
    ScheduledNotificationRecord,
)
from app.models.oauth2_authorization_code import OAuth2AuthorizationCode
from app.models.oauth2_client import PKCEClient
from app.models.person import Person, ScreenerRole
from app.models.procedure import Procedure
from app.models.procedure_credential import ProcedureCredential
from app.models.resilience import (  # Tier 2 models; Tier 3 models; Tier 1 models
    AllostasisRecord,
    AllostasisState,
    CognitiveDecisionRecord,
    CognitiveSessionRecord,
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
from app.models.rotation_enums import (
    ActivityType,
    PreferenceWeight,
    RotationPatternType,
    RotationSettingType,
    TimeOfDay,
)
from app.models.resident_weekly_requirement import ResidentWeeklyRequirement
from app.models.rotation_activity_requirement import RotationActivityRequirement
from app.models.rotation_halfday_requirement import RotationHalfDayRequirement
from app.models.rotation_preference import PREFERENCE_DEFAULTS, RotationPreference
from app.models.rotation_template import RotationTemplate
from app.models.weekly_pattern import WeeklyPattern
from app.models.schedule_run import ScheduleRun
from app.models.scheduled_job import JobExecution, ScheduledJob
from app.models.schema_version import (
    SchemaChangeEvent,
    SchemaCompatibilityType,
    SchemaStatus,
    SchemaVersion,
)
from app.models.settings import ApplicationSettings
from app.models.state_machine import (
    StateMachineInstance,
    StateMachineStatus,
    StateMachineTransition,
)
from app.models.swap import SwapApproval, SwapRecord, SwapStatus, SwapType
from app.models.token_blacklist import TokenBlacklist
from app.models.user import User
from app.webhooks.models import (
    Webhook,
    WebhookDeadLetter,
    WebhookDelivery,
    WebhookDeliveryStatus,
    WebhookEventType,
    WebhookStatus,
)

__all__ = [
    # Activity models (slot-level)
    "Activity",
    "ActivityCategory",
    # Activity Log models
    "ActivityLog",
    "ActivityActionType",
    # Approval Chain models
    "ApprovalRecord",
    "ApprovalAction",
    "Person",
    "ScreenerRole",
    "Block",
    "BlockAssignment",
    "AssignmentReason",
    "RotationTemplate",
    "RotationHalfDayRequirement",
    "RotationActivityRequirement",
    "ResidentWeeklyRequirement",
    "WeeklyPattern",
    "RotationPreference",
    "PREFERENCE_DEFAULTS",
    # Rotation enums
    "RotationPatternType",
    "RotationSettingType",
    "PreferenceWeight",
    "ActivityType",
    "TimeOfDay",
    "Assignment",
    "Absence",
    "CallAssignment",
    "ScheduleRun",
    "User",
    # Agent Memory models
    "ModelTier",
    "AgentEmbedding",
    "TaskHistory",
    # RAG document model
    "RAGDocument",
    # Idempotency models
    "IdempotencyRequest",
    "IdempotencyStatus",
    # Import staging models
    "ImportBatch",
    "ImportBatchStatus",
    "ImportStagedAssignment",
    "StagedAssignmentStatus",
    "ConflictResolutionMode",
    # Credentialing models
    "Procedure",
    "ProcedureCredential",
    # Certification models
    "CertificationType",
    "PersonCertification",
    # Clinic Session models
    "ClinicSession",
    "SessionType",
    "ClinicType",
    "StaffingStatus",
    # Intern Stagger model
    "InternStaggerPattern",
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
    # Faculty Preference model
    "FacultyPreference",
    # Faculty Weekly Activity models
    "FacultyWeeklyTemplate",
    "FacultyWeeklyOverride",
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
    # Gateway Auth models
    "APIKey",
    "OAuth2Client",
    "IPWhitelist",
    "IPBlacklist",
    "RequestSignature",
    # Half-Day Assignment models (TAMC scheduling)
    "HalfDayAssignment",
    "AssignmentSource",
    "InpatientPreload",
    "InpatientRotationType",
    "PreloadAssignedBy",
    "ResidentCallPreload",
    "ResidentCallType",
    # PKCE Auth models
    "PKCEClient",
    "OAuth2AuthorizationCode",
    # Schema Version models
    "SchemaVersion",
    "SchemaChangeEvent",
    "SchemaCompatibilityType",
    "SchemaStatus",
    # State Machine models
    "StateMachineInstance",
    "StateMachineTransition",
    "StateMachineStatus",
]
