"""
Tests for solver control module.

Comprehensive test suite for SolverControl class,
covering abort signaling, progress tracking, and graceful shutdown.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.scheduling.solver_control import SolverControl


@pytest.fixture
def mock_redis():
    """Create mock Redis client."""
    redis_mock = MagicMock()
    redis_mock.setex.return_value = True
    redis_mock.get.return_value = None
    redis_mock.delete.return_value = 1
    return redis_mock


class TestSolverControl:
    """Test suite for SolverControl class."""

    def test_request_abort_sets_abort_flag(self, mock_redis):
        """Test requesting abort sets Redis flag."""
        # Arrange
        run_id = "run-123"
        reason = "timeout exceeded"
        requested_by = "admin"

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            result = SolverControl.request_abort(run_id, reason, requested_by)

            # Assert
            assert result is True
            mock_redis.setex.assert_called_once()

            # Verify key format
            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            assert key == f"{SolverControl.ABORT_KEY_PREFIX}{run_id}"

    def test_request_abort_stores_metadata(self, mock_redis):
        """Test abort request stores reason and requester."""
        # Arrange
        run_id = "run-456"
        reason = "user cancellation"
        requested_by = "user-123"

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            SolverControl.request_abort(run_id, reason, requested_by)

            # Assert
            call_args = mock_redis.setex.call_args
            stored_data = call_args[0][2]  # Third argument is the value

            data = json.loads(stored_data)
            assert data["reason"] == reason
            assert data["requested_by"] == requested_by
            assert "requested_at" in data

    def test_request_abort_uses_default_values(self, mock_redis):
        """Test abort request uses default reason and requester."""
        # Arrange
        run_id = "run-789"

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            SolverControl.request_abort(run_id)

            # Assert
            call_args = mock_redis.setex.call_args
            stored_data = call_args[0][2]

            data = json.loads(stored_data)
            assert data["reason"] == "operator request"
            assert data["requested_by"] == "system"

    def test_request_abort_sets_ttl(self, mock_redis):
        """Test abort request sets appropriate TTL."""
        # Arrange
        run_id = "run-999"

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            SolverControl.request_abort(run_id)

            # Assert
            call_args = mock_redis.setex.call_args
            ttl = call_args[0][1]  # Second argument is the TTL
            assert ttl == SolverControl.ABORT_TTL_SECONDS

    def test_should_abort_returns_none_when_no_flag(self, mock_redis):
        """Test should_abort returns None when no abort flag is set."""
        # Arrange
        run_id = "run-101"
        mock_redis.get.return_value = None

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            result = SolverControl.should_abort(run_id)

            # Assert
            assert result is None
            mock_redis.get.assert_called_once()

    def test_should_abort_returns_reason_when_flag_set(self, mock_redis):
        """Test should_abort returns reason when abort flag is set."""
        # Arrange
        run_id = "run-202"
        abort_data = {
            "reason": "solver timeout",
            "requested_by": "system",
            "requested_at": datetime.utcnow().isoformat(),
        }
        mock_redis.get.return_value = json.dumps(abort_data)

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            result = SolverControl.should_abort(run_id)

            # Assert
            assert result == "solver timeout"

    def test_update_progress_stores_progress_data(self, mock_redis):
        """Test updating progress stores iteration and score."""
        # Arrange
        run_id = "run-303"
        iteration = 100
        score = 0.85

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            SolverControl.update_progress(run_id, iteration, score)

            # Assert
            mock_redis.setex.assert_called_once()

            call_args = mock_redis.setex.call_args
            key = call_args[0][0]
            stored_data = call_args[0][2]

            assert key == f"{SolverControl.PROGRESS_KEY_PREFIX}{run_id}"

            data = json.loads(stored_data)
            assert data["iteration"] == iteration
            assert data["score"] == score
            assert "updated_at" in data

    def test_get_progress_returns_none_when_no_data(self, mock_redis):
        """Test get_progress returns None when no progress data exists."""
        # Arrange
        run_id = "run-404"
        mock_redis.get.return_value = None

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            result = SolverControl.get_progress(run_id)

            # Assert
            assert result is None

    def test_get_progress_returns_progress_data(self, mock_redis):
        """Test get_progress returns stored progress data."""
        # Arrange
        run_id = "run-505"
        progress_data = {
            "iteration": 500,
            "score": 0.92,
            "updated_at": datetime.utcnow().isoformat(),
        }
        mock_redis.get.return_value = json.dumps(progress_data)

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            result = SolverControl.get_progress(run_id)

            # Assert
            assert result is not None
            assert result["iteration"] == 500
            assert result["score"] == 0.92

    def test_clear_abort_removes_flag(self, mock_redis):
        """Test clearing abort flag removes it from Redis."""
        # Arrange
        run_id = "run-606"

        with patch("app.scheduling.solver_control._get_redis_client", return_value=mock_redis):
            # Act
            SolverControl.clear_abort(run_id)

            # Assert
            mock_redis.delete.assert_called_once()

            call_args = mock_redis.delete.call_args
            key = call_args[0][0]
            assert key == f"{SolverControl.ABORT_KEY_PREFIX}{run_id}"


class TestSolverControlKeyFormats:
    """Test suite for Redis key formatting."""

    def test_abort_key_format(self):
        """Test abort key has correct format."""
        # Arrange
        run_id = "test-run"

        # Act
        key = f"{SolverControl.ABORT_KEY_PREFIX}{run_id}"

        # Assert
        assert key == "solver:abort:test-run"
        assert key.startswith("solver:abort:")

    def test_progress_key_format(self):
        """Test progress key has correct format."""
        # Arrange
        run_id = "test-run"

        # Act
        key = f"{SolverControl.PROGRESS_KEY_PREFIX}{run_id}"

        # Assert
        assert key == "solver:progress:test-run"
        assert key.startswith("solver:progress:")

    def test_result_key_format(self):
        """Test result key has correct format."""
        # Arrange
        run_id = "test-run"

        # Act
        key = f"{SolverControl.RESULT_KEY_PREFIX}{run_id}"

        # Assert
        assert key == "solver:result:test-run"
        assert key.startswith("solver:result:")
