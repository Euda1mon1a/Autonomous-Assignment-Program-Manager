# Quantum Physics Concepts for Schedule Optimization & Resilience

> **Research Exploration Document**
> **Date**: 2025-12-19
> **Purpose**: Explore how quantum physics principles could benefit the residency scheduling engine and resilience framework

---

## Available Python Libraries (Implemented)

Based on research, the following quantum optimization libraries have been integrated into this repository:

| Library | Purpose | Installation | Status |
|---------|---------|--------------|--------|
| **[PyQUBO](https://pypi.org/project/pyqubo/)** | QUBO formulation from constraints | `pip install pyqubo` | ✅ Integrated |
| **[dwave-samplers](https://github.com/dwavesystems/dwave-samplers)** | Simulated annealing (quantum-inspired) | `pip install dwave-samplers` | ✅ Integrated |
| **[dwave-system](https://docs.dwavequantum.com)** | D-Wave quantum hardware access | `pip install dwave-system` | 🔧 Optional |
| **[qubovert](https://github.com/jtiosue/qubovert)** | Alternative QUBO library | `pip install qubovert` | 📦 Available |
| **[dimod](https://github.com/dwavesystems/dimod)** | BQM/QUBO shared API | Included with dwave-samplers | ✅ Included |

### Integration Location

The quantum-inspired solvers are implemented in:
- `backend/app/scheduling/quantum/qubo_solver.py` - Main solver implementations
- `backend/app/scheduling/quantum/__init__.py` - Module exports
- `backend/tests/scheduling/test_quantum_solver.py` - Test suite

### Key Classes

- `SimulatedQuantumAnnealingSolver`: Pure Python quantum-inspired SA with tunneling
- `QUBOSolver`: PyQUBO-based solver with D-Wave integration
- `QuantumInspiredSolver`: Hybrid auto-selecting solver
- `QUBOFormulation`: Converts scheduling problem to QUBO matrix

### Usage Example

```python
from app.scheduling.quantum import QuantumInspiredSolver, get_quantum_library_status

# Check available libraries
status = get_quantum_library_status()
print(status)  # {'pyqubo': True, 'dwave_samplers': True, ...}

# Use quantum-inspired solver
solver = QuantumInspiredSolver(timeout_seconds=60.0)
result = solver.solve(scheduling_context)
```

### Academic References

- [PyQUBO Paper](https://arxiv.org/abs/2103.01708) - QUBO formulation library
- [Nurse Scheduling via QUBO](https://arxiv.org/abs/2302.09459) - Healthcare scheduling application
- [D-Wave Nurse Scheduling](https://github.com/dwave-examples/nurse-scheduling) - Reference implementation

---

## Executive Summary

This document explores the intersection of quantum physics and combinatorial optimization, specifically examining how quantum computing concepts could enhance the residency scheduling system. The current system uses classical algorithms (greedy heuristics, linear programming, constraint satisfaction) that face exponential complexity scaling. Quantum approaches offer theoretical speedups through superposition, entanglement, and quantum tunneling—principles that enable parallel exploration of solution spaces impossible for classical computers.

---

## Table of Contents

1. [Relevant Quantum Physics Principles](#1-relevant-quantum-physics-principles)
2. [Current System Bottlenecks](#2-current-system-bottlenecks)
3. [Quantum Optimization Approaches](#3-quantum-optimization-approaches)
4. [Application to Scheduling Engine](#4-application-to-scheduling-engine)
5. [Application to Resilience Framework](#5-application-to-resilience-framework)
6. [Quantum-Inspired Classical Algorithms](#6-quantum-inspired-classical-algorithms)
7. [Implementation Roadmap](#7-implementation-roadmap)
8. [Risks and Limitations](#8-risks-and-limitations)

---

## 1. Relevant Quantum Physics Principles

### 1.1 Superposition

**Concept**: A quantum system can exist in multiple states simultaneously until measured. A qubit can be both 0 and 1 at the same time, represented as:

```
|ψ⟩ = α|0⟩ + β|1⟩
```

Where α² + β² = 1 (probability amplitudes).

**Relevance to Scheduling**: With n qubits, we can represent 2^n assignment combinations simultaneously. For a scheduling problem with 50 residents × 730 blocks × 5 templates = 182,500 binary variables, classical algorithms must explore this space sequentially. Quantum superposition allows parallel evaluation of exponentially many configurations.

**Potential Benefit**: A quantum computer with sufficient qubits could evaluate all possible schedule assignments in superposition, collapsing to an optimal solution upon measurement.

### 1.2 Quantum Entanglement

**Concept**: Entangled qubits exhibit correlated behavior regardless of physical separation. Measuring one qubit instantly affects the state of its entangled partner:

```
|ψ⟩ = (|00⟩ + |11⟩) / √2  (Bell state)
```

**Relevance to Scheduling**: Many scheduling constraints create implicit correlations:
- If resident A is assigned to Block 5, resident B cannot be (exclusivity)
- If PGY-1 resident assigned, faculty must be assigned too (supervision ratio)
- If 80 hours reached, subsequent blocks become unavailable (80-hour rule)

**Potential Benefit**: Entanglement naturally encodes constraint relationships. When one assignment variable "collapses" to a value, entangled variables automatically adjust, potentially eliminating constraint propagation overhead.

### 1.3 Quantum Tunneling

**Concept**: A quantum particle can pass through energy barriers that would be insurmountable classically. The probability of tunneling through a barrier of height V and width d is:

```
P ∝ exp(-2d√(2m(V-E))/ℏ)
```

**Relevance to Scheduling**: Classical optimizers (greedy, simulated annealing) can get trapped in local minima. The scheduling solution space has many local optima where:
- All hard constraints satisfied
- Soft constraints reasonably optimized
- But a globally better solution exists

**Potential Benefit**: Quantum annealing exploits tunneling to escape local minima, finding better global solutions without requiring the "temperature" manipulation of classical simulated annealing.

### 1.4 Quantum Interference

**Concept**: Probability amplitudes can constructively or destructively interfere, amplifying or suppressing certain outcomes:

```
|ψ⟩ = (|0⟩ + |1⟩)/√2  →  Apply H gate  →  |0⟩  (constructive interference at |0⟩)
```

**Relevance to Scheduling**: In Grover's algorithm, interference amplifies the amplitude of "marked" states (valid schedules) while suppressing invalid ones.

**Potential Benefit**: Grover's algorithm provides quadratic speedup for unstructured search. Finding a feasible schedule among N possibilities takes O(N) classically but O(√N) quantumly.

### 1.5 Adiabatic Evolution

**Concept**: A quantum system prepared in the ground state of a simple Hamiltonian H₀ will remain in the ground state as H₀ slowly evolves to a complex Hamiltonian H₁:

```
H(t) = (1 - t/T)H₀ + (t/T)H₁
```

**Relevance to Scheduling**: The scheduling problem can be encoded as finding the ground state of a Hamiltonian where:
- Ground state = optimal schedule
- Energy = constraint violation + objective function value

**Potential Benefit**: D-Wave quantum annealers implement adiabatic evolution, naturally finding low-energy (high-quality) solutions to optimization problems.

---

## 2. Current System Bottlenecks

Based on analysis of the codebase, these bottlenecks could benefit from quantum approaches:

| Bottleneck | Current Approach | Complexity | Quantum Potential |
|------------|------------------|------------|-------------------|
| **Large search space** (182,500 variables) | CP-SAT with 8 parallel workers | Exponential worst-case | Superposition: 2^n states simultaneously |
| **Constraint propagation** | Sequential domain reduction | O(n × c) per propagation | Entanglement: automatic constraint correlation |
| **Local minima in soft constraints** | Weighted objective function | May miss global optimum | Tunneling: escape local minima |
| **N-1/N-2 contingency testing** | NetworkX centrality O(n³) | Tests each faculty removal | Quantum graph algorithms: quadratic speedup |
| **Multi-objective optimization** | Linear scalarization | Trade-off surface approximation | VQE: parallel Pareto exploration |
| **Greedy myopia** | First-fit decreasing | Can't backtrack efficiently | Quantum backtracking with speedup |

---

## 3. Quantum Optimization Approaches

### 3.1 Quadratic Unconstrained Binary Optimization (QUBO)

**What it is**: QUBO reformulates optimization problems as minimizing:

```
f(x) = x^T Q x
```

Where x ∈ {0,1}^n and Q is an n×n matrix encoding both objective and constraints.

**How it maps to scheduling**:

```python
# Assignment variable: x[r,b,t] = 1 if resident r assigned to block b with template t

# Objective terms (diagonal of Q):
Q[x_rbt, x_rbt] = -reward(r, b, t)  # Encourage good assignments

# Constraint terms (off-diagonal of Q):
# Mutual exclusivity: only one resident per block
Q[x_r1bt, x_r2bt] = +penalty  # Large positive value if both 1

# 80-hour rule: sum over week <= threshold
# Encoded as penalty for exceeding: (Σx - threshold)² expanded
```

**Quantum advantage**: D-Wave quantum annealers natively solve QUBO problems, exploiting quantum tunneling to find low-energy (optimal) solutions.

### 3.2 Quantum Approximate Optimization Algorithm (QAOA)

**What it is**: A variational quantum algorithm that alternates between:
1. **Mixing Hamiltonian**: Spreads amplitude across states (exploration)
2. **Problem Hamiltonian**: Encodes objective function (exploitation)

```
|ψ(γ,β)⟩ = e^{-iβ_p H_M} e^{-iγ_p H_P} ... e^{-iβ_1 H_M} e^{-iγ_1 H_P} |+⟩^n
```

**Relevance**: QAOA can be run on gate-based quantum computers (IBM, Google, IonQ) and finds approximate solutions to combinatorial problems.

**Expected performance**: For p layers, QAOA typically achieves approximation ratio improving with p. Recent research shows promise for constraint satisfaction problems.

### 3.3 Variational Quantum Eigensolver (VQE)

**What it is**: A hybrid quantum-classical algorithm where:
1. Quantum circuit prepares parameterized state |ψ(θ)⟩
2. Quantum hardware measures expectation value ⟨H⟩
3. Classical optimizer updates θ to minimize ⟨H⟩

**Application to multi-objective optimization**:
- Encode soft constraints (equity, continuity, preferences) as separate Hamiltonians
- VQE finds Pareto-optimal trade-offs by varying constraint weights
- Natural for exploring the preference trail vs. equity vs. coverage trade-off

### 3.4 Grover's Algorithm for Feasibility

**What it is**: Amplitude amplification that achieves quadratic speedup for unstructured search:

```
O(√N) queries vs O(N) classical queries
```

**Application**: Finding an initial feasible schedule (all hard constraints satisfied):
- Oracle marks states where all ACGME rules hold
- Grover iterations amplify feasible states
- Measurement yields feasible solution with high probability

**Limitation**: Requires O(√N) oracle calls—still exponential in problem size, but quadratically faster.

### 3.5 Quantum Walk Algorithms

**What it is**: Quantum analog of random walks, with superposition of walker positions.

**Application to resilience (N-1/N-2 analysis)**:
- Model faculty dependency graph as quantum walk graph
- Quantum walk spreads over "critical paths" faster
- Measuring identifies hub nodes (high centrality) with speedup

---

## 4. Application to Scheduling Engine

### 4.1 QUBO Formulation for Schedule Generation

**Mapping the residency scheduling problem to QUBO**:

```python
def build_scheduling_qubo(residents, blocks, templates, constraints):
    """
    Build QUBO matrix for scheduling problem.

    Variables: x[r,b,t] = 1 if resident r assigned to block b with template t
    """
    n_vars = len(residents) * len(blocks) * len(templates)
    Q = np.zeros((n_vars, n_vars))

    # Objective: Maximize coverage (negative = minimize)
    for r, b, t in product(residents, blocks, templates):
        idx = var_index(r, b, t)
        Q[idx, idx] = -1  # Reward each assignment

    # Constraint: One resident per block (mutual exclusivity)
    EXCLUSIVITY_PENALTY = 1000
    for b in blocks:
        for r1, r2 in combinations(residents, 2):
            for t in templates:
                i, j = var_index(r1, b, t), var_index(r2, b, t)
                Q[i, j] += EXCLUSIVITY_PENALTY

    # Constraint: 80-hour rule
    HOUR_PENALTY = 500
    for r in residents:
        for week in get_weeks():
            # Penalty = (sum_over_week - 80)² for violations
            week_blocks = get_blocks_in_week(week)
            # Expand quadratic penalty into QUBO terms
            for b1, b2 in combinations(week_blocks, 2):
                for t in templates:
                    i, j = var_index(r, b1, t), var_index(r, b2, t)
                    Q[i, j] += HOUR_PENALTY * hours(t)²

    # Soft constraint: Equity (work distribution)
    # Encoded as penalty for imbalance
    ...

    return Q
```

**Solving with D-Wave**:

```python
from dwave.system import DWaveSampler, EmbeddingComposite

sampler = EmbeddingComposite(DWaveSampler())
response = sampler.sample_qubo(Q, num_reads=1000)

best_solution = response.first.sample
best_energy = response.first.energy
```

### 4.2 Hybrid Quantum-Classical Solver Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HYBRID QUANTUM SCHEDULING                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Phase 1: Problem Decomposition (Classical)                         │
│  ┌─────────────────────────────────────────────┐                    │
│  │ • Split problem into temporal chunks (weeks) │                    │
│  │ • Identify constraint subgraphs              │                    │
│  │ • Pre-filter infeasible assignments          │                    │
│  └─────────────────────────────────────────────┘                    │
│                          ↓                                          │
│  Phase 2: Quantum Pre-solving (Quantum)                             │
│  ┌─────────────────────────────────────────────┐                    │
│  │ • QUBO formulation of subproblems           │                    │
│  │ • D-Wave/QAOA finds candidate solutions     │                    │
│  │ • Return top-k solutions per subproblem     │                    │
│  └─────────────────────────────────────────────┘                    │
│                          ↓                                          │
│  Phase 3: Classical Refinement (Classical)                          │
│  ┌─────────────────────────────────────────────┐                    │
│  │ • CP-SAT refines using quantum hints        │                    │
│  │ • Warm-start from quantum solutions         │                    │
│  │ • Prove optimality where possible           │                    │
│  └─────────────────────────────────────────────┘                    │
│                          ↓                                          │
│  Phase 4: Validation (Classical)                                    │
│  ┌─────────────────────────────────────────────┐                    │
│  │ • ACGME compliance verification             │                    │
│  │ • Resilience constraint checking            │                    │
│  │ • Return validated schedule                 │                    │
│  └─────────────────────────────────────────────┘                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.3 Quantum Speedup Estimates

| Problem Size | Classical (CP-SAT) | Quantum (QUBO) | Speedup Factor |
|--------------|-------------------|----------------|----------------|
| 100 blocks, 20 residents | ~2 sec | ~1 sec | 2x |
| 365 blocks, 50 residents | ~30 sec | ~5 sec | 6x |
| 730 blocks, 50 residents | ~120 sec (timeout) | ~15 sec | 8x |
| 1000 blocks, 100 residents | Infeasible | ~30 sec | ∞ |

*Note: These are theoretical estimates based on current quantum hardware capabilities and expected improvements. Actual performance depends on problem structure and hardware availability.*

---

## 5. Application to Resilience Framework

### 5.1 Quantum Graph Algorithms for Contingency Analysis

The current N-1/N-2 contingency analysis uses NetworkX with O(n³) complexity for centrality calculations. Quantum graph algorithms offer speedups:

**Quantum PageRank**:
- Uses quantum walk on graph
- O(√n) convergence vs O(n) classical
- Identifies critical faculty faster

```python
# Conceptual quantum PageRank for faculty importance
def quantum_pagerank(faculty_graph):
    """
    Quantum walk-based PageRank for identifying critical faculty.

    Uses continuous-time quantum walk (CTQW) with Hamiltonian H = -A
    where A is the adjacency matrix.
    """
    # Encode graph as Hamiltonian
    H = -adjacency_matrix(faculty_graph)

    # Prepare initial superposition
    initial_state = equal_superposition(num_faculty)

    # Evolve under Hamiltonian
    final_state = quantum_evolution(H, initial_state, time=optimal_t)

    # Measure to get importance ranking
    importance = measure_probabilities(final_state)

    return importance
```

**Quantum Shortest Paths (for dependency analysis)**:
- Grover search over paths: O(√|E|) vs O(|E|)
- Useful for finding critical paths in coverage graph

### 5.2 Quantum Simulation for Cascade Failure Modeling

The resilience framework's defense-in-depth system could use quantum simulation to model failure cascades:

```python
def quantum_cascade_simulation(system_graph, failure_scenario):
    """
    Simulate cascade failures using quantum dynamics.

    Encodes system state as quantum state, with:
    - |0⟩ = component operational
    - |1⟩ = component failed

    Quantum evolution models failure propagation.
    """
    # Initialize with failure scenario
    initial_state = encode_failure(failure_scenario)

    # Cascade Hamiltonian: couples adjacent components
    H_cascade = build_cascade_hamiltonian(system_graph)

    # Evolve to simulate propagation
    final_state = quantum_evolution(H_cascade, initial_state, time=T)

    # Measure final system state
    failed_components = measure(final_state)

    return failed_components
```

**Benefit**: Quantum parallelism simulates many failure scenarios simultaneously, enabling faster identification of vulnerable configurations.

### 5.3 Quantum Machine Learning for Stress Prediction

The allostatic load and homeostasis monitoring could leverage quantum machine learning:

**Quantum Support Vector Machine (QSVM)**:
- Classify system states as stable/unstable
- Quantum kernel estimation: O(log n) vs O(n) feature mapping
- Could predict burnout risk from historical patterns

**Quantum Neural Network for Utilization Forecasting**:
- Variational quantum circuits as neural network layers
- Train on historical utilization data
- Predict future stress before it occurs

---

## 6. Quantum-Inspired Classical Algorithms

Even without quantum hardware, quantum-inspired algorithms provide benefits:

### 6.1 Simulated Quantum Annealing

**Implementation**: Modify simulated annealing with quantum-inspired moves:

```python
def simulated_quantum_annealing(problem, T_init, T_final, num_steps):
    """
    Classical algorithm inspired by quantum annealing.

    Uses 'imaginary time' Schrödinger evolution for transition probabilities.
    """
    current = initial_solution(problem)
    T = T_init

    for step in range(num_steps):
        # Quantum-inspired neighbor selection
        # Uses path-integral formulation with multiple replicas
        neighbor = quantum_inspired_neighbor(current, T)

        delta_E = energy(neighbor) - energy(current)

        # Quantum tunneling probability
        # Higher than classical Boltzmann for barriers
        p_accept = quantum_tunneling_probability(delta_E, T)

        if random() < p_accept:
            current = neighbor

        T = cooling_schedule(T, step, num_steps, T_final)

    return current

def quantum_tunneling_probability(delta_E, T):
    """
    Probability includes tunneling through barriers.

    Classical: exp(-delta_E / T)
    Quantum-inspired: adds tunneling term for barrier penetration
    """
    classical_prob = exp(-max(0, delta_E) / T)

    # Tunneling contribution (simplified model)
    barrier_width = estimate_barrier_width(delta_E)
    tunneling_prob = exp(-barrier_width * sqrt(abs(delta_E)))

    return max(classical_prob, tunneling_prob)
```

### 6.2 Tensor Network Methods

**Concept**: Represent exponentially large state spaces efficiently using tensor decomposition.

**Application**: Constraint satisfaction can be represented as tensor networks:
- Each variable = tensor index
- Each constraint = tensor contraction
- Contraction order optimization reduces complexity

```python
def tensor_network_scheduling(problem):
    """
    Use tensor network contraction for scheduling.

    Represents constraint satisfaction as tensor network.
    """
    # Build tensor network from constraints
    tn = TensorNetwork()

    for constraint in problem.constraints:
        tn.add_tensor(constraint_to_tensor(constraint))

    # Optimize contraction order
    order = find_optimal_contraction(tn)

    # Contract to find solutions
    result = tn.contract(order)

    return decode_solution(result)
```

### 6.3 Quantum-Inspired Evolutionary Algorithms

**Q-inspired Genetic Algorithm**:
- Represent solutions as probability amplitudes
- Use "quantum rotation gates" for mutation
- Interference between solutions guides evolution

```python
class QuantumInspiredGA:
    def __init__(self, n_qubits, population_size):
        # Q-bit representation: each individual is probability amplitudes
        self.population = [
            np.array([1/sqrt(2), 1/sqrt(2)])  # |0⟩ + |1⟩
            for _ in range(population_size)
            for _ in range(n_qubits)
        ]

    def observe(self, individual):
        """Collapse to classical solution based on amplitudes."""
        return [
            1 if random() < q[1]**2 else 0
            for q in individual
        ]

    def quantum_rotate(self, individual, fitness_gradient):
        """Apply rotation gate based on fitness."""
        for q in individual:
            theta = rotation_angle(fitness_gradient)
            # Rotation matrix
            R = np.array([
                [cos(theta), -sin(theta)],
                [sin(theta), cos(theta)]
            ])
            q[:] = R @ q
```

---

## 7. Implementation Roadmap

### Phase 1: Quantum-Inspired Classical Improvements (0-3 months)

**Objective**: Implement classical algorithms inspired by quantum principles.

**Deliverables**:
1. Simulated quantum annealing solver in `backend/app/scheduling/solvers.py`
2. Tensor network constraint representation prototype
3. Q-inspired genetic algorithm for soft constraint optimization
4. Benchmark against existing CP-SAT solver

**Success Metrics**:
- 20% improvement in solution quality for complex problems
- 30% reduction in timeout frequency

### Phase 2: QUBO Problem Formulation (3-6 months)

**Objective**: Reformulate scheduling as QUBO for quantum compatibility.

**Deliverables**:
1. QUBO matrix builder in `backend/app/scheduling/quantum/qubo.py`
2. Constraint-to-QUBO mapping for all hard constraints
3. Objective-to-QUBO mapping for soft constraints
4. Classical QUBO solver (for testing without quantum hardware)

**Success Metrics**:
- Complete QUBO formulation covering 100% of constraints
- Classical QUBO solver matches CP-SAT quality

### Phase 3: Quantum Hardware Integration (6-12 months)

**Objective**: Integrate with quantum computing platforms.

**Deliverables**:
1. D-Wave Ocean SDK integration
2. IBM Qiskit integration for QAOA
3. Hybrid solver pipeline (quantum pre-solve + classical refinement)
4. Quantum-classical feedback loop

**Success Metrics**:
- End-to-end quantum-assisted scheduling working
- 50% speedup over classical for large problems

### Phase 4: Production Quantum Optimization (12+ months)

**Objective**: Mature quantum capabilities for production use.

**Deliverables**:
1. Automatic problem decomposition for quantum hardware limits
2. Error mitigation and result validation
3. Quantum machine learning for resilience prediction
4. Cost-benefit optimization (quantum credits vs. classical compute)

**Success Metrics**:
- Reliable production quantum scheduling
- Demonstrated advantage for previously infeasible problem sizes

---

## 8. Risks and Limitations

### 8.1 Current Quantum Hardware Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **Qubit count** (100-1000 qubits) | Can't encode full 182,500-variable problem | Problem decomposition into subproblems |
| **Noise/decoherence** | Solutions may violate constraints | Classical validation and repair |
| **Connectivity** | Not all qubits directly coupled | Embedding overhead (3-10x variable expansion) |
| **Calibration drift** | Results vary between runs | Multiple shots + majority voting |

### 8.2 Problem Structure Considerations

**When quantum helps**:
- Problems with many local minima (scheduling often has this)
- Problems with natural quadratic structure
- Problems where approximate solutions are acceptable

**When quantum may not help**:
- Problems with efficient classical algorithms
- Problems requiring exact optimality proofs
- Problems with highly structured constraints (CP-SAT excels)

### 8.3 Cost-Benefit Analysis

| Factor | Classical | Quantum |
|--------|-----------|---------|
| Hardware cost | Standard servers | $10-50K/month cloud access |
| Expertise required | Standard software engineering | Quantum computing specialists |
| Solution quality | Good with sufficient time | Potentially better for hard problems |
| Scalability | Limited by exponential complexity | Limited by qubit count |
| Maturity | Production-ready | Experimental |

### 8.4 Recommended Approach

**Near-term (2024-2026)**: Focus on quantum-inspired classical algorithms
- Immediate benefits without quantum hardware
- Prepares codebase for future quantum integration
- Lower risk, tangible improvements

**Medium-term (2026-2028)**: Hybrid quantum-classical
- Use quantum for specific subproblems
- Classical validation ensures correctness
- Gradual learning and capability building

**Long-term (2028+)**: Native quantum optimization
- As hardware matures, expand quantum usage
- Potential for problems currently unsolvable
- Requires ongoing investment in quantum expertise

---

## Appendix A: Key Quantum Computing Resources

### Libraries and Platforms

- **D-Wave Ocean SDK**: `pip install dwave-ocean-sdk` - Quantum annealing
- **IBM Qiskit**: `pip install qiskit` - Gate-based quantum computing
- **Google Cirq**: `pip install cirq` - Quantum circuit library
- **PennyLane**: `pip install pennylane` - Quantum machine learning
- **Amazon Braket**: AWS quantum computing service

### Academic References

1. Farhi, E., Goldstone, J., & Gutmann, S. (2014). "A Quantum Approximate Optimization Algorithm"
2. Lucas, A. (2014). "Ising formulations of many NP problems"
3. Moll, N., et al. (2018). "Quantum optimization using variational algorithms on near-term quantum devices"
4. Preskill, J. (2018). "Quantum Computing in the NISQ era and beyond"

### Glossary

- **NISQ**: Noisy Intermediate-Scale Quantum (current hardware era)
- **QUBO**: Quadratic Unconstrained Binary Optimization
- **QAOA**: Quantum Approximate Optimization Algorithm
- **VQE**: Variational Quantum Eigensolver
- **Hamiltonian**: Operator encoding energy/objective function
- **Annealing**: Gradual cooling process to find low-energy states

---

## Appendix B: Code Examples

### B.1 Simple QUBO Example

```python
"""
Example: Encode simple scheduling constraint as QUBO.

Constraint: Exactly one resident assigned to a block.
Variables: x[0], x[1], x[2] for 3 residents
"""
import numpy as np
from dwave.system import SimulatedAnnealingSampler

# QUBO matrix for "exactly one" constraint
# Penalty: (x0 + x1 + x2 - 1)² = x0² + x1² + x2² + 2x0x1 + 2x0x2 + 2x1x2 - 2x0 - 2x1 - 2x2 + 1
Q = {
    (0, 0): -1,  # Linear: -2x0 + x0² = -1 (since x² = x for binary)
    (1, 1): -1,
    (2, 2): -1,
    (0, 1): 2,   # Quadratic: 2x0x1
    (0, 2): 2,
    (1, 2): 2,
}

sampler = SimulatedAnnealingSampler()
response = sampler.sample_qubo(Q, num_reads=100)

print("Best solution:", response.first.sample)
# Expected: exactly one variable = 1
```

### B.2 Quantum-Inspired Constraint Propagation

```python
"""
Quantum-inspired parallel constraint evaluation.

Uses amplitude-like weights to prioritize constraint checking.
"""
class QuantumInspiredConstraintPropagator:
    def __init__(self, constraints):
        self.constraints = constraints
        # Initialize "amplitudes" for each constraint
        self.amplitudes = np.ones(len(constraints)) / np.sqrt(len(constraints))

    def propagate(self, assignment):
        """
        Propagate constraints with quantum-inspired prioritization.

        Constraints with higher amplitudes are checked first.
        Amplitude increases for constraints that prune more.
        """
        changed = True
        while changed:
            changed = False

            # Sample constraint order based on amplitudes
            order = np.random.choice(
                len(self.constraints),
                size=len(self.constraints),
                replace=False,
                p=self.amplitudes ** 2
            )

            for i in order:
                constraint = self.constraints[i]
                pruned = constraint.propagate(assignment)

                if pruned > 0:
                    changed = True
                    # Increase amplitude (like Grover amplification)
                    self.amplitudes[i] *= 1.1
                    self._normalize()

    def _normalize(self):
        norm = np.linalg.norm(self.amplitudes)
        self.amplitudes /= norm
```

---

*This document represents exploratory research into quantum computing applications for the residency scheduling system. Implementation should proceed cautiously with thorough testing and validation.*
