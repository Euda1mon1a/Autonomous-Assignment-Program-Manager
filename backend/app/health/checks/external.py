"""
External service health check implementation.

Provides health monitoring for external services and dependencies:
- HTTP endpoint checks
- API availability
- DNS resolution
- Network connectivity
"""

import asyncio
import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


class ExternalServiceHealthCheck:
    """
    External service health check implementation.

    Performs health checks on external services including:
    - HTTP/HTTPS endpoint availability
    - Response time monitoring
    - Status code validation
    - SSL certificate validation
    """

    def __init__(
        self,
        name: str,
        url: str,
        timeout: float = 10.0,
        expected_status: int = 200,
        check_ssl: bool = True,
    ):
        """
        Initialize external service health check.

        Args:
            name: Service name for identification
            url: URL to check
            timeout: Maximum time in seconds to wait for response
            expected_status: Expected HTTP status code
            check_ssl: Whether to verify SSL certificates
        """
        self.name = name
        self.url = url
        self.timeout = timeout
        self.expected_status = expected_status
        self.check_ssl = check_ssl

    async def check(self) -> dict[str, Any]:
        """
        Perform external service health check.

        Returns:
            Dictionary with health status:
            - status: "healthy", "degraded", or "unhealthy"
            - response_time_ms: Request response time
            - status_code: HTTP status code received
            - url: URL checked
            - error: Error message if unhealthy

        Raises:
            TimeoutError: If check exceeds timeout
        """
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(self._perform_check(), timeout=self.timeout)

            response_time_ms = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time_ms, 2)

            # Determine status based on response
            if result.get("status_code") != self.expected_status:
                result["status"] = "degraded"
                result["warning"] = (
                    f"Unexpected status code: {result.get('status_code')}"
                )
            elif response_time_ms > 5000:  # > 5 seconds is degraded
                result["status"] = "degraded"
                result["warning"] = "Response time is slow"

            return result

        except TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"External service '{self.name}' health check timed out")
            return {
                "status": "unhealthy",
                "url": self.url,
                "error": f"Request timed out after {self.timeout}s",
                "response_time_ms": round(response_time_ms, 2),
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"External service '{self.name}' health check failed: {e}")
            return {
                "status": "unhealthy",
                "url": self.url,
                "error": str(e),
                "response_time_ms": round(response_time_ms, 2),
            }

    async def _perform_check(self) -> dict[str, Any]:
        """
        Perform the actual HTTP health check.

        Returns:
            Dictionary with detailed health information
        """
        try:
            async with httpx.AsyncClient(verify=self.check_ssl) as client:
                # Make GET request to the URL
                response = await client.get(
                    self.url, timeout=self.timeout, follow_redirects=True
                )

                # Extract response details
                status_code = response.status_code
                headers = dict(response.headers)

                # Parse URL for additional info
                parsed_url = urlparse(self.url)

                return {
                    "status": "healthy",
                    "url": self.url,
                    "status_code": status_code,
                    "host": parsed_url.netloc,
                    "scheme": parsed_url.scheme,
                    "content_type": headers.get("content-type", "unknown"),
                }

        except httpx.ConnectError as e:
            logger.error(f"Connection error for {self.url}: {e}")
            return {
                "status": "unhealthy",
                "url": self.url,
                "error": f"Connection error: {str(e)}",
            }

        except httpx.TimeoutException as e:
            logger.error(f"Timeout error for {self.url}: {e}")
            return {
                "status": "unhealthy",
                "url": self.url,
                "error": "Request timeout",
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error for {self.url}: {e}")
            return {
                "status": "unhealthy",
                "url": self.url,
                "error": f"HTTP error: {e.response.status_code}",
                "status_code": e.response.status_code,
            }

        except Exception as e:
            logger.error(f"Unexpected error for {self.url}: {e}")
            return {
                "status": "unhealthy",
                "url": self.url,
                "error": f"Unexpected error: {str(e)}",
            }

    async def check_with_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Perform health check with POST payload.

        Useful for checking API endpoints that require authentication
        or specific request body.

        Args:
            payload: Dictionary to send as JSON payload

        Returns:
            Dictionary with health check results
        """
        try:
            async with httpx.AsyncClient(verify=self.check_ssl) as client:
                response = await client.post(
                    self.url, json=payload, timeout=self.timeout, follow_redirects=True
                )

                return {
                    "status": (
                        "healthy"
                        if response.status_code == self.expected_status
                        else "degraded"
                    ),
                    "url": self.url,
                    "status_code": response.status_code,
                    "method": "POST",
                }

        except Exception as e:
            logger.error(f"POST health check failed for {self.url}: {e}")
            return {
                "status": "unhealthy",
                "url": self.url,
                "error": str(e),
                "method": "POST",
            }


class DNSHealthCheck:
    """
    DNS resolution health check.

    Verifies that DNS resolution is working for critical domains.
    """

    def __init__(self, hostname: str, timeout: float = 5.0):
        """
        Initialize DNS health check.

        Args:
            hostname: Hostname to resolve
            timeout: Maximum time to wait for DNS resolution
        """
        self.hostname = hostname
        self.timeout = timeout
        self.name = f"dns_{hostname}"

    async def check(self) -> dict[str, Any]:
        """
        Perform DNS resolution check.

        Returns:
            Dictionary with DNS health status
        """
        start_time = time.time()

        try:
            # Attempt DNS resolution
            loop = asyncio.get_event_loop()
            addresses = await asyncio.wait_for(
                loop.getaddrinfo(self.hostname, None), timeout=self.timeout
            )

            response_time_ms = (time.time() - start_time) * 1000

            # Extract unique IP addresses
            ips = list(set(addr[4][0] for addr in addresses))

            return {
                "status": "healthy",
                "hostname": self.hostname,
                "resolved_ips": ips,
                "ip_count": len(ips),
                "response_time_ms": round(response_time_ms, 2),
            }

        except TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"DNS resolution timed out for {self.hostname}")
            return {
                "status": "unhealthy",
                "hostname": self.hostname,
                "error": f"DNS resolution timed out after {self.timeout}s",
                "response_time_ms": round(response_time_ms, 2),
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"DNS resolution failed for {self.hostname}: {e}")
            return {
                "status": "unhealthy",
                "hostname": self.hostname,
                "error": str(e),
                "response_time_ms": round(response_time_ms, 2),
            }
