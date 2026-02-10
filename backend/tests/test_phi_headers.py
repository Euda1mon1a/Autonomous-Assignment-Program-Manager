"""Tests for X-Contains-PHI response header middleware."""

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.middleware.phi_middleware import PHIMiddleware


def _ok_handler(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


def _build_app() -> Starlette:
    """Create a minimal Starlette app with PHIMiddleware for testing."""
    routes = [
        Route("/api/v1/people", _ok_handler),
        Route("/api/v1/people/{person_id}", _ok_handler),
        Route("/api/v1/people/residents", _ok_handler),
        Route("/api/v1/people/faculty", _ok_handler),
        Route("/api/v1/absences", _ok_handler),
        Route("/api/v1/absences/{absence_id}", _ok_handler),
        Route("/api/v1/assignments", _ok_handler),
        Route("/api/v1/schedule", _ok_handler),
        Route("/api/v1/export", _ok_handler),
        Route("/health", _ok_handler),
        Route("/api/v1/health", _ok_handler),
        Route("/api/v1/blocks", _ok_handler),
    ]
    app = Starlette(routes=routes)
    app.add_middleware(PHIMiddleware)
    return app


@pytest.fixture()
def client():
    return TestClient(_build_app())


class TestPHIHeaders:
    """Verify X-Contains-PHI header presence on PHI endpoints."""

    def test_header_on_people(self, client):
        resp = client.get("/api/v1/people")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_header_on_people_parameterized(self, client):
        resp = client.get("/api/v1/people/123")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_header_on_residents(self, client):
        resp = client.get("/api/v1/people/residents")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_header_on_faculty(self, client):
        resp = client.get("/api/v1/people/faculty")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_header_on_absences(self, client):
        resp = client.get("/api/v1/absences")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_header_on_absences_parameterized(self, client):
        resp = client.get("/api/v1/absences/42")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_header_on_schedule(self, client):
        resp = client.get("/api/v1/schedule")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_header_on_export(self, client):
        resp = client.get("/api/v1/export")
        assert resp.headers.get("X-Contains-PHI") == "true"

    def test_no_header_on_health(self, client):
        resp = client.get("/health")
        assert "X-Contains-PHI" not in resp.headers

    def test_no_header_on_api_health(self, client):
        resp = client.get("/api/v1/health")
        assert "X-Contains-PHI" not in resp.headers

    def test_no_header_on_blocks(self, client):
        resp = client.get("/api/v1/blocks")
        assert "X-Contains-PHI" not in resp.headers

    def test_phi_handling_header_present(self, client):
        """PHIMiddleware also sets X-PHI-Handling header."""
        resp = client.get("/api/v1/people")
        assert "X-PHI-Handling" in resp.headers
