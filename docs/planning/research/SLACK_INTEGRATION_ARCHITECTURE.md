# Slack Integration Architecture for Natural Language Coding Requests

> **Document Type:** Technical Architecture Specification
> **Created:** 2025-12-19
> **Author:** Autonomous System Design (Terminal 5)
> **Status:** Ready for Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#1-architecture-overview)
3. [Slack App Configuration](#2-slack-app-configuration)
4. [Message Flow Patterns](#3-message-flow-patterns)
5. [Integration with GitHub Actions](#4-integration-with-github-actions)
6. [Security Considerations](#5-security-considerations)
7. [Implementation Guide](#6-implementation-guide)
8. [Performance & Scalability](#7-performance--scalability)
9. [Monitoring & Observability](#8-monitoring--observability)
10. [Implementation Checklist](#implementation-checklist)

---

## Executive Summary

This document defines the architecture for a Slack bot that enables natural language coding requests, automatically creates GitHub issues/PRs, and integrates with GitHub Actions workflows for autonomous code development.

### Key Capabilities

| Feature | Description | Value Proposition |
|---------|-------------|-------------------|
| **Natural Language Interface** | Developers request features in plain English | Reduces friction, improves accessibility |
| **Intelligent Intent Parsing** | Claude AI classifies requests (bug, feature, refactor) | Accurate routing and prioritization |
| **GitHub Integration** | Auto-creates issues/PRs with proper templates | Eliminates manual issue creation |
| **Workflow Automation** | Triggers GitHub Actions for autonomous work | Hands-free development |
| **Real-time Status Updates** | Reports progress back to Slack threads | Transparency and accountability |

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Slack Workspace                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  User: "@bot implement user authentication"              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                  │
│                              ▼                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           Slack Bot (Events API + Slash Commands)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────────────────────────────┘
                      │ HTTPS (Webhook)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Backend Service (FastAPI)                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Intent Parser    │  │ GitHub Client    │  │ Redis Queue  │  │
│  │ (Claude API)     │  │ (PyGithub)       │  │ (Celery)     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────┬────────────────────────────────────────────┘
                      │ GitHub API
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Issues           │  │ Pull Requests    │  │ Actions      │  │
│  │ (Created)        │  │ (Auto-generated) │  │ (Triggered)  │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────┬────────────────────────────────────────────┘
                      │ Status Webhooks
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Slack Thread Updates                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ✅ Created issue #123: Implement user authentication    │  │
│  │  🔄 PR #45 opened by claude-bot                          │  │
│  │  ✅ CI checks passed                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Architecture Overview

### 1.1 System Components

#### A. Slack Bot Layer

**Purpose:** Interface for user interactions and notifications

```
┌─────────────────────────────────────────────────────────┐
│                    Slack Bot (Node.js)                  │
├─────────────────────────────────────────────────────────┤
│  Components:                                            │
│  • Events API Handler (app_mention, message)           │
│  • Slash Commands (/create-issue, /start-pr)           │
│  • Interactive Components (buttons, modals)            │
│  • OAuth Token Management                              │
│  • Rate Limiter (tier-based API limits)                │
└─────────────────────────────────────────────────────────┘
```

**Technology Stack:**
- `@slack/bolt` (Slack SDK for Node.js)
- Express.js (webhook server)
- Redis (session storage, rate limiting)

#### B. Intent Parser (Claude AI)

**Purpose:** Convert natural language to structured task definitions

```
Input:  "@bot implement user authentication with JWT"
        ↓
Claude API Analysis:
  - Task Type: Feature Implementation
  - Priority: Medium
  - Components: Backend (Auth), Frontend (Login UI)
  - Dependencies: JWT library, user database
  - Complexity: Medium (2-4 hours)
        ↓
Output: {
  "type": "feature",
  "title": "Implement user authentication with JWT",
  "labels": ["feature", "backend", "frontend", "authentication"],
  "priority": "medium",
  "description": "Implement JWT-based authentication...",
  "acceptance_criteria": [
    "User can log in with email/password",
    "JWT token issued on successful login",
    "Protected routes verify JWT tokens",
    "Frontend stores token securely (httpOnly cookie)"
  ],
  "estimated_complexity": "medium"
}
```

**Claude Prompt Template:**

```python
INTENT_PARSER_PROMPT = """
Analyze this development request and extract structured information:

Request: "{user_message}"

Context:
- Project: {project_name}
- Tech Stack: {tech_stack}
- Recent Activity: {recent_commits}

Extract:
1. Task Type: [bug, feature, refactor, docs, test, chore]
2. Priority: [low, medium, high, critical]
3. Affected Components: [backend, frontend, database, infrastructure]
4. Title: Clear, actionable title (max 80 chars)
5. Description: Detailed description with context
6. Acceptance Criteria: List of specific, testable requirements
7. Labels: Relevant GitHub labels
8. Estimated Complexity: [trivial, small, medium, large, extra-large]
9. Dependencies: Any blocking issues or required changes

Respond in JSON format.
"""
```

#### C. GitHub Integration Service

**Purpose:** Create issues, PRs, and trigger workflows

```python
"""GitHub integration service for Slack bot."""
from typing import Dict, List, Optional
from github import Github, GithubException
from pydantic import BaseModel


class GitHubTaskRequest(BaseModel):
    """Structured task request from intent parser."""
    task_type: str  # "issue" or "pull_request"
    title: str
    body: str
    labels: List[str]
    assignees: Optional[List[str]] = None
    milestone: Optional[str] = None
    priority: str


class GitHubIntegrationService:
    """Handles all GitHub operations."""

    def __init__(self, github_token: str, repo_name: str):
        self.gh = Github(github_token)
        self.repo = self.gh.get_repo(repo_name)

    async def create_issue(
        self,
        task: GitHubTaskRequest,
        slack_thread_ts: str
    ) -> Dict:
        """
        Create GitHub issue from Slack request.

        Args:
            task: Structured task data
            slack_thread_ts: Slack thread timestamp for linking

        Returns:
            Dict with issue URL, number, and status
        """
        # Add Slack context to issue body
        issue_body = f"""{task.body}

---

**Requested via Slack**
- Thread: {slack_thread_ts}
- Priority: {task.priority}
- Estimated Complexity: {task.estimated_complexity}

**Acceptance Criteria:**
{self._format_acceptance_criteria(task.acceptance_criteria)}
"""

        try:
            issue = self.repo.create_issue(
                title=task.title,
                body=issue_body,
                labels=task.labels,
                assignees=task.assignees or []
            )

            # Add priority label
            issue.add_to_labels(f"priority:{task.priority}")

            # Trigger workflow if auto-implementation requested
            if "auto-implement" in task.labels:
                self._trigger_workflow(issue.number)

            return {
                "url": issue.html_url,
                "number": issue.number,
                "state": "open",
                "labels": [l.name for l in issue.labels]
            }

        except GithubException as e:
            raise ValueError(f"Failed to create issue: {e.data['message']}")

    async def create_pr(
        self,
        branch_name: str,
        title: str,
        body: str,
        base_branch: str = "main"
    ) -> Dict:
        """
        Create pull request.

        Args:
            branch_name: Source branch for PR
            title: PR title
            body: PR description
            base_branch: Target branch (default: main)

        Returns:
            Dict with PR URL, number, and status
        """
        try:
            pr = self.repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=base_branch
            )

            return {
                "url": pr.html_url,
                "number": pr.number,
                "state": "open",
                "draft": pr.draft
            }

        except GithubException as e:
            raise ValueError(f"Failed to create PR: {e.data['message']}")

    def _trigger_workflow(self, issue_number: int):
        """Trigger GitHub Actions workflow for autonomous implementation."""
        workflow = self.repo.get_workflow("autonomous-issue-resolver.yml")
        workflow.create_dispatch(
            ref="main",
            inputs={"issue_number": str(issue_number)}
        )
```

#### D. Background Task Queue (Celery)

**Purpose:** Asynchronous processing of Slack events

```python
"""Celery tasks for Slack/GitHub integration."""
from celery import Celery
from app.core.config import settings
from app.services.slack import SlackService
from app.services.github_integration import GitHubIntegrationService

celery = Celery(__name__, broker=settings.REDIS_URL)


@celery.task(bind=True, max_retries=3)
def process_slack_request(
    self,
    user_message: str,
    channel_id: str,
    thread_ts: str,
    user_id: str
):
    """
    Process Slack coding request asynchronously.

    Flow:
    1. Parse intent with Claude
    2. Create GitHub issue/PR
    3. Trigger GitHub Actions if applicable
    4. Post status update to Slack thread
    """
    try:
        slack = SlackService()
        github = GitHubIntegrationService(
            settings.GITHUB_TOKEN,
            settings.GITHUB_REPO
        )

        # 1. Parse intent
        slack.post_message(
            channel_id,
            "🤔 Analyzing your request...",
            thread_ts=thread_ts
        )

        task_data = parse_intent_with_claude(user_message)

        # 2. Create GitHub resource
        if task_data["create_type"] == "issue":
            result = await github.create_issue(task_data, thread_ts)
            emoji = "📋"
            resource = "issue"
        else:
            result = await github.create_pr(task_data, thread_ts)
            emoji = "🔀"
            resource = "PR"

        # 3. Post success message
        slack.post_message(
            channel_id,
            f"{emoji} Created {resource} #{result['number']}: {result['url']}",
            thread_ts=thread_ts
        )

        # 4. Watch for GitHub webhook updates
        subscribe_to_github_updates(result['number'], channel_id, thread_ts)

    except Exception as e:
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


@celery.task
def handle_github_webhook(event_type: str, payload: Dict):
    """
    Handle GitHub webhook events and post to Slack.

    Events:
    - issue_comment: New comment on issue
    - pull_request: PR opened/closed/merged
    - workflow_run: CI/CD status
    - check_suite: Test results
    """
    slack = SlackService()

    # Get Slack thread from issue/PR metadata
    thread_info = extract_slack_thread(payload)
    if not thread_info:
        return

    # Format message based on event type
    message = format_github_event(event_type, payload)

    slack.post_message(
        thread_info["channel_id"],
        message,
        thread_ts=thread_info["thread_ts"]
    )
```

### 1.2 Data Flow Diagram

```
┌─────────────┐
│ Slack User  │
└──────┬──────┘
       │ 1. "@bot implement feature X"
       │
       ▼
┌─────────────────────────────────────────┐
│      Slack Events API                   │
│  POST /slack/events                     │
│  {                                      │
│    "type": "app_mention",               │
│    "text": "@bot implement feature X",  │
│    "channel": "C123",                   │
│    "thread_ts": "1234567890.123"        │
│  }                                      │
└──────┬──────────────────────────────────┘
       │ 2. Enqueue to Celery
       │
       ▼
┌─────────────────────────────────────────┐
│       Celery Worker                     │
│  • Validate request                     │
│  • Call Claude API (intent parsing)     │
│  • Extract task metadata                │
└──────┬──────────────────────────────────┘
       │ 3. Structured task data
       │
       ▼
┌─────────────────────────────────────────┐
│      GitHub Integration Service         │
│  • Create issue with template           │
│  • Add labels (auto, priority, type)    │
│  • Link Slack thread in metadata        │
│  • Trigger workflow_dispatch if needed  │
└──────┬──────────────────────────────────┘
       │ 4. Issue created
       │
       ▼
┌─────────────────────────────────────────┐
│      GitHub Actions                     │
│  • autonomous-issue-resolver.yml        │
│  • Assigns Claude bot to issue          │
│  • Clones repo, analyzes codebase       │
│  • Implements changes                   │
│  • Creates PR                           │
└──────┬──────────────────────────────────┘
       │ 5. Webhook events
       │
       ▼
┌─────────────────────────────────────────┐
│      Webhook Handler (FastAPI)          │
│  POST /webhooks/github                  │
│  • Extracts Slack thread metadata       │
│  • Formats status message               │
│  • Posts to Slack thread                │
└──────┬──────────────────────────────────┘
       │ 6. Thread updates
       │
       ▼
┌─────────────────────────────────────────┐
│       Slack Thread                      │
│  User:   "@bot implement feature X"     │
│  Bot:    "🤔 Analyzing your request..." │
│  Bot:    "📋 Created issue #123"        │
│  Bot:    "🔄 PR #45 opened"             │
│  Bot:    "✅ CI checks passed"          │
│  Bot:    "🎉 Merged to main!"           │
└─────────────────────────────────────────┘
```

---

## 2. Slack App Configuration

### 2.1 OAuth Scopes

#### Bot Token Scopes

Required for bot functionality:

```
channels:history       # Read channel messages
channels:read          # List public channels
chat:write             # Post messages as bot
chat:write.public      # Post to channels bot isn't in
commands               # Register slash commands
im:history             # Read direct messages
im:read                # List DMs
im:write               # Send DMs
reactions:read         # Read message reactions
reactions:write        # Add reactions to messages
users:read             # Get user info
app_mentions:read      # Receive @mentions
```

#### User Token Scopes (Optional)

For user-impersonation features:

```
users:read             # Get user profile info
search:read            # Search messages
```

### 2.2 Event Subscriptions

**Request URL:** `https://your-domain.com/slack/events`

**Events to Subscribe:**

| Event | Description | Use Case |
|-------|-------------|----------|
| `app_mention` | Bot is @mentioned | Primary trigger for coding requests |
| `message.im` | Direct message to bot | Private feature requests |
| `reaction_added` | User reacts to message | Quick actions (👍 = approve, 🚀 = deploy) |
| `message.channels` | Message in subscribed channels | Monitor #engineering for keywords |

**Event Payload Example:**

```json
{
  "token": "VERIFICATION_TOKEN",
  "team_id": "T123ABC",
  "event": {
    "type": "app_mention",
    "user": "U123ABC",
    "text": "<@U987XYZ> implement user authentication with JWT",
    "ts": "1234567890.123456",
    "channel": "C123ABC",
    "thread_ts": "1234567890.123456"
  },
  "type": "event_callback",
  "event_id": "Ev123ABC",
  "event_time": 1234567890
}
```

### 2.3 Slash Commands

#### `/create-issue` - Quick Issue Creation

**Description:** Create GitHub issue from Slack

**Usage:** `/create-issue [bug|feature|refactor] <description>`

**Examples:**
```
/create-issue bug User can't login after password reset
/create-issue feature Add export to CSV functionality
/create-issue refactor Optimize database queries in schedule generation
```

**Handler:**

```python
@app.route('/slack/commands/create-issue', methods=['POST'])
async def handle_create_issue(request: Request):
    """
    Handle /create-issue slash command.

    Flow:
    1. Parse command text
    2. Open modal for details (if needed)
    3. Create GitHub issue
    4. Respond with issue link
    """
    form_data = await request.form()

    command_text = form_data.get('text', '')
    channel_id = form_data.get('channel_id')
    user_id = form_data.get('user_id')
    response_url = form_data.get('response_url')

    # Parse command
    parts = command_text.split(maxsplit=1)
    if len(parts) < 2:
        return {
            "response_type": "ephemeral",
            "text": "Usage: /create-issue [bug|feature|refactor] <description>"
        }

    issue_type, description = parts

    # Enqueue async task
    task = process_issue_creation.delay(
        issue_type=issue_type,
        description=description,
        user_id=user_id,
        channel_id=channel_id,
        response_url=response_url
    )

    # Immediate response (Slack requires response within 3 sec)
    return {
        "response_type": "ephemeral",
        "text": f"🤖 Creating {issue_type} issue: \"{description}\"\n⏳ This may take a few seconds..."
    }
```

#### `/start-pr` - Create PR from Branch

**Description:** Create pull request from existing branch

**Usage:** `/start-pr <branch-name> [title]`

**Example:**
```
/start-pr feature/user-auth Implement JWT authentication
```

#### `/workflow-status` - Check GitHub Actions Status

**Description:** Get status of running workflows

**Usage:** `/workflow-status [run-id]`

**Example:**
```
/workflow-status          # Latest workflow
/workflow-status 123456   # Specific run
```

### 2.4 Interactive Components

#### Approval Button (Modal)

When bot creates an issue, show approval modal:

```json
{
  "type": "modal",
  "callback_id": "approve_issue",
  "title": {
    "type": "plain_text",
    "text": "Approve Issue Creation"
  },
  "submit": {
    "type": "plain_text",
    "text": "Create Issue"
  },
  "blocks": [
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Issue Title:*\nImplement user authentication with JWT"
      }
    },
    {
      "type": "input",
      "block_id": "priority_block",
      "label": {
        "type": "plain_text",
        "text": "Priority"
      },
      "element": {
        "type": "static_select",
        "action_id": "priority_select",
        "options": [
          {"text": {"type": "plain_text", "text": "Low"}, "value": "low"},
          {"text": {"type": "plain_text", "text": "Medium"}, "value": "medium"},
          {"text": {"type": "plain_text", "text": "High"}, "value": "high"},
          {"text": {"type": "plain_text", "text": "Critical"}, "value": "critical"}
        ]
      }
    },
    {
      "type": "input",
      "block_id": "labels_block",
      "label": {
        "type": "plain_text",
        "text": "Labels"
      },
      "element": {
        "type": "multi_static_select",
        "action_id": "labels_select",
        "options": [
          {"text": {"type": "plain_text", "text": "backend"}, "value": "backend"},
          {"text": {"type": "plain_text", "text": "frontend"}, "value": "frontend"},
          {"text": {"type": "plain_text", "text": "auto-implement"}, "value": "auto-implement"}
        ]
      }
    }
  ]
}
```

---

## 3. Message Flow Patterns

### 3.1 Pattern 1: Simple Issue Creation

**User Intent:** "Create a bug report"

```
┌─────────────────────────────────────────────────────────┐
│ Slack Channel: #engineering                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ @alice: @bot users can't reset their password          │
│         ↓                                               │
│ @bot:   🤔 Analyzing your request...                    │
│         (3 seconds)                                     │
│         ↓                                               │
│ @bot:   📋 Created bug issue #456                       │
│         https://github.com/org/repo/issues/456          │
│                                                         │
│         **Issue Details:**                              │
│         • Type: Bug                                     │
│         • Priority: High (authentication-related)       │
│         • Labels: bug, backend, authentication          │
│         • Assigned to: backend-team                     │
│                                                         │
│         Would you like me to auto-fix this? 🤖          │
│         [Yes, please] [No, manual review needed]        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Backend Processing:**

```python
async def handle_simple_issue_request(message: str, context: Dict):
    """
    Handle simple issue creation request.

    Steps:
    1. Classify as bug/feature/refactor
    2. Extract key details from message
    3. Create issue with minimal info
    4. Offer auto-implementation
    """
    # Parse with Claude
    analysis = await claude_api.parse_intent(
        message=message,
        prompt=SIMPLE_ISSUE_PROMPT
    )

    # Create issue
    issue = await github.create_issue(
        title=analysis["title"],
        body=analysis["description"],
        labels=analysis["labels"]
    )

    # Return formatted response
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"📋 Created {analysis['type']} issue #{issue.number}\n{issue.url}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"**Issue Details:**\n• Type: {analysis['type']}\n• Priority: {analysis['priority']}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Yes, please"},
                        "value": f"auto_implement:{issue.number}",
                        "action_id": "auto_implement_yes"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "No, manual review needed"},
                        "value": f"manual:{issue.number}",
                        "action_id": "auto_implement_no"
                    }
                ]
            }
        ]
    }
```

### 3.2 Pattern 2: Complex Feature Request

**User Intent:** "Implement a feature with multiple components"

```
┌─────────────────────────────────────────────────────────┐
│ Slack Channel: #product-requests                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ @bob:   @bot implement CSV export for schedules        │
│         Users should be able to export their schedule  │
│         to CSV format with filters for date range      │
│         ↓                                               │
│ @bot:   🤔 Analyzing your request...                    │
│         This looks like a medium complexity feature     │
│         ↓                                               │
│ @bot:   📋 I've drafted this feature spec:              │
│                                                         │
│         **Title:** Implement CSV export for schedules   │
│                                                         │
│         **Components:**                                 │
│         • Backend: CSV generation endpoint              │
│         • Frontend: Export button + date filters        │
│         • Database: Query optimization for exports      │
│                                                         │
│         **Acceptance Criteria:**                        │
│         ✓ User can export schedule to CSV              │
│         ✓ CSV includes all assignment details          │
│         ✓ Date range filter (from/to dates)            │
│         ✓ Download initiates client-side               │
│         ✓ Large exports (1000+ rows) are paginated     │
│                                                         │
│         **Estimated Effort:** 2-3 hours                 │
│                                                         │
│         [Create Issue] [Edit Details] [Cancel]          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Claude Intent Parsing:**

```python
COMPLEX_FEATURE_PROMPT = """
Analyze this feature request and create a comprehensive spec:

User Request: "{message}"

Project Context:
- Tech Stack: FastAPI (backend), Next.js (frontend), PostgreSQL
- Existing Features: {related_features}
- Recent PRs: {recent_prs}

Generate:
1. Clear feature title (user-facing)
2. List of affected components (backend/frontend/database/etc)
3. Detailed acceptance criteria (testable, specific)
4. Estimated effort (trivial/small/medium/large/xl)
5. Dependencies (existing features this relies on)
6. Suggested implementation approach
7. Potential edge cases to consider

Format as JSON with these keys: title, components, acceptance_criteria,
estimated_effort, dependencies, implementation_notes, edge_cases
"""

async def parse_complex_feature(message: str) -> Dict:
    """Parse complex feature request with Claude."""
    response = await anthropic.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": COMPLEX_FEATURE_PROMPT.format(
                message=message,
                related_features=get_related_features(),
                recent_prs=get_recent_prs()
            )
        }]
    )

    return json.loads(response.content[0].text)
```

### 3.3 Pattern 3: Auto-Implementation with Progress Updates

**User Intent:** "Bot should implement feature autonomously"

```
┌─────────────────────────────────────────────────────────┐
│ Slack Thread (from issue creation)                     │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ @alice: @bot implement this automatically               │
│         ↓                                               │
│ @bot:   🚀 Starting autonomous implementation...        │
│         • Created branch: feature/csv-export-123        │
│         • Assigned issue #123 to claude-bot             │
│         • GitHub Actions workflow triggered             │
│         ↓                                               │
│ @bot:   📝 Implementation plan:                         │
│         1. Add CSV export endpoint (backend)            │
│         2. Create export service with date filters      │
│         3. Add Export button to UI (frontend)           │
│         4. Write integration tests                      │
│         ↓ (5 minutes later)                             │
│ @bot:   ✅ Step 1/4 complete: Backend endpoint added    │
│         ↓ (3 minutes later)                             │
│ @bot:   ✅ Step 2/4 complete: Export service created    │
│         ↓ (4 minutes later)                             │
│ @bot:   ✅ Step 3/4 complete: UI components added       │
│         ↓ (2 minutes later)                             │
│ @bot:   ✅ Step 4/4 complete: Tests passing ✓           │
│         ↓                                               │
│ @bot:   🔀 Pull Request created: #789                   │
│         https://github.com/org/repo/pull/789            │
│                                                         │
│         **PR Summary:**                                 │
│         • 8 files changed (+234 -12 lines)              │
│         • All tests passing ✓                           │
│         • No linting errors ✓                           │
│         • Ready for review                              │
│                                                         │
│         @alice Please review when you have a chance!    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Progress Update Mechanism:**

```python
class AutoImplementationProgress:
    """Track and report progress of autonomous implementation."""

    def __init__(self, issue_number: int, slack_thread: Dict):
        self.issue_number = issue_number
        self.slack_channel = slack_thread["channel_id"]
        self.slack_thread_ts = slack_thread["thread_ts"]
        self.steps = []
        self.current_step = 0

    async def add_step(self, description: str):
        """Add implementation step."""
        self.steps.append({
            "description": description,
            "status": "pending",
            "started_at": None,
            "completed_at": None
        })

    async def start_step(self, step_index: int):
        """Mark step as started."""
        self.steps[step_index]["status"] = "in_progress"
        self.steps[step_index]["started_at"] = datetime.utcnow()

        await self._post_update(
            f"🔄 Step {step_index + 1}/{len(self.steps)}: {self.steps[step_index]['description']}"
        )

    async def complete_step(self, step_index: int):
        """Mark step as complete."""
        self.steps[step_index]["status"] = "complete"
        self.steps[step_index]["completed_at"] = datetime.utcnow()

        duration = (
            self.steps[step_index]["completed_at"] -
            self.steps[step_index]["started_at"]
        ).total_seconds()

        await self._post_update(
            f"✅ Step {step_index + 1}/{len(self.steps)} complete: "
            f"{self.steps[step_index]['description']} ({duration:.0f}s)"
        )

    async def _post_update(self, message: str):
        """Post progress update to Slack thread."""
        slack = SlackService()
        await slack.post_message(
            self.slack_channel,
            message,
            thread_ts=self.slack_thread_ts
        )


# Usage in GitHub Actions workflow
async def run_autonomous_implementation(issue_number: int):
    """Run autonomous implementation with progress tracking."""
    # Get Slack thread from issue metadata
    issue = github.get_issue(issue_number)
    slack_thread = extract_slack_thread_from_issue(issue)

    progress = AutoImplementationProgress(issue_number, slack_thread)

    # Define implementation steps
    await progress.add_step("Add backend endpoint")
    await progress.add_step("Create service layer logic")
    await progress.add_step("Add frontend UI components")
    await progress.add_step("Write and run tests")

    # Execute steps
    for i, step in enumerate(progress.steps):
        await progress.start_step(i)

        # Execute actual implementation
        await execute_implementation_step(step)

        await progress.complete_step(i)

    # Create PR
    pr = await create_pull_request(issue_number)

    await progress._post_update(
        f"🔀 Pull Request created: #{pr.number}\n{pr.url}"
    )
```

### 3.4 Pattern 4: Error Handling & Escalation

**Scenario:** Bot encounters an error during implementation

```
┌─────────────────────────────────────────────────────────┐
│ Slack Thread                                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ @bot:   ✅ Step 1/4 complete: Backend endpoint added    │
│         ✅ Step 2/4 complete: Export service created    │
│         ↓                                               │
│ @bot:   ❌ Step 3/4 failed: Test failure detected       │
│                                                         │
│         **Error Details:**                              │
│         ```                                             │
│         AssertionError: Expected 200, got 500           │
│         File: tests/test_export.py:45                   │
│         ```                                             │
│                                                         │
│         **Attempted Fixes:**                            │
│         1. ✗ Retry with error handling                  │
│         2. ✗ Adjust test assertions                     │
│         3. ✗ Rollback and re-implement                  │
│                                                         │
│         🆘 **Human intervention required**              │
│                                                         │
│         I've created a draft PR with my progress:       │
│         https://github.com/org/repo/pull/790            │
│                                                         │
│         @alice @bob Can someone help debug this?        │
│                                                         │
│         [View Logs] [Assign to Me] [Close Issue]        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 4. Integration with GitHub Actions

### 4.1 Workflow: Autonomous Issue Resolver

**File:** `.github/workflows/autonomous-issue-resolver.yml`

```yaml
name: Autonomous Issue Resolver

on:
  workflow_dispatch:
    inputs:
      issue_number:
        description: 'GitHub issue number to resolve'
        required: true
        type: string
      slack_thread_ts:
        description: 'Slack thread timestamp for updates'
        required: false
        type: string

permissions:
  contents: write
  pull-requests: write
  issues: write

jobs:
  analyze-issue:
    runs-on: ubuntu-latest
    outputs:
      implementation_plan: ${{ steps.plan.outputs.plan }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v6

      - name: Get issue details
        id: issue
        uses: actions/github-script@v7
        with:
          script: |
            const issue = await github.rest.issues.get({
              owner: context.repo.owner,
              repo: context.repo.repo,
              issue_number: ${{ inputs.issue_number }}
            });

            core.setOutput('title', issue.data.title);
            core.setOutput('body', issue.data.body);
            core.setOutput('labels', issue.data.labels.map(l => l.name).join(','));

      - name: Create implementation plan with Claude
        id: plan
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          # Call Claude API to create implementation plan
          python scripts/create_implementation_plan.py \
            --issue-title "${{ steps.issue.outputs.title }}" \
            --issue-body "${{ steps.issue.outputs.body }}" \
            --output plan.json

          # Output plan for next job
          cat plan.json
          echo "plan=$(cat plan.json | jq -c .)" >> $GITHUB_OUTPUT

      - name: Post plan to Slack
        if: inputs.slack_thread_ts != ''
        uses: slackapi/slack-github-action@v1
        with:
          slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
          channel-id: ${{ secrets.SLACK_CHANNEL_ID }}
          thread-ts: ${{ inputs.slack_thread_ts }}
          payload: |
            {
              "text": "📝 Implementation plan created",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "**Implementation Plan:**\n```${{ steps.plan.outputs.plan }}```"
                  }
                }
              ]
            }

  implement-changes:
    needs: analyze-issue
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v6

      - name: Create feature branch
        run: |
          BRANCH_NAME="auto/issue-${{ inputs.issue_number }}"
          git checkout -b $BRANCH_NAME
          echo "BRANCH_NAME=$BRANCH_NAME" >> $GITHUB_ENV

      - name: Setup environment
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Execute implementation steps
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          IMPLEMENTATION_PLAN: ${{ needs.analyze-issue.outputs.implementation_plan }}
        run: |
          # Run autonomous implementation script
          python scripts/autonomous_implementation.py \
            --plan "$IMPLEMENTATION_PLAN" \
            --issue-number ${{ inputs.issue_number }} \
            --slack-thread-ts "${{ inputs.slack_thread_ts }}"

      - name: Run tests
        run: |
          cd backend
          pytest --maxfail=5

      - name: Commit changes
        run: |
          git config user.name "claude-bot[bot]"
          git config user.email "claude-bot[bot]@users.noreply.github.com"

          git add .
          git commit -m "Auto-implement: ${{ steps.issue.outputs.title }} (#${{ inputs.issue_number }})"

          git push origin $BRANCH_NAME

      - name: Create pull request
        id: create-pr
        uses: actions/github-script@v7
        with:
          script: |
            const pr = await github.rest.pulls.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: `Auto-implement: Issue #${{ inputs.issue_number }}`,
              head: process.env.BRANCH_NAME,
              base: 'main',
              body: `Resolves #${{ inputs.issue_number }}\n\n**Autonomous Implementation**\n\nThis PR was automatically generated by the autonomous issue resolver.\n\nPlease review the changes carefully.`
            });

            core.setOutput('pr_number', pr.data.number);
            core.setOutput('pr_url', pr.data.html_url);

      - name: Post PR to Slack
        if: inputs.slack_thread_ts != ''
        uses: slackapi/slack-github-action@v1
        with:
          slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
          channel-id: ${{ secrets.SLACK_CHANNEL_ID }}
          thread-ts: ${{ inputs.slack_thread_ts }}
          payload: |
            {
              "text": "🔀 Pull Request created: #${{ steps.create-pr.outputs.pr_number }}",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "🔀 **Pull Request Created**\n<${{ steps.create-pr.outputs.pr_url }}|PR #${{ steps.create-pr.outputs.pr_number }}>\n\nReady for review!"
                  }
                }
              ]
            }

  handle-failure:
    needs: implement-changes
    if: failure()
    runs-on: ubuntu-latest

    steps:
      - name: Post failure to Slack
        if: inputs.slack_thread_ts != ''
        uses: slackapi/slack-github-action@v1
        with:
          slack-bot-token: ${{ secrets.SLACK_BOT_TOKEN }}
          channel-id: ${{ secrets.SLACK_CHANNEL_ID }}
          thread-ts: ${{ inputs.slack_thread_ts }}
          payload: |
            {
              "text": "❌ Autonomous implementation failed",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "❌ **Implementation Failed**\n\nI encountered errors during autonomous implementation.\n\n<${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}|View Logs>\n\n🆘 Human intervention required."
                  }
                }
              ]
            }
