# Claude Code for macOS Guide

## Local Development with Claude CLI

This guide covers Claude Code (the CLI tool) for macOS, which provides capabilities not available in the browser-based Claude interface. Claude Code can execute commands, read/write files, run tests, and interact directly with your development environment.

---

## What is Claude Code?

Claude Code is Anthropic's official command-line interface that gives Claude direct access to:
- Your local file system
- Terminal/bash commands
- Git operations
- Package managers (npm, pip, etc.)
- Build tools and compilers
- Docker containers
- Local development servers

**Key Difference from Browser Claude:** Browser Claude can only discuss code. Claude Code can *execute* code, run tests, and make real changes to your project.

---

## Installation & Setup

### Prerequisites
- macOS 10.15 (Catalina) or later
- Node.js 18+ installed
- Anthropic API key

### Installation
```bash
# Install via npm
npm install -g @anthropic-ai/claude-code

# Or via Homebrew
brew install claude-code

# Verify installation
claude --version
```

### Configuration
```bash
# Set your API key
export ANTHROPIC_API_KEY="your-api-key"

# Or configure via CLI
claude config set api_key "your-api-key"

# Set preferred model (optional)
claude config set model "claude-sonnet-4-20250514"
```

---

## Model Selection for Local Development

### Recommended: Claude Sonnet 4 (Default Workhorse)

**Use Sonnet for:**
- Running tests and fixing failures
- Building and compiling code
- Implementing features
- Debugging runtime errors
- Git operations
- File modifications

**Why:** Sonnet provides the best balance of speed, cost, and capability for iterative development work.

### When to Use: Claude Opus 4.5 (Troubleshooting & Complex Issues)

**Escalate to Opus when:**
- Sonnet's fix attempts fail 2-3 times
- Complex debugging across multiple files
- Mysterious test failures with unclear causes
- Performance optimization requiring deep analysis
- Security vulnerability investigation
- Architecture-level refactoring decisions

**Why:** Opus has superior reasoning for complex, multi-step problems where Sonnet gets stuck.

### Model Usage Summary

| Task | Model | Reasoning |
|------|-------|-----------|
| Run tests | Sonnet | Fast iteration cycle |
| Fix failing tests | Sonnet | Standard debugging |
| Build errors | Sonnet | Usually straightforward |
| Implement features | Sonnet | Primary implementation |
| Complex debugging (after Sonnet fails) | Opus | Superior reasoning |
| Performance profiling | Opus | Requires deep analysis |
| Security audit | Opus | Critical thinking required |

---

## Core Capabilities

### 1. Executing Code & Commands

Claude Code can run any bash command in your terminal:

```
Run the test suite and show me failures
```
Claude will execute:
```bash
npm test
# or
pytest
# or
go test ./...
```

**Examples:**
```
Build the project and fix any errors
Run the linter and auto-fix what you can
Start the development server
Check which ports are in use
```

### 2. Reading & Writing Files

Claude Code has full read/write access to your project:

```
Read the main configuration file and explain what each setting does
```

```
Create a new component file at src/components/Button.tsx with proper TypeScript types
```

```
Update the API endpoint in lib/api.ts to use the new authentication header
```

### 3. Running Tests

**Run and Fix Pattern (Recommended):**
```
Run the test suite. If any tests fail, analyze the failures and fix them.
Continue until all tests pass.
```

**Specific Test Files:**
```
Run tests only for the scheduling module and fix any failures
```

**Watch Mode Monitoring:**
```
Run tests in watch mode. I'll work on the code and you monitor for failures.
```

### 4. Build & Compile

```
Build the project. If there are TypeScript errors, fix them one by one.
```

```
Run the production build and ensure no warnings or errors.
```

### 5. Git Operations

**Standard Workflow:**
```
Stage all changes, create a commit with a meaningful message based on what changed,
and push to the current branch.
```

**Branch Management:**
```
Create a new feature branch called "add-user-auth" and switch to it
```

**Review Changes:**
```
Show me a diff of all uncommitted changes and explain what they do
```

### 6. Docker Operations

```
Build the Docker image and run the container locally
```

```
Check if all required containers are running and show their logs
```

```
Run docker-compose up and wait for all services to be healthy
```

### 7. Package Management

```
Install the missing dependencies and update package-lock.json
```

```
Audit the packages for security vulnerabilities and update any that are fixable
```

---

## Development Workflows

### Workflow 1: Test-Driven Development

```
I want to add a function that validates email addresses.

1. First, write a test file with test cases for valid and invalid emails
2. Run the tests (they should fail)
3. Implement the function to make the tests pass
4. Run the tests again to confirm
```

### Workflow 2: Bug Fix with Verification

```
There's a bug where the schedule shows wrong dates on Sundays.

1. First, find the code that handles date display
2. Write a test that reproduces the bug
3. Fix the bug
4. Verify the test passes
5. Run the full test suite to check for regressions
```

### Workflow 3: Feature Implementation

```
I need to add a new API endpoint for bulk user import.

1. Read the existing API route structure
2. Create the new endpoint following the same patterns
3. Add validation for the CSV input
4. Write tests for success and error cases
5. Run tests and fix any issues
6. Update the API documentation
```

### Workflow 4: Debugging Session

**Start with Sonnet:**
```
The application crashes when I click "Save" on the form.
Check the error logs, find the issue, and fix it.
```

**Escalate to Opus if Sonnet struggles:**
```
Sonnet attempted to fix this 3 times but the issue persists.
Here's what was tried: [paste Sonnet's attempts]

Please analyze the root cause more deeply and suggest a fix.
```

---

## Project-Specific Commands

### For This Project (Residency Scheduler)

