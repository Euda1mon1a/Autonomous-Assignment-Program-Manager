"""Tests for the Annual Rotation Optimizer service and API routes.

Uses the test fixtures from conftest.py (TestClient + SQLite in-memory DB).
Tests the full lifecycle: create → optimize → publish → delete.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from app.models.block_assignment import BlockAssignment
from app.models.annual_rotation import AnnualRotationAssignment, AnnualRotationPlan
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def residents_18(db: Session) -> list[Person]:
    """Create 18 residents (6 per PGY level) — matches the ARO model."""
    residents = []
    for pgy in (1, 2, 3):
        for i in range(6):
            r = Person(
                id=uuid4(),
                name=f"Resident_PGY{pgy}_{i}",
                type="resident",
                email=f"res_pgy{pgy}_{i}@test.org",
                pgy_level=pgy,
            )
            db.add(r)
            residents.append(r)
    db.commit()
    return residents


@pytest.fixture
def residents_3(db: Session) -> list[Person]:
    """Create 3 residents (1 per PGY level) — minimal config."""
    residents = []
    for pgy in (1, 2, 3):
        r = Person(
            id=uuid4(),
            name=f"Resident_PGY{pgy}_0",
            type="resident",
            email=f"res_pgy{pgy}_min@test.org",
            pgy_level=pgy,
        )
        db.add(r)
        residents.append(r)
    db.commit()
    return residents


# ── Plan CRUD Tests ─────────────────────────────────────────────────────────


class TestPlanCRUD:
    """Test plan create, list, get, delete via API."""

    def test_create_plan(self, authed_client, db):
        """POST / creates a draft plan."""
        resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={
                "academic_year": 2026,
                "name": "AY 2026-27 Draft",
                "solver_time_limit": 15.0,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["academic_year"] == 2026
        assert data["name"] == "AY 2026-27 Draft"
        assert data["assignments"] == []

    def test_list_plans(self, authed_client, db):
        """GET / returns all plans."""
        # Create two plans
        authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Plan A"},
        )
        authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Plan B"},
        )

        resp = authed_client.get("/api/v1/annual-planner/plans/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_plan(self, authed_client, db):
        """GET /{id} returns plan with assignments."""
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Test Plan"},
        )
        plan_id = create_resp.json()["id"]

        resp = authed_client.get(f"/api/v1/annual-planner/plans/{plan_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == plan_id

    def test_get_plan_not_found(self, authed_client, db):
        """GET /{id} returns 404 for non-existent plan."""
        fake_id = str(uuid4())
        resp = authed_client.get(f"/api/v1/annual-planner/plans/{fake_id}")
        assert resp.status_code == 404

    def test_delete_draft_plan(self, authed_client, db):
        """DELETE /{id} removes a draft plan."""
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "To Delete"},
        )
        plan_id = create_resp.json()["id"]

        resp = authed_client.delete(f"/api/v1/annual-planner/plans/{plan_id}")
        assert resp.status_code == 204

        # Verify it's gone
        resp = authed_client.get(f"/api/v1/annual-planner/plans/{plan_id}")
        assert resp.status_code == 404

    def test_requires_auth(self, client, db):
        """Unauthenticated requests return 401."""
        resp = client.get("/api/v1/annual-planner/plans/")
        assert resp.status_code == 401


# ── Optimize Tests ──────────────────────────────────────────────────────────


class TestOptimize:
    """Test the optimize endpoint."""

    def test_optimize_returns_solution(self, authed_client, residents_3):
        """POST /{id}/optimize runs the solver and returns assignments."""
        # Create plan
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Optimize Test"},
        )
        assert create_resp.status_code == 201
        plan_id = create_resp.json()["id"]

        # Optimize
        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/optimize",
            json={"solver_time_limit": 30.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "optimized"
        assert data["solver_status"] in ("OPTIMAL", "FEASIBLE")
        assert data["total_assignments"] > 0
        assert len(data["plan"]["assignments"]) > 0

    def test_optimize_updates_plan_status(self, authed_client, residents_3):
        """After optimize, plan status should be 'optimized'."""
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Status Test"},
        )
        plan_id = create_resp.json()["id"]

        authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/optimize",
            json={},
        )

        # Verify status
        resp = authed_client.get(f"/api/v1/annual-planner/plans/{plan_id}")
        assert resp.json()["status"] == "optimized"
        assert resp.json()["solver_status"] in ("OPTIMAL", "FEASIBLE")

    def test_optimize_no_residents_400(self, authed_client, db):
        """Optimize with no residents in DB returns 400."""
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "No Residents"},
        )
        plan_id = create_resp.json()["id"]

        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/optimize",
        )
        assert resp.status_code == 400

    def test_re_optimize_clears_old_assignments(self, authed_client, residents_3):
        """Re-optimizing replaces previous assignments."""
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Re-optimize"},
        )
        plan_id = create_resp.json()["id"]

        # First optimize
        resp1 = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/optimize",
        )
        count1 = resp1.json()["total_assignments"]

        # Second optimize
        resp2 = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/optimize",
        )
        count2 = resp2.json()["total_assignments"]

        # Counts should be the same (not doubled)
        assert count1 == count2


# ── Publish Tests ───────────────────────────────────────────────────────────


class TestPublish:
    """Test the publish lifecycle."""

    def test_publish_writes_block_assignments(self, authed_client, residents_3, db):
        """Publishing creates block_assignments rows."""
        # Create + optimize
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Publish Test"},
        )
        plan_id = create_resp.json()["id"]

        authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/optimize",
        )

        # Publish
        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/publish",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"

        # Verify block_assignments were created
        ba_count = (
            db.query(BlockAssignment)
            .filter(
                BlockAssignment.academic_year == 2026,
                BlockAssignment.created_by == "annual_rotation_optimizer",
            )
            .count()
        )
        assert ba_count > 0

    def test_publish_draft_plan_fails(self, authed_client, db):
        """Cannot publish a draft plan."""
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Draft Publish"},
        )
        plan_id = create_resp.json()["id"]

        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/publish",
        )
        assert resp.status_code == 409

    def test_delete_published_plan_fails(self, authed_client, residents_3, db):
        """Cannot delete a published plan."""
        create_resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "No Delete"},
        )
        plan_id = create_resp.json()["id"]

        authed_client.post(f"/api/v1/annual-planner/plans/{plan_id}/optimize")
        authed_client.post(f"/api/v1/annual-planner/plans/{plan_id}/publish")

        resp = authed_client.delete(f"/api/v1/annual-planner/plans/{plan_id}")
        assert resp.status_code == 409


# ── Status Transition Tests ─────────────────────────────────────────────────


class TestStatusTransitions:
    """Test the full lifecycle: draft → optimized → published."""

    def test_full_lifecycle(self, authed_client, residents_3, db):
        """Full lifecycle: create → optimize → publish."""
        # Create
        resp = authed_client.post(
            "/api/v1/annual-planner/plans/",
            json={"academic_year": 2026, "name": "Full Lifecycle"},
        )
        assert resp.status_code == 201
        plan_id = resp.json()["id"]
        assert resp.json()["status"] == "draft"

        # Optimize
        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/optimize",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "optimized"

        # Publish
        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan_id}/publish",
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "published"


# ── Combined Rotation Publish Tests ────────────────────────────────────────


class TestPublishCombinedRotations:
    """Test that publish_plan correctly maps combined rotations."""

    def test_combined_rotation_maps_to_template(self, authed_client, db):
        """Combined rotation names use ARO_COMBINED_TEMPLATE_MAP to find templates."""
        # Create a resident (not in the PGY 1-3 pool to avoid solver conflicts)
        resident = Person(
            id=uuid4(),
            name="Res_Combined_Test",
            type="resident",
            email="combined_test@test.org",
            pgy_level=2,
        )
        db.add(resident)

        # Create the NF-CARDIO combined template in DB
        nf_cardio = RotationTemplate(
            id=uuid4(),
            name="NF + Cardiology Combined",
            rotation_type="inpatient",
            abbreviation="NF-CARDIO",
            display_abbreviation="NF-CARDIO",
            is_block_half_rotation=False,
            leave_eligible=False,
        )
        db.add(nf_cardio)
        db.commit()

        # Create plan directly in "optimized" state (skip solver)
        plan = AnnualRotationPlan(
            id=uuid4(),
            academic_year=2026,
            name="Combined Test",
            status="optimized",
            solver_status="OPTIMAL",
        )
        db.add(plan)
        db.flush()

        # Add a single combined assignment
        db.add(
            AnnualRotationAssignment(
                plan_id=plan.id,
                person_id=resident.id,
                block_number=5,
                rotation_name="[NF + Card]",
                is_fixed=False,
            )
        )
        db.commit()

        # Publish via API
        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan.id}/publish",
        )
        assert resp.status_code == 200

        # Check that the block assignment uses the NF-CARDIO template
        ba = (
            db.query(BlockAssignment)
            .filter(
                BlockAssignment.academic_year == 2026,
                BlockAssignment.resident_id == resident.id,
                BlockAssignment.block_number == 5,
            )
            .first()
        )
        assert ba is not None
        assert ba.rotation_template_id == nf_cardio.id
        # NF-CARDIO is a combined template (None secondary), so secondary should be NULL
        assert ba.secondary_rotation_template_id is None

    def test_two_template_split_sets_secondary(self, authed_client, db):
        """Two-template combined rotations set secondary_rotation_template_id."""
        resident = Person(
            id=uuid4(),
            name="Res_TwoTmpl_Test",
            type="resident",
            email="two_tmpl@test.org",
            pgy_level=3,
        )
        db.add(resident)

        # Create PSYCH and NF-AM templates
        psych = RotationTemplate(
            id=uuid4(),
            name="Psychiatry",
            rotation_type="outpatient",
            abbreviation="PSYCH",
            display_abbreviation="PSYCH",
            is_block_half_rotation=False,
            leave_eligible=True,
        )
        nf_am = RotationTemplate(
            id=uuid4(),
            name="Night Float AM",
            rotation_type="inpatient",
            abbreviation="NF-AM",
            display_abbreviation="NF-AM",
            is_block_half_rotation=True,
            leave_eligible=False,
        )
        db.add(psych)
        db.add(nf_am)
        db.commit()

        # Create plan directly in "optimized" state (skip solver)
        plan = AnnualRotationPlan(
            id=uuid4(),
            academic_year=2026,
            name="Two Template Split",
            status="optimized",
            solver_status="OPTIMAL",
        )
        db.add(plan)
        db.flush()

        # Add a single two-template combined assignment
        db.add(
            AnnualRotationAssignment(
                plan_id=plan.id,
                person_id=resident.id,
                block_number=8,
                rotation_name="[PSYCH + NF]",
                is_fixed=False,
            )
        )
        db.commit()

        # Publish via API
        resp = authed_client.post(
            f"/api/v1/annual-planner/plans/{plan.id}/publish",
        )
        assert resp.status_code == 200

        ba = (
            db.query(BlockAssignment)
            .filter(
                BlockAssignment.academic_year == 2026,
                BlockAssignment.resident_id == resident.id,
                BlockAssignment.block_number == 8,
            )
            .first()
        )
        assert ba is not None
        assert ba.rotation_template_id == psych.id
        assert ba.secondary_rotation_template_id == nf_am.id
