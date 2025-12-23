"""
ML Models package for schedule optimization.

Contains trained models for:
- Preference prediction: Learning faculty scheduling preferences
- Workload optimization: Balancing workload distribution
- Conflict prediction: Detecting potential scheduling conflicts
"""

from app.ml.models.conflict_predictor import ConflictPredictor
from app.ml.models.preference_predictor import PreferencePredictor
from app.ml.models.workload_optimizer import WorkloadOptimizer

__all__ = [
    "ConflictPredictor",
    "PreferencePredictor",
    "WorkloadOptimizer",
]
