# PAI² Framework

**Parallel Agentic Infrastructure × Personal Artificial Intelligence**

---

## Origin

This framework builds on [Daniel Miessler's PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure) (Personal AI Infrastructure), adapted for multi-agent orchestration in an institutional context.

### What We Borrowed

From Miessler's PAI:
- **"System Over Intelligence"** - Orchestration and scaffolding matter more than model intelligence. A well-designed system with an average model beats a brilliant model with poor system design.
- **Modular Architecture** - Independent, composable capabilities (his "packs" → our agents/skills)
- **Plain-Text Configuration** - No vendor lock-in, human-readable
- **Personal Assistant as Core Concept** - AI as collaborator, not just tool

### What We Added

The "squared" represents multiplication, not addition:

| Miessler's PAI | PAI² Extension |
|----------------|----------------|
| Single user, single assistant | Multi-agent hierarchy |
| Personal productivity | Institutional scheduling |
| Sequential task execution | Parallel agent spawning |
| Modular packs | Auftragstaktik command structure |
| Kai as the assistant | ORCHESTRATOR → Deputies → Coordinators → Specialists |

---

## The Two Dimensions

### Dimension 1: Parallel Agentic Infrastructure

The **orchestration layer** - how agents coordinate at scale.

- **Hierarchy**: ORCHESTRATOR → Deputies → Coordinators → Specialists
- **Parallelism**: Party skills spawn 6-120 probes simultaneously
- **Delegation**: Auftragstaktik (mission-type orders, not recipes)
- **Coordination**: G-Staff advisory structure (G1-G6)

See [HIERARCHY.md](./HIERARCHY.md) for the full command structure.

### Dimension 2: Personal Artificial Intelligence

The **philosophy layer** - how the system serves humans.

- **System > Intelligence**: Infrastructure enables outcomes
- **Persistent Context**: Memory across sessions via RAG, handoffs
- **Domain Expertise**: Agents carry specialized knowledge
- **Graceful Degradation**: Fail safely, escalate appropriately

---

## Why "Squared"?

The dimensions multiply:

```
Infrastructure alone = Tools without purpose
Personalization alone = Purpose without scale
PAI² = Purpose × Scale
```

Parallel infrastructure enables personalization at institutional scale. Personalization makes the infrastructure serve actual human needs rather than abstract efficiency.

---

## Application to This Project

### The Domain: Military Medical Residency Scheduling

- **Institutional**: Serves a residency program, not one person
- **Constrained**: ACGME compliance, military regulations, coverage requirements
- **High-Stakes**: Wrong schedules affect patient care and resident wellbeing

### How PAI² Fits

| PAI² Concept | Application Here |
|--------------|------------------|
| Parallel agents | QA-party (8+ validators), search-party (120 probes) |
| Mission-type orders | "Enable ACGME-compliant swap rollback" not "implement POST /api/..." |
| System > intelligence | MCP tools + constraint engine > raw model capability |
| Persistent context | RAG with 67+ domain documents, session handoffs |
| Domain expertise | MEDCOM for ACGME, SCHEDULER for constraints |

---

## Key Principles

### 1. Delegate, Don't Direct

**Bad**: "Create SwapCancellationService in backend/app/services/..."
**Good**: "Enable automatic swap rollback for ACGME violations. Audit trail required."

### 2. Parallelize Where Possible

Independent tasks should run concurrently. The `*-party` skills exist for this:
- `/search-party` - 120 parallel reconnaissance probes
- `/qa-party` - 8+ parallel validators
- `/plan-party` - 10 parallel strategy generators

### 3. Escalate When Blocked

Agents own their domain. They escalate when:
- Approaching a boundary (security, compliance)
- Blocked after 2+ attempts
- Unclear requirements require clarification

### 4. Tools Over Intelligence

MCP tools encode domain knowledge:
- `validate_schedule_tool` catches ACGME violations
- `rag_search` surfaces policy decisions
- `get_defense_level_tool` shows system health

The system knows things the model doesn't.

---

## References

- **Origin**: [danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure)
- **Blog**: [Building a Personal AI Infrastructure](https://danielmiessler.com/blog/personal-ai-infrastructure)
- **Kai Bundle**: [Bundles/Kai](https://github.com/danielmiessler/Personal_AI_Infrastructure/tree/main/Bundles/Kai)
- **Local**: [HIERARCHY.md](./HIERARCHY.md), [SPAWN_CHAINS.md](./SPAWN_CHAINS.md)

---

*Last Updated: 2026-01-13*
