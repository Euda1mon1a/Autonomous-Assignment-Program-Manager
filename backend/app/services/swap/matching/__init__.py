"""
Swap matching subsystem.

Provides various matching algorithms for finding compatible
swap partners and optimizing swap assignments.
"""

from .exact_matcher import ExactMatcher
from .graph_matcher import GraphMatcher
from .preference_scorer import PreferenceScorer

__all__ = [
    "ExactMatcher",
    "GraphMatcher",
    "PreferenceScorer",
]
