"""
Workload Optimizer - ML model for optimizing workload distribution.

Uses clustering and optimization algorithms to:
- Balance workload across faculty and residents
- Identify overloaded individuals
- Suggest workload redistribution
- Ensure fairness in assignments
"""

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class WorkloadOptimizer:
    """
    Optimizes workload distribution using Gradient Boosting and clustering.

    Features:
    - Predicts optimal workload levels for each person
    - Identifies workload imbalances
    - Suggests assignments to balance load
    - Considers ACGME constraints and fairness
    - Clusters similar workload patterns
    """

    def __init__(
        self,
        model_path: Path | None = None,
        n_estimators: int = 100,
        max_depth: int = 6,
        learning_rate: float = 0.1,
        random_state: int = 42,
    ):
        """
        Initialize workload optimizer.

        Args:
            model_path: Path to load pre-trained model from
            n_estimators: Number of boosting stages
            max_depth: Maximum depth of trees
            learning_rate: Learning rate for boosting
            random_state: Random seed for reproducibility
        """
        self.model_path = model_path
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.learning_rate = learning_rate
        self.random_state = random_state

        # Models and preprocessors
        self.workload_model: GradientBoostingRegressor | None = None
        self.scaler: StandardScaler | None = None
        self.clusterer: KMeans | None = None
        self.feature_names: list[str] = []

        # Load pre-trained model if path provided
        if model_path and model_path.exists():
            self.load(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize new models."""
        self.workload_model = GradientBoostingRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            subsample=0.8,
            min_samples_split=10,
            min_samples_leaf=4,
        )
        self.scaler = StandardScaler()
        self.clusterer = KMeans(n_clusters=5, random_state=self.random_state, n_init=10)
        logger.info("Initialized new workload optimization model")

    def extract_features(
        self,
        person_data: dict[str, Any],
        current_assignments: list[dict[str, Any]],
        historical_data: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Extract features for workload prediction.

        Args:
            person_data: Person attributes (type, role, etc.)
            current_assignments: List of current assignments for this person
            historical_data: Historical workload statistics

        Returns:
            DataFrame with feature columns
        """
        features = {}

        # Person characteristics
        features["is_faculty"] = 1 if person_data.get("type") == "faculty" else 0
        features["is_resident"] = 1 if person_data.get("type") == "resident" else 0
        features["pgy_level"] = person_data.get("pgy_level", 0) or 0

        # Faculty role encoding
        faculty_role = person_data.get("faculty_role", "")
        for role in ["pd", "apd", "oic", "dept_chief", "sports_med", "core"]:
            features[f"role_{role}"] = 1 if faculty_role == role else 0

        # Target workload capacity
        features["target_clinical_blocks"] = (
            person_data.get("target_clinical_blocks", 48) or 48
        )

        # Current workload metrics
        num_assignments = len(current_assignments)
        features["current_assignment_count"] = num_assignments

        # Count by rotation type
        rotation_counts = {
            "clinic": 0,
            "inpatient": 0,
            "procedures": 0,
            "admin": 0,
            "other": 0,
        }
        for assignment in current_assignments:
            rotation_name = assignment.get("rotation_name", "").lower()
            if "clinic" in rotation_name:
                rotation_counts["clinic"] += 1
            elif "inpatient" in rotation_name or "ward" in rotation_name:
                rotation_counts["inpatient"] += 1
            elif "procedure" in rotation_name:
                rotation_counts["procedures"] += 1
            elif "admin" in rotation_name or "conference" in rotation_name:
                rotation_counts["admin"] += 1
            else:
                rotation_counts["other"] += 1

        for rot_type, count in rotation_counts.items():
            features[f"assignments_{rot_type}"] = count

        # Workload concentration (diversity measure)
        if num_assignments > 0:
            counts = list(rotation_counts.values())
            counts = [c for c in counts if c > 0]
            # Herfindahl index for diversity
            diversity = sum((c / num_assignments) ** 2 for c in counts) if counts else 0
            features["workload_concentration"] = diversity
        else:
            features["workload_concentration"] = 0.0

        # Weekend/holiday burden
        weekend_count = sum(
            1 for a in current_assignments if a.get("is_weekend", False)
        )
        features["weekend_assignment_count"] = weekend_count

        # Call/night shift burden (if tracked)
        features["call_count"] = person_data.get("weekday_call_count", 0)
        features["sunday_call_count"] = person_data.get("sunday_call_count", 0)
        features["fmit_weeks_count"] = person_data.get("fmit_weeks_count", 0)

        # Historical metrics (if available)
        if historical_data:
            features["historical_avg_workload"] = historical_data.get(
                "avg_workload", 0.0
            )
            features["historical_max_workload"] = historical_data.get(
                "max_workload", 0.0
            )
            features["historical_swap_rate"] = historical_data.get("swap_rate", 0.0)
            features["historical_conflict_rate"] = historical_data.get(
                "conflict_rate", 0.0
            )
        else:
            features["historical_avg_workload"] = 0.0
            features["historical_max_workload"] = 0.0
            features["historical_swap_rate"] = 0.0
            features["historical_conflict_rate"] = 0.0

        # Workload utilization ratio
        target = features["target_clinical_blocks"]
        if target > 0:
            features["workload_utilization"] = num_assignments / target
        else:
            features["workload_utilization"] = 0.0

        return pd.DataFrame([features])

    def train(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        validation_split: float = 0.2,
    ) -> dict[str, float]:
        """
        Train the workload optimization model.

        Args:
            X: Feature matrix
            y: Target optimal workload levels (normalized 0-1)
            validation_split: Fraction for validation

        Returns:
            Training metrics
        """
        logger.info(f"Training workload optimizer on {len(X)} samples")

        # Store feature names
        self.feature_names = list(X.columns)

        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Train workload prediction model
        self.workload_model.fit(X_train_scaled, y_train)

        # Train clustering model for workload patterns
        self.clusterer.fit(X_train_scaled)

        # Evaluate
        train_score = self.workload_model.score(X_train_scaled, y_train)
        val_score = self.workload_model.score(X_val_scaled, y_val)

        # Get feature importances
        feature_importance = dict(
            zip(self.feature_names, self.workload_model.feature_importances_)
        )
        top_features = sorted(
            feature_importance.items(), key=lambda x: x[1], reverse=True
        )[:5]

        logger.info(
            f"Training complete: R² train={train_score:.3f}, val={val_score:.3f}"
        )
        logger.info(f"Top features: {top_features}")

        return {
            "train_r2": float(train_score),
            "val_r2": float(val_score),
            "n_samples": len(X),
            "n_features": len(self.feature_names),
            "n_clusters": int(self.clusterer.n_clusters),
            "top_features": top_features,
        }

    def predict_optimal_workload(
        self,
        person_data: dict[str, Any],
        current_assignments: list[dict[str, Any]],
        historical_data: dict[str, Any] | None = None,
    ) -> float:
        """
        Predict optimal workload level for a person.

        Args:
            person_data: Person attributes
            current_assignments: Current assignments
            historical_data: Historical statistics

        Returns:
            Optimal workload score (0-1, where 0.8 is ideal per resilience framework)
        """
        if self.workload_model is None or self.scaler is None:
            logger.warning("Model not trained, returning default optimal workload")
            return 0.8  # Default to 80% utilization (resilience framework)

        # Extract features
        X = self.extract_features(person_data, current_assignments, historical_data)

        # Ensure all expected features are present
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0

        # Reorder columns
        X = X[self.feature_names]

        # Scale and predict
        X_scaled = self.scaler.transform(X)
        optimal_workload = self.workload_model.predict(X_scaled)[0]

        # Clip to valid range
        return float(np.clip(optimal_workload, 0.0, 1.0))

    def identify_overloaded(
        self,
        people_data: list[dict[str, Any]],
        threshold: float = 0.85,
    ) -> list[dict[str, Any]]:
        """
        Identify people with excessive workload.

        Args:
            people_data: List of person dictionaries with assignments
            threshold: Workload threshold (default 85% per resilience framework)

        Returns:
            List of overloaded people with details
        """
        overloaded = []

        for person in people_data:
            workload = self.predict_optimal_workload(
                person_data=person.get("person", {}),
                current_assignments=person.get("assignments", []),
                historical_data=person.get("historical_data"),
            )

            if workload > threshold:
                overloaded.append(
                    {
                        "person_id": person.get("person", {}).get("id"),
                        "person_name": person.get("person", {}).get("name"),
                        "current_workload": workload,
                        "threshold": threshold,
                        "overload_amount": workload - threshold,
                        "num_assignments": len(person.get("assignments", [])),
                    }
                )

        # Sort by overload amount (most overloaded first)
        overloaded.sort(key=lambda x: x["overload_amount"], reverse=True)

        return overloaded

    def suggest_rebalancing(
        self,
        people_data: list[dict[str, Any]],
        target_utilization: float = 0.8,
    ) -> list[dict[str, Any]]:
        """
        Suggest workload rebalancing actions.

        Args:
            people_data: List of person dictionaries with assignments
            target_utilization: Target workload utilization (default 80%)

        Returns:
            List of suggested actions
        """
        suggestions = []

        # Calculate current workload for everyone
        workloads = []
        for person in people_data:
            workload = self.predict_optimal_workload(
                person_data=person.get("person", {}),
                current_assignments=person.get("assignments", []),
                historical_data=person.get("historical_data"),
            )
            workloads.append(
                {
                    "person": person,
                    "workload": workload,
                    "num_assignments": len(person.get("assignments", [])),
                }
            )

        # Sort by workload
        workloads.sort(key=lambda x: x["workload"])

        # Find underutilized and overutilized
        underutilized = [
            w for w in workloads if w["workload"] < target_utilization - 0.1
        ]
        overutilized = [
            w for w in workloads if w["workload"] > target_utilization + 0.1
        ]

        # Suggest transfers
        for over in overutilized:
            for under in underutilized:
                # Check if roles are compatible
                over_person = over["person"].get("person", {})
                under_person = under["person"].get("person", {})

                if over_person.get("type") == under_person.get("type"):
                    suggestions.append(
                        {
                            "action": "transfer_assignment",
                            "from_person_id": over_person.get("id"),
                            "from_person_name": over_person.get("name"),
                            "to_person_id": under_person.get("id"),
                            "to_person_name": under_person.get("name"),
                            "from_workload": over["workload"],
                            "to_workload": under["workload"],
                            "priority": abs(over["workload"] - target_utilization)
                            + abs(under["workload"] - target_utilization),
                        }
                    )

        # Sort suggestions by priority
        suggestions.sort(key=lambda x: x["priority"], reverse=True)

        return suggestions[:10]  # Return top 10 suggestions

    def get_workload_cluster(
        self,
        person_data: dict[str, Any],
        current_assignments: list[dict[str, Any]],
        historical_data: dict[str, Any] | None = None,
    ) -> int:
        """
        Get workload cluster for a person.

        Args:
            person_data: Person attributes
            current_assignments: Current assignments
            historical_data: Historical statistics

        Returns:
            Cluster ID (0 to n_clusters-1)
        """
        if self.clusterer is None or self.scaler is None:
            return 0

        # Extract features
        X = self.extract_features(person_data, current_assignments, historical_data)

        # Ensure all expected features are present
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0

        # Reorder columns
        X = X[self.feature_names]

        # Scale and predict cluster
        X_scaled = self.scaler.transform(X)
        cluster = self.clusterer.predict(X_scaled)[0]

        return int(cluster)

    def calculate_fairness_metric(
        self,
        people_data: list[dict[str, Any]],
    ) -> dict[str, float]:
        """
        Calculate fairness metrics for workload distribution.

        Args:
            people_data: List of person dictionaries with assignments

        Returns:
            Fairness metrics (Gini coefficient, std deviation, etc.)
        """
        workloads = []
        for person in people_data:
            workload = self.predict_optimal_workload(
                person_data=person.get("person", {}),
                current_assignments=person.get("assignments", []),
                historical_data=person.get("historical_data"),
            )
            workloads.append(workload)

        if not workloads:
            return {"gini_coefficient": 0.0, "std_deviation": 0.0, "mean_workload": 0.0}

        workloads = np.array(workloads)

        # Gini coefficient (measure of inequality)
        sorted_workloads = np.sort(workloads)
        n = len(workloads)
        cumsum = np.cumsum(sorted_workloads)
        gini = (2 * np.sum((np.arange(1, n + 1)) * sorted_workloads)) / (
            n * np.sum(workloads)
        ) - (n + 1) / n

        return {
            "gini_coefficient": float(gini),
            "std_deviation": float(np.std(workloads)),
            "mean_workload": float(np.mean(workloads)),
            "min_workload": float(np.min(workloads)),
            "max_workload": float(np.max(workloads)),
        }

    def save(self, path: Path) -> None:
        """Save model to disk."""
        path.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.workload_model, path / "workload_model.pkl")
        joblib.dump(self.scaler, path / "scaler.pkl")
        joblib.dump(self.clusterer, path / "clusterer.pkl")
        joblib.dump(self.feature_names, path / "features.pkl")

        logger.info(f"Saved workload optimizer to {path}")

    def load(self, path: Path) -> None:
        """Load model from disk."""
        self.workload_model = joblib.load(path / "workload_model.pkl")
        self.scaler = joblib.load(path / "scaler.pkl")
        self.clusterer = joblib.load(path / "clusterer.pkl")
        self.feature_names = joblib.load(path / "features.pkl")

        logger.info(f"Loaded workload optimizer from {path}")
