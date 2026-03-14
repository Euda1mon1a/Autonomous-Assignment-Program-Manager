"""Person service for business logic."""

import logging
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.person import Person
from app.models.person_academic_year import PersonAcademicYear
from app.repositories.person import PersonRepository

logger = logging.getLogger(__name__)


class PersonService:
    """Service for person business logic."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.person_repo = PersonRepository(db)

    def get_person(self, person_id: UUID) -> Person | None:
        """
        Get a single person by ID.

        For performance-critical cases where assignments are needed,
        use get_person_with_assignments() instead.

        Args:
            person_id: The UUID of the person to retrieve.

        Returns:
            The Person object if found, None otherwise.
        """
        return self.person_repo.get_by_id(person_id)

    def get_person_with_assignments(self, person_id: UUID) -> Person | None:
        """
        Get a single person by ID with eager-loaded assignments.

        N+1 Optimization: Uses selectinload to eagerly fetch all assignments
        and their related entities (block, rotation_template) in a batch query,
        preventing N+1 queries when accessing person.assignments.

        Args:
            person_id: The UUID of the person to retrieve.

        Returns:
            The Person object with assignments loaded if found, None otherwise.
        """
        return (
            self.db.query(Person)
            .options(
                selectinload(Person.assignments).selectinload("block"),
                selectinload(Person.assignments).selectinload("rotation_template"),
            )
            .filter(Person.id == person_id)
            .first()
        )

    def list_people(
        self,
        type: str | None = None,
        pgy_level: int | None = None,
        include_assignments: bool = False,
    ) -> dict:
        """
        List people with optional filters.

        N+1 Optimization: When include_assignments=True, uses selectinload to
        eagerly fetch assignments and their relationships in batch queries.

        Args:
            type: Filter by person type ('resident' or 'faculty').
            pgy_level: Filter by PGY level (1-4 for residents).
            include_assignments: If True, eager load assignments to prevent N+1.

        Returns:
            A dict with 'items' (list of Person objects) and 'total' (count).
        """
        if include_assignments:
            query = self.db.query(Person).options(
                selectinload(Person.assignments).selectinload("block"),
                selectinload(Person.assignments).selectinload("rotation_template"),
            )

            if type:
                query = query.filter(Person.type == type)
            if pgy_level is not None:
                query = query.filter(Person.pgy_level == pgy_level)

            people = query.order_by(Person.name).all()
        else:
            people = self.person_repo.list_with_filters(type=type, pgy_level=pgy_level)

        return {"items": people, "total": len(people)}

    def list_residents(
        self,
        pgy_level: int | None = None,
        include_assignments: bool = False,
    ) -> dict:
        """
        List all residents with optional PGY filter.

        N+1 Optimization: When include_assignments=True, uses selectinload to
        eagerly fetch assignments, preventing N+1 queries.

        Args:
            pgy_level: Filter by PGY level (1-4).
            include_assignments: If True, eager load assignments to prevent N+1.

        Returns:
            A dict with 'items' (list of resident Person objects) and 'total' (count).
        """
        if include_assignments:
            query = (
                self.db.query(Person)
                .options(
                    selectinload(Person.assignments).selectinload("block"),
                    selectinload(Person.assignments).selectinload("rotation_template"),
                )
                .filter(Person.type == "resident")
            )

            if pgy_level is not None:
                query = query.filter(Person.pgy_level == pgy_level)

            residents = query.order_by(Person.pgy_level, Person.name).all()
        else:
            residents = self.person_repo.list_residents(pgy_level=pgy_level)

        return {"items": residents, "total": len(residents)}

    def list_faculty(
        self,
        specialty: str | None = None,
        include_assignments: bool = False,
    ) -> dict:
        """
        List all faculty with optional specialty filter.

        N+1 Optimization: When include_assignments=True, uses selectinload to
        eagerly fetch assignments, preventing N+1 queries.

        Args:
            specialty: Filter by faculty specialty (e.g., 'cardiology').
            include_assignments: If True, eager load assignments to prevent N+1.

        Returns:
            A dict with 'items' (list of faculty Person objects) and 'total' (count).
        """
        if include_assignments:
            query = (
                self.db.query(Person)
                .options(
                    selectinload(Person.assignments).selectinload("block"),
                    selectinload(Person.assignments).selectinload("rotation_template"),
                )
                .filter(Person.type == "faculty")
            )

            if specialty:
                query = query.filter(Person.specialties.contains([specialty]))

            faculty = query.order_by(Person.name).all()
        else:
            faculty = self.person_repo.list_faculty(specialty=specialty)

        return {"items": faculty, "total": len(faculty)}

    def create_person(
        self,
        name: str,
        type: str,
        email: str | None = None,
        pgy_level: int | None = None,
        target_clinical_blocks: int | None = None,
        specialties: list[str] | None = None,
        performs_procedures: bool = False,
        faculty_role: str | None = None,
        primary_duty: str | None = None,
        min_clinic_halfdays_per_week: int | None = None,
        max_clinic_halfdays_per_week: int | None = None,
    ) -> dict:
        """
        Create a new person (resident or faculty).

        Validates that residents have a PGY level specified.

        Args:
            name: The person's full name.
            type: Person type, either 'resident' or 'faculty'.
            email: Optional email address.
            pgy_level: PGY level (1-4), required for residents.
            target_clinical_blocks: Optional target number of clinical blocks.
            specialties: Optional list of specialty strings (for faculty).
            performs_procedures: Whether the person performs procedures.
            faculty_role: Optional faculty role (pd, apd, oic, etc.).
            primary_duty: Optional primary duty description.
            min_clinic_halfdays_per_week: Optional min clinic half-days/week.
            max_clinic_halfdays_per_week: Optional max clinic half-days/week.

        Returns:
            A dict with 'person' (Person object or None) and 'error' (string or None).
        """
        # Validate resident requirements
        if type == "resident" and pgy_level is None:
            return {
                "person": None,
                "error": "PGY level required for residents",
            }

        person_data: dict[str, Any] = {
            "name": name,
            "type": type,
        }
        if email:
            person_data["email"] = email
        if pgy_level is not None:
            person_data["pgy_level"] = pgy_level
        if target_clinical_blocks is not None:
            person_data["target_clinical_blocks"] = target_clinical_blocks
        if specialties:
            person_data["specialties"] = specialties
        if performs_procedures:
            person_data["performs_procedures"] = performs_procedures
        if faculty_role is not None:
            person_data["faculty_role"] = (
                faculty_role.value if hasattr(faculty_role, "value") else faculty_role
            )
        if primary_duty is not None:
            person_data["primary_duty"] = primary_duty
        if min_clinic_halfdays_per_week is not None:
            person_data["min_clinic_halfdays_per_week"] = min_clinic_halfdays_per_week
        if max_clinic_halfdays_per_week is not None:
            person_data["max_clinic_halfdays_per_week"] = max_clinic_halfdays_per_week

        try:
            person = self.person_repo.create(person_data)
            self.person_repo.commit()
            self.person_repo.refresh(person)
            return {"person": person, "error": None}
        except IntegrityError:
            self.db.rollback()
            return {
                "person": None,
                "error": "Person with this email already exists",
            }

    def update_person(self, person_id: UUID, update_data: dict) -> dict:
        """
        Update a person's information.

        Args:
            person_id: The UUID of the person to update.
            update_data: Dict of fields to update on the person.

        Returns:
            A dict with 'person' (updated Person or None) and 'error' (string or None).
        """
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"person": None, "error": "Person not found"}

        person = self.person_repo.update(person, update_data)
        self.person_repo.commit()
        self.person_repo.refresh(person)

        return {"person": person, "error": None}

    def rollover_academic_year(self, current_academic_year: int) -> dict:
        """Rollover residents to the next academic year.

        For each non-graduated PersonAcademicYear record in the given AY:
        - PGY-3 residents are marked as graduated (no new record created)
        - PGY-1 and PGY-2 residents get a new record with PGY+1 for AY+1
        - Person.pgy_level is updated for backward compatibility
        - Call counts reset naturally (new AY record starts at 0)

        Args:
            current_academic_year: The academic year to rollover from.

        Returns:
            Dict with 'advanced' (count), 'graduated' (count), 'error' (str|None).
        """
        next_ay = current_academic_year + 1

        # Check for existing records in the next AY to prevent double-rollover
        existing_next = (
            self.db.query(PersonAcademicYear)
            .filter(PersonAcademicYear.academic_year == next_ay)
            .first()
        )
        if existing_next:
            return {
                "advanced": 0,
                "graduated": 0,
                "error": f"AY {next_ay} records already exist. Rollover may have already been performed.",
            }

        current_records = (
            self.db.query(PersonAcademicYear)
            .filter(
                PersonAcademicYear.academic_year == current_academic_year,
                ~PersonAcademicYear.is_graduated,
            )
            .all()
        )

        if not current_records:
            return {
                "advanced": 0,
                "graduated": 0,
                "error": f"No active PersonAcademicYear records found for AY {current_academic_year}",
            }

        advanced = 0
        graduated = 0

        # Pre-fetch all persons to avoid N+1
        person_ids = [r.person_id for r in current_records]
        persons = self.db.query(Person).filter(Person.id.in_(person_ids)).all()
        person_map = {p.id: p for p in persons}

        for record in current_records:
            person = person_map.get(record.person_id)
            if not person:
                logger.warning("Person %s not found during rollover", record.person_id)
                continue

            if record.pgy_level and record.pgy_level >= 3:
                # Graduate PGY-3
                record.is_graduated = True
                graduated += 1
                logger.info(
                    "Graduated person_id=%s from AY %d",
                    record.person_id,
                    current_academic_year,
                )
            else:
                # Advance PGY level
                new_pgy = (record.pgy_level or 0) + 1
                new_record = PersonAcademicYear(
                    person_id=record.person_id,
                    academic_year=next_ay,
                    pgy_level=new_pgy,
                )
                self.db.add(new_record)

                # Update legacy Person.pgy_level for backward compat
                if person:
                    person.pgy_level = new_pgy

                advanced += 1

        self.db.flush()
        self.db.commit()

        logger.info(
            "AY rollover %d→%d: %d advanced, %d graduated",
            current_academic_year,
            next_ay,
            advanced,
            graduated,
        )

        return {"advanced": advanced, "graduated": graduated, "error": None}

    def delete_person(self, person_id: UUID) -> dict:
        """
        Delete a person from the system.

        Args:
            person_id: The UUID of the person to delete.

        Returns:
            A dict with 'success' (boolean) and 'error' (string or None).
        """
        person = self.person_repo.get_by_id(person_id)
        if not person:
            return {"success": False, "error": "Person not found"}

        self.person_repo.delete(person)
        self.person_repo.commit()
        return {"success": True, "error": None}

        # =========================================================================
        # Batch Operations
        # =========================================================================

    def batch_create(self, people_data: list[dict], dry_run: bool = False) -> dict:
        """
        Atomically create multiple people.

        This operation is all-or-nothing: if any validation fails,
        the entire batch is rolled back.

        Args:
            people_data: List of person data dicts matching PersonCreate schema.
            dry_run: If True, validate only without creating.

        Returns:
            Dict with operation results including created_ids:
            - operation_type: "create"
            - total: Number of requested creations
            - succeeded: Number of successful creations
            - failed: Number of failed creations
            - results: Per-person results
            - dry_run: Whether this was a dry run
            - created_ids: List of created person UUIDs (empty if dry_run)

        Raises:
            ValueError: If validation fails (atomic rollback)
        """
        results = []
        people_to_create = []
        created_ids = []

        # Check for duplicate emails within the batch
        seen_emails: set[str] = set()
        for idx, person in enumerate(people_data):
            email = (person.get("email") or "").strip().lower()
            if not email:
                continue
            if email in seen_emails:
                results.append(
                    {
                        "index": idx,
                        "person_id": None,
                        "success": False,
                        "error": f"Duplicate email in batch: {email}",
                    }
                )
            seen_emails.add(email)

            # Phase 1: Validate all people
        for idx, person_data in enumerate(people_data):
            try:
                # Validate resident requirements
                if person_data.get("type") == "resident" and not person_data.get(
                    "pgy_level"
                ):
                    results.append(
                        {
                            "index": idx,
                            "person_id": None,
                            "success": False,
                            "error": "PGY level required for residents",
                        }
                    )
                    continue

                    # Check for duplicate email in database
                email = person_data.get("email")
                if email:
                    existing = (
                        self.db.query(Person).filter(Person.email == email).first()
                    )
                    if existing:
                        results.append(
                            {
                                "index": idx,
                                "person_id": None,
                                "success": False,
                                "error": f"Email already exists: {email}",
                            }
                        )
                        continue

                people_to_create.append((idx, person_data))
                results.append(
                    {
                        "index": idx,
                        "person_id": None,
                        "success": True,
                        "error": None,
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "index": idx,
                        "person_id": None,
                        "success": False,
                        "error": "Operation failed",
                    }
                )

                # Check for failures
        failures = [r for r in results if not r["success"]]
        if failures:
            return {
                "operation_type": "create",
                "total": len(people_data),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
                "created_ids": [],
            }

            # Phase 2: Create people (if not dry run)
        if not dry_run:
            for idx, person_data in people_to_create:
                person = self.person_repo.create(person_data)
                self.db.flush()
                created_ids.append(person.id)
                # Update result with created ID
                results[idx]["person_id"] = person.id

            self.person_repo.commit()

        return {
            "operation_type": "create",
            "total": len(people_data),
            "succeeded": len(people_to_create),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
            "created_ids": created_ids,
        }

    def batch_update(self, updates: list[dict], dry_run: bool = False) -> dict:
        """
        Atomically update multiple people.

        This operation is all-or-nothing: if any person doesn't exist or
        validation fails, the entire batch is rolled back.

        Args:
            updates: List of dicts, each with:
                - person_id: UUID of person to update
                - updates: Dict of field updates
            dry_run: If True, validate only without updating.

        Returns:
            Dict with operation results:
            - operation_type: "update"
            - total: Number of requested updates
            - succeeded: Number of successful updates
            - failed: Number of failed updates
            - results: Per-person results
            - dry_run: Whether this was a dry run

        Raises:
            ValueError: If any person not found or validation fails
        """
        results = []
        people_to_update = []

        # Phase 1: Validate all people exist and collect updates
        for idx, update_item in enumerate(updates):
            person_id = update_item.get("person_id")
            update_data = update_item.get("updates", {})

            person = self.person_repo.get_by_id(person_id)  # type: ignore[arg-type]
            if not person:
                results.append(
                    {
                        "index": idx,
                        "person_id": person_id,
                        "success": False,
                        "error": f"Person not found: {person_id}",
                    }
                )
            else:
                people_to_update.append((idx, person_id, person, update_data))
                results.append(
                    {
                        "index": idx,
                        "person_id": person_id,
                        "success": True,
                        "error": None,
                    }
                )

                # Check for failures
        failures = [r for r in results if not r["success"]]
        if failures:
            return {
                "operation_type": "update",
                "total": len(updates),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

            # Phase 2: Apply updates (if not dry run)
        if not dry_run:
            for idx, person_id, person, update_data in people_to_update:
                for field, value in update_data.items():
                    setattr(person, field, value)
            self.db.flush()
            self.person_repo.commit()

        return {
            "operation_type": "update",
            "total": len(updates),
            "succeeded": len(people_to_update),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }

    def batch_delete(self, person_ids: list[UUID], dry_run: bool = False) -> dict:
        """
        Atomically delete multiple people.

        This operation is all-or-nothing: if any person doesn't exist or
        cannot be deleted, the entire batch is rolled back.

        Args:
            person_ids: List of person UUIDs to delete.
            dry_run: If True, validate only without deleting.

        Returns:
            Dict with operation results:
            - operation_type: "delete"
            - total: Number of requested deletions
            - succeeded: Number of successful deletions
            - failed: Number of failed deletions
            - results: Per-person results
            - dry_run: Whether this was a dry run

        Raises:
            ValueError: If any person not found (atomic rollback)
        """
        results = []
        people_to_delete = []

        # Phase 1: Validate all people exist
        for idx, person_id in enumerate(person_ids):
            person = self.person_repo.get_by_id(person_id)
            if not person:
                results.append(
                    {
                        "index": idx,
                        "person_id": person_id,
                        "success": False,
                        "error": f"Person not found: {person_id}",
                    }
                )
            else:
                people_to_delete.append((idx, person_id, person))
                results.append(
                    {
                        "index": idx,
                        "person_id": person_id,
                        "success": True,
                        "error": None,
                    }
                )

                # Check for failures
        failures = [r for r in results if not r["success"]]
        if failures:
            return {
                "operation_type": "delete",
                "total": len(person_ids),
                "succeeded": 0,
                "failed": len(failures),
                "results": results,
                "dry_run": dry_run,
            }

            # Phase 2: Execute deletions (if not dry run)
        if not dry_run:
            for idx, person_id, person in people_to_delete:
                self.person_repo.delete(person)
            self.db.flush()
            self.person_repo.commit()

        return {
            "operation_type": "delete",
            "total": len(person_ids),
            "succeeded": len(people_to_delete),
            "failed": 0,
            "results": results,
            "dry_run": dry_run,
        }
