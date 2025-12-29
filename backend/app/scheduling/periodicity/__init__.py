"""
Time Crystal-Inspired Periodicity Module

Implements stroboscopic state management and periodic schedule dynamics
based on time crystal physics concepts.

Key Concepts:
- Stroboscopic observation: State advances only at discrete checkpoints
- Phase locking: Maintaining periodic schedule structure
- Subharmonic detection: Identifying emergent longer cycles
- Anti-churn: Minimizing unnecessary schedule changes

Components:
- stroboscopic_manager: Checkpoint-based state transitions
- subharmonic_detector: Natural cycle detection using autocorrelation
- anti_churn: Rigidity objectives for optimization

References:
    - SYNERGY_ANALYSIS.md Section 11: Time Crystal Dynamics
    - docs/explorations/boolean-algebra-parallels.md
    - Shleyfman et al. (2025). Planning with Minimal Disruption. arXiv:2508.15358
"""

from app.scheduling.periodicity.anti_churn import (
    ScheduleSnapshot,
    calculate_schedule_rigidity,
    detect_periodic_patterns,
    estimate_churn_impact,
    hamming_distance,
    hamming_distance_by_person,
    time_crystal_objective,
)
from app.scheduling.periodicity.stroboscopic_manager import (
    CheckpointBoundary,
    CheckpointEvent,
    ScheduleState,
    StroboscopicScheduleManager,
)
from app.scheduling.periodicity.subharmonic_detector import (
    PeriodicityReport,
    SubharmonicDetector,
    TimeSeriesData,
    analyze_periodicity,
    build_assignment_time_series,
    detect_subharmonics,
)

__all__ = [
    # Anti-churn (rigidity) functions
    "ScheduleSnapshot",
    "hamming_distance",
    "hamming_distance_by_person",
    "calculate_schedule_rigidity",
    "time_crystal_objective",
    "estimate_churn_impact",
    "detect_periodic_patterns",
    # Stroboscopic state management
    "CheckpointBoundary",
    "CheckpointEvent",
    "ScheduleState",
    "StroboscopicScheduleManager",
    # Subharmonic detection
    "SubharmonicDetector",
    "PeriodicityReport",
    "TimeSeriesData",
    "detect_subharmonics",
    "build_assignment_time_series",
    "analyze_periodicity",
]
