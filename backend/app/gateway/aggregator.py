"""
Response aggregation for API gateway.

Provides response aggregation from multiple services with different strategies.
"""
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AggregationStrategy(str, Enum):
    """Aggregation strategy types."""

    MERGE = "merge"  # Merge all responses into single object
    ARRAY = "array"  # Collect responses into array
    FIRST_SUCCESS = "first_success"  # Return first successful response
    FASTEST = "fastest"  # Return fastest response
    CONSENSUS = "consensus"  # Return response agreed upon by majority
    WATERFALL = "waterfall"  # Try services in order until success


class AggregationConfig(BaseModel):
    """Configuration for response aggregation."""

    strategy: AggregationStrategy = Field(
        default=AggregationStrategy.MERGE,
        description="Aggregation strategy to use",
    )
    timeout_seconds: int = Field(
        default=30,
        description="Timeout for aggregation in seconds",
    )
    parallel: bool = Field(
        default=True,
        description="Execute requests in parallel",
    )
    fail_fast: bool = Field(
        default=False,
        description="Fail immediately on first error",
    )
    min_success_count: int = Field(
        default=1,
        description="Minimum number of successful responses required",
    )
    merge_strategy: str = Field(
        default="shallow",
        description="Merge strategy: 'shallow' or 'deep'",
    )
    array_key: Optional[str] = Field(
        default=None,
        description="Key to extract from responses for array aggregation",
    )
    consensus_threshold: float = Field(
        default=0.5,
        description="Threshold for consensus (0.0-1.0)",
    )

    class Config:
        use_enum_values = True


@dataclass
class ServiceResponse:
    """Response from a service."""

    service_name: str
    data: Any
    success: bool
    error: Optional[str] = None
    latency_ms: float = 0.0


