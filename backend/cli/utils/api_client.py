"""
API client utilities for CLI.

Provides HTTP client for communicating with the backend API.
"""

from typing import Any, Dict, Optional

import httpx
from rich.console import Console

from cli.config import get_config
from cli.utils.auth import AuthManager

console = Console()


class APIClient:
    """HTTP client for backend API."""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize API client.

        Args:
            base_url: API base URL (defaults to config value)
        """
        config = get_config()
        self.base_url = base_url or config.api_url
        self.auth = AuthManager()
        self.timeout = 30.0

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        return self.auth.get_headers()

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make GET request to API.

        Args:
            endpoint: API endpoint (e.g., "/api/v1/persons")
            params: Query parameters

        Returns:
            Response data
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.get(
                url,
                headers=self._get_headers(),
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP Error {e.response.status_code}: {e.response.text}[/red]")
            raise
        except httpx.RequestError as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            raise

    def post(
        self,
        endpoint: str,
        data: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Make POST request to API.

        Args:
            endpoint: API endpoint
            data: Form data
            json: JSON data

        Returns:
            Response data
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.post(
                url,
                headers=self._get_headers(),
                data=data,
                json=json,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP Error {e.response.status_code}: {e.response.text}[/red]")
            raise
        except httpx.RequestError as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            raise

    def put(self, endpoint: str, json: Dict) -> Dict[str, Any]:
        """
        Make PUT request to API.

        Args:
            endpoint: API endpoint
            json: JSON data

        Returns:
            Response data
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.put(
                url,
                headers=self._get_headers(),
                json=json,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP Error {e.response.status_code}: {e.response.text}[/red]")
            raise
        except httpx.RequestError as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            raise

    def delete(self, endpoint: str) -> None:
        """
        Make DELETE request to API.

        Args:
            endpoint: API endpoint
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = httpx.delete(
                url,
                headers=self._get_headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()

        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP Error {e.response.status_code}: {e.response.text}[/red]")
            raise
        except httpx.RequestError as e:
            console.print(f"[red]Request Error: {str(e)}[/red]")
            raise

    def health_check(self) -> bool:
        """
        Check API health.

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = httpx.get(
                f"{self.base_url}/health",
                timeout=5.0,
            )
            return response.status_code == 200
        except Exception:
            return False
