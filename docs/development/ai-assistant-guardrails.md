# AI Assistant Guardrails

> **Purpose:** Prevent conflicts when using multiple AI coding assistants (Claude Code, GitHub Copilot, Codex, etc.) on the same Git branch
>
> **Audience:** Developers who use multiple AI tools in their IDE workflow

---

## The Problem: AI Assistant Collision

When you run **multiple AI assistants on the same branch simultaneously**, bad things happen:

| Issue | What Goes Wrong |
|-------|-----------------|
| **Overlapping Edits** | Two AIs edit the same file at once, creating merge conflicts |
| **Hidden Conflicts** | Changes look fine separately but break when combined |
| **Duplicated Fixes** | Both AIs "fix" the same issue differently |
| **Unstable Diffs** | `git diff` becomes unreadable with interleaved changes |
| **Lost Context** | Each AI doesn't know what the other did |

### Real Example

```
You: "Fix the login bug" (to Claude Code)
You: "Review my code" (to Copilot)
Result: Claude edits auth.py while Copilot suggests changes to the same file
        → Merge conflict, wasted time, frustration
```

---

## The Solution: Intentional Workflow Separation

### Recommended Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI ASSISTANT WORKFLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CLAUDE CODE (Primary Builder)                              │
│     └─► Works on: feature/my-feature.claude                   │
│     └─► Does: Implementation, bug fixes, new code              │
│                                                                 │
│  2. HUMAN CONSOLIDATION                                         │
│     └─► Review changes, merge to feature/my-feature            │
│     └─► Run tests, verify nothing is broken                    │
│                                                                 │
│  3. CODEX/COPILOT (Secondary Reviewer)                         │
│     └─► Works on: feature/my-feature.review OR same branch     │
│     └─► Does: Code review, suggestions, improvements           │
│     └─► ONLY after Claude's work is committed                  │
│                                                                 │
│  4. HUMAN FINAL ARBITER                                         │
│     └─► Consolidate all changes                                │
│     └─► Create PR for merge to main                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Rules for Safe Multi-AI Usage

### Rule 1: One AI Per Branch at a Time

**DO NOT** run two AI agents making edits on the same branch in parallel.

```bash
# BAD: Both running on feature/login-fix
Claude Code → editing auth.py
Copilot     → editing auth.py (at the same time!)

# GOOD: Sequential or separate branches
Claude Code → feature/login-fix         # Claude finishes first
Copilot     → feature/login-fix.review  # Then Copilot reviews
```

### Rule 2: Check Before Continuing

If another AI has edited this branch in the last N commits, **pause and review** before continuing.

```bash
# Run the checker script before starting work
python scripts/check-ai-assistant-usage.py

# If you see a warning like:
# ⚠️  WARNING: Mixed AI commits detected on this branch
# Then stop and consolidate before continuing
```

### Rule 3: Use Branch Suffixes

Prefer assistant-specific branches over sharing:

```
feature/xyz           # Human-only or primary AI
feature/xyz.claude    # Claude Code working branch
feature/xyz.codex     # Codex review branch
feature/xyz.review    # Generic review branch
```

### Rule 4: Human Consolidation Commits

After an AI finishes work, make a human "consolidation" commit:

```bash
# After Claude finishes
git add .
git commit -m "consolidate: review Claude's login implementation"

# Now it's safe for another AI to work on this branch
```

---

## Pre-Session Checklist

Before starting any AI coding session, check these items:

### Quick Scan (30 seconds)

- [ ] **Branch Name**: Am I on the right branch? Does it match my active assistant?
- [ ] **Last Commit**: Who made the last commit? (`git log -1`)
- [ ] **Which AI**: Is the right AI assistant active? (Close others)
- [ ] **Clean State**: Is my working directory clean? (`git status`)

### Full Check (Use the Script)

```bash
# Run the automated checker
python scripts/check-ai-assistant-usage.py

# For strict mode (exits with error if problems found)
python scripts/check-ai-assistant-usage.py --strict
```

---

## Using the Checker Script

### Installation

