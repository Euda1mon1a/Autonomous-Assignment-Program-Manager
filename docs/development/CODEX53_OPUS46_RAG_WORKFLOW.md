# Codex 5.3 and Opus 4.6 RAG Workflow (Human Guide)

> Last updated: 2026-02-06
> Audience: human operators coordinating Claude and Codex

## Objective

Run a practical two-model workflow where Claude Opus 4.6 can produce RAG-ready docs now, and Codex 5.3 can be folded in for verification and integration without rework.

## Operating Modes

### Mode A: Claude-Only Authoring (Current)

Use when Codex is not yet in the authoring loop.

- Claude drafts docs in `docs/rag-knowledge/`.
- Human checks stability criteria:
  - reusable beyond one session,
  - not transient task state,
  - clear doc_type target.
- Ingest with MCP `rag_ingest`.
- Verify with `rag_search` and `rag_health`.

### Mode B: Hybrid Author + Integrator (Target)

Use when Codex is available for repo integration.

- Claude owns content quality and domain synthesis.
- Codex owns repository wiring:
  - `DOC_TYPE_MAP` updates in scripts/tasks,
  - index/reference updates,
  - consistency checks against existing docs.
- Human approves final ingest run.

## Parallel Execution Pattern

Run these lanes in parallel when possible:

- Lane 1 (Claude Opus 4.6): draft content and evidence table.
- Lane 2 (Codex 5.3): prepare ingestion plumbing and verify taxonomy.

Sync point:

- Merge when Lane 1 delivers final markdown and Lane 2 confirms file path + doc_type mapping + retrieval test command.

## Handoff Contract

Each model handoff must include:

- `file_path`: exact markdown path.
- `doc_type`: final type used for ingestion.
- `metadata`: source/date/scope fields.
- `verification_query`: one unique search phrase.
- `open_items`: anything requiring human decision.

## Definition of Done

A document is ready when all are true:

1. File exists in `docs/rag-knowledge/`.
2. Content matches RAG stability policy in `docs/rag-knowledge/README.md`.
3. Bulk ingestion mapping is explicit for the file if needed.
4. Ingestion command is recorded.
5. Retrieval test returns expected result.

## Minimal Runbook

```bash
# 1) Optional local bulk embed path
python scripts/init_rag_embeddings.py --doc codex53-vs-opus46-capabilities.md
```

```python
# 2) MCP ingest path (preferred for agent workflows)
mcp__residency-scheduler__rag_ingest(
    content=open("docs/rag-knowledge/codex53-vs-opus46-capabilities.md").read(),
    doc_type="ai_patterns",
    metadata={"source": "codex53-vs-opus46-capabilities.md", "updated": "2026-02-06"}
)
```

```python
# 3) Retrieval verification
mcp__residency-scheduler__rag_search(
    query="Codex 5.3 vs Claude Opus 4.6 capability delta",
    doc_type="ai_patterns",
    top_k=3
)
```

## Model Routing Guidance

- Route to `Opus 4.6` when tasks are context-heavy and require deep synthesis across many documents.
- Route to `Codex 5.3` when tasks require direct repo edits, command execution, and multi-file wiring validation.
- Route to both in parallel for high-value docs that need both synthesis quality and integration rigor.

## References

- `docs/rag-knowledge/RAG_CONTENT_LIFECYCLE.md`
- `docs/rag-knowledge/rag-ingestion-patterns.md`
- `docs/rag-knowledge/README.md`
- https://openai.com/index/introducing-gpt-5-3-codex/
- https://www.anthropic.com/news/claude-opus-4-6
