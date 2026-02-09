"""Tests for Behavioral Network Analysis (Counter-Insurgency / Forensic Accounting)."""

from datetime import datetime
from uuid import uuid4

from app.resilience.behavioral_network import (
    BehavioralNetworkAnalyzer,
    BehavioralRole,
    BurdenCategory,
    DEFAULT_BURDEN_WEIGHTS,
    EquityStatus,
    FacultyBurdenProfile,
    ProtectionLevel,
    ShadowOrgChartService,
    ShiftBurden,
    SwapEdge,
    SwapNetworkAnalysis,
    SwapNetworkNode,
)


# ==================== BehavioralRole enum ====================


class TestBehavioralRole:
    def test_values(self):
        assert BehavioralRole.NEUTRAL == "neutral"
        assert BehavioralRole.POWER_BROKER == "power_broker"
        assert BehavioralRole.MARTYR == "martyr"
        assert BehavioralRole.EVADER == "evader"
        assert BehavioralRole.ISOLATE == "isolate"
        assert BehavioralRole.STABILIZER == "stabilizer"

    def test_is_str_enum(self):
        assert isinstance(BehavioralRole.NEUTRAL, str)

    def test_count(self):
        assert len(BehavioralRole) == 6


# ==================== BurdenCategory enum ====================


class TestBurdenCategory:
    def test_values(self):
        assert BurdenCategory.MINIMAL == "minimal"
        assert BurdenCategory.LOW == "low"
        assert BurdenCategory.MODERATE == "moderate"
        assert BurdenCategory.HIGH == "high"
        assert BurdenCategory.SEVERE == "severe"
        assert BurdenCategory.EXTREME == "extreme"

    def test_count(self):
        assert len(BurdenCategory) == 6


# ==================== EquityStatus enum ====================


class TestEquityStatus:
    def test_values(self):
        assert EquityStatus.BALANCED == "balanced"
        assert EquityStatus.LIGHT == "light"
        assert EquityStatus.HEAVY == "heavy"
        assert EquityStatus.VERY_LIGHT == "very_light"
        assert EquityStatus.CRUSHING == "crushing"

    def test_count(self):
        assert len(EquityStatus) == 5


# ==================== ProtectionLevel enum ====================


class TestProtectionLevel:
    def test_values(self):
        assert ProtectionLevel.NONE == "none"
        assert ProtectionLevel.MONITORING == "monitoring"
        assert ProtectionLevel.SOFT_LIMIT == "soft_limit"
        assert ProtectionLevel.HARD_LIMIT == "hard_limit"

    def test_count(self):
        assert len(ProtectionLevel) == 4


# ==================== DEFAULT_BURDEN_WEIGHTS ====================


class TestDefaultBurdenWeights:
    def test_has_time_of_day(self):
        assert "day" in DEFAULT_BURDEN_WEIGHTS
        assert "night" in DEFAULT_BURDEN_WEIGHTS
        assert "evening" in DEFAULT_BURDEN_WEIGHTS

    def test_has_day_of_week(self):
        assert "weekday" in DEFAULT_BURDEN_WEIGHTS
        assert "saturday" in DEFAULT_BURDEN_WEIGHTS
        assert "sunday" in DEFAULT_BURDEN_WEIGHTS
        assert "holiday" in DEFAULT_BURDEN_WEIGHTS

    def test_has_shift_types(self):
        assert "clinic" in DEFAULT_BURDEN_WEIGHTS
        assert "icu" in DEFAULT_BURDEN_WEIGHTS
        assert "on_call" in DEFAULT_BURDEN_WEIGHTS

    def test_night_more_than_day(self):
        assert DEFAULT_BURDEN_WEIGHTS["night"] > DEFAULT_BURDEN_WEIGHTS["day"]

    def test_holiday_more_than_weekday(self):
        assert DEFAULT_BURDEN_WEIGHTS["holiday"] > DEFAULT_BURDEN_WEIGHTS["weekday"]


# ==================== ShiftBurden dataclass ====================


class TestShiftBurden:
    def test_all_fields(self):
        uid = uuid4()
        fid = uuid4()
        sb = ShiftBurden(
            shift_id=uid,
            faculty_id=fid,
            date=datetime.now(),
            shift_type="icu",
            raw_hours=12.0,
            burden_weight=1.8,
            weighted_burden=21.6,
            category=BurdenCategory.HIGH,
            factors=["shift_type:icu"],
        )
        assert sb.shift_id == uid
        assert sb.raw_hours == 12.0
        assert sb.category == BurdenCategory.HIGH

    def test_factors_default(self):
        sb = ShiftBurden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime.now(),
            shift_type="clinic",
            raw_hours=8.0,
            burden_weight=0.8,
            weighted_burden=6.4,
            category=BurdenCategory.LOW,
        )
        assert sb.factors == []


