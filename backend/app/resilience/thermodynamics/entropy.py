"""
Entropy and Information Theory for Schedule Analysis.

Implements Shannon entropy, mutual information, and entropy production
for measuring schedule disorder, predictability, and stability.

Key Concepts:
- Shannon Entropy: H(X) = -Σ p(i) log₂ p(i)
- Mutual Information: I(X;Y) = H(X) + H(Y) - H(X,Y)
- Conditional Entropy: H(X|Y) = H(X,Y) - H(Y)
- Entropy Production: Rate of entropy generation (dissipation)

References:
- Shannon (1948): "A Mathematical Theory of Communication"
- Jaynes (1957): Information theory and statistical mechanics
- Prigogine (1977): Dissipative structures and entropy production
"""

import logging
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class EntropyMetrics:
    """
    Comprehensive entropy analysis of a schedule.

    Attributes:
        person_entropy: Entropy of assignment distribution across faculty
        rotation_entropy: Entropy of rotation assignment distribution
        time_entropy: Entropy of temporal distribution
        joint_entropy: Joint entropy across all dimensions
        mutual_information: Information shared between dimensions
        entropy_production_rate: Rate of entropy generation
        normalized_entropy: Entropy relative to maximum possible
    """
    person_entropy: float
    rotation_entropy: float
    time_entropy: float
    joint_entropy: float
    mutual_information: float
    entropy_production_rate: float = 0.0
    normalized_entropy: float = 0.0

    computed_at: datetime = field(default_factory=datetime.utcnow)


def calculate_shannon_entropy(distribution: list[Any]) -> float:
    """
    Calculate Shannon entropy of a distribution.

    H(X) = -Σ p(i) log₂ p(i)

    Args:
        distribution: List of values (will be counted and converted to probabilities)

    Returns:
        Shannon entropy in bits (0 = perfectly ordered, high = disordered)

    Example:
        >>> calculate_shannon_entropy([1, 1, 1, 1])  # Uniform
        2.0
        >>> calculate_shannon_entropy([1, 1, 1, 2])  # Skewed
        0.811
        >>> calculate_shannon_entropy([1, 1, 1, 1, 2, 2, 2, 2])  # Balanced
        1.0
    """
    if not distribution:
        return 0.0

    # Count occurrences
    counts = Counter(distribution)
    total = len(distribution)

    # Calculate probabilities
    probabilities = [count / total for count in counts.values()]

    # Shannon entropy
    entropy = -sum(p * math.log2(p) for p in probabilities if p > 0)

    return entropy


def calculate_schedule_entropy(assignments: list[Any]) -> EntropyMetrics:
    """
    Calculate comprehensive entropy metrics for a schedule.

    Analyzes entropy across multiple dimensions:
    - Person distribution (faculty workload balance)
    - Rotation distribution (service coverage diversity)
    - Time distribution (temporal balance)
    - Joint entropy (correlations)

    Args:
        assignments: List of assignment objects with person_id, rotation_template_id, block_id

    Returns:
        EntropyMetrics with all entropy measures

    Theory:
        High entropy → diverse, flexible, but potentially chaotic
        Low entropy → concentrated, rigid, but potentially vulnerable
        Optimal: moderate entropy with balanced distribution
    """
    if not assignments:
        return EntropyMetrics(
            person_entropy=0.0,
            rotation_entropy=0.0,
            time_entropy=0.0,
            joint_entropy=0.0,
            mutual_information=0.0,
        )

    # Extract distributions
    person_dist = [a.person_id for a in assignments if hasattr(a, 'person_id')]
    rotation_dist = [
        a.rotation_template_id
        for a in assignments
        if hasattr(a, 'rotation_template_id') and a.rotation_template_id is not None
    ]
    time_dist = [a.block_id for a in assignments if hasattr(a, 'block_id')]

    # Calculate individual entropies
    H_person = calculate_shannon_entropy(person_dist) if person_dist else 0.0
    H_rotation = calculate_shannon_entropy(rotation_dist) if rotation_dist else 0.0
    H_time = calculate_shannon_entropy(time_dist) if time_dist else 0.0

    # Calculate joint entropy (person, rotation)
    if person_dist and rotation_dist:
        joint_dist = list(zip(person_dist, rotation_dist))
        H_joint = calculate_shannon_entropy(joint_dist)

        # Mutual information: how much knowing person tells about rotation
        MI = H_person + H_rotation - H_joint
    else:
        H_joint = 0.0
        MI = 0.0

    # Normalized entropy (relative to maximum possible)
    # Maximum entropy occurs with uniform distribution
    max_person_entropy = math.log2(len(set(person_dist))) if person_dist else 1.0
    normalized = H_person / max_person_entropy if max_person_entropy > 0 else 0.0

    return EntropyMetrics(
        person_entropy=H_person,
        rotation_entropy=H_rotation,
        time_entropy=H_time,
        joint_entropy=H_joint,
        mutual_information=MI,
        normalized_entropy=normalized,
    )


