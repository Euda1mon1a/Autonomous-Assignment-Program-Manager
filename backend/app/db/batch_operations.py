"""Batch database operations for improved performance.

Provides utilities for efficient bulk inserts, updates, and deletes.
"""

import logging
from typing import Any, Sequence, Type, TypeVar

from sqlalchemy import insert, update, delete
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=DeclarativeBase)


class BatchOperations:
    """Utilities for batch database operations."""

    def __init__(self, session: AsyncSession, batch_size: int = 1000) -> None:
        """Initialize batch operations handler.

        Args:
            session: Database session
            batch_size: Number of records per batch
        """
        self.session = session
        self.batch_size = batch_size

    async def bulk_insert(
        self,
        model: type[T],
        records: Sequence[dict[str, Any]],
        return_defaults: bool = False,
    ) -> int:
        """Bulk insert records efficiently.

        Args:
            model: SQLAlchemy model class
            records: List of dictionaries with record data
            return_defaults: Whether to return generated defaults (slower)

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        total_inserted = 0

        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]

            stmt = insert(model).values(batch)
            if return_defaults:
                stmt = stmt.returning(model)

            await self.session.execute(stmt)
            total_inserted += len(batch)

            logger.debug(
                f"Inserted batch {i // self.batch_size + 1}: "
                f"{len(batch)} records into {model.__tablename__}"
            )

        await self.session.commit()
        logger.info(
            f"Bulk inserted {total_inserted} records into {model.__tablename__}"
        )
        return total_inserted

    async def bulk_upsert(
        self,
        model: type[T],
        records: Sequence[dict[str, Any]],
        conflict_columns: list[str],
        update_columns: list[str],
    ) -> int:
        """Bulk insert with conflict resolution (PostgreSQL UPSERT).

        Args:
            model: SQLAlchemy model class
            records: List of dictionaries with record data
            conflict_columns: Columns to check for conflicts
            update_columns: Columns to update on conflict

        Returns:
            Number of records upserted
        """
        if not records:
            return 0

        total_upserted = 0

        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i : i + self.batch_size]

            stmt = pg_insert(model).values(batch)

            # Build update dict for conflict resolution
            update_dict = {col: getattr(stmt.excluded, col) for col in update_columns}

            stmt = stmt.on_conflict_do_update(
                index_elements=conflict_columns, set_=update_dict
            )

            await self.session.execute(stmt)
            total_upserted += len(batch)

            logger.debug(
                f"Upserted batch {i // self.batch_size + 1}: "
                f"{len(batch)} records into {model.__tablename__}"
            )

        await self.session.commit()
        logger.info(
            f"Bulk upserted {total_upserted} records into {model.__tablename__}"
        )
        return total_upserted

    async def bulk_update(
        self,
        model: type[T],
        updates: Sequence[dict[str, Any]],
        id_column: str = "id",
    ) -> int:
        """Bulk update records efficiently.

        Args:
            model: SQLAlchemy model class
            updates: List of dictionaries with id and fields to update
            id_column: Name of the ID column

        Returns:
            Number of records updated
        """
        if not updates:
            return 0

        total_updated = 0

        # Process in batches
        for i in range(0, len(updates), self.batch_size):
            batch = updates[i : i + self.batch_size]

            # Group updates by unique values for efficiency
            for record in batch:
                record_id = record.pop(id_column)
                stmt = (
                    update(model)
                    .where(getattr(model, id_column) == record_id)
                    .values(**record)
                )
                await self.session.execute(stmt)

            total_updated += len(batch)

            logger.debug(
                f"Updated batch {i // self.batch_size + 1}: "
                f"{len(batch)} records in {model.__tablename__}"
            )

        await self.session.commit()
        logger.info(f"Bulk updated {total_updated} records in {model.__tablename__}")
        return total_updated

    async def bulk_delete(
        self,
        model: type[T],
        ids: Sequence[Any],
        id_column: str = "id",
    ) -> int:
        """Bulk delete records efficiently.

        Args:
            model: SQLAlchemy model class
            ids: List of IDs to delete
            id_column: Name of the ID column

        Returns:
            Number of records deleted
        """
        if not ids:
            return 0

        total_deleted = 0

        # Process in batches
        for i in range(0, len(ids), self.batch_size):
            batch = ids[i : i + self.batch_size]

            stmt = delete(model).where(getattr(model, id_column).in_(batch))
            result = await self.session.execute(stmt)
            total_deleted += result.rowcount

            logger.debug(
                f"Deleted batch {i // self.batch_size + 1}: "
                f"{result.rowcount} records from {model.__tablename__}"
            )

        await self.session.commit()
        logger.info(f"Bulk deleted {total_deleted} records from {model.__tablename__}")
        return total_deleted

    async def copy_from_csv(
        self,
        table_name: str,
        csv_file_path: str,
        columns: list[str],
    ) -> int:
        """Use PostgreSQL COPY for extremely fast bulk inserts.

        Args:
            table_name: Target table name
            csv_file_path: Path to CSV file
            columns: List of column names

        Returns:
            Number of records copied
        """
        # Get raw connection for COPY command
        connection = await self.session.connection()
        raw_connection = await connection.get_raw_connection()

        cursor = raw_connection.cursor()

        # Execute COPY command
        with open(csv_file_path) as f:
            copy_sql = f"""
                COPY {table_name} ({",".join(columns)})
                FROM STDIN WITH CSV HEADER
            """
            cursor.copy_expert(copy_sql, f)

        row_count = cursor.rowcount
        await self.session.commit()

        logger.info(f"Copied {row_count} records to {table_name} using COPY")
        return row_count


async def bulk_insert_assignments(
    session: AsyncSession,
    assignments: list[dict[str, Any]],
) -> int:
    """Optimized bulk insert for schedule assignments.

    Args:
        session: Database session
        assignments: List of assignment dictionaries

    Returns:
        Number of assignments inserted
    """
    from app.models.assignment import Assignment

    batch_ops = BatchOperations(session, batch_size=500)
    return await batch_ops.bulk_upsert(
        Assignment,
        assignments,
        conflict_columns=["id"],
        update_columns=["person_id", "block_id", "rotation_id", "updated_at"],
    )
