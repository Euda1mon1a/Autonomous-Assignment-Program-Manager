"""
Family Medicine scheduling constraints.

Belt & suspenders validation for expansion service rules:
- LEC-PM on Wednesday PM for non-exempt rotations
- Continuity clinic (C) for PGY-1 on Wednesday AM
- Night float AM slot patterns (OFF-AM, clinic, etc.)
"""

from typing import Any

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    ConstraintViolation,
    HardConstraint,
)

# Exempt rotations that don't get LEC-PM on Wednesday
LEC_EXEMPT_ROTATIONS = frozenset(
    [
        "NF",
        "NF-PM",
        "NF-ENDO",
        "NEURO-NF",
        "PNF",
        "LDNF",
        "KAPI-LD",
        "HILO",
        "TDY",
    ]
)

# Night float rotations that get OFF-AM
NIGHT_FLOAT_ROTATIONS = frozenset(
    [
        "NF",
        "NF-PM",
        "NF-ENDO",
        "NEURO-NF",
        "PNF",
    ]
)

WEDNESDAY = 2  # Python weekday


class WednesdayPMLecConstraint(HardConstraint):
    """
    Wednesday PM = LEC-PM for non-exempt rotations.

    Residents on non-exempt rotations must have LEC-PM (lecture)
    assigned to their Wednesday PM slot.
    """

    def __init__(self) -> None:
        super().__init__(
            name="WednesdayPMLec",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _is_wednesday_pm(self, block: Any) -> bool:
        return (
            hasattr(block, "date")
            and block.date.weekday() == WEDNESDAY
            and getattr(block, "time_of_day", None) == "PM"
        )

    def _is_exempt_rotation(self, template: Any) -> bool:
        abbrev = getattr(template, "abbreviation", "").upper()
        return abbrev in LEC_EXEMPT_ROTATIONS

    def add_to_cpsat(self, model: Any, variables: dict[str, Any], context: Any) -> None:
        """Add constraint to CP-SAT model (validation-focused, expansion handles assignment)."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        # Find LEC-PM template
        lec_template = None
        for t in context.templates:
            if getattr(t, "abbreviation", "").upper() == "LEC-PM":
                lec_template = t
                break

        if not lec_template:
            return  # No LEC-PM template, skip constraint

        lec_t_i = context.template_idx.get(lec_template.id)
        if lec_t_i is None:
            return

        for block in context.blocks:
            if not self._is_wednesday_pm(block):
                continue

            b_i = context.block_idx.get(block.id)
            if b_i is None:
                continue

            for resident in context.residents:
                r_i = context.resident_idx.get(resident.id)
                if r_i is None:
                    continue

                # Expansion service already sets LEC-PM for non-exempt rotations
                # This constraint validates consistency
                if (r_i, b_i, lec_t_i) in template_vars:
                    pass  # Solver will verify consistency

    def add_to_pulp(self, model: Any, variables: dict[str, Any], context: Any) -> None:
        """Add constraint to PuLP model (validation-focused)."""
        pass  # Expansion service handles assignment

    def validate(self, assignments: list[Any], context: Any) -> ConstraintResult:
        """Validate that Wednesday PM assignments are LEC-PM for non-exempt rotations."""
        violations = []
        for a in assignments:
            block = getattr(a, "block", None)
            template = getattr(a, "rotation_template", None)

            if not block or not template:
                continue

            if self._is_wednesday_pm(block) and not self._is_exempt_rotation(template):
                abbrev = getattr(template, "abbreviation", "").upper()
                if abbrev != "LEC-PM":
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            message=f"Wednesday PM should be LEC-PM, got {abbrev}",
                            entity_id=str(getattr(a, "id", "unknown")),
                            severity="error",
                        )
                    )

        return ConstraintResult(satisfied=len(violations) == 0, violations=violations)


class InternContinuityConstraint(HardConstraint):
    """
    PGY-1 Wednesday AM = C (continuity clinic).

    Interns must have continuity clinic on Wednesday mornings.
    """

    def __init__(self) -> None:
        super().__init__(
            name="InternContinuity",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _is_wednesday_am(self, block: Any) -> bool:
        return (
            hasattr(block, "date")
            and block.date.weekday() == WEDNESDAY
            and getattr(block, "time_of_day", None) == "AM"
        )

    def add_to_cpsat(self, model: Any, variables: dict[str, Any], context: Any) -> None:
        """Add constraint to CP-SAT model (validation-focused)."""
        template_vars = variables.get("template_assignments", {})
        if not template_vars:
            return

        # Find continuity clinic template (C or CONT)
        cont_template = None
        for t in context.templates:
            abbrev = getattr(t, "abbreviation", "").upper()
            if abbrev in ("C", "CONT", "CONTINUITY"):
                cont_template = t
                break

        if not cont_template:
            return

        cont_t_i = context.template_idx.get(cont_template.id)
        if cont_t_i is None:
            return

        # Get PGY-1 residents
        pgy1_residents = {
            r.id for r in context.residents if getattr(r, "pgy_level", 0) == 1
        }

        for block in context.blocks:
            if not self._is_wednesday_am(block):
                continue

            b_i = context.block_idx.get(block.id)
            if b_i is None:
                continue

            for resident in context.residents:
                if resident.id not in pgy1_residents:
                    continue

                r_i = context.resident_idx.get(resident.id)
                if r_i is None:
                    continue

                # Expansion service handles this, constraint validates
                pass

    def add_to_pulp(self, model: Any, variables: dict[str, Any], context: Any) -> None:
        """Add constraint to PuLP model (validation-focused)."""
        pass

    def validate(self, assignments: list[Any], context: Any) -> ConstraintResult:
        """Validate PGY-1 Wednesday AM assignments are continuity clinic."""
        violations = []
        for a in assignments:
            block = getattr(a, "block", None)
            template = getattr(a, "rotation_template", None)
            resident = getattr(a, "resident", None)

            if not block or not template or not resident:
                continue

            pgy = getattr(resident, "pgy_level", 0)
            if pgy != 1:
                continue

            if self._is_wednesday_am(block):
                abbrev = getattr(template, "abbreviation", "").upper()
                if abbrev not in ("C", "CONT", "CONTINUITY"):
                    violations.append(
                        ConstraintViolation(
                            constraint_name=self.name,
                            message=f"PGY-1 Wed AM should be continuity, got {abbrev}",
                            entity_id=str(getattr(a, "id", "unknown")),
                            severity="error",
                        )
                    )

        return ConstraintResult(satisfied=len(violations) == 0, violations=violations)


class NightFloatSlotConstraint(HardConstraint):
    """
    Night float residents get NF in both AM and PM slots (except days off).

    Residents on night float rotations should have NF-variant activity
    in both AM and PM slots, with exceptions only for actual days off.
    The expansion service handles the specific AM/PM patterns per rotation.
    """

    # AM patterns by rotation - what AM slot should be for each NF type
    # Based on expansion service NIGHT_FLOAT_PATTERNS
    NIGHT_FLOAT_AM_PATTERNS: dict[str, str] = {
        "NF": "OFF-AM",  # Regular NF: off in morning (sleeping)
        "NF-PM": "OFF-AM",
        "NF-ENDO": "OFF-AM",
        "NEURO-NF": "NEURO",  # Neuro NF: neuro clinic in morning
        "PNF": "OFF-AM",  # Peds NF: off in morning
        "LDNF": "L&D",  # L&D NF: L&D both AM and PM
        "KAPI-LD": "KAP",  # Kapi L&D: Kapi both AM and PM
    }

    def __init__(self) -> None:
        super().__init__(
            name="NightFloatSlot",
            constraint_type=ConstraintType.ROTATION,
            priority=ConstraintPriority.HIGH,
        )

    def _is_am_slot(self, block: Any) -> bool:
        return getattr(block, "time_of_day", None) == "AM"

    def add_to_cpsat(self, model: Any, variables: dict[str, Any], context: Any) -> None:
        """Add constraint to CP-SAT model (validation-focused)."""
        # Expansion service handles assignment, constraint validates
        pass

    def add_to_pulp(self, model: Any, variables: dict[str, Any], context: Any) -> None:
        """Add constraint to PuLP model (validation-focused)."""
        pass

    def validate(self, assignments: list[Any], context: Any) -> ConstraintResult:
        """Validate night float AM slots match expected patterns."""
        violations = []

        # Build map of resident -> block rotation (from PM slots)
        resident_rotations: dict[tuple[Any, Any], str] = {}
        for a in assignments:
            resident = getattr(a, "resident", None)
            block = getattr(a, "block", None)
            template = getattr(a, "rotation_template", None)

            if not (resident and block and template):
                continue

            time_of_day = getattr(block, "time_of_day", None)
            if time_of_day != "PM":
                continue

            abbrev = getattr(template, "abbreviation", "").upper()
            if abbrev in NIGHT_FLOAT_ROTATIONS:
                key = (resident.id, getattr(block, "date", None))
                resident_rotations[key] = abbrev

        # Check AM slots for night float residents
        for a in assignments:
            block = getattr(a, "block", None)
            template = getattr(a, "rotation_template", None)
            resident = getattr(a, "resident", None)

            if not block or not template or not resident:
                continue

            if not self._is_am_slot(block):
                continue

            key = (resident.id, getattr(block, "date", None))
            if key not in resident_rotations:
                continue

            nf_rotation = resident_rotations[key]
            expected_am = self.NIGHT_FLOAT_AM_PATTERNS.get(nf_rotation)
            if not expected_am:
                continue

            actual_abbrev = getattr(template, "abbreviation", "").upper()
            if actual_abbrev != expected_am:
                violations.append(
                    ConstraintViolation(
                        constraint_name=self.name,
                        message=f"{nf_rotation} AM should be {expected_am}, got {actual_abbrev}",
                        entity_id=str(getattr(a, "id", "unknown")),
                        severity="error",
                    )
                )

        return ConstraintResult(satisfied=len(violations) == 0, violations=violations)
