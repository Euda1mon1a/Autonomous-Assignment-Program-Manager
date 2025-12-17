# Development Guide

This guide covers how to set up a development environment, contribute to the project, and follow coding standards.

---

## Development Setup

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+ and **npm** 9+
- **PostgreSQL** 15
- **Redis** 7
- **Docker** and **Docker Compose** (optional but recommended)
- **Git**

### Clone Repository

```bash
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Copy environment file
cp .env.example .env
# Edit .env with your local settings

# Create database
createdb residency_scheduler

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Start Supporting Services

```bash
# Using Docker (recommended)
docker-compose up -d db redis

# Or start locally
# PostgreSQL: brew services start postgresql
# Redis: redis-server
```

---

## Project Structure

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── controllers/     # Request handlers
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Data access
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── core/            # Config, security
│   │   └── main.py          # App entry point
│   ├── alembic/             # Migrations
│   ├── tests/               # Backend tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js pages
│   │   ├── features/        # Feature modules
│   │   ├── components/      # Reusable components
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities
│   │   └── types/           # TypeScript types
│   ├── __tests__/           # Unit tests
│   └── e2e/                 # E2E tests
└── docs/                    # Documentation
```

---

## Coding Standards

### Python (Backend)

#### Style Guide
- Follow **PEP 8** style guide
- Use **Black** for code formatting
- Use **Ruff** for linting
- Use **mypy** for type checking

#### Running Linters

```bash
cd backend

# Format code
black app tests

# Lint code
ruff check app tests

# Type check
mypy app
```

#### Code Structure

```python
# Example service structure
from app.repositories.person_repository import PersonRepository
from app.schemas.person import PersonCreate, PersonResponse

class PersonService:
    """Service for managing people (residents/faculty)."""

    def __init__(self, repository: PersonRepository):
        self.repository = repository

    async def create_person(self, data: PersonCreate) -> PersonResponse:
        """Create a new person.

        Args:
            data: Person creation data

        Returns:
            Created person response

        Raises:
            ValueError: If email already exists
        """
        existing = await self.repository.get_by_email(data.email)
        if existing:
            raise ValueError(f"Email {data.email} already exists")

        person = await self.repository.create(data)
        return PersonResponse.model_validate(person)
```

### TypeScript (Frontend)

#### Style Guide
- Use **ESLint** for linting
- Use **Prettier** for formatting
- Use **TypeScript strict mode**

#### Running Linters

```bash
cd frontend

# Lint code
npm run lint

# Fix lint issues
npm run lint:fix

# Format code
npm run format
```

#### Code Structure

```typescript
// Example component structure
import { useState } from 'react';
import { usePeople } from '@/hooks/usePeople';
import type { Person } from '@/types/person';

interface PersonListProps {
  role?: 'resident' | 'faculty';
  onSelect?: (person: Person) => void;
}

export function PersonList({ role, onSelect }: PersonListProps) {
  const { data: people, isLoading } = usePeople({ role });

  if (isLoading) {
    return <div>Loading...</div>;
  }

  return (
    <ul>
      {people?.map((person) => (
        <li key={person.id} onClick={() => onSelect?.(person)}>
          {person.fullName}
        </li>
      ))}
    </ul>
  );
}
```

---

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_schedule_service.py

# Run specific test
pytest tests/test_schedule_service.py::test_generate_schedule

# Run tests matching pattern
pytest -k "schedule"

# Run ACGME compliance tests
pytest -m acgme

# Run with verbose output
pytest -v

# Run in parallel
pytest -n auto
```

#### Writing Tests

```python
# tests/test_person_service.py
import pytest
from app.services.person_service import PersonService
from app.schemas.person import PersonCreate

@pytest.fixture
def person_service(db_session):
    return PersonService(db_session)

@pytest.mark.asyncio
async def test_create_person(person_service):
    """Test creating a new person."""
    data = PersonCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        role="resident",
        pgy_level=2
    )

    result = await person_service.create_person(data)

    assert result.id is not None
    assert result.email == "john.doe@example.com"
    assert result.pgy_level == 2

@pytest.mark.asyncio
async def test_create_person_duplicate_email(person_service):
    """Test that duplicate email raises error."""
    data = PersonCreate(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        role="resident"
    )

    await person_service.create_person(data)

    with pytest.raises(ValueError, match="already exists"):
        await person_service.create_person(data)
```

### Frontend Tests

```bash
cd frontend

# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch

# Run specific test file
npm test -- PersonList.test.tsx

# Run E2E tests
npm run test:e2e

# Run E2E with UI
npm run test:e2e:ui
```

#### Writing Tests

```typescript
// __tests__/components/PersonList.test.tsx
import { render, screen } from '@testing-library/react';
import { PersonList } from '@/components/PersonList';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

const wrapper = ({ children }) => (
  <QueryClientProvider client={queryClient}>
    {children}
  </QueryClientProvider>
);

describe('PersonList', () => {
  it('renders loading state', () => {
    render(<PersonList />, { wrapper });
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders people list', async () => {
    render(<PersonList />, { wrapper });
    expect(await screen.findByText('John Doe')).toBeInTheDocument();
  });
});
```

---

## Database Migrations

### Creating Migrations

```bash
cd backend

# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column to person"

# Create empty migration
alembic revision -m "Custom migration"
```

### Running Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply next migration
alembic upgrade +1

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade abc123

# Show current revision
alembic current

# Show migration history
alembic history
```

