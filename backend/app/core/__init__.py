# Core module

# Export TypedDict definitions for type safety
from app.core.types import (
    # Schedule and Metrics
    ScheduleMetrics,
    ComplianceResult,
    ValidationContext,
    ScheduleGenerationMetrics,
    ValidationResultDict,

    # Person and Assignment
    PersonInfo,
    AssignmentInfo,
    BlockInfo,
    SwapInfo,

    # Swap Management
    SwapDetails,

    # Coverage and Analytics
    CoverageReportItem,
    CoverageReport,
    WorkloadDistribution,
    AnalyticsReport,

    # Resilience and API
    ResilienceMetrics,
    ResilienceAnalysisResult,
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
    "ScheduleGenerationMetrics",
    "ValidationResultDict",

    # Person and Assignment
    "PersonInfo",
    "AssignmentInfo",
    "BlockInfo",
    "SwapInfo",

    # Swap Management
    "SwapDetails",

    # Coverage and Analytics
    "CoverageReportItem",
    "CoverageReport",
    "WorkloadDistribution",
    "AnalyticsReport",

    # Resilience and API
    "ResilienceMetrics",
    "ResilienceAnalysisResult",
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
