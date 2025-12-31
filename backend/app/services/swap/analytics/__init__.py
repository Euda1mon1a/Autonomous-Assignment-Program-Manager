"""
Swap analytics subsystem.

Provides analytics, metrics, and trend analysis for swap operations.
"""

from .swap_metrics import SwapMetrics
from .trend_analyzer import SwapTrendAnalyzer

__all__ = [
    "SwapMetrics",
    "SwapTrendAnalyzer",
]
