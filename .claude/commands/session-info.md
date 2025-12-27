<!--
Display session environment info: git branch, remote tracking, uncommitted changes.
Same output as the SessionStart hook - use anytime to check your working state.
-->

Run the session-start environment check to display current git state and warnings:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager
.claude/hooks/session-start.sh 2>&1 | head -80
```

After running, summarize the key information:

## Git Branch Status
- Current branch name
- Whether it has remote tracking (CRITICAL if missing!)
- Number of uncommitted changes

## Warnings to Address
- If on main/master: Create a feature branch first
- If no remote tracking: Push with `git push -u origin <branch>`
- If uncommitted changes: Consider committing or stashing

## Quick Actions
If there are issues, suggest the appropriate fix:

```bash
# If no remote tracking:
git push -u origin $(git branch --show-current)

# If on main, create feature branch:
git checkout -b claude/<task-name> origin/main

# If uncommitted changes need committing:
git add -A && git commit -m "WIP: <description>"
```
