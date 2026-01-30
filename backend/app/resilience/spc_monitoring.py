"""
Statistical Process Control (SPC) Workload Monitoring.

Implements Western Electric Rules for detecting workload drift and anomalies
in medical resident scheduling. Uses control chart theory to identify when
workload patterns deviate from expected norms, enabling early intervention
before ACGME violations or burnout occur.

Western Electric Rules Implemented:
    Rule 1: 1 point beyond 3σ (CRITICAL - process out of control)
    Rule 2: 2 of 3 consecutive points beyond 2σ (WARNING - shift detected)
    Rule 3: 4 of 5 consecutive points beyond 1σ (WARNING - trend detected)
    Rule 4: 8 consecutive points on same side of centerline (INFO - sustained shift)

These rules detect different types of process variation:
    - Special cause variation (rules 1-2): Requires immediate investigation
    - Common cause variation (rules 3-4): Indicates systemic changes

Process Capability Indices:
    - Cp/Cpk: Short-term capability (within-subgroup variation)
    - Pp/Ppk: Long-term performance (total variation)
    - Target: Cpk ≥ 1.33 (4σ process), Cpk ≥ 1.67 (5σ process)
"""

import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class SPCAlert:
    """
    Alert generated when Western Electric Rule is violated.

    Attributes:
        rule: Which Western Electric rule was violated (e.g., "Rule 1", "Rule 2")
        severity: Alert severity level ("CRITICAL", "WARNING", "INFO")
        message: Human-readable description of the violation
        resident_id: Optional UUID of affected resident (None for system-wide alerts)
        timestamp: When the alert was generated
        data_points: The specific data points that triggered the alert
        control_limits: Control chart limits at time of violation
    """

    rule: str
    severity: str
    message: str
    resident_id: UUID | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data_points: list[float] = field(default_factory=list)
    control_limits: dict = field(default_factory=dict)