### Migration Best Practices

1. **Always review** auto-generated migrations
2. **Test migrations** in development first
3. **Make migrations reversible** when possible
4. **Keep migrations small** and focused
5. **Never modify** applied migrations

---

## Git Workflow

### Branch Naming

```
feature/add-swap-matching
bugfix/fix-compliance-check
hotfix/security-patch
docs/update-api-docs
refactor/optimize-queries
```

### Commit Messages

Follow conventional commits:

```
feat: add swap auto-matching algorithm
fix: correct 80-hour rule calculation
docs: update API reference
test: add compliance validator tests
refactor: simplify schedule generator
chore: update dependencies
```

### Pull Request Process

1. Create feature branch from `main`
2. Make changes and commit
3. Push branch and create PR
4. Request review
5. Address feedback
6. Squash and merge

### Pre-commit Hooks

Install pre-commit hooks:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Configuration in `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

---

## API Development

### Adding a New Endpoint

1. **Create schema** in `app/schemas/`:

```python
# app/schemas/example.py
from pydantic import BaseModel

class ExampleCreate(BaseModel):
    name: str
    value: int

class ExampleResponse(BaseModel):
    id: int
    name: str
    value: int

    class Config:
        from_attributes = True
```

2. **Create model** in `app/models/`:

```python
# app/models/example.py
from sqlalchemy import Column, Integer, String
from app.db.base import Base

class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    value = Column(Integer, default=0)
```

3. **Create repository** in `app/repositories/`:

```python
# app/repositories/example_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.example import Example

class ExampleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Example:
        example = Example(**data)
        self.session.add(example)
        await self.session.commit()
        return example
```

4. **Create service** in `app/services/`:

```python
# app/services/example_service.py
from app.repositories.example_repository import ExampleRepository
from app.schemas.example import ExampleCreate, ExampleResponse

class ExampleService:
    def __init__(self, repository: ExampleRepository):
        self.repository = repository

    async def create(self, data: ExampleCreate) -> ExampleResponse:
        example = await self.repository.create(data.model_dump())
        return ExampleResponse.model_validate(example)
```

5. **Create route** in `app/api/routes/`:

```python
# app/api/routes/examples.py
from fastapi import APIRouter, Depends
from app.services.example_service import ExampleService
from app.schemas.example import ExampleCreate, ExampleResponse

router = APIRouter(prefix="/examples", tags=["examples"])

@router.post("/", response_model=ExampleResponse)
async def create_example(
    data: ExampleCreate,
    service: ExampleService = Depends()
):
    return await service.create(data)
```

6. **Register route** in `app/api/routes/__init__.py`:

```python
from app.api.routes import examples

def include_routers(app):
    app.include_router(examples.router)
```

7. **Create migration**:

```bash
alembic revision --autogenerate -m "Add examples table"
alembic upgrade head
```

8. **Add tests**:

```python
# tests/test_example_service.py
@pytest.mark.asyncio
async def test_create_example(example_service):
    result = await example_service.create(
        ExampleCreate(name="test", value=42)
    )
    assert result.name == "test"
```

---

## Debugging

### Backend Debugging

```bash
# Run with debug mode
DEBUG=true uvicorn app.main:app --reload

# Use debugger
python -m debugpy --listen 5678 -m uvicorn app.main:app --reload
```

VS Code launch configuration:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend Debugging

```bash
# Run with debugging
npm run dev

# Debug in browser DevTools
# Use React DevTools extension
# Use TanStack Query DevTools
```

### Database Debugging

```bash
# Connect to database
psql -U postgres -d residency_scheduler

# View recent queries (requires pg_stat_statements)
SELECT query, calls, mean_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Performance Optimization

### Backend Optimization

1. **Use async operations**:
```python
# Good
result = await repository.get_all()

# Avoid
result = repository.get_all()  # Blocking
```

2. **Batch database operations**:
```python
# Good
await session.execute(insert(Model).values(items))

# Avoid
for item in items:
    await repository.create(item)
```

3. **Use caching**:
```python
from fastapi_cache2.decorator import cache

@router.get("/expensive")
@cache(expire=300)
async def expensive_operation():
    return await compute_expensive_result()
```

### Frontend Optimization

1. **Use React Query caching**:
```typescript
const { data } = useQuery({
  queryKey: ['people'],
  queryFn: fetchPeople,
  staleTime: 5 * 60 * 1000,  // 5 minutes
});
```

2. **Memoize expensive computations**:
```typescript
const sortedData = useMemo(
  () => data?.sort((a, b) => a.name.localeCompare(b.name)),
  [data]
);
```

3. **Lazy load components**:
```typescript
const HeavyComponent = lazy(() => import('./HeavyComponent'));
```

---

## Documentation

### Writing Documentation

- Update wiki pages for user-facing changes
- Add JSDoc/docstrings for public APIs
- Include examples in documentation
- Keep CHANGELOG.md updated

### API Documentation

API docs are auto-generated from:
- Route decorators
- Pydantic schemas
- Docstrings

Access at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Getting Help

- **Questions**: Ask in team chat
- **Bugs**: Create GitHub issue
- **Feature requests**: Discuss in team meeting
- **Code review**: Request in PR

---

## Related Documentation

- [Getting Started](Getting-Started) - Setup guide
- [Architecture](Architecture) - System design
- [API Reference](API-Reference) - API docs
- [Troubleshooting](Troubleshooting) - Common issues
