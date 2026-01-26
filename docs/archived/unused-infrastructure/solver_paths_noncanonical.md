# Non-Canonical Solver Paths (Archived)

Status: Archived / non-canonical as of 2026-01-24.

The scheduling pipeline is now CP-SAT only. The following solver paths remain in the codebase for future work but are not used in the canonical generation pathway:

## Solver Implementations (Not Used)

- `backend/app/scheduling/solvers.py`
  - `GreedySolver`
  - `PuLPSolver`
  - `HybridSolver`

## Quantum / QUBO Stack (Not Used)

- `backend/app/scheduling/quantum/*`
- `backend/app/scheduling/quantum/qubo_solver.py`
- `backend/app/scheduling/quantum/call_assignment_qubo.py`

## Legacy Call Generation

- `backend/app/scheduling/constraints/overnight_call.py`
  - `OvernightCallGenerationConstraint` (disabled)

## Why Archived?

- Canonical generation now enforces CP-SAT everywhere.
- Greedy/PuLP/Hybrid are retained for later experimentation but are not part of the authoritative pathway.
- Call variables are created directly in `CPSATSolver` with dedicated call coverage constraints.

## Canonical Reference

- `docs/scheduling/CP_SAT_SCHEDULE_GENERATION.md`
