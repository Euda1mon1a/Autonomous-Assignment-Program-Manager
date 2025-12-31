"""Tests for batch database operations."""

import pytest
from datetime import datetime

from app.db.batch_operations import BatchOperations
from app.models.person import Person


@pytest.mark.asyncio
async def test_bulk_insert(db_session):
    """Test bulk insert operation."""
    batch_ops = BatchOperations(db_session, batch_size=100)

    # Create test data
    persons = [
        {
            "id": f"person_{i}",
            "name": f"Person {i}",
            "type": "resident",
            "email": f"person{i}@example.com",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(250)
    ]

    # Bulk insert
    count = await batch_ops.bulk_insert(Person, persons)

    assert count == 250

    # Verify in database
    from sqlalchemy import select

    result = await db_session.execute(select(Person))
    all_persons = result.scalars().all()

    assert len(all_persons) == 250


@pytest.mark.asyncio
async def test_bulk_upsert(db_session):
    """Test bulk upsert operation."""
    batch_ops = BatchOperations(db_session, batch_size=50)

    # Insert initial data
    initial_persons = [
        {
            "id": f"person_{i}",
            "name": f"Person {i}",
            "type": "resident",
            "email": f"person{i}@example.com",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(100)
    ]

    await batch_ops.bulk_insert(Person, initial_persons)

    # Upsert with updates and new records
    upsert_persons = [
        {
            "id": f"person_{i}",
            "name": f"Updated Person {i}",  # Update
            "type": "resident",
            "email": f"person{i}@example.com",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(150)  # Includes 100 updates + 50 new
    ]

    count = await batch_ops.bulk_upsert(
        Person,
        upsert_persons,
        conflict_columns=["id"],
        update_columns=["name", "updated_at"],
    )

    assert count == 150

    # Verify updates
    from sqlalchemy import select

    result = await db_session.execute(select(Person).where(Person.id == "person_0"))
    person = result.scalar_one()

    assert person.name == "Updated Person 0"


@pytest.mark.asyncio
async def test_bulk_update(db_session):
    """Test bulk update operation."""
    batch_ops = BatchOperations(db_session, batch_size=50)

    # Insert test data
    persons = [
        {
            "id": f"person_{i}",
            "name": f"Person {i}",
            "type": "resident",
            "email": f"person{i}@example.com",
            "pgy_level": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(100)
    ]

    await batch_ops.bulk_insert(Person, persons)

    # Bulk update
    updates = [
        {
            "id": f"person_{i}",
            "pgy_level": 2,
            "updated_at": datetime.utcnow(),
        }
        for i in range(100)
    ]

    count = await batch_ops.bulk_update(Person, updates, id_column="id")

    assert count == 100

    # Verify updates
    from sqlalchemy import select

    result = await db_session.execute(select(Person))
    all_persons = result.scalars().all()

    assert all(p.pgy_level == 2 for p in all_persons)


@pytest.mark.asyncio
async def test_bulk_delete(db_session):
    """Test bulk delete operation."""
    batch_ops = BatchOperations(db_session, batch_size=50)

    # Insert test data
    persons = [
        {
            "id": f"person_{i}",
            "name": f"Person {i}",
            "type": "resident",
            "email": f"person{i}@example.com",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(100)
    ]

    await batch_ops.bulk_insert(Person, persons)

    # Bulk delete
    ids_to_delete = [f"person_{i}" for i in range(50)]
    count = await batch_ops.bulk_delete(Person, ids_to_delete, id_column="id")

    assert count == 50

    # Verify deletion
    from sqlalchemy import select

    result = await db_session.execute(select(Person))
    remaining_persons = result.scalars().all()

    assert len(remaining_persons) == 50


@pytest.mark.asyncio
async def test_batch_size_handling(db_session):
    """Test proper batch size handling."""
    batch_ops = BatchOperations(db_session, batch_size=25)

    # Insert 60 records with batch size of 25
    # Should create 3 batches: 25, 25, 10
    persons = [
        {
            "id": f"person_{i}",
            "name": f"Person {i}",
            "type": "resident",
            "email": f"person{i}@example.com",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        for i in range(60)
    ]

    count = await batch_ops.bulk_insert(Person, persons)

    assert count == 60

    # Verify all inserted
    from sqlalchemy import select

    result = await db_session.execute(select(Person))
    all_persons = result.scalars().all()

    assert len(all_persons) == 60


@pytest.mark.asyncio
async def test_empty_batch_operations(db_session):
    """Test batch operations with empty data."""
    batch_ops = BatchOperations(db_session)

    # All operations should return 0 for empty data
    assert await batch_ops.bulk_insert(Person, []) == 0
    assert await batch_ops.bulk_update(Person, []) == 0
    assert await batch_ops.bulk_delete(Person, []) == 0
