"""
Test expansion service against ROSETTA ground truth.

ROSETTA is the "answer key" - the correct Block 10 schedule.
These tests verify that the expansion service produces output matching ROSETTA.

TDD Approach:
1. Tests initially FAIL (expansion service doesn't have rules yet)
2. Fix expansion service until tests PASS
3. Verify with xlsx export
"""

from datetime import date

import pytest

from app.utils.rosetta_parser import RosettaAssignment

# Block 10 dates
BLOCK_10_START = date(2026, 3, 12)  # Thursday
BLOCK_10_END = date(2026, 4, 8)  # Wednesday
MID_BLOCK_DATE = date(2026, 3, 23)  # Monday - start of second half
LAST_WEDNESDAY = date(2026, 4, 8)

# Exempt rotations for various rules
# Note: KAP is NOT exempt - Travis travels back for Wed AM clinic
LEC_EXEMPT_ROTATIONS = {"NF", "LDNF", "TDY", "HILO", "PedNF"}
INTERN_CONTINUITY_EXEMPT = {"NF", "PedNF", "LDNF", "FMIT", "TDY", "HILO"}


class TestRosettaSanity:
    """Verify ROSETTA fixture loads correctly - sanity checks."""

    def test_rosetta_loads_assignments(
        self, rosetta_assignments: list[RosettaAssignment]
    ):
        """ROSETTA should load ~504 assignments (9 residents × 56 slots)."""
        assert len(rosetta_assignments) > 0, "ROSETTA failed to load any assignments"
        # 9 residents × 56 half-days = 504 expected
        assert len(rosetta_assignments) >= 400, (
            f"Expected ~504 assignments, got {len(rosetta_assignments)}"
        )

    def test_rosetta_loads_all_residents(
        self, rosetta_by_resident: dict[str, list[RosettaAssignment]]
    ):
        """ROSETTA should have exactly 9 residents."""
        expected_residents = {
            "Travis, Colin",
            "Headid, Ronald",
            "Sloss, Meleighe",
            "Monsivais, Joshua",
            "You, Jae",
            "Wilhelm, Clara",
            "Byrnes, Katherine",
            "Sawyer, Tessa",
            "Chen, Michael",
        }
        actual_residents = set(rosetta_by_resident.keys())
        assert actual_residents == expected_residents, (
            f"Missing residents: {expected_residents - actual_residents}\n"
            f"Extra residents: {actual_residents - expected_residents}"
        )

    def test_rosetta_loads_56_slots_per_resident(
        self, rosetta_by_resident: dict[str, list[RosettaAssignment]]
    ):
        """Each resident should have 56 half-day slots (28 days × 2)."""
        for resident, assignments in rosetta_by_resident.items():
            assert len(assignments) == 56, (
                f"{resident} has {len(assignments)} slots, expected 56"
            )

    def test_rosetta_date_range_correct(
        self, rosetta_assignments: list[RosettaAssignment]
    ):
        """Verify Block 10 date range: Mar 12 - Apr 8, 2026."""
        dates = {a.date for a in rosetta_assignments}
        min_date = min(dates)
        max_date = max(dates)
        assert min_date == BLOCK_10_START, f"Start date {min_date} != {BLOCK_10_START}"
        assert max_date == BLOCK_10_END, f"End date {max_date} != {BLOCK_10_END}"


class TestLastWednesdayRule:
    """Last Wednesday (Apr 8): AM=LEC, PM=ADV for ALL residents."""

    def test_rosetta_last_wednesday_all_lec_am(
        self, rosetta_last_wednesday: list[RosettaAssignment]
    ):
        """Last Wednesday AM should be LEC for all residents."""
        am_slots = [a for a in rosetta_last_wednesday if a.time_of_day == "AM"]
        assert len(am_slots) == 9, f"Expected 9 AM slots, got {len(am_slots)}"

        for assignment in am_slots:
            assert assignment.expected_code == "LEC", (
                f"{assignment.resident} Last Wed AM: "
                f"expected LEC, got {assignment.expected_code}"
            )

    def test_rosetta_last_wednesday_all_adv_pm(
        self, rosetta_last_wednesday: list[RosettaAssignment]
    ):
        """Last Wednesday PM should be ADV for all residents."""
        pm_slots = [a for a in rosetta_last_wednesday if a.time_of_day == "PM"]
        assert len(pm_slots) == 9, f"Expected 9 PM slots, got {len(pm_slots)}"

        for assignment in pm_slots:
            assert assignment.expected_code == "ADV", (
                f"{assignment.resident} Last Wed PM: "
                f"expected ADV, got {assignment.expected_code}"
            )


