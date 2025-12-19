***REMOVED*** Contributing to Residency Scheduler

Thank you for your interest in contributing to the Residency Scheduler project! This guide will help you get started with development and ensure your contributions align with project standards.

> **Important**: This is a scheduling application. All contributions must maintain security, privacy, and ACGME compliance standards.

---

***REMOVED******REMOVED*** Table of Contents

- [Development Environment](***REMOVED***development-environment)
- [Code Style](***REMOVED***code-style)
- [Testing Requirements](***REMOVED***testing-requirements)
- [Pull Request Process](***REMOVED***pull-request-process)
- [Architecture Guidelines](***REMOVED***architecture-guidelines)
- [Getting Help](***REMOVED***getting-help)

---

***REMOVED******REMOVED*** Development Environment

***REMOVED******REMOVED******REMOVED*** Fork and Clone

1. **Fork the repository** on GitHub
   - Click "Fork" in the top-right corner
   - This creates a copy under your GitHub account

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Autonomous-Assignment-Program-Manager.git
   cd Autonomous-Assignment-Program-Manager
   ```

3. **Add upstream remote** (to sync with the main repository)
   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/Autonomous-Assignment-Program-Manager.git
   git fetch upstream
   ```

***REMOVED******REMOVED******REMOVED*** Install Dependencies

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend Setup

```bash
cd backend

***REMOVED*** Create and activate virtual environment
python -m venv venv
source venv/bin/activate  ***REMOVED*** On Windows: venv\Scripts\activate

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Set up environment variables
cp ../.env.example ../.env
***REMOVED*** Edit .env with your configuration (see below)

***REMOVED*** Run database migrations
alembic upgrade head
```

**Required Environment Variables** (`.env`):

```bash
***REMOVED*** Database
DATABASE_URL=postgresql://scheduler:scheduler@localhost:5432/residency_scheduler

***REMOVED*** Security (generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))')
SECRET_KEY=your-secret-key-at-least-32-chars
WEBHOOK_SECRET=your-webhook-secret-at-least-32-chars

***REMOVED*** Redis
REDIS_URL=redis://localhost:6379/0

***REMOVED*** Development mode
ENVIRONMENT=development
DEBUG=true
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend Setup

```bash
cd frontend

***REMOVED*** Install dependencies
npm install

***REMOVED*** Set up environment variables
cp .env.example .env.local
***REMOVED*** Edit .env.local with your configuration

***REMOVED*** Generate types from OpenAPI schema (optional)
npm run generate-types
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker Setup (Recommended)

```bash
***REMOVED*** Start all services (backend, frontend, database, Redis)
docker-compose up -d

***REMOVED*** View logs
docker-compose logs -f

***REMOVED*** Access services:
***REMOVED*** - Backend API: http://localhost:8000
***REMOVED*** - Frontend: http://localhost:3000
***REMOVED*** - API Docs: http://localhost:8000/docs
```

***REMOVED******REMOVED******REMOVED*** Run Tests Locally

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend Tests

```bash
cd backend

***REMOVED*** Run all tests
pytest

***REMOVED*** Run with coverage report
pytest --cov=app --cov-report=html

***REMOVED*** Run specific test file
pytest tests/test_swap_executor.py

***REMOVED*** Run tests matching a pattern
pytest -k "test_acgme"

***REMOVED*** Run with verbose output
pytest -v

***REMOVED*** Run ACGME compliance tests only
pytest -m acgme
```

**Coverage Report**: After running with coverage, open `htmlcov/index.html` in your browser.

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend Tests

```bash
cd frontend

***REMOVED*** Run all tests
npm test

***REMOVED*** Run with coverage
npm run test:coverage

***REMOVED*** Run tests in watch mode (during development)
npm test -- --watch

***REMOVED*** Run tests for specific file
npm test -- src/components/Schedule.test.tsx

***REMOVED*** Type checking
npm run type-check

***REMOVED*** Linting
npm run lint
npm run lint:fix
```

***REMOVED******REMOVED******REMOVED*** Verify Your Setup

