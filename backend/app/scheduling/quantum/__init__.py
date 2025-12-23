"""
Quantum-Inspired Optimization for Residency Scheduling.

This module provides quantum-inspired solvers that can run on classical hardware
using simulated annealing, or optionally on D-Wave quantum hardware.

Available Libraries (install as needed):
- pyqubo: QUBO formulation (pip install pyqubo)
- dwave-samplers: Simulated annealing (pip install dwave-samplers)
- dwave-system: D-Wave quantum hardware (pip install dwave-system)
- qubovert: Alternative QUBO library (pip install qubovert)
"""

from app.scheduling.quantum.qubo_solver import (
    QuantumInspiredSolver,
    QUBOFormulation,
    QUBOSolver,
    SimulatedQuantumAnnealingSolver,
    get_quantum_library_status,
)

__all__ = [
    "QUBOFormulation",
    "QUBOSolver",
    "QuantumInspiredSolver",
    "SimulatedQuantumAnnealingSolver",
    "get_quantum_library_status",
]
