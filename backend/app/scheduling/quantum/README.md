# Quantum-Inspired Solvers for Residency Scheduling

## Overview

This module provides quantum-inspired optimization solvers that can run on classical hardware using simulated annealing, or optionally on D-Wave quantum hardware. The solvers use QUBO (Quadratic Unconstrained Binary Optimization) formulations to model the scheduling problem.

## Features

- **Graceful Fallback**: Automatically falls back to classical simulation if quantum hardware is unavailable
- **Environment-Based Configuration**: Easy configuration via environment variables
- **Multiple Backends**: Classical simulation (no dependencies) or D-Wave quantum hardware
- **Comprehensive Error Handling**: Handles missing libraries, invalid tokens, and service outages
- **Production-Ready**: Tested with mock D-Wave for reliability

## Quick Start

### Basic Usage (Classical Simulation)

```python
from app.scheduling.quantum import create_quantum_solver_from_env
from app.scheduling.constraints import SchedulingContext

# Create solver from environment configuration
solver = create_quantum_solver_from_env(timeout_seconds=60.0)

if solver:
    # Solve scheduling problem
    result = solver.solve(context)
    print(f"Found {len(result.assignments)} assignments")
    print(f"Solver used: {result.solver_status}")
else:
    # Quantum solver disabled - use classical solver
    from app.scheduling.solvers import SolverFactory
    solver = SolverFactory.create("cp_sat")
    result = solver.solve(context)
```

### Environment Configuration

```bash
# Enable quantum solver
export USE_QUANTUM_SOLVER=true

# Select backend: "classical" or "quantum"
export QUANTUM_SOLVER_BACKEND=classical

# For D-Wave quantum hardware (optional)
export DWAVE_API_TOKEN=your_api_token_here
```

## Available Solvers

### 1. SimulatedQuantumAnnealingSolver

**Best for**: General use, no dependencies required

Classical simulated annealing with quantum-inspired features:
- Quantum tunneling probability for escaping local minima
- Path-integral inspired temperature schedules
- Pure Python fallback (works without any quantum libraries)

```python
from app.scheduling.quantum import SimulatedQuantumAnnealingSolver

solver = SimulatedQuantumAnnealingSolver(
    timeout_seconds=60.0,
    num_reads=100,        # Number of independent annealing runs
    num_sweeps=1000,      # Number of sweeps per run
    beta_range=(0.1, 4.2) # Annealing schedule
)

result = solver.solve(context)
```

### 2. QuantumInspiredSolver

**Best for**: Production use with automatic backend selection

Hybrid solver that automatically selects the best approach:
- Small problems: Classical simulated annealing
- Medium/large problems: Optimized simulated annealing
- D-Wave available: Quantum hardware for subproblems

```python
from app.scheduling.quantum import QuantumInspiredSolver

# Automatic backend selection
solver = QuantumInspiredSolver(
    use_quantum_hardware=False,  # True to enable D-Wave
    dwave_token=None             # D-Wave API token
)

result = solver.solve(context)
print(f"Backend used: {result.statistics['backend']}")
```

### 3. QUBOSolver

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
    use_tabu=False  # True for tabu search
)

result = solver.solve(context)
```

## Installation

### Classical Mode (No Dependencies)

The quantum solvers work out-of-the-box with pure Python fallback. No additional installation required.

### Enhanced Classical Mode

For better performance, install D-Wave samplers:

```bash
pip install dwave-samplers
```

### Quantum Hardware Mode

To use D-Wave quantum annealing hardware:

```bash
pip install dwave-system dwave-samplers
```

### PyQUBO Support

For the QUBOSolver:

```bash
pip install pyqubo
```

## Environment Configuration Reference

### Required Variables

None - all quantum solver features are optional.

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_QUANTUM_SOLVER` | `false` | Enable quantum solver |
| `QUANTUM_SOLVER_BACKEND` | `classical` | Backend type: `classical` or `quantum` |
| `DWAVE_API_TOKEN` | None | D-Wave API token for quantum hardware |

### Configuration Examples

#### Development (Classical Simulation)

```bash
USE_QUANTUM_SOLVER=true
QUANTUM_SOLVER_BACKEND=classical
```

#### Production (D-Wave Quantum Hardware)

```bash
USE_QUANTUM_SOLVER=true
QUANTUM_SOLVER_BACKEND=quantum
DWAVE_API_TOKEN=your_token_here
```