```bash
***REMOVED*** Backend: Start development server
cd backend
uvicorn app.main:app --reload
***REMOVED*** Visit http://localhost:8000/docs to see API documentation

***REMOVED*** Frontend: Start development server
cd frontend
npm run dev
***REMOVED*** Visit http://localhost:3000 to see the application
```

---

***REMOVED******REMOVED*** Code Style

***REMOVED******REMOVED******REMOVED*** Python (Backend)

We follow **PEP 8** with some modifications:

- **Line length**: Max 100 characters (not 79)
- **Type hints required**: All function signatures must include types
- **Docstrings required**: Google-style docstrings for all public functions/classes

***REMOVED******REMOVED******REMOVED******REMOVED*** Style Guidelines

```python
"""Service for managing schedule assignments."""
from datetime import date, datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.assignment import Assignment
from app.schemas.assignment import AssignmentCreate, AssignmentUpdate


async def create_assignment(
    db: Session,
    assignment_data: AssignmentCreate,
    created_by: str
) -> Assignment:
    """
    Create a new schedule assignment.

    Args:
        db: Database session
        assignment_data: Validated assignment data
        created_by: ID of user creating the assignment

    Returns:
        Assignment: Created assignment instance

    Raises:
        ValueError: If assignment conflicts with existing assignments
        ConflictError: If ACGME compliance would be violated
    """
    ***REMOVED*** Validate compliance
    if not await _validate_acgme_compliance(db, assignment_data):
        raise ValueError("Assignment would violate ACGME rules")

    ***REMOVED*** Create assignment
    assignment = Assignment(
        person_id=assignment_data.person_id,
        block_id=assignment_data.block_id,
        rotation_id=assignment_data.rotation_id,
        created_by=created_by
    )

    db.add(assignment)
    await db.commit()
    await db.refresh(assignment)

    return assignment
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `SwapExecutor`, `ACGMEValidator` |
| Functions/Methods | snake_case | `create_assignment`, `validate_compliance` |
| Constants | UPPER_SNAKE_CASE | `MAX_HOURS_PER_WEEK`, `REDIS_URL` |
| Private methods | Prefix with `_` | `_calculate_utilization` |
| Database models | Singular | `Person`, `Assignment` (not `People`) |

***REMOVED******REMOVED******REMOVED******REMOVED*** Async/Await

**Always use async/await** for database operations:

```python
***REMOVED*** ✅ Good
async def get_person(db: AsyncSession, person_id: str) -> Optional[Person]:
    result = await db.execute(
        select(Person).where(Person.id == person_id)
    )
    return result.scalar_one_or_none()

***REMOVED*** ❌ Bad - synchronous
def get_person(db: Session, person_id: str) -> Optional[Person]:
    return db.query(Person).filter(Person.id == person_id).first()
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Import Organization

Organize imports in three groups, separated by blank lines:

```python
***REMOVED*** 1. Standard library
import os
from datetime import datetime
from typing import Optional, List

***REMOVED*** 2. Third-party packages
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

***REMOVED*** 3. Local imports
from app.models.person import Person
from app.schemas.person import PersonCreate, PersonResponse
from app.api.deps import get_db, get_current_user
```

***REMOVED******REMOVED******REMOVED*** TypeScript (Frontend)

We enforce **strict TypeScript** with ESLint and Prettier:

***REMOVED******REMOVED******REMOVED******REMOVED*** Style Guidelines

```typescript
// Component with explicit props interface
interface ScheduleCardProps {
  scheduleId: string;
  date: Date;
  onEdit?: (id: string) => void;
  className?: string;
}

export function ScheduleCard({
  scheduleId,
  date,
  onEdit,
  className = ''
}: ScheduleCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleEdit = useCallback(() => {
    if (onEdit) {
      onEdit(scheduleId);
    }
  }, [scheduleId, onEdit]);

  return (
    <div className={`schedule-card ${className}`}>
      {/* Component content */}
    </div>
  );
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** TypeScript Rules

- **No `any` type**: Use proper types or `unknown`
- **Explicit return types**: For all exported functions
- **Interface over type**: Use `interface` for object types
- **Strict null checks**: Handle `null` and `undefined` explicitly

```typescript
// ✅ Good
interface User {
  id: string;
  name: string;
  email: string | null; // Explicit null handling
}

