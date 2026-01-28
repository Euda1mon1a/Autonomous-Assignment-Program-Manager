# Architecture Documentation

Complete technical architecture documentation for the Residency Scheduler system.

## Quick Navigation

- **[Architectural Decision Records (ADRs)](decisions/README.md)** - Formal decision records for major design choices
- **[Overview](overview.md)** - High-level system architecture
- **[Backend](backend.md)** - FastAPI backend architecture
- **[Frontend](frontend.md)** - Next.js frontend architecture
- **[Database](database.md)** - PostgreSQL schema and design

## Core Architecture Documents

### System Design

| Document | Description |
|----------|-------------|
| [Overview](overview.md) | High-level system architecture and components |
| [Backend Architecture](backend.md) | FastAPI, SQLAlchemy, async patterns |
| [Frontend Architecture](frontend.md) | Next.js 14, React 18, TailwindCSS |
| [Database Design](database.md) | PostgreSQL schema, relationships, migrations |
| [API Design](api-design.md) | REST API patterns and conventions |

### Scheduling Engine

| Document | Description |
|----------|-------------|
| [Solver Algorithm](SOLVER_ALGORITHM.md) | Schedule generation algorithm and optimization |
| [Engine Assignment Flow](ENGINE_ASSIGNMENT_FLOW.md) | Assignment processing flow |
| [Advanced Scheduling](advanced-scheduling.md) | Multi-objective optimization |
| [Block Schedule Architecture](BLOCK_SCHEDULE_ARCHITECTURE.md) | Block-based scheduling design |
| [Academic Calendar](ACADEMIC_CALENDAR_ARCHITECTURE.md) | Academic year and block structure |

### Constraints & Validation

| Document | Description |
|----------|-------------|
| [Constraint Enablement Guide](CONSTRAINT_ENABLEMENT_GUIDE.md) | How to configure and enable constraints |
| [Constraint Interaction Matrix](CONSTRAINT_INTERACTION_MATRIX.md) | Constraint dependencies and conflicts |
| [FMIT Constraints](FMIT_CONSTRAINTS.md) | Family Medicine In-Training rotation rules |
| [Call Constraints](CALL_CONSTRAINTS.md) | Call scheduling constraints |
| [Clinic Constraints](clinic-constraints.md) | Clinic assignment rules |
| [Primary Duty Constraints](primary-duty-constraints.md) | Primary duty assignment constraints |

### Resilience Framework

| Document | Description |
|----------|-------------|
| [Resilience Overview](resilience.md) | Resilience framework overview |
| [Cross-Disciplinary Resilience](cross-disciplinary-resilience.md) | Multi-domain resilience concepts (Tier 1-4) |
| [Exotic Frontier Concepts](EXOTIC_FRONTIER_CONCEPTS.md) | Advanced optimization (Tier 5) |
| [Time Crystal Scheduling](TIME_CRYSTAL_ANTI_CHURN.md) | Anti-churn scheduling approach |
| [Resilience Contingency Procedures](RESILIENCE_CONTINGENCY_PROCEDURES.md) | Crisis response procedures |
| [Resilience Defense Level Runbook](RESILIENCE_DEFENSE_LEVEL_RUNBOOK.md) | Defense level activation guide |
| [Survivability Audit](SURVIVABILITY_AUDIT.md) | System resilience assessment |
| [Control Theory Tuning Guide](CONTROL_THEORY_TUNING_GUIDE.md) | PID controller configuration |
| [Resilience SPC Configuration](RESILIENCE_SPC_CONFIGURATION.md) | Statistical Process Control setup |
| [Resilience Military Calibration](RESILIENCE_MILITARY_CALIBRATION.md) | Military-specific tuning |

### Advanced Optimization

| Document | Description |
|----------|-------------|
| [Multi-Objective Optimization](multi-objective-optimization.md) | Pareto optimization and tradeoffs |
| [Bio-Inspired Optimization](BIO_INSPIRED_OPTIMIZATION.md) | Biological algorithms for scheduling |
| [Game Theory Framework](game-theory-framework.md) | Strategic scheduling decisions |
| [Mathematical Unification](MATHEMATICAL_UNIFICATION.md) | Unified mathematical framework |
| [Theory to Code Bridge](THEORY_TO_CODE_BRIDGE.md) | Implementing theoretical concepts |

### Experimental Research

