"""Tests for dynamic query builder."""

from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.orm import Session

from app.db.query_builder import (
    QueryBuilder,
    create_query_builder,
)
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person
from app.models.rotation_template import RotationTemplate


class TestQueryBuilderBasicFilters:
    """Test basic filtering operations."""

    def test_filter_by_single_field(self, db: Session, sample_residents: list[Person]):
        """Test simple equality filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident").all()

        assert len(result) == 3
        assert all(p.type == "resident" for p in result)

    def test_filter_by_multiple_fields(
        self, db: Session, sample_residents: list[Person]
    ):
        """Test multiple equality filters (AND)."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident", pgy_level=2).all()

        assert len(result) == 1
        assert result[0].pgy_level == 2

    def test_filter_ne(self, db: Session, sample_residents: list[Person]):
        """Test not-equal filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_ne("pgy_level", 1).all()

        assert all(p.pgy_level != 1 for p in result)

    def test_filter_gt(self, db: Session, sample_residents: list[Person]):
        """Test greater-than filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_gt("pgy_level", 1).all()

        assert all(p.pgy_level > 1 for p in result)
        assert len(result) == 2  # PGY 2 and 3

    def test_filter_gte(self, db: Session, sample_residents: list[Person]):
        """Test greater-than-or-equal filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_gte("pgy_level", 2).all()

        assert all(p.pgy_level >= 2 for p in result)
        assert len(result) == 2

    def test_filter_lt(self, db: Session, sample_residents: list[Person]):
        """Test less-than filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_lt("pgy_level", 3).all()

        assert all(p.pgy_level < 3 for p in result)
        assert len(result) == 2  # PGY 1 and 2

    def test_filter_lte(self, db: Session, sample_residents: list[Person]):
        """Test less-than-or-equal filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_lte("pgy_level", 2).all()

        assert all(p.pgy_level <= 2 for p in result)
        assert len(result) == 2

    def test_filter_in(self, db: Session, sample_residents: list[Person]):
        """Test IN filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_in("pgy_level", [1, 3]).all()

        assert len(result) == 2
        assert all(p.pgy_level in [1, 3] for p in result)

    def test_filter_not_in(self, db: Session, sample_residents: list[Person]):
        """Test NOT IN filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_not_in("pgy_level", [1]).all()

        assert all(p.pgy_level not in [1] for p in result)

    def test_filter_is_null(
        self, db: Session, sample_resident: Person, sample_faculty: Person
    ):
        """Test IS NULL filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_is_null("pgy_level").all()

        # Faculty should have NULL pgy_level
        assert len(result) >= 1
        assert all(p.pgy_level is None for p in result)

    def test_filter_is_not_null(self, db: Session, sample_resident: Person):
        """Test IS NOT NULL filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_is_not_null("pgy_level").all()

        assert all(p.pgy_level is not None for p in result)

    def test_filter_between(self, db: Session, sample_residents: list[Person]):
        """Test BETWEEN filter."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_between("pgy_level", 1, 2).all()

        assert all(1 <= p.pgy_level <= 2 for p in result)
        assert len(result) == 2

    def test_filter_invalid_column(self, db: Session):
        """Test that invalid column names raise errors."""
        qb = QueryBuilder(Person, db)

        with pytest.raises(ValueError, match="Invalid column"):
            qb.filter_by(invalid_column="value")

    def test_filter_like_case_sensitive(self, db: Session):
        """Test LIKE pattern matching (case-sensitive)."""
        # Create test data
        person1 = Person(id=uuid4(), name="Dr. Smith", type="faculty")
        person2 = Person(id=uuid4(), name="Dr. SMITH", type="faculty")
        person3 = Person(id=uuid4(), name="Dr. Jones", type="faculty")
        db.add_all([person1, person2, person3])
        db.commit()

        qb = QueryBuilder(Person, db)
        result = qb.filter_like("name", "%Smith%", case_sensitive=True).all()

        assert len(result) == 1
        assert result[0].name == "Dr. Smith"

    def test_filter_like_case_insensitive(self, db: Session):
        """Test ILIKE pattern matching (case-insensitive)."""
        # Create test data
        person1 = Person(id=uuid4(), name="Dr. Smith", type="faculty")
        person2 = Person(id=uuid4(), name="Dr. SMITH", type="faculty")
        person3 = Person(id=uuid4(), name="Dr. Jones", type="faculty")
        db.add_all([person1, person2, person3])
        db.commit()

        qb = QueryBuilder(Person, db)
        result = qb.filter_like("name", "%smith%", case_sensitive=False).all()

        assert len(result) == 2
        names = {p.name for p in result}
        assert "Dr. Smith" in names
        assert "Dr. SMITH" in names