async function fetchUser(id: string): Promise<User | null> {
  const response = await fetch(`/api/users/${id}`);
  if (!response.ok) return null;
  return response.json();
}

// ❌ Bad
async function fetchUser(id: any): Promise<any> {
  const response = await fetch(`/api/users/${id}`);
  return response.json();
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** React Best Practices

```typescript
// Use functional components with hooks
export function MyComponent() {
  // State
  const [data, setData] = useState<Data | null>(null);

  // Derived state (use useMemo for expensive calculations)
  const filteredData = useMemo(
    () => data?.filter(item => item.active),
    [data]
  );

  // Effects
  useEffect(() => {
    fetchData();
  }, []);

  // Event handlers (use useCallback to prevent re-renders)
  const handleClick = useCallback(() => {
    // Handle click
  }, []);

  return <div>{/* JSX */}</div>;
}
```

***REMOVED******REMOVED******REMOVED*** Commit Message Format

We use **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)
- `perf`: Performance improvements
- `ci`: CI/CD changes

***REMOVED******REMOVED******REMOVED******REMOVED*** Examples

```bash
***REMOVED*** Simple feature
feat: add email notification system

***REMOVED*** Feature with scope
feat(scheduling): implement N-1 contingency analysis

***REMOVED*** Bug fix with issue reference
fix(auth): resolve JWT token expiration bug

Fixes token refresh logic that was causing premature logouts.

Closes ***REMOVED***123

***REMOVED*** Breaking change
feat(api): redesign swap request endpoint

BREAKING CHANGE: The `/swaps` endpoint now requires `swap_type`
in the request body. Update all client code accordingly.

***REMOVED*** Multiple changes
refactor(backend): improve database query performance

- Add selectinload for person assignments
- Optimize ACGME compliance checks
- Cache frequently accessed rotation data

Reduces average API response time by 40%.
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Commit Message Rules

1. **Subject line**: Max 72 characters, imperative mood ("add" not "added")
2. **Body**: Wrap at 100 characters, explain *what* and *why* (not *how*)
3. **Footer**: Reference issues/PRs (e.g., `Closes ***REMOVED***123`, `Relates to ***REMOVED***456`)
4. **Breaking changes**: Must include `BREAKING CHANGE:` in footer

---

***REMOVED******REMOVED*** Testing Requirements

**All code changes must include tests.** Do not submit PRs without test coverage.

***REMOVED******REMOVED******REMOVED*** Backend Testing (pytest)

***REMOVED******REMOVED******REMOVED******REMOVED*** Coverage Thresholds

- **Overall coverage**: Minimum 80%
- **New code**: Minimum 90% coverage
- **Critical paths** (auth, ACGME, scheduling): 95%+ coverage

***REMOVED******REMOVED******REMOVED******REMOVED*** Test Structure

```python
"""Tests for swap executor service."""
import pytest
from datetime import date, timedelta
from sqlalchemy.orm import Session

from app.services.swap_executor import SwapExecutor
from app.models.swap import SwapRequest, SwapType
from app.models.person import Person


