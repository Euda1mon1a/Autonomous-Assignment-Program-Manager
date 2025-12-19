"""
Scheduling Catalyst Library
============================

A Python library applying activation energy and catalyst concepts from
chemistry/biology to personnel scheduling and resource management.

Core Concepts:
- **Activation Energy Barriers**: Obstacles that prevent schedule changes
  (freeze horizons, credential requirements, ACGME rules)
- **Catalysts**: Personnel or mechanisms that lower barriers without being
  consumed (coordinators, cross-trained staff, override codes)
- **Transition States**: Intermediate configurations during schedule changes
- **Reaction Pathways**: Possible routes from current to desired schedule state

Usage:
    from app.scheduling_catalyst import (
        CatalystPerson,
        EnergyBarrier,
        BarrierType,
        CatalystAnalyzer,
        TransitionOptimizer,
    )

    # Identify barriers for a schedule change
    analyzer = CatalystAnalyzer(db_session)
    barriers = await analyzer.identify_barriers(assignment, proposed_change)

    # Find catalysts that can lower these barriers
    catalysts = await analyzer.find_catalysts(barriers)

    # Optimize the transition pathway
    optimizer = TransitionOptimizer(db_session)
    pathway = await optimizer.find_optimal_pathway(
        current_state=assignment,
        target_state=proposed_change,
        available_catalysts=catalysts,
    )
"""

from app.scheduling_catalyst.models import (
    ActivationEnergy,
    BarrierType,
    CatalystType,
    CatalystPerson,
    CatalystMechanism,
    EnergyBarrier,
    TransitionState,
    ReactionPathway,
    ScheduleReaction,
)
from app.scheduling_catalyst.barriers import (
    BarrierDetector,
    BarrierClassifier,
)
from app.scheduling_catalyst.catalysts import (
    CatalystAnalyzer,
    CatalystScorer,
)
from app.scheduling_catalyst.optimizer import (
    TransitionOptimizer,
    PathwayResult,
)

__all__ = [
    # Models
    "ActivationEnergy",
    "BarrierType",
    "CatalystType",
    "CatalystPerson",
    "CatalystMechanism",
    "EnergyBarrier",
    "TransitionState",
    "ReactionPathway",
    "ScheduleReaction",
    # Barrier Detection
    "BarrierDetector",
    "BarrierClassifier",
    # Catalyst Analysis
    "CatalystAnalyzer",
    "CatalystScorer",
    # Optimization
    "TransitionOptimizer",
    "PathwayResult",
]

__version__ = "0.1.0"
