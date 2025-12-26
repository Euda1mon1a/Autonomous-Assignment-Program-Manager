<!--
Document the current session's work for handoff or reference.
Creates comprehensive .md files for Claude Code web consumption.
-->

Invoke the session-documentation skill.

## Arguments

- `$ARGUMENTS` - Session focus or "auto" to detect from context

## Process

1. **Analyze Session**
   - Review git commits on current branch
   - Identify files modified
   - Extract domain knowledge from conversation

2. **Create Documentation** (parallel)
   - Session summary: `docs/sessions/SESSION_YYYY-MM-DD_TOPIC.md`
   - Architecture references: `docs/architecture/*.md` (as needed)
   - Development guides: `docs/development/*.md` (as needed)

3. **Include Required Sections**
   - Problem Statement
   - Solution with code snippets
   - Files Modified with line numbers
   - Domain Knowledge captured
   - Verification steps

## Output

Creates session document(s) in appropriate directories:
- `docs/sessions/` - Session summaries
- `docs/architecture/` - Technical references
- `docs/development/` - Developer guides

## Example

```
/document-session immutable-assignments
```

Creates:
- `docs/sessions/SESSION_2025-12-26_IMMUTABLE_ASSIGNMENTS.md`
- `docs/architecture/ACTIVITY_TYPES.md`
- `docs/architecture/ENGINE_ASSIGNMENT_FLOW.md`

## Related Skills

- session-documentation
- changelog-generator
