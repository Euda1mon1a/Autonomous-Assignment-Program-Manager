# Code Style

Coding standards and conventions.

---

## Python

### Formatting

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
# Format
black .

# Lint
ruff check .

# Type check
mypy app
```

### Conventions

```python
# Type hints required
def get_person(person_id: UUID) -> Person:
    ...

# Docstrings for public functions
def generate_schedule(start_date: date, end_date: date) -> Schedule:
    """
    Generate a schedule for the given date range.

    Args:
        start_date: First day of schedule
        end_date: Last day of schedule

    Returns:
        Generated schedule with assignments
    """
    ...
```

---

## TypeScript

### Formatting

- **ESLint** for linting
- **Prettier** for formatting

```bash
npm run lint
npm run lint:fix
```

### Conventions

```typescript
// Explicit types for function parameters and returns
function calculateCompliance(
  assignments: Assignment[],
  person: Person
): ComplianceResult {
  ...
}

// Use interfaces for objects
interface Person {
  id: string;
  name: string;
  type: 'resident' | 'faculty';
}
```

---

## Pre-commit Hooks

Install hooks:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on commit:
- Ruff
- Black
- MyPy
- ESLint
