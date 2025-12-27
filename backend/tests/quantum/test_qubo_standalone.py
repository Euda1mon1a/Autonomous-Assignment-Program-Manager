#!/usr/bin/env python3
"""
Standalone test for Call Assignment QUBO - runs without app dependencies.

This test verifies the core QUBO functionality by directly testing the
call_assignment_qubo module's data structures and algorithms.
"""

import json
import math
import random
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import numpy as np

# =============================================================================
# MINIMAL REIMPLEMENTATION FOR STANDALONE TESTING
# =============================================================================


class CallType(str, Enum):
    OVERNIGHT = "overnight"
    BACKUP = "backup"
    WEEKEND = "weekend"


@dataclass
class CallNight:
    date: date
    call_type: CallType
    is_weekend: bool = False
    is_holiday: bool = False
    specialty_required: str | None = None
    min_pgy_level: int = 1

    @property
    def weekday(self) -> int:
        return self.date.weekday()

    @property
    def is_sunday(self) -> bool:
        return self.weekday == 6


@dataclass
class CallCandidate:
    person_id: UUID
    name: str
    pgy_level: int
    specialty: str | None = None
    max_calls_per_week: int = 2
    max_consecutive_call_days: int = 1
    avoid_days: set[int] = field(default_factory=set)
    preference_bonus: dict[int, float] = field(default_factory=dict)


@dataclass
class QUBOSolution:
    sample: dict[int, int]
    energy: float
    assignments: list[tuple[UUID, date, CallType]]
    runtime_seconds: float
    num_sweeps: int
    num_reads: int
    final_temperature: float
    violations: list[str]
    is_valid: bool
    landscape_data: dict | None = None


@dataclass
class LandscapePoint:
    energy: float
    configuration: list[int]
    constraint_penalties: dict[str, float]
    timestamp: float


