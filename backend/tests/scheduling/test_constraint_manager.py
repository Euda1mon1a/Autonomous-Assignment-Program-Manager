"""Tests for ConstraintManager (pure logic, no DB required)."""

from types import SimpleNamespace
from uuid import uuid4

from app.scheduling.constraints.base import (
    Constraint,
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
    SchedulingContext,
    SoftConstraint,
)
from app.scheduling.constraints.manager import ConstraintManager


# ==================== Helpers ====================


class _StubHard(HardConstraint):
    """Stub hard constraint for testing."""

    def __init__(self, name="StubHard", enabled=True, satisfied=True, violations=None):
        super().__init__(
            name=name,
            constraint_type=ConstraintType.AVAILABILITY,
            priority=ConstraintPriority.HIGH,
        )
        self.enabled = enabled
        self._satisfied = satisfied
        self._violations = violations or []

    def validate(self, assignments, context):
        return ConstraintResult(
            satisfied=self._satisfied,
            violations=self._violations,
        )

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass


class _StubSoft(SoftConstraint):
    """Stub soft constraint for testing."""

    def __init__(
        self, name="StubSoft", weight=1.0, enabled=True, penalty=0.0, violations=None
    ):
        super().__init__(
            name=name,
            constraint_type=ConstraintType.PREFERENCE,
            priority=ConstraintPriority.LOW,
            weight=weight,
        )
        self.enabled = enabled
        self._penalty = penalty
        self._violations = violations or []

    def validate(self, assignments, context):
        return ConstraintResult(
            satisfied=True,
            violations=self._violations,
            penalty=self._penalty,
        )

    def add_to_cpsat(self, model, variables, context):
        pass

    def add_to_pulp(self, model, variables, context):
        pass


def _context():
    return SchedulingContext(residents=[], faculty=[], blocks=[], templates=[])


def _violation(name="Test", severity="HIGH", message="violation"):
    return ConstraintViolation(
        constraint_name=name,
        constraint_type=ConstraintType.AVAILABILITY,
        severity=severity,
        message=message,
    )


# ==================== ConstraintManager Init ====================


class TestConstraintManagerInit:
    def test_empty_constraints(self):
        m = ConstraintManager()
        assert m.constraints == []
        assert m._hard_constraints == []
        assert m._soft_constraints == []


# ==================== Add / Remove ====================


class TestConstraintManagerAdd:
    def test_add_hard(self):
        m = ConstraintManager()
        h = _StubHard()
        result = m.add(h)
        assert h in m.constraints
        assert h in m._hard_constraints
        assert h not in m._soft_constraints
        assert result is m  # chaining

    def test_add_soft(self):
        m = ConstraintManager()
        s = _StubSoft()
        result = m.add(s)
        assert s in m.constraints
        assert s in m._soft_constraints
        assert s not in m._hard_constraints
        assert result is m

    def test_add_chaining(self):
        m = ConstraintManager()
        h = _StubHard(name="H1")
        s = _StubSoft(name="S1")
        m.add(h).add(s)
        assert len(m.constraints) == 2

    def test_remove_by_name(self):
        m = ConstraintManager()
        h = _StubHard(name="ToRemove")
        m.add(h)
        result = m.remove("ToRemove")
        assert h not in m.constraints
        assert h not in m._hard_constraints
        assert result is m

    def test_remove_nonexistent_noop(self):
        m = ConstraintManager()
        m.add(_StubHard(name="Keep"))
        m.remove("Nonexistent")
        assert len(m.constraints) == 1

    def test_remove_soft(self):
        m = ConstraintManager()
        s = _StubSoft(name="SoftRemove")
        m.add(s)
        m.remove("SoftRemove")
        assert s not in m.constraints
        assert s not in m._soft_constraints


# ==================== Enable / Disable ====================


class TestConstraintManagerEnableDisable:
    def test_disable(self):
        m = ConstraintManager()
        h = _StubHard(name="Disableable", enabled=True)
        m.add(h)
        result = m.disable("Disableable")
        assert h.enabled is False
        assert result is m

    def test_enable(self):
        m = ConstraintManager()
        h = _StubHard(name="Enableable", enabled=False)
        m.add(h)
        result = m.enable("Enableable")
        assert h.enabled is True
        assert result is m

    def test_disable_nonexistent_noop(self):
        m = ConstraintManager()
        m.disable("Nonexistent")  # no error

    def test_enable_nonexistent_noop(self):
        m = ConstraintManager()
        m.enable("Nonexistent")  # no error