class WorkloadControlChart:
    """
    Control chart analyzer for resident workload monitoring.

    Uses Statistical Process Control to detect anomalous workload patterns
    that may indicate scheduling problems, ACGME violations, or burnout risk.

    The control chart assumes workload is normally distributed around a target
    with known or estimated standard deviation. Deviations are flagged using
    Western Electric Rules.

    Typical Usage:
        chart = WorkloadControlChart(target_hours=60, sigma=5)

        # Weekly hours for a resident over 8 weeks
        weekly_hours = [58, 62, 59, 67, 71, 75, 78, 80]

        alerts = chart.detect_western_electric_violations(
            resident_id=resident_uuid,
            weekly_hours=weekly_hours
        )

        for alert in alerts:
            if alert.severity == "CRITICAL":
                # Immediate intervention required
                notify_program_director(alert)
    """

    def __init__(
        self,
        target_hours: float = 60.0,
        sigma: float = 5.0,
    ) -> None:
        """
        Initialize workload control chart.

        Args:
            target_hours: Target/expected weekly hours (centerline). Default 60 hours.
            sigma: Process standard deviation. Default 5 hours.
                  This represents normal variation in workload.

        Notes:
            - For ACGME compliance, 80 hours/week is the hard limit
            - Target of 60 hours provides 20-hour buffer
            - Sigma of 5 hours means 99.7% of weeks should be 45-75 hours (3σ)
        """
        self.target_hours = target_hours
        self.sigma = sigma

        # Pre-calculate control limits
        self.ucl_3sigma = target_hours + 3 * sigma  # Upper Control Limit (3σ)
        self.lcl_3sigma = target_hours - 3 * sigma  # Lower Control Limit (3σ)
        self.ucl_2sigma = target_hours + 2 * sigma  # Upper Warning Limit (2σ)
        self.lcl_2sigma = target_hours - 2 * sigma  # Lower Warning Limit (2σ)
        self.ucl_1sigma = target_hours + 1 * sigma  # Upper Zone A/B boundary
        self.lcl_1sigma = target_hours - 1 * sigma  # Lower Zone A/B boundary

        logger.debug(
            f"Control chart initialized: target={target_hours}h, "
            f"UCL={self.ucl_3sigma:.1f}h, LCL={self.lcl_3sigma:.1f}h"
        )

    def detect_western_electric_violations(
        self,
        resident_id: UUID,
        weekly_hours: list[float],
    ) -> list[SPCAlert]:
        """
        Detect Western Electric Rule violations in workload data.

        Analyzes a time series of weekly work hours to identify patterns
        indicating process instability or special cause variation.

        Args:
            resident_id: UUID of the resident being monitored
            weekly_hours: List of weekly work hours in chronological order.
                         Minimum 8 data points recommended for Rule 4.

        Returns:
            List of SPCAlert objects, one per violation detected.
            Empty list if no violations found.

        Raises:
            ValueError: If weekly_hours is empty or contains invalid values

        Notes:
            - Alerts are ordered chronologically by when violation occurred
            - Multiple rules may trigger on the same data
            - Rule 4 requires at least 8 data points
            - Negative hours or hours > 168 (hours in a week) raise ValueError
        """
        if not weekly_hours:
            raise ValueError("weekly_hours cannot be empty")

            # Validate data
        for i, hours in enumerate(weekly_hours):
            if hours < 0:
                raise ValueError(
                    f"Invalid hours at index {i}: {hours} (cannot be negative)"
                )
            if hours > 168:
                raise ValueError(
                    f"Invalid hours at index {i}: {hours} (exceeds 168 hours/week)"
                )

        alerts = []

        # Check each rule in order
        alerts.extend(self._check_rule_1(resident_id, weekly_hours))
        alerts.extend(self._check_rule_2(resident_id, weekly_hours))
        alerts.extend(self._check_rule_3(resident_id, weekly_hours))
        alerts.extend(self._check_rule_4(resident_id, weekly_hours))

        if alerts:
            logger.info(
                f"SPC violations detected for resident {resident_id}: "
                f"{len(alerts)} alerts generated"
            )
        else:
            logger.debug(f"No SPC violations for resident {resident_id}")

        return alerts

    def _check_rule_1(
        self,
        resident_id: UUID,
        weekly_hours: list[float],
    ) -> list[SPCAlert]:
        """
        Rule 1: One point more than 3σ from the centerline.

        Indicates: Special cause variation - process out of control.
        Action: Immediate investigation required.

        This is the most severe violation, indicating extreme deviation
        from expected workload. May indicate data error, scheduling bug,
        or severe overwork/underwork.
        """
        alerts = []

        for i, hours in enumerate(weekly_hours):
            if hours > self.ucl_3sigma:
                alerts.append(
                    SPCAlert(
                        rule="Rule 1",
                        severity="CRITICAL",
                        message=(
                            f"Workload exceeded 3σ upper limit: {hours:.1f} hours "
                            f"(limit: {self.ucl_3sigma:.1f}h, target: {self.target_hours:.1f}h). "
                            f"Process out of control - immediate investigation required."
                        ),
                        resident_id=resident_id,
                        data_points=[hours],
                        control_limits={
                            "ucl_3sigma": self.ucl_3sigma,
                            "lcl_3sigma": self.lcl_3sigma,
                            "centerline": self.target_hours,
                        },
                    )
                )
                logger.warning(
                    f"Rule 1 violation (upper): resident={resident_id}, "
                    f"hours={hours:.1f}, week_index={i}"
                )
            elif hours < self.lcl_3sigma:
                alerts.append(
                    SPCAlert(
                        rule="Rule 1",
                        severity="CRITICAL",
                        message=(
                            f"Workload below 3σ lower limit: {hours:.1f} hours "
                            f"(limit: {self.lcl_3sigma:.1f}h, target: {self.target_hours:.1f}h). "
                            f"Possible scheduling gap or data error."
                        ),
                        resident_id=resident_id,
                        data_points=[hours],
                        control_limits={
                            "ucl_3sigma": self.ucl_3sigma,
                            "lcl_3sigma": self.lcl_3sigma,
                            "centerline": self.target_hours,
                        },
                    )
                )
                logger.warning(
                    f"Rule 1 violation (lower): resident={resident_id}, "
                    f"hours={hours:.1f}, week_index={i}"
                )

        return alerts

    def _check_rule_2(
        self,
        resident_id: UUID,
        weekly_hours: list[float],
    ) -> list[SPCAlert]:
        """
        Rule 2: Two out of three consecutive points beyond 2σ (same side).

        Indicates: Process shift - sustained change in mean.
        Action: Investigate cause of shift.

        This detects a significant shift in workload level, such as
        rotation change, increased clinical demands, or staffing shortage.
        """
        alerts = []

        if len(weekly_hours) < 3:
            return alerts  # Need at least 3 points

        for i in range(len(weekly_hours) - 2):
            window = weekly_hours[i : i + 3]

            # Check upper 2σ
            upper_violations = [h for h in window if h > self.ucl_2sigma]
            if len(upper_violations) >= 2:
                alerts.append(
                    SPCAlert(
                        rule="Rule 2",
                        severity="WARNING",
                        message=(
                            f"Workload shift detected: {len(upper_violations)} of 3 weeks "
                            f"exceeded 2σ upper limit ({self.ucl_2sigma:.1f}h). "
                            f"Hours: {[f'{h:.1f}' for h in window]}. "
                            f"Sustained overwork pattern detected."
                        ),
                        resident_id=resident_id,
                        data_points=window,
                        control_limits={
                            "ucl_2sigma": self.ucl_2sigma,
                            "lcl_2sigma": self.lcl_2sigma,
                            "centerline": self.target_hours,
                        },
                    )
                )
                logger.warning(
                    f"Rule 2 violation (upper): resident={resident_id}, "
                    f"window_start={i}, hours={window}"
                )
                break  # Only report first occurrence

                # Check lower 2σ
            lower_violations = [h for h in window if h < self.lcl_2sigma]
            if len(lower_violations) >= 2:
                alerts.append(
                    SPCAlert(
                        rule="Rule 2",
                        severity="WARNING",
                        message=(
                            f"Workload shift detected: {len(lower_violations)} of 3 weeks "
                            f"below 2σ lower limit ({self.lcl_2sigma:.1f}h). "
                            f"Hours: {[f'{h:.1f}' for h in window]}. "
                            f"Sustained underutilization pattern detected."
                        ),
                        resident_id=resident_id,
                        data_points=window,
                        control_limits={
                            "ucl_2sigma": self.ucl_2sigma,
                            "lcl_2sigma": self.lcl_2sigma,
                            "centerline": self.target_hours,
                        },
                    )
                )
                logger.warning(
                    f"Rule 2 violation (lower): resident={resident_id}, "
                    f"window_start={i}, hours={window}"
                )
                break  # Only report first occurrence

        return alerts

    def _check_rule_3(
        self,
        resident_id: UUID,
        weekly_hours: list[float],
    ) -> list[SPCAlert]:
        """
        Rule 3: Four out of five consecutive points beyond 1σ (same side).

        Indicates: Process trend - gradual shift in level.
        Action: Monitor and investigate trend.

        This detects a trending pattern in workload, suggesting a gradual
        change in clinical demands or scheduling patterns.
        """
        alerts = []

        if len(weekly_hours) < 5:
            return alerts  # Need at least 5 points

        for i in range(len(weekly_hours) - 4):
            window = weekly_hours[i : i + 5]

            # Check upper 1σ
            upper_violations = [h for h in window if h > self.ucl_1sigma]
            if len(upper_violations) >= 4:
                alerts.append(
                    SPCAlert(
                        rule="Rule 3",
                        severity="WARNING",
                        message=(
                            f"Workload trend detected: {len(upper_violations)} of 5 weeks "
                            f"exceeded 1σ upper threshold ({self.ucl_1sigma:.1f}h). "
                            f"Hours: {[f'{h:.1f}' for h in window]}. "
                            f"Gradual increase in workload detected."
                        ),
                        resident_id=resident_id,
                        data_points=window,
                        control_limits={
                            "ucl_1sigma": self.ucl_1sigma,
                            "lcl_1sigma": self.lcl_1sigma,
                            "centerline": self.target_hours,
                        },
                    )
                )
                logger.warning(
                    f"Rule 3 violation (upper): resident={resident_id}, "
                    f"window_start={i}, hours={window}"
                )
                break  # Only report first occurrence

                # Check lower 1σ
            lower_violations = [h for h in window if h < self.lcl_1sigma]
            if len(lower_violations) >= 4:
                alerts.append(
                    SPCAlert(
                        rule="Rule 3",
                        severity="WARNING",
                        message=(
                            f"Workload trend detected: {len(lower_violations)} of 5 weeks "
                            f"below 1σ lower threshold ({self.lcl_1sigma:.1f}h). "
                            f"Hours: {[f'{h:.1f}' for h in window]}. "
                            f"Gradual decrease in workload detected."
                        ),
                        resident_id=resident_id,
                        data_points=window,
                        control_limits={
                            "ucl_1sigma": self.ucl_1sigma,
                            "lcl_1sigma": self.lcl_1sigma,
                            "centerline": self.target_hours,
                        },
                    )
                )
                logger.warning(
                    f"Rule 3 violation (lower): resident={resident_id}, "
                    f"window_start={i}, hours={window}"
                )
                break  # Only report first occurrence

        return alerts

    def _check_rule_4(
        self,
        resident_id: UUID,
        weekly_hours: list[float],
    ) -> list[SPCAlert]:
        """
        Rule 4: Eight consecutive points on same side of centerline.

        Indicates: Sustained shift in process mean.
        Action: Identify and address root cause of shift.

        This detects a persistent change in workload level, such as
        permanent rotation change, new clinical responsibilities, or
        systematic scheduling changes.
        """
        alerts = []

        if len(weekly_hours) < 8:
            return alerts  # Need at least 8 points

        for i in range(len(weekly_hours) - 7):
            window = weekly_hours[i : i + 8]

            # Check if all points are above centerline
            above_center = [h for h in window if h > self.target_hours]
            if len(above_center) == 8:
                mean_hours = statistics.mean(window)
                alerts.append(
                    SPCAlert(
                        rule="Rule 4",
                        severity="INFO",
                        message=(
                            f"Sustained workload shift detected: 8 consecutive weeks "
                            f"above target ({self.target_hours:.1f}h). "
                            f"Mean: {mean_hours:.1f}h. "
                            f"Indicates systematic change in workload baseline."
                        ),
                        resident_id=resident_id,
                        data_points=window,
                        control_limits={
                            "centerline": self.target_hours,
                            "mean_actual": mean_hours,
                        },
                    )
                )
                logger.info(
                    f"Rule 4 violation (above): resident={resident_id}, "
                    f"window_start={i}, mean={mean_hours:.1f}h"
                )
                break  # Only report first occurrence

                # Check if all points are below centerline
            below_center = [h for h in window if h < self.target_hours]
            if len(below_center) == 8:
                mean_hours = statistics.mean(window)
                alerts.append(
                    SPCAlert(
                        rule="Rule 4",
                        severity="INFO",
                        message=(
                            f"Sustained workload shift detected: 8 consecutive weeks "
                            f"below target ({self.target_hours:.1f}h). "
                            f"Mean: {mean_hours:.1f}h. "
                            f"Indicates systematic change in workload baseline."
                        ),
                        resident_id=resident_id,
                        data_points=window,
                        control_limits={
                            "centerline": self.target_hours,
                            "mean_actual": mean_hours,
                        },
                    )
                )
                logger.info(
                    f"Rule 4 violation (below): resident={resident_id}, "
                    f"window_start={i}, mean={mean_hours:.1f}h"
                )
                break  # Only report first occurrence

        return alerts


