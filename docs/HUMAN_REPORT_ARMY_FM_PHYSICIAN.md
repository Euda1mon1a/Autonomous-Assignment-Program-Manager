# Human Report: Army Family Medicine Physician

Date: 2026-01-18
Scope: /startupO, /startupO-lite, /force-multiplier, hierarchy, command philosophy, agent roster, standing orders, MCP audit visibility, RAG-down operations

## Purpose (Plain Language)
This report explains how the system’s delegation model works, what the two key slash commands do, and where the operational gaps are. It is written for a clinician who needs a high‑level operational picture without deep engineering detail.

## Quick Read
- The system is built around military-style mission command (Auftragstaktik): leaders set intent; subordinates decide how.
- /startupO is the full ORCHESTRATOR startup; it loads local docs and is the fallback when RAG is down.
- /startupO-lite is a token-efficient preflight checklist for system readiness and RAG access.
- /force-multiplier is a governance briefing generator using RAG queries.
- The agent roster is large (54 agents) and structured like a staff organization, including MEDCOM and a SOF medical operator (18D).
- Standing orders exist but are scattered across identity cards; there is no single consolidated standing‑orders registry.
- I cannot see runtime MCP audit logs; I can only see the audit mechanisms and tests in the codebase.

---

## 1) /startupO-lite (What it is, and what it does)
**Purpose:** Token‑efficient ORCHESTRATOR startup. Minimal context (~500 tokens) and RAG-first behavior.

**Key actions it prescribes:**
- Git status + branch check
- Stack health check (`./scripts/stack-health.sh`)
- MCP container health check and explicit RAG health call (`mcp__residency-scheduler__rag_health`)
- Required resilience status check (`mcp__residency-scheduler__get_defense_level_tool`)
- Container staleness check (`./scripts/diagnose-container-staleness.sh`)
- A standard “ORCHESTRATOR Lite Active” status readout

**What’s done well:**
- Strong preflight discipline (health checks before work)
- Explicit “no RAG = flying blind” warning
- Clear guardrails for container staleness (prevents false bug hunts)

**Gaps / Risks:**
- If MCP/RAG is down, the workflow becomes weak or manual.
- Requires local scripts to exist and be executable; no fallback if scripts fail.
- The output template lists key agents but doesn’t validate actual roster in `.claude/agents.yaml`.

---

## 2) /startupO (Full startup and RAG-down fallback)
**Purpose:** Full ORCHESTRATOR startup with broader context loading and operational guardrails. It is the best fallback when RAG is down because it explicitly loads local governance files and warns about tool loss.

**Key actions it prescribes:**
- Read core local context files (CLAUDE.md, AI rules, HUMAN_TODO, ORCHESTRATOR spec, advisor notes, context-aware delegation)
- Git status + branch check and Codex PR feedback check
- Stack health check (`./scripts/stack-health.sh`)
- MCP/RAG health check with explicit warning about tool loss if down
- Required resilience status check (`mcp__residency-scheduler__get_defense_level_tool`)
- Container staleness check (`./scripts/diagnose-container-staleness.sh`)
- A full “ORCHESTRATOR Mode Active” status readout

**What’s done well:**
- Strong guardrails on delegation (99/1 rule and 2-agent direct spawn limit)
- Loads local governance context even when RAG is unavailable
- Explicit MCP/RAG failure warning and restart guidance

**Gaps / Risks:**
- Heavier startup (large context load, slower to use)
- Still depends on MCP tools for resilience checks when available
- No automated offline mode; it relies on the user to adapt behavior

**RAG-down playbook (what to use when RAG is down):**
- Use `/startupO` (not `/startupO-lite`) because it loads local docs and defines degraded operations.
- Rely on local files as primary guidance:
  - `CLAUDE.md`
  - `docs/development/AI_RULES_OF_ENGAGEMENT.md`
  - `HUMAN_TODO.md`
  - `.claude/Agents/ORCHESTRATOR.md`
  - `.claude/Scratchpad/ORCHESTRATOR_ADVISOR_NOTES.md`
  - `.claude/skills/context-aware-delegation/SKILL.md`
  - `.claude/Governance/HIERARCHY.md`
  - `.claude/Governance/SPAWN_CHAINS.md`
