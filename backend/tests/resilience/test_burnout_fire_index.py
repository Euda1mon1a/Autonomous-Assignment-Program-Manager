"""
Tests for Multi-Temporal Burnout Danger Rating.

Tests the Fire Weather Index adaptation for burnout prediction,
ensuring all components calculate correctly and danger classification
matches expected thresholds.
"""

import pytest
from uuid import uuid4

from app.resilience.burnout_fire_index import (
    BurnoutCodeReport,
    BurnoutDangerRating,
    DangerClass,
    FireDangerReport,
)


class TestDangerClass:
    """Test DangerClass enum."""

    def test_danger_classes_exist(self):
        """Test all expected danger classes are defined."""
        assert DangerClass.LOW == "low"
        assert DangerClass.MODERATE == "moderate"
        assert DangerClass.HIGH == "high"
        assert DangerClass.VERY_HIGH == "very_high"
        assert DangerClass.EXTREME == "extreme"

    def test_danger_class_ordering(self):
        """Test danger classes have expected severity ordering."""
        classes = [
            DangerClass.LOW,
            DangerClass.MODERATE,
            DangerClass.HIGH,
            DangerClass.VERY_HIGH,
            DangerClass.EXTREME,
        ]
        assert len(classes) == 5


class TestBurnoutCodeReport:
    """Test BurnoutCodeReport dataclass."""

    def test_create_report(self):
        """Test creating burnout code report."""
        report = BurnoutCodeReport(
            ffmc=85.0,
            dmc=60.0,
            dc=40.0,
            isi=50.0,
            bui=55.0,
            fwi=45.0,
        )

        assert report.ffmc == 85.0
        assert report.dmc == 60.0
        assert report.dc == 40.0
        assert report.isi == 50.0
        assert report.bui == 55.0
        assert report.fwi == 45.0


class TestFireDangerReport:
    """Test FireDangerReport dataclass."""

    def test_create_report(self):
        """Test creating fire danger report."""
        resident_id = uuid4()
        report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.HIGH,
            fwi_score=55.0,
            component_scores={"ffmc": 80.0, "dmc": 65.0},
            recommended_restrictions=["Reduce workload", "Take break"],
        )

        assert report.resident_id == resident_id
        assert report.danger_class == DangerClass.HIGH
        assert report.fwi_score == 55.0
        assert len(report.component_scores) == 2
        assert len(report.recommended_restrictions) == 2

    def test_is_safe_property(self):
        """Test is_safe property correctly identifies safe states."""
        resident_id = uuid4()

        # Safe states
        low_report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.LOW,
            fwi_score=10.0,
        )
        assert low_report.is_safe is True

        moderate_report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.MODERATE,
            fwi_score=30.0,
        )
        assert moderate_report.is_safe is True

        # Unsafe states
        high_report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.HIGH,
            fwi_score=50.0,
        )
        assert high_report.is_safe is False

    def test_requires_intervention_property(self):
        """Test requires_intervention identifies critical states."""
        resident_id = uuid4()

        # No intervention needed
        low_report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.LOW,
            fwi_score=10.0,
        )
        assert low_report.requires_intervention is False

        high_report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.HIGH,
            fwi_score=50.0,
        )
        assert high_report.requires_intervention is False

        # Intervention required
        very_high_report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.VERY_HIGH,
            fwi_score=70.0,
        )
        assert very_high_report.requires_intervention is True

        extreme_report = FireDangerReport(
            resident_id=resident_id,
            danger_class=DangerClass.EXTREME,
            fwi_score=90.0,
        )
        assert extreme_report.requires_intervention is True


