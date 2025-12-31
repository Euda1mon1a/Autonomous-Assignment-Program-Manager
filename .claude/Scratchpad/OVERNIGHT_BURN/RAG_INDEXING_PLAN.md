***REMOVED*** OVERNIGHT_BURN RAG/Indexing Strategy

**Document:** RAG Indexing Plan for OVERNIGHT_BURN Reconnaissance Data
**Created:** 2025-12-30
**Scope:** 208 files, 4.4 MB across 10 domain-specific reconnaissance sessions
**Purpose:** Design retrieval augmented generation (RAG) and semantic search infrastructure for future agent access

---

***REMOVED******REMOVED*** Executive Summary

The OVERNIGHT_BURN directory contains **193 markdown files + 15 supporting documents** organized across **10 reconnaissance domains**. Current state is well-organized by domain (SESSION_1_BACKEND through SESSION_10_AGENTS) but lacks:

1. **Unified semantic indexing** - No vector embeddings for cross-domain similarity search
2. **Metadata extraction layer** - File-level metadata (priority, action items, keywords, dependencies)
3. **Master index** - Single query point to find relevant files across domains
4. **Cross-reference mapping** - Dependencies between files and domains
5. **Vector database integration** - Persistent semantic search capability

***REMOVED******REMOVED*** Current Organization

***REMOVED******REMOVED******REMOVED*** By Domain (10 Sessions)

| Session | Domain | Files | Size | Coverage |
|---------|--------|-------|------|----------|
| 1 | Backend | 11 | 0.3 MB | Patterns: auth, models, services, APIs, error handling |
| 2 | Frontend | 18 | 0.3 MB | React components, accessibility, state management |
| 3 | ACGME | 17 | 0.4 MB | Compliance rules, work hours, evaluation framework |
| 4 | Security | 21 | 0.4 MB | Auth patterns, HIPAA, validation, vulnerability audit |
| 5 | Testing | 23 | 0.4 MB | Coverage analysis, test strategies, unit/integration tests |
| 6 | API Docs | 21 | 0.4 MB | REST endpoints, schemas, authorization, data models |
| 7 | Resilience | 18 | 0.4 MB | Framework concepts, N-1/N-2, epidemiology, chaos engineering |
| 8 | MCP Tools | 28 | 0.6 MB | AI integration, database queries, 34+ tools, agent patterns |
| 9 | Skills | 26 | 0.6 MB | Agent skill specifications, capabilities, frameworks |
| 10 | Agents | 24 | 0.6 MB | Agent architectures, META_UPDATER, coordination patterns |

***REMOVED******REMOVED******REMOVED*** By File Type

- **Markdown (.md):** 193 files (92.8%) - Primary documentation
- **Text (.txt):** 13 files (6.2%) - Summaries, audit results, notes
- **Other:** CSV, LOG files - Supporting data

***REMOVED******REMOVED******REMOVED*** By File Size

- **Small (<5KB):** 11 files (5.3%) - Quick refs, index files
- **Medium (5-20KB):** 97 files (46.6%) - Analysis documents
- **Large (20-50KB):** 92 files (44.2%) - Deep-dive reports
- **XLarge (>50KB):** 8 files (3.8%) - Comprehensive references

---

***REMOVED******REMOVED*** File Categorization Framework

***REMOVED******REMOVED******REMOVED*** Category 1: Index & Navigation Files

**Purpose:** Help users orient and navigate the documentation

**Examples:**
- `SESSION_*/INDEX.md` - Domain-specific navigation
- `SESSION_*/README.md` - Domain overview
- `SESSION_*/EXECUTIVE_SUMMARY.md` - High-level findings

**Metadata:**
- `type: index`
- `serves_as: entry_point`
- `references: [list of other files in domain]`
- `priority: P0` (always read first)

***REMOVED******REMOVED******REMOVED*** Category 2: Discovery & Reconnaissance Reports

**Purpose:** Original reconnaissance findings, SEARCH_PARTY operations

**Examples:**
- `*RECONNAISSANCE_SUMMARY.md`
- `*INVESTIGATION_SUMMARY.md`
- `SEARCH_PARTY_*.md`
- `*FINAL_REPORT.md`

**Metadata:**
- `type: reconnaissance`
- `methodology: [SEARCH_PARTY lenses applied]`
- `findings_count: [number of key findings]`
- `priority: P1` (read to understand how analysis was done)

