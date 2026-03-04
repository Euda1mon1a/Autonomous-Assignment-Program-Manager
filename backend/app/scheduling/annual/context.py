"""AnnualContext — data container for the Annual Rotation Optimizer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from app.scheduling.annual.pgy_config import (
    CAPACITY_OVERRIDES,
    FIXED_ASSIGNMENTS,
    PGY_ROTATIONS,
    SEQUENCING_RULES,
    Rotation,
    get_capacity,
    get_eligible_blocks,
)
from app.utils.academic_blocks import BlockDates, get_all_block_dates


@dataclass(frozen=True)
class LeaveRequest:
    """A parsed leave request mapped to block(s)."""

    person_id: UUID
    resident_name: str
    pgy: int
    start_date: date
    end_date: date
    blocks: list[int]  # Block numbers this leave touches (excluding Block 0)
    raw_text: str = ""


@dataclass
class AnnualContext:
    """All data needed for the annual rotation CP-SAT solver."""

    academic_year: int

    # Block calendar (blocks 1-13 only; Block 0 excluded from solver)
    blocks: list[BlockDates] = field(default_factory=list)

    # Residents grouped by PGY
    residents_by_pgy: dict[int, list[ResidentInfo]] = field(default_factory=dict)

    # Flat list of all residents with indices
    all_residents: list[ResidentInfo] = field(default_factory=list)
    resident_idx: dict[UUID, int] = field(default_factory=dict)

    # Rotation config per PGY
    rotations_by_pgy: dict[int, list[Rotation]] = field(default_factory=dict)

    # Leave requests
    leave_requests: list[LeaveRequest] = field(default_factory=list)

    # Precomputed: (resident_global_idx, block_number) -> list of LeaveRequest
    leave_by_resident_block: dict[tuple[int, int], list[LeaveRequest]] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not self.blocks:
            # Exclude Block 0 — orientation only, no rotation assignment
            self.blocks = [
                b for b in get_all_block_dates(self.academic_year) if b.block_number > 0
            ]
        if not self.rotations_by_pgy:
            self.rotations_by_pgy = dict(PGY_ROTATIONS)

    def build_indices(self) -> None:
        """Build lookup indices after residents and leave are populated."""
        # Flat resident list with global indices
        self.all_residents = []
        self.resident_idx = {}
        for pgy in sorted(self.residents_by_pgy.keys()):
            for r in self.residents_by_pgy[pgy]:
                idx = len(self.all_residents)
                self.all_residents.append(r)
                self.resident_idx[r.person_id] = idx

        # Leave by (resident_idx, block)
        self.leave_by_resident_block = {}
        for lr in self.leave_requests:
            r_idx = self.resident_idx.get(lr.person_id)
            if r_idx is None:
                continue
            for b in lr.blocks:
                key = (r_idx, b)
                self.leave_by_resident_block.setdefault(key, []).append(lr)

    @property
    def block_numbers(self) -> list[int]:
        return [b.block_number for b in self.blocks]


@dataclass(frozen=True)
class ResidentInfo:
    """Lightweight resident data for the optimizer."""

    person_id: UUID
    name: str  # Display name (last name or synthetic ID)
    pgy: int


def map_leave_to_blocks(
    start_date: date,
    end_date: date,
    blocks: list[BlockDates],
) -> list[int]:
    """Map a leave date range to the block numbers it touches.

    Uses standard overlap detection: start_A <= end_B AND end_A >= start_B.
    Block 0 is excluded (handled by the blocks list passed in).
    """
    touched = []
    for block in blocks:
        if start_date <= block.end_date and end_date >= block.start_date:
            touched.append(block.block_number)
    return touched
