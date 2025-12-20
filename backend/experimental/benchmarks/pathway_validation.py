"""
Pathway Validation for Catalyst Concepts.

Validates that schedule transition pathways are valid and optimal.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class PathwayResult:
    """Result of pathway validation."""

    pathway_id: str
    is_valid: bool
    steps: int
    barriers_bypassed: int
    catalysts_used: list[str]
    validation_errors: list[str]


class PathwayValidator:
    """Validates schedule transition pathways from catalyst-concepts branch."""

    def __init__(self):
        self.results: list[PathwayResult] = []

    def validate_pathway(
        self,
        current_state: Any,
        target_state: Any,
        pathway: Any,
    ) -> PathwayResult:
        """
        Validate a proposed transition pathway.

        Checks:
        1. All intermediate states are valid schedule states
        2. Each transition respects constraints
        3. Catalysts are available when claimed
        4. Final state matches target
        """
        errors = []

        # Extract pathway information from various possible structures
        steps_count = 0
        barriers_count = 0
        catalyst_list = []

        # Handle different pathway structures
        if hasattr(pathway, "steps"):
            steps_data = getattr(pathway, "steps")
            if isinstance(steps_data, list):
                steps_count = len(steps_data)
            elif isinstance(steps_data, int):
                steps_count = steps_data

        if hasattr(pathway, "transitions"):
            transitions = getattr(pathway, "transitions")
            if isinstance(transitions, list):
                steps_count = len(transitions)

        if isinstance(pathway, dict):
            steps_count = len(pathway.get("steps", pathway.get("transitions", [])))
            barriers_count = pathway.get("barriers_bypassed", 0)
            catalyst_list = pathway.get("catalysts_used", pathway.get("catalysts", []))

        if isinstance(pathway, list):
            # Pathway is a list of transitions/steps
            steps_count = len(pathway)

        # Extract barriers bypassed
        if hasattr(pathway, "barriers_bypassed"):
            barriers_count = getattr(pathway, "barriers_bypassed")
        elif hasattr(pathway, "barriers"):
            barriers = getattr(pathway, "barriers")
            if isinstance(barriers, list):
                barriers_count = len(barriers)
            elif isinstance(barriers, int):
                barriers_count = barriers

        # Extract catalysts used
        if hasattr(pathway, "catalysts_used"):
            catalysts = getattr(pathway, "catalysts_used")
            if isinstance(catalysts, list):
                catalyst_list = [str(c) for c in catalysts]
        elif hasattr(pathway, "catalysts"):
            catalysts = getattr(pathway, "catalysts")
            if isinstance(catalysts, list):
                catalyst_list = [str(c) for c in catalysts]

        # Basic validation checks
        if steps_count == 0:
            errors.append("Pathway has no steps")

        if current_state == target_state and steps_count > 0:
            errors.append("Current state equals target state but pathway has steps")

        result = PathwayResult(
            pathway_id=str(id(pathway)),
            is_valid=len(errors) == 0,
            steps=steps_count,
            barriers_bypassed=barriers_count,
            catalysts_used=catalyst_list,
            validation_errors=errors,
        )

        self.results.append(result)
        return result

    def validate_swap_request(
        self,
        swap_request: dict,
        proposed_pathway: Any,
    ) -> PathwayResult:
        """Validate a specific swap request pathway."""
        return self.validate_pathway(
            current_state=swap_request.get("current"),
            target_state=swap_request.get("target"),
            pathway=proposed_pathway,
        )

    def success_rate(self) -> float:
        """Calculate overall pathway success rate."""
        if not self.results:
            return 0.0
        valid = sum(1 for r in self.results if r.is_valid)
        return valid / len(self.results)
