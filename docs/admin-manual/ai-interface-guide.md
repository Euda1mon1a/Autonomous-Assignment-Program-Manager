# AI Assistant Interface Guide for Administrators

> **Audience:** Clinician administrators managing the Residency Scheduler
> **Purpose:** Understanding the differences between Web and CLI AI interfaces

---

## Why This Matters

When working with AI assistants like Claude Code or Codex, **the interface you use changes what the AI can see and do**. This guide explains those differences in plain language to help you avoid common pitfalls.

**Think of it like this:** A phone consultation vs an in-person clinic visit. The doctor has different information available in each setting, and what they can do differs accordingly.

---

## Quick Reference: Web vs CLI

| Capability | Web App | CLI (Terminal) |
|------------|---------|----------------|
| **See your files** | Only what you paste/upload | Full access to local files |
| **Make changes** | Suggests code snippets | Directly edits files |
| **Remember context** | Per-session only | Per-session only |
| **Access terminal** | Cannot run commands | Can run commands |
| **Share state with other sessions** | No | No |
| **Risk of breaking things** | Low (copy-paste) | Higher (direct edits) |

---

## What Each Interface Can "See"

### Web App (Browser-Based)

**Limited visibility.** The AI only knows about:

- Text you type in the chat
- Code snippets you copy and paste
- Files you explicitly upload
- What you describe about your system

**It cannot:**
- Browse your files or folders
- See your project structure
- Check if a file already exists
- Verify what's actually in a file

**Analogy:** Like describing your symptoms over the phone. The doctor relies entirely on what you tell them.

### CLI/Terminal

**Full local access.** The AI can:

- Read any file on your computer (within permissions)
- See your complete project structure
- Check existing code before making changes
- Run commands to verify the system state

**It can also:**
- Create, edit, and delete files directly
- Run tests and linters
- Execute database commands
- Push changes to GitHub

**Analogy:** Like an in-person visit where the doctor can run tests, view charts, and examine you directly.

---

## How Changes Are Applied

### Web App: "Suggestion Mode"

1. AI generates code suggestions
2. You review the suggestions
3. **You** copy and paste into your files
4. **You** are responsible for where it goes

**Safety:** High. Nothing changes until you manually apply it.

**Risk:** You might paste code into the wrong file or location.

### CLI: "Direct Edit Mode"

1. AI reads your existing files
2. AI makes changes directly
3. Changes are saved immediately
4. You review what changed (via git diff)

**Safety:** Lower. Changes happen automatically.

**Benefit:** AI can verify its changes worked correctly.

---

## Session Context: The Isolation Problem

### What "Session" Means

Each time you start a conversation with an AI assistant, it begins fresh. **Sessions do not share information with each other.**

**Example Scenario:**
- **Session A:** You ask Claude to add a new scheduling feature
- **Session B:** You ask Claude about the same feature
- **Reality:** Session B has no idea what Session A did

### Why This Causes Problems

If you open multiple browser tabs or terminal windows:
- Each AI session thinks it's the only one working
- They cannot see each other's changes until saved
- They might suggest conflicting changes

**Healthcare Analogy:** Like two specialists treating the same patient but never communicating. They might prescribe conflicting medications.

---

## Split Terminal Is Not Shared Context

**In Plain Language:**

If you have two terminal windows open, each running Claude Code:
- Window 1 and Window 2 are **completely separate**
- They do not "talk" to each other
- They do not know what the other is doing
- Changes made in Window 1 are invisible to Window 2 until saved to disk

**Visual:**
```
┌─────────────────┐    ┌─────────────────┐
│  Terminal 1     │    │  Terminal 2     │
│  Claude Code    │    │  Claude Code    │
│                 │    │                 │
│  "I'm editing   │    │  "I'm editing   │
│   config.py"    │    │   config.py"    │
│                 │    │                 │
│  (no idea about │    │  (no idea about │
│   Terminal 2)   │    │   Terminal 1)   │
└─────────────────┘    └─────────────────┘
         │                      │
         └───────┬──────────────┘
                 ▼
    ┌────────────────────────┐
    │      Your Files        │
    │   (potential conflict) │
    └────────────────────────┘
```

**Rule:** Only use one AI session per project at a time.

---

## Parallel Session Risks

### The Danger Zone

Running multiple AI sessions that can edit the same files is like having multiple surgeons operating on the same patient simultaneously without coordination.

**What Can Go Wrong:**

1. **Overwritten Changes**
   - AI-1 saves changes to `schedule.py`
   - AI-2 saves different changes to `schedule.py`
   - AI-1's work is lost

2. **Merge Conflicts**
   - Both AIs modify the same lines
   - Git cannot automatically resolve
   - Manual intervention required

3. **Broken Code**
   - AI-1 renames a function
   - AI-2 calls the old function name
   - Application crashes

### How to Avoid This

- **One AI session per project** at any time
- If you must switch, close the first session completely
- Wait for one task to finish before starting another
- Use git commits as checkpoints between sessions

---