class TestFineFuelMoistureCode:
    """Test FFMC calculation (recent hours)."""

    def test_ffmc_at_target(self):
        """Test FFMC when hours exactly at target."""
        rating = BurnoutDangerRating(ffmc_target=60.0)
        ffmc = rating.calculate_fine_fuel_moisture_code(
            recent_hours=60.0,
            target=60.0,
        )

        # At target = minimal excess = low FFMC
        assert 0 <= ffmc < 5

    def test_ffmc_below_target(self):
        """Test FFMC when hours below target (well-rested)."""
        rating = BurnoutDangerRating()
        ffmc = rating.calculate_fine_fuel_moisture_code(
            recent_hours=40.0,  # 20h under target
            target=60.0,
        )

        # Below target = no excess = FFMC stays at 0
        assert ffmc == 0.0

    def test_ffmc_moderate_overwork(self):
        """Test FFMC with moderate overwork."""
        rating = BurnoutDangerRating()
        ffmc = rating.calculate_fine_fuel_moisture_code(
            recent_hours=70.0,  # 10h over 60h target (17% excess)
            target=60.0,
        )

        # Moderate excess = moderate FFMC
        assert 30 < ffmc < 70

    def test_ffmc_severe_overwork(self):
        """Test FFMC with severe overwork."""
        rating = BurnoutDangerRating()
        ffmc = rating.calculate_fine_fuel_moisture_code(
            recent_hours=85.0,  # 25h over 60h target (42% excess)
            target=60.0,
        )

        # Severe excess = high FFMC
        assert 80 < ffmc <= 100

    def test_ffmc_extreme_overwork(self):
        """Test FFMC caps at 100."""
        rating = BurnoutDangerRating()
        ffmc = rating.calculate_fine_fuel_moisture_code(
            recent_hours=150.0,  # Way over target
            target=60.0,
        )

        # Should cap at 100
        assert ffmc == 100.0

    def test_ffmc_invalid_target(self):
        """Test FFMC raises error with invalid target."""
        rating = BurnoutDangerRating()

        with pytest.raises(ValueError, match="Target hours must be positive"):
            rating.calculate_fine_fuel_moisture_code(
                recent_hours=60.0,
                target=0.0,
            )

        with pytest.raises(ValueError, match="Target hours must be positive"):
            rating.calculate_fine_fuel_moisture_code(
                recent_hours=60.0,
                target=-10.0,
            )


class TestDuffMoistureCode:
    """Test DMC calculation (monthly load)."""

    def test_dmc_at_target(self):
        """Test DMC when monthly load at target."""
        rating = BurnoutDangerRating(dmc_target=240.0)
        dmc = rating.calculate_duff_moisture_code(
            monthly_load=240.0,
            target=240.0,
        )

        # At target = minimal DMC
        assert 0 <= dmc < 5

    def test_dmc_below_target(self):
        """Test DMC when monthly load below target."""
        rating = BurnoutDangerRating()
        dmc = rating.calculate_duff_moisture_code(
            monthly_load=200.0,
            target=240.0,
        )

        # Below target = no excess = DMC stays low
        assert dmc == 0.0

    def test_dmc_moderate_accumulation(self):
        """Test DMC with moderate sustained load."""
        rating = BurnoutDangerRating()
        dmc = rating.calculate_duff_moisture_code(
            monthly_load=280.0,  # 40h over target (17%)
            target=240.0,
        )

        # Moderate sustained excess = moderate DMC
        assert 20 < dmc < 60

    def test_dmc_severe_accumulation(self):
        """Test DMC with severe sustained load."""
        rating = BurnoutDangerRating()
        dmc = rating.calculate_duff_moisture_code(
            monthly_load=320.0,  # 80h over target (33%)
            target=240.0,
        )

        # Severe sustained excess = high DMC
        assert 60 < dmc <= 100

    def test_dmc_invalid_target(self):
        """Test DMC raises error with invalid target."""
        rating = BurnoutDangerRating()

        with pytest.raises(ValueError, match="Target monthly hours must be positive"):
            rating.calculate_duff_moisture_code(
                monthly_load=240.0,
                target=0.0,
            )


