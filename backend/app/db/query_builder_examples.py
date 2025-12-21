"""
Example usage patterns for the QueryBuilder.

This file demonstrates common usage patterns and best practices
for using the dynamic query builder.
"""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.db.query_builder import QueryBuilder, create_query_builder
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


def example_basic_filtering(db: Session):
    """Example: Basic filtering with equality."""
    # Get all residents
    residents = QueryBuilder(Person, db).filter_by(type="resident").all()

    # Get PGY-2 residents
    pgy2_residents = (
        QueryBuilder(Person, db).filter_by(type="resident", pgy_level=2).all()
    )

    # Get faculty who perform procedures
    procedure_faculty = (
        QueryBuilder(Person, db)
        .filter_by(type="faculty", performs_procedures=True)
        .all()
    )

    return residents, pgy2_residents, procedure_faculty


def example_comparison_filters(db: Session):
    """Example: Comparison operators (>, >=, <, <=, !=)."""
    # Get senior residents (PGY 2 or higher)
    senior_residents = (
        QueryBuilder(Person, db).filter_by(type="resident").filter_gte("pgy_level", 2).all()
    )

    # Get residents who are NOT PGY-1
    non_pgy1 = QueryBuilder(Person, db).filter_ne("pgy_level", 1).all()

    return senior_residents, non_pgy1


def example_pattern_matching(db: Session):
    """Example: Pattern matching with LIKE/ILIKE."""
    # Find people with "Smith" in their name (case-insensitive)
    smiths = QueryBuilder(Person, db).filter_like("name", "%Smith%", case_sensitive=False).all()

    # Find emails from specific domain
    hospital_emails = (
        QueryBuilder(Person, db).filter_like("email", "%@hospital.org").all()
    )

    return smiths, hospital_emails


def example_in_filters(db: Session):
    """Example: IN and NOT IN filters."""
    # Get residents at specific PGY levels
    pgy_1_or_3 = (
        QueryBuilder(Person, db).filter_by(type="resident").filter_in("pgy_level", [1, 3]).all()
    )

    # Exclude specific PGY levels
    not_pgy_1 = (
        QueryBuilder(Person, db)
        .filter_by(type="resident")
        .filter_not_in("pgy_level", [1])
        .all()
    )

    return pgy_1_or_3, not_pgy_1


def example_null_checks(db: Session):
    """Example: NULL checking."""
    # Find faculty (they have NULL pgy_level)
    faculty_via_null = QueryBuilder(Person, db).filter_is_null("pgy_level").all()

    # Find people with email set
    has_email = QueryBuilder(Person, db).filter_is_not_null("email").all()

    return faculty_via_null, has_email


def example_date_ranges(db: Session):
    """Example: Date range filtering."""
    today = date.today()
    next_week = today + timedelta(days=7)
    next_month = today + timedelta(days=30)

    # Get blocks for next week
    next_week_blocks = (
        QueryBuilder(Block, db)
        .filter_date_range("date", start_date=today, end_date=next_week)
        .all()
    )

    # Get all future blocks
    future_blocks = QueryBuilder(Block, db).filter_date_range("date", start_date=today).all()

    return next_week_blocks, future_blocks


def example_sorting(db: Session):
    """Example: Sorting results."""
    # Sort residents by PGY level (ascending)
    sorted_asc = (
        QueryBuilder(Person, db)
        .filter_by(type="resident")
        .order_by("pgy_level", "name")
        .all()
    )

    # Sort by name descending
    sorted_desc = QueryBuilder(Person, db).order_by_desc("name").all()

    return sorted_asc, sorted_desc


def example_pagination(db: Session):
    """Example: Paginated results."""
    # Get page 1 (first 10 residents)
    page1 = (
        QueryBuilder(Person, db)
        .filter_by(type="resident")
        .order_by("name")
        .paginate(page=1, page_size=10)
    )

    # Access pagination metadata
    total_count = page1["total"]
    total_pages = page1["total_pages"]
    items = page1["items"]

    return page1