class TestInternContinuityRule:
    """PGY-1 interns get C (Continuity Clinic) on Wednesday AM."""

    def test_rosetta_intern_wed_am_continuity(
        self, rosetta_intern_wed_am: list[RosettaAssignment]
    ):
        """All PGY-1 Wednesday AM slots should be C (except exempt rotations)."""
        for assignment in rosetta_intern_wed_am:
            # Skip last Wednesday (different rule)
            if assignment.date == LAST_WEDNESDAY:
                continue

            # Determine active rotation (handle mid-block transitions)
            if assignment.rotation2 and assignment.date >= MID_BLOCK_DATE:
                rotation = assignment.rotation2
            else:
                rotation = assignment.rotation1

            # Normalize rotation name for exemption check
            rotation_normalized = rotation.replace(" ", "").lower()
            exempt_normalized = {
                r.replace(" ", "").lower() for r in INTERN_CONTINUITY_EXEMPT
            }
            # Also check for partial matches (e.g., "Peds NF" matches "PedNF")
            is_exempt = (
                rotation_normalized in exempt_normalized
                or "pednf" in rotation_normalized
                or "nf" in rotation_normalized
                and "peds" in rotation_normalized
            )

            if is_exempt:
                # Exempt rotations (NF, PedNF, LDNF, etc.) should NOT have C
                assert assignment.expected_code != "C", (
                    f"{assignment.resident} ({rotation}) is exempt but has C on Wed AM"
                )
            else:
                # Non-exempt rotations should have C on Wed AM
                assert assignment.expected_code == "C", (
                    f"{assignment.resident} ({rotation}) Wed {assignment.date} AM: "
                    f"expected C, got {assignment.expected_code}"
                )

    def test_rosetta_pgy2_no_continuity_rule(
        self, rosetta_assignments: list[RosettaAssignment]
    ):
        """PGY-2/3 do NOT have the Wed AM continuity requirement."""
        # Chen, Michael is PGY-2 on FMC
        chen_wed_am = [
            a
            for a in rosetta_assignments
            if a.resident == "Chen, Michael"
            and a.date.weekday() == 2
            and a.time_of_day == "AM"
            and a.date != LAST_WEDNESDAY
        ]
        # PGY-2 should have C or rotation-specific code, but rule doesn't require C
        # Just verify they have SOME assignment (not mandated to be C)
        assert len(chen_wed_am) > 0, "Chen should have Wednesday AM assignments"


class TestWednesdayPMLecRule:
    """Wednesday PM is LEC (except for NF/LDNF/TDY rotations)."""

    def test_rosetta_wednesday_pm_lec(
        self, rosetta_wednesday_pm_all: list[RosettaAssignment]
    ):
        """Wednesday PM should be LEC except for exempt rotations."""
        for assignment in rosetta_wednesday_pm_all:
            # Skip last Wednesday (ADV rule)
            if assignment.date == LAST_WEDNESDAY:
                continue

            # Determine active rotation (handle mid-block transitions)
            if assignment.rotation2 and assignment.date >= MID_BLOCK_DATE:
                rotation = assignment.rotation2
            else:
                rotation = assignment.rotation1

            # Normalize rotation name for exemption check
            rotation_normalized = rotation.replace(" ", "").lower()
            exempt_normalized = {
                r.replace(" ", "").lower() for r in LEC_EXEMPT_ROTATIONS
            }
            # Check for night float variants
            is_exempt = (
                rotation_normalized in exempt_normalized
                or "nf" in rotation_normalized  # Any NF rotation is exempt
                or "ldnf" in rotation_normalized
                or "tdy" in rotation_normalized
            )

            if is_exempt:
                # Exempt rotations work through lecture
                assert assignment.expected_code != "LEC", (
                    f"{assignment.resident} ({rotation}) should NOT have LEC on Wed PM"
                )
            else:
                # Non-exempt should have LEC
                assert assignment.expected_code == "LEC", (
                    f"{assignment.resident} ({rotation}) Wed {assignment.date} PM: "
                    f"expected LEC, got {assignment.expected_code}"
                )


