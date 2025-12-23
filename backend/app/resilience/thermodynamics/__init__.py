"""
Thermodynamics Module for Resilience Framework.

This module implements exotic thermodynamic and statistical mechanics concepts
for enhanced early warning and stability analysis in scheduling systems.

Based on research: docs/research/thermodynamic_resilience_foundations.md

Key Components:
- Entropy: Schedule disorder and information content
- Free Energy: Stability landscape analysis
- Phase Transitions: Critical phenomena detection
- Boltzmann Distribution: Probabilistic schedule sampling
- Information Thermodynamics: Optimal monitoring strategies
- Dissipative Structures: Self-organization analysis
- Fluctuation-Dissipation: Response prediction from noise

Integration with Existing Framework:
- Extends HomeostasisMonitor with thermodynamic foundations
- Enhances phase transition detection with critical phenomena theory
- Provides deeper theoretical basis for early warning signals
"""

from app.resilience.thermodynamics.entropy import (
    ScheduleEntropyMonitor,
    calculate_schedule_entropy,
    conditional_entropy,
    entropy_production_rate,
    mutual_information,
)
from app.resilience.thermodynamics.free_energy import (
    EnergyLandscapeAnalyzer,
    FreeEnergyMetrics,
    adaptive_temperature,
    calculate_free_energy,
)
from app.resilience.thermodynamics.phase_transitions import (
    CriticalPhenomenaMonitor,
    PhaseTransitionDetector,
    detect_critical_slowing,
    estimate_time_to_transition,
)

__all__ = [
    # Entropy
    "ScheduleEntropyMonitor",
    "calculate_schedule_entropy",
    "mutual_information",
    "conditional_entropy",
    "entropy_production_rate",
    # Free Energy
    "FreeEnergyMetrics",
    "calculate_free_energy",
    "EnergyLandscapeAnalyzer",
    "adaptive_temperature",
    # Phase Transitions
    "PhaseTransitionDetector",
    "CriticalPhenomenaMonitor",
    "detect_critical_slowing",
    "estimate_time_to_transition",
]