- Avoid tasks that require MCP tools or RAG context; stick to read-only reviews or clearly scoped edits with local guidance.
- Attempt recovery first: `./scripts/start-local.sh` (restores MCP and RAG).

---

## 3) /force-multiplier (What it is, and what it does)
**Purpose:** Governance briefing tool. It uses RAG to retrieve hierarchy, command philosophy, standing orders, and roster context.

**Required RAG queries:**
- Auftragstaktik command philosophy
- Chain of command
- L3 minimal context pattern
- Spawn authority matrix
- Party skills
- Standing orders

**Fallback if RAG is incomplete:**
- `.claude/Governance/HIERARCHY.md`
- `.claude/Governance/SPAWN_CHAINS.md`
- `.claude/Governance/CAPABILITIES.md`
- `.claude/dontreadme/synthesis/PATTERNS.md`

**What’s done well:**
- Forces a governance review before multi‑agent work
- Explicitly separates strategic RAG (for leaders) vs tactical RAG (for subagents)
- Enforces mission‑type orders instead of micromanagement

**Gaps / Risks:**
- Depends on RAG freshness; stale RAG could mislead a commander
- Doesn’t verify MCP status first (unlike /startupO-lite)

---

## 4) Command Philosophy (Auftragstaktik)
**Core idea:** The leader provides the objective and why. Subordinates decide how.

**Key rules:**
- Litmus test: “If your delegation reads like a recipe, you’re micromanaging.”
- 99/1 rule: ORCHESTRATOR delegates; only acts directly as a last resort.
- Escalate when blocked or when a decision crosses domain boundaries.

**What’s done well:**
- Clear separation of intent vs execution
- Explicit escalation triggers
- Consistent military command framing (familiar to Army medicine)

**Gaps / Risks:**
- Real-world adherence depends on user discipline; the system cannot enforce this culturally.

---

## 5) Hierarchy (Chain of Command)
**Top level:** ORCHESTRATOR (commander), with two Deputies:
- ARCHITECT (systems/technical)
- SYNTHESIZER (operations/integration)

**Command structure includes:**
- Coordinators (domain managers)
- Specialists (execution)
- G‑Staff (advisory; e.g., G1/G2/G3/G4/G5/G6)
- SOF branch (USASOC + 18-series)
- Oversight (DELEGATION_AUDITOR)

**What’s done well:**
- Clean structure mirrored after military staff doctrine
- Explicit spawn authority matrix
- Party skills mapped to staff functions (e.g., /search-party, /plan-party)

**Gaps / Risks:**
- ORCHESTRATOR is not listed in `.claude/agents.yaml` (roster is missing the top commander entry).

---

## 6) Exceptions & Overrides (USASOC, User, Subagent Types)
**Where it is documented today:** `.claude/Governance/SPAWN_CHAINS.md` (not prominently in ORCHESTRATOR spec).\n+
**Explicit exceptions that exist:**
- **USASOC exception:** USASOC has wide lateral authority to task any Coordinator or Specialist. 18A can task any agent when USASOC is active.
- **User override:** The user can invoke any agent directly (explicit exception to spawn chain enforcement).
- **Emergency exception:** Emergency situations may bypass normal chains if documented with justification.\n+
**Subagent exception (tooling path):**
- Built‑in agent types (e.g., Explore/Plan) can be used directly without MCP spawn‑agent validation. This is documented in `/force-multiplier` but not surfaced in ORCHESTRATOR documentation.\n+
**Gap (visibility):** These exceptions are real but not clearly surfaced in the ORCHESTRATOR spec or a consolidated “exceptions” section; they are easy to miss.\n+
---
\n+## 7) Agent Roster (Counts and Names)
Registry location: `.claude/agents.yaml` (54 total)

