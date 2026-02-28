# Implementing Faculty Full-Day Preference

To add a toggle for full-day vs half-day clinic preferences for faculty, we need to apply the logic within the `FacultyPrimaryDutyClinicConstraint`. This constraint already handles the generation of faculty clinics and currently scatters them.

The `prefer_full_days` field has been added to the `Person` model. The solver needs to look at this boolean and add a soft objective to group AM and PM shifts of the same activity on the same day when true.

## Proposed Logic Update
In `backend/app/scheduling/constraints/primary_duty.py` within `FacultyPrimaryDutyClinicConstraint.add_to_cpsat`:

1.  Identify the faculty member.
2.  If `faculty.prefer_full_days` is true, iterate over the days of the block.
3.  For each day, if an AM slot has an activity variable, reward the solver (add a negative penalty or objective bonus) if the PM slot has the exact same activity variable.
4.  This uses standard CP-SAT `model.AddBoolOr` or `model.AddBoolAnd` logic to create an indicator variable `is_full_day`, and then appends `(bonus_weight, is_full_day)` to the soft objectives list.
