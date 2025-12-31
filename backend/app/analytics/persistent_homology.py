"""
Persistent Homology for Schedule Structure Analysis.

Uses Topological Data Analysis (TDA) to detect multi-scale patterns in schedule data:
- H0 (0th homology): Connected components (resident clustering, isolated groups)
- H1 (1st homology): Loops/cycles (cyclic rotation patterns, recurring shifts)
- H2 (2nd homology): Voids/cavities (gaps in coverage, structural holes)

Mathematical Basis:
    Persistent homology tracks topological features (connected components, loops, voids)
    across different scales in data. As a "filtration parameter" (distance threshold)
    increases, features are "born" and "die". Features with long persistence (high
    birth-death difference) are significant structural patterns.

    The persistence diagram plots (birth, death) pairs for each topological feature.
    Bottleneck distance between diagrams measures structural similarity.

Applications to Medical Residency Scheduling:
    - Identify resident clustering (some residents work together frequently)
    - Detect cyclic patterns in rotations (weekly/monthly cycles)
    - Find coverage voids (time periods or services with structural gaps)
    - Compare schedules topologically (stability over time)
    - Anomaly detection (unusual topological features)

References:
    - Carlsson, G. (2009). "Topology and data." Bulletin of the AMS, 46(2), 255-308.
    - Edelsbrunner, H., & Harer, J. (2010). Computational Topology. AMS.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Try to import TDA libraries
try:
    from ripser import ripser
    from persim import plot_diagrams, bottleneck

    HAS_RIPSER = True
except ImportError:
    HAS_RIPSER = False
    logger.warning(
        "ripser/persim not installed - persistent homology will use mock implementation. "
        "Install with: pip install ripser persim"
    )

# Try to import dimensionality reduction for embeddings
try:
    from sklearn.decomposition import PCA
    from sklearn.manifold import MDS, TSNE
    from sklearn.preprocessing import StandardScaler

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    logger.warning("scikit-learn not installed - using basic embeddings")


@dataclass
class TopologicalFeature:
    """
    A single topological feature detected by persistent homology.

    Attributes:
        dimension: Homology dimension (0=component, 1=loop, 2=void)
        birth: Filtration parameter when feature appears
        death: Filtration parameter when feature disappears
        persistence: death - birth (lifetime of feature)
        interpretation: Human-readable description of what this feature represents
    """

    dimension: int
    birth: float
    death: float
    persistence: float
    interpretation: str = ""

    def __post_init__(self):
        """Compute derived fields."""
        if self.persistence == 0:
            self.persistence = self.death - self.birth

    @property
    def is_significant(self) -> bool:
        """
        Determine if this feature is structurally significant.

        Features with high persistence relative to birth time are meaningful.
        """
        if self.birth == 0:
            return self.persistence > 0.1  # Absolute threshold for birth at 0
        return (self.persistence / self.birth) > 0.5  # Relative threshold

    @property
    def midpoint(self) -> float:
        """Midpoint of feature lifetime (for visualization)."""
        return (self.birth + self.death) / 2.0


@dataclass
class PersistenceDiagram:
    """
    Persistence diagram - collection of topological features across dimensions.

    Attributes:
        h0_features: H0 features (connected components)
        h1_features: H1 features (loops/cycles)
        h2_features: H2 features (voids/cavities)
        computed_at: When this diagram was computed
        max_dimension: Maximum homology dimension computed
    """

    h0_features: list[TopologicalFeature] = field(default_factory=list)
    h1_features: list[TopologicalFeature] = field(default_factory=list)
    h2_features: list[TopologicalFeature] = field(default_factory=list)
    computed_at: datetime = field(default_factory=datetime.utcnow)
    max_dimension: int = 2

    @property
    def total_features(self) -> int:
        """Total number of topological features."""
        return len(self.h0_features) + len(self.h1_features) + len(self.h2_features)

    @property
    def significant_features(self) -> list[TopologicalFeature]:
        """Get all significant features across dimensions."""
        all_features = self.h0_features + self.h1_features + self.h2_features
        return [f for f in all_features if f.is_significant]

    def get_features_by_dimension(self, dimension: int) -> list[TopologicalFeature]:
        """Get features for a specific homology dimension."""
        if dimension == 0:
            return self.h0_features
        elif dimension == 1:
            return self.h1_features
        elif dimension == 2:
            return self.h2_features
        else:
            return []


@dataclass
class CoverageVoid:
    """
    A gap in schedule coverage detected via H2 homology (2D voids).

    Attributes:
        void_id: Unique identifier
        start_date: Start of coverage gap
        end_date: End of coverage gap
        affected_rotations: Rotation IDs with gaps
        severity: How significant the void is (0.0-1.0)
        persistence: Topological persistence of the void
    """

    void_id: str
    start_date: date
    end_date: date
    affected_rotations: list[str] = field(default_factory=list)
    severity: float = 0.0
    persistence: float = 0.0


@dataclass
class CyclicPattern:
    """
    A cyclic rotation pattern detected via H1 homology (loops).

    Attributes:
        pattern_id: Unique identifier
        cycle_length_days: Length of cycle in days
        residents_involved: Resident IDs in the cycle
        rotations_involved: Rotation IDs in the cycle
        strength: How strong/consistent the pattern is (0.0-1.0)
        persistence: Topological persistence of the loop
    """

    pattern_id: str
    cycle_length_days: int
    residents_involved: list[str] = field(default_factory=list)
    rotations_involved: list[str] = field(default_factory=list)
    strength: float = 0.0
    persistence: float = 0.0


class PersistentScheduleAnalyzer:
    """
    Topological Data Analysis for medical residency schedules.

    Uses persistent homology to detect multi-scale structural patterns:
    - Resident clustering (H0)
    - Cyclic rotation patterns (H1)
    - Coverage gaps (H2)
    """

    def __init__(self, db: Session, max_dimension: int = 2):
        """
        Initialize the analyzer.

        Args:
            db: Database session
            max_dimension: Maximum homology dimension to compute (0, 1, or 2)
        """
        self.db = db
        self.max_dimension = max_dimension

    def embed_assignments(
        self,
        assignments: list[Any],
        method: str = "pca",
        n_components: int = 3,
    ) -> np.ndarray:
        """
        Embed schedule assignments as a point cloud in Euclidean space.

        Converts discrete assignment data (person, block, rotation) into a continuous
        geometric representation suitable for persistent homology.

        Args:
            assignments: List of Assignment model instances
            method: Embedding method ('pca', 'mds', 'tsne', 'manual')
            n_components: Number of dimensions for embedding (2 or 3)

        Returns:
            Point cloud as numpy array of shape (n_assignments, n_components)

        Raises:
            ValueError: If assignments is empty or method is invalid
        """
        if not assignments:
            raise ValueError("Cannot embed empty assignment list")

        # Extract features from assignments
        features = self._extract_assignment_features(assignments)

        if features.size == 0:
            raise ValueError("Failed to extract features from assignments")

        # Standardize features
        if HAS_SKLEARN:
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
        else:
            # Manual standardization
            mean = np.mean(features, axis=0)
            std = np.std(features, axis=0) + 1e-8  # Avoid division by zero
            features_scaled = (features - mean) / std

        # Apply dimensionality reduction
        if method == "pca" and HAS_SKLEARN:
            reducer = PCA(n_components=n_components)
            point_cloud = reducer.fit_transform(features_scaled)
            logger.info(
                f"PCA embedding: explained variance = "
                f"{sum(reducer.explained_variance_ratio_):.2%}"
            )
        elif method == "mds" and HAS_SKLEARN:
            reducer = MDS(n_components=n_components, random_state=42)
            point_cloud = reducer.fit_transform(features_scaled)
        elif method == "tsne" and HAS_SKLEARN:
            # t-SNE works better with more initial dimensions
            if features_scaled.shape[1] > n_components:
                pca = PCA(n_components=min(50, features_scaled.shape[1]))
                features_reduced = pca.fit_transform(features_scaled)
            else:
                features_reduced = features_scaled

            reducer = TSNE(n_components=n_components, random_state=42)
            point_cloud = reducer.fit_transform(features_reduced)
        elif method == "manual":
            # Simple manual embedding: take first n_components features
            point_cloud = features_scaled[:, :n_components]
        else:
            # Fallback: use first n_components dimensions
            logger.warning(f"Unknown method '{method}', using manual embedding")
            point_cloud = features_scaled[
                :, : min(n_components, features_scaled.shape[1])
            ]

        logger.info(
            f"Embedded {len(assignments)} assignments to {point_cloud.shape[1]}D point cloud"
        )
        return point_cloud

    def _extract_assignment_features(self, assignments: list[Any]) -> np.ndarray:
        """
        Extract numerical features from assignments for embedding.

        Features include:
        - Person ID (encoded numerically)
        - Block ID (encoded as temporal position)
        - Rotation template ID (encoded numerically)
        - Role (encoded: primary=0, supervising=1, backup=2)
        - Temporal features (day of week, week of year)

        Args:
            assignments: List of Assignment instances

        Returns:
            Feature matrix of shape (n_assignments, n_features)
        """
        from app.models.block import Block

        features_list = []

        # Build lookup maps for categorical encoding
        unique_persons = list(set(a.person_id for a in assignments))
        unique_rotations = list(
            set(a.rotation_template_id for a in assignments if a.rotation_template_id)
        )

        person_to_idx = {pid: idx for idx, pid in enumerate(unique_persons)}
        rotation_to_idx = {rid: idx for idx, rid in enumerate(unique_rotations)}

        # Role encoding
        role_map = {"primary": 0, "supervising": 1, "backup": 2}

        for assignment in assignments:
            # Get block for temporal features
            block = self.db.query(Block).filter(Block.id == assignment.block_id).first()

            if not block or not block.date:
                # Skip assignments without valid blocks
                continue

            # Feature vector for this assignment
            feature_vec = [
                # Categorical encodings
                person_to_idx.get(assignment.person_id, -1),
                rotation_to_idx.get(assignment.rotation_template_id, -1),
                role_map.get(assignment.role, -1),
                # Temporal features
                block.date.toordinal(),  # Absolute day number
                block.date.weekday(),  # Day of week (0-6)
                block.date.isocalendar()[1],  # Week of year (1-53)
                1 if block.session == "AM" else 0,  # Session (AM=1, PM=0)
                # Workload proxy (could be computed from role)
                1.0 if assignment.role == "primary" else 0.5,
            ]

            features_list.append(feature_vec)

        if not features_list:
            return np.array([])

        features = np.array(features_list, dtype=float)
        logger.info(
            f"Extracted {features.shape[1]} features from {features.shape[0]} assignments"
        )
        return features

    def compute_persistence_diagram(
        self, point_cloud: np.ndarray
    ) -> PersistenceDiagram:
        """
        Compute persistent homology from a point cloud.

        Uses Vietoris-Rips filtration to build a simplicial complex and compute
        homology groups across filtration scales.

        Args:
            point_cloud: Point cloud as numpy array of shape (n_points, n_dims)

        Returns:
            PersistenceDiagram with topological features

        Raises:
            ValueError: If point cloud is invalid
        """
        if point_cloud.size == 0:
            raise ValueError("Cannot compute persistence of empty point cloud")

        if not HAS_RIPSER:
            # Mock implementation for when ripser is not installed
            logger.warning("Using mock persistence computation (ripser not available)")
            return self._mock_persistence_diagram(point_cloud)

        # Compute persistent homology using ripser
        logger.info(
            f"Computing persistent homology (max_dim={self.max_dimension}) "
            f"for {len(point_cloud)} points in {point_cloud.shape[1]}D"
        )

        try:
            result = ripser(point_cloud, maxdim=self.max_dimension)
            dgms = result["dgms"]

            # Parse results into TopologicalFeature objects
            h0_features = []
            h1_features = []
            h2_features = []

            # H0 (connected components)
            if len(dgms) > 0:
                for birth, death in dgms[0]:
                    if not np.isinf(death):  # Filter out infinite persistence
                        h0_features.append(
                            TopologicalFeature(
                                dimension=0,
                                birth=float(birth),
                                death=float(death),
                                persistence=float(death - birth),
                                interpretation="Connected component (resident cluster)",
                            )
                        )

            # H1 (loops/cycles)
            if len(dgms) > 1:
                for birth, death in dgms[1]:
                    if not np.isinf(death):
                        h1_features.append(
                            TopologicalFeature(
                                dimension=1,
                                birth=float(birth),
                                death=float(death),
                                persistence=float(death - birth),
                                interpretation="Loop (cyclic rotation pattern)",
                            )
                        )

            # H2 (voids)
            if len(dgms) > 2:
                for birth, death in dgms[2]:
                    if not np.isinf(death):
                        h2_features.append(
                            TopologicalFeature(
                                dimension=2,
                                birth=float(birth),
                                death=float(death),
                                persistence=float(death - birth),
                                interpretation="Void (coverage gap)",
                            )
                        )

            logger.info(
                f"Found {len(h0_features)} H0, {len(h1_features)} H1, "
                f"{len(h2_features)} H2 features"
            )

            return PersistenceDiagram(
                h0_features=h0_features,
                h1_features=h1_features,
                h2_features=h2_features,
                max_dimension=self.max_dimension,
            )

        except Exception as e:
            logger.error(f"Error computing persistence: {e}")
            # Return empty diagram on error
            return PersistenceDiagram(max_dimension=self.max_dimension)

    def _mock_persistence_diagram(self, point_cloud: np.ndarray) -> PersistenceDiagram:
        """
        Create a mock persistence diagram when ripser is unavailable.

        Uses simple heuristics based on distance matrix.

        Args:
            point_cloud: Point cloud array

        Returns:
            Mock PersistenceDiagram
        """
        # Compute pairwise distances
        from scipy.spatial.distance import pdist, squareform

        distances = squareform(pdist(point_cloud))

        # Mock H0: connected components based on distance threshold
        h0_features = []
        thresholds = np.linspace(0, np.max(distances), 10)
        for i, thresh in enumerate(thresholds[:-1]):
            h0_features.append(
                TopologicalFeature(
                    dimension=0,
                    birth=float(thresh),
                    death=float(thresholds[i + 1]),
                    persistence=float(thresholds[i + 1] - thresh),
                    interpretation="Connected component (mock)",
                )
            )

        return PersistenceDiagram(
            h0_features=h0_features,
            h1_features=[],  # No mock H1
            h2_features=[],  # No mock H2
            max_dimension=0,
        )

    def extract_schedule_voids(
        self, diagram: PersistenceDiagram, assignments: list[Any]
    ) -> list[CoverageVoid]:
        """
        Extract coverage voids from H2 topological features.

        Voids represent structural gaps in coverage - combinations of time periods
        and services that lack sufficient staffing.

        Args:
            diagram: Persistence diagram with H2 features
            assignments: Original assignments for context

        Returns:
            List of CoverageVoid objects
        """
        voids = []

        # Get significant H2 features
        significant_h2 = [f for f in diagram.h2_features if f.is_significant]

        if not significant_h2:
            logger.info("No significant coverage voids detected")
            return []

        # Get date range from assignments
        from app.models.block import Block

        blocks = (
            self.db.query(Block)
            .filter(Block.id.in_([a.block_id for a in assignments]))
            .all()
        )
        dates = [b.date for b in blocks if b.date]

        if not dates:
            return []

        start_date = min(dates)
        end_date = max(dates)
        date_range_days = (end_date - start_date).days

        # Map each H2 feature to a coverage void
        for idx, feature in enumerate(significant_h2):
            # Estimate affected date range based on persistence
            # Higher persistence = larger void = longer time span
            void_span_days = int(feature.persistence * date_range_days / 10)
            void_span_days = max(1, min(void_span_days, date_range_days))

            # Estimate start date (proportional to birth time)
            offset_days = int(
                feature.birth
                * date_range_days
                / (np.max([f.death for f in significant_h2]) + 1e-8)
            )
            void_start = start_date + np.timedelta64(offset_days, "D")
            void_end = void_start + np.timedelta64(void_span_days, "D")

            # Severity based on persistence and birth time
            severity = min(1.0, feature.persistence / (feature.birth + 0.1))

            voids.append(
                CoverageVoid(
                    void_id=f"void_{idx}",
                    start_date=void_start.astype(date),
                    end_date=void_end.astype(date),
                    affected_rotations=[],  # Would need clustering to determine
                    severity=severity,
                    persistence=feature.persistence,
                )
            )

        logger.info(f"Extracted {len(voids)} coverage voids from H2 features")
        return voids

    def detect_cyclic_patterns(
        self, diagram: PersistenceDiagram, assignments: list[Any]
    ) -> list[CyclicPattern]:
        """
        Detect cyclic rotation patterns from H1 topological features.

        Loops in the data represent recurring patterns - residents rotating through
        the same services in consistent cycles.

        Args:
            diagram: Persistence diagram with H1 features
            assignments: Original assignments for context

        Returns:
            List of CyclicPattern objects
        """
        patterns = []

        # Get significant H1 features (loops)
        significant_h1 = [f for f in diagram.h1_features if f.is_significant]

        if not significant_h1:
            logger.info("No significant cyclic patterns detected")
            return []

        # Common cycle lengths in medical residency (days)
        common_cycles = [7, 14, 21, 28]  # Weekly, biweekly, 3-week, 4-week

        for idx, feature in enumerate(significant_h1):
            # Estimate cycle length from persistence
            # Higher persistence = more stable cycle
            # Birth time relates to cycle period
            estimated_cycle = feature.birth * 30  # Scale to days

            # Snap to nearest common cycle length
            cycle_length = min(common_cycles, key=lambda x: abs(x - estimated_cycle))

            # Strength based on persistence (how consistent the pattern is)
            strength = min(1.0, feature.persistence / (feature.birth + 0.1))

            patterns.append(
                CyclicPattern(
                    pattern_id=f"cycle_{idx}",
                    cycle_length_days=cycle_length,
                    residents_involved=[],  # Would need clustering to determine
                    rotations_involved=[],  # Would need clustering to determine
                    strength=strength,
                    persistence=feature.persistence,
                )
            )

        logger.info(f"Detected {len(patterns)} cyclic patterns from H1 features")
        return patterns

    def compute_structural_anomaly_score(self, diagram: PersistenceDiagram) -> float:
        """
        Compute an overall structural anomaly score from topological features.

        Higher scores indicate unusual topological structure (e.g., too many voids,
        unexpected clustering, lack of cyclic patterns).

        Args:
            diagram: Persistence diagram

        Returns:
            Anomaly score (0.0-1.0), where 0 = normal, 1 = highly anomalous
        """
        # Baseline expectations for a "normal" schedule
        EXPECTED_H0_COUNT = 5  # Some clustering is normal
        EXPECTED_H1_COUNT = 3  # A few cyclic patterns expected
        EXPECTED_H2_COUNT = 0  # Voids are bad (should be 0)

        # Count significant features
        sig_h0 = sum(1 for f in diagram.h0_features if f.is_significant)
        sig_h1 = sum(1 for f in diagram.h1_features if f.is_significant)
        sig_h2 = sum(1 for f in diagram.h2_features if f.is_significant)

        # Deviation from expectations
        h0_dev = abs(sig_h0 - EXPECTED_H0_COUNT) / max(EXPECTED_H0_COUNT, 1)
        h1_dev = abs(sig_h1 - EXPECTED_H1_COUNT) / max(EXPECTED_H1_COUNT, 1)
        h2_excess = sig_h2  # Any H2 is anomalous

        # Weighted anomaly score
        anomaly_score = (
            0.3 * min(1.0, h0_dev)  # Too many/few clusters
            + 0.3 * min(1.0, h1_dev)  # Unusual cyclic patterns
            + 0.4 * min(1.0, h2_excess / 3)  # Voids are the worst
        )

        logger.info(
            f"Structural anomaly score: {anomaly_score:.3f} "
            f"(H0={sig_h0}, H1={sig_h1}, H2={sig_h2})"
        )

        return float(anomaly_score)

    def compare_schedules_topologically(
        self,
        assignments_a: list[Any],
        assignments_b: list[Any],
        method: str = "bottleneck",
    ) -> float:
        """
        Compare two schedules using topological distance metrics.

        Uses bottleneck distance (or Wasserstein distance) between persistence
        diagrams to measure structural similarity.

        Args:
            assignments_a: First schedule's assignments
            assignments_b: Second schedule's assignments
            method: Distance metric ('bottleneck' or 'wasserstein')

        Returns:
            Distance between schedules (0 = identical, higher = more different)
        """
        # Embed both schedules
        cloud_a = self.embed_assignments(assignments_a)
        cloud_b = self.embed_assignments(assignments_b)

        # Compute persistence diagrams
        dgm_a = self.compute_persistence_diagram(cloud_a)
        dgm_b = self.compute_persistence_diagram(cloud_b)

        if not HAS_RIPSER:
            # Fallback: simple feature count difference
            diff_h0 = abs(len(dgm_a.h0_features) - len(dgm_b.h0_features))
            diff_h1 = abs(len(dgm_a.h1_features) - len(dgm_b.h1_features))
            diff_h2 = abs(len(dgm_a.h2_features) - len(dgm_b.h2_features))
            distance = (diff_h0 + diff_h1 + diff_h2) / 10.0
            logger.info(
                f"Mock topological distance: {distance:.3f} (ripser not available)"
            )
            return distance

        # Compute bottleneck distance for each dimension
        distances = []

        try:
            # H0 distance
            if dgm_a.h0_features and dgm_b.h0_features:
                dgm_a_h0 = np.array([[f.birth, f.death] for f in dgm_a.h0_features])
                dgm_b_h0 = np.array([[f.birth, f.death] for f in dgm_b.h0_features])
                dist_h0 = bottleneck(dgm_a_h0, dgm_b_h0)
                distances.append(dist_h0)

            # H1 distance
            if dgm_a.h1_features and dgm_b.h1_features:
                dgm_a_h1 = np.array([[f.birth, f.death] for f in dgm_a.h1_features])
                dgm_b_h1 = np.array([[f.birth, f.death] for f in dgm_b.h1_features])
                dist_h1 = bottleneck(dgm_a_h1, dgm_b_h1)
                distances.append(dist_h1)

            # H2 distance
            if dgm_a.h2_features and dgm_b.h2_features:
                dgm_a_h2 = np.array([[f.birth, f.death] for f in dgm_a.h2_features])
                dgm_b_h2 = np.array([[f.birth, f.death] for f in dgm_b.h2_features])
                dist_h2 = bottleneck(dgm_a_h2, dgm_b_h2)
                distances.append(dist_h2)

            # Combined distance (weighted average across dimensions)
            if distances:
                total_distance = float(np.mean(distances))
            else:
                # No features to compare
                total_distance = 0.0

            logger.info(f"Topological distance (bottleneck): {total_distance:.3f}")
            return total_distance

        except Exception as e:
            logger.error(f"Error computing bottleneck distance: {e}")
            return 0.0

    def analyze_schedule(
        self,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict[str, Any]:
        """
        Perform comprehensive topological analysis of schedule.

        Args:
            start_date: Start of date range to analyze
            end_date: End of date range to analyze

        Returns:
            Dictionary with analysis results
        """
        from app.models.assignment import Assignment
        from app.models.block import Block

        # Get assignments in date range
        query = self.db.query(Assignment)
        if start_date or end_date:
            query = query.join(Block)
            if start_date:
                query = query.filter(Block.date >= start_date)
            if end_date:
                query = query.filter(Block.date <= end_date)

        assignments = query.all()

        if not assignments:
            return {
                "error": "No assignments found in date range",
                "total_assignments": 0,
            }

        # Perform TDA analysis
        point_cloud = self.embed_assignments(assignments, method="pca")
        diagram = self.compute_persistence_diagram(point_cloud)
        voids = self.extract_schedule_voids(diagram, assignments)
        cycles = self.detect_cyclic_patterns(diagram, assignments)
        anomaly_score = self.compute_structural_anomaly_score(diagram)

        return {
            "total_assignments": len(assignments),
            "point_cloud_shape": point_cloud.shape,
            "persistence_diagram": {
                "h0_features": len(diagram.h0_features),
                "h1_features": len(diagram.h1_features),
                "h2_features": len(diagram.h2_features),
                "total_features": diagram.total_features,
                "significant_features": len(diagram.significant_features),
            },
            "coverage_voids": [
                {
                    "void_id": v.void_id,
                    "start_date": v.start_date.isoformat(),
                    "end_date": v.end_date.isoformat(),
                    "severity": round(v.severity, 3),
                    "persistence": round(v.persistence, 3),
                }
                for v in voids
            ],
            "cyclic_patterns": [
                {
                    "pattern_id": c.pattern_id,
                    "cycle_length_days": c.cycle_length_days,
                    "strength": round(c.strength, 3),
                    "persistence": round(c.persistence, 3),
                }
                for c in cycles
            ],
            "anomaly_score": round(anomaly_score, 3),
            "computed_at": datetime.utcnow().isoformat(),
        }
