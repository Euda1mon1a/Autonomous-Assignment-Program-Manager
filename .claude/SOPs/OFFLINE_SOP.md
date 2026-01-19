# Offline Operations SOP

> **Purpose:** Hard blocks for operations when critical systems are unavailable
> **Version:** 1.0
> **Created:** 2026-01-19

---

## MCP Discovery

### RAG Queries
```
rag_search("offline SOP hard blocks system unavailable")
rag_search("circuit breaker open recovery procedure")
rag_search("database offline cannot proceed")
rag_search("MCP server unavailable fallback")
```

### Detection MCP Tools
| Tool | Detects |
|------|---------|
| `rag_health` | RAG system availability |
| `check_circuit_breakers_tool` | Service-level failures |
| `get_defense_level_tool` | Overall system health |
| `get_breaker_health_tool` | Individual breaker status |
| `get_backup_status_tool` | Backup system availability |

### Recovery MCP Tools
| Tool | Purpose |
|------|---------|
| `test_half_open_tool` | Test if service recovered |
| `restore_backup_tool` | Restore from backup |
| `verify_backup_tool` | Verify backup integrity |

### Pre-Operation Health Check
```python
# Run before any critical operation
rag_health()                    # RAG available?
check_circuit_breakers_tool()   # All services up?
get_defense_level_tool()        # System healthy?
get_backup_status_tool()        # Backup available?
```

---

## Critical Distinction

This SOP defines **HARD BLOCKS**, not soft deferrals.

| Type | Meaning | Example |
|------|---------|---------|
| **HARD BLOCK** | Operation CANNOT proceed, MUST stop | "CANNOT generate schedules without database" |
| **Soft Deferral** | Operation CAN proceed, SHOULD wait | "Consider waiting for CI to finish" |

**All blocks in this SOP are HARD BLOCKS. Agents MUST NOT attempt workarounds.**

---

## System Dependencies

### Critical Systems

| System | Required For | Offline Detection |
|--------|--------------|-------------------|
| PostgreSQL | All DB operations | `check_circuit_breakers_tool` fails |
| Redis | Celery tasks, caching | Task queue timeout |
| MCP Server | AI tools, RAG, validation | MCP tool calls fail |
| RAG | Context queries | `rag_health` returns error |

---

## HARD BLOCK Rules

### BLOCK-001: Database Offline

**Condition:** PostgreSQL connection fails or `check_circuit_breakers_tool` reports database unavailable.

**CANNOT:**
- Generate schedules
- Execute swaps
- Create/modify assignments
- Run migrations
- Access any persistent data

**MUST:**
1. Report to user: "Database unavailable. CANNOT proceed with data operations."
2. Log the outage with timestamp
3. Do NOT attempt cache-only operations
4. Do NOT suggest workarounds

**Escalation:** COORD_RESILIENCE → SYNTHESIZER → Human

---

### BLOCK-002: MCP Server Offline

**Condition:** MCP tool calls fail or return connection errors.

**CANNOT:**
- Validate schedules (`validate_schedule_tool`)
- Check compliance (`check_mtf_compliance_tool`)
- Query RAG (`rag_search`)
- Spawn agents via MCP (`spawn_agent_tool`)
- Access any MCP-provided functionality

**MUST:**
1. Report to user: "MCP server unavailable. CANNOT access scheduling tools or RAG."
2. Fall back to direct file reads for governance context (not for validation)
3. Do NOT simulate MCP tool behavior
4. Do NOT skip validation steps

**Escalation:** Any agent → ORCHESTRATOR → Human

---

### BLOCK-003: RAG Offline (MCP Up)

**Condition:** `rag_health` check fails while other MCP tools work.

**CANNOT:**
- Query governance documentation via RAG
- Search for patterns, decisions, or policies
- Inject RAG context into agent spawning

**MUST:**
1. Report to user: "RAG unavailable. Using direct file access for governance context."
2. Read governance files directly:
   - `.claude/Governance/HIERARCHY.md`
   - `.claude/Governance/CAPABILITIES.md`
   - `.claude/dontreadme/synthesis/PATTERNS.md`
3. Note degraded state in all outputs
4. Do NOT proceed without governance context

**Escalation:** G4_CONTEXT_MANAGER → SYNTHESIZER

---

### BLOCK-004: Backend Services Offline

**Condition:** FastAPI backend not responding (health check fails).

