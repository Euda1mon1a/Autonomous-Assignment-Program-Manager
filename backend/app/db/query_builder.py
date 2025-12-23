"""
Dynamic query builder for SQLAlchemy with fluent API.

Provides a type-safe, SQL-injection-proof query builder for building
complex queries with filtering, sorting, pagination, joins, and aggregations.

Examples:
    Basic filtering and pagination:
        >>> qb = QueryBuilder(Person, db)
        >>> result = (qb
        ...     .filter_by(type="resident")
        ...     .filter_gte("pgy_level", 2)
        ...     .order_by("name")
        ...     .paginate(page=1, page_size=10))

    Join with relationship detection:
        >>> qb = QueryBuilder(Assignment, db)
        >>> result = (qb
        ...     .join_related("person")
        ...     .join_related("block")
        ...     .filter_by_joined("person", name="Dr. Smith")
        ...     .all())

    Aggregation:
        >>> qb = QueryBuilder(Assignment, db)
        >>> count = (qb
        ...     .filter_by(role="primary")
        ...     .count())

    Complex filtering with subqueries:
        >>> subquery = (QueryBuilder(Assignment, db)
        ...     .select_columns(Assignment.person_id)
        ...     .filter_by(role="primary")
        ...     .distinct()
        ...     .as_subquery())
        >>> qb = QueryBuilder(Person, db)
        >>> result = qb.filter_in("id", subquery).all()
"""

from datetime import date
from enum import Enum
from typing import Any, Generic, TypeVar

