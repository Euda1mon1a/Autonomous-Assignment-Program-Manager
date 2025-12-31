"""
FRMS Prediction Validation Framework.

This module provides tools for validating FRMS predictions against
actual resident-reported fatigue and performance data.

Validation Approaches:
1. Prospective validation: Compare predictions vs. actual reports
2. Retrospective analysis: Analyze historical data for model calibration
3. PVT-style cognitive testing: Correlate with objective performance metrics
4. Error correlation: Link fatigue predictions to actual error reports

Key Metrics:
- Prediction accuracy (RMSE, MAE, correlation)
- Sensitivity/Specificity for threshold alerts
- Calibration curves (predicted vs. actual)
- Area Under ROC Curve for risk classification

Based on:
- SAFTE-FAST validation methodology (FAA CAMI 2009-2010)
- PVT correlation studies
- Medical error correlation research
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Any
from uuid import UUID
import math
import json

from app.frms.three_process_model import ThreeProcessModel, EffectivenessScore
from app.frms.performance_predictor import PerformancePredictor, ClinicalRiskLevel

logger = logging.getLogger(__name__)


@dataclass
class PredictionAccuracy:
    """
    Accuracy metrics for FRMS predictions.

    Contains statistical measures of prediction quality.
    """

    # Sample size
    n_predictions: int = 0
    n_actual_reports: int = 0

    # Error metrics
    rmse: float = 0.0  # Root Mean Squared Error
    mae: float = 0.0  # Mean Absolute Error
    correlation: float = 0.0  # Pearson correlation

    # Classification metrics
    true_positives: int = 0  # Predicted high-risk, actual high fatigue
    true_negatives: int = 0  # Predicted low-risk, actual low fatigue
    false_positives: int = 0  # Predicted high-risk, actual low fatigue
    false_negatives: int = 0  # Predicted low-risk, actual high fatigue

    # Derived metrics
    sensitivity: float = 0.0  # TP / (TP + FN)
    specificity: float = 0.0  # TN / (TN + FP)
    ppv: float = 0.0  # Positive Predictive Value
    npv: float = 0.0  # Negative Predictive Value
    accuracy: float = 0.0  # (TP + TN) / total
    auc_roc: float = 0.0  # Area Under ROC Curve

    # Calibration
    calibration_slope: float = 1.0  # Ideal = 1.0
    calibration_intercept: float = 0.0  # Ideal = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "sample_size": {
                "predictions": self.n_predictions,
                "actual_reports": self.n_actual_reports,
            },
            "error_metrics": {
                "rmse": round(self.rmse, 4),
                "mae": round(self.mae, 4),
                "correlation": round(self.correlation, 4),
            },
            "classification": {
                "true_positives": self.true_positives,
                "true_negatives": self.true_negatives,
                "false_positives": self.false_positives,
                "false_negatives": self.false_negatives,
            },
            "performance": {
                "sensitivity": round(self.sensitivity, 4),
                "specificity": round(self.specificity, 4),
                "ppv": round(self.ppv, 4),
                "npv": round(self.npv, 4),
                "accuracy": round(self.accuracy, 4),
                "auc_roc": round(self.auc_roc, 4),
            },
            "calibration": {
                "slope": round(self.calibration_slope, 4),
                "intercept": round(self.calibration_intercept, 4),
            },
        }


@dataclass
class ValidationDataPoint:
    """
    A single validation data point pairing prediction with actual report.

    Represents a matched pair of FRMS prediction and resident-reported
    fatigue for validation analysis.
    """

    person_id: UUID
    timestamp: datetime
    predicted_effectiveness: float
    predicted_risk_level: str
    actual_fatigue_score: float | None = None  # 1-10 scale self-report
    actual_risk_reported: bool = False  # Binary: did they report fatigue?
    pvt_score: float | None = None  # Optional objective test score
    error_occurred: bool = False  # Did a clinical error occur?
    notes: str = ""

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "person_id": str(self.person_id),
            "timestamp": self.timestamp.isoformat(),
            "predicted": {
                "effectiveness": round(self.predicted_effectiveness, 2),
                "risk_level": self.predicted_risk_level,
            },
            "actual": {
                "fatigue_score": self.actual_fatigue_score,
                "risk_reported": self.actual_risk_reported,
                "pvt_score": self.pvt_score,
                "error_occurred": self.error_occurred,
            },
            "notes": self.notes,
        }


class ValidationStudy:
    """
    Framework for validating FRMS predictions.

    Collects prediction-actual pairs and calculates validation metrics.

    Usage:
        study = ValidationStudy(study_name="Q1 2025 Validation")

        # Add data points as they're collected
        study.add_data_point(
            person_id=resident_id,
            timestamp=datetime.now(),
            predicted_effectiveness=75.5,
            predicted_risk_level="caution",
            actual_fatigue_score=7.0,  # Self-reported 1-10
            actual_risk_reported=True,
        )

        # Calculate accuracy metrics
        accuracy = study.calculate_accuracy()

        # Export results
        study.export_results("validation_q1_2025.json")
    """

    def __init__(
        self,
        study_name: str,
        effectiveness_threshold: float = 77.0,  # FAA caution
        fatigue_threshold: float = 6.0,  # Self-report threshold (1-10 scale)
    ):
        """
        Initialize validation study.

        Args:
            study_name: Name/identifier for this validation study
            effectiveness_threshold: FRMS threshold for "at-risk" classification
            fatigue_threshold: Self-report threshold for "fatigued" classification
        """
        self.study_name = study_name
        self.effectiveness_threshold = effectiveness_threshold
        self.fatigue_threshold = fatigue_threshold

        self.data_points: list[ValidationDataPoint] = []
        self.start_time = datetime.now()
        self.model = ThreeProcessModel()

        logger.info(f"Initialized validation study: {study_name}")

    def add_data_point(
        self,
        person_id: UUID,
        timestamp: datetime,
        predicted_effectiveness: float,
        predicted_risk_level: str,
        actual_fatigue_score: float | None = None,
        actual_risk_reported: bool = False,
        pvt_score: float | None = None,
        error_occurred: bool = False,
        notes: str = "",
    ) -> ValidationDataPoint:
        """
        Add a validation data point.

        Args:
            person_id: Resident UUID
            timestamp: When prediction/report occurred
            predicted_effectiveness: FRMS predicted effectiveness (0-100)
            predicted_risk_level: FRMS risk category
            actual_fatigue_score: Self-reported fatigue (1-10 scale)
            actual_risk_reported: Did resident report feeling fatigued?
            pvt_score: Optional PVT or cognitive test score
            error_occurred: Did a clinical error occur in this period?
            notes: Additional notes

        Returns:
            Created ValidationDataPoint
        """
        data_point = ValidationDataPoint(
            person_id=person_id,
            timestamp=timestamp,
            predicted_effectiveness=predicted_effectiveness,
            predicted_risk_level=predicted_risk_level,
            actual_fatigue_score=actual_fatigue_score,
            actual_risk_reported=actual_risk_reported,
            pvt_score=pvt_score,
            error_occurred=error_occurred,
            notes=notes,
        )

        self.data_points.append(data_point)

        logger.debug(
            f"Added validation point: pred={predicted_effectiveness:.1f}%, "
            f"actual={actual_fatigue_score}"
        )

        return data_point

    def calculate_accuracy(self) -> PredictionAccuracy:
        """
        Calculate comprehensive accuracy metrics.

        Returns:
            PredictionAccuracy with all metrics
        """
        if not self.data_points:
            logger.warning("No data points for accuracy calculation")
            return PredictionAccuracy()

        # Filter to points with actual reports
        with_actual = [
            dp for dp in self.data_points if dp.actual_fatigue_score is not None
        ]

        if not with_actual:
            logger.warning("No data points with actual fatigue scores")
            return PredictionAccuracy(n_predictions=len(self.data_points))

        accuracy = PredictionAccuracy(
            n_predictions=len(self.data_points),
            n_actual_reports=len(with_actual),
        )

        # Calculate error metrics
        accuracy.rmse, accuracy.mae = self._calculate_error_metrics(with_actual)
        accuracy.correlation = self._calculate_correlation(with_actual)

        # Calculate classification metrics
        self._calculate_classification_metrics(with_actual, accuracy)

        # Calculate calibration
        accuracy.calibration_slope, accuracy.calibration_intercept = (
            self._calculate_calibration(with_actual)
        )

        # Calculate AUC-ROC
        accuracy.auc_roc = self._calculate_auc(with_actual)

        logger.info(
            f"Validation metrics: RMSE={accuracy.rmse:.2f}, "
            f"correlation={accuracy.correlation:.3f}, "
            f"sensitivity={accuracy.sensitivity:.2%}"
        )

        return accuracy

    def _calculate_error_metrics(
        self,
        data_points: list[ValidationDataPoint],
    ) -> tuple[float, float]:
        """Calculate RMSE and MAE."""
        # Convert self-reported fatigue (1-10) to effectiveness scale (0-100)
        # 10 = highest fatigue -> 0% effectiveness
        # 1 = lowest fatigue -> 100% effectiveness

        squared_errors = []
        absolute_errors = []

        for dp in data_points:
            # Convert actual fatigue score to effectiveness
            # fatigue 1-10 -> effectiveness 100-0
            actual_effectiveness = 100 - (dp.actual_fatigue_score - 1) * (100 / 9)

            error = dp.predicted_effectiveness - actual_effectiveness
            squared_errors.append(error**2)
            absolute_errors.append(abs(error))

        rmse = math.sqrt(sum(squared_errors) / len(squared_errors))
        mae = sum(absolute_errors) / len(absolute_errors)

        return rmse, mae

    def _calculate_correlation(
        self,
        data_points: list[ValidationDataPoint],
    ) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(data_points) < 2:
            return 0.0

        # Extract values
        predicted = [dp.predicted_effectiveness for dp in data_points]
        actual = [100 - (dp.actual_fatigue_score - 1) * (100 / 9) for dp in data_points]

        # Calculate means
        mean_pred = sum(predicted) / len(predicted)
        mean_actual = sum(actual) / len(actual)

        # Calculate correlation
        numerator = sum(
            (p - mean_pred) * (a - mean_actual) for p, a in zip(predicted, actual)
        )

        sum_sq_pred = sum((p - mean_pred) ** 2 for p in predicted)
        sum_sq_actual = sum((a - mean_actual) ** 2 for a in actual)

        denominator = math.sqrt(sum_sq_pred * sum_sq_actual)

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _calculate_classification_metrics(
        self,
        data_points: list[ValidationDataPoint],
        accuracy: PredictionAccuracy,
    ) -> None:
        """Calculate TP, TN, FP, FN and derived metrics."""
        for dp in data_points:
            # FRMS prediction: at-risk if below threshold
            predicted_at_risk = (
                dp.predicted_effectiveness < self.effectiveness_threshold
            )

            # Actual: fatigued if self-report above threshold
            actual_fatigued = dp.actual_fatigue_score >= self.fatigue_threshold

            if predicted_at_risk and actual_fatigued:
                accuracy.true_positives += 1
            elif not predicted_at_risk and not actual_fatigued:
                accuracy.true_negatives += 1
            elif predicted_at_risk and not actual_fatigued:
                accuracy.false_positives += 1
            else:  # not predicted_at_risk and actual_fatigued
                accuracy.false_negatives += 1

        # Calculate derived metrics
        total = (
            accuracy.true_positives
            + accuracy.true_negatives
            + accuracy.false_positives
            + accuracy.false_negatives
        )

        if total > 0:
            accuracy.accuracy = (
                accuracy.true_positives + accuracy.true_negatives
            ) / total

        if accuracy.true_positives + accuracy.false_negatives > 0:
            accuracy.sensitivity = accuracy.true_positives / (
                accuracy.true_positives + accuracy.false_negatives
            )

        if accuracy.true_negatives + accuracy.false_positives > 0:
            accuracy.specificity = accuracy.true_negatives / (
                accuracy.true_negatives + accuracy.false_positives
            )

        if accuracy.true_positives + accuracy.false_positives > 0:
            accuracy.ppv = accuracy.true_positives / (
                accuracy.true_positives + accuracy.false_positives
            )

        if accuracy.true_negatives + accuracy.false_negatives > 0:
            accuracy.npv = accuracy.true_negatives / (
                accuracy.true_negatives + accuracy.false_negatives
            )

    def _calculate_calibration(
        self,
        data_points: list[ValidationDataPoint],
    ) -> tuple[float, float]:
        """
        Calculate calibration curve parameters.

        Uses linear regression: actual = slope * predicted + intercept
        Ideal calibration: slope = 1.0, intercept = 0.0
        """
        if len(data_points) < 2:
            return 1.0, 0.0

        predicted = [dp.predicted_effectiveness for dp in data_points]
        actual = [100 - (dp.actual_fatigue_score - 1) * (100 / 9) for dp in data_points]

        n = len(predicted)
        sum_x = sum(predicted)
        sum_y = sum(actual)
        sum_xy = sum(x * y for x, y in zip(predicted, actual))
        sum_xx = sum(x**2 for x in predicted)

        denominator = n * sum_xx - sum_x**2
        if denominator == 0:
            return 1.0, 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        return slope, intercept

    def _calculate_auc(
        self,
        data_points: list[ValidationDataPoint],
    ) -> float:
        """
        Calculate Area Under ROC Curve.

        Uses trapezoidal approximation.
        """
        if len(data_points) < 2:
            return 0.5

        # Sort by predicted effectiveness (descending = higher risk first)
        sorted_points = sorted(data_points, key=lambda dp: dp.predicted_effectiveness)

        # Calculate TPR and FPR at each threshold
        n_positive = sum(
            1 for dp in data_points if dp.actual_fatigue_score >= self.fatigue_threshold
        )
        n_negative = len(data_points) - n_positive

        if n_positive == 0 or n_negative == 0:
            return 0.5

        roc_points = [(0.0, 0.0)]  # (FPR, TPR)
        tp = 0
        fp = 0

        for dp in sorted_points:
            actual_fatigued = dp.actual_fatigue_score >= self.fatigue_threshold
            if actual_fatigued:
                tp += 1
            else:
                fp += 1

            tpr = tp / n_positive
            fpr = fp / n_negative
            roc_points.append((fpr, tpr))

        # Calculate AUC using trapezoidal rule
        auc = 0.0
        for i in range(1, len(roc_points)):
            x1, y1 = roc_points[i - 1]
            x2, y2 = roc_points[i]
            auc += (x2 - x1) * (y1 + y2) / 2

        return auc

    def analyze_by_subgroup(
        self,
        grouping_key: str = "pgy_level",
    ) -> dict[str, PredictionAccuracy]:
        """
        Analyze accuracy by subgroup.

        Args:
            grouping_key: How to group data points

        Returns:
            Dict of group -> PredictionAccuracy
        """
        groups: dict[str, list[ValidationDataPoint]] = {}

        for dp in self.data_points:
            # For now, just group by risk level as example
            group = dp.predicted_risk_level
            if group not in groups:
                groups[group] = []
            groups[group].append(dp)

        results = {}
        for group_name, group_points in groups.items():
            # Create temporary study for this group
            temp_study = ValidationStudy(
                f"{self.study_name}_{group_name}",
                self.effectiveness_threshold,
                self.fatigue_threshold,
            )
            temp_study.data_points = group_points
            results[group_name] = temp_study.calculate_accuracy()

        return results

    def generate_calibration_plot_data(self) -> dict:
        """
        Generate data for calibration plot visualization.

        Returns decile bins with predicted vs. actual averages.
        """
        if not self.data_points:
            return {}

        with_actual = [
            dp for dp in self.data_points if dp.actual_fatigue_score is not None
        ]

        if not with_actual:
            return {}

        # Sort by predicted effectiveness
        sorted_points = sorted(with_actual, key=lambda dp: dp.predicted_effectiveness)

        # Create decile bins
        n = len(sorted_points)
        bin_size = n // 10 or 1

        bins = []
        for i in range(0, n, bin_size):
            bin_points = sorted_points[i : i + bin_size]
            if bin_points:
                avg_predicted = sum(
                    dp.predicted_effectiveness for dp in bin_points
                ) / len(bin_points)
                avg_actual = sum(
                    100 - (dp.actual_fatigue_score - 1) * (100 / 9) for dp in bin_points
                ) / len(bin_points)

                bins.append(
                    {
                        "bin_index": len(bins),
                        "count": len(bin_points),
                        "avg_predicted": round(avg_predicted, 2),
                        "avg_actual": round(avg_actual, 2),
                    }
                )

        return {
            "bins": bins,
            "perfect_calibration_line": [
                {"x": 0, "y": 0},
                {"x": 100, "y": 100},
            ],
        }

    def export_results(self, filepath: str) -> None:
        """Export validation results to JSON file."""
        accuracy = self.calculate_accuracy()
        calibration_data = self.generate_calibration_plot_data()

        results = {
            "study_name": self.study_name,
            "analysis_time": datetime.now().isoformat(),
            "start_time": self.start_time.isoformat(),
            "configuration": {
                "effectiveness_threshold": self.effectiveness_threshold,
                "fatigue_threshold": self.fatigue_threshold,
            },
            "accuracy": accuracy.to_dict(),
            "calibration_plot": calibration_data,
            "data_points": [dp.to_dict() for dp in self.data_points],
        }

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Exported validation results to {filepath}")

    def get_summary(self) -> dict:
        """Get summary of validation study."""
        accuracy = self.calculate_accuracy()

        return {
            "study_name": self.study_name,
            "total_predictions": len(self.data_points),
            "with_actual_reports": accuracy.n_actual_reports,
            "accuracy_summary": {
                "correlation": round(accuracy.correlation, 3),
                "rmse": round(accuracy.rmse, 2),
                "sensitivity": f"{accuracy.sensitivity:.1%}",
                "specificity": f"{accuracy.specificity:.1%}",
                "auc_roc": round(accuracy.auc_roc, 3),
            },
            "calibration": {
                "well_calibrated": 0.8 <= accuracy.calibration_slope <= 1.2,
                "slope": round(accuracy.calibration_slope, 3),
            },
        }