class TestQueryBuilderOrFilters:
    """Test OR filtering operations."""

    def test_filter_or(self, db: Session, sample_residents: list[Person]):
        """Test OR conditions."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_or(
            Person.pgy_level == 1,
            Person.pgy_level == 3,
        ).all()

        assert len(result) == 2
        pgy_levels = {p.pgy_level for p in result}
        assert pgy_levels == {1, 3}

    def test_filter_and_or_combined(self, db: Session, sample_residents: list[Person]):
        """Test combining AND and OR filters."""
        qb = QueryBuilder(Person, db)
        result = (
            qb.filter_by(type="resident")
            .filter_or(Person.pgy_level == 1, Person.pgy_level == 3)
            .all()
        )

        assert all(p.type == "resident" for p in result)
        assert all(p.pgy_level in [1, 3] for p in result)


class TestQueryBuilderSorting:
    """Test sorting and ordering."""

    def test_order_by_asc(self, db: Session, sample_residents: list[Person]):
        """Test ascending order."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident").order_by("pgy_level").all()

        pgy_levels = [p.pgy_level for p in result]
        assert pgy_levels == sorted(pgy_levels)

    def test_order_by_desc(self, db: Session, sample_residents: list[Person]):
        """Test descending order."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident").order_by_desc("pgy_level").all()

        pgy_levels = [p.pgy_level for p in result]
        assert pgy_levels == sorted(pgy_levels, reverse=True)

    def test_order_by_multiple_fields(self, db: Session):
        """Test ordering by multiple fields."""
        # Create residents with same PGY but different names
        res1 = Person(id=uuid4(), name="Alice", type="resident", pgy_level=2)
        res2 = Person(id=uuid4(), name="Bob", type="resident", pgy_level=2)
        res3 = Person(id=uuid4(), name="Charlie", type="resident", pgy_level=1)
        db.add_all([res1, res2, res3])
        db.commit()

        qb = QueryBuilder(Person, db)
        result = qb.order_by("pgy_level", "name").all()

        # Should be sorted by pgy_level first, then name
        assert result[0].name == "Charlie"  # PGY 1
        assert result[1].name == "Alice"  # PGY 2, alphabetically first
        assert result[2].name == "Bob"  # PGY 2, alphabetically second


class TestQueryBuilderPagination:
    """Test pagination functionality."""

    def test_paginate_first_page(self, db: Session):
        """Test first page of pagination."""
        # Create 25 residents
        for i in range(25):
            person = Person(
                id=uuid4(),
                name=f"Resident {i}",
                type="resident",
                pgy_level=1 + (i % 3),
            )
            db.add(person)
        db.commit()

        qb = QueryBuilder(Person, db)
        result = (
            qb.filter_by(type="resident")
            .order_by("name")
            .paginate(page=1, page_size=10)
        )

        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total"] == 25
        assert result["total_pages"] == 3
        assert len(result["items"]) == 10

    def test_paginate_middle_page(self, db: Session):
        """Test middle page of pagination."""
        # Create 25 residents
        for i in range(25):
            person = Person(
                id=uuid4(),
                name=f"Resident {i:02d}",  # Zero-padded for sorting
                type="resident",
                pgy_level=1,
            )
            db.add(person)
        db.commit()

        qb = QueryBuilder(Person, db)
        result = (
            qb.filter_by(type="resident")
            .order_by("name")
            .paginate(page=2, page_size=10)
        )

        assert result["page"] == 2
        assert len(result["items"]) == 10
        # Should get items 10-19 (0-indexed: items 10-19)
        assert result["items"][0].name == "Resident 10"

    def test_paginate_last_page_partial(self, db: Session):
        """Test last page with partial results."""
        # Create 25 residents
        for i in range(25):
            person = Person(
                id=uuid4(),
                name=f"Resident {i}",
                type="resident",
                pgy_level=1,
            )
            db.add(person)
        db.commit()

        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident").paginate(page=3, page_size=10)

        assert result["page"] == 3
        assert len(result["items"]) == 5  # Only 5 items on last page

    def test_limit_offset(self, db: Session, sample_residents: list[Person]):
        """Test limit and offset."""
        qb = QueryBuilder(Person, db)
        result = (
            qb.filter_by(type="resident").order_by("pgy_level").limit(2).offset(1).all()
        )

        assert len(result) == 2
        # Should skip first resident (PGY 1) and get PGY 2 and 3
        pgy_levels = [p.pgy_level for p in result]
        assert pgy_levels == [2, 3]


class TestQueryBuilderJoins:
    """Test join and relationship functionality."""

    def test_join_related_relationship(
        self,
        db: Session,
        sample_resident: Person,
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ):
        """Test joining related entities."""
        # Create assignment
        assignment = Assignment(
            id=uuid4(),
            block_id=sample_block.id,
            person_id=sample_resident.id,
            rotation_template_id=sample_rotation_template.id,
            role="primary",
        )
        db.add(assignment)
        db.commit()

        qb = QueryBuilder(Assignment, db)
        result = qb.join_related("person").join_related("block").all()

        assert len(result) == 1
        # Verify relationships are loaded (no additional queries)
        assert result[0].person is not None
        assert result[0].block is not None

    def test_filter_by_joined(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ):
        """Test filtering by joined relationship."""
        # Create assignments for different residents
        for resident in sample_residents:
            assignment = Assignment(
                id=uuid4(),
                block_id=sample_block.id,
                person_id=resident.id,
                rotation_template_id=sample_rotation_template.id,
                role="primary",
            )
            db.add(assignment)
        db.commit()

        qb = QueryBuilder(Assignment, db)
        result = qb.filter_by_joined("person", pgy_level=2).all()

        assert len(result) == 1
        assert result[0].person.pgy_level == 2

    def test_join_invalid_relationship(self, db: Session):
        """Test that invalid relationships raise errors."""
        qb = QueryBuilder(Person, db)

        with pytest.raises(ValueError, match="Invalid relationship"):
            qb.join_related("nonexistent_relationship")


class TestQueryBuilderAggregations:
    """Test aggregation functions."""

    def test_count(self, db: Session, sample_residents: list[Person]):
        """Test count aggregation."""
        qb = QueryBuilder(Person, db)
        count = qb.filter_by(type="resident").count()

        assert count == 3

    def test_aggregate_sum(self, db: Session, sample_residents: list[Person]):
        """Test sum aggregation."""
        qb = QueryBuilder(Person, db)
        total = qb.filter_by(type="resident").aggregate("sum", "pgy_level")

        assert total == 6  # 1 + 2 + 3

    def test_aggregate_avg(self, db: Session, sample_residents: list[Person]):
        """Test average aggregation."""
        qb = QueryBuilder(Person, db)
        avg = qb.filter_by(type="resident").aggregate("avg", "pgy_level")

        assert avg == 2.0  # (1 + 2 + 3) / 3

    def test_aggregate_min(self, db: Session, sample_residents: list[Person]):
        """Test min aggregation."""
        qb = QueryBuilder(Person, db)
        min_val = qb.filter_by(type="resident").aggregate("min", "pgy_level")

        assert min_val == 1

    def test_aggregate_max(self, db: Session, sample_residents: list[Person]):
        """Test max aggregation."""
        qb = QueryBuilder(Person, db)
        max_val = qb.filter_by(type="resident").aggregate("max", "pgy_level")

        assert max_val == 3

    def test_aggregate_invalid_function(self, db: Session):
        """Test invalid aggregation function."""
        qb = QueryBuilder(Person, db)

        with pytest.raises(ValueError, match="Invalid aggregate function"):
            qb.aggregate("invalid", "pgy_level")

    def test_group_by_with_count(self, db: Session, sample_residents: list[Person]):
        """Test GROUP BY with count."""
        qb = QueryBuilder(Person, db)
        result = (
            qb.select_columns(Person.pgy_level, func.count(Person.id))
            .filter_by(type="resident")
            .group_by("pgy_level")
            .all()
        )

        # Each PGY level should have 1 resident
        assert len(result) == 3
        for pgy_level, count in result:
            assert count == 1


class TestQueryBuilderTerminalMethods:
    """Test query execution methods."""

    def test_all(self, db: Session, sample_residents: list[Person]):
        """Test all() returns all matching results."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident").all()

        assert isinstance(result, list)
        assert len(result) == 3

    def test_first(self, db: Session, sample_residents: list[Person]):
        """Test first() returns first result."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident").order_by("pgy_level").first()

        assert result is not None
        assert result.pgy_level == 1

    def test_first_no_results(self, db: Session):
        """Test first() returns None when no results."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="nonexistent").first()

        assert result is None

    def test_one(self, db: Session, sample_resident: Person):
        """Test one() returns single result."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(id=sample_resident.id).one()

        assert result.id == sample_resident.id

    def test_one_no_results(self, db: Session):
        """Test one() raises error when no results."""
        qb = QueryBuilder(Person, db)

        with pytest.raises(NoResultFound):
            qb.filter_by(type="nonexistent").one()

    def test_one_multiple_results(self, db: Session, sample_residents: list[Person]):
        """Test one() raises error when multiple results."""
        qb = QueryBuilder(Person, db)

        with pytest.raises(MultipleResultsFound):
            qb.filter_by(type="resident").one()

    def test_one_or_none(self, db: Session, sample_resident: Person):
        """Test one_or_none() returns single result."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(id=sample_resident.id).one_or_none()

        assert result is not None
        assert result.id == sample_resident.id

    def test_one_or_none_no_results(self, db: Session):
        """Test one_or_none() returns None when no results."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="nonexistent").one_or_none()

        assert result is None

    def test_exists_true(self, db: Session, sample_resident: Person):
        """Test exists() returns True when results exist."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="resident").exists()

        assert result is True

    def test_exists_false(self, db: Session):
        """Test exists() returns False when no results."""
        qb = QueryBuilder(Person, db)
        result = qb.filter_by(type="nonexistent").exists()

        assert result is False