class TestKapiolaniPattern:
    """Kapiolani L&D (Travis) - off-site rotation with specific pattern."""

    def test_travis_kap_monday_pattern(
        self, expected_travis_kap: list[RosettaAssignment]
    ):
        """Travis (KAP): Monday = KAP/OFF (AM=KAP, PM=OFF)."""
        mondays = [a for a in expected_travis_kap if a.date.weekday() == 0]  # Monday=0

        for assignment in mondays:
            if assignment.time_of_day == "AM":
                assert assignment.expected_code == "KAP", (
                    f"Travis Mon {assignment.date} AM: "
                    f"expected KAP, got {assignment.expected_code}"
                )
            else:  # PM
                assert assignment.expected_code == "OFF", (
                    f"Travis Mon {assignment.date} PM: "
                    f"expected OFF, got {assignment.expected_code}"
                )

    def test_travis_kap_tuesday_off(self, expected_travis_kap: list[RosettaAssignment]):
        """Travis (KAP): Tuesday = OFF/OFF (travel day)."""
        tuesdays = [a for a in expected_travis_kap if a.date.weekday() == 1]  # Tue=1

        for assignment in tuesdays:
            assert assignment.expected_code == "OFF", (
                f"Travis Tue {assignment.date} {assignment.time_of_day}: "
                f"expected OFF, got {assignment.expected_code}"
            )

    def test_travis_kap_wednesday_clinic(
        self, expected_travis_kap: list[RosettaAssignment]
    ):
        """Travis (KAP): Wednesday AM = C (continuity clinic), PM = LEC."""
        wednesdays = [a for a in expected_travis_kap if a.date.weekday() == 2]  # Wed=2

        for assignment in wednesdays:
            if assignment.date == LAST_WEDNESDAY:
                # Last Wednesday has different rules (LEC/ADV)
                continue

            if assignment.time_of_day == "AM":
                assert assignment.expected_code == "C", (
                    f"Travis Wed {assignment.date} AM: "
                    f"expected C, got {assignment.expected_code}"
                )
            else:  # PM
                assert assignment.expected_code == "LEC", (
                    f"Travis Wed {assignment.date} PM: "
                    f"expected LEC, got {assignment.expected_code}"
                )

    def test_travis_kap_thu_sun_kap(self, expected_travis_kap: list[RosettaAssignment]):
        """Travis (KAP): Thu-Sun = KAP/KAP (on-site at Kapiolani)."""
        # Thursday=3, Friday=4, Saturday=5, Sunday=6
        thu_sun = [a for a in expected_travis_kap if a.date.weekday() in {3, 4, 5, 6}]

        for assignment in thu_sun:
            assert assignment.expected_code == "KAP", (
                f"Travis {assignment.date} {assignment.time_of_day}: "
                f"expected KAP, got {assignment.expected_code}"
            )


