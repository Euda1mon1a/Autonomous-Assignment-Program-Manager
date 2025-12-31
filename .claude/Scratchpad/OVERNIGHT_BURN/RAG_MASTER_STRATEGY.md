# OVERNIGHT_BURN RAG Master Strategy

**Consolidated from:** RAG_STRATEGY_SUMMARY.md + RAG_PLANNING_README.md + RAG_INDEXING_PLAN.md
**Status:** Complete - Ready for Implementation
**Created:** 2025-12-30 | **Updated:** 2025-12-31

---

## Executive Summary

OVERNIGHT_BURN contains **208 files (4.4 MB)** of reconnaissance data across **10 critical domains**. This strategy transforms it from well-organized static documentation into an **intelligent, searchable knowledge base** accessible to AI agents and developers.

### Current State vs. Future State

**Before RAG Implementation:**
- 208 files across 10 domains, no unified access
- Manual navigation required to find patterns
- No semantic search across domains
- Agents have no structured access to knowledge

**After RAG Implementation (4 weeks):**
- Single MASTER_INDEX.md entry point
- Structured FILE_REGISTRY.json for programmatic access
- Vector database for semantic search
- Agent-integrated search tools
- 10x-100x faster pattern discovery

---

## What Is RAG?

**RAG (Retrieval Augmented Generation)** means:
1. **Retrieval:** Find relevant documents efficiently
2. **Augmented:** Enhance generation with retrieved context
3. **Generation:** AI uses retrieved docs to provide better answers

For OVERNIGHT_BURN, this means agents can:
- Find the right documentation automatically
- Understand semantic relationships between domains
- Synthesize patterns across the entire corpus
- Work autonomously without human queries

---

## The Three-Layer Implementation Strategy

### Layer 1: Master Index (Week 1 - 4 hours)

**File:** `MASTER_INDEX.md` (to create)

A single markdown file serving as the navigation hub:

```markdown
# OVERNIGHT_BURN Master Index

## By Domain
- SESSION_1_BACKEND: 11 files, Backend patterns & auth
- SESSION_2_FRONTEND: 18 files, React components & state
- ... (8 more)

## By Type
- Patterns files: [14 matching *-patterns.md]
- Reference files: [21 matching *-reference.md]
- Audit files: [9 matching *-audit.md]

## By Priority
- P0 (Index/Navigation): 8 files
- P1 (Critical): 89 files
- P2 (Supporting): 94 files
- P3 (Archive): 17 files

## Search Tips
[Quick lookup strategies]

## Cross-Domain References
[Links between domains]
```

**Impact:** Immediate navigation improvement (90% faster)
**Implementation:** Manual organization from this document

### Layer 2: Metadata Registry (Week 2 - 6 hours)

**File:** `FILE_REGISTRY.json` (to create)

Structured metadata for every file:

```json
{
  "files": [
    {
      "id": "BACKEND_001",
      "filename": "backend-service-patterns.md",
      "domain": "SESSION_1_BACKEND",
      "type": "patterns",
      "priority": "P1",
      "keywords": ["service", "patterns", "async", "error-handling"],
      "action_items": 4,
      "quality_score": 0.90,
      "related_files": ["BACKEND_002", "BACKEND_003", "SECURITY_001"],
      "last_updated": "2025-12-30"
    }
  ]
}
```

**Uses:**
- Agent filtering: "Give me all P1 patterns files"
- Programmatic queries: Load and search JSON
- Dependency tracking: Cross-references between files
- Quality ranking: Which docs are most reliable

**Implementation:**
1. Extract metadata automatically (filenames, sizes, line counts)
2. Classify by type (patterns, reference, audit, etc.)
3. Assign priority (P0-P3)
4. Add cross-references manually
5. Calculate quality scores

### Layer 3: Vector Database (Week 3 - 4 hours)

**Technology:** Chroma (free, embedded, zero infrastructure)

Semantic search across all documents:

```python
import chromadb

collection = chromadb.load_collection("overnight_burn")
results = collection.query(
    query_texts=["How do we validate ACGME compliance?"],
    n_results=10
)
# Returns: Top 10 semantically similar documents
```