***REMOVED******REMOVED******REMOVED*** Category 3: Pattern & Practice Documents

**Purpose:** Detailed code patterns, best practices, anti-patterns

**Examples:**
- `*-patterns.md` (e.g., backend-service-patterns.md)
- `*-best-practices.md`
- `*-architecture.md`

**Metadata:**
- `type: patterns`
- `domain: [backend/frontend/security/etc]`
- `pattern_count: [number of patterns documented]`
- `code_examples: [yes/no]`
- `priority: P1` (directly useful for development)

***REMOVED******REMOVED******REMOVED*** Category 4: Reference & API Documentation

**Purpose:** Complete reference materials, API specs, architecture

**Examples:**
- `*-reference.md`
- `*-api.md`
- `QUICK_REFERENCE.md`
- `*-matrix.md`

**Metadata:**
- `type: reference`
- `domain: [which system/domain covered]`
- `completeness: [%, coverage depth]`
- `last_verified: [date]`
- `priority: P1` (used during active development)

***REMOVED******REMOVED******REMOVED*** Category 5: Enhanced Specifications

**Purpose:** Augmented capability documents with patterns, best practices

**Examples:**
- `agents-*-enhanced.md`
- `*-ENHANCEMENT_*.md`

**Metadata:**
- `type: specification`
- `enhancement_level: [foundational/comprehensive/expert]`
- `original_document: [reference]`
- `additions: [what was added]`
- `priority: P2` (reference for implementation)

***REMOVED******REMOVED******REMOVED*** Category 6: Summary & Digest Documents

**Purpose:** Condensed findings, quick summaries, TL;DR versions

**Examples:**
- `*QUICK_REFERENCE.md`
- `*SUMMARY.md`
- `*_INDEX.md` (smaller index files)
- `*.txt` summaries

**Metadata:**
- `type: summary`
- `source_documents: [what was condensed]`
- `key_points_count: [number of items highlighted]`
- `priority: P2` (quick lookup)

***REMOVED******REMOVED******REMOVED*** Category 7: Audit & Assessment Documents

**Purpose:** Security/quality audits, findings, recommendations

**Examples:**
- `*AUDIT_*.md`
- `*VALIDATION_*.md`
- `*FINDINGS_*.md`

**Metadata:**
- `type: audit`
- `audit_type: [security/quality/coverage/etc]`
- `findings_critical: [count]`
- `findings_high: [count]`
- `findings_medium: [count]`
- `priority: P1` (critical for risk management)

---

***REMOVED******REMOVED*** Master Index Structure

***REMOVED******REMOVED******REMOVED*** Option A: Single Master Index File (Recommended)

**File:** `OVERNIGHT_BURN/MASTER_INDEX.md` (to be created)

**Structure:**

```markdown
***REMOVED*** OVERNIGHT_BURN Master Index

***REMOVED******REMOVED*** Quick Navigation
- By domain (SESSION_1 → SESSION_10)
- By file type (patterns, references, audits, etc.)
- By priority (P0 → P3)
- By search term (keyword index)

***REMOVED******REMOVED*** Domain Summaries
[For each domain: files, key findings, action items]

***REMOVED******REMOVED*** Cross-Domain References
- Backend ↔ Frontend integration patterns
- Security implications for each domain
- Testing strategy for each domain

***REMOVED******REMOVED*** File Registry (Alphabetical)
- Complete file list with metadata
- One-line description
- Priority, type, domain tags

***REMOVED******REMOVED*** Search Strategies
- How to find files by pattern
- How to find files by use case
- How to find files by technology
```

***REMOVED******REMOVED******REMOVED*** Option B: JSON Metadata Registry (For Vector DB Integration)

**File:** `OVERNIGHT_BURN/FILE_REGISTRY.json` (to be created)

```json
{
  "metadata": {
    "total_files": 208,
    "total_size_mb": 4.4,
    "generated_at": "2025-12-30",
    "version": "1.0"
  },
  "files": [
    {
      "id": "BACKEND_001",
      "path": "SESSION_1_BACKEND/backend-service-patterns.md",
      "filename": "backend-service-patterns.md",
      "domain": "SESSION_1_BACKEND",
      "type": "patterns",
      "title": "Backend Service Layer Architecture Patterns Analysis",
      "size_kb": 45,
      "priority": "P1",
      "keywords": ["service", "architecture", "patterns", "async", "N+1-optimization"],
      "summary": "Analyzes 47 service classes with focus on error handling and async patterns",
      "key_findings": 7,
      "contains_code_examples": true,
      "related_files": ["BACKEND_002", "BACKEND_003"],
      "action_items": ["Implement structured logging in critical paths", "Consolidate error handling"],
      "last_reviewed": "2025-12-30"
    },
    // ... 207 more files
  ],
  "domains": {
    "SESSION_1_BACKEND": {
      "description": "Backend patterns and architecture",
      "file_count": 11,
      "key_files": ["BACKEND_AUTH_SUMMARY.md", "backend-service-patterns.md"],
      "action_items": ["Add structured logging", "Reduce N+1 queries"]
    }
    // ... more domains
  }
}
```

