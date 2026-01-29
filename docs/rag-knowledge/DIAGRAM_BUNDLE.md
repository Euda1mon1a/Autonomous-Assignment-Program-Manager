# Architecture Diagram Bundle

> **Purpose:** Consolidated mermaid diagrams for AI context preloading
> **Auto-generated:** Do not edit manually - run `scripts/generate-diagram-bundle.sh`
> **doc_type:** architecture_diagrams

This bundle contains all architecture diagrams extracted from the codebase for efficient AI context loading. Each diagram is machine-readable mermaid syntax with source attribution.

---

## Quick Stats

- **Files scanned:** 8
- **Total diagrams:** 42
- **Generated:** 2026-01-29T01:00:05Z

---

## ENGINE_ASSIGNMENT_FLOW

**Source:** `docs/architecture/ENGINE_ASSIGNMENT_FLOW.md`
**Diagrams:** 1


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

## MCP_ORCHESTRATION_PATTERNS

**Source:** `docs/architecture/MCP_ORCHESTRATION_PATTERNS.md`
**Diagrams:** 6


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

## TOOL_COMPOSITION_PATTERNS

**Source:** `docs/architecture/TOOL_COMPOSITION_PATTERNS.md`
**Diagrams:** 6


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

## HUB_EPIDEMIOLOGY_BRIDGE

**Source:** `docs/architecture/bridges/HUB_EPIDEMIOLOGY_BRIDGE.md`
**Diagrams:** 1


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

## N8N_WORKFLOW_SUMMARY

**Source:** `docs/data/N8N_WORKFLOW_SUMMARY.md`
**Diagrams:** 1


```mermaid
flowchart TD
    A[Phase 0: Absence Loading] --> B[Phase 1: Block Pairing]
    B --> C[Phase 2: Resident Association]
    C --> D[Phase 3: Faculty Assignment]
    D --> E[Phase 4: Call Scheduling]
    E --> F[Phase 5: SKIPPED/Obsolete]
    F --> G[Phase 6: Minimal Cleanup]
    G --> H[Phase 7: Validation & Reporting]
    H --> I[Phase 8: Emergency Coverage]
    I --> J[Phase 9: Excel Export]
    J --> K[Finalize & Generate Report]
```

---

## AUDIENCE_AUTH_USAGE

**Source:** `docs/development/AUDIENCE_AUTH_USAGE.md`
**Diagrams:** 1


```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant AuthAPI
    participant OperationAPI
    participant Database

    User->>Frontend: Initiate sensitive operation
    Frontend->>AuthAPI: POST /api/audience-tokens/tokens
    Note right of AuthAPI: Validates user<br/>access token
    AuthAPI->>Database: Log token creation
    AuthAPI-->>Frontend: Audience token (2 min TTL)
    Frontend->>OperationAPI: POST /jobs/{id}/abort<br/>(with audience token)
    Note right of OperationAPI: Validates audience<br/>matches operation
    OperationAPI->>Database: Check blacklist
    OperationAPI->>Database: Execute operation
    OperationAPI->>Database: Log operation
    OperationAPI-->>Frontend: Success
    Frontend->>AuthAPI: POST /api/audience-tokens/revoke
    AuthAPI->>Database: Blacklist token
```

---

## MERMAID_GRAPH_RAG_ENHANCEMENT

**Source:** `docs/development/MERMAID_GRAPH_RAG_ENHANCEMENT.md`
**Diagrams:** 9


```mermaid
graph TD
    A[Solver] --> B[Validator]
    B --> C[Committer]
```


```mermaid
        echo "## $(basename "$file" .md)" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
        echo "**Source:** \`$file\`" >> "$OUTPUT"
        echo "" >> "$OUTPUT"

        # Extract mermaid blocks with context

```mermaid
        echo "" >> "$OUTPUT"
        echo "---" >> "$OUTPUT"
        echo "" >> "$OUTPUT"
    fi
done

echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUTPUT"
```


```mermaid
        matches = re.findall(pattern, content, re.DOTALL)
        return matches

    def parse_diagram(
        self,
        mermaid_code: str,
        source_file: str | None = None
    ) -> ParsedDiagram:
        """Parse a mermaid diagram into structured data."""
        lines = mermaid_code.strip().split('\n')

        # Detect diagram type
        diagram_type = "other"
        for line in lines:
            match = self.DIAGRAM_TYPE.match(line.strip())
            if match:
                type_str = match.group(1).lower()
                if type_str in ("graph", "flowchart"):
                    diagram_type = "flowchart"
                elif type_str == "sequencediagram":
                    diagram_type = "sequence"
                elif type_str == "classdiagram":
                    diagram_type = "class"
                elif type_str == "erdiagram":
                    diagram_type = "er"
                elif type_str == "statediagram":
                    diagram_type = "state"
                break

        # Extract title from comments
        title = None
        for line in lines:
            if line.strip().startswith('%%') and 'title' in line.lower():
                title = line.replace('%%', '').replace('title:', '').strip()
                break

        # Parse nodes and edges (flowchart-specific for now)
        nodes = {}
        edges = []

        if diagram_type == "flowchart":
            for line in lines:
                # Find nodes
                for match in self.FLOWCHART_NODE.finditer(line):
                    node_id, label = match.groups()
                    if node_id not in nodes:
                        nodes[node_id] = DiagramNode(
                            id=node_id,
                            label=label.strip(),
                            node_type=self._infer_node_type(label)
                        )

                # Find edges
                for match in self.FLOWCHART_EDGE.finditer(line):
                    source, label, target = match.groups()
                    edges.append(DiagramEdge(
                        source=source,
                        target=target,
                        label=label.strip() if label else None
                    ))

        return ParsedDiagram(
            diagram_type=diagram_type,
            title=title,
            nodes=list(nodes.values()),
            edges=edges,
            raw_mermaid=mermaid_code,
            source_file=source_file
        )

    def _infer_node_type(self, label: str) -> str | None:
        """Infer node type from label text."""
        label_lower = label.lower()
        if any(kw in label_lower for kw in ['database', 'db', 'store']):
            return 'database'
        if any(kw in label_lower for kw in ['api', 'endpoint', 'route']):
            return 'api'
        if any(kw in label_lower for kw in ['service', 'handler']):
            return 'service'
        if any(kw in label_lower for kw in ['?', 'valid', 'check']):
            return 'decision'
        return 'process'

    def to_entity_metadata(self, diagram: ParsedDiagram) -> list[dict]:
        """Convert parsed diagram to entity metadata for RAG storage."""
        entities = []

        for node in diagram.nodes:
            entities.append({
                "entity_type": "diagram_node",
                "entity_id": node.id,
                "entity_label": node.label,
                "node_type": node.node_type,
                "diagram_type": diagram.diagram_type,
                "diagram_title": diagram.title,
                "source_file": diagram.source_file,
                "relations": [
                    {
                        "type": "connects_to",
                        "target": edge.target,
                        "label": edge.label
                    }
                    for edge in diagram.edges
                    if edge.source == node.id
                ]
            })

        return entities
```


```mermaid
%% FILE: scheduling-engine.ai.mmd
%% PURPOSE: End-to-end schedule generation showing solver, validator, committer pipeline
%% DOMAIN: scheduling
%% ENTITIES: Solver, Validator, Committer, Database, Cache
%% UPDATED: 2026-01-28

graph TD
    subgraph Input
        A[Load Preserved Assignments]
        B[Load Constraints]
    end

    subgraph Solver
        C[Initialize CP-SAT]
        D[Add Variables]
        E[Add Constraints]
        F[Solve]
    end

    subgraph Validation
        G{ACGME Valid?}
        H[Log Violations]
    end

    subgraph Output
        I[Commit to DB]
        J[Invalidate Cache]
        K[Notify Subscribers]
    end

    A --> C
    B --> C
    C --> D --> E --> F
    F --> G
    G -->|Yes| I
    G -->|No| H
    H --> F
    I --> J --> K
```


```mermaid
%% FILE: <filename>
%% PURPOSE: <one-line description>
%% DOMAIN: <scheduling|auth|resilience|data|frontend>
%% ENTITIES: <comma-separated list of key nodes>
%% UPDATED: <YYYY-MM-DD>
%% RELATES_TO: <other diagram files>
```


```mermaid
graph TD
    A[Rectangle]           %% Standard process
    B(Rounded)             %% Alternative process
    C{Diamond}             %% Decision
    D[(Database)]          %% Database
    E((Circle))            %% Start/End
    F>Flag]                %% Flag/Note
    G{{Hexagon}}           %% Preparation
```


```mermaid
graph LR
    A --> B                %% Arrow
    A --- B                %% Line
    A -.-> B               %% Dotted arrow
    A ==> B                %% Thick arrow
    A --text--> B          %% Arrow with text
    A -->|text| B          %% Arrow with text (alt)
```


```mermaid
graph TD
    subgraph Backend
        A[Service]
        B[Repository]
    end
    subgraph Frontend
        C[Component]
        D[Hook]
    end
    C --> A
```

---

## MCP_META_TOOLS_SPEC

**Source:** `docs/specs/MCP_META_TOOLS_SPEC.md`
**Diagrams:** 2


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


```mermaid
graph TD
    A[Detect Coverage Gaps] --> B{Gaps Found?}
    B -->|No| Z[No Action Needed]
    B -->|Yes| C[Parallel Analysis]

    C --> D[run_contingency_analysis]
    C --> E[analyze_swap_candidates for each gap]
    C --> F[get_static_fallbacks]

    D --> G[Aggregate Options]
    E --> G
    F --> G

    G --> H[Rank Solutions]
    H --> I{Best Solution?}

    I -->|Swap| J[Validate Swap]
    I -->|Fallback| K[Validate Fallback]
    I -->|Load Shed| L[execute_sacrifice_hierarchy simulate]

    J --> M{Valid?}
    K --> M
    L --> M

    M -->|Yes| N{Auto-Apply?}
    M -->|No| O[Try Next Option]

    N -->|Yes| P[Apply Solution]
    N -->|No| Q[Request Approval]

    P --> R[Verify Resolution]
    Q --> S{Approved?}
    S -->|Yes| P
    S -->|No| O

    R --> T{Gaps Closed?}
    T -->|No| O
    T -->|Yes| U[Success Report]

    O --> H
    Z --> U
```

---

## Regeneration

To regenerate this bundle:

```bash
./scripts/generate-diagram-bundle.sh
```

To check if bundle is stale:

```bash
./scripts/generate-diagram-bundle.sh --check
```

---

*This file is auto-generated. Do not edit manually.*
