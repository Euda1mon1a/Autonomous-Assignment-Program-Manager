***REMOVED*** File Ownership Matrix

This document defines ownership and responsibility for files in the `docs/development/` directory.

***REMOVED******REMOVED*** Overview

| File | Purpose | Primary Owner | Status |
|------|---------|---------------|--------|
| [README.md](./README.md) | Index and overview of developer docs | Development Team | Active |
| [environment-setup.md](./environment-setup.md) | Development environment configuration | DevOps / Development Team | Active |
| [architecture.md](./architecture.md) | Code architecture and design patterns | Tech Lead / Architects | Active |
| [workflow.md](./workflow.md) | Development workflow and branching | Development Team | Active |
| [testing.md](./testing.md) | Testing guidelines and best practices | QA / Development Team | Active |
| [code-style.md](./code-style.md) | Code style and conventions | Development Team | Active |
| [contributing.md](./contributing.md) | Contribution guidelines | Maintainers | Active |
| [FILE_OWNERSHIP.md](./FILE_OWNERSHIP.md) | This file - ownership matrix | Maintainers | Active |

---

***REMOVED******REMOVED*** Detailed File Ownership

***REMOVED******REMOVED******REMOVED*** README.md
- **Path**: `docs/development/README.md`
- **Purpose**: Main index for developer documentation, provides navigation and quick start information
- **Owner**: Development Team
- **Update Frequency**: When new documentation files are added
- **Dependencies**: All other files in this directory

***REMOVED******REMOVED******REMOVED*** environment-setup.md
- **Path**: `docs/development/environment-setup.md`
- **Purpose**: Comprehensive guide for setting up local development environment
- **Owner**: DevOps / Development Team
- **Update Frequency**: When dependencies or tooling changes
- **Dependencies**:
  - `docker-compose.yml`
  - `docker-compose.dev.yml`
  - `.env.example`
  - `backend/requirements.txt`
  - `frontend/package.json`

***REMOVED******REMOVED******REMOVED*** architecture.md
- **Path**: `docs/development/architecture.md`
- **Purpose**: Documents code architecture, design patterns, and system components
- **Owner**: Tech Lead / Architects
- **Update Frequency**: When architectural decisions are made or changed
- **Dependencies**:
  - `backend/app/` directory structure
  - `frontend/src/` directory structure
  - `docs/ARCHITECTURE.md` (main architecture doc)

***REMOVED******REMOVED******REMOVED*** workflow.md
- **Path**: `docs/development/workflow.md`
- **Purpose**: Defines development workflow, branching strategy, and CI/CD processes
- **Owner**: Development Team
- **Update Frequency**: When processes change
- **Dependencies**:
  - `.github/workflows/` (CI configuration)
  - Git configuration

***REMOVED******REMOVED******REMOVED*** testing.md
- **Path**: `docs/development/testing.md`
- **Purpose**: Testing guidelines, tools, and best practices
- **Owner**: QA / Development Team
- **Update Frequency**: When testing tools or practices change
- **Dependencies**:
  - `backend/tests/` test suite
  - `frontend/__tests__/` test suite
  - `frontend/e2e/` E2E tests
  - `backend/pyproject.toml` (pytest config)
  - `frontend/jest.config.js`

***REMOVED******REMOVED******REMOVED*** code-style.md
- **Path**: `docs/development/code-style.md`
- **Purpose**: Coding conventions, formatting rules, and style guidelines
- **Owner**: Development Team
- **Update Frequency**: When style guidelines change
- **Dependencies**:
  - `backend/pyproject.toml` (black, ruff, mypy config)
  - `frontend/.eslintrc.js`
  - `frontend/.prettierrc`

***REMOVED******REMOVED******REMOVED*** contributing.md
- **Path**: `docs/development/contributing.md`
- **Purpose**: Guidelines for contributing to the project
- **Owner**: Maintainers
- **Update Frequency**: When contribution processes change
- **Dependencies**:
  - All other documentation files
  - `CONTRIBUTING.md` (root level)

---

***REMOVED******REMOVED*** Ownership Roles

***REMOVED******REMOVED******REMOVED*** Development Team
- Responsible for keeping documentation accurate and up-to-date
- Reviews changes to documentation in PRs
- Ensures new features are documented

***REMOVED******REMOVED******REMOVED*** DevOps
- Maintains environment setup and deployment documentation
- Updates Docker and CI/CD related documentation

***REMOVED******REMOVED******REMOVED*** Tech Lead / Architects
- Maintains architectural documentation
- Reviews and approves architectural changes

***REMOVED******REMOVED******REMOVED*** QA
- Maintains testing documentation
- Ensures test coverage guidelines are followed

***REMOVED******REMOVED******REMOVED*** Maintainers
- Overall responsibility for all documentation
- Final approval on contribution guidelines
- Manages file ownership assignments

---

***REMOVED******REMOVED*** Update Process

1. **When to Update**
   - Code changes that affect documented behavior
   - New features or tools added
   - Processes or workflows change
   - Errors or outdated information discovered

2. **How to Update**
   - Create a branch: `docs/update-[filename]`
   - Make changes following the style guide
   - Submit PR with "docs" label
   - Request review from file owner

3. **Review Requirements**
   - All documentation changes require at least one review
   - Architectural changes require Tech Lead review
   - Contributing guidelines require Maintainer review

---

***REMOVED******REMOVED*** Document Status Definitions

| Status | Description |
|--------|-------------|
| **Active** | Current and maintained |
| **Draft** | In development, not ready for use |
| **Review** | Under review, pending approval |
| **Deprecated** | Outdated, scheduled for removal |
| **Archived** | Historical reference only |

---

***REMOVED******REMOVED*** Related Documentation

***REMOVED******REMOVED******REMOVED*** Root Level Documentation
| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `CONTRIBUTING.md` | Contribution guidelines (public-facing) |
| `CHANGELOG.md` | Version history |

***REMOVED******REMOVED******REMOVED*** Other Documentation Directories
| Directory | Purpose |
|-----------|---------|
| `docs/` | General documentation |
| `docs/api/` | API documentation |
| `docs/user-guide/` | User guides |
| `docs/admin-manual/` | Admin documentation |

---

***REMOVED******REMOVED*** Contact

For questions about file ownership or documentation:
- Open an issue with the "documentation" label
- Tag the relevant file owner in PR reviews

---

*Last Updated: December 2024*
