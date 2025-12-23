# Core module

# Export TypedDict definitions for type safety
from app.core.types import (
    # ACGME Compliance
    ACGMEViolation,
    AnalyticsReport,
    APIResponse,
    AssignmentInfo,
    # Audit
    AuditStatistics,
    BlockInfo,
    ComplianceResult,
    CoverageReport,
    # Coverage and Analytics
    CoverageReportItem,
    DutyHoursBreakdown,
    DutyHoursDays,
    DutyHoursDetails,
    # ACGME Duty Hours
    DutyHoursPeriod,
    # Fatigue Tracking
    FatigueFactors,
    FatiguePredictionDay,
    FatigueScore,
    FatigueTrend,
    HighRiskResident,
    # Notifications
    NotificationPayload,
    # Person and Assignment
    PersonInfo,
    RecoveryNeeds,
    ResilienceAnalysisResult,
    # Resilience and API
    ResilienceMetrics,
    ScheduleGenerationMetrics,
    # Schedule and Metrics
    ScheduleMetrics,
    # Swap Management
    SwapDetails,
    SwapInfo,
    # Swap Matching
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