from sqlalchemy import and_, asc, desc, func, or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Query, Session, joinedload, selectinload
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import BinaryExpression

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class SortOrder(str, Enum):
    """Sort order enumeration."""

    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Filter operators for type-safe filtering."""

    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    LIKE = "like"  # SQL LIKE (case-sensitive)
    ILIKE = "ilike"  # SQL ILIKE (case-insensitive)
    IN = "in"  # IN list
    NOT_IN = "not_in"  # NOT IN list
    IS_NULL = "is_null"  # IS NULL
    IS_NOT_NULL = "is_not_null"  # IS NOT NULL
    BETWEEN = "between"  # BETWEEN two values
    CONTAINS = "contains"  # Array contains (PostgreSQL)


class QueryBuilder(Generic[ModelType]):
    """
    Fluent query builder for SQLAlchemy models.

    Provides a chainable API for building complex queries with automatic
    SQL injection prevention, type safety, and relationship handling.

    All methods return self for method chaining, except terminal methods
    like all(), first(), count(), paginate(), etc.
    """

    def __init__(self, model: type[ModelType], db: Session):
        """
        Initialize query builder.

        Args:
            model: SQLAlchemy model class to query
            db: Database session
        """
        self.model = model
        self.db = db
        self._query: Query = db.query(model)
        self._joins: set[str] = set()  # Track joined relationships
        self._filters: list[BinaryExpression] = []
        self._or_filters: list[BinaryExpression] = []
        self._eager_loads: list = []

    def filter(self, *expressions: BinaryExpression) -> "QueryBuilder[ModelType]":
        """
        Add raw SQLAlchemy filter expressions (AND conditions).

        Args:
            *expressions: SQLAlchemy binary expressions (e.g., Model.field == value)

        Returns:
            Self for chaining

        Example:
            >>> qb.filter(Person.type == "resident", Person.pgy_level >= 2)
        """
        self._filters.extend(expressions)
        return self

    def filter_or(self, *expressions: BinaryExpression) -> "QueryBuilder[ModelType]":
        """
        Add OR filter expressions.

        Args:
            *expressions: SQLAlchemy binary expressions

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_or(Person.type == "resident", Person.type == "faculty")
        """
        self._or_filters.extend(expressions)
        return self

    def filter_by(self, **kwargs: Any) -> "QueryBuilder[ModelType]":
        """
        Add equality filters using keyword arguments.

        Automatically prevents SQL injection by using bound parameters.

        Args:
            **kwargs: Field name to value mappings

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_by(type="resident", pgy_level=2)
        """
        for field, value in kwargs.items():
            if not self._is_valid_column(field):
                raise ValueError(f"Invalid column name: {field}")
            self._filters.append(getattr(self.model, field) == value)
        return self

    def filter_ne(self, field: str, value: Any) -> "QueryBuilder[ModelType]":
        """Add not-equal filter."""
        self._validate_column(field)
        self._filters.append(getattr(self.model, field) != value)
        return self

    def filter_gt(self, field: str, value: Any) -> "QueryBuilder[ModelType]":
        """Add greater-than filter."""
        self._validate_column(field)
        self._filters.append(getattr(self.model, field) > value)
        return self

    def filter_gte(self, field: str, value: Any) -> "QueryBuilder[ModelType]":
        """Add greater-than-or-equal filter."""
        self._validate_column(field)
        self._filters.append(getattr(self.model, field) >= value)
        return self

    def filter_lt(self, field: str, value: Any) -> "QueryBuilder[ModelType]":
        """Add less-than filter."""
        self._validate_column(field)
        self._filters.append(getattr(self.model, field) < value)
        return self

    def filter_lte(self, field: str, value: Any) -> "QueryBuilder[ModelType]":
        """Add less-than-or-equal filter."""
        self._validate_column(field)
        self._filters.append(getattr(self.model, field) <= value)
        return self

    def filter_like(
        self, field: str, pattern: str, case_sensitive: bool = True
    ) -> "QueryBuilder[ModelType]":
        """
        Add LIKE pattern filter.

        Args:
            field: Column name
            pattern: SQL LIKE pattern (e.g., "%smith%")
            case_sensitive: If False, uses ILIKE for case-insensitive match

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_like("name", "%Smith%", case_sensitive=False)
        """
        self._validate_column(field)
        col = getattr(self.model, field)
        if case_sensitive:
            self._filters.append(col.like(pattern))
        else:
            self._filters.append(col.ilike(pattern))
        return self

    def filter_in(
        self, field: str, values: list[Any] | Select
    ) -> "QueryBuilder[ModelType]":
        """
        Add IN filter.

        Args:
            field: Column name
            values: List of values or subquery

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_in("id", [uuid1, uuid2, uuid3])
        """
        self._validate_column(field)
        self._filters.append(getattr(self.model, field).in_(values))
        return self

    def filter_not_in(self, field: str, values: list[Any]) -> "QueryBuilder[ModelType]":
        """Add NOT IN filter."""
        self._validate_column(field)
        self._filters.append(~getattr(self.model, field).in_(values))
        return self

    def filter_is_null(self, field: str) -> "QueryBuilder[ModelType]":
        """Add IS NULL filter."""
        self._validate_column(field)
        self._filters.append(getattr(self.model, field).is_(None))
        return self

    def filter_is_not_null(self, field: str) -> "QueryBuilder[ModelType]":
        """Add IS NOT NULL filter."""
        self._validate_column(field)
        self._filters.append(getattr(self.model, field).isnot(None))
        return self

    def filter_between(
        self, field: str, start: Any, end: Any
    ) -> "QueryBuilder[ModelType]":
        """
        Add BETWEEN filter.

        Args:
            field: Column name
            start: Start value (inclusive)
            end: End value (inclusive)

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_between("created_at", start_date, end_date)
        """
        self._validate_column(field)
        self._filters.append(getattr(self.model, field).between(start, end))
        return self

    def filter_contains(self, field: str, value: Any) -> "QueryBuilder[ModelType]":
        """
        Add array contains filter (PostgreSQL).

        Args:
            field: Array column name
            value: Value to check for containment

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_contains("specialties", "Sports Medicine")
        """
        self._validate_column(field)
        self._filters.append(getattr(self.model, field).contains([value]))
        return self

    def filter_date_range(
        self,
        field: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> "QueryBuilder[ModelType]":
        """
        Add date range filter.

        Args:
            field: Date column name
            start_date: Start date (inclusive), None for no lower bound
            end_date: End date (inclusive), None for no upper bound

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_date_range("created_at", start_date=date(2024, 1, 1))
        """
        self._validate_column(field)
        if start_date:
            self._filters.append(getattr(self.model, field) >= start_date)
        if end_date:
            self._filters.append(getattr(self.model, field) <= end_date)
        return self

    def join_related(
        self,
        relationship: str,
        eager: bool = True,
        strategy: str = "selectinload",
    ) -> "QueryBuilder[ModelType]":
        """
        Join a relationship using automatic relationship detection.

        Args:
            relationship: Name of the relationship attribute
            eager: If True, eagerly load the relationship (prevents N+1)
            strategy: Eager loading strategy ("selectinload" or "joinedload")

        Returns:
            Self for chaining

        Raises:
            ValueError: If relationship doesn't exist

        Example:
            >>> qb.join_related("person")  # Eagerly load person relationship
            >>> qb.join_related("assignments", strategy="joinedload")
        """
        if not self._is_valid_relationship(relationship):
            raise ValueError(f"Invalid relationship: {relationship}")

        if relationship not in self._joins:
            self._joins.add(relationship)
            if eager:
                if strategy == "selectinload":
                    self._eager_loads.append(
                        selectinload(getattr(self.model, relationship))
                    )
                elif strategy == "joinedload":
                    self._eager_loads.append(
                        joinedload(getattr(self.model, relationship))
                    )
                else:
                    raise ValueError(f"Invalid eager loading strategy: {strategy}")

        return self

    def filter_by_joined(
        self,
        relationship: str,
        **kwargs: Any,
    ) -> "QueryBuilder[ModelType]":
        """
        Filter by fields on a joined relationship.

        Automatically joins the relationship if not already joined.

        Args:
            relationship: Name of the relationship
            **kwargs: Field filters on the related model

        Returns:
            Self for chaining

        Example:
            >>> qb.filter_by_joined("person", name="Dr. Smith", type="faculty")
        """
        if not self._is_valid_relationship(relationship):
            raise ValueError(f"Invalid relationship: {relationship}")

        # Get the related model class
        rel_property = inspect(self.model).relationships[relationship]
        related_model = rel_property.mapper.class_

        # Add join if not already joined
        if relationship not in self._joins:
            self._joins.add(relationship)
            self._query = self._query.join(getattr(self.model, relationship))

        # Add filters on the related model
        for field, value in kwargs.items():
            if not hasattr(related_model, field):
                raise ValueError(f"Invalid column {field} on {related_model.__name__}")
            self._filters.append(getattr(related_model, field) == value)

        return self

    def order_by(
        self, *fields: str, direction: SortOrder = SortOrder.ASC
    ) -> "QueryBuilder[ModelType]":
        """
        Add ordering to the query.

        Args:
            *fields: Field names to order by
            direction: Sort direction (ASC or DESC)

        Returns:
            Self for chaining

        Example:
            >>> qb.order_by("pgy_level", "name")
            >>> qb.order_by("created_at", direction=SortOrder.DESC)
        """
        for field in fields:
            self._validate_column(field)
            col = getattr(self.model, field)
            if direction == SortOrder.DESC:
                self._query = self._query.order_by(desc(col))
            else:
                self._query = self._query.order_by(asc(col))
        return self

    def order_by_desc(self, *fields: str) -> "QueryBuilder[ModelType]":
        """Shorthand for descending order."""
        return self.order_by(*fields, direction=SortOrder.DESC)

    def limit(self, limit: int) -> "QueryBuilder[ModelType]":
        """
        Limit the number of results.

        Args:
            limit: Maximum number of results

        Returns:
            Self for chaining
        """
        self._query = self._query.limit(limit)
        return self

    def offset(self, offset: int) -> "QueryBuilder[ModelType]":
        """
        Skip a number of results.

        Args:
            offset: Number of results to skip

        Returns:
            Self for chaining
        """
        self._query = self._query.offset(offset)
        return self

    def distinct(self, *fields: str) -> "QueryBuilder[ModelType]":
        """
        Apply DISTINCT to the query.

        Args:
            *fields: Optional fields for DISTINCT ON (PostgreSQL)

        Returns:
            Self for chaining
        """
        if fields:
            distinct_cols = [getattr(self.model, f) for f in fields]
            self._query = self._query.distinct(*distinct_cols)
        else:
            self._query = self._query.distinct()
        return self

    def select_columns(self, *columns: Any) -> "QueryBuilder[ModelType]":
        """
        Select specific columns instead of full model.

        Args:
            *columns: Column objects to select

        Returns:
            Self for chaining

        Note:
            This changes the return type from model instances to tuples.

        Example:
            >>> qb.select_columns(Person.id, Person.name).all()
        """
        self._query = self.db.query(*columns)
        return self

    def group_by(self, *fields: str) -> "QueryBuilder[ModelType]":
        """
        Add GROUP BY clause.

        Args:
            *fields: Field names to group by

        Returns:
            Self for chaining

        Example:
            >>> qb.select_columns(Person.type, func.count())
            ...   .group_by("type")
        """
        for field in fields:
            self._validate_column(field)
            self._query = self._query.group_by(getattr(self.model, field))
        return self

    def having(self, *expressions: BinaryExpression) -> "QueryBuilder[ModelType]":
        """
        Add HAVING clause for aggregations.

        Args:
            *expressions: SQLAlchemy expressions

        Returns:
            Self for chaining

        Example:
            >>> qb.group_by("type").having(func.count() > 5)
        """
        for expr in expressions:
            self._query = self._query.having(expr)
        return self

    def _apply_filters(self) -> None:
        """Apply all accumulated filters to the query."""
        if self._filters:
            self._query = self._query.filter(and_(*self._filters))

        if self._or_filters:
            self._query = self._query.filter(or_(*self._or_filters))

        if self._eager_loads:
            self._query = self._query.options(*self._eager_loads)

    def all(self) -> list[ModelType]:
        """
        Execute query and return all results.

        Returns:
            List of model instances
        """
        self._apply_filters()
        return self._query.all()

    def first(self) -> ModelType | None:
        """
        Execute query and return first result.

        Returns:
            First model instance or None
        """
        self._apply_filters()
        return self._query.first()

    def one(self) -> ModelType:
        """
        Execute query and return exactly one result.

        Returns:
            Single model instance

        Raises:
            NoResultFound: If no results
            MultipleResultsFound: If more than one result
        """
        self._apply_filters()
        return self._query.one()

    def one_or_none(self) -> ModelType | None:
        """
        Execute query and return one result or None.

        Returns:
            Single model instance or None

        Raises:
            MultipleResultsFound: If more than one result
        """
        self._apply_filters()
        return self._query.one_or_none()

    def count(self) -> int:
        """
        Count total results.

        Returns:
            Total count of matching records
        """
        self._apply_filters()
        return self._query.count()

    def exists(self) -> bool:
        """
        Check if any results exist.

        Returns:
            True if at least one result exists
        """
        self._apply_filters()
        return self.db.query(self._query.exists()).scalar()

    def paginate(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """
        Paginate results.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dictionary with:
                - items: List of model instances
                - total: Total count
                - page: Current page
                - page_size: Items per page
                - total_pages: Total number of pages

        Example:
            >>> result = qb.paginate(page=2, page_size=10)
            >>> result["items"]  # Items 11-20
            >>> result["total"]  # Total count of all results
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20

        # Get total count before pagination
        total = self.count()

        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size

        # Get paginated results
        items = self.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    def as_subquery(self) -> Select:
        """
        Convert query to a subquery for use in other queries.

        Returns:
            SQLAlchemy subquery

        Example:
            >>> subq = qb.select_columns(Person.id).filter_by(type="faculty").as_subquery()
            >>> main_qb = QueryBuilder(Assignment, db).filter_in("person_id", subq)
        """
        self._apply_filters()
        return self._query.subquery()

    def aggregate(
        self,
        func_name: str,
        field: str | None = None,
    ) -> Any:
        """
        Perform aggregation on a field.

        Args:
            func_name: Aggregate function name (count, sum, avg, min, max)
            field: Field to aggregate (not needed for count)

        Returns:
            Aggregation result

        Example:
            >>> qb.filter_by(type="resident").aggregate("count")
            >>> qb.filter_by(type="faculty").aggregate("avg", "pgy_level")
        """
        self._apply_filters()

        if func_name == "count":
            return self._query.count()

        if field is None:
            raise ValueError(f"Field required for {func_name} aggregation")

        self._validate_column(field)
        col = getattr(self.model, field)

        func_map = {
            "sum": func.sum,
            "avg": func.avg,
            "min": func.min,
            "max": func.max,
        }

        if func_name not in func_map:
            raise ValueError(f"Invalid aggregate function: {func_name}")

        agg_func = func_map[func_name]
        return self.db.query(agg_func(col)).filter(*self._filters).scalar()

    def delete(self) -> int:
        """
        Delete all matching records.

        Returns:
            Number of deleted records

        Warning:
            This performs a bulk delete. Use with caution.
        """
        self._apply_filters()
        count = self._query.count()
        self._query.delete(synchronize_session=False)
        return count

    def update(self, values: dict[str, Any]) -> int:
        """
        Bulk update all matching records.

        Args:
            values: Dictionary of field->value to update

        Returns:
            Number of updated records

        Warning:
            This performs a bulk update. Use with caution.

        Example:
            >>> qb.filter_by(type="resident").update({"pgy_level": 2})
        """
        # Validate all columns
        for field in values:
            self._validate_column(field)

        self._apply_filters()
        count = self._query.count()
        self._query.update(values, synchronize_session=False)
        return count

    def _is_valid_column(self, column_name: str) -> bool:
        """
        Check if column exists on the model.

        Prevents SQL injection by validating column names.

        Args:
            column_name: Name of the column

        Returns:
            True if valid column
        """
        return hasattr(self.model, column_name)

    def _validate_column(self, column_name: str) -> None:
        """
        Validate column exists, raise error if not.

        Args:
            column_name: Name of the column

        Raises:
            ValueError: If column doesn't exist
        """
        if not self._is_valid_column(column_name):
            raise ValueError(f"Invalid column: {column_name}")

    def _is_valid_relationship(self, relationship_name: str) -> bool:
        """
        Check if relationship exists on the model.

        Args:
            relationship_name: Name of the relationship

        Returns:
            True if valid relationship
        """
        mapper = inspect(self.model)
        return relationship_name in mapper.relationships

    def clone(self) -> "QueryBuilder[ModelType]":
        """
        Create a copy of this query builder.

        Useful for creating variations of a base query.

        Returns:
            New QueryBuilder instance with same filters

        Example:
            >>> base_qb = QueryBuilder(Person, db).filter_by(type="resident")
            >>> pgy1_qb = base_qb.clone().filter_by(pgy_level=1)
            >>> pgy2_qb = base_qb.clone().filter_by(pgy_level=2)
        """
        new_qb = QueryBuilder(self.model, self.db)
        new_qb._filters = self._filters.copy()
        new_qb._or_filters = self._or_filters.copy()
        new_qb._joins = self._joins.copy()
        new_qb._eager_loads = self._eager_loads.copy()
        return new_qb


def create_query_builder(
    model: type[ModelType], db: Session
) -> QueryBuilder[ModelType]:
    """
    Factory function to create a QueryBuilder instance.

    Args:
        model: SQLAlchemy model class
        db: Database session

    Returns:
        QueryBuilder instance

    Example:
        >>> from app.models.person import Person
        >>> qb = create_query_builder(Person, db)
        >>> residents = qb.filter_by(type="resident").all()
    """
    return QueryBuilder(model, db)
