"""
Get early warnings tool for detecting burnout precursors.
"""

from typing import Any

from pydantic import BaseModel, Field

from ..base import BaseTool
from ..validator import validate_date_range


class EarlyWarning(BaseModel):
    """An early warning signal."""

    signal_type: str  # STA/LTA, SPC, Fire_Index
    severity: str  # low, medium, high, critical
    person_id: str | None = None
    person_name: str | None = None
    date: str
    value: float
    threshold: float
    message: str


class GetEarlyWarningsRequest(BaseModel):
    """Request to get early warnings."""

    start_date: str = Field(..., description="Start date in YYYY-MM-DD format")
    end_date: str = Field(..., description="End date in YYYY-MM-DD format")
    signal_types: list[str] | None = Field(
        default=None,
        description="Filter by signal types",
    )


class GetEarlyWarningsResponse(BaseModel):
    """Response from get early warnings."""

    start_date: str
    end_date: str
    total_warnings: int
    critical_count: int
    high_count: int
    warnings: list[EarlyWarning]


class GetEarlyWarningsTool(
    BaseTool[GetEarlyWarningsRequest, GetEarlyWarningsResponse]
):
    """
    Tool for getting early warning signals.

    Detects burnout precursors using STA/LTA, SPC, and Fire Index.
    """

    @property
    def name(self) -> str:
        return "get_early_warnings"

    @property
    def description(self) -> str:
        return (
            "Get early warning signals for burnout precursors. "
            "Uses STA/LTA seismic detection, SPC charts, and Fire Index."
        )

    def validate_input(self, **kwargs: Any) -> GetEarlyWarningsRequest:
        """Validate input parameters."""
        # Validate dates
        start_date = kwargs.get("start_date", "")
        end_date = kwargs.get("end_date", "")
        validate_date_range(start_date, end_date, max_days=365)

        # Validate signal types
        signal_types = kwargs.get("signal_types")
        if signal_types is not None:
            valid_types = ["STA/LTA", "SPC", "Fire_Index"]
            if not isinstance(signal_types, list):
                signal_types = [signal_types]
            for st in signal_types:
                if st not in valid_types:
                    from ..base import ValidationError

                    raise ValidationError(
                        f"Invalid signal type: {st}",
                        details={"value": st, "valid": valid_types},
                    )

        return GetEarlyWarningsRequest(
            start_date=start_date,
            end_date=end_date,
            signal_types=signal_types,
        )

    async def execute(
        self, request: GetEarlyWarningsRequest
    ) -> GetEarlyWarningsResponse:
        """Execute the tool."""
        client = self._require_api_client()

        try:
            # Build params
            params: dict[str, Any] = {
                "start_date": request.start_date,
                "end_date": request.end_date,
            }
            if request.signal_types:
                params["signal_types"] = ",".join(request.signal_types)

            # Get early warnings via API
            result = await client.client.get(
                f"{client.config.api_prefix}/resilience/early-warnings",
                headers=await client._ensure_authenticated(),
                params=params,
            )
            result.raise_for_status()
            data = result.json()

            # Parse warnings
            warnings = []
            for item in data.get("warnings", []):
                warning = EarlyWarning(
                    signal_type=item["signal_type"],
                    severity=item["severity"],
                    person_id=item.get("person_id"),
                    person_name=item.get("person_name"),
                    date=item["date"],
                    value=item["value"],
                    threshold=item["threshold"],
                    message=item["message"],
                )
                warnings.append(warning)

            # Count by severity
            critical_count = sum(1 for w in warnings if w.severity == "critical")
            high_count = sum(1 for w in warnings if w.severity == "high")

            return GetEarlyWarningsResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_warnings=len(warnings),
                critical_count=critical_count,
                high_count=high_count,
                warnings=warnings,
            )

        except Exception:
            # Return empty result
            return GetEarlyWarningsResponse(
                start_date=request.start_date,
                end_date=request.end_date,
                total_warnings=0,
                critical_count=0,
                high_count=0,
                warnings=[],
            )
