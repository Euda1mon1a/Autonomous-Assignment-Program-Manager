# Residency Scheduler

> **Last Updated:** 2026-02-15

<p align="center">
  <strong>A comprehensive medical residency scheduling system with ACGME compliance validation and AI-assisted development infrastructure</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#ai-assisted-development">AI Development</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Overview

Residency Scheduler is a production-ready, full-stack application designed to automate and optimize medical residency program scheduling while ensuring compliance with ACGME (Accreditation Council for Graduate Medical Education) requirements. Built with modern technologies, it provides an intuitive interface for program coordinators, faculty, and administrators to manage complex scheduling needs.

### Key Capabilities

- **Automated Schedule Generation** - Constraint-based algorithm with solver kill-switch and progress monitoring
- **ACGME Compliance Monitoring** - Real-time validation against 80-hour rule, 1-in-7 rule, and supervision ratios
- **Emergency Coverage System** - Handle military deployments, TDY assignments, and medical emergencies
- **Role-Based Access Control** - Secure multi-user system with admin, coordinator, and faculty roles
- **Block Schedule Import/Export** - CLI-based Excel parsing, markdown export, and data sanitization
- **AI-Assisted Development** - 34 agent skills, 27 slash commands, and Personal AI Infrastructure (PAI)
- **MCP Server Integration** - 97+ Model Context Protocol tools for AI assistant scheduling operations

---

## What's New (February 2026)

### Claude Opus 4.6 Upgrade

**Model Upgrade** - All PAI agents now run on the Claude 4.5/4.6 model family. ORCHESTRATOR and Deputies use `claude-opus-4-6`, Coordinators use `claude-sonnet-4-5-20250929`, Specialists use `claude-haiku-4-5-20251001`.

**Agent Teams (Experimental)** - Native Claude Code multi-agent coordination. Multiple Claude instances work as a team with shared task lists, peer-to-peer messaging, and centralized management. Enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in settings. Complements existing PAI hierarchy with native orchestration primitives.

**Adaptive Thinking** - Opus 4.6 intelligently determines when extended reasoning is needed. Four effort levels (low/medium/high/max) reduce latency and cost for simpler tasks while preserving deep reasoning for complex ones.

**1M Token Context Window (API Beta)** - 5x expansion from 200K tokens. Requires API usage Tier 4+ and `anthropic-beta: context-1m-2025-08-07` header. Not available on consumer claude.ai plans.

**128K Output Tokens** - Doubled from 64K, enabling longer code generation and analysis responses.

### Project Realization Sprint (February 2026)

**Build Quality & Test Calibration** - A focused 10-PR sprint that fixed build quality issues, calibrated skipped tests, and expanded test coverage. The backend test suite now includes 11,861+ tests; the frontend gained 403 component tests. Overall improvements to test reliability, lint compliance, and CI readiness.

### Previous Highlights (December 2025)

**Personal AI Infrastructure (PAI)** - Complete AI agent framework with 58 agents, 80+ skills, multi-agent orchestration, and Auftragstaktik delegation doctrine.

**MCP Server Integration** - 97+ Model Context Protocol tools for AI-assisted scheduling operations.

**CP-SAT Solver** - Constraint Programming solver with credential penalty ramp, faculty activity preservation, and ACGME compliance.

**Exotic Frontier Concepts** - 10 cutting-edge physics/biology/math scheduling modules from statistical mechanics, quantum physics, topology, neuroscience, ecology, and catastrophe theory.

---

## Features

### Schedule Management
- **Rotation Templates**: Create reusable activity patterns (clinic, inpatient, procedures, conference) with capacity limits and specialty requirements
- **Smart Assignment**: Greedy algorithm with constraint satisfaction ensures optimal coverage
- **Block-Based Scheduling**: 730 blocks per academic year (365 days × AM/PM sessions)
- **Faculty Supervision**: Automatic assignment respecting ACGME supervision ratios

### ACGME Compliance
- **80-Hour Rule**: Maximum 80 hours/week averaged over rolling 4-week periods
- **1-in-7 Rule**: Guaranteed one 24-hour period off every 7 days
- **Supervision Ratios**:
  - PGY-1: 1 faculty per 2 residents
  - PGY-2/3: 1 faculty per 4 residents
