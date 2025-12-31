***REMOVED*** Quantum-Inspired Solvers for Residency Scheduling

***REMOVED******REMOVED*** Overview

This module provides quantum-inspired optimization solvers that can run on classical hardware using simulated annealing, or optionally on D-Wave quantum hardware. The solvers use QUBO (Quadratic Unconstrained Binary Optimization) formulations to model the scheduling problem.

***REMOVED******REMOVED*** Features

- **Graceful Fallback**: Automatically falls back to classical simulation if quantum hardware is unavailable
- **Environment-Based Configuration**: Easy configuration via environment variables
- **Multiple Backends**: Classical simulation (no dependencies) or D-Wave quantum hardware
- **Comprehensive Error Handling**: Handles missing libraries, invalid tokens, and service outages
- **Production-Ready**: Tested with mock D-Wave for reliability

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Basic Usage (Classical Simulation)

```python
from app.scheduling.quantum import create_quantum_solver_from_env
from app.scheduling.constraints import SchedulingContext

***REMOVED*** Create solver from environment configuration
solver = create_quantum_solver_from_env(timeout_seconds=60.0)

if solver:
    ***REMOVED*** Solve scheduling problem
    result = solver.solve(context)
    print(f"Found {len(result.assignments)} assignments")
    print(f"Solver used: {result.solver_status}")
else:
    ***REMOVED*** Quantum solver disabled - use classical solver
    from app.scheduling.solvers import SolverFactory
    solver = SolverFactory.create("cp_sat")
    result = solver.solve(context)
```

***REMOVED******REMOVED******REMOVED*** Environment Configuration

```bash
***REMOVED*** Enable quantum solver
export USE_QUANTUM_SOLVER=true

***REMOVED*** Select backend: "classical" or "quantum"
export QUANTUM_SOLVER_BACKEND=classical

***REMOVED*** For D-Wave quantum hardware (optional)
export DWAVE_API_TOKEN=your_api_token_here
```

***REMOVED******REMOVED*** Available Solvers

***REMOVED******REMOVED******REMOVED*** 1. SimulatedQuantumAnnealingSolver

**Best for**: General use, no dependencies required

Classical simulated annealing with quantum-inspired features:
- Quantum tunneling probability for escaping local minima
- Path-integral inspired temperature schedules
- Pure Python fallback (works without any quantum libraries)

```python
from app.scheduling.quantum import SimulatedQuantumAnnealingSolver

solver = SimulatedQuantumAnnealingSolver(
    timeout_seconds=60.0,
    num_reads=100,        ***REMOVED*** Number of independent annealing runs
    num_sweeps=1000,      ***REMOVED*** Number of sweeps per run
    beta_range=(0.1, 4.2) ***REMOVED*** Annealing schedule
)

result = solver.solve(context)
```

***REMOVED******REMOVED******REMOVED*** 2. QuantumInspiredSolver

**Best for**: Production use with automatic backend selection

Hybrid solver that automatically selects the best approach:
- Small problems: Classical simulated annealing
- Medium/large problems: Optimized simulated annealing
- D-Wave available: Quantum hardware for subproblems

```python
from app.scheduling.quantum import QuantumInspiredSolver

***REMOVED*** Automatic backend selection
solver = QuantumInspiredSolver(
    use_quantum_hardware=False,  ***REMOVED*** True to enable D-Wave
    dwave_token=None             ***REMOVED*** D-Wave API token
)

result = solver.solve(context)
print(f"Backend used: {result.statistics['backend']}")
```

***REMOVED******REMOVED******REMOVED*** 3. QUBOSolver

**Best for**: Research and experimentation

PyQUBO-based solver with high-level QUBO modeling:
- Requires PyQUBO package
- Supports tabu search or simulated annealing
- Automatic constraint handling

```python
from app.scheduling.quantum import QUBOSolver

solver = QUBOSolver(
    timeout_seconds=60.0,
    num_reads=100,
    use_tabu=False  ***REMOVED*** True for tabu search
)

result = solver.solve(context)
```

***REMOVED******REMOVED*** Installation

***REMOVED******REMOVED******REMOVED*** Classical Mode (No Dependencies)

The quantum solvers work out-of-the-box with pure Python fallback. No additional installation required.

