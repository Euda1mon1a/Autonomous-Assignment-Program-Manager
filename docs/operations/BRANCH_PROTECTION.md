# Branch Protection Rules

> **Last Updated:** 2025-12-31
> **Purpose:** Define branch protection policies, required checks, and merge requirements

---

## Table of Contents

1. [Overview](#overview)
2. [Protected Branches](#protected-branches)
3. [Required Status Checks](#required-status-checks)
4. [Review Requirements](#review-requirements)
5. [Merge Requirements](#merge-requirements)
6. [Branch Naming Conventions](#branch-naming-conventions)
7. [Exemptions](#exemptions)
8. [Configuration](#configuration)

---

## Overview

### Purpose

Branch protection ensures quality and prevents accidental merges of broken code to production-ready branches.

### Enforcement

These rules are enforced at the GitHub repository level:
- Push protection (direct pushes blocked)
- PR requirement (all changes via PR)
- Status check gates (CI/CD must pass)
- Review gates (human approval required)

---

## Protected Branches

### Main Branch (`main`)

**Status:** Fully Protected

**Characteristics:**
- Production-ready code only
- Releases created from this branch
- All commits must be via PR
- Cannot be deleted

**Protection Rules:**
```
✓ Require pull request reviews: Yes (1 required)
✓ Require status checks to pass: Yes (all)
✓ Require branches to be up to date: Yes
✓ Require code review before merge: Yes
✓ Require approval of reviewers: 1 minimum
✓ Require CODEOWNERS review: Yes
✓ Allow auto-merge: No
✓ Allow deletions: No
✓ Allow force pushes: No
```

### Master Branch (`master`)

**Status:** Fully Protected (if exists)

**Same rules as `main`** (legacy support)

### Develop Branch (`develop`)

**Status:** Protected (slightly relaxed)

**Characteristics:**
- Integration branch for features
- Merges to `main` regularly
- Can be more experimental

**Protection Rules:**
```
✓ Require pull request reviews: Yes (1 required)
✓ Require status checks to pass: Yes (core only)
✓ Require branches to be up to date: Yes
✓ Allow auto-merge: Yes
✓ Allow deletions: No
✓ Allow force pushes: No
```

### Feature Branches (Non-protected)

**Status:** Unprotected (free-form development)

**Examples:**
- `feat/dark-mode`
- `fix/double-booking-issue`
- `docs/update-readme`
- `claude/**` (AI-generated branches)

**Characteristics:**
- Individual developer control
- No merge restrictions
- Can be deleted freely
- Require PR to merge to protected branches

---

## Required Status Checks

### All PRs Require These Checks

These checks must pass before a PR can be merged:

#### Hard Gates (Blocking)

| Check | Failure Behavior | Details |
|-------|------------------|---------|
| **Linting** | Blocks PR | Ruff errors, ESLint errors |
| **Type Checking** | Blocks PR (Frontend) | TypeScript errors only |
| **Unit Tests** | Blocks PR | pytest or Jest failures |
| **Coverage** | Blocks PR | Below threshold (80%/70%) |
| **Build** | Blocks PR | Build step failures |
| **Secrets** | Blocks PR | Gitleaks detection |
| **Code Quality** | Blocks PR | Merge conflict markers, etc. |

#### Soft Gates (Informational)

| Check | Failure Behavior | Details |
|-------|------------------|---------|
| **Type Checking (Backend)** | Pass with warning | MyPy findings (not blocking) |
| **Security Scans** | Pass with warning | Bandit, npm audit (non-critical) |
| **E2E Tests** | Pass with warning | Optional for some PRs |
| **Documentation** | Pass with warning | Can be addressed post-merge |

### Status Check Configuration

**Current Configuration:**

```yaml
# Required status checks
required_status_checks:
  strict: true  # Must be up to date with base branch
  contexts:
    # Linting
    - "Backend - Ruff Linting"
    - "Frontend - ESLint & Prettier"

    # Type Checking
    - "Frontend - Type Checking (TypeScript)"

    # Tests & Coverage
    - "Backend - Tests & Coverage"
    - "Frontend - Tests & Coverage"

    # Code Quality
    - "Code Quality Checks"
    - "Build Verification"

    # Security
    - "Secrets Detection"

    # Summary
    - "Quality Gate Enforcement"
```

### Local Pre-merge Verification

Before pushing, verify locally:

```bash
# Backend
cd backend
pytest --cov=app --cov-report=term-missing
ruff check .
ruff format --check .
mypy app/ --ignore-missing-imports

# Frontend
cd frontend
npm test
npm run lint
npm run type-check

# General
grep -r "<<<<<<< HEAD" src/ || echo "✓ No merge conflicts"
```

---

## Review Requirements

### Approval Requirements

| Requirement | Setting | Notes |
|------------|---------|-------|
| **Minimum Reviewers** | 1 | At least one approval |
| **CODEOWNERS** | Enabled | Code owners must approve |
| **Dismiss Reviews** | Enabled | Stale reviews dismissed on new commits |
| **Require Updated Branch** | Yes | Must be up-to-date with base |

### Who Can Approve

**Code Owners** (from `.github/CODEOWNERS`):

```
# Core Backend
backend/app/                    @team-backend
backend/alembic/                @team-backend @team-devops

# Frontend
frontend/src/                   @team-frontend
frontend/public/                @team-frontend

# Documentation
docs/                           @team-docs
CHANGELOG.md                    @team-leads

# Configuration
.github/                        @team-devops
docker-compose.yml              @team-devops
.env.example                    @team-devops
```

### Review Process

1. **Author:** Creates PR with description
2. **CI/CD:** Automated checks run
3. **Reviewers:** At least 1 code owner reviews
4. **Discussion:** Address feedback in comments
5. **Approval:** Reviewer approves changes
6. **Merge:** Author merges (if permissions allow)

### Large PR Handling

**Definition:** >400 lines changed (excluding tests/docs)

**Requirement:** Split into smaller PRs

**Exception:** Coordinated refactoring with team agreement

---

## Merge Requirements

### What Can Be Merged

**Allowed:**
- ✓ All status checks passing
- ✓ Approved by 1+ code owner
- ✓ Branch up to date with base
- ✓ No merge conflicts
- ✓ All conversations resolved

**Blocked:**
- ✗ Failing status checks
- ✗ Missing approvals
- ✗ Outdated with base branch
- ✗ Unresolved conversations
- ✗ Secrets detected

### Merge Strategy

**Default:** Squash and merge

**Rationale:**
- Cleaner history on `main`
- Single logical change = single commit
- Easier to revert if needed
- Simplified bisect for debugging

**Commit Message Format:**

```
<type>(<scope>): <subject>

<body (optional)>

<footer (optional)>

Closes #<issue_number>
```

**Example:**
```
feat(scheduling): Add constraint for supervisor fatigue

Add new constraint to prevent scheduling supervisors for >80 hours in
rolling 4-week period, reducing burnout risk and improving safety.

Implements requirement from ACGME guidelines section 4.2.1.
Includes 12 new unit tests covering edge cases.

Closes #247
```

### Merge Options

| Option | Behavior | Use Case |
|--------|----------|----------|
| **Squash Merge** | Single commit | Default for feature PRs |
| **Rebase Merge** | Linear history | Small hotfixes only |
| **Merge Commit** | Creates merge commit | Coordinated team merges |

---

## Branch Naming Conventions

### Branch Name Format

```
<type>/<scope>-<description>

type:      feat | fix | refactor | chore | docs | test | ci | hotfix
scope:     Component or area (optional for chore/docs)
description: Kebab-case, descriptive
```

### Examples

**Feature Branches:**
```
feat/schedule-export-pdf
feat/acgme-compliance-dashboard
feat/rotation-swap-system
```

**Bug Fix Branches:**
```
fix/double-booking-issue
fix/work-hour-calculation
fix/timezone-offset-bug
```

**Refactoring:**
```
refactor/service-layer-cleanup
refactor/database-query-optimization
```

**Documentation:**
```
docs/api-endpoints
docs/deployment-guide
docs/troubleshooting
```

**Chores (Maintenance):**
```
chore/update-dependencies
chore/ci-workflow-improvements
chore/docker-optimization
```

**Testing:**
```
test/add-edge-case-coverage
test/e2e-swap-scenarios
```

### AI-Generated Branches

**Special prefix:** `claude/**`

```
claude/review-feature-request
claude/optimize-scheduler
claude/session-025-tasks
```

---

## Exemptions

### When to Bypass Protection

**Only in emergencies** (critical production issues)

**Process:**
1. Notify team in Slack
2. Create issue with severity label
3. Brief explanation in PR
4. Request emergency approval
5. Document decision

**Allowed Bypasses:**
- Direct push to `main` (requires branch protection override)
- Disable required checks (temporary, max 24 hours)
- Bypass review requirement (requires 2 approvals instead of 1)

**Not Allowed:**
- Force push to `main`
- Disable all checks without review
- Merge without CI passing

### When Bypass Was Used

| Date | Reason | Outcome | Follow-up |
|------|--------|---------|-----------|
| (Track in HUMAN_TODO.md) | | | |

---

## Configuration

### GitHub UI Setup

**Path:** Repository Settings → Branches → Protected Branches

**For `main` branch:**

1. **Basic Settings:**
   - Require pull request reviews: ✓
   - Number of approvals: 1
   - Include administrators: ✓

2. **Advanced:**
   - Require review from CODEOWNERS: ✓
   - Require branches to be up to date: ✓
   - Require status checks to pass: ✓

3. **Push Rules:**
   - Require branches to be up to date: ✓
   - Allow force pushes: ✗
   - Allow deletions: ✗

### Terraform Configuration (If Using)

```hcl
# main branch protection
resource "github_branch_protection" "main" {
  repository_id = github_repository.repo.id
  pattern       = "main"

  require_signed_commits = false
  enforce_admins         = true
  require_linear_history = false

  required_status_checks {
    strict   = true
    contexts = [
      "Backend - Ruff Linting",
      "Frontend - ESLint & Prettier",
      "Backend - Tests & Coverage",
      "Frontend - Tests & Coverage",
      "Code Quality Checks",
      "Secrets Detection",
      "Quality Gate Enforcement"
    ]
  }

  required_pull_request_reviews {
    dismiss_stale_reviews           = true
    require_code_owner_reviews      = true
    required_approving_review_count = 1
  }
}
```

### Verification

To verify protection is correctly configured:

```bash
# Using GitHub CLI
gh api repos/{owner}/{repo}/branches/main/protection

# Check protection status
gh api repos/{owner}/{repo}/branches/main --jq '.protected'
```

---

## Quick Reference

### For Feature Developers

```bash
# 1. Create feature branch
git checkout -b feat/my-feature

# 2. Make changes and test locally
npm test        # Frontend
pytest          # Backend

# 3. Verify pre-commit hooks pass
pre-commit run --all-files

# 4. Push and create PR
git push origin feat/my-feature
# Then create PR on GitHub

# 5. Wait for CI to pass (green checks)

# 6. Request review and get approval

# 7. Merge when ready
```

### For Code Reviewers

```bash
# Review checklist
- [ ] Code matches style guide
- [ ] Tests included and comprehensive
- [ ] No security concerns
- [ ] Documentation updated
- [ ] Backwards compatible (if applicable)
- [ ] Addresses the issue

# Approve (comment: "Approved!" or use GitHub approve)
```

### For Release Manager

```bash
# Merge to main
git checkout main
git pull origin main
git merge --squash origin/feat/my-feature
git commit -m "feat: Description"
git push origin main

# Create release tag
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

---

## Related Documentation

- [QUALITY_GATES.md](QUALITY_GATES.md) - Quality requirements
- [CLAUDE.md](../../CLAUDE.md) - Development workflow
- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches)

---

*Last updated: 2025-12-31*
*Maintained by: DevOps & Development Team*
