"""
Get swap history tool for retrieving swap records.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_person_id, validate_positive_int


class SwapRecord(BaseModel):
    """A swap record."""

    id: str
    swap_type: str
    status: str  # pending, approved, executed, rolled_back, rejected
    person_id: str
    person_name: str | None = None
    assignment_id: str
    target_person_id: str | None = None
    target_person_name: str | None = None
    created_at: str
    executed_at: str | None = None
    rolled_back_at: str | None = None


class GetSwapHistoryRequest(BaseModel):
    """Request to get swap history."""

    person_id: str | None = Field(
        default=None,
        description="Optional person ID to filter by",
    )
    status: str | None = Field(
        default=None,
        description="Optional status filter",
    )
    limit: int = Field(
        default=50,
        ge=1,
        le=500,
        description="Maximum records to return",
    )


class GetSwapHistoryResponse(BaseModel):
    """Response from get swap history."""

    total_records: int
    records: list[SwapRecord]


class GetSwapHistoryTool(
    BaseTool[GetSwapHistoryRequest, GetSwapHistoryResponse]
):
    """
    Tool for retrieving swap history.

    Fetches swap records with optional filtering by person and status.
    """

    @property
    def name(self) -> str:
        return "get_swap_history"

    @property
    def description(self) -> str:
        return (
            "Get swap history records. "
            "Can filter by person and status."
        )

    def validate_input(self, **kwargs: Any) -> GetSwapHistoryRequest:
        """Validate input parameters."""
        # Validate person_id if provided
        person_id = kwargs.get("person_id")
        if person_id is not None:
            person_id = validate_person_id(person_id)

        # Validate status if provided
        status = kwargs.get("status")
        if status is not None:
            valid_statuses = [
                "pending",
                "approved",
                "executed",
                "rolled_back",
                "rejected",
            ]
            if status not in valid_statuses:
                from ..base import ValidationError

                raise ValidationError(
                    f"Invalid status: {status}",
                    details={"value": status, "valid": valid_statuses},
                )

        # Validate limit
        limit = validate_positive_int(
            kwargs.get("limit", 50),
            field_name="limit",
            max_value=500,
        )

        return GetSwapHistoryRequest(
            person_id=person_id,
            status=status,
            limit=limit,
        )

    async def execute(
        self, request: GetSwapHistoryRequest
    ) -> GetSwapHistoryResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Build params
            params: dict[str, Any] = {
                "limit": request.limit,
            }
            if request.person_id:
                params["person_id"] = request.person_id
            if request.status:
                params["status"] = request.status

            # Get swap history via API
            result = await client.client.get(
                f"{client.config.api_prefix}/swaps",
                headers=await client._ensure_authenticated(),
                params=params,
            )
            result.raise_for_status()
            data = result.json()

            # Parse records
            records = []
            for item in data.get("swaps", []):
                record = SwapRecord(
                    id=item["id"],
                    swap_type=item["swap_type"],
                    status=item["status"],
                    person_id=item["person_id"],
                    person_name=item.get("person_name"),
                    assignment_id=item["assignment_id"],
                    target_person_id=item.get("target_person_id"),
                    target_person_name=item.get("target_person_name"),
                    created_at=item["created_at"],
                    executed_at=item.get("executed_at"),
                    rolled_back_at=item.get("rolled_back_at"),
                )
                records.append(record)

            return GetSwapHistoryResponse(
                total_records=len(records),
                records=records,
            )

        except Exception:
            # Return empty result on error
            return GetSwapHistoryResponse(
                total_records=0,
                records=[],
            )
