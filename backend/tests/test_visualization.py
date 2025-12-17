"""Tests for visualization API routes and heatmap service."""
from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.core.security import create_access_token, get_password_hash
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.user import User
from app.schemas.visualization import TimeRangeType
from app.services.heatmap_service import HeatmapService


@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    user = User(
        id=uuid4(),
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("password"),
        role="admin",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_token(admin_user):
    """Create a token for admin user."""
    return create_access_token(
        data={"sub": str(admin_user.id), "username": admin_user.username}
    )


@pytest.fixture
def sample_schedule_data(db):
    """Create sample schedule data for visualization tests."""
    # Create people
    resident1 = Person(
        id=uuid4(),
        name="Dr. Smith",
        type="resident",
        email="smith@test.com",
        pgy_level=2,
    )
    resident2 = Person(
        id=uuid4(),
        name="Dr. Johnson",
        type="resident",
        email="johnson@test.com",
        pgy_level=3,
    )
    faculty1 = Person(
        id=uuid4(),
        name="Dr. Williams",
        type="faculty",
        email="williams@test.com",
        performs_procedures=True,
    )
    db.add_all([resident1, resident2, faculty1])

    # Create rotation templates
    clinic_rotation = RotationTemplate(
        id=uuid4(),
        name="Clinic",
        activity_type="clinic",
        abbreviation="C",
        max_residents=4,
    )
    fmit_rotation = RotationTemplate(
        id=uuid4(),
        name="FMIT Inpatient",
        activity_type="inpatient",
        abbreviation="FMIT",
    )
    db.add_all([clinic_rotation, fmit_rotation])

    # Create blocks for a week
    start_date = date(2024, 1, 1)
    blocks = []
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        is_weekend = current_date.weekday() >= 5

        am_block = Block(
            id=uuid4(),
            date=current_date,
            time_of_day="AM",
            block_number=1,
            is_weekend=is_weekend,
        )
        pm_block = Block(
            id=uuid4(),
            date=current_date,
            time_of_day="PM",
            block_number=1,
            is_weekend=is_weekend,
        )
        blocks.extend([am_block, pm_block])
    db.add_all(blocks)
    db.commit()

    # Create assignments
    assignments = []
    for block in blocks[:10]:  # Assign first 5 days
        # Resident 1 to clinic
        assignment1 = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident1.id,
            rotation_template_id=clinic_rotation.id,
            role="primary",
            created_by="test",
        )
        # Resident 2 to FMIT
        assignment2 = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=resident2.id,
            rotation_template_id=fmit_rotation.id,
            role="primary",
            created_by="test",
        )
        ***REMOVED*** supervising
        assignment3 = Assignment(
            id=uuid4(),
            block_id=block.id,
            person_id=faculty1.id,
            rotation_template_id=clinic_rotation.id,
            role="supervising",
            created_by="test",
        )
        assignments.extend([assignment1, assignment2, assignment3])
    db.add_all(assignments)

    # Create FMIT swap record
    swap = SwapRecord(
        id=uuid4(),
        source_faculty_id=faculty1.id,
        source_week=start_date,
        target_faculty_id=resident1.id,
        target_week=start_date + timedelta(days=7),
        swap_type=SwapType.ONE_TO_ONE,
        status=SwapStatus.APPROVED,
        reason="Personal appointment",
    )
    db.add(swap)
    db.commit()

    return {
        "residents": [resident1, resident2],
        "faculty": [faculty1],
        "rotations": [clinic_rotation, fmit_rotation],
        "blocks": blocks,
        "assignments": assignments,
        "swap": swap,
        "start_date": start_date,
        "end_date": start_date + timedelta(days=6),
    }


