"""
Comprehensive tests for academic blocks API routes.

Tests the /matrix/academic-blocks and /matrix/blocks endpoints,
covering CRUD operations, filtering, validation, and edge cases.
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

# ============================================================================
# Test Data Setup Fixtures
# ============================================================================


@pytest.fixture
def academic_year_2024() -> str:
    """Academic year string for testing."""
    return "2024-2025"


@pytest.fixture
def academic_year_2023() -> str:
    """Previous academic year string for testing."""
    return "2023-2024"


@pytest.fixture
def sample_academic_blocks(db: Session) -> list[Block]:
    """Create blocks for a full academic year (July 1, 2024 - June 30, 2025)."""
    blocks = []
    start_date = date(2024, 7, 1)
    end_date = date(2025, 6, 30)

    current_date = start_date
    block_number = 1

    while current_date <= end_date:
        for time_of_day in ["AM", "PM"]:
            block = Block(
                id=uuid4(),
                date=current_date,
                time_of_day=time_of_day,
                block_number=block_number,
                is_weekend=(current_date.weekday() >= 5),
                is_holiday=False,
            )
            db.add(block)
            blocks.append(block)

        current_date += timedelta(days=1)
        # Update block number every 28 days (4 weeks)
        if (current_date - start_date).days % 28 == 0:
            block_number += 1

    db.commit()
    return blocks


@pytest.fixture
def sample_residents_all_pgy(db: Session) -> list[Person]:
    """Create residents across all PGY levels."""
    residents = []
    for pgy in range(1, 4):
        for i in range(2):  # 2 residents per PGY level
            resident = Person(
                id=uuid4(),
                name=f"Dr. Resident PGY{pgy}-{i + 1}",
                type="resident",
                email=f"resident.pgy{pgy}.{i + 1}@hospital.org",
                pgy_level=pgy,
            )
            db.add(resident)
            residents.append(resident)

    db.commit()
    for r in residents:
        db.refresh(r)
    return residents


@pytest.fixture
def sample_rotations(db: Session) -> list[RotationTemplate]:
    """Create sample rotation templates."""
    rotations = [
        RotationTemplate(
            id=uuid4(),
            name="Sports Medicine Clinic",
            rotation_type="clinic",
            abbreviation="SM",
            max_residents=4,
        ),
        RotationTemplate(
            id=uuid4(),
            name="Primary Care",
            rotation_type="clinic",
            abbreviation="PC",
            max_residents=6,
        ),
        RotationTemplate(
            id=uuid4(),
            name="Emergency Medicine",
            rotation_type="clinic",
            abbreviation="EM",
            max_residents=3,
        ),
    ]

    for rotation in rotations:
        db.add(rotation)

    db.commit()
    for r in rotations:
        db.refresh(r)
    return rotations


@pytest.fixture
def sample_assignments_academic_year(
    db: Session,
    sample_academic_blocks: list[Block],
    sample_residents_all_pgy: list[Person],
    sample_rotations: list[RotationTemplate],
) -> list[Assignment]:
    """Create assignments for the academic year."""
    assignments = []

    # Assign first few weeks for testing
    for block in sample_academic_blocks[:56]:  # First 4 weeks (28 days × 2 blocks/day)
        for i, resident in enumerate(sample_residents_all_pgy[:3]):  # First 3 residents
            rotation = sample_rotations[i % len(sample_rotations)]
            assignment = Assignment(
                id=uuid4(),
                block_id=block.id,
                person_id=resident.id,
                rotation_template_id=rotation.id,
                role="primary",
            )
            db.add(assignment)
            assignments.append(assignment)

    db.commit()
    return assignments


# ============================================================================
# Authentication Tests
# ============================================================================


class TestAcademicBlocksAuthentication:
    """Tests for academic blocks API authentication requirements."""

    def test_get_matrix_requires_authentication(self, client: TestClient):
        """Test that GET /matrix/academic-blocks requires authentication."""
        response = client.get(
            "/api/matrix/academic-blocks", params={"academic_year": "2024-2025"}
        )
        assert response.status_code == 401

    def test_list_blocks_requires_authentication(self, client: TestClient):
        """Test that GET /matrix/blocks requires authentication."""
        response = client.get(
            "/api/matrix/blocks", params={"academic_year": "2024-2025"}
        )
        assert response.status_code == 401


# ============================================================================
# Block Matrix Endpoint Tests
# ============================================================================


class TestGetAcademicBlockMatrix:
    """Tests for GET /matrix/academic-blocks endpoint."""

    def test_get_matrix_success(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
    ):
        """Test successful retrieval of academic block matrix."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "columns" in data
        assert "rows" in data
        assert "cells" in data
        assert "academic_year" in data
        assert "summary" in data

        # Verify academic year
        assert data["academic_year"] == academic_year_2024

        # Verify columns (academic blocks)
        assert isinstance(data["columns"], list)
        assert len(data["columns"]) == 13  # 13 blocks in academic year

        # Verify first column structure
        if data["columns"]:
            column = data["columns"][0]
            assert "block_number" in column
            assert "start_date" in column
            assert "end_date" in column
            assert "name" in column

    def test_get_matrix_with_pgy_filter(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
    ):
        """Test filtering matrix by PGY level."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={
                "academic_year": academic_year_2024,
                "pgy_level": 2,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # All returned residents should be PGY-2
        for row in data["rows"]:
            assert row["pgy_level"] == 2

    def test_get_matrix_pgy_level_1(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
    ):
        """Test filtering for PGY-1 residents."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={
                "academic_year": academic_year_2024,
                "pgy_level": 1,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for row in data["rows"]:
            assert row["pgy_level"] == 1

    def test_get_matrix_pgy_level_3(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
    ):
        """Test filtering for PGY-3 residents."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={
                "academic_year": academic_year_2024,
                "pgy_level": 3,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for row in data["rows"]:
            assert row["pgy_level"] == 3

    def test_get_matrix_rows_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
    ):
        """Test that rows have correct structure."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify rows structure
        assert isinstance(data["rows"], list)
        if data["rows"]:
            row = data["rows"][0]
            assert "resident_id" in row
            assert "name" in row
            assert "pgy_level" in row

    def test_get_matrix_cells_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
        sample_assignments_academic_year: list[Assignment],
    ):
        """Test that cells have correct structure."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify cells structure
        assert isinstance(data["cells"], list)
        if data["cells"]:
            cell = data["cells"][0]
            assert "row_index" in cell
            assert "column_index" in cell
            assert "hours" in cell
            assert "acgme_status" in cell

            # ACGME status structure
            acgme = cell["acgme_status"]
            assert "is_compliant" in acgme
            assert "warnings" in acgme
            assert "violations" in acgme
            assert "hours_worked" in acgme
            assert "max_hours_allowed" in acgme

    def test_get_matrix_summary_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
    ):
        """Test that summary has correct structure."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify summary structure
        summary = data["summary"]
        assert "total_residents" in summary
        assert "total_blocks" in summary
        assert "compliance_rate" in summary
        assert isinstance(summary["total_residents"], int)
        assert isinstance(summary["total_blocks"], int)
        assert isinstance(summary["compliance_rate"], (int, float))

    def test_get_matrix_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_assignments_academic_year: list[Assignment],
    ):
        """Test matrix with actual assignments."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have cells with rotation data
        cells_with_rotation = [
            cell for cell in data["cells"] if cell.get("rotation") is not None
        ]
        assert len(cells_with_rotation) > 0

    def test_get_matrix_empty_academic_year(
        self,
        client: TestClient,
        auth_headers: dict,
        sample_residents_all_pgy: list[Person],
    ):
        """Test matrix for academic year with no blocks/assignments."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": "2022-2023"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return structure but with empty/zero assignments
        assert data["academic_year"] == "2022-2023"
        assert len(data["columns"]) == 13  # Always generates blocks