def example_limit_offset(db: Session):
    """Example: Manual limit and offset."""
    # Get 5 residents, skipping the first 2
    results = (
        QueryBuilder(Person, db)
        .filter_by(type="resident")
        .order_by("pgy_level")
        .offset(2)
        .limit(5)
        .all()
    )

    return results


def example_joins(db: Session):
    """Example: Joining related entities."""
    # Get assignments with eagerly loaded person and block
    assignments_with_relations = (
        QueryBuilder(Assignment, db)
        .join_related("person")
        .join_related("block")
        .join_related("rotation_template")
        .all()
    )

    # No N+1 queries - all relationships are loaded
    for assignment in assignments_with_relations:
        person_name = assignment.person.name  # No additional query
        block_date = assignment.block.date  # No additional query

    return assignments_with_relations


def example_filter_by_joined(db: Session):
    """Example: Filtering on joined relationships."""
    # Get assignments for a specific person by name
    assignments_for_smith = (
        QueryBuilder(Assignment, db)
        .filter_by_joined("person", name="Dr. Smith")
        .all()
    )

    # Get assignments for residents only
    resident_assignments = (
        QueryBuilder(Assignment, db)
        .filter_by_joined("person", type="resident")
        .all()
    )

    return assignments_for_smith, resident_assignments


def example_aggregations(db: Session):
    """Example: Aggregation functions."""
    # Count residents
    resident_count = QueryBuilder(Person, db).filter_by(type="resident").count()

    # Average PGY level
    avg_pgy = (
        QueryBuilder(Person, db)
        .filter_by(type="resident")
        .aggregate("avg", "pgy_level")
    )

    # Min and max PGY levels
    min_pgy = QueryBuilder(Person, db).aggregate("min", "pgy_level")
    max_pgy = QueryBuilder(Person, db).aggregate("max", "pgy_level")

    return resident_count, avg_pgy, min_pgy, max_pgy


def example_exists_check(db: Session):
    """Example: Checking if records exist."""
    # Check if any residents exist
    has_residents = QueryBuilder(Person, db).filter_by(type="resident").exists()

    # Check if specific person exists
    person_exists = (
        QueryBuilder(Person, db).filter_by(email="john.doe@hospital.org").exists()
    )

    return has_residents, person_exists


def example_subqueries(db: Session):
    """Example: Using subqueries."""
    # Find people who have assignments
    subquery = (
        QueryBuilder(Assignment, db).select_columns(Assignment.person_id).distinct().as_subquery()
    )

    people_with_assignments = QueryBuilder(Person, db).filter_in("id", subquery).all()

    return people_with_assignments


def example_or_conditions(db: Session):
    """Example: OR conditions."""
    # Get residents at PGY 1 OR PGY 3
    pgy_1_or_3 = (
        QueryBuilder(Person, db)
        .filter_by(type="resident")
        .filter_or(Person.pgy_level == 1, Person.pgy_level == 3)
        .all()
    )

    return pgy_1_or_3


def example_array_contains(db: Session):
    """Example: PostgreSQL array contains."""
    # Find faculty with Sports Medicine specialty
    sports_med_faculty = (
        QueryBuilder(Person, db)
        .filter_by(type="faculty")
        .filter_contains("specialties", "Sports Medicine")
        .all()
    )

    return sports_med_faculty


def example_complex_query(db: Session):
    """Example: Complex multi-criteria query."""
    today = date.today()
    next_week = today + timedelta(days=7)

    # Find assignments for senior residents (PGY >= 2) in the next week
    # Eagerly load relationships to avoid N+1 queries
    results = (
        QueryBuilder(Assignment, db)
        .join_related("person")
        .join_related("block")
        .filter_by_joined("person", type="resident")
        .filter(Person.pgy_level >= 2)  # Raw filter for joined table
        .filter_date_range("date", start_date=today, end_date=next_week)  # Won't work - need block.date
        .order_by("block_id")
        .paginate(page=1, page_size=20)
    )

    return results