# ==================== FacultyBurdenProfile dataclass ====================


class TestFacultyBurdenProfile:
    def test_defaults(self):
        profile = FacultyBurdenProfile(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            period_start=datetime.now(),
            period_end=datetime.now(),
            calculated_at=datetime.now(),
        )
        assert profile.total_hours == 0.0
        assert profile.total_shifts == 0
        assert profile.total_burden == 0.0
        assert profile.equity_status == EquityStatus.BALANCED
        assert profile.behavioral_role == BehavioralRole.NEUTRAL
        assert profile.protection_level == ProtectionLevel.NONE


# ==================== SwapEdge dataclass ====================


class TestSwapEdge:
    def test_defaults(self):
        edge = SwapEdge(source_id=uuid4(), target_id=uuid4())
        assert edge.swap_count == 0
        assert edge.source_initiated == 0
        assert edge.target_initiated == 0
        assert edge.burden_flow == 0.0
        assert edge.success_rate == 1.0


# ==================== SwapNetworkNode dataclass ====================


class TestSwapNetworkNode:
    def test_defaults(self):
        node = SwapNetworkNode(faculty_id=uuid4(), faculty_name="Dr. Node")
        assert node.degree == 0
        assert node.swap_count == 0
        assert node.net_burden_flow == 0.0
        assert node.behavioral_role == BehavioralRole.NEUTRAL
        assert node.role_confidence == 0.0


# ==================== SwapNetworkAnalysis dataclass ====================


class TestSwapNetworkAnalysis:
    def test_defaults(self):
        analysis = SwapNetworkAnalysis(
            analyzed_at=datetime.now(),
            period_start=datetime.now(),
            period_end=datetime.now(),
            total_swaps=10,
            total_faculty=5,
        )
        assert analysis.network_density == 0.0
        assert analysis.power_brokers == []
        assert analysis.martyrs == []
        assert analysis.evaders == []
        assert analysis.isolates == []
        assert analysis.stabilizers == []
        assert analysis.equity_concerns == []


# ==================== BehavioralNetworkAnalyzer ====================


class TestBehavioralNetworkAnalyzerInit:
    def test_defaults(self):
        analyzer = BehavioralNetworkAnalyzer()
        assert analyzer.burden_weights == DEFAULT_BURDEN_WEIGHTS
        assert analyzer.martyr_threshold == 1.5
        assert analyzer.evader_threshold == -1.5
        assert analyzer.min_swaps == 3
        assert analyzer.nodes == {}
        assert analyzer.edges == {}

    def test_custom(self):
        analyzer = BehavioralNetworkAnalyzer(
            martyr_threshold=2.0,
            evader_threshold=-2.0,
            min_swaps_for_classification=5,
        )
        assert analyzer.martyr_threshold == 2.0
        assert analyzer.evader_threshold == -2.0
        assert analyzer.min_swaps == 5


# ==================== calculate_shift_burden ====================


class TestCalculateShiftBurden:
    def test_basic_clinic(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 5),  # Monday
            shift_type="clinic",
            hours=8.0,
        )
        assert isinstance(result, ShiftBurden)
        assert result.raw_hours == 8.0
        # clinic weight = 0.8, so 8 * 0.8 = 6.4
        assert abs(result.weighted_burden - 6.4) < 0.01
        assert result.category == BurdenCategory.LOW

    def test_night_shift(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 5),
            shift_type="inpatient",
            hours=12.0,
            is_night=True,
        )
        # inpatient=1.2, night=2.5 → 1.2*2.5=3.0, 12*3.0=36.0
        assert result.weighted_burden > 30
        assert "night" in result.factors

    def test_weekend_shift(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 3),  # Saturday
            shift_type="inpatient",
            hours=10.0,
            is_weekend=True,
        )
        assert "weekend" in result.factors

    def test_holiday_shift(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 1),
            shift_type="inpatient",
            hours=12.0,
            is_holiday=True,
        )
        assert "holiday" in result.factors
        assert result.weighted_burden > 30  # High burden

    def test_weekend_night_combined(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 3),
            shift_type="icu",
            hours=12.0,
            is_weekend=True,
            is_night=True,
        )
        # Should use weekend_night=3.5 combined weight
        assert "weekend_night" in result.factors

    def test_minimal_burden_category(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 5),
            shift_type="admin",
            hours=4.0,
        )
        # admin=0.3, 4*0.3=1.2 → MINIMAL
        assert result.category == BurdenCategory.MINIMAL

    def test_extreme_burden_category(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 1),
            shift_type="icu",
            hours=14.0,
            is_holiday=True,
            is_night=True,
        )
        # holiday_night=4.0, 14*4.0=56 → EXTREME
        assert result.category == BurdenCategory.EXTREME

    def test_custom_factors(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2026, 1, 5),
            shift_type="clinic",
            hours=8.0,
            custom_factors=["trainee_supervision"],
        )
        assert "trainee_supervision" in result.factors