## Graceful Fallback Behavior

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

## Usage in Production

### Via SolverFactory

```python
from app.scheduling.solvers import SolverFactory

# Create quantum solver from registry
solver = SolverFactory.create("quantum", timeout_seconds=120.0)
result = solver.solve(context)
```

### Via Environment Helper

```python
from app.scheduling.quantum import create_quantum_solver_from_env

# Automatically configured from environment
solver = create_quantum_solver_from_env(timeout_seconds=120.0)

if solver:
    result = solver.solve(context)
else:
    # Quantum disabled - use classical solver
    solver = SolverFactory.create("cp_sat")
    result = solver.solve(context)
```

### Checking Configuration

```python
from app.scheduling.quantum import get_quantum_solver_config

config = get_quantum_solver_config()
print(f"Enabled: {config['enabled']}")
print(f"Backend: {config['backend']}")
print(f"Use quantum hardware: {config['use_quantum_hardware']}")
print(f"Libraries: {config['libraries_available']}")
```

## Performance Characteristics

### Classical Simulation

- **Speed**: Fast for small/medium problems (<10,000 variables)
- **Scaling**: O(n²) per sweep, linear in num_sweeps
- **Memory**: O(n²) for QUBO matrix
- **Quality**: Good, but not guaranteed optimal

### D-Wave Quantum Hardware

- **Speed**: Very fast (microseconds for annealing)
- **Scaling**: Limited by hardware topology (~5000 variables)
- **Memory**: O(n²) for QUBO, but solved on hardware
- **Quality**: Good for well-structured problems

## QUBO Formulation

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
Q = formulation.build()  # Sparse QUBO matrix

print(f"Variables: {formulation.num_variables}")
print(f"Non-zero terms: {len(Q)}")
```

## Testing

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

## Troubleshooting

### Issue: "D-Wave libraries not available"

**Solution**: Install D-Wave packages
```bash
pip install dwave-samplers  # For classical simulation
pip install dwave-system     # For quantum hardware
```

### Issue: "D-Wave API token not provided"

**Solution**: Set environment variable
```bash
export DWAVE_API_TOKEN=your_token_here
```

Or configure in `.env`:
```bash
DWAVE_API_TOKEN=your_token_here
```

### Issue: "Connection timeout"

**Solution**: Quantum solver automatically falls back to classical simulation. Check logs for details:
```python
import logging
logging.getLogger("app.scheduling.quantum").setLevel(logging.DEBUG)
```

### Issue: Solver always uses classical mode

**Solution**: Check configuration
```python
from app.scheduling.quantum import get_quantum_solver_config
config = get_quantum_solver_config()
print(config)  # Debug configuration
```

## API Reference

### get_quantum_library_status()

Check which quantum libraries are installed.

```python
from app.scheduling.quantum import get_quantum_library_status

status = get_quantum_library_status()
# Returns: {
#   "pyqubo": bool,
#   "dwave_samplers": bool,
#   "dwave_system": bool,
#   "qubovert": bool
# }
```

### get_quantum_solver_config()

Load configuration from environment.

```python
from app.scheduling.quantum import get_quantum_solver_config

config = get_quantum_solver_config()
# Returns: {
#   "enabled": bool,
#   "backend": "classical" | "quantum",
#   "dwave_token": str | None,
#   "use_quantum_hardware": bool,
#   "libraries_available": dict
# }
```

### create_quantum_solver_from_env()

Create quantum solver from environment configuration.

```python
from app.scheduling.quantum import create_quantum_solver_from_env

solver = create_quantum_solver_from_env(
    constraint_manager=None,
    timeout_seconds=60.0
)
# Returns: Solver instance or None if disabled
```

## Contributing

When adding quantum solver features:

1. **Maintain graceful fallback**: Always provide classical fallback
2. **Test with mocks**: Use mock D-Wave for testing
3. **Document environment variables**: Update this README
4. **Log failures**: Use logger.warning() for fallback reasons
5. **Update tests**: Add tests to test_quantum_solver_fallback.py

## References

- [PyQUBO Documentation](https://pyqubo.readthedocs.io/)
- [D-Wave Ocean SDK](https://docs.ocean.dwavesys.com/)
- [Nurse Scheduling via QUBO](https://arxiv.org/abs/2302.09459)
- [QUBO Formulations](https://arxiv.org/abs/2103.01708)

## License

Same as parent project (Residency Scheduler).