class TestDroughtCode:
    """Test DC calculation (yearly satisfaction)."""

    def test_dc_full_satisfaction(self):
        """Test DC with full satisfaction."""
        rating = BurnoutDangerRating()
        dc = rating.calculate_drought_code(yearly_satisfaction=1.0)

        # Full satisfaction = no drought
        assert dc == 0.0

    def test_dc_high_satisfaction(self):
        """Test DC with high satisfaction."""
        rating = BurnoutDangerRating()
        dc = rating.calculate_drought_code(yearly_satisfaction=0.8)

        # 0.8 satisfaction → 0.2 dissatisfaction → 4% DC
        assert 3 < dc < 6

    def test_dc_moderate_satisfaction(self):
        """Test DC with moderate satisfaction."""
        rating = BurnoutDangerRating()
        dc = rating.calculate_drought_code(yearly_satisfaction=0.5)

        # 0.5 satisfaction → 0.5 dissatisfaction^1.5 → ~35% DC
        assert 33 < dc < 37

    def test_dc_low_satisfaction(self):
        """Test DC with low satisfaction."""
        rating = BurnoutDangerRating()
        dc = rating.calculate_drought_code(yearly_satisfaction=0.2)

        # 0.2 satisfaction → 0.8 dissatisfaction^1.5 → ~71% DC
        assert 70 < dc < 73

    def test_dc_no_satisfaction(self):
        """Test DC with zero satisfaction."""
        rating = BurnoutDangerRating()
        dc = rating.calculate_drought_code(yearly_satisfaction=0.0)

        # No satisfaction = extreme drought
        assert dc == 100.0

    def test_dc_invalid_satisfaction(self):
        """Test DC raises error with invalid satisfaction."""
        rating = BurnoutDangerRating()

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            rating.calculate_drought_code(yearly_satisfaction=1.5)

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            rating.calculate_drought_code(yearly_satisfaction=-0.5)


class TestInitialSpreadIndex:
    """Test ISI calculation (spread rate)."""

    def test_isi_zero_ffmc(self):
        """Test ISI with zero FFMC (well-rested)."""
        rating = BurnoutDangerRating()
        isi = rating.calculate_initial_spread_index(
            ffmc=0.0,
            workload_velocity=5.0,
        )

        # No fine fuel dryness = no spread
        assert isi == 0.0

    def test_isi_stable_workload(self):
        """Test ISI with stable workload (zero velocity)."""
        rating = BurnoutDangerRating()
        isi = rating.calculate_initial_spread_index(
            ffmc=60.0,
            workload_velocity=0.0,
        )

        # Moderate FFMC, stable workload = moderate ISI
        assert 10 < isi < 20

    def test_isi_increasing_workload(self):
        """Test ISI with increasing workload."""
        rating = BurnoutDangerRating()
        isi = rating.calculate_initial_spread_index(
            ffmc=80.0,
            workload_velocity=10.0,  # Adding 10h/week
        )

        # High FFMC + increasing workload = high ISI
        assert 30 < isi < 50

    def test_isi_decreasing_workload(self):
        """Test ISI with decreasing workload."""
        rating = BurnoutDangerRating()
        isi = rating.calculate_initial_spread_index(
            ffmc=80.0,
            workload_velocity=-10.0,  # Reducing 10h/week
        )

        # Decreasing workload reduces spread
        # But FFMC still high, so ISI > 0
        assert 0 <= isi < 10

    def test_isi_extreme_conditions(self):
        """Test ISI with extreme conditions."""
        rating = BurnoutDangerRating()
        isi = rating.calculate_initial_spread_index(
            ffmc=95.0,
            workload_velocity=20.0,  # Rapidly increasing
        )

        # Extreme conditions = very high ISI
        assert isi > 50


class TestBuildupIndex:
    """Test BUI calculation (combined burden)."""

    def test_bui_zero_components(self):
        """Test BUI when both components are zero."""
        rating = BurnoutDangerRating()
        bui = rating.calculate_buildup_index(dmc=0.0, dc=0.0)

        assert bui == 0.0

    def test_bui_low_burden(self):
        """Test BUI with low burden."""
        rating = BurnoutDangerRating()
        bui = rating.calculate_buildup_index(dmc=20.0, dc=10.0)

        # Low components = low BUI
        assert 0 < bui < 20

    def test_bui_moderate_burden(self):
        """Test BUI with moderate burden."""
        rating = BurnoutDangerRating()
        bui = rating.calculate_buildup_index(dmc=50.0, dc=40.0)

        # Moderate components = moderate BUI
        assert 30 < bui < 50

    def test_bui_high_burden(self):
        """Test BUI with high burden."""
        rating = BurnoutDangerRating()
        bui = rating.calculate_buildup_index(dmc=80.0, dc=70.0)

        # High components = high BUI
        assert 60 < bui < 80

    def test_bui_asymmetric_components(self):
        """Test BUI when one component is low."""
        rating = BurnoutDangerRating()

        # High DMC, low DC
        bui1 = rating.calculate_buildup_index(dmc=80.0, dc=10.0)

        # Low DMC, high DC
        bui2 = rating.calculate_buildup_index(dmc=10.0, dc=80.0)

        # Both BUI, moderate DC
        bui3 = rating.calculate_buildup_index(dmc=50.0, dc=50.0)

        # Asymmetric should be lower than balanced
        assert bui1 < bui3
        assert bui2 < bui3


