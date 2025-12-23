"""
Unit tests for controller layer.

These tests mock the service layer to test controllers in isolation,
focusing on request/response handling and HTTP exception conversion.
"""

from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.controllers.absence_controller import AbsenceController
from app.controllers.auth_controller import AuthController
from app.controllers.person_controller import PersonController
from app.schemas.absence import AbsenceCreate, AbsenceUpdate
from app.schemas.auth import UserCreate
from app.schemas.person import PersonCreate, PersonUpdate

# ============================================================================
# PersonController Tests
# ============================================================================


class TestPersonControllerListPeople:
    """Tests for PersonController.list_people()"""

    def test_list_people_returns_response(self):
        """Should return PersonListResponse with items and total."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.list_people = MagicMock(
            return_value={"items": [], "total": 0}
        )

        result = controller.list_people()

        assert result.items == []
        assert result.total == 0
        controller.service.list_people.assert_called_once_with(
            type=None, pgy_level=None
        )

    def test_list_people_with_filters(self):
        """Should pass filters to service."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.list_people = MagicMock(
            return_value={"items": [], "total": 0}
        )

        controller.list_people(type="resident", pgy_level=2)

        controller.service.list_people.assert_called_once_with(
            type="resident", pgy_level=2
        )

    def test_list_people_with_data(self):
        """Should return items from service."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        mock_items = [{"id": str(uuid4()), "name": "Dr. Test", "type": "resident"}]
        controller.service.list_people = MagicMock(
            return_value={"items": mock_items, "total": 1}
        )

        result = controller.list_people()

        assert result.total == 1
        assert len(result.items) == 1


class TestPersonControllerListResidents:
    """Tests for PersonController.list_residents()"""

    def test_list_residents_calls_service(self):
        """Should call service.list_residents."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.list_residents = MagicMock(
            return_value={"items": [], "total": 0}
        )

        result = controller.list_residents()

        controller.service.list_residents.assert_called_once_with(pgy_level=None)
        assert result.total == 0

    def test_list_residents_with_pgy_filter(self):
        """Should pass pgy_level filter to service."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.list_residents = MagicMock(
            return_value={"items": [], "total": 0}
        )

        controller.list_residents(pgy_level=3)

        controller.service.list_residents.assert_called_once_with(pgy_level=3)


class TestPersonControllerListFaculty:
    """Tests for PersonController.list_faculty()"""

    def test_list_faculty_calls_service(self):
        """Should call service.list_faculty."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.list_faculty = MagicMock(
            return_value={"items": [], "total": 0}
        )

        result = controller.list_faculty()

        controller.service.list_faculty.assert_called_once_with(specialty=None)
        assert result.total == 0

    def test_list_faculty_with_specialty_filter(self):
        """Should pass specialty filter to service."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.list_faculty = MagicMock(
            return_value={"items": [], "total": 0}
        )

        controller.list_faculty(specialty="Cardiology")

        controller.service.list_faculty.assert_called_once_with(specialty="Cardiology")


class TestPersonControllerGetPerson:
    """Tests for PersonController.get_person()"""

    def test_get_person_success(self):
        """Should return person when found."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        person_id = uuid4()
        mock_person = {"id": str(person_id), "name": "Dr. Test", "type": "resident"}
        controller.service.get_person = MagicMock(return_value=mock_person)

        result = controller.get_person(person_id)

        assert result == mock_person
        controller.service.get_person.assert_called_once_with(person_id)

    def test_get_person_not_found_raises_404(self):
        """Should raise HTTPException 404 when person not found."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.get_person = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_person(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestPersonControllerCreatePerson:
    """Tests for PersonController.create_person()"""

    def test_create_person_success(self):
        """Should return created person."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        mock_person = {"id": str(uuid4()), "name": "Dr. New", "type": "resident"}
        controller.service.create_person = MagicMock(
            return_value={"person": mock_person, "error": None}
        )

        person_in = PersonCreate(
            name="Dr. New",
            type="resident",
            pgy_level=1,
        )
        result = controller.create_person(person_in)

        assert result == mock_person

    def test_create_person_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.create_person = MagicMock(
            return_value={"person": None, "error": "PGY level required for residents"}
        )

        person_in = PersonCreate(
            name="Dr. Bad",
            type="resident",
            pgy_level=None,
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_person(person_in)

        assert exc_info.value.status_code == 400
        assert "PGY" in exc_info.value.detail


class TestPersonControllerUpdatePerson:
    """Tests for PersonController.update_person()"""

    def test_update_person_success(self):
        """Should return updated person."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        person_id = uuid4()
        mock_person = {"id": str(person_id), "name": "Dr. Updated", "type": "resident"}
        controller.service.update_person = MagicMock(
            return_value={"person": mock_person, "error": None}
        )

        person_in = PersonUpdate(name="Dr. Updated")
        result = controller.update_person(person_id, person_in)

        assert result == mock_person
        controller.service.update_person.assert_called_once()

    def test_update_person_not_found_raises_404(self):
        """Should raise HTTPException 404 when person not found."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.update_person = MagicMock(
            return_value={"person": None, "error": "Person not found"}
        )

        person_in = PersonUpdate(name="Ghost")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_person(uuid4(), person_in)

        assert exc_info.value.status_code == 404


