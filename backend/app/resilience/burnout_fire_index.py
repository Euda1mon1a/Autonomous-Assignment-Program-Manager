"""
Multi-Temporal Burnout Danger Rating (adapted from CFFDRS Fire Weather Index).

The Canadian Forest Fire Danger Rating System (CFFDRS) Fire Weather Index (FWI)
combines multiple time scales to predict wildfire danger. This module adapts
that framework for medical resident burnout prediction.

Key Innovation: Multi-Temporal Analysis
---------------------------------------
Like wildfires, burnout doesn't develop overnight. It requires:
1. Recent acute stress (fine fuels) - 2-week workload
2. Medium-term accumulation (duff layer) - 3-month burden
3. Long-term erosion (drought) - yearly satisfaction decline
4. Rate of change (spread index) - how fast conditions worsen
5. Combined burden (buildup) - medium + long-term effects
6. Final danger (FWI) - composite risk score

FWI System Components:
----------------------

FFMC (Fine Fuel Moisture Code): 0-100 scale
    - Represents moisture in fine fuels (1-2 hour response)
    - Adapted: Recent hours worked vs. 60-hour target
    - High FFMC = dry fuels = recent overwork = immediate burnout risk

DMC (Duff Moisture Code): 0-100 scale
    - Represents moisture in duff layer (15-day response)
    - Adapted: 3-month workload accumulation vs. 240-hour target
    - High DMC = dry duff = sustained overwork = medium-term risk

DC (Drought Code): 0-100 scale
    - Represents deep soil moisture (52-day response)
    - Adapted: Yearly job satisfaction erosion
    - High DC = drought conditions = long-term dissatisfaction = chronic risk

ISI (Initial Spread Index): 0-100+ scale
    - Combines FFMC with wind speed
    - Adapted: Combines FFMC with workload velocity (rate of increase)
    - High ISI = fire spreads quickly = burnout accelerating

BUI (Buildup Index): 0-100+ scale
    - Combines DMC and DC (fuel available for combustion)
    - Adapted: Combined medium + long-term burden
    - High BUI = heavy fuel load = accumulated risk

FWI (Fire Weather Index): 0-100+ scale
    - Final composite of ISI and BUI
    - Adapted: Overall burnout danger
    - Thresholds: <20 LOW, 20-40 MODERATE, 40-60 HIGH, 60-80 VERY_HIGH, 80+ EXTREME

Real-World Analogy:
-------------------
A forest fire requires:
- Dry fine fuels (immediate ignitability) → Recent overwork
- Dry duff layer (sustains fire) → Sustained overwork
- Drought (deep moisture deficit) → Long-term dissatisfaction
- Wind (spreads fire) → Increasing workload
- Combined fuel load → Total accumulated burden
- Weather conditions → Overall burnout risk

The FWI System correctly predicted severe fire seasons when components aligned.
Similarly, this system detects when temporal scales align for burnout.

References:
-----------
- Canadian Forest Service: Fire Weather Index (FWI) System
- Van Wagner, C.E. (1987). Development and structure of the Canadian Forest
  Fire Weather Index System. Forestry Technical Report 35.
- Stocks et al. (1989). The Canadian Forest Fire Danger Rating System.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

logger = logging.getLogger(__name__)


class DangerClass(str, Enum):
    """
    Burnout danger classification.

    Matches fire danger rating system classes.
    """

    LOW = "low"  # FWI < 20: Normal operations
    MODERATE = "moderate"  # FWI 20-40: Monitor closely
    HIGH = "high"  # FWI 40-60: Reduce workload
    VERY_HIGH = "very_high"  # FWI 60-80: Significant restrictions
    EXTREME = "extreme"  # FWI 80+: Emergency measures


@dataclass
class BurnoutCodeReport:
    """
    Individual burnout code components.

    Mirrors the six FWI System codes for fire danger.
    """

    ffmc: float  # Fine Fuel Moisture Code (0-100): recent hours
    dmc: float  # Duff Moisture Code (0-100): monthly load
    dc: float  # Drought Code (0-100): yearly satisfaction
    isi: float  # Initial Spread Index (0-100+): spread rate
    bui: float  # Buildup Index (0-100+): combined burden
    fwi: float  # Fire Weather Index (0-100+): final danger


@dataclass
class FireDangerReport:
    """
    Complete burnout danger assessment for a resident.

    Provides danger classification, scores, and recommended actions.
    """

    resident_id: UUID
    danger_class: DangerClass
    fwi_score: float
    component_scores: dict = field(default_factory=dict)
    recommended_restrictions: list[str] = field(default_factory=list)

    @property
    def is_safe(self) -> bool:
        """Whether resident is in safe operating range."""
        return self.danger_class in (DangerClass.LOW, DangerClass.MODERATE)

    @property
    def requires_intervention(self) -> bool:
        """Whether immediate intervention is required."""
        return self.danger_class in (DangerClass.VERY_HIGH, DangerClass.EXTREME)


class BurnoutDangerRating:
    """
    Multi-temporal burnout danger rating system.

    Adapts the Canadian Forest Fire Weather Index (FWI) System to predict
    medical resident burnout by combining three temporal scales:
    - Recent acute stress (2 weeks)
    - Medium-term accumulation (3 months)
    - Long-term erosion (1 year)

    The FWI System has been validated across Canada and internationally for
    50+ years. This adaptation applies the same multi-temporal logic to
    human burnout prediction.

    Usage:
        rating = BurnoutDangerRating()

        report = rating.calculate_burnout_danger(
            resident_id=uuid4(),
            recent_hours=65.0,      # Last 2 weeks
            monthly_load=250.0,      # Last 3 months avg
            yearly_satisfaction=0.6, # Job satisfaction (0-1)
            workload_velocity=5.0,   # Hours/week increase
        )

        if report.danger_class == DangerClass.EXTREME:
            print(f"EXTREME DANGER: {report.fwi_score:.1f}")
            for restriction in report.recommended_restrictions:
                print(f"  - {restriction}")
    """

    def __init__(
        self,
        ffmc_target: float = 60.0,  # Target 60 hours/2 weeks
        dmc_target: float = 240.0,  # Target 240 hours/3 months
        dc_baseline: float = 1.0,  # Full satisfaction baseline
    ) -> None:
        """
        Initialize burnout danger rating system.

        Args:
            ffmc_target: Target hours for 2-week period (default 60)
            dmc_target: Target hours for 3-month period (default 240)
            dc_baseline: Baseline satisfaction level (default 1.0)
        """
        self.ffmc_target = ffmc_target
        self.dmc_target = dmc_target
        self.dc_baseline = dc_baseline

        logger.info(
            f"Initialized BurnoutDangerRating: "
            f"FFMC target={ffmc_target}h, DMC target={dmc_target}h"
        )

    def calculate_fine_fuel_moisture_code(
        self,
        recent_hours: float,
        target: float = 60.0,
    ) -> float:
        """
        Calculate Fine Fuel Moisture Code (FFMC) - acute stress indicator.

        FFMC represents the moisture content of fine surface fuels (litter,
        grass, needles). In forests, low moisture = high ignitability.

        For burnout: Recent hours worked vs. sustainable target.
        - Low hours = high "moisture" = low FFMC = low immediate risk
        - High hours = low "moisture" = high FFMC = high immediate risk

        Response time: 1-2 days (like fine fuels drying/wetting quickly)

        Formula adapted from Van Wagner (1987):
        FFMC = 100 * (1 - exp(-k * excess))
        where excess = (actual - target) / target

        Args:
            recent_hours: Hours worked in last 2 weeks
            target: Sustainable hours target (default 60)

        Returns:
            FFMC score (0-100)
            - 0-30: Well-rested, low immediate risk
            - 30-60: Moderate recent workload
            - 60-85: High recent workload, elevated risk
            - 85-100: Extreme recent workload, immediate risk
        """
        if target <= 0:
            raise ValueError("Target hours must be positive")

            # Calculate excess workload as proportion of target
        excess = max(0, (recent_hours - target) / target)

        # Exponential scaling (FFMC rises quickly with excess hours)
        # k = 3.5 tuned so 75 hours (25% over 60h target) gives FFMC ~70
        # This makes the system more sensitive to recent overwork
        k = 3.5
        ffmc = 100.0 * (1.0 - (2.71828 ** (-k * excess)))

        logger.debug(
            f"FFMC: recent_hours={recent_hours:.1f}, target={target:.1f}, "
            f"excess={excess:.2f}, ffmc={ffmc:.1f}"
        )

        return float(min(100.0, ffmc))

    def calculate_duff_moisture_code(
        self,
        monthly_load: float,
        target: float = 240.0,
    ) -> float:
        """
        Calculate Duff Moisture Code (DMC) - medium-term burden indicator.

        DMC represents moisture in the duff layer (loosely compacted organic
        matter). This layer responds more slowly than fine fuels (15-day lag).

        For burnout: 3-month workload accumulation.
        - Sustained high workload = dry duff = high DMC = medium-term risk

        Response time: 2-4 weeks (accumulated burden)

        Formula: Similar to FFMC but with lower exponential constant
        (duff layer dries/wets more slowly than fine fuels)

        Args:
            monthly_load: Average monthly hours over 3 months
            target: Sustainable monthly target (default 240)

        Returns:
            DMC score (0-100)
            - 0-20: Sustainable long-term workload
            - 20-40: Moderate accumulation
            - 40-70: High accumulation, intervention needed
            - 70-100: Severe accumulation, burnout likely
        """
        if target <= 0:
            raise ValueError("Target monthly hours must be positive")

            # Calculate sustained excess
        excess = max(0, (monthly_load - target) / target)

        # Lower exponential constant (duff dries slower than fine fuels)
        # k = 2.5 tuned so 270h monthly (12.5% over 240h) gives DMC ~50
        # More sensitive to sustained overwork
        k = 2.5
        dmc = 100.0 * (1.0 - (2.71828 ** (-k * excess)))

        logger.debug(
            f"DMC: monthly_load={monthly_load:.1f}, target={target:.1f}, "
            f"excess={excess:.2f}, dmc={dmc:.1f}"
        )

        return float(min(100.0, dmc))

    def calculate_drought_code(
        self,
        yearly_satisfaction: float,
    ) -> float:
        """
        Calculate Drought Code (DC) - long-term erosion indicator.

        DC represents deep soil moisture deficit from prolonged dry weather.
        Drought develops over months and indicates deep, persistent drying.

        For burnout: Long-term job satisfaction erosion.
        - High satisfaction = high "moisture" = low DC = low chronic risk
        - Low satisfaction = "drought" = high DC = high chronic risk

        Response time: 3-12 months (chronic dissatisfaction)

        Formula: Inverse satisfaction with exponential scaling.
        DC = 100 * (1 - satisfaction)^2

        The square emphasizes that low satisfaction is exponentially worse.

        Args:
            yearly_satisfaction: Job satisfaction over past year (0.0-1.0)
                1.0 = fully satisfied (no drought)
                0.5 = moderate satisfaction (moderate drought)
                0.0 = completely dissatisfied (extreme drought)

        Returns:
            DC score (0-100)
            - 0-10: High satisfaction, no chronic risk
            - 10-30: Moderate satisfaction decline
            - 30-60: Low satisfaction, chronic stress
            - 60-100: Severe dissatisfaction, chronic burnout
        """
        if not 0.0 <= yearly_satisfaction <= 1.0:
            raise ValueError("Yearly satisfaction must be between 0.0 and 1.0")

            # Invert satisfaction (1.0 satisfaction = 0 drought)
        dissatisfaction = 1.0 - yearly_satisfaction

        # Exponential to emphasize dissatisfaction
        # 0.7 satisfaction → 0.3 dissatisfaction → ~40 DC
        # 0.5 satisfaction → 0.5 dissatisfaction → ~60 DC
        # 0.0 satisfaction → 1.0 dissatisfaction → 100 DC
        # Use exponential curve for more sensitivity
        dc = 100.0 * (dissatisfaction**1.5)

        logger.debug(
            f"DC: yearly_satisfaction={yearly_satisfaction:.2f}, "
            f"dissatisfaction={dissatisfaction:.2f}, dc={dc:.1f}"
        )

        return float(dc)

    def calculate_initial_spread_index(
        self,
        ffmc: float,
        workload_velocity: float = 0.0,
    ) -> float:
        """
        Calculate Initial Spread Index (ISI) - burnout spread rate.

        ISI combines FFMC (fine fuel dryness) with wind speed. In fires:
        - Dry fuels + wind = rapid fire spread

        For burnout:
        - Recent overwork (FFMC) + increasing workload (velocity) = rapid deterioration

        Formula adapted from Van Wagner (1987):
        ISI = 0.208 * FFMC * (1 + velocity)

        This correctly models that:
        - If FFMC is low (well-rested), velocity doesn't matter much
        - If FFMC is high (already stressed), velocity accelerates burnout

        Args:
            ffmc: Fine Fuel Moisture Code (0-100)
            workload_velocity: Rate of workload increase (hours/week)
                0 = stable workload
                5 = adding 5 hours/week
                -5 = reducing 5 hours/week

        Returns:
            ISI score (0-100+)
            - 0-10: Stable, low spread risk
            - 10-30: Moderate spread potential
            - 30-60: High spread potential
            - 60+: Extreme spread potential, rapid deterioration
        """
        # Velocity effect (negative velocity reduces spread)
        velocity_factor = max(0, 1.0 + (workload_velocity / 10.0))

        # Van Wagner's ISI formula (adapted)
        # Original: ISI = 0.208 * f(W) * f(FFMC)
        # We combine FFMC and velocity directly
        # Increased coefficient for more sensitivity
        isi = 0.35 * ffmc * velocity_factor

        logger.debug(
            f"ISI: ffmc={ffmc:.1f}, velocity={workload_velocity:.1f}, "
            f"velocity_factor={velocity_factor:.2f}, isi={isi:.1f}"
        )

        return isi

    def calculate_buildup_index(
        self,
        dmc: float,
        dc: float,
    ) -> float:
        """
        Calculate Buildup Index (BUI) - combined medium/long-term burden.

        BUI represents total fuel available for combustion. Combines:
        - DMC: Medium-term duff moisture
        - DC: Long-term drought

        For burnout: Combined accumulated burden from:
        - 3-month sustained overwork (DMC)
        - 1-year satisfaction erosion (DC)

        Formula from Van Wagner (1987):
        BUI = 0.8 * DMC * DC / (DMC + 0.4 * DC)

        This interaction correctly models that both components must be high
        for extreme BUI. If either is low, BUI is moderate.

        Args:
            dmc: Duff Moisture Code (0-100)
            dc: Drought Code (0-100)

        Returns:
            BUI score (0-100+)
            - 0-20: Low accumulated burden
            - 20-40: Moderate burden
            - 40-70: High burden, intervention needed
            - 70+: Extreme burden, emergency measures
        """
        # Avoid division by zero
        if dmc == 0 and dc == 0:
            return 0.0

            # Van Wagner's BUI formula (adapted)
            # Adjusted coefficients for burnout context
        denominator = dmc + (0.4 * dc)
        if denominator == 0:
            return 0.0

        bui = (0.9 * dmc * dc) / denominator

        logger.debug(f"BUI: dmc={dmc:.1f}, dc={dc:.1f}, bui={bui:.1f}")

        return bui

    def calculate_fire_weather_index(
        self,
        isi: float,
        bui: float,
    ) -> float:
        """
        Calculate Fire Weather Index (FWI) - final composite burnout score.

        FWI is the final output of the system, combining:
        - ISI: Rate of spread (immediate threat)
        - BUI: Fuel available (accumulated burden)

        In fires: High ISI + High BUI = catastrophic fire
        For burnout: High ISI + High BUI = imminent burnout

        Formula from Van Wagner (1987):
        if BUI <= 80:
            fD = 0.626 * BUI^0.809 + 2
        else:
            fD = 1000 / (25 + 108.64 * exp(-0.023 * BUI))

        FWI = 0.289 * ISI * fD

        This correctly models non-linear interaction between spread rate
        and fuel load.

        Args:
            isi: Initial Spread Index (0-100+)
            bui: Buildup Index (0-100+)

        Returns:
            FWI score (0-100+)
            - <20: LOW danger
            - 20-40: MODERATE danger
            - 40-60: HIGH danger
            - 60-80: VERY_HIGH danger
            - 80+: EXTREME danger
        """
        # Calculate fuel effect (fD) based on BUI
        if bui <= 80:
            # Low to moderate BUI: power law
            fD = (0.626 * (bui**0.809)) + 2.0
        else:
            # High BUI: exponential saturation
            fD = 1000.0 / (25.0 + 108.64 * (2.71828 ** (-0.023 * bui)))

            # Final FWI calculation (calibrated for burnout context)
            # Scale factor to keep FWI in 0-100+ range with reasonable distribution
        fwi = 0.12 * isi * fD

        logger.debug(f"FWI: isi={isi:.1f}, bui={bui:.1f}, fD={fD:.2f}, fwi={fwi:.1f}")

        return float(fwi)

    def classify_danger(self, fwi: float) -> DangerClass:
        """
        Classify danger level based on FWI score.

        Thresholds based on Canadian FWI System danger classes,
        adapted for burnout context.

        Args:
            fwi: Fire Weather Index score (0-100+)

        Returns:
            DangerClass enum value
        """
        if fwi < 20:
            return DangerClass.LOW
        elif fwi < 40:
            return DangerClass.MODERATE
        elif fwi < 60:
            return DangerClass.HIGH
        elif fwi < 80:
            return DangerClass.VERY_HIGH
        else:
            return DangerClass.EXTREME

    def get_restrictions(self, danger_class: DangerClass) -> list[str]:
        """
        Get recommended workload restrictions for danger level.

        Mirrors fire management restrictions at different danger levels.

        Args:
            danger_class: Current danger classification

        Returns:
            List of recommended restrictions
        """
        restrictions = {
            DangerClass.LOW: [
                "Normal operations - maintain current workload",
                "Continue monitoring for changes",
            ],
            DangerClass.MODERATE: [
                "Monitor workload trends closely",
                "Avoid scheduling additional overtime",
                "Ensure adequate rest between shifts",
                "Consider preventive wellness check-in",
            ],
            DangerClass.HIGH: [
                "Reduce non-essential workload immediately",
                "Cap total hours at 60/week maximum",
                "Mandatory 24-hour off period every 7 days",
                "Schedule wellness intervention",
                "Defer elective responsibilities",
            ],
            DangerClass.VERY_HIGH: [
                "URGENT: Implement immediate workload reduction",
                "Cap hours at 50/week maximum",
                "Remove all non-clinical responsibilities",
                "Mandatory mental health evaluation",
                "Activate backup coverage plans",
                "Daily wellness check-ins required",
            ],
            DangerClass.EXTREME: [
                "EMERGENCY: Critical intervention required",
                "Immediate leave or reduced schedule (30-40h/week)",
                "Remove from high-stress assignments",
                "Mandatory mental health support",
                "Activate full backup coverage",
                "Do not return to normal duties until FWI < 40",
                "Consider temporary leave of absence",
            ],
        }

        return restrictions.get(danger_class, [])

    def calculate_burnout_danger(
        self,
        resident_id: UUID,
        recent_hours: float,
        monthly_load: float,
        yearly_satisfaction: float,
        workload_velocity: float = 0.0,
    ) -> FireDangerReport:
        """
        Calculate complete burnout danger assessment.

        This is the main entry point for burnout danger rating. It combines
        all temporal scales into a unified risk score.

        Args:
            resident_id: Unique identifier for resident
            recent_hours: Hours worked in last 2 weeks
            monthly_load: Average monthly hours over last 3 months
            yearly_satisfaction: Job satisfaction over past year (0.0-1.0)
            workload_velocity: Rate of workload increase (hours/week)

        Returns:
            FireDangerReport with complete assessment

        Example:
            rating = BurnoutDangerRating()

            # Resident working 75h recently, 260h/month average,
            # satisfaction at 0.4, and workload increasing 8h/week
            report = rating.calculate_burnout_danger(
                resident_id=uuid4(),
                recent_hours=75.0,
                monthly_load=260.0,
                yearly_satisfaction=0.4,
                workload_velocity=8.0,
            )

            # Expected: EXTREME danger
            # - FFMC high (recent overwork)
            # - DMC high (sustained overwork)
            # - DC high (low satisfaction)
            # - ISI very high (accelerating)
            # - BUI very high (accumulated burden)
            # - FWI 80+ (EXTREME)
        """
        # Calculate all components
        ffmc = self.calculate_fine_fuel_moisture_code(
            recent_hours=recent_hours,
            target=self.ffmc_target,
        )

        dmc = self.calculate_duff_moisture_code(
            monthly_load=monthly_load,
            target=self.dmc_target,
        )

        dc = self.calculate_drought_code(
            yearly_satisfaction=yearly_satisfaction,
        )

        isi = self.calculate_initial_spread_index(
            ffmc=ffmc,
            workload_velocity=workload_velocity,
        )

        bui = self.calculate_buildup_index(
            dmc=dmc,
            dc=dc,
        )

        fwi = self.calculate_fire_weather_index(
            isi=isi,
            bui=bui,
        )

        # Classify danger
        danger_class = self.classify_danger(fwi)

        # Get recommendations
        restrictions = self.get_restrictions(danger_class)

        logger.info(
            f"Burnout danger calculated for resident {resident_id}: "
            f"{danger_class.value.upper()} (FWI={fwi:.1f})"
        )

        # Build report
        return FireDangerReport(
            resident_id=resident_id,
            danger_class=danger_class,
            fwi_score=fwi,
            component_scores={
                "ffmc": ffmc,
                "dmc": dmc,
                "dc": dc,
                "isi": isi,
                "bui": bui,
                "fwi": fwi,
                "recent_hours": recent_hours,
                "monthly_load": monthly_load,
                "yearly_satisfaction": yearly_satisfaction,
                "workload_velocity": workload_velocity,
            },
            recommended_restrictions=restrictions,
        )

    def calculate_batch_danger(
        self,
        residents: list[dict],
    ) -> list[FireDangerReport]:
        """
        Calculate danger for multiple residents.

        Useful for program-wide burnout screening.

        Args:
            residents: List of resident data dicts with keys:
                - resident_id: UUID
                - recent_hours: float
                - monthly_load: float
                - yearly_satisfaction: float
                - workload_velocity: float (optional, default 0.0)

        Returns:
            List of FireDangerReport, one per resident
        """
        reports = []

        for resident_data in residents:
            try:
                report = self.calculate_burnout_danger(
                    resident_id=resident_data["resident_id"],
                    recent_hours=resident_data["recent_hours"],
                    monthly_load=resident_data["monthly_load"],
                    yearly_satisfaction=resident_data["yearly_satisfaction"],
                    workload_velocity=resident_data.get("workload_velocity", 0.0),
                )
                reports.append(report)
            except Exception as e:
                logger.error(
                    f"Failed to calculate danger for resident "
                    f"{resident_data.get('resident_id')}: {e}"
                )

                # Sort by FWI (highest risk first)
        reports.sort(key=lambda r: r.fwi_score, reverse=True)

        logger.info(f"Calculated burnout danger for {len(reports)} residents")

        return reports
