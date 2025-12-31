# RETRIEVAL_PATTERNS.md - Query Patterns and Usage Examples

> **Purpose:** Document retrieval patterns and query strategies for OVERNIGHT_BURN RAG system
> **Created:** 2025-12-31
> **Version:** 1.0
> **Status:** Complete with 15 documented patterns and function signatures

---

## Quick Reference

This document defines how to query the OVERNIGHT_BURN knowledge base. It includes:

1. **5 Basic Retrieval Patterns** - Fundamental query types
2. **5 Advanced Patterns** - Complex multi-step queries
3. **5 Agent-Specific Patterns** - Patterns for AI agent usage
4. **Function Signatures** - Pseudocode for implementation
5. **Search Strategies** - Decision trees for choosing patterns
6. **Caching & Staleness** - Freshness rules and TTL

---

## Part 1: Basic Retrieval Patterns

### Pattern 1: Domain-Specific Search

**Use Case:** Find all files in a specific domain

**Query:**
```json
{
  "type": "domain_search",
  "domain": "SESSION_1_BACKEND",
  "filters": {
    "priority": ["P0", "P1"]
  }
}
```

**Implementation (Pseudocode):**
```python
def search_domain(domain: str, priority: List[str] = None) -> List[File]:
    """
    Search for files in a specific domain.

    Args:
        domain: Domain name (e.g., "SESSION_1_BACKEND")
        priority: Optional priority filter (P0, P1, P2, P3)

    Returns:
        List of matching files, sorted by priority
    """
    files = FILE_REGISTRY['files']
    results = [f for f in files if f['domain'] == domain]

    if priority:
        results = [f for f in results if f['priority'] in priority]

    return sorted(results, key=lambda x: {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}[x['priority']])
```

**Example Results:**
```
SESSION_1_BACKEND: 11 files
├── BACKEND_AUTH_SUMMARY.md (P1)
├── backend-service-patterns.md (P1)
├── backend-auth-patterns.md (P1)
└── backend-repository-patterns.md (P1)
```

**When to Use:**
- New developer in a specific domain
- Implementing features in one domain
- Understanding all documentation for a system

---

### Pattern 2: Keyword Search

**Use Case:** Find files containing specific keywords

**Query:**
```json
{
  "type": "keyword_search",
  "keywords": ["async", "database"],
  "operator": "AND"
}
```

**Implementation (Pseudocode):**
```python
def search_by_keyword(keywords: List[str], operator: str = "AND") -> List[File]:
    """
    Search for files matching keywords.

    Args:
        keywords: List of keywords to search
        operator: "AND" (all keywords) or "OR" (any keyword)

    Returns:
        Files matching criteria, sorted by relevance
    """
    files = FILE_REGISTRY['files']
    results = []

    if operator == "AND":
        results = [f for f in files
                   if all(kw in f['keywords'] for kw in keywords)]
    else:  # OR
        results = [f for f in files
                   if any(kw in f['keywords'] for kw in keywords)]

    # Score by keyword matches
    scores = {}
    for f in results:
        matches = sum(1 for kw in keywords if kw in f['keywords'])
        scores[f['id']] = matches

    return sorted(results, key=lambda f: -scores[f['id']])
```

**Example Query:** `["N+1", "optimization", "backend"]`
**Results:**
```
1. backend-repository-patterns.md (3 keywords match)
2. backend-service-patterns.md (2 keywords match)
3. performance-test-patterns.md (2 keywords match)
```

**When to Use:**
- Looking for specific technical terms
- Cross-domain pattern search
- Finding related files by concept

---

### Pattern 3: Type-Based Search

**Use Case:** Find all files of a specific type

**Query:**
```json
{
  "type": "type_search",
  "file_type": "patterns",
  "domain": "SESSION_2_FRONTEND"
}
```