```

### 4.2 Workflow: GitHub Webhook → Slack Updates

**File:** `backend/app/webhooks/github.py`

```python
"""GitHub webhook handler for Slack integration."""
from fastapi import APIRouter, Request, HTTPException
from app.services.slack import SlackService
from app.core.config import settings
import hmac
import hashlib

router = APIRouter()


@router.post("/webhooks/github")
async def handle_github_webhook(request: Request):
    """
    Handle GitHub webhook events and post to Slack.

    Events handled:
    - pull_request: PR opened/closed/merged
    - workflow_run: CI/CD status
    - check_suite: Test results
    - pull_request_review: Review submitted
    """
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_github_signature(await request.body(), signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    payload = await request.json()
    event_type = request.headers.get('X-GitHub-Event')

    # Extract Slack thread info from issue/PR metadata
    slack_thread = extract_slack_thread_from_payload(payload)

    if not slack_thread:
        # No Slack thread associated, skip
        return {"status": "ok"}

    # Handle different event types
    if event_type == "pull_request":
        await handle_pr_event(payload, slack_thread)
    elif event_type == "workflow_run":
        await handle_workflow_event(payload, slack_thread)
    elif event_type == "check_suite":
        await handle_check_suite_event(payload, slack_thread)
    elif event_type == "pull_request_review":
        await handle_pr_review_event(payload, slack_thread)

    return {"status": "ok"}


async def handle_pr_event(payload: Dict, slack_thread: Dict):
    """Handle pull request events."""
    action = payload["action"]
    pr = payload["pull_request"]

    slack = SlackService()

    messages = {
        "opened": f"🔀 **Pull Request Opened**\n<{pr['html_url']}|PR #{pr['number']}>\n{pr['title']}",
        "closed": f"{'🎉 **Merged**' if pr['merged'] else '❌ **Closed**'}\n<{pr['html_url']}|PR #{pr['number']}>\n{pr['title']}",
        "ready_for_review": f"👀 **Ready for Review**\n<{pr['html_url']}|PR #{pr['number']}>\n{pr['title']}"
    }

    message = messages.get(action)
    if message:
        await slack.post_message(
            slack_thread["channel_id"],
            message,
            thread_ts=slack_thread["thread_ts"]
        )


async def handle_workflow_event(payload: Dict, slack_thread: Dict):
    """Handle workflow run events."""
    workflow = payload["workflow_run"]
    conclusion = workflow.get("conclusion")

    slack = SlackService()

    if conclusion == "success":
        message = f"✅ **CI Checks Passed**\n<{workflow['html_url']}|View Workflow>"
    elif conclusion == "failure":
        message = f"❌ **CI Checks Failed**\n<{workflow['html_url']}|View Logs>"
    else:
        # In progress, skip
        return

    await slack.post_message(
        slack_thread["channel_id"],
        message,
        thread_ts=slack_thread["thread_ts"]
    )


def verify_github_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook signature."""
    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def extract_slack_thread_from_payload(payload: Dict) -> Optional[Dict]:
    """
    Extract Slack thread info from issue/PR body.

    Expected format in issue body:
    ---
    **Requested via Slack**
    - Thread: 1234567890.123456
    - Channel: C123ABC
    """
    body = ""

    if "issue" in payload:
        body = payload["issue"]["body"] or ""
    elif "pull_request" in payload:
        body = payload["pull_request"]["body"] or ""

    # Parse Slack metadata
    import re
    thread_match = re.search(r'Thread: ([\d.]+)', body)
    channel_match = re.search(r'Channel: (C[A-Z0-9]+)', body)

    if thread_match and channel_match:
        return {
            "thread_ts": thread_match.group(1),
            "channel_id": channel_match.group(1)
        }

    return None
```

---

## 5. Security Considerations

### 5.1 Token Management

#### Storage Strategy

```python
"""Secure token storage using encrypted environment variables."""
from cryptography.fernet import Fernet
from app.core.config import settings


class TokenManager:
    """Manage encrypted API tokens."""

    def __init__(self):
        # Encryption key stored in environment (rotate quarterly)
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())

    def encrypt_token(self, token: str) -> str:
        """Encrypt token for storage."""
        return self.cipher.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted: str) -> str:
        """Decrypt token for use."""
        return self.cipher.decrypt(encrypted.encode()).decode()


# Store encrypted tokens in Redis with TTL
class SlackTokenCache:
    """Cache Slack tokens with auto-rotation."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self.token_manager = TokenManager()

    async def store_token(
        self,
        team_id: str,
        token: str,
        ttl_seconds: int = 43200  # 12 hours
    ):
        """Store encrypted token with expiration."""
        encrypted = self.token_manager.encrypt_token(token)

        await self.redis.setex(
            f"slack_token:{team_id}",
            ttl_seconds,
            encrypted
        )

    async def get_token(self, team_id: str) -> Optional[str]:
        """Retrieve and decrypt token."""
        encrypted = await self.redis.get(f"slack_token:{team_id}")

        if not encrypted:
            return None

        return self.token_manager.decrypt_token(encrypted.decode())
```

#### Token Rotation

```yaml
# .github/workflows/rotate-tokens.yml
name: Rotate API Tokens

on:
  schedule:
    - cron: '0 0 1 */3 *'  # Quarterly (1st of every 3rd month)
  workflow_dispatch:

jobs:
  rotate-slack-token:
    runs-on: ubuntu-latest
    steps:
      - name: Generate new Slack token
        run: |
          # Slack tokens can't be auto-rotated via API
          # This workflow creates a GitHub issue to remind admins
          echo "Manual token rotation required for Slack"

      - name: Create reminder issue
        uses: actions/github-script@v7
        with:
          script: |
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '🔒 [SECURITY] Rotate Slack API Tokens',
              body: `**Quarterly Token Rotation Reminder**\n\nPlease rotate the following tokens:\n- Slack Bot Token\n- Slack App Token\n- GitHub Personal Access Token (for bot)\n\nSteps:\n1. Generate new tokens in respective admin panels\n2. Update GitHub Secrets\n3. Restart services\n4. Verify functionality\n\n**Deadline:** ${new Date(Date.now() + 7*24*60*60*1000).toISOString().split('T')[0]}`,
              labels: ['security', 'high-priority', 'ops']
            });
