"""
Resilience Framework for Scheduling System.

Tier 1 Critical Concepts:
1. Utilization Threshold (80% cap from queuing theory)
2. Defense in Depth (5 safety levels from nuclear engineering)
3. Contingency Analysis (N-1/N-2 from power grid)
4. Static Stability (pre-computed fallbacks from AWS)
5. Sacrifice Hierarchy (load shedding from triage medicine)

Tier 2 Strategic Concepts:
6. Homeostasis/Feedback Loops (from biology/physiology)
7. Blast Radius Isolation (zone-based containment from AWS)
8. Le Chatelier's Principle (equilibrium shifts from chemistry)

Tier 3 Tactical Concepts:
9. Cognitive Load Management (from psychology/human factors)
10. Stigmergy/Swarm Intelligence (from biology/AI)
11. Hub Vulnerability Analysis (from network theory)
12. Creep/Fatigue Analysis (from materials science)

Tier 3+ Cross-Disciplinary Concepts:
13. SPC Monitoring (from semiconductor manufacturing)
14. Process Capability (from Six Sigma quality management)
15. Burnout Epidemiology (from epidemiology and public health)
16. Erlang Coverage (from telecommunications queueing theory)
17. Seismic Detection (from seismology early warning systems)
18. Burnout Fire Index (from forestry CFFDRS)
19. Creep Fatigue (from materials science)
"""

# Circuit Breaker
# Tier 1 imports
from app.resilience.blast_radius import (
    BlastRadiusManager,
    BlastRadiusReport,
    BorrowingPriority,
    ContainmentLevel,
    SchedulingZone,
    ZoneHealthReport,
    ZoneIncident,
    ZoneStatus,
    ZoneType,
)

# Tier 3+: Cross-Disciplinary imports
from app.resilience.burnout_epidemiology import (
    BurnoutEpidemiology,
    BurnoutSIRModel,
    BurnoutState,
    EpiReport,
)
from app.resilience.burnout_fire_index import (
    BurnoutCodeReport,
    BurnoutDangerRating,
    DangerClass,
    FireDangerReport,
)
from app.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerMetrics,
    CircuitBreakerRegistry,
    CircuitBreakerTimeoutError,
    CircuitMetrics,
    CircuitOpenError,
    CircuitState,
    MetricsCollector,
    StateMachine,
    StateTransition,
    async_circuit_breaker,
    circuit_breaker,
    collect_metrics_for_all_breakers,
    get_breaker_from_function,
    get_breaker_name_from_function,
)
from app.resilience.circuit_breaker import get_metrics as get_circuit_breaker_metrics
from app.resilience.circuit_breaker import (
    get_registry,
)
from app.resilience.circuit_breaker import (
    setup_metrics as setup_circuit_breaker_metrics,
)
from app.resilience.circuit_breaker import (
    setup_registry,
    with_async_circuit_breaker,
    with_circuit_breaker,
)

# Tier 3 imports
from app.resilience.cognitive_load import (
    CognitiveLoadManager,
    CognitiveLoadReport,
    CognitiveSession,
    CognitiveState,
    Decision,
    DecisionCategory,
    DecisionComplexity,
    DecisionOutcome,
    DecisionQueueStatus,
)
from app.resilience.contingency import (
    CascadeSimulation,
    CentralityScore,
    ContingencyAnalyzer,
    VulnerabilityReport,
)
from app.resilience.recovery_distance import (
    AssignmentEdit,
    N1Event,
    RecoveryDistanceCalculator,
    RecoveryDistanceMetrics,
    RecoveryResult,
)
from app.resilience.creep_fatigue import (
    CreepAnalysis,
    CreepFatigueModel,
    CreepStage,
    FatigueCurve,
)
from app.resilience.defense_in_depth import DefenseInDepth, DefenseLevel
from app.resilience.erlang_coverage import (
    ErlangCCalculator,
    ErlangMetrics,
    SpecialistCoverage,
)

# Tier 2 imports
from app.resilience.homeostasis import (
    AllostasisMetrics,
    AllostasisState,
    CorrectiveAction,
    DeviationSeverity,
    FeedbackLoop,
    HomeostasisMonitor,
    HomeostasisStatus,
    PositiveFeedbackRisk,
    Setpoint,
)
from app.resilience.hub_analysis import (
    CrossTrainingPriority,
    CrossTrainingRecommendation,
    FacultyCentrality,
    HubAnalyzer,
    HubDistributionReport,
    HubProfile,
    HubProtectionPlan,
    HubProtectionStatus,
    HubRiskLevel,
)
from app.resilience.le_chatelier import (
    CompensationResponse,
    CompensationType,
    EquilibriumReport,
    EquilibriumShift,
    EquilibriumState,
    LeChatelierAnalyzer,
    StressResponsePrediction,
    StressType,
    SystemStress,
)
from app.resilience.process_capability import (
    ProcessCapabilityReport,
    ScheduleCapabilityAnalyzer,
)
from app.resilience.sacrifice_hierarchy import (
    ActivityCategory,
    LoadSheddingLevel,
    SacrificeHierarchy,
)
from app.resilience.seismic_detection import (
    BurnoutEarlyWarning,
    PrecursorSignal,
    SeismicAlert,
)