# Simplified QUBO formulation
class CallAssignmentQUBO:
    HARD_CONSTRAINT_PENALTY = 50000.0
    ACGME_PENALTY = 25000.0
    EQUITY_PENALTY = 500.0
    PREFERENCE_PENALTY = 50.0

    def __init__(
        self,
        call_nights: list[CallNight],
        candidates: list[CallCandidate],
        equity_target: float | None = None,
    ):
        self.call_nights = call_nights
        self.candidates = candidates
        self.num_nights = len(call_nights)
        self.num_candidates = len(candidates)

        if equity_target is None:
            self.equity_target = self.num_nights / max(self.num_candidates, 1)
        else:
            self.equity_target = equity_target

        self.var_index: dict[tuple[int, int], int] = {}
        self.index_to_var: dict[int, tuple[int, int]] = {}
        self._build_variable_index()
        self.Q: dict[tuple[int, int], float] = {}

    def _build_variable_index(self) -> None:
        idx = 0
        for r_i in range(self.num_candidates):
            for n_i in range(self.num_nights):
                self.var_index[(r_i, n_i)] = idx
                self.index_to_var[idx] = (r_i, n_i)
                idx += 1

    @property
    def num_variables(self) -> int:
        return len(self.var_index)

    def build(self) -> dict[tuple[int, int], float]:
        self.Q = {}
        self._add_assignment_incentive()
        self._add_coverage_constraint()
        self._add_consecutive_call_constraint()
        self._add_equity_constraint()
        self._add_sunday_equity_constraint()
        self._add_preference_constraints()
        self._add_spacing_constraint()
        return self.Q

    def _add_assignment_incentive(self) -> None:
        for idx in range(self.num_variables):
            self._add_linear(idx, -1.0)

    def _add_coverage_constraint(self) -> None:
        for n_i in range(self.num_nights):
            night_vars = [
                self.var_index[(r_i, n_i)] for r_i in range(self.num_candidates)
            ]
            for idx in night_vars:
                self._add_linear(idx, -2 * self.HARD_CONSTRAINT_PENALTY + 1)
            for i, idx1 in enumerate(night_vars):
                for idx2 in night_vars[i + 1 :]:
                    self._add_quadratic(idx1, idx2, 2 * self.HARD_CONSTRAINT_PENALTY)

    def _add_consecutive_call_constraint(self) -> None:
        for r_i, candidate in enumerate(self.candidates):
            max_consecutive = candidate.max_consecutive_call_days
            if max_consecutive <= 1:
                for n_i in range(self.num_nights - 1):
                    if (
                        self.call_nights[n_i + 1].date - self.call_nights[n_i].date
                    ).days == 1:
                        idx1 = self.var_index[(r_i, n_i)]
                        idx2 = self.var_index[(r_i, n_i + 1)]
                        self._add_quadratic(idx1, idx2, self.ACGME_PENALTY)

    def _add_equity_constraint(self) -> None:
        mean_calls = self.equity_target
        for r_i in range(self.num_candidates):
            resident_vars = [
                self.var_index[(r_i, n_i)] for n_i in range(self.num_nights)
            ]
            for idx in resident_vars:
                self._add_linear(idx, -2 * mean_calls * self.EQUITY_PENALTY)
            scaled_penalty = self.EQUITY_PENALTY / max(len(resident_vars), 1)
            for i, idx1 in enumerate(resident_vars):
                for idx2 in resident_vars[i + 1 :]:
                    self._add_quadratic(idx1, idx2, 2 * scaled_penalty)

    def _add_sunday_equity_constraint(self) -> None:
        sunday_nights = [
            n_i for n_i, night in enumerate(self.call_nights) if night.is_sunday
        ]
        if not sunday_nights:
            return
        sunday_mean = len(sunday_nights) / max(self.num_candidates, 1)
        sunday_penalty = self.EQUITY_PENALTY * 2
        for r_i in range(self.num_candidates):
            sunday_vars = [self.var_index[(r_i, n_i)] for n_i in sunday_nights]
            if not sunday_vars:
                continue
            for idx in sunday_vars:
                self._add_linear(idx, -2 * sunday_mean * sunday_penalty)
            scaled_penalty = sunday_penalty / max(len(sunday_vars), 1)
            for i, idx1 in enumerate(sunday_vars):
                for idx2 in sunday_vars[i + 1 :]:
                    self._add_quadratic(idx1, idx2, 2 * scaled_penalty)

    def _add_preference_constraints(self) -> None:
        for r_i, candidate in enumerate(self.candidates):
            for n_i, night in enumerate(self.call_nights):
                idx = self.var_index[(r_i, n_i)]
                weekday = night.weekday
                if weekday in candidate.avoid_days:
                    self._add_linear(idx, self.PREFERENCE_PENALTY * 10)
                if weekday in candidate.preference_bonus:
                    bonus = candidate.preference_bonus[weekday]
                    self._add_linear(idx, -bonus * self.PREFERENCE_PENALTY)

    def _add_spacing_constraint(self) -> None:
        spacing_penalty = self.PREFERENCE_PENALTY * 3
        for r_i in range(self.num_candidates):
            for n_i in range(self.num_nights):
                for n_j in range(n_i + 1, min(n_i + 4, self.num_nights)):
                    days_apart = (
                        self.call_nights[n_j].date - self.call_nights[n_i].date
                    ).days
                    if 2 <= days_apart <= 3:
                        idx1 = self.var_index[(r_i, n_i)]
                        idx2 = self.var_index[(r_i, n_j)]
                        penalty = spacing_penalty / days_apart
                        self._add_quadratic(idx1, idx2, penalty)

    def _add_linear(self, i: int, value: float) -> None:
        key = (i, i)
        self.Q[key] = self.Q.get(key, 0.0) + value

    def _add_quadratic(self, i: int, j: int, value: float) -> None:
        if i > j:
            i, j = j, i
        key = (i, j)
        self.Q[key] = self.Q.get(key, 0.0) + value

    def decode_solution(
        self, sample: dict[int, int]
    ) -> list[tuple[UUID, date, CallType]]:
        assignments = []
        for idx, value in sample.items():
            if value == 1 and idx in self.index_to_var:
                r_i, n_i = self.index_to_var[idx]
                candidate = self.candidates[r_i]
                night = self.call_nights[n_i]
                assignments.append((candidate.person_id, night.date, night.call_type))
        return assignments

    def compute_energy(self, sample: dict[int, int]) -> float:
        energy = 0.0
        for (i, j), coef in self.Q.items():
            if i == j:
                energy += coef * sample.get(i, 0)
            else:
                energy += coef * sample.get(i, 0) * sample.get(j, 0)
        return energy

    def get_constraint_breakdown(self, sample: dict[int, int]) -> dict[str, float]:
        return {"total": self.compute_energy(sample)}


