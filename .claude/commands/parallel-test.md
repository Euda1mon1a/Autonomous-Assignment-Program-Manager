<!--
Parallel test execution across backend, frontend, and integration domains.
Maintains quality gates with domain-specific validators.
Use when running comprehensive test suites or verifying changes across codebase.
-->

Arguments: $ARGUMENTS

---

## Overview

This command runs tests in parallel across backend (pytest), frontend (jest), and integration (e2e) domains while maintaining quality gates.

## Usage

```
/parallel-test                           # Run all tests
/parallel-test backend/app/services/     # Test specific path
/parallel-test --coverage=80             # Enforce coverage threshold
/parallel-test --quick                   # Fast subset only
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--coverage` | 0 | Minimum coverage % required |
| `--quick` | false | Run only fast tests |
| `--domain` | all | Limit to backend/frontend/e2e |
| `--parallel` | 3 | Max parallel test runners |

## Behavior

1. **Detect Scope** - Identify affected test domains:
   ```
   backend/   -> pytest
   frontend/  -> jest
   tests/e2e/ -> playwright
   ```

2. **Spawn Test Runners** - Parallel execution:
   ```
   Task: "Run pytest backend/tests/ -x --tb=short"
   Task: "Run npm test in frontend/"
   Task: "Run playwright tests if integration affected"
   ```

3. **Aggregate Results** - Combine pass/fail/skip counts

4. **Quality Gate** - Check thresholds:
   - Coverage meets minimum
   - No new failures
   - Skipped tests documented

## Example Output

```
## Test Results

| Domain | Pass | Fail | Skip | Coverage |
|--------|------|------|------|----------|
| Backend | 342 | 0 | 12 | 78% |
| Frontend | 156 | 1 | 8 | 72% |
| E2E | 24 | 0 | 0 | N/A |

### Failures
- frontend/src/components/CallCard.test.tsx:45
  Expected: "Dec 30, 2025" Received: "12/30/2025"

### Quality Gate: WARN
- Frontend coverage below 75% target
- 1 test failure requires attention
```

## Model Selection

Test runners use `haiku` (execution, not reasoning).

## Related Commands

- `/parallel-explore` - Codebase exploration
- `/parallel-implement` - Multi-agent implementation
- `/handoff-session` - Multi-terminal coordination
