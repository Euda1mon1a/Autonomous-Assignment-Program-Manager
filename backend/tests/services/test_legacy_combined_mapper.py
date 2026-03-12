"""Tests for legacy_combined_mapper — pure function, no DB dependency."""

import pytest

from app.services.legacy_combined_mapper import get_canonical_combined_rotation


# ---------------------------------------------------------------------------
# 1. All 8 canonical pairs, primary-first order
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary, expected",
    [
        ("DERM", "NF", "DERM/NF"),
        ("ENDO", "NF", "ENDO/NF"),
        ("CARDIO", "NF", "CARDIO/NF"),
        ("MED", "NF", "MED/NF"),
        ("NICU", "NF", "NICU/NF"),
        ("NEURO", "NF", "NEURO/NF"),
        ("PEDSW", "NF", "PEDSW/NF"),
        ("L&D", "NF", "L&D/NF"),
    ],
    ids=[
        "DERM-primary",
        "ENDO-primary",
        "CARDIO-primary",
        "MED-primary",
        "NICU-primary",
        "NEURO-primary",
        "PEDSW-primary",
        "L&D-primary",
    ],
)
def test_canonical_pairs_primary_first(
    primary: str, secondary: str, expected: str
) -> None:
    assert get_canonical_combined_rotation(primary, secondary) == expected


# ---------------------------------------------------------------------------
# 2. All 8 canonical pairs, secondary-first (swapped) order
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary, expected",
    [
        ("NF", "DERM", "DERM/NF"),
        ("NF", "ENDO", "ENDO/NF"),
        ("NF", "CARDIO", "CARDIO/NF"),
        ("NF", "MED", "MED/NF"),
        ("NF", "NICU", "NICU/NF"),
        ("NF", "NEURO", "NEURO/NF"),
        ("NF", "PEDSW", "PEDSW/NF"),
        ("NF", "L&D", "L&D/NF"),
    ],
    ids=[
        "DERM-swapped",
        "ENDO-swapped",
        "CARDIO-swapped",
        "MED-swapped",
        "NICU-swapped",
        "NEURO-swapped",
        "PEDSW-swapped",
        "L&D-swapped",
    ],
)
def test_canonical_pairs_swapped(primary: str, secondary: str, expected: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) == expected


# ---------------------------------------------------------------------------
# 3. Case insensitivity (lowercase and mixed case)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary, expected",
    [
        ("derm", "nf", "DERM/NF"),
        ("Endo", "Nf", "ENDO/NF"),
        ("cardio", "NF", "CARDIO/NF"),
        ("nf", "med", "MED/NF"),
        ("Nicu", "nF", "NICU/NF"),
        ("neuro", "nf", "NEURO/NF"),
        ("pedsw", "nf", "PEDSW/NF"),
        ("l&d", "nf", "L&D/NF"),
    ],
    ids=[
        "derm-lower",
        "endo-mixed",
        "cardio-lower-NF-upper",
        "nf-lower-med-lower",
        "nicu-mixed",
        "neuro-lower",
        "pedsw-lower",
        "l&d-lower",
    ],
)
def test_case_insensitivity(primary: str, secondary: str, expected: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) == expected


# ---------------------------------------------------------------------------
# 4. Whitespace handling (leading/trailing spaces)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary, expected",
    [
        ("  DERM  ", "  NF  ", "DERM/NF"),
        ("ENDO ", " NF", "ENDO/NF"),
        (" NF ", " CARDIO ", "CARDIO/NF"),
        ("  l&d  ", "  nf  ", "L&D/NF"),
    ],
    ids=[
        "derm-spaces-both",
        "endo-trailing-leading",
        "cardio-swapped-spaces",
        "l&d-spaces-lower",
    ],
)
def test_whitespace_handling(primary: str, secondary: str, expected: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) == expected