**Uses:**
- Pattern discovery: "Show me similar patterns"
- Cross-domain search: "Where else is this concept used?"
- Synthesis: "Find 5 documents about this topic"

**Implementation:**
1. Install Chroma: `pip install chromadb`
2. Generate embeddings for all 208 files
3. Load into Chroma collection
4. Test semantic search queries

---

## File Categorization Framework

### Category 1: Index & Navigation (P0)

**Purpose:** Help users orient and navigate

**Examples:**
- `SESSION_*/INDEX.md` - Domain-specific navigation
- `SESSION_*/README.md` - Domain overview
- `SESSION_*/EXECUTIVE_SUMMARY.md` - High-level findings

**Metadata:**
- `type: index`
- `priority: P0` (always read first)

### Category 2: Discovery & Reconnaissance (P1)

**Purpose:** Original reconnaissance findings

**Examples:**
- `*RECONNAISSANCE_SUMMARY.md`
- `SEARCH_PARTY_*.md`
- `*INVESTIGATION_SUMMARY.md`

**Metadata:**
- `type: reconnaissance`
- `priority: P1` (read to understand analysis)

### Category 3: Patterns & Practices (P1)

**Purpose:** Code patterns, best practices, anti-patterns

**Examples:**
- `*-patterns.md`
- `*-best-practices.md`
- `*-architecture.md`

**Metadata:**
- `type: patterns`
- `priority: P1` (directly useful for development)
- `pattern_count: [number documented]`
- `code_examples: yes/no`

### Category 4: Reference & Analysis (P2)

**Purpose:** Detailed analysis, audit results, reference materials

**Examples:**
- `*-audit.md`
- `*-analysis.md`
- `*-reference.md`

**Metadata:**
- `type: reference`
- `priority: P2` (supporting documentation)

### Category 5: Quick References (P1)

**Purpose:** Quick lookup guides, checklists, matrices

**Examples:**
- `*QUICK_REFERENCE.md`
- `*-matrix.md`

**Metadata:**
- `type: quick_reference`
- `priority: P1` (frequently accessed)

### Category 6: Synthesis & Summaries (P2)

**Purpose:** Cross-domain synthesis, high-level summaries

**Examples:**
- `CROSS_SESSION_SYNTHESIS.md`
- `*COMPLETION_REPORT.md`

**Metadata:**
- `type: synthesis`
- `priority: P2` (useful for context)

### Category 7: Procedural & Guides (P2)

**Purpose:** How-to guides, procedures, instructions

**Examples:**
- `*IMPLEMENTATION_GUIDE.md`
- `*-workflow.md`
- `*QUICK_START*.md`

**Metadata:**
- `type: procedure`
- `priority: P2` (implementation guides)

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Tasks:**
1. Create MASTER_INDEX.md from template
2. Organize by domain, type, priority
3. Test navigation with it
4. Get feedback on organization

**Deliverable:** MASTER_INDEX.md (navigation hub)

### Phase 2: Metadata (Week 2)

**Tasks:**
1. Run metadata extraction scripts
2. Generate FILE_REGISTRY.json
3. Manual enhancement with cross-references
4. Create search utilities

**Deliverable:** FILE_REGISTRY.json (structured metadata)

### Phase 3: Intelligence (Week 3)

**Tasks:**
1. Set up Chroma vector DB
2. Generate embeddings for all files
3. Load into Chroma collection
4. Test semantic search

**Deliverable:** Vector DB with 208 indexed documents

### Phase 4: Integration (Week 4)

**Tasks:**
1. Update agent prompts to use search tools
2. Add search tools to agent toolkit
3. Document best practices
4. Train users/agents on usage

**Deliverable:** Integrated agent search capability

---

## Success Metrics

### Retrieval Speed

| Query | Before | After | Target |
|-------|--------|-------|--------|
| "ACGME patterns" | 10 min | 30 sec | 30 sec ✓ |
| "Security audit files" | 15 min | 20 sec | 30 sec ✓ |
| "Similar patterns" | impossible | 2 sec | 5 sec ✓ |

