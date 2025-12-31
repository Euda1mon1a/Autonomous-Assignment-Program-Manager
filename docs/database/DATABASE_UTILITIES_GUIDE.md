***REMOVED*** Database Utilities Guide

> **Status:** Comprehensive utility implementation for async repositories, migrations, seeding, and health monitoring
> **Last Updated:** 2025-12-31

***REMOVED******REMOVED*** Table of Contents

1. [Async Repository Base](***REMOVED***async-repository-base)
2. [Unit of Work Pattern](***REMOVED***unit-of-work-pattern)
3. [Repository Factory](***REMOVED***repository-factory)
4. [Migration Utilities](***REMOVED***migration-utilities)
5. [Database Seeding](***REMOVED***database-seeding)
6. [Query Optimization](***REMOVED***query-optimization)
7. [Database Health Monitoring](***REMOVED***database-health-monitoring)
8. [Best Practices](***REMOVED***best-practices)

---

***REMOVED******REMOVED*** Async Repository Base

The `AsyncBaseRepository` provides comprehensive async/await CRUD operations with advanced features.

***REMOVED******REMOVED******REMOVED*** Location
`backend/app/repositories/async_base.py`

***REMOVED******REMOVED******REMOVED*** Features

- **Async CRUD Operations**: Full async support for all database operations
- **Pagination**: Built-in pagination with configurable limits
- **Advanced Filtering**: Multiple filter types (exact match, range, text search)
- **Eager Loading**: Prevent N+1 queries with relationship loading
- **Bulk Operations**: Efficient batch create/update/delete
- **Transaction Management**: Explicit commit/rollback support
- **Query Utilities**: Helper methods for common patterns

***REMOVED******REMOVED******REMOVED*** Basic Usage

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.person import Person
from app.repositories.async_base import AsyncBaseRepository, PaginationParams
from app.schemas.person import PersonCreate, PersonUpdate

***REMOVED*** Create repository
repo = AsyncBaseRepository(Person, db_session)

***REMOVED*** Create
new_person = await repo.create(PersonCreate(name="John Doe"))
await repo.commit()

***REMOVED*** Read
person = await repo.get_by_id("person-123")

***REMOVED*** Update
updated = await repo.update(person, PersonUpdate(name="Jane Doe"))
await repo.commit()

***REMOVED*** Delete
await repo.delete(person)
await repo.commit()
```

***REMOVED******REMOVED******REMOVED*** Pagination

```python
from app.repositories.async_base import PaginationParams

***REMOVED*** Create pagination params
pagination = PaginationParams(skip=0, limit=20)

***REMOVED*** Get paginated results
result = await repo.get_paginated(
    pagination,
    order_by="created_at",  ***REMOVED*** or "-created_at" for descending
)

***REMOVED*** Access results
for person in result.data:
    print(person.name)

print(f"Total: {result.total}, Pages: {result.pages}")
```

***REMOVED******REMOVED******REMOVED*** Filtering

```python
***REMOVED*** Simple filter
results = await repo.get_by_filters({"role": "RESIDENT"})

***REMOVED*** Multiple filters
results = await repo.get_by_filters({
    "role": "RESIDENT",
    "is_active": True
})

***REMOVED*** First match only
first = await repo.get_first_by_filters({"role": "FACULTY"})
```

***REMOVED******REMOVED******REMOVED*** Eager Loading

```python
***REMOVED*** Load relationships to prevent N+1
person = await repo.get_by_id_with_relations(
    person_id,
    relations=["assignments", "certifications"]
)

***REMOVED*** All with relationships
persons = await repo.get_all_with_relations(
    relations=["assignments"],
    pagination=pagination
)
```

***REMOVED******REMOVED******REMOVED*** Bulk Operations

```python
***REMOVED*** Bulk create
new_persons = await repo.bulk_create([
    PersonCreate(name="Person 1"),
    PersonCreate(name="Person 2"),
    PersonCreate(name="Person 3"),
])
await repo.commit()

