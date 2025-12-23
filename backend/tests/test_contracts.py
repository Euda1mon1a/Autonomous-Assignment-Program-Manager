"""
Tests for contract testing framework.

Tests the consumer-driven contract testing framework including:
- Contract creation and validation
- Consumer-side contract generation
- Provider-side contract verification
- Contract versioning and compatibility checking
- Contract publishing to broker
- Breaking change detection
"""

import tempfile
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from pydantic import BaseModel

from app.contracts import (
    BreakingChangeType,
    Contract,
    ContractCompatibilityChecker,
    ContractInteraction,
    ContractPublisher,
    ContractRequest,
    ContractResponse,
    ContractTester,
    ContractVerifier,
)


class PersonResponse(BaseModel):
    """Test schema for person response."""

    id: str
    name: str
    email: str
    type: str


class TestContractRequest:
    """Tests for ContractRequest schema."""

    def test_valid_request(self):
        """Test creating a valid contract request."""
        request = ContractRequest(
            method="GET",
            path="/api/persons/{person_id}",
            headers={"Accept": "application/json"},
            query={"include": "assignments"},
        )

        assert request.method == "GET"
        assert request.path == "/api/persons/{person_id}"
        assert request.headers == {"Accept": "application/json"}
        assert request.query == {"include": "assignments"}

    def test_method_case_normalization(self):
        """Test that HTTP method is normalized to uppercase."""
        request = ContractRequest(method="get", path="/api/test")
        assert request.method == "GET"

    def test_invalid_method(self):
        """Test that invalid HTTP methods are rejected."""
        with pytest.raises(ValueError, match="Invalid HTTP method"):
            ContractRequest(method="INVALID", path="/api/test")

    def test_post_request_with_body(self):
        """Test POST request with JSON body."""
        body = {"name": "John Doe", "email": "john@example.com"}
        request = ContractRequest(method="POST", path="/api/persons", body=body)

        assert request.method == "POST"
        assert request.body == body


class TestContractResponse:
    """Tests for ContractResponse schema."""

    def test_valid_response(self):
        """Test creating a valid contract response."""
        response = ContractResponse(
            status=200,
            headers={"Content-Type": "application/json"},
            body={"id": "123", "name": "John Doe"},
        )

        assert response.status == 200
        assert response.headers == {"Content-Type": "application/json"}
        assert response.body["id"] == "123"

    def test_invalid_status_code(self):
        """Test that invalid status codes are rejected."""
        with pytest.raises(ValueError, match="Invalid HTTP status code"):
            ContractResponse(status=999, headers={})

        with pytest.raises(ValueError, match="Invalid HTTP status code"):
            ContractResponse(status=99, headers={})

    def test_response_with_schema(self):
        """Test response with Pydantic schema."""
        response = ContractResponse(status=200, headers={}, body_schema=PersonResponse)

        assert response.body_schema == PersonResponse


class TestContractInteraction:
    """Tests for ContractInteraction."""

    def test_create_interaction(self):
        """Test creating a contract interaction."""
        request = ContractRequest(method="GET", path="/api/persons/123")
        response = ContractResponse(status=200, body={"id": "123", "name": "John"})

        interaction = ContractInteraction(
            description="Get person by ID", request=request, response=response
        )

        assert interaction.description == "Get person by ID"
        assert interaction.request.method == "GET"
        assert interaction.response.status == 200
        assert interaction.id is not None  # Auto-generated UUID

    def test_interaction_with_provider_state(self):
        """Test interaction with provider state."""
        request = ContractRequest(method="GET", path="/api/persons/123")
        response = ContractResponse(status=200, body={"id": "123"})

        interaction = ContractInteraction(
            description="Get person",
            request=request,
            response=response,
            provider_state="person 123 exists",
        )

        assert interaction.provider_state == "person 123 exists"