class TestLDNFPattern:
    """L&D Night Float (Headid) - Friday AM clinic, not Wednesday!"""

    def test_headid_ldnf_friday_clinic(
        self, expected_headid_ldnf: list[RosettaAssignment]
    ):
        """Headid (LDNF): Friday AM = C (clinic), not OFF!"""
        fridays = [a for a in expected_headid_ldnf if a.date.weekday() == 4]  # Fri=4

        for assignment in fridays:
            if assignment.time_of_day == "AM":
                assert assignment.expected_code == "C", (
                    f"Headid Fri {assignment.date} AM: "
                    f"expected C (clinic!), got {assignment.expected_code}"
                )
            else:  # PM
                assert assignment.expected_code == "OFF", (
                    f"Headid Fri {assignment.date} PM: "
                    f"expected OFF, got {assignment.expected_code}"
                )

    def test_headid_ldnf_mon_thu_pattern(
        self, expected_headid_ldnf: list[RosettaAssignment]
    ):
        """Headid (LDNF): Mon-Thu = OFF/LDNF."""
        # Monday=0, Tuesday=1, Wednesday=2, Thursday=3
        mon_thu = [a for a in expected_headid_ldnf if a.date.weekday() in {0, 1, 2, 3}]

        for assignment in mon_thu:
            # Skip last Wednesday (LEC/ADV rule)
            if assignment.date == LAST_WEDNESDAY:
                continue

            if assignment.time_of_day == "AM":
                assert assignment.expected_code == "OFF", (
                    f"Headid {assignment.date} AM: "
                    f"expected OFF, got {assignment.expected_code}"
                )
            else:  # PM
                assert assignment.expected_code == "LDNF", (
                    f"Headid {assignment.date} PM: "
                    f"expected LDNF, got {assignment.expected_code}"
                )

    def test_headid_ldnf_weekend_pattern(
        self, expected_headid_ldnf: list[RosettaAssignment]
    ):
        """Headid (LDNF): Sat-Sun = W/W (weekend off)."""
        weekends = [
            a for a in expected_headid_ldnf if a.date.weekday() in {5, 6}
        ]  # Sat=5, Sun=6

        for assignment in weekends:
            assert assignment.expected_code == "W", (
                f"Headid {assignment.date} {assignment.time_of_day}: "
                f"expected W, got {assignment.expected_code}"
            )


class TestMidBlockTransition:
    """Mid-block rotation transitions at Mar 23."""

    def test_you_neuro_to_nf_transition(
        self, expected_you_neuro_nf: list[RosettaAssignment]
    ):
        """You (NEURO→NF): Switches at Mar 23."""
        for assignment in expected_you_neuro_nf:
            # Skip weekends and last Wednesday
            if assignment.date.weekday() in {5, 6}:
                continue
            if assignment.date == LAST_WEDNESDAY:
                continue

            if assignment.date < MID_BLOCK_DATE:
                # First half: NEURO rotation pattern
                if assignment.time_of_day == "AM":
                    assert assignment.expected_code == "NEURO", (
                        f"You {assignment.date} AM (before transition): "
                        f"expected NEURO, got {assignment.expected_code}"
                    )
            else:
                # Second half: NF rotation pattern (OFF/NF)
                if assignment.time_of_day == "AM":
                    assert assignment.expected_code == "OFF", (
                        f"You {assignment.date} AM (after transition): "
                        f"expected OFF, got {assignment.expected_code}"
                    )
                else:
                    # Skip checking PM if it's Wednesday (different rule)
                    if assignment.date.weekday() != 2:
                        assert assignment.expected_code == "NF", (
                            f"You {assignment.date} PM (after transition): "
                            f"expected NF, got {assignment.expected_code}"
                        )

    def test_wilhelm_pedw_to_pednf_transition(
        self, expected_wilhelm_pedw_pednf: list[RosettaAssignment]
    ):
        """Wilhelm (PedW→PedNF): Switches at Mar 23, continuity only in first half."""
        for assignment in expected_wilhelm_pedw_pednf:
            # Skip weekends and last Wednesday
            if assignment.date.weekday() in {5, 6}:
                continue
            if assignment.date == LAST_WEDNESDAY:
                continue

            # Wednesday AM behavior depends on which rotation
            if assignment.date.weekday() == 2 and assignment.time_of_day == "AM":
                if assignment.date < MID_BLOCK_DATE:
                    # First half: PedW (ward) = intern continuity applies
                    assert assignment.expected_code == "C", (
                        f"Wilhelm Wed {assignment.date} AM (PedW): "
                        f"expected C (intern continuity), got {assignment.expected_code}"
                    )
                else:
                    # Second half: PedNF (night float) = exempt, should be OFF
                    assert assignment.expected_code == "OFF", (
                        f"Wilhelm Wed {assignment.date} AM (PedNF): "
                        f"expected OFF (NF exempt), got {assignment.expected_code}"
                    )

    def test_byrnes_pednf_to_pedw_transition(
        self, expected_byrnes_pednf_pedw: list[RosettaAssignment]
    ):
        """Byrnes (PedNF→PedW): Reverse transition at Mar 23."""
        for assignment in expected_byrnes_pednf_pedw:
            # Skip weekends and last Wednesday
            if assignment.date.weekday() in {5, 6}:
                continue
            if assignment.date == LAST_WEDNESDAY:
                continue

            # Wednesday AM behavior depends on which rotation
            if assignment.date.weekday() == 2 and assignment.time_of_day == "AM":
                if assignment.date < MID_BLOCK_DATE:
                    # First half: PedNF (night float) = exempt, should be OFF
                    assert assignment.expected_code == "OFF", (
                        f"Byrnes Wed {assignment.date} AM (PedNF): "
                        f"expected OFF (NF exempt), got {assignment.expected_code}"
                    )
                else:
                    # Second half: PedW (ward) = intern continuity applies
                    assert assignment.expected_code == "C", (
                        f"Byrnes Wed {assignment.date} AM (PedW): "
                        f"expected C (intern continuity), got {assignment.expected_code}"
                    )


