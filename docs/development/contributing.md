***REMOVED*** Contributing Guidelines

Thank you for your interest in contributing to Residency Scheduler! This document provides guidelines for contributing to the project.

***REMOVED******REMOVED*** Table of Contents

1. [Getting Started](***REMOVED***getting-started)
2. [Types of Contributions](***REMOVED***types-of-contributions)
3. [Development Process](***REMOVED***development-process)
4. [Pull Request Guidelines](***REMOVED***pull-request-guidelines)
5. [Code Review Process](***REMOVED***code-review-process)
6. [Issue Guidelines](***REMOVED***issue-guidelines)
7. [Community Standards](***REMOVED***community-standards)

---

***REMOVED******REMOVED*** Getting Started

***REMOVED******REMOVED******REMOVED*** Prerequisites

Before contributing, ensure you have:

- Git installed and configured
- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)
- A GitHub account

***REMOVED******REMOVED******REMOVED*** Setup Steps

1. **Fork the Repository**

   Click the "Fork" button on the GitHub repository page.

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/YOUR_USERNAME/residency-scheduler.git
   cd residency-scheduler
   ```

3. **Add Upstream Remote**

   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/residency-scheduler.git
   ```

4. **Set Up Development Environment**

   Follow the [Environment Setup Guide](./environment-setup.md) for detailed instructions.

   Quick start:
   ```bash
   cp .env.example .env
   docker compose up -d
   ```

5. **Verify Setup**

   - Frontend: http://localhost:3000
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

***REMOVED******REMOVED*** Types of Contributions

***REMOVED******REMOVED******REMOVED*** Code Contributions

- **Features**: New functionality that adds value to users
- **Bug Fixes**: Corrections to existing functionality
- **Performance**: Optimizations to improve speed or resource usage
- **Refactoring**: Code improvements without changing functionality

***REMOVED******REMOVED******REMOVED*** Non-Code Contributions

- **Documentation**: Improvements to docs, guides, or comments
- **Testing**: Adding or improving tests
- **Bug Reports**: Detailed reports of issues found
- **Feature Requests**: Well-thought-out proposals for new features
- **Code Reviews**: Reviewing other contributors' pull requests

***REMOVED******REMOVED******REMOVED*** First-Time Contributors

Look for issues labeled:
- `good first issue` - Simple issues for newcomers
- `help wanted` - Issues where we need community help
- `documentation` - Documentation improvements

---

***REMOVED******REMOVED*** Development Process

***REMOVED******REMOVED******REMOVED*** 1. Find or Create an Issue

Before starting work:

- **Search existing issues** to avoid duplicates
- **Comment on the issue** if you want to work on it
- **Create a new issue** if none exists for your contribution

***REMOVED******REMOVED******REMOVED*** 2. Create a Branch

```bash
***REMOVED*** Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

***REMOVED*** Create feature branch
git checkout -b feature/your-feature-name
```

***REMOVED******REMOVED******REMOVED*** 3. Make Changes

Follow our guidelines:

- **Code Style**: See [Code Style Guide](./code-style.md)
- **Architecture**: See [Architecture Overview](./architecture.md)
- **Testing**: See [Testing Guidelines](./testing.md)

***REMOVED******REMOVED******REMOVED*** 4. Test Your Changes

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

***REMOVED******REMOVED******REMOVED*** 5. Commit Changes

Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
git add .
git commit -m "feat(scheduling): add support for holiday blocks"
```

***REMOVED******REMOVED******REMOVED*** 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

---

***REMOVED******REMOVED*** Pull Request Guidelines

***REMOVED******REMOVED******REMOVED*** Before Submitting

Ensure your PR:

- [ ] Addresses a specific issue (link it in the PR description)
- [ ] Follows the code style guidelines
- [ ] Includes tests for new functionality
- [ ] Passes all existing tests
- [ ] Updates documentation if needed
- [ ] Has meaningful commit messages
- [ ] Is based on the latest `main` branch

***REMOVED******REMOVED******REMOVED*** PR Title Format

Use conventional commit format:

```
<type>(<scope>): <description>

Examples:
feat(auth): add password reset functionality
fix(schedule): resolve overlap detection bug
docs(api): update endpoint documentation
```

***REMOVED******REMOVED******REMOVED*** PR Description Template

```markdown
***REMOVED******REMOVED*** Summary

Brief description of what this PR does.

***REMOVED******REMOVED*** Related Issue

Fixes ***REMOVED***123

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

Describe the tests you ran:
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

***REMOVED******REMOVED******REMOVED*** PR Size Guidelines

- **Small PRs are preferred** - Easier to review and less likely to have issues
- **One logical change per PR** - Don't combine unrelated changes
- **Large features**: Break into smaller, incremental PRs when possible

---

***REMOVED******REMOVED*** Code Review Process

***REMOVED******REMOVED******REMOVED*** As a Contributor

1. **Respond to feedback promptly**
2. **Ask for clarification** if feedback is unclear
3. **Make requested changes** in new commits
4. **Re-request review** after addressing feedback

