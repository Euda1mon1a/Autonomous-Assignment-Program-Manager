"""Tests for Defense in Depth (nuclear safety resilience pattern)."""

from unittest.mock import MagicMock

from app.resilience.defense_in_depth import (
    DefenseAction,
    DefenseInDepth,
    DefenseLevel,
    DefenseStatus,
    RedundancyStatus,
)


# ==================== DefenseLevel enum ====================


class TestDefenseLevel:
    def test_is_int_enum(self):
        assert isinstance(DefenseLevel.PREVENTION, int)

    def test_values(self):
        assert DefenseLevel.PREVENTION == 1
        assert DefenseLevel.CONTROL == 2
        assert DefenseLevel.SAFETY_SYSTEMS == 3
        assert DefenseLevel.CONTAINMENT == 4
        assert DefenseLevel.EMERGENCY == 5

    def test_count(self):
        assert len(DefenseLevel) == 5

    def test_ordering(self):
        assert DefenseLevel.PREVENTION < DefenseLevel.CONTROL
        assert DefenseLevel.CONTROL < DefenseLevel.SAFETY_SYSTEMS
        assert DefenseLevel.SAFETY_SYSTEMS < DefenseLevel.CONTAINMENT
        assert DefenseLevel.CONTAINMENT < DefenseLevel.EMERGENCY


# ==================== DefenseAction dataclass ====================


class TestDefenseAction:
    def test_required_fields(self):
        action = DefenseAction(
            name="test_action",
            description="A test action",
            level=DefenseLevel.PREVENTION,
        )
        assert action.name == "test_action"
        assert action.description == "A test action"
        assert action.level == DefenseLevel.PREVENTION

    def test_defaults(self):
        action = DefenseAction(
            name="test",
            description="test",
            level=DefenseLevel.CONTROL,
        )
        assert action.is_automated is False
        assert action.trigger_condition is None
        assert action.action_handler is None
        assert action.last_activated is None
        assert action.activation_count == 0

    def test_custom_fields(self):
        def handler(ctx):
            return None

        action = DefenseAction(
            name="auto_action",
            description="Automated action",
            level=DefenseLevel.SAFETY_SYSTEMS,
            is_automated=True,
            trigger_condition="coverage < 85%",
            action_handler=handler,
        )
        assert action.is_automated is True
        assert action.trigger_condition == "coverage < 85%"
        assert action.action_handler is handler


# ==================== DefenseStatus dataclass ====================


class TestDefenseStatus:
    def test_required_fields(self):
        status = DefenseStatus(
            level=DefenseLevel.PREVENTION,
            name="Prevention",
            status="ready",
        )
        assert status.level == DefenseLevel.PREVENTION
        assert status.name == "Prevention"
        assert status.status == "ready"

    def test_defaults(self):
        status = DefenseStatus(
            level=DefenseLevel.CONTROL,
            name="Control",
            status="ready",
        )
        assert status.actions == []
        assert status.alerts == []

    def test_with_actions(self):
        action = DefenseAction(
            name="test",
            description="Test",
            level=DefenseLevel.CONTAINMENT,
        )
        status = DefenseStatus(
            level=DefenseLevel.CONTAINMENT,
            name="Containment",
            status="active",
            actions=[action],
            alerts=["Coverage below 80%"],
        )
        assert len(status.actions) == 1
        assert status.actions[0].name == "test"
        assert len(status.alerts) == 1


# ==================== RedundancyStatus dataclass ====================


class TestRedundancyStatus:
    def test_all_fields(self):
        rs = RedundancyStatus(
            function_name="surgery",
            required_minimum=3,
            current_available=5,
            redundancy_level=2,
            status="N+2",
        )
        assert rs.function_name == "surgery"
        assert rs.required_minimum == 3
        assert rs.current_available == 5
        assert rs.redundancy_level == 2
        assert rs.status == "N+2"


# ==================== DefenseInDepth ====================


class TestDefenseInDepthInit:
    def test_initializes_five_levels(self):
        did = DefenseInDepth()
        assert len(did.levels) == 5

    def test_all_levels_present(self):
        did = DefenseInDepth()
        for level in DefenseLevel:
            assert level in did.levels

    def test_all_levels_ready(self):
        did = DefenseInDepth()
        for status in did.levels.values():
            assert status.status == "ready"

    def test_each_level_has_three_actions(self):
        did = DefenseInDepth()
        for status in did.levels.values():
            assert len(status.actions) == 3

    def test_prevention_actions(self):
        did = DefenseInDepth()
        names = {a.name for a in did.levels[DefenseLevel.PREVENTION].actions}
        assert names == {"capacity_buffer", "cross_training", "absence_forecasting"}

    def test_control_actions(self):
        did = DefenseInDepth()
        names = {a.name for a in did.levels[DefenseLevel.CONTROL].actions}
        assert names == {"coverage_monitoring", "early_warning", "burnout_tracking"}

    def test_safety_systems_actions(self):
        did = DefenseInDepth()
        names = {a.name for a in did.levels[DefenseLevel.SAFETY_SYSTEMS].actions}
        assert names == {
            "auto_reassignment",
            "backup_activation",
            "overtime_authorization",
        }

    def test_containment_actions(self):
        did = DefenseInDepth()
        names = {a.name for a in did.levels[DefenseLevel.CONTAINMENT].actions}
        assert names == {
            "service_reduction",
            "minimum_service_protection",
            "zone_isolation",
        }

    def test_emergency_actions(self):
        did = DefenseInDepth()
        names = {a.name for a in did.levels[DefenseLevel.EMERGENCY].actions}
        assert names == {
            "crisis_communication",
            "external_escalation",
            "incident_documentation",
        }


