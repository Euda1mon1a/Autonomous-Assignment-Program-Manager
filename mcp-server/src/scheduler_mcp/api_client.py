"""
API client for connecting MCP tools to FastAPI backend.

This module provides async HTTP client functionality for MCP tools
to call the FastAPI backend instead of accessing the database directly.
"""

import asyncio
import logging
import os
from typing import Any

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # seconds
RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}


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

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        max_retries: int = DEFAULT_MAX_RETRIES,
        _token_refreshed: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make HTTP request with exponential backoff retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: URL to request
            max_retries: Maximum number of retry attempts
            _token_refreshed: Internal flag to prevent infinite token refresh loop
            **kwargs: Additional arguments to pass to httpx request

        Returns:
            httpx.Response

        Raises:
            httpx.HTTPError: If all retries fail
        """
        last_exception = None

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.request(method, url, **kwargs)

                # Handle 401 Unauthorized - try token refresh once
                if response.status_code == 401 and not _token_refreshed:
                    logger.warning("Received 401 Unauthorized, attempting token refresh")
                    self._token = None  # Clear stale token
                    new_headers = await self._ensure_authenticated()
                    kwargs["headers"] = new_headers
                    return await self._request_with_retry(
                        method, url, max_retries=max_retries, _token_refreshed=True, **kwargs
                    )

                # Don't retry on success or client errors (4xx except 408, 429)
                if response.status_code < 400:
                    return response
                if 400 <= response.status_code < 500 and response.status_code not in RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                    return response

                # Retry on server errors and specific client errors
                if attempt < max_retries and response.status_code in RETRYABLE_STATUS_CODES:
                    delay = DEFAULT_RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Request failed with status {response.status_code}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()
                return response

            except httpx.RequestError as e:
                last_exception = e
                if attempt < max_retries:
                    delay = DEFAULT_RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Request failed with error: {e}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(delay)
                    continue
                raise

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        raise httpx.HTTPError(f"All {max_retries} retry attempts failed")

    async def health_check(self) -> bool:
        """Check if FastAPI backend is available."""
        try:
            response = await self._request_with_retry("GET", "/health", max_retries=1)
            return response.status_code == 200
        except (httpx.RequestError, httpx.HTTPError):
            return False

    async def validate_schedule(
        self, start_date: str, end_date: str, checks: list[str] | None = None
    ) -> dict[str, Any]:
        """Validate schedule via API (ACGME compliance check)."""
        # Note: Uses GET /schedule/validate endpoint (not POST /schedules/validate)
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/schedule/validate",
            params={"start_date": start_date, "end_date": end_date},
        )
        response.raise_for_status()
        return response.json()

    async def validate_schedule_by_id(
        self,
        schedule_id: str,
        constraint_config: str = "default",
        include_suggestions: bool = True,
    ) -> dict[str, Any]:
        """Validate a specific schedule by ID.

        Args:
            schedule_id: Schedule identifier (UUID or alphanumeric)
            constraint_config: Constraint configuration (default, minimal, strict, resilience)
            include_suggestions: Include suggested actions for issues

        Returns:
            Validation results with compliance rate and issues
        """
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/schedules/validate",
            headers=headers,
            json={
                "schedule_id": schedule_id,
                "constraint_config": constraint_config,
                "include_suggestions": include_suggestions,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_conflicts(self, start_date: str, end_date: str) -> dict[str, Any]:
        """Get schedule conflicts via API (conflict analysis)."""
        # Note: Uses GET /conflicts/analysis/analyze endpoint (requires auth)
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/conflicts/analysis/analyze",
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
        response = await self._request_with_retry(
            "POST",
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
        response = await self._request_with_retry(
            "GET",
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
            delete_response = await self._request_with_retry(
                "DELETE",
                f"{self.config.api_prefix}/assignments",
                headers=headers,
                params={"start_date": start_date, "end_date": end_date},
            )
            if delete_response.status_code == 200:
                deleted = delete_response.json().get("deleted", 0)
                logger.info(f"Cleared {deleted} existing assignments")

        # Generate new schedule
        logger.info(f"Generating schedule from {start_date} to {end_date} using {algorithm}")
        response = await self._request_with_retry(
            "POST",
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

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/assignments",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_people(self, limit: int = 100) -> dict[str, Any]:
        """Get all people (residents and faculty)."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
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
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/resilience/mtf-compliance",
            headers=headers,
            params={"check_circuit_breaker": check_circuit_breaker},
        )
        response.raise_for_status()
        return response.json()

    # ==================== ASSIGNMENT CRUD METHODS ====================

    async def create_assignment(
        self,
        person_id: str,
        block_date: str,
        block_session: str,
        rotation_id: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new schedule assignment."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/assignments",
            headers=headers,
            json={
                "person_id": person_id,
                "block_date": block_date,
                "block_session": block_session,
                "rotation_id": rotation_id,
                "notes": notes,
            },
        )
        response.raise_for_status()
        return response.json()

    async def update_assignment(
        self,
        assignment_id: str,
        person_id: str | None = None,
        rotation_id: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing assignment (PATCH method)."""
        headers = await self._ensure_authenticated()
        payload = {}
        if person_id is not None:
            payload["person_id"] = person_id
        if rotation_id is not None:
            payload["rotation_id"] = rotation_id
        if notes is not None:
            payload["notes"] = notes

        response = await self._request_with_retry(
            "PATCH",
            f"{self.config.api_prefix}/assignments/{assignment_id}",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def delete_assignment(self, assignment_id: str) -> dict[str, Any]:
        """Delete a specific assignment."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "DELETE",
            f"{self.config.api_prefix}/assignments/{assignment_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    # ==================== COMPLIANCE METHODS ====================

    async def check_work_hours(
        self,
        start_date: str,
        end_date: str,
        person_id: str | None = None,
        include_details: bool = True,
    ) -> dict[str, Any]:
        """Check ACGME 80-hour work week compliance."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
            "include_details": include_details,
        }
        if person_id:
            params["person_id"] = person_id

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/compliance/work-hours",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def check_day_off(
        self,
        start_date: str,
        end_date: str,
        person_id: str | None = None,
        include_details: bool = True,
    ) -> dict[str, Any]:
        """Check ACGME 1-in-7 day off rule compliance."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
            "include_details": include_details,
        }
        if person_id:
            params["person_id"] = person_id

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/compliance/day-off",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def check_supervision(
        self,
        date: str,
        session: str,
    ) -> dict[str, Any]:
        """Check ACGME supervision ratio compliance for a specific date/session."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/compliance/supervision",
            headers=headers,
            params={
                "date": date,
                "session": session,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_violations(
        self,
        start_date: str,
        end_date: str,
        rule_types: list[str] | None = None,
        severity: str | None = None,
    ) -> dict[str, Any]:
        """Get compliance violations for date range."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if rule_types:
            params["rule_types"] = ",".join(rule_types)
        if severity:
            params["severity"] = severity

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/compliance/violations",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def generate_compliance_report(
        self,
        start_date: str,
        end_date: str,
        include_violations: bool = True,
        include_recommendations: bool = True,
        format: str = "json",
    ) -> dict[str, Any]:
        """Generate comprehensive compliance report."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/compliance/report",
            headers=headers,
            json={
                "start_date": start_date,
                "end_date": end_date,
                "include_violations": include_violations,
                "include_recommendations": include_recommendations,
                "format": format,
            },
        )
        response.raise_for_status()
        return response.json()

    # ==================== SWAP METHODS ====================

    async def create_swap(
        self,
        person_id: str,
        assignment_id: str,
        swap_type: str = "one_to_one",
        target_person_id: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new swap request."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/swaps",
            headers=headers,
            json={
                "person_id": person_id,
                "assignment_id": assignment_id,
                "swap_type": swap_type,
                "target_person_id": target_person_id,
                "notes": notes,
            },
        )
        response.raise_for_status()
        return response.json()

    async def execute_swap(self, swap_id: str) -> dict[str, Any]:
        """Execute a pending swap request."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/swaps/{swap_id}/execute",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def rollback_swap(self, swap_id: str) -> dict[str, Any]:
        """Rollback an executed swap (within 24-hour window)."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/swaps/{swap_id}/rollback",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def get_swap_history(
        self,
        person_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """Get swap history, optionally filtered."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {"limit": limit}
        if person_id:
            params["person_id"] = person_id
        if status:
            params["status"] = status

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/swaps",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    # ==================== RESILIENCE METHODS ====================

    async def get_defense_level(self, date: str | None = None) -> dict[str, Any]:
        """Get current resilience defense level (GREEN/YELLOW/ORANGE/RED/BLACK)."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {}
        if date:
            params["date"] = date

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/resilience/defense-level",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_utilization(
        self,
        start_date: str,
        end_date: str,
        person_id: str | None = None,
    ) -> dict[str, Any]:
        """Get utilization metrics (80% threshold monitoring)."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if person_id:
            params["person_id"] = person_id

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/resilience/utilization",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_burnout_rt(
        self,
        start_date: str,
        end_date: str,
        person_id: str | None = None,
    ) -> dict[str, Any]:
        """Get burnout reproduction number (Rt) from SIR model."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if person_id:
            params["person_id"] = person_id

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/resilience/burnout-rt",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_early_warnings(
        self,
        start_date: str,
        end_date: str,
        warning_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """Get early warning signals (SPC, STA/LTA, etc)."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
        }
        if warning_types:
            params["warning_types"] = ",".join(warning_types)

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/resilience/early-warnings",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    # ==================== ANALYTICS METHODS ====================

    async def get_coverage_metrics(
        self,
        start_date: str,
        end_date: str,
        by_rotation: bool = True,
    ) -> dict[str, Any]:
        """Get schedule coverage analysis."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/analytics/coverage",
            headers=headers,
            params={
                "start_date": start_date,
                "end_date": end_date,
                "by_rotation": by_rotation,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_workload_distribution(
        self,
        start_date: str,
        end_date: str,
        by_person: bool = True,
    ) -> dict[str, Any]:
        """Get workload distribution analysis."""
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/analytics/workload",
            headers=headers,
            params={
                "start_date": start_date,
                "end_date": end_date,
                "by_person": by_person,
            },
        )
        response.raise_for_status()
        return response.json()

    async def get_trend_analysis(
        self,
        start_date: str,
        end_date: str,
        metrics: list[str] | None = None,
        window_days: int = 7,
    ) -> dict[str, Any]:
        """Get trend analysis for schedule metrics."""
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {
            "start_date": start_date,
            "end_date": end_date,
            "window_days": window_days,
        }
        if metrics:
            params["metrics"] = ",".join(metrics)

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/analytics/trends",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    # ==================== RAG METHODS ====================

    async def rag_retrieve(
        self,
        query: str,
        top_k: int = 5,
        doc_type: str | None = None,
        min_similarity: float = 0.5,
    ) -> dict[str, Any]:
        """Retrieve relevant documents from RAG knowledge base.

        Args:
            query: Search query text
            top_k: Number of results to return
            doc_type: Optional filter by document type
            min_similarity: Minimum similarity threshold (0-1)

        Returns:
            Dict with query, documents, total_results, execution_time_ms
        """
        headers = await self._ensure_authenticated()
        payload: dict[str, Any] = {
            "query": query,
            "top_k": top_k,
            "min_similarity": min_similarity,
        }
        if doc_type:
            payload["doc_type"] = doc_type

        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/rag/retrieve",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def rag_build_context(
        self,
        query: str,
        max_tokens: int = 2000,
        doc_type: str | None = None,
        include_metadata: bool = True,
    ) -> dict[str, Any]:
        """Build context string for LLM injection from RAG knowledge base.

        Args:
            query: Query to retrieve context for
            max_tokens: Maximum tokens in context
            doc_type: Optional filter by document type
            include_metadata: Include metadata in context string

        Returns:
            Dict with query, context, sources, token_count, metadata
        """
        headers = await self._ensure_authenticated()
        payload: dict[str, Any] = {
            "query": query,
            "max_tokens": max_tokens,
            "include_metadata": include_metadata,
        }
        if doc_type:
            payload["doc_type"] = doc_type

        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/rag/context",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    async def rag_health(self) -> dict[str, Any]:
        """Get health status of RAG system.

        Returns:
            Dict with status, total_documents, documents_by_type,
            embedding_model, vector_index_status, recommendations
        """
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/rag/health",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def rag_ingest(
        self,
        content: str,
        doc_type: str,
        metadata: dict[str, Any] | None = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ) -> dict[str, Any]:
        """Ingest a document into RAG knowledge base.

        Args:
            content: Document text content
            doc_type: Type of document (acgme_rules, scheduling_policy, etc.)
            metadata: Additional metadata to store
            chunk_size: Target chunk size in tokens
            chunk_overlap: Overlap between chunks

        Returns:
            Dict with status, chunks_created, chunk_ids, doc_type, message
        """
        headers = await self._ensure_authenticated()
        payload: dict[str, Any] = {
            "content": content,
            "doc_type": doc_type,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
        }
        if metadata:
            payload["metadata"] = metadata

        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/rag/ingest",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()

    # ==================== BACKUP METHODS ====================

    async def create_backup(
        self,
        strategy: str = "full",
        description: str = "",
    ) -> dict[str, Any]:
        """Create a database backup.

        Args:
            strategy: Backup strategy - "full", "incremental", or "differential"
            description: Optional description for audit trail

        Returns:
            BackupResult with backup_id, timestamp, size, and status
        """
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/backup/create",
            headers=headers,
            json={
                "strategy": strategy,
                "description": description,
            },
            timeout=300.0,  # 5 minute timeout for backups
        )
        response.raise_for_status()
        return response.json()

    async def list_backups(
        self,
        limit: int = 50,
        strategy: str | None = None,
    ) -> dict[str, Any]:
        """List available database backups.

        Args:
            limit: Maximum backups to return (default 50)
            strategy: Filter by strategy type (optional)

        Returns:
            List of backups with metadata and storage stats
        """
        headers = await self._ensure_authenticated()
        params: dict[str, Any] = {"limit": limit}
        if strategy:
            params["strategy"] = strategy

        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/backup/list",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def restore_backup(
        self,
        backup_id: str,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """Restore database from a backup.

        WARNING: Non-dry-run will replace all database data.

        Args:
            backup_id: ID of backup to restore
            dry_run: If True, preview restore without applying (default True)

        Returns:
            Restore result with status
        """
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "POST",
            f"{self.config.api_prefix}/backup/restore/{backup_id}",
            headers=headers,
            json={"dry_run": dry_run},
            timeout=600.0,  # 10 minute timeout for restore
        )
        response.raise_for_status()
        return response.json()

    async def verify_backup(
        self,
        backup_id: str,
    ) -> dict[str, Any]:
        """Verify backup integrity.

        Args:
            backup_id: ID of backup to verify

        Returns:
            Verification result with checksum and validity
        """
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/backup/verify/{backup_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()

    async def get_backup_status(self) -> dict[str, Any]:
        """Get backup system health status.

        Returns:
            Backup system status with latest backup age, count, and warnings
        """
        headers = await self._ensure_authenticated()
        response = await self._request_with_retry(
            "GET",
            f"{self.config.api_prefix}/backup/status",
            headers=headers,
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