- **Violation Tracking**: Severity-based alerts (Critical, High, Medium, Low)

### Absence Management
- Multiple absence types: vacation, deployment, TDY, medical, family emergency, conference
- Military-specific tracking (deployment orders, TDY locations)
- Calendar and list views
- Automatic availability matrix updates

### User Management
- JWT-based authentication with httpOnly secure cookies
- Rate limiting on authentication endpoints (5 login/min, 3 register/min)
- Eight user roles: Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA
- Activity logging and audit trails
- Full role-based access control (RBAC) with resource-level filtering
- Strong password requirements (12+ chars, complexity rules)

### Security Features
- **Authentication**: httpOnly cookies (XSS-resistant), bcrypt password hashing
- **Authorization**: Role-based access control with admin endpoint protection
- **Input Validation**: Pydantic schemas, file upload validation (size, type, content)
- **Path Security**: Path traversal prevention in file operations
- **Secret Management**: Startup validation rejects default/weak secrets
- **Error Handling**: Global exception handler prevents information leakage
- **API Protection**: Rate limiting, CORS configuration, production doc/metrics restrictions

### Procedure Credentialing
Track faculty qualifications for supervising medical procedures:
- **Procedure Definitions**: Define procedures with complexity levels, supervision ratios, and minimum PGY requirements
- **Faculty Credentials**: Track which faculty are qualified to supervise each procedure
- **Competency Levels**: Trainee, Qualified, Expert, Master designations
- **Expiration Tracking**: Automatic alerts for expiring credentials
- **Certification Management**: Track BLS, ACLS, PALS, and other required certifications
- **Compliance Monitoring**: Ensure qualified supervisors are scheduled for procedure blocks

See [API Documentation](docs/api/AUTH_API.md) for endpoint details.

### Resilience Framework
Built-in system resilience inspired by cross-industry best practices:
- **80% Utilization Threshold** - Queuing theory prevents cascade failures
- **N-1/N-2 Contingency Analysis** - Power grid-style vulnerability detection
- **Defense in Depth** - Nuclear engineering safety levels (GREEN→YELLOW→ORANGE→RED→BLACK)
- **Static Stability** - Pre-computed fallback schedules for instant crisis response
- **Sacrifice Hierarchy** - Triage-based load shedding when capacity is constrained
- **Prometheus Metrics** - Real-time monitoring and alerting
- **Celery Background Tasks** - Automated health checks and contingency analysis

**Exotic Frontier Modules** (Tier 5):
- **Metastability Detection** - Escape stuck solver states using statistical mechanics
- **Spin Glass Model** - Generate diverse schedule replicas via frustrated constraints
- **Persistent Homology** - Topological analysis of coverage patterns
- **Free Energy Scheduling** - Prediction-driven optimization using Friston's neuroscience framework
- **Keystone Species Analysis** - Identify critical resources with cascade collapse potential
- **Catastrophe Theory** - Predict sudden failures from smooth parameter changes

See [Resilience Framework](docs/guides/resilience-framework.md) for detailed documentation.
See [Exotic Frontier Concepts](docs/architecture/EXOTIC_FRONTIER_CONCEPTS.md) for advanced modules.

### Solver Operational Controls
- **Kill-Switch**: Redis-backed abort mechanism for runaway solver jobs
- **Progress Monitoring**: Real-time tracking of solver iterations, objective scores, and violations
- **Partial Result Capture**: Saves best-solution-so-far before termination
- **Constraint Metrics**: Prometheus integration with 8 resilience gauges and 5 operational counters
- **Profiling**: Phase-based timing (pre-processing, solving, post-processing) with memory tracking

### Block Schedule Import/Export
- **CLI Import**: Parse Excel block schedules with fuzzy-tolerant matching for column shifts and name variations
- **Markdown Export**: Auto-generate human-readable schedule summaries with confidence indicators
- **Excel Export**: Legacy format support with AM/PM columns, color-coded rotations, and holiday highlighting
- **Data Sanitization**: PII protection with OPSEC/PERSEC compliance for military medical data

### Schedule Verification
- **Automated Verification Script**: 12 verification checks (FMIT patterns, call requirements, Night Float headcount)
- **Human Verification Skill**: Interactive AI-assisted checklist for manual spot-checking
- **Constraint Pre-Flight**: Validates constraint registration and weight hierarchy before commits
- **CLI Integration**: `/verify-schedule [block]` slash command for quick verification