***REMOVED*** Bulk delete
deleted_count = await repo.bulk_delete(["id1", "id2", "id3"])
await repo.commit()
```

---

***REMOVED******REMOVED*** Unit of Work Pattern

The `UnitOfWork` class coordinates multiple repositories within a single transaction.

***REMOVED******REMOVED******REMOVED*** Location
`backend/app/repositories/unit_of_work.py`

***REMOVED******REMOVED******REMOVED*** Usage

```python
from app.repositories.unit_of_work import UnitOfWork
from app.repositories.async_base import AsyncBaseRepository
from app.models.person import Person
from app.models.assignment import Assignment

***REMOVED*** Create Unit of Work
async with UnitOfWork(db_session) as uow:
    ***REMOVED*** Register repositories
    person_repo = AsyncBaseRepository(Person, db_session)
    assignment_repo = AsyncBaseRepository(Assignment, db_session)

    uow.register_repository("persons", person_repo)
    uow.register_repository("assignments", assignment_repo)

    ***REMOVED*** Perform operations
    person = await person_repo.create(person_data)
    assignment = await assignment_repo.create(assignment_data)

    ***REMOVED*** Both committed atomically on exit
    ***REMOVED*** Rolled back if exception occurs
```

***REMOVED******REMOVED******REMOVED*** Features

- **Atomic Transactions**: All operations commit or rollback together
- **Repository Registration**: Centralized repository management
- **Auto Rollback**: Automatic rollback on exceptions
- **Context Manager**: Safe resource cleanup

---

***REMOVED******REMOVED*** Repository Factory

The `RepositoryFactory` creates and manages repository instances.

***REMOVED******REMOVED******REMOVED*** Location
`backend/app/repositories/factory.py`

***REMOVED******REMOVED******REMOVED*** Usage

```python
from app.repositories.factory import RepositoryProvider
from app.models.person import Person

***REMOVED*** Create provider
provider = RepositoryProvider(db_session)

***REMOVED*** Get repository for model
person_repo = provider.get_repository(Person)

***REMOVED*** Use repository
persons = await person_repo.get_all()
```

***REMOVED******REMOVED******REMOVED*** Features

- **Lazy Creation**: Repositories created on-demand
- **Caching**: Avoid recreating repositories
- **Type-Safe**: Generic type support
- **Custom Repositories**: Register custom implementations

---

***REMOVED******REMOVED*** Migration Utilities

The `MigrationUtils` module provides helpers for Alembic migration management.

***REMOVED******REMOVED******REMOVED*** Location
`backend/scripts/migration_utils.py`

***REMOVED******REMOVED******REMOVED*** Features

- **Generate Migrations**: Simplified migration creation
- **Validate Migrations**: Check for errors and conflicts
- **Detect Conflicts**: Find orphaned branches
- **Migration Status**: Show current state
- **Migration History**: View applied migrations

***REMOVED******REMOVED******REMOVED*** CLI Usage

```bash
***REMOVED*** List all migrations
python backend/scripts/migration_utils.py list

***REMOVED*** Validate migrations
python backend/scripts/migration_utils.py validate

***REMOVED*** Show status
python backend/scripts/migration_utils.py status

***REMOVED*** Detect conflicts
python backend/scripts/migration_utils.py conflicts

***REMOVED*** Show history
python backend/scripts/migration_utils.py history
```

***REMOVED******REMOVED******REMOVED*** Python Usage

```python
from app.scripts.migration_utils import MigrationUtils, MigrationDryRun

utils = MigrationUtils()

***REMOVED*** List migrations
migrations = utils.list_migrations()

***REMOVED*** Validate
is_valid, issues = utils.validate_migrations()
if not is_valid:
    for issue in issues:
        print(f"Issue: {issue}")

***REMOVED*** Generate migration
success, output = utils.generate_migration(
    "Add created_at to persons"
)

***REMOVED*** Check current status
success, status = utils.show_migration_status()

