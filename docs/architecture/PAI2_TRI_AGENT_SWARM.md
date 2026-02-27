# PAI² Tri-Agent Swarm

## Multi-Model Overnight Orchestration Architecture

> **Status:** ARCHITECTURE PROPOSAL
> **Created:** 2026-02-26
> **Supersedes:** Future D (Hybrid Model Orchestration), Comet 8-Lane Browser Automation
> **Prerequisites:** Claude Code CLI, Codex CLI/App, Gemini CLI installed locally
> **Branch:** `codex/wheat-triage-20260226`

---

## Executive Summary

You have a **SCIF-compliant, air-gapped "Perplexity Computer"** sitting on your desk.

By orchestrating Opus 4.6 (Anthropic), Codex 5.3 (OpenAI), and Gemini 3.1 Pro (Google) simultaneously on a single Mac Mini, the PAI² Tri-Agent Swarm delivers 100% of the long-running, autonomous execution power of a cloud multi-agent system — with **zero DoD OPSEC/CUI data spillage risk**.

This document formalizes the architecture, engineering refinements, overnight playbooks, and safety rules for running three heterogeneous AI systems as a coordinated local swarm. It builds on the PAI² framework (`.claude/Governance/PAI_SQUARED.md`) — Parallel Agentic Infrastructure × Personal Artificial Intelligence — and draws from Perplexity Computer's multi-model orchestration patterns while solving the constraints unique to military medical scheduling on air-gapped hardware.

**The core insight:** Perplexity Computer is a Directed Acyclic Graph (DAG) of parallel models communicating over a message bus. Our local equivalent uses Docker `--network none` containers for compute isolation, the filesystem as the message bus, and `asyncio` management for the DAG. API calls stay on the host; math stays in the container. Data never leaves the machine.

---

## Table of Contents