---

***REMOVED******REMOVED*** Metadata Extraction Strategy

***REMOVED******REMOVED******REMOVED*** Phase 1: Automated Extraction (Python Script)

Create `/tmp/extract_metadata.py` to process all files:

```python
def extract_metadata(file_path: Path) -> dict:
    """Extract metadata from markdown file."""
    with open(file_path) as f:
        content = f.read()

    metadata = {
        "filename": file_path.name,
        "path": str(file_path.relative_to(burn_dir)),
        "domain": extract_domain(file_path),
        "type": classify_file_type(file_path.name, content),
        "title": extract_title(content),
        "size_kb": file_path.stat().st_size / 1024,
        "priority": classify_priority(content),
        "keywords": extract_keywords(content),
        "summary": extract_summary(content),
        "key_findings": count_findings(content),
        "action_items": extract_action_items(content),
        "code_examples": count_code_blocks(content),
        "headers": extract_headers(content),
    }
    return metadata
```

**Extraction rules:**

1. **Title:** First H1 header (`***REMOVED*** `)
2. **Type:** Based on filename and content:
   - Contains INDEX/README → `index`
   - Contains SUMMARY/QUICK_REFERENCE → `summary`
   - Contains AUDIT/VALIDATION → `audit`
   - Contains PATTERNS → `patterns`
   - Contains SEARCH_PARTY/RECONNAISSANCE → `reconnaissance`
   - Contains enhanced/specification → `specification`
   - Default → `reference`
3. **Priority:**
   - INDEX/SUMMARY files → P0
   - Contains critical findings/action items → P1
   - Detailed analysis → P1
   - Supporting documents → P2
   - Archive/reference → P3
4. **Keywords:** Extract from:
   - Headers (H2/H3)
   - Bullet lists
   - Code block languages
   - ACGME/Security/Testing terms
5. **Action Items:** Extract lines matching:
   - `- [ ]` (unchecked checkboxes)
   - Lines containing "TODO", "MUST", "SHOULD", "IMPLEMENT"
6. **Code Examples:** Count code blocks by language

***REMOVED******REMOVED******REMOVED*** Phase 2: Manual Enhancement

For each domain:

1. Add domain-specific metadata
2. Identify critical cross-references
3. Tag high-priority findings
4. Map dependencies between files

---

***REMOVED******REMOVED*** Vector Database Candidates

***REMOVED******REMOVED******REMOVED*** Option 1: Pinecone (Cloud-Based)

**Pros:**
- Fully managed, no infrastructure
- Metadata filtering built-in
- 12.5M vectors @ $70/month (pay-as-you-go)
- Python SDK: `pip install pinecone-client`

**Cons:**
- Vendor lock-in
- Monthly cost even if unused
- Network latency

**Setup:**
```python
import pinecone

***REMOVED*** Initialize
pinecone.init(api_key="YOUR_KEY", environment="us-west-2")

***REMOVED*** Create index
pinecone.create_index("overnight-burn", dimension=1536)

***REMOVED*** Upload vectors with metadata
index = pinecone.Index("overnight-burn")
index.upsert([
    {
        "id": "BACKEND_001",
        "values": embedding_vector,
        "metadata": {
            "domain": "SESSION_1_BACKEND",
            "type": "patterns",
            "priority": "P1"
        }
    }
])

***REMOVED*** Query
results = index.query(embedding_vector, top_k=10, filter={"priority": "P1"})
```

***REMOVED******REMOVED******REMOVED*** Option 2: Weaviate (Self-Hosted or Cloud)

**Pros:**
- Open-source, can self-host
- GraphQL API
- Built-in semantic search
- Good for enterprise deployments

**Cons:**
- More complex setup
- Requires deployment infrastructure
- Higher learning curve

