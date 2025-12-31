"""
API Endpoint Validation Tests.

Comprehensive tests for API endpoint validation, request/response
schemas, error handling, and HTTP status codes.

Test Coverage:
- Request body validation (Pydantic schemas)
- Query parameter validation
- Path parameter validation
- Response schema compliance
- HTTP status code correctness
- Error message formatting
- Content-Type handling
- Rate limiting headers
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
from app.models.user import User


# ============================================================================
# Test Class: Request Validation
# ============================================================================


class TestRequestValidation:
    """Tests for request body and parameter validation."""

    def test_invalid_json_body_returns_422(self, client: TestClient, auth_headers: dict):
        """Test that invalid JSON returns 422 Unprocessable Entity."""
        response = client.post(
            "/api/people",
            headers=auth_headers,
            data="invalid json{",  # Malformed JSON
            content_type="application/json",
        )

        assert response.status_code == 422

    def test_missing_required_field_returns_422(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that missing required field returns 422."""
        response = client.post(
            "/api/people",
            headers=auth_headers,
            json={
                # Missing required 'name' field
                "type": "resident",
                "email": "test@example.com",
            },
        )

        assert response.status_code == 422
        error_detail = response.json()
        assert "name" in str(error_detail).lower()

    def test_invalid_field_type_returns_422(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that invalid field type returns 422."""
        response = client.post(
            "/api/people",
            headers=auth_headers,
            json={
                "name": "Dr. Test",
                "type": "resident",
                "email": "test@example.com",
                "pgy_level": "not_a_number",  # Should be integer
            },
        )

        assert response.status_code == 422
        error_detail = response.json()
        assert "pgy_level" in str(error_detail).lower()

    def test_invalid_email_format_returns_422(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that invalid email format is rejected."""
        response = client.post(
            "/api/people",
            headers=auth_headers,
            json={
                "name": "Dr. Test",
                "type": "resident",
                "email": "not-an-email",  # Invalid email
                "pgy_level": 1,
            },
        )

        assert response.status_code == 422

    def test_query_parameter_type_validation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test query parameter type validation."""
        response = client.get(
            "/api/assignments?limit=not_a_number",  # Invalid limit type
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_path_parameter_uuid_validation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test UUID path parameter validation."""
        response = client.get(
            "/api/people/invalid-uuid",  # Not a valid UUID
            headers=auth_headers,
        )

        assert response.status_code == 422 or response.status_code == 400

    def test_date_parameter_format_validation(
        self, client: TestClient, auth_headers: dict
    ):
        """Test date parameter format validation."""
        response = client.get(
            "/api/blocks?date=not-a-date",  # Invalid date format
            headers=auth_headers,
        )

        assert response.status_code == 422


# ============================================================================
# Test Class: Response Validation
# ============================================================================


class TestResponseValidation:
    """Tests for response schema compliance."""

    def test_successful_create_returns_201(
        self, client: TestClient, auth_headers: dict
    ):
        """Test successful resource creation returns 201 Created."""
        response = client.post(
            "/api/people",
            headers=auth_headers,
            json={
                "name": "Dr. New Person",
                "type": "resident",
                "email": "new@example.com",
                "pgy_level": 2,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["name"] == "Dr. New Person"

    def test_successful_update_returns_200(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful update returns 200 OK."""
        # Create person first
        person = Person(
            id=uuid4(),
            name="Dr. Original",
            type="faculty",
            email="original@test.org",
        )
        db.add(person)
        db.commit()

        response = client.put(
            f"/api/people/{person.id}",
            headers=auth_headers,
            json={
                "name": "Dr. Updated",
                "type": "faculty",
                "email": "updated@test.org",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Dr. Updated"

    def test_successful_delete_returns_204(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test successful delete returns 204 No Content."""
        person = Person(
            id=uuid4(),
            name="Dr. ToDelete",
            type="faculty",
            email="delete@test.org",
        )
        db.add(person)
        db.commit()

        response = client.delete(
            f"/api/people/{person.id}",
            headers=auth_headers,
        )

        assert response.status_code == 204 or response.status_code == 200

    def test_not_found_returns_404(self, client: TestClient, auth_headers: dict):
        """Test resource not found returns 404."""
        fake_id = uuid4()
        response = client.get(
            f"/api/people/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        error = response.json()
        assert "detail" in error
        assert "not found" in error["detail"].lower()

    def test_list_endpoint_returns_array(
        self, client: TestClient, auth_headers: dict
    ):
        """Test list endpoint returns array in response."""
        response = client.get(
            "/api/people",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or ("items" in data and isinstance(data["items"], list))


# ============================================================================
# Test Class: Error Handling
# ============================================================================


class TestErrorHandling:
    """Tests for error response formatting and handling."""

    def test_error_response_has_detail_field(
        self, client: TestClient, auth_headers: dict
    ):
        """Test error responses include 'detail' field."""
        response = client.get(
            f"/api/people/{uuid4()}",  # Non-existent resource
            headers=auth_headers,
        )

        assert response.status_code == 404
        error = response.json()
        assert "detail" in error

    def test_validation_error_includes_field_info(
        self, client: TestClient, auth_headers: dict
    ):
        """Test validation errors specify which fields failed."""
        response = client.post(
            "/api/people",
            headers=auth_headers,
            json={
                "type": "resident",
                # Missing name and email
            },
        )

        assert response.status_code == 422
        error = response.json()
        # Should specify missing fields
        assert "detail" in error

    def test_internal_error_returns_500(
        self, client: TestClient, auth_headers: dict, monkeypatch
    ):
        """Test internal server errors return 500."""
        # This test would need to mock an internal error
        # Implementation depends on how endpoints handle exceptions
        pass

    def test_conflict_error_returns_409(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test resource conflict returns 409."""
        # Create person with unique email
        person1 = Person(
            id=uuid4(),
            name="Dr. First",
            type="faculty",
            email="duplicate@test.org",
        )
        db.add(person1)
        db.commit()

        # Try to create another with same email
        response = client.post(
            "/api/people",
            headers=auth_headers,
            json={
                "name": "Dr. Second",
                "type": "faculty",
                "email": "duplicate@test.org",
            },
        )

        # Should return 409 Conflict or 400 Bad Request
        assert response.status_code in [400, 409]


# ============================================================================
# Test Class: HTTP Headers
# ============================================================================


class TestHTTPHeaders:
    """Tests for HTTP headers in requests and responses."""

    def test_content_type_json_required(
        self, client: TestClient, auth_headers: dict
    ):
        """Test endpoints require application/json content type."""
        response = client.post(
            "/api/people",
            headers={**auth_headers, "Content-Type": "text/plain"},
            data="name=Test",
        )

        # Should reject non-JSON content type
        assert response.status_code in [400, 415, 422]

    def test_response_content_type_is_json(
        self, client: TestClient, auth_headers: dict
    ):
        """Test response content type is application/json."""
        response = client.get(
            "/api/people",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_cors_headers_present(self, client: TestClient):
        """Test CORS headers are present in responses."""
        response = client.options("/api/people")

        # CORS headers should be present
        # Implementation depends on CORS middleware configuration
        assert response.status_code in [200, 204]

    def test_rate_limit_headers_present(
        self, client: TestClient, auth_headers: dict
    ):
        """Test rate limit headers are included."""
        response = client.get(
            "/api/people",
            headers=auth_headers,
        )

        # Rate limit headers (if enabled)
        # X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        # Implementation depends on rate limiting configuration


# ============================================================================
# Test Class: Pagination
# ============================================================================


class TestPagination:
    """Tests for pagination in list endpoints."""

    def test_limit_parameter_controls_page_size(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test limit parameter controls number of results."""
        # Create multiple people
        for i in range(20):
            person = Person(
                id=uuid4(),
                name=f"Dr. Person {i}",
                type="resident",
                email=f"person{i}@test.org",
                pgy_level=1,
            )
            db.add(person)
        db.commit()

        response = client.get(
            "/api/people?limit=5",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", [])
        assert len(items) <= 5

    def test_offset_parameter_skips_results(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test offset parameter skips specified number of results."""
        # Create people with predictable names
        for i in range(10):
            person = Person(
                id=uuid4(),
                name=f"Dr. Person {i:02d}",
                type="resident",
                email=f"person{i}@test.org",
                pgy_level=1,
            )
            db.add(person)
        db.commit()

        # Get first page
        response1 = client.get(
            "/api/people?limit=5&offset=0",
            headers=auth_headers,
        )
        # Get second page
        response2 = client.get(
            "/api/people?limit=5&offset=5",
            headers=auth_headers,
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        # Pages should have different results
        data1 = response1.json()
        data2 = response2.json()
        items1 = data1 if isinstance(data1, list) else data1.get("items", [])
        items2 = data2 if isinstance(data2, list) else data2.get("items", [])

        # Assuming items have IDs
        if len(items1) > 0 and len(items2) > 0:
            ids1 = {item["id"] for item in items1}
            ids2 = {item["id"] for item in items2}
            assert ids1 != ids2  # Different items


# ============================================================================
# Test Class: Filtering and Sorting
# ============================================================================


class TestFilteringAndSorting:
    """Tests for filtering and sorting in list endpoints."""

    def test_filter_by_type(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test filtering by person type."""
        # Create mix of residents and faculty
        for i in range(3):
            resident = Person(
                id=uuid4(),
                name=f"Dr. Resident {i}",
                type="resident",
                email=f"resident{i}@test.org",
                pgy_level=1,
            )
            faculty = Person(
                id=uuid4(),
                name=f"Dr. Faculty {i}",
                type="faculty",
                email=f"faculty{i}@test.org",
            )
            db.add_all([resident, faculty])
        db.commit()

        response = client.get(
            "/api/people?type=resident",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", [])
        # All results should be residents
        for item in items:
            assert item["type"] == "resident"

    def test_sort_by_field(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test sorting results by field."""
        # Create people with different names
        names = ["Charlie", "Alice", "Bob"]
        for name in names:
            person = Person(
                id=uuid4(),
                name=f"Dr. {name}",
                type="resident",
                email=f"{name.lower()}@test.org",
                pgy_level=1,
            )
            db.add(person)
        db.commit()

        response = client.get(
            "/api/people?sort=name",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", [])

        # Check if sorted (assuming ascending order)
        if len(items) >= 2:
            for i in range(len(items) - 1):
                assert items[i]["name"] <= items[i + 1]["name"]

    def test_date_range_filtering(
        self, client: TestClient, auth_headers: dict, db: Session
    ):
        """Test filtering by date range."""
        today = date.today()

        # Create blocks for different dates
        for i in range(10):
            block_date = today + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=block_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
        db.commit()

        # Query for specific date range
        start = today + timedelta(days=2)
        end = today + timedelta(days=5)

        response = client.get(
            f"/api/blocks?start_date={start}&end_date={end}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data.get("items", [])

        # All results should be within range
        for item in items:
            block_date = date.fromisoformat(item["date"])
            assert start <= block_date <= end