### Dashboard & Reporting
- Schedule summary with compliance status
- Upcoming absences widget
- Quick action buttons
- Month-by-month compliance visualization

---

## AI-Assisted Development

### Personal AI Infrastructure (PAI)

The project includes a comprehensive AI-assisted development framework:

- **34 Specialized Skills** - Core scheduling, compliance validation, resilience scoring, swap execution, development, and testing skills
- **27 Slash Commands** - Quick-access workflows for schedule generation, debugging, testing, and operations
- **Agent Teams (Experimental)** - Native multi-agent coordination with shared task lists and peer-to-peer messaging
- **Auftragstaktik Delegation** - Mission-type orders: higher levels provide intent, lower levels decide how
- **Constitutions & Constraints** - Foundational rules enforcing ACGME compliance, security, and operational safety

See [CLAUDE.md](CLAUDE.md) for AI development guidelines and agent configuration.

### Slash Commands (27 Available)

| Category | Commands |
|----------|----------|
| **Development** | `/run-tests`, `/write-tests`, `/lint-fix`, `/fix-code`, `/review-code`, `/quality-check` |
| **Debugging** | `/debug`, `/debug-explore`, `/debug-tdd`, `/debug-scheduling` |
| **Scheduling** | `/generate-schedule`, `/optimize-schedule`, `/verify-schedule`, `/check-compliance`, `/swap`, `/solver` |
| **Infrastructure** | `/db-migrate`, `/docker-help`, `/health-check` |
| **Documentation** | `/export-pdf`, `/export-xlsx`, `/changelog`, `/document-session` |
| **Operations** | `/review-pr`, `/incident`, `/security`, `/check-constraints` |

### Agent Skills (34 Available)

| Tier | Skills |
|------|--------|
| **Core Scheduling** | SCHEDULING, COMPLIANCE_VALIDATION, SWAP_EXECUTION, RESILIENCE_SCORING, MCP_ORCHESTRATION |
| **Development** | test-writer, code-review, automated-code-fixer, systematic-debugger, lint-monorepo |
| **Infrastructure** | database-migration, docker-containerization, fastapi-production, frontend-development |
| **Operations** | production-incident-responder, security-audit, solver-control, safe-schedule-generation |
| **Utilities** | pdf, xlsx, changelog-generator, schedule-verification |

### MCP Server (97+ Tools)

AI assistants can interact with the scheduling system through Model Context Protocol:

- **Core Scheduling** (5 tools): validate_schedule, detect_conflicts, analyze_swap_candidates, run_contingency_analysis
- **Resilience Patterns** (13 tools): utilization threshold, defense level, N-1/N-2 analysis, fallback schedules
- **Background Tasks** (4 tools): start_background_task, get_task_status, cancel_task, list_active_tasks
- **Deployment/CI** (7 tools): validate_deployment, run_security_scan, promote_to_production, rollback
- **Empirical Testing** (5 tools): benchmark_solvers, benchmark_constraints, ablation_study
- **Advanced Analytics** (60+ tools): burnout detection, fatigue risk, entropy analysis, circuit breakers, equity metrics, RAG search, schedule quality reports, and more

See [MCP Admin Guide](docs/admin-manual/mcp-admin-guide.md) for complete documentation.

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.2.35 | React framework with App Router |
| React | 18.2.0 | UI component library |
| TypeScript | 5.0+ | Type-safe JavaScript |
| TailwindCSS | 3.4.1 | Utility-first CSS framework |
| TanStack Query | 5.90.14 | Data fetching and caching |
| Axios | 1.6.3 | HTTP client |
| date-fns | 3.1.0 | Date manipulation |
| Lucide React | 0.303.0 | Icon library |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.128.0 | High-performance web framework |
| SQLAlchemy | 2.0.45 | ORM with async support |
| Pydantic | 2.12.5 | Data validation |
| Alembic | 1.17.2 | Database migrations |
| python-jose | 3.3.0 | JWT token handling |
| passlib | 1.7.4 | Password hashing (bcrypt) |
| openpyxl | 3.1.2 | Excel export |
| NetworkX | 3.0+ | Graph analysis for hub vulnerability |
| Celery | 5.x | Background task processing |
| Redis | - | Message broker & result backend |
| Prometheus | - | Metrics and monitoring |

