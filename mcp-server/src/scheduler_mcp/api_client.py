"""
API client for connecting MCP tools to FastAPI backend.

This module provides async HTTP client functionality for MCP tools
to call the FastAPI backend instead of accessing the database directly.
"""

import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class APIConfig(BaseModel):
    """Configuration for API client."""

    base_url: str = "http://localhost:8000"
    timeout: float = 30.0
    api_prefix: str = "/api/v1"
    username: str = "admin"
    password: str = "admin123"


class SchedulerAPIClient:
    """Async client for FastAPI backend with authentication."""

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig(
            base_url=os.environ.get("API_BASE_URL", "http://localhost:8000"),
            username=os.environ.get("API_USERNAME", "admin"),
            password=os.environ.get("API_PASSWORD", "admin123"),
        )
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = None

    async def __aenter__(self) -> "SchedulerAPIClient":
        self._client = httpx.AsyncClient(
            base_url=self.config.base_url, timeout=self.config.timeout
        )
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client, raising if not initialized."""
        if self._client is None:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    async def _ensure_authenticated(self) -> dict[str, str]:
        """Ensure we have a valid token and return auth headers."""
        if self._token is None:
            await self._login()
        return {"Authorization": f"Bearer {self._token}"}

    async def _login(self) -> None:
        """Authenticate and get a JWT token."""
        response = await self.client.post(
            f"{self.config.api_prefix}/auth/login/json",
            json={"username": self.config.username, "password": self.config.password},
        )
        response.raise_for_status()
        data = response.json()
        self._token = data["access_token"]
        logger.info("Successfully authenticated with backend API")

    async def health_check(self) -> bool:
        """Check if FastAPI backend is available."""
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def validate_schedule(
        self, start_date: str, end_date: str, checks: list[str] | None = None
    ) -> dict[str, Any]:
        """Validate schedule via API (ACGME compliance check)."""
        # Note: Uses GET /schedule/validate endpoint (not POST /schedules/validate)
        response = await self.client.get(
            f"{self.config.api_prefix}/schedule/validate",
            params={"start_date": start_date, "end_date": end_date},
        )
        response.raise_for_status()
        return response.json()

    async def get_conflicts(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Get schedule conflicts via API (conflict analysis)."""
        # Note: Uses GET /conflicts/analyze endpoint (requires auth)
        headers = await self._ensure_authenticated()
        response = await self.client.get(
            f"{self.config.api_prefix}/conflicts/analyze",
            headers=headers,
            params={"start_date": start_date, "end_date": end_date},
        )
        response.raise_for_status()
        return response.json()

    async def get_swap_candidates(self, person_id: str, block_id: str) -> dict[str, Any]:
        """Get swap candidates via API.

        NOTE: The backend endpoint /schedule/swaps/find requires file upload
        which isn't suitable for MCP. This method is a placeholder until a
        simpler API endpoint is added. Currently returns NotImplementedError.
        """
        # The actual endpoint POST /schedule/swaps/find requires Excel file upload
        # A simpler JSON-based endpoint is needed for MCP integration
        raise NotImplementedError(
            "Swap candidates API requires file upload. "
            "Use mock implementation in tools.py until backend supports JSON-only endpoint."
        )

    async def run_contingency_analysis(
        self, scenario: str, affected_ids: list[str], start_date: str, end_date: str
    ) -> dict[str, Any]:
        """Run contingency analysis via resilience vulnerability endpoint.

        NOTE: Uses GET /resilience/vulnerability which provides N-1/N-2 analysis.
        The scenario and affected_ids parameters are not used by current backend.
        """
        headers = await self._ensure_authenticated()
        response = await self.client.get(
            f"{self.config.api_prefix}/resilience/vulnerability",
            headers=headers,
            params={"start_date": start_date, "end_date": end_date},
        )
        response.raise_for_status()
        return response.json()

    async def generate_schedule(
        self,
        start_date: str,
        end_date: str,
        algorithm: str = "greedy",
        timeout_seconds: float = 60.0,
        clear_existing: bool = True,
    ) -> dict[str, Any]:
        """
        Generate a schedule for the given date range.

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            algorithm: Scheduling algorithm ('greedy', 'cp_sat', 'pulp', 'hybrid')
            timeout_seconds: Maximum solver runtime (5-300 seconds)
            clear_existing: If True, clears existing assignments in date range first

        Returns:
            Schedule generation result with assignments and validation
        """
        headers = await self._ensure_authenticated()

        # Clear existing assignments if requested
        if clear_existing:
            logger.info(f"Clearing existing assignments from {start_date} to {end_date}")
            delete_response = await self.client.delete(
                f"{self.config.api_prefix}/assignments",
                headers=headers,
                params={"start_date": start_date, "end_date": end_date},
            )
            if delete_response.status_code == 200:
                deleted = delete_response.json().get("deleted", 0)
                logger.info(f"Cleared {deleted} existing assignments")

        # Generate new schedule
        logger.info(f"Generating schedule from {start_date} to {end_date} using {algorithm}")
        response = await self.client.post(
            f"{self.config.api_prefix}/schedule/generate",
            headers=headers,
            json={
                "start_date": start_date,
                "end_date": end_date,
                "algorithm": algorithm,
                "timeout_seconds": timeout_seconds,
            },
            timeout=max(timeout_seconds + 30, self.config.timeout),
        )
        response.raise_for_status()
        return response.json()

    async def get_assignments(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get assignments, optionally filtered by date range."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        response = await self.client.get(
            f"{self.config.api_prefix}/assignments",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_people(self, limit: int = 100) -> dict[str, Any]:
        """Get all people (residents and faculty)."""
        headers = await self._ensure_authenticated()
        response = await self.client.get(
            f"{self.config.api_prefix}/people",
            headers=headers,
            params={"limit": limit},
        )
        response.raise_for_status()
        return response.json()


# Module-level client instance
_api_client: SchedulerAPIClient | None = None


async def get_api_client() -> SchedulerAPIClient:
    """Get or create API client instance."""
    global _api_client
    if _api_client is None:
        _api_client = SchedulerAPIClient()
        await _api_client.__aenter__()
    return _api_client


async def close_api_client() -> None:
    """Close the API client if open."""
    global _api_client
    if _api_client is not None:
        await _api_client.__aexit__(None, None, None)
        _api_client = None