```

### 5.2 Rate Limiting

#### Slack API Rate Limits

```python
"""Rate limiting for Slack API calls."""
from app.core.redis_client import redis
from fastapi import HTTPException
import time


class SlackRateLimiter:
    """
    Implement Slack API rate limits.

    Slack Limits:
    - Tier 1: 1+ req/min
    - Tier 2: 20+ req/min
    - Tier 3: 50+ req/min
    - Tier 4: 100+ req/min

    We use conservative limit: 50 req/min per workspace
    """

    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_requests = 50
        self.window_seconds = 60

    async def check_limit(self, team_id: str) -> bool:
        """
        Check if request is within rate limit.

        Returns:
            True if allowed, raises HTTPException if rate limited
        """
        key = f"slack_ratelimit:{team_id}"

        # Increment counter
        count = await self.redis.incr(key)

        # Set expiry on first request in window
        if count == 1:
            await self.redis.expire(key, self.window_seconds)

        # Check limit
        if count > self.max_requests:
            ttl = await self.redis.ttl(key)
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Retry in {ttl} seconds."
            )

        return True

    async def get_remaining(self, team_id: str) -> int:
        """Get remaining requests in current window."""
        key = f"slack_ratelimit:{team_id}"
        count = await self.redis.get(key)

        if not count:
            return self.max_requests

        return max(0, self.max_requests - int(count))