class TestPersonControllerDeletePerson:
    """Tests for PersonController.delete_person()"""

    def test_delete_person_success(self):
        """Should return None on successful delete."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.delete_person = MagicMock(return_value={"error": None})

        result = controller.delete_person(uuid4())

        assert result is None

    def test_delete_person_not_found_raises_404(self):
        """Should raise HTTPException 404 when person not found."""
        mock_db = MagicMock()
        controller = PersonController(mock_db)
        controller.service.delete_person = MagicMock(
            return_value={"error": "Person not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_person(uuid4())

        assert exc_info.value.status_code == 404


# ============================================================================
# AuthController Tests
# ============================================================================


class TestAuthControllerLogin:
    """Tests for AuthController.login()"""

    def test_login_success(self):
        """Should return Token on successful authentication."""
        mock_db = MagicMock()
        controller = AuthController(mock_db)
        controller.service.authenticate = MagicMock(
            return_value={
                "access_token": "test_token",
                "token_type": "bearer",
                "error": None,
            }
        )

        result = controller.login("testuser", "password123")

        assert result.access_token == "test_token"
        assert result.token_type == "bearer"
        controller.service.authenticate.assert_called_once_with(
            "testuser", "password123"
        )

    def test_login_invalid_credentials_raises_401(self):
        """Should raise HTTPException 401 on invalid credentials."""
        mock_db = MagicMock()
        controller = AuthController(mock_db)
        controller.service.authenticate = MagicMock(
            return_value={"error": "Invalid credentials"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.login("baduser", "wrongpassword")

        assert exc_info.value.status_code == 401
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


class TestAuthControllerRegisterUser:
    """Tests for AuthController.register_user()"""

    def test_register_user_success(self):
        """Should return created user."""
        mock_db = MagicMock()
        controller = AuthController(mock_db)
        mock_user = {
            "id": str(uuid4()),
            "username": "newuser",
            "email": "new@test.com",
            "role": "viewer",
        }
        controller.service.register_user = MagicMock(
            return_value={"user": mock_user, "error": None}
        )

        user_in = UserCreate(
            username="newuser",
            email="new@test.com",
            password="password123",
            role="viewer",
        )
        result = controller.register_user(user_in)

        assert result == mock_user

    def test_register_user_admin_required_raises_403(self):
        """Should raise HTTPException 403 when admin access required."""
        mock_db = MagicMock()
        controller = AuthController(mock_db)
        controller.service.register_user = MagicMock(
            return_value={"user": None, "error": "Admin access required"}
        )

        user_in = UserCreate(
            username="newuser",
            email="new@test.com",
            password="password123",
            role="admin",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.register_user(user_in)

        assert exc_info.value.status_code == 403

    def test_register_user_validation_error_raises_400(self):
        """Should raise HTTPException 400 on validation error."""
        mock_db = MagicMock()
        controller = AuthController(mock_db)
        controller.service.register_user = MagicMock(
            return_value={"user": None, "error": "Username already exists"}
        )

        user_in = UserCreate(
            username="existing",
            email="existing@test.com",
            password="password123",
            role="viewer",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.register_user(user_in)

        assert exc_info.value.status_code == 400


class TestAuthControllerListUsers:
    """Tests for AuthController.list_users()"""

    def test_list_users_returns_list(self):
        """Should return list of users from service."""
        mock_db = MagicMock()
        controller = AuthController(mock_db)
        mock_users = [
            {"id": str(uuid4()), "username": "user1"},
            {"id": str(uuid4()), "username": "user2"},
        ]
        controller.service.list_users = MagicMock(return_value=mock_users)

        result = controller.list_users()

        assert result == mock_users
        controller.service.list_users.assert_called_once()


# ============================================================================
# AbsenceController Tests
# ============================================================================


class TestAbsenceControllerListAbsences:
    """Tests for AbsenceController.list_absences()"""

    def test_list_absences_no_filters(self):
        """Should call service with no filters."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        mock_result = {"items": [], "total": 0}
        controller.service.list_absences = MagicMock(return_value=mock_result)

        result = controller.list_absences()

        assert result == mock_result
        controller.service.list_absences.assert_called_once_with(
            start_date=None,
            end_date=None,
            person_id=None,
            absence_type=None,
        )

    def test_list_absences_with_filters(self):
        """Should pass filters to service."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        controller.service.list_absences = MagicMock(
            return_value={"items": [], "total": 0}
        )

        start = date.today()
        end = date.today() + timedelta(days=7)
        person_id = uuid4()

        controller.list_absences(
            start_date=start,
            end_date=end,
            person_id=person_id,
            absence_type="vacation",
        )

        controller.service.list_absences.assert_called_once_with(
            start_date=start,
            end_date=end,
            person_id=person_id,
            absence_type="vacation",
        )


class TestAbsenceControllerGetAbsence:
    """Tests for AbsenceController.get_absence()"""

    def test_get_absence_success(self):
        """Should return absence when found."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        absence_id = uuid4()
        mock_absence = {"id": str(absence_id), "absence_type": "vacation"}
        controller.service.get_absence = MagicMock(return_value=mock_absence)

        result = controller.get_absence(absence_id)

        assert result == mock_absence
        controller.service.get_absence.assert_called_once_with(absence_id)

    def test_get_absence_not_found_raises_404(self):
        """Should raise HTTPException 404 when absence not found."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        controller.service.get_absence = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_absence(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestAbsenceControllerCreateAbsence:
    """Tests for AbsenceController.create_absence()"""

    def test_create_absence_success(self):
        """Should return created absence."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        mock_absence = {
            "id": str(uuid4()),
            "absence_type": "vacation",
        }
        controller.service.create_absence = MagicMock(
            return_value={"absence": mock_absence, "error": None}
        )

        absence_in = AbsenceCreate(
            person_id=uuid4(),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            absence_type="vacation",
        )
        result = controller.create_absence(absence_in)

        assert result == mock_absence

    def test_create_absence_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        controller.service.create_absence = MagicMock(
            return_value={"absence": None, "error": "Person not found"}
        )

        absence_in = AbsenceCreate(
            person_id=uuid4(),
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            absence_type="vacation",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_absence(absence_in)

        assert exc_info.value.status_code == 400


class TestAbsenceControllerUpdateAbsence:
    """Tests for AbsenceController.update_absence()"""

    def test_update_absence_success(self):
        """Should return updated absence."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        absence_id = uuid4()
        mock_absence = {"id": str(absence_id), "absence_type": "medical"}
        controller.service.update_absence = MagicMock(
            return_value={"absence": mock_absence, "error": None}
        )

        absence_in = AbsenceUpdate(absence_type="medical")
        result = controller.update_absence(absence_id, absence_in)

        assert result == mock_absence

    def test_update_absence_not_found_raises_404(self):
        """Should raise HTTPException 404 when absence not found."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        controller.service.update_absence = MagicMock(
            return_value={"absence": None, "error": "Absence not found"}
        )

        absence_in = AbsenceUpdate(notes="Updated notes")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_absence(uuid4(), absence_in)

        assert exc_info.value.status_code == 404