1. [Evolution — The Lineage](#1-evolution--the-lineage)
2. [Architecture — The Big Picture](#2-architecture--the-big-picture)
3. [Agent Role Cards](#3-agent-role-cards)
4. [Instruction File Protocol](#4-instruction-file-protocol)
5. [Communication Topology](#5-communication-topology)
6. [The "Local Perplexity Computer" Thesis](#6-the-local-perplexity-computer-thesis)
7. [The 5 Engineering Refinements](#7-the-5-engineering-refinements)
8. [Overnight Playbooks](#8-overnight-playbooks)
9. [Reference Implementation — Call Equity YTD](#9-reference-implementation--call-equity-ytd)
10. [Safety Rules — The Three Laws](#10-safety-rules--the-three-laws)
11. [SCIF / Air-Gap Compliance](#11-scif--air-gap-compliance)
12. [Perplexity Computer Lessons](#12-perplexity-computer-lessons)
13. [Comparison to Prior Art](#13-comparison-to-prior-art)
14. [Implementation Roadmap](#14-implementation-roadmap)
15. [Open Questions](#15-open-questions)
16. [Appendices](#16-appendices)

---

## 1. Evolution — The Lineage

The progression: **serial → parallel-same-model → parallel-different-models.** Each stage increased throughput and reduced failure modes.

```
Single Agent ──► Comet 8-Lane ──► Future D (concept) ──► SDK Roadmap (concept)
   (Dec 25)       (Dec 25)          (Dec 25)               (Dec 25)
                                                                │
              Mac Mini + Codex (practice) ◄─────────────────────┘
                   (Feb 26)
                      │
                      ▼
              PAI² Tri-Agent Swarm ◄── Perplexity Computer patterns
                   (Feb 26)              (Feb 25, 2026 launch)
```

### Stage 1: Single Agent (Dec 2025)

One Claude Code instance, serial execution. Throughput: ~1 PR/hour. Bottleneck: context window saturation on large tasks.

### Stage 2: Comet 8-Lane / Signal Transduction (Dec 2025)

Eight Chrome browser tabs running Claude Web, managed by the Comet browser automation agent. Demonstrated 8 PRs/hour throughput. Pain points: 10GB RAM overhead, DOM scraping fragility, tab crashes, no structured responses, session timeouts.

*Reference:* `.antigravity/ROADMAP_SDK_ORCHESTRATION.md` Phase 0

### Stage 3: Future D — Hybrid Model Orchestration (Dec 2025)

Concept document proposing Claude (planning) → Antigravity IDE (tactics) → Qwen Squad (grunt work). Key architectural insight: **skill-required tasks stay on Opus; skill-free tasks go to lower-tier models.** Never implemented — Qwen prerequisite unmet.

*Reference:* `.antigravity/FUTURE_D_HYBRID_MODEL_ORCHESTRATION.md`

### Stage 4: SDK Orchestration Roadmap (Dec 2025)

Four-phase evolution plan: Minimal Viable Orchestrator → 8-Lane Kinase Loop → Dual-Nucleus → Signal Transducer. Introduced domain territory isolation (CORE, API, SCHED, FE, TEST), commit prefixes, and PreToolUse hook guardrails. Code exists in concept form.

*Reference:* `.antigravity/ROADMAP_SDK_ORCHESTRATION.md`

### Stage 5: Mac Mini + Codex Dual System (Feb 2026)

Two autonomous systems running in practice: Mac Mini producing `mini/claude/*` branches (Opus 4.6), Codex 5.3 App running 15 nightly automations (01:00-02:00 HST). 40 branches triaged across two waves: 66% wheat, 34% chaff.

*Reference:* `docs/archived/reports/OPUS_MINI_BRANCH_TRIAGE_REPORT.md`, `docs/development/CODEX_APP_AUTOMATIONS_0100.md`

### Stage 6: Agent Teams (Feb 2026)

Native Opus 4.6 feature (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): shared task lists, peer-to-peer messaging, multi-agent coordination. Used for branch triage. Limitation: TaskList does not survive autocompaction.

### Stage 7: Tri-Agent Swarm (This Document)

Three heterogeneous AI systems from three different companies, orchestrated locally via an async Python DAG, communicating through the filesystem, executing in Docker sandboxes. The first architecture that combines models from three different providers into a coordinated SCIF-compliant local system.

---

## 2. Architecture — The Big Picture

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                     MAC MINI M4 PRO (Apple Silicon, Air-Gapped)              │
│                                                                              │
│  ┌─────────────────────┐  ┌──────────────────────┐  ┌────────────────────┐  │
│  │   GEMINI 3.1 PRO    │  │    OPUS 4.6          │  │   CODEX 5.3       │  │
│  │   Context Engine     │  │    Chief Architect   │  │   Operator        │  │
│  │   & Auditor          │  │                      │  │   & Typist        │  │
│  │                      │  │                      │  │                   │  │
│  │  Reads: GEMINI.md    │  │  Reads: CLAUDE.md    │  │  Reads: AGENTS.md │  │
│  │  CLI: gemini-cli     │  │  CLI: claude         │  │  CLI: codex       │  │
│  │  Window: 1M tokens   │  │  Window: 200K tokens │  │  Speed: 1000+t/s  │  │
│  │  Role: Analyze/Audit │  │  Agent Teams: YES    │  │  Auto: 15/night   │  │
│  └──────────┬───────────┘  └──────────┬───────────┘  └────────┬──────────┘  │
│             │                         │                        │             │
│  ───────────┴─────────────────────────┴────────────────────────┴──────────── │
│                         SHARED COORDINATION LAYER                            │
│                                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │  Git Repo    │ │  Filesystem  │ │  MCP Server  │ │   PostgreSQL 15    │  │
│  │  (branches)  │ │  (msg bus)   │ │  (97+ tools) │ │   (schedules)      │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────────┘  │
│                                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────────┐  │
│  │  Redis       │ │  Celery      │ │  Prometheus   │ │  Docker Sandbox    │  │
│  │  (cache)     │ │  (bg tasks)  │ │  (metrics)    │ │  (--network none)  │  │
│  └──────────────┘ └──────────────┘ └──────────────┘ └────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Four Layers

1. **Agent Layer** — Three AI agents with distinct CLIs, instruction files, and cognitive profiles. Each agent runs on the bare-metal host and makes API calls to its respective provider.

2. **Coordination Layer** — The filesystem acts as the message bus. Git branches provide durable state. `agent_workspace/` provides the inter-agent communication directory with discrete JSON payloads.

3. **Infrastructure Layer** — PostgreSQL, Redis, Celery, OR-Tools solver — all running locally. No cloud dependencies for core scheduling operations.

4. **Isolation Layer** — Docker containers with `--network none` run untrusted agent-generated code. The host handles API calls; the container handles math. Data never traverses a network boundary.

---

## 3. Agent Role Cards

### Gemini 3.1 Pro — "Context Engine & Auditor"

| Attribute | Value |
|-----------|-------|
| **Model** | Gemini 3.1 Pro |
| **CLI** | `gemini-cli` (`brew install gemini-cli`) |
| **Instruction File** | `GEMINI.md` (repo root) |
| **Context Window** | 1M tokens — can ingest entire repository simultaneously |
| **Primary Role** | Repo-wide static analysis, documentation auditing, log compression |
| **Key Strength** | Holds entire codebase in context; Google Search grounding built in |
| **Key Weakness** | No equivalent of `.claude/skills/` or MCP tools; limited code execution safety |
| **Owned Domains** | Documentation, architecture review, cross-file consistency, log analysis |
| **Forbidden Zones** | Direct code modification, database operations, security-critical files |
| **Approval Mode** | `--approval-mode plan` (generates plans, human approves) |

**Example tasks:**
- Ingest `backend/alembic/versions/` and map the full migration dependency graph
- Read 100 `iter_*.json` files and extract CP-SAT weight correlations
- Audit all architecture docs for stale references after a major refactor
- Compare migration chain against model definitions for schema drift

### Opus 4.6 — "Chief Architect"

| Attribute | Value |
|-----------|-------|
| **Model** | Claude Opus 4.6 (`claude-opus-4-6`) |
| **CLI** | `claude` (Claude Code) |
| **Instruction File** | `CLAUDE.md` (repo root, 700+ lines) |
| **Context Window** | 200K tokens (1M via API beta) |
| **Primary Role** | Strategic reasoning, CP-SAT constraint modeling, multi-agent orchestration |
| **Key Strength** | Agent Teams (native), 97+ MCP tools, 35+ skills, Auftragstaktik delegation |
| **Key Weakness** | Slower than Codex for bulk mechanical execution |
| **Owned Domains** | Scheduling engine, ACGME compliance, resilience, architecture decisions |
| **Forbidden Zones** | None (highest-trust agent) — but defers bulk execution to Codex |

**Example tasks:**
- Design migration strategy for `person_academic_years` table (Track A)
- Re-derive CP-SAT weight coefficients via Pareto analysis of sweep results
- Synthesize Gemini's compressed findings into architectural patches
- Orchestrate multi-agent triage of overnight branch output

### Codex 5.3 — "Operator / Typist"

| Attribute | Value |
|-----------|-------|
| **Model** | GPT-5.3 Codex (`gpt-5.3-codex`) |
| **CLI** | `codex` (Codex CLI / macOS App) |
| **Instruction File** | `AGENTS.md` (root) + `.codex/AGENTS.md` (full rules) |
| **Speed** | 1000+ tokens/second (Cerebras WSE-3 acceleration) |
| **Primary Role** | High-speed terminal execution, bulk mechanical fixes, test running |
| **Key Strength** | Fastest execution; 15 nightly automations already running; built-in planning cycle |
| **Key Weakness** | Cannot use `.claude/skills/`; different failure modes (see Feb 2026 20-bug incident) |
| **Owned Domains** | Test execution, linting, formatting, file scaffolding, mechanical code fixes |
| **Forbidden Zones** | ACGME logic, security files, scheduling constraints, database migrations |

**Example tasks:**
- Run 100-iteration CP-SAT weight sweep in Docker sandbox
- Run full test suite (`pytest backend/tests/ && cd frontend && npm test`)
- Apply bulk `datetime.utcnow()` → `datetime.now(UTC)` fixes
- Generate `tune_weights.py` harness from Opus's specification

---

## 4. Instruction File Protocol

### The Hard Lesson (Feb 2026)

Codex CLI produced **20 bugs in one session** because `AGENTS.md` said "See CLAUDE.md" but Codex never read it. Every guardrail — never remove Pydantic constraints, never leak `str(e)`, never modify security files — existed only in `CLAUDE.md`.

**The principle:** Each agent reads ONLY its own instruction file. They do NOT cross-read. Each file must contain inline guardrails.

### File Matrix

| Agent | Primary File | Secondary File | Auto-loaded? |
|-------|-------------|----------------|-------------|
| Gemini 3.1 Pro | `GEMINI.md` | None | Yes (gemini-cli convention) |
| Opus 4.6 | `CLAUDE.md` | `.claude/settings.json` | Yes (Claude Code convention) |
| Codex 5.3 | `AGENTS.md` (root) | `.codex/AGENTS.md` | Yes (Codex CLI convention) |

### Shared Hard Boundaries (Duplicated Across All Three Files)

- NEVER remove or relax Pydantic constraints (`min_length`, `max_length`, `ge`, `le`, `pattern`)
- NEVER weaken type annotations (`dict[str, int]` → `dict[str, Any]`)
- NEVER replace generic client-safe errors with `str(e)`
- NEVER reduce authentication or authorization checks
- NEVER modify scheduling logic or ACGME compliance rules without approval
- NEVER modify models without creating a new Alembic migration
- NEVER edit existing Alembic migrations
- NEVER log or commit PII/OPSEC data (names, schedules, deployments)
- NEVER modify more than 30 files in one branch

**Rule:** Never say "see other file." Inline everything. Assume zero cross-reading.

---

## 5. Communication Topology

The three agents are different products from different companies with no native inter-agent messaging protocol. Coordination happens through shared infrastructure.

### Communication Channels (Ranked by Reliability)

**1. Git Repository (Primary)**

Agents work on separate branches with naming conventions:
- Gemini: `gemini/*` branches
- Opus: `claude/*` branches (or `mini/claude/*` from Mac Mini sessions)
- Codex: `codex/*` branches

Git is the only shared state that survives agent restarts, context compaction, and session boundaries.

**2. Filesystem Message Bus (Secondary)**

Structured files in `agent_workspace/` for inter-agent handoff:

```
agent_workspace/
├── logs/                    # Raw execution output
├── iterations/              # VirtioFS-safe discrete JSON payloads
│   ├── iter_001.json
│   ├── iter_002.json
│   └── ...
├── signals/                 # Compressed inter-agent messages
│   └── compressed_memory.md # Gemini's attention-compacted insights
└── analysis/                # Final outputs
    └── winning_weights.json # Opus's Pareto-optimal results
```

Plus project-level coordination files:
- `TODO.md` — shared task list (single source of truth)
- `RECENT_ACTIVITY.md` — auto-generated, shows recent Claude completions
- `.codex/FEEDBACK.md` — Codex run learnings

**3. MCP Server (Opus Only)**

97+ tools at `http://127.0.0.1:8080/mcp`. Only Opus has native MCP integration via Streamable HTTP transport. Gemini CLI supports MCP (`gemini mcp`) but requires separate registration. Codex CLI has limited MCP support via `.codex/config.toml`.

**4. Agent Teams (Opus Internal Only)**

`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` — shared task lists, peer-to-peer messaging. ONLY between Claude Code instances. Cannot coordinate with Gemini or Codex directly.

### Coordination Patterns

**Pattern 1: Sequential Handoff (Pipeline)**
```
Gemini (audit) ──writes findings──► Opus (reads, plans) ──writes tasks──► Codex (runs)
```

**Pattern 2: Parallel Independent**
```
Gemini: auditing docs/  │  Opus: designing migration  │  Codex: running tests
              (no coordination needed until merge)
```

**Pattern 3: Hub-and-Spoke (Opus as Orchestrator)**
```
                    ┌──► Gemini output (filesystem)
Opus (hub) ────────┤
                    └──► Codex task list (TODO.md / automation prompt)
```

**Pattern 4: Async DAG (swarm_orchestrator.py)**
```
Node A: Codex runs ───────────────────────────────► Node E: Codex deploys
                       │                     ▲
                       │ every 20 iters      │ when complete
                       ▼                     │
                  Node C: Gemini compresses ─► Node D: Opus analyzes
```

### Anti-Patterns (What Does NOT Work)

- Direct messaging between Gemini and Codex (no protocol exists)
- Shared context windows (each agent has its own, non-overlapping)
- Real-time interrupts (agents cannot interrupt each other mid-turn)
- Appending to a single shared file from Docker and host simultaneously (VirtioFS locking — see Refinement 3)

---

## 6. The "Local Perplexity Computer" Thesis

### What Perplexity Computer Is

Perplexity Computer (launched Feb 25, 2026) orchestrates 19 AI models as a cloud-based DAG. Opus 4.6 serves as the core reasoning engine. Tasks are decomposed, routed to specialized models (Gemini for research, Grok for speed, GPT-5.2 for long context), run in parallel with dependency management, and results cached across sessions.

### What We Have

The same architecture, localized:

| Perplexity Computer | PAI² Tri-Agent Swarm |
|---------------------|----------------------|
| 19 cloud models | 3 local models |
| Cloud DAG orchestrator | `swarm_orchestrator.py` (asyncio) |
| Cloud message bus | Filesystem (`agent_workspace/`) |
| Cloud compute | Docker sandbox (`--network none`) |
| Cloud storage | PostgreSQL + Git (local) |
| Per-token billing | Fixed hardware cost |
| Data in transit to cloud | **Data never leaves the machine** |

### The Fundamental Law

> **You cannot rely on text prompts alone for physical system constraints or true parallel execution.**

An LLM cannot natively spawn background processes, handle cross-OS file locks, or physically restrict its own network egress because a prompt told it to. The gap between a theoretical DAG and actual execution requires **5 engineering refinements** (next section).

### The Split-Brain Advantage

Perplexity assumes AI agents live inside the execution environment and need cloud API access. Our architecture is **Split-Brain:**

1. **Host (bare metal):** Antigravity IDE handles all external LLM API calls
2. **Container (Docker):** Only runs the Python scripts that agents generate

The container requires **zero internet access**. If Codex hallucinates a network call to exfiltrate MTF data, it hits a dead network interface.

---

## 7. The 5 Engineering Refinements

These refinements bridge the gap between the theoretical DAG and bulletproof execution on Apple Silicon hardware.

### Refinement 1: Split-Brain Network Isolation (Absolute Air-Gap)

The Docker container needs zero internet access. Wrap all agent-generated code in a strict physical jail.

**Implementation:** `scripts/run_in_sandbox.sh`

Key Docker flags:
- `--network none` — zero egress, prevents data exfiltration
- `--read-only` — container filesystem is immutable
- `--cpus="4.0" --memory="8g"` — reserves remaining cores for host-side LLM inference
- Backend mounted as `:ro` — agent-generated code cannot modify source
- Only `agent_workspace/` is `:rw` — scoped output directory
- `--tmpfs /tmp:rw,noexec,nosuid,size=2g` — scratch space without persistence

The host (bare metal) makes all LLM API calls. The container handles only mathematical computation. This is the **Split-Brain** — API on host, math in container.

### Refinement 2: SSD Armor (Zero-Cost DB Rollbacks)

Running the CP-SAT engine 100 times would write 17,000 `half_day_assignments` per iteration, bloating the Write-Ahead Log and thrashing the SSD.

**Fix:** Use in-memory nested transactions (SAVEPOINTs). Inside each iteration of `tune_weights.py`:

1. Open a `session.begin_nested()` SAVEPOINT
2. Run `SchedulingEngine.generate()` within the SAVEPOINT
3. Extract metrics (MAD, TTFI, coverage)
4. Call `session.rollback()` to instantly reset DB state (0ms, no SSD write)

100 iterations complete in the same DB footprint as 1. The WAL stays clean.

### Refinement 3: VirtioFS Locking Evasion

Docker Desktop on macOS uses VirtioFS for volume mounts. VirtioFS struggles with **POSIX file-locking across OS boundaries**. If Codex appends to a single JSONL file from inside the Linux VM at the exact moment Gemini reads it from macOS, VirtioFS will corrupt the file.

**Fix:** Discrete, atomic payload files.

```
WRONG:  agent_workspace/logs/tune_results.jsonl     (cross-OS contention)
RIGHT:  agent_workspace/iterations/iter_001.json     (zero contention)
        agent_workspace/iterations/iter_002.json
        agent_workspace/iterations/iter_003.json
```

Each write is a complete, atomic file creation. Gemini reads the directory listing and processes completed files. No file is ever written and read simultaneously.

### Refinement 4: CP-SAT Core Illusion

Docker CPU limits create a dangerous interaction with OR-Tools. With `--cpus="4.0"`, the Linux VM still *sees* the M4 Pro's full physical core count (e.g., 14). CP-SAT queries `os.cpu_count()` and spawns 14 search workers. Docker throttles those 14 threads to 4 cores' worth of compute time, causing massive context-switching latency that destroys TTFI metrics.

**Fix:** Hardcode the worker count in `tune_weights.py`:

```
solver.parameters.num_search_workers = 4  # Match Docker --cpus limit
```

NEVER use `os.cpu_count()` inside a Docker container with CPU limits.

### Refinement 5: Async DAG Orchestrator

**Implementation:** `scripts/swarm_orchestrator.py`

A lightweight Python script running on the host that acts as the "message bus" between CLI agents. Uses `asyncio` to manage the full DAG lifecycle:

- **`call_agent(model, prompt)`** — Invokes an LLM agent via Antigravity CLI, captures output
- **`node_b_execute_tuning()`** — Runs 100 iterations in Docker sandbox. On failure, triggers bifurcated error recovery: Gemini classifies (mathematical vs. syntactical), Opus generates a patch. 3-retry max per iteration.
- **`node_c_parallel_monitor()`** — Runs concurrently with Node B. Every 20 iterations, triggers Gemini to compress attention and write `compressed_memory.md`.
- **`node_d_pareto_analysis()`** — After all iterations complete, triggers Opus to read compressed memory and all JSON results, identify Pareto-optimal weights, output `winning_weights.json`.
- **`node_e_deploy()`** — Codex injects winning weights, runs tests, commits if green.

Nodes B and C run concurrently via `asyncio.create_task()`. Nodes D and E run sequentially after B completes.

---

## 8. Overnight Playbooks

Each playbook follows a consistent format: Objective, Agent Roles (DAG), Safety Gates, Expected Artifacts, Failure Modes.

### Playbook 1: Operation Pareto Swarm (CP-SAT Weight Sweeper) — FLAGSHIP

**Objective:** Discover optimal CP-SAT constraint weights via parallel Pareto search with autonomous error recovery.

**DAG:**

```
[Node A: SETUP] ──► [Node B: CODEX runs 100 iterations in Docker sandbox]
                         │                                        │
                         │ every 20 iters                         │ on completion
                         ▼                                        ▼
                    [Node C: GEMINI compresses attention] ──► [Node D: OPUS Pareto analysis]
                                                                  │
                                                                  ▼
                                                         [Node E: CODEX deploys winners]
```

**Agent roles:**
- **Codex** (Node B): Generates and runs `tune_weights.py` in Docker sandbox. Mutates `EQUITY_PENALTY_WEIGHT`, `SundayCallEquityConstraint`, and `WeekdayCallEquityConstraint` weights by +/-15% per iteration. Extracts `MAD_YTD_equity`, `coverage_rate`, `TTFI`. Writes discrete `iter_NNN.json` files.
- **Gemini** (Node C): Every 20 iterations, reads the newest JSON payloads. Extracts mathematical correlations. Overwrites `compressed_memory.md`.
- **Opus** (Node D): Reads compressed memory and all iteration data. Identifies Pareto-optimal configuration minimizing (MAD Equity, TTFI) subject to coverage >= 0.98. Outputs `winning_weights.json`.
- **Codex** (Node E): Injects winning weights into `call_equity.py`. Runs `pytest`. If green, commits.

**Safety gates:**
- Docker `--network none` sandbox for all solver execution
- SAVEPOINT rollbacks (zero SSD wear per iteration)
- `num_search_workers = 4` (prevents Core Illusion)
- Discrete JSON files (prevents VirtioFS corruption)
- 3-retry max on iteration failure with bifurcated recovery (Gemini classifies, Opus patches)

**Expected artifacts:**
- `agent_workspace/iterations/iter_001.json` through `iter_100.json`
- `agent_workspace/signals/compressed_memory.md`
- `agent_workspace/analysis/winning_weights.json`
- Updated `call_equity.py` with optimized weights
- Commit: `chore: auto-tuned CP-SAT weights via Tri-Agent Pareto sweep`

### Playbook 2: Alembic Migration Untangler

**Objective:** Audit the migration chain for orphans, circular dependencies, and revision ID length violations. Propose fixes without modifying existing migrations.

**Agent roles:**
- **Gemini:** Ingest entire `backend/alembic/versions/` (fits in 1M context). Map full dependency graph. Identify orphan revisions, chain breaks, revision IDs exceeding 64 chars.
- **Opus:** Receive Gemini's findings. Design corrective migrations following `YYYYMMDD_short_desc` convention. Validate against `backend/schema.sql`.
- **Codex:** Run `alembic history`, `alembic check`, `alembic upgrade head` / `alembic downgrade -1` in test environment.

**Safety gates:**
- MCP `create_backup_tool` before any migration test
- Each corrective migration = one atomic commit
- 3-retry max, then escalate

### Playbook 3: Chaos Monkey Excel Fuzzing

**Objective:** Generate adversarial Excel workbooks and verify the import pipeline handles them gracefully.

**Agent roles:**
- **Gemini:** Read all import test fixtures and service code (`backend/app/services/xlsx_import.py`, `half_day_import_service.py`). Catalog tested edge cases. Identify gaps.
- **Opus:** Design fuzz test cases based on gap analysis. Write tests using project conventions.
- **Codex:** Run fuzz tests. Report pass/fail. Categorize failures by severity.

**Safety gates:**
- Fuzzing targets the import parser, never the database
- Test fixtures in `backend/tests/fixtures/` (auto-cleaned)
- No production data involved

### Playbook 4: Legacy Excel Archaeology

**Objective:** Reverse-engineer historical Excel workbook structures to improve import pipeline compatibility.

**Agent roles:**
- **Gemini:** Ingest Excel templates and import source code. Map column headers to Pydantic schema fields. Identify unmapped columns and format variations.
- **Opus:** Design schema extensions or normalization rules. Assess impact on existing import tests.
- **Codex:** Create roundtrip import tests (load, import, export, diff). Verify no data loss.

**Safety gates:**
- Legacy files are read-only reference (gitignored)
- Model changes flagged for human approval (require Alembic migration)

---

## 9. Reference Implementation — Call Equity YTD

The Feb 26, 2026 sprint (PRs #1196-#1202) serves as the proof-of-concept that validates this architecture. The Call Equity YTD mini-sprint delivered exactly the kind of multi-concern, mathematically rigorous work that the Tri-Agent Swarm automates.

### What Was Delivered

| Deliverable | PR | Implementation |
|------------|-----|---------------|
| 1. `prior_calls` hydration | #1199 | GROUP BY query in `engine.py:980` with CASE expression for `effective_type` |
| 2. YTD aggregation | #1199 | High-performance `CallAssignment` GROUP BY replacing `extract("dow")` pattern |
| 3. Post-solve write-back | #1199 | `_sync_academic_year_call_counts()` — idempotent recalculation from source of truth |
| 4. MAD restructuring | #1199 | `AddAbsEquality` in `call_equity.py:125` — F-multiplied integers for CP-SAT |
| 5. FMIT weekend split | #1202 | `is_weekend` CASE expression reclassifies overnight+weekend as sunday equity |

### Why This Maps to the Swarm

In the Tri-Agent model, this sprint would decompose as:

- **Gemini:** Ingest `engine.py`, `call_equity.py`, `call_assignment.py`, all test files. Identify the `prior_calls` dead code, the Min-Max formulation flaw, and the FMIT misclassification.
- **Opus:** Design the MAD formulation mathematically. Specify the GROUP BY query. Design the idempotent write-back pattern. Verify Block 1 (July) edge case degrades correctly.
- **Codex:** Apply the code changes. Run `pytest backend/tests/test_call_equity_ytd.py`. Verify 9/9 tests pass.

### Block 1 (July) Edge Case

When `prior_calls` is empty (Block 1, academic year start), the MAD math degrades flawlessly:
1. `history` = 0, `total_history` = 0
2. CP-SAT equation simplifies to: `dev = F * sum(vars) - sum(all_vars)`
3. With 8 faculty and 4 Sundays: Faculty getting 1 call → `|8(1) - 4| = 4`. Faculty getting 0 → `|0 - 4| = 4`. Faculty getting 2 → `|8(2) - 4| = 12` (massive penalty).
4. Acts as a mathematically perfect single-block equity optimizer until YTD history arrives in Block 2.

### Key Files

- `backend/app/scheduling/engine.py:980` — `prior_calls` hydration via GROUP BY
- `backend/app/scheduling/engine.py` — `_sync_academic_year_call_counts()` method
- `backend/app/scheduling/constraints/call_equity.py:125` — MAD formulation
- `backend/tests/test_call_equity_ytd.py` — 9 test cases covering all scenarios

---

## 10. Safety Rules — The Three Laws

### Law 1: DB Snapshot Rule (Backup Before Writes)

**Statement:** Before any operation that writes to the database, a backup must be created.

**Enforcement:**
- MCP tools: `create_backup_tool(reason="...")` → `get_backup_status_tool()` → `restore_backup_tool(backup_id="...")`
- `/safe-schedule-generation` skill already enforces backup-first workflow
- Antigravity guardrails (`.antigravity/guardrails.md`) block DB operations without confirmation
- `CLAUDE.md` "Database Safety Rules" section mandates this

**For overnight runs:** The `tune_weights.py` harness uses SAVEPOINT rollbacks (Refinement 2), so no backup is needed for sweep iterations — the data never actually persists.

### Law 2: Atomic Git Commits (One Concern Per Commit)

**Statement:** Each git commit addresses exactly one concern. No mixed-purpose commits.

**Enforcement:**
- SDK domain territory system: commit prefixes `core:`, `api:`, `sched:`, `fe:`, `test:`
- Codex planning cycle (`.codex/AGENTS.md`): "One focused change per branch"
- Preflight automation template: list changed files in commit message
- Branch naming conventions: `gemini/*`, `claude/*`, `codex/*`

**Why it matters:** The Feb 2026 Mac Mini triage found 34% chaff. Root cause: "Shared Base Contamination" — all branches shared 860 lines of non-task changes because they forked from a dirty tree. Atomic commits prevent this.

### Law 3: Infinite Loop Breaker (5-Attempt Max, Then Escalate)

**Statement:** If any agent fails at the same task 5 times, it must stop and escalate.

**Enforcement:**
- Antigravity guardrails define escalation at 2+ failures (raised to 5 for overnight autonomy)
- Antigravity recovery procedures define a 4-level recovery hierarchy
- Codex planning cycle includes: "If tests fail, analyze and retry. Do not loop."

**Escalation format** (from `.antigravity/autopilot-instructions.md`):
```
ESCALATION REQUIRED:
- Task: [what was being done]
- Blocker: [what prevented completion]
- Attempted: [what was tried, up to 5 times]
- Recommendation: [suggested next step]
```

**Escalation chain:** Gemini/Codex → Opus → Human. If Opus itself is blocked, output to `agent_workspace/signals/escalation.md` for morning human review.

---

## 11. SCIF / Air-Gap Compliance

### Air-Gap Readiness (Verified)

The Air-Gap Readiness Audit (`docs/planning/AIRGAP_READINESS_AUDIT.md`) confirms all core services run 100% local:
- PostgreSQL, Redis: local containers
- OR-Tools CP-SAT solver: bundled Python package
- Scheduling, ACGME validation, resilience framework: zero cloud dependencies
- 97+ MCP tools: local server at `http://127.0.0.1:8080/mcp`

### AI Agent Cloud Dependencies

| Agent | API Provider | Air-Gap Alternative | Capability Loss |
|-------|-------------|---------------------|-----------------|
| Gemini 3.1 Pro | Google | Gemma 2 27B via Ollama | Reduced context (8K vs 1M), no Search grounding |
| Opus 4.6 | Anthropic | Claude Desktop for Mac (if available) | Reduced Agent Teams support |
| Codex 5.3 | OpenAI | DeepSeek-Coder-V3 via Ollama | Reduced speed, no Cerebras acceleration |

### Honest Assessment

**Full Tri-Agent power requires API access.** However:
1. All data stays local (no PII leaves the machine)
2. Only prompts and code snippets traverse the API (sanitizable)
3. Docker `--network none` prevents container-level data exfiltration
4. The MCP server, database, and all tools run locally
5. API access is optional and can be disabled per-agent

### SCIF Deployment Model

For classified environments, substitute local models with reduced capability. The instruction file protocol, communication topology, coordination patterns, and safety rules remain **identical**. The architecture is model-agnostic by design — the same DAG works with any model that can read a prompt and write a response.

---

## 12. Perplexity Computer Lessons

### Patterns Borrowed

**1. Meta-Router / Task Classification**

Perplexity classifies tasks before routing to models. The Tri-Agent Swarm adopts this: Gemini for analysis, Opus for reasoning, Codex for execution. This mirrors the "skill-required vs. skill-free" routing from Future D, but with higher-capability models in each slot.

**2. Sub-Agent Spawning with Dependency Management**

Perplexity spawns specialized sub-agents and queues dependent tasks. The Tri-Agent Swarm implements this via `asyncio.create_task()` in `swarm_orchestrator.py`. Dependencies are managed through the DAG topology: Node D waits for Node B to complete; Node C runs concurrently with Node B.

**3. Cached Intermediate Artifacts**

Perplexity caches intermediate results between sub-agents. The Tri-Agent Swarm uses discrete JSON files and `compressed_memory.md` as the cache layer. Each agent's output is a durable filesystem artifact that other agents read.

**4. Model-Agnostic Tool Layer**

Perplexity's tool execution layer operates independently of the model layer. The Tri-Agent Swarm achieves this through: MCP tools (model-independent), instruction files (model-specific), git (universal), Docker sandbox (model-independent).

### Patterns NOT Applicable

**1. 19-Model Dynamic Routing** — We use 3 models with static role assignment. Simpler, but sufficient for our domain.

**2. Per-Token Cost Optimization** — Irrelevant for local execution with fixed hardware costs.

**3. Persistent Cross-Session Memory** — Perplexity has 3-tier memory. We have: `MEMORY.md` (long-term), instruction files (session-persistent), git history (permanent). Simpler but adequate.

**4. Real-Time Model Swapping** — Perplexity swaps models mid-task. Our agents are assigned at task start. Swapping requires session restart.

### Sources

- [Perplexity Computer: Multi-Model AI Agent Guide](https://www.digitalapplied.com/blog/perplexity-computer-multi-model-ai-agent-guide)
- [Perplexity Computer: Unified Multi-Agent Autonomous AI Platform](https://solidtiming.co/perplexity-computer-unified-ai-platform/5352/)
- [Perplexity Computer Orchestrates 19 AI Models](https://www.trendingtopics.eu/perplexity-computer-orchestrates-19-ai-models-to-execute-month-long-workflows/)
- [Perplexity Launches Computer](https://alternativeto.net/news/2026/2/perplexity-launches-computer-as-general-purpose-ai-agent-platform-with-model-selection/)

---

## 13. Comparison to Prior Art

| Feature | Future D (Qwen) | Comet 8-Lane | SDK Roadmap | Mini + Codex | **Tri-Agent Swarm** |
|---------|-----------------|--------------|-------------|--------------|---------------------|
| **Models** | Opus + Qwen | Opus x8 | Opus x8 | Opus + Codex | **Gemini + Opus + Codex** |
| **Status** | Concept only | Browser demo | Concept code | Practice (2 systems) | **Formalized architecture** |
| **Parallelism** | 4 Qwen instances | 8 browser tabs | 8 async lanes | 2 independent | **3 complementary + DAG** |
| **Instruction files** | CLAUDE.md only | CLAUDE.md only | CLAUDE.md only | CLAUDE.md + AGENTS.md | **All three (isolated)** |
| **Domain skills** | Opus only | Opus only | Opus only | Opus only | **Opus only (by design)** |
| **MCP tools** | No | No | No | Opus only | **Opus only (by design)** |
| **Air-gap ready** | Partial | No (browser) | No (API) | Partial | **Yes (with degradation)** |
| **Docker sandbox** | No | No | No | No | **Yes (`--network none`)** |
| **VirtioFS-safe I/O** | N/A | N/A | N/A | N/A | **Yes (discrete files)** |
| **Overnight capable** | No | No | Designed for it | Codex 15/night | **4 integrated playbooks** |
| **Error recovery** | N/A | Manual | Designed | Partial | **Bifurcated (classify + patch)** |
| **Chaff rate** | N/A | N/A | N/A | 34% | **Target: < 15%** |

### What Is Superseded

- **`.antigravity/FUTURE_D_HYBRID_MODEL_ORCHESTRATION.md`** — Superseded. Qwen replaced by Codex (faster, already running). Gemini added (no Qwen equivalent for 1M context). Skill-required vs. skill-free routing principle preserved.
- **`.antigravity/ROADMAP_SDK_ORCHESTRATION.md`** — Partially superseded. SDK concepts (Kinase Loop, Domain Territory, Dual Nucleus) remain valid as internal Opus patterns. Tri-Agent Swarm is the higher-level orchestration.
- **`.antigravity/FUTURE_B_MANAGER_VIEW.md`** — Superseded for AI coordination. Manager View was 5 agents of same model. Tri-Agent Swarm is 3 agents of different models.

---

## 14. Implementation Roadmap

### Phase 0: Current State (Done)

- Opus 4.6 on Mac Mini running Claude Code with Agent Teams
- Codex 5.3 App with 15 nightly automations (01:00-02:00 HST)
- Gemini CLI installed (`brew install gemini-cli`)
- `GEMINI.md`, `CLAUDE.md`, `AGENTS.md` all exist with inline guardrails
- MCP Server running at `http://127.0.0.1:8080/mcp`
- All three agents can independently work on the repo
- Call Equity YTD sprint validates the multi-concern pattern (7 PRs merged)

### Phase 1: Playbook Prototyping (1-2 weeks)

- Create `agent_workspace/` directory structure
- Write `scripts/run_in_sandbox.sh` and `scripts/swarm_orchestrator.py`
- Manually run Operation Pareto Swarm once with human supervision
- Validate agents can read each other's filesystem artifacts
- Verify git branch naming conventions don't conflict
- Time end-to-end playbook execution
- Document failure modes discovered

### Phase 2: Nightly Integration (2-4 weeks)

- Add Tri-Agent playbooks to Codex automation schedule
- Stagger execution: Gemini (audit) → Opus (plan) → Codex (run)
- Use `cron` or Codex App automation framework for scheduling
- Monitor via Prometheus metrics and structured logs
- Target: reduce chaff rate from 34% to < 15%

### Phase 3: Full Autonomous Operation (4-8 weeks)

- Remove human supervision for proven playbooks
- Add new playbooks based on Phase 1-2 learnings
- Implement automated branch triage
- Add 5th playbook: "Continuous Documentation Sync"

### Phase 4: SCIF Hardening (When Needed)

- Substitute cloud APIs with local models (Gemma, Llama, DeepSeek)
- Validate all playbooks with degraded local models
- Create offline model cache on Mac Mini
- Document reduced capabilities and workarounds

---

## 15. Open Questions

1. **Gemini CLI MCP Integration** — Can `gemini-cli` connect to `http://127.0.0.1:8080/mcp` via `gemini mcp`? If yes, Gemini gains access to all 97+ project tools, massively expanding its capability beyond analysis.

2. **Codex CLI MCP Integration** — Does `.codex/config.toml` MCP support Streamable HTTP transport? If not, Codex remains a "fast operator" without project tool access.

3. **Context Window Overlap** — When Gemini produces a 10-page compressed report, how much can Opus hold in 200K context? May need a summarization step between Nodes C and D.

4. **File Conflict Resolution** — What happens when Gemini and Codex both try to write to `TODO.md` during the same overnight run? Git handles branch-level conflicts, but filesystem-level locking may be needed for shared coordination files.

5. **Chaff Rate Target** — Current dual-system produces 34% chaff. Hypothesis: Gemini's repo-wide auditing reduces chaff by catching errors before Opus/Codex act. Target: < 15%. Measurement method TBD.

6. **Per-Night Cost Model** — API costs for all four playbooks? Gemini free tier (60 req/min, 1000/day) may suffice. Opus and Codex costs depend on token volume per playbook.

7. **Agent Teams Expansion** — When Opus Agent Teams matures, can Gemini or Codex be wrapped as "virtual teammates" using filesystem-based message passing? This would formalize the coordination topology within a single framework.

8. **Partial Overnight Failure Recovery** — If Gemini completes but Opus crashes mid-playbook, how does the next night handle partial state? Each playbook needs idempotency specification.

---

## 16. Appendices

### Appendix A: File Reference Index

| File | Purpose |
|------|---------|
| `.claude/Governance/PAI_SQUARED.md` | PAI² framework (4 principles) |
| `.antigravity/FUTURE_D_HYBRID_MODEL_ORCHESTRATION.md` | Prior art: Qwen hybrid concept |
| `.antigravity/ROADMAP_SDK_ORCHESTRATION.md` | Prior art: SDK phases, Kinase Loop |
| `.antigravity/FUTURE_B_MANAGER_VIEW.md` | Prior art: Manager View (same-model parallel) |
| `docs/planning/AIRGAP_READINESS_AUDIT.md` | Air-gap capability proof |
| `GEMINI.md` | Gemini instruction file |
| `CLAUDE.md` | Opus instruction file |
| `AGENTS.md` / `.codex/AGENTS.md` | Codex instruction files |
| `docs/development/CODEX_APP_AUTOMATIONS_0100.md` | 15 nightly Codex automations |
| `backend/app/scheduling/engine.py` | Scheduling engine (prior_calls, write-back) |
| `backend/app/scheduling/constraints/call_equity.py` | MAD equity formulation |
| `backend/tests/test_call_equity_ytd.py` | Call equity YTD tests (9 cases) |
| `scripts/run_in_sandbox.sh` | Docker sandbox wrapper (to create) |
| `scripts/swarm_orchestrator.py` | Async DAG orchestrator (to create) |

### Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **PAI²** | Parallel Agentic Infrastructure × Personal Artificial Intelligence |
| **SCIF** | Sensitive Compartmented Information Facility |
| **ACGME** | Accreditation Council for Graduate Medical Education |
| **CP-SAT** | Constraint Programming Satisfiability solver (Google OR-Tools) |
| **MAD** | Mean Absolute Deviation — equity metric replacing Min-Max (Chebyshev) |
| **TTFI** | Time To First Item — solver responsiveness metric |
| **Auftragstaktik** | Mission-type orders — delegate intent, not recipe |
| **DAG** | Directed Acyclic Graph — task dependency structure |
| **VirtioFS** | macOS Docker Desktop filesystem driver (POSIX locking issues) |
| **SAVEPOINT** | PostgreSQL nested transaction — enables zero-cost rollbacks |
| **Split-Brain** | Architecture where API calls (host) and compute (container) are physically separated |
| **Chaff** | Branches that fail triage and cannot be merged (34% current rate) |
| **PARL** | Proximal Advantage Reinforcement Learning — self-correction pattern |

### Appendix C: Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2025-12-25 | Comet 8-lane browser automation | Proved parallel execution works; identified fragility |
| 2025-12-26 | Future D concept (Qwen squad) | Skill-required vs. skill-free routing principle |
| 2025-12-26 | SDK Orchestration Roadmap | Replace browser with Python SDK |
| 2026-02-05 | Codex 15 nightly automations | Proved overnight autonomous execution |
| 2026-02-21 | Mac Mini + Codex dual system | Two autonomous systems running in practice |
| 2026-02-26 | Tri-Agent Swarm architecture | Three heterogeneous models > N homogeneous models |
| 2026-02-26 | Docker `--network none` sandbox | Split-Brain: API on host, math in container |
| 2026-02-26 | Discrete JSON files over JSONL | VirtioFS cross-OS locking evasion |
| 2026-02-26 | SAVEPOINT rollbacks for sweeps | Zero SSD wear for iterative optimization |
| 2026-02-26 | Hardcode `num_search_workers = 4` | Docker CPU limit vs `os.cpu_count()` mismatch |

### Appendix D: Master Tri-Agent Prompt Template

The following template is designed for pasting into the Antigravity IDE CLI to initialize Operation Pareto Swarm:

```
@all_agents INITIALIZE OPERATION PARETO SWARM
MISSION: Discover optimal CP-SAT weights using parallel Pareto search.
ENVIRONMENT: Mac Mini (Apple Silicon). DB: PostgreSQL 15. Framework: FastAPI + OR-Tools.

ROLE ENFORCEMENT:
@codex: Orchestrator and Executor. Write Python, run DB operations, trigger workflows.
@gemini: Context Engine. Ingest logs and compress into insights.
@opus: Chief Architect. Read compressed insights and generate mathematical patches.

HARDWARE GUARDRAILS:
1. SAVEPOINT ROLLBACKS: Wrap SchedulingEngine.generate() in session.begin_nested()
   and rollback() after extracting metrics. Zero SSD writes per iteration.
2. CP-SAT CPU BOUNDING: Hardcode solver.parameters.num_search_workers = 4.
3. CONTEXT ISOLATION: @opus must NEVER read raw JSONL. @gemini reads and compresses.

EXECUTION DAG:
[A: SETUP] -> @codex creates agent_workspace/ directories
[B: EXECUTE] -> @codex runs 100 iterations via run_in_sandbox.sh
[C: MONITOR] -> @gemini compresses every 20 iterations to compressed_memory.md
[D: ANALYZE] -> @opus reads compressed memory, outputs winning_weights.json
[E: DEPLOY] -> @codex injects weights, runs pytest, commits if green

ERROR RECOVERY: On failure, @gemini classifies (math vs syntax), @opus patches.
Max 3 retries per iteration. After 3, log to escalation.md and skip.
```

---

*This architecture document describes a SCIF-compliant, air-gapped equivalent of Perplexity Computer, purpose-built for military medical residency scheduling. The system orchestrates three AI models from three different providers on a single Mac Mini, with zero data spillage risk and full overnight autonomous capability.*

*PAI² Tri-Agent Swarm: purpose at scale, secured by design.*
