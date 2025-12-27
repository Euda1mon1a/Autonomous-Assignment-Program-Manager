"""
Fatigue Risk Management System (FRMS) for Medical Residency Scheduling.

Adapted from aviation safety standards (FAA AC 120-103A, ICAO FRMS) to
predict and prevent fatigue-related safety risks in medical training.

Components:
- samn_perelli: 7-level subjective fatigue scale from aviation
- sleep_debt: Accumulated sleep deficit with circadian rhythm modeling
- alertness_engine: Predictive alertness based on prior shift patterns
- hazard_thresholds: Safety thresholds triggering schedule modifications
- temporal_constraints: Chronobiology-based scheduling constraints

Key Aviation FRMS Principles Applied:
1. Data-driven continuous monitoring
2. Scientific basis (circadian biology, sleep homeostasis)
3. Predictive modeling before fatigue occurs
4. Performance-based approach (not just prescriptive rules)
5. Integration with Safety Management System (SMS)

References:
- FAA Advisory Circular AC 120-103A
- ICAO Annex 6 FRMS Standards
- Samn & Perelli (1982) USAF fatigue scale
- Two-process sleep model (Borbély, 1982)
"""

from app.resilience.frms.samn_perelli import (
    SamnPerelliLevel,
    SamnPerelliAssessment,
    assess_fatigue_level,
    is_safe_for_duty,
)
from app.resilience.frms.sleep_debt import (
    SleepDebtModel,
    CircadianPhase,
    SleepOpportunity,
)
from app.resilience.frms.alertness_engine import (
    AlertnessPredictor,
    AlertnessPrediction,
    ShiftPattern,
)
from app.resilience.frms.hazard_thresholds import (
    HazardLevel,
    FatigueHazard,
    HazardThresholdEngine,
)
from app.resilience.frms.frms_service import (
    FRMSService,
)

__all__ = [
    # Samn-Perelli scale
    "SamnPerelliLevel",
    "SamnPerelliAssessment",
    "assess_fatigue_level",
    "is_safe_for_duty",
    # Sleep debt model
    "SleepDebtModel",
    "CircadianPhase",
    "SleepOpportunity",
    # Alertness prediction
    "AlertnessPredictor",
    "AlertnessPrediction",
    "ShiftPattern",
    # Hazard thresholds
    "HazardLevel",
    "FatigueHazard",
    "HazardThresholdEngine",
    # Main service
    "FRMSService",
]