### MCP Server (AI Integration)
| Technology | Version | Purpose |
|------------|---------|---------|
| FastMCP | 2.14.2 | Model Context Protocol framework |
| httpx | 0.25.0+ | Async HTTP client for API calls |

### Infrastructure (Native macOS / Apple Silicon)
| Technology | Version | Purpose |
|------------|---------|---------|
| macOS / Apple Silicon | M-series | Primary deployment target |
| MLX | Latest | Native Apple Silicon LLM inference (default provider) |
| PostgreSQL | 15+ | Primary database (Homebrew) |
| Redis | Latest | Cache, message broker, rate limiting |
| Prometheus | Latest | Metrics collection |
| Grafana | Latest | Dashboard visualization |
| Docker | Latest | Available for compatibility (not primary) |

### Testing
| Technology | Purpose |
|------------|---------|
| pytest | Backend unit and integration testing (11,861+ tests) |
| Jest | Frontend unit and component testing (403 component tests) |
| React Testing Library | Component testing |
| Playwright | End-to-end testing |
| MSW | API mocking |

**Optional dependency warnings:** Some tests emit warnings if optional packages are missing
(`prometheus_client`, `strawberry`, `ripser`, `persim`, `pyyaml`, `msgpack`). These power
metrics export, GraphQL, and advanced analytics. Install them if you need those features
locally; otherwise warnings are expected.

---

## Quick Start

### Prerequisites

- macOS with Apple Silicon (M-series) — primary target
- Homebrew (`brew install postgresql redis python node`)
- Git

### Native macOS (Recommended)

```bash
# Clone the repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager

# Copy environment file
cp .env.example .env

# First time? Bootstrap installs dependencies + starts services
make native-bootstrap

# Subsequent launches (services already installed)
make native-start
# or: ./scripts/start-native.sh

# With MLX local inference (Apple Silicon)
make native-start-mlx

# Access the application
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs (Swagger UI)
# MCP:       http://localhost:8081
```

### Local LLM Inference

The LLM router defaults to MLX for Apple Silicon native inference, with automatic fallback:

```
MLX (port 8082) → Ollama (11434) → Anthropic API (cloud)
```

Configure in `.env`: `LLM_DEFAULT_PROVIDER=mlx` (default). Set `LLM_AIRGAP_MODE=true` for offline-only operation.

### Docker (Alternative)

Docker Compose configs are maintained for compatibility:

```bash
./scripts/start-local.sh        # Docker stack
make local-start                # Same via Makefile
```

### Manual Setup

See [Getting Started](docs/getting-started/installation.md) for detailed instructions.

```bash
# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && alembic upgrade head
uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev
```

See [Operations Guide](docs/operations/) for configuration reference.

---

## Project Structure

```
Autonomous-Assignment-Program-Manager/
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── api/routes/          # API endpoints (87 route files)
│   │   ├── core/                # Configuration, security, Celery
│   │   ├── db/                  # Database session management
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # Data access layer
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic layer
│   │   ├── scheduling/          # Scheduling engine & constraints
│   │   └── resilience/          # Resilience framework (5-level defense)
│   ├── alembic/                 # Database migrations
│   └── tests/                   # Backend test suite (11,861+ tests)
├── frontend/                    # Next.js application
│   ├── src/
│   │   ├── app/                 # App Router pages (20+ routes)
│   │   ├── components/          # React components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── contexts/            # React Context providers
│   │   ├── lib/                 # API client & utilities
│   │   └── types/               # TypeScript definitions (auto-generated)
│   ├── __tests__/               # Jest unit tests (403 component tests)
│   └── e2e/                     # Playwright E2E tests
├── mcp-server/                  # MCP Server (AI Integration)
│   └── src/scheduler_mcp/       # 97+ scheduling tools
├── docs/                        # Project documentation
│   ├── architecture/            # System design & ADRs
│   ├── api/                     # REST API reference
│   ├── guides/                  # Developer & operational guides
│   ├── planning/                # Roadmap, priorities, strategic decisions
│   ├── development/             # Contributing, setup, code style
│   ├── operations/              # Monitoring, security, deployment
│   ├── research/                # Advanced research topics
│   └── archived/                # Historical reports & sessions
├── scripts/                     # 101 CLI tools & utilities
├── monitoring/                  # Prometheus & Grafana configs
├── nginx/                       # Reverse proxy configuration
├── config/                      # Application configuration
├── archived/                    # Prototype experiments (agent-adk, cli, tools)
├── .claude/                     # AI development infrastructure
│   ├── commands/                # 27 slash commands
│   └── skills/                  # 34 agent skills
├── docker-compose.yml           # Production configuration
├── docker-compose.local.yml     # Development configuration
└── README.md
```

