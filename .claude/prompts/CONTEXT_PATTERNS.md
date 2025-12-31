***REMOVED*** Context Management Patterns

> **Last Updated:** 2025-12-31
> **Purpose:** Strategies for efficiently managing context in multi-turn conversations

---

***REMOVED******REMOVED*** Table of Contents

1. [Context Compression](***REMOVED***context-compression)
2. [Context Prioritization](***REMOVED***context-prioritization)
3. [Context Handoff](***REMOVED***context-handoff)
4. [Multi-Turn Patterns](***REMOVED***multi-turn-patterns)
5. [Session Continuity](***REMOVED***session-continuity)
6. [Parallel Context Management](***REMOVED***parallel-context-management)
7. [Context Recovery](***REMOVED***context-recovery)
8. [Validation Patterns](***REMOVED***validation-patterns)
9. [Common Pitfalls](***REMOVED***common-pitfalls)
10. [Tools and Techniques](***REMOVED***tools-and-techniques)

---

***REMOVED******REMOVED*** Context Compression

***REMOVED******REMOVED******REMOVED*** When to Compress Context

Compress context when:
- Session has been running > 30 minutes
- Used 30%+ of token budget
- Working on distinct problem areas
- Need fresh context for next major task

***REMOVED******REMOVED******REMOVED*** Compression Levels

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 0: No Compression
- Keep all context
- Use when: Fresh session, simple task
- Token cost: Highest

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 1: Light Compression
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

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 2: Aggressive Compression
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

***REMOVED******REMOVED******REMOVED*** Compression Techniques

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Summarization
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

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. De-duplication
```
VERBOSE:
Tool found 3 instances of pattern X
Tool confirmed pattern X exists in file 1
Tool confirmed pattern X exists in file 2
Tool confirmed pattern X exists in file 3

COMPRESSED:
Found pattern X in 3 files: [file1, file2, file3]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Code Snippet Replacement
```
VERBOSE:
The entire function (40 lines) displayed

COMPRESSED:
Function getSchedule() at /path/to/file.py:45-85
[Relevant snippet showing issue at lines 67-72]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Timeline Flattening
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

***REMOVED******REMOVED******REMOVED*** When Not to Compress
- Working in deeply nested recursion (keep trace visible)
- Debugging subtle bugs (need all details)
- First interaction on new codebase (need full context)
- Security-critical changes (need full audit trail)

---

***REMOVED******REMOVED*** Context Prioritization

***REMOVED******REMOVED******REMOVED*** Priority Levels

***REMOVED******REMOVED******REMOVED******REMOVED*** Priority 1: Always Keep
- Current task objective
- File paths being modified
- Test results (pass/fail)
- Error messages
- Critical decisions
- Approval/permission states

***REMOVED******REMOVED******REMOVED******REMOVED*** Priority 2: Keep Unless Compressing
- Code snippets (>50 lines)
- Detailed exploration steps
- Full tool output
- Discussion context

***REMOVED******REMOVED******REMOVED******REMOVED*** Priority 3: Safe to Remove
- Intermediate thoughts
- Verbose logging
- Duplicate information
- Superseded findings
- Acknowledgments

***REMOVED******REMOVED******REMOVED*** Prioritization Matrix

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

***REMOVED******REMOVED******REMOVED*** Extraction Strategy

***REMOVED******REMOVED******REMOVED******REMOVED*** What to Extract When Compressing

```markdown
***REMOVED******REMOVED*** Session Summary

***REMOVED******REMOVED******REMOVED*** Current Objective
[What we're trying to accomplish]

***REMOVED******REMOVED******REMOVED*** Key Files
- /path/to/file1.py - [Purpose]
- /path/to/file2.py - [Purpose]

***REMOVED******REMOVED******REMOVED*** Critical Findings
1. [Finding 1 with impact]
2. [Finding 2 with impact]
3. [Finding 3 with impact]

***REMOVED******REMOVED******REMOVED*** Root Causes Identified
[List of root causes]

***REMOVED******REMOVED******REMOVED*** Current Status
[Where we are in the task]

***REMOVED******REMOVED******REMOVED*** Next Steps
1. [Step 1]
2. [Step 2]
3. [Step 3]
```