| Document | Description |
|----------|-------------|
| [Anderson Localization](ANDERSON_LOCALIZATION.md) | Quantum-inspired constraint isolation |
| [Penrose Process](PENROSE_PROCESS_EFFICIENCY_EXTRACTION.md) | Energy extraction from rotation boundaries |
| [Circadian Workload Resonance](circadian-workload-resonance.md) | Biological rhythm alignment |
| [Temporal Dynamics FRMS](temporal-dynamics-frms.md) | Fatigue Risk Management System |
| [Frequency Lens Analysis](frequency-lens-analysis.md) | Fourier analysis of schedules |
| [Reverse Cellular Automata](reverse-cellular-automata-research.md) | CA-based schedule analysis |
| [Hidden Connections Analysis](HIDDEN_CONNECTIONS_ANALYSIS.md) | Non-obvious constraint interactions |
| [Cross-Domain Synthesis](CROSS_DOMAIN_SYNTHESIS.md) | Multi-discipline integration |

### Integration & Orchestration

| Document | Description |
|----------|-------------|
| [MCP Orchestration Patterns](MCP_ORCHESTRATION_PATTERNS.md) | Model Context Protocol patterns |
| [LLM Router Architecture](LLM_ROUTER_ARCHITECTURE.md) | Multi-model LLM routing |
| [Tool Composition Patterns](TOOL_COMPOSITION_PATTERNS.md) | Composable AI tool patterns |

### Swap System

| Document | Description |
|----------|-------------|
| [Faculty Scheduling Specification](FACULTY_SCHEDULING_SPECIFICATION.md) | Faculty assignment rules |
| [Call Generation Architecture](CALL_GENERATION_ARCHITECTURE.md) | Call schedule generation |
| [Overnight Call Processing](OVERNIGHT_CALL_PROCESSING.md) | Overnight shift handling |

### Data Management

| Document | Description |
|----------|-------------|
| [Import/Export System](import-export-system.md) | Data import/export architecture |
| [Block Schedule Parser](BLOCK_SCHEDULE_PARSER.md) | Excel schedule parsing |
| [Academic Year Blocks](ACADEMIC_YEAR_BLOCKS.md) | Block structure and calendar |
| [Rotation Types](ROTATION_TYPES.md) | Rotation category classification |

### Security & Operations

| Document | Description |
|----------|-------------|
| [Audience Auth Architecture](AUDIENCE_AUTH_ARCHITECTURE.md) | Multi-audience authorization |
| [Docker Security Best Practices](DOCKER_SECURITY_BEST_PRACTICES.md) | Container security |
| [Notification System](NOTIFICATION_SYSTEM_IMPLEMENTATION.md) | Alert delivery system |
| [Offline Operations](OFFLINE_OPERATIONS.md) | Offline-first capabilities |
| [Database Index Report](DATABASE_INDEX_REPORT.md) | Database performance optimization |

### Visualization & Analytics

| Document | Description |
|----------|-------------|
| [Holographic Visualization Hub](HOLOGRAPHIC_VISUALIZATION_HUB.md) | 3D schedule visualization |
| [3D Voxel Visualization](3d-voxel-visualization.md) | Voxel-based schedule rendering |
| [Mathematical Unification Diagram](mathematical-unification-diagram.md) | Visual framework representation |

### Infrastructure

| Document | Description |
|----------|-------------|
| [Kubernetes Evaluation](KUBERNETES_EVALUATION.md) | K8s vs Docker Compose analysis |
| [pgvector Decision](PGVECTOR_DECISION.md) | Vector database selection |
| [Bloom Integration Guide](bloom-integration-guide.md) | Bloom filter integration |

### Decision Records & Lessons

| Document | Description |
|----------|-------------|
| [**Architectural Decision Records**](decisions/README.md) | **Formal ADR index** |
| [Expert Consultation Protocol](expert-consultation-protocol.md) | LLM consultation methodology |
| [Consultation Log](CONSULTATION_LOG.md) | Expert consultation history |
| [Multi-Model Comparison Proposal](multi-model-comparison-proposal.md) | Multi-model evaluation approach |
| [Lessons Learned: Freeze Horizon](LESSONS_LEARNED_FREEZE_HORIZON.md) | Freeze horizon implementation insights |

---

## Architectural Decision Records (ADRs)

Formal records of significant architectural decisions:

### Adopted ADRs

