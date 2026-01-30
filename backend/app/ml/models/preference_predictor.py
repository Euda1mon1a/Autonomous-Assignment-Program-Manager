"""
Preference Predictor - ML model for learning faculty scheduling preferences.

Uses historical assignment data and faculty feedback to predict:
- Which assignments faculty prefer
- Optimal assignment scores
- Preference patterns over time
"""

import logging
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


class PreferencePredictor:
    """
    Predicts faculty preferences for schedule assignments using Random Forest.

    Features:
    - Learns from historical assignments and swaps
    - Predicts preference scores (0-1) for person-rotation-block combinations
    - Handles temporal patterns (day of week, time of year)
    - Accounts for faculty role and specialty
    - Fairness-aware predictions
    """

    def __init__(
        self,
        model_path: Path | None = None,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
    ) -> None:
        """
        Initialize preference predictor.

        Args:
            model_path: Path to load pre-trained model from
            n_estimators: Number of trees in random forest
            max_depth: Maximum depth of trees
            random_state: Random seed for reproducibility
        """
        self.model_path = model_path
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state

        # Models and preprocessors
        self.model: RandomForestRegressor | None = None
        self.scaler: StandardScaler | None = None
        self.feature_names: list[str] = []

        # Load pre-trained model if path provided
        if model_path and model_path.exists():
            self.load(model_path)
        else:
            self._initialize_model()

    def _initialize_model(self) -> None:
        """Initialize a new Random Forest model."""
        self.model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.random_state,
            n_jobs=-1,  # Use all CPU cores
            min_samples_split=10,
            min_samples_leaf=4,
        )
        self.scaler = StandardScaler()
        logger.info("Initialized new preference prediction model")

    def extract_features(
        self,
        person_data: dict[str, Any],
        rotation_data: dict[str, Any],
        block_data: dict[str, Any],
        historical_stats: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Extract features from assignment components.

        Args:
            person_data: Person attributes (type, pgy_level, faculty_role, etc.)
            rotation_data: Rotation template attributes (name, type, workload)
            block_data: Block attributes (date, time_of_day, is_weekend, etc.)
            historical_stats: Historical statistics for this person

        Returns:
            DataFrame with feature columns
        """
        features = {}

        # Person features
        features["is_faculty"] = 1 if person_data.get("type") == "faculty" else 0
        features["is_resident"] = 1 if person_data.get("type") == "resident" else 0
        features["pgy_level"] = person_data.get("pgy_level", 0) or 0

        # Faculty role encoding (one-hot)
        faculty_role = person_data.get("faculty_role", "")
        for role in ["pd", "apd", "oic", "dept_chief", "sports_med", "core"]:
            features[f"role_{role}"] = 1 if faculty_role == role else 0

            # Rotation features
        rotation_name = rotation_data.get("name", "")
        for rot_type in ["clinic", "inpatient", "procedures", "conference", "admin"]:
            features[f"rotation_{rot_type}"] = (
                1 if rot_type in rotation_name.lower() else 0
            )

            # Temporal features from block
        block_date = block_data.get("date")
        if isinstance(block_date, str):
            block_date = pd.to_datetime(block_date).date()

        if block_date:
            # Day of week (0=Monday, 6=Sunday)
            features["day_of_week"] = block_date.weekday()
            features["is_monday"] = 1 if block_date.weekday() == 0 else 0
            features["is_friday"] = 1 if block_date.weekday() == 4 else 0
            features["is_weekend"] = 1 if block_date.weekday() >= 5 else 0

            # Month of year (seasonality)
            features["month"] = block_date.month
            features["quarter"] = (block_date.month - 1) // 3 + 1

            # Week of year (academic calendar patterns)
            features["week_of_year"] = block_date.isocalendar()[1]
        else:
            features["day_of_week"] = 0
            features["is_monday"] = 0
            features["is_friday"] = 0
            features["is_weekend"] = 0
            features["month"] = 1
            features["quarter"] = 1
            features["week_of_year"] = 1

            # Time of day
        features["is_am"] = 1 if block_data.get("time_of_day") == "AM" else 0
        features["is_pm"] = 1 if block_data.get("time_of_day") == "PM" else 0

        # Holiday/special days
        features["is_holiday"] = 1 if block_data.get("is_holiday", False) else 0

        # Historical statistics (if available)
        if historical_stats:
            features["historical_preference_score"] = historical_stats.get(
                "avg_preference_score", 0.5
            )
            features["num_similar_assignments"] = historical_stats.get(
                "similar_count", 0
            )
            features["swap_rate"] = historical_stats.get("swap_rate", 0.0)
            features["workload_current"] = historical_stats.get("current_workload", 0.0)
        else:
            features["historical_preference_score"] = 0.5
            features["num_similar_assignments"] = 0
            features["swap_rate"] = 0.0
            features["workload_current"] = 0.0

            # Convert to DataFrame
        df = pd.DataFrame([features])
        return df

    def train(
        self,
        X: pd.DataFrame,
        y: np.ndarray,
        validation_split: float = 0.2,
    ) -> dict[str, float]:
        """
        Train the preference prediction model.

        Args:
            X: Feature matrix (DataFrame)
            y: Target preference scores (0-1 range)
            validation_split: Fraction of data for validation

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training preference predictor on {len(X)} samples")

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

        # Get feature importances
        feature_importance = dict(
            zip(self.feature_names, self.model.feature_importances_)
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
            "top_features": top_features,
        }

    def predict(
        self,
        person_data: dict[str, Any],
        rotation_data: dict[str, Any],
        block_data: dict[str, Any],
        historical_stats: dict[str, Any] | None = None,
    ) -> float:
        """
        Predict preference score for an assignment.

        Args:
            person_data: Person attributes
            rotation_data: Rotation attributes
            block_data: Block attributes
            historical_stats: Historical statistics

        Returns:
            Preference score (0-1, higher is better)
        """
        if self.model is None or self.scaler is None:
            logger.warning("Model not trained, returning default score")
            return 0.5

            # Extract features
        X = self.extract_features(
            person_data, rotation_data, block_data, historical_stats
        )

        # Ensure all expected features are present
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0

                # Reorder columns to match training
        X = X[self.feature_names]

        # Scale and predict
        X_scaled = self.scaler.transform(X)
        score = self.model.predict(X_scaled)[0]

        # Clip to valid range
        return float(np.clip(score, 0.0, 1.0))

    def predict_batch(
        self,
        assignments: list[dict[str, Any]],
    ) -> list[float]:
        """
        Predict preference scores for multiple assignments.

        Args:
            assignments: List of assignment dictionaries with person, rotation, block data

        Returns:
            List of preference scores
        """
        if not assignments:
            return []

        scores = []
        for assignment in assignments:
            score = self.predict(
                person_data=assignment.get("person", {}),
                rotation_data=assignment.get("rotation", {}),
                block_data=assignment.get("block", {}),
                historical_stats=assignment.get("historical_stats"),
            )
            scores.append(score)

        return scores

    def get_feature_importance(self) -> dict[str, float]:
        """
        Get feature importance scores.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.model is None or not self.feature_names:
            return {}

        return dict(zip(self.feature_names, self.model.feature_importances_))

    def save(self, path: Path) -> None:
        """
        Save model to disk.

        Args:
            path: Directory path to save model artifacts
        """
        path.mkdir(parents=True, exist_ok=True)

        # Save model
        joblib.dump(self.model, path / "model.pkl")
        joblib.dump(self.scaler, path / "scaler.pkl")
        joblib.dump(self.feature_names, path / "features.pkl")

        logger.info(f"Saved preference predictor to {path}")

    def load(self, path: Path) -> None:
        """
        Load model from disk.

        Args:
            path: Directory path containing model artifacts
        """
        self.model = joblib.load(path / "model.pkl")
        self.scaler = joblib.load(path / "scaler.pkl")
        self.feature_names = joblib.load(path / "features.pkl")

        logger.info(f"Loaded preference predictor from {path}")

    def explain_prediction(
        self,
        person_data: dict[str, Any],
        rotation_data: dict[str, Any],
        block_data: dict[str, Any],
        historical_stats: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Explain why a prediction was made.

        Args:
            person_data: Person attributes
            rotation_data: Rotation attributes
            block_data: Block attributes
            historical_stats: Historical statistics

        Returns:
            Explanation dictionary with score, features, and contributions
        """
        score = self.predict(person_data, rotation_data, block_data, historical_stats)

        # Extract features
        X = self.extract_features(
            person_data, rotation_data, block_data, historical_stats
        )

        # Get feature values
        feature_values = X.iloc[0].to_dict()

        # Get feature importances
        importances = self.get_feature_importance()

        # Calculate feature contributions (simplified)
        contributions = {
            feat: float(feature_values[feat] * importances.get(feat, 0))
            for feat in feature_values
        }

        # Sort by absolute contribution
        top_contributors = sorted(
            contributions.items(), key=lambda x: abs(x[1]), reverse=True
        )[:5]

        return {
            "score": float(score),
            "interpretation": self._interpret_score(score),
            "top_contributors": top_contributors,
            "feature_values": feature_values,
        }

    def _interpret_score(self, score: float) -> str:
        """
        Interpret preference score as human-readable text.

        Args:
            score: Preference score (0-1)

        Returns:
            Interpretation string
        """
        if score >= 0.8:
            return "Highly preferred assignment"
        elif score >= 0.6:
            return "Moderately preferred assignment"
        elif score >= 0.4:
            return "Neutral assignment"
        elif score >= 0.2:
            return "Less preferred assignment"
        else:
            return "Avoid this assignment if possible"
