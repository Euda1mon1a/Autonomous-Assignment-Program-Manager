# Core module

# Export TypedDict definitions for type safety
from app.core.types import (
    # Schedule and Metrics
    ScheduleMetrics,
    ComplianceResult,
    ValidationContext,

    # Person and Assignment
    PersonInfo,
    AssignmentInfo,
    BlockInfo,
    SwapInfo,

    # Resilience and API
    ResilienceMetrics,
    APIResponse,

    # ACGME Duty Hours
    DutyHoursPeriod,
    DutyHoursDetails,
    DutyHoursDays,
    DutyHoursBreakdown,

    # Fatigue Tracking
    FatigueFactors,
    FatigueScore,
    RecoveryNeeds,
    FatiguePredictionDay,
    FatigueTrend,
    HighRiskResident,

    # Audit
    AuditStatistics,

    # Swap Matching
    SwapMatchResult,

    # ACGME Compliance
    ACGMEViolation,

    # Notifications
    NotificationPayload,
)

__all__ = [
    # Schedule and Metrics
    "ScheduleMetrics",
    "ComplianceResult",
    "ValidationContext",

    # Person and Assignment
    "PersonInfo",
    "AssignmentInfo",
    "BlockInfo",
    "SwapInfo",

    # Resilience and API
    "ResilienceMetrics",
    "APIResponse",

    # ACGME Duty Hours
    "DutyHoursPeriod",
    "DutyHoursDetails",
    "DutyHoursDays",
    "DutyHoursBreakdown",

    # Fatigue Tracking
    "FatigueFactors",
    "FatigueScore",
    "RecoveryNeeds",
    "FatiguePredictionDay",
    "FatigueTrend",
    "HighRiskResident",

    # Audit
    "AuditStatistics",

    # Swap Matching
    "SwapMatchResult",

    # ACGME Compliance
    "ACGMEViolation",

    # Notifications
    "NotificationPayload",
]
