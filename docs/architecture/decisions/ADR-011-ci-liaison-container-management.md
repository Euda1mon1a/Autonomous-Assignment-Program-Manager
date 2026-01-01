# ADR-011: CI_LIAISON Owns Local Container Management

**Date:** 2025-12-31 (Session 41)
**Status:** Adopted

## Context

A significant gap was discovered in the PAI (Programmatic AI) agent hierarchy:

- RAG database found empty due to Docker volume mount not configured
- No agent owned local container operations
- CI_LIAISON owned CI/CD Docker operations
- COORD_PLATFORM owned infrastructure architecture
- Local container ops (docker-compose up/down, volume mounts) were unassigned
- Silent infrastructure failures went undetected

This gap led to infrastructure issues persisting unnoticed.

## Advisory Input

Advisory input was gathered from multiple agents:

| Agent | Recommendation |
|-------|----------------|
| G1_PERSONNEL | Expand CI_LIAISON (minimal overhead) |
| G2_RECON | `docker-containerization` skill already exists |
| G6_SIGNAL | Containers are signal infrastructure (natural fit for CI) |
| G5_PLANNING (PLAN_PARTY) | Hybrid recommendation but convergence on CI_LIAISON |
| MEDCOM | Clear ownership with monitoring needed |

## Decision

**CI_LIAISON** now owns local container orchestration.

### Philosophy
> "It goes up the same way every single time"

This mirrors CI/CD philosophy: reproducibility and consistency.

### Responsibilities

| Area | CI_LIAISON | Escalate To |
|------|------------|-------------|
| `docker-compose up/down/restart` | Owns | - |
| Volume mount validation | Owns | - |
| Container health checks | Owns | - |
| docker-compose.yml changes | Propose | COORD_PLATFORM |
| Dockerfile changes | Diagnose | COORD_PLATFORM |

### Pre-Flight Checklist

Before any task, CI_LIAISON validates:

1. Required containers running (`docker ps`)
2. Volume mounts accessible
3. Inter-container networking functional
4. Health endpoints responding

## Consequences

### Positive
- **Clear ownership**: No more gaps in container responsibility
- **CI philosophy applied**: Consistency in local and remote environments
- **Pre-flight checks**: Catch issues before they cause problems
- **Leverages existing skill**: `docker-containerization` skill already exists
- **Reduced silent failures**: Regular health checks detect issues

### Negative
- **CI_LIAISON scope expands**: Monitor for overload
- **Coordination required**: Must work with COORD_PLATFORM on config changes
- **Learning curve**: CI_LIAISON must understand local development patterns

## Implementation

### Updated CI_LIAISON.md

Added "Local Container Management" section:

```markdown
## Local Container Management

**Philosophy:** "It goes up the same way every single time"

### Responsibilities
- docker-compose lifecycle operations
- Volume mount validation
- Container health monitoring
- Pre-flight infrastructure checks

### Escalation
- Escalate docker-compose.yml changes to COORD_PLATFORM
- Escalate Dockerfile modifications to COORD_PLATFORM
```

### Pre-Flight Validation Checklist

```bash
# CI_LIAISON pre-flight check
docker-compose ps                    # All services running
docker-compose exec backend curl http://localhost:8000/health  # Backend healthy
docker-compose exec mcp-server curl http://localhost:8080/health  # MCP healthy
docker-compose exec db pg_isready    # Database accepting connections
```

## References

- `.claude/Agents/CI_LIAISON.md` - Agent specification
- `.claude/skills/docker-containerization/SKILL.md` - Docker skill
- `docker-compose.yml` - Container orchestration config
- Session 41 handoff documentation

## See Also

**Related ADRs:**
- [ADR-007: Monorepo with Docker Compose](../../.claude/dontreadme/synthesis/DECISIONS.md#adr-007-monorepo-with-docker-compose) - Overall Docker strategy
- [ADR-003: MCP Server for AI Integration](ADR-003-mcp-server-ai-integration.md) - MCP server container management
- [ADR-001: FastAPI + SQLAlchemy](ADR-001-fastapi-sqlalchemy-async.md) - Backend container

**Implementation Files:**
- `docker-compose.yml` - Main orchestration configuration
- `docker-compose.dev.yml` - Development overrides
- `backend/Dockerfile` - Backend container
- `mcp-server/Dockerfile` - MCP server container
- `frontend/Dockerfile` - Frontend container

**Architecture Documentation:**
- [Docker Security Best Practices](../DOCKER_SECURITY_BEST_PRACTICES.md) - Security guidelines

**Agent Specifications:**
- `.claude/Agents/CI_LIAISON.md` - CI_LIAISON responsibilities including container management
- `.claude/Agents/COORD_PLATFORM.md` - COORD_PLATFORM (escalation target for docker-compose.yml changes)

**Skills:**
- `.claude/skills/docker-containerization/` - Docker operations skill

**Development Workflow:**
- `CLAUDE.md#common-commands` - Docker commands reference