# ==================== Get Methods ====================


class TestConstraintManagerGet:
    def test_get_enabled_all_enabled(self):
        m = ConstraintManager()
        m.add(_StubHard(name="H1", enabled=True))
        m.add(_StubSoft(name="S1", enabled=True))
        enabled = m.get_enabled()
        assert len(enabled) == 2

    def test_get_enabled_filters_disabled(self):
        m = ConstraintManager()
        m.add(_StubHard(name="H1", enabled=True))
        m.add(_StubHard(name="H2", enabled=False))
        enabled = m.get_enabled()
        assert len(enabled) == 1
        assert enabled[0].name == "H1"

    def test_get_hard_constraints(self):
        m = ConstraintManager()
        m.add(_StubHard(name="H1", enabled=True))
        m.add(_StubHard(name="H2", enabled=False))
        m.add(_StubSoft(name="S1", enabled=True))
        hard = m.get_hard_constraints()
        assert len(hard) == 1
        assert hard[0].name == "H1"

    def test_get_soft_constraints(self):
        m = ConstraintManager()
        m.add(_StubHard(name="H1", enabled=True))
        m.add(_StubSoft(name="S1", enabled=True))
        m.add(_StubSoft(name="S2", enabled=False))
        soft = m.get_soft_constraints()
        assert len(soft) == 1
        assert soft[0].name == "S1"


# ==================== validate_all ====================


class TestConstraintManagerValidate:
    def test_empty_constraints_satisfied(self):
        m = ConstraintManager()
        ctx = _context()
        result = m.validate_all([], ctx)
        assert result.satisfied is True
        assert result.violations == []
        assert result.penalty == 0.0

    def test_all_satisfied(self):
        m = ConstraintManager()
        m.add(_StubHard(name="H1", satisfied=True))
        m.add(_StubSoft(name="S1", penalty=0.0))
        ctx = _context()
        result = m.validate_all([], ctx)
        assert result.satisfied is True
        assert result.penalty == 0.0

    def test_hard_unsatisfied(self):
        m = ConstraintManager()
        v = _violation(name="H1", severity="CRITICAL", message="Fail")
        m.add(_StubHard(name="H1", satisfied=False, violations=[v]))
        ctx = _context()
        result = m.validate_all([], ctx)
        assert result.satisfied is False
        assert len(result.violations) == 1

    def test_soft_penalty_aggregated(self):
        m = ConstraintManager()
        m.add(_StubSoft(name="S1", penalty=2.5))
        m.add(_StubSoft(name="S2", penalty=3.5))
        ctx = _context()
        result = m.validate_all([], ctx)
        assert result.satisfied is True
        assert result.penalty == 6.0

    def test_violations_aggregated(self):
        m = ConstraintManager()
        v1 = _violation(name="H1", message="v1")
        v2 = _violation(name="S1", message="v2")
        m.add(_StubHard(name="H1", satisfied=True, violations=[v1]))
        m.add(_StubSoft(name="S1", violations=[v2]))
        ctx = _context()
        result = m.validate_all([], ctx)
        assert len(result.violations) == 2

    def test_disabled_constraints_skipped(self):
        m = ConstraintManager()
        v = _violation(name="H1", severity="CRITICAL", message="Fail")
        m.add(_StubHard(name="H1", enabled=False, satisfied=False, violations=[v]))
        ctx = _context()
        result = m.validate_all([], ctx)
        assert result.satisfied is True  # disabled constraint not checked
        assert len(result.violations) == 0

    def test_error_handling_continues(self):
        """Constraint that raises error -> others still run."""

        class _ErrorConstraint(HardConstraint):
            def __init__(self):
                super().__init__(
                    name="Error",
                    constraint_type=ConstraintType.AVAILABILITY,
                    priority=ConstraintPriority.HIGH,
                )

            def validate(self, assignments, context):
                raise RuntimeError("Boom")

            def add_to_cpsat(self, model, variables, context):
                pass

            def add_to_pulp(self, model, variables, context):
                pass

        m = ConstraintManager()
        m.add(_ErrorConstraint())
        m.add(_StubSoft(name="StillRuns", penalty=5.0))
        ctx = _context()
        result = m.validate_all([], ctx)
        # Error constraint logged, soft still runs
        assert result.penalty == 5.0


