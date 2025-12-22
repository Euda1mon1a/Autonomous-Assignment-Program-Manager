"""
Chaos Engineering Toolkit for Residency Scheduler.

This module provides chaos engineering capabilities to test system resilience
through controlled failure injection. It integrates with the resilience framework
to ensure safe experimentation with automatic rollback on SLO violations.

Core Components:
- ChaosExperiment: Define and execute chaos experiments
- LatencyInjector: Inject artificial latency into operations
- ErrorInjector: Inject errors and exceptions
- ResourceStressor: Simulate CPU/memory stress
- NetworkPartitioner: Simulate network failures
- ServiceFailureSimulator: Simulate dependency failures

Safety Features:
- Blast radius control (limit affected scope)
- Automatic rollback on SLO breach
- Integration with resilience defense levels
- Experiment audit logging

Usage:
    from app.chaos import ChaosExperiment, LatencyInjector

    experiment = ChaosExperiment(
        name="api_latency_test",
        description="Test API resilience under high latency",
        blast_radius=0.1,  # Affect 10% of requests
        max_duration_minutes=15
    )

    with experiment:
        injector = LatencyInjector(min_ms=100, max_ms=500)
        injector.inject()
        # Run tests...
"""

from app.chaos.experiments import (
    BlastRadiusScope,
    ChaosExperiment,
    ChaosExperimentConfig,
    ChaosExperimentScheduler,
    ChaosExperimentStatus,
    CPUStressor,
    ErrorInjector,
    ExperimentResult,
    InjectorType,
    LatencyInjector,
    MemoryStressor,
    NetworkPartitioner,
    ResourceStressor,
    ServiceFailureSimulator,
    SLOMonitor,
)

__all__ = [
    # Core experiment types
    "ChaosExperiment",
    "ChaosExperimentConfig",
    "ChaosExperimentStatus",
    "ExperimentResult",
    # Injectors
    "LatencyInjector",
    "ErrorInjector",
    "ResourceStressor",
    "CPUStressor",
    "MemoryStressor",
    "NetworkPartitioner",
    "ServiceFailureSimulator",
    # Safety & Control
    "BlastRadiusScope",
    "SLOMonitor",
    "ChaosExperimentScheduler",
    # Enums
    "InjectorType",
]