---

## Screenshots

*Screenshots available in the [User Guide](docs/user-guide/USER_GUIDE.md)*

---

## Documentation

### Getting Started
| Document | Description |
|----------|-------------|
| [User Guide](docs/user-guide/USER_GUIDE.md) | Complete user guide |
| [Getting Started](docs/getting-started/index.md) | Installation and quickstart |
| [macOS Deploy Guide](docs/getting-started/macos-deploy.md) | Complete macOS Terminal deployment |
| [Configuration](docs/getting-started/configuration.md) | Environment setup |
| [Schedule Generation Runbook](docs/guides/SCHEDULE_GENERATION_RUNBOOK.md) | Step-by-step schedule generation |

### Technical Reference
| Document | Description |
|----------|-------------|
| [Architecture Overview](ARCHITECTURE.md) | System design and data flow |
| [API Documentation](docs/api/index.md) | REST API reference |
| [Resilience Framework](docs/guides/resilience-framework.md) | Cross-industry resilience concepts |
| [Solver Algorithm](docs/architecture/SOLVER_ALGORITHM.md) | Scheduling engine internals |
| [Development Setup](docs/development/setup.md) | Local development environment |

### AI-Assisted Development
| Document | Description |
|----------|-------------|
| [Personal AI Infrastructure (PAI)](docs/PERSONAL_INFRASTRUCTURE.md) | Complete AI agent framework |
| [AI Agent User Guide](docs/guides/AI_AGENT_USER_GUIDE.md) | Skills, MCP tools, and setup |
| [Agent Skills Reference](docs/development/AGENT_SKILLS.md) | Complete skill catalog |
| [MCP Admin Guide](docs/admin-manual/mcp-admin-guide.md) | MCP server administration |
| [AI Rules of Engagement](docs/development/AI_RULES_OF_ENGAGEMENT.md) | Core AI agent rules |
| [AI Interface Guide](docs/admin-manual/ai-interface-guide.md) | Web vs CLI comparison |

### Advanced Architecture
| Document | Description |
|----------|-------------|
| [Cross-Disciplinary Bridges](docs/architecture/bridges/) | 10+ integration specifications |
| [Service Specifications](docs/specs/) | Implementation-ready service designs |
| [Mathematical Unification](docs/architecture/MATHEMATICAL_UNIFICATION.md) | Common foundations across domains |
| [Control Theory Tuning](docs/architecture/CONTROL_THEORY_TUNING_GUIDE.md) | PID controller calibration |

### Research & Innovation
| Document | Description |
|----------|-------------|
| [Research Directory](docs/research/) | Exotic concepts from diverse fields |
| [Signal Processing](docs/research/SIGNAL_PROCESSING_SCHEDULE_ANALYSIS.md) | Schedule pattern analysis |
| [Game Theory](docs/research/GAME_THEORY_FORMAL_PROOFS.md) | Strategic mechanisms for fairness |
| [Complex Systems](docs/research/) | Emergence and resilience |

### Operations
| Document | Description |
|----------|-------------|
| [Admin Manual](docs/admin-manual/README.md) | System administration guide |
| [Security Scanning](docs/operations/SECURITY_SCANNING.md) | Security tools and practices |
| [Metrics & Monitoring](docs/operations/metrics.md) | Prometheus metrics reference |
| [Load Testing](docs/operations/LOAD_TESTING.md) | Performance validation |
| [Deployment](docs/operations/DEPLOYMENT_PROMPT.md) | Production deployment |

