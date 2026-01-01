"""
Tools subpackage for specialized MCP tools.

This package contains specialized tool implementations that integrate
with the backend constraint service and other services.

Production Tools:
- schedule: Schedule management (get, create, update, delete, generate, validate, optimize, export)
- compliance: ACGME compliance checking (work hours, day-off, supervision, violations, reports)
- swap: Schedule swap management (create, find matches, execute, rollback, history)
- resilience: Resilience monitoring (defense level, utilization, N-1 analysis, burnout Rt, early warnings)
- analytics: Schedule analytics (coverage metrics, workload distribution, trend analysis)

Exotic Research Tools (require numpy, scipy):
- game_theory_tools: Nash equilibrium analysis for schedule stability
- ecological_dynamics_tools: Lotka-Volterra supply/demand modeling
- kalman_filter_tools: Workload trend analysis with noise filtering
- fourier_analysis_tools: FFT-based periodicity detection
"""

# Base infrastructure
# Analytics tools
from .analytics import (
    CoverageMetricsTool,
    TrendAnalysisTool,
    WorkloadDistributionTool,
)
from .base import (
    APIError,
    AuthenticationError,
    BaseTool,
    ToolError,
)
from .base import (
    ValidationError as ToolValidationError,
)

# Compliance tools
from .compliance import (
    CheckDayOffTool,
    CheckSupervisionTool,
    CheckWorkHoursTool,
    GenerateComplianceReportTool,
    GetViolationsTool,
)

# Ecological Dynamics Tools - Lotka-Volterra supply/demand modeling
from .ecological_dynamics_tools import (
    # Request Models
    CapacityCrunchRequest,
    # Response Models
    CapacityCrunchResponse,
    EquilibriumRequest,
    EquilibriumResponse,
    HistoricalDataPoint,
    InterventionRequest,
    InterventionResponse,
    # Enums
    InterventionTypeEnum,
    RiskLevelEnum,
    SupplyDemandCyclesRequest,
    SupplyDemandCyclesResponse,
    SystemStabilityEnum,
    # Tool Functions
    analyze_supply_demand_cycles,
    find_equilibrium_point,
    predict_capacity_crunch,
    simulate_intervention,
)
from .executor import ExecutionContext, ToolExecutor, get_executor

# Fourier/FFT Analysis Tools - Periodicity detection
from .fourier_analysis_tools import (
    # Response Models
    DominantPeriod,
    HarmonicResonanceResponse,
    ScheduleCyclesResponse,
    SpectralEntropyResponse,
    # Tool Functions
    analyze_harmonic_resonance,
    calculate_spectral_entropy,
    detect_schedule_cycles,
)

# Game Theory Tools - Nash equilibrium analysis
from .game_theory_tools import (
    CoordinationFailure,
    CoordinationFailuresResponse,
    CoordinationFailureType,
    # Supporting Models
    DeviationIncentive,
    DeviationIncentivesRequest,
    DeviationType,
    # Request Models
    NashStabilityRequest,
    # Response Models
    NashStabilityResponse,
    PersonDeviationAnalysis,
    # Enums
    StabilityStatus,
    UtilityComponents,
    # Analysis Functions
    analyze_nash_stability,
    # Utility Functions
    calculate_person_utility,
    detect_coordination_failures,
    find_deviation_incentives,
)

# Kalman Filter Tools - Workload trend analysis
from .kalman_filter_tools import (
    # Response Models
    AnomalyPoint,
    # Request Models
    WorkloadAnomalyRequest,
    WorkloadAnomalyResponse,
    WorkloadTrendRequest,
    WorkloadTrendResponse,
    # Tool Functions
    analyze_workload_trend,
    detect_workload_anomalies,
)
from .registry import ToolRegistry, get_registry

# Resilience tools
from .resilience import (
    GetBurnoutRtTool,
    GetDefenseLevelTool,
    GetEarlyWarningsTool,
    GetUtilizationTool,
    RunN1AnalysisTool,
)

