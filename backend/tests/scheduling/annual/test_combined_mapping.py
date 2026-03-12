"""Tests for ARO_COMBINED_TEMPLATE_MAP completeness and consistency.

Validates that every combined rotation in PGY_ROTATIONS has a mapping
and that the map's abbreviations are well-formed.
"""

from __future__ import annotations

import pytest

from app.scheduling.annual.pgy_config import (
    ARO_COMBINED_TEMPLATE_MAP,
    PGY_ROTATIONS,
)


class TestCombinedMappingCompleteness:
    """Every is_combined=True rotation should appear in ARO_COMBINED_TEMPLATE_MAP."""

    def test_all_combined_rotations_have_mapping(self):
        """Each combined rotation across all PGY levels must be in the map."""
        missing = []
        for pgy, rotations in PGY_ROTATIONS.items():
            for rot in rotations:
                if rot.is_combined and rot.name not in ARO_COMBINED_TEMPLATE_MAP:
                    missing.append(f"PGY-{pgy}: {rot.name}")

        assert missing == [], (
            f"Combined rotations missing from ARO_COMBINED_TEMPLATE_MAP: {missing}"
        )

    def test_map_keys_match_combined_rotation_names(self):
        """ARO_COMBINED_TEMPLATE_MAP keys should all be valid combined rotation names."""
        combined_names = {
            rot.name
            for rots in PGY_ROTATIONS.values()
            for rot in rots
            if rot.is_combined
        }

        extra_keys = set(ARO_COMBINED_TEMPLATE_MAP.keys()) - combined_names
        assert extra_keys == set(), (
            f"ARO_COMBINED_TEMPLATE_MAP has keys not in PGY_ROTATIONS: {extra_keys}"
        )


class TestCombinedMappingFormat:
    """Validate the structure of each mapping entry."""

    def test_all_entries_are_tuples(self):
        """Each value must be a (str, str|None) tuple."""
        for name, mapping in ARO_COMBINED_TEMPLATE_MAP.items():
            assert isinstance(mapping, tuple), f"{name}: value is not a tuple"
            assert len(mapping) == 2, f"{name}: tuple must have exactly 2 elements"
            primary, secondary = mapping
            assert isinstance(primary, str), f"{name}: primary must be a string"
            assert secondary is None or isinstance(secondary, str), (
                f"{name}: secondary must be str or None"
            )

    def test_primary_abbreviations_non_empty(self):
        """Primary abbreviation must be non-empty."""
        for name, (primary, _) in ARO_COMBINED_TEMPLATE_MAP.items():
            assert primary.strip(), f"{name}: primary abbreviation is empty"

    def test_combined_rotation_halves_match(self):
        """Combined rotation first_half/second_half should be set for all combined rotations."""
        for pgy, rotations in PGY_ROTATIONS.items():
            for rot in rotations:
                if rot.is_combined:
                    assert rot.first_half is not None, (
                        f"PGY-{pgy} {rot.name}: first_half is None"
                    )
                    assert rot.second_half is not None, (
                        f"PGY-{pgy} {rot.name}: second_half is None"
                    )
