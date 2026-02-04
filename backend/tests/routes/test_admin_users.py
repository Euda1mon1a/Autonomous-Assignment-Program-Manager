"""Tests for admin users route."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.security import get_password_hash
from app.models.user import User


def test_admin_users_list_includes_admin(client: TestClient, auth_headers, db):
    extra_user = User(
        id=uuid4(),
        username="staffuser",
        email="staff@test.org",
        hashed_password=get_password_hash("staffpass123"),
        role="resident",
        is_active=True,
    )
    db.add(extra_user)
    db.commit()

    response = client.get("/api/v1/admin/users", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    usernames = {item["username"] for item in data["items"]}
    assert "staffuser" in usernames
