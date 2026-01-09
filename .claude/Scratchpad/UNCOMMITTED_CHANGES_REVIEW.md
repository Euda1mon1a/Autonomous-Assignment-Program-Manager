# Uncommitted Changes for Human Review

**Date:** 2026-01-09
**Branch:** `session/075-continued-work`

---

## Remaining Uncommitted Files

After the 6 commits executed, the following files remain uncommitted for your review.

---

## 1. Weekend Config Migration (UNTRACKED)

**File:** `backend/alembic/versions/20260108_add_weekend_config.py`

**Purpose:** Add `includes_weekend_work` boolean column to `rotation_templates` table.

**What it does:**
- Adds column with default FALSE
- Auto-populates TRUE for known weekend rotations:
  - activity_type = 'inpatient'
  - Names matching: 'night float', 'FMIT', 'call', 'weekend'

**Recommendation:** ARCHIVE
- Not required for Activity model work
- WeekendWorkConstraint can use `activity_type == 'inpatient'` directly
- Can restore later if explicit column needed

**To archive:** Move file content to this document and delete the file.

<details>
<summary>Full Migration Code</summary>

```python
"""Add includes_weekend_work to rotation_templates.

Revision ID: 20260108_add_weekend_config
Revises: 20260108_add_away_prog
Create Date: 2026-01-08
"""

from alembic import op
import sqlalchemy as sa

revision = "20260108_add_weekend_config"
down_revision = "20260108_add_away_prog"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add includes_weekend_work column to rotation_templates."""
    op.add_column(
        "rotation_templates",
        sa.Column(
            "includes_weekend_work",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
            comment="True if rotation includes weekend assignments",
        ),
    )

    # Set True for known weekend rotations based on activity_type or name patterns
    op.execute(
        """
        UPDATE rotation_templates
        SET includes_weekend_work = TRUE
        WHERE activity_type = 'inpatient'
           OR name ILIKE '%night float%'
           OR name ILIKE '%FMIT%'
           OR name ILIKE '%call%'
           OR name ILIKE '%weekend%'
        """
    )


def downgrade() -> None:
    """Remove includes_weekend_work column."""
    op.drop_column("rotation_templates", "includes_weekend_work")
```

</details>

---

## 2. Skills Files (MODIFIED)

**Files:**
- `.claude/skills/startupO-legacy/SKILL.md`
- `.claude/skills/startupO-lite/SKILL.md`
- `.claude/skills/startupO/SKILL.md`

**These are PAI (Programmable AI) skill definitions** for Claude Code orchestration startup.

**Changes appear to be:** Updates to skill documentation/prompts for session initialization.

**To review diffs:**
```bash
git diff .claude/skills/startupO-legacy/SKILL.md
git diff .claude/skills/startupO-lite/SKILL.md
git diff .claude/skills/startupO/SKILL.md
```

**Options:**
1. **COMMIT** - If these are intentional improvements to orchestrator startup
2. **DISCARD** - If these are auto-generated or accidental changes
3. **KEEP** - Leave uncommitted for now, decide later

---

## 3. Faculty Call Alignment Scratchpad (MODIFIED)

**File:** `.claude/Scratchpad/FACULTY_CALL_ALIGNMENT.md`

**Purpose:** Session notes about faculty call/activity alignment work.

**To review diff:**
```bash
git diff .claude/Scratchpad/FACULTY_CALL_ALIGNMENT.md
```

**Options:**
1. **COMMIT** - If notes are valuable for continuity
2. **DISCARD** - If notes are stale or superseded by Activity model
3. **KEEP** - Leave uncommitted, personal working notes

---

## Actions Available

### To commit all remaining:
```bash
git add .claude/skills/ .claude/Scratchpad/FACULTY_CALL_ALIGNMENT.md
git commit -m "docs: Update skills and session scratchpad"
```

### To discard all remaining:
```bash
git checkout -- .claude/skills/ .claude/Scratchpad/FACULTY_CALL_ALIGNMENT.md
```

### To delete weekend config migration:
```bash
rm backend/alembic/versions/20260108_add_weekend_config.py
```

### To check current status:
```bash
git status
```

---

## Summary of Completed Commits (This Session)

| # | Commit | Files |
|---|--------|-------|
| 1 | `feat: WebSocket dual auth + admin alert/export improvements` | 5 |
| 2 | `feat(constraints): Add halfday requirement, weekend work, protected slot` | 2 |
| 3 | `feat: Add bulk pattern update and halfday requirements service` | 2 |
| 4 | `feat: Add bulk weekly pattern editor and halfday requirements UI` | 13 |
| 5 | `feat: Add admin swap management page` | 1 |
| 6 | `fix: Port conflicts, migration fixes, add domain docs` | 4 |
| **Previous** | `feat: Add Activity model and solver integration` | 26 |

**Total this session:** 53 files across 7 commits