***REMOVED*** Get history
success, history = utils.get_migration_history()

***REMOVED*** Dry-run upgrade
success, sql = MigrationDryRun.dry_run_upgrade("head")
print(f"Would execute:\n{sql}")
```

***REMOVED******REMOVED******REMOVED*** Workflow

1. **Modify Models**: Update SQLAlchemy model
2. **Generate**: Auto-generate migration
3. **Review**: Check generated migration in `alembic/versions/`
4. **Edit**: Adjust if needed (autogenerate isn't perfect)
5. **Test**: Run migration on test database
6. **Apply**: Apply to production

---

***REMOVED******REMOVED*** Database Seeding

The `SeedData` module provides development and test data generation.

***REMOVED******REMOVED******REMOVED*** Location
`backend/scripts/seed_data.py`

***REMOVED******REMOVED******REMOVED*** Seed Types

***REMOVED******REMOVED******REMOVED******REMOVED*** Development Seed
Complete, realistic development data (sanitized).

```python
from app.scripts.seed_data import SeedDataManager

result = SeedDataManager.seed_development(db)
***REMOVED*** Creates: users, persons, rotation_templates, blocks, assignments
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Test Fixtures
Minimal test data for unit tests.

```python
result = SeedDataManager.seed_test_fixtures(db)
***REMOVED*** Creates: 1 test user, 2 test persons, 1 template, 2 blocks
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Demo Seed
Complete demo environment data.

```python
result = SeedDataManager.seed_demo(db)
***REMOVED*** Same as development
```

***REMOVED******REMOVED******REMOVED*** CLI Usage

```bash
***REMOVED*** Seed development data
python backend/scripts/seed_data.py dev

***REMOVED*** Seed test fixtures
python backend/scripts/seed_data.py test

***REMOVED*** Seed demo data
python backend/scripts/seed_data.py demo

***REMOVED*** Validate environment
python backend/scripts/seed_data.py validate

***REMOVED*** Clear all seed data
python backend/scripts/seed_data.py clear
```

***REMOVED******REMOVED******REMOVED*** What Gets Created

**Development Seed**:
- 3 admin/coordinator/faculty users
- 9 residents (3 PGY levels × 3 per level)
- 3 faculty members
- 4 rotation templates
- 260 blocks (half year)
- Sample assignments

**Test Fixtures**:
- 1 test user
- 1 resident + 1 faculty
- 1 rotation template
- 2 blocks

***REMOVED******REMOVED******REMOVED*** Security Considerations

- Uses **sanitized identifiers** (PGY1-01, FAC-01)
- Never includes real names or personal data
- Safe for version control
- Environment-specific data only

---

***REMOVED******REMOVED*** Query Optimization

The `query_optimizer` module provides query performance utilities.

***REMOVED******REMOVED******REMOVED*** Location
`backend/app/db/query_optimizer.py`

***REMOVED******REMOVED******REMOVED*** Query Analysis

```python
from app.db.query_optimizer import QueryAnalyzer

***REMOVED*** Enable SQL logging
QueryAnalyzer.enable_query_logging(engine, verbose=True)

***REMOVED*** Detect N+1 patterns
issues = QueryAnalyzer.detect_n_plus_one(session)

***REMOVED*** Analyze execution plan
plan = QueryAnalyzer.analyze_query_plan(session, query)

***REMOVED*** Get table statistics
stats = QueryAnalyzer.get_table_stats(session, Person)
```

***REMOVED******REMOVED******REMOVED*** Performance Tracking

```python
from app.db.query_optimizer import QueryDecorator

***REMOVED*** Track function performance
@QueryDecorator.track_performance(threshold_ms=100)
def expensive_operation():
    pass

***REMOVED*** Cache query results (5 min TTL)
@QueryDecorator.cache_result(ttl_seconds=300)
def get_all_persons():
    return session.query(Person).all()
