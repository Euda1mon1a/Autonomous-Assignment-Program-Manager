# Vector Database Integration Proposal

> **Status:** Proposal
> **Created:** 2025-12-28
> **Author:** Claude (AI Assistant)
> **Stakeholders:** Development Team, Program Directors, IT Operations

---

## Executive Summary

This proposal evaluates vector database integration opportunities for the Residency Scheduler. After comprehensive analysis of six use cases, we recommend a **phased implementation using pgvector** (PostgreSQL extension) as the primary vector store, with **sentence-transformers** for local embedding generation.

### Key Findings

| Use Case | Impact | Effort | Priority |
|----------|--------|--------|----------|
| Documentation RAG | High | Low | **P0 - Start Here** |
| Swap Matching Enhancement | High | Medium | P1 |
| Semantic Search API | Medium | Medium | P1 |
| Schedule Similarity & Anomaly Detection | Medium | Medium | P2 |
| MCP Tool Context Augmentation | Medium | Low | P2 |
| Burnout Contagion Modeling | Very High | High | P3 (Research) |

### Estimated Investment

- **Infrastructure:** $0 additional (uses existing PostgreSQL)
- **Storage:** ~50-100 MB for full vector corpus
- **Latency:** +5-20ms per semantic query
- **Development:** 8-12 weeks for full implementation

---

## Table of Contents

