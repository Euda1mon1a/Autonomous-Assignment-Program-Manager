# Development Workflow

This document describes the development workflow, branching strategy, and collaboration practices for the Residency Scheduler project.

## Table of Contents

1. [Git Workflow](#git-workflow)
2. [Branch Strategy](#branch-strategy)
3. [Development Process](#development-process)
4. [Pull Request Process](#pull-request-process)
5. [Release Process](#release-process)
6. [Continuous Integration](#continuous-integration)

---

## Git Workflow

### Getting Started

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/residency-scheduler.git
cd residency-scheduler

# 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/residency-scheduler.git

# 4. Verify remotes
git remote -v
# origin    https://github.com/YOUR_USERNAME/residency-scheduler.git (fetch)
# origin    https://github.com/YOUR_USERNAME/residency-scheduler.git (push)
# upstream  https://github.com/ORIGINAL_OWNER/residency-scheduler.git (fetch)
# upstream  https://github.com/ORIGINAL_OWNER/residency-scheduler.git (push)
```

### Keeping Your Fork Updated

```bash
# Fetch upstream changes
git fetch upstream

# Switch to main branch
git checkout main

# Merge upstream changes
git merge upstream/main

# Push to your fork
git push origin main
```

---

## Branch Strategy

### Branch Types

| Branch Type | Naming Convention | Purpose | Base Branch |
|-------------|-------------------|---------|-------------|
| Main | `main` | Production-ready code | - |
| Feature | `feature/<name>` | New functionality | `main` |
| Bugfix | `bugfix/<name>` | Bug fixes | `main` |
| Hotfix | `hotfix/<name>` | Critical production fixes | `main` |
| Release | `release/<version>` | Release preparation | `main` |
| Docs | `docs/<name>` | Documentation updates | `main` |
| Refactor | `refactor/<name>` | Code refactoring | `main` |

### Branch Naming Examples

```bash
# Features
feature/add-export-pdf
feature/dark-mode-toggle
feature/notification-system

# Bug fixes
bugfix/fix-assignment-overlap
bugfix/resolve-login-redirect
bugfix/correct-date-calculation

# Hotfixes
hotfix/critical-auth-fix
hotfix/data-corruption-fix

# Documentation
docs/update-api-reference
docs/add-deployment-guide

# Refactoring
refactor/simplify-validation
refactor/extract-scheduling-module
```

### Protected Branches

The `main` branch is protected:
- Direct pushes are not allowed
- Pull requests require approval
- CI checks must pass
- Branch must be up-to-date before merge

---

## Development Process

### Feature Development Workflow

```
1. Sync       2. Branch      3. Develop     4. Test       5. Push       6. PR
   ┌──┐         ┌──┐          ┌──┐          ┌──┐          ┌──┐         ┌──┐
   │  │ ──────▶ │  │ ───────▶ │  │ ───────▶ │  │ ───────▶ │  │ ──────▶ │  │
   └──┘         └──┘          └──┘          └──┘          └──┘         └──┘
   main        feature/       Write         Run           Push to      Open PR
   sync        create         code          tests         origin       for review
```

### Step-by-Step Process

#### 1. Sync with Upstream

```bash
# Ensure you have the latest changes
git fetch upstream
git checkout main
git merge upstream/main
```

#### 2. Create Feature Branch

```bash
# Create and switch to new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b bugfix/description-of-fix
```

#### 3. Make Changes

Follow the coding guidelines:
- Write clean, readable code
- Follow established patterns
- Add tests for new functionality
- Update documentation as needed

#### 4. Commit Changes

Use conventional commit messages:

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat(scheduling): add support for holiday blocks"

# Multiple commits are fine for larger features
git commit -m "test(scheduling): add holiday block test cases"
git commit -m "docs(scheduling): update API documentation for holidays"
```

#### 5. Test Your Changes

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests (if applicable)
npm run test:e2e
```

#### 6. Push to Your Fork

```bash
# Push feature branch
git push origin feature/your-feature-name
```

#### 7. Open Pull Request

Create a PR on GitHub from your feature branch to `upstream/main`.

---

## Pull Request Process

### PR Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts

### PR Title Format

Use conventional commit format for PR titles:

```
<type>(<scope>): <description>

Examples:
feat(auth): add password reset functionality
fix(schedule): resolve overlap detection bug
docs(api): update endpoint documentation
refactor(models): simplify person validation
test(hooks): add usePeople mutation tests
```

### PR Description Template

```markdown
## Summary
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

## Changes Made
- Change 1
- Change 2
- Change 3

## How Has This Been Tested?
Describe the tests you ran to verify your changes:
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Screenshots (if applicable)
Add screenshots for UI changes.

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

### Review Process

1. **Automated Checks**
   - CI runs tests automatically
   - Linting checks run
   - Build verification

2. **Code Review**
   - At least one maintainer reviews
   - Feedback addressed
   - Approval required

3. **Merge**
   - Squash and merge preferred
   - Delete branch after merge

### Addressing Review Feedback

```bash
# Make requested changes
git add .
git commit -m "fix: address review feedback"

# Or amend the last commit
git commit --amend

# Force push to update PR (only for your own branches)
git push origin feature/your-feature-name --force-with-lease
```

---

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

MAJOR - Breaking changes
MINOR - New features (backward compatible)
PATCH - Bug fixes (backward compatible)
```

### Release Steps

1. **Create Release Branch**
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b release/v1.2.0
   ```

2. **Update Version**
   - Update version in `backend/pyproject.toml`
   - Update version in `frontend/package.json`
   - Update `CHANGELOG.md`

3. **Final Testing**
   ```bash
   # Run full test suite
   cd backend && pytest
   cd ../frontend && npm test
   ```

4. **Create PR and Merge**
   - PR title: `release: v1.2.0`
   - Merge to main

5. **Tag Release**
   ```bash
   git checkout main
   git pull upstream main
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push upstream v1.2.0
   ```

6. **Create GitHub Release**
   - Use the tag
   - Add release notes from CHANGELOG

### Changelog Format

```markdown
# Changelog

## [1.2.0] - 2024-12-15

### Added
- New feature description (#PR_NUMBER)
- Another feature (#PR_NUMBER)

### Changed
- Changed functionality description (#PR_NUMBER)

### Fixed
- Bug fix description (#PR_NUMBER)

### Deprecated
- Deprecated feature notice

### Removed
- Removed feature description

### Security
- Security fix description
```

---

## Continuous Integration

### GitHub Actions Workflow

The project uses GitHub Actions for CI/CD:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend
          pytest --cov=app

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      - name: Run tests
        run: |
          cd frontend
          npm test -- --watchAll=false
      - name: Build
        run: |
          cd frontend
          npm run build

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Backend lint
        run: |
          cd backend
          pip install ruff black mypy
          ruff check .
          black --check .
      - name: Frontend lint
        run: |
          cd frontend
          npm ci
          npm run lint
```

### CI Checks

| Check | Backend | Frontend |
|-------|---------|----------|
| Unit Tests | pytest | Jest |
| Linting | ruff, black | ESLint |
| Type Checking | mypy | TypeScript |
| Build | - | next build |
| Coverage | pytest-cov | Jest coverage |

### Local CI Simulation

Run the same checks locally before pushing:

```bash
# Backend
cd backend
ruff check .
black --check .
mypy app
pytest --cov=app

# Frontend
cd frontend
npm run lint
npm test -- --watchAll=false
npm run build
```

---

## Best Practices

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Formatting (no code change)
- `refactor` - Code restructuring
- `test` - Adding/updating tests
- `chore` - Maintenance tasks
- `perf` - Performance improvements
- `ci` - CI/CD changes

**Examples:**
```bash
feat(scheduling): add support for night float rotations
fix(auth): resolve token refresh race condition
docs(api): update schedule endpoint documentation
test(compliance): add 80-hour rule validation tests
refactor(models): extract common validation logic
chore(deps): update FastAPI to 0.110.0
```

### Code Review Guidelines

**As a Reviewer:**
- Be constructive and specific
- Explain the "why" behind suggestions
- Approve promptly when satisfied
- Use "Request changes" sparingly

**As an Author:**
- Respond to all feedback
- Ask for clarification if needed
- Don't take criticism personally
- Thank reviewers for their time

### Communication

- Use GitHub issues for bug reports and feature requests
- Use PR comments for code-specific discussions
- Tag relevant people when needed
- Keep discussions focused and professional

---

## Further Reading

- [Environment Setup](./environment-setup.md) - Development environment
- [Architecture](./architecture.md) - Code structure
- [Testing](./testing.md) - Testing guidelines
- [Code Style](./code-style.md) - Coding conventions
- [Contributing](./contributing.md) - Contribution guidelines

---

*Last Updated: December 2024*
