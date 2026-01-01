"""Analytics schemas for schedule metrics and reporting.

Pydantic models for schedule analytics functionality, including metrics,
comparisons, trend analysis, and research data exports.
"""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================================
# Core Metric Schemas
# ============================================================================


class MetricValue(BaseModel):
    """Single metric value with metadata."""

    name: str = Field(..., min_length=1, max_length=100, description="Metric name")
    value: float = Field(..., description="Metric value")
    unit: str | None = Field(None, max_length=50, description="Unit of measurement")
    status: str = Field(
        ..., max_length=20, description="Status: good, warning, or critical"
    )
    trend: str | None = Field(
        None, max_length=20, description="Trend: up, down, or stable"
    )
    benchmark: float | None = Field(None, description="Benchmark value for comparison")
    description: str | None = Field(
        None, max_length=500, description="Metric description"
    )
    details: dict[str, Any] | None = Field(None, description="Additional details")


class ScheduleVersionMetrics(BaseModel):
    """Comprehensive metrics for a schedule version."""

    version_id: str = Field(alias="versionId")
    schedule_run_id: UUID | None = Field(None, alias="scheduleRunId")
    timestamp: str
    period: dict[str, str]  # start_date, end_date

    # Core metrics
    fairness_index: MetricValue = Field(alias="fairnessIndex")
    coverage_rate: MetricValue = Field(alias="coverageRate")
    acgme_compliance: MetricValue = Field(alias="acgmeCompliance")
    preference_satisfaction: MetricValue = Field(alias="preferenceSatisfaction")

    # Additional metrics
    total_blocks: int = Field(alias="totalBlocks")
    total_assignments: int = Field(alias="totalAssignments")
    unique_residents: int = Field(alias="uniqueResidents")

    # Violations summary
    violations: dict[str, int]

    # Workload distribution
    workload_distribution: dict[str, Any] = Field(alias="workloadDistribution")

    class Config:
        populate_by_name = True


# ============================================================================
# Time Series Schemas
# ============================================================================


class MetricDataPoint(BaseModel):
    """Single data point in a time series."""

    timestamp: str
    value: float
    metadata: dict[str, Any] | None = None


class MetricTimeSeries(BaseModel):
    """Time series data for a metric."""

    metric_name: str = Field(alias="metricName")
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    data_points: list[MetricDataPoint] = Field(alias="dataPoints")
    statistics: dict[str, float]  # mean, median, std_dev, min, max
    trend_direction: str = Field(
        alias="trendDirection"
    )  # "improving", "declining", "stable"

    class Config:
        populate_by_name = True


# ============================================================================
# Fairness Trend Schemas
# ============================================================================


class FairnessTrendDataPoint(BaseModel):
    """Fairness metric at a point in time."""

    date: str
    fairness_index: float = Field(alias="fairnessIndex")
    gini_coefficient: float = Field(alias="giniCoefficient")
    residents_count: int = Field(alias="residentsCount")

    class Config:
        populate_by_name = True


class FairnessTrendReport(BaseModel):
    """Fairness metrics trend over time."""

    period_months: int = Field(alias="periodMonths")
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")
    data_points: list[FairnessTrendDataPoint] = Field(alias="dataPoints")

    # Summary statistics
    average_fairness: float = Field(alias="averageFairness")
    trend: str  # "improving", "declining", "stable"
    most_unfair_period: str | None = Field(None, alias="mostUnfairPeriod")
    most_fair_period: str | None = Field(None, alias="mostFairPeriod")

    # Recommendations
    recommendations: list[str]

    class Config:
        populate_by_name = True


# ============================================================================
# Version Comparison Schemas
# ============================================================================


class VersionMetricComparison(BaseModel):
    """Comparison of a single metric between versions."""

    metric_name: str = Field(alias="metricName")
    version_a_value: float = Field(alias="versionAValue")
    version_b_value: float = Field(alias="versionBValue")
    difference: float
    percent_change: float = Field(alias="percentChange")
    improvement: bool  # True if version B is better

    class Config:
        populate_by_name = True


class VersionComparison(BaseModel):
    """Detailed comparison between two schedule versions."""

    version_a: str = Field(alias="versionA")
    version_b: str = Field(alias="versionB")
    timestamp: str

    # Metric comparisons
    metrics: list[VersionMetricComparison]

    # Overall assessment
    overall_improvement: bool = Field(alias="overallImprovement")
    improvement_score: float = Field(alias="improvementScore")  # 0-100

    # Detailed changes
    assignments_changed: int = Field(alias="assignmentsChanged")
    residents_affected: int = Field(alias="residentsAffected")

    # Recommendations
    summary: str = Field(..., max_length=1000, description="Summary of comparison")
    recommendations: list[str] = Field(
        ..., max_length=20, description="List of recommendations (max 20)"
    )

    class Config:
        populate_by_name = True


# ============================================================================
# What-If Analysis Schemas
# ============================================================================