**Implementation (Pseudocode):**
```python
def search_by_type(file_type: str, domain: str = None) -> List[File]:
    """
    Search for files by type (patterns, reference, audit, etc).

    Args:
        file_type: Type to search (patterns, reference, audit, summary, etc)
        domain: Optional domain filter

    Returns:
        Files of matching type
    """
    files = FILE_REGISTRY['files']
    results = [f for f in files if f['type'] == file_type]

    if domain:
        results = [f for f in results if f['domain'] == domain]

    return sorted(results, key=lambda x: (x['priority'], x['filename']))
```

**File Types Available:**
- **patterns** - Code patterns and best practices
- **reference** - Complete technical reference
- **audit** - Security/quality audits
- **summary** - Condensed findings
- **reconnaissance** - Investigation results
- **specification** - Enhanced specifications
- **index** - Navigation and orientation

**When to Use:**
- Finding all pattern files in system
- Collecting audit findings for review
- Building pattern library for domain

---

### Pattern 4: Priority-Based Search

**Use Case:** Find files by priority level

**Query:**
```json
{
  "type": "priority_search",
  "priority": ["P0", "P1"],
  "domain": "SESSION_3_ACGME"
}
```

**Implementation (Pseudocode):**
```python
def search_by_priority(priority: List[str], domain: str = None) -> List[File]:
    """
    Search for files by priority level.

    Args:
        priority: List of priority levels (P0, P1, P2, P3)
        domain: Optional domain filter

    Returns:
        Files matching priority levels
    """
    files = FILE_REGISTRY['files']
    results = [f for f in files if f['priority'] in priority]

    if domain:
        results = [f for f in results if f['domain'] == domain]

    # Sort by priority order
    priority_order = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    return sorted(results, key=lambda x: (priority_order[x['priority']], x['filename']))
```

**Priority Levels:**
- **P0** - Entry points, navigation, executive summaries (start here!)
- **P1** - Core content, critical patterns, compliance rules
- **P2** - Reference materials, supporting details
- **P3** - Archive, historical (rare)

**When to Use:**
- Onboarding new developers (read P0 first)
- Focusing on essential files only
- Building reading order

---

### Pattern 5: Action Item Search

**Use Case:** Find all files with action items/TODOs

**Query:**
```json
{
  "type": "action_items_search",
  "has_action_items": true,
  "priority": ["P0", "P1"]
}
```

**Implementation (Pseudocode):**
```python
def search_action_items(domain: str = None, priority: List[str] = None) -> List[File]:
    """
    Search for files containing action items.

    Args:
        domain: Optional domain filter
        priority: Optional priority filter

    Returns:
        Files with action items, sorted by priority
    """
    files = FILE_REGISTRY['files']
    results = [f for f in files if len(f['action_items']) > 0]

    if domain:
        results = [f for f in results if f['domain'] == domain]

    if priority:
        results = [f for f in results if f['priority'] in priority]

    # Sort by action item count
    return sorted(results, key=lambda x: -len(x['action_items']))
```

**Example Output:**
```
Files with Action Items:

SESSION_1_BACKEND/backend-service-patterns.md (3 items)
  - [ ] Implement structured logging in critical paths
  - [ ] Consolidate error handling patterns
  - [ ] Reduce N+1 queries in repository layer

SESSION_5_TESTING/test-coverage-analysis.md (5 items)
  - [ ] Increase ACGME test coverage to 95%
  - [ ] Add async test patterns for Celery tasks
  ...
```

**When to Use:**
- Planning implementation tasks
- Finding what needs to be done
- Implementation checklist creation

---

## Part 2: Advanced Retrieval Patterns

### Pattern 6: Cross-Domain Impact Analysis

**Use Case:** Find how changes in one domain affect others

**Query:**
```json
{
  "type": "cross_domain_impact",
  "source_domain": "SESSION_3_ACGME",
  "target_domain": "SESSION_1_BACKEND"
}
```

