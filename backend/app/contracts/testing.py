"""
Contract testing framework implementation.

This module provides a comprehensive Pact-style contract testing framework with
support for consumer-driven contracts, provider verification, version management,
breaking change detection, and contract publishing to a broker.

Architecture:
-------------
1. Consumer Side: Define expected API interactions and generate contracts
2. Provider Side: Verify that the API satisfies all consumer contracts
3. Broker Integration: Publish and retrieve contracts from a central broker
4. Compatibility: Detect breaking changes between contract versions

References:
-----------
- Pact: https://docs.pact.io/
- Consumer-Driven Contracts: https://martinfowler.com/articles/consumerDrivenContracts.html
"""

import hashlib
import json
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class ContractFormat(str, Enum):
    """Supported contract formats."""

    PACT_V2 = "pact_v2"
    PACT_V3 = "pact_v3"
    PACT_V4 = "pact_v4"
    OPENAPI_3_0 = "openapi_3.0"
    OPENAPI_3_1 = "openapi_3.1"


class BreakingChangeType(str, Enum):
    """Types of breaking changes in contracts."""

    REMOVED_ENDPOINT = "removed_endpoint"
    CHANGED_METHOD = "changed_method"
    REMOVED_REQUIRED_FIELD = "removed_required_field"
    CHANGED_FIELD_TYPE = "changed_field_type"
    ADDED_REQUIRED_FIELD = "added_required_field"
    CHANGED_STATUS_CODE = "changed_status_code"
    REMOVED_STATUS_CODE = "removed_status_code"
    CHANGED_RESPONSE_STRUCTURE = "changed_response_structure"


@dataclass
class BreakingChange:
    """Represents a breaking change between contract versions."""

    type: BreakingChangeType
    description: str
    old_value: Any
    new_value: Any
    path: str
    severity: str = "high"  # high, medium, low


class ContractRequest(BaseModel):
    """Contract request specification."""

    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    path: str = Field(..., description="URL path with optional path parameters")
    headers: dict[str, str] = Field(default_factory=dict, description="Request headers")
    query: dict[str, str | list[str]] = Field(
        default_factory=dict, description="Query parameters"
    )
    body: dict[str, Any] | list | str | None = Field(
        None, description="Request body (JSON, string, or None)"
    )
    body_schema: type[BaseModel] | None = Field(
        None, description="Pydantic schema for request body validation"
    )

    @field_validator("method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        """Validate HTTP method."""
        allowed = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Invalid HTTP method: {v}. Must be one of {allowed}")
        return v_upper

    class Config:
        arbitrary_types_allowed = True


class ContractResponse(BaseModel):
    """Contract response specification."""

    status: int = Field(..., description="HTTP status code")
    headers: dict[str, str] = Field(
        default_factory=dict, description="Response headers"
    )
    body: dict[str, Any] | list | str | None = Field(
        None, description="Response body (JSON, string, or None)"
    )
    body_schema: type[BaseModel] | None = Field(
        None, description="Pydantic schema for response body validation"
    )
    body_matchers: dict[str, Callable] = Field(
        default_factory=dict,
        description="Custom matchers for response fields (jsonpath -> matcher function)",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: int) -> int:
        """Validate HTTP status code."""
        if not 100 <= v <= 599:
            raise ValueError(f"Invalid HTTP status code: {v}")
        return v

    class Config:
        arbitrary_types_allowed = True


class ContractInteraction(BaseModel):
    """Represents a single request/response interaction in a contract."""

    id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique interaction ID"
    )
    description: str = Field(..., description="Human-readable interaction description")
    provider_state: str | None = Field(
        None, description="Required provider state for this interaction"
    )
    request: ContractRequest = Field(..., description="Expected request")
    response: ContractResponse = Field(..., description="Expected response")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    class Config:
        arbitrary_types_allowed = True


class Contract(BaseModel):
    """
    Contract definition following Pact-style consumer-driven contracts.

    A contract specifies the interactions between a consumer and provider,
    including request/response expectations and versioning information.
    """

    consumer: str = Field(..., description="Consumer application name")
    provider: str = Field(..., description="Provider application name")
    version: str = Field(..., description="Contract version (semantic versioning)")
    interactions: list[ContractInteraction] = Field(
        default_factory=list, description="List of interactions"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Contract metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Contract creation timestamp"
    )
    format: ContractFormat = Field(
        default=ContractFormat.PACT_V3, description="Contract format version"
    )

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semantic version format."""
        # Simple semantic version check: MAJOR.MINOR.PATCH
        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.-]+)?(\+[a-zA-Z0-9.-]+)?$"
        if not re.match(pattern, v):
            raise ValueError(
                f"Invalid version format: {v}. Must follow semantic versioning (e.g., 1.0.0)"
            )
        return v

    def add_interaction(self, interaction: ContractInteraction) -> None:
        """Add an interaction to the contract."""
        self.interactions.append(interaction)

    def get_hash(self) -> str:
        """
        Generate a hash of the contract for version tracking.

        Returns:
            str: SHA256 hash of contract content
        """
        # Create a stable representation for hashing
        content = {
            "consumer": self.consumer,
            "provider": self.provider,
            "version": self.version,
            "interactions": [
                {
                    "description": i.description,
                    "request": {
                        "method": i.request.method,
                        "path": i.request.path,
                        "headers": i.request.headers,
                        "query": i.request.query,
                        "body": i.request.body,
                    },
                    "response": {
                        "status": i.response.status,
                        "headers": i.response.headers,
                        "body": i.response.body,
                    },
                }
                for i in self.interactions
            ],
        }
        content_str = json.dumps(content, sort_keys=True)
        return hashlib.sha256(content_str.encode()).hexdigest()

    def to_pact_format(self) -> dict[str, Any]:
        """
        Convert contract to Pact format for publishing.

        Returns:
            dict: Contract in Pact JSON format
        """
        return {
            "consumer": {"name": self.consumer},
            "provider": {"name": self.provider},
            "interactions": [
                {
                    "description": interaction.description,
                    "providerState": interaction.provider_state,
                    "request": {
                        "method": interaction.request.method,
                        "path": interaction.request.path,
                        "headers": interaction.request.headers,
                        "query": interaction.request.query,
                        "body": interaction.request.body,
                    },
                    "response": {
                        "status": interaction.response.status,
                        "headers": interaction.response.headers,
                        "body": interaction.response.body,
                    },
                }
                for interaction in self.interactions
            ],
            "metadata": {
                "pactSpecification": {
                    "version": self.format.value.replace("pact_v", "")
                },
                "created": self.created_at.isoformat(),
                **self.metadata,
            },
        }

    class Config:
        arbitrary_types_allowed = True