class TestSwapExecutor:
    """Test suite for swap execution logic."""

    @pytest.fixture
    def swap_executor(self):
        """Create swap executor instance."""
        return SwapExecutor()

    @pytest.fixture
    async def sample_swap_request(self, db: Session) -> SwapRequest:
        """Create a sample swap request for testing."""
        person_a = Person(
            id="person-a",
            name="Dr. Alice",
            role="FACULTY"
        )
        person_b = Person(
            id="person-b",
            name="Dr. Bob",
            role="FACULTY"
        )

        db.add_all([person_a, person_b])
        await db.commit()

        swap = SwapRequest(
            requester_id="person-a",
            target_id="person-b",
            swap_type=SwapType.ONE_TO_ONE,
            requester_block_id="block-1",
            target_block_id="block-2",
            status="pending"
        )

        db.add(swap)
        await db.commit()
        await db.refresh(swap)

        return swap

    async def test_execute_one_to_one_swap_success(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        sample_swap_request: SwapRequest
    ):
        """Test successful execution of one-to-one swap."""
        ***REMOVED*** Act
        result = await swap_executor.execute_swap(db, sample_swap_request)

        ***REMOVED*** Assert
        assert result.status == "completed"
        assert result.executed_at is not None

        ***REMOVED*** Verify assignments were swapped
        person_a_assignment = await db.get(Assignment, "assignment-a")
        person_b_assignment = await db.get(Assignment, "assignment-b")

        assert person_a_assignment.block_id == "block-2"
        assert person_b_assignment.block_id == "block-1"

    async def test_execute_swap_validation_failure(
        self,
        db: Session,
        swap_executor: SwapExecutor
    ):
        """Test swap execution fails with ACGME violation."""
        ***REMOVED*** Arrange: Create swap that would violate 80-hour rule
        invalid_swap = SwapRequest(
            requester_id="person-a",
            target_id="person-b",
            swap_type=SwapType.ONE_TO_ONE,
            requester_block_id="block-overloaded",
            target_block_id="block-2",
            status="pending"
        )

        ***REMOVED*** Act & Assert
        with pytest.raises(ValueError, match="ACGME compliance"):
            await swap_executor.execute_swap(db, invalid_swap)

        ***REMOVED*** Verify no changes were made
        assert invalid_swap.status == "pending"

    @pytest.mark.parametrize("swap_type,expected_status", [
        (SwapType.ONE_TO_ONE, "completed"),
        (SwapType.ABSORB, "completed"),
    ])
    async def test_execute_swap_by_type(
        self,
        db: Session,
        swap_executor: SwapExecutor,
        swap_type: SwapType,
        expected_status: str
    ):
        """Test swap execution for different swap types."""
        ***REMOVED*** Parametrized test implementation
        pass
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Pytest Markers

Use markers to categorize tests:

```python
@pytest.mark.acgme
async def test_80_hour_rule_validation():
    """Test ACGME 80-hour rule validation."""
    pass

@pytest.mark.slow
async def test_full_schedule_generation():
    """Test complete schedule generation (slow)."""
    pass

@pytest.mark.integration
async def test_api_endpoint_integration():
    """Test API endpoint with database."""
    pass
```

Run specific markers:
```bash
pytest -m acgme           ***REMOVED*** Only ACGME tests
pytest -m "not slow"      ***REMOVED*** Skip slow tests
pytest -m integration     ***REMOVED*** Only integration tests
```

***REMOVED******REMOVED******REMOVED*** Frontend Testing (Jest + React Testing Library)

***REMOVED******REMOVED******REMOVED******REMOVED*** Coverage Thresholds

```json
{
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 80,
      "lines": 80,
      "statements": 80
    }
  }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Test Structure

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ScheduleCard } from './ScheduleCard';

// Mock setup
const mockOnEdit = jest.fn();
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
  },
});

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('ScheduleCard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders schedule information correctly', () => {
    const date = new Date('2024-01-15');

    render(
      <ScheduleCard
        scheduleId="schedule-1"
        date={date}
        onEdit={mockOnEdit}
      />,
      { wrapper }
    );

    expect(screen.getByText('January 15, 2024')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument();
  });

  it('calls onEdit when edit button is clicked', async () => {
    render(
      <ScheduleCard
        scheduleId="schedule-1"
        date={new Date()}
        onEdit={mockOnEdit}
      />,
      { wrapper }
    );

    const editButton = screen.getByRole('button', { name: /edit/i });
    fireEvent.click(editButton);

    await waitFor(() => {
      expect(mockOnEdit).toHaveBeenCalledWith('schedule-1');
    });
  });

  it('displays loading state while fetching data', async () => {
    render(
      <ScheduleCard
        scheduleId="schedule-1"
        date={new Date()}
      />,
      { wrapper }
    );

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByTestId('loading-spinner')).not.toBeInTheDocument();
    });
  });

  it('handles error state gracefully', async () => {
    // Mock API error
    jest.spyOn(console, 'error').mockImplementation(() => {});

    render(
      <ScheduleCard
        scheduleId="invalid-id"
        date={new Date()}
      />,
      { wrapper }
    );

    await waitFor(() => {
      expect(screen.getByText(/error loading schedule/i)).toBeInTheDocument();
    });
  });
});
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Testing Best Practices

1. **Test user behavior**: Focus on what users see and do, not implementation details
2. **Use semantic queries**: Prefer `getByRole`, `getByLabelText` over `getByTestId`
3. **Test accessibility**: Ensure components work with screen readers
4. **Mock external dependencies**: API calls, timers, third-party libraries
5. **Clean up**: Reset mocks and state between tests

***REMOVED******REMOVED******REMOVED*** Pre-commit Checklist

Before committing, ensure:

```bash
***REMOVED*** Backend
cd backend
pytest --cov=app --cov-report=term-missing  ***REMOVED*** Check coverage
black app/ tests/                            ***REMOVED*** Format code
isort app/ tests/                            ***REMOVED*** Sort imports
mypy app/                                    ***REMOVED*** Type checking
flake8 app/ tests/                           ***REMOVED*** Linting