**Backend (Python/FastAPI):**
```
# Run backend tests
cd backend && pytest

# Run with coverage
cd backend && pytest --cov=app

# Start dev server
cd backend && uvicorn app.main:app --reload

# Run linter
cd backend && ruff check .

# Apply database migrations
cd backend && alembic upgrade head
```

**Frontend (Next.js):**
```
# Run frontend tests
cd frontend && npm test

# Build for production
cd frontend && npm run build

# Run linter
cd frontend && npm run lint

# Start dev server
cd frontend && npm run dev

# Type check
cd frontend && npx tsc --noEmit
```

**Docker:**
```
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Rebuild after changes
docker-compose up -d --build
```

### Example Prompts for This Project

**Test Everything:**
```
Run both backend and frontend tests. Fix any failures you find.
Start with backend pytest, then frontend npm test.
```

**Full Build Verification:**
```
Run a full build verification:
1. Backend: pytest with coverage
2. Frontend: npm run build
3. Docker: docker-compose build

Report any issues found.
```

**Pre-Commit Check:**
```
Before I commit, run:
1. Linters (ruff for backend, eslint for frontend)
2. Type checks (mypy for backend, tsc for frontend)
3. Full test suite

Fix any issues and let me know when it's clean.
```

---

## Troubleshooting Escalation Path

### Level 1: Sonnet (First Attempt)
```
[Describe the problem]
Investigate and fix it.
```

### Level 2: Sonnet (With Context)
```
I'm seeing [error/behavior].
I've already checked [what you checked].
Please investigate [specific file/area].
```

### Level 3: Opus (After Sonnet Failures)
```
This issue has resisted multiple fix attempts by Sonnet.

Problem: [description]
Symptoms: [what you observe]
Attempted fixes: [what Sonnet tried]
Files involved: [list]

Please perform a deeper analysis and identify the root cause.
```

### Level 4: Opus (Complex System Issue)
```
I need a comprehensive analysis of why [complex behavior].

This seems to involve:
- [component 1]
- [component 2]
- [component 3]

Please trace through the execution flow and identify where things go wrong.
```

---

## Best Practices

### Do's

1. **Be Specific About Success Criteria**
   ```
   Run tests and fix failures UNTIL all tests pass
   ```
   vs.
   ```
   Run tests  (Claude might stop after one fix attempt)
   ```

2. **Provide Context for Debugging**
   ```
   The error started appearing after I updated the auth library.
   Check if there are breaking changes.
   ```

3. **Use Iterative Approach**
   ```
   Fix one error at a time, running tests after each fix.
   ```

4. **Request Verification**
   ```
   After making the change, verify it works by running the relevant test.
   ```

### Don'ts

1. **Don't Ask to "Fix Everything" Without Limits**
   ```
   Bad: Fix all the code
   Good: Fix the type errors in src/components/
   ```

2. **Don't Skip the Verification Step**
   ```
   Bad: Add the new field to the database model
   Good: Add the new field and run migrations. Verify the schema updated correctly.
   ```

3. **Don't Ignore Cascading Failures**
   ```
   Bad: Just make the test pass
   Good: Make the test pass without breaking other tests
   ```

---

## Advanced Usage

### Background Tasks
```
Run the dev server in the background, then run the integration tests against it.
```

### Multi-Service Coordination
```
Start the backend and frontend in separate processes.
Wait for both to be healthy, then run the E2E tests.
```

### Environment Management
```
Check if .env.local exists. If not, copy .env.example and fill in the test values.
Then start the application.
```

### Log Analysis
```
The application threw an error. Check the last 100 lines of the log file at
/var/log/app.log and identify the root cause.
```

---

## Quick Reference Card

### Start Development Session
```
Start the development environment:
1. Check that dependencies are installed (npm install, pip install -r requirements.txt)
2. Start Docker services
3. Run database migrations
4. Start backend and frontend dev servers
```

### End Development Session
```
Before I stop:
1. Run the full test suite
2. Run linters
3. Show me uncommitted changes
4. Suggest a commit message
```

### Daily Standup Check
```
Give me a status on:
1. Any failing tests
2. Any linter warnings
3. Any outdated dependencies with security issues
4. Any TODO comments added recently
```

---

## Integration with Multi-Model Workflow

When using Claude Code as part of the multi-model orchestration system:

### Sonnet via Claude Code (Implementation)
Use Claude Code with Sonnet for all implementation tasks that require:
- Running commands
- Executing tests
- Making file changes
- Git operations

### Opus via Claude Code (Troubleshooting)
Switch to Opus model when:
```
claude --model claude-opus-4-5-20250514
```
Or within a session:
```
Switch to Opus model - I need deeper analysis on this issue.
```

### Haiku via Claude Code (Batch Operations)
For high-volume repetitive tasks:
```
claude --model claude-haiku-3-5-sonnet
```
Use for: generating boilerplate, bulk file creation, repetitive modifications.

---

## Security Considerations

### What Claude Code Can Access
- All files in your current directory and subdirectories
- Ability to run any bash command
- Network access (API calls, package downloads)
- Docker daemon (if available)

### Recommended Practices
1. Run Claude Code in project directories only
2. Review commands before confirmation when dealing with:
   - Production credentials
   - Database operations
   - Network-exposed services
3. Use `.claudeignore` to exclude sensitive files:
   ```
   .env
   .env.local
   credentials.json
   *.pem
   *.key
   ```

### Sandboxing (Optional)
For additional security, Claude Code can run in a sandboxed mode:
```
claude --sandbox
```
This restricts access to the current directory only.

---

*Last Updated: 2024-12-13*
*Version: 1.0*