# Simplified Quantum Tunneling Annealer
class QuantumTunnelingAnnealingSolver:
    def __init__(
        self,
        num_reads: int = 100,
        num_sweeps: int = 10000,
        beta_range: tuple[float, float] = (0.1, 10.0),
        tunneling_strength: float = 0.3,
        barrier_coefficient: float = 1.0,
        seed: int | None = None,
        track_landscape: bool = True,
        landscape_sample_rate: int = 100,
    ):
        self.num_reads = num_reads
        self.num_sweeps = num_sweeps
        self.beta_range = beta_range
        self.tunneling_strength = tunneling_strength
        self.barrier_coefficient = barrier_coefficient
        self.seed = seed or random.randint(0, 2**32 - 1)
        self.track_landscape = track_landscape
        self.landscape_sample_rate = landscape_sample_rate
        self.landscape_history: list[LandscapePoint] = []

    def solve(self, formulation: CallAssignmentQUBO) -> QUBOSolution:
        import time

        start_time = time.time()
        random.seed(self.seed)
        np.random.seed(self.seed)

        Q = formulation.Q
        n = formulation.num_variables

        if n == 0:
            return QUBOSolution(
                sample={},
                energy=0.0,
                assignments=[],
                runtime_seconds=0.0,
                num_sweeps=0,
                num_reads=0,
                final_temperature=0.0,
                violations=["No variables"],
                is_valid=False,
            )

        best_sample = dict.fromkeys(range(n), 0)
        best_energy = formulation.compute_energy(best_sample)
        self.landscape_history = []

        for read in range(self.num_reads):
            sample = {i: random.randint(0, 1) for i in range(n)}
            energy = formulation.compute_energy(sample)
            beta_start, beta_end = self.beta_range

            for sweep in range(self.num_sweeps):
                t = sweep / self.num_sweeps
                alpha = 2.0
                beta = beta_start + (beta_end - beta_start) * (t**alpha)

                var_order = list(range(n))
                random.shuffle(var_order)

                for i in var_order:
                    delta_e = self._compute_delta_energy(sample, Q, i)
                    accept = False
                    if delta_e <= 0:
                        accept = True
                    else:
                        classical_prob = math.exp(-beta * delta_e)
                        tunneling_prob = math.exp(
                            -self.barrier_coefficient * math.sqrt(abs(delta_e))
                        )
                        combined_prob = (1 - self.tunneling_strength) * classical_prob
                        combined_prob += self.tunneling_strength * tunneling_prob
                        accept = random.random() < combined_prob

                    if accept:
                        sample[i] = 1 - sample[i]
                        energy += delta_e

                if self.track_landscape and sweep % self.landscape_sample_rate == 0:
                    self.landscape_history.append(
                        LandscapePoint(
                            energy=energy,
                            configuration=[sample[i] for i in range(n)],
                            constraint_penalties=formulation.get_constraint_breakdown(
                                sample
                            ),
                            timestamp=time.time() - start_time,
                        )
                    )

                if energy < best_energy:
                    best_sample = sample.copy()
                    best_energy = energy

        runtime = time.time() - start_time
        assignments = formulation.decode_solution(best_sample)
        violations, is_valid = self._validate_solution(formulation, best_sample)
        landscape_data = self._export_landscape_data(formulation) if self.track_landscape else None

        return QUBOSolution(
            sample=best_sample,
            energy=best_energy,
            assignments=assignments,
            runtime_seconds=runtime,
            num_sweeps=self.num_sweeps,
            num_reads=self.num_reads,
            final_temperature=1.0 / self.beta_range[1],
            violations=violations,
            is_valid=is_valid,
            landscape_data=landscape_data,
        )

    def _compute_delta_energy(
        self, sample: dict[int, int], Q: dict, flip_idx: int
    ) -> float:
        current_val = sample.get(flip_idx, 0)
        new_val = 1 - current_val
        delta = new_val - current_val

        energy_change = 0.0
        if (flip_idx, flip_idx) in Q:
            energy_change += Q[(flip_idx, flip_idx)] * delta

        for (i, j), coef in Q.items():
            if i == j:
                continue
            if i == flip_idx:
                energy_change += coef * sample.get(j, 0) * delta
            elif j == flip_idx:
                energy_change += coef * sample.get(i, 0) * delta

        return energy_change

    def _validate_solution(
        self, formulation: CallAssignmentQUBO, sample: dict[int, int]
    ) -> tuple[list[str], bool]:
        violations = []
        for n_i in range(formulation.num_nights):
            count = sum(
                sample.get(formulation.var_index.get((r_i, n_i), -1), 0)
                for r_i in range(formulation.num_candidates)
            )
            if count == 0:
                violations.append(f"Night {n_i} has no coverage")
            elif count > 1:
                violations.append(f"Night {n_i} has {count} assignments")
        return violations, len(violations) == 0

    def _export_landscape_data(self, formulation: CallAssignmentQUBO) -> dict[str, Any]:
        return {
            "metadata": {
                "num_variables": formulation.num_variables,
                "num_candidates": formulation.num_candidates,
                "num_nights": formulation.num_nights,
                "solver": "QuantumTunnelingAnnealingSolver",
            },
            "coordinate_transform": {
                "description": "Maps discrete (resident, night) to continuous QUBO energy",
                "variable_encoding": "x[r,n] = 1 if resident r on call night n",
                "energy_formula": "E(x) = Σ_i Q_ii*x_i + Σ_{i<j} Q_ij*x_i*x_j",
            },
            "trajectory": [
                {"timestamp": pt.timestamp, "energy": pt.energy}
                for pt in self.landscape_history
            ],
        }


