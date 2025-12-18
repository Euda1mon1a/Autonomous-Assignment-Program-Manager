# Documentation Index

Welcome to the Residency Scheduler documentation. This comprehensive guide will help you install, configure, use, and develop the system.

---

## Quick Navigation

### For New Users
1. [Getting Started](getting-started/index.md) - Installation and first steps
2. [Configuration](getting-started/configuration.md) - Environment setup
3. [Quick Start Guide](getting-started/quickstart.md) - First steps after installation
4. [User Guide](user-guide/index.md) - How to use the application

### For Administrators
1. [Admin Manual](admin-manual/index.md) - System administration
2. [Configuration Guide](admin-manual/configuration.md) - Advanced settings
3. [Backup & Recovery](admin-manual/backup.md) - Data protection
4. [User Management](admin-manual/users.md) - Managing accounts

### For Developers
1. [Development Setup](development/setup.md) - Local development environment
2. [Contributing Guide](development/contributing.md) - How to contribute
3. [Code Style](development/code-style.md) - Coding standards
4. [Testing](development/testing.md) - Test suite and coverage

---

## Documentation Structure

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
| [Index](architecture/index.md) | Architecture overview |
| [Overview](architecture/overview.md) | High-level system design |
| [Backend](architecture/backend.md) | Backend architecture |
| [Frontend](architecture/frontend.md) | Frontend architecture |
| [Database](architecture/database.md) | Database schema and design |
| [Resilience](architecture/resilience.md) | Resilience framework overview |
| [Clinic Constraints](architecture/clinic-constraints.md) | Clinic scheduling constraints |
| [Expert Consultation Protocol](architecture/expert-consultation-protocol.md) | LLM consultation system |
| [Multi-Model Comparison](architecture/multi-model-comparison-proposal.md) | Multi-model evaluation approach |
| [Lessons Learned](architecture/LESSONS_LEARNED_FREEZE_HORIZON.md) | Freeze horizon implementation lessons |
| [Consultation Log](architecture/CONSULTATION_LOG.md) | Expert consultation history |

### :material-api: API Reference
Complete REST API documentation.

| Document | Description |
|----------|-------------|
| [Index](api/index.md) | API overview |
| [Authentication](api/authentication.md) | Authentication endpoints |
| [People](api/people.md) | People management API |
| [Schedule](api/schedule.md) | Schedule management API |
| [Absences](api/absences.md) | Absence management API |
| [Swaps](api/swaps.md) | Swap system API |
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
| [CI/CD Recommendations](development/CI_CD_RECOMMENDATIONS.md) | CI/CD pipeline improvements |

### :material-cog-outline: Operations
Operational guides and monitoring.

| Document | Description |
|----------|-------------|
| [Metrics](operations/metrics.md) | Monitoring and metrics |
| [Security Scanning](operations/SECURITY_SCANNING.md) | Security scanning setup |

### :material-clipboard-check: Planning
Project planning and tracking documents.

| Document | Description |
|----------|-------------|
| [Implementation Tracker](planning/IMPLEMENTATION_TRACKER.md) | Feature implementation status |
| [TODO Tracker](planning/TODO_TRACKER.md) | Outstanding tasks |
| [ChatGPT Feature Review](planning/CHATGPT_FEATURE_REVIEW.md) | Review of ChatGPT Codex and Pulse |
| [Parallel Priorities Evaluation](planning/PARALLEL_PRIORITIES_EVALUATION.md) | Parallel development evaluation |
| [Leadership Discussion Guide](planning/LEADERSHIP_DISCUSSION_GUIDE.md) | Strategic discussion guide |
| [Code Complexity Analysis](planning/CODE_COMPLEXITY_ANALYSIS.md) | Code complexity metrics |

### :material-archive: Archived
Historical documentation retained for reference.

| Document | Description |
|----------|-------------|
| [Celery Setup Summary](archived/CELERY_SETUP_SUMMARY.md) | Celery task queue setup |
| [Celery Configuration](archived/CELERY_CONFIGURATION_REPORT.md) | Celery configuration details |
| [Celery Production Checklist](archived/CELERY_PRODUCTION_CHECKLIST.md) | Production deployment checklist |
| [Celery Quick Reference](archived/CELERY_QUICK_REFERENCE.md) | Celery quick reference |

---

## Additional Resources

### :material-tools: Troubleshooting
[Troubleshooting Guide](troubleshooting.md) - Common issues and solutions

### :material-history: Changelog
[Changelog](changelog.md) - Version history and release notes

### :material-clipboard-text: Task Templates
Located in [tasks/templates/](tasks/templates/):
- [Beacon Test](tasks/templates/beacon-test.md) - System health verification
- [Cascade](tasks/templates/cascade.md) - Cascading updates
- [Consultation](tasks/templates/consultation.md) - Expert consultation template
- [Oracle Query](tasks/templates/oracle-query.md) - Knowledge base queries
- [Research](tasks/templates/research.md) - Research task template

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

Version: 1.0.0 | Last Updated: 2025-12-18

</div>