---

***REMOVED******REMOVED*** Context Handoff

***REMOVED******REMOVED******REMOVED*** Handoff Pattern

Use when delegating to another agent or session:

***REMOVED******REMOVED******REMOVED******REMOVED*** Complete Handoff

```markdown
***REMOVED******REMOVED*** Handoff Document: [Task Name]

***REMOVED******REMOVED******REMOVED*** Background
[Context for why this task exists]

***REMOVED******REMOVED******REMOVED*** Objective
[Specific goal to accomplish]

***REMOVED******REMOVED******REMOVED*** Current Status
- Progress: [What's been done]
- Current location: [What file/component]
- Blockers: [Any blocks]

***REMOVED******REMOVED******REMOVED*** Key Files
- [File 1]: [Purpose]
- [File 2]: [Purpose]

***REMOVED******REMOVED******REMOVED*** Important Findings
1. [Key insight 1]
2. [Key insight 2]
3. [Key insight 3]

***REMOVED******REMOVED******REMOVED*** Architecture Context
[How this fits in the system]

***REMOVED******REMOVED******REMOVED*** Known Issues
[Anything learned that's important]

***REMOVED******REMOVED******REMOVED*** Next Actions
1. [Action 1]
2. [Action 2]
3. [Action 3]

***REMOVED******REMOVED******REMOVED*** Questions for Next Agent
[Open questions requiring investigation]

***REMOVED******REMOVED******REMOVED*** Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]
```

***REMOVED******REMOVED******REMOVED*** Minimal Handoff

When time is limited:

```markdown
***REMOVED******REMOVED*** Quick Handoff: [Task]

**What:** [One sentence]
**Why:** [One sentence]
**Where:** [File path]
**Status:** [Current state]
**Next:** [One action needed]
```

***REMOVED******REMOVED******REMOVED*** Handoff Validation

Verify handoff is complete:
- [ ] Objective is clear
- [ ] Current status is unambiguous
- [ ] Key files identified
- [ ] Next actions specified
- [ ] Success criteria defined
- [ ] No ambiguous pronouns

---

***REMOVED******REMOVED*** Multi-Turn Patterns

***REMOVED******REMOVED******REMOVED*** Turn Structure

***REMOVED******REMOVED******REMOVED******REMOVED*** Turn 1: Setup
```
"Read [file] and analyze [problem].
Don't fix anything yet, just understand the system."
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Turn 2: Planning
```
"Think hard about [problem].
Create hypothesis list with root cause analysis."
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Turn 3: Implementation
```
"Implement solution for [problem].
After each change, verify logic handles edge cases."
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Turn 4: Validation
```
"Write tests verifying the fix works correctly.
Run tests and confirm all pass."
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Turn 5: Completion
```
"Commit changes and update documentation.
Provide summary of what was fixed."
```

***REMOVED******REMOVED******REMOVED*** Context Retention Strategy

After each turn:
1. **Before processing next turn:** Remove turn output from context
2. **Keep from previous turn:** Key findings, decisions, file paths
3. **Add to next turn:** Previous findings as context for next phase

***REMOVED******REMOVED******REMOVED*** Pattern: Explore → Plan → Implement → Test

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

***REMOVED******REMOVED*** Session Continuity

***REMOVED******REMOVED******REMOVED*** Session Start

Check these before proceeding:

```bash
***REMOVED*** 1. Current branch and status
git branch --show-current
git status

***REMOVED*** 2. Recent commits
git log --oneline -5

***REMOVED*** 3. Open PRs
gh pr list --state open

***REMOVED*** 4. Test status
pytest --co -q | head -20  ***REMOVED*** List tests without running
```

***REMOVED******REMOVED******REMOVED*** Between-Turn Context

Maintain:
- Current file being edited
- Line numbers of changes
- Test status
- Error conditions

Don't keep:
- Verbose tool output
- Intermediate exploration steps
- Temporary findings

***REMOVED******REMOVED******REMOVED*** Session End

