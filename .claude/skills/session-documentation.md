# Session Documentation Skill

Generate comprehensive session documentation for Claude Code web consumption.

---

## Purpose

After completing significant work sessions, create structured .md documentation that:
1. Captures what was accomplished
2. Documents domain knowledge learned
3. Provides reference material for future sessions
4. Enables Claude Code web to understand context

---

## Trigger Conditions

Use this skill when:
- Session involved multiple bug fixes or features
- New domain knowledge was captured from user
- Architecture or constraint changes were made
- Pre-push documentation is needed

---

## Documentation Template

### Session Summary (`docs/sessions/SESSION_YYYY-MM-DD_TOPIC.md`)

```markdown
# Session: [Topic]

**Date:** YYYY-MM-DD
**Branch:** [branch-name]
**Type:** [Bug Fix | Feature | Refactor | Documentation]

---

## Problem Statement

[What problem was being solved]

---

## Root Cause Analysis

[Why the problem existed]

---

## Solution

[What was implemented]

### Code Changes

[Key code snippets with file paths and line numbers]

---

## Domain Knowledge Captured

[User-provided context and business rules]

---

## Files Modified

[List of files with brief descriptions]

---

## Verification

[How the fix was verified]
```

---

## Architecture Reference Files

Create these when session involves system behavior:

### Activity Types (`docs/architecture/ACTIVITY_TYPES.md`)
- Classification table
- Solver handling rules
- Template examples

### Constraints (`docs/architecture/*_CONSTRAINTS.md`)
- Constraint class descriptions
- Registration requirements
- Validation rules

### Flow Diagrams (`docs/architecture/*_FLOW.md`)
- Mermaid diagrams
- Step-by-step process
- Error handling

---

## Required Sections

Every session doc MUST include:

1. **Problem Statement** - What was broken/needed
2. **Solution** - What was implemented
3. **Files Modified** - With line numbers
4. **Verification** - How it was tested
5. **Domain Knowledge** - User-provided context

---

## Parallel Documentation

Create multiple docs simultaneously:

```python
# Launch parallel file creation
Write(session_summary)
Write(architecture_reference_1)
Write(architecture_reference_2)
Write(architecture_reference_3)
```

---

## File Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Session | `SESSION_YYYY-MM-DD_TOPIC.md` | `SESSION_2025-12-26_IMMUTABLE_ASSIGNMENTS.md` |
| Architecture | `TOPIC.md` | `ACTIVITY_TYPES.md` |
| Constraints | `*_CONSTRAINTS.md` | `FMIT_CONSTRAINTS.md` |
| Flow | `*_FLOW.md` | `ENGINE_ASSIGNMENT_FLOW.md` |

---

## Post-Documentation Checklist

After creating docs:
- [ ] All .md files created in appropriate directories
- [ ] Cross-references added between related docs
- [ ] Code snippets include file paths
- [ ] Domain knowledge captured accurately
- [ ] Ready for git commit

---

## Integration with Other Skills

- **changelog-generator** - Use session docs as input
- **pr-reviewer** - Reference docs in PR description
- **code-review** - Check docs match code changes
