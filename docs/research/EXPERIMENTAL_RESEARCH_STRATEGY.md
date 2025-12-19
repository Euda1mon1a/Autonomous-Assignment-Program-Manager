# Experimental Research Strategy

> **Created:** 2025-12-19
> **Purpose:** Define isolation strategy for novel scheduling algorithms
> **Status:** Active Research

---

## Overview

This repository contains three novel algorithmic approaches to scheduling optimization, each inspired by different scientific domains. These are **research-grade implementations** that require rigorous validation before any production consideration.

### Research Branches

| Branch | Inspiration | Status |
|--------|-------------|--------|
| `claude/quantum-physics-scheduler-*` | Quantum annealing / QUBO | Experimental |
| `claude/catalyst-concepts-research-*` | Chemical kinetics | Experimental |
| `claude/transcription-factors-scheduler-*` | Gene regulatory networks | Experimental |

---

## Isolation Principles

### 1. No Contamination of Core Paths

Experimental code **must never** be imported by production code paths. The isolation is enforced by:

- Keeping research on separate git branches
- Using conditional imports behind feature flags
- Plugin architecture for solver registration

### 2. Shadow Mode Validation

Before any integration, experimental solvers run in **shadow mode**:

```
Production Request → [Production Solver] → Production Result (returned)
                  ↘ [Experimental Solver] → Shadow Result (logged only)
```

Shadow results are compared offline without affecting users.

### 3. Defined Success Criteria

Each experimental approach must demonstrate measurable improvement:

| Approach | Success Metric | Threshold |
|----------|---------------|-----------|
| QUBO Solver | Solution quality vs CP-SAT | ≥95% quality in ≤50% time |
| Catalyst Pathways | Swap success rate | >90% valid transitions |
| Transcription Factors | Constraint satisfaction under stress | Graceful degradation at 120% load |

---

## Test Harness Architecture

```
backend/
├── experimental/                    # Experimental test harness (gitignored from main)
│   ├── __init__.py
│   ├── harness.py                   # Main test harness runner
│   ├── benchmarks/
│   │   ├── solver_comparison.py     # Compare solver outputs
│   │   ├── pathway_validation.py    # Validate transition pathways
│   │   └── stress_testing.py        # Constraint stress tests
│   ├── fixtures/
│   │   ├── scheduling_scenarios.json
│   │   └── stress_scenarios.json
│   └── reports/                     # Generated comparison reports
│       └── .gitkeep
```

### Running the Harness

```bash
# From backend directory
python -m experimental.harness --branch quantum-physics --scenario standard
python -m experimental.harness --branch catalyst-concepts --scenario swap-heavy
python -m experimental.harness --branch transcription-factors --scenario crisis-mode
python -m experimental.harness --compare-all --output reports/comparison.json
```

---

## Branch Integration Protocol

### Phase 1: Isolated Testing (Current)
- Research continues on separate branches
- Test harness validates against production baseline
- No code touches main branch

### Phase 2: Plugin Integration
When success criteria met:
1. Extract stable interfaces from experimental code
2. Create plugin entry points in production
3. Gate behind `EXPERIMENTAL_SOLVERS_ENABLED=false` (default off)

### Phase 3: Shadow Mode
1. Enable in staging environment only
2. Log all shadow results to dedicated analytics
3. Monitor for 2+ weeks with production-like load

### Phase 4: Gradual Rollout
1. Enable for specific scenarios (e.g., only swap operations)
2. A/B test with 5% of requests
3. Expand based on metrics

---

## Scientific Foundations

### Quantum-Inspired (QUBO)

**Principle:** Quadratic Unconstrained Binary Optimization formulates scheduling as energy minimization.

**Why it might work:**
- Scheduling naturally maps to combinatorial optimization
- QUBO has proven effective for nurse scheduling (arXiv:2302.09459)
- D-Wave hardware could provide speedup for large instances

**Risks:**
- Embedding overhead may negate quantum advantage
- Classical simulated annealing may be "good enough"

### Chemical Kinetics (Catalyst)

**Principle:** Schedule changes face "activation energy barriers" that can be lowered by "catalysts" (cross-trained staff, coordinators).

**Why it might work:**
- Models real organizational friction in schedule changes
- Identifies key personnel who enable flexibility
- Provides pathway optimization for complex swaps

**Risks:**
- Metaphor may not map perfectly to scheduling domain
- Barrier quantification is subjective

### Gene Regulatory Networks (Transcription Factors)

**Principle:** Constraints are "genes" regulated by context-sensitive "transcription factors" that activate/repress based on system state.

**Why it might work:**
- Provides graceful degradation under stress (chromatin silencing)
- Hierarchical control via master regulators (patient safety)
- Signal transduction models event-driven constraint changes

**Risks:**
- Complexity may not justify benefits
- Debugging regulatory networks is non-trivial

---

## Metrics Collection

The test harness collects:

```python
@dataclass
class ExperimentResult:
    branch: str
    scenario: str
    timestamp: datetime

    # Quality metrics
    constraint_violations: int
    acgme_compliance: float  # 0.0-1.0
    coverage_score: float    # 0.0-1.0
    equity_variance: float   # Lower is better

    # Performance metrics
    solve_time_ms: int
    memory_peak_mb: int

    # Comparison to baseline
    baseline_solve_time_ms: int
    quality_delta: float  # Positive = better than baseline
```

---

## Current Status

### Quantum Physics Scheduler
- **Lines:** 874 (solver) + 367 (tests)
- **Stage:** Unit tests pass, no integration testing
- **Next:** Benchmark against CP-SAT on realistic scenarios

### Catalyst Concepts
- **Lines:** 2,869 (library) + 1,340 (tests)
- **Stage:** Most complete, comprehensive test suite
- **Next:** Validate pathway optimization against real swap history

### Transcription Factors
- **Lines:** 1,255 (core) + 933 (tests)
- **Stage:** Core model complete, integration incomplete
- **Next:** Stress testing with simulated crisis scenarios

---

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-19 | Keep research on branches | Avoid contaminating production |
| 2025-12-19 | Create test harness | Enable safe comparison |
| 2025-12-19 | Define success criteria | Objective merge decisions |

---

## References

1. PyQUBO: QUBO Formulation Library - https://arxiv.org/abs/2103.01708
2. Nurse Scheduling via QUBO - https://arxiv.org/abs/2302.09459
3. Transition State Theory (Chemistry) - Eyring equation
4. Gene Regulatory Networks - https://www.nature.com/subjects/gene-regulatory-networks

---

*This document tracks the experimental research strategy. Update as research progresses.*