# ==================== calculate_faculty_burden_profile ====================


class TestCalculateFacultyBurdenProfile:
    def _make_shift(
        self,
        hours=8.0,
        burden=10.0,
        category=BurdenCategory.MODERATE,
        shift_type="clinic",
    ):
        return ShiftBurden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime.now(),
            shift_type=shift_type,
            raw_hours=hours,
            burden_weight=burden / hours if hours > 0 else 1.0,
            weighted_burden=burden,
            category=category,
        )

    def test_empty_shifts(self):
        analyzer = BehavioralNetworkAnalyzer()
        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=uuid4(),
            faculty_name="Dr. Empty",
            shifts=[],
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert profile.total_shifts == 0
        assert profile.total_hours == 0.0
        assert profile.total_burden == 0.0

    def test_aggregates_shifts(self):
        analyzer = BehavioralNetworkAnalyzer()
        shifts = [
            self._make_shift(hours=8.0, burden=10.0, shift_type="clinic"),
            self._make_shift(hours=12.0, burden=25.0, shift_type="icu"),
        ]
        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            shifts=shifts,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert profile.total_shifts == 2
        assert abs(profile.total_hours - 20.0) < 0.01
        assert abs(profile.total_burden - 35.0) < 0.01
        assert profile.shift_breakdown["clinic"] == 1
        assert profile.shift_breakdown["icu"] == 1

    def test_burden_per_hour(self):
        analyzer = BehavioralNetworkAnalyzer()
        shifts = [self._make_shift(hours=10.0, burden=20.0)]
        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            shifts=shifts,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert abs(profile.burden_per_hour - 2.0) < 0.01

    def test_high_burden_count(self):
        analyzer = BehavioralNetworkAnalyzer()
        shifts = [
            self._make_shift(category=BurdenCategory.MODERATE),
            self._make_shift(category=BurdenCategory.SEVERE),
            self._make_shift(category=BurdenCategory.EXTREME),
        ]
        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=uuid4(),
            faculty_name="Dr. Test",
            shifts=shifts,
            period_start=datetime.now(),
            period_end=datetime.now(),
        )
        assert profile.high_burden_shifts == 2  # SEVERE + EXTREME

    def test_equity_crushing(self):
        analyzer = BehavioralNetworkAnalyzer()
        shifts = [self._make_shift(hours=8.0, burden=200.0)]
        # Need many low-burden peers so the outlier is >2 std devs above mean
        all_burdens = [200.0] + [20.0] * 9
        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=uuid4(),
            faculty_name="Dr. Overworked",
            shifts=shifts,
            period_start=datetime.now(),
            period_end=datetime.now(),
            all_faculty_burdens=all_burdens,
        )
        assert profile.equity_status == EquityStatus.CRUSHING

    def test_equity_very_light(self):
        analyzer = BehavioralNetworkAnalyzer()
        shifts = [self._make_shift(hours=2.0, burden=2.0)]
        # Need many high-burden peers so the outlier is >2 std devs below mean
        all_burdens = [2.0] + [80.0] * 9
        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=uuid4(),
            faculty_name="Dr. Light",
            shifts=shifts,
            period_start=datetime.now(),
            period_end=datetime.now(),
            all_faculty_burdens=all_burdens,
        )
        assert profile.equity_status == EquityStatus.VERY_LIGHT

    def test_equity_balanced(self):
        analyzer = BehavioralNetworkAnalyzer()
        shifts = [self._make_shift(hours=8.0, burden=50.0)]
        all_burdens = [50.0, 48.0, 52.0, 49.0, 51.0]
        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=uuid4(),
            faculty_name="Dr. Balanced",
            shifts=shifts,
            period_start=datetime.now(),
            period_end=datetime.now(),
            all_faculty_burdens=all_burdens,
        )
        assert profile.equity_status == EquityStatus.BALANCED