# ---------------------------------------------------------------------------
# 5. PEDS WARD variations (PEDSW, PEDS-W, PEDS WARD) — both orders
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary, expected",
    [
        ("PEDS WARD", "NF", "PEDSW/NF"),
        ("PEDSW", "NF", "PEDSW/NF"),
        ("PEDS-W", "NF", "PEDSW/NF"),
        ("NF", "PEDS WARD", "PEDSW/NF"),
        ("NF", "PEDSW", "PEDSW/NF"),
        ("NF", "PEDS-W", "PEDSW/NF"),
        # Case-insensitive variants
        ("peds ward", "nf", "PEDSW/NF"),
        ("peds-w", "nf", "PEDSW/NF"),
        ("pedsw", "nf", "PEDSW/NF"),
    ],
    ids=[
        "PEDS-WARD-primary",
        "PEDSW-primary",
        "PEDS-W-primary",
        "PEDS-WARD-swapped",
        "PEDSW-swapped",
        "PEDS-W-swapped",
        "peds-ward-lower",
        "peds-w-lower",
        "pedsw-lower",
    ],
)
def test_peds_ward_variations(primary: str, secondary: str, expected: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) == expected


# ---------------------------------------------------------------------------
# 6. L&D variations (L&D, L AND D) — both orders
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary, expected",
    [
        ("L&D", "NF", "L&D/NF"),
        ("L AND D", "NF", "L&D/NF"),
        ("NF", "L&D", "L&D/NF"),
        ("NF", "L AND D", "L&D/NF"),
        # Case-insensitive variants
        ("l and d", "nf", "L&D/NF"),
        ("l&d", "nf", "L&D/NF"),
    ],
    ids=[
        "L&D-primary",
        "L-AND-D-primary",
        "L&D-swapped",
        "L-AND-D-swapped",
        "l-and-d-lower",
        "l&d-lower",
    ],
)
def test_ld_variations(primary: str, secondary: str, expected: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) == expected


# ---------------------------------------------------------------------------
# 7. Empty / None-like inputs return None
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary",
    [
        ("", "NF"),
        ("DERM", ""),
        ("", ""),
        (None, "NF"),  # type: ignore[arg-type]
        ("DERM", None),  # type: ignore[arg-type]
        (None, None),  # type: ignore[arg-type]
    ],
    ids=[
        "empty-primary",
        "empty-secondary",
        "both-empty",
        "none-primary",
        "none-secondary",
        "both-none",
    ],
)
def test_empty_and_none_inputs_return_none(primary: str, secondary: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) is None


# ---------------------------------------------------------------------------
# 8. Unknown rotations return None
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary",
    [
        ("SURGERY", "NF"),
        ("NF", "SURGERY"),
        ("DERM", "ENDO"),
        ("ORTHO", "PSYCH"),
        ("DERM", "DERM"),
        ("NF", "NF"),
        ("RANDOM", "STUFF"),
    ],
    ids=[
        "surgery-nf",
        "nf-surgery",
        "derm-endo-no-nf",
        "ortho-psych",
        "derm-derm",
        "nf-nf",
        "random-stuff",
    ],
)
def test_unknown_rotations_return_none(primary: str, secondary: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) is None


# ---------------------------------------------------------------------------
# 9. Partial / substring matches (e.g., "ENDOCRINE" contains "ENDO")
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "primary, secondary, expected",
    [
        ("ENDOCRINE", "NF", "ENDO/NF"),
        ("DERMATOLOGY", "NF", "DERM/NF"),
        ("CARDIOLOGY", "NF", "CARDIO/NF"),
        ("MEDICINE", "NF", "MED/NF"),
        ("NEUROLOGY", "NF", "NEURO/NF"),
        ("NF", "ENDOCRINE", "ENDO/NF"),
        ("NF", "DERMATOLOGY", "DERM/NF"),
        ("NF", "CARDIOLOGY", "CARDIO/NF"),
    ],
    ids=[
        "endocrine-partial",
        "dermatology-partial",
        "cardiology-partial",
        "medicine-partial",
        "neurology-partial",
        "endocrine-swapped",
        "dermatology-swapped",
        "cardiology-swapped",
    ],
)
def test_partial_substring_matches(primary: str, secondary: str, expected: str) -> None:
    assert get_canonical_combined_rotation(primary, secondary) == expected
