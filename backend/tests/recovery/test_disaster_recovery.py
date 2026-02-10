"""Tests for Disaster Recovery Service pure logic (no DB, no Redis).

Covers: enums, Pydantic models (RPO, RTO, SyncVerificationResult, RecoveryMetrics),
dataclasses (RecoveryStep, RecoveryPlan, FailoverEvent, RecoveryConfig),
DisasterRecoveryService (register/verify RPO/RTO, failover initiation/approval,
recovery plan CRUD, recovery plan execution, health monitoring,
documentation generation, event handling, status reporting).
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.recovery.disaster_recovery import (
    DisasterRecoveryService,
    FailoverEvent,
    FailoverReason,
    FailoverStatus,
    FailoverTrigger,
    RecoveryConfig,
    RecoveryMetrics,
    RecoveryPlan,
    RecoveryPlanStatus,
    RecoveryPointObjective,
    RecoveryStatus,
    RecoveryStep,
    RecoveryTimeObjective,
    SyncStatus,
    SyncVerificationResult,
)


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ===========================================================================
# Enum Tests
# ===========================================================================


class TestRecoveryStatusEnum:
    def test_values(self):
        assert RecoveryStatus.NORMAL.value == "normal"
        assert RecoveryStatus.DEGRADED.value == "degraded"
        assert RecoveryStatus.FAILOVER_IN_PROGRESS.value == "failover_in_progress"
        assert RecoveryStatus.RECOVERED.value == "recovered"
        assert RecoveryStatus.RECOVERY_FAILED.value == "recovery_failed"

    def test_count(self):
        assert len(RecoveryStatus) == 5

    def test_is_str_enum(self):
        assert isinstance(RecoveryStatus.NORMAL, str)


class TestRecoveryPlanStatusEnum:
    def test_values(self):
        assert RecoveryPlanStatus.DRAFT.value == "draft"
        assert RecoveryPlanStatus.APPROVED.value == "approved"
        assert RecoveryPlanStatus.IN_PROGRESS.value == "in_progress"
        assert RecoveryPlanStatus.COMPLETED.value == "completed"
        assert RecoveryPlanStatus.FAILED.value == "failed"
        assert RecoveryPlanStatus.CANCELLED.value == "cancelled"

    def test_count(self):
        assert len(RecoveryPlanStatus) == 6


class TestFailoverTriggerEnum:
    def test_count(self):
        assert len(FailoverTrigger) == 8

    def test_manual(self):
        assert FailoverTrigger.MANUAL.value == "manual"

    def test_health_check_failed(self):
        assert FailoverTrigger.HEALTH_CHECK_FAILED.value == "health_check_failed"


class TestFailoverStatusEnum:
    def test_count(self):
        assert len(FailoverStatus) == 9

    def test_lifecycle_values(self):
        assert FailoverStatus.NOT_STARTED.value == "not_started"
        assert FailoverStatus.COMPLETED.value == "completed"
        assert FailoverStatus.ROLLED_BACK.value == "rolled_back"


class TestSyncStatusEnum:
    def test_count(self):
        assert len(SyncStatus) == 5

    def test_values(self):
        expected = {"in_sync", "syncing", "lag", "out_of_sync", "failed"}
        assert {e.value for e in SyncStatus} == expected


class TestFailoverReasonEnum:
    def test_count(self):
        assert len(FailoverReason) == 4

    def test_values(self):
        assert FailoverReason.PRIMARY_FAILURE.value == "primary_failure"
        assert FailoverReason.TESTING.value == "testing"


# ===========================================================================
# Pydantic Model Tests
# ===========================================================================


class TestRecoveryPointObjective:
    def test_valid(self):
        rpo = RecoveryPointObjective(
            name="database",
            max_data_loss_minutes=5,
        )
        assert rpo.name == "database"
        assert rpo.description == ""
        assert rpo.current_lag_minutes == 0.0
        assert rpo.backup_frequency_minutes == 60
        assert rpo.last_backup_at is None
        assert rpo.is_compliant is True
        assert rpo.violation_count == 0

    def test_max_data_loss_minutes_negative(self):
        with pytest.raises(ValidationError):
            RecoveryPointObjective(name="db", max_data_loss_minutes=-1)

    def test_current_lag_negative(self):
        with pytest.raises(ValidationError):
            RecoveryPointObjective(
                name="db", max_data_loss_minutes=5, current_lag_minutes=-0.1
            )

    def test_backup_frequency_zero(self):
        with pytest.raises(ValidationError):
            RecoveryPointObjective(
                name="db", max_data_loss_minutes=5, backup_frequency_minutes=0
            )

    def test_violation_count_negative(self):
        with pytest.raises(ValidationError):
            RecoveryPointObjective(
                name="db", max_data_loss_minutes=5, violation_count=-1
            )

    def test_with_all_fields(self):
        now = datetime.utcnow()
        rpo = RecoveryPointObjective(
            name="redis",
            description="Redis cache",
            max_data_loss_minutes=1,
            current_lag_minutes=0.5,
            backup_frequency_minutes=30,
            last_backup_at=now,
            is_compliant=True,
            violation_count=3,
        )
        assert rpo.last_backup_at == now
        assert rpo.violation_count == 3


class TestRecoveryTimeObjective:
    def test_valid(self):
        rto = RecoveryTimeObjective(
            name="database",
            max_downtime_minutes=30,
        )
        assert rto.estimated_recovery_time_minutes == 0
        assert rto.actual_recovery_time_minutes is None
        assert rto.is_achievable is True
        assert rto.automated_failover_enabled is True
        assert rto.dependencies == []

    def test_max_downtime_negative(self):
        with pytest.raises(ValidationError):
            RecoveryTimeObjective(name="db", max_downtime_minutes=-1)

    def test_estimated_recovery_negative(self):
        with pytest.raises(ValidationError):
            RecoveryTimeObjective(
                name="db",
                max_downtime_minutes=30,
                estimated_recovery_time_minutes=-1,
            )

    def test_actual_recovery_negative(self):
        with pytest.raises(ValidationError):
            RecoveryTimeObjective(
                name="db",
                max_downtime_minutes=30,
                actual_recovery_time_minutes=-0.1,
            )

    def test_with_dependencies(self):
        rto = RecoveryTimeObjective(
            name="application",
            max_downtime_minutes=10,
            dependencies=["database", "redis"],
        )
        assert rto.dependencies == ["database", "redis"]


class TestSyncVerificationResult:
    def test_valid(self):
        result = SyncVerificationResult(
            resource="database",
            status=SyncStatus.IN_SYNC,
        )
        assert result.lag_seconds == 0.0
        assert result.records_behind == 0
        assert result.is_healthy is True
        assert result.error is None
        assert result.details == {}

    def test_lag_negative(self):
        with pytest.raises(ValidationError):
            SyncVerificationResult(
                resource="db", status=SyncStatus.IN_SYNC, lag_seconds=-1.0
            )

    def test_records_behind_negative(self):
        with pytest.raises(ValidationError):
            SyncVerificationResult(
                resource="db", status=SyncStatus.IN_SYNC, records_behind=-1
            )

    def test_with_error(self):
        result = SyncVerificationResult(
            resource="redis",
            status=SyncStatus.FAILED,
            is_healthy=False,
            error="Connection refused",
        )
        assert result.error == "Connection refused"


class TestRecoveryMetrics:
    def test_defaults(self):
        m = RecoveryMetrics()
        assert isinstance(m.recovery_id, UUID)
        assert isinstance(m.started_at, datetime)
        assert m.completed_at is None
        assert m.duration_seconds == 0.0
        assert m.rto_achieved is False
        assert m.rpo_achieved is False
        assert m.health_check_passes == 0
        assert m.health_check_failures == 0
        assert m.rollback_count == 0
        assert m.issues_encountered == []

    def test_duration_negative(self):
        with pytest.raises(ValidationError):
            RecoveryMetrics(duration_seconds=-1.0)

    def test_health_check_passes_negative(self):
        with pytest.raises(ValidationError):
            RecoveryMetrics(health_check_passes=-1)


# ===========================================================================
# Dataclass Tests
# ===========================================================================


class TestRecoveryStep:
    def test_defaults(self):
        step = RecoveryStep()
        assert isinstance(step.id, UUID)
        assert step.name == ""
        assert step.order == 0
        assert step.is_automated is True
        assert step.estimated_duration_minutes == 5
        assert step.is_critical is True
        assert step.rollback_possible is True
        assert step.dependencies == []
        assert step.validation_required is True
        assert step.status == RecoveryPlanStatus.DRAFT
        assert step.started_at is None
        assert step.completed_at is None
        assert step.error is None

    def test_custom_values(self):
        step = RecoveryStep(
            name="Promote replica",
            description="Promote secondary to primary",
            order=3,
            is_automated=False,
            estimated_duration_minutes=10,
            is_critical=True,
        )
        assert step.name == "Promote replica"
        assert step.order == 3
        assert step.is_automated is False


class TestRecoveryPlan:
    def test_defaults(self):
        plan = RecoveryPlan()
        assert isinstance(plan.id, UUID)
        assert plan.name == ""
        assert plan.version == "1.0.0"
        assert plan.rto_minutes == 30
        assert plan.rpo_minutes == 5
        assert plan.trigger == FailoverTrigger.MANUAL
        assert plan.severity == "moderate"
        assert plan.steps == []
        assert plan.status == RecoveryPlanStatus.DRAFT
        assert plan.execution_count == 0
        assert plan.last_execution_successful is False
        assert plan.prerequisites == []
        assert plan.success_criteria == []

    def test_custom_values(self):
        plan = RecoveryPlan(
            name="Database Recovery",
            description="Full database failover plan",
            rto_minutes=10,
            rpo_minutes=1,
            trigger=FailoverTrigger.DATABASE_FAILURE,
            severity="critical",
        )
        assert plan.name == "Database Recovery"
        assert plan.rto_minutes == 10
        assert plan.trigger == FailoverTrigger.DATABASE_FAILURE


class TestFailoverEvent:
    def test_defaults(self):
        event = FailoverEvent()
        assert isinstance(event.id, UUID)
        assert isinstance(event.timestamp, datetime)
        assert event.trigger == FailoverTrigger.MANUAL
        assert event.reason == FailoverReason.TESTING
        assert event.status == FailoverStatus.NOT_STARTED
        assert event.initiated_by == "system"
        assert event.source_region == "primary"
        assert event.target_region == "secondary"
        assert event.services_affected == []
        assert event.successful is False
        assert event.data_loss_detected is False
        assert event.rto_target_minutes == 30
        assert event.rolled_back is False

    def test_custom_values(self):
        event = FailoverEvent(
            trigger=FailoverTrigger.DATA_CENTER_OUTAGE,
            reason=FailoverReason.DISASTER,
            source_region="us-east",
            target_region="us-west",
            services_affected=["database", "redis"],
        )
        assert event.trigger == FailoverTrigger.DATA_CENTER_OUTAGE
        assert event.services_affected == ["database", "redis"]


class TestRecoveryConfig:
    def test_defaults(self):
        config = RecoveryConfig()
        assert config.default_rpo_minutes == 5
        assert config.default_rto_minutes == 30
        assert config.critical_rpo_minutes == 1
        assert config.critical_rto_minutes == 10
        assert config.health_check_interval_seconds == 60
        assert config.max_consecutive_failures == 3
        assert config.auto_failover_enabled is False
        assert config.rollback_on_failure is True
        assert config.max_acceptable_lag_seconds == 300
        assert config.allow_production_testing is False
        assert config.test_mode_enabled is False
        assert config.notification_recipients == []

    def test_custom_values(self):
        config = RecoveryConfig(
            default_rpo_minutes=1,
            auto_failover_enabled=True,
            allow_production_testing=True,
        )
        assert config.default_rpo_minutes == 1
        assert config.auto_failover_enabled is True


# ===========================================================================
# Service Initialization Tests
# ===========================================================================


class TestServiceInit:
    def test_default_config(self):
        svc = DisasterRecoveryService()
        assert isinstance(svc.config, RecoveryConfig)
        assert svc._current_status == RecoveryStatus.NORMAL
        assert svc._failover_in_progress is None
        assert svc._active_recovery is None

    def test_custom_config(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        assert svc.config.auto_failover_enabled is True

    def test_default_objectives_initialized(self):
        svc = DisasterRecoveryService()
        # Should have default RPO and RTO objectives
        assert "database" in svc._rpo_objectives
        assert "redis" in svc._rpo_objectives
        assert "database" in svc._rto_objectives
        assert "redis" in svc._rto_objectives
        assert "application" in svc._rto_objectives

    def test_default_rpo_values(self):
        svc = DisasterRecoveryService()
        db_rpo = svc._rpo_objectives["database"]
        assert db_rpo.max_data_loss_minutes == 5
        assert db_rpo.backup_frequency_minutes == 60

    def test_default_rto_values(self):
        svc = DisasterRecoveryService()
        db_rto = svc._rto_objectives["database"]
        assert db_rto.max_downtime_minutes == 30
        assert db_rto.estimated_recovery_time_minutes == 15
        assert db_rto.automated_failover_enabled is True

    def test_application_rto_dependencies(self):
        svc = DisasterRecoveryService()
        app_rto = svc._rto_objectives["application"]
        assert "database" in app_rto.dependencies
        assert "redis" in app_rto.dependencies


# ===========================================================================
# RPO Management Tests
# ===========================================================================


class TestRegisterRPO:
    def test_register_custom_rpo(self):
        svc = DisasterRecoveryService()
        rpo = RecoveryPointObjective(
            name="audit_log",
            description="Audit trail",
            max_data_loss_minutes=0,
        )
        svc.register_rpo(rpo)
        assert "audit_log" in svc._rpo_objectives
        assert svc._rpo_objectives["audit_log"].max_data_loss_minutes == 0

    def test_register_overwrites(self):
        svc = DisasterRecoveryService()
        rpo = RecoveryPointObjective(
            name="database",
            max_data_loss_minutes=1,
        )
        svc.register_rpo(rpo)
        assert svc._rpo_objectives["database"].max_data_loss_minutes == 1


class TestVerifyRPO:
    def test_verify_all(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_rpo())
        assert "database" in results
        assert "redis" in results

    def test_verify_specific(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_rpo("database"))
        assert "database" in results
        assert "redis" not in results

    def test_rpo_compliant_when_lag_within_limit(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_rpo("database"))
        # Simulated lag is 0.5 min, max allowed is 5 min
        db_rpo = results["database"]
        assert db_rpo.is_compliant is True
        assert db_rpo.current_lag_minutes == 0.5


# ===========================================================================
# RTO Management Tests
# ===========================================================================


class TestRegisterRTO:
    def test_register_custom_rto(self):
        svc = DisasterRecoveryService()
        rto = RecoveryTimeObjective(
            name="scheduler",
            max_downtime_minutes=15,
            estimated_recovery_time_minutes=10,
        )
        svc.register_rto(rto)
        assert "scheduler" in svc._rto_objectives

    def test_register_overwrites(self):
        svc = DisasterRecoveryService()
        rto = RecoveryTimeObjective(
            name="database",
            max_downtime_minutes=10,
            estimated_recovery_time_minutes=5,
        )
        svc.register_rto(rto)
        assert svc._rto_objectives["database"].max_downtime_minutes == 10


class TestVerifyRTO:
    def test_verify_all(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_rto())
        assert "database" in results
        assert "redis" in results
        assert "application" in results

    def test_verify_specific(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_rto("database"))
        assert "database" in results
        assert len(results) == 1

    def test_rto_achievable_when_estimated_within_max(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_rto("database"))
        db_rto = results["database"]
        # estimated=15, max=30 => achievable
        assert db_rto.is_achievable is True

    def test_rto_not_achievable_when_estimated_exceeds_max(self):
        svc = DisasterRecoveryService()
        svc.register_rto(
            RecoveryTimeObjective(
                name="slow_service",
                max_downtime_minutes=5,
                estimated_recovery_time_minutes=20,
            )
        )
        results = _run(svc.verify_rto("slow_service"))
        assert results["slow_service"].is_achievable is False

    def test_rto_dependency_failure_cascades(self):
        svc = DisasterRecoveryService()
        # Make database RTO unachievable
        svc.register_rto(
            RecoveryTimeObjective(
                name="database",
                max_downtime_minutes=5,
                estimated_recovery_time_minutes=20,
            )
        )
        # Application depends on database
        results = _run(svc.verify_rto())
        assert results["application"].is_achievable is False


# ===========================================================================
# Failover Management Tests
# ===========================================================================


class TestInitiateFailover:
    def test_basic_failover(self):
        svc = DisasterRecoveryService()
        event = _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
            )
        )
        assert isinstance(event, FailoverEvent)
        assert event.trigger == FailoverTrigger.MANUAL
        assert event.reason == FailoverReason.TESTING
        assert event.status == FailoverStatus.INITIALIZING
        assert svc._current_status == RecoveryStatus.FAILOVER_IN_PROGRESS

    def test_failover_custom_regions(self):
        svc = DisasterRecoveryService()
        event = _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.DATA_CENTER_OUTAGE,
                reason=FailoverReason.DISASTER,
                source_region="us-east",
                target_region="us-west",
                services=["database"],
                initiated_by="admin",
            )
        )
        assert event.source_region == "us-east"
        assert event.target_region == "us-west"
        assert event.services_affected == ["database"]
        assert event.initiated_by == "admin"

    def test_failover_already_in_progress(self):
        svc = DisasterRecoveryService()
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
            )
        )
        with pytest.raises(RuntimeError, match="already in progress"):
            _run(
                svc.initiate_failover(
                    trigger=FailoverTrigger.MANUAL,
                    reason=FailoverReason.TESTING,
                )
            )

    def test_auto_approve_without_permission(self):
        svc = DisasterRecoveryService()
        # auto_failover_enabled is False by default
        with pytest.raises(PermissionError, match="Auto-failover not enabled"):
            _run(
                svc.initiate_failover(
                    trigger=FailoverTrigger.AUTOMATED,
                    reason=FailoverReason.PRIMARY_FAILURE,
                    auto_approve=True,
                )
            )

    def test_auto_approve_with_permission(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        event = _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.AUTOMATED,
                reason=FailoverReason.PRIMARY_FAILURE,
                auto_approve=True,
            )
        )
        # Auto-approved failover should have executed
        assert event.status == FailoverStatus.COMPLETED
        assert event.successful is True
        assert svc._current_status == RecoveryStatus.RECOVERED

    def test_default_services(self):
        svc = DisasterRecoveryService()
        event = _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
            )
        )
        assert event.services_affected == ["database", "redis", "application"]


class TestApproveFailover:
    def test_approve_pending(self):
        svc = DisasterRecoveryService()
        event = _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
            )
        )
        result = _run(svc.approve_failover(event.id, "admin"))
        assert result is True
        assert svc._current_status == RecoveryStatus.RECOVERED

    def test_approve_no_pending(self):
        svc = DisasterRecoveryService()
        with pytest.raises(ValueError, match="No failover pending"):
            _run(svc.approve_failover(uuid4(), "admin"))

    def test_approve_wrong_event_id(self):
        svc = DisasterRecoveryService()
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
            )
        )
        with pytest.raises(ValueError, match="does not match"):
            _run(svc.approve_failover(uuid4(), "admin"))


class TestExecuteFailover:
    def test_successful_failover_records_history(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        event = _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        assert len(svc._failover_history) == 1
        assert svc._failover_history[0].id == event.id

    def test_failover_timing_recorded(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        event = _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        assert event.started_at is not None
        assert event.completed_at is not None
        assert event.duration_seconds > 0
        assert event.actual_downtime_minutes > 0

    def test_failover_clears_in_progress(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        assert svc._failover_in_progress is None


# ===========================================================================
# Recovery Plan Management Tests
# ===========================================================================


class TestCreateRecoveryPlan:
    def test_basic_creation(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan(
            name="DB Recovery",
            description="Database failover procedure",
        )
        assert isinstance(plan, RecoveryPlan)
        assert plan.name == "DB Recovery"
        assert plan.status == RecoveryPlanStatus.DRAFT
        assert plan.id in svc._recovery_plans

    def test_custom_objectives(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan(
            name="Critical Recovery",
            description="Critical service recovery",
            trigger=FailoverTrigger.DATABASE_FAILURE,
            rto_minutes=10,
            rpo_minutes=1,
        )
        assert plan.rto_minutes == 10
        assert plan.rpo_minutes == 1
        assert plan.trigger == FailoverTrigger.DATABASE_FAILURE


class TestAddRecoveryStep:
    def test_add_step(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        step = svc.add_recovery_step(
            plan_id=plan.id,
            name="Verify replica",
            description="Check replica health",
            order=1,
        )
        assert isinstance(step, RecoveryStep)
        assert step.name == "Verify replica"
        assert step.order == 1
        assert len(plan.steps) == 1

    def test_steps_sorted_by_order(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        svc.add_recovery_step(plan.id, "Step 3", "Third", order=3)
        svc.add_recovery_step(plan.id, "Step 1", "First", order=1)
        svc.add_recovery_step(plan.id, "Step 2", "Second", order=2)
        orders = [s.order for s in plan.steps]
        assert orders == [1, 2, 3]

    def test_plan_not_found(self):
        svc = DisasterRecoveryService()
        with pytest.raises(ValueError, match="not found"):
            svc.add_recovery_step(uuid4(), "Step", "Desc", order=1)

    def test_step_with_dependencies(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        step1 = svc.add_recovery_step(plan.id, "Step 1", "First", order=1)
        step2 = svc.add_recovery_step(
            plan.id, "Step 2", "Second", order=2, dependencies=[step1.id]
        )
        assert step1.id in step2.dependencies

    def test_updates_last_updated_at(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        before = plan.last_updated_at
        svc.add_recovery_step(plan.id, "Step", "Desc", order=1)
        assert plan.last_updated_at >= before


class TestExecuteRecoveryPlan:
    def _create_approved_plan(self, svc):
        plan = svc.create_recovery_plan("Test", "Test plan")
        svc.add_recovery_step(plan.id, "Step 1", "First", order=1)
        svc.add_recovery_step(plan.id, "Step 2", "Second", order=2)
        plan.status = RecoveryPlanStatus.APPROVED
        return plan

    def test_successful_execution(self):
        svc = DisasterRecoveryService()
        plan = self._create_approved_plan(svc)
        metrics = _run(svc.execute_recovery_plan(plan.id))
        assert isinstance(metrics, RecoveryMetrics)
        assert metrics.completed_at is not None
        assert metrics.duration_seconds > 0
        assert plan.status == RecoveryPlanStatus.COMPLETED
        assert plan.last_execution_successful is True
        assert plan.execution_count == 1

    def test_plan_not_found(self):
        svc = DisasterRecoveryService()
        with pytest.raises(ValueError, match="not found"):
            _run(svc.execute_recovery_plan(uuid4()))

    def test_plan_not_approved(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        # Status is DRAFT, not APPROVED
        with pytest.raises(ValueError, match="must be approved"):
            _run(svc.execute_recovery_plan(plan.id))

    def test_recovery_already_in_progress(self):
        svc = DisasterRecoveryService()
        plan = self._create_approved_plan(svc)
        # Manually set active recovery
        svc._active_recovery = RecoveryMetrics()
        with pytest.raises(RuntimeError, match="already in progress"):
            _run(svc.execute_recovery_plan(plan.id))

    def test_clears_active_recovery_after_completion(self):
        svc = DisasterRecoveryService()
        plan = self._create_approved_plan(svc)
        _run(svc.execute_recovery_plan(plan.id))
        assert svc._active_recovery is None


# ===========================================================================
# Sync Verification Tests
# ===========================================================================


class TestVerifySync:
    def test_verify_default_resources(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_sync())
        assert "database" in results
        assert "redis" in results

    def test_verify_specific_resources(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_sync(["database"]))
        assert "database" in results
        assert "redis" not in results

    def test_sync_result_structure(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_sync(["database"]))
        db_sync = results["database"]
        assert isinstance(db_sync, SyncVerificationResult)
        assert db_sync.resource == "database"
        assert db_sync.status in [SyncStatus.IN_SYNC, SyncStatus.LAG]
        assert db_sync.is_healthy is True
        assert db_sync.lag_seconds >= 0

    def test_redis_sync_healthy(self):
        svc = DisasterRecoveryService()
        results = _run(svc.verify_sync(["redis"]))
        redis_sync = results["redis"]
        assert redis_sync.is_healthy is True


# ===========================================================================
# Test Recovery Plan Tests
# ===========================================================================


class TestTestRecoveryPlan:
    def test_plan_not_found(self):
        svc = DisasterRecoveryService()
        with pytest.raises(ValueError, match="not found"):
            _run(svc.test_recovery_plan(uuid4()))

    def test_production_testing_blocked(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        plan.status = RecoveryPlanStatus.APPROVED
        # allow_production_testing is False by default
        with pytest.raises(PermissionError, match="not allowed"):
            _run(svc.test_recovery_plan(plan.id, test_mode=False))

    def test_production_testing_allowed(self):
        config = RecoveryConfig(allow_production_testing=True)
        svc = DisasterRecoveryService(config=config)
        plan = svc.create_recovery_plan("Test", "Test plan")
        svc.add_recovery_step(plan.id, "Step 1", "First", order=1)
        plan.status = RecoveryPlanStatus.APPROVED
        metrics = _run(svc.test_recovery_plan(plan.id, test_mode=False))
        assert isinstance(metrics, RecoveryMetrics)

    def test_updates_last_tested_at(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        svc.add_recovery_step(plan.id, "Step 1", "First", order=1)
        plan.status = RecoveryPlanStatus.APPROVED
        assert plan.last_tested_at is None
        _run(svc.test_recovery_plan(plan.id))
        assert plan.last_tested_at is not None

    def test_restores_test_mode_setting(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Test plan")
        svc.add_recovery_step(plan.id, "Step 1", "First", order=1)
        plan.status = RecoveryPlanStatus.APPROVED
        original_setting = svc.config.test_mode_enabled
        _run(svc.test_recovery_plan(plan.id, test_mode=True))
        assert svc.config.test_mode_enabled == original_setting


# ===========================================================================
# Health Monitoring Tests
# ===========================================================================


class TestMonitorHealth:
    def test_returns_health_dict(self):
        svc = DisasterRecoveryService()
        health = _run(svc.monitor_health())
        assert "timestamp" in health
        assert "overall_status" in health
        assert "rpo_compliance" in health
        assert "rto_achievability" in health
        assert "failover_ready" in health
        assert "sync_status" in health
        assert "issues" in health

    def test_overall_status_is_normal(self):
        svc = DisasterRecoveryService()
        health = _run(svc.monitor_health())
        assert health["overall_status"] == "normal"

    def test_updates_last_health_check(self):
        svc = DisasterRecoveryService()
        assert svc._last_health_check is None
        _run(svc.monitor_health())
        assert svc._last_health_check is not None

    def test_failover_ready_when_healthy(self):
        svc = DisasterRecoveryService()
        health = _run(svc.monitor_health())
        assert health["failover_ready"] is True


# ===========================================================================
# Documentation Generation Tests
# ===========================================================================


class TestGenerateRecoveryDocumentation:
    def test_basic_documentation(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan(
            name="DB Failover",
            description="Database failover procedure",
            rto_minutes=30,
            rpo_minutes=5,
        )
        doc = svc.generate_recovery_documentation(plan.id)
        assert "DB Failover" in doc
        assert "Database failover procedure" in doc
        assert "30 minutes" in doc
        assert "5 minutes" in doc

    def test_documentation_includes_steps(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test Plan", "Description")
        svc.add_recovery_step(plan.id, "Verify Replica", "Check health", order=1)
        svc.add_recovery_step(plan.id, "Promote Replica", "Make primary", order=2)
        doc = svc.generate_recovery_documentation(plan.id)
        assert "Verify Replica" in doc
        assert "Promote Replica" in doc

    def test_documentation_includes_contacts(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Desc")
        plan.contact_list = [
            {"role": "DBA", "name": "John Doe", "contact": "555-0100"},
        ]
        doc = svc.generate_recovery_documentation(plan.id)
        assert "DBA" in doc
        assert "John Doe" in doc

    def test_plan_not_found(self):
        svc = DisasterRecoveryService()
        with pytest.raises(ValueError, match="not found"):
            svc.generate_recovery_documentation(uuid4())

    def test_documentation_includes_prerequisites(self):
        svc = DisasterRecoveryService()
        plan = svc.create_recovery_plan("Test", "Desc")
        plan.prerequisites = ["VPN access", "Admin credentials"]
        doc = svc.generate_recovery_documentation(plan.id)
        assert "VPN access" in doc
        assert "Admin credentials" in doc


# ===========================================================================
# Event Handling Tests
# ===========================================================================


class TestEventHandling:
    def test_register_handler(self):
        svc = DisasterRecoveryService()
        events_received = []
        svc.register_event_handler(
            "test_event", lambda data: events_received.append(data)
        )
        assert "test_event" in svc._event_handlers
        assert len(svc._event_handlers["test_event"]) == 1

    def test_register_multiple_handlers(self):
        svc = DisasterRecoveryService()
        svc.register_event_handler("evt", lambda d: None)
        svc.register_event_handler("evt", lambda d: None)
        assert len(svc._event_handlers["evt"]) == 2

    def test_emit_calls_handlers(self):
        svc = DisasterRecoveryService()
        events_received = []
        svc.register_event_handler("test", lambda data: events_received.append(data))
        _run(svc._emit_event("test", {"key": "value"}))
        assert len(events_received) == 1
        assert events_received[0]["key"] == "value"

    def test_emit_async_handler(self):
        svc = DisasterRecoveryService()
        events_received = []

        async def async_handler(data):
            events_received.append(data)

        svc.register_event_handler("async_test", async_handler)
        _run(svc._emit_event("async_test", {"async": True}))
        assert len(events_received) == 1

    def test_emit_handler_error_does_not_raise(self):
        svc = DisasterRecoveryService()

        def bad_handler(data):
            raise RuntimeError("handler error")

        svc.register_event_handler("bad", bad_handler)
        # Should not raise
        _run(svc._emit_event("bad", {}))

    def test_failover_emits_events(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        events = []
        svc.register_event_handler(
            "failover_initiated", lambda d: events.append("init")
        )
        svc.register_event_handler(
            "failover_completed", lambda d: events.append("complete")
        )
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        assert "init" in events
        assert "complete" in events


# ===========================================================================
# Status and Reporting Tests
# ===========================================================================


class TestGetStatus:
    def test_initial_status(self):
        svc = DisasterRecoveryService()
        status = svc.get_status()
        assert status["recovery_status"] == "normal"
        assert status["failover_in_progress"] is False
        assert status["active_recovery"] is False
        assert status["rpo_objectives_count"] == 2  # database + redis
        assert status["rto_objectives_count"] == 3  # database + redis + application
        assert status["recovery_plans_count"] == 0
        assert status["failover_history_count"] == 0
        assert status["last_health_check"] is None
        assert status["auto_failover_enabled"] is False
        assert status["test_mode"] is False

    def test_status_after_failover(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        status = svc.get_status()
        assert status["recovery_status"] == "recovered"
        assert status["failover_history_count"] == 1


class TestGetFailoverHistory:
    def test_empty_history(self):
        svc = DisasterRecoveryService()
        history = svc.get_failover_history()
        assert history == []

    def test_history_after_failover(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        history = svc.get_failover_history()
        assert len(history) == 1
        assert history[0]["trigger"] == "manual"
        assert history[0]["reason"] == "testing"
        assert history[0]["successful"] is True

    def test_history_limit(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        # Run 3 failovers
        for _ in range(3):
            _run(
                svc.initiate_failover(
                    trigger=FailoverTrigger.MANUAL,
                    reason=FailoverReason.TESTING,
                    auto_approve=True,
                )
            )
        history = svc.get_failover_history(limit=2)
        assert len(history) == 2

    def test_history_most_recent_first(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.SCHEDULED,
                reason=FailoverReason.MAINTENANCE,
                auto_approve=True,
            )
        )
        history = svc.get_failover_history()
        assert history[0]["trigger"] == "scheduled"
        assert history[1]["trigger"] == "manual"

    def test_history_dict_keys(self):
        config = RecoveryConfig(auto_failover_enabled=True)
        svc = DisasterRecoveryService(config=config)
        _run(
            svc.initiate_failover(
                trigger=FailoverTrigger.MANUAL,
                reason=FailoverReason.TESTING,
                auto_approve=True,
            )
        )
        item = svc.get_failover_history()[0]
        expected_keys = {
            "id",
            "timestamp",
            "trigger",
            "reason",
            "status",
            "successful",
            "duration_seconds",
            "rto_achieved",
            "data_loss_detected",
        }
        assert set(item.keys()) == expected_keys
