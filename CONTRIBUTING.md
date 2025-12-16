# Contributing to Residency Scheduler

> **Last Updated:** 2025-12-16

Thank you for your interest in contributing to Residency Scheduler! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

---

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please be respectful, inclusive, and constructive in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

---

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Git installed and configured
- Docker and Docker Compose
- Node.js 20+ (for frontend development)
- Python 3.11+ (for backend development)
- A GitHub account

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/residency-scheduler.git
   cd residency-scheduler
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/residency-scheduler.git
   ```

---

## Development Setup

### Quick Start with Docker

```bash
# Copy environment file
cp .env.example .env

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f
```

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Set up database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Database Setup

The application requires PostgreSQL. With Docker:

```bash
docker-compose up -d postgres
```

Or install PostgreSQL locally and create a database:

```sql
CREATE DATABASE residency_scheduler;
CREATE USER scheduler WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;
```

---

## Code Style Guidelines

### Python (Backend)

We follow PEP 8 with these specifications:

- **Line length**: Maximum 100 characters
- **Imports**: Group by standard library, third-party, local; alphabetize within groups
- **Type hints**: Required for all function parameters and return types
- **Docstrings**: Google style for public functions and classes

```python
# Example function style
def calculate_hours(
    assignments: list[Assignment],
    start_date: date,
    end_date: date,
) -> float:
    """Calculate total hours for a date range.

    Args:
        assignments: List of assignment objects to process.
        start_date: Start of the calculation period.
        end_date: End of the calculation period.

    Returns:
        Total hours as a float.

    Raises:
        ValueError: If end_date is before start_date.
    """
    ...
```

**Tools**:
- `black` for code formatting
- `isort` for import sorting
- `flake8` for linting
- `mypy` for type checking

### TypeScript/JavaScript (Frontend)

- **Formatting**: Prettier with project configuration
- **Linting**: ESLint with Next.js rules
- **Components**: Functional components with TypeScript
- **Naming**:
  - Components: PascalCase (`UserProfile.tsx`)
  - Utilities: camelCase (`formatDate.ts`)
  - Constants: UPPER_SNAKE_CASE
  - Types/Interfaces: PascalCase with descriptive names

```typescript
// Example component style
interface UserCardProps {
  user: User;
  onSelect: (userId: number) => void;
  isActive?: boolean;
}

export function UserCard({ user, onSelect, isActive = false }: UserCardProps) {
  return (
    <div className={cn('card', isActive && 'card-active')}>
      {/* ... */}
    </div>
  );
}
```

### CSS/Styling

- Use TailwindCSS utility classes
- Extract common patterns to component classes
- Follow mobile-first responsive design
- Use CSS variables for theming

### Commit Messages

Follow the Conventional Commits specification:

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(scheduling): add support for holiday blocks
fix(auth): resolve token refresh race condition
docs(api): update endpoint documentation
test(compliance): add 80-hour rule validation tests
```

---

## Making Changes

### Branch Naming

Use descriptive branch names:

```
feature/add-export-pdf
bugfix/fix-assignment-overlap
docs/update-api-reference
refactor/simplify-validation
```

### Development Workflow

1. **Sync with upstream**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code following style guidelines
   - Add tests for new functionality
   - Update documentation as needed

4. **Test your changes**:
   ```bash
   # Backend tests
   cd backend && pytest

   # Frontend tests
   cd frontend && npm test

   # E2E tests
   cd frontend && npm run test:e2e
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat(scope): description of changes"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

---

## Pull Request Process

### Before Submitting

- [ ] All tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main

### PR Template

When creating a pull request, include:

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How Has This Been Tested?
Describe the tests you ran

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
- [ ] I have updated the documentation
```

### Review Process

1. Submit your PR against the `main` branch
2. Automated checks will run (tests, linting)
3. A maintainer will review your PR
4. Address any requested changes
5. Once approved, a maintainer will merge your PR

### After Merge

- Delete your feature branch
- Sync your fork with upstream

---

## Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Description**: Clear description of the bug
2. **Steps to Reproduce**: Detailed steps to reproduce the issue
3. **Expected Behavior**: What should happen
4. **Actual Behavior**: What actually happens
5. **Environment**: OS, browser, versions
6. **Screenshots**: If applicable
7. **Error Logs**: Relevant log output

**Bug Report Template**:
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

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g., Windows 11]
- Browser: [e.g., Chrome 120]
- Version: [e.g., 1.0.0]

**Additional context**
Any other context about the problem.
```

### Feature Requests

When requesting features:

1. **Description**: Clear description of the feature
2. **Use Case**: Why this feature would be useful
3. **Proposed Solution**: How you envision it working
4. **Alternatives**: Any alternatives you've considered

---

## Testing Guidelines

### Backend Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_scheduling_engine.py

# Run tests by marker
pytest -m acgme      # ACGME compliance tests
pytest -m unit       # Unit tests only
pytest -m integration # Integration tests
```

**Writing Backend Tests**:

```python
import pytest
from app.models import Person

class TestPersonModel:
    def test_create_resident(self, db_session):
        """Test creating a resident person."""
        person = Person(
            name="John Doe",
            email="john.doe@example.com",
            type="resident",
            pgy_level=1
        )
        db_session.add(person)
        db_session.commit()

        assert person.id is not None
        assert person.type == "resident"

    @pytest.mark.acgme
    def test_supervision_ratio(self, db_session):
        """Test PGY-1 supervision ratio requirement."""
        # Test ACGME supervision requirements
        ...
```

### Frontend Testing

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run E2E tests
npm run test:e2e

# Run E2E with UI
npm run test:e2e:ui
```

**Writing Frontend Tests**:

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { UserCard } from '@/components/UserCard';

describe('UserCard', () => {
  it('renders user name', () => {
    const user = { id: 1, name: 'John Doe', email: 'john@example.com' };
    render(<UserCard user={user} onSelect={jest.fn()} />);

    expect(screen.getByText('John Doe')).toBeInTheDocument();
  });

  it('calls onSelect when clicked', () => {
    const onSelect = jest.fn();
    const user = { id: 1, name: 'John Doe', email: 'john@example.com' };
    render(<UserCard user={user} onSelect={onSelect} />);

    fireEvent.click(screen.getByRole('button'));
    expect(onSelect).toHaveBeenCalledWith(1);
  });
});
```

### Test Coverage Requirements

- Minimum 70% code coverage for both frontend and backend
- New features must include tests
- Bug fixes should include regression tests

---

## Documentation

### When to Update Documentation

- Adding new features
- Changing existing behavior
- Adding new API endpoints
- Modifying configuration options
- Updating dependencies

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `CONTRIBUTING.md` | This file - contribution guidelines |
| `CHANGELOG.md` | Version history |
| `docs/SETUP.md` | Detailed setup instructions |
| `docs/API_REFERENCE.md` | API endpoint documentation |
| `docs/ARCHITECTURE.md` | System design documentation |

### API Documentation

Backend API documentation is auto-generated from code. Add docstrings to endpoints:

```python
@router.post("/generate", response_model=ScheduleResponse)
async def generate_schedule(
    request: ScheduleGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate a new schedule for the specified date range.

    - **start_date**: Beginning of the scheduling period
    - **end_date**: End of the scheduling period
    - **algorithm**: Scheduling algorithm to use (greedy, min_conflicts, cp_sat)

    Returns the generated schedule with compliance validation results.
    """
    ...
```

---

## Questions?

If you have questions about contributing:

1. Check existing documentation
2. Search existing issues
3. Open a new issue with the "question" label
4. Reach out to maintainers

Thank you for contributing to Residency Scheduler!