class TestGetLevelStatus:
    def test_returns_status(self):
        did = DefenseInDepth()
        status = did.get_level_status(DefenseLevel.PREVENTION)
        assert isinstance(status, DefenseStatus)
        assert status.level == DefenseLevel.PREVENTION

    def test_returns_each_level(self):
        did = DefenseInDepth()
        for level in DefenseLevel:
            status = did.get_level_status(level)
            assert status.level == level


class TestGetAllStatus:
    def test_returns_all_five(self):
        did = DefenseInDepth()
        all_status = did.get_all_status()
        assert len(all_status) == 5

    def test_returns_list_of_defense_status(self):
        did = DefenseInDepth()
        for s in did.get_all_status():
            assert isinstance(s, DefenseStatus)


class TestActivateAction:
    def test_activate_valid_action(self):
        did = DefenseInDepth()
        result = did.activate_action(DefenseLevel.PREVENTION, "capacity_buffer")
        assert result is True

    def test_updates_activation_count(self):
        did = DefenseInDepth()
        did.activate_action(DefenseLevel.PREVENTION, "capacity_buffer")
        action = next(
            a
            for a in did.levels[DefenseLevel.PREVENTION].actions
            if a.name == "capacity_buffer"
        )
        assert action.activation_count == 1

    def test_sets_last_activated(self):
        did = DefenseInDepth()
        did.activate_action(DefenseLevel.CONTROL, "early_warning")
        action = next(
            a
            for a in did.levels[DefenseLevel.CONTROL].actions
            if a.name == "early_warning"
        )
        assert action.last_activated is not None

    def test_multiple_activations(self):
        did = DefenseInDepth()
        did.activate_action(DefenseLevel.EMERGENCY, "crisis_communication")
        did.activate_action(DefenseLevel.EMERGENCY, "crisis_communication")
        action = next(
            a
            for a in did.levels[DefenseLevel.EMERGENCY].actions
            if a.name == "crisis_communication"
        )
        assert action.activation_count == 2

    def test_unknown_action_returns_false(self):
        did = DefenseInDepth()
        result = did.activate_action(DefenseLevel.PREVENTION, "nonexistent_action")
        assert result is False

    def test_calls_action_handler(self):
        did = DefenseInDepth()
        handler = MagicMock()
        did.register_action_handler(DefenseLevel.PREVENTION, "capacity_buffer", handler)
        context = {"coverage": 0.85}
        did.activate_action(DefenseLevel.PREVENTION, "capacity_buffer", context=context)
        handler.assert_called_once_with(context)

    def test_handler_exception_returns_false(self):
        did = DefenseInDepth()
        handler = MagicMock(side_effect=RuntimeError("handler failed"))
        did.register_action_handler(
            DefenseLevel.CONTROL, "coverage_monitoring", handler
        )
        result = did.activate_action(
            DefenseLevel.CONTROL, "coverage_monitoring", context={"x": 1}
        )
        assert result is False

    def test_no_handler_call_without_context(self):
        did = DefenseInDepth()
        handler = MagicMock()
        did.register_action_handler(DefenseLevel.PREVENTION, "capacity_buffer", handler)
        did.activate_action(DefenseLevel.PREVENTION, "capacity_buffer")
        handler.assert_not_called()


class TestCheckRedundancy:
    def test_n_plus_2(self):
        did = DefenseInDepth()
        status = did.check_redundancy("surgery", ["A", "B", "C", "D", "E"], 3)
        assert status.status == "N+2"
        assert status.redundancy_level == 2

    def test_n_plus_1(self):
        did = DefenseInDepth()
        status = did.check_redundancy("surgery", ["A", "B", "C", "D"], 3)
        assert status.status == "N+1"
        assert status.redundancy_level == 1

    def test_n_plus_0(self):
        did = DefenseInDepth()
        status = did.check_redundancy("surgery", ["A", "B", "C"], 3)
        assert status.status == "N+0"
        assert status.redundancy_level == 0

    def test_below_minimum(self):
        did = DefenseInDepth()
        status = did.check_redundancy("surgery", ["A", "B"], 3)
        assert status.status == "BELOW"
        assert status.redundancy_level == 0  # max(0, -1)

    def test_high_redundancy(self):
        did = DefenseInDepth()
        status = did.check_redundancy("surgery", list(range(10)), 3)
        assert status.status == "N+2"
        assert status.redundancy_level == 7

    def test_fields_populated(self):
        did = DefenseInDepth()
        status = did.check_redundancy("ortho", ["A", "B"], 2)
        assert status.function_name == "ortho"
        assert status.required_minimum == 2
        assert status.current_available == 2