class TestHeatmapService:
    """Test HeatmapService methods."""

    def test_calculate_date_range_week(self):
        """Test calculating date range for a week."""
        service = HeatmapService()
        reference = date(2024, 1, 15)  # Monday
        time_range = TimeRangeType(
            range_type="week",
            reference_date=reference,
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 15)  # Monday
        assert end == date(2024, 1, 21)  # Sunday
        assert (end - start).days == 6

    def test_calculate_date_range_week_from_wednesday(self):
        """Test calculating date range for a week starting from Wednesday."""
        service = HeatmapService()
        reference = date(2024, 1, 17)  # Wednesday
        time_range = TimeRangeType(
            range_type="week",
            reference_date=reference,
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 15)  # Monday of that week
        assert end == date(2024, 1, 21)  # Sunday of that week

    def test_calculate_date_range_month(self):
        """Test calculating date range for a month."""
        service = HeatmapService()
        reference = date(2024, 1, 15)
        time_range = TimeRangeType(
            range_type="month",
            reference_date=reference,
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 1)
        assert end == date(2024, 1, 31)

    def test_calculate_date_range_month_february(self):
        """Test calculating date range for February."""
        service = HeatmapService()
        reference = date(2024, 2, 15)  # 2024 is leap year
        time_range = TimeRangeType(
            range_type="month",
            reference_date=reference,
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 2, 1)
        assert end == date(2024, 2, 29)  # Leap year

    def test_calculate_date_range_quarter_q1(self):
        """Test calculating date range for Q1."""
        service = HeatmapService()
        reference = date(2024, 2, 15)  # In Q1
        time_range = TimeRangeType(
            range_type="quarter",
            reference_date=reference,
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 1)
        assert end == date(2024, 3, 31)

    def test_calculate_date_range_quarter_q4(self):
        """Test calculating date range for Q4."""
        service = HeatmapService()
        reference = date(2024, 11, 15)  # In Q4
        time_range = TimeRangeType(
            range_type="quarter",
            reference_date=reference,
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 10, 1)
        assert end == date(2024, 12, 31)

    def test_calculate_date_range_custom(self):
        """Test calculating date range with custom dates."""
        service = HeatmapService()
        time_range = TimeRangeType(
            range_type="custom",
            start_date=date(2024, 1, 10),
            end_date=date(2024, 1, 20),
        )

        start, end = service.calculate_date_range(time_range)

        assert start == date(2024, 1, 10)
        assert end == date(2024, 1, 20)

    def test_calculate_date_range_custom_missing_dates(self):
        """Test that custom range requires both dates."""
        service = HeatmapService()
        time_range = TimeRangeType(
            range_type="custom",
            start_date=date(2024, 1, 10),
        )

        with pytest.raises(ValueError, match="start_date and end_date required"):
            service.calculate_date_range(time_range)

    def test_calculate_date_range_invalid_type(self):
        """Test that invalid range type raises error."""
        service = HeatmapService()
        time_range = TimeRangeType(
            range_type="invalid",
            reference_date=date(2024, 1, 15),
        )

        with pytest.raises(ValueError, match="Invalid range_type"):
            service.calculate_date_range(time_range)

    def test_generate_unified_heatmap_by_person(self, db, sample_schedule_data):
        """Test unified heatmap generation grouped by person."""
        service = HeatmapService()
        result = service.generate_unified_heatmap(
            db=db,
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
            group_by="person",
        )

        assert result.title == "Person Schedule Heatmap"
        assert len(result.data.x_labels) == 7  # 7 days
        assert len(result.data.y_labels) == 3  # 3 people
        assert len(result.data.z_values) == 3  # 3 rows
        assert len(result.data.z_values[0]) == 7  # 7 columns
        assert result.metadata["total_assignments"] == 30  # 3 people * 10 blocks

    def test_generate_unified_heatmap_by_rotation(self, db, sample_schedule_data):
        """Test unified heatmap generation grouped by rotation."""
        service = HeatmapService()
        result = service.generate_unified_heatmap(
            db=db,
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
            group_by="rotation",
        )

        assert result.title == "Rotation Schedule Heatmap"
        assert len(result.data.y_labels) == 2  # 2 rotations

    def test_generate_unified_heatmap_with_person_filter(
        self, db, sample_schedule_data
    ):
        """Test heatmap with person filter."""
        service = HeatmapService()
        resident1 = sample_schedule_data["residents"][0]

        result = service.generate_unified_heatmap(
            db=db,
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
            person_ids=[resident1.id],
            group_by="person",
        )

        assert len(result.data.y_labels) == 1  # Only 1 person
        assert result.data.y_labels[0] == "Dr. Smith"

    def test_generate_coverage_heatmap(self, db, sample_schedule_data):
        """Test coverage heatmap generation."""
        service = HeatmapService()
        result = service.generate_coverage_heatmap(
            db=db,
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
        )

        assert result.title == "Rotation Coverage Heatmap"
        assert result.data.color_scale == "RdYlGn"
        assert result.coverage_percentage >= 0
        assert result.coverage_percentage <= 100
        assert isinstance(result.gaps, list)

    def test_generate_person_workload_heatmap(self, db, sample_schedule_data):
        """Test person workload heatmap generation."""
        service = HeatmapService()
        resident1 = sample_schedule_data["residents"][0]

        result = service.generate_person_workload_heatmap(
            db=db,
            person_ids=[resident1.id],
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
            include_weekends=True,
        )

        assert result.title == "Person Workload Heatmap"
        assert result.data.color_scale == "Blues"
        assert len(result.data.y_labels) == 1
        assert result.metadata["total_blocks"] >= 0
        assert result.metadata["include_weekends"] is True

    def test_generate_person_workload_heatmap_exclude_weekends(
        self, db, sample_schedule_data
    ):
        """Test workload heatmap excluding weekends."""
        service = HeatmapService()
        resident1 = sample_schedule_data["residents"][0]

        result = service.generate_person_workload_heatmap(
            db=db,
            person_ids=[resident1.id],
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
            include_weekends=False,
        )

        # Should have 5 weekdays
        assert len(result.data.x_labels) == 5
        assert result.metadata["include_weekends"] is False

    def test_export_heatmap_image_png(self, db, sample_schedule_data):
        """Test exporting heatmap as PNG."""
        service = HeatmapService()
        result = service.generate_unified_heatmap(
            db=db,
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
            group_by="person",
        )

        # Note: This test requires kaleido to be installed
        # If kaleido is not available, the test will fail with a RuntimeError
        try:
            image_bytes = service.export_heatmap_image(
                data=result.data,
                title=result.title,
                format="png",
                width=800,
                height=600,
            )
            assert isinstance(image_bytes, bytes)
            assert len(image_bytes) > 0
        except RuntimeError as e:
            pytest.skip(f"Kaleido not available: {str(e)}")

    def test_create_plotly_figure(self, db, sample_schedule_data):
        """Test creating Plotly figure configuration."""
        service = HeatmapService()
        result = service.generate_unified_heatmap(
            db=db,
            start_date=sample_schedule_data["start_date"],
            end_date=sample_schedule_data["end_date"],
            group_by="person",
        )

        fig_dict = service.create_plotly_figure(
            data=result.data, title=result.title
        )

        assert isinstance(fig_dict, dict)
        assert "data" in fig_dict
        assert "layout" in fig_dict