***REMOVED******REMOVED******REMOVED*** What Reviewers Look For

- **Correctness**: Does the code do what it's supposed to?
- **Tests**: Are there adequate tests?
- **Style**: Does it follow our conventions?
- **Performance**: Are there any performance concerns?
- **Security**: Are there any security implications?
- **Documentation**: Is it documented appropriately?

***REMOVED******REMOVED******REMOVED*** Responding to Reviews

```bash
***REMOVED*** Make changes based on feedback
git add .
git commit -m "fix: address review feedback"
git push origin feature/your-feature-name

***REMOVED*** Or amend the last commit (use carefully)
git commit --amend
git push origin feature/your-feature-name --force-with-lease
```

***REMOVED******REMOVED******REMOVED*** After Approval

- A maintainer will merge your PR
- Delete your feature branch
- Update your fork:
  ```bash
  git checkout main
  git pull upstream main
  git push origin main
  ```

---

***REMOVED******REMOVED*** Issue Guidelines

***REMOVED******REMOVED******REMOVED*** Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, browser, versions
6. **Screenshots**: If applicable
7. **Logs**: Relevant error messages

**Bug Report Template:**

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Actual behavior**
What actually happened.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11, macOS 14]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 1.0.0]

**Error logs**
```
Paste any error messages here
```

**Additional context**
Any other relevant information.
```

***REMOVED******REMOVED******REMOVED*** Feature Requests

When requesting features:

1. **Problem Statement**: What problem does this solve?
2. **Proposed Solution**: How do you envision it working?
3. **Alternatives Considered**: Other approaches you've thought of
4. **Additional Context**: Any other relevant information

**Feature Request Template:**

```markdown
**Problem Statement**
Describe the problem you're trying to solve.

**Proposed Solution**
Describe how you'd like this to work.

**Alternatives Considered**
Other approaches you've considered.

**Additional Context**
Any other relevant information.
```

***REMOVED******REMOVED******REMOVED*** Issue Labels

| Label | Description |
|-------|-------------|
| `bug` | Something isn't working |
| `feature` | New feature request |
| `enhancement` | Improvement to existing feature |
| `documentation` | Documentation improvements |
| `good first issue` | Good for newcomers |
| `help wanted` | Community help needed |
| `question` | Further information requested |
| `wontfix` | Will not be worked on |

---

***REMOVED******REMOVED*** Community Standards

***REMOVED******REMOVED******REMOVED*** Code of Conduct

We are committed to providing a welcoming and inclusive environment. All participants are expected to:

- **Be Respectful**: Use welcoming and inclusive language
- **Be Constructive**: Focus on what is best for the community
- **Be Collaborative**: Work together towards common goals
- **Be Patient**: Remember that everyone was a beginner once
- **Be Professional**: Keep discussions focused and on-topic

***REMOVED******REMOVED******REMOVED*** Communication Guidelines

- **Be Clear**: Write clear, concise messages
- **Be Specific**: Provide details when reporting issues
- **Be Kind**: Assume good intentions
- **Be Patient**: Allow time for responses

***REMOVED******REMOVED******REMOVED*** Unacceptable Behavior

- Harassment of any kind
- Discriminatory language or actions
- Personal attacks
- Trolling or deliberate disruption
- Publishing others' private information

***REMOVED******REMOVED******REMOVED*** Reporting Issues

If you experience or witness unacceptable behavior:

1. Document the incident
2. Report to project maintainers
3. Reports will be handled confidentially

---

***REMOVED******REMOVED*** Recognition

Contributors are recognized in several ways:

- **GitHub Contributors**: Your contributions appear in the repo
- **CHANGELOG**: Significant contributions are mentioned
- **Release Notes**: Feature contributors are credited

---

***REMOVED******REMOVED*** Getting Help

If you need help:

1. **Check Documentation**: Start with the docs in this folder
2. **Search Issues**: Look for similar questions
3. **Ask Questions**: Open an issue with the "question" label
4. **Be Patient**: Maintainers volunteer their time

---

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Common Commands

```bash
***REMOVED*** Setup
cp .env.example .env
docker compose up -d

***REMOVED*** Development
cd backend && source venv/bin/activate && uvicorn app.main:app --reload
cd frontend && npm run dev

***REMOVED*** Testing
cd backend && pytest
cd frontend && npm test

***REMOVED*** Formatting
cd backend && black . && ruff check .
cd frontend && npm run lint

***REMOVED*** Git
git checkout -b feature/your-feature
git commit -m "feat(scope): description"
git push origin feature/your-feature
```

***REMOVED******REMOVED******REMOVED*** Useful Links

- [Environment Setup](./environment-setup.md)
- [Architecture Overview](./architecture.md)
- [Development Workflow](./workflow.md)
- [Testing Guidelines](./testing.md)
- [Code Style Guide](./code-style.md)

---

Thank you for contributing to Residency Scheduler!

---

*Last Updated: December 2024*