***REMOVED*** Frontend
cd frontend
npm test -- --coverage                       ***REMOVED*** Run tests with coverage
npm run type-check                           ***REMOVED*** TypeScript type checking
npm run lint                                 ***REMOVED*** ESLint
npm run format                               ***REMOVED*** Prettier formatting
```

---

***REMOVED******REMOVED*** Pull Request Process

***REMOVED******REMOVED******REMOVED*** Branch Naming

Use descriptive branch names with prefixes:

```bash
***REMOVED*** Feature branches
feature/add-email-notifications
feature/implement-n1-contingency

***REMOVED*** Bug fixes
bugfix/fix-swap-validation-error
bugfix/resolve-jwt-expiration

***REMOVED*** Documentation
docs/update-api-reference
docs/add-deployment-guide

***REMOVED*** Refactoring
refactor/optimize-database-queries
refactor/improve-scheduling-engine

***REMOVED*** Chores
chore/update-dependencies
chore/configure-ci-pipeline
```

***REMOVED******REMOVED******REMOVED*** Creating a Pull Request

1. **Update your fork** with latest changes:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   git push origin main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-new-feature
   ```

3. **Make your changes** and commit:
   ```bash
   ***REMOVED*** Stage changes
   git add .

   ***REMOVED*** Commit with conventional commit message
   git commit -m "feat: add email notification system"
   ```

4. **Push to your fork**:
   ```bash
   git push origin feature/my-new-feature
   ```

5. **Open a Pull Request** on GitHub

***REMOVED******REMOVED******REMOVED*** PR Template Requirements

Your PR description should include:

```markdown
***REMOVED******REMOVED*** Description
Brief description of changes (1-2 sentences).

***REMOVED******REMOVED*** Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)

***REMOVED******REMOVED*** Related Issues
Closes ***REMOVED***123
Relates to ***REMOVED***456

***REMOVED******REMOVED*** Changes Made
- Added email notification service
- Updated user model to include email preferences
- Added Celery task for sending notifications
- Created email templates

***REMOVED******REMOVED*** Testing
- [ ] All existing tests pass
- [ ] Added unit tests for new functionality
- [ ] Added integration tests
- [ ] Tested manually in development environment
- [ ] Coverage increased/maintained (check coverage report)

***REMOVED******REMOVED*** ACGME Compliance
- [ ] N/A - No scheduling changes
- [ ] Validated 80-hour rule compliance
- [ ] Validated 1-in-7 rule compliance
- [ ] Validated supervision ratios

***REMOVED******REMOVED*** Security
- [ ] No sensitive data exposed in logs or errors
- [ ] Input validation added for all new endpoints
- [ ] No hardcoded secrets or credentials
- [ ] Reviewed for SQL injection vulnerabilities
- [ ] Security best practices followed

***REMOVED******REMOVED*** Database Changes
- [ ] No database changes
- [ ] Migration created and tested (up and down)
- [ ] Updated models with proper relationships
- [ ] Backward compatible

***REMOVED******REMOVED*** Documentation
- [ ] Updated relevant documentation
- [ ] Added/updated docstrings
- [ ] Updated API documentation (if applicable)
- [ ] Updated CLAUDE.md (if applicable)

***REMOVED******REMOVED*** Screenshots (if applicable)
Before:
[Screenshot or N/A]

After:
[Screenshot or N/A]

***REMOVED******REMOVED*** Additional Notes
Any additional context, concerns, or discussion points.
```