class TestCheckAllRedundancy:
    def test_multiple_services(self):
        did = DefenseInDepth()
        services = {
            "surgery": {
                "available_providers": ["A", "B", "C", "D", "E"],
                "minimum_required": 3,
            },
            "medicine": {
                "available_providers": ["X", "Y"],
                "minimum_required": 2,
            },
        }
        results = did.check_all_redundancy(services)
        assert len(results) == 2
        assert results[0].function_name == "surgery"
        assert results[0].status == "N+2"
        assert results[1].function_name == "medicine"
        assert results[1].status == "N+0"

    def test_empty_services(self):
        did = DefenseInDepth()
        results = did.check_all_redundancy({})
        assert results == []

    def test_defaults_for_missing_keys(self):
        did = DefenseInDepth()
        services = {"service_x": {}}
        results = did.check_all_redundancy(services)
        assert len(results) == 1
        assert results[0].required_minimum == 1
        assert results[0].current_available == 0


class TestGetRecommendedLevel:
    def test_prevention_at_95_plus(self):
        assert DefenseInDepth.get_recommended_level(0.95) == DefenseLevel.PREVENTION
        assert DefenseInDepth.get_recommended_level(1.0) == DefenseLevel.PREVENTION

    def test_control_at_90_to_95(self):
        assert DefenseInDepth.get_recommended_level(0.90) == DefenseLevel.CONTROL
        assert DefenseInDepth.get_recommended_level(0.94) == DefenseLevel.CONTROL

    def test_safety_systems_at_80_to_90(self):
        assert DefenseInDepth.get_recommended_level(0.80) == DefenseLevel.SAFETY_SYSTEMS
        assert DefenseInDepth.get_recommended_level(0.89) == DefenseLevel.SAFETY_SYSTEMS

    def test_containment_at_70_to_80(self):
        assert DefenseInDepth.get_recommended_level(0.70) == DefenseLevel.CONTAINMENT
        assert DefenseInDepth.get_recommended_level(0.79) == DefenseLevel.CONTAINMENT

    def test_emergency_below_70(self):
        assert DefenseInDepth.get_recommended_level(0.69) == DefenseLevel.EMERGENCY
        assert DefenseInDepth.get_recommended_level(0.0) == DefenseLevel.EMERGENCY

    def test_is_cached(self):
        # Call twice — lru_cache should return same object
        r1 = DefenseInDepth.get_recommended_level(0.85)
        r2 = DefenseInDepth.get_recommended_level(0.85)
        assert r1 is r2


class TestGetStatusReport:
    def test_report_structure(self):
        did = DefenseInDepth()
        report = did.get_status_report()
        assert "levels" in report
        assert "summary" in report
        assert len(report["levels"]) == 5

    def test_all_ready_summary(self):
        did = DefenseInDepth()
        report = did.get_status_report()
        assert report["summary"]["all_levels_ready"] is True
        assert report["summary"]["active_alerts"] == 0

    def test_level_detail_structure(self):
        did = DefenseInDepth()
        report = did.get_status_report()
        level_info = report["levels"][0]
        assert "level" in level_info
        assert "name" in level_info
        assert "status" in level_info
        assert "actions" in level_info
        assert "alerts" in level_info

    def test_action_detail_structure(self):
        did = DefenseInDepth()
        report = did.get_status_report()
        action_info = report["levels"][0]["actions"][0]
        assert "name" in action_info
        assert "description" in action_info
        assert "automated" in action_info
        assert "activations" in action_info
        assert "last_activated" in action_info

    def test_activation_reflected_in_report(self):
        did = DefenseInDepth()
        did.activate_action(DefenseLevel.PREVENTION, "capacity_buffer")
        report = did.get_status_report()
        prevention = report["levels"][0]
        buffer_action = next(
            a for a in prevention["actions"] if a["name"] == "capacity_buffer"
        )
        assert buffer_action["activations"] == 1
        assert buffer_action["last_activated"] is not None

    def test_alerts_reflected(self):
        did = DefenseInDepth()
        did.levels[DefenseLevel.CONTROL].alerts.append("Coverage dropping")
        report = did.get_status_report()
        assert report["summary"]["active_alerts"] == 1
        assert report["summary"]["all_levels_ready"] is True  # status still "ready"


class TestRegisterActionHandler:
    def test_registers_handler(self):
        did = DefenseInDepth()
        handler = MagicMock()
        did.register_action_handler(DefenseLevel.PREVENTION, "capacity_buffer", handler)
        action = next(
            a
            for a in did.levels[DefenseLevel.PREVENTION].actions
            if a.name == "capacity_buffer"
        )
        assert action.action_handler is handler

    def test_nonexistent_action(self):
        did = DefenseInDepth()
        handler = MagicMock()
        # Should not raise, just log warning
        did.register_action_handler(DefenseLevel.PREVENTION, "nonexistent", handler)
