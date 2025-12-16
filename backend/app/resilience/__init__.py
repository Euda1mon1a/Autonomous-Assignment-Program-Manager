"""
Resilience Framework for Scheduling System.

Implements Tier 1 critical concepts from the resilience framework:
1. Utilization Threshold (80% cap from queuing theory)
2. Defense in Depth (5 safety levels from nuclear engineering)
3. Contingency Analysis (N-1/N-2 from power grid)
4. Static Stability (pre-computed fallbacks from AWS)
5. Sacrifice Hierarchy (load shedding from triage medicine)
"""

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
from app.resilience.service import ResilienceService

__all__ = [
    # Utilization
    "UtilizationMonitor",
    "UtilizationThreshold",
    # Defense in Depth
    "DefenseLevel",
    "DefenseInDepth",
    # Contingency
    "ContingencyAnalyzer",
    "VulnerabilityReport",
    "CascadeSimulation",
    "CentralityScore",
    # Static Stability
    "FallbackScheduler",
    "FallbackScenario",
    # Sacrifice Hierarchy
    "SacrificeHierarchy",
    "ActivityCategory",
    "LoadSheddingLevel",
    # Service
    "ResilienceService",
]
