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
"""

# Tier 1 imports
from app.resilience.utilization import UtilizationMonitor, UtilizationThreshold
from app.resilience.defense_in_depth import DefenseLevel, DefenseInDepth
from app.resilience.contingency import (
    ContingencyAnalyzer,
    VulnerabilityReport,
    CascadeSimulation,
    CentralityScore,
)
from app.resilience.static_stability import FallbackScheduler, FallbackScenario
from app.resilience.sacrifice_hierarchy import (
    SacrificeHierarchy,
    ActivityCategory,
    LoadSheddingLevel,
)

# Tier 2 imports
from app.resilience.homeostasis import (
    HomeostasisMonitor,
    AllostasisMetrics,
    AllostasisState,
    HomeostasisStatus,
    FeedbackLoop,
    Setpoint,
    PositiveFeedbackRisk,
    CorrectiveAction,
    DeviationSeverity,
)
from app.resilience.blast_radius import (
    BlastRadiusManager,
    SchedulingZone,
    ZoneStatus,
    ZoneType,
    ContainmentLevel,
    ZoneHealthReport,
    BlastRadiusReport,
    BorrowingPriority,
    ZoneIncident,
)
from app.resilience.le_chatelier import (
    LeChatelierAnalyzer,
    SystemStress,
    StressType,
    CompensationResponse,
    CompensationType,
    EquilibriumShift,
    EquilibriumState,
    EquilibriumReport,
    StressResponsePrediction,
)

# Main service
from app.resilience.service import ResilienceService, ResilienceConfig

__all__ = [
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
    # Service
    "ResilienceService",
    "ResilienceConfig",
]
