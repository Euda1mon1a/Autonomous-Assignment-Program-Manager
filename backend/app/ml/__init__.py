"""
Machine Learning package for schedule optimization.

This package provides ML-based tools for:
- Learning from historical scheduling patterns
- Predicting optimal assignments
- Scoring schedule quality
- Detecting potential conflicts
- Optimizing workload distribution
- Learning faculty preferences

The ML models use scikit-learn and can be trained on historical data
to improve scheduling decisions over time.
"""

from app.ml.inference.schedule_scorer import ScheduleScorer
from app.ml.models.conflict_predictor import ConflictPredictor
from app.ml.models.preference_predictor import PreferencePredictor
from app.ml.models.workload_optimizer import WorkloadOptimizer
from app.ml.training.data_pipeline import TrainingDataPipeline

__all__ = [
    "ScheduleScorer",
    "ConflictPredictor",
    "PreferencePredictor",
    "WorkloadOptimizer",
    "TrainingDataPipeline",
]
