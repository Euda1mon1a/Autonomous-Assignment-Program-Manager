# Development Guide

> **Last Updated:** 2025-12-26

This section contains information for developers working on the Residency Scheduler.

## AI-Assisted Development

The project includes a comprehensive Personal AI Infrastructure (PAI) with 34 skills, 27 slash commands, and 4 operational modes.

### Quick Start

- **[Personal AI Infrastructure (PAI)](../PERSONAL_INFRASTRUCTURE.md)** - Complete AI agent framework documentation
- **[AI Agent User Guide](../guides/AI_AGENT_USER_GUIDE.md)** - Skills, MCP tools, and Claude Code setup
- **[Agent Skills Reference](./AGENT_SKILLS.md)** - Complete catalog of 34 available skills
- **[AI Rules of Engagement](./AI_RULES_OF_ENGAGEMENT.md)** - Core rules for AI agents

### MCP & Integration

- **[MCP Admin Guide](../admin-manual/mcp-admin-guide.md)** - MCP server administration
- **[MCP IDE Integration](../MCP_IDE_INTEGRATION.md)** - VSCode and Zed setup for MCP tools
- **[Agent Instructions](./AGENTS.md)** - AI background monitoring guidelines

### Slash Commands (27 Available)

| Category | Commands |
|----------|----------|
| **Development** | `/run-tests`, `/write-tests`, `/lint-fix`, `/fix-code`, `/review-code` |
| **Debugging** | `/debug`, `/debug-explore`, `/debug-tdd`, `/debug-scheduling` |
| **Scheduling** | `/generate-schedule`, `/verify-schedule`, `/check-compliance`, `/swap` |
| **Infrastructure** | `/db-migrate`, `/docker-help`, `/health-check` |
| **Operations** | `/review-pr`, `/incident`, `/security` |

### Agent Skills (34 Available)

| Tier | Skills |
|------|--------|
| **Core Scheduling** | SCHEDULING, COMPLIANCE_VALIDATION, SWAP_EXECUTION, RESILIENCE_SCORING |
| **Development** | test-writer, code-review, automated-code-fixer, systematic-debugger |
| **Infrastructure** | database-migration, docker-containerization, fastapi-production |
| **Operations** | production-incident-responder, security-audit, solver-control |

## Topics

- [Architecture Overview](../architecture/index.md) - System design
- [Setup Guide](./setup.md) - Development environment setup
- [Contributing Guidelines](./contributing.md) - Contribution guidelines
- [API Documentation](../api/index.md) - REST API reference

## Performance & Optimization

- [N+1 Query Optimization Guide](./N1_QUERY_OPTIMIZATION.md) - SQLAlchemy eager loading patterns
- [Implementation Verification](./IMPLEMENTATION_VERIFICATION.md) - Testing and verification checklist

## Type Safety

- [TypedDict Type Safety Guide](./TYPEDDICT_TYPE_SAFETY.md) - Typed dictionary patterns for better IDE support

## Testing

- [Testing Guide](./testing.md) - pytest and Jest testing practices
- [CI/CD Recommendations](./CI_CD_RECOMMENDATIONS.md) - Continuous integration setup
- [CI/CD Troubleshooting](./CI_CD_TROUBLESHOOTING.md) - Error codes and fixes

## Debugging

- [Debugging Workflow](./DEBUGGING_WORKFLOW.md) - Systematic debugging methodology
- [Parallel Claude Best Practices](./PARALLEL_CLAUDE_BEST_PRACTICES.md) - Multi-agent coordination

## Advanced Topics

- [Cross-Disciplinary Bridges](../architecture/bridges/) - Integration specifications
- [Service Specifications](../specs/) - Implementation-ready service designs
- [Research Directory](../research/) - Advanced research topics