def calculate_control_limits(data: list[float]) -> dict:
    """
    Calculate control chart limits from empirical data.

    Estimates centerline and control limits from observed data using
    standard statistical estimators. Use this when process parameters
    are unknown and must be estimated from historical data.

    Args:
        data: List of observed values (e.g., weekly hours over time)

    Returns:
        Dictionary containing:
            - centerline: Process mean (x̄)
            - sigma: Process standard deviation (s)
            - ucl: Upper Control Limit (x̄ + 3s)
            - lcl: Lower Control Limit (x̄ - 3s)
            - ucl_2sigma: Upper Warning Limit (x̄ + 2s)
            - lcl_2sigma: Lower Warning Limit (x̄ - 2s)
            - n: Sample size

    Raises:
        ValueError: If data is empty or has fewer than 2 points

    Notes:
        - Requires at least 2 data points (preferably 20+ for stable estimates)
        - Uses sample standard deviation (n-1 denominator)
        - Assumes data is approximately normally distributed

    Example:
        >>> weekly_hours = [58, 62, 59, 61, 63, 60, 58, 62]
        >>> limits = calculate_control_limits(weekly_hours)
        >>> print(f"Center: {limits['centerline']:.1f}h")
        >>> print(f"UCL: {limits['ucl']:.1f}h")
    """
    if not data:
        raise ValueError("data cannot be empty")
    if len(data) < 2:
        raise ValueError("data must contain at least 2 points for standard deviation")

    centerline = statistics.mean(data)
    sigma = statistics.stdev(data)  # Sample standard deviation (n-1)

    return {
        "centerline": centerline,
        "sigma": sigma,
        "ucl": centerline + 3 * sigma,
        "lcl": centerline - 3 * sigma,
        "ucl_2sigma": centerline + 2 * sigma,
        "lcl_2sigma": centerline - 2 * sigma,
        "ucl_1sigma": centerline + 1 * sigma,
        "lcl_1sigma": centerline - 1 * sigma,
        "n": len(data),
    }