### Completeness

- **File coverage:** 100% (all 208 files indexed)
- **Metadata extraction:** 95%+ accuracy
- **Cross-references:** 3+ per file average
- **Action items identified:** 100%

### Agent Productivity

- **Time to find patterns:** < 5 seconds
- **Autonomous discovery:** YES
- **Human intervention needed:** Reduced 80%

---

## Quick Start: What To Do Now

### Immediate (Today)

```
[ ] Read RAG_MASTER_STRATEGY.md (this file)
[ ] Review file categorization framework
[ ] Understand 3-layer approach
```

### Week 1: Master Index

**Tasks:**
1. Create MASTER_INDEX.md using the template below
2. Organize files by domain, type, priority
3. Add cross-domain references
4. Test navigation

**Time:** ~4 hours

**Master Index Template:**

```markdown
# OVERNIGHT_BURN Master Index

## Navigation Quick Links

### By Domain (SESSION folders)
- [SESSION_1_BACKEND](SESSION_1_BACKEND/) - 11 files
- [SESSION_2_FRONTEND](SESSION_2_FRONTEND/) - 18 files
- [SESSION_3_ACGME](SESSION_3_ACGME/) - 17 files
- [SESSION_4_SECURITY](SESSION_4_SECURITY/) - 21 files
- [SESSION_5_TESTING](SESSION_5_TESTING/) - 23 files
- [SESSION_6_API_DOCS](SESSION_6_API_DOCS/) - 21 files
- [SESSION_7_RESILIENCE](SESSION_7_RESILIENCE/) - 18 files
- [SESSION_8_MCP](SESSION_8_MCP/) - 28 files
- [SESSION_9_SKILLS](SESSION_9_SKILLS/) - 26 files
- [SESSION_10_AGENTS](SESSION_10_AGENTS/) - 24 files

### By Priority

#### P0 - Start Here (Navigation Files)
- MASTER_INDEX.md (this file)
- RAG_MASTER_STRATEGY.md
- QUICK_START_RETRIEVAL.md

#### P1 - Critical Reading
- All INDEX.md files (1 per domain)
- All EXECUTIVE_SUMMARY.md files
- All *-patterns.md files

#### P2 - Reference Material
- All audit files
- All analysis files
- All synthesis documents

#### P3 - Archive / Context
- Development notes
- Meeting summaries
- Historical documents

### Search By Topic

#### ACGME Compliance
[Links to all ACGME-related files]

#### Backend Architecture
[Links to all backend pattern files]

#### Security & Authorization
[Links to all security-related files]

#### API & Integration
[Links to all API documentation]

[... continue for other major topics]
```

### Week 2: Metadata Registry

**Tasks:**
1. Run extraction scripts
2. Generate FILE_REGISTRY.json
3. Add cross-references
4. Create search tools

**Time:** ~6 hours

**Implementation Script Template:**

```python
import os
import json
from pathlib import Path

class MetadataExtractor:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.files = []

    def extract_all(self):
        """Extract metadata for all files."""
        for md_file in self.root_dir.rglob("*.md"):
            metadata = self.extract_file(md_file)
            self.files.append(metadata)
        return self.files

    def extract_file(self, filepath):
        """Extract metadata from single file."""
        with open(filepath, 'r') as f:
            content = f.read()

        return {
            "id": self._generate_id(filepath),
            "filename": filepath.name,
            "path": str(filepath.relative_to(self.root_dir)),
            "domain": self._detect_domain(filepath),
            "type": self._detect_type(filepath),
            "priority": self._assign_priority(filepath),
            "size_bytes": filepath.stat().st_size,
            "line_count": len(content.split('\n')),
            "keywords": self._extract_keywords(content),
            "action_items": self._count_action_items(content),
            "quality_score": self._calculate_quality(filepath, content),
            "last_updated": "2025-12-31"
        }

    def save_registry(self, output_file="FILE_REGISTRY.json"):
        """Save registry to JSON."""
        with open(output_file, 'w') as f:
            json.dump({"files": self.files}, f, indent=2)

# Usage
extractor = MetadataExtractor("/path/to/OVERNIGHT_BURN")
files = extractor.extract_all()
extractor.save_registry()
```