**Setup:**
```python
import weaviate

client = weaviate.Client("http://localhost:8080")

***REMOVED*** Create class
client.schema.create_class({
    "class": "OvernightBurnDocument",
    "properties": [
        {"name": "domain", "dataType": ["string"]},
        {"name": "type", "dataType": ["string"]},
        {"name": "priority", "dataType": ["string"]},
    ]
})

***REMOVED*** Add documents
client.data_object.create({
    "text": document_content,
    "domain": "SESSION_1_BACKEND",
    "type": "patterns",
    "priority": "P1"
}, "OvernightBurnDocument")

***REMOVED*** Search
results = client.query.get("OvernightBurnDocument").with_near_text({
    "concepts": ["service layer patterns"]
}).do()
```

***REMOVED******REMOVED******REMOVED*** Option 3: Chroma (Local/Embedded)

**Pros:**
- Lightweight, embeds in Python
- Zero infrastructure
- Free and open-source
- Perfect for local development

**Cons:**
- Limited to single machine
- Not suitable for large-scale deployments
- Memory-bound

**Setup:**
```python
import chromadb

***REMOVED*** Create client
client = chromadb.Client()

***REMOVED*** Create collection
collection = client.create_collection(name="overnight_burn")

***REMOVED*** Add documents
collection.add(
    ids=["BACKEND_001"],
    documents=["backend service patterns..."],
    metadatas=[{"domain": "SESSION_1_BACKEND", "type": "patterns"}]
)

***REMOVED*** Search
results = collection.query(
    query_texts=["service layer patterns"],
    n_results=10
)
```

***REMOVED******REMOVED******REMOVED*** Option 4: Milvus (Distributed, Open-Source)

**Pros:**
- Highly scalable (distributed)
- Open-source
- High performance
- Good for large indexes

**Cons:**
- Complex deployment
- Infrastructure overhead
- Steeper learning curve

**Recommendation:** **Start with Option 3 (Chroma)** for local development, migrate to **Option 1 (Pinecone)** if cloud integration needed later.

---

***REMOVED******REMOVED*** Implementation Roadmap

***REMOVED******REMOVED******REMOVED*** Phase 1: Master Index (Week 1)

1. Create `OVERNIGHT_BURN/MASTER_INDEX.md`
   - Domain summaries
   - File registry
   - Search strategies

2. Create `OVERNIGHT_BURN/FILE_REGISTRY.json`
   - Automated metadata extraction
   - Manual enhancement

3. Document search patterns
   - By domain
   - By type
   - By priority
   - By keyword

***REMOVED******REMOVED******REMOVED*** Phase 2: Vector Database (Week 2)

1. Set up Chroma locally
   - Embed document content
   - Index with metadata
   - Test retrieval

2. Create search utilities
   ```python
   def find_patterns(keyword: str, domain: str = None) -> List[str]:
       """Find pattern files by keyword and optional domain."""
       ***REMOVED*** Query vector DB
       ***REMOVED*** Filter by metadata
       ***REMOVED*** Rank by relevance

   def find_related(file_id: str) -> List[str]:
       """Find related files (cross-references)."""
       ***REMOVED*** Query by semantic similarity
       ***REMOVED*** Boost same-domain results
   ```

3. Test with sample queries
   - "How do we handle N+1 queries?"
   - "What are the HIPAA requirements?"
   - "Show me async patterns"

***REMOVED******REMOVED******REMOVED*** Phase 3: Integration with Future Sessions (Week 3)

1. Update agent prompts to reference master index
   ```
   "Before implementing, search OVERNIGHT_BURN master index for related patterns:
    - Use MASTER_INDEX.md for quick navigation
    - Use FILE_REGISTRY.json for detailed metadata
    - Query vector DB for semantic similarity"
   ```

2. Create retrieval tools for agents
   ```python
   @ai_tool
   def search_overnight_burn(query: str) -> List[RelevantFile]:
       """Search OVERNIGHT_BURN for relevant documentation."""
   ```

3. Document best practices
   - When to use master index vs. vector DB
   - How to interpret search results
   - How to add new reconnaissance data

---

***REMOVED******REMOVED*** Search & Retrieval Patterns

***REMOVED******REMOVED******REMOVED*** Pattern 1: Domain-Specific Search

**Use Case:** "I'm implementing backend service patterns. Show me all relevant docs."

