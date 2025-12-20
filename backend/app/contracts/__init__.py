"""
Contract testing framework for API contracts.

This module provides a comprehensive contract testing framework based on
Pact-style consumer-driven contracts with additional features for versioning,
breaking change detection, and contract publishing.

Key Components:
---------------
- Contract: Contract definition with version tracking
- ContractInteraction: Individual request/response interaction
- ContractVerifier: Provider-side contract verification
- ContractPublisher: Contract broker integration
- ContractTester: Consumer-side contract generation
- ContractCompatibility: Breaking change detection

Usage Example:
--------------
    # Consumer-side: Define a contract
    contract = Contract(
        consumer="frontend-app",
        provider="residency-scheduler-api",
        version="1.0.0"
    )

    interaction = ContractInteraction(
        description="Get person by ID",
        request=ContractRequest(
            method="GET",
            path="/api/persons/{person_id}",
            headers={"Accept": "application/json"}
        ),
        response=ContractResponse(
            status=200,
            headers={"Content-Type": "application/json"},
            body_schema=PersonResponseSchema
        )
    )
    contract.add_interaction(interaction)

    # Provider-side: Verify the contract
    verifier = ContractVerifier(app=fastapi_app)
    results = await verifier.verify_contract(contract)

    # Publish to broker
    publisher = ContractPublisher(broker_url="http://pact-broker")
    await publisher.publish(contract, git_sha="abc123")
"""

from app.contracts.testing import (
    BreakingChange,
    BreakingChangeType,
    Contract,
    ContractCompatibilityChecker,
    ContractFormat,
    ContractInteraction,
    ContractPublisher,
    ContractRequest,
    ContractResponse,
    ContractTester,
    ContractVerificationResult,
    ContractVerifier,
    InteractionVerificationResult,
    PublishResult,
)

__all__ = [
    "Contract",
    "ContractInteraction",
    "ContractRequest",
    "ContractResponse",
    "ContractVerifier",
    "ContractTester",
    "ContractPublisher",
    "ContractCompatibilityChecker",
    "ContractVerificationResult",
    "InteractionVerificationResult",
    "PublishResult",
    "BreakingChange",
    "BreakingChangeType",
    "ContractFormat",
]