```

***REMOVED******REMOVED******REMOVED*** Bulk Operations

```python
from app.db.query_optimizer import BulkOperations

***REMOVED*** Bulk insert
data = [
    {"name": "Person 1"},
    {"name": "Person 2"},
]
count = BulkOperations.bulk_insert(session, Person, data)

***REMOVED*** Bulk update
updates = [
    {"id": "1", "is_active": False},
    {"id": "2", "is_active": False},
]
count = BulkOperations.bulk_update(session, Person, updates)

***REMOVED*** Bulk delete
count = BulkOperations.bulk_delete(session, Person, ["id1", "id2"])
```

***REMOVED******REMOVED******REMOVED*** Filtering and Sorting

```python
from app.db.query_optimizer import FilterHelper, SortHelper

***REMOVED*** Apply filters
query = FilterHelper.apply_filters(
    query,
    {"role": "RESIDENT", "is_active": True}
)

***REMOVED*** Range filter
query = FilterHelper.apply_range_filter(
    query,
    "created_at",
    Person,
    min_val=start_date,
    max_val=end_date
)

***REMOVED*** Text search
query = FilterHelper.apply_search(
    query,
    Person,
    "john",
    fields=["name", "email"]
)

***REMOVED*** Sorting
query = SortHelper.apply_sort(query, Person, "name")
query = SortHelper.apply_sort(query, Person, "-created_at")  ***REMOVED*** Descending
```

***REMOVED******REMOVED******REMOVED*** Pagination

```python
from app.db.query_optimizer import PaginationHelper

***REMOVED*** Paginate
query, total = PaginationHelper.paginate(
    query,
    skip=0,
    limit=20
)

***REMOVED*** Get pagination info
info = PaginationHelper.get_pagination_info(
    total=total,
    skip=0,
    limit=20
)
***REMOVED*** {total, skip, limit, pages, current_page, has_next, has_previous}
```

---

***REMOVED******REMOVED*** Database Health Monitoring

The `health_check` module provides database health monitoring.

***REMOVED******REMOVED******REMOVED*** Location
`backend/app/db/health_check.py`

***REMOVED******REMOVED******REMOVED*** Connection Pool Monitoring

```python
from app.db.health_check import ConnectionPoolMonitor

monitor = ConnectionPoolMonitor(engine)

***REMOVED*** Get current metrics
metrics = monitor.get_current_metrics()
print(f"Utilization: {metrics.pool_utilization_percent}%")

***REMOVED*** Check health
is_healthy = monitor.is_healthy(max_utilization=85.0)

***REMOVED*** Get summary
summary = monitor.get_metrics_summary()
```

***REMOVED******REMOVED******REMOVED*** Query Latency Tracking

```python
from app.db.health_check import QueryLatencyTracker

tracker = QueryLatencyTracker(slow_query_threshold_ms=100)

***REMOVED*** Record query
tracker.record_query("SELECT * FROM persons", duration_ms=45.5)

***REMOVED*** Get metrics
metrics = tracker.get_metrics()
print(f"Avg: {metrics.avg_duration_ms}ms, Slow: {metrics.slow_query_count}")

***REMOVED*** Get slowest queries
slow = tracker.get_slow_queries(limit=5)
```

***REMOVED******REMOVED******REMOVED*** Index Usage Analysis

```python
from app.db.health_check import IndexUsageAnalyzer

analyzer = IndexUsageAnalyzer(session)

***REMOVED*** Get unused indexes
unused = analyzer.get_unused_indexes()

***REMOVED*** Get efficiency metrics
efficiency = analyzer.get_index_efficiency()
```

***REMOVED******REMOVED******REMOVED*** Table Size Monitoring

```python
from app.db.health_check import TableSizeMonitor

monitor = TableSizeMonitor(session)

***REMOVED*** Get all table sizes
sizes = monitor.get_table_sizes()

***REMOVED*** Get largest tables
largest = monitor.get_largest_tables(limit=10)