# Middleware for rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to Slack webhook endpoints."""
    if request.url.path.startswith("/slack/"):
        # Extract team ID from request
        team_id = extract_team_id(request)

        # Check rate limit
        limiter = SlackRateLimiter(redis)
        await limiter.check_limit(team_id)

    response = await call_next(request)
    return response
```

#### User-Based Rate Limiting

```python
"""Per-user rate limiting to prevent abuse."""


class UserRateLimiter:
    """
    Limit requests per user to prevent spam.

    Limits:
    - 10 issue creations per hour per user
    - 5 auto-implementation requests per day per user
    """

    def __init__(self, redis_client):
        self.redis = redis_client

    async def check_issue_creation_limit(self, user_id: str) -> bool:
        """Check if user can create another issue."""
        key = f"user_issue_limit:{user_id}"
        count = await self.redis.incr(key)

        if count == 1:
            await self.redis.expire(key, 3600)  # 1 hour

        if count > 10:
            raise HTTPException(
                status_code=429,
                detail="You've reached the hourly limit of 10 issue creations. Please try again later."
            )

        return True

    async def check_auto_implement_limit(self, user_id: str) -> bool:
        """Check if user can request auto-implementation."""
        key = f"user_auto_implement_limit:{user_id}"
        count = await self.redis.incr(key)

        if count == 1:
            await self.redis.expire(key, 86400)  # 24 hours

        if count > 5:
            raise HTTPException(
                status_code=429,
                detail="You've reached the daily limit of 5 auto-implementation requests. Please try again tomorrow."
            )

        return True