**Counts by tier:**
- Deputy: 2
- Coordinator: 9
- Specialist: 17
- G‑Staff: 9
- Special: 8
- SOF: 8
- Oversight: 1

**Roster by tier (full list):**
- Deputy: ARCHITECT, SYNTHESIZER
- Coordinator: COORD_AAR, COORD_ENGINE, COORD_FRONTEND, COORD_INTEL, COORD_OPS, COORD_PLATFORM, COORD_QUALITY, COORD_RESILIENCE, COORD_TOOLING
- Specialist: API_DEVELOPER, BACKEND_ENGINEER, CI_LIAISON, CODE_REVIEWER, COMPLIANCE_AUDITOR, DBA, FRONTEND_ENGINEER, OPTIMIZATION_SPECIALIST, QA_TESTER, RELEASE_MANAGER, RESILIENCE_ENGINEER, SCHEDULER, SECURITY_AUDITOR, SWAP_MANAGER, TOOL_QA, TOOL_REVIEWER, UX_SPECIALIST
- G‑Staff: DEVCOM_RESEARCH, G1_PERSONNEL, G2_RECON, G3_OPERATIONS, G4_CONTEXT_MANAGER, G4_LIBRARIAN, G4_SCRIPT_KIDDY, G5_PLANNING, G6_SIGNAL
- Special: AGENT_FACTORY, ASTRONAUT, CRASH_RECOVERY_SPECIALIST, FORCE_MANAGER, HISTORIAN, MEDCOM, META_UPDATER, TOOLSMITH
- SOF: 18A_DETACHMENT_COMMANDER, 18B_WEAPONS, 18C_ENGINEER, 18D_MEDICAL, 18E_COMMS, 18F_INTEL, 18Z_OPERATIONS, USASOC
- Oversight: DELEGATION_AUDITOR

**Clinician-relevant note:** The presence of MEDCOM and 18D_MEDICAL indicates explicit support for medical domain needs and operational medicine scenarios.

---

## 8) Standing Orders (What they are)
**Where they live:** Individual identity cards in `.claude/Identities/*.identity.md` and the hierarchy doc.

**Known standing orders (global):**
- L3 Minimal Context Standing Order: When mission is clear and tools are available, use minimal context to delegate.
- Container staleness protocol (in /startupO-lite) to avoid false bug hunts.
- Escalation rules (tests failing, security sensitive changes, architecture decisions).

**What’s done well:**
- Standing orders are embedded in identity cards (agents know their authority).
- L3 pattern reduces overload and supports rapid delegation.

**Gaps / Risks:**
- There is no single consolidated list of standing orders; you must open identity cards individually.

---

## 9) MCP Audit Visibility
**Can I see MCP audit logs?**
- I can see the audit mechanisms in code and docs, but not runtime audit logs.
- Deployment tools support audit logging via `DEPLOYMENT_AUDIT_LOG` (default `/var/log/scheduler/deployments.log`).
- Spawn agent tests define expected audit entry structure, but no real log files are present in this repo.

**Bottom line:** The audit framework exists, but the actual audit trail is external to this repository and not visible here.

---

## 10) “What you might want to know” (Clinician‑focused)
- The system’s chain‑of‑command is deliberately military‑style; it should feel familiar to staff officers.
- There is a built‑in medical advisory agent (MEDCOM) and a SOF medical operator (18D), so medical domain inputs are first‑class.
- The governance model is rigorous, but success depends on consistent user discipline (delegation vs micromanagement).

---

## 11) Mitigating “Context Death” (Revised Model)
**Problem:** Subagents do not share a global context pool. Each spawn is a one‑shot with its own prompt. The biggest gap is not the Specialists; it is Deputies getting incomplete context from ORCHESTRATOR.

