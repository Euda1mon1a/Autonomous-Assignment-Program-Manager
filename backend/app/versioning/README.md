# Data Versioning Service

Comprehensive version control functionality for the Residency Scheduler backend.

## Overview

The Data Versioning Service provides Git-like version control for schedule entities, enabling teams to:
- Track complete history of all changes
- Query entity state at any point in time
- Compare different versions and generate diffs
- Rollback to previous versions with full audit trail
- Create branches to explore alternative schedules
- Detect and resolve merge conflicts
- Tag and annotate versions

## Features

### 1. Entity Version Tracking

Track complete version history for all entities with full audit trail:

```python
from app.versioning import DataVersioningService

versioning = DataVersioningService(db)

# Get version history
history = await versioning.get_version_history(
    entity_type="assignment",
    entity_id=assignment_id,
    limit=100
)

# Each version includes:
# - Timestamp and user who made the change
# - Operation type (create, update, delete)
# - SHA-256 checksum for integrity verification
# - Tags and labels
# - Branch information
```

### 2. Point-in-Time Queries

Query the state of entities at any point in time:

```python
# Query single entity at specific time
past_state = await versioning.query_at_time(
    entity_type="assignment",
    entity_id=assignment_id,
    timestamp=datetime(2024, 1, 15, 10, 30)
)

# Query all entities at specific time
all_assignments = await versioning.query_all_at_time(
    entity_type="assignment",
    timestamp=datetime(2024, 1, 15)
)

# Result includes:
# - Entity data as it existed at that time
# - Version ID active at that time
# - Whether entity existed (handles creates/deletes)
```

### 3. Version Comparison and Diff

Compare any two versions to see what changed:

```python
diff = await versioning.compare_versions(
    entity_type="assignment",
    entity_id=assignment_id,
    from_version=100,
    to_version=105
)

# Diff includes:
# - All field changes with old/new values
# - Added, removed, and modified fields
# - Timestamps for both versions
# - Human-readable change summary
```

### 4. Version Rollback

Rollback entities to previous versions with full audit trail:

```python
result = await versioning.rollback_to_version(
    entity_type="assignment",
    entity_id=assignment_id,
    target_version=100,
    user_id="dr_smith",
    reason="Reverting mistaken change to rotation assignment"
)

# Rollback:
# - Creates new version with old data (preserves history)
# - Adds rollback metadata to notes
# - Requires user ID and optional reason
# - Returns complete rollback information
```

### 5. Branch/Fork Support

Create branches to explore alternative schedules:

```python
# Create a new branch
branch = await versioning.create_branch(
    parent_branch="main",
    new_branch_name="experiment-new-rotation",
    user_id="dr_jones",
    description="Testing alternative rotation structure"
)

# Get branch information
info = await versioning.get_branch_info("experiment-new-rotation")

# List all branches
branches = await versioning.list_branches()

# Delete branch when done
await versioning.delete_branch("experiment-new-rotation", user_id="dr_jones")
```

### 6. Merge Conflict Detection

Detect conflicts when merging branches:

```python
# Detect conflicts between branches
conflicts = await versioning.detect_merge_conflicts(
    source_branch="experiment-new-rotation",
    target_branch="main",
    entity_types=["assignment", "absence"]
)

# Each conflict shows:
# - Entity and field with conflict
# - Values in source, target, and base
# - Conflict type (modify-modify, modify-delete, etc.)

# Resolve conflicts
for conflict in conflicts:
    await versioning.resolve_conflict(
        conflict=conflict,
        resolution="source",  # or "target", "base", or custom value
        user_id="dr_jones"
    )
```

### 7. Version Metadata and Tagging

Tag and annotate important versions:

```python
# Tag a version
await versioning.tag_version(
    entity_type="assignment",
    entity_id=assignment_id,
    version_id=100,
    tag="pre-production",
    user_id="dr_smith"
)

# Add comment to version
await versioning.add_version_comment(
    entity_type="assignment",
    entity_id=assignment_id,
    version_id=100,
    comment="Reviewed and approved by scheduling committee",
    user_id="dr_jones"
)
```

### 8. Lineage and Comparison

Track complete lineage and compare branches:

```python
# Get complete lineage of an entity
lineage = await versioning.get_entity_lineage(
    entity_type="assignment",
    entity_id=assignment_id
)

# Compare two branches
comparison = await versioning.compare_branches(
    branch1="main",
    branch2="experiment-new-rotation",
    entity_types=["assignment"]
)

# Shows:
# - Entities unique to each branch
# - Entities modified in both branches
# - Identical entities
```

## Supported Entity Types

The versioning service supports these entity types:

- `assignment` - Schedule assignments
- `absence` - Faculty/resident absences
- `schedule_run` - Schedule generation runs
- `swap_record` - Schedule swap requests

## Integration with SQLAlchemy-Continuum

This service extends the built-in version tracking provided by SQLAlchemy-Continuum:

- **Base version tracking**: Provided by `__versioned__ = {}` in models
- **Advanced features**: Provided by this service (branching, merging, PIT queries)

All models with `__versioned__ = {}` automatically track:
- Who made the change (user_id)
- When the change was made (timestamp)
- What changed (old/new values)
- Operation type (create/update/delete)

## Use Cases

