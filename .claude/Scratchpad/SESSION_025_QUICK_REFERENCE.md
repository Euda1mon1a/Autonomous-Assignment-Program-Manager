# Session 025 Quick Reference Index

**Updated:** 2025-12-30
**Purpose:** Fast lookup for Session 025 concepts and artifacts
**Format:** Organized by use case

---

## When You Need...

### A Quick Parallel Task

**Use:** `/parallel-explore`, `/parallel-implement`, `/parallel-test`, `/handoff-session`

**Files:** `.claude/commands/`

**Example:**
```bash
/parallel-explore "Find all ACGME validation logic"
# Auto-spawns 3-5 agents in parallel
# Synthesizes findings
```

---

### To Understand Parallelization

**Start here:** `.claude/docs/PARALLELISM_FRAMEWORK.md`

**Then read:** `.claude/Scratchpad/histories/SIGNAL_AMPLIFICATION_SESSION_025.md` (lines 1-50)

**Key insight:** Parallelization has no overhead. Architecture exists. Session 025 solved *ergonomics*.

---

### To Understand a Specific Signal Type

**Signal Propagation signals:** `.claude/protocols/SIGNAL_PROPAGATION.md` (lines 19-29)
- CHECKPOINT_REACHED
- DEPENDENCY_RESOLVED
- CONFLICT_DETECTED
- INTEGRATION_REQUIRED
- EARLY_COMPLETION
- BLOCKED
- ESCALATE

**Result Streaming signals:** `.claude/protocols/RESULT_STREAMING.md` (lines 16-24)
- STARTED
- PROGRESS(n%)
- PARTIAL_RESULT
- BLOCKED
- COMPLETED
- FAILED

---

### To Clarify Explore vs G2_RECON

**Read:** `.claude/Scratchpad/histories/EXPLORER_VS_G2_RECON.md`

**TL;DR:**
- **Explore** = Infrastructure (subagent_type parameter)
- **G2_RECON** = Role/Persona (uses Explore as execution mechanism)
- **Analogy:** Helicopter (Explore) vs Scout (G2_RECON)

**Decision tree:** Lines 219-232

---

### To Define a Parallel Task with Dependencies

**Read:** `.claude/docs/TODO_PARALLEL_SCHEMA.md`

**Schema fields:**
```python
{
    "content": str,
    "parallel_group": str,       # Tasks in same group run together
    "can_merge_after": [str],    # Task dependencies
    "blocks": [str],             # What this task unblocks
    "stream": str,               # Stream assignment (A-E)
    "terminal": int,             # Terminal assignment (1-10)
}
```

---

### To Set Up a 10-Terminal Session

**Use:** `/handoff-session` command

**Or read:** `.claude/protocols/MULTI_TERMINAL_HANDOFF.md`

**File created:** `.claude/Scratchpad/PARALLEL_SESSION_[YYYYMMDD_HHMMSS].md`

**Layout:**
```
Terminals 1-3:  Stream A (MCP/Scheduling)
Terminals 4-6:  Stream B (Backend Tests)
Terminals 7-8:  Stream C (Frontend)
Terminal 9:     Stream D (Integration)
Terminal 10:    Stream E (Security/Performance)
```

---

### To Know What Model Tier to Use

**Algorithm:** `.claude/Scratchpad/histories/SIGNAL_AMPLIFICATION_SESSION_025.md` (lines 71-82)

```
Complexity Score = (Domains × 3) + (Dependencies × 2) + (Time × 2) + (Risk × 1) + (Knowledge × 1)

0-5   → haiku
6-12  → sonnet
13+   → opus
```

**Or check:** Skill `model_tier` field in `.claude/skills/*/SKILL.md`

---

### To Find What Skills Can Run in Parallel

**Look for:** `parallel_hints` field in `.claude/skills/*/SKILL.md`

**Example:**
```yaml
parallel_hints:
  can_parallel_with: [code-review, lint-monorepo, security-audit]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
```

---

### To Understand Result Streaming vs Signal Propagation

**Result Streaming:** Agent emits progress (5 messages during 5-minute task)
**Signal Propagation:** Agents coordinate with each other (Agent A says "I'm done", Agent B resumes)

