# Kimi K2.5 — Moonshot AI

> **doc_type:** ai_patterns
> **Last Updated:** 2026-02-05
> **Keywords:** kimi, k2.5, moonshot, MoE, agent swarm, open source, multimodal, PARL

---

## Overview

Kimi K2.5 is an open-source native multimodal agentic model from Moonshot AI, released January 27, 2026. It is built through continual pretraining on approximately 15 trillion mixed visual and text tokens atop Kimi-K2-Base.

## Architecture

| Property | Value |
|----------|-------|
| Architecture | Mixture-of-Experts (MoE) |
| Total parameters | ~1 trillion |
| Active parameters | ~32 billion per request |
| Context window | 256K tokens |
| Modalities | Text, vision, video (native multimodal) |
| License | Open source (HuggingFace: `moonshotai/Kimi-K2.5`) |

## Modes

| Mode | Description |
|------|-------------|
| **K2.5 Instant** | Fast responses, low latency |
| **K2.5 Thinking** | Extended reasoning (similar to chain-of-thought) |
| **K2.5 Agent** | Single-agent tool use and execution |
| **K2.5 Agent Swarm** (beta) | Multi-agent orchestration, up to 100 sub-agents |

## Agent Swarm

The headline feature. For complex tasks, K2.5 self-directs an agent swarm:

- Up to **100 sub-agents** executing in parallel
- Up to **1,500 tool calls** per swarm session
- **3x-4.5x wall-clock speedup** vs single-agent execution
- **80% reduction in end-to-end runtime** on complex tasks
- Trained via **PARL** (Parallel-Agent Reinforcement Learning)

This is distinct from our PAI hierarchy — K2.5's swarm is model-native parallelism, while PAI uses explicit agent spawning with identity cards and chain-of-command.

## Benchmark Performance

| Benchmark | K2.5 Score | Notes |
|-----------|-----------|-------|
| BrowseComp | 74.9% | vs 29.2% human baseline |
| Hallucinations | 100% | Perfect score |
| General Knowledge | 100% | Perfect score |
| Reasoning | 100% | Perfect score |
| Ethics | 100% | Perfect score |
| Mathematics | 96.8% | |
| Coding | 92.0% | Especially strong on frontend |
| HLE (text, no tools) | 31.5 | |
| HLE (text, with tools) | 51.8 | |
| HLE (image, no tools) | 21.3 | |
| HLE (image, with tools) | 39.8 | |

K2.5 shows **59.3%** and **24.3%** improvements over K2 Thinking on internal benchmarks.

## Competitive Position

Kimi K2.5 is positioned as competitive with GPT-5.2, Claude Opus 4.5, and Gemini 3 Pro across multiple benchmarks while being fully open-source. Agent Swarm outperforms Claude Opus 4.5 on BrowseComp.

**Key differentiators:**
- Open-source (MoE weights on HuggingFace)
- Native multimodal (not bolted-on vision)
- Agent Swarm is model-native, not framework-dependent
- Strong visual coding (image-to-code, UI generation, video reconstruction)

## Availability

| Surface | URL |
|---------|-----|
| Web app | kimi.com |
| API | platform.moonshot.ai |
| IDE integration | Kimi Code |
| Model weights | huggingface.co/moonshotai/Kimi-K2.5 |

## Relevance to This Project

### Potential Use Cases

1. **Visual schedule review** — K2.5's vision capabilities could analyze schedule screenshots or Excel exports for anomalies
2. **Agent Swarm for parallel validation** — Native 100-agent parallelism could run comprehensive ACGME checks faster than sequential PAI spawning
3. **Frontend development** — K2.5 excels at frontend/UI coding, potentially useful for schedule visualization components
4. **Open-source deployment** — 32B active params makes local deployment feasible, avoiding API costs for non-sensitive operations

### Limitations for This Project

1. **No Claude Code integration** — K2.5 doesn't run in Claude Code CLI; would need separate tooling
2. **Untested with MCP** — Agent Swarm uses its own orchestration, not MCP protocol
3. **Military context** — No evidence of HIPAA/military compliance tooling
4. **Reliability unknown** — New model, limited production track record

### Model Routing Recommendation

| Task | Best Model | Why |
|------|-----------|-----|
| Scheduling engine (CP-SAT) | Claude Opus 4.6 | Deep codebase context, MCP integration |
| ACGME compliance validation | Claude Opus 4.6 | RAG integration, proven reliability |
| Frontend UI components | K2.5 or Claude | K2.5 strong on frontend, but Claude has project context |
| Visual schedule analysis | K2.5 | Native multimodal, strong vision |
| Parallel research/exploration | K2.5 Agent Swarm | 100-agent native parallelism |
| RAG document authoring | Claude Opus 4.6 | Best long-context reasoning |

## Sources

- [Kimi K2.5 Blog](https://www.kimi.com/blog/kimi-k2-5.html)
- [HuggingFace Model Card](https://huggingface.co/moonshotai/Kimi-K2.5)
- [NVIDIA NIM Model Card](https://build.nvidia.com/moonshotai/kimi-k2.5/modelcard)
- [Artificial Analysis Benchmarks](https://artificialanalysis.ai/models/kimi-k2-5)