### Exploring Alternative Schedules

```python
# Create experimental branch
branch = await versioning.create_branch(
    parent_branch="main",
    new_branch_name="try-4-week-rotations",
    user_id="coordinator",
    description="Testing 4-week rotation structure instead of 2-week"
)

# Make changes to assignments in experimental branch...
# (Changes are isolated from main branch)

# Compare results
comparison = await versioning.compare_branches(
    branch1="main",
    branch2="try-4-week-rotations"
)

# If experiment successful, merge changes
# If not, simply delete the branch
await versioning.delete_branch("try-4-week-rotations", user_id="coordinator")
```

### Compliance Auditing

```python
# Get all changes in last 30 days
history = await versioning.get_version_history(
    entity_type="assignment",
    entity_id=assignment_id
)

# Check state at time of compliance violation
violation_time = datetime(2024, 1, 15, 14, 30)
state_at_violation = await versioning.query_at_time(
    entity_type="assignment",
    entity_id=assignment_id,
    timestamp=violation_time
)

# Generate audit report showing what changed
diff = await versioning.compare_versions(
    entity_type="assignment",
    entity_id=assignment_id,
    from_version=before_version,
    to_version=after_version
)
```

### Rollback After Errors

```python
# Something went wrong with schedule generation
# Query state before the changes
pre_error_time = datetime.utcnow() - timedelta(hours=2)
assignments_before = await versioning.query_all_at_time(
    entity_type="assignment",
    timestamp=pre_error_time
)

# Rollback to previous version
for assignment in affected_assignments:
    await versioning.rollback_to_version(
        entity_type="assignment",
        entity_id=assignment.id,
        target_version=previous_good_version,
        user_id="system",
        reason="Automatic rollback due to scheduling error"
    )
```

## API Schemas

The service uses Pydantic schemas for all operations. See `schemas.py` for:

- `VersionMetadataSchema` - Version metadata
- `VersionDiffSchema` - Version comparison results
- `PointInTimeQuerySchema` - Point-in-time query results
- `VersionBranchSchema` - Branch information
- `MergeConflictSchema` - Merge conflict details

## Performance Considerations

### Version History Queries

- Use `limit` parameter to avoid loading excessive history
- Index on `transaction_id` for fast version lookups
- Consider archiving very old versions for performance

### Point-in-Time Queries

- PIT queries scan version tables backwards from target time
- For bulk PIT queries, consider caching results
- Use `query_all_at_time()` instead of multiple `query_at_time()` calls

### Branch Operations

- Branches are currently in-memory (registry)
- For production use, persist branches to database
- Consider branch lifecycle policies (auto-cleanup)

## Security Considerations

### Audit Trail Integrity

- Version checksums (SHA-256) verify data integrity
- Transaction IDs ensure ordering
- User IDs track who made each change
- Cannot modify historical versions (immutable)

### Access Control

- Rollback operations require user authentication
- Branch creation/deletion should require permissions
- Consider role-based restrictions on version access

### Data Privacy

- Version history may contain sensitive data
- Apply same access controls as live data
- Consider data retention policies for old versions

## Testing

Comprehensive test suite in `tests/versioning/test_data_versioning.py`:

```bash
# Run all versioning tests
pytest tests/versioning/

# Run specific test class
pytest tests/versioning/test_data_versioning.py::TestVersionHistory

# Run with coverage
pytest --cov=app.versioning tests/versioning/
```

## Future Enhancements

Potential improvements for future versions:

1. **Persistent Branch Storage**: Store branches in database instead of in-memory
2. **Automatic Conflict Resolution**: Smart merge strategies for common conflicts
3. **Version Compression**: Compress old versions to save storage
4. **Delta Storage**: Store diffs instead of full versions for efficiency
5. **Multi-Entity Transactions**: Version multiple entities atomically
6. **Branch Permissions**: Fine-grained access control per branch
7. **Version Analytics**: Statistics on change patterns and frequencies
8. **Scheduled Snapshots**: Automatic tagging of versions at intervals

## Implementation Notes

### Database Integration

The service integrates with SQLAlchemy-Continuum's version tables:
- `assignment_version`
- `absence_version`
- `schedule_run_version`
- `swap_record_version`

### Transaction Management

- All operations use database transactions
- Rollbacks create new versions (no data loss)
- Checksums ensure data integrity

### Type Safety

- Full type hints throughout
- Pydantic schemas for validation
- TypedDict for internal structures

## Contributing

When extending the versioning service:

1. **Add new entity types**: Update `ENTITY_MODEL_MAP` in `data_versioning.py`
2. **Add new features**: Follow async patterns and type hints
3. **Write tests**: Add tests to `test_data_versioning.py`
4. **Update schemas**: Add Pydantic schemas to `schemas.py`
5. **Document**: Update this README with usage examples

## References

- [SQLAlchemy-Continuum Documentation](https://sqlalchemy-continuum.readthedocs.io/)
- [Git Branching Model](https://git-scm.com/book/en/v2/Git-Branching-Branching-Workflows)
- [Event Sourcing Pattern](https://martinfowler.com/eaaDev/EventSourcing.html)

---

**Version**: 1.0.0
**Last Updated**: 2025-12-20
**Maintainer**: Residency Scheduler Team