# Main service
from app.resilience.service import ResilienceConfig, ResilienceService
from app.resilience.spc_monitoring import (
    SPCAlert,
    WorkloadControlChart,
    calculate_control_limits,
    calculate_process_capability,
)
from app.resilience.static_stability import FallbackScenario, FallbackScheduler
from app.resilience.stigmergy import (
    CollectivePreference,
    PreferenceTrail,
    SignalType,
    StigmergicScheduler,
    StigmergyStatus,
    SwapNetwork,
    TrailStrength,
    TrailType,
)
from app.resilience.utilization import UtilizationMonitor, UtilizationThreshold

__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerError",
    "CircuitOpenError",
    "CircuitBreakerTimeoutError",
    "CircuitState",
    "CircuitMetrics",
    "StateTransition",
    "StateMachine",
    "CircuitBreakerRegistry",
    "get_registry",
    "setup_registry",
    "circuit_breaker",
    "async_circuit_breaker",
    "with_circuit_breaker",
    "with_async_circuit_breaker",
    "get_breaker_from_function",
    "get_breaker_name_from_function",
    "CircuitBreakerMetrics",
    "get_circuit_breaker_metrics",
    "setup_circuit_breaker_metrics",
    "collect_metrics_for_all_breakers",
    "MetricsCollector",
    # Tier 1: Utilization
    "UtilizationMonitor",
    "UtilizationThreshold",
    # Tier 1: Defense in Depth
    "DefenseLevel",
    "DefenseInDepth",
    # Tier 1: Contingency
    "ContingencyAnalyzer",
    "VulnerabilityReport",
    "CascadeSimulation",
    "CentralityScore",
    # Tier 1: Recovery Distance
    "RecoveryDistanceCalculator",
    "RecoveryDistanceMetrics",
    "RecoveryResult",
    "N1Event",
    "AssignmentEdit",
    # Tier 1: Static Stability
    "FallbackScheduler",
    "FallbackScenario",
    # Tier 1: Sacrifice Hierarchy
    "SacrificeHierarchy",
    "ActivityCategory",
    "LoadSheddingLevel",
    # Tier 2: Homeostasis
    "HomeostasisMonitor",
    "AllostasisMetrics",
    "AllostasisState",
    "HomeostasisStatus",
    "FeedbackLoop",
    "Setpoint",
    "PositiveFeedbackRisk",
    "CorrectiveAction",
    "DeviationSeverity",
    # Tier 2: Blast Radius
    "BlastRadiusManager",
    "SchedulingZone",
    "ZoneStatus",
    "ZoneType",
    "ContainmentLevel",
    "ZoneHealthReport",
    "BlastRadiusReport",
    "BorrowingPriority",
    "ZoneIncident",
    # Tier 2: Le Chatelier
    "LeChatelierAnalyzer",
    "SystemStress",
    "StressType",
    "CompensationResponse",
    "CompensationType",
    "EquilibriumShift",
    "EquilibriumState",
    "EquilibriumReport",
    "StressResponsePrediction",
    # Tier 3: Cognitive Load
    "CognitiveLoadManager",
    "CognitiveSession",
    "CognitiveState",
    "Decision",
    "DecisionCategory",
    "DecisionComplexity",
    "DecisionOutcome",
    "CognitiveLoadReport",
    "DecisionQueueStatus",
    # Tier 3: Creep/Fatigue
    "CreepFatigueModel",
    "CreepStage",
    "CreepAnalysis",
    "FatigueCurve",
    # Tier 3: Stigmergy
    "StigmergicScheduler",
    "PreferenceTrail",
    "TrailType",
    "TrailStrength",
    "SignalType",
    "CollectivePreference",
    "SwapNetwork",
    "StigmergyStatus",
    # Tier 3: Hub Analysis
    "HubAnalyzer",
    "FacultyCentrality",
    "HubProfile",
    "HubRiskLevel",
    "HubProtectionStatus",
    "HubProtectionPlan",
    "CrossTrainingRecommendation",
    "CrossTrainingPriority",
    "HubDistributionReport",
    # Tier 3: SPC Monitoring
    "SPCAlert",
    "WorkloadControlChart",
    "calculate_control_limits",
    "calculate_process_capability",
    # Tier 3+: Cross-Disciplinary
    # Burnout Epidemiology
    "BurnoutEpidemiology",
    "BurnoutSIRModel",
    "BurnoutState",
    "EpiReport",
    # Burnout Fire Index
    "BurnoutCodeReport",
    "BurnoutDangerRating",
    "DangerClass",
    "FireDangerReport",
    # Erlang Coverage
    "ErlangCCalculator",
    "ErlangMetrics",
    "SpecialistCoverage",
    # Process Capability
    "ProcessCapabilityReport",
    "ScheduleCapabilityAnalyzer",
    # Seismic Detection
    "BurnoutEarlyWarning",
    "PrecursorSignal",
    "SeismicAlert",
    # Service
    "ResilienceService",
    "ResilienceConfig",
]
