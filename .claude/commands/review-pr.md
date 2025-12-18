<!--
Review a pull request with comprehensive analysis.
Usage: /review-pr <PR_NUMBER>
-->

Review pull request #$ARGUMENTS with comprehensive analysis:

1. Fetch the PR details using GitHub CLI
2. Review the code changes
3. Check for common issues
4. Run relevant tests
5. Provide a structured review

Execute these checks:

```bash
cd /home/user/Autonomous-Assignment-Program-Manager

# Get PR information
gh pr view $ARGUMENTS

# Get PR diff
gh pr diff $ARGUMENTS

# Check out the PR branch locally (optional)
gh pr checkout $ARGUMENTS

# Run tests on the PR branch
cd backend
pytest -v

# Run linting checks
ruff check app/ tests/
black app/ tests/ --check

# Check for ACGME compliance if relevant
pytest -m acgme -v
```

Provide a comprehensive review covering:

## Code Quality
- [ ] Code follows project style guidelines (Black, Ruff)
- [ ] No linting errors or warnings
- [ ] Type hints are present and correct
- [ ] Variable and function names are clear and descriptive

## Testing
- [ ] All tests pass
- [ ] New code has appropriate test coverage
- [ ] ACGME compliance tests pass (if relevant)
- [ ] Integration tests pass (if relevant)

## Architecture & Design
- [ ] Changes align with ARCHITECTURE.md
- [ ] No violations of separation of concerns
- [ ] Database migrations are included (if schema changes)
- [ ] API endpoints follow RESTful conventions

## Security & Compliance
- [ ] No hardcoded credentials or secrets
- [ ] Input validation is present
- [ ] ACGME compliance rules not violated
- [ ] Audit trail requirements met (if applicable)

## Documentation
- [ ] Code comments explain complex logic
- [ ] README or docs updated (if needed)
- [ ] CHANGELOG.md updated (if needed)
- [ ] API documentation current

## Specific Concerns
- Check for N+1 query issues in database operations
- Verify proper error handling and logging
- Ensure async/await usage is correct
- Check for resource cleanup (DB connections, file handles)
- Validate timezone handling for scheduling operations

Provide specific, actionable feedback with line numbers and code suggestions where applicable.