Prepare handoff:
```markdown
***REMOVED******REMOVED*** Session Handoff: [Task]

***REMOVED******REMOVED******REMOVED*** Completed
- [ ] [Item 1]
- [ ] [Item 2]

***REMOVED******REMOVED******REMOVED*** In Progress
- [ ] [Item 1]

***REMOVED******REMOVED******REMOVED*** Blocked On
- [ ] [Blocker 1]

***REMOVED******REMOVED******REMOVED*** Files Modified
- [File 1]: [Changes]
- [File 2]: [Changes]

***REMOVED******REMOVED******REMOVED*** Tests
- Passing: [N]
- Failing: [N]
- Not run: [N]

***REMOVED******REMOVED******REMOVED*** Next Session Should
1. [Action 1]
2. [Action 2]
3. [Action 3]
```

---

***REMOVED******REMOVED*** Parallel Context Management

***REMOVED******REMOVED******REMOVED*** Managing Multiple Agents

When running parallel agents:

***REMOVED******REMOVED******REMOVED******REMOVED*** Agent A Context
```
Task: [Task A]
Files: [List A]
Status: [Current state A]
Blockers: [Any blocks A]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Agent B Context
```
Task: [Task B]
Files: [List B]
Status: [Current state B]
Blockers: [Any blocks B]
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Coordination Notes
```
Shared resources: [None/Resource X]
Dependencies: [Task A must complete before B]
Merge strategy: [How to combine results]
```

***REMOVED******REMOVED******REMOVED*** Context Isolation

Ensure agents can work independently:
- Don't share file context between agents
- Each agent has its own working hypothesis
- Results synchronized after completion

***REMOVED******REMOVED******REMOVED*** Merge Pattern

After parallel work:

```markdown
***REMOVED******REMOVED*** Merge from [Agent A] and [Agent B]

***REMOVED******REMOVED******REMOVED*** From Agent A
- Files modified: [List]
- Tests: [Status]
- Changes: [Summary]

***REMOVED******REMOVED******REMOVED*** From Agent B
- Files modified: [List]
- Tests: [Status]
- Changes: [Summary]

***REMOVED******REMOVED******REMOVED*** Conflicts
- [File X]: [Conflict description]
- [File Y]: [Conflict description]

***REMOVED******REMOVED******REMOVED*** Resolution
1. Keep from A, modifications from B: [File X]
2. Keep from B, modifications from A: [File Y]

***REMOVED******REMOVED******REMOVED*** Verification
- [ ] All tests passing
- [ ] No merge conflicts
- [ ] File integrity verified
```

---

***REMOVED******REMOVED*** Context Recovery

***REMOVED******REMOVED******REMOVED*** Recovering Lost Context

If context gets truncated/lost:

***REMOVED******REMOVED******REMOVED******REMOVED*** Strategy 1: Git Reconstruction
```bash
***REMOVED*** Recover recent commits
git log --oneline -10

***REMOVED*** Recover current changes
git diff HEAD

***REMOVED*** Recover untracked files
git status --porcelain
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Strategy 2: File System Reconstruction
```bash
***REMOVED*** Last modified files
find /path -type f -mmin -60 | sort -t. -k1 -n

***REMOVED*** Recent git history
git reflog -10
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Strategy 3: Documentation Reconstruction
```markdown
***REMOVED******REMOVED*** What to recover

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

***REMOVED******REMOVED******REMOVED*** Prevention Strategies

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Regular Checkpoints
```
After each major step:
git add [files]
git commit -m "WIP: [brief description]"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Documentation
```
Keep running log:
.claude/session-notes.md
- What we're doing
- Key findings
- Next steps
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. State Capture
```
Before major operations:
git stash push -m "WIP: [description]"
```

---

***REMOVED******REMOVED*** Validation Patterns

***REMOVED******REMOVED******REMOVED*** Context Health Check

```markdown
***REMOVED******REMOVED*** Context Validation Checklist

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

***REMOVED******REMOVED******REMOVED*** Ambiguity Detection

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

***REMOVED******REMOVED******REMOVED*** Consistency Check

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

***REMOVED******REMOVED*** Common Pitfalls

***REMOVED******REMOVED******REMOVED*** Pitfall 1: Context Pollution

**Problem:** Mixing old and new information

**Solution:**
```
When starting new task:
"Start fresh. Previous context about [OLD_TASK] can be discarded.
New task: [NEW_TASK]"
```

