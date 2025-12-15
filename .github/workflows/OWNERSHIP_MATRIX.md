# GitHub Workflows File Ownership Matrix

This document defines the ownership and responsibility matrix for all CI/CD workflow files in the `.github/workflows/` directory.

## Ownership Matrix

| File | Purpose | Primary Owner | Secondary Owner | Review Required |
|------|---------|---------------|-----------------|-----------------|
| `ci.yml` | Continuous Integration - runs tests on PRs | DevOps Team | Backend/Frontend Teams | Yes |
| `cd.yml` | Continuous Deployment - staging/production | DevOps Team | Platform Team | Yes (2 reviewers) |
| `code-quality.yml` | Linting, type checking, formatting | DevOps Team | All Developers | Yes |
| `security.yml` | Security scanning (SAST, dependencies) | Security Team | DevOps Team | Yes |
| `dependabot-auto-merge.yml` | Auto-merge Dependabot PRs | DevOps Team | Security Team | Yes |

## File Descriptions

### ci.yml
- **Triggers**: Pull requests to main/master/develop, pushes to main/master
- **Jobs**: Backend tests (pytest), Frontend unit tests (Jest), Frontend E2E tests (Playwright)
- **Dependencies**: PostgreSQL service container
- **Artifacts**: Coverage reports

### cd.yml
- **Triggers**: Pushes to main/master, releases, manual dispatch
- **Jobs**: Build Docker images, deploy to staging, deploy to production, run migrations
- **Environments**: staging, production (with approval gates)
- **Dependencies**: GHCR for container registry

### code-quality.yml
- **Triggers**: Pull requests, pushes to main/master
- **Jobs**: Backend quality (ruff, black, mypy), Frontend quality (ESLint, TypeScript), Common checks
- **Purpose**: Enforce code standards and prevent technical debt

### security.yml
- **Triggers**: Pull requests, pushes, weekly schedule, manual dispatch
- **Jobs**: CodeQL, dependency scanning, Bandit, Trivy, secret scanning, Semgrep
- **Purpose**: Identify security vulnerabilities and prevent secrets leakage

### dependabot-auto-merge.yml
- **Triggers**: Dependabot pull requests
- **Purpose**: Auto-merge minor/patch dependency updates after CI passes

## Configuration Files

| File | Purpose |
|------|---------|
| `../dependabot.yml` | Dependabot configuration for automatic dependency updates |

## Responsibility Matrix (RACI)

| Task | DevOps | Security | Backend | Frontend | Platform |
|------|--------|----------|---------|----------|----------|
| CI Pipeline Maintenance | R/A | C | I | I | C |
| CD Pipeline Maintenance | R/A | C | I | I | R |
| Security Scanning Setup | C | R/A | I | I | C |
| Code Quality Rules | R | C | A | A | I |
| Dependency Updates | R/A | C | I | I | I |
| Production Deployments | R | C | I | I | A |

**Legend**: R = Responsible, A = Accountable, C = Consulted, I = Informed

## Change Management

### Making Changes to Workflows
1. Create a feature branch with descriptive name
2. Make changes and test locally where possible
3. Create PR with detailed description of changes
4. Request review from appropriate owners (see matrix above)
5. CD changes require 2 reviewers including Platform team
6. Security workflow changes require Security team approval
7. After approval, merge and monitor initial runs

### Emergency Changes
- For critical fixes, contact DevOps team lead directly
- Use `workflow_dispatch` to manually trigger workflows if needed
- Document emergency changes in post-incident review

## Secrets and Variables Required

### Repository Secrets
| Secret | Used By | Description |
|--------|---------|-------------|
| `CODECOV_TOKEN` | ci.yml | Code coverage reporting |
| `DATABASE_URL` | cd.yml | Database connection for migrations |
| `GITHUB_TOKEN` | All | Auto-provided by GitHub |
| `GITLEAKS_LICENSE` | security.yml | Gitleaks secret scanning (optional) |

### Environment Variables
| Variable | Environment | Description |
|----------|-------------|-------------|
| `STAGING_URL` | staging | Staging environment URL |
| `PRODUCTION_URL` | production | Production environment URL |
| `NEXT_PUBLIC_API_URL` | All | API URL for frontend |

## Monitoring and Alerts

- Failed CI runs: Notified via GitHub notifications
- Failed deployments: Notified via configured webhooks (Slack/Discord)
- Security findings: Visible in GitHub Security tab
- Dependabot PRs: Auto-created, labeled appropriately

---

*Last updated: December 2024*
*Maintained by: DevOps Team*
