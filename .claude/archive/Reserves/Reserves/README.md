# PAI Reserves - Production-Ready Agent Reserves

> **Purpose:** Agents defined but not active during development phase
> **Status:** Reserved for production activation
> **Last Updated:** 2026-01-06

## Philosophy

These are NOT "ghost agents" or unused code. They are **strategic reserves** designed for production operations that aren't needed during development.

> **Note:** MCP tool reserves are in `mcp-server/src/scheduler_mcp/armory/` (separate from agent reserves).

## Activation Triggers

### Production Phase (`production/`)
Activate when transitioning to live environment with real residents:

| Agent | Trigger | Purpose |
|-------|---------|---------|
| INCIDENT_COMMANDER | Production deployment | Crisis response |
| BURNOUT_SENTINEL | Real workload data | Early warning for burnout |
| EPIDEMIC_ANALYST | Real utilization patterns | Burnout transmission modeling |
| CAPACITY_OPTIMIZER | Real staffing decisions | Queuing theory optimization |
| CHAOS_ENGINEER | Production stability testing | Fault injection |
| AGENT_HEALTH_MONITOR | Agent fleet at scale | Performance monitoring |

### Scale Phase (`scale/`)
Activate when agent usage and session volume increases:

| Agent | Trigger | Purpose |
|-------|---------|---------|
| PATTERN_ANALYST | High session volume | Cross-session pattern detection |
| KNOWLEDGE_CURATOR | Large knowledge base | RAG curation at scale |

### Specialized (`specialized/`)
Activate for specific needs:

| Agent | Trigger | Purpose |
|-------|---------|---------|
| TRAINING_OFFICER | Onboarding users | Training documentation |
| DOMAIN_ANALYST | New domain requirements | Domain analysis |
| WORKFLOW_EXECUTOR | Complex multi-step workflows | Step-by-step execution |

## Activation Process

1. Identify activation trigger met
2. Move agent spec from `Reserves/[phase]/` to `.claude/Agents/`
3. Update HIERARCHY.md with new agent
4. Update relevant Coordinator to include in spawn list
5. Test agent in isolation before production use

## DO NOT DELETE

These specs represent significant design work. They are reserves, not waste.
