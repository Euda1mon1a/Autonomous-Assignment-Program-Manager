"""
API client for connecting MCP tools to FastAPI backend.

This module provides async HTTP client functionality for MCP tools
to call the FastAPI backend instead of accessing the database directly.
"""

import os
from typing import Any

import httpx
from pydantic import BaseModel


class APIConfig(BaseModel):
    """Configuration for API client."""

    base_url: str = "http://localhost:8000"
    timeout: float = 30.0
    api_prefix: str = "/api/v1"


class SchedulerAPIClient:
    """Async client for FastAPI backend."""

    def __init__(self, config: APIConfig | None = None):
        self.config = config or APIConfig(
            base_url=os.environ.get("API_BASE_URL", "http://localhost:8000")
        )
        self._client: httpx.AsyncClient | None = None

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
        """Validate schedule via API."""
        response = await self.client.post(
            f"{self.config.api_prefix}/schedules/validate",
            json={"start_date": start_date, "end_date": end_date, "checks": checks or ["all"]},
        )
        response.raise_for_status()
        return response.json()

    async def get_conflicts(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Get schedule conflicts via API."""
        response = await self.client.get(
            f"{self.config.api_prefix}/conflicts",
            params={"start_date": start_date, "end_date": end_date},
        )
        response.raise_for_status()
        return response.json()

    async def get_swap_candidates(self, person_id: str, block_id: str) -> dict[str, Any]:
        """Get swap candidates via API."""
        response = await self.client.get(
            f"{self.config.api_prefix}/swaps/candidates",
            params={"person_id": person_id, "block_id": block_id},
        )
        response.raise_for_status()
        return response.json()

    async def run_contingency_analysis(
        self, scenario: str, affected_ids: list[str], start_date: str, end_date: str
    ) -> dict[str, Any]:
        """Run contingency analysis via API."""
        response = await self.client.post(
            f"{self.config.api_prefix}/resilience/contingency",
            json={
                "scenario": scenario,
                "affected_person_ids": affected_ids,
                "start_date": start_date,
                "end_date": end_date,
            },
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
