***REMOVED*** Quantum Solver Quick Start Guide

***REMOVED******REMOVED*** TL;DR

The quantum solver now has graceful fallback and environment-based configuration. It won't crash if D-Wave is unavailable.

***REMOVED******REMOVED*** Basic Usage

***REMOVED******REMOVED******REMOVED*** Option 1: Environment-Based (Recommended)

```bash
***REMOVED*** In .env file
USE_QUANTUM_SOLVER=true
QUANTUM_SOLVER_BACKEND=classical  ***REMOVED*** or "quantum" for D-Wave hardware
```

```python
from app.scheduling.quantum import create_quantum_solver_from_env

solver = create_quantum_solver_from_env(timeout_seconds=60.0)
if solver:
    result = solver.solve(context)
else:
    ***REMOVED*** Quantum disabled - use classical solver
    from app.scheduling.solvers import SolverFactory
    result = SolverFactory.create("cp_sat").solve(context)
```

***REMOVED******REMOVED******REMOVED*** Option 2: Direct Instantiation

```python
from app.scheduling.quantum import SimulatedQuantumAnnealingSolver

***REMOVED*** Classical simulated annealing (no dependencies)
solver = SimulatedQuantumAnnealingSolver(
    timeout_seconds=60.0,
    num_reads=100,
    num_sweeps=1000
)

result = solver.solve(context)
print(f"Status: {result.solver_status}")
print(f"Assignments: {len(result.assignments)}")
```

***REMOVED******REMOVED******REMOVED*** Option 3: Via SolverFactory

```python
from app.scheduling.solvers import SolverFactory

***REMOVED*** Auto-selects quantum or classical
solver = SolverFactory.create("quantum", timeout_seconds=120.0)
result = solver.solve(context)
```

***REMOVED******REMOVED*** Configuration Examples

***REMOVED******REMOVED******REMOVED*** Development (Classical Simulation)

```bash
***REMOVED*** .env
USE_QUANTUM_SOLVER=true
QUANTUM_SOLVER_BACKEND=classical
```

**Result**: Uses classical simulated annealing (no API key needed)

***REMOVED******REMOVED******REMOVED*** Production (D-Wave Quantum Hardware)

```bash
***REMOVED*** .env
USE_QUANTUM_SOLVER=true
QUANTUM_SOLVER_BACKEND=quantum
DWAVE_API_TOKEN=your_api_token_here
```

**Result**: Tries D-Wave hardware, falls back to classical if unavailable

***REMOVED******REMOVED******REMOVED*** Disabled (Default)

```bash
***REMOVED*** .env
USE_QUANTUM_SOLVER=false
```

**Result**: Quantum solver disabled, use classical solvers (CP-SAT, PuLP, Greedy)

***REMOVED******REMOVED*** Graceful Fallback

The solver automatically falls back to classical simulation if:

1. ❌ D-Wave libraries not installed → Classical SA
2. ❌ API token missing → Classical SA
3. ❌ Invalid token → Classical SA
4. ❌ Service unreachable → Classical SA
5. ❌ Problem too large → Classical SA

You'll see a warning log but the solver will still succeed.

***REMOVED******REMOVED*** Check Configuration

```python
from app.scheduling.quantum import get_quantum_solver_config

config = get_quantum_solver_config()
print(f"Enabled: {config['enabled']}")
print(f"Backend: {config['backend']}")
print(f"Quantum hardware: {config['use_quantum_hardware']}")
print(f"Libraries: {config['libraries_available']}")
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** "D-Wave libraries not available"

```bash
pip install dwave-samplers  ***REMOVED*** Classical mode
pip install dwave-system     ***REMOVED*** Quantum hardware
```

***REMOVED******REMOVED******REMOVED*** "D-Wave API token not provided"

Add to `.env`:
```bash
DWAVE_API_TOKEN=your_token_here
```

***REMOVED******REMOVED******REMOVED*** Solver always uses classical mode

1. Check environment: `get_quantum_solver_config()`
2. Verify token set: `echo $DWAVE_API_TOKEN`
3. Check logs: Look for "quantum" or "dwave" messages

***REMOVED******REMOVED*** Performance

- **Classical SA**: Fast for <10,000 variables
- **D-Wave**: Very fast but limited to ~5,000 variables
- **Fallback overhead**: ~50-100ms for connection attempt

***REMOVED******REMOVED*** See Also

- Full documentation: `backend/app/scheduling/quantum/README.md`
- Test examples: `backend/tests/quantum/test_quantum_solver_fallback.py`
- Session report: `.claude/dontreadme/sessions/SESSION_50_QUANTUM_SOLVER_FIXES.md`