class TestContract:
    """Tests for Contract model."""

    def test_create_contract(self):
        """Test creating a contract."""
        contract = Contract(
            consumer="frontend-app",
            provider="residency-scheduler-api",
            version="1.0.0",
        )

        assert contract.consumer == "frontend-app"
        assert contract.provider == "residency-scheduler-api"
        assert contract.version == "1.0.0"
        assert len(contract.interactions) == 0

    def test_invalid_version_format(self):
        """Test that invalid version formats are rejected."""
        with pytest.raises(ValueError, match="Invalid version format"):
            Contract(
                consumer="app1",
                provider="app2",
                version="1.0",  # Missing patch version
            )

        with pytest.raises(ValueError, match="Invalid version format"):
            Contract(consumer="app1", provider="app2", version="invalid")

    def test_valid_version_with_prerelease(self):
        """Test version with prerelease suffix."""
        contract = Contract(consumer="app1", provider="app2", version="1.0.0-alpha.1")
        assert contract.version == "1.0.0-alpha.1"

    def test_add_interaction(self):
        """Test adding interactions to contract."""
        contract = Contract(consumer="app1", provider="app2", version="1.0.0")

        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={})
        interaction = ContractInteraction(
            description="Test", request=request, response=response
        )

        contract.add_interaction(interaction)

        assert len(contract.interactions) == 1
        assert contract.interactions[0] == interaction

    def test_contract_hash(self):
        """Test contract hash generation."""
        contract1 = Contract(consumer="app1", provider="app2", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={"key": "value"})
        interaction = ContractInteraction(
            description="Test", request=request, response=response
        )
        contract1.add_interaction(interaction)

        # Same contract should have same hash
        contract2 = Contract(consumer="app1", provider="app2", version="1.0.0")
        contract2.add_interaction(interaction)

        assert contract1.get_hash() == contract2.get_hash()

        # Different contract should have different hash
        contract3 = Contract(consumer="app1", provider="app2", version="1.0.0")
        different_request = ContractRequest(method="POST", path="/api/test")
        different_interaction = ContractInteraction(
            description="Test", request=different_request, response=response
        )
        contract3.add_interaction(different_interaction)

        assert contract1.get_hash() != contract3.get_hash()

    def test_to_pact_format(self):
        """Test conversion to Pact format."""
        contract = Contract(consumer="app1", provider="app2", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={"result": "success"})
        interaction = ContractInteraction(
            description="Test interaction",
            request=request,
            response=response,
            provider_state="test state",
        )
        contract.add_interaction(interaction)

        pact_format = contract.to_pact_format()

        assert pact_format["consumer"]["name"] == "app1"
        assert pact_format["provider"]["name"] == "app2"
        assert len(pact_format["interactions"]) == 1
        assert pact_format["interactions"][0]["description"] == "Test interaction"
        assert pact_format["interactions"][0]["providerState"] == "test state"
        assert pact_format["metadata"]["pactSpecification"]["version"] == "3"


class TestContractTester:
    """Tests for consumer-side contract tester."""

    def test_create_contract_tester(self):
        """Test creating a contract tester."""
        tester = ContractTester(
            consumer="frontend-app",
            provider="api",
            version="1.0.0",
        )

        assert tester.contract.consumer == "frontend-app"
        assert tester.contract.provider == "api"
        assert tester.contract.version == "1.0.0"

    def test_add_interaction(self):
        """Test adding interaction to contract."""
        tester = ContractTester(consumer="app1", provider="api", version="1.0.0")

        request = ContractRequest(method="GET", path="/api/persons/123")
        response = ContractResponse(status=200, body={"id": "123", "name": "John Doe"})

        tester.add_interaction(
            description="Get person by ID",
            request=request,
            response=response,
            provider_state="person 123 exists",
        )

        contract = tester.get_contract()
        assert len(contract.interactions) == 1
        assert contract.interactions[0].description == "Get person by ID"

    def test_save_and_load_contract(self):
        """Test saving contract to file and loading it back."""
        tester = ContractTester(consumer="app1", provider="api", version="1.0.0")

        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={"result": "success"})

        tester.add_interaction(
            description="Test interaction", request=request, response=response
        )

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            filepath = f.name

        try:
            tester.save_contract(filepath)

            # Load it back
            loaded_contract = ContractTester.load_contract(filepath)

            assert loaded_contract.consumer == "app1"
            assert loaded_contract.provider == "api"
            assert len(loaded_contract.interactions) == 1
            assert loaded_contract.interactions[0].description == "Test interaction"
        finally:
            import os

            os.unlink(filepath)


