"""PGY-level rotation requirements for the Annual Rotation Optimizer.

Static configuration encoding rotation assignments, block eligibility,
sequencing rules, and capacity limits per PGY level for AY 2026-27.

Reference: docs/architecture/aro/PGY_ROTATION_CONFIG.md (gitignored, local only)
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Rotation:
    """A rotation available to a specific PGY level."""

    name: str
    leave_eligible: bool
    allowed_blocks: frozenset[int] | None = None  # None = all blocks
    blocked_blocks: frozenset[int] | None = None  # None = no blocks restricted
    is_combined: bool = False  # True = half-block split (two rows with block_half=1,2)
    first_half: str | None = None  # For combined rotations: first 14 days
    second_half: str | None = None  # For combined rotations: days 15-28


# ── PGY-1 Rotations (12 total) ──────────────────────────────────────────────

PGY1_ROTATIONS = [
    # Leave-eligible
    Rotation("MSK-Select", leave_eligible=True),
    Rotation("TAMC L+D", leave_eligible=True, blocked_blocks=frozenset({1, 2})),
    Rotation("Procedures", leave_eligible=True),
    Rotation("Peds Clinic", leave_eligible=True),
    Rotation("FMC", leave_eligible=True),
    Rotation("NBN", leave_eligible=True),
    # Non-leave-eligible
    Rotation("ICU", leave_eligible=False),
    Rotation("FMIT1", leave_eligible=False),
    Rotation("IM", leave_eligible=False),
    Rotation("Kap L+D", leave_eligible=False),
    Rotation(
        "[Peds NF + Peds Ward]",
        leave_eligible=False,
        allowed_blocks=frozenset({7, 9, 10, 11, 12, 13}),
        is_combined=True,
        first_half="Peds NF",
        second_half="Peds Ward",
    ),
    Rotation(
        "[FMIT 2 + NF]",
        leave_eligible=False,
        is_combined=True,
        first_half="FMIT 2",
        second_half="NF",
    ),
]

# ── PGY-2 Rotations (13 total) ──────────────────────────────────────────────

PGY2_ROTATIONS = [
    # Leave-eligible
    Rotation("ELE1", leave_eligible=True),
    Rotation("ELE2", leave_eligible=True),
    Rotation("FMC", leave_eligible=True),
    Rotation("Gyn Clinic", leave_eligible=True, blocked_blocks=frozenset({1, 2})),
    Rotation("Peds Sub", leave_eligible=True),
    Rotation("SM", leave_eligible=True),
    # Non-leave-eligible
    Rotation(
        "[NF + Card]",
        leave_eligible=False,
        is_combined=True,
        first_half="NF",
        second_half="Cardiology",
    ),
    Rotation("L+D NF", leave_eligible=False, blocked_blocks=frozenset({1, 2})),
    Rotation("FMIT 1", leave_eligible=False),
    Rotation("FMIT 2", leave_eligible=False),
    Rotation("Surg Exp", leave_eligible=False),
    Rotation(
        "[Derm + NF]",
        leave_eligible=False,
        is_combined=True,
        first_half="Dermatology",
        second_half="NF",
    ),
    Rotation("EM", leave_eligible=False),
]

# ── PGY-3 Rotations (12 total) ──────────────────────────────────────────────

PGY3_ROTATIONS = [
    # Leave-eligible
    Rotation("Peds EM", leave_eligible=True),
    Rotation("FMC", leave_eligible=True),
    Rotation("Select Med", leave_eligible=True),
    Rotation("Geriatrics", leave_eligible=True),
    Rotation("Elective", leave_eligible=True),
    # Non-leave-eligible
    Rotation(
        "[NF + NICU]",
        leave_eligible=False,
        is_combined=True,
        first_half="NF",
        second_half="NICU",
    ),
    Rotation("FMIT 1", leave_eligible=False),
    Rotation("FMIT2", leave_eligible=False),
    Rotation("Hilo", leave_eligible=False),
    Rotation("Japan", leave_eligible=False),
    Rotation(
        "[PSYCH + NF]",
        leave_eligible=False,
        allowed_blocks=frozenset(range(4, 13)),  # blocks 4-12 only
        is_combined=True,
        first_half="Psychiatry",
        second_half="NF",
    ),
    Rotation("EM", leave_eligible=False),
]

# ── Aggregated config ────────────────────────────────────────────────────────

PGY_ROTATIONS: dict[int, list[Rotation]] = {
    1: PGY1_ROTATIONS,
    2: PGY2_ROTATIONS,
    3: PGY3_ROTATIONS,
}

# Fixed block assignments (not solver variables)
FIXED_ASSIGNMENTS: dict[int, dict[int, str]] = {
    1: {1: "FMO"},  # PGY-1 Block 1 = Family Medicine Orientation
    3: {13: "Military"},  # PGY-3 Block 13 = Military Rotation
}

# Sequencing rules: (predecessor, successor) — successor must be in a later block
SEQUENCING_RULES: dict[int, list[tuple[str, str]]] = {
    1: [("TAMC L+D", "Kap L+D")],  # PGY-1: Kap L+D after TAMC L+D
}

# Capacity overrides (max residents per rotation per block, cross-PGY)
# Default is 1 per rotation per block (across all PGY levels sharing that name)
CAPACITY_OVERRIDES: dict[str, int] = {
    # Canonical group names (used by solver capacity constraint)
    "FMIT": 3,
    "FMIT2_canonical": 3,
    # Original names (used by get_capacity for direct lookups)
    "FMIT1": 3,
    "FMIT 1": 3,
    "FMIT 2": 3,
    "FMIT2": 3,
    "[FMIT 2 + NF]": 3,
    "FMC": 6,
    "ELE1": 6,
    "ELE2": 6,
    "Elective": 6,
    "SM": 1,
    "MSK-Select": 1,
}


def get_eligible_blocks(rotation: Rotation, pgy: int) -> set[int]:
    """Return the set of blocks where this rotation can be assigned.

    Considers allowed_blocks, blocked_blocks, and fixed-assignment blocks.
    Block 0 is always excluded (orientation only).
    """
    fixed = FIXED_ASSIGNMENTS.get(pgy, {})

    if pgy == 1:
        # PGY-1: blocks 2-13 (block 1 = FMO)
        all_blocks = set(range(2, 14))
    elif pgy == 2:
        # PGY-2: blocks 1-13
        all_blocks = set(range(1, 14))
    elif pgy == 3:
        # PGY-3: blocks 1-12 (block 13 = Military)
        all_blocks = set(range(1, 13))
    else:
        all_blocks = set(range(1, 14))

    # Remove fixed-assignment blocks
    for block_num in fixed:
        all_blocks.discard(block_num)

    if rotation.allowed_blocks is not None:
        return all_blocks & set(rotation.allowed_blocks)
    if rotation.blocked_blocks is not None:
        return all_blocks - set(rotation.blocked_blocks)
    return all_blocks


# Canonical names for capacity grouping (aliases → single pool)
CAPACITY_CANONICAL: dict[str, str] = {
    "FMIT1": "FMIT",
    "FMIT 1": "FMIT",
    "FMIT 2": "FMIT2_canonical",
    "FMIT2": "FMIT2_canonical",
    "[FMIT 2 + NF]": "FMIT2_canonical",
}


def canonical_capacity_name(rotation_name: str) -> str:
    """Return the canonical capacity group name for a rotation."""
    return CAPACITY_CANONICAL.get(rotation_name, rotation_name)


def get_capacity(rotation_name: str) -> int:
    """Return max residents per block for this rotation."""
    return CAPACITY_OVERRIDES.get(rotation_name, 1)


# ── ARO Combined Template Map ──────────────────────────────────────────────
# Maps ARO solver combined rotation names → DB rotation template abbreviations.
#
# Format: ARO_name → (primary_template_abbrev, secondary_template_abbrev | None)
#   - None = combined template handles the split internally via NF_COMBINED_ACTIVITY_MAP
#     (the template encodes both halves, e.g. NF-CARDIO = NF wk1-2 + CARDS wk3-4)
#   - str  = two separate templates; written as two BlockAssignment rows
#     with block_half=1 and block_half=2
ARO_COMBINED_TEMPLATE_MAP: dict[str, tuple[str, str | None]] = {
    # PGY-1
    "[Peds NF + Peds Ward]": (
        "NF-PEDS-PG",
        None,
    ),  # NF-first: NF wk1-2, Peds Ward wk3-4
    "[FMIT 2 + NF]": ("FMIT-PGY1", "NF-AM"),  # Two-template split
    # PGY-2
    "[NF + Card]": ("NF-CARDIO", None),  # NF-first: NF wk1-2, Cardiology wk3-4
    "[Derm + NF]": ("DERM", "NF-AM"),  # Two-template split: Derm wk1-2, NF wk3-4
    # PGY-3
    "[NF + NICU]": ("NF-NICU-PG", None),  # NF-first: NF wk1-2, NICU wk3-4
    "[PSYCH + NF]": ("PSYCH", "NF-AM"),  # Two-template split
}