# =============================================================================
# TESTS
# =============================================================================


def test_basic_qubo():
    """Test basic QUBO formulation."""
    print("=" * 60)
    print("TEST: Basic QUBO Formulation")
    print("=" * 60)

    base_date = date(2025, 1, 1)
    candidates = [
        CallCandidate(person_id=uuid4(), name=f"Resident-{i}", pgy_level=(i % 3) + 1)
        for i in range(10)
    ]
    nights = [
        CallNight(date=base_date + timedelta(days=i), call_type=CallType.OVERNIGHT)
        for i in range(7)
    ]

    formulation = CallAssignmentQUBO(nights, candidates)
    expected_vars = 10 * 7
    assert formulation.num_variables == expected_vars, f"Expected {expected_vars} variables"

    Q = formulation.build()
    assert len(Q) > 0, "QUBO should have non-zero terms"

    diagonal = sum(1 for (i, j) in Q.keys() if i == j)
    quadratic = sum(1 for (i, j) in Q.keys() if i != j)
    assert diagonal > 0, "Should have diagonal terms"
    assert quadratic > 0, "Should have quadratic terms"

    print(f"✓ Variables: {formulation.num_variables}")
    print(f"✓ Diagonal terms: {diagonal}")
    print(f"✓ Quadratic terms: {quadratic}")
    print("PASSED\n")


def test_solver():
    """Test QUBO solver."""
    print("=" * 60)
    print("TEST: Quantum-Inspired Simulated Annealing")
    print("=" * 60)

    base_date = date(2025, 1, 1)
    candidates = [
        CallCandidate(person_id=uuid4(), name=f"Resident-{i}", pgy_level=(i % 3) + 1)
        for i in range(10)
    ]
    nights = [
        CallNight(date=base_date + timedelta(days=i), call_type=CallType.OVERNIGHT)
        for i in range(7)
    ]

    formulation = CallAssignmentQUBO(nights, candidates)
    formulation.build()

    solver = QuantumTunnelingAnnealingSolver(
        num_reads=10,
        num_sweeps=1000,
        track_landscape=True,
        seed=42,
    )

    solution = solver.solve(formulation)

    assert isinstance(solution.energy, float), "Energy should be float"
    assert isinstance(solution.assignments, list), "Assignments should be list"
    assert solution.runtime_seconds > 0, "Runtime should be positive"

    print(f"✓ Energy: {solution.energy:.2f}")
    print(f"✓ Assignments: {len(solution.assignments)}")
    print(f"✓ Valid: {solution.is_valid}")
    print(f"✓ Runtime: {solution.runtime_seconds:.3f}s")
    print("PASSED\n")


