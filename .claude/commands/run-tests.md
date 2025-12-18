<!--
Run the pytest test suite for the residency scheduler backend.
Executes all tests with coverage reporting and verbose output.
-->

Run the complete pytest test suite for the residency scheduler backend:

1. Navigate to the backend directory
2. Run pytest with coverage reporting using the configured options from pyproject.toml
3. Display test results with verbose output including:
   - All test successes and failures
   - Coverage report for the app/ directory
   - Any warnings or deprecation notices
   - Summary of test markers (acgme, slow, integration)

Commands to execute:
```bash
cd /home/user/Autonomous-Assignment-Program-Manager/backend
pytest --cov=app --cov-report=term-missing --cov-report=html -v
```

After running tests:
- Report the total number of tests passed/failed
- Show the overall code coverage percentage
- Highlight any failed tests with their error messages
- Note if coverage falls below the 70% threshold configured in pyproject.toml
- Mention that detailed HTML coverage report is available in htmlcov/index.html

If you need to run specific test categories:
- ACGME compliance tests only: `pytest -m acgme`
- Skip slow tests: `pytest -m "not slow"`
- Integration tests only: `pytest -m integration`