class AssignmentChange(BaseModel):
    """Proposed change to an assignment."""

    assignment_id: UUID | None = Field(None, alias="assignmentId")
    person_id: UUID = Field(alias="personId")
    block_id: UUID = Field(alias="blockId")
    rotation_template_id: UUID | None = Field(None, alias="rotationTemplateId")
    change_type: str = Field(alias="changeType")  # "add", "remove", "modify"

    class Config:
        populate_by_name = True


class WhatIfMetricImpact(BaseModel):
    """Predicted impact on a metric."""

    metric_name: str = Field(alias="metricName")
    current_value: float = Field(alias="currentValue")
    predicted_value: float = Field(alias="predictedValue")
    change: float
    impact_severity: str = Field(
        alias="impactSeverity"
    )  # "positive", "negative", "neutral"
    confidence: float  # 0-1

    class Config:
        populate_by_name = True


class WhatIfViolation(BaseModel):
    """Potential violation from proposed changes."""

    type: str
    severity: str
    person_id: UUID | None = Field(None, alias="personId")
    person_name: str | None = Field(None, alias="personName")
    message: str

    class Config:
        populate_by_name = True


class WhatIfResult(BaseModel):
    """Results of what-if analysis."""

    timestamp: str
    changes_analyzed: int = Field(alias="changesAnalyzed")

    # Metric impacts
    metric_impacts: list[WhatIfMetricImpact] = Field(alias="metricImpacts")

    # Violations
    new_violations: list[WhatIfViolation] = Field(alias="newViolations")
    resolved_violations: list[str] = Field(alias="resolvedViolations")

    # Overall assessment
    overall_impact: str = Field(
        alias="overallImpact"
    )  # "positive", "negative", "mixed", "neutral"
    recommendation: str
    safe_to_apply: bool = Field(alias="safeToApply")

    # Detailed analysis
    affected_residents: list[str] = Field(alias="affectedResidents")
    workload_changes: dict[str, dict[str, float]] = Field(alias="workloadChanges")

    class Config:
        populate_by_name = True


# ============================================================================
# Research Export Schemas
# ============================================================================


class ResidentWorkloadData(BaseModel):
    """Anonymized resident workload data."""

    resident_id: str = Field(alias="residentId")  # Anonymized if requested
    pgy_level: int = Field(alias="pgyLevel")
    total_blocks: int = Field(alias="totalBlocks")
    target_blocks: int = Field(alias="targetBlocks")
    utilization_percent: float = Field(alias="utilizationPercent")
    clinical_blocks: int = Field(alias="clinicalBlocks")
    non_clinical_blocks: int = Field(alias="nonClinicalBlocks")
    max_consecutive_days: int = Field(alias="maxConsecutiveDays")
    average_rest_days: float = Field(alias="averageRestDays")

    class Config:
        populate_by_name = True


class RotationCoverageData(BaseModel):
    """Anonymized rotation coverage data."""

    rotation_id: str = Field(alias="rotationId")  # Anonymized if requested
    rotation_type: str = Field(alias="rotationType")
    activity_type: str = Field(alias="activityType")
    total_assignments: int = Field(alias="totalAssignments")
    unique_residents: int = Field(alias="uniqueResidents")
    average_duration: float = Field(alias="averageDuration")

    class Config:
        populate_by_name = True


class ComplianceData(BaseModel):
    """ACGME compliance statistics."""

    total_checks: int = Field(alias="totalChecks")
    total_violations: int = Field(alias="totalViolations")
    compliance_rate: float = Field(alias="complianceRate")
    violations_by_type: dict[str, int] = Field(alias="violationsByType")
    violations_by_severity: dict[str, int] = Field(alias="violationsBySeverity")
    override_count: int = Field(alias="overrideCount")

    class Config:
        populate_by_name = True


class ResearchDataExport(BaseModel):
    """Anonymized data export for research and publication."""

    export_id: str = Field(alias="exportId")
    timestamp: str
    anonymized: bool

    # Date range
    start_date: str = Field(alias="startDate")
    end_date: str = Field(alias="endDate")

    # Summary statistics
    total_residents: int = Field(alias="totalResidents")
    total_blocks: int = Field(alias="totalBlocks")
    total_assignments: int = Field(alias="totalAssignments")
    total_rotations: int = Field(alias="totalRotations")

    # Detailed data
    resident_workload: list[ResidentWorkloadData] = Field(alias="residentWorkload")
    rotation_coverage: list[RotationCoverageData] = Field(alias="rotationCoverage")
    compliance_data: ComplianceData = Field(alias="complianceData")

    # Aggregate metrics
    fairness_metrics: dict[str, float] = Field(alias="fairnessMetrics")
    coverage_metrics: dict[str, float] = Field(alias="coverageMetrics")

    # Metadata
    institution_type: str | None = Field(
        None, max_length=100, alias="institutionType", description="Type of institution"
    )
    program_size: str | None = Field(
        None, max_length=50, alias="programSize", description="Size of program"
    )
    speciality: str | None = Field(
        None, max_length=100, alias="speciality", description="Medical speciality"
    )

    # Export notes
    notes: str | None = Field(None, max_length=2000, description="Export notes")

    class Config:
        populate_by_name = True
