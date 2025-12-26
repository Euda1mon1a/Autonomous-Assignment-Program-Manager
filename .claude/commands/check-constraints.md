<!--
Pre-flight verification for scheduling constraint development.
Use when adding or modifying constraints to ensure proper registration.
-->

Invoke the constraint-preflight skill to verify constraints.

***REMOVED******REMOVED*** Arguments

- `$ARGUMENTS` - Constraint name or "all" to check all constraints

***REMOVED******REMOVED*** Verification Steps

1. Constraint class exists in correct module
2. Constraint exported in __init__.py
3. Constraint registered in ConstraintManager.create_default()
4. Unit tests exist for constraint
5. Integration test covers constraint behavior

***REMOVED******REMOVED*** Output

Preflight checklist with pass/fail for each step.
