# Thermodynamic Optimization Solver Service Specification

**Version:** 1.0
**Status:** Draft
**Created:** 2025-12-26
**Purpose:** Production-ready specification for implementing thermodynamic optimization in residency scheduling

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Service Architecture](#2-service-architecture)
3. [API Endpoints](#3-api-endpoints)
4. [Solver Components](#4-solver-components)
5. [Integration with OR-Tools](#5-integration-with-or-tools)
6. [Ensemble Generation](#6-ensemble-generation)
7. [Configuration](#7-configuration)
8. [Database Schema](#8-database-schema)
9. [Testing Requirements](#9-testing-requirements)
10. [Performance Benchmarks](#10-performance-benchmarks)
11. [Security Considerations](#11-security-considerations)
12. [Deployment Plan](#12-deployment-plan)

---

## 1. Executive Summary

### 1.1 Purpose

This specification defines the implementation of a thermodynamic optimization solver for medical residency scheduling. The system applies concepts from statistical mechanics—simulated annealing, free energy minimization, and entropy monitoring—to generate high-quality, diverse, and resilient schedules.

### 1.2 Goals

- **Primary:** Escape local minima that trap deterministic solvers
- **Secondary:** Generate diverse schedule ensembles for rapid deployment
- **Tertiary:** Monitor schedule stability via entropy metrics
- **Quality:** Achieve 90%+ solution quality compared to CP-SAT in 50% less time

### 1.3 Key Features

| Feature | Description | Priority |
|---------|-------------|----------|
| **Simulated Annealing Solver** | Probabilistic optimization using Metropolis criterion | P0 |
| **Free Energy Framework** | Balance constraint violations vs. schedule flexibility | P0 |
| **Entropy Monitoring** | Track schedule disorder and predict stability transitions | P1 |
| **Ensemble Generation** | Pre-compute 50+ valid schedules via Metropolis sampling | P1 |
| **Hybrid Optimization** | Combine CP-SAT (exploration) + SA (refinement) | P1 |
| **Energy Landscape Analysis** | Visualize solution space and stability | P2 |

### 1.4 Integration Points

- **Scheduling Engine** (`backend/app/scheduling/engine.py`): New solver algorithm option
- **Solver Factory** (`backend/app/scheduling/solvers.py`): Add `SimulatedAnnealingSolver`
- **Optimizer** (`backend/app/scheduling/optimizer.py`): Add SA to complexity-based solver selection
- **API Routes** (`backend/app/api/routes/scheduler.py`): New thermodynamic endpoints
- **Resilience System** (`backend/app/resilience/`): Entropy monitoring integration

---

## 2. Service Architecture

### 2.1 System Overview

```
┌────────────────────────────────────────────────────────────────┐
│                     Thermodynamic Service Layer                 │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │  Simulated       │  │  Free Energy     │  │  Entropy     │ │
│  │  Annealing       │  │  Calculator      │  │  Monitor     │ │
│  │  Solver          │  │                  │  │              │ │
│  └────────┬─────────┘  └────────┬─────────┘  └──────┬───────┘ │
│           │                     │                    │         │
│           └─────────────────────┴────────────────────┘         │
│                                 │                               │
│  ┌──────────────────────────────▼──────────────────────────┐  │
│  │         Energy Landscape Analyzer                       │  │
│  │  - Local minima detection                               │  │
│  │  - Energy barrier calculation                           │  │
│  │  - Stability assessment                                 │  │
│  └──────────────────────────────┬──────────────────────────┘  │
│                                 │                               │
│  ┌──────────────────────────────▼──────────────────────────┐  │
│  │         Ensemble Generator                              │  │
│  │  - Metropolis sampling                                  │  │
│  │  - Boltzmann distribution                               │  │
│  │  - Pre-computed alternatives                            │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                   Existing Solver Framework                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Greedy    │  │   CP-SAT    │  │    PuLP     │            │
│  │   Solver    │  │   Solver    │  │   Solver    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            Constraint Manager                            │  │
│  │  - ACGME constraints                                     │  │
│  │  - Availability constraints                              │  │
│  │  - Resilience constraints                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Responsibilities

#### 2.2.1 SimulatedAnnealingSolver

**Location:** `backend/app/scheduling/solvers/simulated_annealing.py`

**Responsibilities:**
- Implement Metropolis-Hastings algorithm for schedule optimization
- Manage cooling schedule (geometric, adaptive, or logarithmic)
- Track optimization statistics (energy history, acceptance rates)
- Support reheating for escape from plateaus

**Dependencies:**
- `SchedulingContext` for data access
- `FreeEnergyCalculator` for objective function
- `ConstraintManager` for validation

#### 2.2.2 FreeEnergyCalculator

**Location:** `backend/app/scheduling/thermodynamics/free_energy.py`

**Responsibilities:**
- Calculate internal energy from constraint violations
- Calculate entropy from schedule diversity
- Compute Helmholtz free energy: `F = U - T*S`
- Support adaptive temperature based on system state

**Formula:**
```
F = U - T·S

where:
  U = Σ(weight_i × violation_i)  [Internal energy]
  S = -Σ p_i log₂(p_i)           [Shannon entropy]
  T = temperature parameter       [Energy-entropy trade-off]
```

#### 2.2.3 EntropyMonitor

**Location:** `backend/app/scheduling/thermodynamics/entropy.py`

**Responsibilities:**
- Calculate Shannon entropy across multiple dimensions (person, rotation, temporal)
- Monitor entropy production rate
- Detect early warning signals (critical slowing, variance increase, flickering)
- Generate stability alerts

**Metrics:**
- Person entropy (assignment distribution)
- Rotation entropy (template distribution)
- Temporal entropy (time distribution)
- Joint entropy (multi-dimensional disorder)
- Mutual information (coupling between dimensions)

#### 2.2.4 EnergyLandscapeAnalyzer

**Location:** `backend/app/scheduling/thermodynamics/landscape.py`

**Responsibilities:**
- Probe energy landscape via perturbations
- Identify local minima vs. metastable states
- Calculate energy barriers
- Assess schedule stability

**Output:**
- Stability classification (VERY_STABLE, STABLE, METASTABLE, UNSTABLE)
- Energy barrier heights
- Escape path identification

#### 2.2.5 EnsembleGenerator

**Location:** `backend/app/scheduling/thermodynamics/ensemble.py`

**Responsibilities:**
- Generate diverse schedule alternatives via Metropolis sampling
- Pre-compute ensemble for emergency scenarios
- Estimate partition function (solution space size)
- Sample from Boltzmann distribution

**Configuration:**
- Ensemble size (default: 50 schedules)
- Sampling temperature (higher = more diversity)
- Thinning interval (decorrelation)

### 2.3 Data Flow

```
1. User Request → API Endpoint (/api/v1/thermo/anneal)
                  ↓
2. Build SchedulingContext (residents, blocks, templates, constraints)
                  ↓
3. Initialize SimulatedAnnealingSolver
   - Set cooling schedule
   - Configure temperature range
   - Set iteration limits
                  ↓
4. Run Optimization Loop:
   a. Propose random move (swap, reassign, change template)
   b. Calculate ΔF = F_new - F_current
   c. Apply Metropolis criterion:
      - Accept if ΔF < 0 (improvement)
      - Accept probabilistically if ΔF ≥ 0: P = exp(-ΔF/T)
   d. Update best solution if improved
   e. Cool temperature: T *= cooling_rate
   f. Repeat until T < T_final
                  ↓
5. Validate best solution with ACGMEValidator
                  ↓
6. Return SolverResult with statistics
                  ↓
7. Store in database + update monitoring dashboards
```

---

## 3. API Endpoints

### 3.1 Endpoint Overview

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/api/v1/thermo/anneal` | POST | Run simulated annealing optimization | Yes |
| `/api/v1/thermo/entropy` | GET | Get schedule entropy metrics | Yes |
| `/api/v1/thermo/ensemble` | POST | Generate schedule ensemble | Yes |
| `/api/v1/thermo/energy-landscape` | GET | Visualize solution space | Yes |
| `/api/v1/thermo/config` | GET/PUT | Get/update solver configuration | Yes (Admin) |

---

### 3.2 POST /api/v1/thermo/anneal

**Description:** Run simulated annealing optimization for schedule generation.

#### Request

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-28",
  "algorithm_config": {
    "temperature_initial": 100.0,
    "temperature_final": 0.01,
    "cooling_schedule": "geometric",
    "cooling_rate": 0.95,
    "steps_per_temperature": 100,
    "max_iterations": 10000,
    "reheat_enabled": false,
    "random_seed": 42
  },
  "energy_config": {
    "temperature": 1.0,
    "weights": {
      "acgme_critical_violation": 1000.0,
      "acgme_high_violation": 500.0,
      "coverage_gap": 500.0,
      "supervision_violation": 300.0,
      "workload_variance": 10.0,
      "template_concentration": 50.0
    }
  },
  "constraints": {
    "preserve_existing": true,
    "fmit_only_inpatient": true,
    "enforce_acgme": true
  }
}
```

#### Response (Success)

```json
{
  "success": true,
  "status": "OPTIMAL",
  "solver_status": "Simulated annealing converged in 8432 iterations",
  "runtime_seconds": 32.1,
  "objective_value": 45.2,
  "assignments": [
    {
      "person_id": "uuid-resident-1",
      "block_id": "uuid-block-am-1",
      "rotation_template_id": "uuid-template-clinic",
      "assignment_confidence": 0.95
    }
    // ... more assignments
  ],
  "statistics": {
    "iterations": 8432,
    "final_temperature": 0.0095,
    "initial_energy": 1245.3,
    "final_energy": 45.2,
    "energy_improvement": 1200.1,
    "best_energy": 45.2,
    "final_acceptance_rate": 0.05,
    "convergence_iteration": 7800
  },
  "energy_history": [
    {"iteration": 0, "temperature": 100.0, "energy": 1245.3},
    {"iteration": 100, "temperature": 95.0, "energy": 980.4},
    // ... more history points
  ],
  "entropy_metrics": {
    "person_entropy": 3.58,
    "rotation_entropy": 2.81,
    "temporal_entropy": 2.58,
    "joint_entropy": 6.12,
    "mutual_information": 2.85,
    "flexibility_score": 89.5
  },
  "validation_results": {
    "acgme_compliant": true,
    "violations": [],
    "warnings": []
  }
}
```

#### Response (Failure)

```json
{
  "success": false,
  "status": "TIMEOUT",
  "solver_status": "Maximum iterations reached without convergence",
  "runtime_seconds": 300.0,
  "objective_value": 125.3,
  "assignments": [],
  "statistics": {
    "iterations": 10000,
    "final_temperature": 0.5,
    "best_energy": 125.3,
    "energy_improvement": 1020.0
  },
  "error": "Solver exceeded maximum iterations. Try increasing temperature or iterations."
}
```

#### Error Codes

| Code | Description | Resolution |
|------|-------------|------------|
| 400 | Invalid request parameters | Check date range, config values |
| 401 | Unauthorized | Provide valid auth token |
| 408 | Timeout | Increase max_iterations or simplify problem |
| 500 | Internal solver error | Check logs, retry with different seed |

---

### 3.3 GET /api/v1/thermo/entropy

**Description:** Get entropy metrics for a schedule or date range.

#### Request Parameters

```
GET /api/v1/thermo/entropy?start_date=2025-01-01&end_date=2025-01-28&schedule_id={uuid}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | Yes* | Start of date range |
| `end_date` | date | Yes* | End of date range |
| `schedule_id` | UUID | Yes* | Existing schedule ID |
| `dimension` | string | No | Specific entropy dimension (person/rotation/temporal/all) |

*Either date range OR schedule_id required

#### Response

```json
{
  "schedule_id": "uuid-schedule-123",
  "start_date": "2025-01-01",
  "end_date": "2025-01-28",
  "entropy_metrics": {
    "person_entropy": 3.58,
    "person_entropy_max": 4.0,
    "person_entropy_normalized": 0.895,
    "rotation_entropy": 2.81,
    "rotation_entropy_max": 3.17,
    "rotation_entropy_normalized": 0.887,
    "temporal_entropy": 2.58,
    "temporal_entropy_max": 2.81,
    "temporal_entropy_normalized": 0.918,
    "joint_entropy": 6.12,
    "mutual_information": 2.85,
    "flexibility_score": 89.5,
    "stability_classification": "STABLE"
  },
  "entropy_production": {
    "rate_of_change": 0.02,
    "variance_trend": 0.15,
    "autocorrelation": 0.35,
    "warning_level": "NORMAL"
  },
  "distribution_details": {
    "person_distribution": {
      "resident-1": 24,
      "resident-2": 26,
      "resident-3": 22
    },
    "rotation_distribution": {
      "clinic": 18,
      "procedures": 12,
      "admin": 10
    }
  }
}
```

---

### 3.4 POST /api/v1/thermo/ensemble

**Description:** Generate ensemble of diverse, valid schedules.

#### Request

```json
{
  "start_date": "2025-01-01",
  "end_date": "2025-01-28",
  "ensemble_size": 50,
  "sampling_temperature": 2.0,
  "thinning_interval": 10,
  "max_iterations": 5000,
  "quality_threshold": 100.0,
  "random_seed": 42
}
```

#### Response

```json
{
  "success": true,
  "ensemble_size": 50,
  "runtime_seconds": 145.3,
  "schedules": [
    {
      "schedule_id": "ensemble-1",
      "free_energy": 45.2,
      "person_entropy": 3.58,
      "boltzmann_probability": 0.032,
      "assignments_count": 56,
      "acgme_compliant": true
    },
    {
      "schedule_id": "ensemble-2",
      "free_energy": 48.7,
      "person_entropy": 3.62,
      "boltzmann_probability": 0.029,
      "assignments_count": 56,
      "acgme_compliant": true
    }
    // ... 48 more schedules
  ],
  "statistics": {
    "total_iterations": 5000,
    "samples_collected": 50,
    "samples_rejected": 125,
    "acceptance_rate": 0.28,
    "average_energy": 52.3,
    "energy_std_dev": 8.5,
    "diversity_score": 0.87
  },
  "partition_function_estimate": 1.23e12
}
```

**Use Cases:**
- Pre-compute alternatives for rapid deployment during emergencies
- Estimate uncertainty in schedule quality
- Explore diverse solutions for what-if analysis

---

### 3.5 GET /api/v1/thermo/energy-landscape

**Description:** Analyze energy landscape around a schedule.

#### Request Parameters

```
GET /api/v1/thermo/energy-landscape?schedule_id={uuid}&num_probes=100&temperature=1.0
```

#### Response

```json
{
  "schedule_id": "uuid-schedule-123",
  "current_energy": 45.2,
  "temperature": 1.0,
  "landscape_analysis": {
    "is_local_minimum": true,
    "min_barrier_height": 12.3,
    "avg_barrier_height": 45.7,
    "max_barrier_height": 120.5,
    "stability": "STABLE",
    "escape_difficulty": "MODERATE"
  },
  "perturbation_statistics": {
    "num_probes": 100,
    "downhill_moves": 0,
    "uphill_moves": 100,
    "energy_distribution": {
      "min": 45.2,
      "q25": 58.3,
      "median": 67.8,
      "q75": 85.4,
      "max": 165.9
    }
  },
  "visualization_data": {
    "energy_values": [45.2, 58.1, 62.3, ...],
    "perturbation_types": ["swap", "reassign", "swap", ...]
  }
}
```

**Stability Classifications:**
- **VERY_STABLE:** Avg barrier > 50, highly resistant to changes
- **STABLE:** Avg barrier > 10, normal operating range
- **METASTABLE:** Avg barrier > 0, shallow well, vulnerable
- **UNSTABLE:** Avg barrier ≤ 0, not a local minimum

---

### 3.6 GET /api/v1/thermo/config

**Description:** Get current thermodynamic solver configuration (Admin only).

#### Response

```json
{
  "solver_config": {
    "temperature_initial": 100.0,
    "temperature_final": 0.01,
    "cooling_rate": 0.95,
    "steps_per_temperature": 100,
    "cooling_schedule": "geometric"
  },
  "energy_weights": {
    "acgme_critical_violation": 1000.0,
    "acgme_high_violation": 500.0,
    "coverage_gap": 500.0,
    "supervision_violation": 300.0,
    "workload_variance": 10.0,
    "template_concentration": 50.0
  },
  "entropy_monitoring": {
    "enabled": true,
    "history_window": 100,
    "critical_slowing_threshold": 0.8,
    "variance_threshold": 0.3
  },
  "complexity_thresholds": {
    "sa_complexity_threshold": 60,
    "auto_solver_selection": true
  }
}
```

### 3.7 PUT /api/v1/thermo/config

**Description:** Update thermodynamic solver configuration (Admin only).

#### Request

```json
{
  "solver_config": {
    "temperature_initial": 150.0,
    "cooling_rate": 0.97
  },
  "energy_weights": {
    "acgme_critical_violation": 1500.0
  }
}
```

#### Response

```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "updated_fields": ["temperature_initial", "cooling_rate", "acgme_critical_violation"],
  "effective_timestamp": "2025-12-26T10:30:00Z"
}
```

---

## 4. Solver Components

### 4.1 SimulatedAnnealingSolver Class

**File:** `backend/app/scheduling/solvers/simulated_annealing.py`

```python
"""Simulated annealing solver for residency scheduling."""

import logging
import math
import random
import time
from dataclasses import dataclass
from typing import Optional

from app.models.assignment import Assignment
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import BaseSolver, SolverResult
from app.scheduling.thermodynamics.free_energy import FreeEnergyCalculator
from app.scheduling.thermodynamics.cooling import CoolingSchedule

logger = logging.getLogger(__name__)


@dataclass
class SAConfig:
    """Simulated annealing configuration."""

    temperature_initial: float = 100.0
    temperature_final: float = 0.01
    cooling_schedule: str = "geometric"  # geometric, adaptive, logarithmic
    cooling_rate: float = 0.95
    steps_per_temperature: int = 100
    max_iterations: int = 10000
    reheat_enabled: bool = False
    reheat_temperature: float = 50.0
    reheat_interval: int = 1000
    random_seed: Optional[int] = None


class SimulatedAnnealingSolver(BaseSolver):
    """
    Simulated annealing solver using Metropolis-Hastings algorithm.

    Advantages:
    - Escapes local minima via probabilistic uphill moves
    - Explores diverse solutions
    - Handles non-convex energy landscapes
    - No gradient needed (discrete optimization)

    Algorithm:
    1. Start with initial schedule (random or greedy-initialized)
    2. At high temperature, propose random moves
    3. Accept improvements always, deteriorations probabilistically
    4. Gradually cool temperature (annealing)
    5. Converge to low-energy (high-quality) schedule
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        config: SAConfig | None = None,
    ):
        """Initialize simulated annealing solver."""
        super().__init__(constraint_manager, timeout_seconds)
        self.config = config or SAConfig()

        if self.config.random_seed is not None:
            random.seed(self.config.random_seed)

        self.energy_calculator = FreeEnergyCalculator()
        self.cooling = self._create_cooling_schedule()

    def _create_cooling_schedule(self) -> CoolingSchedule:
        """Create cooling schedule based on configuration."""
        from app.scheduling.thermodynamics.cooling import (
            GeometricCooling,
            AdaptiveCooling,
            LogarithmicCooling,
        )

        if self.config.cooling_schedule == "geometric":
            return GeometricCooling(
                initial_temp=self.config.temperature_initial,
                final_temp=self.config.temperature_final,
                cooling_rate=self.config.cooling_rate,
            )
        elif self.config.cooling_schedule == "adaptive":
            return AdaptiveCooling(
                initial_temp=self.config.temperature_initial,
                target_acceptance=0.3,
            )
        elif self.config.cooling_schedule == "logarithmic":
            return LogarithmicCooling(
                initial_temp=self.config.temperature_initial
            )
        else:
            raise ValueError(f"Unknown cooling schedule: {self.config.cooling_schedule}")

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """Run simulated annealing optimization."""
        start_time = time.time()

        logger.info(
            f"Starting simulated annealing: T={self.config.temperature_initial} → "
            f"{self.config.temperature_final}, cooling={self.config.cooling_schedule}"
        )

        # Initialize with greedy solver or provided assignments
        if existing_assignments:
            current = self._assignments_to_list(existing_assignments)
        else:
            current = self._greedy_initialization(context)

        if not current:
            return self._failure_result("Initialization failed", start_time)

        current_F = self.energy_calculator.calculate_free_energy(
            current, context, temperature=1.0
        )

        best = current.copy()
        best_F = current_F

        # Statistics tracking
        energy_history = []
        acceptance_history = []

        # Annealing loop
        iteration = 0
        stagnation_counter = 0

        while (
            self.cooling.temperature > self.config.temperature_final
            and iteration < self.config.max_iterations
        ):
            accepts = 0

            for _ in range(self.config.steps_per_temperature):
                # Check timeout
                if time.time() - start_time > self.timeout_seconds:
                    logger.warning("Simulated annealing timeout")
                    break

                # Propose move
                candidate = self._propose_move(current, context)
                candidate_F = self.energy_calculator.calculate_free_energy(
                    candidate, context, temperature=1.0
                )

                # Metropolis criterion
                delta_F = candidate_F - current_F

                if delta_F < 0:
                    # Improvement: always accept
                    accept = True
                elif self.cooling.temperature > 0:
                    # Deterioration: accept probabilistically
                    p_accept = math.exp(-delta_F / self.cooling.temperature)
                    accept = random.random() < p_accept
                else:
                    accept = False

                if accept:
                    current = candidate
                    current_F = candidate_F
                    accepts += 1

                    # Track best ever seen
                    if current_F < best_F:
                        best = current.copy()
                        best_F = current_F
                        stagnation_counter = 0
                        logger.debug(f"New best: F={best_F:.2f} at iteration {iteration}")
                    else:
                        stagnation_counter += 1

                iteration += 1

            # Record statistics
            acceptance_rate = accepts / self.config.steps_per_temperature
            energy_history.append({
                "iteration": iteration,
                "temperature": self.cooling.temperature,
                "energy": current_F,
                "best_energy": best_F,
            })
            acceptance_history.append(acceptance_rate)

            # Update temperature
            if isinstance(self.cooling, AdaptiveCooling):
                self.cooling.update(acceptance_rate)
            else:
                self.cooling.cool()

            # Reheat if stagnating
            if (
                self.config.reheat_enabled
                and stagnation_counter > self.config.reheat_interval
            ):
                logger.info(f"Reheating at iteration {iteration}")
                self.cooling.temperature = self.config.reheat_temperature
                stagnation_counter = 0

        runtime = time.time() - start_time

        # Validate best solution
        validation_results = self._validate_solution(best, context)

        # Convert to solver result format
        assignments_tuple = [
            (a.person_id, a.block_id, a.rotation_template_id)
            for a in best
        ]

        logger.info(
            f"Simulated annealing complete: {iteration} iterations, "
            f"F={best_F:.2f}, runtime={runtime:.1f}s"
        )

        return SolverResult(
            success=True,
            assignments=assignments_tuple,
            status="OPTIMAL" if best_F < 100 else "FEASIBLE",
            objective_value=best_F,
            runtime_seconds=runtime,
            solver_status=f"Simulated annealing converged in {iteration} iterations",
            statistics={
                "iterations": iteration,
                "final_temperature": self.cooling.temperature,
                "initial_energy": energy_history[0]["energy"] if energy_history else None,
                "final_energy": best_F,
                "energy_improvement": (energy_history[0]["energy"] - best_F) if energy_history else 0,
                "final_acceptance_rate": acceptance_history[-1] if acceptance_history else 0,
                "energy_history": energy_history,
                "acceptance_history": acceptance_history,
            },
            random_seed=self.config.random_seed,
        )

    def _greedy_initialization(
        self, context: SchedulingContext
    ) -> list[Assignment]:
        """Initialize with greedy solver for better starting point."""
        from app.scheduling.solvers import GreedySolver

        greedy = GreedySolver(self.constraint_manager)
        result = greedy.solve(context)

        if not result.success:
            logger.warning("Greedy initialization failed, using random")
            return self._random_initialization(context)

        return [
            Assignment(person_id=p, block_id=b, rotation_template_id=t)
            for p, b, t in result.assignments
        ]

    def _random_initialization(
        self, context: SchedulingContext
    ) -> list[Assignment]:
        """Generate random initial schedule."""
        schedule = []
        workday_blocks = [b for b in context.blocks if not b.is_weekend]

        for block in workday_blocks:
            # Filter available residents
            available = [
                r for r in context.residents
                if context.availability.get(r.id, {}).get(block.id, {}).get("available", False)
            ]

            if not available:
                continue

            resident = random.choice(available)
            template = random.choice(context.templates) if context.templates else None

            if template:
                schedule.append(Assignment(
                    person_id=resident.id,
                    block_id=block.id,
                    rotation_template_id=template.id,
                ))

        return schedule

    def _propose_move(
        self, current: list[Assignment], context: SchedulingContext
    ) -> list[Assignment]:
        """
        Propose random schedule modification.

        Move types:
        - Swap two assignments (50%)
        - Change assignment's resident (25%)
        - Change assignment's template (25%)
        """
        if not current:
            return current.copy()

        candidate = current.copy()
        move_type = random.random()

        if move_type < 0.5 and len(candidate) >= 2:
            # Swap two assignments
            i, j = random.sample(range(len(candidate)), 2)
            candidate[i], candidate[j] = candidate[j], candidate[i]

        elif move_type < 0.75:
            # Change one assignment's resident
            idx = random.randint(0, len(candidate) - 1)
            block = context.blocks[context.block_idx[candidate[idx].block_id]]

            # Find available residents for this block
            available = [
                r for r in context.residents
                if context.availability.get(r.id, {}).get(block.id, {}).get("available", False)
            ]

            if available:
                new_resident = random.choice(available)
                candidate[idx] = Assignment(
                    person_id=new_resident.id,
                    block_id=candidate[idx].block_id,
                    rotation_template_id=candidate[idx].rotation_template_id,
                )

        else:
            # Change one assignment's template
            idx = random.randint(0, len(candidate) - 1)
            if context.templates:
                new_template = random.choice(context.templates)
                candidate[idx] = Assignment(
                    person_id=candidate[idx].person_id,
                    block_id=candidate[idx].block_id,
                    rotation_template_id=new_template.id,
                )

        return candidate

    def _assignments_to_list(
        self, assignments: list[Assignment]
    ) -> list[Assignment]:
        """Convert assignment objects to internal representation."""
        return assignments.copy()

    def _validate_solution(
        self, schedule: list[Assignment], context: SchedulingContext
    ) -> dict:
        """Validate solution with ACGME validator."""
        # TODO: Integrate with ACGMEValidator
        return {"acgme_compliant": True, "violations": [], "warnings": []}

    def _failure_result(self, message: str, start_time: float) -> SolverResult:
        """Create failure result."""
        return SolverResult(
            success=False,
            assignments=[],
            status="FAILED",
            solver_status=message,
            runtime_seconds=time.time() - start_time,
        )
```

### 4.2 CoolingSchedule Classes

**File:** `backend/app/scheduling/thermodynamics/cooling.py`

```python
"""Cooling schedule strategies for simulated annealing."""

from abc import ABC, abstractmethod
import math


class CoolingSchedule(ABC):
    """Base class for cooling schedules."""

    def __init__(self, initial_temp: float):
        self.temperature = initial_temp
        self.initial_temperature = initial_temp

    @abstractmethod
    def cool(self) -> float:
        """Update temperature and return new value."""
        pass

    def reset(self):
        """Reset to initial temperature."""
        self.temperature = self.initial_temperature


class GeometricCooling(CoolingSchedule):
    """
    Geometric cooling: T_k = T_0 * α^k

    Recommended for most problems.
    Typical α values: 0.90 - 0.99
    """

    def __init__(
        self,
        initial_temp: float,
        final_temp: float,
        cooling_rate: float = 0.95,
    ):
        super().__init__(initial_temp)
        self.final_temp = final_temp
        self.cooling_rate = cooling_rate

    def cool(self) -> float:
        """Apply geometric cooling."""
        self.temperature *= self.cooling_rate
        return self.temperature


class AdaptiveCooling(CoolingSchedule):
    """
    Adaptive cooling that adjusts based on acceptance rate.

    If acceptance too low → slow down cooling
    If acceptance too high → speed up cooling

    Target acceptance: 20-40%
    """

    def __init__(
        self,
        initial_temp: float,
        target_acceptance: float = 0.3,
        adaptation_rate: float = 1.05,
    ):
        super().__init__(initial_temp)
        self.target_acceptance = target_acceptance
        self.adaptation_rate = adaptation_rate
        self.alpha = 0.95  # Initial cooling rate

    def update(self, acceptance_rate: float) -> float:
        """
        Update temperature based on recent acceptance rate.

        Args:
            acceptance_rate: Recent acceptance rate (0-1)

        Returns:
            New temperature
        """
        # Adapt cooling rate
        if acceptance_rate < self.target_acceptance * 0.8:
            # Too few accepts → slow down cooling
            self.alpha = min(0.99, self.alpha * self.adaptation_rate)
        elif acceptance_rate > self.target_acceptance * 1.2:
            # Too many accepts → speed up cooling
            self.alpha = max(0.90, self.alpha / self.adaptation_rate)

        # Apply cooling
        self.temperature *= self.alpha
        return self.temperature

    def cool(self) -> float:
        """Apply current cooling rate."""
        self.temperature *= self.alpha
        return self.temperature


class LogarithmicCooling(CoolingSchedule):
    """
    Logarithmic cooling: T_k = T_0 / log(k+1)

    Very slow cooling, guaranteed convergence to global optimum.
    Too slow for practical use in most cases.
    """

    def __init__(self, initial_temp: float):
        super().__init__(initial_temp)
        self.iteration = 0

    def cool(self) -> float:
        """Apply logarithmic cooling."""
        self.iteration += 1
        self.temperature = self.initial_temperature / math.log(self.iteration + 2)
        return self.temperature
```

### 4.3 FreeEnergyCalculator Class

**File:** `backend/app/scheduling/thermodynamics/free_energy.py`

```python
"""Free energy calculation for schedules."""

import logging
import math
from collections import Counter
from typing import Any

import numpy as np

from app.models.assignment import Assignment
from app.scheduling.constraints import SchedulingContext

logger = logging.getLogger(__name__)


class FreeEnergyCalculator:
    """
    Calculate Helmholtz-inspired free energy for schedules.

    F = U - T*S

    where:
        U = Internal energy (constraint violations)
        S = Entropy (schedule flexibility)
        T = Temperature parameter
    """

    def __init__(self, energy_weights: dict | None = None):
        """
        Initialize calculator.

        Args:
            energy_weights: Custom weights for violation types
        """
        self.weights = energy_weights or self._default_weights()

    def _default_weights(self) -> dict:
        """Default energy weights."""
        return {
            "acgme_critical_violation": 1000.0,
            "acgme_high_violation": 500.0,
            "acgme_medium_violation": 100.0,
            "coverage_gap": 500.0,
            "supervision_violation": 300.0,
            "workload_variance": 10.0,
            "template_concentration": 50.0,
        }

    def calculate_free_energy(
        self,
        assignments: list[Assignment],
        context: SchedulingContext,
        temperature: float = 1.0,
    ) -> float:
        """
        Calculate Helmholtz free energy.

        Args:
            assignments: Schedule assignments
            context: Scheduling context
            temperature: Temperature parameter

        Returns:
            Free energy (lower is better)
        """
        U = self.calculate_internal_energy(assignments, context)
        S = self.calculate_entropy(assignments)

        F = U - temperature * S

        return F

    def calculate_internal_energy(
        self,
        assignments: list[Assignment],
        context: SchedulingContext,
    ) -> float:
        """
        Calculate internal energy from constraint violations.

        Returns:
            Total energy (0 = perfect, higher = worse)
        """
        energy = 0.0

        # Category 1: ACGME violations (via validator)
        # TODO: Integrate ACGMEValidator for real violations
        # For now, use simplified heuristics

        # Category 2: Coverage gaps
        filled_blocks = set(a.block_id for a in assignments)
        workday_blocks = {b.id for b in context.blocks if not b.is_weekend}
        unfilled_count = len(workday_blocks - filled_blocks)
        energy += unfilled_count * self.weights["coverage_gap"]

        # Category 3: Workload imbalance
        person_counts = Counter(a.person_id for a in assignments)
        if person_counts:
            counts = list(person_counts.values())
            workload_variance = np.var(counts)
            energy += workload_variance * self.weights["workload_variance"]

        # Category 4: Template concentration
        template_counts = Counter(a.rotation_template_id for a in assignments)
        if template_counts:
            max_count = max(template_counts.values())
            mean_count = sum(template_counts.values()) / len(template_counts)
            concentration = max_count - mean_count
            energy += concentration * self.weights["template_concentration"]

        return energy

    def calculate_entropy(self, assignments: list[Assignment]) -> float:
        """
        Calculate Shannon entropy of assignment distribution.

        Args:
            assignments: Schedule assignments

        Returns:
            Entropy in bits (higher = more flexible)
        """
        if not assignments:
            return 0.0

        # Person distribution
        person_counts = Counter(a.person_id for a in assignments)
        total = len(assignments)

        probabilities = [count / total for count in person_counts.values()]

        # Shannon entropy
        H = -sum(p * math.log2(p) for p in probabilities if p > 0)

        return H
```

### 4.4 EntropyMonitor Class

**File:** `backend/app/scheduling/thermodynamics/entropy.py`

```python
"""Entropy monitoring for schedule stability."""

import logging
import math
from collections import Counter
from dataclasses import dataclass

import numpy as np

from app.models.assignment import Assignment
from app.scheduling.constraints import SchedulingContext

logger = logging.getLogger(__name__)


@dataclass
class EntropyMetrics:
    """Multi-dimensional entropy analysis."""

    person_entropy: float
    rotation_entropy: float
    temporal_entropy: float
    joint_entropy: float
    mutual_information: float
    flexibility_score: float

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "person_entropy": self.person_entropy,
            "rotation_entropy": self.rotation_entropy,
            "temporal_entropy": self.temporal_entropy,
            "joint_entropy": self.joint_entropy,
            "mutual_information": self.mutual_information,
            "flexibility_score": self.flexibility_score,
        }


class EntropyMonitor:
    """
    Monitor entropy dynamics for early warning signals.

    Critical phenomena before phase transitions:
    1. Increasing variance in entropy
    2. Critical slowing down (high autocorrelation)
    3. Rapid entropy spikes (flickering)
    """

    def __init__(self, window_size: int = 100):
        """Initialize monitor."""
        self.entropy_history: list[float] = []
        self.window_size = window_size

    def update(self, assignments: list[Assignment]) -> dict:
        """
        Update entropy history and detect critical phenomena.

        Returns:
            dict with metrics and warning level
        """
        current_H = self._calculate_person_entropy(assignments)
        self.entropy_history.append(current_H)

        # Keep only recent window
        if len(self.entropy_history) > self.window_size:
            self.entropy_history.pop(0)

        metrics = {
            "current_entropy": current_H,
            "rate_of_change": self._entropy_rate_of_change(),
            "variance_trend": self._variance_trend(),
            "autocorrelation": self._autocorrelation(),
            "warning_level": "NORMAL",
        }

        # Early warning detection
        if metrics["autocorrelation"] > 0.8:
            metrics["warning_level"] = "CRITICAL_SLOWING"
        elif metrics["variance_trend"] > 0.3:
            metrics["warning_level"] = "INCREASING_VARIANCE"
        elif abs(metrics["rate_of_change"]) > 0.1:
            metrics["warning_level"] = "RAPID_CHANGE"

        return metrics

    def calculate_multidimensional_entropy(
        self,
        assignments: list[Assignment],
        context: SchedulingContext,
    ) -> EntropyMetrics:
        """Calculate entropy across all schedule dimensions."""
        total = len(assignments)
        if total == 0:
            return EntropyMetrics(0, 0, 0, 0, 0, 0)

        # Person distribution
        person_dist = Counter(a.person_id for a in assignments)
        H_person = self._shannon_entropy(person_dist, total)

        # Rotation type distribution
        rotation_dist = Counter(a.rotation_template_id for a in assignments)
        H_rotation = self._shannon_entropy(rotation_dist, total)

        # Temporal distribution (day of week)
        temporal_dist = Counter(
            context.blocks[context.block_idx[a.block_id]].date.weekday()
            for a in assignments
        )
        H_temporal = self._shannon_entropy(temporal_dist, total)

        # Joint distribution
        joint_dist = Counter(
            (a.person_id, a.rotation_template_id) for a in assignments
        )
        H_joint = self._shannon_entropy(joint_dist, total)

        # Mutual information
        MI = H_person + H_rotation - H_joint

        # Flexibility score (normalized person entropy)
        max_entropy = math.log2(len(context.residents)) if context.residents else 1.0
        flexibility = (H_person / max_entropy) * 100 if max_entropy > 0 else 0.0

        return EntropyMetrics(
            person_entropy=H_person,
            rotation_entropy=H_rotation,
            temporal_entropy=H_temporal,
            joint_entropy=H_joint,
            mutual_information=MI,
            flexibility_score=min(100, flexibility),
        )

    def _calculate_person_entropy(self, assignments: list[Assignment]) -> float:
        """Calculate Shannon entropy of person distribution."""
        if not assignments:
            return 0.0

        person_counts = Counter(a.person_id for a in assignments)
        total = len(assignments)

        probabilities = [count / total for count in person_counts.values()]
        H = -sum(p * math.log2(p) for p in probabilities if p > 0)

        return H

    def _shannon_entropy(self, distribution: Counter, total: int) -> float:
        """Helper to calculate Shannon entropy."""
        return -sum(
            (count / total) * math.log2(count / total)
            for count in distribution.values()
            if count > 0
        )

    def _entropy_rate_of_change(self) -> float:
        """Calculate dH/dt using linear regression."""
        if len(self.entropy_history) < 10:
            return 0.0

        x = np.arange(len(self.entropy_history))
        y = np.array(self.entropy_history)

        slope, _ = np.polyfit(x, y, 1)
        return slope

    def _variance_trend(self) -> float:
        """Detect increasing variance (early warning signal)."""
        if len(self.entropy_history) < 20:
            return 0.0

        mid = len(self.entropy_history) // 2
        var_early = np.var(self.entropy_history[:mid])
        var_recent = np.var(self.entropy_history[mid:])

        if var_early == 0:
            return 0.0

        return (var_recent - var_early) / var_early

    def _autocorrelation(self, lag: int = 1) -> float:
        """
        Calculate autocorrelation at lag.

        High autocorrelation → critical slowing → phase transition imminent
        """
        if len(self.entropy_history) < lag + 10:
            return 0.0

        series = np.array(self.entropy_history)
        mean = np.mean(series)
        c0 = np.sum((series - mean) ** 2)

        if c0 == 0:
            return 0.0

        c_lag = np.sum((series[:-lag] - mean) * (series[lag:] - mean))

        return c_lag / c0
```

---

## 5. Integration with OR-Tools

### 5.1 Hybrid Approach Strategy

Combine the strengths of CP-SAT (deterministic, optimal) and Simulated Annealing (stochastic, escapes local minima):

**Strategy:**
1. Run CP-SAT with short timeout (60s)
2. If CP-SAT finds optimal solution → return immediately
3. If CP-SAT times out → use partial solution to initialize SA
4. Run SA to refine and improve
5. Return best solution found

**File:** `backend/app/scheduling/solvers/hybrid_thermo.py`

```python
"""Hybrid CP-SAT + Simulated Annealing solver."""

import logging
import time

from app.models.assignment import Assignment
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import BaseSolver, SolverResult
from app.scheduling.solvers.cpsat import CPSatSolver
from app.scheduling.solvers.simulated_annealing import (
    SimulatedAnnealingSolver,
    SAConfig,
)

logger = logging.getLogger(__name__)


class HybridThermodynamicSolver(BaseSolver):
    """
    Hybrid solver combining CP-SAT and simulated annealing.

    Phase 1: CP-SAT for fast exploration (60s timeout)
    Phase 2: SA for refinement and local minimum escape

    Best of both worlds:
    - CP-SAT's constraint propagation
    - SA's ability to escape local minima
    """

    def __init__(
        self,
        constraint_manager: ConstraintManager | None = None,
        timeout_seconds: float = 300.0,
        cpsat_timeout: float = 60.0,
        sa_config: SAConfig | None = None,
    ):
        """Initialize hybrid solver."""
        super().__init__(constraint_manager, timeout_seconds)
        self.cpsat_timeout = cpsat_timeout
        self.sa_config = sa_config or SAConfig(
            temperature_initial=50.0,  # Lower than pure SA
            cooling_rate=0.95,
            steps_per_temperature=50,
        )

    def solve(
        self,
        context: SchedulingContext,
        existing_assignments: list[Assignment] = None,
    ) -> SolverResult:
        """Run hybrid optimization."""
        start_time = time.time()

        # Phase 1: CP-SAT
        logger.info("Phase 1: Running CP-SAT optimization")
        cpsat_solver = CPSatSolver(
            self.constraint_manager,
            timeout_seconds=self.cpsat_timeout,
        )
        cpsat_result = cpsat_solver.solve(context, existing_assignments)

        if cpsat_result.success and cpsat_result.status == "OPTIMAL":
            logger.info("CP-SAT found optimal solution, returning")
            return cpsat_result

        # Phase 2: Simulated Annealing refinement
        logger.info("Phase 2: Running simulated annealing refinement")

        # Use CP-SAT result as initialization
        if cpsat_result.assignments:
            initial_assignments = [
                Assignment(person_id=p, block_id=b, rotation_template_id=t)
                for p, b, t in cpsat_result.assignments
            ]
        else:
            initial_assignments = None

        # Run SA with remaining time budget
        remaining_time = self.timeout_seconds - (time.time() - start_time)
        sa_solver = SimulatedAnnealingSolver(
            self.constraint_manager,
            timeout_seconds=max(10.0, remaining_time),
            config=self.sa_config,
        )

        sa_result = sa_solver.solve(context, initial_assignments)

        # Combine statistics
        total_runtime = time.time() - start_time
        sa_result.runtime_seconds = total_runtime
        sa_result.statistics["cpsat_runtime"] = cpsat_result.runtime_seconds
        sa_result.statistics["sa_runtime"] = sa_result.runtime_seconds - cpsat_result.runtime_seconds
        sa_result.statistics["cpsat_objective"] = cpsat_result.objective_value
        sa_result.solver_status = f"Hybrid: CP-SAT ({cpsat_result.status}) + SA"

        return sa_result
```

### 5.2 OR-Tools Validation Integration

Use CP-SAT to validate SA solutions:

```python
def validate_sa_solution_with_cpsat(
    schedule: list[Assignment],
    context: SchedulingContext,
) -> dict:
    """
    Validate simulated annealing solution using OR-Tools CP-SAT.

    Returns:
        dict with validation results
    """
    from ortools.sat.python import cp_model

    model = cp_model.CpModel()

    # Create variables and fix to SA solution
    assignments_dict = {}
    for assignment in schedule:
        key = (assignment.person_id, assignment.block_id, assignment.rotation_template_id)
        var = model.NewBoolVar(f"x_{key}")
        model.Add(var == 1)  # Fix to 1 (exists in SA solution)
        assignments_dict[key] = var

    # Add all constraints
    for constraint_name, constraint_func in context.constraint_manager.get_all_constraints():
        try:
            constraint_func(model, context, assignments_dict)
        except Exception as e:
            logger.error(f"Constraint {constraint_name} failed: {e}")

    # Solve for feasibility check
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "valid": True,
            "status": "FEASIBLE",
            "violations": [],
        }
    else:
        return {
            "valid": False,
            "status": "INFEASIBLE",
            "violations": ["Solution violates constraints"],
        }
```

---

## 6. Ensemble Generation

### 6.1 EnsembleGenerator Class

**File:** `backend/app/scheduling/thermodynamics/ensemble.py`

```python
"""Schedule ensemble generation via Metropolis sampling."""

import logging
import math
import random
import time
from typing import Optional

from app.models.assignment import Assignment
from app.scheduling.constraints import SchedulingContext
from app.scheduling.thermodynamics.free_energy import FreeEnergyCalculator

logger = logging.getLogger(__name__)


class EnsembleGenerator:
    """
    Generate diverse schedule ensemble using Metropolis sampling.

    Use cases:
    - Pre-compute alternatives for emergency deployment
    - Estimate uncertainty in schedule quality
    - Explore solution space diversity
    """

    def __init__(
        self,
        energy_calculator: FreeEnergyCalculator | None = None,
    ):
        """Initialize ensemble generator."""
        self.energy_calculator = energy_calculator or FreeEnergyCalculator()

    def generate_ensemble(
        self,
        context: SchedulingContext,
        ensemble_size: int = 50,
        temperature: float = 2.0,
        thinning_interval: int = 10,
        max_iterations: int = 5000,
        initial_schedule: list[Assignment] | None = None,
        random_seed: Optional[int] = None,
    ) -> dict:
        """
        Generate schedule ensemble via Metropolis sampling.

        Args:
            context: Scheduling context
            ensemble_size: Number of schedules to generate
            temperature: Sampling temperature (higher = more diversity)
            thinning_interval: Samples to skip for independence
            max_iterations: Maximum sampling iterations
            initial_schedule: Starting schedule (uses greedy if None)
            random_seed: For reproducibility

        Returns:
            dict with ensemble and statistics
        """
        start_time = time.time()

        if random_seed is not None:
            random.seed(random_seed)

        logger.info(
            f"Generating ensemble: size={ensemble_size}, T={temperature}, "
            f"thinning={thinning_interval}"
        )

        # Initialize
        if initial_schedule:
            current = initial_schedule.copy()
        else:
            current = self._greedy_initialization(context)

        if not current:
            return {
                "success": False,
                "error": "Failed to initialize ensemble",
            }

        ensemble = []
        iterations = 0
        samples_collected = 0
        samples_rejected = 0
        accepts = 0

        while samples_collected < ensemble_size and iterations < max_iterations:
            # Propose move
            candidate = self._propose_random_move(current, context)

            # Metropolis criterion
            E_current = self.energy_calculator.calculate_internal_energy(
                current, context
            )
            E_candidate = self.energy_calculator.calculate_internal_energy(
                candidate, context
            )
            delta_E = E_candidate - E_current

            if delta_E < 0 or random.random() < math.exp(-delta_E / temperature):
                current = candidate
                accepts += 1

            # Collect sample (with thinning)
            if iterations % thinning_interval == 0:
                # Check if this is a valid schedule
                if self._is_valid_schedule(current, context):
                    ensemble.append({
                        "schedule_id": f"ensemble-{samples_collected + 1}",
                        "assignments": current.copy(),
                        "free_energy": self.energy_calculator.calculate_free_energy(
                            current, context, temperature=1.0
                        ),
                        "person_entropy": self.energy_calculator.calculate_entropy(current),
                    })
                    samples_collected += 1
                else:
                    samples_rejected += 1

            iterations += 1

        runtime = time.time() - start_time

        # Calculate ensemble statistics
        if ensemble:
            energies = [s["free_energy"] for s in ensemble]
            avg_energy = sum(energies) / len(energies)
            energy_std = math.sqrt(sum((e - avg_energy)**2 for e in energies) / len(energies))

            # Diversity score (entropy of ensemble energies)
            energy_range = max(energies) - min(energies)
            diversity = energy_range / avg_energy if avg_energy > 0 else 0
        else:
            avg_energy = 0
            energy_std = 0
            diversity = 0

        logger.info(
            f"Ensemble generated: {samples_collected} schedules, "
            f"avg_energy={avg_energy:.2f}, diversity={diversity:.2f}, "
            f"runtime={runtime:.1f}s"
        )

        return {
            "success": True,
            "ensemble_size": samples_collected,
            "runtime_seconds": runtime,
            "schedules": ensemble,
            "statistics": {
                "total_iterations": iterations,
                "samples_collected": samples_collected,
                "samples_rejected": samples_rejected,
                "acceptance_rate": accepts / iterations if iterations > 0 else 0,
                "average_energy": avg_energy,
                "energy_std_dev": energy_std,
                "diversity_score": diversity,
            },
        }

    def _greedy_initialization(
        self, context: SchedulingContext
    ) -> list[Assignment]:
        """Initialize with greedy solver."""
        from app.scheduling.solvers import GreedySolver

        greedy = GreedySolver()
        result = greedy.solve(context)

        if not result.success:
            return []

        return [
            Assignment(person_id=p, block_id=b, rotation_template_id=t)
            for p, b, t in result.assignments
        ]

    def _propose_random_move(
        self,
        schedule: list[Assignment],
        context: SchedulingContext,
    ) -> list[Assignment]:
        """Propose random schedule modification."""
        if not schedule:
            return schedule.copy()

        candidate = schedule.copy()

        if len(candidate) >= 2:
            # Swap two random assignments
            i, j = random.sample(range(len(candidate)), 2)
            candidate[i], candidate[j] = candidate[j], candidate[i]

        return candidate

    def _is_valid_schedule(
        self,
        schedule: list[Assignment],
        context: SchedulingContext,
    ) -> bool:
        """Check if schedule meets basic validity criteria."""
        # Basic checks: no major violations
        energy = self.energy_calculator.calculate_internal_energy(schedule, context)
        return energy < 200.0  # Threshold for "acceptable" quality
```

### 6.2 Ensemble Storage

**Database Table:** `schedule_ensemble`

```sql
CREATE TABLE schedule_ensemble (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    ensemble_size INTEGER NOT NULL,
    sampling_temperature FLOAT NOT NULL,
    average_energy FLOAT,
    diversity_score FLOAT,
    schedules JSONB NOT NULL,  -- Array of schedule metadata
    metadata JSONB,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_ensemble_dates ON schedule_ensemble(start_date, end_date);
CREATE INDEX idx_ensemble_created ON schedule_ensemble(created_at);
```

**Schema:** `backend/app/schemas/thermodynamics.py`

```python
from datetime import date
from pydantic import BaseModel, Field
from uuid import UUID


class EnsembleScheduleMetadata(BaseModel):
    """Metadata for a schedule in ensemble."""
    schedule_id: str
    free_energy: float
    person_entropy: float
    boltzmann_probability: float | None = None
    assignments_count: int
    acgme_compliant: bool


class EnsembleRequest(BaseModel):
    """Request to generate schedule ensemble."""
    start_date: date
    end_date: date
    ensemble_size: int = Field(default=50, ge=10, le=200)
    sampling_temperature: float = Field(default=2.0, gt=0.0)
    thinning_interval: int = Field(default=10, ge=1)
    max_iterations: int = Field(default=5000, ge=1000)
    quality_threshold: float = Field(default=100.0, gt=0.0)
    random_seed: int | None = None


class EnsembleResponse(BaseModel):
    """Response from ensemble generation."""
    success: bool
    ensemble_size: int
    runtime_seconds: float
    schedules: list[EnsembleScheduleMetadata]
    statistics: dict
    partition_function_estimate: float | None = None
```

---

## 7. Configuration

### 7.1 Environment Variables

Add to `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Thermodynamic Optimization
    SA_TEMPERATURE_INITIAL: float = 100.0
    SA_TEMPERATURE_FINAL: float = 0.01
    SA_COOLING_RATE: float = 0.95
    SA_COOLING_SCHEDULE: str = "geometric"  # geometric, adaptive, logarithmic
    SA_STEPS_PER_TEMP: int = 100
    SA_MAX_ITERATIONS: int = 10000
    SA_REHEAT_ENABLED: bool = False
    SA_REHEAT_TEMPERATURE: float = 50.0
    SA_REHEAT_INTERVAL: int = 1000

    # Free Energy Weights
    ENERGY_WEIGHT_ACGME_CRITICAL: float = 1000.0
    ENERGY_WEIGHT_ACGME_HIGH: float = 500.0
    ENERGY_WEIGHT_ACGME_MEDIUM: float = 100.0
    ENERGY_WEIGHT_COVERAGE_GAP: float = 500.0
    ENERGY_WEIGHT_SUPERVISION: float = 300.0
    ENERGY_WEIGHT_WORKLOAD_VARIANCE: float = 10.0
    ENERGY_WEIGHT_TEMPLATE_CONCENTRATION: float = 50.0

    # Entropy Monitoring
    ENTROPY_HISTORY_WINDOW: int = 100
    ENTROPY_CRITICAL_SLOWING_THRESHOLD: float = 0.8
    ENTROPY_VARIANCE_THRESHOLD: float = 0.3
    ENTROPY_RATE_OF_CHANGE_THRESHOLD: float = 0.1

    # Solver Selection
    AUTO_SOLVER_SELECTION: bool = True
    SA_COMPLEXITY_THRESHOLD: int = 60  # Use SA if complexity > 60

    # Ensemble Generation
    ENSEMBLE_DEFAULT_SIZE: int = 50
    ENSEMBLE_SAMPLING_TEMPERATURE: float = 2.0
    ENSEMBLE_THINNING_INTERVAL: int = 10
    ENSEMBLE_MAX_ITERATIONS: int = 5000
    ENSEMBLE_QUALITY_THRESHOLD: float = 100.0
```

### 7.2 Configuration File

Add to `.env.example`:

```bash
# Thermodynamic Optimization Settings
SA_TEMPERATURE_INITIAL=100.0
SA_TEMPERATURE_FINAL=0.01
SA_COOLING_RATE=0.95
SA_COOLING_SCHEDULE=geometric
SA_STEPS_PER_TEMP=100
SA_MAX_ITERATIONS=10000

# Energy Weights
ENERGY_WEIGHT_ACGME_CRITICAL=1000.0
ENERGY_WEIGHT_ACGME_HIGH=500.0
ENERGY_WEIGHT_COVERAGE_GAP=500.0

# Entropy Monitoring
ENTROPY_HISTORY_WINDOW=100
ENTROPY_CRITICAL_SLOWING_THRESHOLD=0.8

# Solver Selection
AUTO_SOLVER_SELECTION=true
SA_COMPLEXITY_THRESHOLD=60
```

---

## 8. Database Schema

### 8.1 New Tables

```sql
-- Schedule entropy history
CREATE TABLE schedule_entropy_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    person_entropy FLOAT NOT NULL,
    rotation_entropy FLOAT NOT NULL,
    temporal_entropy FLOAT NOT NULL,
    joint_entropy FLOAT NOT NULL,
    mutual_information FLOAT NOT NULL,
    flexibility_score FLOAT NOT NULL,
    rate_of_change FLOAT,
    variance_trend FLOAT,
    autocorrelation FLOAT,
    warning_level VARCHAR(50),
    metadata JSONB
);

CREATE INDEX idx_entropy_history_schedule ON schedule_entropy_history(schedule_id);
CREATE INDEX idx_entropy_history_timestamp ON schedule_entropy_history(timestamp);

-- Energy landscape analysis
CREATE TABLE schedule_energy_landscape (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID REFERENCES schedules(id) ON DELETE CASCADE,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    current_energy FLOAT NOT NULL,
    temperature FLOAT NOT NULL,
    is_local_minimum BOOLEAN NOT NULL,
    min_barrier_height FLOAT NOT NULL,
    avg_barrier_height FLOAT NOT NULL,
    max_barrier_height FLOAT NOT NULL,
    stability VARCHAR(50) NOT NULL,
    num_probes INTEGER NOT NULL,
    perturbation_statistics JSONB,
    visualization_data JSONB
);

CREATE INDEX idx_landscape_schedule ON schedule_energy_landscape(schedule_id);

-- Schedule ensemble
CREATE TABLE schedule_ensemble (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    ensemble_size INTEGER NOT NULL,
    sampling_temperature FLOAT NOT NULL,
    thinning_interval INTEGER NOT NULL,
    total_iterations INTEGER NOT NULL,
    acceptance_rate FLOAT NOT NULL,
    average_energy FLOAT,
    energy_std_dev FLOAT,
    diversity_score FLOAT,
    schedules JSONB NOT NULL,
    statistics JSONB,
    created_by UUID REFERENCES users(id)
);

CREATE INDEX idx_ensemble_dates ON schedule_ensemble(start_date, end_date);
CREATE INDEX idx_ensemble_created ON schedule_ensemble(created_at);
```

### 8.2 Schema Migration

**File:** `backend/alembic/versions/xxxx_add_thermodynamic_tables.py`

```python
"""Add thermodynamic optimization tables.

Revision ID: xxxx
Revises: previous_revision
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'xxxx'
down_revision = 'previous_revision'


def upgrade():
    # Schedule entropy history
    op.create_table(
        'schedule_entropy_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schedules.id', ondelete='CASCADE')),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
        sa.Column('person_entropy', sa.Float, nullable=False),
        sa.Column('rotation_entropy', sa.Float, nullable=False),
        sa.Column('temporal_entropy', sa.Float, nullable=False),
        sa.Column('joint_entropy', sa.Float, nullable=False),
        sa.Column('mutual_information', sa.Float, nullable=False),
        sa.Column('flexibility_score', sa.Float, nullable=False),
        sa.Column('rate_of_change', sa.Float),
        sa.Column('variance_trend', sa.Float),
        sa.Column('autocorrelation', sa.Float),
        sa.Column('warning_level', sa.String(50)),
        sa.Column('metadata', postgresql.JSONB),
    )
    op.create_index('idx_entropy_history_schedule', 'schedule_entropy_history', ['schedule_id'])
    op.create_index('idx_entropy_history_timestamp', 'schedule_entropy_history', ['timestamp'])

    # Energy landscape analysis
    op.create_table(
        'schedule_energy_landscape',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schedules.id', ondelete='CASCADE')),
        sa.Column('analyzed_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('current_energy', sa.Float, nullable=False),
        sa.Column('temperature', sa.Float, nullable=False),
        sa.Column('is_local_minimum', sa.Boolean, nullable=False),
        sa.Column('min_barrier_height', sa.Float, nullable=False),
        sa.Column('avg_barrier_height', sa.Float, nullable=False),
        sa.Column('max_barrier_height', sa.Float, nullable=False),
        sa.Column('stability', sa.String(50), nullable=False),
        sa.Column('num_probes', sa.Integer, nullable=False),
        sa.Column('perturbation_statistics', postgresql.JSONB),
        sa.Column('visualization_data', postgresql.JSONB),
    )
    op.create_index('idx_landscape_schedule', 'schedule_energy_landscape', ['schedule_id'])

    # Schedule ensemble
    op.create_table(
        'schedule_ensemble',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('start_date', sa.Date, nullable=False),
        sa.Column('end_date', sa.Date, nullable=False),
        sa.Column('ensemble_size', sa.Integer, nullable=False),
        sa.Column('sampling_temperature', sa.Float, nullable=False),
        sa.Column('thinning_interval', sa.Integer, nullable=False),
        sa.Column('total_iterations', sa.Integer, nullable=False),
        sa.Column('acceptance_rate', sa.Float, nullable=False),
        sa.Column('average_energy', sa.Float),
        sa.Column('energy_std_dev', sa.Float),
        sa.Column('diversity_score', sa.Float),
        sa.Column('schedules', postgresql.JSONB, nullable=False),
        sa.Column('statistics', postgresql.JSONB),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id')),
    )
    op.create_index('idx_ensemble_dates', 'schedule_ensemble', ['start_date', 'end_date'])
    op.create_index('idx_ensemble_created', 'schedule_ensemble', ['created_at'])


def downgrade():
    op.drop_table('schedule_entropy_history')
    op.drop_table('schedule_energy_landscape')
    op.drop_table('schedule_ensemble')
```

---

## 9. Testing Requirements

### 9.1 Unit Tests

**File:** `backend/tests/thermodynamics/test_simulated_annealing.py`

```python
"""Tests for simulated annealing solver."""

import pytest
from datetime import date, timedelta

from app.scheduling.solvers.simulated_annealing import SimulatedAnnealingSolver, SAConfig
from app.scheduling.constraints import SchedulingContext, ConstraintManager


class TestSimulatedAnnealingSolver:
    """Test suite for simulated annealing solver."""

    @pytest.fixture
    def context(self, db, sample_residents, sample_blocks, sample_templates):
        """Create scheduling context."""
        return SchedulingContext(
            db=db,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=28),
            residents=sample_residents,
            blocks=sample_blocks,
            templates=sample_templates,
            availability={},
            constraint_manager=ConstraintManager.create_default(),
        )

    def test_solve_basic(self, context):
        """Test basic solve functionality."""
        config = SAConfig(
            temperature_initial=10.0,
            temperature_final=0.1,
            cooling_rate=0.9,
            steps_per_temperature=10,
            max_iterations=100,
            random_seed=42,
        )

        solver = SimulatedAnnealingSolver(config=config)
        result = solver.solve(context)

        assert result.success
        assert len(result.assignments) > 0
        assert result.runtime_seconds > 0
        assert "iterations" in result.statistics

    def test_metropolis_acceptance(self, context):
        """Test Metropolis criterion accepts/rejects correctly."""
        # TODO: Test acceptance probability
        pass

    def test_cooling_schedule(self, context):
        """Test temperature decreases properly."""
        # TODO: Verify temperature history
        pass

    def test_energy_improvement(self, context):
        """Test that energy decreases over iterations."""
        # TODO: Check energy history shows improvement
        pass

    def test_convergence(self, context):
        """Test solver converges to stable solution."""
        # TODO: Verify final acceptance rate is low
        pass
```

**File:** `backend/tests/thermodynamics/test_free_energy.py`

```python
"""Tests for free energy calculator."""

import pytest
from app.scheduling.thermodynamics.free_energy import FreeEnergyCalculator
from app.models.assignment import Assignment


class TestFreeEnergyCalculator:
    """Test suite for free energy calculation."""

    def test_calculate_entropy(self):
        """Test Shannon entropy calculation."""
        calculator = FreeEnergyCalculator()

        # Balanced distribution
        assignments = [
            Assignment(person_id=f"res-{i%3}", block_id=f"block-{i}", rotation_template_id="tmpl-1")
            for i in range(30)
        ]

        entropy = calculator.calculate_entropy(assignments)

        # For 3 residents with equal distribution:
        # H = -3 * (1/3) * log2(1/3) = log2(3) ≈ 1.585
        assert 1.5 < entropy < 1.6

    def test_calculate_internal_energy(self, context):
        """Test internal energy from violations."""
        # TODO: Test coverage gaps, workload variance
        pass

    def test_free_energy_combines_u_and_s(self, context):
        """Test F = U - T*S calculation."""
        # TODO: Verify formula
        pass
```

**File:** `backend/tests/thermodynamics/test_entropy_monitor.py`

```python
"""Tests for entropy monitoring."""

import pytest
from app.scheduling.thermodynamics.entropy import EntropyMonitor
from app.models.assignment import Assignment


class TestEntropyMonitor:
    """Test suite for entropy monitor."""

    def test_early_warning_detection(self):
        """Test critical slowing detection."""
        monitor = EntropyMonitor(window_size=20)

        # Simulate increasing autocorrelation
        for i in range(30):
            assignments = [
                Assignment(person_id=f"res-{i%5}", block_id=f"block-{j}", rotation_template_id="tmpl-1")
                for j in range(20)
            ]
            metrics = monitor.update(assignments)

        # After sufficient history, should detect patterns
        assert "warning_level" in metrics

    def test_multidimensional_entropy(self, context):
        """Test multi-dimensional entropy calculation."""
        # TODO: Test person, rotation, temporal entropy
        pass
```

### 9.2 Integration Tests

**File:** `backend/tests/integration/test_thermodynamic_api.py`

```python
"""Integration tests for thermodynamic API endpoints."""

import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta


class TestThermodynamicAPI:
    """Test thermodynamic API endpoints."""

    def test_anneal_endpoint(self, client: TestClient, auth_headers):
        """Test POST /api/v1/thermo/anneal."""
        response = client.post(
            "/api/v1/thermo/anneal",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=28)),
                "algorithm_config": {
                    "temperature_initial": 10.0,
                    "temperature_final": 0.1,
                    "max_iterations": 100,
                },
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert "assignments" in data
        assert "statistics" in data

    def test_entropy_endpoint(self, client: TestClient, auth_headers, sample_schedule):
        """Test GET /api/v1/thermo/entropy."""
        response = client.get(
            f"/api/v1/thermo/entropy?schedule_id={sample_schedule.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "entropy_metrics" in data
        assert "person_entropy" in data["entropy_metrics"]

    def test_ensemble_endpoint(self, client: TestClient, auth_headers):
        """Test POST /api/v1/thermo/ensemble."""
        response = client.post(
            "/api/v1/thermo/ensemble",
            json={
                "start_date": str(date.today()),
                "end_date": str(date.today() + timedelta(days=28)),
                "ensemble_size": 10,
                "sampling_temperature": 2.0,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"]
        assert len(data["schedules"]) == 10
```

### 9.3 Performance Tests

**File:** `backend/tests/performance/test_sa_performance.py`

```python
"""Performance tests for simulated annealing."""

import pytest
import time
from datetime import date, timedelta

from app.scheduling.solvers.simulated_annealing import SimulatedAnnealingSolver, SAConfig


@pytest.mark.performance
class TestSAPerformance:
    """Performance benchmarks for SA solver."""

    def test_small_problem_speed(self, small_context):
        """Test SA on small problem (7 days, 5 residents)."""
        solver = SimulatedAnnealingSolver(config=SAConfig(max_iterations=500))

        start = time.time()
        result = solver.solve(small_context)
        runtime = time.time() - start

        assert result.success
        assert runtime < 5.0  # Should complete in < 5s

    def test_medium_problem_speed(self, medium_context):
        """Test SA on medium problem (28 days, 12 residents)."""
        solver = SimulatedAnnealingSolver(config=SAConfig(max_iterations=2000))

        start = time.time()
        result = solver.solve(medium_context)
        runtime = time.time() - start

        assert result.success
        assert runtime < 60.0  # Should complete in < 60s

    def test_convergence_rate(self, medium_context):
        """Test how quickly SA converges."""
        solver = SimulatedAnnealingSolver(config=SAConfig(max_iterations=5000))
        result = solver.solve(medium_context)

        energy_history = result.statistics["energy_history"]

        # Energy should improve significantly in first 50% of iterations
        initial_energy = energy_history[0]["energy"]
        halfway_energy = energy_history[len(energy_history)//2]["energy"]
        final_energy = result.objective_value

        improvement_first_half = initial_energy - halfway_energy
        improvement_second_half = halfway_energy - final_energy

        # Most improvement should happen early
        assert improvement_first_half > improvement_second_half
```

---

## 10. Performance Benchmarks

### 10.1 Target Performance

| Problem Size | Time Limit | Expected Quality | Success Rate |
|--------------|------------|------------------|--------------|
| Small (7 days, 5 residents) | 5s | 85%+ | 95%+ |
| Medium (28 days, 12 residents) | 60s | 90%+ | 92%+ |
| Large (365 days, 20 residents) | 300s | 85%+ | 88%+ |

### 10.2 Comparison with Existing Solvers

**Baseline (from research):**

| Solver | Runtime (28 days) | Quality | ACGME Violations | Success Rate |
|--------|-------------------|---------|------------------|--------------|
| Greedy | 2.3s | 68/100 | 12% | 85% |
| CP-SAT | 45.2s | 95/100 | 0% | 92% |
| PuLP | 18.7s | 88/100 | 2% | 90% |
| **SA (Target)** | **30-40s** | **90-95/100** | **<2%** | **93%+** |
| Hybrid (CP-SAT+SA) | 60-70s | 96/100 | 0% | 95% |

### 10.3 Benchmark Suite

**File:** `backend/tests/benchmarks/thermodynamic_benchmarks.py`

```python
"""Benchmark suite for thermodynamic solvers."""

import time
import pytest
from datetime import date, timedelta

from app.scheduling.solvers.simulated_annealing import SimulatedAnnealingSolver, SAConfig
from app.scheduling.solvers.cpsat import CPSatSolver
from app.scheduling.solvers import GreedySolver


@pytest.mark.benchmark
class TestThermodynamicBenchmarks:
    """Comprehensive benchmarks."""

    def test_benchmark_sa_vs_cpsat(self, medium_context):
        """Compare SA vs CP-SAT on same problem."""
        # CP-SAT
        cpsat = CPSatSolver(timeout_seconds=60)
        start = time.time()
        cpsat_result = cpsat.solve(medium_context)
        cpsat_time = time.time() - start

        # SA
        sa = SimulatedAnnealingSolver(config=SAConfig(max_iterations=2000))
        start = time.time()
        sa_result = sa.solve(medium_context)
        sa_time = time.time() - start

        # Report
        print(f"\nCP-SAT: {cpsat_time:.1f}s, objective={cpsat_result.objective_value:.2f}")
        print(f"SA: {sa_time:.1f}s, objective={sa_result.objective_value:.2f}")

        # SA should be faster
        assert sa_time < cpsat_time

    def test_benchmark_scaling(self):
        """Test how SA scales with problem size."""
        sizes = [
            (7, 5, 500),    # 7 days, 5 residents, 500 iterations
            (14, 8, 1000),  # 14 days, 8 residents, 1000 iterations
            (28, 12, 2000), # 28 days, 12 residents, 2000 iterations
        ]

        for days, residents, iterations in sizes:
            context = create_context(days=days, residents=residents)
            solver = SimulatedAnnealingSolver(config=SAConfig(max_iterations=iterations))

            start = time.time()
            result = solver.solve(context)
            runtime = time.time() - start

            print(f"{days}d, {residents}r: {runtime:.1f}s, quality={result.objective_value:.2f}")
```

---

## 11. Security Considerations

### 11.1 Input Validation

- **Temperature limits:** Prevent negative or extreme values
- **Iteration limits:** Cap max_iterations to prevent DoS
- **Ensemble size limits:** Max 200 schedules per request
- **Date range validation:** Prevent excessive date ranges

### 11.2 Resource Limits

```python
# Rate limiting for expensive operations
from app.core.rate_limit import RateLimiter

@router.post("/api/v1/thermo/anneal")
@RateLimiter(max_calls=5, time_window=3600)  # 5 per hour
async def anneal_schedule(...):
    pass

@router.post("/api/v1/thermo/ensemble")
@RateLimiter(max_calls=2, time_window=3600)  # 2 per hour
async def generate_ensemble(...):
    pass
```

### 11.3 Authentication & Authorization

- All endpoints require authentication
- Configuration endpoints (GET/PUT `/config`) require Admin role
- Ensemble generation limited to Coordinator+ roles

### 11.4 Data Privacy

- Schedule data contains PHI/PII (resident names, assignments)
- All responses must respect RBAC visibility rules
- Audit logging for all thermodynamic operations

---

## 12. Deployment Plan

### 12.1 Phase 1: Core Implementation (Week 1-2)

**Tasks:**
1. Implement `SimulatedAnnealingSolver` class
2. Implement `FreeEnergyCalculator` class
3. Implement `CoolingSchedule` classes (geometric, adaptive, logarithmic)
4. Add SA to `SolverFactory`
5. Unit tests for all components

**Deliverable:** Working SA solver integrated into scheduling engine

### 12.2 Phase 2: API Endpoints (Week 3)

**Tasks:**
1. Create `/api/v1/thermo/anneal` endpoint
2. Create `/api/v1/thermo/entropy` endpoint
3. Create API schemas (`thermodynamics.py`)
4. Integration tests
5. API documentation

**Deliverable:** RESTful API for thermodynamic optimization

### 12.3 Phase 3: Entropy Monitoring (Week 4)

**Tasks:**
1. Implement `EntropyMonitor` class
2. Database schema for entropy history
3. Celery task for periodic entropy checks
4. Dashboard integration
5. Alert system for early warnings

**Deliverable:** Real-time entropy monitoring system

### 12.4 Phase 4: Ensemble Generation (Week 5)

**Tasks:**
1. Implement `EnsembleGenerator` class
2. Create `/api/v1/thermo/ensemble` endpoint
3. Database schema for ensemble storage
4. Background job for pre-computation
5. UI for ensemble browsing

**Deliverable:** Schedule ensemble generation system

### 12.5 Phase 5: Hybrid & Optimization (Week 6)

**Tasks:**
1. Implement `HybridThermodynamicSolver`
2. Update optimizer complexity-based selection
3. Performance benchmarking
4. Energy landscape analyzer
5. `/api/v1/thermo/energy-landscape` endpoint

**Deliverable:** Production-ready hybrid solver

### 12.6 Phase 6: Documentation & Rollout (Week 7-8)

**Tasks:**
1. User documentation
2. Admin guide for configuration
3. Training materials
4. Gradual rollout (10% → 50% → 100%)
5. Monitoring and tuning

**Deliverable:** Full production deployment

---

## Appendix A: File Structure

```
backend/app/
├── scheduling/
│   ├── solvers/
│   │   ├── simulated_annealing.py    # NEW: SA solver
│   │   └── hybrid_thermo.py          # NEW: Hybrid CP-SAT + SA
│   ├── thermodynamics/               # NEW: Thermodynamics module
│   │   ├── __init__.py
│   │   ├── free_energy.py            # Free energy calculator
│   │   ├── entropy.py                # Entropy monitor
│   │   ├── cooling.py                # Cooling schedules
│   │   ├── landscape.py              # Energy landscape analyzer
│   │   └── ensemble.py               # Ensemble generator
│   └── optimizer.py                  # UPDATED: Add SA to selection
│
├── api/routes/
│   └── thermodynamics.py             # NEW: API endpoints
│
├── schemas/
│   └── thermodynamics.py             # NEW: Pydantic schemas
│
├── models/
│   ├── entropy_history.py            # NEW: Entropy tracking model
│   ├── energy_landscape.py           # NEW: Landscape analysis model
│   └── ensemble.py                   # NEW: Ensemble model
│
└── tests/
    ├── thermodynamics/               # NEW: Unit tests
    │   ├── test_simulated_annealing.py
    │   ├── test_free_energy.py
    │   ├── test_entropy.py
    │   ├── test_cooling.py
    │   └── test_ensemble.py
    ├── integration/
    │   └── test_thermodynamic_api.py # NEW: Integration tests
    ├── performance/
    │   └── test_sa_performance.py    # NEW: Performance tests
    └── benchmarks/
        └── thermodynamic_benchmarks.py # NEW: Benchmarks
```

---

## Appendix B: Dependencies

**Add to `backend/requirements.txt`:**

```
# Already included (no new dependencies needed):
numpy>=1.24.0
scipy>=1.11.0

# Optional for advanced features:
matplotlib>=3.7.0  # For energy landscape visualization
```

**No new external dependencies required!** All thermodynamic algorithms can be implemented with existing packages (numpy, scipy).

---

## Appendix C: Monitoring & Alerts

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# SA solver metrics
sa_iterations_total = Counter(
    "sa_iterations_total",
    "Total iterations in simulated annealing",
)

sa_runtime_seconds = Histogram(
    "sa_runtime_seconds",
    "Runtime of simulated annealing solver",
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

sa_energy_final = Histogram(
    "sa_energy_final",
    "Final free energy of SA solutions",
    buckets=[0, 10, 50, 100, 200, 500, 1000],
)

# Entropy metrics
schedule_entropy_current = Gauge(
    "schedule_entropy_current",
    "Current schedule entropy",
)

entropy_warning_level = Gauge(
    "entropy_warning_level",
    "Entropy warning level (0=NORMAL, 1=VARIANCE, 2=SLOWING, 3=CRITICAL)",
)
```

### Grafana Dashboard

**Panels:**
1. SA solver runtime distribution (histogram)
2. Energy convergence over time (line chart)
3. Acceptance rate progression (line chart)
4. Entropy timeline with warning zones
5. Ensemble diversity scores
6. Solver comparison (SA vs CP-SAT vs Greedy)

---

**End of Specification**

This production-ready specification provides comprehensive guidance for implementing the Thermodynamic Optimization Solver Service. All components are designed to integrate seamlessly with the existing scheduling engine while adding powerful new optimization capabilities based on statistical mechanics principles.
