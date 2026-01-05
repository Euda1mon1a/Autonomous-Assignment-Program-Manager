"""Batch operations for person service.

This module contains batch operation methods that should be added to PersonService class.
"""

from uuid import UUID
from app.models.person import Person


# Add these methods to the PersonService class in person_service.py

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
    emails_in_batch = [
        p.get("email", "").strip().lower() for p in people_data if p.get("email")
    ]
    seen_emails = set()
    for idx, email in enumerate(emails_in_batch):
        if email and email in seen_emails:
            results.append(
                {
                    "index": idx,
                    "person_id": None,
                    "success": False,
                    "error": f"Duplicate email in batch: {email}",
                }
            )
        if email:
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
                    "error": str(e),
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