The script is already in the repo at `scripts/check-ai-assistant-usage.py`.

### Basic Usage

```bash
# Check current branch
python scripts/check-ai-assistant-usage.py

# Strict mode (for CI/hooks)
python scripts/check-ai-assistant-usage.py --strict

# Check more commits (default is 20)
python scripts/check-ai-assistant-usage.py --commits 50

# Quiet mode (only show warnings)
python scripts/check-ai-assistant-usage.py --quiet
```

### What It Checks

1. **Interleaved AI Commits**: Detects patterns like `claude → codex → claude` without human consolidation
2. **Recent AI Activity**: Warns if another AI was recently active
3. **Uncommitted Changes**: Alerts if there are pending changes that could conflict

### Output Examples

**Clean State:**
```
✓ Branch: feature/add-login
✓ Last 20 commits checked
✓ No mixed AI assistant patterns detected
✓ Safe to proceed with any AI assistant
```

**Warning State:**
```
⚠️  WARNING: Mixed AI commits detected!

Recent commits:
  [claude] fix: resolve auth redirect
  [codex]  chore: update dependencies  ← Different AI
  [claude] feat: add login form

Recommendation:
  1. Review the interleaved changes
  2. Create a consolidation commit: git commit --allow-empty -m "consolidate: reviewed mixed AI changes"
  3. Then continue with your preferred AI
```

---

## Optional: Git Hook

For automatic checking, you can install the pre-commit hook:

```bash
# Copy the hook template
cp hooks/pre-commit-ai-guardrails.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

This will warn you (but not block) before each commit if AI mixing is detected.

---

## Commit Message Conventions

Use these prefixes so the checker can identify AI commits:

| Prefix | Meaning | Example |
|--------|---------|---------|
| `feat(claude):` | Claude Code feature | `feat(claude): add user dashboard` |
| `fix(claude):` | Claude Code bug fix | `fix(claude): resolve null pointer` |
| `feat(codex):` | Codex/Copilot feature | `feat(codex): optimize query` |
| `fix(codex):` | Codex/Copilot fix | `fix(codex): fix typo in docs` |
| `consolidate:` | Human review point | `consolidate: verified Claude's work` |
| `refactor(human):` | Human refactoring | `refactor(human): cleanup after AI` |

### Auto-Detection

The script also looks for these patterns in commit messages:
- `🤖 Generated by Claude` / `Claude Code`
- `Co-authored-by: Claude` / `Copilot` / `Codex`
- Branch names ending in `.claude`, `.codex`, etc.

---

## FAQ

### Q: Can I use Copilot autocomplete while Claude Code is running?

**A:** Yes, for small completions. Copilot's inline suggestions are typically single-line and won't conflict. The risk is with larger "chat" or "agent" modes that make multi-file changes.

### Q: What if I accidentally ran both AIs?

**A:**
1. Stop both AIs
2. Run `git status` and `git diff` to see what changed
3. Review changes carefully
4. Either:
   - Keep all changes if they don't conflict
   - `git stash` one set and re-apply manually
   - `git checkout -- <file>` to discard conflicting changes

### Q: Do I need to use the branch suffix convention?

**A:** No, it's optional but recommended. The key is to not run multiple AIs simultaneously, regardless of branch naming.

### Q: How do I know which AI made a change?

**A:**
1. Check commit message prefixes (if you follow the convention)
2. Look for AI signatures in commit metadata
3. Review git log for patterns

---

## Integration with Existing Workflows

This guardrail system is designed to complement the existing [AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md):

- **Environment Detection**: Both docs emphasize checking context before editing
- **Branch Safety**: Both require feature branches for changes
- **Human Review**: Both require human approval before merging to main

---

## Related Documentation

- [AI Rules of Engagement](AI_RULES_OF_ENGAGEMENT.md) - Core AI agent rules
- [Git Safe Sync Checklist](CLAUDE_GIT_SAFE_SYNC_CHECKLIST.md) - Daily sync procedures
- [AI Interface Guide](../admin-manual/ai-interface-guide.md) - Web vs CLI comparison
