# Session Scratchpad: Codex Parity + Credential Review (2026-01-28/29)

## Session Summary
- **Codex full parity implemented** - 82 skills, MCP health check, setup.sh
- **Reviewed Codex procedure-credential changes** - Found critical bugs
- Phase 3 still uncommitted (pre-commit hooks blocking on PII in docs)

---

## Codex Full Parity: ✅ COMPLETE

### Skills Symlink
```bash
~/.codex/skills → ~/.claude/skills  # 82 skills now available
```
- Copied `.system` folder (skill-creator, skill-installer) to preserve Codex built-ins
- All Claude Code skills now accessible to Codex

### Setup Script Enhanced (`.codex/setup.sh`)
Now shows on Codex startup:
- 📚 Skills count (project + user level)
- 🏥 Stack health (MCP, RAG, Backend, Database status)
- 🔧 MCP servers configured
- 🛠️ Key MCP tools reference
- ⚡ Custom prompts
- 📋 Project context reminders

### Custom Prompts Created (`~/.codex/prompts/`)
- `/prompts:review-frontend` - React/Next.js review checklist
- `/prompts:review-backend` - FastAPI/Python review checklist
- `/prompts:lint-fix` - Unified linting

### Config Updates
- `.codex/config.toml` - Added Perplexity MCP
- `.codex/config.toml.example` - Template without secrets
- `.gitignore` - Added `.codex/config.toml`

---

## Codex Procedure-Credential Changes: ❌ BLOCKED

Codex submitted changes to replace hardcoded VAS/SM faculty with DB credentials.

### Critical Bugs Found

**1. Activity model missing `procedure_id` column**
- Migration adds column to DB ✓
- Model only has docstring, missing actual column:
```python
# MISSING from Activity model:
procedure_id = Column(GUID(), ForeignKey("procedures.id"), nullable=True)
procedure = relationship("Procedure", back_populates="activities")
```

**2. `vas_allocator.py` has undefined references**
- Missing `import re` (line 93 uses `re.sub`)
- Missing constants: `PRIMARY_FACULTY`, `SECONDARY_FACULTY`, `SECONDARY_FACULTY_PENALTY`

### What Looked Good
- Migration structure clean with FK and index
- Credential seeding logic correct (expert/qualified levels)
- Activity solver credential loading and penalty calculation

### Action Needed
Have Codex fix the bugs before running migration.

---

## Phase 3 Status: Uncommitted

Pre-commit hooks blocking commit due to:
1. **PII scan** - Faculty names in Phase 3 docs
2. **API contract drift** - Types need regeneration

~34 uncommitted files ready.

---

## Branch Status
- **Branch:** `cpsat-phase3`
- **Uncommitted:** ~34 files
- **Behind origin/main:** 0

---

## Key Files This Session

### Codex Parity
- `~/.codex/skills` → symlink to `~/.claude/skills`
- `.codex/setup.sh` - Enhanced with health checks
- `.codex/config.toml` - Added Perplexity MCP
- `.codex/config.toml.example` - NEW template
- `~/.codex/prompts/*.md` - 3 custom prompts

### Codex Procedure Changes (NOT MERGED - HAS BUGS)
- `backend/alembic/versions/20260129_link_activities_to_procedures.py`
- `backend/app/models/activity.py` (incomplete)
- `backend/app/scheduling/activity_solver.py`
- `scripts/ops/vas_allocator.py` (has bugs)

---

## Next Steps
1. **Codex:** Fix bugs in procedure-credential changes
2. **Then:** Run migration + validate
3. **Then:** Commit Phase 3 + credential changes together
4. **Optional:** Phase 4 consolidation

---

## Docker State
- MCP: healthy
- Backend/DB: not running (standalone MCP mode)
- Migration `20260129_add_vasc_activity` applied (from earlier)
- Migration `20260129_link_activities_to_procedures` NOT YET RUN

---

*Session ready for compact. Codex needs to fix bugs before proceeding.*