```

### 5.3 Audit Logging

#### Comprehensive Activity Log

```python
"""Audit logging for all Slack/GitHub operations."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.db.base_class import Base


class AuditLog(Base):
    """Audit log for security tracking."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Who performed the action
    user_id = Column(String, nullable=False, index=True)  # Slack user ID
    user_email = Column(String, nullable=True)
    team_id = Column(String, nullable=False, index=True)  # Slack team ID

    # What action was performed
    action_type = Column(String, nullable=False, index=True)  # "issue_create", "pr_create", "auto_implement"
    resource_type = Column(String, nullable=False)  # "issue", "pr", "workflow"
    resource_id = Column(String, nullable=True)  # GitHub issue/PR number

    # Context
    slack_channel = Column(String, nullable=True)
    slack_thread_ts = Column(String, nullable=True)
    github_repo = Column(String, nullable=False)

    # Details (JSON)
    metadata = Column(JSON, nullable=True)

    # Result
    status = Column(String, nullable=False)  # "success", "failure", "rate_limited"
    error_message = Column(String, nullable=True)


async def log_action(
    user_id: str,
    action_type: str,
    resource_type: str,
    status: str,
    **kwargs
):
    """Log user action to audit trail."""
    log_entry = AuditLog(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        status=status,
        **kwargs
    )

    db.add(log_entry)
    await db.commit()

    # Also log to external SIEM if configured
    if settings.SIEM_ENABLED:
        await send_to_siem(log_entry)


