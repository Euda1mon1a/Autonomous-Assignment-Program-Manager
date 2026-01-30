"""
Conflict Predictor - ML model for predicting scheduling conflicts.

Uses classification algorithms to predict:
- Potential ACGME violations
- Schedule conflicts before they occur
- Swap request likelihood
- Coverage gaps
"""

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class ConflictPredictor:
    """
    Predicts scheduling conflicts using Gradient Boosting Classifier.

    Features:
    - Predicts probability of ACGME violations
    - Detects potential schedule conflicts
    - Identifies coverage gaps
    - Predicts swap requests
    - Provides early warning system
    """

    def __init__(
        self,
        model_path: Path | None = None,
        n_estimators: int = 100,
        max_depth: int = 5,
        learning_rate: float = 0.1,
        random_state: int = 42,
    ) -> None:
        """
        Initialize conflict predictor.

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
        self.model: GradientBoostingClassifier | None = None
        self.scaler: StandardScaler | None = None
        self.feature_names: list[str] = []

        # Load pre-trained model if path provided
        if model_path and model_path.exists():
            self.load(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize a new Gradient Boosting classifier."""
        self.model = GradientBoostingClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            random_state=self.random_state,
            subsample=0.8,
            min_samples_split=10,
            min_samples_leaf=4,
        )
        self.scaler = StandardScaler()
        logger.info("Initialized new conflict prediction model")

    def extract_features(
        self,
        person_data: dict[str, Any],
        proposed_assignment: dict[str, Any],
        existing_assignments: list[dict[str, Any]],
        context_data: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Extract features for conflict prediction.

        Args:
            person_data: Person attributes
            proposed_assignment: New assignment being considered
            existing_assignments: Person's current assignments
            context_data: Additional context (team composition, coverage levels)

        Returns:
            DataFrame with feature columns
        """
        features = {}

        # Person characteristics
        features["is_faculty"] = 1 if person_data.get("type") == "faculty" else 0
        features["is_resident"] = 1 if person_data.get("type") == "resident" else 0
        features["pgy_level"] = person_data.get("pgy_level", 0) or 0

        # Current workload
        features["current_assignment_count"] = len(existing_assignments)

        # Calculate hours worked this week (for 80-hour rule)
        # Assuming each assignment is a half-day (4 hours)
        total_hours = len(existing_assignments) * 4
        features["hours_this_week"] = total_hours
        features["approaching_80_hour_limit"] = 1 if total_hours >= 70 else 0
        features["exceeds_80_hour_limit"] = 1 if total_hours >= 80 else 0

        # Days worked (for 1-in-7 rule)
        unique_dates = set()
        for assignment in existing_assignments:
            if "date" in assignment:
                unique_dates.add(assignment["date"])

        features["days_worked_this_week"] = len(unique_dates)
        features["violates_1_in_7"] = 1 if len(unique_dates) >= 7 else 0

        # Consecutive days worked
        if existing_assignments:
            # Sort by date
            sorted_assignments = sorted(
                existing_assignments, key=lambda x: x.get("date", "")
            )
            consecutive_days = 1
            max_consecutive = 1

            for i in range(1, len(sorted_assignments)):
                prev_date = sorted_assignments[i - 1].get("date", "")
                curr_date = sorted_assignments[i].get("date", "")

                if prev_date and curr_date:
                    # Check if dates are consecutive (simplified)
                    consecutive_days += 1
                    max_consecutive = max(max_consecutive, consecutive_days)
                else:
                    consecutive_days = 1

            features["max_consecutive_days"] = max_consecutive
        else:
            features["max_consecutive_days"] = 0

            # Proposed assignment characteristics
        proposed_date = proposed_assignment.get("date")
        features["proposed_is_weekend"] = (
            1 if proposed_assignment.get("is_weekend", False) else 0
        )
        features["proposed_is_holiday"] = (
            1 if proposed_assignment.get("is_holiday", False) else 0
        )

        # Day of week for proposed assignment
        if proposed_date and isinstance(proposed_date, str):
            try:
                date_obj = pd.to_datetime(proposed_date).date()
                features["proposed_day_of_week"] = date_obj.weekday()
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Failed to parse proposed date '{proposed_date}': {e}")
                features["proposed_day_of_week"] = 0
        else:
            features["proposed_day_of_week"] = 0

            # Rotation type conflicts
        proposed_rotation = proposed_assignment.get("rotation_name", "").lower()
        features["proposed_is_clinic"] = 1 if "clinic" in proposed_rotation else 0
        features["proposed_is_inpatient"] = (
            1 if "inpatient" in proposed_rotation or "ward" in proposed_rotation else 0
        )
        features["proposed_is_procedure"] = 1 if "procedure" in proposed_rotation else 0

        # Check for same-day conflicts
        same_day_assignments = [
            a for a in existing_assignments if a.get("date") == proposed_date
        ]
        features["same_day_assignment_count"] = len(same_day_assignments)
        features["has_same_day_conflict"] = 1 if len(same_day_assignments) > 0 else 0

        # ACGME supervision ratio check (for residents)
        if features["is_resident"]:
            supervision_ratio = 2 if features["pgy_level"] == 1 else 4
            features["supervision_ratio"] = supervision_ratio

            # Check if adequate supervision in context
            if context_data:
                faculty_count = context_data.get("faculty_count_on_date", 0)
                resident_count = context_data.get("resident_count_on_date", 1)
                actual_ratio = resident_count / max(faculty_count, 1)
                features["actual_supervision_ratio"] = actual_ratio
                features["violates_supervision"] = (
                    1 if actual_ratio > supervision_ratio else 0
                )
            else:
                features["actual_supervision_ratio"] = 0
                features["violates_supervision"] = 0
        else:
            features["supervision_ratio"] = 0
            features["actual_supervision_ratio"] = 0
            features["violates_supervision"] = 0

            # Call/night shift patterns
        features["call_count"] = person_data.get("weekday_call_count", 0)
        features["sunday_call_count"] = person_data.get("sunday_call_count", 0)

        # Historical conflict rate
        if context_data:
            features["historical_conflict_rate"] = context_data.get(
                "historical_conflict_rate", 0.0
            )
            features["recent_swap_count"] = context_data.get("recent_swap_count", 0)
        else:
            features["historical_conflict_rate"] = 0.0
            features["recent_swap_count"] = 0

            # Coverage level on proposed date
        if context_data:
            features["coverage_level"] = context_data.get("coverage_level", 1.0)
            features["understaffed"] = (
                1 if context_data.get("coverage_level", 1.0) < 0.8 else 0
            )
        else:
            features["coverage_level"] = 1.0
            features["understaffed"] = 0

            # Workload concentration
        rotation_types = [
            a.get("rotation_name", "").lower() for a in existing_assignments
        ]
        if rotation_types:
            # Calculate diversity
            unique_rotations = len(set(rotation_types))
            total_rotations = len(rotation_types)
            features["workload_diversity"] = (
                unique_rotations / total_rotations if total_rotations > 0 else 0
            )
        else:
            features["workload_diversity"] = 0

        return pd.DataFrame([features])

    def train(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        validation_split: float = 0.2,
    ) -> dict[str, float]:
        """
        Train the conflict prediction model.

        Args:
            X: Feature matrix
            y: Binary labels (1 = conflict occurred, 0 = no conflict)
            validation_split: Fraction for validation

        Returns:
            Training metrics
        """
        logger.info(f"Training conflict predictor on {len(X)} samples")

        # Store feature names
        self.feature_names = list(X.columns)

        # Split data
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Train model
        self.model.fit(X_train_scaled, y_train)

        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        val_score = self.model.score(X_val_scaled, y_val)

        # Calculate additional metrics
        y_pred = self.model.predict(X_val_scaled)

        # Confusion matrix components
        tp = np.sum((y_val == 1) & (y_pred == 1))
        fp = np.sum((y_val == 0) & (y_pred == 1))
        tn = np.sum((y_val == 0) & (y_pred == 0))
        fn = np.sum((y_val == 1) & (y_pred == 0))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0
        )

        # Get feature importances
        feature_importance = dict(
            zip(self.feature_names, self.model.feature_importances_)
        )
        top_features = sorted(
            feature_importance.items(), key=lambda x: x[1], reverse=True
        )[:5]

        logger.info(
            f"Training complete: accuracy train={train_score:.3f}, val={val_score:.3f}"
        )
        logger.info(f"Precision: {precision:.3f}, Recall: {recall:.3f}, F1: {f1:.3f}")
        logger.info(f"Top features: {top_features}")

        return {
            "train_accuracy": float(train_score),
            "val_accuracy": float(val_score),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "n_samples": len(X),
            "n_features": len(self.feature_names),
            "top_features": top_features,
        }

    def predict_conflict_probability(
        self,
        person_data: dict[str, Any],
        proposed_assignment: dict[str, Any],
        existing_assignments: list[dict[str, Any]],
        context_data: dict[str, Any] | None = None,
    ) -> float:
        """
        Predict probability of conflict for a proposed assignment.

        Args:
            person_data: Person attributes
            proposed_assignment: New assignment being considered
            existing_assignments: Person's current assignments
            context_data: Additional context

        Returns:
            Conflict probability (0-1, higher means more likely to conflict)
        """
        if self.model is None or self.scaler is None:
            logger.warning("Model not trained, returning default probability")
            return 0.0

            # Extract features
        X = self.extract_features(
            person_data, proposed_assignment, existing_assignments, context_data
        )

        # Ensure all expected features are present
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0

                # Reorder columns
        X = X[self.feature_names]

        # Scale and predict probability
        X_scaled = self.scaler.transform(X)
        prob = self.model.predict_proba(X_scaled)[0][
            1
        ]  # Probability of class 1 (conflict)

        return float(prob)

    def predict_conflict(
        self,
        person_data: dict[str, Any],
        proposed_assignment: dict[str, Any],
        existing_assignments: list[dict[str, Any]],
        context_data: dict[str, Any] | None = None,
        threshold: float = 0.5,
    ) -> bool:
        """
        Predict if a conflict will occur.

        Args:
            person_data: Person attributes
            proposed_assignment: New assignment being considered
            existing_assignments: Person's current assignments
            context_data: Additional context
            threshold: Probability threshold for classification

        Returns:
            True if conflict predicted, False otherwise
        """
        prob = self.predict_conflict_probability(
            person_data, proposed_assignment, existing_assignments, context_data
        )

        return prob >= threshold

    def identify_high_risk_assignments(
        self,
        assignments: list[dict[str, Any]],
        threshold: float = 0.7,
    ) -> list[dict[str, Any]]:
        """
        Identify assignments with high conflict risk.

        Args:
            assignments: List of assignment dictionaries
            threshold: Risk threshold (default 0.7)

        Returns:
            List of high-risk assignments with details
        """
        high_risk = []

        for assignment in assignments:
            prob = self.predict_conflict_probability(
                person_data=assignment.get("person", {}),
                proposed_assignment=assignment.get("proposed", {}),
                existing_assignments=assignment.get("existing", []),
                context_data=assignment.get("context"),
            )

            if prob >= threshold:
                high_risk.append(
                    {
                        "assignment": assignment,
                        "conflict_probability": prob,
                        "risk_level": self._risk_level(prob),
                    }
                )

                # Sort by probability (highest risk first)
        high_risk.sort(key=lambda x: x["conflict_probability"], reverse=True)

        return high_risk

    def explain_conflict_risk(
        self,
        person_data: dict[str, Any],
        proposed_assignment: dict[str, Any],
        existing_assignments: list[dict[str, Any]],
        context_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Explain why a conflict is predicted.

        Args:
            person_data: Person attributes
            proposed_assignment: New assignment being considered
            existing_assignments: Person's current assignments
            context_data: Additional context

        Returns:
            Explanation dictionary with probability and risk factors
        """
        prob = self.predict_conflict_probability(
            person_data, proposed_assignment, existing_assignments, context_data
        )

        # Extract features
        X = self.extract_features(
            person_data, proposed_assignment, existing_assignments, context_data
        )

        # Get feature values
        feature_values = X.iloc[0].to_dict()

        # Get feature importances
        importances = dict(zip(self.feature_names, self.model.feature_importances_))

        # Identify risk factors (features with high values and high importance)
        risk_factors = []
        for feat, value in feature_values.items():
            importance = importances.get(feat, 0)
            if value > 0 and importance > 0.05:  # Significant features
                risk_factors.append(
                    {
                        "factor": feat,
                        "value": float(value),
                        "importance": float(importance),
                    }
                )

                # Sort by importance
        risk_factors.sort(key=lambda x: x["importance"], reverse=True)

        return {
            "conflict_probability": float(prob),
            "risk_level": self._risk_level(prob),
            "top_risk_factors": risk_factors[:5],
            "all_feature_values": feature_values,
        }

    def _risk_level(self, probability: float) -> str:
        """
        Convert probability to risk level.

        Args:
            probability: Conflict probability (0-1)

        Returns:
            Risk level string
        """
        if probability >= 0.8:
            return "CRITICAL"
        elif probability >= 0.6:
            return "HIGH"
        elif probability >= 0.4:
            return "MEDIUM"
        elif probability >= 0.2:
            return "LOW"
        else:
            return "MINIMAL"

    def save(self, path: Path) -> None:
        """Save model to disk."""
        path.mkdir(parents=True, exist_ok=True)

        joblib.dump(self.model, path / "model.pkl")
        joblib.dump(self.scaler, path / "scaler.pkl")
        joblib.dump(self.feature_names, path / "features.pkl")

        logger.info(f"Saved conflict predictor to {path}")

    def load(self, path: Path) -> None:
        """Load model from disk."""
        self.model = joblib.load(path / "model.pkl")
        self.scaler = joblib.load(path / "scaler.pkl")
        self.feature_names = joblib.load(path / "features.pkl")

        logger.info(f"Loaded conflict predictor from {path}")