***REMOVED*** Track growth
trend = monitor.get_growth_trend("persons")
print(f"Growth rate: {trend['growth_rate_mb_per_hour']} MB/hour")
```

***REMOVED******REMOVED******REMOVED*** Full Health Check

```python
from app.db.health_check import DatabaseHealthCheck

health_check = DatabaseHealthCheck(engine, session)

***REMOVED*** Run comprehensive check
report = health_check.run_full_check()

***REMOVED*** Get health status
status = health_check.get_health_status()
print(f"Healthy: {status['healthy']}")

***REMOVED*** Check if healthy
is_healthy = health_check.is_healthy(
    max_pool_utilization=85.0,
    max_avg_query_time=200.0
)
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** Repository Usage

1. **Use AsyncBaseRepository for new code**: Provides full async support
2. **Create repository per model**: Don't reuse repositories across models
3. **Use eager loading**: Load relationships with queries
4. **Paginate large result sets**: Avoid loading everything into memory
5. **Use bulk operations**: For importing multiple records

***REMOVED******REMOVED******REMOVED*** Migration Management

1. **Run migrations before deployment**: Never skip
2. **Review autogenerated migrations**: Autogenerate makes mistakes
3. **Test rollbacks**: Ensure downgrade works
4. **Keep migrations small**: One logical change per migration
5. **Document data migrations**: Explain transformations

***REMOVED******REMOVED******REMOVED*** Query Optimization

1. **Enable query logging**: Catch N+1 patterns early
2. **Use pagination**: Especially for public APIs
3. **Index frequently filtered columns**: Improves performance
4. **Monitor slow queries**: Set threshold and track
5. **Use bulk operations**: 10x faster for many records

***REMOVED******REMOVED******REMOVED*** Health Monitoring

1. **Monitor pool utilization**: Alert at 80%+
2. **Track query latency**: Alert if avg > 200ms
3. **Check for deadlocks**: Daily audit
4. **Monitor table growth**: Plan for storage
5. **Analyze unused indexes**: Remove to improve write performance

***REMOVED******REMOVED******REMOVED*** Security

1. **Never log sensitive data**: Passwords, tokens, PII
2. **Use parameterized queries**: SQLAlchemy does this automatically
3. **Validate input**: Use Pydantic schemas
4. **Limit query results**: Pagination prevents abuse
5. **Use read replicas**: For heavy analytics

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** N+1 Query Problem

**Symptom**: Many SELECT queries for one operation
**Solution**: Use eager loading
```python
person = await repo.get_by_id_with_relations(id, ["assignments"])
```

***REMOVED******REMOVED******REMOVED*** Slow Queries

**Symptom**: Queries exceed 100ms
**Solution**: Check indexes, use pagination, add eager loading

***REMOVED******REMOVED******REMOVED*** Connection Pool Exhaustion

**Symptom**: "QueuePool limit exceeded"
**Solution**:
- Increase DB_POOL_SIZE
- Close sessions properly
- Use context managers

***REMOVED******REMOVED******REMOVED*** Deadlocks

**Symptom**: Random "Deadlock detected" errors
**Solution**:
- Use UnitOfWork for consistent ordering
- Keep transactions short
- Use timeouts

---

***REMOVED******REMOVED*** Summary

| Module | Purpose | Key Classes |
|--------|---------|------------|
| async_base.py | Async CRUD operations | AsyncBaseRepository, PaginationParams |
| unit_of_work.py | Transaction coordination | UnitOfWork |
| factory.py | Repository creation | RepositoryFactory, RepositoryProvider |
| migration_utils.py | Migration management | MigrationUtils, MigrationDryRun |
| seed_data.py | Data generation | SeedDataManager, DevelopmentSeed |
| query_optimizer.py | Query optimization | BulkOperations, FilterHelper, SortHelper |
| health_check.py | Health monitoring | DatabaseHealthCheck, TableSizeMonitor |

---

*This guide is maintained as a living document. Update when new utilities are added.*