# Usage example
@app.post("/slack/events")
async def handle_slack_event(request: Request):
    """Handle Slack event with audit logging."""
    payload = await request.json()

    try:
        # Process event
        result = await process_event(payload)

        # Log success
        await log_action(
            user_id=payload["event"]["user"],
            action_type="slack_request",
            resource_type="issue",
            status="success",
            metadata={"event_type": payload["event"]["type"]}
        )

        return {"ok": True}

    except Exception as e:
        # Log failure
        await log_action(
            user_id=payload["event"]["user"],
            action_type="slack_request",
            resource_type="issue",
            status="failure",
            error_message=str(e)
        )

        raise
```

#### Security Monitoring Queries

```sql
-- Detect unusual activity patterns

-- 1. Users with excessive failed requests (possible attack)
SELECT
    user_id,
    COUNT(*) as failed_attempts,
    COUNT(DISTINCT action_type) as unique_actions
FROM audit_logs
WHERE
    status = 'failure'
    AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY user_id
HAVING COUNT(*) > 10
ORDER BY failed_attempts DESC;

-- 2. Rate-limited users (hitting limits frequently)
SELECT
    user_id,
    COUNT(*) as rate_limit_hits,
    DATE_TRUNC('hour', timestamp) as hour
FROM audit_logs
WHERE
    status = 'rate_limited'
    AND timestamp > NOW() - INTERVAL '24 hours'
GROUP BY user_id, hour
HAVING COUNT(*) > 5;

