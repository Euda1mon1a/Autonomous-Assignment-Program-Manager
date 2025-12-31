"""
Enhanced swap subsystem for medical residency scheduling.

Provides comprehensive swap management including:
- Swap request creation and execution
- Advanced matching algorithms (exact, fuzzy, graph-based)
- Multi-party chain swaps
- ACGME compliance validation
- Coverage and skill validation
- Notifications and analytics
"""

from .swap_engine import SwapEngine, SwapEngineResult, SwapExecutionPlan
from .compatibility_checker import CompatibilityChecker, CompatibilityResult
from .chain_swap import ChainSwapCoordinator, SwapChain, ChainNode

# Matching
from .matching import ExactMatcher, GraphMatcher, PreferenceScorer

# Validation
from .validation import (
    PreSwapValidator,
    ACGMEComplianceChecker,
    CoverageValidator,
    SkillValidator,
)

# Notifications
from .notifications import SwapNotifier, SwapEmailTemplates

# Analytics
from .analytics import SwapMetrics, SwapTrendAnalyzer


__all__ = [
    # Core
    "SwapEngine",
    "SwapEngineResult",
    "SwapExecutionPlan",
    "CompatibilityChecker",
    "CompatibilityResult",
    "ChainSwapCoordinator",
    "SwapChain",
    "ChainNode",
    # Matching
    "ExactMatcher",
    "GraphMatcher",
    "PreferenceScorer",
    # Validation
    "PreSwapValidator",
    "ACGMEComplianceChecker",
    "CoverageValidator",
    "SkillValidator",
    # Notifications
    "SwapNotifier",
    "SwapEmailTemplates",
    # Analytics
    "SwapMetrics",
    "SwapTrendAnalyzer",
]

__version__ = "2.0.0"
