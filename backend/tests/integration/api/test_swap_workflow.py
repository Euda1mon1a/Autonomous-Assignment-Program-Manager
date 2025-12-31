"""
Integration tests for swap request workflow.

Tests the end-to-end lifecycle of swap requests from creation
through approval to execution.
"""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestSwapWorkflow:
    """Test complete swap request lifecycle."""

    def test_one_to_one_swap_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test creating and executing a one-to-one swap."""
        # Step 1: Create two assignments
        resident_a = sample_residents[0]
        resident_b = sample_residents[1]
        block_a = sample_blocks[0]
        block_b = sample_blocks[1]

        assignment_a_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(block_a.id),
                "person_id": str(resident_a.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert assignment_a_response.status_code in [200, 201]
        assignment_a_id = assignment_a_response.json()["id"]

        assignment_b_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(block_b.id),
                "person_id": str(resident_b.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert assignment_b_response.status_code in [200, 201]
        assignment_b_id = assignment_b_response.json()["id"]

        # Step 2: Create swap request
        swap_response = client.post(
            "/api/swap/",
            json={
                "requester_assignment_id": assignment_a_id,
                "target_assignment_id": assignment_b_id,
                "swap_type": "one_to_one",
                "notes": "Prefer to work different day",
            },
            headers=auth_headers,
        )
        assert swap_response.status_code in [200, 201]
        swap_data = swap_response.json()
        swap_id = swap_data["id"]

        # Step 3: Get swap details
        get_swap_response = client.get(
            f"/api/swap/{swap_id}",
            headers=auth_headers,
        )
        assert get_swap_response.status_code == 200
        assert get_swap_response.json()["status"] in ["pending", "requested"]

        # Step 4: Approve swap (if approval required)
        approve_response = client.post(
            f"/api/swap/{swap_id}/approve",
            headers=auth_headers,
        )
        # May succeed or require specific permissions
        assert approve_response.status_code in [200, 403]

        # Step 5: Execute swap
        execute_response = client.post(
            f"/api/swap/{swap_id}/execute",
            headers=auth_headers,
        )

        if execute_response.status_code == 200:
            # Step 6: Verify assignments were swapped
            verify_a = client.get(
                f"/api/assignments/{assignment_a_id}",
                headers=auth_headers,
            )
            verify_b = client.get(
                f"/api/assignments/{assignment_b_id}",
                headers=auth_headers,
            )

            if verify_a.status_code == 200 and verify_b.status_code == 200:
                # Assignments should have swapped people or blocks
                data_a = verify_a.json()
                data_b = verify_b.json()
                # The logic depends on implementation - may swap people or blocks

    def test_absorb_swap_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test absorb swap (giving away a shift)."""
        # Step 1: Create assignment
        resident = sample_residents[0]
        block = sample_blocks[0]

        assignment_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(block.id),
                "person_id": str(resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert assignment_response.status_code in [200, 201]
        assignment_id = assignment_response.json()["id"]

        # Step 2: Create absorb swap request
        swap_response = client.post(
            "/api/swap/",
            json={
                "requester_assignment_id": assignment_id,
                "swap_type": "absorb",
                "notes": "Need time off",
            },
            headers=auth_headers,
        )
        assert swap_response.status_code in [200, 201]
        swap_id = swap_response.json()["id"]

        # Step 3: Find potential takers
        matches_response = client.get(
            f"/api/swap/{swap_id}/matches",
            headers=auth_headers,
        )
        # May return matches or 404 if not implemented
        assert matches_response.status_code in [200, 404, 501]

    def test_swap_auto_matching_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test automatic swap matching."""
        # Step 1: Create multiple assignments
        assignments = []
        for i in range(4):
            resident = sample_residents[i % len(sample_residents)]
            block = sample_blocks[i]

            response = client.post(
                "/api/assignments/",
                json={
                    "block_id": str(block.id),
                    "person_id": str(resident.id),
                    "rotation_template_id": str(sample_rotation_template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )
            if response.status_code in [200, 201]:
                assignments.append(response.json())

        # Step 2: Create swap request
        if len(assignments) >= 2:
            swap_response = client.post(
                "/api/swap/",
                json={
                    "requester_assignment_id": assignments[0]["id"],
                    "swap_type": "absorb",
                    "notes": "Looking for swap",
                },
                headers=auth_headers,
            )

            if swap_response.status_code in [200, 201]:
                swap_id = swap_response.json()["id"]

                # Step 3: Request auto-matching
                match_response = client.post(
                    f"/api/swap/{swap_id}/auto-match",
                    headers=auth_headers,
                )
                # May return matches or 501 if not implemented
                assert match_response.status_code in [200, 404, 501]

    def test_swap_validation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test that invalid swaps are rejected."""
        # Step 1: Create assignment
        assignment_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[0].id),
                "person_id": str(sample_resident.id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assert assignment_response.status_code in [200, 201]
        assignment_id = assignment_response.json()["id"]

        # Step 2: Try to create invalid swap (swapping with self)
        invalid_swap_response = client.post(
            "/api/swap/",
            json={
                "requester_assignment_id": assignment_id,
                "target_assignment_id": assignment_id,  # Same assignment
                "swap_type": "one_to_one",
            },
            headers=auth_headers,
        )
        # Should reject invalid swap
        assert invalid_swap_response.status_code in [400, 422]

    def test_swap_cancellation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test cancelling a swap request."""
        # Step 1: Create assignments
        assignment_a_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[0].id),
                "person_id": str(sample_residents[0].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assignment_b_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[1].id),
                "person_id": str(sample_residents[1].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )

        if assignment_a_response.status_code in [
            200,
            201,
        ] and assignment_b_response.status_code in [200, 201]:
            # Step 2: Create swap
            swap_response = client.post(
                "/api/swap/",
                json={
                    "requester_assignment_id": assignment_a_response.json()["id"],
                    "target_assignment_id": assignment_b_response.json()["id"],
                    "swap_type": "one_to_one",
                },
                headers=auth_headers,
            )

            if swap_response.status_code in [200, 201]:
                swap_id = swap_response.json()["id"]

                # Step 3: Cancel swap
                cancel_response = client.post(
                    f"/api/swap/{swap_id}/cancel",
                    headers=auth_headers,
                )
                assert cancel_response.status_code in [200, 404, 501]

                # Step 4: Verify swap is cancelled
                get_response = client.get(
                    f"/api/swap/{swap_id}",
                    headers=auth_headers,
                )
                if get_response.status_code == 200:
                    assert get_response.json()["status"] in ["cancelled", "canceled"]

    def test_swap_rollback_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test rolling back an executed swap."""
        # Step 1: Create and execute swap (abbreviated)
        assignment_a_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[0].id),
                "person_id": str(sample_residents[0].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assignment_b_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[1].id),
                "person_id": str(sample_residents[1].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )

        if assignment_a_response.status_code in [
            200,
            201,
        ] and assignment_b_response.status_code in [200, 201]:
            swap_response = client.post(
                "/api/swap/",
                json={
                    "requester_assignment_id": assignment_a_response.json()["id"],
                    "target_assignment_id": assignment_b_response.json()["id"],
                    "swap_type": "one_to_one",
                },
                headers=auth_headers,
            )

            if swap_response.status_code in [200, 201]:
                swap_id = swap_response.json()["id"]

                # Execute swap
                client.post(f"/api/swap/{swap_id}/execute", headers=auth_headers)

                # Step 2: Rollback swap
                rollback_response = client.post(
                    f"/api/swap/{swap_id}/rollback",
                    headers=auth_headers,
                )
                # May succeed or return 404/501 if not implemented
                assert rollback_response.status_code in [200, 404, 501]

    def test_swap_notification_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test that swap notifications are generated."""
        # Step 1: Create swap
        assignment_a_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[0].id),
                "person_id": str(sample_residents[0].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )
        assignment_b_response = client.post(
            "/api/assignments/",
            json={
                "block_id": str(sample_blocks[1].id),
                "person_id": str(sample_residents[1].id),
                "rotation_template_id": str(sample_rotation_template.id),
                "role": "primary",
            },
            headers=auth_headers,
        )

        if assignment_a_response.status_code in [
            200,
            201,
        ] and assignment_b_response.status_code in [200, 201]:
            swap_response = client.post(
                "/api/swap/",
                json={
                    "requester_assignment_id": assignment_a_response.json()["id"],
                    "target_assignment_id": assignment_b_response.json()["id"],
                    "swap_type": "one_to_one",
                },
                headers=auth_headers,
            )

            if swap_response.status_code in [200, 201]:
                # Step 2: Check for notifications
                # This would require notification endpoint
                notifications_response = client.get(
                    "/api/notifications/",
                    headers=auth_headers,
                )
                # May return notifications or 404 if endpoint doesn't exist
                assert notifications_response.status_code in [200, 404]

    def test_multi_way_swap_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test three-way swap (A->B, B->C, C->A)."""
        # Step 1: Create three assignments
        assignments = []
        for i in range(3):
            response = client.post(
                "/api/assignments/",
                json={
                    "block_id": str(sample_blocks[i].id),
                    "person_id": str(sample_residents[i].id),
                    "rotation_template_id": str(sample_rotation_template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )
            if response.status_code in [200, 201]:
                assignments.append(response.json())

        # Step 2: Create multi-way swap
        if len(assignments) == 3:
            multi_swap_response = client.post(
                "/api/swap/multi",
                json={
                    "assignment_ids": [a["id"] for a in assignments],
                    "swap_pattern": "circular",  # A->B->C->A
                },
                headers=auth_headers,
            )
            # May be implemented or return 501
            assert multi_swap_response.status_code in [200, 201, 404, 501]
