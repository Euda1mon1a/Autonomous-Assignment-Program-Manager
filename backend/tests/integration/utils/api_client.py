"""
Test API client for integration tests.

Provides convenience methods for making API requests in tests.
"""

from typing import Any, Optional

from fastapi.testclient import TestClient


class TestAPIClient:
    """Test API client with convenience methods."""

    def __init__(self, client: TestClient, auth_headers: dict | None = None):
        """
        Initialize test API client.

        Args:
            client: FastAPI test client
            auth_headers: Optional authentication headers
        """
        self.client = client
        self.auth_headers = auth_headers or {}

    def get(self, url: str, **kwargs) -> Any:
        """Make GET request with auth headers."""
        headers = {**self.auth_headers, **kwargs.pop("headers", {})}
        return self.client.get(url, headers=headers, **kwargs)

    def post(self, url: str, **kwargs) -> Any:
        """Make POST request with auth headers."""
        headers = {**self.auth_headers, **kwargs.pop("headers", {})}
        return self.client.post(url, headers=headers, **kwargs)

    def put(self, url: str, **kwargs) -> Any:
        """Make PUT request with auth headers."""
        headers = {**self.auth_headers, **kwargs.pop("headers", {})}
        return self.client.put(url, headers=headers, **kwargs)

    def patch(self, url: str, **kwargs) -> Any:
        """Make PATCH request with auth headers."""
        headers = {**self.auth_headers, **kwargs.pop("headers", {})}
        return self.client.patch(url, headers=headers, **kwargs)

    def delete(self, url: str, **kwargs) -> Any:
        """Make DELETE request with auth headers."""
        headers = {**self.auth_headers, **kwargs.pop("headers", {})}
        return self.client.delete(url, headers=headers, **kwargs)

    # Convenience methods for common operations

    def create_person(self, data: dict) -> Any:
        """Create a person via API."""
        return self.post("/api/people/", json=data)

    def create_block(self, data: dict) -> Any:
        """Create a block via API."""
        return self.post("/api/blocks/", json=data)

    def create_assignment(self, data: dict) -> Any:
        """Create an assignment via API."""
        return self.post("/api/assignments/", json=data)

    def create_swap_request(self, data: dict) -> Any:
        """Create a swap request via API."""
        return self.post("/api/swap/", json=data)

    def get_schedule(self, start_date: str, end_date: str) -> Any:
        """Get schedule for date range."""
        return self.get(f"/api/schedule/?start_date={start_date}&end_date={end_date}")

    def validate_compliance(self, person_id: str, start_date: str) -> Any:
        """Validate ACGME compliance for person."""
        return self.get(
            f"/api/analytics/acgme/compliance?person_id={person_id}&start_date={start_date}"
        )

    def check_response(
        self,
        response: Any,
        expected_status: int = 200,
        expected_keys: list[str] | None = None,
    ) -> Any:
        """
        Check response status and structure.

        Args:
            response: API response
            expected_status: Expected HTTP status code
            expected_keys: Optional list of expected keys in response JSON

        Returns:
            Response JSON data

        Raises:
            AssertionError: If response doesn't match expectations
        """
        assert response.status_code == expected_status, (
            f"Expected status {expected_status}, got {response.status_code}. "
            f"Response: {response.text}"
        )

        if expected_keys and response.status_code == 200:
            data = response.json()
            for key in expected_keys:
                assert key in data, f"Expected key '{key}' not found in response"

        return response.json() if response.status_code == 200 else None
