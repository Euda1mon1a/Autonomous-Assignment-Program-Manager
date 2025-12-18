<!--
Run code linting and auto-fix issues using Black and Ruff.
Formats code and fixes common issues automatically.
-->

Run linting and auto-fix code quality issues:

1. Run Black to auto-format Python code (line length 88)
2. Run Ruff to check and auto-fix linting issues
3. Run mypy for type checking (informational only, no auto-fix)
4. Report all issues found and fixed

Execute these commands:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend

# Format code with Black
black app/ tests/ --line-length 88

# Auto-fix linting issues with Ruff
ruff check app/ tests/ --fix

# Check for remaining Ruff issues
ruff check app/ tests/

# Run type checking with mypy (optional, informational)
mypy app/ --python-version 3.11
```

After running linting:
- Report number of files formatted by Black
- List files modified by Ruff auto-fix
- Show any remaining Ruff violations that need manual fixing
- Highlight any critical type checking errors from mypy

Configuration is defined in `/home/user/Autonomous-Assignment-Program-Manager/backend/pyproject.toml`:
- Black: 88 character line length, Python 3.11 target
- Ruff: Enforces pycodestyle, Pyflakes, isort, flake8-bugbear, flake8-comprehensions, pyupgrade, flake8-simplify
- Mypy: Strict type checking with Pydantic plugin support

Key areas to check:
- Code formatting consistency
- Import sorting (isort via Ruff)
- Unused imports and variables
- Code complexity and comprehensions
- Type annotations completeness

If pre-commit hooks are configured, these checks run automatically on commit.
To run pre-commit manually:
```bash
cd /home/user/Autonomous-Assignment-Program-Manager
pre-commit run --all-files
```
