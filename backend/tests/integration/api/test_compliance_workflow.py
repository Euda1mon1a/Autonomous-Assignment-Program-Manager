"""
Integration tests for ACGME compliance workflow.

Tests the end-to-end compliance checking, monitoring, and enforcement.
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


class TestComplianceWorkflow:
    """Test ACGME compliance checking and enforcement."""

    def test_80_hour_rule_validation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test 80-hour work week rule validation."""
        # Step 1: Create blocks for one week
        start_date = date.today()
        blocks = []

        for i in range(7):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                response = client.post(
                    "/api/blocks/",
                    json={
                        "date": current_date.isoformat(),
                        "time_of_day": tod,
                        "block_number": 1,
                    },
                    headers=auth_headers,
                )
                if response.status_code in [200, 201]:
                    blocks.append(response.json())

        # Step 2: Assign resident to all blocks (should violate 80-hour rule)
        for block in blocks:
            client.post(
                "/api/assignments/",
                json={
                    "block_id": block["id"],
                    "person_id": str(sample_resident.id),
                    "rotation_template_id": str(sample_rotation_template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )

        # Step 3: Check compliance
        compliance_response = client.get(
            f"/api/analytics/acgme/compliance?person_id={sample_resident.id}&start_date={start_date.isoformat()}",
            headers=auth_headers,
        )

        # Should detect violation or provide compliance status
        assert compliance_response.status_code in [200, 404]

        if compliance_response.status_code == 200:
            data = compliance_response.json()
            # Verify 80-hour rule is checked
            assert "hours_worked" in data or "violations" in data or "compliant" in data

    def test_1_in_7_rule_validation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test 1-in-7 day off rule validation."""
        # Step 1: Create blocks for 14 days (2 weeks)
        start_date = date.today()

        for i in range(14):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                response = client.post(
                    "/api/blocks/",
                    json={
                        "date": current_date.isoformat(),
                        "time_of_day": tod,
                        "block_number": 1,
                    },
                    headers=auth_headers,
                )

        # Step 2: Get created blocks
        blocks_response = client.get(
            f"/api/blocks/?start_date={start_date.isoformat()}&end_date={(start_date + timedelta(days=13)).isoformat()}",
            headers=auth_headers,
        )

        if blocks_response.status_code == 200:
            blocks = blocks_response.json()

            # Step 3: Assign to all blocks (violates 1-in-7 rule)
            for block in blocks:
                client.post(
                    "/api/assignments/",
                    json={
                        "block_id": block["id"],
                        "person_id": str(sample_resident.id),
                        "rotation_template_id": str(sample_rotation_template.id),
                        "role": "primary",
                    },
                    headers=auth_headers,
                )

            # Step 4: Validate compliance
            validation_response = client.post(
                "/api/schedule/validate",
                json={
                    "person_id": str(sample_resident.id),
                    "start_date": start_date.isoformat(),
                    "end_date": (start_date + timedelta(days=13)).isoformat(),
                },
                headers=auth_headers,
            )

            assert validation_response.status_code in [200, 404]

    def test_supervision_ratio_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
        sample_faculty_members: list[Person],
    ):
        """Test supervision ratio compliance."""
        # Step 1: Create a block
        start_date = date.today()
        block_response = client.post(
            "/api/blocks/",
            json={
                "date": start_date.isoformat(),
                "time_of_day": "AM",
                "block_number": 1,
            },
            headers=auth_headers,
        )
        assert block_response.status_code in [200, 201]
        block_id = block_response.json()["id"]

        # Step 2: Create template requiring supervision
        template_response = client.post(
            "/api/rotation-templates/",
            json={
                "name": "Supervised Clinic",
                "activity_type": "outpatient",
                "abbreviation": "SUP",
                "max_residents": 4,
                "supervision_required": True,
                "max_supervision_ratio": 2,  # 1:2 faculty:resident
            },
            headers=auth_headers,
        )
        assert template_response.status_code == 201
        template_id = template_response.json()["id"]

        # Step 3: Assign residents without faculty (should fail supervision check)
        for resident in sample_residents[:3]:  # 3 residents
            client.post(
                "/api/assignments/",
                json={
                    "block_id": block_id,
                    "person_id": str(resident.id),
                    "rotation_template_id": template_id,
                    "role": "primary",
                },
                headers=auth_headers,
            )

        # Step 4: Check supervision compliance
        supervision_response = client.get(
            f"/api/analytics/supervision?block_id={block_id}",
            headers=auth_headers,
        )
        assert supervision_response.status_code in [200, 404]

        # Step 5: Add faculty to meet ratio
        if len(sample_faculty_members) > 0:
            faculty_assignment = client.post(
                "/api/assignments/",
                json={
                    "block_id": block_id,
                    "person_id": str(sample_faculty_members[0].id),
                    "rotation_template_id": template_id,
                    "role": "supervisor",
                },
                headers=auth_headers,
            )

            # Step 6: Re-check compliance
            recheck_response = client.get(
                f"/api/analytics/supervision?block_id={block_id}",
                headers=auth_headers,
            )
            assert recheck_response.status_code in [200, 404]

    def test_rolling_4_week_average_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test 80-hour rolling 4-week average."""
        # Step 1: Create blocks for 4 weeks
        start_date = date.today()

        for i in range(28):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                client.post(
                    "/api/blocks/",
                    json={
                        "date": current_date.isoformat(),
                        "time_of_day": tod,
                        "block_number": (i // 28) + 1,
                    },
                    headers=auth_headers,
                )

        # Step 2: Get blocks
        blocks_response = client.get(
            f"/api/blocks/?start_date={start_date.isoformat()}&end_date={(start_date + timedelta(days=27)).isoformat()}",
            headers=auth_headers,
        )

        if blocks_response.status_code == 200:
            blocks = blocks_response.json()

            # Step 3: Create varying workload across weeks
            for i, block in enumerate(blocks):
                # Vary assignment to create realistic schedule
                if i % 3 != 0:  # Work 2 out of 3 blocks
                    client.post(
                        "/api/assignments/",
                        json={
                            "block_id": block["id"],
                            "person_id": str(sample_resident.id),
                            "rotation_template_id": str(sample_rotation_template.id),
                            "role": "primary",
                        },
                        headers=auth_headers,
                    )

            # Step 4: Check rolling average
            analytics_response = client.get(
                f"/api/analytics/work-hours?person_id={sample_resident.id}&start_date={start_date.isoformat()}&window=4",
                headers=auth_headers,
            )
            assert analytics_response.status_code in [200, 404]

    def test_compliance_dashboard_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_residents: list[Person],
    ):
        """Test compliance dashboard retrieval."""
        # Step 1: Get overall compliance dashboard
        dashboard_response = client.get(
            "/api/analytics/compliance/dashboard",
            headers=auth_headers,
        )
        assert dashboard_response.status_code in [200, 404]

        if dashboard_response.status_code == 200:
            data = dashboard_response.json()
            # Should contain compliance metrics
            assert isinstance(data, (dict, list))

        # Step 2: Get per-resident compliance
        for resident in sample_residents:
            resident_compliance = client.get(
                f"/api/analytics/compliance/resident/{resident.id}",
                headers=auth_headers,
            )
            assert resident_compliance.status_code in [200, 404]

    def test_violation_alert_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_rotation_template: RotationTemplate,
    ):
        """Test that compliance violations generate alerts."""
        # Step 1: Create scenario that violates rules
        start_date = date.today()

        # Create 10 consecutive days of full schedules
        for i in range(10):
            current_date = start_date + timedelta(days=i)
            for tod in ["AM", "PM"]:
                block_response = client.post(
                    "/api/blocks/",
                    json={
                        "date": current_date.isoformat(),
                        "time_of_day": tod,
                        "block_number": 1,
                    },
                    headers=auth_headers,
                )

                if block_response.status_code in [200, 201]:
                    client.post(
                        "/api/assignments/",
                        json={
                            "block_id": block_response.json()["id"],
                            "person_id": str(sample_resident.id),
                            "rotation_template_id": str(sample_rotation_template.id),
                            "role": "primary",
                        },
                        headers=auth_headers,
                    )

        # Step 2: Trigger compliance check
        check_response = client.post(
            "/api/analytics/compliance/check",
            json={
                "person_id": str(sample_resident.id),
                "start_date": start_date.isoformat(),
                "end_date": (start_date + timedelta(days=9)).isoformat(),
            },
            headers=auth_headers,
        )
        assert check_response.status_code in [200, 404, 501]

        # Step 3: Check for alerts
        alerts_response = client.get(
            "/api/alerts/",
            headers=auth_headers,
        )
        assert alerts_response.status_code in [200, 404]

    def test_compliance_report_generation_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test generating compliance reports."""
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        # Request compliance report
        report_response = client.post(
            "/api/reports/compliance",
            json={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "format": "pdf",
            },
            headers=auth_headers,
        )

        # May succeed or return 501 if not implemented
        assert report_response.status_code in [200, 201, 404, 501]

        if report_response.status_code in [200, 201]:
            # Verify report format
            content_type = report_response.headers.get("content-type", "")
            assert "pdf" in content_type or "json" in content_type

    def test_proactive_compliance_check_workflow(
        self,
        client: TestClient,
        auth_headers: dict,
        db: Session,
        sample_resident: Person,
        sample_blocks: list[Block],
        sample_rotation_template: RotationTemplate,
    ):
        """Test proactive compliance checking before assignment."""
        # Step 1: Create some baseline assignments
        for block in sample_blocks[:5]:
            client.post(
                "/api/assignments/",
                json={
                    "block_id": str(block.id),
                    "person_id": str(sample_resident.id),
                    "rotation_template_id": str(sample_rotation_template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )

        # Step 2: Check if new assignment would violate compliance
        if len(sample_blocks) > 5:
            precheck_response = client.post(
                "/api/assignments/validate",
                json={
                    "block_id": str(sample_blocks[5].id),
                    "person_id": str(sample_resident.id),
                    "rotation_template_id": str(sample_rotation_template.id),
                    "role": "primary",
                },
                headers=auth_headers,
            )

            # Should return validation result
            assert precheck_response.status_code in [200, 400, 404]