| ADR | Title | Date |
|-----|-------|------|
| [ADR-001](decisions/ADR-001-fastapi-sqlalchemy-async.md) | FastAPI + SQLAlchemy 2.0 (Async) | 2024-12 |
| [ADR-002](decisions/ADR-002-constraint-programming-ortools.md) | Constraint Programming (OR-Tools) | 2024-12 |
| [ADR-003](decisions/ADR-003-mcp-server-ai-integration.md) | MCP Server for AI Integration | 2025-12 |
| [ADR-004](decisions/ADR-004-resilience-framework.md) | Cross-Disciplinary Resilience Framework | 2025-12 |
| [ADR-009](decisions/ADR-009-time-crystal-scheduling.md) | Time Crystal Scheduling (Anti-Churn) | 2025-12 |
| [ADR-011](decisions/ADR-011-ci-liaison-container-management.md) | CI_LIAISON Owns Container Management | 2025-12-31 |

See [decisions/README.md](decisions/README.md) for the complete ADR index.

---

## Key Architectural Principles

### 1. Layered Architecture
```
API Route (FastAPI) → Controller → Service → Repository → Model (SQLAlchemy)
```

### 2. Async-First Design
- All database operations use SQLAlchemy 2.0 async
- FastAPI async endpoints throughout
- Non-blocking I/O for scalability

### 3. Constraint Programming
- OR-Tools CP-SAT solver for schedule generation
- Declarative constraint modeling
- Multi-objective optimization

### 4. Resilience Framework
- Cross-disciplinary concepts (power grid, epidemiology, materials science)
- Defense-in-depth: 5 levels (GREEN → YELLOW → ORANGE → RED → BLACK)
- N-1/N-2 contingency analysis
- 80% utilization threshold

### 5. ACGME Compliance
- 80-hour work week rule
- 1-in-7 days off rule
- Supervision ratios (PGY-1: 1:2, PGY-2/3: 1:4)
- Automated validation and reporting

### 6. Security
- JWT authentication with httpOnly cookies
- Role-based access control (RBAC)
- Rate limiting on sensitive endpoints
- OPSEC/PERSEC for military medical data

### 7. Testability
- Pytest for backend (90%+ coverage)
- Jest + React Testing Library for frontend
- Integration tests for critical workflows
- Load testing with k6

---

## Tech Stack Overview

### Backend
- **Python 3.11+** with type hints
- **FastAPI 0.109.0** - Web framework
- **SQLAlchemy 2.0.25** - ORM with async support
- **Pydantic 2.5.3** - Data validation
- **Alembic 1.13.1** - Database migrations
- **PostgreSQL 15** - Primary database
- **Redis** - Caching and Celery broker
- **Celery 5.x** - Background tasks
- **OR-Tools** - Constraint programming

### Frontend
- **Next.js 14.0.4** - React framework with App Router
- **React 18.2.0** - UI library
- **TypeScript 5.0+** - Type safety
- **TailwindCSS 3.3.0** - Utility-first CSS
- **TanStack Query 5.17.0** - Data fetching

### MCP Server (AI Integration)
- **FastMCP 0.2.0+** - Model Context Protocol
- **httpx 0.25.0+** - Async HTTP client
- **29+ scheduling tools** for AI orchestration

### Infrastructure
- **Docker + Docker Compose** - Containerization
- **Prometheus** - Metrics
- **Grafana** - Dashboards

---

## Related Documentation

- **[CLAUDE.md](../../CLAUDE.md)** - Project guidelines for AI-assisted development
- **[API Reference](../api/README.md)** - Complete API documentation
- **[Development Guide](../development/index.md)** - Development setup and guidelines
- **[User Guide](../user-guide/index.md)** - End-user documentation

---

## Contributing to Architecture

### When to Document

Document architectural decisions when:
- Choosing technologies or frameworks
- Designing major system components
- Establishing patterns or conventions
- Rejecting common approaches (document why)

### ADR Process

1. Create ADR using template in `decisions/README.md`
2. Discuss with team and iterate
3. Update status: Proposed → Accepted → Adopted
4. Reference ADR in relevant code/docs

### Documentation Standards

- Use Markdown with clear headings
- Include diagrams where helpful (Mermaid, PlantUML)
- Provide code examples
- Link to related documentation
- Keep docs up-to-date with implementation

---

<div style="text-align: center; margin-top: 3rem; opacity: 0.7;">

**Architecture built for reliability, compliance, and resilience**

Last Updated: 2026-01-01

</div>
