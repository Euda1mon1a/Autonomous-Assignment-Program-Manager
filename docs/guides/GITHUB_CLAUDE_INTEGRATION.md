# GitHub Claude Integration Guide

> **Last Updated:** 2025-12-18

This guide explains how to set up autonomous Claude integration with GitHub for automated code review, issue resolution, and development assistance.

---

## Table of Contents

1. [Overview](#overview)
2. [Setup Options](#setup-options)
3. [Quick Setup](#quick-setup-recommended)
4. [Manual Setup](#manual-setup)
5. [Advanced Enterprise Setup](#advanced-enterprise-setup)
6. [Required Secrets](#required-secrets)
7. [Workflow Triggers](#workflow-triggers)
8. [Using Claude in GitHub](#using-claude-in-github)
9. [Background Task Behavior](#background-task-behavior)
10. [Best Practices](#best-practices-for-this-project)
11. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Autonomous Claude GitHub Integration?

The Claude GitHub integration enables AI-powered autonomous assistance directly within your GitHub workflow. Claude can:

- **Review Pull Requests** - Analyze code changes, suggest improvements, identify potential issues
- **Resolve Issues** - Understand issue descriptions and implement solutions
- **Answer Questions** - Provide technical guidance on issues and PRs via comments
- **Automate Tasks** - Execute background tasks like running tests, generating documentation, refactoring code
- **Maintain Consistency** - Ensure code follows project conventions and best practices

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Autonomous Development** | Claude can implement features, fix bugs, and refactor code independently |
| **Code Review** | Automatic PR reviews with inline comments and suggestions |
| **Issue Triage** | Understands issue context and proposes solutions |
| **Documentation** | Generates and updates documentation based on code changes |
| **Testing** | Runs tests, interprets failures, and fixes broken tests |
| **Compliance Checking** | Validates code against project standards |

### How It Works

1. You mention `@claude` in a GitHub issue, PR comment, or review comment
2. GitHub triggers a workflow that invokes Claude via the Anthropic API
3. Claude analyzes the repository context, reads relevant files, and understands the request
4. Claude executes the task (code changes, analysis, documentation, etc.)
5. Claude responds with results, commits changes, or provides feedback
6. All actions are logged and can be monitored in GitHub Actions

---

## Setup Options

Choose the setup method that best fits your needs:

| Option | Best For | Setup Time | Customization |
|--------|----------|------------|---------------|
| **Quick Setup** | Individual developers, small teams | 5 minutes | Limited |
| **Manual Setup** | Teams with existing workflows | 15 minutes | Moderate |
| **Enterprise Setup** | Large organizations, custom requirements | 30+ minutes | Full control |

### Quick Setup (Recommended)

Use the Claude CLI to automatically configure the integration.

**Best for:** Getting started quickly, personal projects, small teams

**Pros:**
- Fastest setup
- Automatic configuration
- Pre-configured workflow templates
- Minimal manual steps

**Cons:**
- Uses standard GitHub App (shared with other users)
- Limited customization options

### Manual Setup

Configure the GitHub App and workflow files yourself.

**Best for:** Teams that want control over workflow configuration

**Pros:**
- More control over workflow triggers
- Customizable behavior
- Can integrate with existing CI/CD

**Cons:**
- Requires manual configuration
- Need to understand GitHub Actions

### Enterprise Setup

Create your own custom GitHub App with full control.

**Best for:** Large organizations, enterprise security requirements, custom branding

**Pros:**
- Complete control over permissions
- Custom branding and naming
- Private app installation
- Advanced security controls

**Cons:**
- Most complex setup
- Requires GitHub organization admin access
- Need to maintain app configuration

---

## Quick Setup (Recommended)

### Prerequisites

- Claude CLI installed (`npm install -g @anthropic-ai/claude-cli`)
- GitHub repository with admin access
- Anthropic API key with GitHub integration enabled

### Installation Steps

1. **Navigate to your repository**

```bash
cd /path/to/your/repository
```

2. **Run the installation command**

```bash
claude /install-github-app
```

3. **Follow the prompts**

The CLI will:
- Verify you have necessary GitHub permissions
- Install the Claude GitHub App to your repository
- Create `.github/workflows/claude.yml` workflow file
- Set up required repository secrets
- Test the configuration

4. **Authorize the integration**

When prompted:
- Click the authorization URL
- Review the requested permissions
- Click "Install" to authorize Claude access to your repository

5. **Configure the API key**

```bash
# The CLI will prompt you to add your Anthropic API key
# This is stored as a GitHub secret: ANTHROPIC_API_KEY
```

6. **Verify installation**

```bash
# Create a test issue
gh issue create --title "Test: @claude can you help?" --body "Just testing the integration"

# Claude should respond within 1-2 minutes
```

### What Gets Configured

The quick setup creates:

```
.github/
└── workflows/
    └── claude.yml          # Main workflow file
```

And sets these repository secrets:
- `ANTHROPIC_API_KEY` - Your Anthropic API key
- `CLAUDE_GITHUB_TOKEN` - GitHub token for Claude actions (auto-generated)

---

## Manual Setup

### Prerequisites

- GitHub repository with admin access
- Anthropic API key
- Basic understanding of GitHub Actions

### Step 1: Install the Claude GitHub App

1. Visit the [Claude GitHub App page](https://github.com/apps/claude-code)
2. Click "Install"
3. Select the repositories you want to enable
4. Review and accept the requested permissions
5. Click "Install"

### Step 2: Add Repository Secrets

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secret:

| Name | Value | Description |
|------|-------|-------------|
| `ANTHROPIC_API_KEY` | Your API key | Required for Claude API access |

To obtain an API key:
- Visit [console.anthropic.com](https://console.anthropic.com)
- Navigate to **API Keys**
- Click **Create Key**
- Copy the key (starts with `sk-ant-...`)
- Paste into GitHub secrets

### Step 3: Create Workflow File

Create `.github/workflows/claude.yml`:

```yaml
name: Claude Integration

on:
  # Trigger on issue comments
  issue_comment:
    types: [created, edited]

  # Trigger on PR review comments
  pull_request_review_comment:
    types: [created, edited]

  # Trigger on PR reviews
  pull_request_review:
    types: [submitted]

  # Trigger on issues with specific labels
  issues:
    types: [opened, labeled]

  # Optional: Auto-review PRs
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: write
  issues: write
  pull-requests: write
  checks: write

jobs:
  claude-assist:
    # Only run if @claude is mentioned OR if auto-review is enabled
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && contains(github.event.issue.labels.*.name, 'claude-assist')) ||
      (github.event_name == 'pull_request' && contains(github.event.pull_request.labels.*.name, 'auto-review'))

    runs-on: ubuntu-latest
    timeout-minutes: 30

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for better context

      - name: Set up Claude CLI
        run: |
          npm install -g @anthropic-ai/claude-cli
          claude --version

      - name: Configure Claude
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Claude CLI configuration
          claude config set api-key $ANTHROPIC_API_KEY

      - name: Run Claude
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Invoke Claude with GitHub context
          claude github-assist \
            --event-type "${{ github.event_name }}" \
            --event-payload "${{ toJson(github.event) }}" \
            --repository "${{ github.repository }}" \
            --run-id "${{ github.run_id }}"

      - name: Post results
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            // Post Claude's response as a comment
            const fs = require('fs');
            const response = fs.readFileSync('.claude-response.md', 'utf8');

            if (context.eventName === 'issue_comment' || context.eventName === 'issues') {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.issue.number,
                body: response
              });
            } else if (context.eventName === 'pull_request_review_comment' || context.eventName === 'pull_request') {
              await github.rest.issues.createComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                issue_number: context.payload.pull_request.number,
                body: response
              });
            }
```

### Step 4: Commit and Push

```bash
git add .github/workflows/claude.yml
git commit -m "Add Claude GitHub integration"
git push origin main
```

### Step 5: Test the Integration

Create a test issue:

```bash
gh issue create \
  --title "Test Claude Integration" \
  --body "@claude Can you analyze this repository structure and suggest improvements?"
```

---

## Advanced Enterprise Setup

### Overview

Create a custom GitHub App for your organization with full control over permissions, branding, and configuration.

### Prerequisites

- GitHub Organization admin access
- Anthropic API key
- Server to host webhook receiver (optional for advanced features)

### Step 1: Create Custom GitHub App

1. Go to your organization's settings
2. Navigate to **Developer settings** → **GitHub Apps**
3. Click **New GitHub App**
4. Configure the app:

**Basic Information:**
- **App name:** `[YourOrg] Claude Code Assistant`
- **Homepage URL:** Your organization's URL
- **Webhook URL:** Your webhook endpoint (or use GitHub Actions directly)
- **Webhook secret:** Generate a secure secret

**Permissions:**

Repository permissions:
- Contents: Read & write
- Issues: Read & write
- Pull requests: Read & write
- Metadata: Read-only
- Workflows: Read & write
- Checks: Read & write

Organization permissions:
- Members: Read-only (for user context)

**Events:**

Subscribe to events:
- [x] Issue comments
- [x] Issues
- [x] Pull request review comments
- [x] Pull request reviews
- [x] Pull requests

5. Click **Create GitHub App**

### Step 2: Generate Private Key

1. Scroll down to **Private keys**
2. Click **Generate a private key**
3. Save the downloaded `.pem` file securely
4. Convert to base64 for GitHub secrets:

```bash
cat your-app-name.2024-12-18.private-key.pem | base64 -w 0 > private-key.txt
```

### Step 3: Install App to Organization

1. Click **Install App** in the left sidebar
2. Select your organization
3. Choose **All repositories** or select specific ones
4. Click **Install**

### Step 4: Configure Advanced Workflow

Create `.github/workflows/claude-enterprise.yml`:

```yaml
name: Claude Enterprise Integration

on:
  issue_comment:
    types: [created, edited]
  pull_request_review_comment:
    types: [created, edited]
  pull_request_review:
    types: [submitted]
  issues:
    types: [opened, labeled]
  pull_request:
    types: [opened, synchronize]

permissions:
  contents: write
  issues: write
  pull-requests: write
  checks: write

jobs:
  claude-assist:
    if: |
      (github.event_name == 'issue_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review_comment' && contains(github.event.comment.body, '@claude')) ||
      (github.event_name == 'pull_request_review' && contains(github.event.review.body, '@claude')) ||
      (github.event_name == 'issues' && contains(github.event.issue.labels.*.name, 'claude-assist'))

    runs-on: ubuntu-latest
    timeout-minutes: 60  # Extended for complex tasks

    steps:
      - name: Generate App Token
        id: app-token
        uses: actions/create-github-app-token@v1
        with:
          app-id: ${{ secrets.CLAUDE_APP_ID }}
          private-key: ${{ secrets.CLAUDE_PRIVATE_KEY }}
          owner: ${{ github.repository_owner }}

      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          token: ${{ steps.app-token.outputs.token }}
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          npm install -g @anthropic-ai/claude-cli
          pip install anthropic

      - name: Run Claude with Enterprise Config
        env:
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          CLAUDE_MODEL: claude-opus-4-5  # Use latest model
          CLAUDE_MAX_TOKENS: 8192
          CLAUDE_TEMPERATURE: 0.7
        run: |
          claude github-assist \
            --event-type "${{ github.event_name }}" \
            --event-payload "${{ toJson(github.event) }}" \
            --repository "${{ github.repository }}" \
            --model "$CLAUDE_MODEL" \
            --max-tokens "$CLAUDE_MAX_TOKENS" \
            --temperature "$CLAUDE_TEMPERATURE"

      - name: Create Check Run
        uses: actions/github-script@v7
        if: always()
        with:
          github-token: ${{ steps.app-token.outputs.token }}
          script: |
            await github.rest.checks.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              name: 'Claude Analysis',
              head_sha: context.sha,
              status: 'completed',
              conclusion: '${{ job.status }}',
              output: {
                title: 'Claude Code Review',
                summary: 'Claude has completed the analysis',
              }
            });
```

### Step 5: Add Enterprise Secrets

Add these secrets to your organization or repository:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `CLAUDE_APP_ID` | Your GitHub App ID | From app settings |
| `CLAUDE_PRIVATE_KEY` | Base64-encoded private key | From Step 2 |
| `CLAUDE_WEBHOOK_SECRET` | Webhook secret | From app settings |

### Step 6: Configure Security

1. **Enable required status checks:**
   - Go to **Settings** → **Branches**
   - Add branch protection rules
   - Require Claude checks to pass

2. **Set up CODEOWNERS:**

```
# .github/CODEOWNERS
* @your-org/engineering-team

# Claude should review all PRs
* @claude
```

3. **Configure access controls:**
   - Limit who can trigger Claude
   - Set up approval workflows
   - Enable audit logging

---

## Required Secrets

### ANTHROPIC_API_KEY

**Purpose:** Authenticates requests to the Anthropic API

**How to obtain:**
1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Sign in or create an account
3. Navigate to **API Keys** section
4. Click **Create Key**
5. Give it a descriptive name: "GitHub Integration - [Repo Name]"
6. Copy the key (starts with `sk-ant-...`)

**How to add to GitHub:**
1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: Paste your API key
5. Click **Add secret**

**Security notes:**
- Never commit API keys to your repository
- Rotate keys periodically (every 90 days recommended)
- Use separate keys for each environment (dev, staging, prod)
- Monitor usage in Anthropic console
- Revoke keys immediately if compromised

### Optional: CLAUDE_GITHUB_TOKEN

**Purpose:** Enhanced GitHub access for Claude (auto-generated in Quick Setup)

Not required for manual setup - uses `GITHUB_TOKEN` instead.

---

## Workflow Triggers

### issue_comment

Triggers when someone comments on an issue or PR.

**Use cases:**
- Ask Claude questions about code
- Request assistance on issues
- Get suggestions for implementation

**Example:**
```markdown
@claude Can you help me implement the user authentication feature described in this issue?
```

**Workflow configuration:**
```yaml
on:
  issue_comment:
    types: [created, edited]
```

**Filtering:**
```yaml
if: contains(github.event.comment.body, '@claude')
```

### pull_request_review_comment

Triggers on inline code review comments in PRs.

**Use cases:**
- Ask Claude about specific code changes
- Request refactoring suggestions
- Get explanations for complex code

**Example:**
In a PR review, comment on a line:
```markdown
@claude Is there a more efficient way to implement this algorithm?
```

**Workflow configuration:**
```yaml
on:
  pull_request_review_comment:
    types: [created, edited]
```

### issues (with labels)

Triggers when issues are opened or labeled.

**Use cases:**
- Auto-assign Claude to specific issue types
- Triage and categorization
- Automatic analysis of bug reports

**Example:**
Add label `claude-assist` to an issue to automatically invoke Claude.

**Workflow configuration:**
```yaml
on:
  issues:
    types: [opened, labeled]

jobs:
  claude-assist:
    if: contains(github.event.issue.labels.*.name, 'claude-assist')
```

**Supported labels:**
- `claude-assist` - General Claude assistance
- `claude-review` - Request code review
- `claude-document` - Generate documentation
- `claude-test` - Write or fix tests
- `claude-refactor` - Refactoring suggestions

### pull_request (for auto-review)

Triggers automatically on PR creation or updates.

**Use cases:**
- Automatic code review on every PR
- Compliance checking
- Quality assurance

**Example:**
Add label `auto-review` to PR to enable automatic Claude review.

**Workflow configuration:**
```yaml
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  claude-auto-review:
    if: contains(github.event.pull_request.labels.*.name, 'auto-review')
```

**What Claude checks:**
- Code quality and best practices
- Potential bugs and security issues
- Test coverage
- Documentation completeness
- ACGME compliance (for this project)
- Naming conventions and style

### Trigger Combinations

You can combine multiple triggers for comprehensive coverage:

```yaml
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [labeled]
  pull_request:
    types: [opened, synchronize]
```

---

## Using Claude in GitHub

### Basic Mentions

Simply mention `@claude` in any comment:

**In an issue:**
```markdown
@claude Can you help me understand the residency scheduling algorithm?
```

**In a PR comment:**
```markdown
@claude Please review these changes to the ACGME compliance checker
```

**In an inline code comment:**
```markdown
@claude Is this the correct way to calculate the 80-hour rule?
```

### Advanced Usage

#### Specific Instructions

Be explicit about what you want:

```markdown
@claude Please:
1. Review the new faculty credential tracking feature
2. Check for security vulnerabilities
3. Suggest performance improvements
4. Ensure ACGME compliance is maintained
```

#### Code Generation

Ask Claude to implement features:

```markdown
@claude Can you implement the absence overlap detection feature described in issue #123?

Requirements:
- Check for overlapping absences in the same department
- Alert if critical coverage is affected
- Suggest alternative coverage options
```

#### Documentation

Request documentation updates:

```markdown
@claude Please update the API documentation for the new swap marketplace endpoints in `/docs/api/`
```

#### Testing

Ask for test coverage:

```markdown
@claude Can you add unit tests for the resilience framework's utilization monitoring? Focus on edge cases for the 80% threshold.
```

#### Refactoring

Request code improvements:

```markdown
@claude The `schedule_generator.py` file is getting complex. Can you refactor it into smaller, more maintainable functions?
```

### Command Patterns

| Pattern | Purpose | Example |
|---------|---------|---------|
| `@claude analyze` | Code analysis | `@claude analyze the authentication flow` |
| `@claude fix` | Bug fixes | `@claude fix the N+1 query in the schedule endpoint` |
| `@claude implement` | Feature development | `@claude implement the absence calendar export` |
| `@claude review` | Code review | `@claude review the security changes` |
| `@claude test` | Testing | `@claude test the emergency coverage system` |
| `@claude document` | Documentation | `@claude document the Celery background tasks` |
| `@claude optimize` | Performance | `@claude optimize the schedule generation algorithm` |

### Response Format

Claude will respond with:

1. **Analysis summary** - What was requested and understood
2. **Findings** - Issues, suggestions, or analysis results
3. **Actions taken** - Commits, file changes, or recommendations
4. **Next steps** - What you should review or do next

Example response:
```markdown
## Analysis Complete

I've reviewed the PR changes to the swap marketplace feature.

### Findings

1. **Security**: The auto-matching algorithm properly validates user permissions
2. **Performance**: Consider adding an index on `swap_requests.status`
3. **Tests**: Missing test case for concurrent swap requests

### Changes Made

- Added database index: `idx_swap_requests_status`
- Created test case: `test_concurrent_swap_resolution`
- Updated API documentation

### Recommendations

1. Add rate limiting to the swap request endpoint
2. Consider implementing optimistic locking for swap acceptance
3. Monitor database query performance in production

Let me know if you'd like me to implement any of these recommendations!
```

---

## Background Task Behavior

### How Background Tasks Work

When you mention `@claude`, GitHub Actions spins up a runner that:

1. **Clones the repository** - Full context of your codebase
2. **Analyzes the request** - Understands what you're asking
3. **Reads relevant files** - Uses Grep, Read, and Glob tools
4. **Executes the task** - Writes code, runs tests, generates docs
5. **Creates commits** - Pushes changes to your branch
6. **Posts response** - Comments with results and summary

### Task Duration

| Task Type | Typical Duration | Max Duration |
|-----------|------------------|--------------|
| Simple question | 30-60 seconds | 2 minutes |
| Code review | 1-3 minutes | 5 minutes |
| Feature implementation | 5-15 minutes | 30 minutes |
| Complex refactoring | 10-20 minutes | 30 minutes |
| Full test suite | 15-30 minutes | 60 minutes |

### Monitoring Tasks

**View running tasks:**
1. Go to **Actions** tab in your repository
2. Look for "Claude Integration" workflow runs
3. Click on a run to see detailed logs

**Check progress:**
```bash
# Using GitHub CLI
gh run list --workflow=claude.yml
gh run view <run-id> --log
```

### Resource Limits

GitHub Actions imposes these limits:

| Resource | Limit | Notes |
|----------|-------|-------|
| **Workflow duration** | 6 hours | Configure timeout in workflow |
| **Job duration** | 6 hours | Use `timeout-minutes` |
| **Disk space** | 14 GB | Claude cleans up temporary files |
| **Memory** | 7 GB | Sufficient for most tasks |
| **API rate limit** | 5,000 req/hour | Anthropic API limit |

### Concurrent Execution

By default, workflows run concurrently. To prevent conflicts:

```yaml
concurrency:
  group: claude-${{ github.ref }}
  cancel-in-progress: false  # Don't cancel ongoing work
```

### Background Task States

Claude tasks go through these states:

1. **Queued** - Waiting for available runner
2. **In Progress** - Actively working on your request
3. **Committing** - Creating commits with changes
4. **Completing** - Posting results and cleaning up
5. **Success** - Task completed successfully
6. **Failed** - Error occurred (check logs)

### Cancelling Tasks

If Claude is working on the wrong thing:

1. Go to **Actions** tab
2. Find the running workflow
3. Click **Cancel workflow**
4. Start a new request with clarification

---

## Best Practices for This Project

### Residency Scheduler Specific Guidelines

#### 1. ACGME Compliance Focus

When asking Claude for help, mention compliance requirements:

```markdown
@claude Please review this schedule generation change and ensure it maintains ACGME compliance for:
- 80-hour weekly limit
- 1-in-7 day off rule
- Appropriate supervision ratios
```

#### 2. Testing Requirements

Always request tests for critical features:

```markdown
@claude Implement the deployment absence tracking feature with:
- Unit tests for validation logic
- Integration tests with schedule generation
- Test cases for edge scenarios (partial deployments, extensions)
```

#### 3. Security Considerations

For authentication and authorization changes:

```markdown
@claude Review these auth changes for:
- JWT token security
- Rate limiting bypass vulnerabilities
- RBAC permission checks
- Input validation gaps
```

#### 4. Database Migrations

When schema changes are needed:

```markdown
@claude Create an Alembic migration for the new procedure credentialing table. Ensure:
- Foreign key constraints are correct
- Indexes are added for performance
- Down migration is reversible
```

#### 5. API Documentation

Keep API docs synchronized:

```markdown
@claude Update the API documentation in `/docs/api/` to reflect the new resilience endpoints. Include:
- Request/response schemas
- Example curl commands
- Error codes and handling
```

#### 6. Background Tasks (Celery)

For Celery-related features:

```markdown
@claude Implement a Celery task for automated absence conflict detection. Requirements:
- Periodic task running every 4 hours
- Check for overlapping absences
- Send notifications for conflicts
- Log results to resilience metrics
```

### Project Conventions

Claude is configured to follow these project patterns:

**Backend (Python/FastAPI):**
- Repository pattern for data access
- Service layer for business logic
- Pydantic schemas for validation
- Comprehensive docstrings
- Type hints on all functions

**Frontend (Next.js/TypeScript):**
- Functional components with hooks
- TypeScript strict mode
- TanStack Query for data fetching
- Tailwind CSS for styling
- Comprehensive component props

**Testing:**
- pytest for backend
- Jest and React Testing Library for frontend
- Playwright for E2E tests
- Minimum 80% code coverage

**Documentation:**
- API changes require doc updates
- New features need user guide updates
- Complex algorithms need explanation docs

### Commit Messages

Claude follows this project's commit style:

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

Example:
```
feat(scheduling): Add emergency coverage reassignment

Implements automatic coverage reassignment when residents
are deployed or on emergency leave. Uses availability matrix
to find qualified replacements.

Resolves #145
```

---

## Troubleshooting

### Common Issues

#### 1. Claude Doesn't Respond

**Symptom:** Mentioned `@claude` but no response after 5+ minutes

**Possible causes:**
- Workflow not configured correctly
- API key missing or invalid
- Trigger condition not met
- GitHub Actions quota exceeded

**Solutions:**

Check workflow runs:
```bash
gh run list --workflow=claude.yml --limit 5
```

Verify secrets:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Confirm `ANTHROPIC_API_KEY` exists
3. Check the key hasn't expired

Check workflow file:
```bash
# Ensure the file exists
ls -la .github/workflows/claude.yml

# Check syntax
cat .github/workflows/claude.yml
```

#### 2. Workflow Fails Immediately

**Symptom:** Workflow starts but fails in first few seconds

**Possible causes:**
- Invalid API key
- Network connectivity issues
- Syntax error in workflow file

**Solutions:**

View error logs:
```bash
gh run view --log
```

Common errors:

**"Invalid API key":**
```bash
# Regenerate API key at console.anthropic.com
# Update GitHub secret
gh secret set ANTHROPIC_API_KEY
```

**"Checkout failed":**
```yaml
# Ensure proper permissions in workflow
permissions:
  contents: read  # Add this
```

#### 3. Claude Makes Incorrect Changes

**Symptom:** Claude commits code that doesn't work or isn't what you wanted

**Solutions:**

1. **Revert the commit:**
```bash
git revert <commit-hash>
git push
```

2. **Provide clearer instructions:**
```markdown
@claude I need to clarify my previous request. Please:

1. [Be more specific about what you want]
2. [Provide examples if applicable]
3. [Mention any constraints or requirements]

Previous attempt had these issues:
- [List what was wrong]
```

3. **Review before merging:**
- Always review Claude's changes before merging to main
- Use PR reviews and approval workflows
- Enable branch protection

#### 4. Timeout Errors

**Symptom:** "The job running on runner... has exceeded the maximum execution time of 30 minutes"

**Solutions:**

Increase timeout in workflow:
```yaml
jobs:
  claude-assist:
    timeout-minutes: 60  # Increase from 30
```

Break large tasks into smaller ones:
```markdown
@claude Let's break this into steps:

Step 1: Implement the data model
Step 2: Create the API endpoints
Step 3: Add tests
Step 4: Update documentation

Please start with Step 1 only.
```

#### 5. Permission Errors

**Symptom:** "Resource not accessible by integration" or "403 Forbidden"

**Solutions:**

Add required permissions to workflow:
```yaml
permissions:
  contents: write      # For creating commits
  issues: write        # For commenting on issues
  pull-requests: write # For commenting on PRs
  checks: write        # For creating check runs
```

Check GitHub App permissions:
1. Go to **Settings** → **Integrations** → **GitHub Apps**
2. Click on the Claude app
3. Verify repository access and permissions

#### 6. Rate Limiting

**Symptom:** "Rate limit exceeded" errors

**Solutions:**

**Anthropic API rate limits:**
- Free tier: 50 requests/day
- Paid tier: Much higher limits
- Solution: Upgrade your Anthropic plan

**GitHub API rate limits:**
- Authenticated: 5,000 requests/hour
- Solution: Use GitHub App token instead of personal token

#### 7. Merge Conflicts

**Symptom:** Claude's commit creates merge conflicts

**Solutions:**

1. **Pull latest changes first:**
```bash
git pull origin main
# Then ask Claude again
```

2. **Mention the conflict:**
```markdown
@claude Your previous changes conflict with recent commits. Please:
1. Pull the latest changes
2. Reimplement the feature accounting for the new code
3. Ensure all tests still pass
```

### Getting Help

If you're still stuck:

1. **Check documentation:**
   - [Claude CLI docs](https://github.com/anthropics/claude-cli)
   - [GitHub Actions docs](https://docs.github.com/actions)

2. **Review workflow logs:**
```bash
gh run list --workflow=claude.yml
gh run view <run-id> --log
```

3. **Test API key:**
```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-3-5-sonnet-20241022","max_tokens":10,"messages":[{"role":"user","content":"Hi"}]}'
```

4. **Create a minimal test case:**
```markdown
@claude Can you respond with "Hello, integration test successful"?
```

5. **Contact support:**
   - Claude support: [support.anthropic.com](https://support.anthropic.com)
   - GitHub support: [support.github.com](https://support.github.com)

---

## Related Documentation

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Anthropic API Reference](https://docs.anthropic.com/en/api)
- [Claude CLI GitHub Repository](https://github.com/anthropics/claude-cli)
- [CI/CD Recommendations](../CI_CD_RECOMMENDATIONS.md) - Project-specific CI/CD setup
- [Development Guide](../development/README.md) - Local development setup

---

## Appendix: Example Prompts

### Code Review

```markdown
@claude Please review this PR for:
- Code quality and maintainability
- Security vulnerabilities
- ACGME compliance impact
- Test coverage
- Documentation completeness
```

### Bug Fix

```markdown
@claude There's a bug in the swap marketplace matching algorithm where it's not correctly filtering by specialty requirements. Can you:

1. Identify the root cause
2. Fix the logic
3. Add a test case that would have caught this
4. Verify the fix doesn't break existing tests
```

### Feature Implementation

```markdown
@claude Please implement a feature to export absence data to Excel:

Requirements:
- New endpoint: GET /api/absences/export
- Include all absence types with date ranges
- Group by person and department
- Use openpyxl library (already in requirements.txt)
- Add authentication check (admin or coordinator only)
- Write tests for the endpoint
- Update API documentation

Follow the existing pattern in `/backend/app/api/routes/schedule.py` for Excel exports.
```

### Documentation

```markdown
@claude The resilience framework is complex and needs better documentation. Please:

1. Review the code in `/backend/app/resilience/`
2. Update `/docs/guides/resilience-framework.md` with:
   - How each component works
   - When each defense level triggers
   - Examples of real-world scenarios
   - How to configure thresholds
3. Add inline code documentation where it's sparse
4. Create a visual diagram showing the flow (can be ASCII art or mermaid)
```

### Testing

```markdown
@claude Our Celery background tasks in `/backend/app/resilience/tasks.py` need better test coverage. Please:

1. Analyze current test coverage
2. Add unit tests for each task function
3. Mock external dependencies (Redis, database)
4. Test error handling and retry logic
5. Ensure tests run fast (use fixtures for setup)

Target: 90%+ coverage on the tasks module.
```

---

## Quick Reference Card

### Setup Commands

```bash
# Quick setup
claude /install-github-app

# Manual setup
gh secret set ANTHROPIC_API_KEY
git add .github/workflows/claude.yml
git commit -m "Add Claude integration"
git push

# Test integration
gh issue create --title "Test" --body "@claude hello"
```

### Workflow Triggers

| Event | When | Example |
|-------|------|---------|
| `issue_comment` | Comment on issue/PR | `@claude help` |
| `pull_request_review_comment` | Inline code comment | `@claude refactor this` |
| `issues` with label | Label added | Add `claude-assist` label |
| `pull_request` | PR opened/updated | Auto-review if labeled |

### Common Commands

| Command | Purpose |
|---------|---------|
| `@claude analyze <thing>` | Code analysis |
| `@claude fix <issue>` | Bug fix |
| `@claude implement <feature>` | New feature |
| `@claude review` | Code review |
| `@claude test <component>` | Add tests |
| `@claude document <feature>` | Documentation |

### Troubleshooting Quick Checks

```bash
# Check workflow runs
gh run list --workflow=claude.yml

# View logs
gh run view --log

# Verify secrets
gh secret list

# Test API key
echo $ANTHROPIC_API_KEY | cut -c1-20
```

---

<p align="center">
  Questions? Issues? Mention <code>@claude</code> for help!
</p>