# ==================== Factory Methods ====================


class TestConstraintManagerFactories:
    def test_create_default(self):
        m = ConstraintManager.create_default()
        assert len(m.constraints) > 0
        names = {c.name for c in m.constraints}
        # ACGME must be present
        assert "Availability" in names
        assert "80HourRule" in names or "EightyHourRule" in names

    def test_create_default_hard_and_soft(self):
        m = ConstraintManager.create_default()
        assert len(m._hard_constraints) > 0
        assert len(m._soft_constraints) > 0

    def test_create_default_overnight_disabled(self):
        m = ConstraintManager.create_default()
        for c in m.constraints:
            if c.name == "OvernightCallGeneration":
                assert c.enabled is False
                break

    def test_create_default_sm_disabled(self):
        m = ConstraintManager.create_default()
        for c in m.constraints:
            if c.name == "SMResidentFacultyAlignment":
                assert c.enabled is False
                break

    def test_create_default_resilience_tier2_disabled(self):
        m = ConstraintManager.create_default()
        for c in m.constraints:
            if c.name == "ZoneBoundary":
                assert c.enabled is False
            if c.name == "N1Vulnerability":
                assert c.enabled is False

    def test_create_call_only(self):
        m = ConstraintManager.create_call_only()
        names = {c.name for c in m.constraints}
        assert "OvernightCallCoverage" in names
        assert "AdjunctCallExclusion" in names
        assert "CallAvailability" in names
        # Should NOT include rotation constraints
        assert "Availability" not in names

    def test_create_resilience_aware_tier2(self):
        m = ConstraintManager.create_resilience_aware(tier=2)
        names_enabled = {c.name for c in m.get_enabled()}
        assert "HubProtection" in names_enabled
        assert "UtilizationBuffer" in names_enabled
        assert "ZoneBoundary" in names_enabled
        assert "N1Vulnerability" in names_enabled

    def test_create_resilience_aware_tier1(self):
        m = ConstraintManager.create_resilience_aware(tier=1)
        for c in m.constraints:
            if c.name == "ZoneBoundary":
                assert c.enabled is False
            if c.name == "N1Vulnerability":
                assert c.enabled is False
        names_enabled = {c.name for c in m.get_enabled()}
        assert "HubProtection" in names_enabled
        assert "UtilizationBuffer" in names_enabled

    def test_create_resilience_aware_custom_utilization(self):
        m = ConstraintManager.create_resilience_aware(target_utilization=0.70)
        for c in m.constraints:
            if c.name == "UtilizationBuffer":
                assert c.target_utilization == 0.70
                break

    def test_create_minimal(self):
        m = ConstraintManager.create_minimal()
        names = {c.name for c in m.constraints}
        assert "Availability" in names
        assert "Coverage" in names
        assert len(m.constraints) == 2

    def test_create_strict(self):
        m = ConstraintManager.create_strict()
        # Should have same constraints as default but higher weights
        default = ConstraintManager.create_default()
        assert len(m.constraints) == len(default.constraints)

    def test_create_strict_doubled_weights(self):
        default = ConstraintManager.create_default()
        strict = ConstraintManager.create_strict()
        # Find a soft constraint and compare weights
        for sc in strict._soft_constraints:
            for dc in default._soft_constraints:
                if sc.name == dc.name:
                    assert sc.weight == dc.weight * 2, (
                        f"{sc.name}: strict={sc.weight}, default={dc.weight}"
                    )
                    break


# ==================== Method Chaining ====================


class TestConstraintManagerChaining:
    def test_full_chain(self):
        m = ConstraintManager()
        result = (
            m.add(_StubHard(name="H1"))
            .add(_StubSoft(name="S1"))
            .disable("S1")
            .enable("S1")
            .remove("H1")
        )
        assert result is m
        assert len(m.constraints) == 1
        assert m.constraints[0].name == "S1"
        assert m.constraints[0].enabled is True