# ==================== record_swap ====================


class TestRecordSwap:
    def test_creates_nodes_and_edge(self):
        analyzer = BehavioralNetworkAnalyzer()
        s_id, t_id = uuid4(), uuid4()
        analyzer.record_swap(
            source_id=s_id,
            source_name="Dr. A",
            target_id=t_id,
            target_name="Dr. B",
            initiated_by=s_id,
            source_burden=15.0,
            target_burden=10.0,
            was_successful=True,
        )
        assert s_id in analyzer.nodes
        assert t_id in analyzer.nodes
        assert len(analyzer.edges) == 1

    def test_updates_request_counts(self):
        analyzer = BehavioralNetworkAnalyzer()
        s_id, t_id = uuid4(), uuid4()
        analyzer.record_swap(
            source_id=s_id,
            source_name="A",
            target_id=t_id,
            target_name="B",
            initiated_by=s_id,
            source_burden=10.0,
            target_burden=0.0,
            was_successful=True,
        )
        assert analyzer.nodes[s_id].requests_made == 1
        assert analyzer.nodes[s_id].requests_granted == 1
        assert analyzer.nodes[t_id].requests_received == 1
        assert analyzer.nodes[t_id].requests_accepted == 1

    def test_unsuccessful_swap(self):
        analyzer = BehavioralNetworkAnalyzer()
        s_id, t_id = uuid4(), uuid4()
        analyzer.record_swap(
            source_id=s_id,
            source_name="A",
            target_id=t_id,
            target_name="B",
            initiated_by=s_id,
            source_burden=10.0,
            target_burden=0.0,
            was_successful=False,
        )
        assert analyzer.nodes[s_id].swap_count == 0
        assert analyzer.nodes[s_id].requests_made == 1
        assert analyzer.nodes[s_id].requests_granted == 0

    def test_burden_tracking(self):
        analyzer = BehavioralNetworkAnalyzer()
        s_id, t_id = uuid4(), uuid4()
        analyzer.record_swap(
            source_id=s_id,
            source_name="A",
            target_id=t_id,
            target_name="B",
            initiated_by=s_id,
            source_burden=20.0,
            target_burden=5.0,
            was_successful=True,
        )
        # Source offloaded burden, target absorbed it
        assert analyzer.nodes[s_id].burden_offloaded == 20.0
        assert analyzer.nodes[t_id].burden_absorbed == 20.0

    def test_multiple_swaps_same_pair(self):
        analyzer = BehavioralNetworkAnalyzer()
        s_id, t_id = uuid4(), uuid4()
        for _ in range(3):
            analyzer.record_swap(
                source_id=s_id,
                source_name="A",
                target_id=t_id,
                target_name="B",
                initiated_by=s_id,
                source_burden=10.0,
                target_burden=0.0,
                was_successful=True,
            )
        assert len(analyzer.edges) == 1  # Same edge
        edge = list(analyzer.edges.values())[0]
        assert edge.swap_count == 3


# ==================== analyze_network ====================


