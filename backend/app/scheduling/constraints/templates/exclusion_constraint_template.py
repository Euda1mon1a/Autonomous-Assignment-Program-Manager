"""Exclusion Constraint Template

Constraints for preventing certain assignments together.

Examples:
    - Adjuncts cannot take call
    - Faculty cannot work in unavailable rotations
    - Ineligible residents cannot work specialty clinics
"""

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
)


class ExclusionConstraintTemplate(HardConstraint):
    """Template for exclusion constraints."""

    def __init__(self):
        super().__init__(
            name="ExclusionConstraint",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )
        self.excluded_person_type = None  # 'adjunct', 'new_faculty', etc.
        self.excluded_rotation_types = []  # Rotations excluded for type
        self.excluded_combinations = []  # (person_type, rotation) tuples

    def validate(
        self,
        assignments: list,
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate exclusion constraints."""
        violations = []

        for assignment in assignments:
            person = self._get_person(assignment.person_id, context)
            rotation = self._get_rotation(assignment.rotation_id, context)

            # Check person type exclusions
            if self._should_be_excluded(person, rotation):
                violations.append(
                    {
                        "constraint_name": self.name,
                        "message": f"{self.excluded_person_type} cannot work {rotation.name}",
                        "person_id": assignment.person_id,
                        "rotation_id": assignment.rotation_id,
                    }
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _should_be_excluded(self, person, rotation):
        """Check if person-rotation combination is excluded."""
        # Check person type
        if self._matches_person_type(person):
            # Check if rotation is excluded
            if rotation.type in self.excluded_rotation_types:
                return True

        # Check specific combinations
        for excluded_type, excluded_rotation in self.excluded_combinations:
            if self._matches_person_type(person, excluded_type):
                if rotation.type == excluded_rotation:
                    return True

        return False

    def _matches_person_type(self, person, person_type=None):
        """Check if person matches type."""
        check_type = person_type or self.excluded_person_type
        if check_type == "adjunct":
            return person.faculty_type == "ADJUNCT"
        elif check_type == "new":
            return person.is_new
        return False

    def _get_person(self, person_id, context):
        """Get person object."""
        for person in context.residents + context.faculty:
            if person.id == person_id:
                return person
        return None

    def _get_rotation(self, rotation_id, context):
        """Get rotation object."""
        for rotation in context.templates:
            if rotation.id == rotation_id:
                return rotation
        return None

    def add_to_cpsat(self, model, variables, context):
        """
        Add exclusion constraint to CP-SAT model.

        For each excluded person-rotation combination, sets the assignment
        variable to 0 (forbidden).

        Args:
            model: OR-Tools CP-SAT model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with persons and rotations
        """
        x = variables.get("assignments", {})
        if not x:
            return

        # Identify excluded persons
        excluded_person_ids = set()
        for person in context.residents + context.faculty:
            if self._matches_person_type(person):
                excluded_person_ids.add(person.id)

            # Also check specific combinations
            for excluded_type, _ in self.excluded_combinations:
                if self._matches_person_type(person, excluded_type):
                    excluded_person_ids.add(person.id)

        if not excluded_person_ids:
            return

        # Build person to index mapping
        person_to_idx = {}
        for person in context.residents:
            person_to_idx[person.id] = context.resident_idx[person.id]
        for person in context.faculty:
            person_to_idx[person.id] = context.faculty_idx[person.id]

        # For each excluded person, forbid assignments to excluded rotations
        for person_id in excluded_person_ids:
            if person_id not in person_to_idx:
                continue

            p_i = person_to_idx[person_id]
            person = self._get_person(person_id, context)

            # Forbid assignments for this person
            for key in x:
                if key[0] != p_i:
                    continue

                # Check if this rotation is excluded for this person
                # key[1] is the block index
                for block in context.blocks:
                    if context.block_idx[block.id] == key[1]:
                        # Check each template/rotation
                        for template in context.templates:
                            rotation = template
                            if self._should_be_excluded(person, rotation):
                                model.Add(x[key] == 0)
                                break
                        break

    def add_to_pulp(self, model, variables, context):
        """
        Add exclusion constraint to PuLP model.

        For each excluded person-rotation combination, sets the assignment
        variable to 0 (forbidden).

        Args:
            model: PuLP model
            variables: Dict containing 'assignments' decision variables
            context: SchedulingContext with persons and rotations
        """
        x = variables.get("assignments", {})
        if not x:
            return

        # Identify excluded persons
        excluded_person_ids = set()
        for person in context.residents + context.faculty:
            if self._matches_person_type(person):
                excluded_person_ids.add(person.id)

            # Also check specific combinations
            for excluded_type, _ in self.excluded_combinations:
                if self._matches_person_type(person, excluded_type):
                    excluded_person_ids.add(person.id)

        if not excluded_person_ids:
            return

        # Build person to index mapping
        person_to_idx = {}
        for person in context.residents:
            person_to_idx[person.id] = context.resident_idx[person.id]
        for person in context.faculty:
            person_to_idx[person.id] = context.faculty_idx[person.id]

        constraint_count = 0
        # For each excluded person, forbid assignments to excluded rotations
        for person_id in excluded_person_ids:
            if person_id not in person_to_idx:
                continue

            p_i = person_to_idx[person_id]
            person = self._get_person(person_id, context)

            # Forbid assignments for this person
            for key in x:
                if key[0] != p_i:
                    continue

                # Check if this rotation is excluded for this person
                for block in context.blocks:
                    if context.block_idx[block.id] == key[1]:
                        for template in context.templates:
                            rotation = template
                            if self._should_be_excluded(person, rotation):
                                model += (
                                    x[key] == 0,
                                    f"exclusion_{person_id}_{constraint_count}"
                                )
                                constraint_count += 1
                                break
                        break
