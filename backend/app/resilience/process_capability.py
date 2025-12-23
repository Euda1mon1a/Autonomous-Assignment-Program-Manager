"""
Six Sigma Process Capability Metrics for Schedule Quality.

Applies Six Sigma process capability indices (Cp, Cpk, Pp, Ppk, Cpm) to
measure schedule quality and process control. These metrics quantify how
well the scheduling process maintains ACGME compliance and operational
constraints.

Process Capability Indices:
- Cp: Process potential (assumes centered process)
- Cpk: Process capability (accounts for centering)
- Pp: Process performance (long-term variation)
- Ppk: Process performance capability
- Cpm: Taguchi capability (penalizes deviation from target)

Capability Classification:
- Cpk >= 2.0: World Class (6σ quality)
- Cpk >= 1.67: Excellent (5σ quality)
- Cpk >= 1.33: Capable (4σ quality)
- Cpk >= 1.0: Marginal (3σ quality)
- Cpk < 1.0: Incapable (defects likely)

Application to Scheduling:
- Workload hours: LSL=40, USL=80, Target=60
- Coverage rates: LSL=0.95, USL=1.0, Target=1.0
- Utilization: LSL=0.0, USL=0.8, Target=0.65
"""

import logging
import statistics
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ProcessCapabilityReport:
    """
    Six Sigma process capability report.

    Attributes:
        cp: Process capability index (potential)
        cpk: Process capability index (actual, accounting for centering)
        pp: Process performance index (long-term potential)
        ppk: Process performance index (long-term actual)
        cpm: Taguchi capability index (penalizes off-target)
        capability_status: Classification (EXCELLENT, CAPABLE, MARGINAL, INCAPABLE)
        sigma_level: Estimated sigma level from Cpk
        sample_size: Number of data points analyzed
        mean: Sample mean
        std_dev: Sample standard deviation
        lsl: Lower specification limit
        usl: Upper specification limit
        target: Target value (if applicable)
    """

    cp: float
    cpk: float
    pp: float
    ppk: float
    cpm: float
    capability_status: str
    sigma_level: float
    sample_size: int
    mean: float
    std_dev: float
    lsl: float
    usl: float
    target: float | None = None