**Implementation (Pseudocode):**
```python
def cross_domain_impact(source_domain: str, target_domain: str) -> Dict:
    """
    Find how changes in source domain affect target domain.

    Args:
        source_domain: Source domain (e.g., SESSION_3_ACGME)
        target_domain: Target domain (e.g., SESSION_1_BACKEND)

    Returns:
        Files affected and type of impact
    """
    files = FILE_REGISTRY['files']

    # Find files in source domain
    source_files = [f for f in files if f['domain'] == source_domain]

    # Find cross-references
    impacts = {
        'primary': [],      # Direct implementations
        'secondary': [],    # Indirect implications
        'testing': []       # Test coverage needed
    }

    for source_file in source_files:
        # Look for target domain mentions in keywords/summary
        target_files = [f for f in files
                        if f['domain'] == target_domain]

        for target_file in target_files:
            if has_cross_reference(source_file, target_file):
                impacts['primary'].append({
                    'source': source_file['filename'],
                    'target': target_file['filename'],
                    'reason': determine_relationship(source_file, target_file)
                })

    return impacts
```

**Example:**
```
Impact of SESSION_3_ACGME changes on SESSION_1_BACKEND:

Primary Impacts (direct implementation):
- backend-scheduler.py: Must implement new work hour rules
- backend-validator.py: Must validate against new compliance rules
- test-acgme-compliance.py: Must add tests for new rules

Secondary Impacts (indirect):
- backend-models.py: May need schema changes
- error-handling.py: May need new error codes

Testing Needed:
- Integration tests: Scheduler + ACGME validator
- E2E tests: Full schedule generation with new rules
```

**When to Use:**
- Planning system-wide changes
- Impact analysis for new features
- Tracing dependencies across domains

---

### Pattern 7: Semantic Similarity Search

**Use Case:** Find files similar to a given concept/document

**Query:**
```json
{
  "type": "semantic_search",
  "query_text": "How do we optimize database queries to avoid N+1 problems?",
  "top_k": 10,
  "domain_filter": "SESSION_1_BACKEND"
}
```

**Implementation (Pseudocode):**
```python
def semantic_search(query_text: str, top_k: int = 10, domain: str = None) -> List[File]:
    """
    Find semantically similar files using vector embeddings.

    Note: Requires vector database (Chroma, Pinecone, etc)

    Args:
        query_text: Query text to find similar documents
        top_k: Number of results to return
        domain: Optional domain filter

    Returns:
        Top K files by semantic similarity
    """
    # This requires vector DB implementation
    # Pseudocode assumes vector DB is available

    # 1. Embed query text
    query_vector = embed(query_text)

    # 2. Search vector database
    vector_results = vector_db.search(query_vector, top_k=top_k*2)

    # 3. Apply domain filter if specified
    if domain:
        vector_results = [r for r in vector_results
                          if FILE_REGISTRY[r['file_id']]['domain'] == domain]

    # 4. Return top K results with relevance scores
    return vector_results[:top_k]
```

**Example Results:**
```
Query: "How do we optimize database queries?"

1. backend-repository-patterns.md (similarity: 0.92)
   - Keywords: N+1, optimization, eager-loading, selectinload

2. backend-service-patterns.md (similarity: 0.85)
   - Keywords: query-optimization, caching, memoization

3. test-performance-coverage-analysis.md (similarity: 0.78)
   - Keywords: query-benchmarks, optimization-metrics
```

**When to Use:**
- Finding related patterns across domains
- Discovering existing solutions
- Building knowledge graph connections
- (Requires vector DB setup)

---

### Pattern 8: Code Example Search

**Use Case:** Find files with specific type of code examples

**Query:**
```json
{
  "type": "code_example_search",
  "language": "python",
  "pattern": "async",
  "domain": "SESSION_1_BACKEND"
}
```

**Implementation (Pseudocode):**
```python
def search_code_examples(language: str, pattern: str = None,
                         domain: str = None) -> List[File]:
    """
    Search for files with code examples in specific language.

    Args:
        language: Programming language (python, typescript, sql)
        pattern: Optional pattern to search within code
        domain: Optional domain filter

    Returns:
        Files with code examples in specified language
    """
    files = FILE_REGISTRY['files']

    # Filter by language
    results = [f for f in files
               if language in f['code_languages'] and f['contains_code_examples']]

    # Filter by domain if specified
    if domain:
        results = [f for f in results if f['domain'] == domain]

    # Sort by number of code examples
    return sorted(results, key=lambda x: -x['code_block_count'])
```