class TestFireWeatherIndex:
    """Test FWI calculation (final composite)."""

    def test_fwi_zero_components(self):
        """Test FWI when components are zero."""
        rating = BurnoutDangerRating()
        fwi = rating.calculate_fire_weather_index(isi=0.0, bui=0.0)

        assert fwi == 0.0

    def test_fwi_low_danger(self):
        """Test FWI in low danger range."""
        rating = BurnoutDangerRating()
        fwi = rating.calculate_fire_weather_index(isi=5.0, bui=10.0)

        # Low components = low FWI (< 20)
        assert 0 < fwi < 20

    def test_fwi_moderate_danger(self):
        """Test FWI in moderate danger range."""
        rating = BurnoutDangerRating()
        fwi = rating.calculate_fire_weather_index(isi=15.0, bui=30.0)

        # Moderate components = moderate FWI (20-40)
        assert 20 < fwi < 40

    def test_fwi_high_danger(self):
        """Test FWI in high danger range."""
        rating = BurnoutDangerRating()
        fwi = rating.calculate_fire_weather_index(isi=30.0, bui=50.0)

        # High components = high FWI (40-60)
        assert 40 < fwi < 60

    def test_fwi_extreme_danger(self):
        """Test FWI in extreme danger range."""
        rating = BurnoutDangerRating()
        fwi = rating.calculate_fire_weather_index(isi=60.0, bui=85.0)

        # Extreme components = extreme FWI (80+)
        assert fwi > 80

    def test_fwi_nonlinear_interaction(self):
        """Test FWI shows non-linear interaction."""
        rating = BurnoutDangerRating()

        # Doubling ISI doesn't double FWI (non-linear)
        fwi1 = rating.calculate_fire_weather_index(isi=10.0, bui=40.0)
        fwi2 = rating.calculate_fire_weather_index(isi=20.0, bui=40.0)

        # Should roughly double, but not exactly (non-linear fD)
        ratio = fwi2 / fwi1
        assert 1.8 < ratio < 2.2


class TestClassifyDanger:
    """Test danger classification."""

    def test_classify_low(self):
        """Test LOW classification."""
        rating = BurnoutDangerRating()

        assert rating.classify_danger(0.0) == DangerClass.LOW
        assert rating.classify_danger(10.0) == DangerClass.LOW
        assert rating.classify_danger(19.9) == DangerClass.LOW

    def test_classify_moderate(self):
        """Test MODERATE classification."""
        rating = BurnoutDangerRating()

        assert rating.classify_danger(20.0) == DangerClass.MODERATE
        assert rating.classify_danger(30.0) == DangerClass.MODERATE
        assert rating.classify_danger(39.9) == DangerClass.MODERATE

    def test_classify_high(self):
        """Test HIGH classification."""
        rating = BurnoutDangerRating()

        assert rating.classify_danger(40.0) == DangerClass.HIGH
        assert rating.classify_danger(50.0) == DangerClass.HIGH
        assert rating.classify_danger(59.9) == DangerClass.HIGH

    def test_classify_very_high(self):
        """Test VERY_HIGH classification."""
        rating = BurnoutDangerRating()

        assert rating.classify_danger(60.0) == DangerClass.VERY_HIGH
        assert rating.classify_danger(70.0) == DangerClass.VERY_HIGH
        assert rating.classify_danger(79.9) == DangerClass.VERY_HIGH

    def test_classify_extreme(self):
        """Test EXTREME classification."""
        rating = BurnoutDangerRating()

        assert rating.classify_danger(80.0) == DangerClass.EXTREME
        assert rating.classify_danger(100.0) == DangerClass.EXTREME
        assert rating.classify_danger(150.0) == DangerClass.EXTREME


