# Key Database Schema (SQLAlchemy Models)

## half_day_assignments
- person_id: UUID FK → people
- date: Date
- time_of_day: String(2) — "AM" or "PM"
- activity_id: UUID FK → activities
- source: String(20) — "preload", "manual", "solver", "template"
- block_assignment_id: UUID FK → block_assignments (nullable)
- is_override: Boolean
- Unique: (person_id, date, time_of_day)

## rotation_templates
- name: String(255)
- rotation_type: String(255)
- template_category: String(20) — default "rotation"
- is_block_half_rotation: Boolean
- includes_weekend_work: Boolean
- leave_eligible: Boolean
- max_residents: Integer
- supervision_required: Boolean
- is_archived: Boolean (soft delete)

## rotation_activity_requirements
- rotation_template_id: UUID FK → rotation_templates (CASCADE)
- activity_id: UUID FK → activities (RESTRICT)
- min_halfdays: Integer (default 0)
- max_halfdays: Integer (default 14)
- target_halfdays: Integer (nullable, soft constraint)
- applicable_weeks: JSONB — e.g. [1,2,3,4] or null for all
- prefer_full_days: Boolean (default True)
- preferred_days: JSONB — e.g. [1,2,3,4,5]
- avoid_days: JSONB — e.g. [0,6]
- priority: Integer 0-100
- Unique: (rotation_template_id, activity_id, applicable_weeks_hash)

## block_assignments
- block_number: Integer (1-13)
- academic_year: Integer
- resident_id: UUID FK → people
- rotation_template_id: UUID FK → rotation_templates (primary)
- secondary_rotation_template_id: UUID FK → rotation_templates (day 14+)
- has_leave: Boolean
- assignment_reason: String — "leave_eligible_match", "coverage_priority", "balanced", "manual", "specialty_match"
- Unique: (block_number, academic_year, resident_id)

## weekly_patterns
- rotation_template_id: UUID FK → rotation_templates (CASCADE)
- day_of_week: Integer (0=Sunday..6=Saturday)
- time_of_day: String — "AM" or "PM"
- week_number: Integer 1-4 (nullable = all weeks)
- activity_id: UUID FK → activities (RESTRICT)
- is_protected: Boolean
- Unique: (rotation_template_id, day_of_week, time_of_day, week_number)

## activities
- code: String(50) — unique, e.g. "FMIT", "NF", "KAP-LD"
- name: String(255)
- activity_category: String(20)
- requires_supervision: Boolean
- is_protected: Boolean
- counts_toward_clinical_hours: Boolean

## people
- name: String(255)
- type: String(50) — "resident" or "faculty"
- pgy_level: Integer (1-3, nullable for faculty)
- target_clinical_blocks: Integer