# ============================================================================
# Block Matrix Validation Tests
# ============================================================================


class TestAcademicBlockMatrixValidation:
    """Tests for validation and error handling in block matrix endpoint."""

    def test_get_matrix_missing_academic_year(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that academic_year parameter is required."""
        response = client.get(
            "/api/matrix/academic-blocks",
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_get_matrix_invalid_academic_year_format(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test invalid academic year format."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": "2024"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "format" in response.json()["detail"].lower()

    def test_get_matrix_invalid_year_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test academic year with invalid year range."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": "2024-2026"},  # Should be 2024-2025
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "year" in response.json()["detail"].lower()

    def test_get_matrix_invalid_pgy_level_too_low(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
    ):
        """Test PGY level below valid range."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={
                "academic_year": academic_year_2024,
                "pgy_level": 0,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_get_matrix_invalid_pgy_level_too_high(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
    ):
        """Test PGY level above valid range."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={
                "academic_year": academic_year_2024,
                "pgy_level": 4,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_get_matrix_malformed_year_string(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test malformed academic year string."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": "twenty-twenty-four"},
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_get_matrix_empty_year_string(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test empty academic year string."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": ""},
            headers=auth_headers,
        )

        assert response.status_code == 400 or response.status_code == 422


# ============================================================================
# Block List Endpoint Tests
# ============================================================================


class TestListAcademicBlocks:
    """Tests for GET /matrix/blocks endpoint."""

    def test_list_blocks_success(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
    ):
        """Test successful retrieval of academic blocks list."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "blocks" in data
        assert "academic_year" in data
        assert "total_blocks" in data

        # Verify academic year
        assert data["academic_year"] == academic_year_2024

        # Verify blocks
        assert isinstance(data["blocks"], list)
        assert data["total_blocks"] == len(data["blocks"])
        assert len(data["blocks"]) == 13  # 13 blocks per academic year

    def test_list_blocks_structure(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
    ):
        """Test that block summaries have correct structure."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify block structure
        if data["blocks"]:
            block = data["blocks"][0]
            assert "block_number" in block
            assert "name" in block
            assert "start_date" in block
            assert "end_date" in block
            assert "total_assignments" in block
            assert "total_residents" in block
            assert "compliance_rate" in block
            assert "average_hours" in block

    def test_list_blocks_ordering(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
    ):
        """Test that blocks are ordered correctly."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Blocks should be in sequential order
        block_numbers = [block["block_number"] for block in data["blocks"]]
        assert block_numbers == sorted(block_numbers)
        assert block_numbers[0] == 1
        assert block_numbers[-1] == 13

    def test_list_blocks_date_ranges(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
    ):
        """Test that block date ranges are correct."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # First block should start July 1, 2024
        first_block = data["blocks"][0]
        assert first_block["start_date"] == "2024-07-01"

        # Last block should end June 30, 2025
        last_block = data["blocks"][-1]
        assert last_block["end_date"] == "2025-06-30"

        # Check that blocks are contiguous (no gaps)
        for i in range(len(data["blocks"]) - 1):
            current_end = date.fromisoformat(data["blocks"][i]["end_date"])
            next_start = date.fromisoformat(data["blocks"][i + 1]["start_date"])
            assert (next_start - current_end).days == 1

    def test_list_blocks_with_assignments(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_assignments_academic_year: list[Assignment],
    ):
        """Test block list with actual assignments."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # First block should have assignments
        first_block = data["blocks"][0]
        assert first_block["total_assignments"] > 0
        assert first_block["total_residents"] > 0

    def test_list_blocks_statistics_accuracy(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_assignments_academic_year: list[Assignment],
    ):
        """Test that block statistics are accurate."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for block in data["blocks"]:
            # Compliance rate should be 0-100
            assert 0 <= block["compliance_rate"] <= 100

            # Average hours should be non-negative
            assert block["average_hours"] >= 0

            # Total assignments should be non-negative
            assert block["total_assignments"] >= 0
            assert block["total_residents"] >= 0

    def test_list_blocks_empty_academic_year(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test listing blocks for academic year with no data."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": "2020-2021"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return structure with zero statistics
        assert data["total_blocks"] == 13
        for block in data["blocks"]:
            assert block["total_assignments"] == 0
            assert block["total_residents"] == 0


# ============================================================================
# Block List Validation Tests
# ============================================================================


class TestListAcademicBlocksValidation:
    """Tests for validation and error handling in blocks list endpoint."""

    def test_list_blocks_missing_academic_year(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test that academic_year parameter is required."""
        response = client.get(
            "/api/matrix/blocks",
            headers=auth_headers,
        )

        assert response.status_code == 422  # Validation error

    def test_list_blocks_invalid_academic_year_format(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test invalid academic year format."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": "2024/2025"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "format" in response.json()["detail"].lower()

    def test_list_blocks_invalid_year_range(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test academic year with invalid year range."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": "2025-2024"},  # Reversed
            headers=auth_headers,
        )

        assert response.status_code == 400

    def test_list_blocks_malformed_year(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test malformed academic year."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": "not-a-year"},
            headers=auth_headers,
        )

        assert response.status_code == 400