def calculate_process_capability(
    data: list[float],
    lsl: float,
    usl: float,
) -> dict:
    """
    Calculate process capability indices (Cp, Cpk, Pp, Ppk).

    Process capability measures how well a process meets specifications.
    Used to assess whether workload distribution fits within acceptable
    bounds (e.g., ACGME limits).

    Args:
        data: List of observed values (e.g., weekly hours)
        lsl: Lower Specification Limit (e.g., 40 hours/week minimum)
        usl: Upper Specification Limit (e.g., 80 hours/week ACGME max)

    Returns:
        Dictionary containing:
            - cp: Process Capability (potential, assumes centered)
                 Cp = (USL - LSL) / (6σ)
            - cpk: Process Capability Index (actual, accounts for centering)
                  Cpk = min((USL - μ) / 3σ, (μ - LSL) / 3σ)
            - pp: Process Performance (long-term capability)
            - ppk: Process Performance Index (long-term actual)
            - mean: Process mean
            - sigma: Process standard deviation
            - interpretation: Human-readable assessment

    Raises:
        ValueError: If data is empty, LSL >= USL, or < 2 points

    Interpretation:
        - Cpk < 1.0: Process not capable (defects expected)
        - Cpk = 1.0: Process barely capable (2700 ppm defects)
        - Cpk = 1.33: Process capable (63 ppm defects, 4σ)
        - Cpk = 1.67: Process highly capable (0.6 ppm, 5σ)
        - Cpk = 2.0: World-class process (0.002 ppm, 6σ)

    Notes:
        - For this implementation, Pp and Ppk equal Cp and Cpk
          (would differ if using subgroup-based estimates)
        - Assumes normal distribution
        - Negative Cpk indicates mean outside specification limits

    Example:
        >>> weekly_hours = [58, 62, 59, 61, 63, 60, 58, 62]
        >>> capability = calculate_process_capability(
        ...     data=weekly_hours,
        ...     lsl=40,  # Minimum hours
        ...     usl=80,  # ACGME maximum
        ... )
        >>> print(f"Cpk: {capability['cpk']:.2f}")
        >>> print(capability['interpretation'])
    """
    if not data:
        raise ValueError("data cannot be empty")
    if len(data) < 2:
        raise ValueError("data must contain at least 2 points")
    if lsl >= usl:
        raise ValueError(f"LSL ({lsl}) must be less than USL ({usl})")

    mean = statistics.mean(data)
    sigma = statistics.stdev(data)

    if sigma == 0:
        # Perfect process with no variation
        if lsl <= mean <= usl:
            # Within spec
            return {
                "cp": float("inf"),
                "cpk": float("inf"),
                "pp": float("inf"),
                "ppk": float("inf"),
                "mean": mean,
                "sigma": 0.0,
                "interpretation": "Perfect process - no variation",
            }
        else:
            # Outside spec
            return {
                "cp": float("inf"),
                "cpk": float("-inf"),
                "pp": float("inf"),
                "ppk": float("-inf"),
                "mean": mean,
                "sigma": 0.0,
                "interpretation": "Process outside specifications with no variation",
            }

            # Cp: Potential capability (if perfectly centered)
    cp = (usl - lsl) / (6 * sigma)

    # Cpk: Actual capability (accounts for centering)
    cpu = (usl - mean) / (3 * sigma)  # Upper capability
    cpl = (mean - lsl) / (3 * sigma)  # Lower capability
    cpk = min(cpu, cpl)

    # Pp and Ppk: For this implementation, same as Cp/Cpk
    # (In practice, Pp/Ppk would use overall σ vs within-subgroup σ)
    pp = cp
    ppk = cpk

    # Interpretation
    if cpk < 0:
        interpretation = "Process mean outside specification limits - not capable"
    elif cpk < 1.0:
        interpretation = "Process not capable - high defect rate expected"
    elif cpk < 1.33:
        interpretation = "Process marginally capable - improvement recommended"
    elif cpk < 1.67:
        interpretation = "Process capable - meets 4-sigma quality"
    elif cpk < 2.0:
        interpretation = "Process highly capable - meets 5-sigma quality"
    else:
        interpretation = "World-class process - meets 6-sigma quality"

    return {
        "cp": cp,
        "cpk": cpk,
        "pp": pp,
        "ppk": ppk,
        "mean": mean,
        "sigma": sigma,
        "lsl": lsl,
        "usl": usl,
        "interpretation": interpretation,
    }