def example_bulk_operations(db: Session):
    """
    Example: Bulk update and delete.

    WARNING: Use with caution - these operations bypass SQLAlchemy events.
    """
    # Bulk update: Promote all PGY-1 residents to PGY-2
    # NOTE: In production, this should be in a transaction with proper validation
    updated_count = (
        QueryBuilder(Person, db)
        .filter_by(type="resident", pgy_level=1)
        .update({"pgy_level": 2})
    )
    db.commit()

    # Bulk delete: Remove test accounts
    # NOTE: Use with extreme caution
    deleted_count = (
        QueryBuilder(Person, db).filter_like("email", "%@test.org").delete()
    )
    db.commit()

    return updated_count, deleted_count


def example_clone_for_variations(db: Session):
    """Example: Clone query builder to create variations."""
    # Base query: all residents
    base_query = QueryBuilder(Person, db).filter_by(type="resident").order_by("name")

    # Create variations without repeating the base filters
    pgy1_residents = base_query.clone().filter_by(pgy_level=1).all()
    pgy2_residents = base_query.clone().filter_by(pgy_level=2).all()
    pgy3_residents = base_query.clone().filter_by(pgy_level=3).all()

    return pgy1_residents, pgy2_residents, pgy3_residents


def example_factory_function(db: Session):
    """Example: Using the factory function."""
    # Alternative way to create query builder
    qb = create_query_builder(Person, db)
    residents = qb.filter_by(type="resident").all()

    return residents


def example_terminal_methods(db: Session):
    """Example: Different ways to execute queries."""
    # Get all results
    all_residents = QueryBuilder(Person, db).filter_by(type="resident").all()

    # Get first result (or None)
    first_resident = QueryBuilder(Person, db).filter_by(type="resident").first()

    # Get one result (raises error if 0 or multiple)
    try:
        one_result = (
            QueryBuilder(Person, db)
            .filter_by(type="resident", pgy_level=2)
            .one()
        )
    except Exception:
        one_result = None

    # Get one or none (raises error only if multiple)
    one_or_none = (
        QueryBuilder(Person, db)
        .filter_by(type="resident", pgy_level=2)
        .one_or_none()
    )

    # Just count without fetching
    count = QueryBuilder(Person, db).filter_by(type="resident").count()

    # Check existence
    exists = QueryBuilder(Person, db).filter_by(type="resident").exists()

    return all_residents, first_resident, one_result, one_or_none, count, exists


def example_in_service_layer(db: Session, person_id: str):
    """
    Example: Using QueryBuilder in a service method.

    This demonstrates the recommended pattern for using QueryBuilder
    in the service layer.
    """
    from uuid import UUID

    # Simple query with type safety
    person = (
        QueryBuilder(Person, db)
        .filter_by(id=UUID(person_id))
        .join_related("assignments")  # Eager load to prevent N+1
        .first()
    )

    if not person:
        return None

    # Access relationships without additional queries
    assignment_count = len(person.assignments)

    return {
        "person": person,
        "assignment_count": assignment_count,
    }


def example_replacing_repository_pattern(db: Session):
    """
    Example: Using QueryBuilder as an alternative to repositories.

    QueryBuilder can replace simple repository methods while providing
    more flexibility and composability.
    """
    # Instead of: person_repo.list_residents(pgy_level=2)
    pgy2_residents = (
        QueryBuilder(Person, db)
        .filter_by(type="resident", pgy_level=2)
        .order_by("name")
        .all()
    )

    # Instead of: person_repo.get_available_for_block(...)
    # More complex logic can be composed fluently
    available_faculty = (
        QueryBuilder(Person, db)
        .filter_by(type="faculty")
        .filter_is_not_null("email")
        .filter_not_in("id", [])  # Would pass list of unavailable IDs
        .order_by("name")
        .all()
    )

    return pgy2_residents, available_faculty
