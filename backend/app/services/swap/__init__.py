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

***REMOVED*** Matching
from .matching import ExactMatcher, GraphMatcher, PreferenceScorer

***REMOVED*** Validation
from .validation import (
    PreSwapValidator,
    ACGMEComplianceChecker,
    CoverageValidator,
    SkillValidator,
)

***REMOVED*** Notifications
from .notifications import SwapNotifier, SwapEmailTemplates

***REMOVED*** Analytics
from .analytics import SwapMetrics, SwapTrendAnalyzer


__all__ = [
    ***REMOVED*** Core
    "SwapEngine",
    "SwapEngineResult",
    "SwapExecutionPlan",
    "CompatibilityChecker",
    "CompatibilityResult",
    "ChainSwapCoordinator",
    "SwapChain",
    "ChainNode",
    ***REMOVED*** Matching
    "ExactMatcher",
    "GraphMatcher",
    "PreferenceScorer",
    ***REMOVED*** Validation
    "PreSwapValidator",
    "ACGMEComplianceChecker",
    "CoverageValidator",
    "SkillValidator",
    ***REMOVED*** Notifications
    "SwapNotifier",
    "SwapEmailTemplates",
    ***REMOVED*** Analytics
    "SwapMetrics",
    "SwapTrendAnalyzer",
]

__version__ = "2.0.0"