@dataclass
class InteractionVerificationResult:
    """Result of verifying a single interaction."""

    interaction_id: str
    description: str
    passed: bool
    request_matched: bool
    response_matched: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    actual_response: dict[str, Any] | None = None


@dataclass
class ContractVerificationResult:
    """Result of verifying an entire contract."""

    contract_version: str
    consumer: str
    provider: str
    passed: bool
    total_interactions: int
    passed_interactions: int
    failed_interactions: int
    interaction_results: list[InteractionVerificationResult]
    verification_time: float
    errors: list[str] = field(default_factory=list)


class ContractVerifier:
    """
    Provider-side contract verifier.

    Verifies that a provider API satisfies all interactions defined in
    consumer contracts.
    """

    def __init__(
        self,
        app: FastAPI | None = None,
        base_url: str | None = None,
        provider_states: dict[str, Callable] | None = None,
    ) -> None:
        """
        Initialize the contract verifier.

        Args:
            app: FastAPI application instance for testing
            base_url: Base URL for remote API testing
            provider_states: Mapping of provider state names to setup functions
        """
        self.app = app
        self.base_url = base_url
        self.provider_states = provider_states or {}
        self.client: TestClient | httpx.AsyncClient | None = None

    async def verify_contract(
        self, contract: Contract, setup_db: Callable | None = None
    ) -> ContractVerificationResult:
        """
        Verify that the provider satisfies all contract interactions.

        Args:
            contract: Contract to verify
            setup_db: Optional function to set up test database

        Returns:
            ContractVerificationResult: Verification results
        """
        start_time = datetime.utcnow()
        interaction_results: list[InteractionVerificationResult] = []
        errors: list[str] = []

        # Set up test client
        if self.app:
            self.client = TestClient(self.app)
        elif self.base_url:
            self.client = httpx.AsyncClient(base_url=self.base_url)
        else:
            errors.append("No FastAPI app or base_url provided for verification")
            return ContractVerificationResult(
                contract_version=contract.version,
                consumer=contract.consumer,
                provider=contract.provider,
                passed=False,
                total_interactions=len(contract.interactions),
                passed_interactions=0,
                failed_interactions=len(contract.interactions),
                interaction_results=[],
                verification_time=0.0,
                errors=errors,
            )

            # Verify each interaction
        for interaction in contract.interactions:
            result = await self._verify_interaction(interaction, setup_db)
            interaction_results.append(result)

            # Calculate summary statistics
        passed_count = sum(1 for r in interaction_results if r.passed)
        failed_count = len(interaction_results) - passed_count
        all_passed = passed_count == len(interaction_results)

        end_time = datetime.utcnow()
        verification_time = (end_time - start_time).total_seconds()

        return ContractVerificationResult(
            contract_version=contract.version,
            consumer=contract.consumer,
            provider=contract.provider,
            passed=all_passed,
            total_interactions=len(interaction_results),
            passed_interactions=passed_count,
            failed_interactions=failed_count,
            interaction_results=interaction_results,
            verification_time=verification_time,
            errors=errors,
        )

    async def _verify_interaction(
        self, interaction: ContractInteraction, setup_db: Callable | None = None
    ) -> InteractionVerificationResult:
        """
        Verify a single interaction.

        Args:
            interaction: Interaction to verify
            setup_db: Optional database setup function

        Returns:
            InteractionVerificationResult: Verification result
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Set up provider state if needed
        if interaction.provider_state:
            if interaction.provider_state in self.provider_states:
                try:
                    await self._run_provider_state(
                        self.provider_states[interaction.provider_state], setup_db
                    )
                except Exception as e:
                    errors.append(f"Provider state setup failed: {str(e)}")
                    return InteractionVerificationResult(
                        interaction_id=interaction.id,
                        description=interaction.description,
                        passed=False,
                        request_matched=False,
                        response_matched=False,
                        errors=errors,
                    )
            else:
                warnings.append(
                    f"Provider state '{interaction.provider_state}' not configured"
                )

                # Make the request
        try:
            actual_response = await self._make_request(interaction.request)
        except Exception as e:
            errors.append(f"Request failed: {str(e)}")
            return InteractionVerificationResult(
                interaction_id=interaction.id,
                description=interaction.description,
                passed=False,
                request_matched=True,
                response_matched=False,
                errors=errors,
                warnings=warnings,
            )

            # Verify response
        response_matched, response_errors = self._verify_response(
            interaction.response, actual_response
        )
        errors.extend(response_errors)

        return InteractionVerificationResult(
            interaction_id=interaction.id,
            description=interaction.description,
            passed=response_matched and len(errors) == 0,
            request_matched=True,
            response_matched=response_matched,
            errors=errors,
            warnings=warnings,
            actual_response=actual_response,
        )

    async def _run_provider_state(
        self, state_func: Callable, setup_db: Callable | None = None
    ) -> None:
        """Run a provider state setup function."""
        if setup_db:
            # If state function accepts db parameter
            import inspect

            sig = inspect.signature(state_func)
            if "db" in sig.parameters:
                await state_func(db=setup_db())
            else:
                await state_func()
        else:
            await state_func()

    async def _make_request(self, request: ContractRequest) -> dict[str, Any]:
        """Make an HTTP request to the provider."""
        if isinstance(self.client, TestClient):
            # Synchronous TestClient
            response = self.client.request(
                method=request.method,
                url=request.path,
                headers=request.headers,
                params=request.query,
                json=request.body if isinstance(request.body, (dict, list)) else None,
                data=request.body if isinstance(request.body, str) else None,
            )
        else:
            # Async httpx client
            response = await self.client.request(  # type: ignore
                method=request.method,
                url=request.path,
                headers=request.headers,
                params=request.query,
                json=request.body if isinstance(request.body, (dict, list)) else None,
                data=request.body if isinstance(request.body, str) else None,
            )

        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "body": response.json() if response.content else None,
        }

    def _verify_response(
        self, expected: ContractResponse, actual: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Verify that actual response matches expected response.

        Returns:
            tuple: (matched: bool, errors: list[str])
        """
        errors: list[str] = []

        # Check status code
        if actual["status"] != expected.status:
            errors.append(
                f"Status code mismatch: expected {expected.status}, got {actual['status']}"
            )

            # Check headers
        for key, value in expected.headers.items():
            actual_value = actual["headers"].get(key)
            if actual_value != value:
                errors.append(
                    f"Header '{key}' mismatch: expected '{value}', got '{actual_value}'"
                )

                # Check body with schema if provided
        if expected.body_schema and actual["body"]:
            try:
                expected.body_schema(**actual["body"])
            except Exception as e:
                errors.append(f"Response body validation failed: {str(e)}")

                # Check body structure if no schema
        elif expected.body is not None:
            if not self._compare_structures(expected.body, actual["body"]):
                errors.append(
                    f"Response body structure mismatch:\n"
                    f"Expected: {expected.body}\n"
                    f"Actual: {actual['body']}"
                )

                # Apply custom matchers
        for json_path, matcher in expected.body_matchers.items():
            try:
                value = self._extract_json_path(actual["body"], json_path)
                if not matcher(value):
                    errors.append(f"Custom matcher failed for path '{json_path}'")
            except Exception as e:
                errors.append(f"Matcher error for path '{json_path}': {str(e)}")

        return len(errors) == 0, errors

    def _compare_structures(self, expected: Any, actual: Any) -> bool:
        """
        Compare two data structures for compatibility.

        Uses flexible matching: actual can have additional fields,
        but must have all expected fields with matching types.
        """
        if type(expected) != type(actual):
            return False

        if isinstance(expected, dict):
            for key, value in expected.items():
                if key not in actual:
                    return False
                if not self._compare_structures(value, actual[key]):
                    return False
            return True

        if isinstance(expected, list):
            if len(expected) == 0:
                return True  # Empty list matches any list
                # Check if actual list items match expected structure
            if len(actual) == 0:
                return False
            return all(self._compare_structures(expected[0], item) for item in actual)

        return True

    def _extract_json_path(self, data: Any, path: str) -> Any:
        """Extract value from JSON data using simple path notation."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                raise ValueError(f"Cannot extract path '{path}' from data")
        return current


class ContractTester:
    """
    Consumer-side contract test generator.

    Helps consumers generate contracts from their test cases.
    """

    def __init__(self, consumer: str, provider: str, version: str = "1.0.0") -> None:
        """
        Initialize contract tester.

        Args:
            consumer: Consumer application name
            provider: Provider application name
            version: Contract version
        """
        self.contract = Contract(consumer=consumer, provider=provider, version=version)

    def add_interaction(
        self,
        description: str,
        request: ContractRequest,
        response: ContractResponse,
        provider_state: str | None = None,
    ) -> None:
        """
        Add an interaction to the contract.

        Args:
            description: Interaction description
            request: Expected request
            response: Expected response
            provider_state: Provider state requirement
        """
        interaction = ContractInteraction(
            description=description,
            request=request,
            response=response,
            provider_state=provider_state,
        )
        self.contract.add_interaction(interaction)

    def get_contract(self) -> Contract:
        """Get the generated contract."""
        return self.contract

    def save_contract(self, filepath: str) -> None:
        """Save contract to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.contract.to_pact_format(), f, indent=2)

    @staticmethod
    def load_contract(filepath: str) -> Contract:
        """Load contract from a JSON file."""
        with open(filepath) as f:
            data = json.load(f)

            # Convert from Pact format to our Contract model
        contract = Contract(
            consumer=data["consumer"]["name"],
            provider=data["provider"]["name"],
            version=data.get("metadata", {}).get("version", "1.0.0"),
            format=ContractFormat.PACT_V3,
        )

        for interaction_data in data["interactions"]:
            request = ContractRequest(
                method=interaction_data["request"]["method"],
                path=interaction_data["request"]["path"],
                headers=interaction_data["request"].get("headers", {}),
                query=interaction_data["request"].get("query", {}),
                body=interaction_data["request"].get("body"),
            )

            response = ContractResponse(
                status=interaction_data["response"]["status"],
                headers=interaction_data["response"].get("headers", {}),
                body=interaction_data["response"].get("body"),
            )

            interaction = ContractInteraction(
                description=interaction_data["description"],
                request=request,
                response=response,
                provider_state=interaction_data.get("providerState"),
            )

            contract.add_interaction(interaction)

        return contract