**Visual:**
```
Result Streaming:  Single agent → ORCHESTRATOR (progress updates)
Signal Propagation: Agent A → ORCHESTRATOR → Agent B (coordination)
```

---

### To Resuming an Interrupted Marathon Session

**File:** `.claude/Scratchpad/PARALLEL_SESSION_*.md`

**Read:**
1. **Session Configuration** section - What's the context?
2. **Stream Status** section - Where was each stream?
3. **Blocking Issues** section - What was blocked?
4. **Handoff Notes** section - What's next?

**Protocol:** `.claude/protocols/MULTI_TERMINAL_HANDOFF.md`

---

### To Report Progress from Your Agent

**Emit:** Result Streaming signals

```json
{
  "signal": "PROGRESS",
  "percent": 50,
  "checkpoint": "files_analyzed",
  "partial": {
    "files_found": 12,
    "patterns_matched": 3
  },
  "next_checkpoint": "tests_verified"
}
```

**Details:** `.claude/protocols/RESULT_STREAMING.md` (lines 47-73)

---

### To Coordinate with Other Parallel Agents

**Emit:** Signal Propagation signals

```json
{
  "signal_type": "DEPENDENCY_RESOLVED",
  "emitter": "ARCHITECT",
  "stream": "A",
  "payload": {
    "dependency_id": "schema-migration",
    "output_location": "alembic/versions/xyz.py",
    "consumers": ["SCHEDULER", "QA_TESTER"]
  }
}
```

**Details:** `.claude/protocols/SIGNAL_PROPAGATION.md` (lines 33-46)

---

### To Batch-Read Multiple Files (Speculative Parallelism)

**Pattern:** Level 4 of PARALLELISM_FRAMEWORK

```python
# Old (sequential)
read("swap_service.py")
# [analyze]
read("swap_models.py")
# [analyze]
read("swap_routes.py")

# New (speculative, parallel)
files = await read_parallel([
    "swap_service.py",
    "swap_models.py",
    "swap_routes.py",
    "swap_auto_matcher.py",
    "test_swap*.py"
])
# [analyze all at once]
```

**Why:** Reading is cheap, round-trips are expensive. Even over-reading is faster than sequential discovery.

---

### To Understand How This All Fits Together

**Read in order:**
1. `.claude/Scratchpad/histories/SIGNAL_AMPLIFICATION_SESSION_025.md` (Master narrative)
2. `.claude/docs/PARALLELISM_FRAMEWORK.md` (Decision rules)
3. `.claude/protocols/SIGNAL_PROPAGATION.md` (Coordination)
4. `.claude/protocols/RESULT_STREAMING.md` (Visibility)
5. `.claude/protocols/MULTI_TERMINAL_HANDOFF.md` (Marathon execution)

**Time:** ~30-40 minutes

---

## File Locations Quick Map

```
.claude/
├── Scratchpad/
│   ├── histories/
│   │   ├── SIGNAL_AMPLIFICATION_SESSION_025.md    ← Master narrative
│   │   ├── EXPLORER_VS_G2_RECON.md                ← Infrastructure clarity
│   │   └── SESSION_025_HANDOFF_SUMMARY.md         ← This session's work
│   ├── VECTOR_DB_PENDING.md                       ← Indexing plan
│   └── PARALLEL_SESSION_*.md                      ← Created by /handoff-session
│
├── commands/
│   ├── parallel-explore.md                        ← Parallel exploration
│   ├── parallel-implement.md                      ← Parallel implementation
│   ├── parallel-test.md                           ← Parallel testing
│   └── handoff-session.md                         ← 10-terminal setup
│
├── protocols/
│   ├── RESULT_STREAMING.md                        ← Progress visibility
│   ├── SIGNAL_PROPAGATION.md                      ← Agent coordination
│   └── MULTI_TERMINAL_HANDOFF.md                  ← Marathon coordination
│
├── docs/
│   ├── PARALLELISM_FRAMEWORK.md                   ← Level 1-4 decision rules
│   ├── TODO_PARALLEL_SCHEMA.md                    ← Task metadata
│   └── CCW_PARALLELIZATION_ANALYSIS.md            ← Comparative analysis
│
└── skills/
    ├── test-writer/SKILL.md                       ← Has parallel_hints
    ├── code-review/SKILL.md                       ← Has parallel_hints
    ├── lint-monorepo/SKILL.md                     ← Has parallel_hints
    └── [7 more skills with parallel_hints]
```

