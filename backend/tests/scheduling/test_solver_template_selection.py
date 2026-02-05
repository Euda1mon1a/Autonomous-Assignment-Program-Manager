"""Tests for solver template selection behavior."""

from types import SimpleNamespace
from datetime import date
from uuid import uuid4

from app.scheduling.solvers import BaseSolver
from app.scheduling.constraints import ConstraintManager, SchedulingContext
from app.scheduling.solvers import CPSATSolver


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


def test_cpsat_allows_templates_requiring_procedure_credential():
    """CP-SAT should consider templates even when they require credentials."""
    resident = SimpleNamespace(id=uuid4())
    block = SimpleNamespace(
        id=uuid4(),
        date=date(2026, 1, 6),
        is_weekend=False,
        time_of_day="AM",
    )
    template = SimpleNamespace(
        id=uuid4(),
        name="Procedure Clinic",
        abbreviation="PROC",
        requires_procedure_credential=True,
    )

    context = SchedulingContext(
        residents=[resident],
        faculty=[],
        blocks=[block],
        templates=[template],
    )

    solver = CPSATSolver(constraint_manager=ConstraintManager.create_minimal())
    result = solver.solve(context)

    assert result.success is True
    assert any(t_id == template.id for _, _, t_id in result.assignments)


def test_cpsat_respects_locked_blocks():
    """CP-SAT should not assign residents into locked blocks."""
    resident = SimpleNamespace(id=uuid4())
    locked_block = SimpleNamespace(
        id=uuid4(),
        date=date(2026, 1, 6),
        is_weekend=False,
        time_of_day="AM",
    )
    unlocked_block = SimpleNamespace(
        id=uuid4(),
        date=date(2026, 1, 7),
        is_weekend=False,
        time_of_day="AM",
    )
    template = SimpleNamespace(
        id=uuid4(),
        name="Clinic",
        abbreviation="CLIN",
        requires_procedure_credential=False,
    )

    context = SchedulingContext(
        residents=[resident],
        faculty=[],
        blocks=[locked_block, unlocked_block],
        templates=[template],
        locked_blocks={(resident.id, locked_block.id)},
    )

    solver = CPSATSolver(constraint_manager=ConstraintManager.create_minimal())
    result = solver.solve(context)

    assert result.success is True
    assigned_block_ids = {block_id for _, block_id, _ in result.assignments}
    assert locked_block.id not in assigned_block_ids
    assert unlocked_block.id in assigned_block_ids