class TestAnalyzeNetwork:
    def _build_network(self, analyzer, num_swaps=5):
        """Build a simple network with known patterns."""
        ids = [uuid4() for _ in range(4)]
        names = ["Martyr", "Evader", "Stabilizer", "Isolate"]

        # Martyr absorbs burden from everyone
        for i in range(1, 3):
            for _ in range(num_swaps):
                analyzer.record_swap(
                    source_id=ids[i],
                    source_name=names[i],
                    target_id=ids[0],
                    target_name=names[0],
                    initiated_by=ids[i],
                    source_burden=20.0,
                    target_burden=0.0,
                    was_successful=True,
                )
        return ids

    def test_empty_network(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.analyze_network(datetime.now(), datetime.now())
        assert isinstance(result, SwapNetworkAnalysis)
        assert result.total_faculty == 0
        assert result.total_swaps == 0

    def test_network_statistics(self):
        analyzer = BehavioralNetworkAnalyzer()
        self._build_network(analyzer)
        result = analyzer.analyze_network(datetime.now(), datetime.now())
        assert result.total_faculty == 3  # 3 participants (Isolate not added)
        assert result.total_swaps > 0
        assert result.network_density > 0

    def test_classifies_roles(self):
        analyzer = BehavioralNetworkAnalyzer(min_swaps_for_classification=2)
        ids = self._build_network(analyzer, num_swaps=5)
        analyzer.analyze_network(datetime.now(), datetime.now())
        # The node that absorbed all the burden should be MARTYR
        martyr_node = analyzer.nodes[ids[0]]
        assert martyr_node.behavioral_role == BehavioralRole.MARTYR

    def test_equity_concerns_generated(self):
        analyzer = BehavioralNetworkAnalyzer(min_swaps_for_classification=2)
        # Create many martyrs (>20% of total)
        ids = [uuid4() for _ in range(10)]
        # 3 martyrs absorbing from 7 others
        for i in range(3):
            for j in range(3, 10):
                for _ in range(5):
                    analyzer.record_swap(
                        source_id=ids[j],
                        source_name=f"Evader{j}",
                        target_id=ids[i],
                        target_name=f"Martyr{i}",
                        initiated_by=ids[j],
                        source_burden=20.0,
                        target_burden=0.0,
                        was_successful=True,
                    )
        result = analyzer.analyze_network(datetime.now(), datetime.now())
        assert len(result.martyrs) > 0


# ==================== _classify_roles ====================


class TestClassifyRoles:
    def test_isolate_detection(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Loner",
            swap_count=0,
            requests_made=0,
            requests_received=0,
        )
        # Need at least 2 nodes with swaps for stdev
        s1, s2 = uuid4(), uuid4()
        analyzer.nodes[s1] = SwapNetworkNode(
            faculty_id=s1,
            faculty_name="Dr. A",
            swap_count=5,
            net_burden_flow=10.0,
        )
        analyzer.nodes[s2] = SwapNetworkNode(
            faculty_id=s2,
            faculty_name="Dr. B",
            swap_count=5,
            net_burden_flow=-10.0,
        )
        analyzer._classify_roles()
        assert analyzer.nodes[uid].behavioral_role == BehavioralRole.ISOLATE

    def test_not_enough_data(self):
        analyzer = BehavioralNetworkAnalyzer()
        analyzer._classify_roles()  # Empty nodes - should not error


# ==================== get_martyr_protection_level ====================


class TestGetMartyrProtectionLevel:
    def test_not_in_network(self):
        analyzer = BehavioralNetworkAnalyzer()
        level, reason = analyzer.get_martyr_protection_level(uuid4())
        assert level == ProtectionLevel.NONE
        assert "Not in swap network" in reason

    def test_non_martyr_no_protection(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Normal",
            behavioral_role=BehavioralRole.NEUTRAL,
        )
        level, reason = analyzer.get_martyr_protection_level(uid)
        assert level == ProtectionLevel.NONE

    def test_non_martyr_high_stress(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Stressed",
            behavioral_role=BehavioralRole.NEUTRAL,
        )
        level, _ = analyzer.get_martyr_protection_level(uid, current_allostatic_load=85)
        assert level == ProtectionLevel.SOFT_LIMIT

    def test_martyr_high_stress_hard_limit(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Martyr",
            behavioral_role=BehavioralRole.MARTYR,
        )
        level, _ = analyzer.get_martyr_protection_level(uid, current_allostatic_load=75)
        assert level == ProtectionLevel.HARD_LIMIT

    def test_martyr_severe_imbalance_hard_limit(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Martyr",
            behavioral_role=BehavioralRole.MARTYR,
            burden_absorbed=100.0,
            burden_offloaded=10.0,  # 10x ratio > 3x threshold
        )
        level, _ = analyzer.get_martyr_protection_level(uid)
        assert level == ProtectionLevel.HARD_LIMIT

    def test_martyr_moderate_imbalance_soft_limit(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Martyr",
            behavioral_role=BehavioralRole.MARTYR,
            burden_absorbed=50.0,
            burden_offloaded=20.0,  # 2.5x ratio > 2x threshold
        )
        level, _ = analyzer.get_martyr_protection_level(uid)
        assert level == ProtectionLevel.SOFT_LIMIT

    def test_martyr_monitoring(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Martyr",
            behavioral_role=BehavioralRole.MARTYR,
            burden_absorbed=30.0,
            burden_offloaded=20.0,  # 1.5x ratio < 2x threshold
        )
        level, _ = analyzer.get_martyr_protection_level(uid)
        assert level == ProtectionLevel.MONITORING


# ==================== should_block_swap ====================


class TestShouldBlockSwap:
    def test_no_block_for_normal(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Normal",
            behavioral_role=BehavioralRole.NEUTRAL,
        )
        blocked, reason = analyzer.should_block_swap(uid, source_burden=10.0)
        assert not blocked
        assert reason == ""

    def test_blocks_hard_limit(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Martyr",
            behavioral_role=BehavioralRole.MARTYR,
            burden_absorbed=100.0,
            burden_offloaded=10.0,
        )
        blocked, reason = analyzer.should_block_swap(uid, source_burden=10.0)
        assert blocked
        assert "BLOCKED" in reason

    def test_blocks_soft_limit_high_burden(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Martyr",
            behavioral_role=BehavioralRole.MARTYR,
            burden_absorbed=50.0,
            burden_offloaded=20.0,
        )
        # Soft limit + high burden shift (>15)
        blocked, reason = analyzer.should_block_swap(uid, source_burden=20.0)
        assert blocked
        assert "BLOCKED" in reason

    def test_allows_soft_limit_low_burden(self):
        analyzer = BehavioralNetworkAnalyzer()
        uid = uuid4()
        analyzer.nodes[uid] = SwapNetworkNode(
            faculty_id=uid,
            faculty_name="Dr. Martyr",
            behavioral_role=BehavioralRole.MARTYR,
            burden_absorbed=50.0,
            burden_offloaded=20.0,
        )
        # Soft limit but low burden shift (<=15) → allowed
        blocked, _ = analyzer.should_block_swap(uid, source_burden=10.0)
        assert not blocked


# ==================== analyze_burden_equity ====================


class TestAnalyzeBurdenEquity:
    def _make_profile(
        self, name, total_burden, total_hours=40.0, equity_status=EquityStatus.BALANCED
    ):
        return FacultyBurdenProfile(
            faculty_id=uuid4(),
            faculty_name=name,
            period_start=datetime.now(),
            period_end=datetime.now(),
            calculated_at=datetime.now(),
            total_burden=total_burden,
            total_hours=total_hours,
            equity_status=equity_status,
        )

    def test_empty_profiles(self):
        analyzer = BehavioralNetworkAnalyzer()
        result = analyzer.analyze_burden_equity([])
        assert "error" in result

    def test_basic_statistics(self):
        analyzer = BehavioralNetworkAnalyzer()
        profiles = [
            self._make_profile("A", 50.0),
            self._make_profile("B", 60.0),
            self._make_profile("C", 40.0),
        ]
        result = analyzer.analyze_burden_equity(profiles)
        assert abs(result["mean_burden"] - 50.0) < 0.01
        assert result["gini_coefficient"] >= 0

    def test_gini_perfect_equality(self):
        analyzer = BehavioralNetworkAnalyzer()
        profiles = [self._make_profile(f"Dr{i}", 50.0) for i in range(5)]
        result = analyzer.analyze_burden_equity(profiles)
        assert abs(result["gini_coefficient"]) < 0.01

    def test_crushing_recommendations(self):
        analyzer = BehavioralNetworkAnalyzer()
        profiles = [
            self._make_profile(
                "Overworked", 100.0, equity_status=EquityStatus.CRUSHING
            ),
            self._make_profile("Normal1", 40.0),
            self._make_profile("Normal2", 40.0),
        ]
        result = analyzer.analyze_burden_equity(profiles)
        assert result["distribution"]["crushing"] == 1
        assert any("CRITICAL" in r for r in result["recommendations"])

    def test_rebalancing_recommendation(self):
        analyzer = BehavioralNetworkAnalyzer()
        profiles = [
            self._make_profile("Crushed", 100.0, equity_status=EquityStatus.CRUSHING),
            self._make_profile("Light", 10.0, equity_status=EquityStatus.VERY_LIGHT),
        ]
        result = analyzer.analyze_burden_equity(profiles)
        assert any("Rebalancing" in r for r in result["recommendations"])

    def test_equity_grade(self):
        analyzer = BehavioralNetworkAnalyzer()
        assert "A" in analyzer._grade_equity(0.05)
        assert "B" in analyzer._grade_equity(0.15)
        assert "C" in analyzer._grade_equity(0.25)
        assert "D" in analyzer._grade_equity(0.35)
        assert "F" in analyzer._grade_equity(0.45)

    def test_burden_light_pattern_detection(self):
        analyzer = BehavioralNetworkAnalyzer()
        profiles = [
            self._make_profile(
                "Dr. Games", 10.0, total_hours=60.0
            ),  # High hours, low burden
            self._make_profile("Dr. Works", 50.0, total_hours=40.0),
            self._make_profile("Dr. Normal", 45.0, total_hours=40.0),
        ]
        result = analyzer.analyze_burden_equity(profiles)
        assert any("burden-light" in r.lower() for r in result["recommendations"])


# ==================== ShadowOrgChartService ====================


class TestShadowOrgChartServiceInit:
    def test_init(self):
        service = ShadowOrgChartService()
        assert isinstance(service.analyzer, BehavioralNetworkAnalyzer)
        assert service.network_history == []


class TestBuildFromSwapRecords:
    def test_builds_network(self):
        service = ShadowOrgChartService()
        s_id, t_id = uuid4(), uuid4()
        records = [
            {
                "source_id": s_id,
                "source_name": "Dr. A",
                "target_id": t_id,
                "target_name": "Dr. B",
                "initiated_by": s_id,
                "source_burden": 15.0,
                "target_burden": 5.0,
                "status": "approved",
            }
        ]
        service.build_from_swap_records(records)
        assert s_id in service.analyzer.nodes
        assert t_id in service.analyzer.nodes

    def test_uses_default_burden(self):
        service = ShadowOrgChartService()
        s_id, t_id = uuid4(), uuid4()
        records = [
            {
                "source_id": s_id,
                "target_id": t_id,
                "initiated_by": s_id,
                "status": "approved",
            }
        ]
        service.build_from_swap_records(records)
        # Default burden is 10.0
        assert service.analyzer.nodes[s_id].burden_offloaded == 10.0

    def test_unsuccessful_status(self):
        service = ShadowOrgChartService()
        s_id, t_id = uuid4(), uuid4()
        records = [
            {
                "source_id": s_id,
                "target_id": t_id,
                "initiated_by": s_id,
                "status": "rejected",
            }
        ]
        service.build_from_swap_records(records)
        assert service.analyzer.nodes[s_id].swap_count == 0


class TestGenerateReport:
    def test_empty_report(self):
        service = ShadowOrgChartService()
        report = service.generate_report(datetime.now(), datetime.now())
        assert report["network_summary"]["total_faculty"] == 0
        assert report["network_summary"]["total_swaps"] == 0

    def test_report_structure(self):
        service = ShadowOrgChartService()
        s_id, t_id = uuid4(), uuid4()
        records = [
            {
                "source_id": s_id,
                "source_name": "Dr. A",
                "target_id": t_id,
                "target_name": "Dr. B",
                "initiated_by": s_id,
                "status": "approved",
            }
        ]
        service.build_from_swap_records(records)
        report = service.generate_report(datetime.now(), datetime.now())
        assert "generated_at" in report
        assert "period" in report
        assert "network_summary" in report
        assert "behavioral_roles" in report
        assert "risk_flags" in report
        assert "recommendations" in report

    def test_with_burden_profiles(self):
        service = ShadowOrgChartService()
        s_id, t_id = uuid4(), uuid4()
        records = [
            {
                "source_id": s_id,
                "source_name": "Dr. A",
                "target_id": t_id,
                "target_name": "Dr. B",
                "initiated_by": s_id,
                "status": "executed",
            }
        ]
        service.build_from_swap_records(records)
        profiles = [
            FacultyBurdenProfile(
                faculty_id=s_id,
                faculty_name="Dr. A",
                period_start=datetime.now(),
                period_end=datetime.now(),
                calculated_at=datetime.now(),
                total_burden=50.0,
                total_hours=40.0,
            ),
            FacultyBurdenProfile(
                faculty_id=t_id,
                faculty_name="Dr. B",
                period_start=datetime.now(),
                period_end=datetime.now(),
                calculated_at=datetime.now(),
                total_burden=60.0,
                total_hours=45.0,
            ),
        ]
        report = service.generate_report(
            datetime.now(), datetime.now(), burden_profiles=profiles
        )
        assert "burden_equity" in report

    def test_appends_to_history(self):
        service = ShadowOrgChartService()
        service.generate_report(datetime.now(), datetime.now())
        service.generate_report(datetime.now(), datetime.now())
        assert len(service.network_history) == 2
