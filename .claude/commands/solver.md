<!--
Solver kill-switch and progress monitoring.
Use when aborting runaway solvers or monitoring long-running generation.
-->

Invoke the solver-control skill for solver management.

***REMOVED******REMOVED*** Arguments

- `$ARGUMENTS` - "status", "abort", or "monitor"

***REMOVED******REMOVED*** Commands

- `status` - Check if solver is running, show progress
- `abort` - Kill runaway solver immediately
- `monitor` - Watch solver progress in real-time

***REMOVED******REMOVED*** Abort Conditions

- Solver running > 5 minutes
- Memory usage > 4GB
- No improvement in 60 seconds
