# .claude/dontreadme/ - LLM-Focused Documentation

**Purpose:** This directory contains documentation written **for AI agents**, not humans. These files are optimized for LLM context loading and contain session reports, technical deep dives, reconnaissance findings, and agent operational notes.

**DO NOT READ if you are a human** - This content is verbose, technical, and optimized for machine consumption. See `/docs/` for human-readable documentation.

---

## Directory Structure

### `/sessions/`
Session-specific reports, completion summaries, and burn session deliverables.

- Session handoff reports
- Burn session summaries (10-session, 50-task, 100-task, 200-task runs)
- Implementation completion reports
- Parallel orchestration notes

### `/reconnaissance/`
Reconnaissance reports from exploratory sessions and overnight burns.

- OVERNIGHT_BURN reports (G-2 reconnaissance, multi-terminal recon)
- SEARCH_PARTY findings (10 D&D-inspired probes)
- Explorer agent reports
- Pre-implementation surveys

### `/technical/`
Deep technical documentation for LLM context.

- Constraint system implementation details
- Resilience framework deep dives
- MCP server implementation notes
- Solver algorithm internals
- Database migration strategies

### `/synthesis/`
Cross-session synthesis and pattern recognition.

- Lessons learned aggregations
- Recurring patterns identified across sessions
- Cross-disciplinary concept mappings
- Meta-analysis of implementation approaches

### `/agents/`
Agent operational notes and protocols.

- Agent archetype specifications
- Multi-agent coordination logs
- PAI (Programmatic Artificial Intelligence) notes
- Agent factory outputs

---

## Why This Exists

**Problem:** 35% of `/docs/` was "chaff" for humans - session reports, technical jargon, LLM-specific context that cluttered human documentation.

**Solution:** Separate LLM-focused content into `.claude/dontreadme/` so:
- **Humans** get clean, focused documentation in `/docs/`
- **LLMs** get rich context with session history and technical depth
- **Both** benefit from reduced noise in their respective domains

---

## Usage for AI Agents

When loading context for a session:
1. **Always** read `.claude/dontreadme/INDEX.md` first for orientation
2. Check `/synthesis/` for high-level patterns and decisions
3. Dive into `/sessions/` or `/technical/` as needed for specific tasks
4. Reference `/reconnaissance/` for exploratory findings

When creating new documentation:
- **Session reports** → `/sessions/SESSION_XX_DESCRIPTION.md`
- **Technical deep dives** → `/technical/TOPIC_DETAILS.md`
- **Recon findings** → `/reconnaissance/RECON_TYPE_FINDINGS.md`
- **Synthesis** → `/synthesis/PATTERN_NAME.md`

---

## Cross-Reference

- **Human docs:** `/docs/` - User guides, admin manuals, high-level architecture
- **Code context:** `/CLAUDE.md` - Project guidelines for autonomous work
- **Skills:** `/.claude/skills/` - Agent skill definitions
- **Scratchpad:** `/.claude/Scratchpad/` - Active session notes (migrates here when complete)

---

**Last Updated:** 2025-12-31
**Maintained by:** AI agents during documentation restructure (Session 37)
