# Session Protocols and Triggers

> **Purpose:** Semantic triggers for ORCHESTRATOR actions at key session moments
> **RAG Category:** session_protocols
> **Last Updated:** 2025-12-30

---

## Session End Protocol

### Trigger Phrases

When the user says any of these (or semantically similar):
- "wrapping up"
- "coming to a close"
- "finishing up"
- "let's wrap this up"
- "end of session"
- "almost done"
- "before we finish"
- "final tasks"
- "closing out"
- "that's all for today"
- "signing off"

### Required Actions

**ORCHESTRATOR must deploy these assets before session ends:**

#### 1. Audit Team (Parallel)

| Agent | Purpose | Priority |
|-------|---------|----------|
| **DELEGATION_AUDITOR** | Capture delegation metrics, identify patterns | HIGH |
| **QA_TESTER** | Run test suite, verify no regressions | HIGH |
| **CODE_REVIEWER** | Review security-critical changes | MEDIUM |

#### 2. G-Staff Updates (Parallel)

| Agent | Purpose | Priority |
|-------|---------|----------|
| **G1_PERSONNEL** | Update agent roster utilization | MEDIUM |
| **G4_CONTEXT_MANAGER** | Curate session knowledge for RAG | HIGH |
| **META_UPDATER** | Update advisor notes with learnings | MEDIUM |

#### 3. Documentation (If Significant Session)

| Agent | Purpose | Condition |
|-------|---------|-----------|
| **HISTORIAN** | Create session narrative | If novel patterns or turning points |
| **COORD_AAR** | After Action Review | If mission-based session |

### Spawn Pattern

```
ORCHESTRATOR detects session-end trigger
├── Wave 1: Audit Team (parallel)
│   ├── DELEGATION_AUDITOR
│   ├── QA_TESTER
│   └── CODE_REVIEWER
│
├── Wave 2: G-Staff (parallel, after Wave 1)
│   ├── G1_PERSONNEL
│   ├── G4_CONTEXT_MANAGER
│   └── META_UPDATER
│
└── Wave 3: Documentation (if warranted)
    ├── HISTORIAN (if significant)
    └── COORD_AAR (if mission-based)
```

### Why This Matters

**Recursive Self-Improvement Loop:**
1. Session work generates insights
2. Session-end protocol captures those insights
3. Insights are embedded in RAG
4. Future sessions retrieve and build on insights
5. Each session compounds on previous knowledge

**Without this protocol:**
- Learnings stay in one session's context
- Same patterns rediscovered repeatedly
- No institutional memory

**With this protocol:**
- Every session contributes to knowledge base
- Patterns compound across sessions
- ORCHESTRATOR gets smarter over time

---

## Session Start Protocol

### Trigger Phrases

When session begins or user invokes `/startupO`:
- "starting new session"
- "let's begin"
- "new task"
- `/startupO`

### Required Actions

1. **Load Core Context:**
   - CLAUDE.md
   - AI_RULES_OF_ENGAGEMENT.md
   - HUMAN_TODO.md
   - ORCHESTRATOR_ADVISOR_NOTES.md

2. **Check Git State:**
   - Current branch
   - Commits behind main
   - Uncommitted changes

3. **Query RAG for Recent Learnings:**
   - "What did we learn in recent sessions?"
   - "Are there pending recommendations from G1?"
   - "Any unresolved issues from previous sessions?"

4. **Check Codex Feedback:**
   - If PR exists, check for pending Codex comments
   - Codex is rate-limiting step before merge

---

## Mid-Session Checkpoints

### Trigger Phrases

- "let's pause and assess"
- "checkpoint"
- "status check"
- "where are we"

### Actions

1. Review todo list progress
2. Check for blocked tasks
3. Assess context window usage
4. Consider spawning G4 for intermediate knowledge capture

---

## Emergency Protocols

### Trigger Phrases

- "something's broken"
- "production issue"
- "urgent"
- "incident"

### Actions

1. **Spawn COORD_INTEL** for forensic investigation
2. **Check backups** before any fix attempts
3. **Document current state** before changes
4. **Create rollback plan**

---

## Knowledge Compounding Examples

### Example 1: Delegation Pattern Discovery

**Session 015:** Discovered coordinator pattern works well
**Session 020:** Scaled to 16 concurrent agents
**Future Sessions:** RAG retrieves "coordinator pattern scales to 16" automatically

### Example 2: Security Implementation

**Session 020:** Implemented role-based audience restrictions
**Captured:** Pattern stored in session-learnings.md
**Future Sessions:** When building auth features, RAG retrieves the pattern

### Example 3: Test Calibration

**Session 020:** Identified 45 failing tests are calibration issues
**Captured:** Documented in technical debt tracker
**Future Sessions:** When tests fail, RAG can distinguish "calibration" from "regression"

---

## Checklist for ORCHESTRATOR

Before ending any significant session:

- [ ] Deploy DELEGATION_AUDITOR for metrics
- [ ] Deploy G4_CONTEXT_MANAGER to curate knowledge
- [ ] Update ORCHESTRATOR_ADVISOR_NOTES via META_UPDATER
- [ ] Check if HISTORIAN narrative warranted
- [ ] Commit and push changes
- [ ] Create PR if work is complete
- [ ] Document any unfinished work in HUMAN_TODO.md

---

*This document is semantically indexed to trigger on session-end phrases. When you say "wrapping up", RAG retrieval should surface this protocol.*