**Example Results:**
```
Files with Python async examples:

1. backend-service-patterns.md (8 code blocks)
   - async def patterns
   - await patterns
   - error handling examples

2. backend-celery-patterns.md (5 code blocks)
   - async task patterns
   - task result handling
```

**When to Use:**
- Learning by code example
- Finding implementation patterns
- Building code snippets library

---

### Pattern 9: Findings and Issues Search

**Use Case:** Find all audit findings and issues by severity

**Query:**
```json
{
  "type": "findings_search",
  "finding_type": "security",
  "min_findings": 5
}
```

**Implementation (Pseudocode):**
```python
def search_findings(finding_type: str = None,
                   min_findings: int = 0,
                   domain: str = None) -> List[File]:
    """
    Search for files with findings/issues.

    Args:
        finding_type: Type of findings (security, coverage, quality)
        min_findings: Minimum number of findings
        domain: Optional domain filter

    Returns:
        Files with findings meeting criteria
    """
    files = FILE_REGISTRY['files']

    # Filter files with sufficient findings count
    results = [f for f in files if f['findings_count'] >= min_findings]

    # Filter by domain if specified
    if domain:
        results = [f for f in results if f['domain'] == domain]

    # Filter by finding type (if determinable from type/keywords)
    if finding_type:
        results = [f for f in results
                   if f['type'] == 'audit' and finding_type in f['keywords']]

    # Sort by findings count descending
    return sorted(results, key=lambda x: -x['findings_count'])
```

**Example Output:**
```
Security Audit Findings:

1. security-auth-audit.md (12 findings)
   - PASSWORD_POLICY: Enforce 12+ character requirement
   - RATE_LIMITING: Implement on auth endpoints
   - JWT_EXPIRY: Set reasonable token expiration

2. security-input-validation-audit.md (8 findings)
   - SQL_INJECTION: Prevent with parameterized queries
   - XSS_PREVENTION: Sanitize user input
```

**When to Use:**
- Security audit planning
- Finding high-risk issues
- Building compliance checklist

---

### Pattern 10: Metadata-Based Filtering

**Use Case:** Complex filtering with multiple criteria

**Query:**
```json
{
  "type": "metadata_filter",
  "criteria": {
    "domain": ["SESSION_1_BACKEND", "SESSION_6_API_DOCS"],
    "priority": ["P0", "P1"],
    "type": ["patterns", "reference"],
    "min_size_kb": 10,
    "max_size_kb": 50
  }
}
```

**Implementation (Pseudocode):**
```python
def metadata_filter(criteria: Dict) -> List[File]:
    """
    Complex filtering with multiple metadata criteria.

    Args:
        criteria: Filter criteria dictionary with:
          - domain: List of domains
          - priority: List of priorities
          - type: List of file types
          - min_size_kb: Minimum file size
          - max_size_kb: Maximum file size
          - min_findings: Minimum findings count
          - has_code: Boolean - has code examples

    Returns:
        Files matching all criteria
    """
    files = FILE_REGISTRY['files']
    results = files

    # Apply each filter
    if 'domain' in criteria:
        results = [f for f in results if f['domain'] in criteria['domain']]

    if 'priority' in criteria:
        results = [f for f in results if f['priority'] in criteria['priority']]

    if 'type' in criteria:
        results = [f for f in results if f['type'] in criteria['type']]

    if 'min_size_kb' in criteria:
        results = [f for f in results if f['size_kb'] >= criteria['min_size_kb']]

    if 'max_size_kb' in criteria:
        results = [f for f in results if f['size_kb'] <= criteria['max_size_kb']]

    if 'has_code' in criteria and criteria['has_code']:
        results = [f for f in results if f['contains_code_examples']]

    return results
```

**When to Use:**
- Building custom knowledge bases
- Creating targeted file collections
- Filtering for specific needs

---

## Part 3: Agent-Specific Patterns

