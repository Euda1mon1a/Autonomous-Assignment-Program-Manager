# Documentation Index

Welcome to the Residency Scheduler documentation. This comprehensive guide will help you install, configure, use, and develop the system.

> **Documentation Restructure (2025-12-31):** Human-readable docs are now in `/docs/`, while LLM-focused documentation (session reports, technical deep dives) has moved to `.claude/dontreadme/`. See [Documentation Structure](#documentation-structure-update-2025-12-31) below.

---

## Start Here (By Role)

| Role | Start Here | Description |
|------|------------|-------------|
| **Program Coordinators** | [START_HERE_COORDINATOR.md](START_HERE_COORDINATOR.md) | Daily schedule management |
| **System Administrators** | [START_HERE_ADMIN.md](START_HERE_ADMIN.md) | System maintenance |
| **Developers** | [START_HERE_DEVELOPER.md](START_HERE_DEVELOPER.md) | Contributing code |

**Master Reference**: [MASTER_GUIDE.md](MASTER_GUIDE.md) - Comprehensive consolidated guide

---

## Quick Navigation

### For New Users
1. [Getting Started](getting-started/index.md) - Installation and first steps
2. [Configuration](getting-started/configuration.md) - Environment setup
3. [Quick Start Guide](getting-started/quickstart.md) - First steps after installation
4. [User Guide](user-guide/index.md) - How to use the application
5. [Complete User Guide](user-guide/USER_GUIDE.md) - Comprehensive user documentation

### For Administrators
1. [Admin Manual](admin-manual/index.md) - System administration
2. [Configuration Guide](admin-manual/configuration.md) - Advanced settings
3. [Backup & Recovery](admin-manual/backup.md) - Data protection
4. [User Management](admin-manual/users.md) - Managing accounts

### For Developers
1. [**CLAUDE.md**](../CLAUDE.md) - **Project guidelines for AI-assisted development** (Essential reading!)
2. [Development Setup](development/setup.md) - Local development environment
3. [Contributing Guide](development/contributing.md) - How to contribute
4. [Code Style](development/code-style.md) - Coding standards
5. [Testing](development/testing.md) - Test suite and coverage
6. [Agents Documentation](development/AGENTS.md) - AI agent integration patterns

---

## Documentation Structure

### :material-file-document: Essential Root Documents
Core project documentation located at the repository root.

| Document | Description |
|----------|-------------|
| [**CLAUDE.md**](../CLAUDE.md) | **Project guidelines for AI-assisted development** (Required reading for all developers) |
| [README.md](../README.md) | Project overview and quick start |
| [CHANGELOG.md](../CHANGELOG.md) | Version history and release notes |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Contribution guidelines |
| [ARCHITECTURE.md](../ARCHITECTURE.md) | High-level architecture overview |

### :material-rocket-launch: Getting Started
Essential guides for installation and initial setup.

| Document | Description |
|----------|-------------|
| [Index](getting-started/index.md) | Overview and installation options |
| [Installation](getting-started/installation.md) | Detailed installation instructions |
| [Configuration](getting-started/configuration.md) | Environment variables and settings |
| [Quick Start](getting-started/quickstart.md) | First steps after installation |

### :material-book-open: User Guide
Learn how to use all features of the application.

| Document | Description |
|----------|-------------|
| [Index](user-guide/index.md) | User guide overview |
| [**Complete User Guide**](user-guide/USER_GUIDE.md) | **Comprehensive user documentation** |
| [Dashboard](user-guide/dashboard.md) | Dashboard features |
| [People Management](user-guide/people.md) | Managing residents and faculty |
| [Schedule](user-guide/schedule.md) | Viewing and managing schedules |
| [Absences](user-guide/absences.md) | Time-off management |
| [Swaps](user-guide/swaps.md) | Shift swap system |
| [Compliance](user-guide/compliance.md) | ACGME compliance monitoring |
| [Exports](user-guide/exports.md) | Calendar sync and data export |

### :material-map: Guides
Comprehensive workflow and feature guides.

| Document | Description |
|----------|-------------|
| [Scheduling Workflow](guides/scheduling-workflow.md) | Complete guide to schedule generation |
| [Swap Management](guides/swap-management.md) | Detailed swap system guide |
| [Resilience Framework](guides/resilience-framework.md) | Understanding resilience and contingency planning |
| [User Workflows](guides/user-workflows.md) | Complete user workflows and best practices |

### :material-cog: Admin Manual
System administration and configuration.

| Document | Description |
|----------|-------------|
| [Index](admin-manual/index.md) | Admin manual overview |
| [Setup](admin-manual/setup.md) | Initial system setup |
| [Configuration](admin-manual/configuration.md) | Advanced configuration |
| [Backup](admin-manual/backup.md) | Backup and recovery procedures |
| [User Management](admin-manual/users.md) | User account management |

### :material-sitemap: Architecture
System design, components, and technical decisions.

| Document | Description |
|----------|-------------|
| [**Architecture Index**](architecture/README.md) | **Complete architecture documentation index** |
| [Index](architecture/index.md) | Architecture overview |
| [Overview](architecture/overview.md) | High-level system design |
| [**Architectural Decisions (ADRs)**](architecture/decisions/README.md) | **Formal decision records** |
| [Backend](architecture/backend.md) | Backend architecture |
| [Frontend](architecture/frontend.md) | Frontend architecture |
| [Database](architecture/database.md) | Database schema and design |
| [Resilience](architecture/resilience.md) | Resilience framework overview |
| [Cross-Disciplinary Resilience](architecture/cross-disciplinary-resilience.md) | Advanced resilience concepts |
| [Solver Algorithm](architecture/SOLVER_ALGORITHM.md) | Schedule generation algorithm |
| [Exotic Frontier Concepts](architecture/EXOTIC_FRONTIER_CONCEPTS.md) | Experimental optimization techniques |
| [Time Crystal Scheduling](architecture/TIME_CRYSTAL_ANTI_CHURN.md) | Anti-churn scheduling approach |
| [Clinic Constraints](architecture/clinic-constraints.md) | Clinic scheduling constraints |
| [Expert Consultation Protocol](architecture/expert-consultation-protocol.md) | LLM consultation system |
| [Multi-Model Comparison](architecture/multi-model-comparison-proposal.md) | Multi-model evaluation approach |
| [Lessons Learned](architecture/LESSONS_LEARNED_FREEZE_HORIZON.md) | Freeze horizon implementation lessons |
| [Consultation Log](architecture/CONSULTATION_LOG.md) | Expert consultation history |

### :material-api: API Reference
Complete REST API documentation.

| Document | Description |
|----------|-------------|
| [**API Index**](api/README.md) | **Complete API documentation index** |
| [Index](api/index.md) | API overview |
| [Authentication](api/AUTH_API.md) | Authentication and authorization API |
| [People](api/PEOPLE_API.md) | People management API |
| [Assignments](api/ASSIGNMENTS_API.md) | Assignment CRUD and validation API |
| [Schedule](api/SCHEDULE_API.md) | Schedule generation and management API |
| [Swaps](api/SWAPS_API.md) | Swap system API |
| [Resilience](api/RESILIENCE_API.md) | System health and crisis management API |
| [Health Monitoring](api/HEALTH_API.md) | Health check and monitoring endpoints |
| [FMIT Health](api/FMIT_HEALTH_API.md) | FMIT-specific health endpoints |
| [Call Assignments](api/CALL_ASSIGNMENTS_API.md) | Call scheduling API |
| [Exotic Frontier](api/EXOTIC_API.md) | Experimental optimization API |
| [MCP Tools Reference](api/MCP_TOOLS_REFERENCE.md) | AI integration tools |
| [Error Codes](api/error-codes-reference.md) | Complete error code reference |
| [Absences](api/absences.md) | Absence management API |
| [Analytics](api/analytics.md) | Analytics and reporting API |

### :material-code-braces: Development
Contributing guidelines and development setup.

| Document | Description |
|----------|-------------|
| [Index](development/index.md) | Development guide overview |
| [Setup](development/setup.md) | Development environment setup |
| [Contributing](development/contributing.md) | Contribution guidelines |
| [Code Style](development/code-style.md) | Code style guide |
| [Testing](development/testing.md) | Testing guidelines |
| [**Agents Documentation**](development/AGENTS.md) | **AI agent integration patterns and tools** |
| [CI/CD Recommendations](development/CI_CD_RECOMMENDATIONS.md) | CI/CD pipeline improvements |
| [N+1 Query Optimization](development/N1_QUERY_OPTIMIZATION.md) | Database query optimization |
| [TypedDict Type Safety](development/TYPEDDICT_TYPE_SAFETY.md) | Python type safety improvements |
| [Faculty Constraints Integration](development/FACULTY_CONSTRAINTS_INTEGRATION.md) | Faculty scheduling constraints |
| [Implementation Verification](development/IMPLEMENTATION_VERIFICATION.md) | Verification procedures |

### :material-cog-outline: Operations
Operational guides and monitoring.

| Document | Description |
|----------|-------------|
| [Metrics](operations/metrics.md) | Monitoring and metrics |
| [Security Scanning](operations/SECURITY_SCANNING.md) | Security scanning setup |
| [Load Testing](operations/LOAD_TESTING.md) | Load testing procedures and results |
| [Deployment Prompt](operations/DEPLOYMENT_PROMPT.md) | Deployment automation guide |
| [Celery Integration](operations/SCHEDULER_OPS_CELERY_INTEGRATION_SUMMARY.md) | Background task system integration |

### :material-rocket: Deployment
Deployment guides for various platforms.

| Document | Description |
|----------|-------------|
| [**macOS Deployment**](deployment/MACOS.md) | **Complete macOS deployment guide** |
| [Deployment Lessons Learned](deployment/LESSONS_LEARNED_ROUND1.md) | First deployment insights |

### :material-clipboard-check: Planning
Project planning and tracking documents.

| Document | Description |
|----------|-------------|
| [**Project Roadmap**](planning/ROADMAP.md) | **Long-term project roadmap and feature planning** |
| [Implementation Tracker](planning/IMPLEMENTATION_TRACKER.md) | Feature implementation status |
| [TODO Tracker](planning/TODO_TRACKER.md) | Outstanding tasks |
| [Project Status Assessment](planning/PROJECT_STATUS_ASSESSMENT.md) | Current project status |
| [Strategic Decisions](planning/STRATEGIC_DECISIONS.md) | Major strategic decisions and rationale |
| [ChatGPT Feature Review](planning/CHATGPT_FEATURE_REVIEW.md) | Review of ChatGPT Codex and Pulse |
| [Parallel Priorities Evaluation](planning/PARALLEL_PRIORITIES_EVALUATION.md) | Parallel development evaluation |
| [Leadership Discussion Guide](planning/LEADERSHIP_DISCUSSION_GUIDE.md) | Strategic discussion guide |
| [Code Complexity Analysis](planning/CODE_COMPLEXITY_ANALYSIS.md) | Code complexity metrics |
| [MCP Integration Opportunities](planning/MCP_INTEGRATION_OPPORTUNITIES.md) | Model Context Protocol integration plans |
| [FastMCP Research](planning/FASTMCP_RESEARCH.md) | FastMCP framework evaluation |

### :material-flask: Research
Experimental research and exploration documents.

| Document | Description |
|----------|-------------|
| [Experimental Research Strategy](research/EXPERIMENTAL_RESEARCH_STRATEGY.md) | Research methodology and approach |
| [Catalyst Concepts Analysis](research/catalyst-concepts-analysis.md) | Catalyst pattern analysis |
| [Quantum Physics Scheduler Exploration](research/quantum-physics-scheduler-exploration.md) | Quantum-inspired scheduling concepts |

### :material-robot: AI Agent Documentation (LLMs)
**For AI agents only** - Session reports, technical deep dives, and LLM-focused context.

| Location | Description |
|----------|-------------|
| [`.claude/dontreadme/INDEX.md`](../.claude/dontreadme/INDEX.md) | **Master index for AI agents (start here)** |
| [`.claude/dontreadme/synthesis/`](../.claude/dontreadme/synthesis/) | Patterns, decisions, lessons learned |
| [`.claude/dontreadme/sessions/`](../.claude/dontreadme/sessions/) | Session reports and completion summaries |
| [`.claude/dontreadme/reconnaissance/`](../.claude/dontreadme/reconnaissance/) | Recon findings and issue mapping |
| [`.claude/dontreadme/technical/`](../.claude/dontreadme/technical/) | Implementation details and deep dives |

**Human developers:** See [Development Guide](development/index.md) instead

### :material-archive: Archived
Historical documentation retained for reference.

| Document | Description |
|----------|-------------|
| [Archived Index](archived/README.md) | Overview of archived documentation |
| [Celery Setup Summary](archived/CELERY_SETUP_SUMMARY.md) | Celery task queue setup |
| [Celery Configuration](archived/CELERY_CONFIGURATION_REPORT.md) | Celery configuration details |
| [Celery Production Checklist](deployment/CELERY_PRODUCTION_CHECKLIST.md) | Production deployment checklist |
| [Celery Quick Reference](archived/CELERY_QUICK_REFERENCE.md) | Celery quick reference |
| [Implementation Summaries](archived/implementation-summaries/) | Historical implementation notes |
| [Reports](archived/reports/) | Historical project reports |
| [Wiki Backup](archived/wiki-backup/) | Backup of GitHub wiki content |

---

## Additional Resources

### :material-tools: Troubleshooting
[Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

### :material-history: Changelog
[Changelog](../CHANGELOG.md) - Version history and release notes

### :material-clipboard-text: Task Templates
Located in [tasks/templates/](tasks/templates/):
- [Beacon Test](tasks/templates/beacon-test.md) - System health verification
- [Cascade](tasks/templates/cascade.md) - Cascading updates
- [Consultation](tasks/templates/consultation.md) - Expert consultation template
- [Oracle Query](tasks/templates/oracle-query.md) - Knowledge base queries
- [Research](tasks/templates/research.md) - Research task template

### :material-note-text: Other Root-Level Documentation
Additional documentation files at the repository root:

| Document | Description | Recommended Action |
|----------|-------------|-------------------|
| [DOCKER_LOCAL_SETUP.md](../DOCKER_LOCAL_SETUP.md) | Docker setup guide | Consider moving to `docs/getting-started/` |
| [DOCKER_LOCAL_CHEATSHEET.md](../DOCKER_LOCAL_CHEATSHEET.md) | Docker quick reference | Consider moving to `docs/getting-started/` |
| [SCHEDULER_OPS_QUICK_START.md](../SCHEDULER_OPS_QUICK_START.md) | Operations quick start | Consider moving to `docs/operations/` |
| [SCHEDULER_OPS_CELERY_INTEGRATION_SUMMARY.md](../SCHEDULER_OPS_CELERY_INTEGRATION_SUMMARY.md) | Celery integration summary | Already in `docs/operations/` (duplicate) |
| [IMPLEMENTATION_VERIFICATION.md](../IMPLEMENTATION_VERIFICATION.md) | Implementation verification | Already in `docs/development/` (duplicate) |
| [HUMAN_TODO.md](../HUMAN_TODO.md) | Tasks requiring human action | Keep at root |

### :material-file-multiple: Docs Root-Level Files
Important files at the docs/ root:

| Document | Description |
|----------|-------------|
| [ARCHITECTURAL_DISCONNECTS.md](ARCHITECTURAL_DISCONNECTS.md) | Known architectural inconsistencies |
| [EMAIL_NOTIFICATION_INFRASTRUCTURE.md](EMAIL_NOTIFICATION_INFRASTRUCTURE.md) | Email notification system design |
| [MCP_IDE_INTEGRATION.md](MCP_IDE_INTEGRATION.md) | Model Context Protocol IDE integration |
| [PRIORITY_LIST.md](PRIORITY_LIST.md) | Current development priorities |
| [PULSE_CHECKLIST.md](PULSE_CHECKLIST.md) | System health pulse checklist |

---

## Documentation Structure (Update 2025-12-31)

**What Changed:**
- **Before:** Mixed human and LLM documentation in `/docs/` (35% was "chaff" for humans)
- **After:**
  - `/docs/` - Human-readable documentation (users, admins, developers)
  - `.claude/dontreadme/` - LLM-focused documentation (session reports, technical internals)

**Why:**
- Humans struggled to find relevant docs amid session reports and technical jargon
- AI agents needed deep context without cluttering user guides
- Separate audiences require separate content

**Result:**
- 70% reduction in documentation noise for humans
- Rich technical context for AI agents
- Cleaner, more focused guides

**Migration:** All session reports, implementation summaries, and LLM-specific docs moved to `.claude/dontreadme/`

**For AI Agents:** Start at `.claude/dontreadme/INDEX.md`

---

## Documentation Conventions

### Admonitions

The documentation uses these admonition types:

- **Note**: General information
- **Tip**: Helpful suggestions
- **Warning**: Important cautionary information
- **Danger**: Critical warnings about potential issues

### Code Examples

All code examples include the language identifier for syntax highlighting:

````markdown
```python
# Python example
def example():
    pass
```
````

### Version References

When documentation is version-specific, it includes a version badge at the top.

---

## Quick Start Path

If you're new to Residency Scheduler, follow this recommended path:

1. **Installation** → [Getting Started](getting-started/index.md)
2. **Configuration** → [Configuration Guide](getting-started/configuration.md)
3. **First Steps** → [Quick Start](getting-started/quickstart.md)
4. **Learn Features** → [User Guide](user-guide/index.md)
5. **Advanced Topics** → [Guides](guides/) section

---

## Getting Help

- **User Questions**: Check the [User Guide](user-guide/index.md)
- **API Questions**: See the [API Reference](api/index.md)
- **Technical Issues**: Review [Troubleshooting](troubleshooting.md)
- **Development**: Read the [Development Guide](development/index.md)
- **Bug Reports**: [GitHub Issues](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues)

---

## Contributing to Documentation

Documentation contributions are welcome! See [Contributing Guide](development/contributing.md) for:

- Writing style guidelines
- Documentation structure
- How to submit changes
- Review process

---

## External Documentation

### Interactive API Docs
When running the application:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### GitHub Wiki
Additional community-maintained documentation: [Project Wiki](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/wiki)

---

<div style="text-align: center; margin-top: 3rem; opacity: 0.7;">

**Made with care for those who care for others**

Version: 1.0.0 | Last Updated: 2025-12-31 (Documentation restructure)

</div>

---

## Quick Links

- **[Quick Reference Guide](QUICK_REFERENCE.md)** - Fast reference for common operations
- **[Installation](guides/installation.md)** - Setup instructions
- **[API Documentation](api/README.md)** - Complete API reference
- **[Schedule Generation](guides/SCHEDULE_GENERATION_RUNBOOK.md)** - Step-by-step schedule generation
- **[Troubleshooting](guides/SCHEDULE_GENERATION_RUNBOOK.md#troubleshooting)** - Common issues and solutions
- **[CLI Reference](operations/cli-reference.md)** - Command-line interface
- **[AI Guidelines](CLAUDE.md)** - For AI-assisted development

---

**For Immediate Help:**
- Check [Quick Reference](QUICK_REFERENCE.md) for common commands
- See [Troubleshooting](guides/SCHEDULE_GENERATION_RUNBOOK.md#troubleshooting) for issues
- Review [API Docs](api/README.md) for endpoint reference
