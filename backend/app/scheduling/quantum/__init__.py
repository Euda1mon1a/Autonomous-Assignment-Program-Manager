"""
Quantum-Inspired Optimization for Residency Scheduling.

This module provides quantum-inspired solvers that can run on classical hardware
using simulated annealing, or optionally on D-Wave quantum hardware.

Two solver categories:

1. General Scheduling QUBO (qubo_solver.py):
   - QUBOFormulation: General half-day scheduling
   - SimulatedQuantumAnnealingSolver: Quantum-inspired SA
   - QUBOSolver: PyQUBO-based solver
   - QuantumInspiredSolver: Hybrid auto-selector

2. Call Assignment QUBO (call_assignment_qubo.py):
   - CallAssignmentQUBO: Specialized for overnight call
   - QuantumTunnelingAnnealingSolver: Enhanced SA with tunneling
   - CallAssignmentValidator: Solution validator
   - CallAssignmentBenchmark: OR-Tools comparison

Available Libraries (install as needed):
- pyqubo: QUBO formulation (pip install pyqubo)
- dwave-samplers: Simulated annealing (pip install dwave-samplers)
- dwave-system: D-Wave quantum hardware (pip install dwave-system)
- qubovert: Alternative QUBO library (pip install qubovert)
- numpy: Required for call assignment QUBO (pip install numpy)
"""

from app.scheduling.quantum.qubo_solver import (
    QuantumInspiredSolver,
    QUBOFormulation,
    QUBOSolver,
    SimulatedQuantumAnnealingSolver,
    get_quantum_library_status,
)

from app.scheduling.quantum.call_assignment_qubo import (
    CallAssignmentQUBO,
    CallCandidate,
    CallNight,
    CallType,
    QuantumTunnelingAnnealingSolver,
    CallAssignmentValidator,
    CallAssignmentBenchmark,
    QUBOSolution,
    solve_call_assignment,
    create_call_nights_from_dates,
    create_candidates_from_residents,
)

__all__ = [
    # General scheduling QUBO
    "QUBOFormulation",
    "QUBOSolver",
    "QuantumInspiredSolver",
    "SimulatedQuantumAnnealingSolver",
    "get_quantum_library_status",
    # Call assignment QUBO
    "CallAssignmentQUBO",
    "CallCandidate",
    "CallNight",
    "CallType",
    "QuantumTunnelingAnnealingSolver",
    "CallAssignmentValidator",
    "CallAssignmentBenchmark",
    "QUBOSolution",
    "solve_call_assignment",
    "create_call_nights_from_dates",
    "create_candidates_from_residents",
]
