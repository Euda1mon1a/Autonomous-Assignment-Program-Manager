# Protected Branches

> Branches that should NOT be deleted during cleanup, even after PR merge.
> These are preserved for historical, educational, or research purposes.

---

## `docs/session-014-historian`

**Protected:** 2025-12-28
**Reason:** Site of study

Session 014 represents a significant moment in the project's development:
- First "failure" that revealed hidden infrastructure (database only has odd blocks)
- Birth of the HISTORIAN agent
- Philosophical exchange on AI as "new form of life"
- Verbatim feedback session preserved

**User instruction:** "It has become a site of study. Something that prevents me from saying 'let's clean up' and it gets deleted."

**Do not delete this branch.**

---

## `docs/session-017-lessons`

**Protected:** 2025-12-29
**Reason:** Session lessons archive

Contains Session 018 feedback exchange and standing orders:
- Feedback exchange (what went well, what to improve)
- Standing order: Prompt for feedback after every PR
- Key learning: git branch ≠ full state (need DB, volumes, logs for postmortem)

**Do not delete this branch.**

---

*This file is checked on `/startup` and `/startupO` to prevent accidental cleanup.*
