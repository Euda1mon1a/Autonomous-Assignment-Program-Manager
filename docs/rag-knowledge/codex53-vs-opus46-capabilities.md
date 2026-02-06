# Codex 5.3 vs Claude Opus 4.6 Capability Delta

> Last updated: 2026-02-06
> Suggested doc_type: `ai_patterns`
> Audience: orchestrators, agent authors, and documentation maintainers

## Purpose

Provide a stable capability comparison for routing work between Codex and Claude in this repository, with a special focus on RAG document authoring and ingestion.

## Release Snapshot

- `GPT-5.3-Codex` announced by OpenAI on `2026-02-05`.
- `Claude Opus 4.6` announced by Anthropic on `2026-02-05`.
- Both are positioned for longer-running, tool-using, agentic workflows.

## Capability Matrix

| Capability Area | Codex 5.3 | Claude Opus 4.6 | Repo Impact |
|---|---|---|---|
| Long-running agentic coding | OpenAI positions Codex 5.3 for long-running tasks with research, tools, and complex execution | Anthropic positions Opus 4.6 for sustained agentic tasks in large codebases | Either model can own multi-step backend/frontend tasks if guardrails are explicit |
| Interactive steering during execution | Codex emphasizes in-task steering and frequent progress updates while the task runs | Anthropic emphasizes adaptive reasoning and effort controls for balancing depth/latency | For high-risk changes, keep human steering checkpoints every major phase |
| Benchmark framing in vendor materials | OpenAI highlights SWE-Bench Pro, Terminal-Bench 2.0, OSWorld, GDPval | Anthropic highlights Terminal-Bench 2.0, Humanity's Last Exam, GDPval-AA, long-context retrieval | Do not route solely on benchmark names; route on concrete repo workflow fit |
| Long-context behavior | Codex post emphasizes stronger end-to-end computer work and interactive supervision | Opus 4.6 introduces a 1M-token context window in beta and improved long-context retrieval claims | Large documentation and architecture synthesis can be routed to Opus-first |
| Model controls | Codex workflow is centered on task execution + steering in Codex surfaces | Opus 4.6 adds adaptive thinking and explicit effort controls | Opus is useful when you need predictable depth tuning for doc-heavy reasoning |
| Availability surfaces | OpenAI states Codex 5.3 availability in app/CLI/IDE/web for paid ChatGPT plans | Anthropic states Opus 4.6 availability on claude.ai, API, and major cloud platforms | Mixed-model operating model is viable for this monorepo |

## Recommended Split for This Repo

- `Claude Opus 4.6` primary lane:
  - Drafting and structuring new RAG documents.
  - Long-context synthesis across existing docs and policies.
  - High-depth reasoning passes before ingestion.
- `Codex 5.3` primary lane:
  - Repo-grounded implementation and verification of doc wiring changes.
  - Tooling updates (`DOC_TYPE_MAP`, ingestion scripts, index docs).
  - Fast follow-up edits across multiple files with execution feedback.

## Current Mode: RAG Docs Sans Codex

Use this when Claude is creating RAG docs before Codex is in the loop.

1. Write the document in `docs/rag-knowledge/` with stable, reusable content.
2. Assign an approved `doc_type` (typically `ai_patterns` or `agent_spec` for model workflow docs).
3. Ingest with `rag_ingest` and include source/date metadata.
4. Verify retrieval with `rag_search` using a unique phrase.
5. Add file-to-doc_type mapping in ingestion automation if this file should be included in bulk refresh.

## Future Mode: Incorporate Codex After Authoring

1. Claude generates initial draft and rationale.
2. Codex performs repo fit pass:
   - checks taxonomy consistency,
   - updates ingestion maps,
   - updates index/readme references,
   - validates no broken internal links.
3. Human approves publication and ingestion.

## Canonical Ingestion Snippet

```python
content = open("docs/rag-knowledge/codex53-vs-opus46-capabilities.md").read()

result = mcp__residency-scheduler__rag_ingest(
    content=content,
    doc_type="ai_patterns",
    metadata={
        "source": "codex53-vs-opus46-capabilities.md",
        "updated": "2026-02-06",
        "scope": "model-routing"
    }
)
```

## Sources

- OpenAI: https://openai.com/index/introducing-gpt-5-3-codex/
- OpenAI Codex changelog: https://developers.openai.com/codex/changelog/
- Anthropic announcement: https://www.anthropic.com/news/claude-opus-4-6
- Anthropic model page: https://www.anthropic.com/claude/opus