# ============================================================================
# Edge Cases and Special Scenarios
# ============================================================================


class TestAcademicBlocksEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_matrix_no_residents(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
    ):
        """Test matrix when no residents exist."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty rows
        assert len(data["rows"]) == 0
        assert data["summary"]["total_residents"] == 0

    def test_matrix_pgy_level_no_matches(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
        sample_residents_all_pgy: list[Person],
    ):
        """Test filtering by PGY level with no matches should still work."""
        # Note: All PGY levels 1-3 exist, so this tests the filtering logic
        response = client.get(
            "/api/matrix/academic-blocks",
            params={
                "academic_year": academic_year_2024,
                "pgy_level": 1,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return PGY-1 residents
        assert all(row["pgy_level"] == 1 for row in data["rows"])

    def test_blocks_multiple_academic_years(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        academic_year_2023: str,
    ):
        """Test that different academic years return different data."""
        response_2024 = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        response_2023 = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2023},
            headers=auth_headers,
        )

        assert response_2024.status_code == 200
        assert response_2023.status_code == 200

        data_2024 = response_2024.json()
        data_2023 = response_2023.json()

        # Academic years should be different
        assert data_2024["academic_year"] != data_2023["academic_year"]

        # Date ranges should be different
        assert (
            data_2024["blocks"][0]["start_date"] != data_2023["blocks"][0]["start_date"]
        )

    def test_matrix_acgme_compliance_calculation(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_assignments_academic_year: list[Assignment],
    ):
        """Test ACGME compliance is calculated in matrix cells."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check that ACGME status is populated
        for cell in data["cells"]:
            acgme = cell["acgme_status"]
            assert isinstance(acgme["is_compliant"], bool)
            assert isinstance(acgme["warnings"], list)
            assert isinstance(acgme["violations"], list)
            assert acgme["hours_worked"] >= 0

    def test_blocks_compliance_rate_range(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_assignments_academic_year: list[Assignment],
    ):
        """Test that compliance rate is always in valid range."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for block in data["blocks"]:
            compliance_rate = block["compliance_rate"]
            assert 0 <= compliance_rate <= 100
            assert isinstance(compliance_rate, (int, float))

    def test_matrix_cell_count(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_residents_all_pgy: list[Person],
    ):
        """Test that matrix has correct number of cells."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Total cells = residents × blocks
        expected_cells = len(data["rows"]) * len(data["columns"])
        assert len(data["cells"]) == expected_cells

    def test_matrix_future_academic_year(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test matrix for future academic year."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": "2030-2031"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should work even for future years
        assert data["academic_year"] == "2030-2031"
        assert len(data["columns"]) == 13

    def test_blocks_past_academic_year(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """Test blocks for past academic year."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": "2010-2011"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should work for past years
        assert data["academic_year"] == "2010-2011"
        assert data["total_blocks"] == 13


# ============================================================================
# Response Format Tests
# ============================================================================


class TestAcademicBlocksResponseFormat:
    """Tests for response format and data types."""

    def test_matrix_response_json_format(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
    ):
        """Test that matrix response is valid JSON."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Should be valid JSON
        data = response.json()
        assert isinstance(data, dict)

    def test_blocks_response_json_format(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
    ):
        """Test that blocks response is valid JSON."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        data = response.json()
        assert isinstance(data, dict)

    def test_matrix_date_format(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
    ):
        """Test that dates are in ISO format."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check date formats in columns
        for column in data["columns"]:
            start_date = column["start_date"]
            end_date = column["end_date"]

            # Should be parseable as ISO date
            try:
                date.fromisoformat(start_date)
                date.fromisoformat(end_date)
            except ValueError:
                pytest.fail(f"Invalid date format: {start_date} or {end_date}")

    def test_blocks_date_format(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_academic_blocks: list[Block],
    ):
        """Test that block dates are in ISO format."""
        response = client.get(
            "/api/matrix/blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for block in data["blocks"]:
            try:
                date.fromisoformat(block["start_date"])
                date.fromisoformat(block["end_date"])
            except ValueError:
                pytest.fail(f"Invalid date format in block {block['block_number']}")

    def test_matrix_uuid_format(
        self,
        client: TestClient,
        auth_headers: dict,
        academic_year_2024: str,
        sample_residents_all_pgy: list[Person],
    ):
        """Test that resident IDs are valid UUIDs."""
        response = client.get(
            "/api/matrix/academic-blocks",
            params={"academic_year": academic_year_2024},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        for row in data["rows"]:
            resident_id = row["resident_id"]
            try:
                # Should be valid UUID
                from uuid import UUID

                UUID(resident_id)
            except (ValueError, AttributeError):
                pytest.fail(f"Invalid UUID format: {resident_id}")