class TestContractVerifier:
    """Tests for provider-side contract verification."""

    def test_create_verifier_with_app(self):
        """Test creating verifier with FastAPI app."""
        app = FastAPI()
        verifier = ContractVerifier(app=app)

        assert verifier.app == app
        assert verifier.base_url is None

    def test_create_verifier_with_url(self):
        """Test creating verifier with base URL."""
        verifier = ContractVerifier(base_url="http://localhost:8000")

        assert verifier.base_url == "http://localhost:8000"
        assert verifier.app is None

    @pytest.mark.asyncio
    async def test_verify_simple_contract(self):
        """Test verifying a simple contract."""
        # Create a simple FastAPI app
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return {"result": "success"}

        # Create contract
        contract = Contract(consumer="test-app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={"result": "success"})
        interaction = ContractInteraction(
            description="Test endpoint", request=request, response=response
        )
        contract.add_interaction(interaction)

        # Verify
        verifier = ContractVerifier(app=app)
        result = await verifier.verify_contract(contract)

        assert result.passed is True
        assert result.total_interactions == 1
        assert result.passed_interactions == 1
        assert result.failed_interactions == 0

    @pytest.mark.asyncio
    async def test_verify_contract_with_path_params(self):
        """Test verifying contract with path parameters."""
        app = FastAPI()

        @app.get("/api/persons/{person_id}")
        def get_person(person_id: str):
            return {"id": person_id, "name": "John Doe", "email": "john@example.com"}

        contract = Contract(consumer="frontend", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/persons/123")
        response = ContractResponse(
            status=200,
            body={"id": "123", "name": "John Doe", "email": "john@example.com"},
        )
        interaction = ContractInteraction(
            description="Get person", request=request, response=response
        )
        contract.add_interaction(interaction)

        verifier = ContractVerifier(app=app)
        result = await verifier.verify_contract(contract)

        assert result.passed is True
        assert result.passed_interactions == 1

    @pytest.mark.asyncio
    async def test_verify_contract_status_mismatch(self):
        """Test verification fails when status codes don't match."""
        app = FastAPI()

        @app.get("/api/test")
        def test_endpoint():
            return {"result": "success"}  # Returns 200

        contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(
            status=201,
            body={"result": "success"},  # Expects 201
        )
        interaction = ContractInteraction(
            description="Test", request=request, response=response
        )
        contract.add_interaction(interaction)

        verifier = ContractVerifier(app=app)
        result = await verifier.verify_contract(contract)

        assert result.passed is False
        assert result.failed_interactions == 1
        assert any(
            "Status code mismatch" in error
            for r in result.interaction_results
            for error in r.errors
        )

    @pytest.mark.asyncio
    async def test_verify_contract_with_provider_state(self):
        """Test verification with provider states."""
        app = FastAPI()
        state_executed = {"value": False}

        @app.get("/api/persons/{person_id}")
        def get_person(person_id: str):
            return {"id": person_id, "name": "John Doe"}

        async def setup_person_exists():
            state_executed["value"] = True

        contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/persons/123")
        response = ContractResponse(status=200, body={"id": "123", "name": "John Doe"})
        interaction = ContractInteraction(
            description="Get person",
            request=request,
            response=response,
            provider_state="person exists",
        )
        contract.add_interaction(interaction)

        verifier = ContractVerifier(
            app=app, provider_states={"person exists": setup_person_exists}
        )
        result = await verifier.verify_contract(contract)

        assert result.passed is True
        assert state_executed["value"] is True

    @pytest.mark.asyncio
    async def test_verify_contract_no_app_or_url(self):
        """Test verification fails when no app or URL provided."""
        contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={})
        interaction = ContractInteraction(
            description="Test", request=request, response=response
        )
        contract.add_interaction(interaction)

        verifier = ContractVerifier()
        result = await verifier.verify_contract(contract)

        assert result.passed is False
        assert len(result.errors) > 0
        assert "No FastAPI app or base_url provided" in result.errors[0]


class TestContractPublisher:
    """Tests for contract publishing to broker."""

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_publish_contract_success(self, mock_client_class):
        """Test successful contract publication."""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.content = b'{"success": true}'
        mock_response.json.return_value = {"success": True}

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.put = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        publisher = ContractPublisher(broker_url="http://pact-broker")

        contract = Contract(consumer="app1", provider="app2", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={})
        interaction = ContractInteraction(
            description="Test", request=request, response=response
        )
        contract.add_interaction(interaction)

        result = await publisher.publish(contract, git_sha="abc123")

        assert result.success is True
        assert result.contract_version == "1.0.0"
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_publish_contract_failure(self, mock_client_class):
        """Test failed contract publication."""
        # Mock HTTP error response
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.put = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        publisher = ContractPublisher(broker_url="http://pact-broker")

        contract = Contract(consumer="app1", provider="app2", version="1.0.0")

        result = await publisher.publish(contract)

        assert result.success is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_contract_success(self, mock_client_class):
        """Test fetching contract from broker."""
        # Mock Pact format response
        pact_data = {
            "consumer": {"name": "app1"},
            "provider": {"name": "app2"},
            "metadata": {"version": "1.0.0"},
            "interactions": [
                {
                    "description": "Test interaction",
                    "request": {"method": "GET", "path": "/api/test"},
                    "response": {"status": 200, "body": {"result": "success"}},
                }
            ],
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = pact_data

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        publisher = ContractPublisher(broker_url="http://pact-broker")

        contract = await publisher.fetch_contract(
            consumer="app1", provider="app2", version="1.0.0"
        )

        assert contract is not None
        assert contract.consumer == "app1"
        assert contract.provider == "app2"
        assert len(contract.interactions) == 1

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_fetch_contract_not_found(self, mock_client_class):
        """Test fetching non-existent contract."""
        mock_response = Mock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        publisher = ContractPublisher(broker_url="http://pact-broker")

        contract = await publisher.fetch_contract(
            consumer="app1", provider="app2", version="1.0.0"
        )

        assert contract is None


class TestContractCompatibilityChecker:
    """Tests for breaking change detection."""

    def test_compatible_contracts(self):
        """Test that identical contracts are compatible."""
        old_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={"result": "success"})
        interaction = ContractInteraction(
            description="Test", request=request, response=response
        )
        old_contract.add_interaction(interaction)

        new_contract = Contract(consumer="app", provider="api", version="1.1.0")
        new_contract.add_interaction(interaction)

        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            old_contract, new_contract
        )

        assert is_compatible is True
        assert len(breaking_changes) == 0

    def test_removed_endpoint_breaking_change(self):
        """Test that removing an endpoint is a breaking change."""
        old_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/test")
        response = ContractResponse(status=200, body={})
        interaction = ContractInteraction(
            description="Test", request=request, response=response
        )
        old_contract.add_interaction(interaction)

        new_contract = Contract(consumer="app", provider="api", version="2.0.0")
        # No interactions - endpoint removed

        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            old_contract, new_contract
        )

        assert is_compatible is False
        assert len(breaking_changes) == 1
        assert breaking_changes[0].type == BreakingChangeType.REMOVED_ENDPOINT

    def test_changed_status_code_breaking_change(self):
        """Test that changing status code is a breaking change."""
        old_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="POST", path="/api/create")
        old_response = ContractResponse(status=200, body={"id": "123"})
        old_interaction = ContractInteraction(
            description="Create", request=request, response=old_response
        )
        old_contract.add_interaction(old_interaction)

        new_contract = Contract(consumer="app", provider="api", version="2.0.0")
        new_response = ContractResponse(status=201, body={"id": "123"})
        new_interaction = ContractInteraction(
            description="Create", request=request, response=new_response
        )
        new_contract.add_interaction(new_interaction)

        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            old_contract, new_contract
        )

        assert is_compatible is False
        assert len(breaking_changes) == 1
        assert breaking_changes[0].type == BreakingChangeType.CHANGED_STATUS_CODE

    def test_removed_field_breaking_change(self):
        """Test that removing a response field is a breaking change."""
        old_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/person")
        old_response = ContractResponse(
            status=200, body={"id": "123", "name": "John", "email": "john@example.com"}
        )
        old_interaction = ContractInteraction(
            description="Get person", request=request, response=old_response
        )
        old_contract.add_interaction(old_interaction)

        new_contract = Contract(consumer="app", provider="api", version="2.0.0")
        new_response = ContractResponse(
            status=200,
            body={"id": "123", "name": "John"},  # email removed
        )
        new_interaction = ContractInteraction(
            description="Get person", request=request, response=new_response
        )
        new_contract.add_interaction(new_interaction)

        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            old_contract, new_contract
        )

        assert is_compatible is False
        assert any(
            change.type == BreakingChangeType.REMOVED_REQUIRED_FIELD
            for change in breaking_changes
        )

    def test_changed_field_type_breaking_change(self):
        """Test that changing field type is a breaking change."""
        old_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/stats")
        old_response = ContractResponse(status=200, body={"count": 42})  # int
        old_interaction = ContractInteraction(
            description="Get stats", request=request, response=old_response
        )
        old_contract.add_interaction(old_interaction)

        new_contract = Contract(consumer="app", provider="api", version="2.0.0")
        new_response = ContractResponse(status=200, body={"count": "42"})  # str
        new_interaction = ContractInteraction(
            description="Get stats", request=request, response=new_response
        )
        new_contract.add_interaction(new_interaction)

        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            old_contract, new_contract
        )

        assert is_compatible is False
        assert any(
            change.type == BreakingChangeType.CHANGED_FIELD_TYPE
            for change in breaking_changes
        )

    def test_added_field_not_breaking(self):
        """Test that adding a new field is not a breaking change."""
        old_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/person")
        old_response = ContractResponse(status=200, body={"id": "123", "name": "John"})
        old_interaction = ContractInteraction(
            description="Get person", request=request, response=old_response
        )
        old_contract.add_interaction(old_interaction)

        new_contract = Contract(consumer="app", provider="api", version="1.1.0")
        new_response = ContractResponse(
            status=200,
            body={
                "id": "123",
                "name": "John",
                "email": "john@example.com",
            },  # Added field
        )
        new_interaction = ContractInteraction(
            description="Get person", request=request, response=new_response
        )
        new_contract.add_interaction(new_interaction)

        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            old_contract, new_contract
        )

        # Adding fields is backward compatible
        assert is_compatible is True
        assert len(breaking_changes) == 0

    def test_nested_object_field_removal(self):
        """Test detecting removed field in nested object."""
        old_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/user")
        old_response = ContractResponse(
            status=200,
            body={
                "id": "123",
                "profile": {"name": "John", "email": "john@example.com"},
            },
        )
        old_interaction = ContractInteraction(
            description="Get user", request=request, response=old_response
        )
        old_contract.add_interaction(old_interaction)

        new_contract = Contract(consumer="app", provider="api", version="2.0.0")
        new_response = ContractResponse(
            status=200,
            body={"id": "123", "profile": {"name": "John"}},  # email removed
        )
        new_interaction = ContractInteraction(
            description="Get user", request=request, response=new_response
        )
        new_contract.add_interaction(new_interaction)

        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            old_contract, new_contract
        )

        assert is_compatible is False
        assert any(
            "email" in change.path
            and change.type == BreakingChangeType.REMOVED_REQUIRED_FIELD
            for change in breaking_changes
        )