class TestQueryBuilderSubqueries:
    """Test subquery functionality."""

    def test_filter_in_with_subquery(
        self,
        db: Session,
        sample_residents: list[Person],
        sample_block: Block,
        sample_rotation_template: RotationTemplate,
    ):
        """Test using subquery in IN filter."""
        # Create assignments for PGY 2 and 3 only
        for resident in sample_residents:
            if resident.pgy_level > 1:
                assignment = Assignment(
                    id=uuid4(),
                    block_id=sample_block.id,
                    person_id=resident.id,
                    rotation_template_id=sample_rotation_template.id,
                    role="primary",
                )
                db.add(assignment)
        db.commit()

        # Create subquery to get person IDs with assignments
        subquery_qb = QueryBuilder(Assignment, db)
        subquery = (
            subquery_qb.select_columns(Assignment.person_id).distinct().as_subquery()
        )

        # Find residents with assignments
        qb = QueryBuilder(Person, db)
        result = qb.filter_in("id", subquery).all()

        assert len(result) == 2
        assert all(p.pgy_level > 1 for p in result)


class TestQueryBuilderDateFilters:
    """Test date filtering functionality."""

    def test_filter_date_range_both_bounds(self, db: Session):
        """Test date range with both start and end."""
        start = date.today()
        end = date.today() + timedelta(days=7)

        # Create blocks
        for i in range(10):
            block_date = start + timedelta(days=i)
            block = Block(
                id=uuid4(),
                date=block_date,
                time_of_day="AM",
                block_number=1,
                is_weekend=False,
            )
            db.add(block)
        db.commit()

        qb = QueryBuilder(Block, db)
        result = qb.filter_date_range("date", start_date=start, end_date=end).all()

        assert len(result) == 8  # Days 0-7 inclusive
        assert all(start <= b.date <= end for b in result)

    def test_filter_date_range_start_only(self, db: Session):
        """Test date range with only start date."""
        start = date.today()

        # Create blocks
        for i in range(10):
            block_date = start + timedelta(days=i - 5)
            block = Block(
                id=uuid4(),
                date=block_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
        db.commit()

        qb = QueryBuilder(Block, db)
        result = qb.filter_date_range("date", start_date=start).all()

        assert all(b.date >= start for b in result)

    def test_filter_date_range_end_only(self, db: Session):
        """Test date range with only end date."""
        end = date.today()

        # Create blocks
        for i in range(10):
            block_date = end + timedelta(days=i - 5)
            block = Block(
                id=uuid4(),
                date=block_date,
                time_of_day="AM",
                block_number=1,
            )
            db.add(block)
        db.commit()

        qb = QueryBuilder(Block, db)
        result = qb.filter_date_range("date", end_date=end).all()

        assert all(b.date <= end for b in result)


class TestQueryBuilderArrayOperations:
    """Test PostgreSQL array operations."""

    def test_filter_contains(self, db: Session):
        """Test array contains filter."""
        # Create faculty with different specialties
        fac1 = Person(
            id=uuid4(),
            name="Dr. Sports",
            type="faculty",
            specialties=["Sports Medicine", "Primary Care"],
        )
        fac2 = Person(
            id=uuid4(),
            name="Dr. General",
            type="faculty",
            specialties=["Primary Care"],
        )
        fac3 = Person(
            id=uuid4(),
            name="Dr. None",
            type="faculty",
            specialties=[],
        )
        db.add_all([fac1, fac2, fac3])
        db.commit()

        qb = QueryBuilder(Person, db)
        result = qb.filter_contains("specialties", "Sports Medicine").all()

        assert len(result) == 1
        assert result[0].name == "Dr. Sports"


class TestQueryBuilderBulkOperations:
    """Test bulk update and delete."""

    def test_bulk_update(self, db: Session, sample_residents: list[Person]):
        """Test bulk update operation."""
        qb = QueryBuilder(Person, db)
        count = qb.filter_by(pgy_level=1).update({"pgy_level": 2})

        assert count == 1

        # Verify update
        db.expire_all()  # Clear session cache
        updated = db.query(Person).filter(Person.pgy_level == 2).all()
        assert len(updated) == 2  # Original PGY 2 + updated from PGY 1

    def test_bulk_delete(self, db: Session, sample_residents: list[Person]):
        """Test bulk delete operation."""
        qb = QueryBuilder(Person, db)
        count = qb.filter_by(pgy_level=1).delete()

        assert count == 1

        # Verify deletion
        db.commit()
        remaining = db.query(Person).filter(Person.type == "resident").count()
        assert remaining == 2


class TestQueryBuilderClone:
    """Test query builder cloning."""

    def test_clone_basic(self, db: Session, sample_residents: list[Person]):
        """Test cloning a query builder."""
        base_qb = QueryBuilder(Person, db).filter_by(type="resident")

        # Clone and add different filters
        qb1 = base_qb.clone().filter_by(pgy_level=1)
        qb2 = base_qb.clone().filter_by(pgy_level=2)

        result1 = qb1.all()
        result2 = qb2.all()

        assert len(result1) == 1
        assert result1[0].pgy_level == 1

        assert len(result2) == 1
        assert result2[0].pgy_level == 2

    def test_clone_preserves_filters(self, db: Session, sample_residents: list[Person]):
        """Test that cloning preserves existing filters."""
        base_qb = (
            QueryBuilder(Person, db)
            .filter_by(type="resident")
            .filter_gte("pgy_level", 2)
        )

        cloned_qb = base_qb.clone()
        result = cloned_qb.all()

        assert len(result) == 2
        assert all(p.type == "resident" and p.pgy_level >= 2 for p in result)


class TestQueryBuilderFactoryFunction:
    """Test factory function."""

    def test_create_query_builder(self, db: Session, sample_resident: Person):
        """Test factory function creates valid builder."""
        qb = create_query_builder(Person, db)
        result = qb.filter_by(type="resident").all()

        assert isinstance(qb, QueryBuilder)
        assert len(result) >= 1


class TestQueryBuilderDistinct:
    """Test DISTINCT functionality."""

    def test_distinct_basic(self, db: Session, sample_residents: list[Person]):
        """Test basic DISTINCT."""
        qb = QueryBuilder(Person, db)
        result = (
            qb.select_columns(Person.type).filter_by(type="resident").distinct().all()
        )

        # Should get one row with type="resident"
        assert len(result) == 1
        assert result[0][0] == "resident"

    def test_distinct_on_field(self, db: Session):
        """Test DISTINCT ON specific field (PostgreSQL)."""
        # Create residents with duplicate PGY levels
        for i in range(6):
            person = Person(
                id=uuid4(),
                name=f"Resident {i}",
                type="resident",
                pgy_level=1 + (i % 3),
            )
            db.add(person)
        db.commit()

        qb = QueryBuilder(Person, db)
        result = qb.distinct("pgy_level").order_by("pgy_level").all()

        # Should get 3 results (one per PGY level)
        pgy_levels = [p.pgy_level for p in result]
        assert len(set(pgy_levels)) == 3


class TestQueryBuilderChaining:
    """Test method chaining."""

    def test_complex_chaining(self, db: Session):
        """Test complex method chaining."""
        # Create test data
        for i in range(10):
            person = Person(
                id=uuid4(),
                name=f"Resident {i:02d}",
                type="resident",
                pgy_level=1 + (i % 3),
                email=f"resident{i}@test.org",
            )
            db.add(person)
        db.commit()

        # Complex query with multiple chained methods
        result = (
            QueryBuilder(Person, db)
            .filter_by(type="resident")
            .filter_gte("pgy_level", 2)
            .order_by("pgy_level", "name")
            .limit(5)
            .all()
        )

        assert len(result) <= 5
        assert all(p.type == "resident" and p.pgy_level >= 2 for p in result)

        # Verify ordering
        for i in range(len(result) - 1):
            assert result[i].pgy_level <= result[i + 1].pgy_level


class TestQueryBuilderSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_filter_by_prevents_injection(self, db: Session, sample_resident: Person):
        """Test that filter_by prevents SQL injection."""
        # Attempt SQL injection via field value
        malicious_value = "'; DROP TABLE people; --"

        qb = QueryBuilder(Person, db)
        result = qb.filter_by(name=malicious_value).all()

        # Should safely return no results, not execute SQL injection
        assert len(result) == 0

        # Verify table still exists
        count = db.query(Person).count()
        assert count >= 1

    def test_invalid_column_name_injection(self, db: Session):
        """Test that invalid column names are rejected."""
        qb = QueryBuilder(Person, db)

        # Attempt injection via column name
        with pytest.raises(ValueError, match="Invalid column"):
            qb.filter_by(**{"name; DROP TABLE people; --": "value"})

    def test_order_by_validates_columns(self, db: Session):
        """Test that order_by validates column names."""
        qb = QueryBuilder(Person, db)

        with pytest.raises(ValueError, match="Invalid column"):
            qb.order_by("invalid_column; DROP TABLE people; --")