# Schedule tools
from .schedule import (
    CreateAssignmentTool,
    DeleteAssignmentTool,
    ExportScheduleTool,
    GenerateScheduleTool,
    GetScheduleTool,
    OptimizeScheduleTool,
    UpdateAssignmentTool,
    ValidateScheduleTool,
)

# Swap tools
from .swap import (
    CreateSwapTool,
    ExecuteSwapTool,
    FindSwapMatchesTool,
    GetSwapHistoryTool,
    RollbackSwapTool,
)
from .validate_schedule import (
    ConstraintConfig,
    ScheduleValidationRequest,
    ScheduleValidationResponse,
    validate_schedule,
)

__all__ = [
    # Base Infrastructure
    "BaseTool",
    "ToolError",
    "ToolValidationError",
    "APIError",
    "AuthenticationError",
    "ToolRegistry",
    "get_registry",
    "ToolExecutor",
    "get_executor",
    "ExecutionContext",
    # Schedule Tools
    "GetScheduleTool",
    "CreateAssignmentTool",
    "UpdateAssignmentTool",
    "DeleteAssignmentTool",
    "GenerateScheduleTool",
    "ValidateScheduleTool",
    "OptimizeScheduleTool",
    "ExportScheduleTool",
    # Compliance Tools
    "CheckWorkHoursTool",
    "CheckDayOffTool",
    "CheckSupervisionTool",
    "GetViolationsTool",
    "GenerateComplianceReportTool",
    # Swap Tools
    "CreateSwapTool",
    "FindSwapMatchesTool",
    "ExecuteSwapTool",
    "RollbackSwapTool",
    "GetSwapHistoryTool",
    # Resilience Tools
    "GetDefenseLevelTool",
    "GetUtilizationTool",
    "RunN1AnalysisTool",
    "GetBurnoutRtTool",
    "GetEarlyWarningsTool",
    # Analytics Tools
    "CoverageMetricsTool",
    "WorkloadDistributionTool",
    "TrendAnalysisTool",
    # Validate Schedule
    "ConstraintConfig",
    "ScheduleValidationRequest",
    "ScheduleValidationResponse",
    "validate_schedule",
    # Game Theory Tools
    "analyze_nash_stability",
    "find_deviation_incentives",
    "detect_coordination_failures",
    "NashStabilityRequest",
    "DeviationIncentivesRequest",
    "NashStabilityResponse",
    "PersonDeviationAnalysis",
    "CoordinationFailuresResponse",
    "DeviationIncentive",
    "CoordinationFailure",
    "UtilityComponents",
    "StabilityStatus",
    "DeviationType",
    "CoordinationFailureType",
    "calculate_person_utility",
    # Ecological Dynamics Tools
    "InterventionTypeEnum",
    "RiskLevelEnum",
    "SystemStabilityEnum",
    "CapacityCrunchRequest",
    "EquilibriumRequest",
    "InterventionRequest",
    "SupplyDemandCyclesRequest",
    "CapacityCrunchResponse",
    "EquilibriumResponse",
    "HistoricalDataPoint",
    "InterventionResponse",
    "SupplyDemandCyclesResponse",
    "analyze_supply_demand_cycles",
    "find_equilibrium_point",
    "predict_capacity_crunch",
    "simulate_intervention",
    # Kalman Filter Tools
    "WorkloadAnomalyRequest",
    "WorkloadTrendRequest",
    "AnomalyPoint",
    "WorkloadAnomalyResponse",
    "WorkloadTrendResponse",
    "analyze_workload_trend",
    "detect_workload_anomalies",
    # Fourier Analysis Tools
    "DominantPeriod",
    "HarmonicResonanceResponse",
    "ScheduleCyclesResponse",
    "SpectralEntropyResponse",
    "analyze_harmonic_resonance",
    "calculate_spectral_entropy",
    "detect_schedule_cycles",
]
