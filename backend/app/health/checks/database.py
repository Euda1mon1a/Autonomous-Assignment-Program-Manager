"""
Database health check implementation.

Provides comprehensive database health monitoring including:
- Connection pool status
- Query execution time
- Connection count
- Database version
- Table accessibility
"""

import asyncio
import logging
import time
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal, engine

logger = logging.getLogger(__name__)
settings = get_settings()


class DatabaseHealthCheck:
    """
    Database health check implementation.

    Performs health checks on the PostgreSQL database including:
    - Basic connectivity test
    - Query performance test
    - Connection pool status
    - Database metadata
    """

    def __init__(self, timeout: float = 5.0) -> None:
        """
        Initialize database health check.

        Args:
            timeout: Maximum time in seconds to wait for health check
        """
        self.timeout = timeout
        self.name = "database"

    async def check(self) -> dict[str, Any]:
        """
        Perform database health check.

        Returns:
            Dictionary with health status:
            - status: "healthy", "degraded", or "unhealthy"
            - response_time_ms: Query execution time
            - connection_pool: Pool status information
            - database_version: PostgreSQL version
            - error: Error message if unhealthy

        Raises:
            TimeoutError: If check exceeds timeout
        """
        start_time = time.time()

        try:
            # Run check with timeout
            result = await asyncio.wait_for(self._perform_check(), timeout=self.timeout)

            response_time_ms = (time.time() - start_time) * 1000
            result["response_time_ms"] = round(response_time_ms, 2)

            # Determine status based on response time
            if response_time_ms > 1000:  # > 1 second is degraded
                result["status"] = "degraded"
                result["warning"] = "Database response time is slow"

            return result

        except TimeoutError:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check timed out after {self.timeout}s")
            return {
                "status": "unhealthy",
                "error": f"Health check timed out after {self.timeout}s",
                "response_time_ms": round(response_time_ms, 2),
            }

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}", exc_info=True)
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(response_time_ms, 2),
            }

    async def _perform_check(self) -> dict[str, Any]:
        """
        Perform the actual database health check.

        Returns:
            Dictionary with detailed health information
        """
        db: Session | None = None

        try:
            db = SessionLocal()

            # 1. Test basic connectivity with simple query
            result = db.execute(text("SELECT 1"))
            result.scalar()

            # 2. Get database version
            version_result = db.execute(text("SELECT version()"))
            db_version = version_result.scalar()

            # 3. Get connection pool statistics
            pool_status = self._get_pool_status()

            # 4. Test table accessibility (check if core tables exist)
            table_check = self._check_core_tables(db)

            # All checks passed
            return {
                "status": "healthy",
                "database_version": (
                    db_version.split(",")[0] if db_version else "unknown"
                ),
                "connection_pool": pool_status,
                "tables_accessible": table_check["accessible"],
                "tables_checked": table_check["checked"],
            }

        except SQLAlchemyError as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": f"Database error: {str(e)}",
            }

        finally:
            if db:
                db.close()

    def _get_pool_status(self) -> dict[str, Any]:
        """
        Get database connection pool status.

        Returns:
            Dictionary with pool statistics
        """
        try:
            pool = engine.pool

            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "max_overflow": settings.DB_POOL_MAX_OVERFLOW,
                "pool_size": settings.DB_POOL_SIZE,
            }

        except Exception as e:
            logger.warning(f"Failed to get pool status: {e}")
            return {
                "error": "Could not retrieve pool status",
            }

    def _check_core_tables(self, db: Session) -> dict[str, Any]:
        """
        Check if core database tables are accessible.

        Args:
            db: Database session

        Returns:
            Dictionary with table accessibility information
        """
        core_tables = [
            "persons",
            "blocks",
            "assignments",
            "rotation_templates",
        ]

        accessible = []
        checked = len(core_tables)

        for table_name in core_tables:
            try:
                # Try to query table (with limit to avoid loading data)
                query = text(f"SELECT 1 FROM {table_name} LIMIT 1")
                db.execute(query)
                accessible.append(table_name)

            except SQLAlchemyError:
                # Table not accessible
                logger.warning(f"Core table '{table_name}' not accessible")

        return {
            "accessible": len(accessible),
            "checked": checked,
            "tables": accessible,
        }

    async def check_read_write(self) -> dict[str, Any]:
        """
        Perform read-write health check (more comprehensive).

        This check creates a temporary test record to verify
        database write capabilities.

        Returns:
            Dictionary with read-write health status
        """
        db: Session | None = None

        try:
            db = SessionLocal()

            # Create a temporary table for health checks
            db.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS health_check_temp (
                    id SERIAL PRIMARY KEY,
                    checked_at TIMESTAMP DEFAULT NOW()
                )
            """
                )
            )

            # Insert test record
            db.execute(text("INSERT INTO health_check_temp DEFAULT VALUES"))

            # Read back
            result = db.execute(text("SELECT COUNT(*) FROM health_check_temp"))
            count = result.scalar()

            # Cleanup old records (keep only last 10)
            db.execute(
                text(
                    """
                DELETE FROM health_check_temp
                WHERE id NOT IN (
                    SELECT id FROM health_check_temp
                    ORDER BY checked_at DESC
                    LIMIT 10
                )
            """
                )
            )

            db.commit()

            return {
                "status": "healthy",
                "read_write": "functional",
                "test_records": count,
            }

        except SQLAlchemyError as e:
            if db:
                db.rollback()

            logger.error(f"Database read-write check failed: {e}")
            return {
                "status": "degraded",
                "read_write": "failed",
                "error": str(e),
            }

        finally:
            if db:
                db.close()