class TestAbsenceControllerDeleteAbsence:
    """Tests for AbsenceController.delete_absence()"""

    def test_delete_absence_success(self):
        """Should return None on successful delete."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        controller.service.delete_absence = MagicMock(return_value={"error": None})

        result = controller.delete_absence(uuid4())

        assert result is None

    def test_delete_absence_not_found_raises_404(self):
        """Should raise HTTPException 404 when absence not found."""
        mock_db = MagicMock()
        controller = AbsenceController(mock_db)
        controller.service.delete_absence = MagicMock(
            return_value={"error": "Absence not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_absence(uuid4())

        assert exc_info.value.status_code == 404


# ============================================================================
# AssignmentController Tests
# ============================================================================

from app.controllers.assignment_controller import AssignmentController
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate


class TestAssignmentControllerListAssignments:
    """Tests for AssignmentController.list_assignments()"""

    def test_list_assignments_no_filters(self):
        """Should call service with no filters."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        mock_result = {"items": [], "total": 0}
        controller.service.list_assignments = MagicMock(return_value=mock_result)

        result = controller.list_assignments()

        assert result == mock_result
        controller.service.list_assignments.assert_called_once_with(
            start_date=None,
            end_date=None,
            person_id=None,
            role=None,
        )

    def test_list_assignments_with_filters(self):
        """Should pass filters to service."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        controller.service.list_assignments = MagicMock(
            return_value={"items": [], "total": 0}
        )

        start = date.today()
        end = date.today() + timedelta(days=7)
        person_id = uuid4()

        controller.list_assignments(
            start_date=start,
            end_date=end,
            person_id=person_id,
            role="primary",
        )

        controller.service.list_assignments.assert_called_once_with(
            start_date=start,
            end_date=end,
            person_id=person_id,
            role="primary",
        )


class TestAssignmentControllerGetAssignment:
    """Tests for AssignmentController.get_assignment()"""

    def test_get_assignment_success(self):
        """Should return assignment when found."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        assignment_id = uuid4()
        mock_assignment = {"id": str(assignment_id), "role": "primary"}
        controller.service.get_assignment = MagicMock(return_value=mock_assignment)

        result = controller.get_assignment(assignment_id)

        assert result == mock_assignment
        controller.service.get_assignment.assert_called_once_with(assignment_id)

    def test_get_assignment_not_found_raises_404(self):
        """Should raise HTTPException 404 when assignment not found."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        controller.service.get_assignment = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_assignment(uuid4())

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()


class TestAssignmentControllerCreateAssignment:
    """Tests for AssignmentController.create_assignment()"""

    def test_create_assignment_success(self):
        """Should return created assignment with ACGME warnings."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)

        # Mock assignment object with __dict__
        mock_assignment = MagicMock()
        mock_assignment.__dict__ = {
            "id": uuid4(),
            "block_id": uuid4(),
            "person_id": uuid4(),
            "role": "primary",
        }

        controller.service.create_assignment = MagicMock(
            return_value={
                "assignment": mock_assignment,
                "acgme_warnings": [],
                "is_compliant": True,
                "error": None,
            }
        )

        mock_user = MagicMock()
        mock_user.username = "testuser"

        assignment_in = AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            role="primary",
        )
        result = controller.create_assignment(assignment_in, mock_user)

        assert result.is_compliant is True
        assert result.acgme_warnings == []

    def test_create_assignment_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        controller.service.create_assignment = MagicMock(
            return_value={"assignment": None, "error": "Block not found"}
        )

        mock_user = MagicMock()
        mock_user.username = "testuser"

        assignment_in = AssignmentCreate(
            block_id=uuid4(),
            person_id=uuid4(),
            role="primary",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_assignment(assignment_in, mock_user)

        assert exc_info.value.status_code == 400


class TestAssignmentControllerUpdateAssignment:
    """Tests for AssignmentController.update_assignment()"""

    def test_update_assignment_success(self):
        """Should return updated assignment with warnings."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        assignment_id = uuid4()

        mock_assignment = MagicMock()
        mock_assignment.__dict__ = {
            "id": assignment_id,
            "role": "backup",
        }

        controller.service.update_assignment = MagicMock(
            return_value={
                "assignment": mock_assignment,
                "acgme_warnings": ["Warning: exceeds weekly limit"],
                "is_compliant": False,
                "error": None,
            }
        )

        assignment_in = AssignmentUpdate(role="backup")
        result = controller.update_assignment(assignment_id, assignment_in)

        assert result.is_compliant is False
        assert len(result.acgme_warnings) == 1

    def test_update_assignment_not_found_raises_404(self):
        """Should raise HTTPException 404 when assignment not found."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        controller.service.update_assignment = MagicMock(
            return_value={"assignment": None, "error": "Assignment not found"}
        )

        assignment_in = AssignmentUpdate(role="backup")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_assignment(uuid4(), assignment_in)

        assert exc_info.value.status_code == 404

    def test_update_assignment_conflict_raises_409(self):
        """Should raise HTTPException 409 on concurrent modification."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        controller.service.update_assignment = MagicMock(
            return_value={
                "assignment": None,
                "error": "Assignment was modified by another user",
            }
        )

        assignment_in = AssignmentUpdate(role="backup")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_assignment(uuid4(), assignment_in)

        assert exc_info.value.status_code == 409


class TestAssignmentControllerDeleteAssignment:
    """Tests for AssignmentController.delete_assignment()"""

    def test_delete_assignment_success(self):
        """Should return None on successful delete."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        controller.service.delete_assignment = MagicMock(return_value={"error": None})

        result = controller.delete_assignment(uuid4())

        assert result is None

    def test_delete_assignment_not_found_raises_404(self):
        """Should raise HTTPException 404 when assignment not found."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        controller.service.delete_assignment = MagicMock(
            return_value={"error": "Assignment not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_assignment(uuid4())

        assert exc_info.value.status_code == 404


class TestAssignmentControllerDeleteBulk:
    """Tests for AssignmentController.delete_assignments_bulk()"""

    def test_delete_assignments_bulk(self):
        """Should call service with date range."""
        mock_db = MagicMock()
        controller = AssignmentController(mock_db)
        mock_result = {"deleted_count": 10}
        controller.service.delete_assignments_bulk = MagicMock(return_value=mock_result)

        start = date.today()
        end = date.today() + timedelta(days=7)

        result = controller.delete_assignments_bulk(start, end)

        assert result == mock_result
        controller.service.delete_assignments_bulk.assert_called_once_with(start, end)


# ============================================================================
# ProcedureController Tests
# ============================================================================

from app.controllers.procedure_controller import ProcedureController
from app.schemas.procedure import ProcedureCreate, ProcedureUpdate


class TestProcedureControllerListProcedures:
    """Tests for ProcedureController.list_procedures()"""

    def test_list_procedures_no_filters(self):
        """Should return ProcedureListResponse."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.list_procedures = MagicMock(
            return_value={"items": [], "total": 0}
        )

        result = controller.list_procedures()

        assert result.items == []
        assert result.total == 0

    def test_list_procedures_with_filters(self):
        """Should pass filters to service."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.list_procedures = MagicMock(
            return_value={"items": [], "total": 0}
        )

        controller.list_procedures(
            specialty="Orthopedics",
            category="Major",
            is_active=True,
            complexity_level="high",
        )

        controller.service.list_procedures.assert_called_once_with(
            specialty="Orthopedics",
            category="Major",
            is_active=True,
            complexity_level="high",
        )


class TestProcedureControllerGetProcedure:
    """Tests for ProcedureController.get_procedure()"""

    def test_get_procedure_success(self):
        """Should return procedure when found."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        procedure_id = uuid4()
        mock_procedure = {"id": str(procedure_id), "name": "ACL Repair"}
        controller.service.get_procedure = MagicMock(return_value=mock_procedure)

        result = controller.get_procedure(procedure_id)

        assert result == mock_procedure

    def test_get_procedure_not_found_raises_404(self):
        """Should raise HTTPException 404 when procedure not found."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.get_procedure = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_procedure(uuid4())

        assert exc_info.value.status_code == 404


class TestProcedureControllerGetByName:
    """Tests for ProcedureController.get_procedure_by_name()"""

    def test_get_procedure_by_name_success(self):
        """Should return procedure when found by name."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        mock_procedure = {"id": str(uuid4()), "name": "ACL Repair"}
        controller.service.get_procedure_by_name = MagicMock(
            return_value=mock_procedure
        )

        result = controller.get_procedure_by_name("ACL Repair")

        assert result == mock_procedure

    def test_get_procedure_by_name_not_found_raises_404(self):
        """Should raise HTTPException 404 when procedure not found."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.get_procedure_by_name = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_procedure_by_name("Unknown Procedure")

        assert exc_info.value.status_code == 404


class TestProcedureControllerCreateProcedure:
    """Tests for ProcedureController.create_procedure()"""

    def test_create_procedure_success(self):
        """Should return created procedure."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        mock_procedure = {"id": str(uuid4()), "name": "New Procedure"}
        controller.service.create_procedure = MagicMock(
            return_value={"procedure": mock_procedure, "error": None}
        )

        procedure_in = ProcedureCreate(
            name="New Procedure",
            description="Test procedure",
            category="Minor",
            specialty="General",
        )
        result = controller.create_procedure(procedure_in)

        assert result == mock_procedure

    def test_create_procedure_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.create_procedure = MagicMock(
            return_value={"procedure": None, "error": "Procedure already exists"}
        )

        procedure_in = ProcedureCreate(
            name="Duplicate",
            description="Test",
            category="Minor",
            specialty="General",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_procedure(procedure_in)

        assert exc_info.value.status_code == 400


class TestProcedureControllerUpdateProcedure:
    """Tests for ProcedureController.update_procedure()"""

    def test_update_procedure_success(self):
        """Should return updated procedure."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        procedure_id = uuid4()
        mock_procedure = {"id": str(procedure_id), "name": "Updated Procedure"}
        controller.service.update_procedure = MagicMock(
            return_value={"procedure": mock_procedure, "error": None}
        )

        procedure_in = ProcedureUpdate(name="Updated Procedure")
        result = controller.update_procedure(procedure_id, procedure_in)

        assert result == mock_procedure

    def test_update_procedure_not_found_raises_404(self):
        """Should raise HTTPException 404 when procedure not found."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.update_procedure = MagicMock(
            return_value={"procedure": None, "error": "Procedure not found"}
        )

        procedure_in = ProcedureUpdate(name="Ghost")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_procedure(uuid4(), procedure_in)

        assert exc_info.value.status_code == 404