### Pattern 11: Initialization/Context Loading

**Use Case:** Agent loads OVERNIGHT_BURN context at startup

**Implementation (Pseudocode):**
```python
def load_overnight_burn_context() -> Dict:
    """
    Load OVERNIGHT_BURN context for agent initialization.

    Returns:
        Dictionary with:
        - master_index: MASTER_INDEX.md content
        - file_registry: FILE_REGISTRY.json
        - search_functions: Available search functions
    """
    context = {
        'master_index': read_file('MASTER_INDEX.md'),
        'file_registry': load_json('FILE_REGISTRY.json'),
        'domains': get_domain_summaries(),
        'search_functions': {
            'search_domain': search_domain,
            'search_by_keyword': search_by_keyword,
            'search_by_type': search_by_type,
            'search_action_items': search_action_items,
        }
    }
    return context
```

**When Used:**
- Agent initialization
- Session startup
- Knowledge base warming

---

### Pattern 12: Domain Onboarding

**Use Case:** Agent needs to understand a new domain before implementation

**Query:**
```json
{
  "type": "domain_onboarding",
  "domain": "SESSION_7_RESILIENCE",
  "depth": "comprehensive"
}
```

**Implementation (Pseudocode):**
```python
def domain_onboarding(domain: str, depth: str = "basic") -> Dict:
    """
    Prepare comprehensive domain understanding for agent.

    Args:
        domain: Domain to onboard (e.g., SESSION_1_BACKEND)
        depth: "basic" (P0 files) or "comprehensive" (P0+P1)

    Returns:
        Organized domain knowledge
    """
    # Step 1: Get domain summary
    domain_info = FILE_REGISTRY['domains'][domain]

    # Step 2: Load entry point files (P0)
    entry_files = search_domain(domain, priority=['P0'])

    # Step 3: Load core files if comprehensive
    if depth == "comprehensive":
        core_files = search_domain(domain, priority=['P1'])
    else:
        core_files = []

    # Step 4: Build context
    onboarding = {
        'domain_summary': domain_info['description'],
        'file_count': domain_info['file_count'],
        'entry_points': [read_file(f['path']) for f in entry_files],
        'core_concepts': [read_file(f['path']) for f in core_files],
        'action_items': domain_info['critical_action_items'],
        'dependencies': domain_info.get('dependencies', [])
    }

    return onboarding
```

**When Used:**
- Agent starting work in new domain
- Task delegation to specialized agent
- Cross-domain implementation

---

### Pattern 13: Task-Specific Content Retrieval

**Use Case:** Agent needs content specific to current task

**Query:**
```json
{
  "type": "task_retrieval",
  "task": "implement_rest_endpoint",
  "context": {
    "domain": "SESSION_1_BACKEND",
    "resource": "Person"
  }
}
```

**Implementation (Pseudocode):**
```python
def task_retrieval(task: str, context: Dict = None) -> List[File]:
    """
    Retrieve content relevant to specific development task.

    Args:
        task: Task type (implement_rest_endpoint, write_tests, etc)
        context: Additional context (domain, resource, feature)

    Returns:
        Prioritized list of relevant files
    """
    # Task-to-pattern mapping
    task_patterns = {
        'implement_rest_endpoint': {
            'types': ['patterns', 'reference'],
            'domains': ['SESSION_1_BACKEND', 'SESSION_6_API_DOCS'],
            'keywords': ['endpoint', 'validation', 'error-handling']
        },
        'write_tests': {
            'types': ['patterns', 'reference'],
            'domains': ['SESSION_5_TESTING'],
            'keywords': ['pytest', 'mock', 'fixture']
        },
        'add_security': {
            'types': ['audit', 'patterns', 'reference'],
            'domains': ['SESSION_4_SECURITY'],
            'keywords': ['validation', 'authentication', 'authorization']
        },
        'ensure_compliance': {
            'types': ['reference', 'patterns'],
            'domains': ['SESSION_3_ACGME'],
            'keywords': ['compliance', 'validation']
        }
    }

    # Get task patterns
    patterns = task_patterns.get(task, {})

    # Search with patterns
    results = metadata_filter({
        'type': patterns.get('types', []),
        'domain': patterns.get('domains', []),
        'priority': ['P0', 'P1']
    })

    # Boost by keywords
    for result in results:
        keyword_matches = sum(1 for kw in patterns.get('keywords', [])
                             if kw in result['keywords'])
        result['relevance_score'] = keyword_matches

    return sorted(results, key=lambda x: -x.get('relevance_score', 0))
```

