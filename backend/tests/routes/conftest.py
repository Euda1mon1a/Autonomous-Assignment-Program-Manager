"""Route-specific test fixtures."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def db_session():
    """Provide a MagicMock database session for route tests that need it.

    Some tests call internal functions directly (not through HTTP endpoints)
    and need a mock session parameter.
    """
    return MagicMock()
