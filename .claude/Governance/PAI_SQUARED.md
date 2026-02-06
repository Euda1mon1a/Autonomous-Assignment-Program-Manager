# PAI² Framework

**Parallel Agentic Infrastructure × Personal Artificial Intelligence**

---

## Origin

This framework builds on [Daniel Miessler's PAI](https://github.com/danielmiessler/Personal_AI_Infrastructure) (Personal AI Infrastructure), adapted for multi-agent orchestration in an institutional context.

---

## The Two Dimensions

**Dimension 1 -- Parallel Agentic Infrastructure.**
The orchestration layer. How agents coordinate at scale: concurrent work, shared context, structured delegation.

**Dimension 2 -- Personal Artificial Intelligence.**
The philosophy layer. How the system serves humans: persistent memory, domain expertise, graceful degradation.

The dimensions multiply. Infrastructure alone is tools without purpose. Personalization alone is purpose without scale. PAI² is purpose at scale.

---

## Core Principles

### System > Intelligence

Orchestration and scaffolding matter more than model intelligence. A well-designed system with an average model beats a brilliant model with poor system design. The infrastructure is the product; the model is a replaceable component.

### Tools Over Intelligence

Encode domain knowledge in tools, not prompts. Tools survive model upgrades, context window limits, and session boundaries. The system should know things the model does not.

### Delegate, Don't Direct (Auftragstaktik)

Issue mission-type orders, not recipes. Provide the objective and constraints; let the executor decide how.

- **Bad**: "Create SwapCancellationService in backend/app/services/..."
- **Good**: "Enable automatic swap rollback for ACGME violations. Audit trail required."

The litmus test: if your delegation reads like a recipe, you are micromanaging. If it reads like mission orders, you are delegating.

### Escalate When Blocked

Agents own their domain. They escalate when approaching a boundary (security, compliance), blocked after repeated attempts, or facing ambiguous requirements. Autonomy within boundaries; escalation at boundaries.

---

## References

- [danielmiessler/Personal_AI_Infrastructure](https://github.com/danielmiessler/Personal_AI_Infrastructure)
- [Building a Personal AI Infrastructure](https://danielmiessler.com/blog/personal-ai-infrastructure)

---

*These principles apply regardless of which model, framework, or hierarchy is in use.*
