# Core module

# Export TypedDict definitions for type safety
from app.core.types import (  # ACGME Compliance; Audit; Coverage and Analytics; ACGME Duty Hours; Fatigue Tracking; Notifications; Person and Assignment; Resilience and API; Schedule and Metrics; Swap Management; Swap Matching
    ACGMEViolation,
    AnalyticsReport,
    APIResponse,
    AssignmentInfo,
    AuditStatistics,
    BlockInfo,
    ComplianceResult,
    CoverageReport,
    CoverageReportItem,
    DutyHoursBreakdown,
    DutyHoursDays,
    DutyHoursDetails,
    DutyHoursPeriod,
    FatigueFactors,
    FatiguePredictionDay,
    FatigueScore,
    FatigueTrend,
    HighRiskResident,
    NotificationPayload,
    PersonInfo,
    RecoveryNeeds,
    ResilienceAnalysisResult,
    ResilienceMetrics,
    ScheduleGenerationMetrics,
    ScheduleMetrics,
    SwapDetails,
    SwapInfo,
    SwapMatchResult,
    ValidationContext,
    ValidationResultDict,
    WorkloadDistribution,
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
