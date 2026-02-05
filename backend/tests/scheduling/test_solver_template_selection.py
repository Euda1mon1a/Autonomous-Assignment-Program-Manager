"""Tests for solver template selection behavior."""

from types import SimpleNamespace

from app.scheduling.solvers import BaseSolver


class _DummySolver(BaseSolver):
    """Concrete solver for testing BaseSolver helpers."""

    def solve(self, context, existing_assignments=None):  # pragma: no cover - unused
        raise NotImplementedError


def test_select_template_does_not_filter_requires_procedure_credential():
    """Templates requiring procedure credentials are still eligible for residents."""
    solver = _DummySolver()
    resident = SimpleNamespace()
    templates = [
        SimpleNamespace(requires_procedure_credential=True),
        SimpleNamespace(requires_procedure_credential=False),
    ]

    selected = solver._select_template(resident, templates)

    assert selected is templates[0]


def test_select_template_returns_none_for_empty_list():
    """No templates yields None."""
    solver = _DummySolver()
    resident = SimpleNamespace()

    assert solver._select_template(resident, []) is None