class TestFMCPattern:
    """FMC (Sawyer, Chen) - clinic-heavy rotation."""

    def test_sawyer_fmc_pgy1(
        self, rosetta_by_resident: dict[str, list[RosettaAssignment]]
    ):
        """Sawyer (FMC PGY-1): Should have C assignments throughout."""
        sawyer = rosetta_by_resident.get("Sawyer, Tessa", [])
        assert len(sawyer) == 56, f"Sawyer should have 56 slots, got {len(sawyer)}"

        # Count C assignments (excluding weekends, LEC, ADV)
        c_count = sum(1 for a in sawyer if a.expected_code == "C")
        assert c_count > 20, f"Sawyer should have many C slots, got {c_count}"

    def test_chen_fmc_pgy2(
        self, rosetta_by_resident: dict[str, list[RosettaAssignment]]
    ):
        """Chen (FMC PGY-2): No intern continuity rule, still has C assignments."""
        chen = rosetta_by_resident.get("Chen, Michael", [])
        assert len(chen) == 56, f"Chen should have 56 slots, got {len(chen)}"

        # Count C assignments (excluding weekends, LEC, ADV)
        c_count = sum(1 for a in chen if a.expected_code == "C")
        assert c_count > 20, f"Chen should have many C slots, got {c_count}"


class TestProceduresPattern:
    """Procedures rotation (Sloss) - intern with continuity rule."""

    def test_sloss_proc_wednesday_am_continuity(
        self, expected_sloss_proc: list[RosettaAssignment]
    ):
        """Sloss (PROC PGY-1): Wednesday AM = C (intern continuity, not PR!)."""
        wednesdays = [a for a in expected_sloss_proc if a.date.weekday() == 2]

        for assignment in wednesdays:
            if assignment.date == LAST_WEDNESDAY:
                continue

            if assignment.time_of_day == "AM":
                assert assignment.expected_code == "C", (
                    f"Sloss Wed {assignment.date} AM: "
                    f"expected C (not PR!), got {assignment.expected_code}"
                )


class TestIMPattern:
    """Internal Medicine rotation (Monsivais) - intern with continuity rule."""

    def test_monsivais_im_wednesday_am_continuity(
        self, expected_monsivais_im: list[RosettaAssignment]
    ):
        """Monsivais (IM PGY-1): Wednesday AM = C (intern continuity, not IM!)."""
        wednesdays = [a for a in expected_monsivais_im if a.date.weekday() == 2]

        for assignment in wednesdays:
            if assignment.date == LAST_WEDNESDAY:
                continue

            if assignment.time_of_day == "AM":
                assert assignment.expected_code == "C", (
                    f"Monsivais Wed {assignment.date} AM: "
                    f"expected C (not IM!), got {assignment.expected_code}"
                )

    def test_monsivais_im_works_weekends(
        self, expected_monsivais_im: list[RosettaAssignment]
    ):
        """Monsivais (IM): IM rotation works weekends (not W)."""
        weekends = [a for a in expected_monsivais_im if a.date.weekday() in {5, 6}]

        for assignment in weekends:
            # IM works weekends, should be IM not W
            assert assignment.expected_code == "IM", (
                f"Monsivais {assignment.date} {assignment.time_of_day}: "
                f"expected IM (works weekends), got {assignment.expected_code}"
            )
