"""
Minimal conftest for resilience tests.

This avoids importing the full app which has missing dependencies.
"""

import pytest


# Minimal fixtures for resilience tests
@pytest.fixture
def mock_assignments():
    """Create mock assignments for testing."""

    class MockAssignment:
        def __init__(self, person_id, rotation_template_id=None, block_id=0):
            self.person_id = person_id
            self.rotation_template_id = rotation_template_id
            self.block_id = block_id

    return MockAssignment
