"""
FRMS (Fatigue Risk Management System) Predictive Analytics.

This module implements aviation-grade fatigue risk management for medical
residency scheduling, based on validated bio-mathematical models.

Key Components:
- Three-Process Model of Alertness (circadian, homeostatic, sleep inertia)
- ML-based performance degradation prediction
- Fatigue-aware constraint generation for schedule optimization
- What-if scenario testing and impact analysis
- Real-time monitoring and alerting
- Holographic visualization data export

Based on:
- SAFTE-FAST model (validated by FAA CAMI 2009-2010)
- Two-Process Model (Borbély 1982)
- ICAO FRMS guidelines (Doc 9966)
- FAA Part 117 flight duty regulations

Integration Points:
- Session 1-2: QUBO solvers (fatigue as soft constraint)
- Session 3: Core FRMS implementation
- Holographic Hub: Time-series data export
"""

from app.frms.three_process_model import (
    ThreeProcessModel,
    AlertnessState,
    CircadianPhase,
    SleepInertiaState,
    EffectivenessScore,
)
from app.frms.performance_predictor import (
    PerformancePredictor,
    PerformanceDegradation,
    ClinicalRiskLevel,
)
from app.frms.fatigue_constraint import (
    FatigueConstraint,
    FatigueSoftConstraint,
    CircadianConstraint,
)
from app.frms.scenario_analyzer import (
    ScenarioAnalyzer,
    FatigueImpactReport,
    WhatIfScenario,
)
from app.frms.monitoring import (
    FatigueMonitor,
    FatigueAlert,
    AlertSeverity,
)
from app.frms.holographic_export import (
    HolographicExporter,
    FatigueTimeSeries,
    TemporalDynamicsData,
)
from app.frms.validation import (
    ValidationStudy,
    PredictionAccuracy,
)

__all__ = [
    # Three-Process Model
    "ThreeProcessModel",
    "AlertnessState",
    "CircadianPhase",
    "SleepInertiaState",
    "EffectivenessScore",
    # Performance Prediction
    "PerformancePredictor",
    "PerformanceDegradation",
    "ClinicalRiskLevel",
    # Constraints
    "FatigueConstraint",
    "FatigueSoftConstraint",
    "CircadianConstraint",
    # Scenario Analysis
    "ScenarioAnalyzer",
    "FatigueImpactReport",
    "WhatIfScenario",
    # Monitoring
    "FatigueMonitor",
    "FatigueAlert",
    "AlertSeverity",
    # Holographic Export
    "HolographicExporter",
    "FatigueTimeSeries",
    "TemporalDynamicsData",
    # Validation
    "ValidationStudy",
    "PredictionAccuracy",
]
