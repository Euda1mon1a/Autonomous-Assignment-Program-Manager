"""Tests for ProcedureController."""

import pytest
from uuid import uuid4
from fastapi import HTTPException

from app.controllers.procedure_controller import ProcedureController
from app.models.procedure import Procedure
from app.schemas.procedure import ProcedureCreate, ProcedureUpdate


class TestProcedureController:
    """Test suite for ProcedureController."""

    @pytest.fixture
    def setup_data(self, db):
        """Create common test data."""
        procedures = []
        procedure_data = [
            {
                "name": "Mastectomy",
                "description": "Breast surgery procedure",
                "category": "surgical",
                "specialty": "Surgery",
                "complexity_level": "advanced",
                "min_pgy_level": 3,
            },
            {
                "name": "IUD Placement",
                "description": "Contraceptive device placement",
                "category": "office",
                "specialty": "OB/GYN",
                "complexity_level": "standard",
                "min_pgy_level": 1,
            },
            {
                "name": "Botox Injection",
                "description": "Cosmetic injection procedure",
                "category": "office",
                "specialty": "Dermatology",
                "complexity_level": "basic",
                "min_pgy_level": 1,
            },
            {
                "name": "Colposcopy",
                "description": "Cervical examination procedure",
                "category": "office",
                "specialty": "OB/GYN",
                "complexity_level": "standard",
                "min_pgy_level": 2,
            },
        ]

        for data in procedure_data:
            procedure = Procedure(
                id=uuid4(),
                name=data["name"],
                description=data["description"],
                category=data["category"],
                specialty=data["specialty"],
                supervision_ratio=1,
                requires_certification=True,
                complexity_level=data["complexity_level"],
                min_pgy_level=data["min_pgy_level"],
                is_active=True,
            )
            db.add(procedure)
            procedures.append(procedure)

        db.commit()

        return {"procedures": procedures}

    # ========================================================================
    # List Procedures Tests
    # ========================================================================

    def test_list_procedures_no_filters(self, db, setup_data):
        """Test listing all procedures without filters."""
        controller = ProcedureController(db)
        result = controller.list_procedures()

        assert result.total >= 4
        assert len(result.items) >= 4

    def test_list_procedures_filter_by_specialty(self, db, setup_data):
        """Test filtering procedures by specialty."""
        controller = ProcedureController(db)
        result = controller.list_procedures(specialty="OB/GYN")

        assert result.total >= 2
        assert all(p.specialty == "OB/GYN" for p in result.items)

    def test_list_procedures_filter_by_category(self, db, setup_data):
        """Test filtering procedures by category."""
        controller = ProcedureController(db)
        result = controller.list_procedures(category="office")

        assert result.total >= 3
        assert all(p.category == "office" for p in result.items)

    def test_list_procedures_filter_by_complexity(self, db, setup_data):
        """Test filtering procedures by complexity level."""
        controller = ProcedureController(db)
        result = controller.list_procedures(complexity_level="advanced")

        assert result.total >= 1
        assert all(p.complexity_level == "advanced" for p in result.items)

    def test_list_procedures_filter_active_only(self, db, setup_data):
        """Test filtering to active procedures only."""
        # Create inactive procedure
        inactive = Procedure(
            id=uuid4(),
            name="Inactive Procedure",
            category="office",
            is_active=False,
        )
        db.add(inactive)
        db.commit()

        controller = ProcedureController(db)
        result = controller.list_procedures(is_active=True)

        assert all(p.is_active for p in result.items)

    def test_list_procedures_multiple_filters(self, db, setup_data):
        """Test combining multiple filters."""
        controller = ProcedureController(db)
        result = controller.list_procedures(
            specialty="OB/GYN",
            category="office",
        )

        assert result.total >= 2
        assert all(
            p.specialty == "OB/GYN" and p.category == "office" for p in result.items
        )

    # ========================================================================
    # Get Procedure Tests
    # ========================================================================

    def test_get_procedure_success(self, db, setup_data):
        """Test getting a procedure by ID."""
        procedure = setup_data["procedures"][0]

        controller = ProcedureController(db)
        result = controller.get_procedure(procedure.id)

        assert result is not None
        assert result.id == procedure.id
        assert result.name == procedure.name

    def test_get_procedure_not_found(self, db):
        """Test getting a non-existent procedure raises 404."""
        controller = ProcedureController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_procedure(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    def test_get_procedure_by_name_success(self, db, setup_data):
        """Test getting a procedure by name."""
        controller = ProcedureController(db)
        result = controller.get_procedure_by_name("Mastectomy")

        assert result is not None
        assert result.name == "Mastectomy"

    def test_get_procedure_by_name_not_found(self, db):
        """Test getting non-existent procedure by name raises 404."""
        controller = ProcedureController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_procedure_by_name("NonexistentProcedure")

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Create Procedure Tests
    # ========================================================================

    def test_create_procedure_success(self, db):
        """Test creating a new procedure."""
        controller = ProcedureController(db)

        procedure_data = ProcedureCreate(
            name="Vasectomy",
            description="Male sterilization procedure",
            category="surgical",
            specialty="Urology",
            supervision_ratio=1,
            requires_certification=True,
            complexity_level="standard",
            min_pgy_level=2,
        )

        result = controller.create_procedure(procedure_data)

        assert result is not None
        assert result.name == "Vasectomy"
        assert result.specialty == "Urology"
        assert result.complexity_level == "standard"

    def test_create_procedure_minimal_data(self, db):
        """Test creating procedure with minimal required fields."""
        controller = ProcedureController(db)

        procedure_data = ProcedureCreate(
            name="Simple Procedure",
            category="office",
        )

        result = controller.create_procedure(procedure_data)

        assert result is not None
        assert result.name == "Simple Procedure"
        assert result.is_active is True  # Default

    def test_create_procedure_duplicate_name(self, db, setup_data):
        """Test creating procedure with duplicate name fails."""
        controller = ProcedureController(db)

        procedure_data = ProcedureCreate(
            name="Mastectomy",  # Already exists
            category="surgical",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_procedure(procedure_data)

        assert exc_info.value.status_code == 400

    # ========================================================================
    # Update Procedure Tests
    # ========================================================================

    def test_update_procedure_success(self, db, setup_data):
        """Test updating a procedure."""
        procedure = setup_data["procedures"][0]

        controller = ProcedureController(db)

        update_data = ProcedureUpdate(
            description="Updated description",
            min_pgy_level=4,
        )
        result = controller.update_procedure(procedure.id, update_data)

        assert result.description == "Updated description"
        assert result.min_pgy_level == 4

    def test_update_procedure_change_complexity(self, db, setup_data):
        """Test changing procedure complexity level."""
        procedure = setup_data["procedures"][2]  # Botox - basic

        controller = ProcedureController(db)

        update_data = ProcedureUpdate(complexity_level="standard")
        result = controller.update_procedure(procedure.id, update_data)

        assert result.complexity_level == "standard"

    def test_update_procedure_not_found(self, db):
        """Test updating non-existent procedure raises 404."""
        controller = ProcedureController(db)

        update_data = ProcedureUpdate(description="New description")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_procedure(uuid4(), update_data)

        assert exc_info.value.status_code == 404

    def test_update_procedure_deactivate(self, db, setup_data):
        """Test deactivating a procedure."""
        procedure = setup_data["procedures"][0]

        controller = ProcedureController(db)

        update_data = ProcedureUpdate(is_active=False)
        result = controller.update_procedure(procedure.id, update_data)

        assert result.is_active is False

    # ========================================================================
    # Delete Procedure Tests
    # ========================================================================

    def test_delete_procedure_success(self, db):
        """Test deleting a procedure."""
        procedure = Procedure(
            id=uuid4(),
            name="ToDelete",
            category="office",
        )
        db.add(procedure)
        db.commit()
        procedure_id = procedure.id

        controller = ProcedureController(db)
        controller.delete_procedure(procedure_id)

        # Verify deletion
        deleted = db.query(Procedure).filter(Procedure.id == procedure_id).first()
        assert deleted is None

    def test_delete_procedure_not_found(self, db):
        """Test deleting non-existent procedure raises 404."""
        controller = ProcedureController(db)

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_procedure(uuid4())

        assert exc_info.value.status_code == 404

    # ========================================================================
    # Get Specialties/Categories Tests
    # ========================================================================

    def test_get_specialties(self, db, setup_data):
        """Test getting list of unique specialties."""
        controller = ProcedureController(db)
        result = controller.get_specialties()

        assert isinstance(result, list)
        assert "Surgery" in result
        assert "OB/GYN" in result
        assert "Dermatology" in result

    def test_get_categories(self, db, setup_data):
        """Test getting list of unique categories."""
        controller = ProcedureController(db)
        result = controller.get_categories()

        assert isinstance(result, list)
        assert "surgical" in result
        assert "office" in result

    def test_get_specialties_empty(self, db):
        """Test getting specialties when no procedures exist."""
        controller = ProcedureController(db)
        result = controller.get_specialties()

        assert isinstance(result, list)

    # ========================================================================
    # Integration Tests
    # ========================================================================

    def test_create_get_update_delete_workflow(self, db):
        """Test complete CRUD workflow for procedure."""
        controller = ProcedureController(db)

        # Create
        procedure_data = ProcedureCreate(
            name="Workflow Procedure",
            description="Test procedure for workflow",
            category="office",
            specialty="General",
            complexity_level="basic",
        )
        created = controller.create_procedure(procedure_data)
        procedure_id = created.id

        # Get by ID
        retrieved = controller.get_procedure(procedure_id)
        assert retrieved.name == "Workflow Procedure"

        # Get by name
        by_name = controller.get_procedure_by_name("Workflow Procedure")
        assert by_name.id == procedure_id

        # Update
        update_data = ProcedureUpdate(
            description="Updated workflow procedure",
            complexity_level="standard",
        )
        updated = controller.update_procedure(procedure_id, update_data)
        assert updated.description == "Updated workflow procedure"
        assert updated.complexity_level == "standard"

        # Delete
        controller.delete_procedure(procedure_id)

        # Verify deletion
        with pytest.raises(HTTPException):
            controller.get_procedure(procedure_id)

    def test_filter_chain(self, db, setup_data):
        """Test filtering procedures with various criteria."""
        controller = ProcedureController(db)

        # Start with all procedures
        all_procs = controller.list_procedures()
        all_count = all_procs.total

        # Filter by specialty
        specialty_filtered = controller.list_procedures(specialty="OB/GYN")
        assert specialty_filtered.total < all_count

        # Filter by specialty and category
        double_filtered = controller.list_procedures(
            specialty="OB/GYN", category="office"
        )
        assert double_filtered.total <= specialty_filtered.total

    def test_specialties_and_categories_update(self, db, setup_data):
        """Test that specialties and categories update when procedures change."""
        controller = ProcedureController(db)

        # Get initial specialties
        initial_specialties = controller.get_specialties()

        # Add new procedure with new specialty
        new_procedure = ProcedureCreate(
            name="New Specialty Procedure",
            category="office",
            specialty="Cardiology",
        )
        controller.create_procedure(new_procedure)

        # Check specialties now include new one
        updated_specialties = controller.get_specialties()
        assert "Cardiology" in updated_specialties
        assert len(updated_specialties) > len(initial_specialties)
