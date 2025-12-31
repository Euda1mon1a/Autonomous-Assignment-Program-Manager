# Review Patches for Claude (Schedule Run Persistence)

This document captures the observed Block 10 run loss and proposes concrete fixes.

## Findings

- A `hybrid` run for Block 10 reported `total_blocks_assigned=80`, but those assignments no longer exist.
- A later failed run likely deleted prior assignments because deletions happen before solving.
- Assignments have no `schedule_run_id`, so there is no durable linkage between runs and generated rows.

## Patch 1) Defer deletions until after a successful solve

Problem: `_delete_existing_assignments` is called before solving and commits even on failure, wiping prior schedules.

Recommendation:
- Only delete existing assignments after a successful solver result.
- Alternatively, wrap the generation in a transaction and roll back on failure so deletions do not persist.

```diff
diff --git a/backend/app/scheduling/engine.py b/backend/app/scheduling/engine.py
index a330e44..XXXXXXX 100644
--- a/backend/app/scheduling/engine.py
+++ b/backend/app/scheduling/engine.py
@@
-            # Issue #2: Delete existing assignments for this date range to avoid duplicates
-            self._delete_existing_assignments(preserve_ids=preserve_ids)
+            # Defer deletion until after a successful solve
@@
             solver_result = self._run_solver(algorithm, context, timeout_seconds)
 
             if not solver_result.success:
                 logger.warning(f"Solver failed: {solver_result.solver_status}")
                 # Fallback to greedy if advanced solver fails
                 if algorithm != "greedy":
                     logger.info("Falling back to greedy solver")
                     solver_result = self._run_solver("greedy", context, timeout_seconds)
 
+            if not solver_result.success:
+                # Do not delete existing assignments on failure
+                self._update_run_status(run, "failed", 0, 0, time.time() - start_time)
+                self.db.commit()
+                return {
+                    "status": "failed",
+                    "message": "Schedule generation failed; existing assignments preserved",
+                    "total_assigned": 0,
+                    "total_blocks": len(blocks),
+                    "validation": self._empty_validation(),
+                    "run_id": run.id,
+                }
+
+            # Delete existing assignments only after a successful solve
+            self._delete_existing_assignments(preserve_ids=preserve_ids)
+
             # Step 6: Convert solver results to assignments
             self._create_assignments_from_result(solver_result, residents, templates)
```

Notes:
- If you prefer stricter consistency, wrap generation in a transaction and rollback on failure instead of returning early.

## Patch 2) Add `schedule_run_id` to assignments

Problem: Assignments are not linked to the schedule run that generated them, making audits and rollback impossible.

Recommendation:
- Add `schedule_run_id` to the `assignments` table.
- Set it when creating assignments from solver results.
- Optionally include it in API responses for traceability.

Migration sketch:

```diff
diff --git a/backend/alembic/versions/XXXXXXXX_add_schedule_run_id_to_assignments.py b/backend/alembic/versions/XXXXXXXX_add_schedule_run_id_to_assignments.py
new file mode 100644
--- /dev/null
+++ b/backend/alembic/versions/XXXXXXXX_add_schedule_run_id_to_assignments.py
@@
from alembic import op
import sqlalchemy as sa

revision = "XXXXXXXX_add_schedule_run_id_to_assignments"
down_revision = "<previous_revision>"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("assignments", sa.Column("schedule_run_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_assignments_schedule_run",
        "assignments",
        "schedule_runs",
        ["schedule_run_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_assignments_schedule_run", "assignments", ["schedule_run_id"])

def downgrade():
    op.drop_index("idx_assignments_schedule_run", table_name="assignments")
    op.drop_constraint("fk_assignments_schedule_run", "assignments", type_="foreignkey")
    op.drop_column("assignments", "schedule_run_id")
```

Engine update sketch:

```diff
diff --git a/backend/app/scheduling/engine.py b/backend/app/scheduling/engine.py
index a330e44..XXXXXXX 100644
--- a/backend/app/scheduling/engine.py
+++ b/backend/app/scheduling/engine.py
@@
-    def _create_assignments_from_result(self, result: SolverResult, residents: list[Person], templates: list[RotationTemplate]):
+    def _create_assignments_from_result(self, result: SolverResult, residents: list[Person], templates: list[RotationTemplate], run_id: UUID | None = None):
@@
-            assignment = Assignment(
+            assignment = Assignment(
                 block_id=block_id,
                 person_id=person_id,
                 rotation_template_id=template_id,
                 role="primary",
+                schedule_run_id=run_id,
             )
@@
-            self._create_assignments_from_result(solver_result, residents, templates)
+            self._create_assignments_from_result(solver_result, residents, templates, run_id=run.id)
```

## Minimal verification

- Trigger a schedule generation that fails; confirm prior assignments remain.
- Trigger a successful run; confirm assignments have `schedule_run_id` and match `schedule_runs.id`.