**When Used:**
- During active development
- Task delegation
- Feature implementation

---

### Pattern 14: Decision Support

**Use Case:** Agent needs to make a design decision and wants best practices

**Query:**
```json
{
  "type": "decision_support",
  "decision": "error_handling_strategy",
  "context": {
    "layer": "service",
    "scope": "database_operations"
  }
}
```

**Implementation (Pseudocode):**
```python
def decision_support(decision: str, context: Dict = None) -> Dict:
    """
    Retrieve information to support design decisions.

    Args:
        decision: Decision type (error_handling_strategy, caching, etc)
        context: Additional context about the decision

    Returns:
        Patterns, best practices, and anti-patterns
    """
    # Decision-to-search mapping
    decision_map = {
        'error_handling_strategy': {
            'pattern_files': search_by_type('patterns', 'SESSION_1_BACKEND'),
            'keywords': ['error-handling', 'exception', 'validation'],
            'audit_files': search_by_type('audit', 'SESSION_4_SECURITY')
        },
        'caching_strategy': {
            'pattern_files': search_by_keyword(['caching', 'performance']),
            'reference_files': search_by_type('reference', 'SESSION_1_BACKEND')
        },
        'testing_approach': {
            'pattern_files': search_by_type('patterns', 'SESSION_5_TESTING'),
            'keywords': ['unit', 'integration', 'e2e']
        }
    }

    search_config = decision_map.get(decision, {})

    decision_package = {
        'patterns': search_config.get('pattern_files', []),
        'references': search_config.get('reference_files', []),
        'audit_findings': search_config.get('audit_files', []),
        'anti_patterns': find_anti_patterns(decision, context),
        'recommended_approach': synthesize_recommendation(decision, search_config)
    }

    return decision_package
```

**When Used:**
- Design decisions
- Architecture choices
- Best practice lookup

---

### Pattern 15: Learning Path / Skill Building

**Use Case:** Agent needs to build expertise in an area

**Query:**
```json
{
  "type": "learning_path",
  "skill": "acgme_compliance",
  "level": "expert"
}
```

**Implementation (Pseudocode):**
```python
def learning_path(skill: str, level: str = "intermediate") -> Dict:
    """
    Build structured learning path for skill development.

    Args:
        skill: Skill to learn (acgme_compliance, resilience, etc)
        level: Target level (beginner, intermediate, expert)

    Returns:
        Organized learning path with resources
    """
    # Skill-to-domain mapping
    skill_domains = {
        'acgme_compliance': {
            'primary': 'SESSION_3_ACGME',
            'supporting': ['SESSION_1_BACKEND', 'SESSION_5_TESTING', 'SESSION_7_RESILIENCE']
        },
        'resilience': {
            'primary': 'SESSION_7_RESILIENCE',
            'supporting': ['SESSION_1_BACKEND', 'SESSION_8_MCP']
        },
        'backend_patterns': {
            'primary': 'SESSION_1_BACKEND',
            'supporting': ['SESSION_4_SECURITY', 'SESSION_6_API_DOCS']
        }
    }

    domains = skill_domains.get(skill, {})

    # Build path by level
    learning_path = {
        'beginner': {
            'duration_hours': 4,
            'phase1': read_p0_files(domains['primary']),  # Overview
            'phase2': read_key_pattern_files(domains['primary']),  # Patterns
            'assessment': 'Understand core concepts'
        },
        'intermediate': {
            'duration_hours': 12,
            'phase1': complete_primary_domain(domains['primary']),
            'phase2': supporting_domain_files(domains['supporting']),
            'phase3': cross_domain_patterns(domains['supporting']),
            'assessment': 'Implement basic features'
        },
        'expert': {
            'duration_hours': 40,
            'phase1': deep_dive_all_files(domains['primary']),
            'phase2': related_audit_findings(domains),
            'phase3': cutting_edge_patterns(skill),
            'phase4': teach_and_mentor_others(skill),
            'assessment': 'Design and review solutions'
        }
    }

    return learning_path[level]
```