## Checklists: Web vs CLI

### If You're Using the Web App

Before starting:
- [ ] Have the relevant files open in another tab to copy from
- [ ] Know the exact file paths where changes should go
- [ ] Understand your current project structure

When working:
- [ ] Paste complete file contents when asking for changes
- [ ] Specify exact file names and locations
- [ ] Review all suggestions before applying
- [ ] Apply changes one at a time, testing between each

After changes:
- [ ] Verify changes are in the correct files
- [ ] Run tests if applicable
- [ ] Commit to version control

### If You're Using CLI (Terminal)

Before starting:
- [ ] Close any other AI sessions for this project
- [ ] Ensure you're in the correct project directory
- [ ] Check git status (clean working tree is ideal)
- [ ] Know which branch you should be on

When working:
- [ ] Let the AI read files before making changes
- [ ] Review proposed changes before confirming
- [ ] Ask for `git diff` after changes to verify
- [ ] Request tests be run after modifications

After changes:
- [ ] Review git diff for all changes made
- [ ] Run the test suite
- [ ] Commit changes with clear message
- [ ] Create a Pull Request (do NOT push directly to main)

---

## Common Mistakes and How to Avoid Them

### Mistake 1: Assuming the Web AI "Knows" Your Project

**Wrong assumption:** "It should know what files I have."

**Reality:** Web-based AI only knows what you paste or describe.

**Fix:** Always provide complete context when using Web interfaces.

### Mistake 2: Running Multiple CLI Sessions

**Wrong assumption:** "I can work faster with two AI helpers."

**Reality:** They will conflict and potentially corrupt your work.

**Fix:** One session at a time. Use git branches for parallel work.

### Mistake 3: Trusting CLI to Push Safely

**Wrong assumption:** "The AI knows not to break things."

**Reality:** CLI has full permissions. It can push directly to main.

**Fix:** Always require Pull Requests. Never allow direct pushes to main.

### Mistake 4: Switching Interfaces Mid-Task

**Wrong assumption:** "I can continue my work in a different interface."

**Reality:** Each interface/session has no memory of the other.

**Fix:** Complete tasks in one session, commit, then switch if needed.

---

## Local-Only Git Workflow (For PII Files)

Some files contain real names (faculty, residents) and should **NEVER go to GitHub**. These stay on your local machine only.

### The Simple Rule

| Action | For PII Files | For Code |
|--------|---------------|----------|
| `git add` | ✅ Yes | ✅ Yes |
| `git commit` | ✅ Yes | ✅ Yes |
| `git merge` | ✅ Yes (locally) | ✅ Yes |
| `git push` | ❌ **NEVER** | ✅ Via PR |
| `git pull` | ❌ Skip for main | ✅ Yes |

### What Are PII Files?

Files in `docs/data/` that contain real names:
- `LOCAL_SCHEDULE_NOTES.md` - Program-specific documentation
- `*.csv` - Schedule exports with names
- `*.json` - Airtable exports with names

### How It Works

```
Your Local Machine                     GitHub (origin)
─────────────────                     ────────────────

local main ──────────────────────     origin/main
    │                                      │
    ├── PII commit (stays here)            │ (no PII)
    │                                      │
    └── Never push ────────X───────────────┘
```

**Step by step:**

1. **Make changes** to local files (schedules, notes with real names)
2. **Commit locally:** `git add` + `git commit`
3. **Stay on local main** - your local main will diverge from origin/main
4. **That's OK** - PII stays on your machine, code goes to GitHub separately

### What "Diverge" Means

Your local main has commits that origin/main doesn't have. This is intentional:

```bash
$ git status
On branch main
Your branch is ahead of 'origin/main' by 1 commit.
  (use "git push" to publish your local commits)   # ← DO NOT DO THIS
```

**Ignore the suggestion to push.** Those commits contain PII.

### If You Accidentally Push PII

1. **Don't panic** - but act quickly
2. Contact the repository owner immediately
3. The commit history needs to be rewritten (force push)
4. GitHub support may need to purge cached data

**Prevention:** Create a pre-push hook that blocks `docs/data/` files.

---

## Summary

| Situation | Recommendation |
|-----------|---------------|
| Quick question about code | Web app is fine |
| Need to review suggestions carefully | Web app preferred |
| Making actual code changes | CLI preferred |
| Complex multi-file changes | CLI required |
| Reviewing what changed | CLI with git diff |
| Learning or experimenting | Web app (safer) |
| Production changes | CLI with PR workflow |
| **Files with real names** | **Local commit only, NEVER push** |

**Golden Rules:**
1. One AI session per project at a time
2. Web suggests, CLI edits
3. Always use Pull Requests, never push to main
4. Each session starts fresh - provide context
5. **PII files: commit locally, never push**

---

## Related Documentation

- [AI Rules of Engagement](../development/AI_RULES_OF_ENGAGEMENT.md) - Policies for AI agents
- [Configuration Guide](configuration.md) - System settings
- [User Management](users.md) - Access control