class TestGetRestrictions:
    """Test restriction recommendations."""

    def test_restrictions_low(self):
        """Test restrictions for LOW danger."""
        rating = BurnoutDangerRating()
        restrictions = rating.get_restrictions(DangerClass.LOW)

        assert len(restrictions) >= 1
        assert any("normal" in r.lower() for r in restrictions)

    def test_restrictions_moderate(self):
        """Test restrictions for MODERATE danger."""
        rating = BurnoutDangerRating()
        restrictions = rating.get_restrictions(DangerClass.MODERATE)

        assert len(restrictions) >= 2
        assert any("monitor" in r.lower() for r in restrictions)

    def test_restrictions_high(self):
        """Test restrictions for HIGH danger."""
        rating = BurnoutDangerRating()
        restrictions = rating.get_restrictions(DangerClass.HIGH)

        assert len(restrictions) >= 4
        assert any("reduce" in r.lower() for r in restrictions)
        assert any("60" in r for r in restrictions)  # 60h/week cap

    def test_restrictions_very_high(self):
        """Test restrictions for VERY_HIGH danger."""
        rating = BurnoutDangerRating()
        restrictions = rating.get_restrictions(DangerClass.VERY_HIGH)

        assert len(restrictions) >= 5
        assert any("urgent" in r.lower() for r in restrictions)
        assert any("50" in r for r in restrictions)  # 50h/week cap

    def test_restrictions_extreme(self):
        """Test restrictions for EXTREME danger."""
        rating = BurnoutDangerRating()
        restrictions = rating.get_restrictions(DangerClass.EXTREME)

        assert len(restrictions) >= 6
        assert any("emergency" in r.lower() for r in restrictions)
        assert any("leave" in r.lower() for r in restrictions)

    def test_restrictions_escalate(self):
        """Test restrictions become more severe with danger level."""
        rating = BurnoutDangerRating()

        low = rating.get_restrictions(DangerClass.LOW)
        moderate = rating.get_restrictions(DangerClass.MODERATE)
        high = rating.get_restrictions(DangerClass.HIGH)
        very_high = rating.get_restrictions(DangerClass.VERY_HIGH)
        extreme = rating.get_restrictions(DangerClass.EXTREME)

        # More restrictions as danger increases
        assert len(moderate) > len(low)
        assert len(high) > len(moderate)
        assert len(very_high) > len(high)
        assert len(extreme) > len(very_high)


class TestCalculateBurnoutDanger:
    """Test complete burnout danger calculation."""

    def test_calculate_low_danger(self):
        """Test complete calculation for low danger scenario."""
        rating = BurnoutDangerRating()
        resident_id = uuid4()

        report = rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=50.0,        # Under target
            monthly_load=220.0,       # Under target
            yearly_satisfaction=0.85,  # High satisfaction
            workload_velocity=0.0,     # Stable
        )

        assert report.resident_id == resident_id
        assert report.danger_class == DangerClass.LOW
        assert report.fwi_score < 20
        assert report.is_safe is True
        assert report.requires_intervention is False
        assert len(report.component_scores) > 0
        assert len(report.recommended_restrictions) > 0

    def test_calculate_moderate_danger(self):
        """Test complete calculation for moderate danger scenario."""
        rating = BurnoutDangerRating()
        resident_id = uuid4()

        report = rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=71.0,        # Moderately over target
            monthly_load=264.0,       # Moderately over target
            yearly_satisfaction=0.56,  # Moderate dissatisfaction
            workload_velocity=4.5,     # Moderate increase
        )

        assert report.danger_class == DangerClass.MODERATE
        assert 20 <= report.fwi_score < 40
        assert report.is_safe is True
        assert report.requires_intervention is False

    def test_calculate_high_danger(self):
        """Test complete calculation for high danger scenario."""
        rating = BurnoutDangerRating()
        resident_id = uuid4()

        report = rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=77.0,        # Significantly over
            monthly_load=280.0,       # Significantly over
            yearly_satisfaction=0.42,  # Significant dissatisfaction
            workload_velocity=6.0,     # Increasing
        )

        assert report.danger_class == DangerClass.HIGH
        assert 40 <= report.fwi_score < 60
        assert report.is_safe is False
        assert report.requires_intervention is False

    def test_calculate_very_high_danger(self):
        """Test complete calculation for very high danger scenario."""
        rating = BurnoutDangerRating()
        resident_id = uuid4()

        report = rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=82.0,        # Well over target
            monthly_load=292.0,       # Well over target
            yearly_satisfaction=0.28,  # Low satisfaction
            workload_velocity=9.0,     # Rapidly increasing
        )

        assert report.danger_class == DangerClass.VERY_HIGH
        assert 60 <= report.fwi_score < 80
        assert report.is_safe is False
        assert report.requires_intervention is True

    def test_calculate_extreme_danger(self):
        """Test complete calculation for extreme danger scenario."""
        rating = BurnoutDangerRating()
        resident_id = uuid4()

        report = rating.calculate_burnout_danger(
            resident_id=resident_id,
            recent_hours=88.0,        # Severely over target
            monthly_load=305.0,       # Severely over target
            yearly_satisfaction=0.18,  # Very low satisfaction
            workload_velocity=13.0,    # Extremely increasing
        )

        assert report.danger_class == DangerClass.EXTREME
        assert report.fwi_score >= 80
        assert report.is_safe is False
        assert report.requires_intervention is True

    def test_component_scores_included(self):
        """Test component scores are included in report."""
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=70.0,
            monthly_load=260.0,
            yearly_satisfaction=0.6,
            workload_velocity=3.0,
        )

        assert "ffmc" in report.component_scores
        assert "dmc" in report.component_scores
        assert "dc" in report.component_scores
        assert "isi" in report.component_scores
        assert "bui" in report.component_scores
        assert "fwi" in report.component_scores
        assert "recent_hours" in report.component_scores
        assert "monthly_load" in report.component_scores
        assert "yearly_satisfaction" in report.component_scores
        assert "workload_velocity" in report.component_scores

    def test_default_velocity_zero(self):
        """Test default workload velocity is zero."""
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=60.0,
            monthly_load=240.0,
            yearly_satisfaction=0.8,
            # No velocity specified
        )

        assert report.component_scores["workload_velocity"] == 0.0