@dataclass
class PublishResult:
    """Result of publishing a contract to a broker."""

    success: bool
    contract_version: str
    broker_url: str
    published_at: datetime
    errors: list[str] = field(default_factory=list)
    response_data: dict[str, Any] | None = None


class ContractPublisher:
    """
    Contract broker integration for publishing and retrieving contracts.

    Supports Pact Broker API for centralized contract management.
    """

    def __init__(self, broker_url: str, auth_token: str | None = None) -> None:
        """
        Initialize contract publisher.

        Args:
            broker_url: URL of the Pact broker
            auth_token: Optional authentication token
        """
        self.broker_url = broker_url.rstrip("/")
        self.auth_token = auth_token
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if auth_token:
            self.headers["Authorization"] = f"Bearer {auth_token}"

    async def publish(
        self,
        contract: Contract,
        git_sha: str | None = None,
        git_branch: str | None = None,
        tags: list[str] | None = None,
    ) -> PublishResult:
        """
        Publish a contract to the broker.

        Args:
            contract: Contract to publish
            git_sha: Git commit SHA for versioning
            git_branch: Git branch name
            tags: Tags to apply to this version (e.g., ['prod', 'staging'])

        Returns:
            PublishResult: Publication result
        """
        errors: list[str] = []

        # Prepare contract in Pact format
        pact_data = contract.to_pact_format()

        # Add version metadata
        if git_sha:
            pact_data["metadata"]["git_sha"] = git_sha
        if git_branch:
            pact_data["metadata"]["git_branch"] = git_branch

            # Publish to broker
        url = (
            f"{self.broker_url}/pacts/provider/{contract.provider}/"
            f"consumer/{contract.consumer}/version/{contract.version}"
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    url, json=pact_data, headers=self.headers, timeout=30.0
                )

                if response.status_code not in (200, 201):
                    errors.append(
                        f"Broker returned status {response.status_code}: {response.text}"
                    )
                    return PublishResult(
                        success=False,
                        contract_version=contract.version,
                        broker_url=self.broker_url,
                        published_at=datetime.utcnow(),
                        errors=errors,
                    )

                response_data = response.json() if response.content else None

                # Apply tags if provided
                if tags:
                    await self._apply_tags(contract, tags)

                return PublishResult(
                    success=True,
                    contract_version=contract.version,
                    broker_url=self.broker_url,
                    published_at=datetime.utcnow(),
                    response_data=response_data,
                )

        except httpx.HTTPError as e:
            errors.append(f"HTTP error publishing contract: {str(e)}")
        except Exception as e:
            errors.append(f"Error publishing contract: {str(e)}")

        return PublishResult(
            success=False,
            contract_version=contract.version,
            broker_url=self.broker_url,
            published_at=datetime.utcnow(),
            errors=errors,
        )

    async def _apply_tags(self, contract: Contract, tags: list[str]) -> None:
        """Apply tags to a published contract version."""
        for tag in tags:
            url = (
                f"{self.broker_url}/pacticipants/{contract.consumer}/versions/"
                f"{contract.version}/tags/{tag}"
            )
            try:
                async with httpx.AsyncClient() as client:
                    await client.put(url, headers=self.headers, timeout=10.0)
            except Exception as e:
                logger.warning(f"Failed to apply tag '{tag}': {str(e)}")

    async def fetch_contract(
        self,
        consumer: str,
        provider: str,
        version: str | None = None,
        tag: str | None = None,
    ) -> Contract | None:
        """
        Fetch a contract from the broker.

        Args:
            consumer: Consumer name
            provider: Provider name
            version: Specific version to fetch (optional)
            tag: Tag to fetch (e.g., 'prod', 'latest') - alternative to version

        Returns:
            Contract | None: Fetched contract or None if not found
        """
        if version:
            url = f"{self.broker_url}/pacts/provider/{provider}/consumer/{consumer}/version/{version}"
        elif tag:
            url = f"{self.broker_url}/pacts/provider/{provider}/consumer/{consumer}/latest/{tag}"
        else:
            url = f"{self.broker_url}/pacts/provider/{provider}/consumer/{consumer}/latest"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, timeout=30.0)

                if response.status_code == 404:
                    logger.warning(f"Contract not found: {url}")
                    return None

                if response.status_code != 200:
                    logger.error(
                        f"Broker error {response.status_code}: {response.text}"
                    )
                    return None

                pact_data = response.json()

                # Convert to our Contract model
                contract = Contract(
                    consumer=pact_data["consumer"]["name"],
                    provider=pact_data["provider"]["name"],
                    version=pact_data.get("metadata", {}).get("version", "1.0.0"),
                )

                for interaction_data in pact_data["interactions"]:
                    request = ContractRequest(
                        method=interaction_data["request"]["method"],
                        path=interaction_data["request"]["path"],
                        headers=interaction_data["request"].get("headers", {}),
                        query=interaction_data["request"].get("query", {}),
                        body=interaction_data["request"].get("body"),
                    )

                    response_obj = ContractResponse(
                        status=interaction_data["response"]["status"],
                        headers=interaction_data["response"].get("headers", {}),
                        body=interaction_data["response"].get("body"),
                    )

                    interaction = ContractInteraction(
                        description=interaction_data["description"],
                        request=request,
                        response=response_obj,
                        provider_state=interaction_data.get("providerState"),
                    )

                    contract.add_interaction(interaction)

                return contract

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching contract: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching contract: {str(e)}")

        return None


