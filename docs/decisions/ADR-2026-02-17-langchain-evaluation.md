# ADR: LangChain Framework Evaluation

**Date:** 2026-02-17
**Status:** DEFERRED
**Context:** Evaluated whether LangChain should be incorporated into the project or personal assistant stack.

---

## Context

LangChain is an open-source LLM orchestration framework (Python/JS) providing chains, agents, memory, RAG, and tool-calling abstractions. Evaluated for two potential use cases:
1. **Personal assistant stack** (OpenClaw/text-router on Mac Mini)
2. **AAPM scheduling agent** (multi-step constraint solving with RAG)

## Decision

**Do not incorporate now.** Revisit for AAPM scheduling agent when building production multi-agent workflows.

---

## Risk/Benefit Analysis

### Benefits

| Benefit | Relevance to AAPM | Relevance to PA Stack |
|---------|-------------------|----------------------|
| **Model-agnostic interfaces** — swap LLM providers with minimal code | Medium (already use FastAPI + httpx) | Low (already switching 4 models) |
| **Structured agent loops** — ReAct, plan-and-execute, tool-calling patterns | High (scheduling solver could use multi-step reasoning) | Low (text-router already does this) |
| **LangGraph** — multi-agent orchestration with state machines | High (research agent + solver + validator pipeline) | Low (not needed for iMessage) |
| **LangSmith** — observability, tracing, evaluation framework | High (production system needs proper eval) | Low (CSV logging sufficient for personal use) |
| **RAG abstractions** — vector store integrations, retrieval chains | Medium (already have RAG via MCP, 67+ docs) | Low (Gemini embeddings working) |
| **Community ecosystem** — 700+ integrations, extensive docs | Medium | Low |

### Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Latency overhead** — LangChain agent loops add 2-5s per step vs custom code | High for PA (need <0.6s), Low for AAPM (batch OK) | Only use for AAPM, not PA stack |
| **Dependency bloat** — langchain-core, langchain-community, langchain-openai, etc. | Medium | Pin versions, isolate in AAPM venv |
| **Abstraction opacity** — logic scattered across chains, callbacks, agent executors | Medium | Mitigate with LangSmith tracing |
| **Version churn** — LangChain has frequent breaking changes (v0.1→0.2→0.3 in 2024-2025) | Medium | Pin to stable release, test on upgrade |
| **MLX incompatibility** — tool-calling formats optimized for OpenAI/Anthropic cloud, not local models | High for PA, N/A for AAPM | AAPM uses cloud models anyway |
| **Vendor lock-in to LangSmith** — observability tied to their platform | Low | Can use open-source alternatives (Langfuse) |
| **Over-engineering** — adds abstraction for things already working | High for PA, Medium for AAPM | Only adopt where custom code insufficient |

### Cost/Benefit Summary

| Use Case | Net Assessment |
|----------|---------------|
| **Personal assistant (OpenClaw/text-router)** | **Skip.** Custom stack is faster, simpler, and purpose-built. LangChain adds latency and complexity for no gain. |
| **AAPM scheduling agent** | **Consider when building.** Multi-step constraint solving + RAG + tool calling + evaluation is LangChain's sweet spot. LangGraph for multi-agent coordination. LangSmith for production observability. |

---

## When to Revisit

Adopt LangChain for AAPM when ANY of these conditions are met:
1. Building a multi-step scheduling agent that needs RAG + tools + structured output
2. Need standardized evaluation framework for schedule quality (LangSmith)
3. Building multi-agent pipeline (research → solve → validate → explain)
4. Current MCP tool orchestration becomes insufficient for complex workflows

## Alternatives Considered

| Alternative | Assessment |
|-------------|------------|
| **Raw OpenAI/Anthropic SDKs** | Current approach for AAPM. Works but doesn't scale to multi-agent. |
| **CrewAI** | Simpler multi-agent framework. Less mature than LangGraph. |
| **AutoGen (Microsoft)** | Good for code generation agents. Overkill for scheduling. |
| **Custom (current PA stack)** | Best for personal assistant. Not worth replacing. |
| **Haystack** | RAG-focused. Less agent support than LangChain. |

## References

- LangChain docs: https://python.langchain.com
- LangGraph: https://langchain-ai.github.io/langgraph/
- LangSmith: https://smith.langchain.com
- Terminal Bench Deep Agents (GPT-5.2-Codex + LangChain harness)
