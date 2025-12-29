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
    username: str = ""  # REQUIRED: Set via API_USERNAME env var
    password: str = ""  # REQUIRED: Set via API_PASSWORD env var


class SchedulerAPIClient:
    """Async client for FastAPI backend with authentication."""

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig(
            base_url=os.environ.get("API_BASE_URL", "http://localhost:8000"),
            username=os.environ.get("API_USERNAME", ""),
            password=os.environ.get("API_PASSWORD", ""),
        )
        if not self.config.username or not self.config.password:
            raise ValueError(
                "API_USERNAME and API_PASSWORD environment variables are required. "
                "Set these in your .env file or docker-compose environment."
            )
        self._client: httpx.AsyncClient | None = None
        self._token: str | None = None

    async def __aenter__(self) -> "SchedulerAPIClient":
        self._client = httpx.AsyncClient(base_url=self.config.base_url, timeout=self.config.timeout)
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

    async def get_swap_candidates(
        self,
        person_id: str,
        assignment_id: str | None = None,
        block_id: str | None = None,
        max_candidates: int = 10,
    ) -> dict[str, Any]:
        """Get swap candidates via JSON-based API.

        Uses the /schedule/swaps/candidates endpoint which queries the database
        directly without requiring file upload.

        Args:
            person_id: ID of the person requesting the swap
            assignment_id: Optional specific assignment to swap
            block_id: Optional specific block to find candidates for
            max_candidates: Maximum number of candidates to return

        Returns:
            SwapCandidateJsonResponse with ranked candidates
        """
        headers = await self._ensure_authenticated()
        response = await self.client.post(
            f"{self.config.api_prefix}/schedule/swaps/candidates",
            headers=headers,
            json={
                "person_id": person_id,
                "assignment_id": assignment_id,
                "block_id": block_id,
                "max_candidates": max_candidates,
            },
        )
        response.raise_for_status()
        return response.json()

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

    async def get_mtf_compliance(self, check_circuit_breaker: bool = True) -> dict[str, Any]:
        """Get MTF compliance status using the Iron Dome service.

        Returns DRRS readiness ratings, circuit breaker status, and compliance data.

        Args:
            check_circuit_breaker: Whether to include circuit breaker check

        Returns:
            MTF compliance response with:
            - drrs_category: C1-C5 readiness rating
            - mission_capability: FMC/PMC/NMC
            - personnel_rating: P1-P4
            - capability_rating: S1-S4
            - circuit_breaker: Circuit breaker status
            - executive_summary: SITREP-style narrative
            - deficiencies: List of specific issues
            - iron_dome_status: green/yellow/red
            - severity: healthy/warning/critical/emergency
        """
        headers = await self._ensure_authenticated()
        response = await self.client.get(
            f"{self.config.api_prefix}/resilience/mtf-compliance",
            headers=headers,
            params={"check_circuit_breaker": check_circuit_breaker},
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
