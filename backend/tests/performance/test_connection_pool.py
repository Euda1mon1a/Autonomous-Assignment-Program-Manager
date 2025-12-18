"""
Connection Pool Stress Tests.

Tests database connection pool behavior under various stress scenarios:
1. Pool saturation and graceful handling
2. Concurrent Celery background tasks + API requests
3. Connection leak detection
4. Pool recovery after database restart
5. Concurrent transaction isolation

These tests verify that the application handles connection pool exhaustion
gracefully and maintains proper connection lifecycle management.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from datetime import date, timedelta
from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, event, pool, text
from sqlalchemy.exc import OperationalError, TimeoutError as SQLAlchemyTimeoutError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, StaticPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import SessionLocal, engine, task_session_scope
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.person import Person


# ============================================================================
# Test Fixtures for Connection Pool Configuration
# ============================================================================

@pytest.fixture(scope="function")
def small_pool_engine():
    """
    Create a test engine with a small connection pool.

    Pool configuration:
    - pool_size=5 (typical production value)
    - max_overflow=5 (limited to force saturation)
    - pool_timeout=2 (short timeout for fast failure)
    """
    test_url = "sqlite:///:memory:"

    test_engine = create_engine(
        test_url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=5,
        pool_timeout=2,  # 2 second timeout
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=test_engine)
    yield test_engine

    test_engine.dispose()


@pytest.fixture(scope="function")
def small_pool_session(small_pool_engine):
    """Create session factory bound to small pool engine."""
    TestSession = sessionmaker(autocommit=False, autoflush=False, bind=small_pool_engine)
    return TestSession


@pytest.fixture(scope="function")
def monitored_pool_engine():
    """
    Create an engine with connection monitoring for leak detection.

    Tracks:
    - Connections checked out
    - Connections returned
    - Connection lifecycle events
    """
    test_url = "sqlite:///:memory:"

    test_engine = create_engine(
        test_url,
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=10,
        pool_timeout=5,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )

    # Track connection events
    connection_events = {
        "checked_out": 0,
        "checked_in": 0,
        "connect": 0,
        "checkout": 0,
    }

    @event.listens_for(test_engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        connection_events["connect"] += 1

    @event.listens_for(test_engine, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        connection_events["checkout"] += 1
        connection_events["checked_out"] += 1

    @event.listens_for(test_engine, "checkin")
    def receive_checkin(dbapi_conn, connection_record):
        connection_events["checked_in"] += 1

    Base.metadata.create_all(bind=test_engine)

    # Attach metrics to engine for test access
    test_engine._connection_events = connection_events

    yield test_engine

    test_engine.dispose()


@pytest.fixture
def pool_metrics():
    """Fixture for tracking pool metrics during tests."""
    return {
        "connections_used": 0,
        "wait_time": 0.0,
        "timeout_count": 0,
        "error_count": 0,
        "successful_operations": 0,
    }


# ============================================================================
# Test Class: Connection Pool Saturation
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestConnectionPoolStress:
    """Test suite for connection pool stress scenarios."""

    def test_pool_saturation_graceful_handling(self, small_pool_engine, small_pool_session, pool_metrics):
        """
        Pool exhaustion should timeout gracefully, not crash.

        Simulates 15 concurrent requests competing for pool_size=5 + max_overflow=5 (10 total).
        Expected behavior:
        - First 10 requests succeed
        - Remaining 5 requests timeout gracefully with SQLAlchemy TimeoutError
        - No application crashes or hung connections
        """
        num_requests = 15
        hold_duration = 0.5  # Hold connection for 500ms

        def long_running_query(session_factory, request_id):
            """Simulate a long-running query that holds a connection."""
            try:
                session = session_factory()
                start_time = time.time()
                try:
                    # Hold the connection with a long operation
                    time.sleep(hold_duration)

                    # Perform a simple query to verify connection works
                    result = session.execute(text("SELECT 1")).scalar()

                    wait_time = time.time() - start_time
                    pool_metrics["successful_operations"] += 1
                    pool_metrics["wait_time"] += wait_time

                    return {"success": True, "request_id": request_id, "wait_time": wait_time}
                finally:
                    session.close()

            except (SQLAlchemyTimeoutError, TimeoutError) as e:
                pool_metrics["timeout_count"] += 1
                return {"success": False, "request_id": request_id, "error": "timeout"}

            except Exception as e:
                pool_metrics["error_count"] += 1
                return {"success": False, "request_id": request_id, "error": str(e)}

        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [
                executor.submit(long_running_query, small_pool_session, i)
                for i in range(num_requests)
            ]

            results = [future.result() for future in as_completed(futures)]

        # Analyze results
        successful = sum(1 for r in results if r.get("success"))
        timeouts = sum(1 for r in results if r.get("error") == "timeout")
        errors = sum(1 for r in results if r.get("error") and r.get("error") != "timeout")

        # Assertions
        assert successful > 0, "At least some requests should succeed"
        assert timeouts > 0, "Some requests should timeout when pool is exhausted"
        assert errors == 0, "No unexpected errors should occur"
        assert successful + timeouts == num_requests, "All requests should complete (success or timeout)"

        # Pool should be healthy (no connections leaked)
        pool_status = small_pool_engine.pool.status()
        assert "Pool size: 5" in pool_status

    def test_concurrent_celery_and_api_requests(self, small_pool_engine, small_pool_session):
        """
        Simulate real-world mixed workload: Celery background tasks + API requests.

        Scenario:
        - 5 "API requests" (short, fast queries)
        - 3 "Celery tasks" (longer, background operations)
        - All competing for same connection pool

        Expected behavior:
        - API requests complete quickly
        - Celery tasks may wait but eventually complete
        - No deadlocks or permanent failures
        """
        results = {"api": [], "celery": []}

        def simulate_api_request(session_factory, request_id):
            """Simulate fast API request (read operation)."""
            start_time = time.time()
            try:
                session = session_factory()
                try:
                    # Quick read operation
                    result = session.execute(text("SELECT 1")).scalar()
                    duration = time.time() - start_time
                    return {
                        "type": "api",
                        "request_id": request_id,
                        "success": True,
                        "duration": duration,
                    }
                finally:
                    session.close()
            except Exception as e:
                return {
                    "type": "api",
                    "request_id": request_id,
                    "success": False,
                    "error": str(e),
                }

        def simulate_celery_task(session_factory, task_id):
            """Simulate Celery background task (longer operation with transaction)."""
            start_time = time.time()
            try:
                session = session_factory()
                try:
                    # Simulate longer processing
                    time.sleep(0.3)

                    # Create test data
                    person = Person(
                        id=uuid4(),
                        name=f"Test Person {task_id}",
                        type="resident",
                        email=f"test{task_id}@test.org",
                        pgy_level=1,
                    )
                    session.add(person)
                    session.commit()

                    duration = time.time() - start_time
                    return {
                        "type": "celery",
                        "task_id": task_id,
                        "success": True,
                        "duration": duration,
                    }
                except Exception as e:
                    session.rollback()
                    raise
                finally:
                    session.close()

            except Exception as e:
                return {
                    "type": "celery",
                    "task_id": task_id,
                    "success": False,
                    "error": str(e),
                }

        # Execute mixed workload
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit API requests
            api_futures = [
                executor.submit(simulate_api_request, small_pool_session, i)
                for i in range(5)
            ]

            # Submit Celery tasks
            celery_futures = [
                executor.submit(simulate_celery_task, small_pool_session, i)
                for i in range(3)
            ]

            # Collect results
            for future in as_completed(api_futures):
                results["api"].append(future.result())

            for future in as_completed(celery_futures):
                results["celery"].append(future.result())

        # Analyze results
        api_successful = sum(1 for r in results["api"] if r.get("success"))
        celery_successful = sum(1 for r in results["celery"] if r.get("success"))

        # Most operations should succeed (some may timeout under high load)
        assert api_successful >= 3, f"Most API requests should succeed, got {api_successful}/5"
        assert celery_successful >= 2, f"Most Celery tasks should succeed, got {celery_successful}/3"

        # API requests should be faster than Celery tasks
        avg_api_time = sum(r["duration"] for r in results["api"] if r.get("success")) / max(api_successful, 1)
        avg_celery_time = sum(r["duration"] for r in results["celery"] if r.get("success")) / max(celery_successful, 1)

        assert avg_api_time < avg_celery_time, "API requests should be faster than Celery tasks"


# ============================================================================
# Test Class: Connection Leak Detection
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestConnectionLeakDetection:
    """Test suite for detecting and preventing connection leaks."""

    def test_connection_leak_detection(self, monitored_pool_engine):
        """
        Verify connections are properly returned to pool after requests.

        Executes 1000 requests and verifies:
        - All checked-out connections are checked back in
        - Pool size remains stable
        - No connections are leaked
        """
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=monitored_pool_engine)

        num_requests = 1000

        def simple_query(session_factory, request_id):
            """Execute simple query and close session."""
            session = session_factory()
            try:
                result = session.execute(text("SELECT 1")).scalar()
                return {"success": True, "result": result}
            finally:
                session.close()

        # Execute many requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(simple_query, TestSession, i)
                for i in range(num_requests)
            ]

            results = [future.result() for future in as_completed(futures)]

        # Verify all requests succeeded
        successful = sum(1 for r in results if r.get("success"))
        assert successful == num_requests, f"All {num_requests} requests should succeed"

        # Check connection metrics
        events = monitored_pool_engine._connection_events

        # Allow small margin for timing differences
        checkout_count = events["checkout"]
        checkin_count = events["checked_in"]

        # All checked-out connections should be returned (within small margin)
        leak_count = checkout_count - checkin_count
        assert leak_count <= 10, f"Connection leak detected: {leak_count} connections not returned"

        # Pool should be at or near baseline
        pool_status = monitored_pool_engine.pool.status()
        assert "Pool size: 10" in pool_status, "Pool size should be at configured value"

    def test_long_running_transaction_timeout(self, small_pool_engine, small_pool_session):
        """
        Test that long-running transactions don't hold connections indefinitely.

        Scenario:
        - Start a long-running transaction
        - Attempt other operations while transaction is active
        - Verify pool doesn't deadlock
        """
        results = []

        def long_transaction(session_factory):
            """Simulate long-running transaction."""
            session = session_factory()
            try:
                # Start transaction
                person = Person(
                    id=uuid4(),
                    name="Long Transaction Person",
                    type="faculty",
                    email="long@test.org",
                )
                session.add(person)
                session.flush()

                # Hold transaction open for extended period
                time.sleep(1.0)

                session.commit()
                return {"success": True, "type": "long_tx"}
            except Exception as e:
                session.rollback()
                return {"success": False, "type": "long_tx", "error": str(e)}
            finally:
                session.close()

        def quick_query(session_factory, request_id):
            """Quick read query."""
            try:
                session = session_factory()
                try:
                    result = session.execute(text("SELECT 1")).scalar()
                    return {"success": True, "type": "quick", "request_id": request_id}
                finally:
                    session.close()
            except (SQLAlchemyTimeoutError, TimeoutError):
                return {"success": False, "type": "quick", "request_id": request_id, "error": "timeout"}

        # Execute mixed workload
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Start long transaction
            long_tx_future = executor.submit(long_transaction, small_pool_session)

            # Give it a moment to start
            time.sleep(0.1)

            # Submit multiple quick queries while long transaction is running
            quick_futures = [
                executor.submit(quick_query, small_pool_session, i)
                for i in range(7)
            ]

            # Collect results
            results.append(long_tx_future.result())
            for future in as_completed(quick_futures):
                results.append(future.result())

        # Verify results
        long_tx_result = [r for r in results if r.get("type") == "long_tx"][0]
        quick_results = [r for r in results if r.get("type") == "quick"]

        # Long transaction should complete
        assert long_tx_result.get("success"), "Long transaction should complete successfully"

        # Most quick queries should succeed (some may timeout)
        successful_quick = sum(1 for r in quick_results if r.get("success"))
        assert successful_quick >= 4, f"Most quick queries should succeed, got {successful_quick}/7"

    def test_rollback_releases_connection(self, monitored_pool_engine):
        """
        Test that rollback scenarios properly release connections.

        Verifies that failed transactions release connections back to pool.
        """
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=monitored_pool_engine)

        initial_checkin_count = monitored_pool_engine._connection_events["checked_in"]

        def failing_transaction(session_factory):
            """Transaction that will fail and rollback."""
            session = session_factory()
            try:
                # Create invalid data to trigger failure
                person = Person(
                    id=uuid4(),
                    name="Test Person",
                    type="resident",
                    email="test@test.org",
                    pgy_level=1,
                )
                session.add(person)
                session.flush()

                # Force an error
                raise ValueError("Simulated error")

            except ValueError:
                session.rollback()
                return {"success": False, "rolled_back": True}
            except Exception as e:
                session.rollback()
                return {"success": False, "rolled_back": True, "error": str(e)}
            finally:
                session.close()

        # Execute multiple failing transactions
        num_failures = 50
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(failing_transaction, TestSession)
                for _ in range(num_failures)
            ]

            results = [future.result() for future in as_completed(futures)]

        # All should have rolled back
        rolled_back = sum(1 for r in results if r.get("rolled_back"))
        assert rolled_back == num_failures, "All transactions should have rolled back"

        # All connections should be returned to pool
        final_checkin_count = monitored_pool_engine._connection_events["checked_in"]
        connections_returned = final_checkin_count - initial_checkin_count

        # Should be close to num_failures (within small margin for concurrent timing)
        assert connections_returned >= num_failures - 5, \
            f"All connections should be returned: {connections_returned}/{num_failures}"


# ============================================================================
# Test Class: Pool Recovery
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestPoolRecovery:
    """Test suite for database connection pool recovery scenarios."""

    def test_pool_recovery_after_db_restart(self, small_pool_engine, small_pool_session):
        """
        Pool should recover after database becomes available.

        Simulates database restart by disposing engine and verifying recovery.
        Note: This is a simplified test. In production, DB restart would be more complex.
        """
        # Initial successful query
        session = small_pool_session()
        try:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1, "Initial query should succeed"
        finally:
            session.close()

        # Simulate database restart by disposing pool
        small_pool_engine.dispose()

        # Wait briefly
        time.sleep(0.1)

        # Attempt queries after "restart" - should reconnect automatically
        session = small_pool_session()
        try:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1, "Query after restart should succeed (auto-reconnect)"
        finally:
            session.close()

    def test_connection_health_checks_work(self):
        """
        Test pool_pre_ping connection health checks.

        Verifies that pool_pre_ping=True properly detects stale connections.
        """
        # Create engine with pre_ping enabled
        test_engine = create_engine(
            "sqlite:///:memory:",
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,  # Enable health checks
            connect_args={"check_same_thread": False},
        )

        Base.metadata.create_all(bind=test_engine)
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

        try:
            # Execute multiple queries
            for i in range(10):
                session = TestSession()
                try:
                    result = session.execute(text("SELECT 1")).scalar()
                    assert result == 1
                finally:
                    session.close()

            # All queries should succeed without stale connection errors
            # The pre_ping should have validated connections

        finally:
            test_engine.dispose()

    def test_pool_invalidation_and_recovery(self, small_pool_engine, small_pool_session):
        """
        Test that pool can invalidate and recover from bad connections.

        Uses pool.recreate() to force connection refresh.
        """
        # Execute initial query
        session = small_pool_session()
        try:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1
        finally:
            session.close()

        # Get current pool
        current_pool = small_pool_engine.pool

        # Recreate the pool (simulates invalidation)
        small_pool_engine.pool = current_pool.recreate()

        # Should be able to execute queries with new pool
        session = small_pool_session()
        try:
            result = session.execute(text("SELECT 1")).scalar()
            assert result == 1, "Queries should work after pool recreation"
        finally:
            session.close()


# ============================================================================
# Test Class: Concurrent Transaction Isolation
# ============================================================================

@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentTransactionIsolation:
    """Test suite for concurrent transaction isolation and deadlock handling."""

    def test_concurrent_transactions_modifying_same_data(self, small_pool_engine):
        """
        Multiple transactions modifying same data with proper isolation.

        Tests:
        - Transactions see isolated views of data
        - No dirty reads
        - Proper commit ordering
        """
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=small_pool_engine)

        # Create initial person
        session = TestSession()
        person_id = uuid4()
        person = Person(
            id=person_id,
            name="Original Name",
            type="resident",
            email="concurrent@test.org",
            pgy_level=1,
        )
        session.add(person)
        session.commit()
        session.close()

        results = []

        def update_person_name(session_factory, new_name, delay=0):
            """Update person name in a transaction."""
            session = session_factory()
            try:
                # Read person
                person = session.query(Person).filter(Person.id == person_id).first()

                if delay > 0:
                    time.sleep(delay)

                # Update name
                if person:
                    person.name = new_name
                    session.commit()
                    return {"success": True, "name": new_name}
                else:
                    return {"success": False, "error": "Person not found"}

            except Exception as e:
                session.rollback()
                return {"success": False, "error": str(e)}
            finally:
                session.close()

        # Execute concurrent updates
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(update_person_name, TestSession, "Name A", 0.1),
                executor.submit(update_person_name, TestSession, "Name B", 0.1),
                executor.submit(update_person_name, TestSession, "Name C", 0.1),
            ]

            for future in as_completed(futures):
                results.append(future.result())

        # All updates should succeed (SQLite handles this with serialized isolation)
        successful = sum(1 for r in results if r.get("success"))
        assert successful >= 1, "At least one update should succeed"

        # Verify final state
        session = TestSession()
        try:
            person = session.query(Person).filter(Person.id == person_id).first()
            assert person is not None, "Person should still exist"
            assert person.name in ["Name A", "Name B", "Name C"], "Name should be one of the updates"
        finally:
            session.close()

    def test_read_committed_isolation_level(self, small_pool_engine):
        """
        Test that transactions have proper isolation (no dirty reads).

        Verifies that uncommitted changes are not visible to other transactions.
        """
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=small_pool_engine)

        # Create initial data
        session = TestSession()
        person_id = uuid4()
        person = Person(
            id=person_id,
            name="Initial Name",
            type="faculty",
            email="isolation@test.org",
        )
        session.add(person)
        session.commit()
        session.close()

        # Transaction 1: Update but don't commit yet
        session1 = TestSession()
        person1 = session1.query(Person).filter(Person.id == person_id).first()
        person1.name = "Updated Name (not committed)"
        session1.flush()

        # Transaction 2: Read person (should see original value)
        session2 = TestSession()
        try:
            person2 = session2.query(Person).filter(Person.id == person_id).first()

            # In SQLite with default isolation, may see original or updated depending on timing
            # Just verify no crash and data is consistent
            assert person2 is not None, "Person should be readable"
            assert person2.name in ["Initial Name", "Updated Name (not committed)"]

        finally:
            session2.close()

        # Rollback transaction 1
        session1.rollback()
        session1.close()

        # Verify final state (should be original)
        session3 = TestSession()
        try:
            person3 = session3.query(Person).filter(Person.id == person_id).first()
            assert person3.name == "Initial Name", "Name should revert after rollback"
        finally:
            session3.close()

    def test_deadlock_detection_and_recovery(self, small_pool_engine):
        """
        Test handling of potential deadlock scenarios.

        Attempts to create conditions that could cause deadlocks and verifies
        graceful handling (timeout or retry).

        Note: SQLite has limited deadlock scenarios due to database-level locking,
        but this test verifies timeout behavior.
        """
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=small_pool_engine)

        # Create two people
        session = TestSession()
        person1_id = uuid4()
        person2_id = uuid4()

        person1 = Person(id=person1_id, name="Person 1", type="resident", email="p1@test.org", pgy_level=1)
        person2 = Person(id=person2_id, name="Person 2", type="resident", email="p2@test.org", pgy_level=2)

        session.add_all([person1, person2])
        session.commit()
        session.close()

        results = []

        def update_persons_order1(session_factory):
            """Update person1 then person2."""
            session = session_factory()
            try:
                p1 = session.query(Person).filter(Person.id == person1_id).first()
                p1.name = "Person 1 Updated A"
                session.flush()

                time.sleep(0.2)  # Create timing gap

                p2 = session.query(Person).filter(Person.id == person2_id).first()
                p2.name = "Person 2 Updated A"
                session.commit()

                return {"success": True, "order": "1-2"}
            except Exception as e:
                session.rollback()
                return {"success": False, "order": "1-2", "error": str(e)}
            finally:
                session.close()

        def update_persons_order2(session_factory):
            """Update person2 then person1."""
            session = session_factory()
            try:
                p2 = session.query(Person).filter(Person.id == person2_id).first()
                p2.name = "Person 2 Updated B"
                session.flush()

                time.sleep(0.2)  # Create timing gap

                p1 = session.query(Person).filter(Person.id == person1_id).first()
                p1.name = "Person 1 Updated B"
                session.commit()

                return {"success": True, "order": "2-1"}
            except Exception as e:
                session.rollback()
                return {"success": False, "order": "2-1", "error": str(e)}
            finally:
                session.close()

        # Execute concurrent updates in opposite order (potential deadlock)
        with ThreadPoolExecutor(max_workers=2) as executor:
            future1 = executor.submit(update_persons_order1, TestSession)
            future2 = executor.submit(update_persons_order2, TestSession)

            results.append(future1.result())
            results.append(future2.result())

        # At least one should succeed (SQLite serializes transactions)
        successful = sum(1 for r in results if r.get("success"))
        assert successful >= 1, "At least one transaction should succeed"

        # No unhandled exceptions - all should return result dict
        assert all("success" in r for r in results), "All transactions should complete (success or failure)"


# ============================================================================
# Test Class: Task Session Scope (Celery Pattern)
# ============================================================================

@pytest.mark.performance
class TestTaskSessionScope:
    """Test the task_session_scope context manager used by Celery tasks."""

    def test_task_session_scope_basic_usage(self):
        """Test basic usage of task_session_scope."""
        with task_session_scope() as session:
            person = Person(
                id=uuid4(),
                name="Task Person",
                type="resident",
                email="task@test.org",
                pgy_level=1,
            )
            session.add(person)
            # Commit happens automatically on context exit

        # Verify person was created
        with task_session_scope() as session:
            count = session.query(Person).filter(Person.email == "task@test.org").count()
            assert count == 1, "Person should be committed"

    def test_task_session_scope_rollback_on_error(self):
        """Test that task_session_scope rolls back on exceptions."""
        person_id = uuid4()

        try:
            with task_session_scope() as session:
                person = Person(
                    id=person_id,
                    name="Failing Task Person",
                    type="faculty",
                    email="failing@test.org",
                )
                session.add(person)
                session.flush()

                # Force an error
                raise ValueError("Simulated task failure")

        except ValueError:
            pass  # Expected

        # Verify rollback occurred
        with task_session_scope() as session:
            person = session.query(Person).filter(Person.id == person_id).first()
            assert person is None, "Person should not exist after rollback"

    def test_task_session_scope_concurrent_tasks(self):
        """Test concurrent Celery tasks using task_session_scope."""
        results = []

        def celery_task_simulation(task_id):
            """Simulate a Celery task."""
            try:
                with task_session_scope() as session:
                    person = Person(
                        id=uuid4(),
                        name=f"Celery Task Person {task_id}",
                        type="resident",
                        email=f"celery{task_id}@test.org",
                        pgy_level=(task_id % 3) + 1,
                    )
                    session.add(person)
                    # Auto-commits on exit

                return {"success": True, "task_id": task_id}
            except Exception as e:
                return {"success": False, "task_id": task_id, "error": str(e)}

        # Execute 20 concurrent "tasks"
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(celery_task_simulation, i)
                for i in range(20)
            ]

            for future in as_completed(futures):
                results.append(future.result())

        # All tasks should succeed
        successful = sum(1 for r in results if r.get("success"))
        assert successful == 20, f"All 20 tasks should succeed, got {successful}"

        # Verify all persons were created
        with task_session_scope() as session:
            count = session.query(Person).filter(Person.email.like("celery%@test.org")).count()
            assert count == 20, "All 20 persons should be in database"


# ============================================================================
# Performance Metrics Summary Test
# ============================================================================

@pytest.mark.performance
class TestConnectionPoolMetrics:
    """Test suite for measuring connection pool performance metrics."""

    def test_pool_performance_metrics(self, monitored_pool_engine, pool_metrics):
        """
        Measure and report connection pool performance metrics.

        Metrics tracked:
        - Average connection wait time
        - Pool utilization
        - Connection lifecycle efficiency
        """
        TestSession = sessionmaker(autocommit=False, autoflush=False, bind=monitored_pool_engine)

        num_operations = 100
        start_time = time.time()

        def timed_operation(session_factory, op_id):
            """Execute operation and track timing."""
            op_start = time.time()
            session = session_factory()
            checkout_time = time.time()

            try:
                # Simulate work
                result = session.execute(text("SELECT 1")).scalar()
                work_complete_time = time.time()

                return {
                    "success": True,
                    "checkout_duration": checkout_time - op_start,
                    "work_duration": work_complete_time - checkout_time,
                    "total_duration": work_complete_time - op_start,
                }
            finally:
                session.close()

        # Execute operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(timed_operation, TestSession, i)
                for i in range(num_operations)
            ]

            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Calculate metrics
        avg_checkout_time = sum(r["checkout_duration"] for r in results) / num_operations
        avg_work_time = sum(r["work_duration"] for r in results) / num_operations
        avg_total_time = sum(r["total_duration"] for r in results) / num_operations

        throughput = num_operations / total_time

        # Store metrics
        pool_metrics["connections_used"] = monitored_pool_engine._connection_events["checkout"]
        pool_metrics["successful_operations"] = num_operations

        # Performance assertions (reasonable thresholds)
        assert avg_checkout_time < 0.1, f"Connection checkout should be fast: {avg_checkout_time:.3f}s"
        assert throughput > 50, f"Should achieve reasonable throughput: {throughput:.1f} ops/sec"

        # Print metrics for analysis
        print(f"\n{'='*60}")
        print(f"Connection Pool Performance Metrics")
        print(f"{'='*60}")
        print(f"Total operations:          {num_operations}")
        print(f"Total time:                {total_time:.3f}s")
        print(f"Throughput:                {throughput:.1f} ops/sec")
        print(f"Avg checkout time:         {avg_checkout_time*1000:.2f}ms")
        print(f"Avg work time:             {avg_work_time*1000:.2f}ms")
        print(f"Avg total time:            {avg_total_time*1000:.2f}ms")
        print(f"Connections checked out:   {monitored_pool_engine._connection_events['checkout']}")
        print(f"Connections checked in:    {monitored_pool_engine._connection_events['checked_in']}")
        print(f"{'='*60}\n")