def mutual_information(dist_X: list[Any], dist_Y: list[Any]) -> float:
    """
    Calculate mutual information between two distributions.

    I(X;Y) = H(X) + H(Y) - H(X,Y)

    Measures how much knowing X reduces uncertainty about Y.

    Args:
        dist_X: First distribution
        dist_Y: Second distribution (must be same length)

    Returns:
        Mutual information in bits
        - 0: X and Y are independent
        - > 0: X and Y share information (correlated)
        - High MI: Strong coupling, changes cascade

    Example:
        >>> # Faculty and rotation strongly coupled
        >>> faculty = [1, 1, 2, 2, 3, 3]
        >>> rotations = ['A', 'A', 'B', 'B', 'C', 'C']
        >>> mutual_information(faculty, rotations)
        1.585  # High MI: perfect correlation
    """
    if len(dist_X) != len(dist_Y):
        raise ValueError("Distributions must have same length")

    if not dist_X:
        return 0.0

    # Individual entropies
    H_X = calculate_shannon_entropy(dist_X)
    H_Y = calculate_shannon_entropy(dist_Y)

    # Joint entropy
    joint_dist = list(zip(dist_X, dist_Y))
    H_joint = calculate_shannon_entropy(joint_dist)

    # Mutual information
    MI = H_X + H_Y - H_joint

    return max(0.0, MI)  # Ensure non-negative (numerical errors)


def conditional_entropy(dist_X: list[Any], dist_Y: list[Any]) -> float:
    """
    Calculate conditional entropy H(X|Y).

    Remaining uncertainty in X given knowledge of Y.

    H(X|Y) = H(X,Y) - H(Y)

    Args:
        dist_X: Target distribution
        dist_Y: Conditioning distribution

    Returns:
        Conditional entropy in bits
        - Low: Y highly predictive of X
        - High: Y doesn't help predict X

    Application:
        H(Coverage | Faculty) → Can we predict coverage from faculty assignment?
        Low conditional entropy → good predictability
    """
    if len(dist_X) != len(dist_Y):
        raise ValueError("Distributions must have same length")

    if not dist_X:
        return 0.0

    # Joint and individual entropies
    joint_dist = list(zip(dist_X, dist_Y))
    H_joint = calculate_shannon_entropy(joint_dist)
    H_Y = calculate_shannon_entropy(dist_Y)

    # Conditional entropy
    H_cond = H_joint - H_Y

    return max(0.0, H_cond)


def entropy_production_rate(
    old_assignments: list[Any],
    new_assignments: list[Any],
    time_delta: float = 1.0
) -> float:
    """
    Calculate entropy production rate from schedule changes.

    Rate of irreversible entropy generation (always non-negative).

    dS/dt = (S_new - S_old) / Δt

    Args:
        old_assignments: Previous schedule
        new_assignments: Current schedule
        time_delta: Time interval in hours (default 1.0)

    Returns:
        Entropy production rate (bits/hour)
        - 0: No change (equilibrium)
        - > 0: System evolving, dissipating
        - High rate: Rapid reorganization, far from equilibrium

    Theory:
        Dissipative structures maintain order by exporting entropy.
        High production rate → system working hard to maintain stability.
    """
    S_old = calculate_schedule_entropy(old_assignments).person_entropy
    S_new = calculate_schedule_entropy(new_assignments).person_entropy

    # Entropy change
    dS = S_new - S_old

    # Production rate (only count increases, not decreases)
    # Decreases are compensated by entropy export to environment
    dS_production = max(0.0, dS) / time_delta

    return dS_production