***REMOVED******REMOVED******REMOVED*** Enhanced Classical Mode

For better performance, install D-Wave samplers:

```bash
pip install dwave-samplers
```

***REMOVED******REMOVED******REMOVED*** Quantum Hardware Mode

To use D-Wave quantum annealing hardware:

```bash
pip install dwave-system dwave-samplers
```

***REMOVED******REMOVED******REMOVED*** PyQUBO Support

For the QUBOSolver:

```bash
pip install pyqubo
```

***REMOVED******REMOVED*** Environment Configuration Reference

***REMOVED******REMOVED******REMOVED*** Required Variables

None - all quantum solver features are optional.

***REMOVED******REMOVED******REMOVED*** Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_QUANTUM_SOLVER` | `false` | Enable quantum solver |
| `QUANTUM_SOLVER_BACKEND` | `classical` | Backend type: `classical` or `quantum` |
| `DWAVE_API_TOKEN` | None | D-Wave API token for quantum hardware |

***REMOVED******REMOVED******REMOVED*** Configuration Examples

***REMOVED******REMOVED******REMOVED******REMOVED*** Development (Classical Simulation)

```bash
USE_QUANTUM_SOLVER=true
QUANTUM_SOLVER_BACKEND=classical
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Production (D-Wave Quantum Hardware)

```bash
USE_QUANTUM_SOLVER=true
QUANTUM_SOLVER_BACKEND=quantum
DWAVE_API_TOKEN=your_token_here
```

***REMOVED******REMOVED*** Graceful Fallback Behavior

The quantum solver automatically falls back to classical simulation in these cases:

1. **Libraries Not Installed**: D-Wave packages missing → Pure Python simulation
2. **No API Token**: `DWAVE_API_TOKEN` not set → Classical simulation
3. **Invalid Token**: API token authentication fails → Classical simulation
4. **Service Unavailable**: D-Wave service unreachable → Classical simulation
5. **Problem Too Large**: Exceeds quantum hardware limits → Classical simulation

**Fallback Process**:
```
1. Check if quantum hardware requested
2. Validate D-Wave libraries available
3. Validate API token present
4. Attempt D-Wave connection
5. On any failure → Fall back to classical SA
6. Log warning with reason for fallback
```

***REMOVED******REMOVED*** Usage in Production

***REMOVED******REMOVED******REMOVED*** Via SolverFactory

```python
from app.scheduling.solvers import SolverFactory

***REMOVED*** Create quantum solver from registry
solver = SolverFactory.create("quantum", timeout_seconds=120.0)
result = solver.solve(context)
```

***REMOVED******REMOVED******REMOVED*** Via Environment Helper

```python
from app.scheduling.quantum import create_quantum_solver_from_env

***REMOVED*** Automatically configured from environment
solver = create_quantum_solver_from_env(timeout_seconds=120.0)

if solver:
    result = solver.solve(context)
else:
    ***REMOVED*** Quantum disabled - use classical solver
    solver = SolverFactory.create("cp_sat")
    result = solver.solve(context)
```

***REMOVED******REMOVED******REMOVED*** Checking Configuration

```python
from app.scheduling.quantum import get_quantum_solver_config

config = get_quantum_solver_config()
print(f"Enabled: {config['enabled']}")
print(f"Backend: {config['backend']}")
print(f"Use quantum hardware: {config['use_quantum_hardware']}")
print(f"Libraries: {config['libraries_available']}")
```

***REMOVED******REMOVED*** Performance Characteristics

***REMOVED******REMOVED******REMOVED*** Classical Simulation

- **Speed**: Fast for small/medium problems (<10,000 variables)
- **Scaling**: O(n²) per sweep, linear in num_sweeps
- **Memory**: O(n²) for QUBO matrix
- **Quality**: Good, but not guaranteed optimal

***REMOVED******REMOVED******REMOVED*** D-Wave Quantum Hardware

- **Speed**: Very fast (microseconds for annealing)
- **Scaling**: Limited by hardware topology (~5000 variables)
- **Memory**: O(n²) for QUBO, but solved on hardware
- **Quality**: Good for well-structured problems

***REMOVED******REMOVED*** QUBO Formulation

The scheduling problem is encoded as:

```
minimize: x^T Q x

where:
- x is binary vector of assignments
- Q encodes constraints as penalties
```

