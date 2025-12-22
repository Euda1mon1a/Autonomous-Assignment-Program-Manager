"""
Shadow Traffic System.

Provides shadow traffic routing capabilities for testing and validation:
- Request duplication to shadow services
- Response comparison and diff reporting
- Configurable sampling rates
- Shadow service health monitoring
- Performance comparison metrics
- Traffic filtering rules
"""

from app.shadow.traffic import (
    DiffReport,
    DiffSeverity,
    ResponseComparison,
    ShadowConfig,
    ShadowHealthMetrics,
    ShadowPerformanceMetrics,
    ShadowTrafficFilter,
    ShadowTrafficManager,
    ShadowTrafficStats,
)

__all__ = [
    "ShadowTrafficManager",
    "ShadowConfig",
    "ShadowTrafficFilter",
    "ResponseComparison",
    "DiffReport",
    "DiffSeverity",
    "ShadowHealthMetrics",
    "ShadowPerformanceMetrics",
    "ShadowTrafficStats",
]