class ScheduleEntropyMonitor:
    """
    Monitor entropy dynamics for early warning signals.

    Tracks entropy over time to detect:
    - Critical slowing down (entropy changes slow near transitions)
    - Rapid entropy changes (system instability)
    - Entropy production rate (dissipation)

    Integration:
        Use with HomeostasisMonitor for thermodynamic foundations.
    """

    def __init__(self, history_window: int = 100):
        """
        Initialize entropy monitor.

        Args:
            history_window: Number of entropy measurements to retain
        """
        self.history_window = history_window

        self.entropy_history: list[float] = []
        self.production_rate_history: list[float] = []
        self.timestamp_history: list[datetime] = []

        logger.info(f"ScheduleEntropyMonitor initialized with window={history_window}")

    def update(self, assignments: list[Any]):
        """
        Update with latest schedule.

        Args:
            assignments: Current assignments
        """
        metrics = calculate_schedule_entropy(assignments)

        self.entropy_history.append(metrics.person_entropy)
        self.timestamp_history.append(datetime.utcnow())

        # Calculate production rate if we have previous state
        if len(self.entropy_history) >= 2:
            dS = self.entropy_history[-1] - self.entropy_history[-2]
            dt = (self.timestamp_history[-1] - self.timestamp_history[-2]).total_seconds() / 3600

            if dt > 0:
                production_rate = max(0.0, dS) / dt
                self.production_rate_history.append(production_rate)

        # Maintain window size
        if len(self.entropy_history) > self.history_window:
            self.entropy_history.pop(0)
            self.timestamp_history.pop(0)
            if self.production_rate_history:
                self.production_rate_history.pop(0)

    def get_entropy_rate_of_change(self) -> float:
        """
        Calculate rate of entropy change.

        Slowing rate → approaching critical transition (critical slowing down).

        Returns:
            Slope of entropy vs time (bits/hour)
        """
        if len(self.entropy_history) < 2:
            return 0.0

        # Linear regression
        x = np.arange(len(self.entropy_history))
        y = np.array(self.entropy_history)

        if len(x) < 2:
            return 0.0

        # Simple slope calculation
        slope = (y[-1] - y[0]) / (len(y) - 1) if len(y) > 1 else 0.0

        return slope

    def detect_critical_slowing(self) -> bool:
        """
        Detect critical slowing down in entropy dynamics.

        Critical slowing: entropy changes slow near phase transitions
        because system explores many microstates.

        Returns:
            True if critical slowing detected
        """
        if len(self.entropy_history) < 10:
            return False

        # Calculate autocorrelation (increases near critical point)
        recent = self.entropy_history[-10:]
        autocorr = self._autocorrelation(recent, lag=1)

        # Critical slowing: high autocorrelation + low rate of change
        rate = abs(self.get_entropy_rate_of_change())

        is_slowing = autocorr > 0.8 and rate < 0.1

        if is_slowing:
            logger.warning(
                f"Critical slowing detected: autocorr={autocorr:.2f}, rate={rate:.3f}"
            )

        return is_slowing

    def _autocorrelation(self, values: list[float], lag: int = 1) -> float:
        """Calculate autocorrelation at given lag."""
        if len(values) < lag + 2:
            return 0.0

        mean = np.mean(values)
        c0 = np.sum((np.array(values) - mean) ** 2)

        if c0 == 0:
            return 0.0

        c_lag = np.sum(
            (np.array(values[:-lag]) - mean) * (np.array(values[lag:]) - mean)
        )

        return c_lag / c0

    def get_current_metrics(self) -> dict[str, float]:
        """
        Get current entropy metrics.

        Returns:
            Dictionary with current entropy state
        """
        if not self.entropy_history:
            return {
                "current_entropy": 0.0,
                "rate_of_change": 0.0,
                "production_rate": 0.0,
                "critical_slowing": False,
            }

        return {
            "current_entropy": self.entropy_history[-1],
            "rate_of_change": self.get_entropy_rate_of_change(),
            "production_rate": self.production_rate_history[-1] if self.production_rate_history else 0.0,
            "critical_slowing": self.detect_critical_slowing(),
            "measurements": len(self.entropy_history),
        }
