"""
Tests for Behavioral Network module (Shadow Org Chart, Burden Equity).

Tests cover:
1. Burden calculation and weighting
2. Swap network analysis
3. Behavioral role classification
4. Martyr protection
5. Burden equity analysis
"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.resilience.behavioral_network import (
    BehavioralNetworkAnalyzer,
    BehavioralRole,
    BurdenCategory,
    EquityStatus,
    FacultyBurdenProfile,
    ProtectionLevel,
    ShadowOrgChartService,
)


# =============================================================================
# Burden Calculation Tests
# =============================================================================


class TestBurdenCalculation:
    """Tests for shift burden calculation."""

    def test_basic_day_shift(self):
        """Test burden calculation for standard day shift."""
        analyzer = BehavioralNetworkAnalyzer()

        burden = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2024, 1, 15, 8, 0),  # Monday
            shift_type="clinic",
            hours=8.0,
            is_weekend=False,
            is_holiday=False,
            is_night=False,
        )

        assert burden.raw_hours == 8.0
        assert burden.burden_weight < 1.5  # Clinic should be low weight
        assert burden.weighted_burden < 12.0
        assert burden.category in (BurdenCategory.MINIMAL, BurdenCategory.LOW)

    def test_night_shift_high_burden(self):
        """Test night shift has higher burden weight."""
        analyzer = BehavioralNetworkAnalyzer()

        burden = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2024, 1, 15, 20, 0),
            shift_type="inpatient",
            hours=12.0,
            is_weekend=False,
            is_holiday=False,
            is_night=True,
        )

        assert burden.burden_weight > 2.0  # Night modifier
        assert burden.weighted_burden > 24.0
        assert burden.category in (BurdenCategory.HIGH, BurdenCategory.SEVERE)

    def test_weekend_night_extreme_burden(self):
        """Test weekend night shift has extreme burden."""
        analyzer = BehavioralNetworkAnalyzer()

        burden = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2024, 1, 13, 20, 0),  # Saturday
            shift_type="icu",
            hours=12.0,
            is_weekend=True,
            is_holiday=False,
            is_night=True,
        )

        assert burden.burden_weight >= 3.5  # Weekend night combined
        assert burden.weighted_burden >= 42.0
        assert burden.category == BurdenCategory.EXTREME

    def test_holiday_multiplier(self):
        """Test holiday shifts have multiplied burden."""
        analyzer = BehavioralNetworkAnalyzer()

        regular = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2024, 1, 15),
            shift_type="inpatient",
            hours=8.0,
        )

        holiday = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2024, 12, 25),  # Christmas
            shift_type="inpatient",
            hours=8.0,
            is_holiday=True,
        )

        assert holiday.weighted_burden > regular.weighted_burden * 2

    def test_admin_minimal_burden(self):
        """Test admin shifts have minimal burden."""
        analyzer = BehavioralNetworkAnalyzer()

        burden = analyzer.calculate_shift_burden(
            shift_id=uuid4(),
            faculty_id=uuid4(),
            date=datetime(2024, 1, 15),
            shift_type="admin",
            hours=8.0,
        )

        assert burden.burden_weight < 0.5
        assert burden.category == BurdenCategory.MINIMAL


# =============================================================================
***REMOVED*** Burden Profile Tests
# =============================================================================


class TestFacultyBurdenProfile:
    """Tests for faculty burden profile calculation."""

    def test_profile_calculation(self):
        """Test burden profile aggregation."""
        analyzer = BehavioralNetworkAnalyzer()
        faculty_id = uuid4()

        # Create sample shifts
        shifts = [
            analyzer.calculate_shift_burden(
                shift_id=uuid4(),
                faculty_id=faculty_id,
                date=datetime(2024, 1, i),
                shift_type="clinic",
                hours=8.0,
            )
            for i in range(1, 6)
        ]

        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=faculty_id,
            faculty_name="Dr. Test",
            shifts=shifts,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )

        assert profile.total_shifts == 5
        assert profile.total_hours == 40.0
        assert profile.total_burden > 0
        assert "clinic" in profile.shift_breakdown

    def test_equity_status_calculation(self):
        """Test equity status is calculated relative to group."""
        analyzer = BehavioralNetworkAnalyzer()

        # Create profiles with varying burdens
        faculty_id = uuid4()
        shifts = [
            analyzer.calculate_shift_burden(
                shift_id=uuid4(),
                faculty_id=faculty_id,
                date=datetime(2024, 1, i),
                shift_type="icu",
                hours=12.0,
                is_night=True,
            )
            for i in range(1, 11)  # 10 heavy shifts
        ]

        # All faculty burdens (this person is much higher)
        all_burdens = [30, 35, 40, 45, 50, 200]  # Last one is our test faculty

        profile = analyzer.calculate_faculty_burden_profile(
            faculty_id=faculty_id,
            faculty_name="Dr. Overworked",
            shifts=shifts,
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            all_faculty_burdens=all_burdens,
        )

        # Should be flagged as heavy burden
        assert profile.std_devs_from_mean > 1
        assert profile.equity_status in (EquityStatus.HEAVY, EquityStatus.CRUSHING)


# =============================================================================
# Swap Network Analysis Tests
# =============================================================================


class TestSwapNetworkAnalysis:
    """Tests for swap network analysis and role classification."""

    def test_record_swap(self):
        """Test recording a swap in the network."""
        analyzer = BehavioralNetworkAnalyzer()

        source_id = uuid4()
        target_id = uuid4()

        analyzer.record_swap(
            source_id=source_id,
            source_name="Dr. Source",
            target_id=target_id,
            target_name="Dr. Target",
            initiated_by=source_id,
            source_burden=20.0,
            target_burden=0.0,
            was_successful=True,
        )

        assert source_id in analyzer.nodes
        assert target_id in analyzer.nodes
        assert len(analyzer.edges) == 1

        source_node = analyzer.nodes[source_id]
        target_node = analyzer.nodes[target_id]

        assert source_node.requests_made == 1
        assert target_node.requests_received == 1
        assert target_node.burden_absorbed == 20.0

    def test_martyr_classification(self):
        """Test martyr role classification."""
        analyzer = BehavioralNetworkAnalyzer(min_swaps_for_classification=2)

        martyr_id = uuid4()
        others = [uuid4() for _ in range(5)]

        # Record many swaps where martyr absorbs burden from everyone
        for i, other_id in enumerate(others):
            for _ in range(3):
                analyzer.record_swap(
                    source_id=other_id,
                    source_name=f"Dr. Other{i}",
                    target_id=martyr_id,
                    target_name="Dr. Martyr",
                    initiated_by=other_id,
                    source_burden=25.0,  # High burden shifts
                    target_burden=0.0,   # Absorb (no exchange)
                    was_successful=True,
                )

        analysis = analyzer.analyze_network(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )

        # Martyr should be identified
        assert martyr_id in analysis.martyrs
        assert analyzer.nodes[martyr_id].behavioral_role == BehavioralRole.MARTYR

    def test_evader_classification(self):
        """Test evader role classification."""
        analyzer = BehavioralNetworkAnalyzer(min_swaps_for_classification=2)

        evader_id = uuid4()
        others = [uuid4() for _ in range(5)]

        # Record many swaps where evader offloads to everyone
        for i, other_id in enumerate(others):
            for _ in range(3):
                analyzer.record_swap(
                    source_id=evader_id,
                    source_name="Dr. Evader",
                    target_id=other_id,
                    target_name=f"Dr. Other{i}",
                    initiated_by=evader_id,
                    source_burden=30.0,  # Evader offloads high burden
                    target_burden=5.0,   # Gives back low burden
                    was_successful=True,
                )

        analysis = analyzer.analyze_network(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )

        # Evader should be identified
        assert evader_id in analysis.evaders
        assert analyzer.nodes[evader_id].behavioral_role == BehavioralRole.EVADER

    def test_isolate_classification(self):
        """Test isolate role classification (no swaps)."""
        analyzer = BehavioralNetworkAnalyzer()

        isolate_id = uuid4()
        other1 = uuid4()
        other2 = uuid4()

        # Create isolate node but no swaps
        analyzer.nodes[isolate_id] = analyzer.nodes.get(isolate_id) or \
            type('obj', (object,), {
                'faculty_id': isolate_id,
                'faculty_name': 'Dr. Isolate',
                'swap_count': 0,
                'requests_made': 0,
                'requests_received': 0,
            })()

        # Others swap with each other
        analyzer.record_swap(
            source_id=other1,
            source_name="Dr. Other1",
            target_id=other2,
            target_name="Dr. Other2",
            initiated_by=other1,
            source_burden=10.0,
            target_burden=10.0,
            was_successful=True,
        )

        # Force add isolate to nodes for analysis
        from app.resilience.behavioral_network import SwapNetworkNode
        analyzer.nodes[isolate_id] = SwapNetworkNode(
            faculty_id=isolate_id,
            faculty_name="Dr. Isolate",
        )

        analysis = analyzer.analyze_network(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )

        assert isolate_id in analysis.isolates

    def test_network_statistics(self):
        """Test network-level statistics calculation."""
        analyzer = BehavioralNetworkAnalyzer()

        # Create a small network
        faculty = [uuid4() for _ in range(4)]

        # Create some swaps
        analyzer.record_swap(
            source_id=faculty[0],
            source_name="A",
            target_id=faculty[1],
            target_name="B",
            initiated_by=faculty[0],
            source_burden=10.0,
            target_burden=10.0,
            was_successful=True,
        )
        analyzer.record_swap(
            source_id=faculty[1],
            source_name="B",
            target_id=faculty[2],
            target_name="C",
            initiated_by=faculty[1],
            source_burden=10.0,
            target_burden=10.0,
            was_successful=True,
        )

        analysis = analyzer.analyze_network(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )

        assert analysis.total_faculty == 3
        assert analysis.total_swaps == 2
        assert analysis.network_density > 0


# =============================================================================
# Martyr Protection Tests
# =============================================================================


class TestMartyrProtection:
    """Tests for martyr protection feature."""

    def test_martyr_protection_level_high_stress(self):
        """Test martyr gets hard limit at high stress."""
        analyzer = BehavioralNetworkAnalyzer(min_swaps_for_classification=1)

        martyr_id = uuid4()
        other_id = uuid4()

        # Create martyr pattern
        for _ in range(5):
            analyzer.record_swap(
                source_id=other_id,
                source_name="Dr. Other",
                target_id=martyr_id,
                target_name="Dr. Martyr",
                initiated_by=other_id,
                source_burden=30.0,
                target_burden=0.0,
                was_successful=True,
            )

        # Run analysis to classify
        analyzer.analyze_network(
            datetime(2024, 1, 1),
            datetime(2024, 1, 31)
        )

        # Check protection at high stress
        level, reason = analyzer.get_martyr_protection_level(
            martyr_id,
            current_allostatic_load=75.0,
        )

        assert level == ProtectionLevel.HARD_LIMIT
        assert "blocked" in reason.lower()

    def test_should_block_swap_for_martyr(self):
        """Test swap blocking for at-risk martyr."""
        analyzer = BehavioralNetworkAnalyzer(min_swaps_for_classification=1)

        martyr_id = uuid4()
        other_id = uuid4()

        # Create severe burden imbalance
        for _ in range(10):
            analyzer.record_swap(
                source_id=other_id,
                source_name="Dr. Other",
                target_id=martyr_id,
                target_name="Dr. Martyr",
                initiated_by=other_id,
                source_burden=25.0,
                target_burden=0.0,
                was_successful=True,
            )

        analyzer.analyze_network(datetime(2024, 1, 1), datetime(2024, 1, 31))

        # Try to give them another high-burden shift
        should_block, reason = analyzer.should_block_swap(
            target_id=martyr_id,
            source_burden=30.0,
            target_current_load=65.0,
        )

        assert should_block is True
        assert "BLOCKED" in reason

    def test_no_block_for_healthy_faculty(self):
        """Test no blocking for healthy faculty."""
        analyzer = BehavioralNetworkAnalyzer()

        healthy_id = uuid4()

        # No swap history, low stress
        should_block, reason = analyzer.should_block_swap(
            target_id=healthy_id,
            source_burden=20.0,
            target_current_load=30.0,
        )

        assert should_block is False


# =============================================================================
# Burden Equity Analysis Tests
# =============================================================================


class TestBurdenEquityAnalysis:
    """Tests for burden equity analysis."""

    def test_gini_coefficient_equal(self):
        """Test Gini coefficient is low for equal distribution."""
        analyzer = BehavioralNetworkAnalyzer()

        # Create equal burden profiles
        profiles = [
            FacultyBurdenProfile(
                faculty_id=uuid4(),
                faculty_name=f"Dr. {i}",
                period_start=datetime(2024, 1, 1),
                period_end=datetime(2024, 1, 31),
                calculated_at=datetime.now(),
                total_burden=100.0,  # All equal
                total_hours=40.0,
                total_shifts=5,
            )
            for i in range(5)
        ]

        analysis = analyzer.analyze_burden_equity(profiles)

        assert analysis["gini_coefficient"] == 0.0  # Perfect equality
        assert "A" in analysis["equity_grade"]

    def test_gini_coefficient_unequal(self):
        """Test Gini coefficient is high for unequal distribution."""
        analyzer = BehavioralNetworkAnalyzer()

        # Create unequal burden profiles
        burdens = [10, 20, 30, 40, 200]  # Very unequal
        profiles = [
            FacultyBurdenProfile(
                faculty_id=uuid4(),
                faculty_name=f"Dr. {i}",
                period_start=datetime(2024, 1, 1),
                period_end=datetime(2024, 1, 31),
                calculated_at=datetime.now(),
                total_burden=float(burden),
                total_hours=40.0,
                total_shifts=5,
            )
            for i, burden in enumerate(burdens)
        ]

        analysis = analyzer.analyze_burden_equity(profiles)

        assert analysis["gini_coefficient"] > 0.3  # Significant inequality
        assert "D" in analysis["equity_grade"] or "F" in analysis["equity_grade"]

    def test_equity_recommendations_generated(self):
        """Test recommendations are generated for inequity."""
        analyzer = BehavioralNetworkAnalyzer()

        # Create profiles with crushing and very light extremes
        profiles = [
            FacultyBurdenProfile(
                faculty_id=uuid4(),
                faculty_name="Dr. Crushed",
                period_start=datetime(2024, 1, 1),
                period_end=datetime(2024, 1, 31),
                calculated_at=datetime.now(),
                total_burden=300.0,
                total_hours=60.0,
                total_shifts=10,
                equity_status=EquityStatus.CRUSHING,
            ),
            FacultyBurdenProfile(
                faculty_id=uuid4(),
                faculty_name="Dr. Light",
                period_start=datetime(2024, 1, 1),
                period_end=datetime(2024, 1, 31),
                calculated_at=datetime.now(),
                total_burden=20.0,
                total_hours=40.0,
                total_shifts=5,
                equity_status=EquityStatus.VERY_LIGHT,
            ),
        ]

        analysis = analyzer.analyze_burden_equity(profiles)

        assert len(analysis["recommendations"]) > 0
        assert len(analysis["crushing_faculty"]) == 1
        assert len(analysis["very_light_faculty"]) == 1


# =============================================================================
# Shadow Org Chart Service Tests
# =============================================================================


class TestShadowOrgChartService:
    """Tests for shadow org chart service."""

    def test_generate_report(self):
        """Test comprehensive report generation."""
        service = ShadowOrgChartService()

        # Build some network data
        swap_records = [
            {
                "source_id": uuid4(),
                "source_name": "Dr. A",
                "target_id": uuid4(),
                "target_name": "Dr. B",
                "initiated_by": uuid4(),
                "source_burden": 20.0,
                "target_burden": 10.0,
                "status": "executed",
            }
            for _ in range(5)
        ]

        service.build_from_swap_records(swap_records)

        report = service.generate_report(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
        )

        assert "network_summary" in report
        assert "behavioral_roles" in report
        assert "risk_flags" in report
        assert "recommendations" in report

    def test_report_includes_burden_equity(self):
        """Test report includes burden equity when profiles provided."""
        service = ShadowOrgChartService()

        profiles = [
            FacultyBurdenProfile(
                faculty_id=uuid4(),
                faculty_name=f"Dr. {i}",
                period_start=datetime(2024, 1, 1),
                period_end=datetime(2024, 1, 31),
                calculated_at=datetime.now(),
                total_burden=float(50 + i * 10),
                total_hours=40.0,
                total_shifts=5,
            )
            for i in range(5)
        ]

        report = service.generate_report(
            period_start=datetime(2024, 1, 1),
            period_end=datetime(2024, 1, 31),
            burden_profiles=profiles,
        )

        assert "burden_equity" in report
        assert "gini_coefficient" in report["burden_equity"]