***REMOVED******REMOVED******REMOVED*** Code Review Process

1. **Automated Checks**: All CI checks must pass before review
   - Tests (pytest, Jest)
   - Linting (flake8, ESLint)
   - Type checking (mypy, TypeScript)
   - Coverage thresholds
   - Security scans

2. **Review Requirements**:
   - At least 1 approval required
   - No unresolved comments
   - All requested changes addressed

3. **Reviewer Guidelines**:
   - Check for security issues (data leaks, SQL injection, etc.)
   - Verify tests cover edge cases
   - Ensure ACGME compliance if touching scheduling
   - Validate architecture patterns are followed
   - Check for performance implications

4. **Addressing Feedback**:
   ```bash
   ***REMOVED*** Make requested changes
   git add .
   git commit -m "refactor: address review feedback"
   git push origin feature/my-new-feature
   ```

***REMOVED******REMOVED******REMOVED*** CI Checks That Must Pass

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend CI

- **Tests**: All pytest tests pass
- **Coverage**: Minimum 80% overall, 90% on new code
- **Type checking**: `mypy` passes with no errors
- **Linting**: `flake8` passes
- **Formatting**: Code formatted with `black` and `isort`
- **Security**: Bandit security scan passes
- **Dependencies**: No known vulnerabilities in dependencies

***REMOVED******REMOVED******REMOVED******REMOVED*** Frontend CI

- **Tests**: All Jest tests pass
- **Coverage**: Minimum 80% on all metrics
- **Type checking**: `tsc --noEmit` passes
- **Linting**: ESLint passes with no errors
- **Formatting**: Prettier formatting applied
- **Build**: Production build succeeds

***REMOVED******REMOVED******REMOVED******REMOVED*** Integration CI

- **Docker build**: All containers build successfully
- **E2E tests**: Playwright tests pass (if applicable)
- **API compatibility**: OpenAPI schema validation

***REMOVED******REMOVED******REMOVED*** Merge Requirements

Before merging:

1. All CI checks pass
2. At least 1 approval from maintainer
3. No merge conflicts
4. Branch is up-to-date with main
5. All conversations resolved

**Squash and merge** is preferred for cleaner history.

---

***REMOVED******REMOVED*** Architecture Guidelines

***REMOVED******REMOVED******REMOVED*** Backend Layered Architecture

Follow strict separation of concerns:

```
API Route (FastAPI endpoint)
    ↓
Controller (request/response handling, validation)
    ↓
Service (business logic)
    ↓
Repository (data access, if used)
    ↓
Model (SQLAlchemy ORM)
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Example: Adding a New Feature

**1. Create Pydantic Schemas** (`backend/app/schemas/notification.py`):

```python
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class NotificationBase(BaseModel):
    recipient_id: str
    subject: str
    message: str
    notification_type: str

class NotificationCreate(NotificationBase):
    pass

class NotificationResponse(NotificationBase):
    id: str
    sent_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True