**CANNOT:**
- Test API endpoints
- Validate API contracts
- Run integration tests
- Access schedule data via API

**MUST:**
1. Report to user: "Backend offline. CANNOT proceed with API operations."
2. Check Docker container status
3. Provide diagnostic steps:
   ```bash
   docker-compose ps
   docker-compose logs backend --tail 50
   ```
4. Do NOT mock API responses

**Escalation:** COORD_PLATFORM → ARCHITECT → Human

---

### BLOCK-005: Pre-Schedule Write Backup Unavailable

**Condition:** `create_backup_tool` fails before schedule write operation.

**CANNOT:**
- Write any schedule data to database
- Execute swaps
- Bulk assign residents
- Modify assignments

**MUST:**
1. Report to user: "Backup system unavailable. CANNOT write schedule data without backup."
2. Attempt backup retry (max 3 attempts)
3. If retry fails, HARD BLOCK all write operations
4. Do NOT proceed without verified backup

**Escalation:** SCHEDULER → COORD_ENGINE → ARCHITECT → Human

---

### BLOCK-006: Circuit Breaker Open

**Condition:** `check_circuit_breakers_tool` reports any breaker in OPEN state.

**CANNOT:**
- Access the affected service
- Route requests through degraded path
- Assume "it might work now"

**MUST:**
1. Report to user: "Circuit breaker OPEN for [service]. Service is unavailable."
2. Query `get_breaker_health_tool` for details
3. Wait for breaker to enter HALF_OPEN state before retry
4. Do NOT force-close circuit breakers

**Escalation:** COORD_RESILIENCE → SYNTHESIZER → Human

---

## Recovery Procedures

### Database Recovery

```bash
# Check PostgreSQL status
docker-compose ps postgres

# Restart if needed
docker-compose restart postgres

# Verify connection
docker-compose exec postgres pg_isready
```

**After recovery:** Run `check_circuit_breakers_tool` to verify all systems nominal.

### MCP Server Recovery

```bash
# Check MCP status
docker-compose ps mcp

# Restart MCP server
docker-compose restart mcp

# Verify tools available
mcp__residency-scheduler__rag_health()
```

**After recovery:** Run force-multiplier skill to verify governance context accessible.

### Backend Recovery

```bash
# Check backend status
docker-compose ps backend

# View logs
docker-compose logs backend --tail 100

# Restart if needed
docker-compose restart backend

# Run health check
curl http://localhost:8000/health
```

**After recovery:** Run integration tests to verify API contracts.

---

## Emergency Contacts

| Scenario | Escalation Path | Human Notification |
|----------|-----------------|-------------------|
| Database corruption | COORD_PLATFORM → ARCHITECT → Human | Immediate |
| Security breach | COORD_INTEL → SYNTHESIZER → Human | Immediate |
| ACGME violation in production | COMPLIANCE_AUDITOR → ORCHESTRATOR → Human | Immediate |
| Extended outage (>30 min) | Any → ORCHESTRATOR → Human | Within 10 min |

---

## Audit Requirements

All offline events MUST be logged:

**Log Location:** `logs/offline_events.log`

**Log Format:**
```
[TIMESTAMP] [AGENT] [SYSTEM] [DURATION] [RESOLUTION]
2026-01-19T10:30:00Z SCHEDULER PostgreSQL 15m Restart via docker-compose
```

**Review:** DELEGATION_AUDITOR reviews offline logs weekly.

---

## Prohibited Workarounds

The following are **NEVER** acceptable:

| Workaround | Why Prohibited |
|------------|----------------|
| Mock database responses | Data integrity |
| Skip validation steps | ACGME compliance |
| Simulate MCP tool results | Incorrect outputs |
| Force-close circuit breakers | Cascade failures |
| Proceed without backup | Data loss risk |
| Assume cached data is current | Stale data risk |

---

## Related Documents

- [EXCEPTIONS.md](../Governance/EXCEPTIONS.md) - Override catalog (does NOT override HARD BLOCKs)
- [HIERARCHY.md](../Governance/HIERARCHY.md) - Escalation chain
- [STANDING_ORDERS_INDEX.md](../Governance/STANDING_ORDERS_INDEX.md) - Pre-authorized actions (suspended during outage)

---

*HARD BLOCKS are non-negotiable. When in doubt, STOP and escalate.*
