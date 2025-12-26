<!--
Proactive code health monitoring and quality gate enforcement.
Use when validating code changes or ensuring standards before merging.
-->

Invoke the code-quality-monitor skill to validate code quality.

## Arguments

- `$ARGUMENTS` - File paths to check, or "all" for full codebase scan

## Checks Performed

1. Lint status (ruff/eslint)
2. Type coverage (mypy/tsc)
3. Test coverage percentage
4. Security scan results
5. Code complexity metrics

## Output

Quality report with pass/fail status for each gate.