---

## Key Vocabulary

| Term | Meaning | Example |
|------|---------|---------|
| **Signal** | A structured message from one agent or to ORCHESTRATOR | DEPENDENCY_RESOLVED, PROGRESS(75%) |
| **Stream** | A work domain (A-E) with 2-3 terminals | Stream A = MCP/Scheduling |
| **Terminal** | A parallel Claude session (1-10 in marathons) | Terminal 4 runs backend tests |
| **Checkpoint** | Safe pause point where agents can synchronize | After schema migration completes |
| **Handoff** | File tracking multi-terminal session state | PARALLEL_SESSION_20251230_191300.md |
| **Parallel Group** | Tasks that can run concurrently | quality-checks, backend-tests |
| **Architecture** | System design and structure | G-Staff, PARALLELISM_FRAMEWORK |
| **Ergonomics** | How easy it is to use the architecture | `/parallel-explore`, auto-tier selection |

---

## Signal Types at a Glance

### Result Streaming (Single Agent → Visibility)

| Signal | Meaning |
|--------|---------|
| STARTED | Work begun |
| PROGRESS(n%) | Partial completion |
| PARTIAL_RESULT | Early findings available |
| BLOCKED | Waiting on dependency |
| COMPLETED | Full results ready |
| FAILED | Unrecoverable error |

### Signal Propagation (Agent ↔ Agent Coordination)

| Signal | Meaning |
|--------|---------|
| CHECKPOINT_REACHED | Safe pause point reached |
| DEPENDENCY_RESOLVED | Output available for consumers |
| CONFLICT_DETECTED | Write collision imminent |
| INTEGRATION_REQUIRED | Milestone reached, sync needed |
| EARLY_COMPLETION | Finished ahead of schedule |
| BLOCKED | Cannot proceed, waiting |
| ESCALATE | Needs human/higher authority |

---

## Common Patterns

### Pattern: Independent Parallel Tasks
```
Skill A --+
Skill B --+-→ SYNTHESIZER → Result
Skill C --+
```

**Use when:** Tasks don't depend on each other
**Example:** 3 code reviews of different modules

### Pattern: Sequential with Handoff
```
Skill A (schema) → DEPENDENCY_RESOLVED → Skill B (tests) → DEPENDENCY_RESOLVED → Skill C (integration)
```

**Use when:** Output of one is input to next
**Example:** Schema migration → test writing → integration test

### Pattern: Level 3 Integration Point
```
Stream A ──┐
Stream B ──┼→ CHECKPOINT_REACHED → Integration Phase → All Streams Resume
Stream C ──┘
```

**Use when:** All streams must sync before continuing
**Example:** Database migration needs all test suites to understand new schema

---

## Decision Tree: Which Pattern to Use?

```
Can tasks run independently?
├─ YES → Parallel (spawn together)
│        Emit PROGRESS signals
│        SYNTHESIZER merges results
│
└─ NO → Are dependencies known?
       ├─ YES → Sequential with DEPENDENCY_RESOLVED signals
       │        Producer → Consumer chain
       │
       └─ NO → Exploratory
              Use Explore subagent_type
              Read speculatively (Level 4)
              Decide after partial analysis
```

---

## Next Steps

1. **Read:** SIGNAL_AMPLIFICATION_SESSION_025.md (5 min)
2. **Skim:** PARALLELISM_FRAMEWORK.md (10 min)
3. **Reference:** This file when you need to invoke patterns
4. **Use:** `/parallel-explore`, `/parallel-implement`, etc. for common tasks
5. **Extend:** Add `parallel_hints` to your own skills

---

*Last Updated: 2025-12-30*
*Created by: G4_CONTEXT_MANAGER*
*Status: Ready for immediate use*