class ScheduleCapabilityAnalyzer:
    """
    Analyzes schedule quality using Six Sigma process capability metrics.

    Uses statistical process control to measure how consistently the
    scheduling system produces compliant, balanced schedules.

    Example:
        analyzer = ScheduleCapabilityAnalyzer()

        # Analyze weekly hours for ACGME compliance
        weekly_hours = [65, 72, 58, 75, 68, 70, 62, 77]
        report = analyzer.analyze_workload_capability(
            weekly_hours,
            min_hours=40,
            max_hours=80
        )

        print(f"Capability: {report.capability_status}")
        print(f"Sigma Level: {report.sigma_level:.2f}σ")
        print(f"Cpk: {report.cpk:.3f}")
    """

    def __init__(self, min_sample_size: int = 30):
        """
        Initialize the capability analyzer.

        Args:
            min_sample_size: Minimum samples for reliable statistical analysis.
                            Six Sigma typically requires 30+ samples.
        """
        self.min_sample_size = min_sample_size

    def calculate_cp(
        self,
        data: list[float],
        lsl: float,
        usl: float,
    ) -> float:
        """
        Calculate Cp (Process Capability Index).

        Cp measures the potential capability of the process, assuming it is
        centered between specification limits. It ignores the actual mean.

        Formula: Cp = (USL - LSL) / (6 * σ_within)

        Args:
            data: Sample measurements
            lsl: Lower specification limit
            usl: Upper specification limit

        Returns:
            Cp index (higher is better)

        Raises:
            ValueError: If data is empty or has insufficient variation
        """
        if not data:
            raise ValueError("Cannot calculate Cp with empty data")

        if len(data) < 2:
            raise ValueError("Need at least 2 samples to calculate standard deviation")

        std_dev = statistics.stdev(data)

        if std_dev == 0:
            logger.warning(
                "Zero standard deviation - process may be static or simulated"
            )
            return float("inf")

        cp = (usl - lsl) / (6 * std_dev)

        logger.debug(
            f"Cp calculation: (USL={usl} - LSL={lsl}) / (6 * σ={std_dev:.3f}) = {cp:.3f}"
        )

        return cp

    def calculate_cpk(
        self,
        data: list[float],
        lsl: float,
        usl: float,
    ) -> float:
        """
        Calculate Cpk (Process Capability Index, accounting for centering).

        Cpk measures actual capability, penalizing processes that are off-center.
        It represents the distance from the mean to the nearest specification
        limit, in units of 3σ.

        Formula: Cpk = min((USL - μ) / 3σ, (μ - LSL) / 3σ)

        Args:
            data: Sample measurements
            lsl: Lower specification limit
            usl: Upper specification limit

        Returns:
            Cpk index (higher is better, 0 if outside specs)

        Raises:
            ValueError: If data is empty or has insufficient variation
        """
        if not data:
            raise ValueError("Cannot calculate Cpk with empty data")

        if len(data) < 2:
            raise ValueError("Need at least 2 samples to calculate standard deviation")

        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)

        if std_dev == 0:
            logger.warning(
                "Zero standard deviation - Cpk calculation may be unreliable"
            )
            # If process is perfectly centered at target, it's infinitely capable
            # If outside specs, it's completely incapable
            if lsl <= mean <= usl:
                return float("inf")
            else:
                return 0.0

        cpu = (usl - mean) / (3 * std_dev)  # Upper capability
        cpl = (mean - lsl) / (3 * std_dev)  # Lower capability

        cpk = min(cpu, cpl)

        logger.debug(
            f"Cpk calculation: mean={mean:.2f}, σ={std_dev:.3f}, "
            f"CPU={cpu:.3f}, CPL={cpl:.3f}, Cpk={cpk:.3f}"
        )

        return cpk

    def calculate_pp(
        self,
        data: list[float],
        lsl: float,
        usl: float,
    ) -> float:
        """
        Calculate Pp (Process Performance Index).

        Pp is similar to Cp but uses overall standard deviation (σ_overall)
        instead of within-subgroup variation (σ_within). For single samples,
        Pp equals Cp.

        Formula: Pp = (USL - LSL) / (6 * σ_overall)

        Args:
            data: Sample measurements
            lsl: Lower specification limit
            usl: Upper specification limit

        Returns:
            Pp index (higher is better)

        Raises:
            ValueError: If data is empty or has insufficient variation
        """
        # For our use case (single time series), Pp = Cp
        # In manufacturing, Pp would use long-term σ vs short-term σ
        return self.calculate_cp(data, lsl, usl)

    def calculate_ppk(
        self,
        data: list[float],
        lsl: float,
        usl: float,
    ) -> float:
        """
        Calculate Ppk (Process Performance Index, accounting for centering).

        Ppk is to Pp what Cpk is to Cp - it accounts for centering.
        Uses overall standard deviation.

        Formula: Ppk = min((USL - μ) / 3σ_overall, (μ - LSL) / 3σ_overall)

        Args:
            data: Sample measurements
            lsl: Lower specification limit
            usl: Upper specification limit

        Returns:
            Ppk index (higher is better)

        Raises:
            ValueError: If data is empty or has insufficient variation
        """
        # For our use case (single time series), Ppk = Cpk
        return self.calculate_cpk(data, lsl, usl)

    def calculate_cpm(
        self,
        data: list[float],
        lsl: float,
        usl: float,
        target: float,
    ) -> float:
        """
        Calculate Cpm (Taguchi Capability Index).

        Cpm is a more stringent index that penalizes deviation from target,
        not just from specification limits. Developed by Genichi Taguchi
        for robust quality engineering.

        Formula: Cpm = (USL - LSL) / (6 * √(σ² + (μ - T)²))

        Or equivalently: Cpm = Cp / √(1 + ((μ - T) / σ)²)

        Args:
            data: Sample measurements
            lsl: Lower specification limit
            usl: Upper specification limit
            target: Target value (ideal center point)

        Returns:
            Cpm index (higher is better, always <= Cp)

        Raises:
            ValueError: If data is empty or has insufficient variation
        """
        if not data:
            raise ValueError("Cannot calculate Cpm with empty data")

        if len(data) < 2:
            raise ValueError("Need at least 2 samples to calculate standard deviation")

        mean = statistics.mean(data)
        std_dev = statistics.stdev(data)

        # Taguchi's loss function: penalize deviation from target
        deviation_from_target = mean - target
        adjusted_variance = std_dev**2 + deviation_from_target**2

        if adjusted_variance == 0:
            logger.warning("Zero adjusted variance in Cpm calculation")
            return float("inf")

        cpm = (usl - lsl) / (6 * (adjusted_variance**0.5))

        logger.debug(
            f"Cpm calculation: mean={mean:.2f}, target={target:.2f}, "
            f"σ={std_dev:.3f}, deviation={deviation_from_target:.2f}, Cpm={cpm:.3f}"
        )

        return cpm

    def get_sigma_level(self, cpk: float) -> float:
        """
        Convert Cpk to sigma level.

        Approximate relationship:
        - Cpk = 1.0 → 3σ (99.73% within spec)
        - Cpk = 1.33 → 4σ (99.994% within spec)
        - Cpk = 1.67 → 5σ (99.99994% within spec)
        - Cpk = 2.0 → 6σ (99.9999998% within spec)

        Formula: σ_level ≈ 3 * Cpk

        Args:
            cpk: Process capability index

        Returns:
            Estimated sigma level (e.g., 4.5 for 4.5σ)
        """
        if cpk <= 0:
            return 0.0

        # Linear approximation: sigma_level = 3 * Cpk
        # This is accurate enough for practical purposes
        sigma_level = 3.0 * cpk

        return sigma_level

    def classify_capability(self, cpk: float) -> str:
        """
        Classify process capability based on Cpk value.

        Industry standard classifications:
        - Cpk >= 2.0: EXCELLENT (World Class, 6σ)
        - Cpk >= 1.67: EXCELLENT (5σ quality)
        - Cpk >= 1.33: CAPABLE (4σ quality, industry standard)
        - Cpk >= 1.0: MARGINAL (3σ quality, minimum acceptable)
        - Cpk < 1.0: INCAPABLE (defects expected)

        Args:
            cpk: Process capability index

        Returns:
            Classification string: EXCELLENT, CAPABLE, MARGINAL, or INCAPABLE
        """
        if cpk >= 1.67:
            return "EXCELLENT"
        elif cpk >= 1.33:
            return "CAPABLE"
        elif cpk >= 1.0:
            return "MARGINAL"
        else:
            return "INCAPABLE"

    def analyze_workload_capability(
        self,
        weekly_hours: list[float],
        min_hours: float = 40.0,
        max_hours: float = 80.0,
        target_hours: float | None = None,
    ) -> ProcessCapabilityReport:
        """
        Analyze workload distribution capability for ACGME compliance.

        Evaluates how consistently the scheduling process maintains resident
        weekly hours within acceptable limits. Target defaults to midpoint
        if not specified.

        Args:
            weekly_hours: List of weekly hour totals
            min_hours: Lower specification limit (default: 40 hours)
            max_hours: Upper specification limit (default: 80 hours, ACGME limit)
            target_hours: Target hours (default: midpoint = 60 hours)

        Returns:
            ProcessCapabilityReport with all indices and classification

        Raises:
            ValueError: If insufficient data or invalid specification limits
        """
        if not weekly_hours:
            raise ValueError("Cannot analyze capability with empty data")

        if len(weekly_hours) < self.min_sample_size:
            logger.warning(
                f"Sample size ({len(weekly_hours)}) below recommended minimum "
                f"({self.min_sample_size}) for Six Sigma analysis. "
                f"Results may be unreliable."
            )

        if min_hours >= max_hours:
            raise ValueError(
                f"Invalid specification limits: LSL ({min_hours}) must be < USL ({max_hours})"
            )

        # Default target to midpoint if not specified
        if target_hours is None:
            target_hours = (min_hours + max_hours) / 2

        # Calculate all capability indices
        cp = self.calculate_cp(weekly_hours, min_hours, max_hours)
        cpk = self.calculate_cpk(weekly_hours, min_hours, max_hours)
        pp = self.calculate_pp(weekly_hours, min_hours, max_hours)
        ppk = self.calculate_ppk(weekly_hours, min_hours, max_hours)
        cpm = self.calculate_cpm(weekly_hours, min_hours, max_hours, target_hours)

        # Derive metrics
        sigma_level = self.get_sigma_level(cpk)
        capability_status = self.classify_capability(cpk)

        # Calculate statistics
        mean = statistics.mean(weekly_hours)
        std_dev = statistics.stdev(weekly_hours) if len(weekly_hours) >= 2 else 0.0

        report = ProcessCapabilityReport(
            cp=cp,
            cpk=cpk,
            pp=pp,
            ppk=ppk,
            cpm=cpm,
            capability_status=capability_status,
            sigma_level=sigma_level,
            sample_size=len(weekly_hours),
            mean=mean,
            std_dev=std_dev,
            lsl=min_hours,
            usl=max_hours,
            target=target_hours,
        )

        logger.info(
            f"Workload capability analysis: Cpk={cpk:.3f} ({capability_status}), "
            f"{sigma_level:.2f}σ quality, n={len(weekly_hours)}"
        )

        return report

    def get_capability_summary(self, report: ProcessCapabilityReport) -> dict:
        """
        Generate human-readable capability summary.

        Args:
            report: Process capability report

        Returns:
            Dictionary with formatted summary information
        """
        # Calculate defect rate estimate (simplified)
        # For Cpk=1.0: ~2700 PPM (0.27%)
        # For Cpk=1.33: ~66 PPM (0.0066%)
        # For Cpk=2.0: ~0.002 PPM (near zero)
        if report.cpk > 0:
            # Rough approximation: defect_ppm ≈ 10^(6 - 2*sigma_level)
            estimated_defect_ppm = 10 ** (6 - 2 * report.sigma_level)
            estimated_defect_ppm = max(0.001, min(1_000_000, estimated_defect_ppm))
        else:
            estimated_defect_ppm = 1_000_000  # 100% if completely incapable

        recommendations = self._get_capability_recommendations(report)

        return {
            "status": report.capability_status,
            "sigma_level": f"{report.sigma_level:.2f}σ",
            "indices": {
                "Cpk": f"{report.cpk:.3f}",
                "Cp": f"{report.cp:.3f}",
                "Ppk": f"{report.ppk:.3f}",
                "Pp": f"{report.pp:.3f}",
                "Cpm": f"{report.cpm:.3f}",
            },
            "centering": self._assess_centering(report),
            "statistics": {
                "mean": f"{report.mean:.2f}",
                "std_dev": f"{report.std_dev:.2f}",
                "target": f"{report.target:.2f}" if report.target else "N/A",
                "sample_size": report.sample_size,
            },
            "estimated_defect_rate": {
                "ppm": f"{estimated_defect_ppm:.2f}",
                "percentage": f"{estimated_defect_ppm / 10000:.4f}%",
            },
            "recommendations": recommendations,
        }

    def _assess_centering(self, report: ProcessCapabilityReport) -> str:
        """Assess how well the process is centered."""
        if report.cp == 0:
            return "UNDEFINED"

        centering_ratio = report.cpk / report.cp

        if centering_ratio >= 0.95:
            return "EXCELLENT - Process well centered"
        elif centering_ratio >= 0.85:
            return "GOOD - Minor centering improvement possible"
        elif centering_ratio >= 0.75:
            return "FAIR - Process somewhat off-center"
        else:
            return "POOR - Process significantly off-center"

    def _get_capability_recommendations(
        self, report: ProcessCapabilityReport
    ) -> list[str]:
        """Generate recommendations based on capability analysis."""
        recommendations = []

        if report.capability_status == "INCAPABLE":
            recommendations.extend(
                [
                    "URGENT: Process cannot reliably meet specifications",
                    "Review schedule generation constraints",
                    "Consider tightening ACGME compliance validation",
                    "Investigate root causes of variation",
                ]
            )
        elif report.capability_status == "MARGINAL":
            recommendations.extend(
                [
                    "Process barely meets specifications - improvement needed",
                    "Reduce process variation through better load balancing",
                    "Monitor closely for ACGME violations",
                ]
            )
        elif report.capability_status == "CAPABLE":
            recommendations.extend(
                [
                    "Process meets industry standards",
                    "Aim for 5σ quality by reducing variation",
                    "Continue monitoring for regression",
                ]
            )
        else:  # EXCELLENT
            recommendations.extend(
                [
                    "World-class process capability",
                    "Maintain current practices",
                    "Document best practices for replication",
                ]
            )

        # Centering recommendations
        if report.cp > 0:
            centering_ratio = report.cpk / report.cp
            if centering_ratio < 0.85:
                recommendations.append(
                    f"Improve centering: Cpk/Cp = {centering_ratio:.2f} "
                    f"(target mean closer to {report.target})"
                )

        # Taguchi recommendations
        if report.target and report.cpm < report.cp * 0.9:
            recommendations.append(
                "High off-target loss - aim for target value, not just spec limits"
            )

        return recommendations
