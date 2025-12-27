"""
Multi-Objective Optimization Framework.

This module provides a comprehensive framework for multi-objective optimization
with interactive decision support, complementing the existing NSGA-II implementation
with MOEA/D and advanced constraint handling.

Modules:
    - core: Base types, objectives, solutions
    - moead: MOEA/D algorithm (decomposition-based)
    - constraints: Advanced constraint handling (penalty, repair, relaxation)
    - preferences: Preference articulation (a priori, a posteriori, interactive)
    - indicators: Quality metrics (hypervolume, spread, epsilon)
    - decision_support: Interactive decision maker interface
    - diversity: Diversity preservation (crowding, epsilon-dominance)
    - export: JSON export for holographic hub
    - reweighting: Dynamic objective reweighting

Multi-Objective Lens:
    Multi-objective optimization recognizes that real-world problems often have
    conflicting goals that cannot all be optimized simultaneously. Instead of
    finding a single "best" solution, we discover the Pareto frontier - the set
    of solutions where improving one objective necessarily degrades another.

    In medical scheduling:
    - Coverage vs. Equity: Full coverage may overload some staff
    - Preferences vs. Compliance: Staff wishes may conflict with ACGME rules
    - Efficiency vs. Resilience: Lean staffing offers no buffer for emergencies

    The framework enables decision makers to:
    1. Explore trade-offs between competing objectives
    2. Articulate preferences at different stages of optimization
    3. Navigate the solution space interactively
    4. Make informed decisions about acceptable compromises
"""

from .core import (
    DominanceRelation,
    ObjectiveConfig,
    ObjectiveDirection,
    ObjectiveType,
    ParetoFrontier,
    Solution,
    SolutionArchive,
)
from .moead import MOEADAlgorithm, DecompositionMethod, WeightVector
from .constraints import (
    ConstraintHandler,
    ConstraintHandlingMethod,
    FeasibilityPreserver,
    PenaltyMethod,
    RepairOperator,
)
from .preferences import (
    PreferenceArticulator,
    PreferenceMethod,
    ReferencePoint,
    WeightedSum,
    AchievementScalarizing,
)
from .indicators import (
    HypervolumeIndicator,
    QualityIndicator,
    SpreadIndicator,
    EpsilonIndicator,
    GenerationalDistance,
    InvertedGenerationalDistance,
)
from .decision_support import (
    DecisionMaker,
    TradeOffAnalyzer,
    SolutionExplorer,
    PreferenceElicitor,
)
from .diversity import (
    CrowdingDistance,
    DiversityMechanism,
    EpsilonDominance,
    NichingOperator,
)
from .export import (
    HolographicExporter,
    TradeOffLandscape,
    ParetoVisualization,
)
from .reweighting import (
    DynamicReweighter,
    FeedbackProcessor,
    ObjectiveAdjuster,
)

__all__ = [
    # Core types
    "DominanceRelation",
    "ObjectiveConfig",
    "ObjectiveDirection",
    "ObjectiveType",
    "ParetoFrontier",
    "Solution",
    "SolutionArchive",
    # MOEA/D
    "MOEADAlgorithm",
    "DecompositionMethod",
    "WeightVector",
    # Constraint handling
    "ConstraintHandler",
    "ConstraintHandlingMethod",
    "FeasibilityPreserver",
    "PenaltyMethod",
    "RepairOperator",
    # Preferences
    "PreferenceArticulator",
    "PreferenceMethod",
    "ReferencePoint",
    "WeightedSum",
    "AchievementScalarizing",
    # Indicators
    "HypervolumeIndicator",
    "QualityIndicator",
    "SpreadIndicator",
    "EpsilonIndicator",
    "GenerationalDistance",
    "InvertedGenerationalDistance",
    # Decision support
    "DecisionMaker",
    "TradeOffAnalyzer",
    "SolutionExplorer",
    "PreferenceElicitor",
    # Diversity
    "CrowdingDistance",
    "DiversityMechanism",
    "EpsilonDominance",
    "NichingOperator",
    # Export
    "HolographicExporter",
    "TradeOffLandscape",
    "ParetoVisualization",
    # Reweighting
    "DynamicReweighter",
    "FeedbackProcessor",
    "ObjectiveAdjuster",
]