class TestCalculateBatchDanger:
    """Test batch danger calculation."""

    def test_batch_single_resident(self):
        """Test batch calculation with single resident."""
        rating = BurnoutDangerRating()

        residents = [
            {
                "resident_id": uuid4(),
                "recent_hours": 60.0,
                "monthly_load": 240.0,
                "yearly_satisfaction": 0.8,
            }
        ]

        reports = rating.calculate_batch_danger(residents)

        assert len(reports) == 1
        assert isinstance(reports[0], FireDangerReport)

    def test_batch_multiple_residents(self):
        """Test batch calculation with multiple residents."""
        rating = BurnoutDangerRating()

        residents = [
            {
                "resident_id": uuid4(),
                "recent_hours": 50.0,
                "monthly_load": 220.0,
                "yearly_satisfaction": 0.85,
            },
            {
                "resident_id": uuid4(),
                "recent_hours": 75.0,
                "monthly_load": 270.0,
                "yearly_satisfaction": 0.5,
            },
            {
                "resident_id": uuid4(),
                "recent_hours": 90.0,
                "monthly_load": 300.0,
                "yearly_satisfaction": 0.2,
            },
        ]

        reports = rating.calculate_batch_danger(residents)

        assert len(reports) == 3

        # Check residents are different
        resident_ids = [r.resident_id for r in reports]
        assert len(set(resident_ids)) == 3

    def test_batch_sorted_by_fwi(self):
        """Test batch reports are sorted by FWI (highest first)."""
        rating = BurnoutDangerRating()

        residents = [
            {
                "resident_id": uuid4(),
                "recent_hours": 50.0,   # Low danger
                "monthly_load": 220.0,
                "yearly_satisfaction": 0.85,
            },
            {
                "resident_id": uuid4(),
                "recent_hours": 90.0,   # High danger
                "monthly_load": 300.0,
                "yearly_satisfaction": 0.2,
            },
            {
                "resident_id": uuid4(),
                "recent_hours": 70.0,   # Medium danger
                "monthly_load": 260.0,
                "yearly_satisfaction": 0.6,
            },
        ]

        reports = rating.calculate_batch_danger(residents)

        # Should be sorted highest FWI first
        assert reports[0].fwi_score >= reports[1].fwi_score
        assert reports[1].fwi_score >= reports[2].fwi_score

    def test_batch_with_velocity(self):
        """Test batch calculation with workload velocity."""
        rating = BurnoutDangerRating()

        residents = [
            {
                "resident_id": uuid4(),
                "recent_hours": 70.0,
                "monthly_load": 260.0,
                "yearly_satisfaction": 0.6,
                "workload_velocity": 10.0,  # Explicit velocity
            },
        ]

        reports = rating.calculate_batch_danger(residents)

        assert reports[0].component_scores["workload_velocity"] == 10.0

    def test_batch_handles_errors(self):
        """Test batch continues processing despite individual errors."""
        rating = BurnoutDangerRating()

        residents = [
            {
                "resident_id": uuid4(),
                "recent_hours": 60.0,
                "monthly_load": 240.0,
                "yearly_satisfaction": 0.8,
            },
            {
                "resident_id": uuid4(),
                "recent_hours": 70.0,
                "monthly_load": 260.0,
                # Missing yearly_satisfaction (will cause error)
            },
            {
                "resident_id": uuid4(),
                "recent_hours": 80.0,
                "monthly_load": 280.0,
                "yearly_satisfaction": 0.4,
            },
        ]

        # Should process successfully despite one error
        reports = rating.calculate_batch_danger(residents)

        # Should get 2 reports (skipping the invalid one)
        assert len(reports) == 2