```

**2. Create/Update Model** (`backend/app/models/notification.py`):

```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import uuid

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_id = Column(String, ForeignKey("persons.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(String, nullable=False)
    notification_type = Column(String, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")

    recipient = relationship("Person", back_populates="notifications")
```

**3. Create Migration**:

```bash
alembic revision --autogenerate -m "Add notifications table"
alembic upgrade head
```

**4. Create Service** (`backend/app/services/notification_service.py`):

```python
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from typing import List

class NotificationService:
    async def create_notification(
        self,
        db: Session,
        notification_data: NotificationCreate
    ) -> Notification:
        """Create a new notification."""
        notification = Notification(**notification_data.dict())
        db.add(notification)
        await db.commit()
        await db.refresh(notification)
        return notification

    async def get_user_notifications(
        self,
        db: Session,
        user_id: str
    ) -> List[Notification]:
        """Get all notifications for a user."""
        result = await db.execute(
            select(Notification)
            .where(Notification.recipient_id == user_id)
            .order_by(Notification.sent_at.desc())
        )
        return result.scalars().all()
```

**5. Create Route** (`backend/app/api/routes/notifications.py`):

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.schemas.notification import NotificationCreate, NotificationResponse
from app.services.notification_service import NotificationService
from app.models.person import Person

router = APIRouter()

@router.post("/", response_model=NotificationResponse)
async def create_notification(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user)
):
    """Create a new notification."""
    service = NotificationService()
    notification = await service.create_notification(db, notification_data)
    return notification

@router.get("/my-notifications", response_model=List[NotificationResponse])
async def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: Person = Depends(get_current_user)
):
    """Get current user's notifications."""
    service = NotificationService()
    notifications = await service.get_user_notifications(db, current_user.id)
    return notifications
```

**6. Write Tests** (`backend/tests/test_notification_service.py`):

```python
import pytest
from app.services.notification_service import NotificationService
from app.schemas.notification import NotificationCreate

class TestNotificationService:
    async def test_create_notification(self, db):
        service = NotificationService()
        data = NotificationCreate(
            recipient_id="user-1",
            subject="Test",
            message="Test message",
            notification_type="email"
        )

        notification = await service.create_notification(db, data)

        assert notification.id is not None
        assert notification.status == "pending"

    async def test_get_user_notifications(self, db):
        ***REMOVED*** Test implementation
        pass
```

***REMOVED******REMOVED******REMOVED*** Frontend Component Patterns

***REMOVED******REMOVED******REMOVED******REMOVED*** Component Structure

```typescript
// components/ScheduleCard/ScheduleCard.tsx
import { useCallback } from 'react';
import { useScheduleData } from '@/hooks/useScheduleData';
import { Schedule } from '@/types/schedule';

interface ScheduleCardProps {
  scheduleId: string;
  onEdit?: (id: string) => void;
}

export function ScheduleCard({ scheduleId, onEdit }: ScheduleCardProps) {
  // 1. Data fetching
  const { data: schedule, isLoading, error } = useScheduleData(scheduleId);

  // 2. Event handlers
  const handleEdit = useCallback(() => {
    if (onEdit) {
      onEdit(scheduleId);
    }
  }, [scheduleId, onEdit]);

  // 3. Render logic
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  if (!schedule) return null;

  return (
    <div className="schedule-card">
      <h3>{schedule.title}</h3>
      <button onClick={handleEdit}>Edit</button>
    </div>
  );
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Directory Structure

```
frontend/src/
├── app/                    ***REMOVED*** Next.js app router pages
├── components/             ***REMOVED*** Reusable components
│   ├── ui/                ***REMOVED*** Base UI components
│   ├── features/          ***REMOVED*** Feature-specific components
│   └── layouts/           ***REMOVED*** Layout components
├── hooks/                 ***REMOVED*** Custom React hooks
├── lib/                   ***REMOVED*** Utilities and helpers
├── types/                 ***REMOVED*** TypeScript types
├── api/                   ***REMOVED*** API client functions
└── styles/                ***REMOVED*** Global styles
```

***REMOVED******REMOVED******REMOVED*** Database Change Process (Migrations)

**NEVER** modify database models without creating a migration.

***REMOVED******REMOVED******REMOVED******REMOVED*** Step-by-Step Process

1. **Modify the model**:
   ```python
   ***REMOVED*** backend/app/models/person.py
   class Person(Base):
       ***REMOVED*** ... existing fields ...
       middle_name = Column(String, nullable=True)  ***REMOVED*** New field
   ```

2. **Create migration**:
   ```bash
   cd backend
   alembic revision --autogenerate -m "Add middle_name to Person model"
   ```

3. **Review generated migration** (`backend/alembic/versions/xxxx_add_middle_name.py`):
   ```python
   def upgrade() -> None:
       op.add_column('persons', sa.Column('middle_name', sa.String(), nullable=True))

   def downgrade() -> None:
       op.drop_column('persons', 'middle_name')
   ```

4. **Test migration**:
   ```bash
   ***REMOVED*** Apply migration
   alembic upgrade head

   ***REMOVED*** Test rollback
   alembic downgrade -1

   ***REMOVED*** Re-apply
   alembic upgrade head
   ```

5. **Update Pydantic schemas** if needed:
   ```python
   ***REMOVED*** backend/app/schemas/person.py
   class PersonBase(BaseModel):
       ***REMOVED*** ... existing fields ...
       middle_name: Optional[str] = None
   ```

6. **Write tests** for the new field

7. **Commit both model and migration**:
   ```bash
   git add backend/app/models/person.py
   git add backend/alembic/versions/xxxx_add_middle_name.py
   git commit -m "feat: add middle_name field to Person model"
   ```

***REMOVED******REMOVED******REMOVED******REMOVED*** Migration Best Practices

- **Never edit applied migrations**: Create a new migration instead
- **Test both upgrade and downgrade**: Ensure rollback works
- **Consider data migration**: Add data transformation if needed
- **Add indexes**: For frequently queried columns
- **Maintain backward compatibility**: Use nullable for new required fields initially

---

***REMOVED******REMOVED*** Getting Help

***REMOVED******REMOVED******REMOVED*** Issue Templates

When creating an issue, use the appropriate template:

***REMOVED******REMOVED******REMOVED******REMOVED*** Bug Report Template

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

**Environment**
- OS: [e.g., Ubuntu 22.04]
- Browser: [e.g., Chrome 120]
- Backend version: [e.g., 1.2.0]
- Frontend version: [e.g., 1.2.0]

**Additional context**
Any other relevant information.
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Feature Request Template

```markdown
**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
How would you solve this problem?

**Alternatives Considered**
Other solutions you've considered.

**ACGME Impact**
Does this affect ACGME compliance? If yes, how?

**Security Considerations**
Any security or privacy concerns?

**Additional Context**
Mockups, examples, or other context.
```

***REMOVED******REMOVED******REMOVED*** Discussion Channels

- **GitHub Issues**: Bug reports, feature requests
- **GitHub Discussions**: General questions, ideas, show-and-tell
- **Pull Request Comments**: Code-specific questions

***REMOVED******REMOVED******REMOVED*** Documentation Resources

- **[README.md](../../README.md)**: Project overview and quick start
- **[CLAUDE.md](../../CLAUDE.md)**: Comprehensive development guidelines
- **[docs/](../../docs/)**: Full documentation
  - [Architecture](../architecture/): System design documentation
  - [API Reference](../api/): API endpoints and schemas
  - [User Guide](../user-guide/): End-user documentation
  - [Deployment](../deployment/): Deployment guides

***REMOVED******REMOVED******REMOVED*** Getting Unstuck

1. **Check existing documentation**: Most questions are answered in docs
2. **Search closed issues**: Your question may have been answered before
3. **Review similar code**: Look at existing patterns in the codebase
4. **Ask in discussions**: Create a discussion post for general questions
5. **Be specific**: Provide context, error messages, and what you've tried

***REMOVED******REMOVED******REMOVED*** Learning Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Next.js**: https://nextjs.org/docs
- **TanStack Query**: https://tanstack.com/query/latest
- **ACGME Requirements**: Internal documentation in `docs/compliance/`

---

***REMOVED******REMOVED*** Thank You!

Thank you for contributing to Residency Scheduler! Your efforts help improve healthcare scheduling and ensure resident well-being through ACGME-compliant schedules.

***REMOVED******REMOVED******REMOVED*** Recognition

Contributors are recognized in:
- Release notes for their contributions
- `CONTRIBUTORS.md` file (if applicable)
- Special thanks in documentation

***REMOVED******REMOVED******REMOVED*** Code of Conduct

We are committed to providing a welcoming and inclusive environment:

- **Be respectful**: Treat all contributors with respect
- **Be constructive**: Provide helpful feedback
- **Be patient**: Remember everyone is learning
- **Assume good intentions**: Give others the benefit of the doubt
- **Ask for help**: Don't be afraid to ask questions

***REMOVED******REMOVED******REMOVED*** Questions?

If you have questions about contributing that aren't covered here, please:

1. Check the [documentation](../../docs/)
2. Search [existing discussions](../../../discussions)
3. Create a new discussion post

Happy coding!