1. [Infrastructure Recommendation](#1-infrastructure-recommendation)
2. [Use Case 1: Documentation RAG](#2-use-case-1-documentation-rag)
3. [Use Case 2: Swap Matching Enhancement](#3-use-case-2-swap-matching-enhancement)
4. [Use Case 3: Semantic Search API](#4-use-case-3-semantic-search-api)
5. [Use Case 4: Schedule Similarity & Anomaly Detection](#5-use-case-4-schedule-similarity--anomaly-detection)
6. [Use Case 5: MCP Tool Context Augmentation](#6-use-case-5-mcp-tool-context-augmentation)
7. [Use Case 6: Burnout Contagion Modeling](#7-use-case-6-burnout-contagion-modeling)
8. [Implementation Roadmap](#8-implementation-roadmap)
9. [Success Metrics](#9-success-metrics)
10. [Risk Mitigation](#10-risk-mitigation)
11. [Appendix: Code Snippets](#11-appendix-code-snippets)

---

## 1. Infrastructure Recommendation

### Primary Choice: pgvector

**Rationale:**
1. **Zero new infrastructure** - Uses existing PostgreSQL 15
2. **ACID compliance** - Critical for medical/military data (PERSEC/OPSEC)
3. **Unified data model** - Embeddings and metadata in same database
4. **Security alignment** - Data stays in controlled environment (HIPAA-ready)
5. **Familiar tooling** - SQL queries, Alembic migrations, existing backups

### Comparison Matrix

| Criteria | **pgvector** | Qdrant | Pinecone | Weaviate |
|----------|-------------|--------|----------|----------|
| Deployment | In-database | Container | Cloud SaaS | Container |
| Setup | 1 SQL command | Docker | API key | Docker |
| ACID | ✅ Yes | ❌ No | ❌ No | ❌ No |
| Latency | 5-10ms | 2-5ms | 10-20ms | 5-15ms |
| Cost | $0 (existing) | Infrastructure | $$$/vector | Infrastructure |
| HIPAA Ready | ✅ Yes | ⚠️ Self-host | ❌ Cloud | ⚠️ Self-host |

### Embedding Model Choice: sentence-transformers

**Model:** `all-MiniLM-L6-v2` (384 dimensions)

- **Size:** 44MB (fits in memory)
- **Speed:** ~10ms per embedding on CPU
- **Quality:** Excellent for general text, good for medical terminology
- **Privacy:** Runs locally, no external API calls

**Alternative for medical domain:** `BioBERT` or `PubMedBERT` (if specialized accuracy needed)

### Docker-Compose Addition

```yaml
# No new services required - just enable pgvector in PostgreSQL
db:
  image: postgres:15-alpine
  environment:
    POSTGRES_EXTENSIONS: vector
  volumes:
    - ./backend/docker/init-pgvector.sql:/docker-entrypoint-initdb.d/01-pgvector.sql
```

### Backend Dependencies

```txt
# Add to requirements.txt
pgvector==0.3.4
sentence-transformers==3.0.1
```

---

## 2. Use Case 1: Documentation RAG

### Problem Statement

The system has **175,600+ lines of documentation** across 407 markdown files covering:
- API endpoints (15+ files)
- Architecture patterns (48+ files)
- Cross-disciplinary resilience theory
- ACGME compliance rules
- Operational guides

**Current limitation:** Keyword search only. Users can't ask *"How do I handle a resident approaching 80 hours?"* and get relevant guidance.

### Solution: Semantic Documentation Search

Embed all documentation chunks and enable natural language queries via:
1. REST API endpoint (`/docs/search`)
2. MCP tool for Claude agents (`search_documentation`)

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  User Query: "How do I handle ACGME violations?"           │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Embedding Service                                          │
│  └── sentence-transformers → 384-dim query vector          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  pgvector Similarity Search                                 │
│  SELECT * FROM doc_chunks                                   │
│  ORDER BY embedding <=> query_embedding                     │
│  LIMIT 5                                                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Results with semantic context                              │
│  - ACGME compliance documentation                           │
│  - Constraint violation handling                            │
│  - Related fix guidance                                     │
└─────────────────────────────────────────────────────────────┘
```

### Schema Design

```python
class DocumentationChunk(Base):
    """Stores documentation chunks with embeddings."""
    __tablename__ = "doc_chunks"

    id = Column(String(36), primary_key=True)
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), unique=True)
    source_file = Column(String(512), nullable=False)
    section_title = Column(String(256))
    chunk_type = Column(String(50))  # text, code, table
    domains = Column(ARRAY(String))  # ['api', 'acgme', 'resilience']
    is_regulatory = Column(Boolean, default=False)
    embedding = Column(Vector(384), nullable=False)

    __table_args__ = (
        Index("idx_doc_chunks_embedding", "embedding",
              postgresql_using="ivfflat"),
    )
```

### Chunking Strategy

```python
class DocumentationChunker:
    def __init__(self, chunk_size_tokens: int = 800, overlap_tokens: int = 200):
        self.tokenizer = tiktoken.encoding_for_model("gpt-4")
        self.chunk_size = chunk_size_tokens
        self.overlap = overlap_tokens

    def chunk_document(self, doc: DocumentMetadata) -> list[DocumentChunk]:
        """
        Content-aware chunking:
        1. Parse markdown into heading-based sections
        2. Preserve code blocks as atomic units
        3. Split text by token boundaries with overlap
        4. Tag with domain metadata
        """
        chunks = []
        sections = self._parse_sections(doc.content)

        for section in sections:
            if section["type"] == "code":
                # Preserve code blocks intact
                chunks.append(self._create_chunk(
                    content=section["content"],
                    metadata={"type": "code_example", "section": section["title"]}
                ))
            else:
                # Split text with overlap
                for text_chunk in self._split_by_tokens(section["content"]):
                    chunks.append(self._create_chunk(
                        content=text_chunk,
                        metadata={"type": "text", "section": section["title"]}
                    ))

        return chunks
```

### Storage Estimates

| Component | Size |
|-----------|------|
| 1,500 chunks × 384 dims × 4 bytes | 2.3 MB |
| Text content (~1.5 KB/chunk) | 2.25 MB |
| Indices (IVFFlat) | ~20 MB |
| **Total** | **~25 MB** |

### MCP Tool Integration

```python
@mcp_tool(name="search_documentation")
async def search_docs(
    query: str,
    limit: int = 5,
    domain_filter: str | None = None,
) -> ToolResult:
    """
    Search documentation for guidance on a topic.

    Examples:
        - "How do I debug a constraint violation?"
        - "What's the API endpoint for assignments?"
        - "Explain the 80-hour rule"
    """
    results = await search_service.search(
        query=query,
        limit=limit,
        filter_domains=domain_filter.split(",") if domain_filter else None,
    )

    return ToolResult(content=[{
        "type": "text",
        "text": format_search_results(results)
    }])
```

---

## 3. Use Case 2: Swap Matching Enhancement

### Problem Statement

Current `SwapAutoMatcher` uses **explicit rule-based scoring** across 5 factors:
- Date proximity (20%)
- Preference alignment (35%)
- Workload balance (15%)
- History score (15%)
- Availability (15%)

**Limitation:** Cannot learn implicit patterns from historical swap success/failure.

### Solution: Hybrid Scoring (Explicit + Semantic)

Add semantic similarity layer that learns from:
1. Swap request patterns (what do successful swaps look like?)
2. Faculty behavioral profiles (who accepts what?)
3. Pair compatibility (which faculty combinations work well?)

### Feature Vector Design

#### Request Context Embedding (7D)

```python
class SwapRequestEmbedding:
    """7-dimensional embedding for swap request context."""

    # Temporal (1D)
    temporal_urgency: float      # 0=far future, 1=imminent

    # Burden (2D)
    burden_intensity: float      # 0=minimal, 1=extreme
    burden_trend: float          # -1=avoiding, 0=neutral, 1=seeking

    # Preference (2D)
    preference_strength: float   # 0=no preference, 1=strong
    preference_stability: float  # 0=volatile, 1=consistent

    # Pattern (2D)
    swap_frequency: float        # 0=never, 1=always swapping
    acceptance_likelihood: float # P(acceptance) from history
```

#### Faculty Profile Embedding (10D)

```python
class FacultyProfileEmbedding:
    """10-dimensional embedding of faculty swap behavior."""

    # Behavioral role (3D: orthogonal encoding)
    role_stabilizer_axis: float   # -1=martyr, 0=neutral, 1=stabilizer
    role_engagement_axis: float   # -1=isolate, 0=neutral, 1=power_broker
    role_fairness_axis: float     # -1=evader, 0=neutral, 1=balanced

    # Responsiveness (2D)
    response_speed: float         # Median hours to respond
    response_consistency: float   # Std dev of response times

    # Partnership (3D)
    reciprocity_score: float      # Mutual vs one-way swaps
    partner_loyalty: float        # Concentration with few partners
    conflict_avoidance: float     # Accepts low-compatibility requests

    # Capacity (2D)
    capacity_utilization: float   # Current % of ideal swaps
    capacity_trend: float         # +1=taking more, -1=reducing
```

### Hybrid Scoring Integration

```python
def score_swap_compatibility_hybrid(
    self,
    request_a: SwapRecord,
    request_b: SwapRecord,
) -> dict:
    """Hybrid scoring combining explicit rules + semantic similarity."""

    # Phase 1: Explicit scoring (current system)
    explicit_score = self._score_explicitly(request_a, request_b)

    # Phase 2: Semantic scoring via embeddings
    req_emb_a = self._embed_request(request_a)
    req_emb_b = self._embed_request(request_b)
    fac_emb_a = self._embed_faculty(request_a.source_faculty_id)
    fac_emb_b = self._embed_faculty(request_b.source_faculty_id)
    pair_emb = self._embed_pair(request_a.source_faculty_id, request_b.source_faculty_id)

    semantic_score = calculate_compatibility(
        req_emb_a, req_emb_b, fac_emb_a, fac_emb_b, pair_emb
    )

    # Phase 3: Adaptive weighting based on agreement
    agreement = correlation(explicit_score, semantic_score)

    if agreement > 0.8:
        weight_explicit, weight_semantic = 0.6, 0.4
        confidence = 'high'
    elif agreement > 0.5:
        weight_explicit, weight_semantic = 0.75, 0.25
        confidence = 'medium'
    else:
        weight_explicit, weight_semantic = 0.9, 0.1
        confidence = 'low'  # Flag for human review

    hybrid_score = (explicit_score * weight_explicit) + (semantic_score * weight_semantic)

    return {
        'explicit_score': explicit_score,
        'semantic_score': semantic_score,
        'hybrid_score': hybrid_score,
        'confidence': confidence
    }
```

### Success Prediction Model

```python
class SwapSuccessPredictor:
    """Predicts P(swap accepted AND executed)."""

    def __init__(self):
        self.model = LogisticRegression(max_iter=1000)
        self.scaler = StandardScaler()

    def train(self, db_session):
        """Train on historical swap outcomes."""
        X, y = self._prepare_training_data(db_session)
        self.model.fit(X, y)

    def predict_success_probability(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord
    ) -> float:
        """P(success | these two requests matched)."""
        features = np.concatenate([
            self._embed_request(request_a),  # 7D
            self._embed_request(request_b),  # 7D
            self._embed_faculty(request_a.source_faculty_id),  # 10D
            self._embed_faculty(request_b.source_faculty_id),  # 10D
        ])

        return float(self.model.predict_proba(features.reshape(1, -1))[0, 1])
```

### Data Requirements

- **Minimum:** 100 historical swaps, 6 months of data
- **Target distribution:** ~30% executed, ~40% rejected, ~20% pending

---

## 4. Use Case 3: Semantic Search API

### Problem Statement

Current search uses PostgreSQL ILIKE + Redis inverted index with fuzzy matching (Levenshtein, Soundex, N-gram). Works for exact/fuzzy keywords but fails for:

- Semantic synonyms: "call" vs "night duty" vs "coverage"
- Medical terminology: "knee arthroscopy" vs "arthroscopic knee surgery"
- Abbreviation understanding: "FMIT" vs "family medicine inpatient training"

### Solution: Hybrid Search Layer

Add semantic search that combines:
1. **Keyword layer (BM25):** Fast, exact matches
2. **Semantic layer (vector):** Conceptual similarity
3. **Reranking layer:** Weighted combination

### Entity-Specific Benefits

| Entity | Semantic Value | Example |
|--------|---------------|---------|
| **Procedure** | Critical | "knee arthroscopy" → "arthroscopic knee surgery" |
| **Rotation** | High | "inpatient teaching" → "FMIT" |
| **Person** | High | Find by expertise, not just name |
| **Assignment** | Medium | Cross-entity semantic linking |
| **Swap** | Medium | Status intent understanding |

### Hybrid Scoring Formula

```python
def compute_hybrid_score(
    keyword_score: float,      # BM25: 0-1
    semantic_score: float,     # Cosine similarity: 0-1
    entity_type: str,
    query_length: int,
) -> float:
    """
    Adaptive hybrid scoring.

    Short queries (<5 chars): favor keyword exactness
    Long queries (>10 words): favor semantic understanding
    """

    # Entity-specific weights
    entity_weights = {
        "person": {"keyword": 0.55, "semantic": 0.40},
        "procedure": {"keyword": 0.35, "semantic": 0.60},
        "rotation": {"keyword": 0.48, "semantic": 0.47},
        "assignment": {"keyword": 0.52, "semantic": 0.43},
        "swap": {"keyword": 0.60, "semantic": 0.35},
    }

    weights = entity_weights.get(entity_type, {"keyword": 0.50, "semantic": 0.45})

    # Query length adaptation
    if query_length <= 2:
        weights["keyword"] += 0.10
        weights["semantic"] -= 0.10
    elif query_length >= 5:
        weights["semantic"] += 0.08
        weights["keyword"] -= 0.08

    return keyword_score * weights["keyword"] + semantic_score * weights["semantic"]
```

### Query Expansion

```python
class QueryExpander:
    """Expand queries with medical domain knowledge."""

    MEDICAL_EXPANSIONS = {
        "FMIT": "family medicine inpatient training hospital ward",
        "PGY": "post graduate year resident trainee",
        "ER": "emergency room emergency department acute",
        "ICU": "intensive care unit critical care",
    }

    ACTIVITY_SYNONYMS = {
        "call": ["night duty", "on-call coverage", "24-hour", "hospital duty"],
        "clinic": ["office", "ambulatory", "outpatient", "day session"],
        "inpatient": ["hospital", "ward", "acute care", "hospitalized"],
    }

    def expand(self, query: str) -> dict:
        tokens = query.lower().split()
        expanded = set(tokens)

        for token in tokens:
            if token.upper() in self.MEDICAL_EXPANSIONS:
                expanded.update(self.MEDICAL_EXPANSIONS[token.upper()].split())
            if token in self.ACTIVITY_SYNONYMS:
                expanded.update(self.ACTIVITY_SYNONYMS[token])

        return {
            "original": query,
            "expanded_terms": list(expanded),
        }
```

### API Endpoint

```python
@router.post("/search/hybrid", response_model=SearchResponse)
async def hybrid_search(
    request: SearchRequest,
    db=Depends(get_db),
):
    """
    Hybrid keyword + semantic search.

    Query parameter: semantic_weight (0.0-1.0)
    - 0.0: Pure keyword search (fast)
    - 0.5: Balanced (default)
    - 1.0: Pure semantic search
    """
    service = HybridSearchService(db)

    results = await service.hybrid_search(
        query_string=request.query,
        entity_types=request.entity_types,
        semantic_weight=request.semantic_weight or 0.5,
    )

    return SearchResponse(items=results)
```

---

## 5. Use Case 4: Schedule Similarity & Anomaly Detection

### Problem Statement

Current conflict detection is **rule-based** (ACGME violations). Cannot detect:
- Unusual-but-valid patterns
- Systemic scheduling problems
- Early warning signs before violations occur

### Solution: Schedule Embeddings

Represent schedules as vectors for:
1. **Similarity search:** Find similar past schedules
2. **Anomaly detection:** Flag unusual patterns
3. **Trend analysis:** Detect gradual drift

### Schedule Embedding Schema

```python
class DailyActivityVector:
    """16-dimensional feature vector for a single day."""

    # One-hot activity (9D): clinic, inpatient, procedure, conference,
    #                        fmit, call, night_float, off, unknown
    # Special markers (3D): back_to_back_call, post_call, rest_day
    # Intensity (1D): 0.0 (off) to 1.0 (call)
    # Supervision (1D): 0-1 scale
    # Continuity (1D): continuous duty indicator
    # Reserved (1D): future use

class WeeklyScheduleEmbedding:
    """Weekly embedding: 7 days × 16 features = 112D."""

    daily_vectors: np.ndarray  # Shape: (7, 16)
    total_intensity: float
    duty_continuity_score: float
    coverage_efficiency: float

    @property
    def embedding_vector(self) -> np.ndarray:
        return self.daily_vectors.flatten()  # (112,)

class BlockScheduleEmbedding:
    """28-day academic block: 28 × 16 = 448D."""

    daily_vectors: np.ndarray  # Shape: (28, 16)
    max_consecutive_duty_days: int
    rest_period_regularity: float
    acgme_compliance_violations: int
```

### Anomaly Detection

```python
class AnomalyDetector:
    """Multi-method anomaly detection for schedules."""

    def __init__(self, baseline_embeddings: list[np.ndarray]):
        self.baseline_mean = np.array(baseline_embeddings).mean(axis=0)
        self.baseline_std = np.array(baseline_embeddings).std(axis=0)

    def compute_anomaly_score(
        self,
        embedding: np.ndarray,
        person_id: str,
        peer_embeddings: dict[str, np.ndarray],
    ) -> AnomalyScore:
        """
        Composite anomaly score from 4 methods:
        1. Statistical outliers (Z-score)
        2. Baseline deviation (cosine distance)
        3. ACGME constraint violations
        4. Fairness anomalies (vs peers)
        """

        stat_score = self._detect_statistical_outliers(embedding)
        baseline_score = self._detect_baseline_deviation(embedding)
        acgme_score = self._detect_acgme_violations(embedding)
        fairness_score = self._detect_fairness_anomalies(
            person_id, embedding, peer_embeddings
        )

        overall = (stat_score + baseline_score + acgme_score + fairness_score) / 4.0

        severity = (
            "critical" if overall >= 0.75 else
            "high" if overall >= 0.5 else
            "medium" if overall >= 0.25 else
            "low"
        )

        return AnomalyScore(
            overall_anomaly_score=overall,
            severity=severity,
            statistical_outlier_score=stat_score,
            baseline_deviation_score=baseline_score,
            constraint_violation_score=acgme_score,
            fairness_deviation_score=fairness_score,
        )
```

### Similarity Search

```python
class ScheduleSimilarityEngine:
    """Find similar schedules using vector similarity."""

    def find_similar_weeks(
        self,
        query_embedding: np.ndarray,
        candidate_embeddings: list[tuple[str, int, np.ndarray]],
        k: int = 10,
        metric: str = "cosine"
    ) -> list[tuple[str, int, float]]:
        """
        Find K most similar weeks.

        Use cases:
        - Fair scheduling: ensure similar workload distribution
        - Learning from history: what worked for similar patterns?
        - Anomaly context: how does this differ from similar weeks?
        """
        distances = []

        for person_id, week_num, embedding in candidate_embeddings:
            if metric == "cosine":
                dist = cosine(query_embedding, embedding)
            else:
                dist = euclidean(query_embedding, embedding)
            distances.append((person_id, week_num, dist))

        distances.sort(key=lambda x: x[2])
        return distances[:k]
```

---

## 6. Use Case 5: MCP Tool Context Augmentation

### Problem Statement

The MCP server exposes **112 async tools** that return raw data without semantic context. Claude doesn't understand:
- Why ACGME rules matter
- What "utilization threshold 0.82" means
- How to interpret resilience metrics

### Solution: Semantic Tool Wrapper

Inject domain context into tool responses:

```python
class SemanticToolWrapper:
    """Inject semantic context into MCP tool responses."""

    TOOL_CONTEXT_MAP = {
        "validate_schedule": ["acgme_rules", "constraint_explanations"],
        "detect_conflicts": ["conflict_types", "constraint_explanations"],
        "check_utilization_threshold": ["queuing_theory", "defense_levels"],
        "analyze_homeostasis": ["biological_patterns", "feedback_loops"],
    }

    async def call_with_context(
        self,
        tool_func,
        tool_name: str,
        *args, **kwargs
    ) -> dict:
        # Get required contexts
        contexts = self._retrieve_contexts(tool_name)

        # Execute tool
        raw_response = await tool_func(*args, **kwargs)

        # Enrich response
        enriched = self._enrich_response(raw_response, tool_name, contexts)

        return enriched

    def _enrich_response(self, response, tool_name, contexts):
        """Add semantic metadata to response."""
        enriched = response.copy()

        if tool_name == "validate_schedule" and "issues" in response:
            for issue in enriched["issues"]:
                # Add constraint explanation
                explanation = explain_constraint(issue.get("rule_type"))
                if explanation:
                    issue["_explanation"] = explanation
                    issue["_fix_options"] = explanation.get("fix_options", [])
                    issue["_regulatory_reference"] = explanation.get("code_reference")

        # Expand abbreviations
        enriched = self._expand_abbreviations(enriched)

        return enriched
```

### Priority Tools to Augment

| Priority | Tool | Context Needed |
|----------|------|----------------|
| P0 | `validate_schedule` | ACGME rules, constraint explanations |
| P0 | `detect_conflicts` | Conflict types, fix guidance |
| P1 | `analyze_swap_candidates` | Compatibility factors |
| P1 | `check_utilization_threshold` | Queuing theory (80% rule) |
| P2 | `run_contingency_analysis` | N-1/N-2 concepts |
| P2 | `analyze_homeostasis` | Biological feedback loops |

### Response Enrichment Example

**Before (raw):**
```json
{
  "violation_type": "80_hour_rule",
  "person_id": "pgy1_001",
  "message": "Exceeded 80 hours in rolling 4-week"
}
```

**After (enriched):**
```json
{
  "violation_type": "80_hour_rule",
  "person_id": "pgy1_001",
  "message": "Exceeded 80 hours in rolling 4-week",
  "_explanation": {
    "regulatory_reference": "ACGME Section VI.F.1",
    "impact_level": "CRITICAL",
    "why_rule_exists": "Resident safety and patient care quality",
    "constraint_type": "hard"
  },
  "_fix_options": [
    "Reduce assignments in upcoming week",
    "Redistribute call among peers",
    "Request coverage from backup pool"
  ],
  "_decision_guide": [
    "1. Review current week assignments",
    "2. Identify removable non-essential blocks",
    "3. Run schedule validator after changes"
  ]
}
```

---

## 7. Use Case 6: Burnout Contagion Modeling

### Problem Statement

The resilience framework includes burnout detection (Fire Weather Index, Creep/Fatigue, SIR epidemiology) but lacks:
- Network-aware risk propagation
- Learned transmission parameters
- Embedding-based behavioral profiles

### Solution: Behavioral Vector Embeddings + Network Analysis

**Note:** This is a research-grade feature requiring significant development and validation.

### Behavioral Feature Vector (21D)

```python
class BehavioralFeatureVector:
    """21-dimensional burnout risk representation."""

    DIMENSIONS = {
        # Workload signals (0-4)
        "recent_hours_ratio": 0,       # Current/target hours
        "workload_trend": 1,           # Slope over 4 weeks
        "high_burden_shifts": 2,       # Count of severe shifts
        "swing_shift_ratio": 3,        # % evening/night
        "recovery_deficit": 4,         # Target - actual / target

        # Behavioral signals (5-9)
        "swap_request_spike": 5,       # Recent vs baseline
        "sick_call_frequency": 6,      # Per week
        "response_delay_trend": 7,     # Hours to respond
        "coverage_decline": 8,         # From historical
        "preference_deviation": 9,     # Assigned vs preferred

        # Network position (10-13)
        "degree_centrality": 10,       # Direct connections
        "betweenness_centrality": 11,  # Bridge position
        "burden_absorption_ratio": 12, # Absorbed/offloaded
        "martyr_classification": 13,   # 0-1 score

        # Stress accumulation (14-17)
        "fwi_component": 14,           # Fire Weather Index
        "creep_stage": 15,             # Primary/secondary/tertiary
        "allostatic_load": 16,         # Physiological stress
        "sta_lta_ratio": 17,           # Seismic precursor

        # Cognitive impact (18-20)
        "decision_fatigue": 18,        # Cumulative cost
        "context_switches": 19,        # Per week
        "cognitive_state": 20,         # Fresh=1, depleted=0
    }
```

### Network Embedding (Node2Vec-style)

```python
class BurnoutNetworkEmbedder:
    """Learn network position embeddings for contagion modeling."""

    def __init__(self, embedding_dim: int = 32):
        self.embedding_dim = embedding_dim

    def embed_network(
        self,
        G: nx.Graph,
        behavioral_vectors: dict[str, np.ndarray],
    ) -> dict[str, np.ndarray]:
        """
        Learn 32D embeddings from:
        1. Network structure (random walks)
        2. Behavioral context (21D vectors)
        3. Temporal dynamics (trend information)
        """

        # Generate random walks
        walks = self._generate_biased_walks(G)

        # Skip-gram embedding
        structural_emb = self._skip_gram_embedding(walks)

        # Contextualize with behavioral vectors
        contextualized = self._add_behavioral_context(
            structural_emb, behavioral_vectors
        )

        return contextualized
```

### SIR Parameter Learning

```python
class AdaptiveSIRLearner:
    """Learn transmission parameters from observed burnout spreads."""

    def learn_parameters(
        self,
        G: nx.Graph,
        behavioral_vectors: dict,
        historical_transitions: list,
        burnout_history: dict,
    ) -> dict:
        """
        Learn beta (transmission) and gamma (recovery) from history.

        Returns:
            global_beta: Base transmission rate
            global_gamma: Base recovery rate
            beta_by_contact_type: Transmission modifiers
            susceptibility_coefficients: Feature weights
        """

        # Learn which features increase transmission
        beta_params = self._learn_transmission_rates(
            historical_transitions, behavioral_vectors, G
        )

        # Learn which features slow recovery
        gamma_params = self._learn_recovery_rates(
            burnout_history, behavioral_vectors
        )

        return {
            'global_beta': beta_params['mean_beta'],
            'global_gamma': gamma_params['mean_gamma'],
            'susceptibility_coefficients': beta_params['vector_coeff'],
        }
```

### Research Questions

1. **Feature importance:** Which behavioral signals predict transmission?
2. **Embedding quality:** Do learned embeddings separate burned-out from healthy?
3. **Forecast accuracy:** Can trajectory embeddings predict 4-week ahead burnout?
4. **Intervention ROI:** Which network targets prevent most cascade infections?

---

## 8. Implementation Roadmap

### Phase 0: Foundation (Weeks 1-2)

**Goal:** Set up vector infrastructure

| Task | Owner | Deliverable |
|------|-------|-------------|
| Add pgvector extension | DevOps | Docker config, Alembic migration |
| Create EmbeddingService | Backend | `sentence-transformers` wrapper |
| Add base vector columns | Backend | Schema + migration |
| Unit tests | QA | Embedding generation tests |

**Alembic Migration:**
```python
def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.add_column('doc_chunks', sa.Column('embedding', Vector(384)))
    op.execute("""
        CREATE INDEX idx_doc_chunks_embedding
        ON doc_chunks USING ivfflat (embedding vector_cosine_ops)
    """)
```

### Phase 1: Documentation RAG (Weeks 3-4)

**Goal:** Enable semantic documentation search

| Task | Owner | Deliverable |
|------|-------|-------------|
| Implement DocumentationChunker | Backend | Markdown parsing, chunking |
| Create ingestion pipeline | Backend | Batch embed 407 files |
| Add `/docs/search` endpoint | API | REST semantic search |
| Create MCP `search_documentation` tool | MCP | Claude agent access |
| Quality validation | QA | Spot-check relevance |

**Success Criteria:**
- Query "How do I handle ACGME violations?" returns relevant constraint docs
- Latency < 200ms for 10-result queries
- MCP tool works in Claude conversations

### Phase 2: Search Enhancement (Weeks 5-6)

**Goal:** Add semantic search to entity search

| Task | Owner | Deliverable |
|------|-------|-------------|
| Add entity embedding columns | Backend | Person, Procedure, Rotation |
| Implement HybridSearchRanker | Backend | Keyword + semantic combo |
| Update `/search/hybrid` endpoint | API | Semantic weight parameter |
| Query expansion service | Backend | Medical synonym handling |
| A/B test vs keyword-only | QA | Measure relevance lift |

**Success Criteria:**
- "knee arthroscopy" finds "arthroscopic knee surgery"
- Hybrid search relevance > keyword-only by 10%+
- Latency < 250ms with semantic layer

### Phase 3: Swap Matching (Weeks 7-8)

**Goal:** Enhance swap auto-matching with semantic scoring

| Task | Owner | Deliverable |
|------|-------|-------------|
| Design swap embedding schema | Backend | Request/Faculty/Pair vectors |
| Implement SwapEmbeddingService | Backend | Feature extraction |
| Create hybrid scorer | Backend | Explicit + semantic combination |
| Train success predictor | ML | LogisticRegression on history |
| Feature flag rollout | DevOps | Enable for 5% → 25% → 100% |

**Success Criteria:**
- Hybrid score correlates with actual swap success
- Acceptance rate lift of 5-10%
- No regression in matching speed

### Phase 4: MCP Augmentation (Weeks 9-10)

**Goal:** Add semantic context to MCP tools

| Task | Owner | Deliverable |
|------|-------|-------------|
| Create SemanticToolWrapper | MCP | Context injection pattern |
| Augment scheduling tools | MCP | validate_schedule, detect_conflicts |
| Augment resilience tools | MCP | utilization, contingency |
| Add explanation cache | Backend | LRU with 5-min TTL |

**Success Criteria:**
- Claude explains *why* violations matter
- Tool responses include fix guidance
- Caching keeps latency < 20ms overhead

### Phase 5: Schedule Embeddings (Weeks 11-12)

**Goal:** Enable schedule similarity and anomaly detection

| Task | Owner | Deliverable |
|------|-------|-------------|
| Implement DailyActivityVector | Backend | 16D feature encoding |
| Create WeeklyScheduleEmbedding | Backend | 112D weekly vectors |
| Build AnomalyDetector | Backend | Multi-method scoring |
| Add similarity search | Backend | Find similar weeks |
| Dashboard integration | Frontend | Anomaly alerts |

**Success Criteria:**
- Detect unusual-but-valid schedules
- Anomaly severity correlates with actual problems
- Similar week search aids fair scheduling

### Phase 6: Burnout Research (Weeks 13+)

**Goal:** Research-grade burnout contagion modeling

| Task | Owner | Deliverable |
|------|-------|-------------|
| Design 21D behavioral vector | Research | Feature specification |
| Implement BehavioralFeatureExtractor | Backend | Connect data sources |
| Create BurnoutNetworkEmbedder | Research | Node2Vec adaptation |
| Train SIR parameter learner | Research | Historical calibration |
| Validate against outcomes | Research | Retrospective analysis |

**Success Criteria:**
- Behavioral vectors predict current burnout states
- Embeddings separate burned-out from healthy
- SIR parameters match observed spread patterns

---

## 9. Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Embedding latency | < 50ms | Per-text embedding time |
| Search latency (hybrid) | < 250ms | P95 query time |
| Vector storage | < 100 MB | Database size |
| Cache hit rate | > 90% | LRU cache performance |
| Index build time | < 5 min | Full corpus reindex |

### Business Metrics

| Use Case | Metric | Target |
|----------|--------|--------|
| Documentation RAG | Query relevance | > 80% top-5 relevant |
| Semantic Search | Relevance lift vs keyword | > 10% improvement |
| Swap Matching | Acceptance rate | +5-10% lift |
| Anomaly Detection | Precision | > 75% true anomalies |
| MCP Augmentation | Claude explanation accuracy | > 90% correct |

### User Impact

| Outcome | Indicator |
|---------|-----------|
| Faster answers | Reduced doc search time |
| Better swaps | Higher match satisfaction |
| Early warnings | Anomalies caught pre-violation |
| Claude understanding | Fewer clarification questions |

---

## 10. Risk Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| pgvector performance at scale | Low | Medium | Start with IVFFlat, upgrade to HNSW if needed |
| Embedding drift over time | Medium | Low | Monthly retraining, monitor quality metrics |
| Cache staleness | Low | Low | 5-min TTL, explicit invalidation on updates |
| Model size for medical domain | Low | Medium | Start with MiniLM, evaluate BioBERT if accuracy insufficient |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Embedding API outage | N/A | N/A | Local model, no external dependencies |
| Database migration complexity | Low | Medium | Add columns as nullable, backfill async |
| Storage growth | Low | Low | ~100 MB total, well within PostgreSQL capacity |

### Privacy/Security Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PHI in embeddings | Low | High | Use local model, no external APIs |
| Embedding inversion attacks | Very Low | Medium | Embeddings are not reversible to original text |
| PERSEC/OPSEC data exposure | Low | High | All data stays in PostgreSQL, existing security applies |

---

## 11. Appendix: Code Snippets

### A. EmbeddingService (Core)

```python
# backend/app/services/embedding_service.py

from sentence_transformers import SentenceTransformer
from typing import Union
import numpy as np

class EmbeddingService:
    """Generate and manage embeddings using local model."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.model.max_seq_length = 512
        self.embedding_dim = 384

    def embed_text(self, text: str) -> list[float]:
        """Convert text to 384-dimensional vector."""
        embedding = self.model.encode(text, convert_to_tensor=False)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding for efficiency."""
        embeddings = self.model.encode(texts, convert_to_tensor=False)
        return embeddings.tolist()

    async def embed_text_async(self, text: str) -> list[float]:
        """Async wrapper for embedding generation."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_text, text)
```

### B. SemanticSearchService

```python
# backend/app/services/semantic_search_service.py

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class SemanticSearchService:
    """Hybrid keyword + semantic search."""

    def __init__(self, db: AsyncSession, embedding_service: EmbeddingService):
        self.db = db
        self.embedding_service = embedding_service

    async def hybrid_search(
        self,
        query: str,
        entity_type: str,
        semantic_weight: float = 0.5,
        limit: int = 20,
    ) -> list[dict]:
        """
        Combined keyword + semantic search.

        Args:
            query: Search query
            entity_type: person, procedure, rotation, etc.
            semantic_weight: 0.0 (keyword only) to 1.0 (semantic only)
            limit: Max results
        """
        query_embedding = await self.embedding_service.embed_text_async(query)

        # Semantic search via pgvector
        semantic_results = await self._semantic_search(
            query_embedding, entity_type, limit * 2
        )

        # Keyword search (existing infrastructure)
        keyword_results = await self._keyword_search(
            query, entity_type, limit * 2
        )

        # Combine and rerank
        combined = self._combine_results(
            keyword_results,
            semantic_results,
            semantic_weight
        )

        return combined[:limit]

    async def _semantic_search(
        self,
        embedding: list[float],
        entity_type: str,
        limit: int,
    ) -> list[dict]:
        """Vector similarity search using pgvector."""
        stmt = text("""
            SELECT
                entity_id,
                entity_type,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM entity_embeddings
            WHERE entity_type = :entity_type
            ORDER BY embedding <=> :embedding::vector
            LIMIT :limit
        """)

        result = await self.db.execute(
            stmt,
            {
                "embedding": str(embedding),
                "entity_type": entity_type,
                "limit": limit,
            }
        )

        return [dict(row._mapping) for row in result]
```

### C. DocumentationSearchTool (MCP)

```python
# mcp-server/src/scheduler_mcp/doc_search_tool.py

from mcp import tool

@tool(name="search_documentation")
async def search_documentation(
    query: str,
    limit: int = 5,
    domain_filter: str | None = None,
) -> dict:
    """
    Search documentation for guidance on a topic.

    Args:
        query: Natural language question or topic
        limit: Maximum results to return
        domain_filter: Comma-separated domains (api,acgme,resilience)

    Returns:
        Ranked list of relevant documentation with sources

    Examples:
        - "How do I debug a constraint violation?"
        - "What's the API for creating assignments?"
        - "Explain the 80-hour rule"
    """
    domains = domain_filter.split(",") if domain_filter else None

    results = await doc_search_service.search(
        query=query,
        limit=limit,
        filter_domains=domains,
    )

    formatted = []
    for r in results:
        formatted.append({
            "source": r["source_file"],
            "section": r["section_title"],
            "excerpt": r["content"][:500] + "...",
            "relevance": f"{r['similarity']:.1%}",
        })

    return {
        "query": query,
        "results": formatted,
        "total": len(formatted),
    }
```

### D. AnomalyScore Model

```python
# backend/app/models/anomaly_score.py

from dataclasses import dataclass
from enum import Enum

class AnomalyType(Enum):
    EXCESSIVE_CALL = "excessive_call"
    INSUFFICIENT_REST = "insufficient_rest"
    BACK_TO_BACK_CALLS = "back_to_back_calls"
    OVERSATURATION = "oversaturation"
    SUDDEN_CHANGE = "sudden_change"
    BIASED_DISTRIBUTION = "biased_distribution"
    SUPERVISION_SHORTAGE = "supervision_shortage"
    OUTLIER_INTENSITY = "outlier_intensity"

@dataclass
class AnomalyScore:
    """Composite anomaly score for a schedule."""

    person_id: str
    date_or_period: str

    # Individual scores (0-1 scale)
    statistical_outlier_score: float
    baseline_deviation_score: float
    constraint_violation_score: float
    fairness_deviation_score: float
    trend_score: float

    # Composite
    overall_anomaly_score: float
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical

    explanation: str
    recommended_action: str
```

---

## Conclusion

Vector database integration offers significant value for the Residency Scheduler across multiple use cases. The recommended approach:

1. **Start with pgvector** - zero new infrastructure, HIPAA-ready
2. **Begin with Documentation RAG** - highest ROI, lowest risk
3. **Layer in semantic search** - entity-type specific benefits
4. **Enhance swap matching** - learn from historical patterns
5. **Add MCP context** - improve Claude understanding
6. **Research burnout modeling** - longer-term strategic value

**Total investment:** 8-12 weeks development, ~$0 additional infrastructure cost

**Expected outcomes:**
- Better documentation discovery
- Improved search relevance
- Higher swap acceptance rates
- Early anomaly detection
- Enhanced AI assistant capabilities

---

*Document generated by Claude Code analysis - December 2025*
