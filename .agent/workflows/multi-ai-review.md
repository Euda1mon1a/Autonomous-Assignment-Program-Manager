---
description: Multi-AI development and review workflow using Claude and Codex
---

# Multi-AI Review Workflow

This workflow establishes a two-AI pattern for development and independent review.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Direction)                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│               CLAUDE (Implementation)                        │
│      Antigravity IDE / Claude Code - file/terminal access   │
│      - Writes code                                          │
│      - Runs tests                                           │
│      - Commits changes                                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            CODEX (Independent Review)                        │
│          OpenAI CLI - `codex` command                        │
│          - Reviews code for bugs                            │
│          - Checks security issues                           │
│          - Suggests improvements                            │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
                    Iterate/Merge
```

---

## When to Use This Workflow

- After completing a significant feature
- Before merging a PR
- When debugging complex issues
- For security-sensitive changes

---

## Codex Review Commands

### Basic Review
```bash
# Review a specific file
codex "Review backend/app/services/swap.py for bugs and security issues"

# Review recent changes
codex "Review the changes in $(git diff --name-only HEAD~1) for issues"

# Review with specific focus
codex "Review backend/app/api/routes/auth.py focusing on authentication security"
```

### Targeted Reviews
```bash
# Security review
codex "Security audit: Check for SQL injection, XSS, and auth bypass in backend/app/api/"

# Performance review
codex "Review backend/app/scheduling/engine.py for performance issues and N+1 queries"

# ACGME compliance review
codex "Verify backend/app/scheduling/acgme_validator.py correctly implements 80-hour rule"
```

### Full PR Review
```bash
# Review all changes in current branch vs main
codex "Review all changes between main and HEAD for bugs, security issues, and code quality"
```

---

## Review Checklist

### Claude Implementation Phase
- [ ] Code follows project architecture
- [ ] Tests written and passing
- [ ] Linting/formatting passes
- [ ] No security warnings

### Codex Review Phase
- [ ] No logic errors identified
- [ ] No security vulnerabilities found
- [ ] No performance issues flagged
- [ ] Code is maintainable

### Post-Review
- [ ] Address Codex feedback
- [ ] Re-run tests
- [ ] Commit with review notes
- [ ] Ready for merge

---

## Example Session

### 1. Claude Implements Feature
```
User: Add a new endpoint to check schedule conflicts

Claude: [Implements endpoint, writes tests, runs pytest]
        Created: backend/app/api/routes/conflicts.py
        Created: backend/tests/test_conflicts.py
        Tests: 5/5 passing
```

### 2. Codex Reviews
```bash
codex "Review backend/app/api/routes/conflicts.py and backend/tests/test_conflicts.py for bugs and security"
```

### 3. Codex Output
```
Review of conflicts.py:

1. SECURITY: Line 45 - Input validation missing for date parameters
   Recommendation: Add Pydantic validation for start_date/end_date

2. BUG: Line 78 - Possible race condition when checking overlapping assignments
   Recommendation: Use database-level locking or transaction isolation

3. STYLE: Line 92 - Function exceeds 50 lines, consider extracting helper
   Recommendation: Extract conflict detection logic to service layer
```

### 4. Claude Fixes
```
User: Apply Codex recommendations

Claude: [Makes fixes based on review]
        - Added date validation schema
        - Added select_for_update() to prevent race condition
        - Extracted _detect_overlaps() to service layer
        Tests: 5/5 passing
```

### 5. Final Codex Check
```bash
codex "Re-review backend/app/api/routes/conflicts.py - verify previous issues fixed"
```

---

## Codex Configuration

Codex is an interactive CLI tool. No project-level config file is supported.

### Installation
```bash
# Via npm (if available)
npm install -g @openai/codex-cli

# Or via pip
pip install openai-codex
```

### Environment
```bash
# Set API key
export OPENAI_API_KEY="your-key-here"
```

### Tips
- Keep reviews focused (one file or small set of files)
- Be specific about what to look for
- Use for second opinion, not primary development
- Combine with Claude's implementation for best results

---

## Integration with Hooks

The Claude Code hooks can trigger Codex review:

```bash
# In .claude/hooks/stop-verify.sh (optional enhancement)
# Suggest Codex review if significant changes were made

CHANGED_FILES=$(git diff --name-only HEAD~1 2>/dev/null | wc -l)
if [ "$CHANGED_FILES" -gt 5 ]; then
    echo "Tip: Consider running Codex review on your changes"
    echo "  codex 'Review changes in $(git diff --name-only HEAD~1)'"
fi
```

---

## Limitations

### Codex Cannot:
- Edit files directly (provides recommendations only)
- Run tests or commands
- Access git history (must be provided context)
- Maintain conversation state between calls

### Best Practices:
- Use Claude for implementation, Codex for review
- Don't expect Codex to make changes
- Copy relevant context into Codex prompts
- Treat Codex output as suggestions, not commands
