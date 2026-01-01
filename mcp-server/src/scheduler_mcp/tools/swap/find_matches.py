"""
Find swap matches tool for discovering compatible swap candidates.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_person_id, validate_positive_int


class FindSwapMatchesRequest(BaseModel):
    """Request to find swap matches."""

    person_id: str = Field(..., description="Person requesting the swap")
    assignment_id: str | None = Field(
        default=None,
        description="Optional specific assignment to swap",
    )
    block_id: str | None = Field(
        default=None,
        description="Optional specific block to find candidates for",
    )
    max_candidates: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum candidates to return",
    )


class SwapCandidate(BaseModel):
    """A swap candidate."""

    person_id: str
    person_name: str | None = None
    assignment_id: str
    block_date: str
    block_session: str
    compatibility_score: float = Field(ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)


class FindSwapMatchesResponse(BaseModel):
    """Response from find swap matches."""

    person_id: str
    total_candidates: int
    candidates: list[SwapCandidate]


class FindSwapMatchesTool(
    BaseTool[FindSwapMatchesRequest, FindSwapMatchesResponse]
):
    """
    Tool for finding compatible swap candidates.

    Auto-matches based on preferences, availability, and qualifications.
    """

    @property
    def name(self) -> str:
        return "find_swap_matches"

    @property
    def description(self) -> str:
        return (
            "Find compatible swap candidates for a person. "
            "Auto-matches based on preferences, availability, and ACGME compliance."
        )

    def validate_input(self, **kwargs: Any) -> FindSwapMatchesRequest:
        """Validate input parameters."""
        # Validate person_id
        person_id = validate_person_id(kwargs.get("person_id", ""))

        # Validate optional IDs
        assignment_id = kwargs.get("assignment_id")
        if assignment_id is not None:
            assignment_id = validate_person_id(assignment_id, "assignment_id")

        block_id = kwargs.get("block_id")
        if block_id is not None:
            block_id = validate_person_id(block_id, "block_id")

        # Validate max candidates
        max_candidates = validate_positive_int(
            kwargs.get("max_candidates", 10),
            field_name="max_candidates",
            max_value=100,
        )

        return FindSwapMatchesRequest(
            person_id=person_id,
            assignment_id=assignment_id,
            block_id=block_id,
            max_candidates=max_candidates,
        )

    async def execute(
        self, request: FindSwapMatchesRequest
    ) -> FindSwapMatchesResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Find matches via API
            result = await client.get_swap_candidates(
                person_id=request.person_id,
                assignment_id=request.assignment_id,
                block_id=request.block_id,
                max_candidates=request.max_candidates,
            )

            # Parse candidates
            candidates = []
            for item in result.get("candidates", []):
                candidate = SwapCandidate(
                    person_id=item["person_id"],
                    person_name=item.get("person_name"),
                    assignment_id=item["assignment_id"],
                    block_date=item["block_date"],
                    block_session=item["block_session"],
                    compatibility_score=item.get("compatibility_score", 0.0),
                    reasons=item.get("reasons", []),
                )
                candidates.append(candidate)

            return FindSwapMatchesResponse(
                person_id=request.person_id,
                total_candidates=len(candidates),
                candidates=candidates,
            )

        except Exception:
            # Return empty result on error
            return FindSwapMatchesResponse(
                person_id=request.person_id,
                total_candidates=0,
                candidates=[],
            )
