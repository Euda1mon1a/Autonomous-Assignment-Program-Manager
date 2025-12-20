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
    ***REMOVED*** Tier 2 models
    AllostasisState,
    CognitiveDecisionRecord,
    CognitiveSessionRecord,
    ***REMOVED*** Tier 3 models
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
    ***REMOVED*** Tier 1 models
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

__all__ = [
    "Person",
    "Block",
    "RotationTemplate",
    "Assignment",
    "Absence",
    "CallAssignment",
    "ScheduleRun",
    "User",
    ***REMOVED*** Idempotency models
    "IdempotencyRequest",
    "IdempotencyStatus",
    ***REMOVED*** Credentialing models
    "Procedure",
    "ProcedureCredential",
    ***REMOVED*** Certification models
    "CertificationType",
    "PersonCertification",
    ***REMOVED*** Settings model
    "ApplicationSettings",
    ***REMOVED*** Notification models
    "Notification",
    "ScheduledNotificationRecord",
    "NotificationPreferenceRecord",
    ***REMOVED*** Email notification models
    "EmailLog",
    "EmailStatus",
    "EmailTemplate",
    "EmailTemplateType",
    ***REMOVED*** Token blacklist
    "TokenBlacklist",
    ***REMOVED*** FMIT Swap models
    "SwapRecord",
    "SwapApproval",
    "SwapStatus",
    "SwapType",
    ***REMOVED*** Conflict Alert models
    "ConflictAlert",
    "ConflictAlertStatus",
    "ConflictSeverity",
    "ConflictType",
    ***REMOVED*** Preference model
    "FacultyPreference",
    ***REMOVED*** Tier 1 Resilience models
    "ResilienceHealthCheck",
    "ResilienceEvent",
    "SacrificeDecision",
    "FallbackActivation",
    "VulnerabilityRecord",
    "ResilienceEventType",
    "OverallStatus",
    ***REMOVED*** Tier 2 Resilience models
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
    ***REMOVED*** Tier 3 Resilience models
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
    ***REMOVED*** Calendar Subscription model
    "CalendarSubscription",
    ***REMOVED*** Feature Flag models
    "FeatureFlag",
    "FeatureFlagEvaluation",
    "FeatureFlagAudit",
]