**When Used:**
- Skill development
- Knowledge base building
- Expert system training

---

## Part 4: Function Signatures for Implementation

### Core Search Functions

```python
# Mandatory functions for RAG system
def search_domain(domain: str, priority: List[str] = None) -> List[File]:
    """Search files in specific domain."""
    pass

def search_by_keyword(keywords: List[str], operator: str = "AND") -> List[File]:
    """Search files by keywords."""
    pass

def search_by_type(file_type: str, domain: str = None) -> List[File]:
    """Search files by type."""
    pass

def search_by_priority(priority: List[str], domain: str = None) -> List[File]:
    """Search files by priority."""
    pass

def search_action_items(domain: str = None, priority: List[str] = None) -> List[File]:
    """Find files with action items."""
    pass

# Advanced search functions
def cross_domain_impact(source_domain: str, target_domain: str) -> Dict:
    """Analyze cross-domain impacts."""
    pass

def semantic_search(query_text: str, top_k: int = 10, domain: str = None) -> List[File]:
    """Find semantically similar files (requires vector DB)."""
    pass

def search_code_examples(language: str, pattern: str = None, domain: str = None) -> List[File]:
    """Find code examples by language."""
    pass

def metadata_filter(criteria: Dict) -> List[File]:
    """Complex filtering with multiple criteria."""
    pass

# Agent-specific functions
def load_overnight_burn_context() -> Dict:
    """Load context for agent initialization."""
    pass

def domain_onboarding(domain: str, depth: str = "basic") -> Dict:
    """Prepare domain understanding for agent."""
    pass

def task_retrieval(task: str, context: Dict = None) -> List[File]:
    """Get content for specific task."""
    pass

def decision_support(decision: str, context: Dict = None) -> Dict:
    """Support design decisions with patterns."""
    pass

def learning_path(skill: str, level: str = "intermediate") -> Dict:
    """Build learning path for skill development."""
    pass
```

---

## Part 5: Search Decision Tree

Use this flowchart to choose the right search pattern:

```
START: What do you need?

├─ Navigation/Orientation?
│  ├─ First time in domain → domain_onboarding()
│  └─ Find entry points → search_domain(priority=['P0'])
│
├─ Specific Information?
│  ├─ In one domain → search_domain()
│  ├─ By keyword → search_by_keyword()
│  ├─ Code example → search_code_examples()
│  └─ Action items → search_action_items()
│
├─ Patterns/Best Practices?
│  ├─ In specific domain → search_by_type('patterns', domain)
│  ├─ Similar concept → semantic_search() [requires vector DB]
│  └─ Design decision → decision_support()
│
├─ Audit/Security Information?
│  ├─ All findings → search_by_type('audit')
│  ├─ By severity → search_findings()
│  └─ By domain → search_by_type('audit', domain)
│
├─ Complex Query?
│  ├─ Multiple criteria → metadata_filter()
│  ├─ Cross-domain analysis → cross_domain_impact()
│  └─ Learning path → learning_path()
│
└─ Agent Task?
   ├─ Initialize → load_overnight_burn_context()
   ├─ Domain work → domain_onboarding()
   ├─ Specific task → task_retrieval()
   └─ Skill building → learning_path()
```

---

## Part 6: Caching and Staleness

### Cache TTL (Time-To-Live) Rules

| Resource | TTL | Rationale |
|----------|-----|-----------|
| FILE_REGISTRY.json | 24 hours | Metadata stable, rare changes |
| MASTER_INDEX.md | 24 hours | Navigation stable |
| Domain files | 1 hour | Content changes more frequently |
| Search results | 30 minutes | Recommendations may change |
| Semantic embeddings | 7 days | Regenerate weekly for vector DB |

