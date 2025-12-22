"""
Experiments module for A/B testing infrastructure.

This module provides comprehensive A/B testing capabilities including:
- Experiment definition and variant management
- Consistent user bucketing and assignment
- Targeting rules and audience segmentation
- Metric collection and analysis
- Statistical significance testing
- Feature flag integration

Usage:
    from app.experiments import ExperimentService, Experiment, Variant

    # Create an experiment
    experiment = Experiment(
        key="new_scheduler_ui",
        name="New Scheduler UI Test",
        description="Testing new UI design for schedule generation",
        variants=[
            Variant(key="control", name="Current UI", allocation=50),
            Variant(key="treatment", name="New UI", allocation=50),
        ],
    )

    # Assign user to variant
    service = ExperimentService()
    variant = await service.assign_user(experiment.key, user_id)

    # Track metrics
    await service.track_metric(
        experiment_key="new_scheduler_ui",
        user_id=user_id,
        metric_name="schedule_generated",
        value=1.0,
    )

    # Get experiment results
    results = await service.get_results(experiment.key)
"""

from app.experiments.ab_testing import (
    Experiment,
    ExperimentConfig,
    ExperimentLifecycle,
    ExperimentResults,
    ExperimentService,
    ExperimentStatus,
    ExperimentTargeting,
    MetricData,
    TargetingRule,
    Variant,
    VariantAssignment,
    VariantMetrics,
    calculate_statistical_significance,
)

__all__ = [
    "Experiment",
    "ExperimentConfig",
    "ExperimentLifecycle",
    "ExperimentResults",
    "ExperimentService",
    "ExperimentStatus",
    "ExperimentTargeting",
    "MetricData",
    "TargetingRule",
    "Variant",
    "VariantAssignment",
    "VariantMetrics",
    "calculate_statistical_significance",
]