class TestProcedureControllerDeleteProcedure:
    """Tests for ProcedureController.delete_procedure()"""

    def test_delete_procedure_success(self):
        """Should return None on successful delete."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.delete_procedure = MagicMock(return_value={"error": None})

        result = controller.delete_procedure(uuid4())

        assert result is None

    def test_delete_procedure_not_found_raises_404(self):
        """Should raise HTTPException 404 when procedure not found."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        controller.service.delete_procedure = MagicMock(
            return_value={"error": "Procedure not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_procedure(uuid4())

        assert exc_info.value.status_code == 404


class TestProcedureControllerHelpers:
    """Tests for ProcedureController helper methods."""

    def test_get_specialties(self):
        """Should return list of specialties."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        mock_specialties = ["Orthopedics", "Cardiology", "General"]
        controller.service.get_specialties = MagicMock(return_value=mock_specialties)

        result = controller.get_specialties()

        assert result == mock_specialties

    def test_get_categories(self):
        """Should return list of categories."""
        mock_db = MagicMock()
        controller = ProcedureController(mock_db)
        mock_categories = ["Major", "Minor", "Diagnostic"]
        controller.service.get_categories = MagicMock(return_value=mock_categories)

        result = controller.get_categories()

        assert result == mock_categories


# ============================================================================
# BlockController Tests
# ============================================================================

from app.controllers.block_controller import BlockController
from app.schemas.block import BlockCreate


class TestBlockControllerListBlocks:
    """Tests for BlockController.list_blocks()"""

    def test_list_blocks_no_filters(self):
        """Should return BlockListResponse."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        controller.service.list_blocks = MagicMock(
            return_value={"items": [], "total": 0}
        )

        result = controller.list_blocks()

        assert result.items == []
        assert result.total == 0

    def test_list_blocks_with_filters(self):
        """Should pass filters to service."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        controller.service.list_blocks = MagicMock(
            return_value={"items": [], "total": 0}
        )

        start = date.today()
        end = date.today() + timedelta(days=7)

        controller.list_blocks(
            start_date=start,
            end_date=end,
            block_number=1,
        )

        controller.service.list_blocks.assert_called_once_with(
            start_date=start,
            end_date=end,
            block_number=1,
        )


class TestBlockControllerGetBlock:
    """Tests for BlockController.get_block()"""

    def test_get_block_success(self):
        """Should return block when found."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        block_id = uuid4()
        mock_block = {"id": str(block_id), "time_of_day": "AM"}
        controller.service.get_block = MagicMock(return_value=mock_block)

        result = controller.get_block(block_id)

        assert result == mock_block

    def test_get_block_not_found_raises_404(self):
        """Should raise HTTPException 404 when block not found."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        controller.service.get_block = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_block(uuid4())

        assert exc_info.value.status_code == 404


class TestBlockControllerCreateBlock:
    """Tests for BlockController.create_block()"""

    def test_create_block_success(self):
        """Should return created block."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        mock_block = {
            "id": str(uuid4()),
            "date": str(date.today()),
            "time_of_day": "AM",
        }
        controller.service.create_block = MagicMock(
            return_value={"block": mock_block, "error": None}
        )

        block_in = BlockCreate(
            date=date.today(),
            time_of_day="AM",
        )
        result = controller.create_block(block_in)

        assert result == mock_block

    def test_create_block_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        controller.service.create_block = MagicMock(
            return_value={"block": None, "error": "Block already exists"}
        )

        block_in = BlockCreate(
            date=date.today(),
            time_of_day="AM",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_block(block_in)

        assert exc_info.value.status_code == 400


class TestBlockControllerGenerateBlocks:
    """Tests for BlockController.generate_blocks()"""

    def test_generate_blocks(self):
        """Should return generated blocks."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        mock_blocks = [{"id": str(uuid4()), "time_of_day": "AM"}]
        controller.service.generate_blocks = MagicMock(
            return_value={"items": mock_blocks, "total": 1}
        )

        start = date.today()
        end = date.today() + timedelta(days=7)

        result = controller.generate_blocks(start, end, base_block_number=1)

        assert result.total == 1
        controller.service.generate_blocks.assert_called_once_with(
            start_date=start,
            end_date=end,
            base_block_number=1,
        )


class TestBlockControllerDeleteBlock:
    """Tests for BlockController.delete_block()"""

    def test_delete_block_success(self):
        """Should return None on successful delete."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        controller.service.delete_block = MagicMock(return_value={"error": None})

        result = controller.delete_block(uuid4())

        assert result is None

    def test_delete_block_not_found_raises_404(self):
        """Should raise HTTPException 404 when block not found."""
        mock_db = MagicMock()
        controller = BlockController(mock_db)
        controller.service.delete_block = MagicMock(
            return_value={"error": "Block not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_block(uuid4())

        assert exc_info.value.status_code == 404


# ============================================================================
# CredentialController Tests
# ============================================================================

from app.controllers.credential_controller import CredentialController
from app.schemas.procedure_credential import CredentialCreate, CredentialUpdate


class TestCredentialControllerGetCredential:
    """Tests for CredentialController.get_credential()"""

    def test_get_credential_success(self):
        """Should return credential when found."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        credential_id = uuid4()
        mock_credential = {"id": str(credential_id), "status": "active"}
        controller.service.get_credential = MagicMock(return_value=mock_credential)

        result = controller.get_credential(credential_id)

        assert result == mock_credential

    def test_get_credential_not_found_raises_404(self):
        """Should raise HTTPException 404 when credential not found."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.get_credential = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_credential(uuid4())

        assert exc_info.value.status_code == 404


class TestCredentialControllerListCredentials:
    """Tests for CredentialController list methods."""

    def test_list_credentials_for_person(self):
        """Should return credentials for a person."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.list_credentials_for_person = MagicMock(
            return_value={"items": [], "total": 0}
        )

        person_id = uuid4()
        result = controller.list_credentials_for_person(person_id)

        assert result.total == 0
        controller.service.list_credentials_for_person.assert_called_once_with(
            person_id=person_id,
            status=None,
            include_expired=False,
        )

    def test_list_credentials_for_procedure(self):
        """Should return credentials for a procedure."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.list_credentials_for_procedure = MagicMock(
            return_value={"items": [], "total": 0}
        )

        procedure_id = uuid4()
        result = controller.list_credentials_for_procedure(procedure_id)

        assert result.total == 0


class TestCredentialControllerQualifiedFaculty:
    """Tests for CredentialController.get_qualified_faculty()"""

    def test_get_qualified_faculty_success(self):
        """Should return qualified faculty for procedure."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        procedure_id = uuid4()
        controller.service.list_qualified_faculty_for_procedure = MagicMock(
            return_value={
                "procedure_id": procedure_id,
                "procedure_name": "ACL Repair",
                "qualified_faculty": [],
                "total": 0,
            }
        )

        result = controller.get_qualified_faculty(procedure_id)

        assert result.procedure_name == "ACL Repair"
        assert result.total == 0

    def test_get_qualified_faculty_error_raises_404(self):
        """Should raise HTTPException 404 on error."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.list_qualified_faculty_for_procedure = MagicMock(
            return_value={"error": "Procedure not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.get_qualified_faculty(uuid4())

        assert exc_info.value.status_code == 404


class TestCredentialControllerCreateCredential:
    """Tests for CredentialController.create_credential()"""

    def test_create_credential_success(self):
        """Should return created credential."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        mock_credential = {"id": str(uuid4()), "status": "active"}
        controller.service.create_credential = MagicMock(
            return_value={"credential": mock_credential, "error": None}
        )

        credential_in = CredentialCreate(
            person_id=uuid4(),
            procedure_id=uuid4(),
            status="active",
            competency_level="advanced",
        )
        result = controller.create_credential(credential_in)

        assert result == mock_credential

    def test_create_credential_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.create_credential = MagicMock(
            return_value={"credential": None, "error": "Person not found"}
        )

        credential_in = CredentialCreate(
            person_id=uuid4(),
            procedure_id=uuid4(),
            status="active",
            competency_level="advanced",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_credential(credential_in)

        assert exc_info.value.status_code == 400


class TestCredentialControllerUpdateCredential:
    """Tests for CredentialController.update_credential()"""

    def test_update_credential_success(self):
        """Should return updated credential."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        credential_id = uuid4()
        mock_credential = {"id": str(credential_id), "status": "suspended"}
        controller.service.update_credential = MagicMock(
            return_value={"credential": mock_credential, "error": None}
        )

        credential_in = CredentialUpdate(status="suspended")
        result = controller.update_credential(credential_id, credential_in)

        assert result == mock_credential

    def test_update_credential_not_found_raises_404(self):
        """Should raise HTTPException 404 when credential not found."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.update_credential = MagicMock(
            return_value={"credential": None, "error": "Credential not found"}
        )

        credential_in = CredentialUpdate(status="suspended")

        with pytest.raises(HTTPException) as exc_info:
            controller.update_credential(uuid4(), credential_in)

        assert exc_info.value.status_code == 404


class TestCredentialControllerStatusActions:
    """Tests for CredentialController status action methods."""

    def test_suspend_credential_success(self):
        """Should return suspended credential."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        mock_credential = {"id": str(uuid4()), "status": "suspended"}
        controller.service.suspend_credential = MagicMock(
            return_value={"credential": mock_credential, "error": None}
        )

        result = controller.suspend_credential(uuid4(), notes="Under review")

        assert result == mock_credential

    def test_suspend_credential_not_found_raises_404(self):
        """Should raise HTTPException 404 when credential not found."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.suspend_credential = MagicMock(
            return_value={"credential": None, "error": "Credential not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.suspend_credential(uuid4())

        assert exc_info.value.status_code == 404

    def test_activate_credential_success(self):
        """Should return activated credential."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        mock_credential = {"id": str(uuid4()), "status": "active"}
        controller.service.activate_credential = MagicMock(
            return_value={"credential": mock_credential, "error": None}
        )

        result = controller.activate_credential(uuid4())

        assert result == mock_credential

    def test_verify_credential_success(self):
        """Should return verified credential."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        mock_credential = {"id": str(uuid4()), "status": "active"}
        controller.service.verify_credential = MagicMock(
            return_value={"credential": mock_credential, "error": None}
        )

        result = controller.verify_credential(uuid4())

        assert result == mock_credential


class TestCredentialControllerExpiring:
    """Tests for CredentialController.list_expiring_credentials()"""

    def test_list_expiring_credentials(self):
        """Should return expiring credentials."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.list_expiring_credentials = MagicMock(
            return_value={"items": [], "total": 0}
        )

        result = controller.list_expiring_credentials(days=30)

        assert result.total == 0
        controller.service.list_expiring_credentials.assert_called_once_with(days=30)


class TestCredentialControllerFacultySummary:
    """Tests for CredentialController.get_faculty_summary()"""

    def test_get_faculty_summary_success(self):
        """Should return faculty credential summary."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        person_id = uuid4()
        controller.service.get_faculty_credential_summary = MagicMock(
            return_value={
                "person_id": person_id,
                "person_name": "Dr. Test",
                "total_credentials": 5,
                "active_credentials": 4,
                "expiring_soon": 1,
                "procedures": [],
            }
        )

        result = controller.get_faculty_summary(person_id)

        assert result.person_name == "Dr. Test"
        assert result.total_credentials == 5

    def test_get_faculty_summary_not_found_raises_404(self):
        """Should raise HTTPException 404 when person not found."""
        mock_db = MagicMock()
        controller = CredentialController(mock_db)
        controller.service.get_faculty_credential_summary = MagicMock(
            return_value={"error": "Person not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.get_faculty_summary(uuid4())

        assert exc_info.value.status_code == 404


# ============================================================================
# CertificationController Tests
# ============================================================================

from app.controllers.certification_controller import CertificationController
from app.schemas.certification import (
    CertificationTypeCreate,
    PersonCertificationCreate,
)


class TestCertificationControllerTypes:
    """Tests for CertificationController certification type methods."""

    def test_list_certification_types(self):
        """Should return certification types."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.list_certification_types = MagicMock(
            return_value={"items": [], "total": 0}
        )

        result = controller.list_certification_types(active_only=True)

        assert result.total == 0

    def test_get_certification_type_success(self):
        """Should return certification type when found."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        cert_type_id = uuid4()
        mock_cert_type = {"id": str(cert_type_id), "name": "BLS"}
        controller.service.get_certification_type = MagicMock(
            return_value=mock_cert_type
        )

        result = controller.get_certification_type(cert_type_id)

        assert result == mock_cert_type

    def test_get_certification_type_not_found_raises_404(self):
        """Should raise HTTPException 404 when type not found."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.get_certification_type = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_certification_type(uuid4())

        assert exc_info.value.status_code == 404

    def test_create_certification_type_success(self):
        """Should return created certification type."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        mock_cert_type = {"id": str(uuid4()), "name": "ACLS"}
        controller.service.create_certification_type = MagicMock(
            return_value={"certification_type": mock_cert_type, "error": None}
        )

        cert_type_in = CertificationTypeCreate(
            name="ACLS",
            full_name="Advanced Cardiac Life Support",
        )
        result = controller.create_certification_type(cert_type_in)

        assert result == mock_cert_type

    def test_create_certification_type_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.create_certification_type = MagicMock(
            return_value={"certification_type": None, "error": "Name already exists"}
        )

        cert_type_in = CertificationTypeCreate(
            name="BLS",
            full_name="Basic Life Support",
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_certification_type(cert_type_in)

        assert exc_info.value.status_code == 400


class TestCertificationControllerPersonCerts:
    """Tests for CertificationController person certification methods."""

    def test_list_certifications_for_person(self):
        """Should return certifications for a person."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.list_certifications_for_person = MagicMock(
            return_value={"items": [], "total": 0}
        )

        person_id = uuid4()
        result = controller.list_certifications_for_person(person_id)

        assert result.total == 0

    def test_get_person_certification_success(self):
        """Should return person certification when found."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        cert_id = uuid4()
        mock_cert = {"id": str(cert_id), "status": "active"}
        controller.service.get_person_certification = MagicMock(return_value=mock_cert)

        result = controller.get_person_certification(cert_id)

        assert result == mock_cert

    def test_get_person_certification_not_found_raises_404(self):
        """Should raise HTTPException 404 when certification not found."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.get_person_certification = MagicMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            controller.get_person_certification(uuid4())

        assert exc_info.value.status_code == 404

    def test_create_person_certification_success(self):
        """Should return created certification."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        mock_cert = {"id": str(uuid4()), "status": "active"}
        controller.service.create_person_certification = MagicMock(
            return_value={"certification": mock_cert, "error": None}
        )

        cert_in = PersonCertificationCreate(
            person_id=uuid4(),
            certification_type_id=uuid4(),
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
        )
        result = controller.create_person_certification(cert_in)

        assert result == mock_cert

    def test_create_person_certification_error_raises_400(self):
        """Should raise HTTPException 400 on service error."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.create_person_certification = MagicMock(
            return_value={"certification": None, "error": "Person not found"}
        )

        cert_in = PersonCertificationCreate(
            person_id=uuid4(),
            certification_type_id=uuid4(),
            issued_date=date.today(),
            expiration_date=date.today() + timedelta(days=365),
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.create_person_certification(cert_in)

        assert exc_info.value.status_code == 400

    def test_renew_certification_success(self):
        """Should return renewed certification."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        mock_cert = {"id": str(uuid4()), "status": "active"}
        controller.service.renew_certification = MagicMock(
            return_value={"certification": mock_cert, "error": None}
        )

        result = controller.renew_certification(
            cert_id=uuid4(),
            new_issued_date=date.today(),
            new_expiration_date=date.today() + timedelta(days=730),
        )

        assert result == mock_cert

    def test_renew_certification_not_found_raises_404(self):
        """Should raise HTTPException 404 when certification not found."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.renew_certification = MagicMock(
            return_value={"certification": None, "error": "Certification not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.renew_certification(
                cert_id=uuid4(),
                new_issued_date=date.today(),
                new_expiration_date=date.today() + timedelta(days=730),
            )

        assert exc_info.value.status_code == 404

    def test_delete_person_certification_success(self):
        """Should return None on successful delete."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.delete_person_certification = MagicMock(
            return_value={"error": None}
        )

        result = controller.delete_person_certification(uuid4())

        assert result is None

    def test_delete_person_certification_not_found_raises_404(self):
        """Should raise HTTPException 404 when certification not found."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.delete_person_certification = MagicMock(
            return_value={"error": "Certification not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.delete_person_certification(uuid4())

        assert exc_info.value.status_code == 404


class TestCertificationControllerCompliance:
    """Tests for CertificationController compliance methods."""

    def test_get_compliance_summary(self):
        """Should return compliance summary."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        mock_summary = {
            "total_people": 50,
            "fully_compliant": 45,
            "non_compliant": 5,
            "compliance_rate": 0.90,
            "expiring_soon": 10,
            "expired": 3,
        }
        controller.service.get_compliance_summary = MagicMock(return_value=mock_summary)

        result = controller.get_compliance_summary()

        assert result.total_people == 50
        assert result.compliance_rate == 0.90

    def test_get_person_compliance_success(self):
        """Should return person compliance status."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)

        mock_person = MagicMock()
        mock_person.id = uuid4()
        mock_person.name = "Dr. Test"
        mock_person.type = "resident"
        mock_person.email = "test@test.com"

        controller.service.get_person_compliance = MagicMock(
            return_value={
                "person": mock_person,
                "total_required": 3,
                "total_current": 2,
                "expired": 0,
                "expiring_soon": 1,
                "missing": [],
                "is_compliant": False,
            }
        )

        result = controller.get_person_compliance(uuid4())

        assert result.is_compliant is False
        assert result.total_required == 3

    def test_get_person_compliance_not_found_raises_404(self):
        """Should raise HTTPException 404 when person not found."""
        mock_db = MagicMock()
        controller = CertificationController(mock_db)
        controller.service.get_person_compliance = MagicMock(
            return_value={"error": "Person not found"}
        )

        with pytest.raises(HTTPException) as exc_info:
            controller.get_person_compliance(uuid4())

        assert exc_info.value.status_code == 404
