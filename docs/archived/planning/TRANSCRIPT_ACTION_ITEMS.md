# Transcript Extraction: Arcane Scheduling Rules & "Excel-able" Fixes

> **Source:** Human Coordinator Transcript (March 3, 2026)
> **Goal:** Bridge the gap between mathematically optimal solver outputs and coordinator expectations (the "Last Mile").

## 1. The C30 / C40 PGY Booking Rule (CRITICAL)
**The Problem:** The solver outputs generic `C` for clinic. Interns (PGY-1) require 40-minute slots (`C40`), while PGY-2/3 require 30-minute slots (`C30`). Using generic `C` causes front-desk patient booking errors.
**Action Items:**
- [ ] Fix `C30` in the database (currently `display_abbreviation` is `None`).
- [ ] Add `C30` background color to `TAMC_Color_Scheme_Reference.xml`.
- [ ] Add post-processing logic in `engine.py` to auto-translate generic `C` to `C40` for PGY-1s and `C30` for PGY-2/3s.

## 2. Night Float Continuity Touchpoint (`C-N`)
**The Problem:** An onboarding night-float resident must have a continuity clinic touchpoint early in the block (usually Thursday PM).
**Action Items:**
- [ ] Create a `NightFloatContinuityConstraint` (or preloader) that explicitly assigns the existing `C-N` code to the first Thursday PM of a Night Float block.
- [ ] Ensure `C-N` maps to the correct color in the XML schema.

## 3. The 1-Day Call Spacing Gap
**The Problem:** The transcript explicitly flags a call on the 15th and 17th as a "back-to-back" violation because there are "no days in between." Our solver only penalizes true consecutive days (e.g., 15th and 16th).
**Action Items:**
- [ ] Expand the `NoConsecutiveCallConstraint` in `overnight_call.py` to penalize a 1-day gap (< 48 hours rest).

## 4. Final Wednesday Continuity Loss
**The Problem:** Rotations like IM Wards often strip away the "final Wednesday" clinic, causing residents to lose a continuity week in the ACGME tally.
**Action Items:**
- [ ] Create a `FinalWednesdayContinuityConstraint` (SoftConstraint) that penalizes the solver if a PGY-1/2 reaches the final Wednesday of a block without at least one `C` or `C-I` scheduled that day.

## 5. HC & CLC Hardcoding (Template Immunity)
**The Problem:** `HC` (Hospital Committee) and `CLC` (Clinic Learning Conf) are universal protected PM blocks that punch through even intensive inpatient rotations like FMIT and L&D.
**Action Items:**
- [ ] Seed `HC` into the `activities` DB table (`activity_category="administrative"`, `is_protected=True`).
- [ ] Verify `CLC` is `is_protected=True` in the DB.
- [ ] Ensure the solver and import engine respect these as locked structural blocks that override regular rotation logic.

## 6. Night Float Block Misalignment
**The Problem:** Night Float must strictly start on Thursday and end on Wednesday, followed by a post-call Thursday. The transcript notes the current output is off by ~3-4 days.
**Status:** **Resolved.** The `NightFloatPostCallConstraint` and block boundary rules natively handle this Thursday-to-Wednesday alignment.

## 7. The COUNTIF Intern Misclassification Bug
**The Problem:** Legacy Excel `COUNTIF` miscounted residents as interns.
**Status:** **Resolved.** PR #1229 introduced dynamic Python-generated `COUNTIFS` that use strictly mapped `$D$9:$D$30,"PGY 1"` roles rather than legacy name searches.

## 8. Clinic Session Capacity Cap
**The Problem:** Cannot exceed 6 residents in clinic simultaneously (previously hit 9).
**Status:** **Resolved.** The `ClinicCapacityConstraint` (re-enabled in PR #1215) explicitly enforces the capacity units defined in `fmc_capacity.py` (which caps physical slots at 6).
