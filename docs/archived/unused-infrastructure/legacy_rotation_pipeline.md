# Legacy Rotation Pipeline (Archived)

Status: Removed from runtime. Retained for historical reference only.

This document describes the legacy scheduling path that operated on block-level
rotation assignments (Assignment table) instead of half-day slots. The canonical
pipeline now requires expand_block_assignments=True and writes to
half_day_assignments.

## What the legacy pipeline did

- Solver assigned residents to rotation blocks (Assignment table)
- Faculty supervision was assigned via legacy _assign_faculty
- No half-day expansion, no activity solver
- Call assignments were handled via greedy or other solver variants

## Why it is archived

- Block 10 and current operations require half-day AM/PM slots
- Preloads and activity locking occur at the half-day level
- Call/PCAT/DO synchronization depends on half-day assignments
- CP-SAT is now canonical for call/activity/faculty

## Where it still exists (archived only)

- backend/app/scheduling/solvers.py: rotation-level solvers (Greedy/PuLP/Hybrid)
- backend/app/models/assignment.py: legacy output table
- This document (verbatim code excerpts below)

## Reactivation (not recommended)

If you ever need to revive the legacy pipeline:
- Re-enable expand_block_assignments=False flow in SchedulingEngine
- Restore any rotation-only constraint expectations
- Re-validate call and faculty supervision paths


## Removed legacy code (verbatim)

Source: backend/app/scheduling/engine.py (removed during full excision of legacy path).

### Legacy solver branch
```python
            # Step 5: Run solver
            # NOTE: In half-day mode (expand_block_assignments=True), the activity solver
            # (CPSATActivitySolver in Step 1.5i) handles activity assignment to HalfDayAssignment.
            # The legacy rotation solver is skipped because its results are discarded anyway.
            if not expand_block_assignments:
                solver_result = self._run_solver(algorithm, context, timeout_seconds)

                if not solver_result.success:
                    logger.error(f"CP-SAT solver failed: {solver_result.solver_status}")
                    self._update_run_status(
                        run, "failed", 0, 0, time.time() - start_time
                    )
                    self.db.commit()
                    return {
                        "status": "failed",
                        "message": f"CP-SAT solver failed: {solver_result.solver_status}",
                        "total_assigned": 0,
                        "total_blocks": len(blocks),
                        "validation": self._empty_validation(),
                        "run_id": run.id,
                    }
            else:
                # Half-day mode: Run CP-SAT solver ONLY for call assignments (Sun-Thu)
                # Rotation assignments come from expansion service, but call equity
                # logic is in CP-SAT constraints. We discard rotation assignments but
                # keep call_assignments from the result.
                logger.info(
                    "Running CP-SAT solver for Sun-Thu call assignments only "
                    "(rotation assignments handled by expansion service)"
                )
                solver_result = self._run_solver("cp_sat", context, timeout_seconds)
                if not solver_result.success:
                    logger.error(
                        f"CP-SAT call solver failed: {solver_result.solver_status}"
                    )
                    self._update_run_status(
                        run, "failed", 0, 0, time.time() - start_time
                    )
                    self.db.commit()
                    return {
                        "status": "failed",
                        "message": f"CP-SAT call solver failed: {solver_result.solver_status}",
                        "total_assigned": 0,
                        "total_blocks": len(blocks),
                        "validation": self._empty_validation(),
                        "run_id": run.id,
                    }
                # Clear rotation assignments (we don't need them in half-day mode)
                # but preserve call_assignments for Step 6.5
                solver_result.assignments = []
                logger.info(
                    f"Greedy solver generated {len(solver_result.call_assignments)} "
                    f"Sun-Thu call assignments"
                )
```

### Legacy assignment persistence (Assignment table)
```python
            # Step 5.6: Add expanded assignments from block_assignments
            # These are NEW records generated from the master rotation schedule
            # NOTE: When expand_block_assignments=True with persist_half_day=True,
            # HalfDayAssignment records are already created by the expansion service.
            # We DO NOT add to self.assignments since that list gets persisted to
            # the old Assignment table in Step 8, causing constraint violations.
            if not expand_block_assignments:
                # Legacy path: persist Assignment objects to old table
                for assignment in expanded_assignments:
                    self.db.add(assignment)
                    self.assignments.append(assignment)
                if expanded_assignments:
                    logger.info(
                        f"Added {len(expanded_assignments)} expanded assignments to session"
                    )
            else:
                # New path: HalfDayAssignment already persisted by expansion service
                # Skip adding to self.assignments to avoid duplicate persistence
                logger.info(
                    f"Skipped {len(expanded_assignments)} expanded assignments "
                    f"(already persisted as HalfDayAssignment)"
                )
```

### Legacy solver-to-assignment conversion
```python
            # Step 6: Convert solver results to assignments
            # In half-day mode, resident assignments come from expansion, not solver
            if not expand_block_assignments:
                self._create_assignments_from_result(
                    solver_result,
                    residents,
                    templates,
                    cast(UUID, run.id),
                    preserved_assignments,
                )
            else:
                logger.info(
                    "Skipping solver assignment conversion in half-day mode "
                    "(residents already assigned via expansion)"
                )
```

### Legacy faculty supervision assignment
```python
            # Step 7: Assign faculty supervision (legacy mode only)
            # In half-day mode, faculty assignments already created by Step 6.8
            # (FacultyAssignmentExpansionService fills all 56 slots per faculty)
            if not expand_block_assignments:
                self._assign_faculty(
                    faculty, blocks, cast(UUID, run.id), preserved_assignments
                )
            else:
                logger.info(
                    "Skipping legacy faculty supervision - already handled by "
                    "FacultyAssignmentExpansionService in Step 6.8"
                )
```