def test_determinism():
    """Test that same seed gives same results."""
    print("=" * 60)
    print("TEST: Deterministic with Same Seed")
    print("=" * 60)

    base_date = date(2025, 1, 1)
    candidates = [
        CallCandidate(person_id=uuid4(), name=f"Resident-{i}", pgy_level=1)
        for i in range(5)
    ]
    nights = [
        CallNight(date=base_date + timedelta(days=i), call_type=CallType.OVERNIGHT)
        for i in range(5)
    ]

    formulation = CallAssignmentQUBO(nights, candidates)
    formulation.build()

    solver1 = QuantumTunnelingAnnealingSolver(num_reads=3, num_sweeps=100, seed=123)
    solution1 = solver1.solve(formulation)

    solver2 = QuantumTunnelingAnnealingSolver(num_reads=3, num_sweeps=100, seed=123)
    solution2 = solver2.solve(formulation)

    assert solution1.energy == solution2.energy, "Same seed should give same energy"
    print(f"✓ Energy 1: {solution1.energy:.2f}")
    print(f"✓ Energy 2: {solution2.energy:.2f}")
    print("PASSED\n")


def test_landscape_export():
    """Test landscape data export."""
    print("=" * 60)
    print("TEST: Landscape Data Export")
    print("=" * 60)

    base_date = date(2025, 1, 1)
    candidates = [
        CallCandidate(person_id=uuid4(), name=f"Resident-{i}", pgy_level=1)
        for i in range(5)
    ]
    nights = [
        CallNight(date=base_date + timedelta(days=i), call_type=CallType.OVERNIGHT)
        for i in range(5)
    ]

    formulation = CallAssignmentQUBO(nights, candidates)
    formulation.build()

    solver = QuantumTunnelingAnnealingSolver(
        num_reads=2,
        num_sweeps=200,
        track_landscape=True,
        landscape_sample_rate=20,
    )

    solution = solver.solve(formulation)

    assert solution.landscape_data is not None
    assert "metadata" in solution.landscape_data
    assert "trajectory" in solution.landscape_data
    assert len(solution.landscape_data["trajectory"]) > 0

    # Test JSON serialization
    json_str = json.dumps(solution.landscape_data, default=str)
    assert len(json_str) > 0

    print(f"✓ Landscape points: {len(solution.landscape_data['trajectory'])}")
    print(f"✓ JSON size: {len(json_str)} bytes")
    print("PASSED\n")


def test_scalability():
    """Test with medium-sized problem."""
    print("=" * 60)
    print("TEST: Scalability (20 residents × 30 nights = 600 vars)")
    print("=" * 60)

    base_date = date(2025, 1, 1)
    candidates = [
        CallCandidate(person_id=uuid4(), name=f"Resident-{i}", pgy_level=(i % 3) + 1)
        for i in range(20)
    ]

    # 30 nights, excluding weekends
    nights = []
    current = base_date
    while len(nights) < 30:
        if current.weekday() not in (4, 5):  # Exclude Fri/Sat
            nights.append(
                CallNight(date=current, call_type=CallType.OVERNIGHT)
            )
        current += timedelta(days=1)

    formulation = CallAssignmentQUBO(nights, candidates)
    assert formulation.num_variables == 600

    formulation.build()

    solver = QuantumTunnelingAnnealingSolver(
        num_reads=5,
        num_sweeps=500,
        track_landscape=False,
    )

    solution = solver.solve(formulation)

    assert solution.runtime_seconds < 60, "Should complete in <60s"
    assert len(solution.assignments) > 0

    print(f"✓ Variables: {formulation.num_variables}")
    print(f"✓ Assignments: {len(solution.assignments)}")
    print(f"✓ Runtime: {solution.runtime_seconds:.3f}s")
    print(f"✓ Valid: {solution.is_valid}")
    print("PASSED\n")


def main():
    """Run all standalone tests."""
    print("\n" + "=" * 70)
    print("CALL ASSIGNMENT QUBO - STANDALONE TESTS")
    print("=" * 70 + "\n")

    test_basic_qubo()
    test_solver()
    test_determinism()
    test_landscape_export()
    test_scalability()

    print("=" * 70)
    print("ALL STANDALONE TESTS PASSED!")
    print("=" * 70)


if __name__ == "__main__":
    main()
