***REMOVED*** Development Workflow

This document describes the development workflow, branching strategy, and collaboration practices for the Residency Scheduler project.

***REMOVED******REMOVED*** Table of Contents

1. [Git Workflow](***REMOVED***git-workflow)
2. [Branch Strategy](***REMOVED***branch-strategy)
3. [Development Process](***REMOVED***development-process)
4. [Pull Request Process](***REMOVED***pull-request-process)
5. [Release Process](***REMOVED***release-process)
6. [Continuous Integration](***REMOVED***continuous-integration)

---

***REMOVED******REMOVED*** Git Workflow

***REMOVED******REMOVED******REMOVED*** Getting Started

```bash
***REMOVED*** 1. Fork the repository on GitHub

***REMOVED*** 2. Clone your fork
git clone https://github.com/YOUR_USERNAME/residency-scheduler.git
cd residency-scheduler

***REMOVED*** 3. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/residency-scheduler.git

***REMOVED*** 4. Verify remotes
git remote -v
***REMOVED*** origin    https://github.com/YOUR_USERNAME/residency-scheduler.git (fetch)
***REMOVED*** origin    https://github.com/YOUR_USERNAME/residency-scheduler.git (push)
***REMOVED*** upstream  https://github.com/ORIGINAL_OWNER/residency-scheduler.git (fetch)
***REMOVED*** upstream  https://github.com/ORIGINAL_OWNER/residency-scheduler.git (push)
```

***REMOVED******REMOVED******REMOVED*** Keeping Your Fork Updated

```bash
***REMOVED*** Fetch upstream changes
git fetch upstream

***REMOVED*** Switch to main branch
git checkout main

***REMOVED*** Merge upstream changes
git merge upstream/main

***REMOVED*** Push to your fork
git push origin main
```

---

***REMOVED******REMOVED*** Branch Strategy

***REMOVED******REMOVED******REMOVED*** Branch Types

| Branch Type | Naming Convention | Purpose | Base Branch |
|-------------|-------------------|---------|-------------|
| Main | `main` | Production-ready code | - |
| Feature | `feature/<name>` | New functionality | `main` |
| Bugfix | `bugfix/<name>` | Bug fixes | `main` |
| Hotfix | `hotfix/<name>` | Critical production fixes | `main` |
| Release | `release/<version>` | Release preparation | `main` |
| Docs | `docs/<name>` | Documentation updates | `main` |
| Refactor | `refactor/<name>` | Code refactoring | `main` |

***REMOVED******REMOVED******REMOVED*** Branch Naming Examples

```bash
***REMOVED*** Features
feature/add-export-pdf
feature/dark-mode-toggle
feature/notification-system

***REMOVED*** Bug fixes
bugfix/fix-assignment-overlap
bugfix/resolve-login-redirect
bugfix/correct-date-calculation

***REMOVED*** Hotfixes
hotfix/critical-auth-fix
hotfix/data-corruption-fix

***REMOVED*** Documentation
docs/update-api-reference
docs/add-deployment-guide

***REMOVED*** Refactoring
refactor/simplify-validation
refactor/extract-scheduling-module
```

***REMOVED******REMOVED******REMOVED*** Protected Branches

The `main` branch is protected:
- Direct pushes are not allowed
- Pull requests require approval
- CI checks must pass
- Branch must be up-to-date before merge

---

***REMOVED******REMOVED*** Development Process

***REMOVED******REMOVED******REMOVED*** Feature Development Workflow

```
1. Sync       2. Branch      3. Develop     4. Test       5. Push       6. PR
   ┌──┐         ┌──┐          ┌──┐          ┌──┐          ┌──┐         ┌──┐
   │  │ ──────▶ │  │ ───────▶ │  │ ───────▶ │  │ ───────▶ │  │ ──────▶ │  │
   └──┘         └──┘          └──┘          └──┘          └──┘         └──┘
   main        feature/       Write         Run           Push to      Open PR
   sync        create         code          tests         origin       for review
```

***REMOVED******REMOVED******REMOVED*** Step-by-Step Process

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Sync with Upstream

```bash
***REMOVED*** Ensure you have the latest changes
git fetch upstream
git checkout main
git merge upstream/main
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Create Feature Branch

```bash
***REMOVED*** Create and switch to new branch
git checkout -b feature/your-feature-name

***REMOVED*** Or for bug fixes
git checkout -b bugfix/description-of-fix
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Make Changes

Follow the coding guidelines:
- Write clean, readable code
- Follow established patterns
- Add tests for new functionality
- Update documentation as needed

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Commit Changes

Use conventional commit messages:

