# Program Adoption Roadmap

## Purpose

This roadmap defines the product and infrastructure boundary for the next phase of the scheduler.

Near-term goal:
- Each residency program can clone the repo, deploy its own instance, and tune its own policy without editing Python.

Explicit non-goal for this phase:
- Multi-tenant hosted platform
- Kubernetes-based fleet management
- Centralized operations across multiple external programs

## Strategic Position

Build for single-tenant, self-hosted deployments first.

Target model:
- One repo clone per program deployment
- One database per program
- Python owns solver logic
- Postgres owns program policy and operational data
- GUI owns safe human tuning of program policy
- Docker Compose is the supported deployment path

This is the right boundary because the first outside-program pain points will be:
- installation
- configuration
- safe upgrades
- backups and recovery
- policy tuning

They will not be:
- Kubernetes orchestration
- multi-tenant isolation in a shared cluster
- centralized control planes

## Current State

What is already moving in the right direction:
- Constraint configuration is DB-backed
- Primary duty configuration is DB-backed
- Calendar policy is DB-backed
- Rotation-template preload classification is DB-backed
- More non-physical constraints are now soft and weight-tunable

What still blocks true per-program tuning:
- Some human-owned policy still lives in Python
- Some DB-backed policy still has no GUI
- Settings are still mostly global rather than program-scoped and academic-year-scoped
- Outside-program installation and upgrade workflows are not yet the main product surface

## Phase 1: Now

Objective:
- Make one program successful for one academic year with minimal manual code edits.

### Product boundary

Must be GUI-editable or at least DB-editable without Python changes:
- constraint enable/disable and weights
- primary duty config
- preload classification flags
- clinic caps
- overnight call calendar policy
- FMIT calendar policy
- academic half-day / protected curriculum timing

Must remain in Python:
- solver math
- CP-SAT variable construction
- hard/soft implementation details
- constraint orchestration

### Required engineering work

1. Finish migrating remaining human policy out of Python.
- Faculty role defaults and call preferences
- Academic-slot timing policy for residents, interns, and learners
- Remove fallback preload/export classification tables as primary truth

2. Finish GUI coverage for already-DB-backed policy.
- Primary duty admin screen
- Rotation-template preload classification editor
- Person-level clinic cap and primary duty editing
- Fix any create/edit flows that still drop fields

3. Introduce policy portability.
- Export program policy
- Import program policy
- Diff current policy vs baseline/default

4. Harden self-hosted deployment.
- Reliable Docker Compose path
- Bootstrap script for first-time setup
- Backup and restore procedure
- Upgrade and migration procedure

### Exit criteria

A program admin can:
- deploy from docs without editing source code
- configure core policy in the app
- run backups and restore confidently
- upgrade to a newer version without guessing at manual steps

## Phase 2: Before First Outside Program

Objective:
- Make the system safe and repeatable for a second program that is not yours.

### Architecture changes

1. Add program-scoped policy.
- Introduce `program_id` ownership for policy tables where appropriate
- Stop assuming one global `ApplicationSettings` row is enough

2. Add academic-year scoping where policy legitimately changes year to year.
- Academic half-day timing
- Call/FMIT policy if needed
- Role/cap policy if it changes across years

3. Make policy state inspectable.
- Audit history for policy changes
- Last-updated metadata
- Safe defaults and validation on every policy editor

### Product work

1. Create a real "program profile" concept.
- Program identity
- Default calendars and conventions
- Policy bundle for schedule generation

2. Add change-impact visibility.
- "What changed?"
- "What schedules will this affect?"
- "Will this create coverage/compliance risk?"

3. Improve operator trust.
- Validation before save
- Pre-flight checks before schedule generation
- Clear failure modes instead of fallback behavior

### Packaging and docs

1. Produce an outside-program install guide.
- Prerequisites
- Initial seeding
- First login
- Policy tuning checklist

2. Produce an upgrade guide.
- Backup first
- Migration steps
- Post-upgrade validation

3. Produce an operator handbook.
- What can be tuned
- What should not be tuned casually
- How to recover from mistakes

### Exit criteria

A second program can:
- deploy its own instance from docs
- configure its own policy without Python edits
- understand what changed and when
- upgrade safely with backup/restore and validation

## Phase 3: Before Centralized Hosting Or Kubernetes

Objective:
- Decide whether a central platform is justified by real operating load, not by anticipation.

Do not start this phase until there is evidence of one or more of these:
- multiple external programs actively using the system
- repeated requests for centralized upgrades or support
- operational burden from maintaining many separate deployments
- need for shared observability, fleet policy rollout, or tenant isolation

### Work that belongs here, not earlier

1. Multi-tenant architecture decisions.
- shared control plane vs isolated stacks
- data isolation guarantees
- tenant-aware policy boundaries

2. Kubernetes or equivalent orchestration.
- only if deployment count and operational complexity justify it

3. Centralized observability and fleet operations.
- rollout tracking
- health monitoring across tenants
- version management

4. Platform security hardening for hosted use.
- tenant boundaries
- secret management at scale
- hosted backup and restore operations

### Exit criteria

Centralized platform work should start only when:
- self-hosted per-program deployments are already stable
- policy boundaries are well-modeled in the database
- upgrade, backup, and restore flows are routine
- the platform problem is real, not hypothetical

## Recommended Priority Order

1. Finish moving remaining human policy from Python to Postgres
2. Finish GUI coverage for DB-backed policy
3. Add program-scoped and academic-year-scoped policy models
4. Build export/import/diff for policy bundles
5. Harden self-hosted deployment, backup, restore, and upgrades
6. Bring on a second outside program
7. Re-evaluate centralized hosting only after real external usage

## Immediate Backlog

### Backend
- Add DB model(s) for faculty role defaults and call preferences
- Add DB model(s) for program-specific academic-slot policy
- Remove Python fallback classification tables as source of truth
- Add policy export/import APIs
- Add program and academic-year scoping where policy should vary

### Frontend
- Build primary duty admin UI
- Build preload classification editor in rotation-template admin
- Expose clinic cap and primary duty fields in person admin flows
- Build academic-slot policy editor
- Add policy diff/history views

### Operations
- Write self-hosted deployment guide
- Write upgrade guide
- Write backup/restore runbook
- Add bootstrap command for new program instances

## Related Docs

- `docs/architecture/POLICY_STORAGE_BOUNDARY.md`
- `docs/architecture/GUI_EDITABILITY_BOUNDARY.md`
- `docs/planning/HARDCODED_TO_POSTGRES_ROADMAP.md`
- `docs/planning/POLICY_GUI_MIGRATION_BACKLOG_20260314.md`
- `docs/architecture/KUBERNETES_EVALUATION.md`