### Staleness Detection

```python
def is_stale(resource: str, cached_time: datetime) -> bool:
    """
    Check if cached resource is stale.

    Args:
        resource: Resource type
        cached_time: When resource was cached

    Returns:
        True if stale, False if fresh
    """
    ttl_map = {
        'FILE_REGISTRY': 24 * 3600,      # 24 hours
        'MASTER_INDEX': 24 * 3600,       # 24 hours
        'domain_files': 3600,            # 1 hour
        'search_results': 1800,          # 30 minutes
        'embeddings': 7 * 24 * 3600      # 7 days
    }

    ttl = ttl_map.get(resource, 3600)
    elapsed = (datetime.now() - cached_time).total_seconds()

    return elapsed > ttl
```

### Validation Checklist

Before returning cached results, validate:

- [ ] File registry version matches current
- [ ] File count hasn't changed significantly
- [ ] Domain structure unchanged
- [ ] No critical files deleted
- [ ] Priority classifications stable
- [ ] File content checksums valid (optional)

---

## Part 7: Error Handling

### Common Search Scenarios

| Scenario | Response |
|----------|----------|
| Domain not found | Return empty list with error message |
| No files match criteria | Return empty list with helpful message |
| Keyword not found | Return files with partial matches |
| Vector DB unavailable | Fall back to keyword search |
| FILE_REGISTRY.json corrupted | Reload from source, alert admin |
| Stale cache detected | Refresh and return fresh results |

---

## Implementation Priorities

### Phase 1: Essential (Must Have)
- [x] Pattern 1: Domain-specific search
- [x] Pattern 2: Keyword search
- [x] Pattern 3: Type-based search
- [x] Pattern 4: Priority-based search
- [ ] FILE_REGISTRY.json loader

### Phase 2: Important (Should Have)
- [ ] Pattern 5: Action item search
- [ ] Pattern 13: Task-specific retrieval
- [ ] Caching layer
- [ ] Error handling

### Phase 3: Nice-to-Have (Can Have Later)
- [ ] Pattern 7: Semantic search (requires vector DB)
- [ ] Pattern 6: Cross-domain impact
- [ ] Pattern 14: Decision support
- [ ] Pattern 15: Learning paths

---

## Testing Retrieval Patterns

### Sample Queries to Test

```python
# Pattern 1: Domain search
assert len(search_domain('SESSION_1_BACKEND', priority=['P0', 'P1'])) > 0

# Pattern 2: Keyword search
results = search_by_keyword(['async', 'database'], 'AND')
assert all('async' in f['keywords'] for f in results)

# Pattern 3: Type search
patterns = search_by_type('patterns')
assert all(f['type'] == 'patterns' for f in patterns)

# Pattern 4: Priority search
p0_files = search_by_priority(['P0'])
assert all(f['priority'] == 'P0' for f in p0_files)

# Pattern 5: Action items
action_files = search_action_items(priority=['P1'])
assert all(len(f['action_items']) > 0 for f in action_files)
```

---

## Performance Characteristics

| Operation | Complexity | Time Estimate |
|-----------|-----------|---------------|
| Domain search | O(n) | <10ms |
| Keyword search | O(n*m) | <50ms |
| Type search | O(n) | <10ms |
| Priority search | O(n) | <10ms |
| Metadata filter | O(n*k) | <100ms |
| Semantic search | O(log n) | 1-5 seconds |

(n = 223 files, m = keywords per file, k = criteria)

---

## Success Criteria

Retrieval system is working well when:

1. Domain search returns P0 files first (orientation)
2. Keyword search finds cross-domain patterns
3. Type search builds comprehensive pattern library
4. Priority search helps with reading order
5. Action items are easily discoverable
6. Agents load context in <1 second
7. File metadata is always current
8. Search results are relevant and ranked

---

**Document Status:** Complete v1.0
**Last Updated:** 2025-12-31
**Next Review:** 2026-03-31
