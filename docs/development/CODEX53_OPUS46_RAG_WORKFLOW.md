# Codex + Opus RAG Workflow (Human Operator Guide)

> Last verified: 2026-02-06
> Audience: humans coordinating Claude and Codex in one shared repo

## Goal

Run a safe two-lane workflow:

- Claude Opus 4.6 can author high-context RAG docs now.
- Codex can integrate, validate, and operationalize those docs in-repo.

## Execution modes

### Mode A: Opus-only authoring (Codex not yet in authoring lane)

1. Draft docs in `docs/rag-knowledge/`.
2. Keep content stable and reusable (no ephemeral session chatter).
3. Add `doc_type`, `source`, and `verified_on` metadata.
4. Ingest with `rag_ingest`.
5. Verify with `rag_search`.

### Mode B: Hybrid author + integrator (recommended target)

1. Opus drafts and revises content for clarity/coverage.
2. Codex performs repo-fit pass:
   - file naming and placement,
   - ingestion map updates,
   - references/index updates,
   - verification command checks.
3. Human approves and runs final ingestion.

## Parallel pattern (best throughput)

- Lane 1 (Opus): content synthesis + evidence quality.
- Lane 2 (Codex): script/config/docs wiring and validation commands.

Sync when both are complete:

- Lane 1 outputs final markdown.
- Lane 2 confirms ingestion and retrieval test readiness.

## Handoff contract (required)

Each draft handoff should include:

- `file_path`
- `doc_type`
- `metadata`
- `verification_query`
- `open_items` (human decisions only)

## Definition of done

A doc is done when all are true:

1. File exists under `docs/rag-knowledge/`.
2. Content is durable and reuse-safe.
3. Ingestion target (`doc_type`) is explicit.
4. Ingestion command is recorded.
5. Retrieval query confirms the doc is returned.

## Minimal commands

```bash
# 1) Optional local bulk embed path
python scripts/init_rag_embeddings.py --doc codex53-vs-opus46-capabilities.md
```

```python
# 2) MCP ingest path (preferred in agent workflows)
mcp__residency-scheduler__rag_ingest(
    content=open("docs/rag-knowledge/codex53-vs-opus46-capabilities.md").read(),
    doc_type="ai_patterns",
    metadata={
        "source": "codex53-vs-opus46-capabilities.md",
        "verified_on": "2026-02-06",
        "scope": "model-routing"
    }
)
```

```python
# 3) Retrieval verification
mcp__residency-scheduler__rag_search(
    query="Codex vs Opus routing guidance for repo integration",
    doc_type="ai_patterns",
    top_k=3
)
```

## Routing quick rules

- Opus-first: deep, long-context synthesis.
- Codex-first: implementation, verification, and repo wiring.
- Parallel: high-value docs where both synthesis depth and integration rigor matter.

## Source links

- OpenAI GPT-5.3-Codex: https://openai.com/index/introducing-gpt-5-3-codex/
- OpenAI Codex changelog: https://developers.openai.com/codex/changelog
- Anthropic Opus 4.6: https://www.anthropic.com/news/claude-opus-4-6
- Anthropic Opus model page: https://www.anthropic.com/claude/opus
- Local RAG lifecycle: `docs/rag-knowledge/RAG_CONTENT_LIFECYCLE.md`