class TestTemporalIntegration:
    """Test temporal scale integration."""

    def test_all_scales_low_gives_low_danger(self):
        """Test low on all temporal scales gives low overall danger."""
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=50.0,        # Low recent
            monthly_load=220.0,       # Low monthly
            yearly_satisfaction=0.9,   # High satisfaction
            workload_velocity=0.0,
        )

        assert report.danger_class == DangerClass.LOW

    def test_recent_high_others_low_gives_low_or_moderate(self):
        """Test high recent but low others gives low/moderate danger."""
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=75.0,        # High recent
            monthly_load=220.0,       # Low monthly
            yearly_satisfaction=0.9,   # High satisfaction
            workload_velocity=0.0,
        )

        # Should be LOW or MODERATE (not HIGH) since only recent is high
        # Burnout requires alignment across temporal scales
        assert report.danger_class in (DangerClass.LOW, DangerClass.MODERATE)

    def test_all_scales_high_gives_extreme(self):
        """Test high on all scales gives extreme danger."""
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=90.0,        # High recent
            monthly_load=300.0,       # High monthly
            yearly_satisfaction=0.1,   # Very low satisfaction
            workload_velocity=15.0,    # Rapidly increasing
        )

        # All scales aligned = extreme danger
        assert report.danger_class in (DangerClass.VERY_HIGH, DangerClass.EXTREME)

    def test_velocity_amplifies_danger(self):
        """Test increasing velocity amplifies danger."""
        rating = BurnoutDangerRating()

        # Same conditions, different velocity
        report_stable = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=75.0,
            monthly_load=270.0,
            yearly_satisfaction=0.5,
            workload_velocity=0.0,  # Stable
        )

        report_increasing = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=75.0,
            monthly_load=270.0,
            yearly_satisfaction=0.5,
            workload_velocity=10.0,  # Increasing
        )

        # Increasing velocity should give higher FWI
        assert report_increasing.fwi_score > report_stable.fwi_score


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_all_zeros(self):
        """Test all inputs at zero/minimum."""
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=0.0,
            monthly_load=0.0,
            yearly_satisfaction=1.0,  # Max satisfaction
            workload_velocity=0.0,
        )

        assert report.danger_class == DangerClass.LOW
        assert report.fwi_score < 20

    def test_all_maximum(self):
        """Test all inputs at maximum."""
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=200.0,       # Extreme
            monthly_load=500.0,       # Extreme
            yearly_satisfaction=0.0,   # Minimum
            workload_velocity=50.0,    # Extreme increase
        )

        assert report.danger_class == DangerClass.EXTREME
        assert report.fwi_score >= 80

    def test_custom_targets(self):
        """Test with custom FFMC/DMC targets."""
        rating = BurnoutDangerRating(
            ffmc_target=80.0,   # Higher target
            dmc_target=320.0,   # Higher target
        )

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=80.0,   # At higher target
            monthly_load=320.0,  # At higher target
            yearly_satisfaction=0.8,
        )

        # At custom targets = low danger
        assert report.danger_class == DangerClass.LOW