```python
results = search_by_domain(domain="SESSION_1_BACKEND", types=["patterns", "reference"])
***REMOVED*** Returns: All pattern files, sorted by priority
```

***REMOVED******REMOVED******REMOVED*** Pattern 2: Cross-Domain Search

**Use Case:** "Where are security implications for backend services?"

```python
results = search_by_keyword(
    keywords=["security", "backend"],
    logic="AND"  ***REMOVED*** Must mention both
)
***REMOVED*** Returns: Files mentioning both security and backend concepts
```

***REMOVED******REMOVED******REMOVED*** Pattern 3: Action-Item Search

**Use Case:** "What needs to be fixed or implemented?"

```python
results = search_by_action_items()
***REMOVED*** Returns: Files with TODO/MUST/SHOULD, sorted by priority
```

***REMOVED******REMOVED******REMOVED*** Pattern 4: Semantic Similarity Search

**Use Case:** "I found a pattern. Are there similar patterns elsewhere?"

```python
results = semantic_search(
    query_text="How do we validate ACGME compliance?",
    top_k=10
)
***REMOVED*** Returns: Most semantically similar documents
```

***REMOVED******REMOVED******REMOVED*** Pattern 5: Dependency-Based Search

**Use Case:** "What files depend on this one?"

```python
results = find_related_files(file_id="BACKEND_001")
***REMOVED*** Returns: Files that reference or depend on BACKEND_001
```

---

***REMOVED******REMOVED*** Metadata Schema

***REMOVED******REMOVED******REMOVED*** File-Level Metadata

```yaml
file_metadata:
  id: "DOMAIN_NNN"  ***REMOVED*** e.g., BACKEND_001
  path: "SESSION_X/filename.md"
  filename: "string"
  domain: "SESSION_N_*"
  type: "index|summary|patterns|reference|reconnaissance|specification|audit"
  title: "Full title from H1"
  size_kb: float
  priority: "P0|P1|P2|P3"
  keywords: ["keyword1", "keyword2"]
  summary: "1-3 sentence description"
  key_findings: integer
  action_items: ["item1", "item2"]
  code_examples: integer
  contains_code_examples: boolean
  related_files: ["FILE_ID1", "FILE_ID2"]
  cross_references:
    - domain: "SESSION_X"
      reason: "discusses related patterns"
  created_at: "2025-12-30"
  last_reviewed: "2025-12-30"
  vector_embedding: [float_array]  ***REMOVED*** For vector DB
```

***REMOVED******REMOVED******REMOVED*** Domain-Level Metadata

```yaml
domain_metadata:
  name: "SESSION_1_BACKEND"
  description: "Backend patterns and architecture analysis"
  file_count: integer
  total_size_kb: float
  focus_areas: ["patterns", "architecture", "error-handling"]
  key_files: ["file1.md", "file2.md"]
  key_findings_summary: "string"
  critical_action_items: ["item1"]
  dependencies:
    - domain: "SESSION_4_SECURITY"
      reason: "auth patterns"
  created_at: "2025-12-30"
  status: "complete|in-progress|archived"
```

---

***REMOVED******REMOVED*** Search Query Examples

***REMOVED******REMOVED******REMOVED*** Example 1: New Backend Developer

**Query:** "Show me backend service patterns"

```
1. MASTER_INDEX.md → SESSION_1_BACKEND section
2. Retrieve: backend-service-patterns.md
3. Then: backend-repository-patterns.md, backend-auth-patterns.md
4. Vector search: Similar architectural patterns from other domains
5. Action items: Things to implement/fix in services
```

***REMOVED******REMOVED******REMOVED*** Example 2: Security Audit

**Query:** "What are HIPAA and security requirements?"

```
1. MASTER_INDEX.md → Search for HIPAA, security keywords
2. Retrieve: SESSION_4_SECURITY files
3. Cross-reference: SESSION_1_BACKEND, SESSION_6_API_DOCS
4. Vector search: "HIPAA compliance", "data protection"
5. Find: All related files across domains
```

***REMOVED******REMOVED******REMOVED*** Example 3: Testing Implementation

**Query:** "What patterns exist for testing async code?"

```
1. FILE_REGISTRY.json → Filter type=patterns, domain=SESSION_5
2. Vector search: "async testing", "pytest patterns"
3. Find: async test examples, fixtures
4. Cross-reference: Backend services, frontend tests
5. Action items: Testing gaps to address
```

***REMOVED******REMOVED******REMOVED*** Example 4: Implementation Planning

