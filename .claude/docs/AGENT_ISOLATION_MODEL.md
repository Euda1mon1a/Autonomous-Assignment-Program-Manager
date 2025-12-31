***REMOVED*** AGENT ISOLATION MODEL

**Version:** 1.0
**Last Updated:** 2025-12-31
**Purpose:** Define context isolation, memory boundaries, and inter-agent communication protocols

---

***REMOVED******REMOVED*** 1. CONTEXT ISOLATION REQUIREMENTS

***REMOVED******REMOVED******REMOVED*** Purpose

Prevent information leakage between parallel agents and ensure each agent operates with proper scope boundaries.

***REMOVED******REMOVED******REMOVED*** Isolation Levels

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 1: Input Isolation

Each agent receives:

```
[Agent Context]
├── Explicit Mission/Task
├── Allowed File Paths (whitelist)
├── Forbidden File Paths (blacklist)
├── Permission Tier
├── Time Limit
└── Resource Budget
```

**NOT Included:**
```
✗ Previous agent conversations
✗ Other agents' scratch pads
✗ Session memory from other agents
✗ Shared global state
✗ Credentials or environment variables
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 2: Working Isolation

During execution, agents operate in isolated contexts:

**Separate State:**
- Agents cannot read each other's files
- Agents cannot access each other's variables
- Agents cannot modify each other's outputs
- Each agent has its own file read cache

**Example: Parallel Agents**

```
Agent A (Code Review)        Agent B (Test Writer)        Agent C (Documentation)
├── Read docs/api.md        ├── Read tests/conftest.py  ├── Read README.md
├── Read backend/app/**     ├── Read app/**             ├── Write docs/
└── Generate review.txt     ├── Write tests/test_*.py   └── Update README.md
                            └── Generate test_report.md
```

Each agent sees ONLY its assigned scope.

***REMOVED******REMOVED******REMOVED******REMOVED*** Level 3: Output Isolation

Agents produce outputs in designated locations:

```
.claude/
├── agent-outputs/
│   ├── agent-A-review-12345.txt      ***REMOVED*** Agent A results
│   ├── agent-B-tests-12345.py        ***REMOVED*** Agent B results
│   └── agent-C-docs-12345.md         ***REMOVED*** Agent C results
└── scratchpad/
    ├── agent-A-work.txt              ***REMOVED*** Agent A working notes
    ├── agent-B-work.txt              ***REMOVED*** Agent B working notes
    └── agent-C-work.txt              ***REMOVED*** Agent C working notes
```

Agents cannot directly modify each other's outputs.

---

***REMOVED******REMOVED*** 2. MEMORY ISOLATION

***REMOVED******REMOVED******REMOVED*** Session Memory Boundaries

***REMOVED******REMOVED******REMOVED******REMOVED*** What Each Agent Knows

```
Self Memory (Private)
├── Current task/mission
├── File contents read during session
├── Execution history (current only)
├── Computation results
├── Temporary state/variables
└── Scratch notes

NOT Available (Private to Other Agents)
├── Other agent sessions
├── Previous session memory (if multi-session)
├── Global state
├── Shared variables
└── Cross-agent communication history
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Memory Cleanup

**After Agent Completion:**

```bash
***REMOVED*** Safe cleanup (data archived)
1. Archive scratchpad to timestamped file
2. Archive results to timestamped file
3. Clear runtime memory
4. Clear file read cache
5. Clear API call history
```

**Safe Archive Example:**
```
.claude/archives/
└── 2025-12-31-14-30-45/
    ├── agent-context.json       ***REMOVED*** Mission parameters
    ├── scratchpad.md            ***REMOVED*** Working notes
    ├── results.md               ***REMOVED*** Final output
    ├── file-access-log.json     ***REMOVED*** Files read
    └── execution-log.json       ***REMOVED*** Operations log
```

***REMOVED******REMOVED******REMOVED*** Context Window Management

**For Long Sessions:**

When context grows large (check with `/context`):

```
1. Create session summary:
   - What was accomplished
   - Key findings
   - Decisions made
   - Remaining work

2. Document in .claude/session-summary.md

3. Use /clear to reset context

4. Resume: "Read .claude/session-summary.md and continue"
```

**Example Session Summary:**

```markdown
***REMOVED*** Session Summary - Code Review Agent

***REMOVED******REMOVED*** Task
Review Pull Request ***REMOVED***42 for security issues

***REMOVED******REMOVED*** Completed
- [x] Reviewed authentication changes
- [x] Checked input validation
- [x] Verified SQL injection prevention
- [x] Found 3 security issues

***REMOVED******REMOVED*** Findings
1. Missing CSRF token validation in /api/swap
2. Weak password validation (8 chars min needed)
3. Sensitive data in error messages

***REMOVED******REMOVED*** Next Steps
- [x] Create review comments
- [ ] Verify fixes are applied
```

---

***REMOVED******REMOVED*** 3. CACHE ISOLATION

***REMOVED******REMOVED******REMOVED*** File Read Cache

**Per-Agent Caching:**

```
Agent Read Cache
├── Key: file_path + modification_time
├── Value: file_contents
├── TTL: Duration of agent execution
└── Isolation: Not shared with other agents
```

**Cache Invalidation:**

```python
***REMOVED*** If a file is modified during agent execution
***REMOVED*** (e.g., by another agent)
***REMOVED***
***REMOVED*** Previous agent's cache is stale
***REMOVED*** - Don't automatically refresh
***REMOVED*** - Agent should re-read if needed
***REMOVED*** - Not agent's responsibility to detect changes
```

**Best Practice:**

Agent A reads file → Cache stored
Agent B writes file → Agent A's cache becomes stale
Agent A reads again → Gets fresh copy from disk

This is safe because agents operate sequentially on files.

***REMOVED******REMOVED******REMOVED*** API Response Cache

**Caching Strategy:**

```
API calls (to backend API or external services)
├── Cache responses for 15 minutes
├── Key: {endpoint} + {params}
├── Isolation: Per-agent, not shared
└── Bypass: If agent explicitly re-reads
```

**Example:**

```
Agent requests: GET /api/persons/PGY1-01
Response cached locally
Next request (if same params): Served from cache
After 15 min: Cache expires, fresh request made
```

***REMOVED******REMOVED******REMOVED*** Preventing Cache Poisoning

**Validation:**

```python
***REMOVED*** Before using cached data:
1. Verify cache key matches request
2. Check cache age (within TTL)
3. Validate response structure
4. If any doubt, bypass cache and re-fetch
```

---

***REMOVED******REMOVED*** 4. ENVIRONMENT VARIABLE HANDLING

***REMOVED******REMOVED******REMOVED*** Agent Access to Environment Variables

**FORBIDDEN:**
```
✗ .env files (secrets)
✗ DATABASE_URL
✗ JWT_SECRET_KEY
✗ WEBHOOK_SECRET
✗ API_KEYS
✗ AWS credentials
✗ Any credential variables
```

**ALLOWED (if needed for work):**
```
✓ DEBUG_MODE                ***REMOVED*** Boolean flag
✓ LOG_LEVEL                 ***REMOVED*** Info, debug, warning
✓ APP_ENV                   ***REMOVED*** Development, staging, production
✓ ALLOWED_CORS_ORIGINS      ***REMOVED*** Public configuration
```

**Access Pattern:**

```python
***REMOVED*** WRONG - Reading .env directly
with open('.env', 'r') as f:
    config = f.read()

***REMOVED*** CORRECT - Use official config class
from app.core.config import Settings
settings = Settings()
log_level = settings.LOG_LEVEL  ***REMOVED*** Public config only
```

***REMOVED******REMOVED******REMOVED*** Secrets Management

**Rule: Never expose secrets to agents**

```
┌─────────────────────┐
│  Production Secret  │  ← Hidden from agents
│   (JWT_SECRET)      │
└─────────────────────┘
         ↓ (decrypted server-side only)
┌──────────────────────────┐
│   Token Validation       │  ← Agent can call API
│   (Use API endpoints)    │  ← Agent cannot see secret
└──────────────────────────┘
```

**When Agent Needs API Access:**

```
1. User provides API endpoint URL
2. User provides read-only API key (if needed)
3. Agent uses endpoint to fetch data
4. Agent NEVER sees underlying secrets
```

---

***REMOVED******REMOVED*** 5. INTER-AGENT COMMUNICATION

***REMOVED******REMOVED******REMOVED*** Communication Protocols

***REMOVED******REMOVED******REMOVED******REMOVED*** Asynchronous Communication (Recommended)

Agents communicate through files and git:

```
Agent A
└── Commit: "Add new feature X"
    └── Push to feature branch

Agent B (reads from git)
└── Review commits
└── Create PR comment
└── Commit: "Add tests for feature X"

Agent C (reads from git)
└── Review all commits
└── Approve PR
```

**Advantages:**
- Explicit audit trail
- No timing dependencies
- Clear cause-and-effect

***REMOVED******REMOVED******REMOVED******REMOVED*** Synchronous Communication (Careful)

For multi-agent orchestration:

```
Orchestrator Agent
├── Agent A: "Analyze file X"
│   └── Wait for completion
│   └── Get results from output file
│
├── Agent B: "Write tests based on Agent A results"
│   └── Read Agent A output
│   └── Generate tests
│   └── Write output
│
└── Agent C: "Review all work"
    └── Read Agent A + B outputs
    └── Verify consistency
```

**Rules:**
- Use timestamped file names to avoid race conditions
- Orchestrator responsible for sequencing
- Clear input/output file specifications
- Timeout if agent doesn't complete

***REMOVED******REMOVED******REMOVED*** Avoiding Communication Antipatterns

**Bad: Shared Global State**
```python
***REMOVED*** WRONG - Don't do this
global_state = {"counter": 0}

Agent A increments counter → 1
Agent B reads counter → 1
Agent A increments counter → 2
Agent B reads counter → ??? (stale value)
```

**Good: Explicit File Handoff**
```
Agent A
└── Write: output.json
    {"task": "parsed", "result": "X"}

Agent B
└── Read: output.json
└── Proceed with Agent A's result
```

---

***REMOVED******REMOVED*** 6. SENSITIVE DATA ISOLATION

***REMOVED******REMOVED******REMOVED*** Personal Information (PII/PHI)

**NEVER Share Between Agents:**

```
✗ Resident names
✗ Faculty names
✗ Email addresses
✗ Phone numbers
✗ Medical information
✗ Schedule assignments (reveals deployment patterns)
✗ Absence records
```

**Instead: Use Identifiers**

```
✓ PGY1-01 (synthetic resident ID)
✓ FAC-PD (program director)
✓ BLOCK-2025-001 (block identifier)
✓ ROT-INPATIENT-Q1 (rotation type)
```

***REMOVED******REMOVED******REMOVED*** OPSEC/PERSEC Handling

For military medical residency data:

```
Exposure Risk                  Handling
─────────────────────────────────────────────
Duty patterns reveal           Keep local only
military capabilities          Don't share via agents

TDY/Deployment data            Never in logs
indicates redeployment          Never in outputs

Absence data                   Keep local only
reveals movements              Don't transmit

Schedule shows                 Synthetic IDs only
staffing levels                In documentation
```

***REMOVED******REMOVED******REMOVED*** Data Leakage Prevention

**Audit Checklist:**

Before agent outputs to files/logs:

```
[ ] No resident names
[ ] No faculty names
[ ] No email addresses
[ ] No medical information
[ ] No deployment data
[ ] No schedule assignments
[ ] No TDY information
[ ] No absence records
[ ] Using synthetic IDs only
[ ] Generic error messages
```

---

***REMOVED******REMOVED*** 7. ERROR HANDLING & ISOLATION

***REMOVED******REMOVED******REMOVED*** Exception Isolation

**Errors don't leak across agents:**

```
Agent A encounters error
└── Agent A's exception handler catches
    └── Agent A logs locally
    └── Agent A reports to user
    └── Agent A cleanup/rollback
    └── Agent B NOT affected
```

**Example:**

```python
***REMOVED*** Agent A - Database agent
try:
    migration_result = await run_migration()
except MigrationError as e:
    logger.error(f"Migration failed: {e}")
    ***REMOVED*** Agent A handles gracefully
    ***REMOVED*** Agent B (if parallel) continues unaffected
    await rollback_changes()
    return {"status": "failed", "reason": "See logs"}
```

***REMOVED******REMOVED******REMOVED*** Cascading Failure Prevention

**Monitor for cascade patterns:**

```
Agent A fails
  ├─→ Writes error state to shared file
  └─→ Agent B detects error, handles gracefully
      ├─→ Agent B skips dependent work
      └─→ User alerted to dependency issue
```

**Best Practice:**

- Make each agent independent where possible
- Document dependencies explicitly
- Implement timeouts and fallbacks
- Never assume other agents succeeded

---

***REMOVED******REMOVED*** 8. ISOLATION VALIDATION CHECKLIST

Before spawning parallel agents:

- [ ] Each agent has explicit, non-overlapping file scope
- [ ] Input contexts are complete and self-contained
- [ ] No shared mutable state
- [ ] Communication protocol defined (if needed)
- [ ] File naming prevents collisions
- [ ] Secrets/PII not passed to agents
- [ ] Output locations are isolated
- [ ] Error handling doesn't affect other agents
- [ ] Cleanup procedures documented
- [ ] Monitoring/observability in place

---

***REMOVED******REMOVED*** 9. TECHNICAL ARCHITECTURE

***REMOVED******REMOVED******REMOVED*** Process Model

```
┌──────────────┐
│ Orchestrator │
└──────┬───────┘
       │
       ├─→ [Agent A] ──→ [File Output A]
       │
       ├─→ [Agent B] ──→ [File Output B]
       │
       ├─→ [Agent C] ──→ [File Output C]
       │
       └──→ [Synthesizer] ──→ Combine results
```

Each agent operates in isolation, results merged at end.

***REMOVED******REMOVED******REMOVED*** Memory Model

```
Global Memory (Read-Only)
├── Codebase files
├── Shared documentation
└── Project constants

Per-Agent Memory (Isolated)
├── Agent task context
├── File read cache
├── Computation results
├── Scratch space
└── Output files
```

***REMOVED******REMOVED******REMOVED*** State Machine

```
Agent Lifecycle:

[Created]
    ↓ (receive context)
[Initialized]
    ↓ (begin work)
[Executing]
    ├→ Read files (cache locally)
    ├→ Process data (isolated)
    ├→ Write outputs (designated location)
    └→ (repeats)
[Completed]
    ↓ (cleanup)
[Archived]
```

---

***REMOVED******REMOVED*** References

- [Access Control Model](AGENT_ACCESS_CONTROL.md)
- [Input Validation](AGENT_INPUT_VALIDATION.md)
- [Data Protection](AGENT_DATA_PROTECTION.md)
- [Security Audit Framework](AGENT_SECURITY_AUDIT.md)
