# Scheduling Engine Constraints Registry

This document lists all the constraints available to the CP-SAT scheduling engine.

| Constraint Class | File | Type | Description |
| --- | --- | --- | --- |
| `ActivityRequirementConstraint` | `activity_requirement.py` | Soft | Soft constraint enforcing min/max/target halfdays per activity. |
| `AdjunctCallExclusionConstraint` | `call_coverage.py` | Hard | Prevents adjunct faculty from being auto-assigned overnight call. |
| `AvailabilityConstraint` | `acgme.py` | Hard | Ensures residents are only assigned to blocks when available. |
| `CallAvailabilityConstraint` | `call_coverage.py` | Hard | Prevents call assignment when faculty is unavailable. |
| `CallNightBeforeLeaveConstraint` | `call_equity.py` | Soft | Soft penalty for overnight call the night before a leave/absence. |
| `CallSpacingConstraint` | `call_equity.py` | Soft | Penalizes back-to-back call weeks for the same faculty. |
| `ClinicCapacityConstraint` | `capacity.py` | Hard | Ensures clinic capacity limits are respected. |
| `ConstraintCategory` | `config.py` | Unknown | Constraint categories for organization. |
| `ConstraintConfigManager` | `config.py` | Unknown | Manages constraint configurations. |
| `ConstraintConfig` | `config.py` | Unknown | Configuration for a single constraint. |
| `ConstraintManager` | `manager.py` | Unknown | Manages a collection of constraints for scheduling. |
| `ConstraintPriorityLevel` | `config.py` | Unknown | Priority levels for constraint application. |
| `ContinuityConstraint` | `equity.py` | Soft | Encourages schedule continuity - residents staying in same rotation |
| `CoverageConstraint` | `capacity.py` | Soft | Maximizes block coverage (number of assigned blocks). |
| `DeptChiefWednesdayPreferenceConstraint` | `call_equity.py` | Soft | Soft preference for Department Chief to take Wednesday call. |
| `EightyHourRuleConstraint` | `acgme.py` | Hard | ACGME 80-hour rule: Maximum 80 hours per week, strictly calculated |
| `EquityConstraint` | `equity.py` | Soft | Balances workload across residents. |
| `FMITContinuityTurfConstraint` | `fmit.py` | Hard | FMIT continuity delivery turf rules based on system load. |
| `FMITMandatoryCallConstraint` | `fmit.py` | Hard | Ensures FMIT attending covers Friday and Saturday night call. |
| `FMITResidentClinicDayConstraint` | `inpatient.py` | Hard | Enforces PGY-specific clinic days for FMIT residents. |
| `FMITStaffingFloorConstraint` | `fmit.py` | Hard | Ensures minimum faculty available before FMIT assignments. |
| `FMITWeekBlockingConstraint` | `fmit.py` | Hard | Blocks clinic and Sun-Thurs call during FMIT week. |
| `FacultyCallPreferenceConstraint` | `call_equity.py` | Soft | Soft preferences for faculty call based on day of week. |
| `FacultyClinicCapConstraint` | `faculty_clinic.py` | Soft | Enforce MIN and MAX clinic sessions per week per faculty. |
| `FacultyClinicEquitySoftConstraint` | `primary_duty.py` | Soft | Soft constraint that optimizes toward target clinic coverage. |
| `FacultyDayAvailabilityConstraint` | `primary_duty.py` | Hard | Enforces day-of-week availability based on primary duty configuration. |
| `FacultyPrimaryDutyClinicConstraint` | `primary_duty.py` | Hard | Enforces clinic half-day requirements based on primary duty configuration. |
| `FacultyRoleClinicConstraint` | `faculty_role.py` | Hard | Enforces clinic half-day limits for faculty. |
| `FacultySupervisionConstraint` | `faculty_clinic.py` | Soft | Ensure ACGME AT (Attending Time) coverage for residents in clinic. |
| `FacultyWeeklyTemplateConstraint` | `faculty_weekly_template.py` | Soft | Enforces faculty weekly activity templates and overrides. |
| `HalfDayRequirementConstraint` | `halfday_requirement.py` | Soft | Soft constraint that optimizes activity distribution per rotation. |
| `HolidayCallEquityConstraint` | `call_equity.py` | Soft | Ensures fair distribution of holiday overnight call. |
| `HubProtectionConstraint` | `resilience.py` | Soft | Protects hub faculty from over-assignment. |
| `IntegratedWorkloadConstraint` | `integrated_workload.py` | Soft | Ensures fair distribution of total workload across faculty. |
| `InternContinuityConstraint` | `fm_scheduling.py` | Hard | PGY-1 Wednesday AM = C (continuity clinic). |
| `InvertedWednesdayConstraint` | `temporal.py` | Hard | Ensures 4th Wednesday has single faculty AM and different faculty PM. |
| `MaxPhysiciansInClinicConstraint` | `capacity.py` | Hard | Ensures physical space limitations are respected. |
| `N1VulnerabilityConstraint` | `resilience.py` | Soft | Prevents schedules that create single points of failure. |
| `NightFloatPostCallConstraint` | `night_float_post_call.py` | Hard | Enforces PC (Post-Call) full day after Night Float ends. |
| `NightFloatSlotConstraint` | `fm_scheduling.py` | Hard | Night float residents get NF in both AM and PM slots (except days off). |
| `OneInSevenRuleConstraint` | `acgme.py` | Hard | ACGME 1-in-7 rule: At least one 24-hour period off every 7 days. |
| `OnePersonPerBlockConstraint` | `capacity.py` | Hard | Ensures at most one primary resident assigned per block. |
| `OvernightCallCoverageConstraint` | `call_coverage.py` | Hard | Ensures exactly one faculty member is on overnight call each Sun-Thurs night. |
| `OvernightCallGenerationConstraint` | `overnight_call.py` | Hard | Generates overnight call assignments for Sunday through Thursday nights. |
| `PostCallAutoAssignmentConstraint` | `post_call.py` | Soft | Automatically assigns PCAT (AM) and DO (PM) after overnight call. |
| `PostFMITRecoveryConstraint` | `fmit.py` | Hard | Blocks the Friday after FMIT week for recovery. |
| `PostFMITSundayBlockingConstraint` | `fmit.py` | Soft | Penalizes Sunday call for faculty immediately after FMIT week. |
| `PreferenceConstraint` | `faculty.py` | Soft | Handles resident preferences for specific rotations, times, or blocks. |
| `PreferenceTrailConstraint` | `resilience.py` | Soft | Uses stigmergy preference trails for assignment optimization. |
| `ProtectedSlotConstraint` | `protected_slot.py` | Hard | Enforces protected slots from weekly patterns. |
| `ResidentAcademicTimeConstraint` | `resident_weekly_clinic.py` | Hard | Protects academic time (Wednesday AM) from clinic assignments. |
| `ResidentClinicDayPreferenceConstraint` | `resident_weekly_clinic.py` | Soft | Soft constraint that optimizes clinic assignments to allowed days. |
| `ResidentInpatientHeadcountConstraint` | `inpatient.py` | Hard | Enforces headcount limits for resident inpatient rotations. |
| `ResidentWeeklyClinicConstraint` | `resident_weekly_clinic.py` | Soft | Penalizes deviation from weekly FM clinic half-day targets for residents. |
| `SMFacultyClinicConstraint` | `faculty_role.py` | Hard | Ensures Sports Medicine faculty is not assigned to regular clinic. |
| `SMResidentFacultyAlignmentConstraint` | `sports_medicine.py` | Hard | Ensures SM residents are scheduled with SM faculty. |
| `SundayCallEquityConstraint` | `call_equity.py` | Soft | Ensures fair distribution of Sunday overnight call. |
| `SupervisionRatioConstraint` | `acgme.py` | Hard | ACGME supervision ratios: Ensures adequate faculty supervision. |
| `TuesdayCallPreferenceConstraint` | `call_equity.py` | Soft | Soft preference to avoid PD and APD on Tuesday call. |
| `UtilizationBufferConstraint` | `resilience.py` | Soft | Maintains capacity buffer to absorb unexpected demand. |
| `WednesdayAMInternOnlyConstraint` | `temporal.py` | Hard | Ensures Wednesday morning clinic is staffed by interns (PGY-1) only. |
| `WednesdayPMLecConstraint` | `fm_scheduling.py` | Hard | Wednesday PM = LEC-PM for non-exempt rotations. |
| `WednesdayPMSingleFacultyConstraint` | `temporal.py` | Hard | Ensures exactly 1 faculty is assigned to clinic on Wednesday PM. |
| `WeekdayCallEquityConstraint` | `call_equity.py` | Soft | Ensures fair distribution of Mon-Thurs overnight call. |
| `WeekendWorkConstraint` | `halfday_requirement.py` | Hard | Enforces weekend work configuration per rotation. |
| `ZoneBoundaryConstraint` | `resilience.py` | Soft | Respects blast radius zone boundaries in scheduling. |
