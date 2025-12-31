"""
Check supervision tool for ACGME supervision ratio compliance.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_string


class SupervisionCheckRequest(BaseModel):
    """Request to check supervision ratios."""

    date: str = Field(..., description="Date to check in YYYY-MM-DD format")
    session: str = Field(..., description="Session to check (AM or PM)")


class SupervisionRatio(BaseModel):
    """Supervision ratio for a level."""

    level: str  # PGY-1, PGY-2, PGY-3, etc.
    residents: int
    faculty: int
    required_faculty: int
    ratio: str
    compliant: bool


class SupervisionCheckResponse(BaseModel):
    """Response from supervision check."""

    date: str
    session: str
    overall_compliant: bool
    ratios: list[SupervisionRatio]
    total_residents: int
    total_faculty: int


class CheckSupervisionTool(
    BaseTool[SupervisionCheckRequest, SupervisionCheckResponse]
):
    """
    Tool for checking ACGME supervision ratio compliance.

    Validates supervision ratios:
    - PGY-1: 1 faculty per 2 residents
    - PGY-2/3: 1 faculty per 4 residents
    """

    @property
    def name(self) -> str:
        return "check_supervision"

    @property
    def description(self) -> str:
        return (
            "Check ACGME supervision ratio compliance. "
            "Validates faculty-to-resident ratios for each training level."
        )

    def validate_input(self, **kwargs: Any) -> SupervisionCheckRequest:
        """Validate input parameters."""
        # Validate date
        date_value = validate_date_string(kwargs.get("date", ""))

        # Validate session
        session = kwargs.get("session", "").upper()
        if session not in ["AM", "PM"]:
            from ..base import ValidationError

            raise ValidationError(
                "session must be AM or PM",
                details={"value": session},
            )

        return SupervisionCheckRequest(
            date=date_value,
            session=session,
        )

    async def execute(
        self, request: SupervisionCheckRequest
    ) -> SupervisionCheckResponse:
        """
        Execute ACGME supervision ratio compliance check.

        Validates faculty-to-resident ratios for each PGY level to ensure adequate
        supervision per ACGME requirements. Ratios vary by training level to reflect
        increasing autonomy.

        ACGME Supervision Requirements:
        - PGY-1: 1 faculty per 2 residents (1:2 ratio)
        - PGY-2: 1 faculty per 4 residents (1:4 ratio)
        - PGY-3: 1 faculty per 4 residents (1:4 ratio)

        Args:
            request: Validated request with specific date and session (AM/PM)

        Returns:
            SupervisionCheckResponse with per-level ratios and overall compliance

        Raises:
            APIError: Backend API request fails
            ValidationError: Invalid date or session
        """
        client = self._require_api_client()

        try:
            # Check supervision via API client
            data = await client.check_supervision(
                date=request.date,
                session=request.session,
            )

            # Parse ratios
            ratios = []
            for item in data.get("ratios", []):
                ratio = SupervisionRatio(
                    level=item["level"],
                    residents=item["residents"],
                    faculty=item["faculty"],
                    required_faculty=item["required_faculty"],
                    ratio=item["ratio"],
                    compliant=item["compliant"],
                )
                ratios.append(ratio)

            # Check overall compliance
            overall_compliant = all(r.compliant for r in ratios)

            return SupervisionCheckResponse(
                date=request.date,
                session=request.session,
                overall_compliant=overall_compliant,
                ratios=ratios,
                total_residents=data.get("total_residents", 0),
                total_faculty=data.get("total_faculty", 0),
            )

        except (ConnectionError, TimeoutError) as e:
            # Network connectivity issues
            return SupervisionCheckResponse(
                date=request.date,
                session=request.session,
                overall_compliant=False,
                ratios=[],
                total_residents=0,
                total_faculty=0,
            )
        except KeyError as e:
            # Missing required data fields
            return SupervisionCheckResponse(
                date=request.date,
                session=request.session,
                overall_compliant=False,
                ratios=[],
                total_residents=0,
                total_faculty=0,
            )
        except Exception as e:
            # Unexpected errors
            return SupervisionCheckResponse(
                date=request.date,
                session=request.session,
                overall_compliant=False,
                ratios=[],
                total_residents=0,
                total_faculty=0,
            )
