***REMOVED*** Code Style

Coding standards and conventions.

---

***REMOVED******REMOVED*** Python

***REMOVED******REMOVED******REMOVED*** Formatting

- **Black** for code formatting
- **Ruff** for linting
- **MyPy** for type checking

```bash
***REMOVED*** Format
black .

***REMOVED*** Lint
ruff check .

***REMOVED*** Type check
mypy app
```

***REMOVED******REMOVED******REMOVED*** Conventions

```python
***REMOVED*** Type hints required
def get_person(person_id: UUID) -> Person:
    ...

***REMOVED*** Docstrings for public functions
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

***REMOVED******REMOVED*** TypeScript

***REMOVED******REMOVED******REMOVED*** Formatting

- **ESLint** for linting
- **Prettier** for formatting

```bash
npm run lint
npm run lint:fix
```

***REMOVED******REMOVED******REMOVED*** Conventions

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

***REMOVED******REMOVED*** Pre-commit Hooks

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