### Planning & Status
| Document | Description |
|----------|-------------|
| [Master Priority List](docs/planning/MASTER_PRIORITY_LIST.md) | Authoritative prioritized work backlog |
| [Roadmap](docs/planning/ROADMAP.md) | Feature roadmap and milestones |
| [Strategic Decisions](docs/planning/STRATEGIC_DECISIONS.md) | Key project decisions |
| [Human TODO](HUMAN_TODO.md) | Tasks requiring human action |

### Reference Materials
| Document | Description |
|----------|-------------|
| [Schedule Abbreviations](docs/reference/SCHEDULE_ABBREVIATIONS.md) | Activity code reference |
| [Debugging Workflow](docs/development/DEBUGGING_WORKFLOW.md) | Systematic debugging guide |
| [CI/CD Troubleshooting](docs/development/CI_CD_TROUBLESHOOTING.md) | Error codes and fixes |

### Archived Documentation
Historical session logs, implementation summaries, and reports are preserved in [docs/archived/](docs/archived/README.md).

---

## API Overview

### Authentication
```
POST /api/auth/register     # Create new user
POST /api/auth/login        # OAuth2 password flow
POST /api/auth/login/json   # JSON-based login
GET  /api/auth/me           # Current user info
```

### People
```
GET    /api/people              # List all (with filters)
GET    /api/people/residents    # List residents
GET    /api/people/faculty      # List faculty
POST   /api/people              # Create person
PUT    /api/people/{id}         # Update person
DELETE /api/people/{id}         # Delete person
```

### Schedule
```
POST /api/schedule/generate           # Generate schedule
GET  /api/schedule/validate           # Validate compliance
POST /api/schedule/emergency-coverage # Handle emergencies
```

### Absences
```
GET    /api/absences      # List absences
POST   /api/absences      # Create absence
PUT    /api/absences/{id} # Update absence
DELETE /api/absences/{id} # Delete absence
```

### Resilience & Monitoring
```
GET  /health/resilience              # Resilience system status
GET  /metrics                        # Prometheus metrics endpoint
POST /api/resilience/health-check    # Trigger manual health check
GET  /api/resilience/contingency     # Run N-1/N-2 analysis
POST /api/resilience/crisis          # Activate crisis response
GET  /api/resilience/fallbacks       # List available fallback schedules
```

See [API Reference](docs/api/index.md) for complete documentation.

---

## Environment Variables

```bash
# Database Configuration
DB_PASSWORD=your_secure_password

# Security (REQUIRED - no defaults allowed in production)
SECRET_KEY=your_secret_key_here_min_32_chars  # Generate: python -c 'import secrets; print(secrets.token_urlsafe(32))'
WEBHOOK_SECRET=your_webhook_secret_min_32_chars

# Application Settings
DEBUG=false

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Redis (for Celery background tasks and rate limiting)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password  # Required for authenticated Redis

# Rate Limiting
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW=60
RATE_LIMIT_REGISTER_ATTEMPTS=3
RATE_LIMIT_REGISTER_WINDOW=60
RATE_LIMIT_ENABLED=true

# Monitoring Services (required - no defaults)
N8N_PASSWORD=your_n8n_password
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# Prometheus (optional)
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
```

> **Security Note**: The application will refuse to start in production (`DEBUG=false`) if `SECRET_KEY` or `WEBHOOK_SECRET` are empty or use default values.

---

## Running Tests

### Backend
```bash
cd backend
pytest                          # Run all tests
pytest -m acgme                 # ACGME compliance tests
pytest --cov=app --cov-report=html  # With coverage
```

### Frontend
```bash
cd frontend
npm test                        # Unit tests
npm run test:coverage           # With coverage
npm run test:ci                 # CI-optimized tests
npm run test:e2e                # E2E tests
npm run type-check              # TypeScript check (source only)
npm run lint:fix                # Auto-fix lint issues
npm run validate                # Run all checks (type-check, lint, test)
npm run audit                   # Security vulnerability check
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Steps
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` and `npm test`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [ACGME](https://www.acgme.org/) for residency program requirements
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [Next.js](https://nextjs.org/) for the React framework
- [TailwindCSS](https://tailwindcss.com/) for utility-first CSS

---

<p align="center">
  Made with care for medical education programs
</p>