**Constraint Penalties**:
- Hard constraints: 10,000 (must be satisfied)
- ACGME rules: 5,000 (compliance critical)
- Soft constraints: 100 (optimization targets)

**Example**:
```python
from app.scheduling.quantum import QUBOFormulation

formulation = QUBOFormulation(context)
Q = formulation.build()  ***REMOVED*** Sparse QUBO matrix

print(f"Variables: {formulation.num_variables}")
print(f"Non-zero terms: {len(Q)}")
```

***REMOVED******REMOVED*** Testing

Comprehensive tests with mock D-Wave:

```bash
pytest tests/quantum/test_quantum_solver_fallback.py -v
```

**Test Coverage**:
- ✓ Library availability detection
- ✓ Environment configuration
- ✓ Graceful fallback on missing libraries
- ✓ Graceful fallback on missing token
- ✓ Graceful fallback on connection errors
- ✓ Mock D-Wave quantum solver
- ✓ Classical simulation solver
- ✓ Error handling

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Issue: "D-Wave libraries not available"

**Solution**: Install D-Wave packages
```bash
pip install dwave-samplers  ***REMOVED*** For classical simulation
pip install dwave-system     ***REMOVED*** For quantum hardware
```

***REMOVED******REMOVED******REMOVED*** Issue: "D-Wave API token not provided"

**Solution**: Set environment variable
```bash
export DWAVE_API_TOKEN=your_token_here
```

Or configure in `.env`:
```bash
DWAVE_API_TOKEN=your_token_here
```

***REMOVED******REMOVED******REMOVED*** Issue: "Connection timeout"

**Solution**: Quantum solver automatically falls back to classical simulation. Check logs for details:
```python
import logging
logging.getLogger("app.scheduling.quantum").setLevel(logging.DEBUG)
```

***REMOVED******REMOVED******REMOVED*** Issue: Solver always uses classical mode

**Solution**: Check configuration
```python
from app.scheduling.quantum import get_quantum_solver_config
config = get_quantum_solver_config()
print(config)  ***REMOVED*** Debug configuration
```

***REMOVED******REMOVED*** API Reference

***REMOVED******REMOVED******REMOVED*** get_quantum_library_status()

Check which quantum libraries are installed.

```python
from app.scheduling.quantum import get_quantum_library_status

status = get_quantum_library_status()
***REMOVED*** Returns: {
***REMOVED***   "pyqubo": bool,
***REMOVED***   "dwave_samplers": bool,
***REMOVED***   "dwave_system": bool,
***REMOVED***   "qubovert": bool
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** get_quantum_solver_config()

Load configuration from environment.

```python
from app.scheduling.quantum import get_quantum_solver_config

config = get_quantum_solver_config()
***REMOVED*** Returns: {
***REMOVED***   "enabled": bool,
***REMOVED***   "backend": "classical" | "quantum",
***REMOVED***   "dwave_token": str | None,
***REMOVED***   "use_quantum_hardware": bool,
***REMOVED***   "libraries_available": dict
***REMOVED*** }
```

***REMOVED******REMOVED******REMOVED*** create_quantum_solver_from_env()

Create quantum solver from environment configuration.

```python
from app.scheduling.quantum import create_quantum_solver_from_env

solver = create_quantum_solver_from_env(
    constraint_manager=None,
    timeout_seconds=60.0
)
***REMOVED*** Returns: Solver instance or None if disabled
```

***REMOVED******REMOVED*** Contributing

When adding quantum solver features:

1. **Maintain graceful fallback**: Always provide classical fallback
2. **Test with mocks**: Use mock D-Wave for testing
3. **Document environment variables**: Update this README
4. **Log failures**: Use logger.warning() for fallback reasons
5. **Update tests**: Add tests to test_quantum_solver_fallback.py

***REMOVED******REMOVED*** References

- [PyQUBO Documentation](https://pyqubo.readthedocs.io/)
- [D-Wave Ocean SDK](https://docs.ocean.dwavesys.com/)
- [Nurse Scheduling via QUBO](https://arxiv.org/abs/2302.09459)
- [QUBO Formulations](https://arxiv.org/abs/2103.01708)

***REMOVED******REMOVED*** License

Same as parent project (Residency Scheduler).
