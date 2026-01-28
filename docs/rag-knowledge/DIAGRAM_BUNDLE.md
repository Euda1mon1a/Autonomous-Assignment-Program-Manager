# Architecture Diagram Bundle

> **Purpose:** Consolidated mermaid diagrams for AI context preloading
> **Auto-generated:** 2026-01-28
> **Source:** docs/architecture/*.md

This bundle contains all architecture diagrams extracted from the codebase for efficient AI context loading. Each diagram is machine-readable mermaid syntax with metadata.

---

## Table of Contents

1. [Engine Assignment Flow](#engine-assignment-flow)
2. [MCP Orchestration Patterns](#mcp-orchestration-patterns)
3. [Tool Composition Patterns](#tool-composition-patterns)
4. [Hub-Epidemiology Bridge](#hub-epidemiology-bridge)
5. [Meta-Tool Specifications](#meta-tool-specifications)

---

## Engine Assignment Flow

**Source:** `docs/architecture/ENGINE_ASSIGNMENT_FLOW.md`
**Domain:** Scheduling Engine
**Entities:** Solver, Validator, Assignments, Database, Preserved Slots

### Diagram: Schedule Generation Pipeline

```mermaid
graph TD
    A[Start Schedule Generation] --> B[Load Preserved Assignments]

    B --> C1[_load_fmit_assignments]
    B --> C2[_load_resident_inpatient_assignments]
    B --> C3[_load_absence_assignments]
    B --> C4[_load_offsite_assignments]
    B --> C5[_load_recovery_assignments]
    B --> C6[_load_education_assignments]

    C1 --> D[Combine into preserved_assignments]
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C6 --> D

    D --> E[Build SchedulingContext with existing_assignments]
    E --> F[Run Solver with constraints]
    F --> G{Solver Success?}

    G -->|No| H[Return Error, Keep Existing Data]
    G -->|Yes| I[_create_assignments_from_result]

    I --> J[Filter against occupied_slots]
    J --> K[Create new Assignment objects]
    K --> L[_assign_faculty with preserved check]
    L --> M[Commit to database]
    M --> N[Delete old solver-managed assignments]
    N --> O[Return ScheduleRunResult]
```

---

## MCP Orchestration Patterns

**Source:** `docs/architecture/MCP_ORCHESTRATION_PATTERNS.md`
**Domain:** Tool Orchestration, DAG Execution
**Entities:** MCP Tools, Meta-Tools, DAG Executor, Parallel Tasks

### Diagram: Deep Schedule Audit DAG

```mermaid
graph TD
    A[validate_schedule] --> B{Valid?}
    B -->|Yes| C[detect_conflicts]
    B -->|No| Z[Return Validation Errors]

    C --> D{Conflicts Found?}
    D -->|Yes| E[analyze_swap_candidates]
    D -->|No| F[run_contingency_analysis_resilience]

    E --> F
    F --> G[check_utilization_threshold]
    G --> H[get_defense_level]
    H --> I[check_mtf_compliance]
    I --> J[Deep Audit Report]

    Z --> J
```

### Diagram: Conflict Resolution Pipeline

```mermaid
graph TD
    A[detect_conflicts] --> B{Auto-Resolvable?}
    B -->|Yes| C[For Each Conflict]
    B -->|No| Z[Manual Review Required]

    C --> D[analyze_swap_candidates]
    D --> E[validate_schedule]
    E --> F{Still Valid?}
    F -->|Yes| G[Apply Resolution]
    F -->|No| H[Try Next Candidate]

    G --> I[validate_schedule]
    I --> J{Conflicts Resolved?}
    J -->|Yes| K[Success]
    J -->|No| C

    H --> C
    Z --> K
```

### Diagram: Resilience Health Check Tiers

```mermaid
graph TD
    A[Start] --> B{Run in Parallel}

    B --> C[check_utilization_threshold]
    B --> D[get_defense_level]
    B --> E[run_contingency_analysis_resilience]
    B --> F[analyze_hub_centrality]
    B --> G[check_mtf_compliance]

    C --> H[Tier 1 Complete]
    D --> H
    E --> H

    H --> I{Barrier: Tier 1 Done}

    I --> J{Run in Parallel}
    J --> K[analyze_homeostasis]
    J --> L[calculate_blast_radius]
    J --> M[analyze_le_chatelier]

    K --> N[Tier 2 Complete]
    L --> N
    M --> N

    N --> O{Barrier: Tier 2 Done}

    O --> P{Run in Parallel}
    P --> F
    P --> Q[assess_cognitive_load]
    P --> R[get_behavioral_patterns]
    P --> S[analyze_stigmergy]

    F --> T[Tier 3 Complete]
    Q --> T
    R --> T
    S --> T

    G --> T
    T --> U[Aggregate Resilience Report]
```

### Diagram: Background Task Lifecycle

```mermaid
graph TD
    A[start_background_task] --> B[Task Queued]
    B --> C{Poll Status}

    C --> D[get_task_status]
    D --> E{Status?}

    E -->|pending| F[Wait 2s]
    E -->|started| G[Wait 5s]
    E -->|success| H[Return Result]
    E -->|failure| I[Handle Error]
    E -->|retry| J[Wait 3s]

    F --> C
    G --> C
    J --> C

    I --> K{Retry?}
    K -->|Yes| L[start_background_task]
    K -->|No| M[Abort]

    L --> B

    N[User Cancel] --> O[cancel_task]
    O --> P[Revoked]
```

### Diagram: Deployment Pipeline

```mermaid
graph TD
    A[validate_deployment] --> B{Valid?}
    B -->|No| Z[Abort: Fix Issues]
    B -->|Yes| C[run_security_scan]

    C --> D{Vulnerabilities?}
    D -->|Critical| Z
    D -->|Safe| E[Parallel: Deploy to Staging]

    E --> F[run_smoke_tests staging]
    E --> G[get_deployment_status polling]

    F --> H{Tests Pass?}
    H -->|No| I[rollback_deployment]
    H -->|Yes| J[Human Approval]

    J --> K{Approved?}
    K -->|No| L[Deployment Stopped]
    K -->|Yes| M[promote_to_production]

    M --> N[run_smoke_tests production]
    N --> O{Tests Pass?}

    O -->|No| P[rollback_deployment]
    O -->|Yes| Q[Success]

    G --> R[Monitor Logs]
    R --> S{Errors?}
    S -->|Yes| I

    I --> L
    P --> L
```

### Diagram: Tool Dependency Graph

```mermaid
graph TD
    subgraph "Independent (Max Parallel)"
    A[validate_schedule]
    B[detect_conflicts]
    C[check_utilization]
    D[get_defense_level]
    E[check_mtf_compliance]
    end

    subgraph "Dependent (Sequential)"
    F[validate_deployment] --> G[run_security_scan]
    G --> H[deploy_to_staging]
    H --> I[run_smoke_tests]
    I --> J[promote_to_production]
    end

    subgraph "Background (Async)"
    K[start_background_task] -.-> L[get_task_status]
    L -.-> L
    L -.-> M[Task Complete]
    end

    subgraph "Barrier Sync (Phased)"
    N[Tier 1: Utilization + Defense + Contingency] --> O[Barrier]
    O --> P[Tier 2: Homeostasis + Blast + Le Chatelier]
    P --> Q[Barrier]
    Q --> R[Tier 3: Hubs + Cognitive + Behavioral + Stigmergy]
    end
```

---

## Tool Composition Patterns

**Source:** `docs/architecture/TOOL_COMPOSITION_PATTERNS.md`
**Domain:** Pattern Library
**Entities:** Sequential Chain, Parallel Fan-Out, Conditional Branch, Retry, Saga

### Diagram: Sequential Chain Pattern

```mermaid
graph LR
    A[validate_schedule] -->|issues| B[detect_conflicts]
    B -->|conflicts| C[analyze_swap_candidates]
    C -->|candidates| D[Result]

    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#DDA0DD
    style D fill:#FFD700
```

### Diagram: Parallel Fan-Out Pattern

```mermaid
graph TB
    A[Input: schedule_id] --> B[validate_schedule]
    A --> C[check_utilization_threshold]
    A --> D[analyze_homeostasis]
    A --> E[get_defense_level]

    B --> F[Aggregate Results]
    C --> F
    D --> F
    E --> F

    F --> G[Unified Health Score]

    style A fill:#FFD700
    style B fill:#90EE90
    style C fill:#87CEEB
    style D fill:#DDA0DD
    style E fill:#FFB6C1
    style F fill:#FFA07A
    style G fill:#98FB98
```

### Diagram: Conditional Branching Pattern

```mermaid
graph TB
    A[validate_schedule] --> B{is_valid?}
    B -->|Yes| C[Success: No action]
    B -->|No| D{critical_count > 0?}

    D -->|Yes| E[Emergency: execute_sacrifice_hierarchy]
    D -->|No| F{auto_resolvable?}

    F -->|Yes| G[Auto-fix: detect_conflicts + apply]
    F -->|No| H[Manual review required]

    E --> I[Alert coordinator]
    G --> I
    H --> I

    style A fill:#90EE90
    style B fill:#FFD700
    style C fill:#98FB98
    style D fill:#FFD700
    style E fill:#FF6B6B
    style F fill:#FFD700
    style G fill:#87CEEB
    style H fill:#FFA07A
    style I fill:#DDA0DD
```

### Diagram: Retry with Fallback Pattern

```mermaid
graph TB
    A[Start] --> B[Try: validate_schedule_by_id]
    B --> C{Success?}

    C -->|Yes| D[Return real result]
    C -->|No| E{Retry < 3?}

    E -->|Yes| F[Wait with exponential backoff]
    F --> B

    E -->|No| G[Fallback: validate_schedule_tool]
    G --> H{Success?}

    H -->|Yes| I[Return fallback result]
    H -->|No| J[Fallback: Mock validation]
    J --> K[Return degraded result]

    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#FFD700
    style D fill:#98FB98
    style E fill:#FFD700
    style F fill:#DDA0DD
    style G fill:#FFA07A
    style H fill:#FFD700
    style I fill:#98FB98
    style J fill:#FF6B6B
    style K fill:#FFB6C1
```

### Diagram: Long-Running Task Pattern

```mermaid
graph TB
    A[Start] --> B[start_background_task]
    B --> C[Get task_id]
    C --> D[Poll: get_task_status]

    D --> E{Status?}
    E -->|pending/started| F[Wait 2 seconds]
    F --> D

    E -->|success| G[Retrieve result]
    E -->|failure| H[Handle error]
    E -->|retry| I[Log retry, continue polling]
    I --> D

    G --> J[Return result]
    H --> K[Log error, return failure]

    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#DDA0DD
    style D fill:#FFD700
    style E fill:#FFA07A
    style F fill:#FFB6C1
    style G fill:#98FB98
    style H fill:#FF6B6B
    style I fill:#FFA500
    style J fill:#98FB98
    style K fill:#FF6B6B
```

### Diagram: Transactional Saga Pattern

```mermaid
graph TB
    A[Start] --> B[Step 1: validate_deployment]
    B --> C{Valid?}

    C -->|Yes| D[Step 2: run_security_scan]
    C -->|No| E[Abort: Invalid deployment]

    D --> F{Secure?}
    F -->|Yes| G[Step 3: promote_to_production]
    F -->|No| H[Compensate: rollback_deployment]

    G --> I{Success?}
    I -->|Yes| J[Commit: Success]
    I -->|No| K[Compensate: rollback_deployment]

    H --> L[Log failure]
    K --> L
    L --> M[Return failure]

    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#FFD700
    style D fill:#DDA0DD
    style E fill:#FF6B6B
    style F fill:#FFD700
    style G fill:#FFB6C1
    style H fill:#FFA500
    style I fill:#FFD700
    style J fill:#98FB98
    style K fill:#FFA500
    style L fill:#FF6B6B
    style M fill:#FF6B6B
```

---

## Hub-Epidemiology Bridge

**Source:** `docs/architecture/bridges/HUB_EPIDEMIOLOGY_BRIDGE.md`
**Domain:** Resilience Framework, Network Analysis, Epidemiology
**Entities:** Hub Analyzer, Burnout Epidemiology, Super-spreader Detection, UCI

### Diagram: Data Flow Sequence

```mermaid
sequenceDiagram
    participant UCI as UnifiedCriticalIndexAnalyzer
    participant Hub as HubAnalyzer
    participant Epi as BurnoutEpidemiology
    participant Bridge as HubEpidemiologyBridge

    UCI->>Hub: calculate_centrality(faculty, assignments, services)
    Hub-->>UCI: centrality_dict {person_id: centrality_scores}

    UCI->>Bridge: map_centrality_to_contact_rates(centrality_dict)
    Bridge-->>UCI: contact_rates {person_id: contact_rate}

    UCI->>Epi: update_contact_rates(contact_rates)
    Epi-->>UCI: Updated SIR model

    UCI->>Epi: identify_super_spreaders(threshold=5)
    Epi-->>UCI: super_spreader_list (degree-based)

    UCI->>Bridge: identify_super_spreader_profiles(centrality, burnout_states, secondary_cases)
    Bridge-->>UCI: super_spreader_profiles (three-signal)

    UCI->>UCI: Cross-validate structural vs empirical super-spreaders
    UCI-->>User: Unified super-spreader analysis + interventions
```

---

## Meta-Tool Specifications

**Source:** `docs/specs/MCP_META_TOOLS_SPEC.md`
**Domain:** MCP Meta-Tools
**Entities:** full_schedule_generation, emergency_coverage, swap_workflow

### Diagram: Full Schedule Generation DAG

```mermaid
graph TD
    A[Pre-Generation Validation] --> B{Valid Context?}
    B -->|No| Z[Abort with Errors]
    B -->|Yes| C[Verify Database Backup]

    C --> D{Backup Exists?}
    D -->|No| E[Create Backup]
    D -->|Yes| F[Generate Schedule via API]
    E --> F

    F --> G[Validate Generated Schedule]
    G --> H{ACGME Compliant?}

    H -->|No| I[Detect Conflicts]
    I --> J{Auto-Resolvable?}
    J -->|Yes| K[Auto-Resolve Conflicts]
    K --> G
    J -->|No| L[Manual Review Required]

    H -->|Yes| M[Parallel Health Checks]
    M --> N[check_utilization_threshold]
    M --> O[run_contingency_analysis]
    M --> P[detect_conflicts]

    N --> Q[Aggregate Report]
    O --> Q
    P --> Q

    Q --> R{Approval Required?}
    R -->|Yes| S[Request Human Approval]
    R -->|No| T[Apply Schedule]
    S --> U{Approved?}
    U -->|Yes| T
    U -->|No| V[Rollback to Backup]

    T --> W[Post-Generation Validation]
    W --> X{Success?}
    X -->|No| V
    X -->|Yes| Y[Success Report]

    L --> Y
    V --> Y
    Z --> Y
```

---

## Quick Reference: Entity Relationships

### Core Scheduling Flow
```
Preserved Assignments --> Solver --> Validator --> Committer --> Database
```

### Resilience Analysis Flow
```
Faculty --> Hub Analyzer --> Centrality Scores --> Epidemiology --> Super-spreader Detection
```

### Tool Orchestration Flow
```
Meta-Tool --> DAG Executor --> Atomic Tools (parallel) --> Aggregator --> Report
```

### Deployment Flow
```
Validate --> Security Scan --> Stage --> Smoke Test --> Approve --> Production
```

---

## Diagram Metadata Summary

| Diagram | Type | Nodes | Edges | Domain |
|---------|------|-------|-------|--------|
| Schedule Generation Pipeline | flowchart | 16 | 18 | scheduling |
| Deep Schedule Audit DAG | flowchart | 11 | 13 | orchestration |
| Conflict Resolution Pipeline | flowchart | 12 | 14 | orchestration |
| Resilience Health Check Tiers | flowchart | 21 | 24 | resilience |
| Background Task Lifecycle | flowchart | 16 | 17 | async |
| Deployment Pipeline | flowchart | 19 | 21 | deployment |
| Tool Dependency Graph | flowchart | 18 | 12 | orchestration |
| Sequential Chain Pattern | flowchart | 4 | 3 | pattern |
| Parallel Fan-Out Pattern | flowchart | 7 | 8 | pattern |
| Conditional Branching Pattern | flowchart | 9 | 10 | pattern |
| Retry with Fallback Pattern | flowchart | 11 | 12 | pattern |
| Long-Running Task Pattern | flowchart | 11 | 12 | pattern |
| Transactional Saga Pattern | flowchart | 13 | 13 | pattern |
| Hub-Epidemiology Data Flow | sequence | 4 | 12 | resilience |
| Full Schedule Generation DAG | flowchart | 25 | 28 | meta-tool |

**Total:** 15 diagrams, 197 nodes, 207 edges

---

*Bundle generated: 2026-01-28 | Source files: 5*
