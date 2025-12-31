"""
Metastability Detection.

From statistical mechanics: detecting when a system is trapped in a local
energy minimum and at risk of sudden transition to a more stable state.

Application to scheduling:
- Solver trapped in suboptimal schedule
- Organization stuck in inefficient pattern
- Sudden reorganization risk (morale collapse, mass resignations)

Key concept: Activation energy barrier - how much perturbation needed to escape
current state.

Based on:
- Kramers escape rate theory
- Eyring transition state theory
- Energy landscape analysis
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.optimize import differential_evolution

logger = logging.getLogger(__name__)


@dataclass
class MetastableState:
    """Metastable state characterization."""

    energy: float  # Current energy (lower = more stable)
    barrier_height: float  # Energy barrier to nearest stable state
    escape_rate: float  # Probability of spontaneous escape per time unit
    lifetime: float  # Expected lifetime in current state
    is_metastable: bool  # True if trapped in local minimum
    stability_score: float  # 0-1, higher = more stable
    nearest_stable_state: float | None = None  # Energy of nearest true minimum


class MetastabilityDetector:
    """
    Detect metastable states in scheduling systems.

    Uses energy landscape metaphor:
    - Energy = quality metric (burnout level, violation count, dissatisfaction)
    - Metastable = locally optimal but globally suboptimal
    - Barrier = difficulty of reorganization
    """

    def __init__(self, temperature: float = 1.0):
        """
        Initialize metastability detector.

        Args:
            temperature: System temperature (controls thermal fluctuations)
                        Higher T = easier to escape metastable states
        """
        self.temperature = temperature
        self.boltzmann_constant = 1.0  # Normalized units

    def analyze_state(
        self,
        current_energy: float,
        energy_landscape: list[float],  # Energy at nearby states
        barrier_samples: list[float],  # Energy barriers to nearby states
    ) -> MetastableState:
        """
        Analyze if current state is metastable.

        Args:
            current_energy: Energy of current state
            energy_landscape: Energies of sampled nearby states
            barrier_samples: Energy barriers to those states

        Returns:
            MetastableState characterization
        """
        logger.info("Analyzing metastability: current_energy=%.2f, landscape_size=%d", current_energy, len(energy_landscape))
        if not energy_landscape or not barrier_samples:
            # Insufficient data
            logger.warning("Insufficient data for metastability analysis")
            return MetastableState(
                energy=current_energy,
                barrier_height=0.0,
                escape_rate=0.0,
                lifetime=float("inf"),
                is_metastable=False,
                stability_score=1.0,
            )

        # Find nearest lower-energy state
        lower_states = [e for e in energy_landscape if e < current_energy]

        if not lower_states:
            # Current state is global minimum (not metastable)
            return MetastableState(
                energy=current_energy,
                barrier_height=float("inf"),
                escape_rate=0.0,
                lifetime=float("inf"),
                is_metastable=False,
                stability_score=1.0,
                nearest_stable_state=None,
            )

        # Current state has lower-energy states available
        global_min = min(lower_states)
        energy_difference = current_energy - global_min

        # Find minimum barrier height to lower-energy state
        min_barrier = min(barrier_samples)

        # Calculate escape rate using Kramers theory
        # k_escape ≈ ω_0 * exp(-ΔE / kT)
        # where ΔE = barrier height, ω_0 = attempt frequency
        attempt_frequency = 1.0  # Normalized
        escape_rate = attempt_frequency * np.exp(
            -min_barrier / (self.boltzmann_constant * self.temperature)
        )

        # Expected lifetime: τ = 1 / k_escape
        lifetime = 1.0 / escape_rate if escape_rate > 0 else float("inf")

        # Determine if metastable
        # Criteria: barrier exists AND significantly lower energy state exists
        is_metastable = min_barrier > 0.1 and energy_difference > 0.05

        # Stability score: higher barrier = more stable metastable state
        stability_score = min(1.0, min_barrier / 10.0)  # Normalize to [0,1]

        return MetastableState(
            energy=current_energy,
            barrier_height=min_barrier,
            escape_rate=escape_rate,
            lifetime=lifetime,
            is_metastable=is_metastable,
            stability_score=stability_score,
            nearest_stable_state=global_min,
        )

    def calculate_transition_probability(
        self,
        current_energy: float,
        target_energy: float,
        barrier_height: float,
        time_elapsed: float,
    ) -> float:
        """
        Calculate probability of transitioning to target state.

        Uses Arrhenius equation from chemical kinetics.

        Args:
            current_energy: Current state energy
            target_energy: Target state energy
            barrier_height: Energy barrier between states
            time_elapsed: Time elapsed

        Returns:
            Transition probability (0-1)
        """
        # Escape rate
        escape_rate = np.exp(
            -barrier_height / (self.boltzmann_constant * self.temperature)
        )

        # Probability: P = 1 - exp(-k*t)
        prob = 1.0 - np.exp(-escape_rate * time_elapsed)

        return min(1.0, prob)

    def find_escape_paths(
        self,
        current_state: list[float],
        energy_function,
        num_paths: int = 5,
    ) -> list[dict]:
        """
        Find lowest-energy escape paths from current state.

        Args:
            current_state: Current state vector
            energy_function: Function mapping state -> energy
            num_paths: Number of escape paths to find

        Returns:
            List of escape path descriptions
        """
        current_energy = energy_function(current_state)
        paths = []

        # Sample random perturbations
        for _ in range(num_paths * 10):  # Oversample then select best
            # Random perturbation
            perturbation = np.random.randn(len(current_state)) * 0.1
            perturbed_state = np.array(current_state) + perturbation

            perturbed_energy = energy_function(perturbed_state)

            # Calculate barrier (maximum energy along linear path)
            # Simplified - linear interpolation
            barrier = max(
                energy_function(np.array(current_state) + t * perturbation)
                for t in np.linspace(0, 1, 10)
            )

            barrier_height = barrier - current_energy

            paths.append(
                {
                    "target_energy": perturbed_energy,
                    "energy_change": perturbed_energy - current_energy,
                    "barrier_height": barrier_height,
                    "is_downhill": perturbed_energy < current_energy,
                }
            )

        # Sort by energy change (prioritize downhill paths)
        paths.sort(key=lambda p: p["target_energy"])

        return paths[:num_paths]

    def predict_reorganization_risk(
        self,
        current_stability: float,
        external_perturbation: float,
        system_temperature: float,
    ) -> dict:
        """
        Predict risk of sudden system reorganization.

        Args:
            current_stability: Current stability score (0-1)
            external_perturbation: Magnitude of external stress
            system_temperature: System "temperature" (agitation level)

        Returns:
            Dict with risk assessment
        """
        # Effective barrier reduced by perturbation
        effective_barrier = current_stability - external_perturbation

        if effective_barrier <= 0:
            risk_level = "critical"
            risk_score = 1.0
            interpretation = "Immediate reorganization likely"
        elif effective_barrier < 0.2:
            risk_level = "high"
            risk_score = 0.8
            interpretation = "High risk of sudden transition"
        elif effective_barrier < 0.5:
            risk_level = "moderate"
            risk_score = 0.5
            interpretation = "Moderate reorganization risk"
        else:
            risk_level = "low"
            risk_score = 0.2
            interpretation = "System stable, low reorganization risk"

        # Estimate time to reorganization
        if effective_barrier > 0:
            escape_rate = np.exp(-effective_barrier / system_temperature)
            time_to_event = 1.0 / escape_rate if escape_rate > 0 else float("inf")
        else:
            time_to_event = 0.0  # Immediate

        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "interpretation": interpretation,
            "effective_barrier": max(0, effective_barrier),
            "estimated_time_to_reorganization": time_to_event,
            "recommendations": self._generate_recommendations(risk_level),
        }

    def _generate_recommendations(self, risk_level: str) -> list[str]:
        """Generate recommendations based on risk level."""
        if risk_level == "critical":
            return [
                "URGENT: System reorganization imminent",
                "Activate emergency stabilization protocols",
                "Reduce external stressors immediately",
                "Prepare for major schedule restructuring",
            ]
        elif risk_level == "high":
            return [
                "High risk of sudden transition",
                "Reduce workload and stress factors",
                "Proactively plan schedule adjustments",
                "Monitor closely for early warning signs",
            ]
        elif risk_level == "moderate":
            return [
                "Monitor stability trends",
                "Prepare contingency plans",
                "Maintain current stress reduction efforts",
            ]
        else:
            return [
                "System stable",
                "Continue current management approach",
                "Periodic monitoring sufficient",
            ]
