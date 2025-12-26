<!--
Schedule swap workflow for faculty and resident shift exchanges.
Use when processing swap requests or finding compatible matches.
-->

Invoke the swap-management skill for swap operations.

## Arguments

- `$ARGUMENTS` - "find matches", "execute [swap_id]", or "status"

## Operations

1. Find compatible swap matches
2. Validate swap maintains compliance
3. Execute approved swaps
4. Rollback within 24-hour window

## Match Criteria

- Both parties available
- No ACGME violations created
- Coverage maintained
- Skill requirements met
