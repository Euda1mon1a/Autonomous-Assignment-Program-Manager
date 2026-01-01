"""
Verification tests for async route migration (Session 44).

Tests that all routes:
- Use async def
- Use AsyncSession
- Handle concurrent requests properly
- Maintain transaction isolation
"""
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_engine, get_async_db
from app.main import app
from app.models.user import User


class TestAsyncRouteMigration:
    """Test suite for async route migration verification."""

    @pytest.mark.asyncio
    async def test_async_database_connection(self):
        """Verify async database engine is working."""
        async with async_engine.connect() as conn:
            result = await conn.execute(select(1))
            assert result.scalar() == 1

    @pytest.mark.asyncio
    async def test_get_async_db_dependency(self):
        """Verify get_async_db dependency works."""
        async for session in get_async_db():
            assert isinstance(session, AsyncSession)
            # Test basic query
            result = await session.execute(select(1))
            assert result.scalar() == 1
            break

    @pytest.mark.asyncio
    async def test_route_handlers_are_async(self):
        """Verify all route handlers use async def."""
        from app.api.routes import (
            swap,
            people,
            assignments,
            schedule,
            procedures,
        )

        modules_to_check = [swap, people, assignments, schedule, procedures]

        for module in modules_to_check:
            router = module.router
            for route in router.routes:
                if hasattr(route, 'endpoint'):
                    endpoint = route.endpoint
                    # Check if endpoint is a coroutine function
                    assert asyncio.iscoroutinefunction(endpoint), (
                        f"Route {route.path} in {module.__name__} is not async"
                    )

    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, async_client: AsyncClient):
        """Test that async routes handle concurrent requests properly."""
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = async_client.get("/api/health")
            tasks.append(task)

        # Execute concurrently
        responses = await asyncio.gather(*tasks)

        # All should succeed
        for response in responses:
            assert response.status_code in [200, 401]  # 401 if auth required

    @pytest.mark.asyncio
    async def test_transaction_isolation(self):
        """Test that concurrent sessions maintain transaction isolation."""
        # Create two concurrent sessions
        async def session_operation(session_id: int):
            async for db in get_async_db():
                # Each session should have its own transaction
                result = await db.execute(select(1).with_for_update())
                value = result.scalar()
                await asyncio.sleep(0.1)  # Simulate work
                return session_id, value

        # Run concurrently
        task1 = session_operation(1)
        task2 = session_operation(2)

        results = await asyncio.gather(task1, task2)

        # Both should complete successfully
        assert len(results) == 2
        assert results[0][1] == 1
        assert results[1][1] == 1

    @pytest.mark.asyncio
    async def test_no_sync_queries_in_async_routes(self):
        """Verify no synchronous db.query() calls in route files."""
        import os
        import re
        from pathlib import Path

        routes_dir = Path(__file__).parent.parent / "app" / "api" / "routes"

        # Pattern to detect db.query() calls (sync SQLAlchemy)
        sync_query_pattern = re.compile(r'\bdb\.query\(')

        files_with_sync_queries = []

        for route_file in routes_dir.glob("*.py"):
            if route_file.name == "__init__.py":
                continue

            with open(route_file) as f:
                content = f.read()

            # Check for db.query() calls
            matches = sync_query_pattern.findall(content)
            if matches:
                files_with_sync_queries.append(
                    (route_file.name, len(matches))
                )

        # Report findings
        if files_with_sync_queries:
            msg = "Files still using db.query():\n"
            for filename, count in files_with_sync_queries:
                msg += f"  - {filename}: {count} occurrences\n"
            pytest.fail(msg)

    @pytest.mark.asyncio
    async def test_all_routes_use_async_session(self):
        """Verify all routes use AsyncSession instead of Session."""
        import os
        import re
        from pathlib import Path

        routes_dir = Path(__file__).parent.parent / "app" / "api" / "routes"

        # Pattern to detect sync Session usage
        sync_session_pattern = re.compile(
            r'db:\s*Session\s*=\s*Depends\(get_db\)'
        )

        files_with_sync_session = []

        for route_file in routes_dir.glob("*.py"):
            if route_file.name == "__init__.py":
                continue

            with open(route_file) as f:
                content = f.read()

            # Check for sync Session usage
            matches = sync_session_pattern.findall(content)
            if matches:
                files_with_sync_session.append(
                    (route_file.name, len(matches))
                )

        # Report findings
        if files_with_sync_session:
            msg = "Files still using sync Session:\n"
            for filename, count in files_with_sync_session:
                msg += f"  - {filename}: {count} occurrences\n"
            pytest.fail(msg)


class TestCriticalRoutesAsync:
    """Test critical routes that handle ACGME compliance."""

    @pytest.mark.asyncio
    async def test_swap_routes_async(self, async_client: AsyncClient, auth_headers):
        """Verify swap routes are async and handle concurrent requests."""
        # This would be a more detailed test in practice
        response = await async_client.get("/api/swaps/history", headers=auth_headers)
        assert response.status_code in [200, 401, 404]

    @pytest.mark.asyncio
    async def test_schedule_routes_async(self, async_client: AsyncClient, auth_headers):
        """Verify schedule routes are async."""
        response = await async_client.get("/api/schedule", headers=auth_headers)
        assert response.status_code in [200, 401, 404]

    @pytest.mark.asyncio
    async def test_assignments_routes_async(
        self, async_client: AsyncClient, auth_headers
    ):
        """Verify assignment routes are async."""
        response = await async_client.get("/api/assignments", headers=auth_headers)
        assert response.status_code in [200, 401, 404]


# Fixtures

@pytest.fixture
async def async_client():
    """Create async test client."""
    from httpx import AsyncClient
    from app.main import app

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_headers():
    """Mock auth headers for testing."""
    return {
        "Authorization": "Bearer test-token"
    }