class ResponseAggregator:
    """
    Response aggregator for API gateway.

    Aggregates responses from multiple services using configurable strategies.
    """

    def __init__(self, config: Optional[AggregationConfig] = None):
        """
        Initialize response aggregator.

        Args:
            config: Aggregation configuration
        """
        self.config = config or AggregationConfig()
        logger.info(
            f"Response aggregator initialized with strategy: {self.config.strategy}"
        )

    async def aggregate(
        self,
        responses: list[ServiceResponse],
    ) -> dict[str, Any]:
        """
        Aggregate responses from multiple services.

        Args:
            responses: List of service responses

        Returns:
            dict: Aggregated response

        Raises:
            ValueError: If aggregation fails or constraints not met
        """
        # Filter successful responses
        successful_responses = [r for r in responses if r.success]

        # Check minimum success count
        if len(successful_responses) < self.config.min_success_count:
            error_details = [
                f"{r.service_name}: {r.error}" for r in responses if not r.success
            ]
            raise ValueError(
                f"Insufficient successful responses: "
                f"{len(successful_responses)}/{len(responses)} succeeded. "
                f"Errors: {'; '.join(error_details)}"
            )

        # Apply aggregation strategy
        strategy = self.config.strategy

        if strategy == AggregationStrategy.MERGE:
            return await self._merge_responses(successful_responses)

        elif strategy == AggregationStrategy.ARRAY:
            return await self._array_responses(successful_responses)

        elif strategy == AggregationStrategy.FIRST_SUCCESS:
            return await self._first_success(successful_responses)

        elif strategy == AggregationStrategy.FASTEST:
            return await self._fastest_response(successful_responses)

        elif strategy == AggregationStrategy.CONSENSUS:
            return await self._consensus_response(successful_responses)

        elif strategy == AggregationStrategy.WATERFALL:
            return await self._waterfall_response(responses)

        else:
            raise ValueError(f"Unsupported aggregation strategy: {strategy}")

    async def aggregate_parallel(
        self,
        service_calls: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        """
        Execute service calls in parallel and aggregate responses.

        Args:
            service_calls: List of (service_name, coroutine) tuples

        Returns:
            dict: Aggregated response
        """
        import time

        responses: list[ServiceResponse] = []

        # Execute calls in parallel
        for service_name, coro in service_calls:
            start_time = time.time()
            try:
                data = await asyncio.wait_for(
                    coro,
                    timeout=self.config.timeout_seconds,
                )
                latency = (time.time() - start_time) * 1000
                responses.append(
                    ServiceResponse(
                        service_name=service_name,
                        data=data,
                        success=True,
                        latency_ms=latency,
                    )
                )
            except asyncio.TimeoutError:
                latency = (time.time() - start_time) * 1000
                responses.append(
                    ServiceResponse(
                        service_name=service_name,
                        data=None,
                        success=False,
                        error="Timeout",
                        latency_ms=latency,
                    )
                )
                if self.config.fail_fast:
                    break
            except Exception as e:
                latency = (time.time() - start_time) * 1000
                responses.append(
                    ServiceResponse(
                        service_name=service_name,
                        data=None,
                        success=False,
                        error=str(e),
                        latency_ms=latency,
                    )
                )
                if self.config.fail_fast:
                    break

        return await self.aggregate(responses)

    async def _merge_responses(
        self, responses: list[ServiceResponse]
    ) -> dict[str, Any]:
        """
        Merge responses into single object.

        Args:
            responses: List of successful responses

        Returns:
            dict: Merged response
        """
        if not responses:
            return {}

        result: dict[str, Any] = {
            "data": {},
            "metadata": {
                "sources": [r.service_name for r in responses],
                "count": len(responses),
                "avg_latency_ms": sum(r.latency_ms for r in responses)
                / len(responses),
            },
        }

        # Merge data
        if self.config.merge_strategy == "deep":
            result["data"] = self._deep_merge([r.data for r in responses])
        else:
            # Shallow merge
            for response in responses:
                if isinstance(response.data, dict):
                    result["data"].update(response.data)
                else:
                    # If not dict, store under service name
                    result["data"][response.service_name] = response.data

        return result

    async def _array_responses(
        self, responses: list[ServiceResponse]
    ) -> dict[str, Any]:
        """
        Collect responses into array.

        Args:
            responses: List of successful responses

        Returns:
            dict: Response with data array
        """
        if not responses:
            return {"data": [], "metadata": {"count": 0}}

        # Extract array key if specified
        if self.config.array_key:
            data = []
            for response in responses:
                if isinstance(response.data, dict):
                    value = response.data.get(self.config.array_key)
                    if value is not None:
                        if isinstance(value, list):
                            data.extend(value)
                        else:
                            data.append(value)
        else:
            data = [r.data for r in responses]

        return {
            "data": data,
            "metadata": {
                "sources": [r.service_name for r in responses],
                "count": len(data),
                "avg_latency_ms": sum(r.latency_ms for r in responses)
                / len(responses),
            },
        }

    async def _first_success(
        self, responses: list[ServiceResponse]
    ) -> dict[str, Any]:
        """
        Return first successful response.

        Args:
            responses: List of successful responses

        Returns:
            dict: First successful response
        """
        if not responses:
            raise ValueError("No successful responses")

        response = responses[0]
        return {
            "data": response.data,
            "metadata": {
                "source": response.service_name,
                "latency_ms": response.latency_ms,
            },
        }

    async def _fastest_response(
        self, responses: list[ServiceResponse]
    ) -> dict[str, Any]:
        """
        Return fastest successful response.

        Args:
            responses: List of successful responses

        Returns:
            dict: Fastest response
        """
        if not responses:
            raise ValueError("No successful responses")

        fastest = min(responses, key=lambda r: r.latency_ms)
        return {
            "data": fastest.data,
            "metadata": {
                "source": fastest.service_name,
                "latency_ms": fastest.latency_ms,
            },
        }

    async def _consensus_response(
        self, responses: list[ServiceResponse]
    ) -> dict[str, Any]:
        """
        Return consensus response (most common).

        Args:
            responses: List of successful responses

        Returns:
            dict: Consensus response
        """
        if not responses:
            raise ValueError("No successful responses")

        # Count identical responses
        from collections import Counter
        import json

        response_counts = Counter(
            json.dumps(r.data, sort_keys=True) for r in responses
        )

        # Find most common
        most_common = response_counts.most_common(1)[0]
        count = most_common[1]
        threshold_count = len(responses) * self.config.consensus_threshold

        if count < threshold_count:
            raise ValueError(
                f"No consensus reached: {count}/{len(responses)} "
                f"(threshold: {threshold_count:.1f})"
            )

        # Find matching response
        consensus_data = json.loads(most_common[0])
        matching_response = next(
            r for r in responses if r.data == consensus_data
        )

        return {
            "data": consensus_data,
            "metadata": {
                "consensus_count": count,
                "total_responses": len(responses),
                "source": matching_response.service_name,
            },
        }

    async def _waterfall_response(
        self, responses: list[ServiceResponse]
    ) -> dict[str, Any]:
        """
        Return first successful response from ordered list.

        Args:
            responses: List of responses (ordered by priority)

        Returns:
            dict: First successful response
        """
        for response in responses:
            if response.success:
                return {
                    "data": response.data,
                    "metadata": {
                        "source": response.service_name,
                        "latency_ms": response.latency_ms,
                    },
                }

        raise ValueError("All services failed in waterfall")

    def _deep_merge(self, dicts: list[Any]) -> dict[str, Any]:
        """
        Deep merge multiple dictionaries.

        Args:
            dicts: List of dictionaries to merge

        Returns:
            dict: Merged dictionary
        """
        result = {}

        for d in dicts:
            if not isinstance(d, dict):
                continue

            for key, value in d.items():
                if key in result:
                    # Key exists - merge values
                    if isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = self._deep_merge([result[key], value])
                    elif isinstance(result[key], list) and isinstance(value, list):
                        result[key].extend(value)
                    else:
                        # Overwrite with new value
                        result[key] = value
                else:
                    result[key] = value

        return result