**Revised doctrine (your model):**  
ORCHESTRATOR has full oversight of RAG + docs (RAG preferred; open files only when necessary). Deputies receive **everything any of their subordinates could need**. Deputies decide what to pass down. Coordinators then refine and pass a smaller “kit” to Specialists, who can choose which pieces to use.

**Recommended pattern by tier:**
- **ORCHESTRATOR (strategic + full kit):** Mission intent + constraints **plus a complete “domain kit”** (relevant RAG results, doc pointers, tools, and skills). This is the master context pool for the domain.
- **Deputy (domain‑strategic):** Curates the kit by domain, removes noise, and decides what Coordinators need.
- **Coordinator (tactical‑strategic):** Produces a smaller execution kit (file paths, APIs, acceptance criteria).
- **Specialist (execution):** Uses the kit as optional tools, not mandatory steps.

**Why this helps:**
- Removes the single biggest failure mode: Deputies lacking enough context to delegate.
- Keeps Specialists agile: they can choose the tools/assets they need without being constrained.
- Preserves mission command: higher levels provide resources and intent, lower levels decide how to use them.

**Operational guidance:**
- Prefer RAG for institutional context; read full docs only when needed for specifics.
- Treat Deputies as **context curators**, not just dispatchers.
- A good “kit” is a list of assets, not a script.

---

## 12) Diff: /startupO vs /startupO-lite vs /force-multiplier (Commands, skills, tools)

**Role difference:**
- /startupO = full startup (reads local docs, checks Codex, stack health, and MCP/RAG; best fallback when RAG is down)
- /startupO-lite = readiness checklist + RAG health gate
- /force-multiplier = governance briefing + roster/authority snapshot

**Tooling difference:**
- /startupO calls:
  - Local file reads (governance and command docs)
  - Local scripts (`./scripts/stack-health.sh`, `./scripts/diagnose-container-staleness.sh`)
  - MCP tools: `mcp__residency-scheduler__rag_health`, `mcp__residency-scheduler__get_defense_level_tool`
- /startupO-lite calls:
  - Local scripts (`./scripts/stack-health.sh`, `./scripts/diagnose-container-staleness.sh`)
  - MCP tools: `mcp__residency-scheduler__rag_health`, `mcp__residency-scheduler__get_defense_level_tool`
- /force-multiplier calls:
  - MCP tools: multiple `mcp__residency-scheduler__rag_search` queries
  - Optional fallback: direct file reads in `.claude/Governance/`

**Operational difference:**
- /startupO loads governance context, checks system health, and enforces delegation limits.
- /startupO-lite checks system health before mission start with minimal context.
- /force-multiplier checks governance and delegation readiness, not system health.

---

## 13) Gaps to Track (Summary)
1) No standardized “full kit” handoff from ORCHESTRATOR to Deputies (primary operational gap).
2) Exceptions (USASOC/user override/subagent types) are not surfaced in ORCHESTRATOR spec or a single consolidated section.
3) No ORCHESTRATOR entry in `.claude/agents.yaml` (roster omission).
4) Standing orders are dispersed across identity cards (no consolidated index).
5) MCP audit logs are not visible in-repo; only audit mechanisms are documented.
6) /force-multiplier depends heavily on RAG freshness; no automated “RAG health check” in the skill.
7) No formal offline SOP beyond `/startupO` warnings; degraded operations rely on user discipline.

---

## 14) Sources (Files consulted)
- `.claude/skills/startupO/SKILL.md`
- `.claude/skills/startupO-lite/SKILL.md`
- `.claude/skills/force-multiplier/SKILL.md`
- `.claude/Governance/HIERARCHY.md`
- `.claude/Governance/SPAWN_CHAINS.md`
- `.claude/Identities/README.md`
- `.claude/agents.yaml`
- `mcp-server/docs/deployment-tools.md`
- `mcp-server/docs/AGENT_SERVER.md`
- `mcp-server/tests/test_spawn_agent_tool.py`