### Week 3: Vector Database

**Setup Steps:**

```bash
# 1. Install Chroma
pip install chromadb

# 2. Create indexing script
cat > index_chroma.py << 'EOF'
import chromadb
from pathlib import Path
import json

# Initialize Chroma client
client = chromadb.Client()
collection = client.create_collection("overnight_burn")

# Load all markdown files
overnight_burn = Path("./OVERNIGHT_BURN")
for md_file in overnight_burn.rglob("*.md"):
    with open(md_file, 'r') as f:
        content = f.read()

    collection.add(
        ids=[str(md_file.stem)],
        documents=[content],
        metadatas=[{
            "filename": md_file.name,
            "domain": md_file.parent.name,
            "path": str(md_file)
        }]
    )

print(f"Indexed {collection.count()} documents")
EOF

# 3. Run indexing
python index_chroma.py

# 4. Test queries
python -c "
import chromadb
client = chromadb.Client()
collection = client.get_collection('overnight_burn')
results = collection.query(
    query_texts=['ACGME compliance validation'],
    n_results=5
)
for r in results['documents'][0]:
    print(r[:100] + '...')
"
```

---

## Cross-Domain Reference Examples

### ACGME Compliance
- Core rules: SESSION_3_ACGME/acgme-work-hour-rules.md
- Supervision: SESSION_3_ACGME/acgme-supervision-ratios.md
- Implementation: SESSION_6_API_DOCS/api-docs-assignments.md
- Validation: SESSION_1_BACKEND/backend-acgme-validator.md
- Testing: SESSION_5_TESTING/test-acgme-coverage-analysis.md

### Security & Authorization
- Auth patterns: SESSION_4_SECURITY/security-auth-audit.md
- HIPAA: SESSION_4_SECURITY/security-hipaa-audit.md
- Role-based access: SESSION_4_SECURITY/rbac-matrix-detailed.md
- Frontend patterns: SESSION_2_FRONTEND/frontend-authentication.md
- API security: SESSION_6_API_DOCS/api-docs-authentication.md

### Schedule Generation
- Algorithm: SESSION_1_BACKEND/backend-scheduling-engine.md
- ACGME rules: SESSION_3_ACGME/acgme-work-hour-rules.md
- MCP tools: SESSION_8_MCP/mcp-tools-schedule.md
- API docs: SESSION_6_API_DOCS/api-docs-schedule.md
- Testing: SESSION_5_TESTING/test-scheduler-coverage-analysis.md

---

## FAQs

**Q: How long does implementation take?**
A: ~20 hours phased over 4 weeks. Can be accelerated to 1 week if needed.

**Q: Can we start with just Master Index?**
A: Yes! Layer 1 is immediately useful. Layers 2-3 add progressive value.

**Q: What if the corpus keeps growing?**
A: Process is iterative. Re-run metadata extraction quarterly.

**Q: How do agents access this?**
A: Via search tools (File Registry queries) and embedding similarity (Vector DB).

**Q: What about maintenance?**
A: Quarterly review of metadata, annual vector DB rebuild.

---

## Related Documents

- **QUICK_START_RETRIEVAL.md** - User guide for finding files now
- **METADATA_EXTRACTION_TEMPLATE.md** - Implementation code template
- **MASTER_INDEX.md** - To be created in Phase 1

---

## Next Steps

1. Read this document
2. Share RAG strategy with team
3. Week 1: Create MASTER_INDEX.md
4. Week 2: Run metadata extraction
5. Week 3: Set up Chroma
6. Week 4: Integrate with agents

---

**Status:** Complete and ready for implementation
**Effort Estimate:** 20 hours total across 4 weeks
**Expected ROI:** 10-100x faster pattern discovery
**Updated:** 2025-12-31