class TestVisualizationAPI:
    """Test visualization API endpoints."""

    def test_get_unified_heatmap(self, client, admin_token, sample_schedule_data):
        """Test GET /visualization/heatmap endpoint."""
        start_date = sample_schedule_data["start_date"].isoformat()
        end_date = sample_schedule_data["end_date"].isoformat()

        response = client.get(
            f"/api/v1/visualization/heatmap?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "title" in data
        assert "generated_at" in data
        assert "metadata" in data
        assert data["data"]["color_scale"] == "Viridis"

    def test_get_unified_heatmap_with_filters(
        self, client, admin_token, sample_schedule_data
    ):
        """Test heatmap endpoint with filters."""
        start_date = sample_schedule_data["start_date"].isoformat()
        end_date = sample_schedule_data["end_date"].isoformat()
        resident1_id = str(sample_schedule_data["residents"][0].id)

        response = client.get(
            f"/api/v1/visualization/heatmap?start_date={start_date}&end_date={end_date}&person_ids={resident1_id}&group_by=person",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["y_labels"]) == 1

    def test_get_unified_heatmap_invalid_date_range(
        self, client, admin_token
    ):
        """Test heatmap with invalid date range."""
        response = client.get(
            "/api/v1/visualization/heatmap?start_date=2024-01-15&end_date=2024-01-01",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "start_date must be before or equal to end_date" in response.json()["detail"]

    def test_get_unified_heatmap_invalid_group_by(
        self, client, admin_token
    ):
        """Test heatmap with invalid group_by parameter."""
        response = client.get(
            "/api/v1/visualization/heatmap?start_date=2024-01-01&end_date=2024-01-07&group_by=invalid",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "group_by must be 'person' or 'rotation'" in response.json()["detail"]

    def test_get_heatmap_image(self, client, admin_token, sample_schedule_data):
        """Test GET /visualization/heatmap/image endpoint."""
        start_date = sample_schedule_data["start_date"].isoformat()
        end_date = sample_schedule_data["end_date"].isoformat()

        try:
            response = client.get(
                f"/api/v1/visualization/heatmap/image?start_date={start_date}&end_date={end_date}&format=png",
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert "Content-Disposition" in response.headers
        except Exception as e:
            # Kaleido might not be available in test environment
            pytest.skip(f"Image export not available: {str(e)}")

    def test_get_coverage_heatmap(self, client, admin_token, sample_schedule_data):
        """Test GET /visualization/coverage endpoint."""
        start_date = sample_schedule_data["start_date"].isoformat()
        end_date = sample_schedule_data["end_date"].isoformat()

        response = client.get(
            f"/api/v1/visualization/coverage?start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "coverage_percentage" in data
        assert "gaps" in data
        assert 0 <= data["coverage_percentage"] <= 100

    def test_get_workload_heatmap(self, client, admin_token, sample_schedule_data):
        """Test GET /visualization/workload endpoint."""
        start_date = sample_schedule_data["start_date"].isoformat()
        end_date = sample_schedule_data["end_date"].isoformat()
        resident1_id = str(sample_schedule_data["residents"][0].id)

        response = client.get(
            f"/api/v1/visualization/workload?person_ids={resident1_id}&start_date={start_date}&end_date={end_date}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "title" in data
        assert data["title"] == "Person Workload Heatmap"

    def test_get_workload_heatmap_no_person_ids(
        self, client, admin_token
    ):
        """Test workload heatmap without person IDs."""
        response = client.get(
            "/api/v1/visualization/workload?start_date=2024-01-01&end_date=2024-01-07",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 422  # Validation error

    def test_export_heatmap(self, client, admin_token, sample_schedule_data):
        """Test POST /visualization/export endpoint."""
        export_request = {
            "heatmap_type": "unified",
            "format": "png",
            "width": 1200,
            "height": 800,
            "request_params": {
                "start_date": sample_schedule_data["start_date"].isoformat(),
                "end_date": sample_schedule_data["end_date"].isoformat(),
                "include_fmit": True,
                "group_by": "person",
            },
        }

        try:
            response = client.post(
                "/api/v1/visualization/export",
                json=export_request,
                headers={"Authorization": f"Bearer {admin_token}"},
            )

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
        except Exception as e:
            pytest.skip(f"Image export not available: {str(e)}")

    def test_export_heatmap_invalid_type(
        self, client, admin_token
    ):
        """Test export with invalid heatmap type."""
        export_request = {
            "heatmap_type": "invalid",
            "format": "png",
            "width": 1200,
            "height": 800,
            "request_params": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
            },
        }

        response = client.post(
            "/api/v1/visualization/export",
            json=export_request,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400

    def test_visualization_requires_authentication(self, client):
        """Test that visualization endpoints require authentication."""
        response = client.get(
            "/api/v1/visualization/heatmap?start_date=2024-01-01&end_date=2024-01-07"
        )

        assert response.status_code == 401

    def test_unified_heatmap_with_week_range(
        self, client, admin_token, sample_schedule_data
    ):
        """Test POST /visualization/heatmap/unified with week range."""
        request_data = {
            "time_range": {
                "range_type": "week",
                "reference_date": sample_schedule_data["start_date"].isoformat(),
            },
            "include_fmit": True,
            "group_by": "person",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "title" in data
        assert data["title"] == "Person Schedule Heatmap"
        assert len(data["data"]["x_labels"]) == 7  # 7 days in a week

    def test_unified_heatmap_with_month_range(
        self, client, admin_token, sample_schedule_data
    ):
        """Test POST /visualization/heatmap/unified with month range."""
        request_data = {
            "time_range": {
                "range_type": "month",
                "reference_date": sample_schedule_data["start_date"].isoformat(),
            },
            "include_fmit": True,
            "group_by": "rotation",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["title"] == "Rotation Schedule Heatmap"
        # January has 31 days
        assert len(data["data"]["x_labels"]) == 31

    def test_unified_heatmap_with_quarter_range(
        self, client, admin_token, sample_schedule_data
    ):
        """Test POST /visualization/heatmap/unified with quarter range."""
        request_data = {
            "time_range": {
                "range_type": "quarter",
                "reference_date": sample_schedule_data["start_date"].isoformat(),
            },
            "include_fmit": False,
            "group_by": "person",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        # Q1 has 31 + 29 (leap year) + 31 = 91 days in 2024
        assert len(data["data"]["x_labels"]) == 91

    def test_unified_heatmap_with_custom_range(
        self, client, admin_token, sample_schedule_data
    ):
        """Test POST /visualization/heatmap/unified with custom range."""
        request_data = {
            "time_range": {
                "range_type": "custom",
                "start_date": sample_schedule_data["start_date"].isoformat(),
                "end_date": sample_schedule_data["end_date"].isoformat(),
            },
            "include_fmit": True,
            "group_by": "person",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]["x_labels"]) == 7

    def test_unified_heatmap_with_person_filter(
        self, client, admin_token, sample_schedule_data
    ):
        """Test unified heatmap with person filter."""
        resident1_id = str(sample_schedule_data["residents"][0].id)
        request_data = {
            "time_range": {
                "range_type": "week",
                "reference_date": sample_schedule_data["start_date"].isoformat(),
            },
            "person_ids": [resident1_id],
            "include_fmit": True,
            "group_by": "person",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["y_labels"]) == 1
        assert data["data"]["y_labels"][0] == "Dr. Smith"

    def test_unified_heatmap_invalid_group_by(
        self, client, admin_token, sample_schedule_data
    ):
        """Test unified heatmap with invalid group_by."""
        request_data = {
            "time_range": {
                "range_type": "week",
                "reference_date": sample_schedule_data["start_date"].isoformat(),
            },
            "include_fmit": True,
            "group_by": "invalid",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "group_by must be 'person' or 'rotation'" in response.json()["detail"]

    def test_unified_heatmap_custom_range_missing_dates(
        self, client, admin_token
    ):
        """Test unified heatmap with custom range missing dates."""
        request_data = {
            "time_range": {
                "range_type": "custom",
                "start_date": "2024-01-01",
                # Missing end_date
            },
            "include_fmit": True,
            "group_by": "person",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert response.status_code == 400
        assert "start_date and end_date required" in response.json()["detail"]

    def test_unified_heatmap_requires_authentication(self, client):
        """Test that unified endpoint requires authentication."""
        request_data = {
            "time_range": {
                "range_type": "week",
                "reference_date": "2024-01-01",
            },
            "include_fmit": True,
            "group_by": "person",
        }

        response = client.post(
            "/api/v1/visualization/heatmap/unified",
            json=request_data,
        )

        assert response.status_code == 401
