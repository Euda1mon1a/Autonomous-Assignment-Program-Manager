"""
MTF Compliance: "The Iron Dome" - Automated Bureaucratic Defense.

In a Military Treatment Facility, you can't solve problems with money or hiring.
You solve them with Rank, Regulations, and Paper Trails.

This module "weaponizes compliance" to protect schedulers from the inevitable
fallout of staffing crises. It turns the scheduler into an automated JAG
(Judge Advocate General) / Inspector General officer.

Key Components:
1. DRRS Translation - Converts metrics to military readiness language
2. MFR Generator - Creates Memoranda for Record documenting risk acceptance
3. Circuit Breaker - Locks scheduling when safety thresholds are breached
4. RFF Drafter - Generates Request for Forces documentation

The insight: The system already calculates risk. This module makes risk
visible in ways that create accountability and force action.
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from app.resilience.mtf_types import (
    CascadePrediction,
    PositiveFeedbackRisk,
    ProjectionWithoutSupport,
    SupportingMetrics,
    SystemHealthState,
)
from app.schemas.mtf_compliance import (
    CircuitBreakerState,
    CircuitBreakerTrigger,
    DRRSCategory,
    EquipmentReadinessLevel,
    MFRPriority,
    MFRType,
    MissionCapabilityStatus,
    MissionType,
    OverrideAuthority,
    PersonnelReadinessLevel,
    RiskLevel,
)
from app.schemas.resilience import (
    EquilibriumState,
    LoadSheddingLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# DRRS Translation Layer
# =============================================================================


class DRRSTranslator:
    """
    Translates internal scheduling metrics to Defense Readiness Reporting System.

    The Commander doesn't care about "resident wellness" or "fairness."
    They care about Readiness and Mission Capability.

    This translator turns:
    - LoadSheddingLevel -> DRRS C-ratings
    - EquilibriumState -> Mission capability percentage
    - AllostasisMetrics -> Personnel readiness
    """

    # Map LoadSheddingLevel to DRRS Category
    LOAD_SHEDDING_TO_DRRS = {
        LoadSheddingLevel.NORMAL: DRRSCategory.C1,
        LoadSheddingLevel.YELLOW: DRRSCategory.C2,
        LoadSheddingLevel.ORANGE: DRRSCategory.C3,
        LoadSheddingLevel.RED: DRRSCategory.C4,
        LoadSheddingLevel.BLACK: DRRSCategory.C4,
        LoadSheddingLevel.CRITICAL: DRRSCategory.C5,
    }

    # Map EquilibriumState to Mission Capability
    EQUILIBRIUM_TO_MISSION = {
        EquilibriumState.STABLE: MissionCapabilityStatus.FMC,
        EquilibriumState.COMPENSATING: MissionCapabilityStatus.PMC,
        EquilibriumState.STRESSED: MissionCapabilityStatus.PMC,
        EquilibriumState.UNSUSTAINABLE: MissionCapabilityStatus.NMC,
        EquilibriumState.CRITICAL: MissionCapabilityStatus.NMC,
    }

    # Military Occupational Specialty codes for medical personnel
    MOS_DESCRIPTIONS = {
        "60H": "Physician, Attending",
        "60M": "Physician, Resident",
        "66H": "Nurse Practitioner",
        "68W": "Combat Medic/Healthcare Specialist",
        "68C": "Practical Nursing Specialist",
        "68K": "Medical Laboratory Specialist",
    }

    def translate_load_shedding(
        self,
        level: LoadSheddingLevel,
    ) -> tuple[DRRSCategory, str]:
        """
        Translate LoadSheddingLevel to DRRS C-rating with explanation.

        Args:
            level: Current load shedding level

        Returns:
            Tuple of (DRRS category, explanation)
        """
        drrs = self.LOAD_SHEDDING_TO_DRRS.get(level, DRRSCategory.C5)

        explanations = {
            DRRSCategory.C1: "Fully Mission Capable. All medical services operational.",
            DRRSCategory.C2: "Substantially Mission Capable. Minor deficiencies in non-essential services.",
            DRRSCategory.C3: "Marginally Mission Capable. Significant deficiencies affecting mission support.",
            DRRSCategory.C4: "Not Mission Capable. Major deficiencies. Unit cannot fully perform core mission.",
            DRRSCategory.C5: "Not Mission Capable. Critical deficiencies. Only emergency patient safety maintained.",
        }

        return drrs, explanations.get(drrs, "Unknown status")

    def translate_personnel_strength(
        self,
        available_faculty: int,
        required_faculty: int,
        overloaded_count: int = 0,
    ) -> tuple[PersonnelReadinessLevel, float]:
        """
        Translate faculty availability to Personnel (P) readiness.

        Args:
            available_faculty: Number of faculty available
            required_faculty: Number of faculty required
            overloaded_count: Number of faculty in allostatic overload

        Returns:
            Tuple of (P-rating, percentage)
        """
        if required_faculty == 0:
            return PersonnelReadinessLevel.P4, 0.0

        # Effective availability reduces by overloaded count (they're not really available)
        effective_available = max(0, available_faculty - (overloaded_count * 0.5))
        percentage = (effective_available / required_faculty) * 100

        if percentage >= 100:
            return PersonnelReadinessLevel.P1, percentage
        elif percentage >= 90:
            return PersonnelReadinessLevel.P2, percentage
        elif percentage >= 80:
            return PersonnelReadinessLevel.P3, percentage
        else:
            return PersonnelReadinessLevel.P4, percentage

    def translate_capability(
        self,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
    ) -> tuple[EquipmentReadinessLevel, list[str]]:
        """
        Translate contingency analysis to Capability (S) readiness.

        N-1/N-2 failures represent single points of failure in capabilities.

        Args:
            n1_pass: Whether system passes N-1 (single loss) test
            n2_pass: Whether system passes N-2 (double loss) test
            coverage_rate: Current coverage rate

        Returns:
            Tuple of (S-rating, list of deficiencies)
        """
        deficiencies = []

        if not n1_pass:
            deficiencies.append("Single Point of Failure: Any faculty loss causes service gaps")

        if not n2_pass:
            deficiencies.append("Dual Point of Failure: Two faculty losses cause critical gaps")

        if coverage_rate < 0.90:
            deficiencies.append(f"Coverage degraded: {coverage_rate*100:.0f}% vs 90% minimum")

        if not deficiencies:
            return EquipmentReadinessLevel.S1, deficiencies
        elif len(deficiencies) == 1 and n1_pass:
            return EquipmentReadinessLevel.S2, deficiencies
        elif n1_pass:
            return EquipmentReadinessLevel.S3, deficiencies
        else:
            return EquipmentReadinessLevel.S4, deficiencies

    def generate_sitrep_summary(
        self,
        drrs_rating: DRRSCategory,
        p_rating: PersonnelReadinessLevel,
        s_rating: EquipmentReadinessLevel,
        load_shedding_level: LoadSheddingLevel,
        deficiencies: list[str],
    ) -> str:
        """
        Generate a SITREP (Situational Report) style summary.

        This is the slide for the Morning Briefing that forces the Commander
        to stare at a giant "RED" status on their readiness dashboard.

        Args:
            drrs_rating: Overall DRRS category
            p_rating: Personnel readiness
            s_rating: Capability readiness
            load_shedding_level: Current sacrifice hierarchy level
            deficiencies: List of identified deficiencies

        Returns:
            Executive summary in military format
        """
        severity_word = {
            DRRSCategory.C1: "GREEN",
            DRRSCategory.C2: "AMBER",
            DRRSCategory.C3: "YELLOW",
            DRRSCategory.C4: "RED",
            DRRSCategory.C5: "BLACK",
        }

        status = severity_word.get(drrs_rating, "UNKNOWN")

        if drrs_rating in (DRRSCategory.C4, DRRSCategory.C5):
            template = (
                f"UNIT STATUS: {status}\n"
                f"Overall: {drrs_rating.value} | Personnel: {p_rating.value} | Capability: {s_rating.value}\n\n"
                f"MISSION IMPACT: Unit is Non-Mission Capable for standard operations. "
                f"Load shedding at {load_shedding_level.value} level. "
                f"Recommend immediate Cross-Leveling of assets or diversion of non-emergency cases.\n\n"
                f"DEFICIENCIES:\n"
            )
        elif drrs_rating == DRRSCategory.C3:
            template = (
                f"UNIT STATUS: {status}\n"
                f"Overall: {drrs_rating.value} | Personnel: {p_rating.value} | Capability: {s_rating.value}\n\n"
                f"MISSION IMPACT: Unit is Marginally Mission Capable. "
                f"Non-essential services suspended. Commander attention required.\n\n"
                f"DEFICIENCIES:\n"
            )
        else:
            template = (
                f"UNIT STATUS: {status}\n"
                f"Overall: {drrs_rating.value} | Personnel: {p_rating.value} | Capability: {s_rating.value}\n\n"
                f"MISSION IMPACT: Unit is Mission Capable with minor limitations.\n\n"
            )
            if not deficiencies:
                return template.strip()
            template += "WATCH ITEMS:\n"

        for deficiency in deficiencies:
            template += f"  - {deficiency}\n"

        return template.strip()


# =============================================================================
# MFR (Memorandum for Record) Generator
# =============================================================================


@dataclass
class MFRDocument:
    """A generated Memorandum for Record."""
    id: UUID
    generated_at: datetime
    mfr_type: MFRType
    priority: MFRPriority
    subject: str
    header: str
    body: str
    findings: list[str]
    risk_assessment: str
    recommendations: list[str]
    system_state_snapshot: dict[str, Any]
    document_hash: str
    risk_level: RiskLevel
    requires_commander_signature: bool
    distribution_list: list[str]


class MFRGenerator:
    """
    Generates Memoranda for Record for liability protection.

    When a Commander orders you to "make it work" with zero resources,
    you usually comply and take the blame when a patient gets hurt or
    residents burn out.

    This generator auto-creates formal MFRs stamped with the current
    timestamp and system state, putting the liability back on Command.

    "On [Date], the Scheduling System calculated a 98% probability of
    ACGME violation and a 'High' risk of patient safety errors. The
    Scheduler advised against this. This schedule was published under
    direct order/duress."
    """

    MFR_TEMPLATES = {
        MFRType.RISK_ACCEPTANCE: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Risk Acceptance - {subject}",
            "requires_signature": True,
            "distribution": ["Designated Institutional Official", "Risk Management", "Quality Assurance"],
        },
        MFRType.SAFETY_CONCERN: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Patient/Staff Safety Concern - {subject}",
            "requires_signature": True,
            "distribution": ["DIO", "Risk Management", "Patient Safety Officer", "Commander"],
        },
        MFRType.COMPLIANCE_VIOLATION: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: ACGME/DHA Compliance Concern - {subject}",
            "requires_signature": True,
            "distribution": ["Program Director", "DIO", "GME Office"],
        },
        MFRType.RESOURCE_REQUEST: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Resource Request Documentation - {subject}",
            "requires_signature": False,
            "distribution": ["Department Chief", "Resource Manager"],
        },
        MFRType.STAND_DOWN: {
            "header_template": "MEMORANDUM FOR RECORD\n\nSUBJECT: Safety Stand-Down Initiated - {subject}",
            "requires_signature": True,
            "distribution": ["Commander", "DIO", "Risk Management", "Patient Safety Officer"],
        },
    }

    def generate_mfr(
        self,
        mfr_type: MFRType,
        subject: str,
        system_state: SystemHealthState | dict[str, Any],
        scheduler_name: str,
        scheduler_objection: str | None = None,
        priority: MFRPriority = MFRPriority.ROUTINE,
        additional_findings: list[str] | None = None,
    ) -> MFRDocument:
        """
        Generate a Memorandum for Record.

        Args:
            mfr_type: Type of MFR
            subject: Subject line
            system_state: Current system state snapshot
            scheduler_name: Name of scheduler creating MFR
            scheduler_objection: Scheduler's documented objection
            priority: Urgency level
            additional_findings: Extra findings to include

        Returns:
            Generated MFR document
        """
        template = self.MFR_TEMPLATES[mfr_type]
        mfr_id = uuid4()
        now = datetime.now()

        # Generate header
        header = template["header_template"].format(subject=subject)
        header += f"\n\nDATE: {now.strftime('%d %B %Y')}"
        header += f"\nPRIORITY: {priority.value.upper()}"
        header += f"\nMFR ID: {mfr_id}"

        # Extract key metrics from system state
        findings = self._extract_findings(system_state, additional_findings)
        risk_level = self._assess_risk_level(system_state)
        risk_assessment = self._generate_risk_assessment(system_state, risk_level)

        # Generate body
        body = self._generate_body(
            mfr_type=mfr_type,
            system_state=system_state,
            scheduler_name=scheduler_name,
            scheduler_objection=scheduler_objection,
            findings=findings,
            now=now,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(mfr_type, system_state, risk_level)

        # Generate hash for immutability verification
        hash_content = f"{mfr_id}{now.isoformat()}{header}{body}"
        document_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        # Convert system_state to dict for snapshot
        state_snapshot = system_state.to_dict() if isinstance(system_state, SystemHealthState) else system_state

        return MFRDocument(
            id=mfr_id,
            generated_at=now,
            mfr_type=mfr_type,
            priority=priority,
            subject=subject,
            header=header,
            body=body,
            findings=findings,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            system_state_snapshot=state_snapshot,
            document_hash=document_hash,
            risk_level=risk_level,
            requires_commander_signature=template["requires_signature"],
            distribution_list=template["distribution"],
        )

    def _extract_findings(
        self,
        system_state: SystemHealthState | dict[str, Any],
        additional: list[str] | None,
    ) -> list[str]:
        """Extract findings from system state."""
        findings = []

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            n1_pass = system_state.n1_pass
            n2_pass = system_state.n2_pass
            load_level = system_state.load_shedding_level
            coverage = system_state.coverage_rate
            avg_load = system_state.average_allostatic_load
            eq_state = system_state.equilibrium_state
            phase_risk = system_state.phase_transition_risk
        else:
            n1_pass = system_state.get("n1_pass", True)
            n2_pass = system_state.get("n2_pass", True)
            load_level = system_state.get("load_shedding_level")
            coverage = system_state.get("coverage_rate", 1.0)
            avg_load = system_state.get("average_allostatic_load", 0)
            eq_state = system_state.get("equilibrium_state")
            phase_risk = system_state.get("phase_transition_risk", "low")

        # N-1/N-2 analysis
        if not n1_pass:
            findings.append(
                "N-1 VULNERABILITY: System will fail to maintain coverage if ANY single "
                "faculty member is unavailable. Single point of failure exists."
            )

        if not n2_pass:
            findings.append(
                "N-2 VULNERABILITY: System will fail catastrophically if two faculty "
                "members are simultaneously unavailable. Fatal pairs identified."
            )

        # Load shedding
        if load_level and load_level not in ("NORMAL", LoadSheddingLevel.NORMAL):
            findings.append(
                f"LOAD SHEDDING ACTIVE: Operating at {load_level} level. "
                f"Non-essential services have been suspended."
            )

        # Coverage
        if coverage < 0.90:
            findings.append(
                f"COVERAGE DEGRADED: Current coverage at {coverage*100:.0f}%, "
                f"below 90% minimum standard."
            )

        # Allostatic load
        if avg_load > 60:
            findings.append(
                f"STAFF OVERLOAD: Average allostatic load at {avg_load:.0f}/100. "
                f"Personnel are in chronic stress state."
            )

        # Equilibrium
        if eq_state in ("unsustainable", "critical", EquilibriumState.UNSUSTAINABLE, EquilibriumState.CRITICAL):
            findings.append(
                "UNSUSTAINABLE OPERATIONS: Current staffing model mathematically cannot "
                "be maintained. System will degrade further without intervention."
            )

        # Phase transition risk
        if phase_risk in ("high", "critical"):
            findings.append(
                f"PHASE TRANSITION RISK: {phase_risk.upper()}. System is approaching "
                "bifurcation point where small changes may cause catastrophic failure."
            )

        if additional:
            findings.extend(additional)

        return findings

    def _assess_risk_level(self, system_state: SystemHealthState | dict[str, Any]) -> RiskLevel:
        """Assess overall risk level from system state."""
        risk_score = 0

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            n1_pass = system_state.n1_pass
            n2_pass = system_state.n2_pass
            coverage = system_state.coverage_rate
            avg_load = system_state.average_allostatic_load
            eq_state = system_state.equilibrium_state
        else:
            n1_pass = system_state.get("n1_pass", True)
            n2_pass = system_state.get("n2_pass", True)
            coverage = system_state.get("coverage_rate", 1.0)
            avg_load = system_state.get("average_allostatic_load", 0)
            eq_state = system_state.get("equilibrium_state", "stable")

        if not n1_pass:
            risk_score += 3
        if not n2_pass:
            risk_score += 2

        if coverage < 0.70:
            risk_score += 4
        elif coverage < 0.80:
            risk_score += 3
        elif coverage < 0.90:
            risk_score += 2

        if avg_load > 80:
            risk_score += 3
        elif avg_load > 60:
            risk_score += 2

        if eq_state in ("critical", EquilibriumState.CRITICAL):
            risk_score += 4
        elif eq_state in ("unsustainable", EquilibriumState.UNSUSTAINABLE):
            risk_score += 3

        if risk_score >= 10:
            return RiskLevel.CATASTROPHIC
        elif risk_score >= 7:
            return RiskLevel.CRITICAL
        elif risk_score >= 4:
            return RiskLevel.HIGH
        elif risk_score >= 2:
            return RiskLevel.MODERATE
        return RiskLevel.LOW

    def _generate_risk_assessment(
        self,
        system_state: SystemHealthState | dict[str, Any],
        risk_level: RiskLevel,
    ) -> str:
        """Generate risk assessment narrative."""
        templates = {
            RiskLevel.CATASTROPHIC: (
                "RISK ASSESSMENT: CATASTROPHIC\n\n"
                "Multiple critical indicators suggest imminent system failure. "
                "Patient safety cannot be assured under current conditions. "
                "Immediate command intervention required. Any schedule published "
                "under these conditions represents acceptance of liability for "
                "preventable adverse outcomes."
            ),
            RiskLevel.CRITICAL: (
                "RISK ASSESSMENT: CRITICAL\n\n"
                "System is operating beyond safe parameters. High probability of "
                "adverse patient or staff outcomes if conditions persist. "
                "Command awareness is required before continuing operations."
            ),
            RiskLevel.HIGH: (
                "RISK ASSESSMENT: HIGH\n\n"
                "Significant deficiencies exist that increase likelihood of "
                "adverse outcomes. Continued operation requires documented risk "
                "acceptance and mitigation planning."
            ),
            RiskLevel.MODERATE: (
                "RISK ASSESSMENT: MODERATE\n\n"
                "Conditions are strained but manageable with vigilance. "
                "Monitoring recommended to prevent escalation."
            ),
            RiskLevel.LOW: (
                "RISK ASSESSMENT: LOW\n\n"
                "Operations are within normal parameters. Standard monitoring "
                "continues."
            ),
        }
        return templates.get(risk_level, "Risk level undetermined.")

    def _generate_body(
        self,
        mfr_type: MFRType,
        system_state: SystemHealthState | dict[str, Any],
        scheduler_name: str,
        scheduler_objection: str | None,
        findings: list[str],
        now: datetime,
    ) -> str:
        """Generate the body of the MFR."""
        body = f"\n\n1. PURPOSE: To document system conditions at {now.strftime('%H%M hours, %d %B %Y')}.\n\n"

        body += "2. BACKGROUND: The automated scheduling system continuously monitors "
        body += "staffing levels, coverage rates, and system health indicators. This "
        body += "memorandum documents conditions that warrant formal record.\n\n"

        body += "3. FINDINGS:\n"
        for i, finding in enumerate(findings, 1):
            body += f"   {chr(96+i)}. {finding}\n"

        if scheduler_objection:
            body += f"\n4. SCHEDULER OBJECTION:\n"
            body += f"   {scheduler_name} has documented the following objection:\n"
            body += f'   "{scheduler_objection}"\n\n'
            body += "5. "
        else:
            body += "\n4. "

        if mfr_type == MFRType.RISK_ACCEPTANCE:
            body += (
                "RISK ACCEPTANCE NOTICE: By approving or publishing the schedule "
                "under these documented conditions, the approving authority accepts "
                "responsibility for associated risks. The scheduling system has "
                "documented this as a 'Force Majeure' event.\n"
            )
        elif mfr_type == MFRType.STAND_DOWN:
            body += (
                "STAND-DOWN INITIATED: Due to conditions documented above, scheduling "
                "operations have been suspended pending command review. Patient safety "
                "operations continue. All non-emergency assignments are frozen.\n"
            )

        return body

    def _generate_recommendations(
        self,
        mfr_type: MFRType,
        system_state: SystemHealthState | dict[str, Any],
        risk_level: RiskLevel,
    ) -> list[str]:
        """Generate recommendations based on MFR type and risk level."""
        recs = []

        if risk_level in (RiskLevel.CRITICAL, RiskLevel.CATASTROPHIC):
            recs.append("IMMEDIATE: Notify Commander and DIO of conditions")
            recs.append("IMMEDIATE: Initiate Safety Stand-Down protocol if not already active")

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            n1_pass = system_state.n1_pass
            coverage = system_state.coverage_rate
            avg_load = system_state.average_allostatic_load
        else:
            n1_pass = system_state.get("n1_pass", True)
            coverage = system_state.get("coverage_rate", 1.0)
            avg_load = system_state.get("average_allostatic_load", 0)

        if not n1_pass:
            recs.append("Request cross-leveling of personnel from adjacent units")
            recs.append("Activate reserve/backup coverage pools")

        if coverage < 0.85:
            recs.append("Consider diversion of non-emergency cases to partner facilities")
            recs.append("Implement graduated return-to-normal coverage plan")

        if avg_load > 60:
            recs.append("Implement mandatory rest periods for high-load personnel")
            recs.append("Defer all non-essential administrative requirements")

        if mfr_type == MFRType.RESOURCE_REQUEST:
            recs.append("Submit Request for Forces (RFF) to DHA")
            recs.append("Document timeline to mission failure without resources")

        return recs


# =============================================================================
# Circuit Breaker (Safety Stand-Down)
# =============================================================================


@dataclass
class CircuitBreakerOverride:
    """An active override of the circuit breaker."""
    id: UUID
    authority: OverrideAuthority
    reason: str
    activated_at: datetime
    expires_at: datetime
    mfr_id: UUID | None = None


@dataclass
class CircuitBreakerStatus:
    """Current status of the circuit breaker."""
    state: CircuitBreakerState
    triggered_at: datetime | None
    trigger: CircuitBreakerTrigger | None
    trigger_details: str | None
    override: CircuitBreakerOverride | None
    locked_operations: list[str]
    allowed_operations: list[str]


class CircuitBreaker:
    """
    Scheduling Circuit Breaker - The Nuclear Option.

    In aviation, if safety metrics drop, the fleet is grounded.
    In medicine, we keep grinding.

    This circuit breaker implements a safety stop based on system health.
    When conditions are mathematically unsafe, it:
    - LOCKS the schedule
    - REFUSES to assign new shifts
    - TRIGGERS a Safety Stand-Down protocol
    - NOTIFIES the DIO and Risk Management

    The algorithm says no, citing "Patient Safety Priority 1.0",
    and refuses to let you break the law.
    """

    # Thresholds that trigger the circuit breaker
    THRESHOLDS = {
        "coverage_rate_critical": 0.70,
        "coverage_rate_warning": 0.85,
        "allostatic_load_critical": 80,
        "allostatic_load_warning": 60,
        "compensation_debt_critical": 1000,
        "positive_feedback_confidence": 0.8,
    }

    # Operations locked at each state
    LOCKED_OPERATIONS = {
        CircuitBreakerState.CLOSED: [],
        CircuitBreakerState.HALF_OPEN: [
            "new_assignments",
            "schedule_changes",
            "leave_approval",
        ],
        CircuitBreakerState.OPEN: [
            "new_assignments",
            "schedule_changes",
            "leave_approval",
            "fallback_deactivation",
            "load_shedding_reduction",
        ],
    }

    # Operations always allowed (patient safety)
    ALWAYS_ALLOWED = [
        "emergency_coverage",
        "patient_safety_assignment",
        "crisis_response",
        "view_schedule",
        "read_reports",
    ]

    def __init__(self):
        self.state = CircuitBreakerState.CLOSED
        self.triggered_at: datetime | None = None
        self.trigger: CircuitBreakerTrigger | None = None
        self.trigger_details: str | None = None
        self.override: CircuitBreakerOverride | None = None
        self.trip_count = 0
        self.last_trip: datetime | None = None

    def check_and_trip(
        self,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
        average_allostatic_load: float,
        volatility_level: str,
        compensation_debt: float,
        positive_feedback_risks: list[PositiveFeedbackRisk | dict] | None = None,
    ) -> tuple[bool, CircuitBreakerTrigger | None, str | None]:
        """
        Check conditions and trip circuit breaker if thresholds breached.

        Args:
            n1_pass: N-1 analysis result
            n2_pass: N-2 analysis result
            coverage_rate: Current coverage rate
            average_allostatic_load: Average faculty allostatic load
            volatility_level: Current volatility level
            compensation_debt: Accumulated compensation debt
            positive_feedback_risks: Detected positive feedback risks

        Returns:
            Tuple of (tripped, trigger, details)
        """
        if self.state == CircuitBreakerState.OPEN and not self._override_active():
            # Already tripped and no override
            return False, self.trigger, self.trigger_details

        trigger = None
        details = None

        # Check each threshold
        if not n1_pass:
            trigger = CircuitBreakerTrigger.N1_VIOLATION
            details = "N-1 analysis failed: Any single faculty loss causes service gaps"

        elif not n2_pass and coverage_rate < self.THRESHOLDS["coverage_rate_warning"]:
            trigger = CircuitBreakerTrigger.N2_VIOLATION
            details = "N-2 analysis failed with degraded coverage"

        elif coverage_rate < self.THRESHOLDS["coverage_rate_critical"]:
            trigger = CircuitBreakerTrigger.COVERAGE_COLLAPSE
            details = f"Coverage rate ({coverage_rate*100:.0f}%) below critical threshold (70%)"

        elif average_allostatic_load > self.THRESHOLDS["allostatic_load_critical"]:
            trigger = CircuitBreakerTrigger.ALLOSTATIC_OVERLOAD
            details = f"Average allostatic load ({average_allostatic_load:.0f}) exceeds critical threshold (80)"

        elif volatility_level in ("critical", "CRITICAL"):
            trigger = CircuitBreakerTrigger.VOLATILITY_CRITICAL
            details = "System volatility at critical level - phase transition risk"

        elif compensation_debt > self.THRESHOLDS["compensation_debt_critical"]:
            trigger = CircuitBreakerTrigger.COMPENSATION_DEBT_EXCEEDED
            details = f"Compensation debt ({compensation_debt:.0f}) exceeds sustainable threshold"

        elif positive_feedback_risks:
            # Handle both PositiveFeedbackRisk and dict
            high_confidence_risks = [
                r for r in positive_feedback_risks
                if (r.confidence if isinstance(r, PositiveFeedbackRisk) else r.get("confidence", 0))
                > self.THRESHOLDS["positive_feedback_confidence"]
            ]
            if high_confidence_risks:
                trigger = CircuitBreakerTrigger.POSITIVE_FEEDBACK_CASCADE
                details = f"High-confidence positive feedback risks detected: {len(high_confidence_risks)}"

        if trigger:
            self._trip(trigger, details)
            return True, trigger, details

        # Check if we can close from half-open
        if self.state == CircuitBreakerState.HALF_OPEN:
            if self._conditions_safe(coverage_rate, average_allostatic_load, n1_pass):
                self.close()

        return False, None, None

    def _trip(self, trigger: CircuitBreakerTrigger, details: str):
        """Trip the circuit breaker."""
        self.state = CircuitBreakerState.OPEN
        self.triggered_at = datetime.now()
        self.trigger = trigger
        self.trigger_details = details
        self.trip_count += 1
        self.last_trip = datetime.now()

        logger.critical(
            f"CIRCUIT BREAKER TRIPPED: {trigger.value} - {details}"
        )

    def _conditions_safe(
        self,
        coverage_rate: float,
        allostatic_load: float,
        n1_pass: bool,
    ) -> bool:
        """Check if conditions are safe to close breaker."""
        return (
            coverage_rate >= self.THRESHOLDS["coverage_rate_warning"]
            and allostatic_load < self.THRESHOLDS["allostatic_load_warning"]
            and n1_pass
        )

    def _override_active(self) -> bool:
        """Check if a valid override is active."""
        if not self.override:
            return False
        return datetime.now() < self.override.expires_at

    def close(self):
        """Close the circuit breaker (resume normal operations)."""
        self.state = CircuitBreakerState.CLOSED
        self.triggered_at = None
        self.trigger = None
        self.trigger_details = None
        self.override = None
        logger.info("Circuit breaker CLOSED - normal operations resumed")

    def half_open(self):
        """Set circuit breaker to half-open (limited operations)."""
        self.state = CircuitBreakerState.HALF_OPEN
        logger.info("Circuit breaker HALF-OPEN - limited operations")

    def override_breaker(
        self,
        authority: OverrideAuthority,
        reason: str,
        duration_hours: int = 8,
        mfr_id: UUID | None = None,
    ) -> CircuitBreakerOverride:
        """
        Override the circuit breaker.

        This creates a documented override that allows operations despite
        the trip. The override expires and generates an MFR.

        Args:
            authority: Who is authorizing the override
            reason: Why the override is needed
            duration_hours: How long the override lasts
            mfr_id: Associated MFR documenting the override

        Returns:
            The override record
        """
        now = datetime.now()
        self.override = CircuitBreakerOverride(
            id=uuid4(),
            authority=authority,
            reason=reason,
            activated_at=now,
            expires_at=now + timedelta(hours=duration_hours),
            mfr_id=mfr_id,
        )

        logger.warning(
            f"Circuit breaker OVERRIDE by {authority.value}: {reason} "
            f"(expires in {duration_hours} hours)"
        )

        return self.override

    def is_operation_allowed(self, operation: str) -> tuple[bool, str | None]:
        """
        Check if an operation is allowed given current state.

        Args:
            operation: Name of the operation to check

        Returns:
            Tuple of (allowed, reason_if_blocked)
        """
        # Always-allowed operations
        if operation in self.ALWAYS_ALLOWED:
            return True, None

        # If override is active, allow everything except patient-safety critical
        if self._override_active():
            return True, None

        # Check locked operations for current state
        locked = self.LOCKED_OPERATIONS.get(self.state, [])
        if operation in locked:
            return False, (
                f"HTTP 451 Unavailable For Legal Reasons: Operation '{operation}' "
                f"suspended per Patient Safety Protocol 1.0. Circuit breaker state: "
                f"{self.state.value}. Trigger: {self.trigger.value if self.trigger else 'None'}. "
                f"Contact Risk Management to override."
            )

        return True, None

    def get_status(self) -> CircuitBreakerStatus:
        """Get current circuit breaker status."""
        locked = self.LOCKED_OPERATIONS.get(self.state, [])

        return CircuitBreakerStatus(
            state=self.state,
            triggered_at=self.triggered_at,
            trigger=self.trigger,
            trigger_details=self.trigger_details,
            override=self.override,
            locked_operations=locked,
            allowed_operations=self.ALWAYS_ALLOWED.copy(),
        )


# =============================================================================
# RFF (Request for Forces) Drafter
# =============================================================================


@dataclass
class RFFDocument:
    """A generated Request for Forces document."""
    id: UUID
    generated_at: datetime
    requesting_unit: str
    uic: str | None
    mission_affected: list[MissionType]
    mos_required: list[str]
    personnel_count: int
    duration_days: int
    header: str
    situation: str
    mission_impact: str
    execution: str
    sustainment: str
    command_and_signal: str
    supporting_metrics: SupportingMetrics
    projected_without_support: ProjectionWithoutSupport
    document_hash: str


class RFFDrafter:
    """
    Drafts Request for Forces (RFF) documents.

    Since you can't hire in a military hospital, you have to "request assets."
    This is usually a painful manual process of filling out forms that get rejected.

    This drafter uses LeChatelier stress analysis to mathematically prove
    the need for Reservists or cross-leveled personnel. It speaks the language
    of the bureaucracy to unlock resources that "don't exist" for normal requests.

    "Based on cascade scenario projections, Department X will hit 'Extinction
    Vortex' in 14 days. Request activation of 2 Reservists or 3 GS-Civilians
    immediately to prevent mission failure."
    """

    def draft_rff(
        self,
        requesting_unit: str,
        mission_affected: list[MissionType],
        mos_required: list[str],
        personnel_count: int,
        duration_days: int,
        justification: str,
        system_state: SystemHealthState | dict[str, Any],
        cascade_prediction: CascadePrediction | dict[str, Any] | None = None,
        uic: str | None = None,
    ) -> RFFDocument:
        """
        Draft a Request for Forces document.

        Args:
            requesting_unit: Name of requesting unit/department
            mission_affected: Which missions are impacted
            mos_required: MOSs needed (e.g., "60H", "66H")
            personnel_count: Number of personnel requested
            duration_days: Duration of request
            justification: Text justification
            system_state: Current system metrics
            cascade_prediction: Optional cascade failure prediction
            uic: Unit Identification Code

        Returns:
            Generated RFF document
        """
        rff_id = uuid4()
        now = datetime.now()

        # Generate header
        header = self._generate_header(requesting_unit, now, rff_id, uic)

        # Generate SMEAC paragraphs (Situation, Mission, Execution, Admin, Command)
        situation = self._generate_situation(system_state, cascade_prediction)
        mission_impact = self._generate_mission_impact(mission_affected, system_state)
        execution = self._generate_execution(mos_required, personnel_count, duration_days)
        sustainment = self._generate_sustainment(duration_days)
        command_and_signal = self._generate_command()

        # Compile supporting metrics
        supporting_metrics = self._compile_metrics(system_state)

        # Generate projection without support
        projected_without = self._project_without_support(
            system_state, cascade_prediction, duration_days
        )

        # Generate hash
        hash_content = f"{rff_id}{now.isoformat()}{header}{situation}"
        document_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        return RFFDocument(
            id=rff_id,
            generated_at=now,
            requesting_unit=requesting_unit,
            uic=uic,
            mission_affected=mission_affected,
            mos_required=mos_required,
            personnel_count=personnel_count,
            duration_days=duration_days,
            header=header,
            situation=situation,
            mission_impact=mission_impact,
            execution=execution,
            sustainment=sustainment,
            command_and_signal=command_and_signal,
            supporting_metrics=supporting_metrics,
            projected_without_support=projected_without,
            document_hash=document_hash,
        )

    def _generate_header(
        self,
        unit: str,
        now: datetime,
        rff_id: UUID,
        uic: str | None,
    ) -> str:
        """Generate RFF header."""
        header = "REQUEST FOR FORCES (RFF)\n"
        header += "=" * 40 + "\n\n"
        header += f"DATE: {now.strftime('%d %B %Y')}\n"
        header += f"RFF ID: {rff_id}\n"
        header += f"REQUESTING UNIT: {unit}\n"
        if uic:
            header += f"UIC: {uic}\n"
        header += f"PRIORITY: IMMEDIATE\n"
        return header

    def _generate_situation(
        self,
        system_state: SystemHealthState | dict[str, Any],
        cascade_prediction: CascadePrediction | dict[str, Any] | None,
    ) -> str:
        """Generate Situation paragraph."""
        situation = "\n1. SITUATION:\n\n"

        situation += "   a. General: Unit experiencing critical personnel shortage "
        situation += "affecting mission capability.\n\n"

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            coverage = system_state.coverage_rate
            n1_pass = system_state.n1_pass
            load = system_state.average_allostatic_load
        else:
            coverage = system_state.get("coverage_rate", 1.0)
            n1_pass = system_state.get("n1_pass", True)
            load = system_state.get("average_allostatic_load", 0)

        situation += f"   b. Current Status:\n"
        situation += f"      - Coverage Rate: {coverage*100:.0f}%\n"

        if not n1_pass:
            situation += "      - N-1 Analysis: FAILED (single point of failure exists)\n"

        if load > 50:
            situation += f"      - Personnel Stress Level: {load:.0f}/100 (elevated)\n"

        if cascade_prediction:
            # Handle both CascadePrediction and dict
            if isinstance(cascade_prediction, CascadePrediction):
                days_to_failure = cascade_prediction.days_until_exhaustion
            else:
                days_to_failure = cascade_prediction.get("days_until_exhaustion", 999)

            if days_to_failure < 30:
                situation += f"\n   c. CRITICAL: Based on cascade analysis, unit will reach\n"
                situation += f"      mission failure state in {days_to_failure} days without intervention.\n"

        return situation

    def _generate_mission_impact(
        self,
        missions: list[MissionType],
        system_state: SystemHealthState | dict[str, Any],
    ) -> str:
        """Generate Mission Impact paragraph."""
        impact = "\n2. MISSION IMPACT:\n\n"

        impact += "   a. Affected Missions:\n"
        for mission in missions:
            impact += f"      - {mission.value.replace('_', ' ').title()}\n"

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            load_level = system_state.load_shedding_level
            eq_state = system_state.equilibrium_state
        else:
            load_level = system_state.get("load_shedding_level", "NORMAL")
            eq_state = system_state.get("equilibrium_state", "stable")

        if load_level not in ("NORMAL", LoadSheddingLevel.NORMAL):
            impact += f"\n   b. Current Load Shedding: {load_level}\n"
            impact += "      Non-essential services have been suspended.\n"

        if eq_state in ("unsustainable", "critical", EquilibriumState.UNSUSTAINABLE, EquilibriumState.CRITICAL):
            eq_str = eq_state.value if hasattr(eq_state, 'value') else str(eq_state)
            impact += f"\n   c. CRITICAL: Current operational tempo is {eq_str.upper()}.\n"
            impact += "      Unit cannot maintain mission without additional resources.\n"

        return impact

    def _generate_execution(
        self,
        mos_required: list[str],
        count: int,
        duration: int,
    ) -> str:
        """Generate Execution paragraph."""
        execution = "\n3. EXECUTION:\n\n"

        execution += "   a. Request:\n"
        execution += f"      - Personnel Count: {count}\n"
        execution += f"      - Duration: {duration} days\n"
        execution += f"      - MOS Required:\n"

        mos_desc = DRRSTranslator.MOS_DESCRIPTIONS
        for mos in mos_required:
            desc = mos_desc.get(mos, "Medical Personnel")
            execution += f"         * {mos} - {desc}\n"

        execution += "\n   b. Preferred Support:\n"
        execution += "      - Reserve Component activation\n"
        execution += "      - Cross-leveling from adjacent MTFs\n"
        execution += "      - GS-Civilian temporary hires (if authorized)\n"

        return execution

    def _generate_sustainment(self, duration: int) -> str:
        """Generate Sustainment (Admin/Logistics) paragraph."""
        sustainment = "\n4. SUSTAINMENT:\n\n"

        sustainment += "   a. Billeting: Requesting unit will provide\n"
        sustainment += "   b. Meals: Available at MTF dining facility\n"
        sustainment += f"   c. Duration: {duration} days with option to extend\n"
        sustainment += "   d. Travel: Requesting unit funds authorized\n"

        return sustainment

    def _generate_command(self) -> str:
        """Generate Command and Signal paragraph."""
        command = "\n5. COMMAND AND SIGNAL:\n\n"

        command += "   a. Command: OPCON to receiving MTF Commander\n"
        command += "   b. Reporting: Daily SITREP to originating unit\n"
        command += "   c. Signal: Standard MTF communications\n"

        return command

    def _compile_metrics(self, system_state: SystemHealthState | dict[str, Any]) -> SupportingMetrics:
        """Compile supporting metrics for the RFF."""
        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            return SupportingMetrics(
                coverage_rate=system_state.coverage_rate,
                n1_pass=system_state.n1_pass,
                n2_pass=system_state.n2_pass,
                load_shedding_level=str(system_state.load_shedding_level),
                average_allostatic_load=system_state.average_allostatic_load,
                equilibrium_state=str(system_state.equilibrium_state),
                compensation_debt=system_state.compensation_debt,
                snapshot_timestamp=datetime.now().isoformat(),
            )
        else:
            return SupportingMetrics(
                coverage_rate=system_state.get("coverage_rate"),
                n1_pass=system_state.get("n1_pass"),
                n2_pass=system_state.get("n2_pass"),
                load_shedding_level=str(system_state.get("load_shedding_level")),
                average_allostatic_load=system_state.get("average_allostatic_load"),
                equilibrium_state=str(system_state.get("equilibrium_state")),
                compensation_debt=system_state.get("compensation_debt"),
                snapshot_timestamp=datetime.now().isoformat(),
            )

    def _project_without_support(
        self,
        system_state: SystemHealthState | dict[str, Any],
        cascade_prediction: CascadePrediction | dict[str, Any] | None,
        duration: int,
    ) -> ProjectionWithoutSupport:
        """Project what happens without the requested support."""
        outcomes: list[str] = []

        days_to_fail = 999
        if cascade_prediction:
            if isinstance(cascade_prediction, CascadePrediction):
                days_to_fail = cascade_prediction.days_until_exhaustion
            else:
                days_to_fail = cascade_prediction.get("days_until_exhaustion", 999)

        mission_failure_likely = False
        if days_to_fail < duration:
            outcomes.append(
                f"Day {days_to_fail}: System exhaustion - compensation mechanisms fail"
            )
            outcomes.append(
                f"Day {days_to_fail + 7}: Estimated ACGME citation risk"
            )
            mission_failure_likely = True

        # Handle both SystemHealthState and dict
        if isinstance(system_state, SystemHealthState):
            load = system_state.average_allostatic_load
            n1_pass = system_state.n1_pass
        else:
            load = system_state.get("average_allostatic_load", 0)
            n1_pass = system_state.get("n1_pass", True)

        if load > 60:
            outcomes.append(
                "Ongoing: Faculty burnout accelerating - attrition risk elevated"
            )

        if not n1_pass:
            outcomes.append(
                "Continuous: Single faculty absence = immediate coverage gaps"
            )

        return ProjectionWithoutSupport(
            timeline_days=duration,
            outcomes=outcomes,
            mission_failure_likely=mission_failure_likely,
        )


# =============================================================================
# Iron Dome Service (Unified Interface)
# =============================================================================


class IronDomeService:
    """
    The Iron Dome - Unified MTF Compliance Service.

    Combines DRRS translation, MFR generation, circuit breaker, and RFF
    drafting into a single service that acts as your Regulatory Bodyguard.

    This service shields schedulers from the friction of a collapsing
    chain of command by weaponizing compliance documentation.
    """

    def __init__(self):
        self.translator = DRRSTranslator()
        self.mfr_generator = MFRGenerator()
        self.circuit_breaker = CircuitBreaker()
        self.rff_drafter = RFFDrafter()

        # Document storage (in production, this would be database-backed)
        self.mfr_history: list[MFRDocument] = []
        self.rff_history: list[RFFDocument] = []

    def assess_readiness(
        self,
        load_shedding_level: LoadSheddingLevel,
        equilibrium_state: EquilibriumState,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
        available_faculty: int,
        required_faculty: int,
        overloaded_faculty_count: int = 0,
    ) -> dict[str, Any]:
        """
        Perform full DRRS readiness assessment.

        Returns military-formatted readiness report (the SITREP).
        """
        # Translate each component
        drrs_rating, drrs_explanation = self.translator.translate_load_shedding(
            load_shedding_level
        )

        p_rating, personnel_pct = self.translator.translate_personnel_strength(
            available_faculty, required_faculty, overloaded_faculty_count
        )

        s_rating, deficiencies = self.translator.translate_capability(
            n1_pass, n2_pass, coverage_rate
        )

        # Generate summary
        summary = self.translator.generate_sitrep_summary(
            drrs_rating, p_rating, s_rating, load_shedding_level, deficiencies
        )

        # Determine overall capability
        if drrs_rating in (DRRSCategory.C4, DRRSCategory.C5):
            capability = MissionCapabilityStatus.NMC
        elif drrs_rating == DRRSCategory.C3:
            capability = MissionCapabilityStatus.PMC
        else:
            capability = MissionCapabilityStatus.FMC

        return {
            "overall_rating": drrs_rating.value,
            "overall_capability": capability.value,
            "personnel_rating": p_rating.value,
            "personnel_percentage": personnel_pct,
            "capability_rating": s_rating.value,
            "deficiencies": deficiencies,
            "load_shedding_level": load_shedding_level.value if hasattr(load_shedding_level, 'value') else str(load_shedding_level),
            "equilibrium_state": equilibrium_state.value if hasattr(equilibrium_state, 'value') else str(equilibrium_state),
            "executive_summary": summary,
        }

    def check_circuit_breaker(
        self,
        n1_pass: bool,
        n2_pass: bool,
        coverage_rate: float,
        average_allostatic_load: float,
        volatility_level: str,
        compensation_debt: float,
        positive_feedback_risks: list[PositiveFeedbackRisk | dict] | None = None,
    ) -> dict[str, Any]:
        """
        Check circuit breaker and trip if thresholds breached.

        Returns current status and any trip information.
        """
        tripped, trigger, details = self.circuit_breaker.check_and_trip(
            n1_pass=n1_pass,
            n2_pass=n2_pass,
            coverage_rate=coverage_rate,
            average_allostatic_load=average_allostatic_load,
            volatility_level=volatility_level,
            compensation_debt=compensation_debt,
            positive_feedback_risks=positive_feedback_risks,
        )

        status = self.circuit_breaker.get_status()

        return {
            "tripped": tripped,
            "state": status.state.value,
            "trigger": trigger.value if trigger else None,
            "trigger_details": details,
            "locked_operations": status.locked_operations,
            "allowed_operations": status.allowed_operations,
            "override_active": self.circuit_breaker._override_active(),
        }

    def generate_risk_mfr(
        self,
        subject: str,
        system_state: SystemHealthState | dict[str, Any],
        scheduler_name: str,
        scheduler_objection: str | None = None,
    ) -> MFRDocument:
        """
        Generate a risk acceptance MFR.

        Called when publishing a schedule under dangerous conditions.
        """
        mfr = self.mfr_generator.generate_mfr(
            mfr_type=MFRType.RISK_ACCEPTANCE,
            subject=subject,
            system_state=system_state,
            scheduler_name=scheduler_name,
            scheduler_objection=scheduler_objection,
            priority=MFRPriority.PRIORITY,
        )

        self.mfr_history.append(mfr)
        return mfr

    def initiate_safety_stand_down(
        self,
        reason: str,
        initiator: str,
        system_state: SystemHealthState | dict[str, Any],
    ) -> tuple[MFRDocument, dict[str, Any]]:
        """
        Initiate a safety stand-down.

        This trips the circuit breaker and generates documentation.
        """
        # Trip circuit breaker manually
        self.circuit_breaker._trip(
            CircuitBreakerTrigger.MANUAL_ACTIVATION,
            f"Safety stand-down initiated by {initiator}: {reason}"
        )

        # Generate MFR
        mfr = self.mfr_generator.generate_mfr(
            mfr_type=MFRType.STAND_DOWN,
            subject=f"Safety Stand-Down: {reason}",
            system_state=system_state,
            scheduler_name=initiator,
            priority=MFRPriority.IMMEDIATE,
        )

        self.mfr_history.append(mfr)

        status = self.circuit_breaker.get_status()

        return mfr, {
            "stand_down_active": True,
            "circuit_breaker_state": status.state.value,
            "locked_operations": status.locked_operations,
            "mfr_id": str(mfr.id),
        }

    def draft_resource_request(
        self,
        requesting_unit: str,
        mission_affected: list[MissionType],
        mos_required: list[str],
        personnel_count: int,
        duration_days: int,
        justification: str,
        system_state: SystemHealthState | dict[str, Any],
        cascade_prediction: CascadePrediction | dict[str, Any] | None = None,
    ) -> RFFDocument:
        """
        Draft a Request for Forces document.
        """
        rff = self.rff_drafter.draft_rff(
            requesting_unit=requesting_unit,
            mission_affected=mission_affected,
            mos_required=mos_required,
            personnel_count=personnel_count,
            duration_days=duration_days,
            justification=justification,
            system_state=system_state,
            cascade_prediction=cascade_prediction,
        )

        self.rff_history.append(rff)
        return rff

    def get_status(self) -> dict[str, Any]:
        """Get overall Iron Dome status."""
        cb_status = self.circuit_breaker.get_status()

        return {
            "circuit_breaker_state": cb_status.state.value,
            "scheduling_locked": cb_status.state == CircuitBreakerState.OPEN,
            "override_active": self.circuit_breaker._override_active(),
            "trigger": cb_status.trigger.value if cb_status.trigger else None,
            "mfrs_generated": len(self.mfr_history),
            "rffs_generated": len(self.rff_history),
            "locked_operations": cb_status.locked_operations,
        }