**Query:** "I need to implement schedule generation. What do I need to know?"

```
1. MASTER_INDEX.md → Search for "scheduling"
2. Retrieve: SESSION_3_ACGME (compliance), SESSION_7_RESILIENCE (fault tolerance)
3. Vector search: "schedule generation", "constraint solving"
4. Find: All related patterns, references, best practices
5. Build: Implementation checklist from action items
```

---

***REMOVED******REMOVED*** Implementation Tools & Scripts

***REMOVED******REMOVED******REMOVED*** Script 1: Metadata Extraction (Python)

Location: `/tmp/extract_metadata_comprehensive.py`

```python
***REMOVED***!/usr/bin/env python3
"""Extract comprehensive metadata from OVERNIGHT_BURN files."""

import json
import re
from pathlib import Path
from typing import Dict, List

def extract_metadata(file_path: Path) -> Dict:
    """Extract metadata from a single file."""
    with open(file_path, encoding='utf-8') as f:
        content = f.read()

    ***REMOVED*** Extract title (first H1)
    title_match = re.search(r'^***REMOVED*** (.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else file_path.stem

    ***REMOVED*** Extract headers for keyword extraction
    headers = re.findall(r'^***REMOVED***{2,3} (.+)$', content, re.MULTILINE)

    ***REMOVED*** Count code blocks
    code_blocks = re.findall(r'```(\w*)', content)

    ***REMOVED*** Extract action items
    action_items = re.findall(
        r'^[-*] \[ \]\s+(.+)$|TODO|MUST|SHOULD',
        content,
        re.MULTILINE
    )

    ***REMOVED*** Extract key findings
    findings = re.findall(r'^***REMOVED******REMOVED***+ .*Finding', content, re.IGNORECASE)

    return {
        "filename": file_path.name,
        "path": str(file_path),
        "title": title,
        "size_kb": file_path.stat().st_size / 1024,
        "headers": headers,
        "code_block_count": len(code_blocks),
        "code_languages": list(set(code_blocks)),
        "action_items": action_items,
        "findings_count": len(findings),
    }
```

***REMOVED******REMOVED******REMOVED*** Script 2: Master Index Generator

Location: `/tmp/generate_master_index.py`

```python
***REMOVED***!/usr/bin/env python3
"""Generate MASTER_INDEX.md from extracted metadata."""

import json
from pathlib import Path

def generate_master_index(metadata_registry: Dict) -> str:
    """Generate markdown master index."""

    index = "***REMOVED*** OVERNIGHT_BURN Master Index\n\n"

    ***REMOVED*** Group by domain
    by_domain = {}
    for file_meta in metadata_registry['files']:
        domain = file_meta['domain']
        if domain not in by_domain:
            by_domain[domain] = []
        by_domain[domain].append(file_meta)

    ***REMOVED*** Generate domain sections
    for domain in sorted(by_domain.keys()):
        files = by_domain[domain]
        index += f"***REMOVED******REMOVED*** {domain}\n\n"
        index += f"**Files:** {len(files)}\n\n"

        ***REMOVED*** Highest priority files first
        priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        sorted_files = sorted(
            files,
            key=lambda f: priority_order.get(f['priority'], 99)
        )

        for f in sorted_files:
            index += f"- **{f['filename']}** ({f['type']})\n"
            index += f"  {f['summary']}\n\n"

    return index
```

***REMOVED******REMOVED******REMOVED*** Script 3: Vector DB Loader

Location: `/tmp/load_to_vectordb.py`

```python
***REMOVED***!/usr/bin/env python3
"""Load documents into vector database (Chroma)."""

import chromadb
import openai
from pathlib import Path

def load_documents_to_vectordb(metadata_registry: Dict):
    """Load all documents into Chroma."""

    client = chromadb.Client()
    collection = client.create_collection("overnight_burn")

    for file_meta in metadata_registry['files']:
        file_path = Path(file_meta['path'])

        ***REMOVED*** Read document content
        with open(file_path) as f:
            content = f.read()

        ***REMOVED*** Generate embedding (using OpenAI API)
        response = openai.Embedding.create(
            input=content,
            model="text-embedding-ada-002"
        )
        embedding = response['data'][0]['embedding']

        ***REMOVED*** Add to collection
        collection.add(
            ids=[file_meta['id']],
            documents=[content],
            embeddings=[embedding],
            metadatas=[{
                "domain": file_meta['domain'],
                "type": file_meta['type'],
                "priority": file_meta['priority'],
                "keywords": ",".join(file_meta['keywords']),
            }]
        )
