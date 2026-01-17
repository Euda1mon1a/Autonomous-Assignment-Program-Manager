# RAG Content Lifecycle Guide

> **Purpose:** How to maintain RAG content over time
> **Last Updated:** 2026-01-16

---

## When to Add Documents

Add content to RAG when it is:

| Criteria | Description |
|----------|-------------|
| **Stable** | Won't change daily; represents settled knowledge |
| **Reusable** | Applies beyond a single session or task |
| **Domain Knowledge** | ACGME rules, scheduling policies, patterns |
| **Cross-Disciplinary** | Validated exotic concepts with academic grounding |
| **Reference Material** | FAQs, troubleshooting guides, architectural decisions |

### Good Candidates for RAG

- ACGME compliance rules (regulatory, rarely changes)
- Scheduling constraint documentation (domain knowledge)
- PAI agent identity cards (agent_spec)
- Validated resilience patterns (cross-disciplinary)
- Architectural decision records (stable decisions)
- Delegation patterns / Auftragstaktik doctrine

---

## When NOT to Add (Content Policy)

**Do NOT add ephemeral content:**

| Bad Content | Why |
|-------------|-----|
| Session handoffs | Changes every session, quickly stale |
| Current task status | Outdated within hours |
| Individual PR descriptions | Transient, loses relevance after merge |
| Temporary debugging notes | Not generalizable |
| Meeting minutes (raw) | Use synthesized learnings instead |

**Rule of Thumb:** If it will be outdated in a week, it probably shouldn't be in RAG.

---

## Addition Workflow

### Step 1: Create or Update Source Document

Create markdown in `docs/rag-knowledge/`:
```bash
docs/rag-knowledge/
├── acgme-rules.md          # Existing
├── scheduling-policies.md  # Existing
├── my-new-topic.md         # New document
```

### Step 2: Assign Appropriate doc_type

| Content Type | doc_type |
|--------------|----------|
| ACGME regulations | `acgme_rules` |
| Internal procedures | `scheduling_policy` |
| Cross-disciplinary patterns | `resilience_concepts` |
| Physics/biology analogies | `exotic_concepts` |
| Academic sources | `research_paper` |
| Agent identities | `agent_spec` |
| Delegation philosophy | `delegation_patterns` |
| Architecture decisions | `ai_decisions` |

### Step 3: Ingest via MCP

```python
content = open("docs/rag-knowledge/my-new-topic.md").read()

mcp__residency-scheduler__rag_ingest(
    content=content,
    doc_type="appropriate_type",
    metadata={
        "source": "my-new-topic.md",
        "date": "2026-01-16",
        "session": "optional_session_id"
    }
)
```

### Step 4: Verify Ingestion

```python
# Check that content is searchable
mcp__residency-scheduler__rag_search(
    query="unique term from new document",
    doc_type="appropriate_type"
)
```

---

## Update Workflow

When source content changes:

### Step 1: Update Source File

Edit the markdown in `docs/rag-knowledge/`.

### Step 2: Clear Old Chunks

```bash
python scripts/init_rag_embeddings.py --clear-all --doc my-topic.md
```

### Step 3: Re-Ingest

```python
mcp__residency-scheduler__rag_ingest(
    content=open("docs/rag-knowledge/my-topic.md").read(),
    doc_type="same_type",
    metadata={
        "source": "my-topic.md",
        "updated": "2026-01-16"
    }
)
```

---

## Deprecation Workflow

When content is no longer relevant:

### Step 1: Mark Document as Deprecated

Add deprecation notice to source file:
```markdown
> **DEPRECATED:** This document is no longer maintained.
> See [new-document.md](./new-document.md) for current information.
```

### Step 2: Clear RAG Chunks

```bash
python scripts/init_rag_embeddings.py --clear-all --doc deprecated-doc.md
```

### Step 3: Archive or Remove Source

```bash
# Option A: Archive
mv docs/rag-knowledge/deprecated-doc.md docs/rag-knowledge/archive/

# Option B: Delete if truly obsolete
rm docs/rag-knowledge/deprecated-doc.md
```

---

## Quality Criteria Checklist

Before adding content to RAG, verify:

- [ ] **Stable** - Content won't change daily
- [ ] **Reusable** - Applies beyond one session
- [ ] **Searchable** - Uses domain terminology
- [ ] **Attributed** - Source, date, session (if applicable)
- [ ] **Appropriate doc_type** - Matches content category
- [ ] **Well-structured** - Clear headings, scannable format

---

## Integration with /deep-research

When using `/deep-research` to validate exotic patterns:

### Research → RAG Workflow

```
1. Run /deep-research with academic query
   └── Agent creates findings in .claude/Scratchpad/RESEARCH_[topic].md

2. Review findings for stability/reusability
   └── Is this generalizable? Will it stay relevant?

3. If stable, create RAG document
   └── Move validated content to docs/rag-knowledge/

4. Ingest via MCP
   └── Use doc_type="exotic_concepts" or "research_paper"
```

### Example: Research → RAG

```python
# After /deep-research validates DTC patterns:
content = open("docs/rag-knowledge/time-crystal-patterns.md").read()

mcp__residency-scheduler__rag_ingest(
    content=content,
    doc_type="exotic_concepts",
    metadata={
        "source": "deep-research session 2026-01-16",
        "papers": [
            "https://arxiv.org/abs/...",
            "https://www.nature.com/..."
        ]
    }
)
```

---

## Maintenance Schedule

| Task | Frequency | Method |
|------|-----------|--------|
| Health check | Daily (automated) | Celery Beat |
| Content audit | Monthly | Manual review |
| Deprecated content cleanup | Quarterly | Manual |
| Re-embedding (model upgrade) | As needed | CLI script |

---

## Related Documentation

- Quick reference: `docs/guides/RAG_QUICK_REFERENCE.md`
- Full init guide: `docs/guides/RAG_INITIALIZATION_GUIDE.md`
- Ingestion patterns: `docs/rag-knowledge/rag-ingestion-patterns.md`
- Content policy: `docs/rag-knowledge/README.md`

---

*Lifecycle guide v1.0 | Created 2026-01-16*
