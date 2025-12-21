"""
Artificial Immune System (AIS) for Schedule Anomaly Detection.

Inspired by the biological immune system's ability to distinguish "self" from
"non-self" without explicit definition of all possible threats. This module uses:

1. **Negative Selection Algorithm (NSA)**: Generate detectors that match anomalous
   states by training on valid schedules. Detectors learn what is NOT normal.

2. **Clonal Selection**: When an anomaly is detected, select and apply the most
   appropriate repair strategy based on affinity matching.

3. **Real-Valued Negative Selection (RNSA)**: Detectors are hyperspheres in
   feature space. A schedule state is anomalous if it falls within any detector's
   radius.

Key Concepts:
- **Self**: Valid, compliant schedule states
- **Non-Self**: Invalid/anomalous schedule states (ACGME violations, coverage gaps)
- **Detector**: Hypersphere in feature space that triggers on non-self
- **Antibody**: Repair strategy with affinity for specific anomaly patterns
- **Affinity**: How well an antibody matches an anomaly (distance-based)

Example Usage:
    >>> immune = ScheduleImmuneSystem(feature_dims=10, detector_count=100)
    >>> immune.train(valid_schedules)
    >>> if immune.is_anomaly(new_schedule):
    ...     repaired = immune.apply_repair(new_schedule)

Biological Inspiration:
    The immune system doesn't know all possible pathogens in advance. Instead,
    it generates random detectors and destroys any that react to "self" cells.
    This negative selection process creates a diverse set of detectors that
    collectively recognize non-self threats.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Detector:
    """
    A detector in feature space (hypersphere).

    Detectors are generated during training to NOT match valid schedules.
    If a detector matches a new schedule, it indicates an anomaly.
    """
    id: UUID
    center: np.ndarray  # Center point in feature space
    radius: float  # Detection radius
    created_at: datetime
    matches_count: int = 0  # How many anomalies this detector has caught

    def matches(self, feature_vector: np.ndarray) -> bool:
        """
        Check if a feature vector falls within detector's radius.

        Args:
            feature_vector: Schedule feature vector

        Returns:
            True if vector is within detection radius (anomaly detected)
        """
        distance = np.linalg.norm(feature_vector - self.center)
        return distance < self.radius

    def get_distance(self, feature_vector: np.ndarray) -> float:
        """
        Get distance from detector center to feature vector.

        Args:
            feature_vector: Schedule feature vector

        Returns:
            Euclidean distance
        """
        return float(np.linalg.norm(feature_vector - self.center))


@dataclass
class Antibody:
    """
    A repair strategy (antibody) that can fix specific types of anomalies.

    Antibodies have affinity for certain anomaly patterns based on feature
    similarity. When an anomaly is detected, clonal selection chooses the
    antibody with highest affinity.
    """
    id: UUID
    name: str
    description: str
    repair_function: Callable[[dict], dict]
    affinity_center: np.ndarray  # Feature pattern this antibody targets
    affinity_radius: float  # How broadly applicable
    applications_count: int = 0
    success_count: int = 0

    def get_affinity(self, feature_vector: np.ndarray) -> float:
        """
        Calculate affinity (match strength) for a feature vector.

        Higher affinity = better match = more likely to be effective.
        Affinity is inverse of distance (closer = higher affinity).

        Args:
            feature_vector: Anomaly feature vector

        Returns:
            Affinity score (0-1, higher is better)
        """
        distance = np.linalg.norm(feature_vector - self.affinity_center)
        # Normalize by radius: distance 0 = affinity 1.0, distance >= radius = affinity 0
        if distance >= self.affinity_radius:
            return 0.0
        return 1.0 - (distance / self.affinity_radius)

    @property
    def success_rate(self) -> float:
        """Calculate success rate of this antibody."""
        if self.applications_count == 0:
            return 0.0
        return self.success_count / self.applications_count


@dataclass
class AnomalyReport:
    """Report of a detected anomaly."""
    id: UUID
    detected_at: datetime
    feature_vector: np.ndarray
    anomaly_score: float  # Distance to nearest detector (higher = more anomalous)
    matching_detectors: list[UUID]  # Detectors that triggered
    severity: str  # "low", "medium", "high", "critical"
    description: str

    def __post_init__(self):
        """Determine severity based on anomaly score."""
        if self.anomaly_score > 2.0:
            self.severity = "critical"
        elif self.anomaly_score > 1.0:
            self.severity = "high"
        elif self.anomaly_score > 0.5:
            self.severity = "medium"
        else:
            self.severity = "low"


@dataclass
class RepairResult:
    """Result of applying a repair strategy."""
    id: UUID
    antibody_id: UUID
    antibody_name: str
    applied_at: datetime
    original_state: dict
    repaired_state: dict
    successful: bool
    anomaly_before: float
    anomaly_after: float
    message: str


class ScheduleImmuneSystem:
    """
    Artificial Immune System for schedule anomaly detection and repair.

    Uses Negative Selection Algorithm to learn what valid schedules look like,
    then detects deviations. Employs Clonal Selection to choose and apply
    appropriate repair strategies.

    Training Process:
        1. Extract features from valid schedules
        2. Generate random detector candidates
        3. Discard candidates that match valid schedules (negative selection)
        4. Keep remaining detectors for anomaly detection

    Detection Process:
        1. Extract features from new schedule
        2. Check if any detector matches
        3. If match: anomaly detected
        4. Calculate anomaly score (distance to nearest detector)

    Repair Process (Clonal Selection):
        1. Extract features from anomaly
        2. Calculate affinity of all antibodies
        3. Select antibody with highest affinity
        4. Apply repair function
        5. Verify repair reduced anomaly score
    """

    def __init__(
        self,
        feature_dims: int,
        detector_count: int = 100,
        detection_radius: float = 0.1,
    ):
        """
        Initialize the immune system.

        Args:
            feature_dims: Dimensionality of feature vectors
            detector_count: Number of detectors to generate
            detection_radius: Radius for detector matching
        """
        self.feature_dims = feature_dims
        self.detector_count = detector_count
        self.detection_radius = detection_radius

        # Immune components
        self.detectors: list[Detector] = []
        self.antibodies: dict[str, Antibody] = {}

        # Training data (for reference)
        self.training_features: list[np.ndarray] = []
        self.is_trained: bool = False

        # Statistics
        self.anomalies_detected: int = 0
        self.repairs_applied: int = 0
        self.successful_repairs: int = 0

        logger.info(
            f"Initialized ScheduleImmuneSystem: "
            f"{feature_dims}D features, {detector_count} detectors, "
            f"radius={detection_radius}"
        )

    def extract_features(self, schedule_state: dict) -> np.ndarray:
        """
        Extract feature vector from a schedule state.

        Feature vector includes:
        - Coverage ratios per block type
        - ACGME compliance scores (80-hour, 1-in-7, supervision)
        - Utilization levels
        - Workload balance (std dev)
        - Schedule stability

        Args:
            schedule_state: Dict with schedule information:
                - total_blocks: int
                - covered_blocks: int
                - faculty_count: int
                - resident_count: int
                - acgme_violations: list
                - avg_hours_per_week: float
                - supervision_ratio: float
                - workload_std_dev: float
                - schedule_changes: int
                - coverage_by_type: dict

        Returns:
            Feature vector as numpy array
        """
        features = []

        # Coverage metrics (4 features)
        total_blocks = schedule_state.get("total_blocks", 1)
        covered_blocks = schedule_state.get("covered_blocks", 0)
        coverage_rate = covered_blocks / total_blocks if total_blocks > 0 else 0
        features.append(coverage_rate)

        # Coverage by type (normalized)
        coverage_by_type = schedule_state.get("coverage_by_type", {})
        clinic_coverage = coverage_by_type.get("clinic", 0.0)
        inpatient_coverage = coverage_by_type.get("inpatient", 0.0)
        procedure_coverage = coverage_by_type.get("procedure", 0.0)
        features.extend([clinic_coverage, inpatient_coverage, procedure_coverage])

        # ACGME compliance metrics (3 features)
        violations = schedule_state.get("acgme_violations", [])
        total_violations = len(violations)
        critical_violations = sum(1 for v in violations if v.get("severity") == "CRITICAL")

        # Normalize by number of people (avoid unbounded growth)
        people_count = (
            schedule_state.get("faculty_count", 1) +
            schedule_state.get("resident_count", 1)
        )
        violation_rate = total_violations / max(1, people_count)
        critical_rate = critical_violations / max(1, people_count)
        features.extend([violation_rate, critical_rate])

        # Hours compliance (0-1, where 1 = compliant)
        avg_hours = schedule_state.get("avg_hours_per_week", 0)
        hours_compliance = 1.0 - min(1.0, max(0, avg_hours - 80) / 20)  # Penalty above 80
        features.append(hours_compliance)

        # Supervision ratio (2 features)
        supervision_ratio = schedule_state.get("supervision_ratio", 1.0)
        # Normalize: 1:1 = 1.0, 1:2 = 0.5, etc.
        supervision_score = min(1.0, 1.0 / supervision_ratio) if supervision_ratio > 0 else 0
        faculty_count = schedule_state.get("faculty_count", 0)
        faculty_availability = faculty_count / max(1, people_count)
        features.extend([supervision_score, faculty_availability])

        # Workload balance (1 feature)
        workload_std = schedule_state.get("workload_std_dev", 0.0)
        # Normalize: 0 std dev = perfect (1.0), high std dev = poor (0.0)
        balance_score = 1.0 / (1.0 + workload_std)
        features.append(balance_score)

        # Schedule stability (1 feature)
        total_assignments = schedule_state.get("total_assignments", 1)
        changes = schedule_state.get("schedule_changes", 0)
        stability = 1.0 - min(1.0, changes / max(1, total_assignments))
        features.append(stability)

        # Convert to numpy array and pad/truncate to match feature_dims
        features_array = np.array(features, dtype=np.float32)

        if len(features_array) < self.feature_dims:
            # Pad with zeros
            features_array = np.pad(
                features_array,
                (0, self.feature_dims - len(features_array)),
                mode='constant'
            )
        elif len(features_array) > self.feature_dims:
            # Truncate
            features_array = features_array[:self.feature_dims]

        return features_array

    def train(self, valid_schedules: list[dict], max_attempts: int = 1000):
        """
        Train the immune system on valid schedules using Negative Selection.

        Process:
        1. Extract features from all valid schedules
        2. Generate random detector candidates
        3. For each candidate:
           - If it matches any valid schedule: REJECT (it's too close to "self")
           - If it doesn't match any valid: ACCEPT (it detects "non-self")
        4. Keep accepted detectors

        Args:
            valid_schedules: List of valid schedule state dicts
            max_attempts: Maximum attempts to generate each detector
        """
        logger.info(f"Training immune system on {len(valid_schedules)} valid schedules...")

        # Extract features from valid schedules
        self.training_features = [
            self.extract_features(schedule)
            for schedule in valid_schedules
        ]

        if not self.training_features:
            logger.warning("No training features extracted!")
            return

        # Calculate feature space bounds
        features_array = np.array(self.training_features)
        min_vals = features_array.min(axis=0)
        max_vals = features_array.max(axis=0)

        # Generate detectors using negative selection
        self.detectors = []
        attempts = 0

        while len(self.detectors) < self.detector_count and attempts < max_attempts:
            attempts += 1

            # Generate random detector center within feature space bounds
            center = np.random.uniform(min_vals, max_vals).astype(np.float32)

            # Check if this detector matches any valid schedule (self)
            matches_self = False
            for valid_features in self.training_features:
                distance = np.linalg.norm(center - valid_features)
                if distance < self.detection_radius:
                    matches_self = True
                    break

            # Negative selection: only keep detectors that DON'T match self
            if not matches_self:
                detector = Detector(
                    id=uuid4(),
                    center=center,
                    radius=self.detection_radius,
                    created_at=datetime.now(),
                )
                self.detectors.append(detector)

                if len(self.detectors) % 10 == 0:
                    logger.debug(f"Generated {len(self.detectors)}/{self.detector_count} detectors")

        self.is_trained = True
        logger.info(
            f"Training complete: {len(self.detectors)} detectors generated "
            f"in {attempts} attempts"
        )

    def is_anomaly(self, schedule_state: dict) -> bool:
        """
        Check if a schedule state is anomalous.

        A state is anomalous if it matches any detector (falls within
        any detector's radius).

        Args:
            schedule_state: Schedule state to check

        Returns:
            True if anomalous, False if normal
        """
        if not self.is_trained:
            logger.warning("Immune system not trained yet!")
            return False

        features = self.extract_features(schedule_state)

        # Check if any detector matches
        for detector in self.detectors:
            if detector.matches(features):
                detector.matches_count += 1
                self.anomalies_detected += 1
                return True

        return False

    def get_anomaly_score(self, schedule_state: dict) -> float:
        """
        Calculate anomaly score for a schedule state.

        Score is based on distance to nearest detector:
        - Score 0.0: Very close to a detector center (highly anomalous)
        - Score 1.0+: Far from all detectors (likely normal)

        Args:
            schedule_state: Schedule state to score

        Returns:
            Anomaly score (0 = most anomalous, higher = more normal)
        """
        if not self.is_trained or not self.detectors:
            return 0.0

        features = self.extract_features(schedule_state)

        # Find minimum distance to any detector center
        min_distance = float('inf')
        for detector in self.detectors:
            distance = detector.get_distance(features)
            min_distance = min(min_distance, distance)

        # Invert: closer to detector = higher anomaly score
        # Normalize by detection radius
        if min_distance < self.detection_radius:
            # Inside detection radius: high anomaly score
            score = 2.0 * (1.0 - min_distance / self.detection_radius)
        else:
            # Outside all detectors: low anomaly score
            score = 0.5 * self.detection_radius / min_distance

        return score

    def detect_anomaly(self, schedule_state: dict) -> AnomalyReport | None:
        """
        Detect anomaly and generate detailed report.

        Args:
            schedule_state: Schedule state to check

        Returns:
            AnomalyReport if anomaly detected, None otherwise
        """
        features = self.extract_features(schedule_state)
        matching_detectors = []

        for detector in self.detectors:
            if detector.matches(features):
                matching_detectors.append(detector.id)
                detector.matches_count += 1

        if not matching_detectors:
            return None

        self.anomalies_detected += 1
        anomaly_score = self.get_anomaly_score(schedule_state)

        # Generate description
        violations = schedule_state.get("acgme_violations", [])
        coverage_rate = schedule_state.get("covered_blocks", 0) / max(1, schedule_state.get("total_blocks", 1))

        description_parts = []
        if coverage_rate < 0.9:
            description_parts.append(f"Low coverage: {coverage_rate:.0%}")
        if violations:
            description_parts.append(f"{len(violations)} ACGME violations")
        if schedule_state.get("workload_std_dev", 0) > 0.3:
            description_parts.append("High workload imbalance")

        description = "; ".join(description_parts) if description_parts else "Schedule state anomaly detected"

        return AnomalyReport(
            id=uuid4(),
            detected_at=datetime.now(),
            feature_vector=features,
            anomaly_score=anomaly_score,
            matching_detectors=matching_detectors,
            severity="",  # Will be set in __post_init__
            description=description,
        )

    def register_antibody(
        self,
        name: str,
        repair_fn: Callable[[dict], dict],
        affinity_pattern: dict | None = None,
        affinity_radius: float = 1.0,
        description: str = "",
    ):
        """
        Register a repair strategy (antibody).

        Antibodies are repair functions with affinity for specific anomaly
        patterns. When an anomaly is detected, the antibody with highest
        affinity is selected (clonal selection).

        Args:
            name: Unique name for this antibody
            repair_fn: Function that takes schedule_state and returns repaired state
            affinity_pattern: Example anomaly this antibody targets (for affinity center)
            affinity_radius: How broadly applicable this antibody is
            description: Human-readable description
        """
        # If pattern provided, use it as affinity center
        if affinity_pattern:
            affinity_center = self.extract_features(affinity_pattern)
        else:
            # Random affinity center
            affinity_center = np.random.randn(self.feature_dims).astype(np.float32)

        antibody = Antibody(
            id=uuid4(),
            name=name,
            description=description,
            repair_function=repair_fn,
            affinity_center=affinity_center,
            affinity_radius=affinity_radius,
        )

        self.antibodies[name] = antibody
        logger.info(f"Registered antibody: {name} - {description}")

    def select_antibody(self, anomaly_state: dict) -> tuple[str, Antibody] | None:
        """
        Select best antibody for an anomaly (clonal selection).

        Calculates affinity of all antibodies and selects the one with
        highest affinity (best match).

        Args:
            anomaly_state: Anomalous schedule state

        Returns:
            Tuple of (name, antibody) with highest affinity, or None if no antibodies
        """
        if not self.antibodies:
            return None

        features = self.extract_features(anomaly_state)

        # Calculate affinities
        affinities = []
        for name, antibody in self.antibodies.items():
            affinity = antibody.get_affinity(features)
            # Bonus for successful track record
            affinity_adjusted = affinity * (1.0 + 0.5 * antibody.success_rate)
            affinities.append((affinity_adjusted, name, antibody))

        # Select highest affinity
        affinities.sort(reverse=True, key=lambda x: x[0])

        if affinities[0][0] > 0:
            best_name = affinities[0][1]
            best_antibody = affinities[0][2]
            logger.info(
                f"Selected antibody '{best_name}' with affinity {affinities[0][0]:.2f}"
            )
            return best_name, best_antibody

        return None

    def apply_repair(self, schedule_state: dict) -> RepairResult | None:
        """
        Apply clonal selection to repair an anomaly.

        Process:
        1. Select antibody with highest affinity
        2. Apply repair function
        3. Verify repair reduced anomaly score
        4. Update antibody statistics

        Args:
            schedule_state: Anomalous schedule state

        Returns:
            RepairResult if repair attempted, None if no suitable antibody
        """
        # Select antibody
        selection = self.select_antibody(schedule_state)
        if not selection:
            logger.warning("No suitable antibody found for repair")
            return None

        name, antibody = selection

        # Get anomaly score before repair
        anomaly_before = self.get_anomaly_score(schedule_state)

        # Apply repair
        try:
            repaired_state = antibody.repair_function(schedule_state)
            anomaly_after = self.get_anomaly_score(repaired_state)

            # Check if repair was successful (reduced anomaly score)
            successful = anomaly_after < anomaly_before

            # Update statistics
            antibody.applications_count += 1
            if successful:
                antibody.success_count += 1
                self.successful_repairs += 1

            self.repairs_applied += 1

            result = RepairResult(
                id=uuid4(),
                antibody_id=antibody.id,
                antibody_name=name,
                applied_at=datetime.now(),
                original_state=schedule_state,
                repaired_state=repaired_state,
                successful=successful,
                anomaly_before=anomaly_before,
                anomaly_after=anomaly_after,
                message=(
                    f"Repair {'successful' if successful else 'unsuccessful'}: "
                    f"anomaly score {anomaly_before:.2f} -> {anomaly_after:.2f}"
                ),
            )

            logger.info(result.message)
            return result

        except Exception as e:
            logger.error(f"Repair function failed: {e}")
            antibody.applications_count += 1
            self.repairs_applied += 1

            return RepairResult(
                id=uuid4(),
                antibody_id=antibody.id,
                antibody_name=name,
                applied_at=datetime.now(),
                original_state=schedule_state,
                repaired_state=schedule_state,  # No change
                successful=False,
                anomaly_before=anomaly_before,
                anomaly_after=anomaly_before,
                message=f"Repair failed: {e}",
            )

    def get_statistics(self) -> dict[str, Any]:
        """
        Get immune system statistics.

        Returns:
            Dict with statistics
        """
        return {
            "is_trained": self.is_trained,
            "feature_dims": self.feature_dims,
            "detector_count": len(self.detectors),
            "detection_radius": self.detection_radius,
            "training_samples": len(self.training_features),
            "antibody_count": len(self.antibodies),
            "anomalies_detected": self.anomalies_detected,
            "repairs_applied": self.repairs_applied,
            "successful_repairs": self.successful_repairs,
            "repair_success_rate": (
                self.successful_repairs / self.repairs_applied
                if self.repairs_applied > 0 else 0.0
            ),
            "most_active_detectors": sorted(
                [
                    {"detector_id": str(d.id), "matches": d.matches_count}
                    for d in self.detectors
                ],
                key=lambda x: x["matches"],
                reverse=True,
            )[:5],
            "antibody_performance": {
                name: {
                    "applications": ab.applications_count,
                    "success_count": ab.success_count,
                    "success_rate": ab.success_rate,
                }
                for name, ab in self.antibodies.items()
            },
        }

    def reset_statistics(self):
        """Reset detection and repair statistics."""
        self.anomalies_detected = 0
        self.repairs_applied = 0
        self.successful_repairs = 0

        for detector in self.detectors:
            detector.matches_count = 0

        for antibody in self.antibodies.values():
            antibody.applications_count = 0
            antibody.success_count = 0

        logger.info("Immune system statistics reset")