```bash
***REMOVED*** Stage changes
git add .

***REMOVED*** Commit with descriptive message
git commit -m "feat(scheduling): add support for holiday blocks"

***REMOVED*** Multiple commits are fine for larger features
git commit -m "test(scheduling): add holiday block test cases"
git commit -m "docs(scheduling): update API documentation for holidays"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Test Your Changes

```bash
***REMOVED*** Backend tests
cd backend
pytest

***REMOVED*** Frontend tests
cd frontend
npm test

***REMOVED*** E2E tests (if applicable)
npm run test:e2e
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 6. Push to Your Fork

```bash
***REMOVED*** Push feature branch
git push origin feature/your-feature-name
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 7. Open Pull Request

Create a PR on GitHub from your feature branch to `upstream/main`.

---

***REMOVED******REMOVED*** Pull Request Process

***REMOVED******REMOVED******REMOVED*** PR Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up-to-date with main
- [ ] No merge conflicts

***REMOVED******REMOVED******REMOVED*** PR Title Format

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

***REMOVED******REMOVED******REMOVED*** PR Description Template

```markdown
***REMOVED******REMOVED*** Summary
Brief description of changes made.

***REMOVED******REMOVED*** Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

***REMOVED******REMOVED*** Changes Made
- Change 1
- Change 2
- Change 3

***REMOVED******REMOVED*** How Has This Been Tested?
Describe the tests you ran to verify your changes:
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

***REMOVED******REMOVED*** Screenshots (if applicable)
Add screenshots for UI changes.

***REMOVED******REMOVED*** Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
```

***REMOVED******REMOVED******REMOVED*** Review Process

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

***REMOVED******REMOVED******REMOVED*** Addressing Review Feedback

```bash
***REMOVED*** Make requested changes
git add .
git commit -m "fix: address review feedback"

***REMOVED*** Or amend the last commit
git commit --amend

***REMOVED*** Force push to update PR (only for your own branches)
git push origin feature/your-feature-name --force-with-lease
```

---

***REMOVED******REMOVED*** Release Process

***REMOVED******REMOVED******REMOVED*** Version Numbering

We follow [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

MAJOR - Breaking changes
MINOR - New features (backward compatible)
PATCH - Bug fixes (backward compatible)
```

***REMOVED******REMOVED******REMOVED*** Release Steps

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
   ***REMOVED*** Run full test suite
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

***REMOVED******REMOVED******REMOVED*** Changelog Format

```markdown
***REMOVED*** Changelog

***REMOVED******REMOVED*** [1.2.0] - 2024-12-15

***REMOVED******REMOVED******REMOVED*** Added
- New feature description (***REMOVED***PR_NUMBER)
- Another feature (***REMOVED***PR_NUMBER)

***REMOVED******REMOVED******REMOVED*** Changed
- Changed functionality description (***REMOVED***PR_NUMBER)

***REMOVED******REMOVED******REMOVED*** Fixed
- Bug fix description (***REMOVED***PR_NUMBER)

***REMOVED******REMOVED******REMOVED*** Deprecated
- Deprecated feature notice

***REMOVED******REMOVED******REMOVED*** Removed
- Removed feature description

***REMOVED******REMOVED******REMOVED*** Security
- Security fix description
```

---

***REMOVED******REMOVED*** Continuous Integration

***REMOVED******REMOVED******REMOVED*** GitHub Actions Workflow

The project uses GitHub Actions for CI/CD:

```yaml
***REMOVED*** .github/workflows/ci.yml
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

***REMOVED******REMOVED******REMOVED*** CI Checks

| Check | Backend | Frontend |
|-------|---------|----------|
| Unit Tests | pytest | Jest |
| Linting | ruff, black | ESLint |
| Type Checking | mypy | TypeScript |
| Build | - | next build |
| Coverage | pytest-cov | Jest coverage |

***REMOVED******REMOVED******REMOVED*** Local CI Simulation

Run the same checks locally before pushing:

```bash
***REMOVED*** Backend
cd backend
ruff check .
black --check .
mypy app
pytest --cov=app

***REMOVED*** Frontend
cd frontend
npm run lint
npm test -- --watchAll=false
npm run build
```

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** Commit Messages

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

***REMOVED******REMOVED******REMOVED*** Code Review Guidelines

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

***REMOVED******REMOVED******REMOVED*** Communication

- Use GitHub issues for bug reports and feature requests
- Use PR comments for code-specific discussions
- Tag relevant people when needed
- Keep discussions focused and professional

---

***REMOVED******REMOVED*** Further Reading

- [Environment Setup](./environment-setup.md) - Development environment
- [Architecture](./architecture.md) - Code structure
- [Testing](./testing.md) - Testing guidelines
- [Code Style](./code-style.md) - Coding conventions
- [Contributing](./contributing.md) - Contribution guidelines

---

*Last Updated: December 2024*
