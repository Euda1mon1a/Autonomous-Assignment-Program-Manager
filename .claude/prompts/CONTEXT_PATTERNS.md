# Context Management Patterns

> **Last Updated:** 2025-12-31
> **Purpose:** Strategies for efficiently managing context in multi-turn conversations

---

## Table of Contents

1. [Context Compression](#context-compression)
2. [Context Prioritization](#context-prioritization)
3. [Context Handoff](#context-handoff)
4. [Multi-Turn Patterns](#multi-turn-patterns)
5. [Session Continuity](#session-continuity)
6. [Parallel Context Management](#parallel-context-management)
7. [Context Recovery](#context-recovery)
8. [Validation Patterns](#validation-patterns)
9. [Common Pitfalls](#common-pitfalls)
10. [Tools and Techniques](#tools-and-techniques)

---

## Context Compression

### When to Compress Context

Compress context when:
- Session has been running > 30 minutes
- Used 30%+ of token budget
- Working on distinct problem areas
- Need fresh context for next major task

### Compression Levels

#### Level 0: No Compression
- Keep all context
- Use when: Fresh session, simple task
- Token cost: Highest

#### Level 1: Light Compression
- Remove verbose tool output
- Keep code snippets
- Summarize long discussions

**Pattern:**
```
Instead of: Full tool output with 50 lines of debug info
Use: "Tool confirmed [result]: [one-liner summary]"

Tool output analysis:
- Keep: Final result, key findings
- Remove: Intermediate steps, repetition
- Keep: File paths, line numbers
```

**Example:**
```
BEFORE (verbose):
Tool output:
Lines 1-45: Debug output...
Lines 46-50: Actual result: "Found 3 issues in file.py"

AFTER (compressed):
Found 3 issues in /path/to/file.py: [issue1, issue2, issue3]
```

#### Level 2: Aggressive Compression
- Summarize entire sections
- Remove intermediate findings
- Keep only actionable insights

**Pattern:**
```
Instead of: Details of exploration process
Use: Summary of findings

Example:
"Explored 5 files, narrowed issue to database query caching.
Root cause: N+1 query in Assignment.get_by_schedule() at line 45."
```

### Compression Techniques

#### 1. Summarization
```
VERBOSE:
- Checked file A: No issues found
- Checked file B: Found issue X at line 42
- Checked file C: No issues found
- Checked file D: No issues found
- Checked file E: Found issue Y at line 156

COMPRESSED:
Checked 5 files. Issues found:
- file B, line 42: [issue X]
- file E, line 156: [issue Y]
```

#### 2. De-duplication
```
VERBOSE:
Tool found 3 instances of pattern X
Tool confirmed pattern X exists in file 1
Tool confirmed pattern X exists in file 2
Tool confirmed pattern X exists in file 3

COMPRESSED:
Found pattern X in 3 files: [file1, file2, file3]
```

#### 3. Code Snippet Replacement
```
VERBOSE:
The entire function (40 lines) displayed

COMPRESSED:
Function getSchedule() at /path/to/file.py:45-85
[Relevant snippet showing issue at lines 67-72]
```

#### 4. Timeline Flattening
```
VERBOSE:
Phase 1: Explored A, found nothing
Phase 2: Explored B, found X
Phase 3: Explored C, found Y
Phase 4: Explored D, confirmed root cause

COMPRESSED:
Exploration found root cause in B/C, confirmed in D
Issue: [specific issue]
```

### When Not to Compress
- Working in deeply nested recursion (keep trace visible)
- Debugging subtle bugs (need all details)
- First interaction on new codebase (need full context)
- Security-critical changes (need full audit trail)

---

## Context Prioritization

### Priority Levels

#### Priority 1: Always Keep
- Current task objective
- File paths being modified
- Test results (pass/fail)
- Error messages
- Critical decisions
- Approval/permission states

#### Priority 2: Keep Unless Compressing
- Code snippets (>50 lines)
- Detailed exploration steps
- Full tool output
- Discussion context

#### Priority 3: Safe to Remove
- Intermediate thoughts
- Verbose logging
- Duplicate information
- Superseded findings
- Acknowledgments

### Prioritization Matrix

| Content | New Session | Mid-Session | Long Session |
|---------|------------|-------------|--------------|
| Current task | KEEP | KEEP | KEEP |
| File paths | KEEP | KEEP | KEEP |
| Test results | KEEP | KEEP | KEEP |
| Error messages | KEEP | KEEP | KEEP |
| Code snippets | KEEP | KEEP | Summarize |
| Exploration steps | KEEP | Keep key | Remove |
| Tool output | KEEP | Summary | Remove |
| Discussion | Keep recent | Recent only | Summary |

### Extraction Strategy

#### What to Extract When Compressing

```markdown
## Session Summary

### Current Objective
[What we're trying to accomplish]

### Key Files
- /path/to/file1.py - [Purpose]
- /path/to/file2.py - [Purpose]

### Critical Findings
1. [Finding 1 with impact]
2. [Finding 2 with impact]
3. [Finding 3 with impact]

### Root Causes Identified
[List of root causes]

### Current Status
[Where we are in the task]

### Next Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

---

## Context Handoff

### Handoff Pattern

Use when delegating to another agent or session:

#### Complete Handoff

```markdown
## Handoff Document: [Task Name]

### Background
[Context for why this task exists]

### Objective
[Specific goal to accomplish]

### Current Status
- Progress: [What's been done]
- Current location: [What file/component]
- Blockers: [Any blocks]

### Key Files
- [File 1]: [Purpose]
- [File 2]: [Purpose]

### Important Findings
1. [Key insight 1]
2. [Key insight 2]
3. [Key insight 3]

### Architecture Context
[How this fits in the system]

### Known Issues
[Anything learned that's important]

### Next Actions
1. [Action 1]
2. [Action 2]
3. [Action 3]

### Questions for Next Agent
[Open questions requiring investigation]

### Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]
```

### Minimal Handoff

When time is limited:

```markdown
## Quick Handoff: [Task]

**What:** [One sentence]
**Why:** [One sentence]
**Where:** [File path]
**Status:** [Current state]
**Next:** [One action needed]
```

### Handoff Validation

Verify handoff is complete:
- [ ] Objective is clear
- [ ] Current status is unambiguous
- [ ] Key files identified
- [ ] Next actions specified
- [ ] Success criteria defined
- [ ] No ambiguous pronouns

---

## Multi-Turn Patterns

### Turn Structure

#### Turn 1: Setup
```
"Read [file] and analyze [problem].
Don't fix anything yet, just understand the system."
```

#### Turn 2: Planning
```
"Think hard about [problem].
Create hypothesis list with root cause analysis."
```

#### Turn 3: Implementation
```
"Implement solution for [problem].
After each change, verify logic handles edge cases."
```

#### Turn 4: Validation
```
"Write tests verifying the fix works correctly.
Run tests and confirm all pass."
```

#### Turn 5: Completion
```
"Commit changes and update documentation.
Provide summary of what was fixed."
```

### Context Retention Strategy

After each turn:
1. **Before processing next turn:** Remove turn output from context
2. **Keep from previous turn:** Key findings, decisions, file paths
3. **Add to next turn:** Previous findings as context for next phase

### Pattern: Explore → Plan → Implement → Test

```
Turn 1 - EXPLORE:
"Read [file] and examine [error].
Don't fix anything yet."

[Output: Understanding of the issue]

---

Turn 2 - PLAN (compress Turn 1 output):
"Given the issue in [file] at [lines]:
Think hard about solutions.
Create ranked list of options."

[Output: Plan with rationale]

---

Turn 3 - IMPLEMENT (compress Turns 1-2):
"Implement option 1: [description]
[File] needs changes at [lines]"

[Output: Fixed code]

---

Turn 4 - TEST:
"Write tests for the fix in [file].
Verify tests pass."

[Output: Tests + results]
```

---

## Session Continuity

### Session Start

Check these before proceeding:

```bash
# 1. Current branch and status
git branch --show-current
git status

# 2. Recent commits
git log --oneline -5

# 3. Open PRs
gh pr list --state open

# 4. Test status
pytest --co -q | head -20  # List tests without running
```

### Between-Turn Context

Maintain:
- Current file being edited
- Line numbers of changes
- Test status
- Error conditions

Don't keep:
- Verbose tool output
- Intermediate exploration steps
- Temporary findings

### Session End

Prepare handoff:
```markdown
## Session Handoff: [Task]

### Completed
- [ ] [Item 1]
- [ ] [Item 2]

### In Progress
- [ ] [Item 1]

### Blocked On
- [ ] [Blocker 1]

### Files Modified
- [File 1]: [Changes]
- [File 2]: [Changes]

### Tests
- Passing: [N]
- Failing: [N]
- Not run: [N]

### Next Session Should
1. [Action 1]
2. [Action 2]
3. [Action 3]
```

---

## Parallel Context Management

### Managing Multiple Agents

When running parallel agents:

#### Agent A Context
```
Task: [Task A]
Files: [List A]
Status: [Current state A]
Blockers: [Any blocks A]
```

#### Agent B Context
```
Task: [Task B]
Files: [List B]
Status: [Current state B]
Blockers: [Any blocks B]
```

#### Coordination Notes
```
Shared resources: [None/Resource X]
Dependencies: [Task A must complete before B]
Merge strategy: [How to combine results]
```

### Context Isolation

Ensure agents can work independently:
- Don't share file context between agents
- Each agent has its own working hypothesis
- Results synchronized after completion

### Merge Pattern

After parallel work:

```markdown
## Merge from [Agent A] and [Agent B]

### From Agent A
- Files modified: [List]
- Tests: [Status]
- Changes: [Summary]

### From Agent B
- Files modified: [List]
- Tests: [Status]
- Changes: [Summary]

### Conflicts
- [File X]: [Conflict description]
- [File Y]: [Conflict description]

### Resolution
1. Keep from A, modifications from B: [File X]
2. Keep from B, modifications from A: [File Y]

### Verification
- [ ] All tests passing
- [ ] No merge conflicts
- [ ] File integrity verified
```

---

## Context Recovery

### Recovering Lost Context

If context gets truncated/lost:

#### Strategy 1: Git Reconstruction
```bash
# Recover recent commits
git log --oneline -10

# Recover current changes
git diff HEAD

# Recover untracked files
git status --porcelain
```

#### Strategy 2: File System Reconstruction
```bash
# Last modified files
find /path -type f -mmin -60 | sort -t. -k1 -n

# Recent git history
git reflog -10
```

#### Strategy 3: Documentation Reconstruction
```markdown
## What to recover

1. What files were being modified?
   - Check git status and diff

2. What was the objective?
   - Check HUMAN_TODO.md or similar

3. What errors occurred?
   - Check recent commit messages
   - Check test failures

4. What's the current status?
   - Run tests
   - Check git diff
```

### Prevention Strategies

#### 1. Regular Checkpoints
```
After each major step:
git add [files]
git commit -m "WIP: [brief description]"
```

#### 2. Documentation
```
Keep running log:
.claude/session-notes.md
- What we're doing
- Key findings
- Next steps
```

#### 3. State Capture
```
Before major operations:
git stash push -m "WIP: [description]"
```

---

## Validation Patterns

### Context Health Check

```markdown
## Context Validation Checklist

- [ ] Objective is clear and achievable
- [ ] Current status is unambiguous
- [ ] Key files are identified
- [ ] No conflicting information
- [ ] Decisions are documented
- [ ] Next steps are clear
- [ ] No ambiguous pronouns ("it", "this")
- [ ] File paths are absolute
- [ ] Tests are in known state
```

### Ambiguity Detection

Watch for:
- "It should..." - What is "it"?
- "This file..." - Which file?
- "After we..." - Who is "we"?
- "The issue" - Which issue?
- "They said..." - Who is "they"?

Fix by being explicit:
- "File /path/to/file.py should..."
- "The issue in line 45 of schedule.py..."
- "The test framework requires..."

### Consistency Check

```
Questions to ask about context:

1. Do all file paths match?
   - Git paths consistent?
   - Absolute paths used?

2. Do findings agree?
   - Earlier findings contradict new findings?
   - Need to revisit assumptions?

3. Is status clear?
   - Are we in an unknown state?
   - Do we need to verify state?

4. Are decisions documented?
   - Why did we choose X over Y?
   - Can we explain rationale?
```

---

## Common Pitfalls

### Pitfall 1: Context Pollution

**Problem:** Mixing old and new information

**Solution:**
```
When starting new task:
"Start fresh. Previous context about [OLD_TASK] can be discarded.
New task: [NEW_TASK]"
```

### Pitfall 2: Ambiguous Pronouns

**Bad:**
"After reading the file, it should be modified"

**Good:**
"After reading /path/to/file.py, the function getSchedule() at line 45 should be modified"

### Pitfall 3: Lost Requirements

**Prevention:**
```
At session start, capture requirements:

## Session Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

Don't let these scroll out of context.
Reference them regularly.
```

### Pitfall 4: Forgotten Test Status

**Solution:**
```
After each code change:

## Test Status
- Unit tests: [PASS/FAIL]
- Integration tests: [PASS/FAIL]
- Type checking: [PASS/FAIL]
- Linting: [PASS/FAIL]

Don't assume tests still pass.
Verify after each significant change.
```

### Pitfall 5: Context Explosion

**Prevention:**
```
When session approaches 40% token usage:
1. Document key findings
2. Compress verbose sections
3. Summarize progress
4. Create handoff document

Don't wait until context is exhausted.
Compress proactively.
```

---

## Tools and Techniques

### Context Markers

Use these phrases to manage context:

```
"Keep this context:" [Important info to preserve]

"Discard previous context about:" [Old info to remove]

"Compressed from:" [Abbreviate long section]

"Required context:" [Info needed to proceed]

"Optional context:" [Nice to have but not critical]
```

### Context Logging

Create running log in session:

```markdown
## Context Log

- Turn 1: Explored database queries, found N+1 issue
- Turn 2: Planned solution using eager loading
- Turn 3: Implemented fix in file X
- Turn 4: Added tests, all passing
- Turn 5: Committed and closing task
```

### Context Snapshots

Save periodically:

```
## Snapshot at Turn [N]

Current file: [path]
Current line: [number]
Test status: [PASS/FAIL]
Blockers: [None/List]
Progress: [X% complete]
```

### Context Checklist

Before major task:
```
- [ ] Read full objective
- [ ] Verified file paths
- [ ] Checked git status
- [ ] Run baseline tests
- [ ] Understand current state
- [ ] Know success criteria
```

---

## Quick Reference

### Compression Decision Tree

```
Is context getting too large?
├─ YES: Are we stuck?
│  ├─ YES → Compress aggressively, create handoff
│  └─ NO → Compress moderately, continue
└─ NO → Keep full context, continue
```

### Handoff Decision Tree

```
Need to hand off to another agent?
├─ YES: Is this a clean break point?
│  ├─ YES → Create complete handoff
│  └─ NO → Create partial handoff
└─ NO → Stay in session
```

### Context Recovery Decision Tree

```
Did context get truncated?
├─ YES: Can we recover from git?
│  ├─ YES → Use git reconstruction
│  └─ NO → Use handoff document
└─ NO → Continue normally
```

---

## Session Context Template

Use this at the start of each session:

```markdown
# Session Context: [Date]

## Objective
[One sentence about what we're doing]

## Background
[Why are we doing this?]

## Scope
[What's included/excluded]

## Key Files
- [File 1]: [Purpose]
- [File 2]: [Purpose]

## Known Issues
- [Issue 1]: [Impact]
- [Issue 2]: [Impact]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

## Progress Tracking
[Updated after each major step]

## Decisions Made
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]

## Next Session Should
1. [Action 1]
2. [Action 2]
```

---

## Performance Notes

- Compress context when approaching 30% token budget
- Keep critical information even when compressing
- Validate context consistency regularly
- Use clear handoff documents for agent transitions
- Document decisions and rationale for future reference

