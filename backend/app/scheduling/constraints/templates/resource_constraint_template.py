"""
Resource Constraint Template

Resource constraints regulate allocation of limited resources like
clinic slots, faculty time, facilities, etc.

Examples:
    - Clinic capacity limits
    - Faculty availability/workload limits
    - Facility/room availability
    - Equipment sharing constraints
"""

from typing import Any

from app.scheduling.constraints.base import (
    ConstraintPriority,
    ConstraintResult,
    ConstraintType,
    HardConstraint,
    SchedulingContext,
)


class ResourceConstraintTemplate(HardConstraint):
    """
    Template for resource constraints.

    Resource constraints ensure that limited resources are not over-allocated.

    Resources:
        - clinic_slots: Fixed number of clinic positions available
        - faculty_capacity: Faculty available hours
        - room_availability: Rooms available for assignments
        - equipment: Specialized equipment needed

    Examples:
        >>> constraint = ResourceConstraintTemplate()
        >>> constraint.resource_type = 'clinic'
        >>> constraint.max_capacity = 4  # Max 4 residents per clinic
        >>> constraint.resource_id = clinic_uuid
    """

    def __init__(self) -> None:
        """Initialize resource constraint."""
        super().__init__(
            name="ResourceConstraint",
            constraint_type=ConstraintType.CAPACITY,
            priority=ConstraintPriority.HIGH,
        )
        self.resource_type = None  # 'clinic', 'faculty', 'room', etc.
        self.resource_id = None  # UUID of specific resource
        self.max_capacity = None  # Maximum allocation
        self.min_utilization = 0  # Minimum usage requirement

    def _get_resource_allocation(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> dict[Any, int]:
        """Count allocations per resource."""
        allocation = {}

        for assignment in assignments:
            resource_key = self._get_resource_key(assignment, context)

            if resource_key not in allocation:
                allocation[resource_key] = 0

            allocation[resource_key] += 1

        return allocation

    def _get_resource_key(self, assignment: Any, context: SchedulingContext) -> Any:
        """Extract resource identifier from assignment."""
        # Override in subclasses to return appropriate key
        if self.resource_type == "clinic":
            return assignment.clinic_id
        elif self.resource_type == "faculty":
            return assignment.faculty_id
        else:
            return assignment.resource_id

    def add_to_cpsat(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add resource constraint to CP-SAT model."""
        x = variables.get("assignments", {})

        # Group assignments by resource
        for resource_id in self._get_resources(context):
            resource_assignments = self._get_assignments_for_resource(
                resource_id, context
            )

            # Create sum variable for resource usage
            usage_sum = sum(
                x.get((res.id, block.id), 0)
                for res in resource_assignments
                for block in context.blocks
            )

            # Add capacity constraint
            if self.max_capacity:
                model.Add(usage_sum <= self.max_capacity)

            # Add minimum utilization constraint
            if self.min_utilization:
                model.Add(usage_sum >= self.min_utilization)

    def add_to_pulp(
        self,
        model: Any,
        variables: dict[str, Any],
        context: SchedulingContext,
    ) -> None:
        """Add resource constraint to PuLP model."""
        x = variables.get("assignments", {})

        for resource_id in self._get_resources(context):
            resource_assignments = self._get_assignments_for_resource(
                resource_id, context
            )

            # Create sum for resource usage
            usage_sum = sum(
                x.get((res.id, block.id), 0)
                for res in resource_assignments
                for block in context.blocks
            )

            # Add capacity constraint
            if self.max_capacity:
                model += usage_sum <= self.max_capacity

            # Add minimum utilization constraint
            if self.min_utilization:
                model += usage_sum >= self.min_utilization

    def validate(
        self,
        assignments: list[Any],
        context: SchedulingContext,
    ) -> ConstraintResult:
        """Validate resource constraints."""
        violations = []

        # Count allocations per resource
        allocation = self._get_resource_allocation(assignments, context)

        for resource_id, count in allocation.items():
            # Check maximum capacity
            if self.max_capacity and count > self.max_capacity:
                violations.append(
                    type(
                        "ConstraintViolation",
                        (),
                        {
                            "constraint_name": self.name,
                            "constraint_type": self.constraint_type,
                            "severity": "HIGH",
                            "message": f"Resource {resource_id} over capacity: "
                            f"{count} > {self.max_capacity}",
                            "details": {"count": count, "capacity": self.max_capacity},
                        },
                    )()
                )

            # Check minimum utilization
            if self.min_utilization and count < self.min_utilization:
                violations.append(
                    type(
                        "ConstraintViolation",
                        (),
                        {
                            "constraint_name": self.name,
                            "constraint_type": self.constraint_type,
                            "severity": "MEDIUM",
                            "message": f"Resource {resource_id} under-utilized: "
                            f"{count} < {self.min_utilization}",
                            "details": {
                                "count": count,
                                "minimum": self.min_utilization,
                            },
                        },
                    )()
                )

        return ConstraintResult(
            satisfied=len(violations) == 0,
            violations=violations,
        )

    def _get_resources(self, context: SchedulingContext) -> list[Any]:
        """Get list of relevant resources."""
        if self.resource_type == "clinic":
            return getattr(context, "clinics", [])
        elif self.resource_type == "faculty":
            return context.faculty
        else:
            return []

    def _get_assignments_for_resource(
        self,
        resource_id: Any,
        context: SchedulingContext,
    ) -> list[Any]:
        """Get assignments for specific resource."""
        # Override in subclasses
        return []
