<!--
Automated IT helper for detecting and fixing code issues.
Use when code fails tests, linting, type-checking, or has security vulnerabilities.
-->

Invoke the automated-code-fixer skill to detect and fix code issues.

## Arguments

- `$ARGUMENTS` - File path, error message, or description of issue to fix

## Process

1. Analyze the error or issue provided
2. Identify root cause (lint, type, test, security)
3. Apply automated fix if possible
4. Run quality gates to verify fix
5. Report what was fixed

## Quality Gates

- Ruff lint check passes
- Type checking passes (mypy/tsc)
- Related tests pass
- No security vulnerabilities introduced
