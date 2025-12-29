"""
Tools subpackage for specialized MCP tools.

This package contains specialized tool implementations that integrate
with the backend constraint service and other services.

Exotic Research Tools (require numpy, scipy):
- game_theory_tools: Nash equilibrium analysis for schedule stability
- ecological_dynamics_tools: Lotka-Volterra supply/demand modeling
- kalman_filter_tools: Workload trend analysis with noise filtering
- fourier_analysis_tools: FFT-based periodicity detection
"""

from .validate_schedule import (
    ConstraintConfig,
    ScheduleValidationRequest,
    ScheduleValidationResponse,
    validate_schedule,
)

# Game Theory Tools - Nash equilibrium analysis
from .game_theory_tools import (
    # Analysis Functions
    analyze_nash_stability,
    find_deviation_incentives,
    detect_coordination_failures,
    # Request Models
    NashStabilityRequest,
    DeviationIncentivesRequest,
    # Response Models
    NashStabilityResponse,
    PersonDeviationAnalysis,
    CoordinationFailuresResponse,
    # Supporting Models
    DeviationIncentive,
    CoordinationFailure,
    UtilityComponents,
    # Enums
    StabilityStatus,
    DeviationType,
    CoordinationFailureType,
    # Utility Functions
    calculate_person_utility,
)

# Ecological Dynamics Tools - Lotka-Volterra supply/demand modeling
from .ecological_dynamics_tools import (
    # Enums
    InterventionTypeEnum,
    RiskLevelEnum,
    SystemStabilityEnum,
    # Request Models
    CapacityCrunchRequest,
    EquilibriumRequest,
    InterventionRequest,
    SupplyDemandCyclesRequest,
    # Response Models
    CapacityCrunchResponse,
    EquilibriumResponse,
    HistoricalDataPoint,
    InterventionResponse,
    SupplyDemandCyclesResponse,
    # Tool Functions
    analyze_supply_demand_cycles,
    find_equilibrium_point,
    predict_capacity_crunch,
    simulate_intervention,
)

# Kalman Filter Tools - Workload trend analysis
from .kalman_filter_tools import (
    # Request Models
    WorkloadAnomalyRequest,
    WorkloadTrendRequest,
    # Response Models
    AnomalyPoint,
    WorkloadAnomalyResponse,
    WorkloadTrendResponse,
    # Tool Functions
    analyze_workload_trend,
    detect_workload_anomalies,
)

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

__all__ = [
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