class TestContractIntegration:
    """Integration tests for complete contract workflows."""

    @pytest.mark.asyncio
    async def test_complete_consumer_provider_workflow(self):
        """Test complete workflow: consumer creates contract, provider verifies it."""
        # Consumer side: Create contract
        tester = ContractTester(
            consumer="frontend-app",
            provider="residency-api",
            version="1.0.0",
        )

        # Add interaction: Get person
        request = ContractRequest(
            method="GET",
            path="/api/persons/123",
            headers={"Accept": "application/json"},
        )
        response = ContractResponse(
            status=200,
            headers={"Content-Type": "application/json"},
            body={"id": "123", "name": "John Doe", "type": "faculty"},
        )
        tester.add_interaction(
            description="Get person by ID",
            request=request,
            response=response,
            provider_state="person 123 exists",
        )

        contract = tester.get_contract()

        # Provider side: Create API
        app = FastAPI()

        @app.get("/api/persons/{person_id}")
        def get_person(person_id: str):
            return {"id": person_id, "name": "John Doe", "type": "faculty"}

        # Provider side: Verify contract
        verifier = ContractVerifier(app=app)
        result = await verifier.verify_contract(contract)

        assert result.passed is True
        assert result.total_interactions == 1
        assert result.passed_interactions == 1

    @pytest.mark.asyncio
    async def test_version_evolution_workflow(self):
        """Test evolving contract versions and checking compatibility."""
        # Version 1.0.0
        v1_contract = Contract(consumer="app", provider="api", version="1.0.0")
        request = ContractRequest(method="GET", path="/api/data")
        response_v1 = ContractResponse(status=200, body={"id": "123", "value": "test"})
        interaction_v1 = ContractInteraction(
            description="Get data", request=request, response=response_v1
        )
        v1_contract.add_interaction(interaction_v1)

        # Version 2.0.0 - Remove field (breaking change)
        v2_contract = Contract(consumer="app", provider="api", version="2.0.0")
        response_v2 = ContractResponse(status=200, body={"id": "123"})  # value removed
        interaction_v2 = ContractInteraction(
            description="Get data", request=request, response=response_v2
        )
        v2_contract.add_interaction(interaction_v2)

        # Check compatibility
        checker = ContractCompatibilityChecker()
        is_compatible, breaking_changes = checker.check_compatibility(
            v1_contract, v2_contract
        )

        assert is_compatible is False
        assert len(breaking_changes) > 0
        assert any(
            change.type == BreakingChangeType.REMOVED_REQUIRED_FIELD
            for change in breaking_changes
        )

        # Version 1.1.0 - Add field (non-breaking)
        v1_1_contract = Contract(consumer="app", provider="api", version="1.1.0")
        response_v1_1 = ContractResponse(
            status=200, body={"id": "123", "value": "test", "extra": "field"}
        )
        interaction_v1_1 = ContractInteraction(
            description="Get data", request=request, response=response_v1_1
        )
        v1_1_contract.add_interaction(interaction_v1_1)

        is_compatible, breaking_changes = checker.check_compatibility(
            v1_contract, v1_1_contract
        )

        assert is_compatible is True  # Adding fields is compatible
        assert len(breaking_changes) == 0