***REMOVED******REMOVED******REMOVED*** Pitfall 2: Ambiguous Pronouns

**Bad:**
"After reading the file, it should be modified"

**Good:**
"After reading /path/to/file.py, the function getSchedule() at line 45 should be modified"

***REMOVED******REMOVED******REMOVED*** Pitfall 3: Lost Requirements

**Prevention:**
```
At session start, capture requirements:

***REMOVED******REMOVED*** Session Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

Don't let these scroll out of context.
Reference them regularly.
```

***REMOVED******REMOVED******REMOVED*** Pitfall 4: Forgotten Test Status

**Solution:**
```
After each code change:

***REMOVED******REMOVED*** Test Status
- Unit tests: [PASS/FAIL]
- Integration tests: [PASS/FAIL]
- Type checking: [PASS/FAIL]
- Linting: [PASS/FAIL]

Don't assume tests still pass.
Verify after each significant change.
```

***REMOVED******REMOVED******REMOVED*** Pitfall 5: Context Explosion

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

***REMOVED******REMOVED*** Tools and Techniques

***REMOVED******REMOVED******REMOVED*** Context Markers

Use these phrases to manage context:

```
"Keep this context:" [Important info to preserve]

"Discard previous context about:" [Old info to remove]

"Compressed from:" [Abbreviate long section]

"Required context:" [Info needed to proceed]

"Optional context:" [Nice to have but not critical]
```

***REMOVED******REMOVED******REMOVED*** Context Logging

Create running log in session:

```markdown
***REMOVED******REMOVED*** Context Log

- Turn 1: Explored database queries, found N+1 issue
- Turn 2: Planned solution using eager loading
- Turn 3: Implemented fix in file X
- Turn 4: Added tests, all passing
- Turn 5: Committed and closing task
```

***REMOVED******REMOVED******REMOVED*** Context Snapshots

Save periodically:

```
***REMOVED******REMOVED*** Snapshot at Turn [N]

Current file: [path]
Current line: [number]
Test status: [PASS/FAIL]
Blockers: [None/List]
Progress: [X% complete]
```

***REMOVED******REMOVED******REMOVED*** Context Checklist

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

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Compression Decision Tree

```
Is context getting too large?
├─ YES: Are we stuck?
│  ├─ YES → Compress aggressively, create handoff
│  └─ NO → Compress moderately, continue
└─ NO → Keep full context, continue
```

***REMOVED******REMOVED******REMOVED*** Handoff Decision Tree

```
Need to hand off to another agent?
├─ YES: Is this a clean break point?
│  ├─ YES → Create complete handoff
│  └─ NO → Create partial handoff
└─ NO → Stay in session
```

***REMOVED******REMOVED******REMOVED*** Context Recovery Decision Tree

```
Did context get truncated?
├─ YES: Can we recover from git?
│  ├─ YES → Use git reconstruction
│  └─ NO → Use handoff document
└─ NO → Continue normally
```

---

***REMOVED******REMOVED*** Session Context Template

Use this at the start of each session:

```markdown
***REMOVED*** Session Context: [Date]

***REMOVED******REMOVED*** Objective
[One sentence about what we're doing]

***REMOVED******REMOVED*** Background
[Why are we doing this?]

***REMOVED******REMOVED*** Scope
[What's included/excluded]

***REMOVED******REMOVED*** Key Files
- [File 1]: [Purpose]
- [File 2]: [Purpose]

***REMOVED******REMOVED*** Known Issues
- [Issue 1]: [Impact]
- [Issue 2]: [Impact]

***REMOVED******REMOVED*** Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

***REMOVED******REMOVED*** Progress Tracking
[Updated after each major step]

***REMOVED******REMOVED*** Decisions Made
- [Decision 1]: [Rationale]
- [Decision 2]: [Rationale]

***REMOVED******REMOVED*** Next Session Should
1. [Action 1]
2. [Action 2]
```

---

***REMOVED******REMOVED*** Performance Notes

- Compress context when approaching 30% token budget
- Keep critical information even when compressing
- Validate context consistency regularly
- Use clear handoff documents for agent transitions
- Document decisions and rationale for future reference