-- 3. Unusual auto-implementation patterns
SELECT
    user_id,
    COUNT(*) as auto_implement_count,
    AVG(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_rate
FROM audit_logs
WHERE
    action_type = 'auto_implement'
    AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY user_id
ORDER BY auto_implement_count DESC;
```

### 5.4 Input Validation & Sanitization

```python
"""Input validation for Slack messages."""
from pydantic import BaseModel, validator, Field
import re


class SlackMessageRequest(BaseModel):
    """Validated Slack message request."""

    user_id: str = Field(..., regex=r'^U[A-Z0-9]{10}$')
    channel_id: str = Field(..., regex=r'^C[A-Z0-9]{10}$')
    text: str = Field(..., min_length=1, max_length=3000)
    thread_ts: Optional[str] = Field(None, regex=r'^\d+\.\d+$')

    @validator('text')
    def sanitize_text(cls, v):
        """Remove potentially malicious content."""
        # Remove script tags
        v = re.sub(r'<script[^>]*>.*?</script>', '', v, flags=re.DOTALL | re.IGNORECASE)

        # Remove SQL injection attempts
        dangerous_patterns = [
            r';\s*DROP\s+TABLE',
            r';\s*DELETE\s+FROM',
            r'UNION\s+SELECT',
            r'<iframe',
            r'javascript:',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Invalid input detected")

        # Trim whitespace
        v = v.strip()

        return v

    @validator('user_id', 'channel_id')
    def validate_slack_ids(cls, v):
        """Ensure Slack IDs are valid format."""
        if not re.match(r'^[UC][A-Z0-9]{10}$', v):
            raise ValueError("Invalid Slack ID format")
        return v


# Use in endpoint
@app.post("/slack/events")
async def handle_slack_event(request: Request):
    """Handle validated Slack event."""
    payload = await request.json()

    # Validate with Pydantic
    try:
        validated = SlackMessageRequest(**payload["event"])
    except ValidationError as e:
        logger.warning(f"Invalid Slack event: {e}")
        return {"ok": False, "error": "Invalid request"}

    # Process validated data
    await process_slack_message(validated)
```

---

## 6. Implementation Guide

### 6.1 Prerequisites

```bash
# Required accounts and tokens
- Slack Workspace (admin access)
- GitHub Organization (admin or owner)
- Anthropic API key (for Claude)
- Redis instance (for caching/queue)

# Required secrets
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...
GITHUB_TOKEN=ghp_...
GITHUB_WEBHOOK_SECRET=...
ANTHROPIC_API_KEY=sk-ant-...
ENCRYPTION_KEY=...  # Generate with: python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

### 6.2 Step-by-Step Setup

#### Step 1: Create Slack App

```bash
# 1. Go to https://api.slack.com/apps
# 2. Click "Create New App" → "From scratch"
# 3. Name: "Code Assistant Bot"
# 4. Workspace: Your workspace

# 5. Configure OAuth Scopes (Settings → OAuth & Permissions)
#    Add bot scopes from section 2.1

# 6. Install app to workspace
#    Get SLACK_BOT_TOKEN (starts with xoxb-)

# 7. Enable Events (Settings → Event Subscriptions)
#    Request URL: https://your-domain.com/slack/events
#    Subscribe to events from section 2.2

# 8. Create slash commands (Settings → Slash Commands)
#    /create-issue → https://your-domain.com/slack/commands/create-issue
#    /start-pr → https://your-domain.com/slack/commands/start-pr
```

#### Step 2: Deploy Backend Service

```bash
# Clone repo
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

# Create .env file
cat > .env << EOF
# Slack
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_SIGNING_SECRET=your-signing-secret

# GitHub
GITHUB_TOKEN=ghp_your-token
GITHUB_REPO=your-org/residency-scheduler
GITHUB_WEBHOOK_SECRET=your-webhook-secret

# Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
ENCRYPTION_KEY=your-fernet-key
SECRET_KEY=your-app-secret-key
EOF

# Install dependencies
cd backend
pip install -r requirements.txt

# Add new dependencies for Slack integration
pip install slack-bolt python-github anthropic redis celery

# Run migrations
alembic upgrade head

# Start services
# Terminal 1: Backend API
uvicorn app.main:app --reload

# Terminal 2: Celery worker
celery -A app.celery_app worker --loglevel=info

# Terminal 3: Celery beat (scheduler)
celery -A app.celery_app beat --loglevel=info

# Terminal 4: Redis
redis-server
```

#### Step 3: Configure GitHub Webhooks

```bash
# GitHub Repository → Settings → Webhooks → Add webhook

Payload URL: https://your-domain.com/webhooks/github
Content type: application/json
Secret: your-webhook-secret

Events to trigger:
☑ Pull requests
☑ Workflow runs
☑ Check suites
☑ Pull request reviews
☑ Issues
```

#### Step 4: Test Integration

```bash
# 1. Test Slack event handling
curl -X POST https://your-domain.com/slack/events \
  -H "Content-Type: application/json" \
  -d '{
    "token": "verification_token",
    "type": "url_verification",
    "challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"
  }'

# Should return: {"challenge": "3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"}

# 2. Test slash command
# In Slack: /create-issue bug Test issue

# 3. Test mention
# In Slack: @bot implement user authentication

# 4. Test GitHub webhook
# Create a test PR in your repo
# Should see message in Slack thread
```

### 6.3 Production Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    env_file: .env
    ports:
      - "8000:8000"
    depends_on:
      - redis
      - postgres
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  celery-worker:
    build: ./backend
    env_file: .env
    depends_on:
      - redis
      - postgres
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4

  celery-beat:
    build: ./backend
    env_file: .env
    depends_on:
      - redis
    command: celery -A app.celery_app beat --loglevel=info

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  postgres:
    image: postgres:15-alpine
    env_file: .env
    volumes:
      - postgres-data:/var/lib/postgresql/data

volumes:
  redis-data:
  postgres-data:
```

---

## 7. Performance & Scalability

### 7.1 Performance Targets

| Metric | Target | Current (Estimated) |
|--------|--------|---------------------|
| Slack event response time | < 3 seconds | ~2 seconds |
| Intent parsing (Claude) | < 5 seconds | ~3-4 seconds |
| GitHub issue creation | < 2 seconds | ~1 second |
| Workflow trigger | < 1 second | ~500ms |
| End-to-end (mention → issue) | < 10 seconds | ~6-8 seconds |

### 7.2 Scaling Strategy

```
┌─────────────────────────────────────────────────────────┐
│                   Load Balancer (Nginx)                 │
└────────────────┬──────────────────┬─────────────────────┘
                 │                  │
         ┌───────▼───────┐  ┌───────▼───────┐
         │  Backend API  │  │  Backend API  │  (Horizontal scaling)
         │   Instance 1  │  │   Instance 2  │
         └───────┬───────┘  └───────┬───────┘
                 │                  │
         ┌───────▼──────────────────▼───────┐
         │         Redis (Cluster)          │
         │  • Session cache                 │
         │  • Rate limiting                 │
         │  • Celery broker                 │
         └───────┬──────────────────────────┘
                 │
         ┌───────▼───────┐  ┌───────────────┐
         │ Celery Worker │  │ Celery Worker │  (Auto-scale based on queue depth)
         │   Pool 1      │  │   Pool 2      │
         └───────────────┘  └───────────────┘
```

#### Auto-Scaling Configuration

```yaml
# Kubernetes HPA (Horizontal Pod Autoscaler)
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: celery_queue_depth
      target:
        type: AverageValue
        averageValue: "50"  # Scale up if queue > 50 tasks
```

### 7.3 Caching Strategy

```python
"""Multi-layer caching for performance."""
from functools import lru_cache
from app.core.redis_client import redis


# Layer 1: In-memory cache (LRU)
@lru_cache(maxsize=1000)
def get_user_info(user_id: str) -> Dict:
    """Get Slack user info (cached in memory)."""
    return slack_api.users_info(user=user_id)


# Layer 2: Redis cache (distributed)
async def get_issue_template(issue_type: str) -> str:
    """Get GitHub issue template with Redis caching."""
    cache_key = f"issue_template:{issue_type}"

    # Try cache first
    cached = await redis.get(cache_key)
    if cached:
        return cached.decode()

    # Fetch from GitHub
    template = await github.get_issue_template(issue_type)

    # Cache for 1 hour
    await redis.setex(cache_key, 3600, template)

    return template


# Layer 3: Claude response caching (expensive API calls)
async def parse_intent_cached(message: str) -> Dict:
    """Parse intent with aggressive caching."""
    # Hash message for cache key
    message_hash = hashlib.sha256(message.encode()).hexdigest()
    cache_key = f"intent_parse:{message_hash}"

    # Try cache (24 hour TTL)
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached.decode())

    # Call Claude API (expensive)
    result = await claude_api.parse_intent(message)

    # Cache for 24 hours
    await redis.setex(cache_key, 86400, json.dumps(result))

    return result
```

---

## 8. Monitoring & Observability

### 8.1 Prometheus Metrics

```python
"""Prometheus metrics for Slack integration."""
from prometheus_client import Counter, Histogram, Gauge


# Request counters
slack_events_total = Counter(
    'slack_events_total',
    'Total Slack events received',
    ['event_type', 'status']
)

github_api_calls_total = Counter(
    'github_api_calls_total',
    'Total GitHub API calls',
    ['operation', 'status']
)

# Latency histograms
slack_event_duration = Histogram(
    'slack_event_processing_seconds',
    'Time to process Slack event',
    ['event_type'],
    buckets=[0.5, 1, 2, 5, 10, 30]
)

claude_api_duration = Histogram(
    'claude_api_call_seconds',
    'Time for Claude API calls',
    ['operation'],
    buckets=[1, 2, 5, 10, 20, 30]
)

# Queue depth gauge
celery_queue_depth = Gauge(
    'celery_queue_depth',
    'Number of tasks in Celery queue',
    ['queue_name']
)


# Usage
@slack_event_duration.labels(event_type='app_mention').time()
async def handle_app_mention(event: Dict):
    """Handle @mention with metrics."""
    try:
        result = await process_mention(event)
        slack_events_total.labels(event_type='app_mention', status='success').inc()
        return result
    except Exception as e:
        slack_events_total.labels(event_type='app_mention', status='failure').inc()
        raise
```

### 8.2 Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Slack Integration Monitoring",
    "panels": [
      {
        "title": "Slack Events per Minute",
        "targets": [
          {
            "expr": "rate(slack_events_total[5m])"
          }
        ]
      },
      {
        "title": "Event Processing Latency (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(slack_event_duration_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Celery Queue Depth",
        "targets": [
          {
            "expr": "celery_queue_depth"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {
                "params": [100],
                "type": "gt"
              },
              "query": {"params": ["A", "5m", "now"]},
              "type": "query"
            }
          ],
          "name": "High Celery Queue Depth"
        }
      },
      {
        "title": "GitHub API Rate Limit Remaining",
        "targets": [
          {
            "expr": "github_ratelimit_remaining"
          }
        ]
      }
    ]
  }
}
```

### 8.3 Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: slack_integration
    interval: 30s
    rules:
      - alert: HighSlackEventFailureRate
        expr: rate(slack_events_total{status="failure"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High Slack event failure rate"
          description: "{{ $value }} events/sec failing for 5 minutes"

      - alert: SlowClaudeAPIResponse
        expr: histogram_quantile(0.95, rate(claude_api_duration_bucket[5m])) > 10
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Claude API responding slowly"
          description: "p95 latency is {{ $value }} seconds"

      - alert: CeleryQueueBacklog
        expr: celery_queue_depth > 200
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Celery queue has {{ $value }} tasks"
          description: "Scale up workers immediately"

      - alert: GitHubRateLimitLow
        expr: github_ratelimit_remaining < 100
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "GitHub API rate limit running low"
          description: "Only {{ $value }} requests remaining"
```

---

## Implementation Checklist

### Phase 1: Foundation (Week 1)

- [ ] Create Slack app with OAuth scopes
- [ ] Set up backend webhook endpoints (`/slack/events`, `/webhooks/github`)
- [ ] Implement signature verification (Slack + GitHub)
- [ ] Configure Redis for caching and Celery
- [ ] Set up Celery workers
- [ ] Create audit logging database tables
- [ ] Implement rate limiting (Slack API + user-based)
- [ ] Write integration tests for webhook handlers

**Estimated Time:** 2-3 days
**Risk:** Low (foundation work)

### Phase 2: Core Features (Week 2)

- [ ] Implement Claude intent parser
- [ ] Build GitHub integration service (issue/PR creation)
- [ ] Create slash commands (`/create-issue`, `/start-pr`)
- [ ] Implement simple issue creation flow (Pattern 1)
- [ ] Add Slack message formatting (blocks, buttons)
- [ ] Test end-to-end: Slack → Claude → GitHub
- [ ] Create unit tests for intent parsing
- [ ] Create integration tests for GitHub service

**Estimated Time:** 4-5 days
**Risk:** Medium (Claude API integration)

### Phase 3: Autonomous Implementation (Week 3)

- [ ] Create `autonomous-issue-resolver.yml` workflow
- [ ] Implement progress tracking system
- [ ] Build GitHub webhook → Slack update handler
- [ ] Add error handling and escalation (Pattern 4)
- [ ] Create PR review → Slack notification
- [ ] Implement workflow status checks
- [ ] Test auto-implementation with real issues
- [ ] Document autonomous workflow usage

**Estimated Time:** 5-6 days
**Risk:** High (complex automation)

### Phase 4: Security & Monitoring (Week 4)

- [ ] Implement token encryption and storage
- [ ] Set up token rotation workflow
- [ ] Configure audit logging for all operations
- [ ] Add Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Set up alerting rules
- [ ] Conduct security audit
- [ ] Penetration testing (input validation)
- [ ] Load testing (100 concurrent Slack events)

**Estimated Time:** 3-4 days
**Risk:** Medium (security critical)

### Phase 5: Production Deployment (Week 5)

- [ ] Set up production environment (Docker Compose or K8s)
- [ ] Configure auto-scaling (HPA)
- [ ] Deploy to staging environment
- [ ] Run end-to-end tests in staging
- [ ] Configure DNS and SSL certificates
- [ ] Deploy to production
- [ ] Monitor for 48 hours
- [ ] Create runbook for operations team
- [ ] Train team on using Slack bot

**Estimated Time:** 2-3 days
**Risk:** Medium (deployment complexity)

### Optional Enhancements (Future)

- [ ] Multi-workspace support (different Slack teams)
- [ ] Custom intent training (fine-tune Claude on project data)
- [ ] Slack app directory submission
- [ ] Advanced analytics dashboard
- [ ] Integration with Jira/Linear (issue sync)
- [ ] Voice command support (Slack Huddle)
- [ ] Proactive suggestions ("I noticed X, should I fix it?")

---

## Conclusion

This Slack integration architecture provides a comprehensive natural language interface for autonomous code development. By combining Slack's excellent UX, Claude's intent parsing, and GitHub Actions' automation capabilities, developers can request features in plain English and watch as the system autonomously implements them.

### Key Benefits

1. **Developer Productivity:** Reduce friction from idea to implementation
2. **Transparency:** All activity logged and visible in Slack threads
3. **Accessibility:** No need to learn Git/GitHub for simple requests
4. **Scalability:** Handles 100+ concurrent requests with auto-scaling
5. **Security:** Comprehensive audit logging, rate limiting, and input validation

### Success Metrics

Track these KPIs after deployment:

- **Adoption Rate:** % of team using Slack bot weekly
- **Issue Creation Time:** Reduced from ~5 min to ~10 sec
- **Auto-Implementation Success Rate:** Target 70%+ for small tasks
- **User Satisfaction:** NPS score > 8/10
- **Cost Savings:** Reduced developer time on repetitive tasks

### Next Steps

1. **Prototype:** Build MVP with basic issue creation (Phase 1-2)
2. **Beta Test:** Roll out to small team (5-10 users)
3. **Iterate:** Gather feedback and refine intent parsing
4. **Scale:** Deploy to full engineering team
5. **Expand:** Add advanced features based on usage patterns

---

**Document Version:** 1.0
**Last Updated:** 2025-12-19
**Maintained By:** Autonomous Systems Team (Terminal 5)
**Review Schedule:** Monthly for first quarter, then quarterly
**Contact:** For questions or issues, create a GitHub issue with label `slack-integration`
