"""Type definitions for analytics module using TypedDict."""

from typing import TypedDict


class MetricDetails(TypedDict, total=False):
    """Details for a metric."""

    min_assignments: int
    max_assignments: int
    mean_assignments: float
    std_dev: float
    total_blocks: int
    covered_blocks: int
    uncovered_blocks: int
    total_checks: int
    violations: int
    compliance_checks_passed: int
    total_preferences: int
    assignments_with_preferences: int
    preferences_matched: int
    total_assignments: int
    unique_duty_dates: int
    rest_periods: int


class MetricResult(TypedDict):
    """Result of a metric calculation."""

    value: float
    trend: str
    benchmark: float
    status: str
    description: str
    details: MetricDetails


class PeriodInfo(TypedDict):
    """Information about a reporting period."""

    start_date: str
    end_date: str
    total_days: int


class SummaryInfo(TypedDict, total=False):
    """Summary information for analysis."""

    total_blocks: int
    total_assignments: int
    unique_people: int
    schedule_runs: int
    unique_residents: int
    acgme_violations: int
    total_residents: int
    fairness_index: float
    over_utilized_count: int
    under_utilized_count: int
    total_violations: int
    acknowledged_overrides: int
    unacknowledged_violations: int
    compliance_rate: float
    total_schedule_runs: int
    successful_runs: int


class MetricsInfo(TypedDict):
    """Metrics information for analysis."""

    fairness: MetricResult
    coverage: MetricResult
    compliance: MetricResult


class ViolationsInfo(TypedDict):
    """Violations information."""

    total: int
    overrides_acknowledged: int
    unacknowledged: int


class ResidentWorkload(TypedDict):
    """Workload data for a single resident."""

    person_id: str
    name: str
    pgy_level: int | None
    assignments: int
    target: int
    utilization_percent: float
    variance: int
    target_blocks: int
    actual_blocks: int


class WorkloadStatistics(TypedDict):
    """Statistics for workload distribution."""

    total_residents: int
    average_assignments: float
    std_deviation: float
    min_assignments: int
    max_assignments: int


class WorkloadDistribution(TypedDict):
    """Workload distribution data."""

    residents: list[ResidentWorkload]
    statistics: WorkloadStatistics


class RotationCoverage(TypedDict):
    """Coverage data for a rotation."""

    rotation_id: str
    name: str
    rotation_type: str
    total_assignments: int


class RotationCoverageStats(TypedDict):
    """Rotation coverage statistics."""

    rotations: list[RotationCoverage]
    by_rotation_type: dict[str, int]
    total_rotations: int


class TrendDataPoint(TypedDict):
    """A single data point in a trend analysis."""

    date: str
    run_id: str
    status: str
    value: float


class TrendAnalysis(TypedDict):
    """Trend analysis data."""

    metric: str
    period: str
    data_points: list[TrendDataPoint]
    total_runs: int


class ScheduleRunInfo(TypedDict):
    """Information about a schedule run."""

    id: str
    date_range: str
    status: str
    violations: int
    blocks_assigned: int
    runtime_seconds: float


class ScheduleComparison(TypedDict):
    """Comparison between two schedules."""

    run_1: ScheduleRunInfo
    run_2: ScheduleRunInfo
    differences: dict[str, int | float]


class AnalysisResult(TypedDict):
    """Result of comprehensive schedule analysis."""

    period: PeriodInfo
    summary: SummaryInfo
    metrics: MetricsInfo
    workload: WorkloadDistribution
    violations: ViolationsInfo
    generated_at: str


class ConsecutiveDutyStats(TypedDict):
    """Statistics for consecutive duty patterns."""

    person_id: str
    max_consecutive_days: int
    total_duty_days: int
    average_rest_days: float
    status: str
    description: str
    details: MetricDetails


class ChartDataItem(TypedDict, total=False):
    """Generic chart data item."""

    name: str
    count: int
    rotation: str
    blocks: int
    date: str
    coverage_percent: float
    utilization: float
    pgy_level: int
    resident_count: int
    average_blocks: float
    run_id: str
    violations: int


class MonthlyReportPeriod(TypedDict):
    """Period information for monthly report."""

    year: int
    month: int
    start_date: str
    end_date: str


class MonthlyReportCharts(TypedDict):
    """Charts for monthly report."""

    top_rotations: list[ChartDataItem]
    daily_coverage: list[ChartDataItem]


class MonthlyReport(TypedDict):
    """Monthly summary report."""

    report_type: str
    period: MonthlyReportPeriod
    summary: SummaryInfo
    metrics: MetricsInfo
    charts: MonthlyReportCharts
    recommendations: list[str]
    generated_at: str


class ResidentReportPerson(TypedDict):
    """Person information for resident report."""

    id: str
    name: str
    pgy_level: int | None
    target_blocks: int


class ResidentReportPeriod(TypedDict):
    """Period information for resident report."""

    start_date: str
    end_date: str


class ResidentReportSummary(TypedDict):
    """Summary for resident report."""

    total_assignments: int
    unique_rotations: int
    utilization_percent: float


class ResidentReportCharts(TypedDict):
    """Charts for resident report."""

    rotation_distribution: list[ChartDataItem]


class ResidentReport(TypedDict):
    """Individual resident statistics report."""

    report_type: str
    person: ResidentReportPerson
    period: ResidentReportPeriod
    summary: ResidentReportSummary
    duty_patterns: ConsecutiveDutyStats
    rotations: list[ChartDataItem]
    charts: ResidentReportCharts
    recommendations: list[str]
    generated_at: str


class ComplianceReportDetails(TypedDict):
    """Details for compliance report."""

    compliance_metric: MetricResult
    supervision_issues: list[dict[str, str | int]]


class ComplianceReportCharts(TypedDict):
    """Charts for compliance report."""

    violations_by_run: list[ChartDataItem]


class ComplianceReport(TypedDict):
    """ACGME compliance summary report."""

    report_type: str
    period: ResidentReportPeriod
    summary: SummaryInfo
    details: ComplianceReportDetails
    charts: ComplianceReportCharts
    recommendations: list[str]
    generated_at: str


class WorkloadReportCharts(TypedDict):
    """Charts for workload report."""

    utilization_distribution: list[ChartDataItem]
    pgy_level_distribution: list[ChartDataItem]


class WorkloadReportDetails(TypedDict):
    """Details for workload report."""

    fairness_metric: MetricResult
    workload_by_resident: list[ResidentWorkload]


class WorkloadReport(TypedDict):
    """Workload distribution report."""

    report_type: str
    period: ResidentReportPeriod
    summary: SummaryInfo
    details: WorkloadReportDetails
    charts: WorkloadReportCharts
    recommendations: list[str]
    generated_at: str


class StabilityMetricsDict(TypedDict):
    """Dictionary representation of stability metrics."""

    assignments_changed: int
    churn_rate: float
    ripple_factor: float
    n1_vulnerability_score: float
    new_violations: int
    days_since_major_change: int
    total_assignments: int
    computed_at: str | None
    version_id: str | None
    is_stable: bool
    stability_grade: str