```

---

***REMOVED******REMOVED*** Retrieval Workflow for Agents

***REMOVED******REMOVED******REMOVED*** Workflow 1: Fast Lookup (Synchronous)

```
User Query
  ↓
MASTER_INDEX.md lookup (by keyword)
  ↓
FILE_REGISTRY.json filtered search (by metadata)
  ↓
Return top 5 files
  ↓
Agent reads files and implements
```

**Speed:** < 1 second
**Best for:** Quick reference during coding

***REMOVED******REMOVED******REMOVED*** Workflow 2: Semantic Search (Async)

```
User Query
  ↓
Vectorize query (OpenAI API)
  ↓
Query Chroma vector DB (semantic similarity)
  ↓
Rank results by metadata filters
  ↓
Return top 10 semantically similar documents
  ↓
Agent synthesizes patterns across files
```

**Speed:** 2-5 seconds
**Best for:** Finding related patterns, best practices

***REMOVED******REMOVED******REMOVED*** Workflow 3: Comprehensive Analysis (Hybrid)

```
User Query
  ↓
Execute both Fast Lookup + Semantic Search in parallel
  ↓
Merge results (deduplicate, rank by priority + relevance)
  ↓
Return ranked list with explanations
  ↓
Agent gets comprehensive view
```

**Speed:** 2-5 seconds
**Best for:** Complex questions requiring cross-domain knowledge

---

***REMOVED******REMOVED*** Maintenance & Updates

***REMOVED******REMOVED******REMOVED*** Quarterly Review Schedule

**Q1 (Jan-Mar):** Backend & Frontend reviews
- Review SESSION_1, SESSION_2, SESSION_4 files
- Update with new patterns from recent code
- Archive outdated findings

**Q2 (Apr-Jun):** ACGME & Testing reviews
- Review SESSION_3, SESSION_5 files
- Update compliance rules if changed
- Update test strategies

**Q3 (Jul-Sep):** Security & API reviews
- Review SESSION_4, SESSION_6 files
- Security audit findings
- API deprecation/changes

**Q4 (Oct-Dec):** Resilience & Agent reviews
- Review SESSION_7, SESSION_8, SESSION_9, SESSION_10
- Update framework documentation
- Archive obsolete agent specs

***REMOVED******REMOVED******REMOVED*** When Adding New Reconnaissance Data

1. Create new SESSION_N folder with clear domain name
2. Extract metadata (run extraction script)
3. Add to FILE_REGISTRY.json
4. Update MASTER_INDEX.md
5. Re-index vector DB with new documents
6. Document cross-references to existing sessions

---

***REMOVED******REMOVED*** Success Metrics

***REMOVED******REMOVED******REMOVED*** Retrieval Effectiveness

- **Precision:** % of retrieved documents actually relevant to query
- **Recall:** % of all relevant documents retrieved
- **Target:** Precision > 80%, Recall > 70%

***REMOVED******REMOVED******REMOVED*** Agent Productivity

- **Time to find patterns:** < 5 seconds
- **Files read before implementing:** < 10
- **Implementation time:** Reduced by pattern awareness
- **Rework due to missed patterns:** < 5%

***REMOVED******REMOVED******REMOVED*** Index Quality

- **Metadata completeness:** 100% of files have extracted metadata
- **Cross-references:** Average 3+ related files per document
- **Action item clarity:** All action items are specific and actionable
- **Update frequency:** Quarterly reviews completed

---

***REMOVED******REMOVED*** Conclusion

This RAG/indexing strategy transforms OVERNIGHT_BURN from a well-organized but isolated documentation library into an intelligent, queryable knowledge base.

**Key components:**

1. **Master Index** - Quick navigation and orientation
2. **File Registry JSON** - Structured metadata for filtering
3. **Vector Database** - Semantic similarity search
4. **Search Utilities** - Agent-friendly query tools
5. **Maintenance Schedule** - Keeps index fresh and relevant

**Implementation order:**

1. Create Master Index (1 day)
2. Extract and enhance metadata (2 days)
3. Set up vector DB locally (1 day)
4. Build search utilities (1 day)
5. Integrate with agent workflows (2 days)

**Total effort:** ~1 week of focused work

This positions future sessions to leverage OVERNIGHT_BURN as a high-velocity knowledge base rather than static documentation.