class ContractCompatibilityChecker:
    """
    Detects breaking changes between contract versions.

    Uses semantic diffing to identify changes that would break
    existing consumers.
    """

    def check_compatibility(
        self, old_contract: Contract, new_contract: Contract
    ) -> tuple[bool, list[BreakingChange]]:
        """
        Check if new contract is compatible with old contract.

        Args:
            old_contract: Previous contract version
            new_contract: New contract version

        Returns:
            tuple: (is_compatible: bool, breaking_changes: list[BreakingChange])
        """
        breaking_changes: list[BreakingChange] = []

        # Build interaction maps
        old_interactions = {
            f"{i.request.method} {i.request.path}": i for i in old_contract.interactions
        }
        new_interactions = {
            f"{i.request.method} {i.request.path}": i for i in new_contract.interactions
        }

        # Check for removed endpoints
        for key, old_interaction in old_interactions.items():
            if key not in new_interactions:
                breaking_changes.append(
                    BreakingChange(
                        type=BreakingChangeType.REMOVED_ENDPOINT,
                        description=f"Endpoint removed: {key}",
                        old_value=old_interaction.description,
                        new_value=None,
                        path=key,
                        severity="high",
                    )
                )
                continue

                # Check for changes in existing endpoints
            new_interaction = new_interactions[key]
            endpoint_changes = self._check_interaction_compatibility(
                old_interaction, new_interaction, key
            )
            breaking_changes.extend(endpoint_changes)

        is_compatible = len(breaking_changes) == 0

        return is_compatible, breaking_changes

    def _check_interaction_compatibility(
        self, old: ContractInteraction, new: ContractInteraction, path: str
    ) -> list[BreakingChange]:
        """Check compatibility between two interactions."""
        changes: list[BreakingChange] = []

        # Check response status code
        if old.response.status != new.response.status:
            changes.append(
                BreakingChange(
                    type=BreakingChangeType.CHANGED_STATUS_CODE,
                    description=f"Status code changed for {path}",
                    old_value=old.response.status,
                    new_value=new.response.status,
                    path=path,
                    severity="high",
                )
            )

            # Check response body structure
        if old.response.body and new.response.body:
            body_changes = self._check_body_compatibility(
                old.response.body, new.response.body, f"{path}.response.body"
            )
            changes.extend(body_changes)

            # Check if response body was removed
        if old.response.body and not new.response.body:
            changes.append(
                BreakingChange(
                    type=BreakingChangeType.CHANGED_RESPONSE_STRUCTURE,
                    description=f"Response body removed for {path}",
                    old_value="present",
                    new_value="absent",
                    path=f"{path}.response.body",
                    severity="high",
                )
            )

        return changes

    def _check_body_compatibility(
        self, old_body: Any, new_body: Any, path: str
    ) -> list[BreakingChange]:
        """Check compatibility between response body structures."""
        changes: list[BreakingChange] = []

        if isinstance(old_body, dict) and isinstance(new_body, dict):
            # Check for removed fields
            for key in old_body.keys():
                if key not in new_body:
                    changes.append(
                        BreakingChange(
                            type=BreakingChangeType.REMOVED_REQUIRED_FIELD,
                            description=f"Field removed: {key}",
                            old_value=old_body[key],
                            new_value=None,
                            path=f"{path}.{key}",
                            severity="high",
                        )
                    )
                    continue

                    # Check for type changes
                old_value = old_body[key]
                new_value = new_body[key]

                if type(old_value) != type(new_value):
                    changes.append(
                        BreakingChange(
                            type=BreakingChangeType.CHANGED_FIELD_TYPE,
                            description=f"Field type changed: {key}",
                            old_value=type(old_value).__name__,
                            new_value=type(new_value).__name__,
                            path=f"{path}.{key}",
                            severity="high",
                        )
                    )
                elif isinstance(old_value, dict):
                    # Recursively check nested objects
                    nested_changes = self._check_body_compatibility(
                        old_value, new_value, f"{path}.{key}"
                    )
                    changes.extend(nested_changes)

        elif isinstance(old_body, list) and isinstance(new_body, list):
            # Check list item compatibility
            if old_body and new_body:
                item_changes = self._check_body_compatibility(
                    old_body[0], new_body[0], f"{path}[0]"
                )
                changes.extend(item_changes)

        return changes
