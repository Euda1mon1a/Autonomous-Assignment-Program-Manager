# Claude Code Slack Integration Guide

## Overview

Claude Code Slack integration is a beta feature announced by Anthropic in December 2024 that enables developers to delegate coding tasks directly from Slack conversations. When you mention `@Claude` in a Slack channel with a coding request, Claude automatically analyzes the message, gathers context from the thread, and creates a Claude Code session on the web to handle the task.

### What It Provides

- **Automated Task Detection**: Claude analyzes your messages to determine if they're coding tasks and routes them appropriately
- **Context-Aware Sessions**: Gathers information from recent channel and thread messages to understand the full conversation
- **Repository Auto-Selection**: Automatically chooses which authenticated repository to work on based on context
- **Real-Time Updates**: Posts progress updates back to your Slack thread as work progresses
- **Seamless PR Creation**: Provides direct links to view the full session and create pull requests upon completion

### Architecture

The integration works as a bridge between Slack conversations and Claude Code web sessions:

```
Slack Channel → @Claude mention → Task Analysis → Claude Code Session → GitHub Repository
                                                         ↓
                                         Status Updates to Slack Thread
                                                         ↓
                                            Session Link + PR Creation
```

## Comparison with Existing n8n Slack Workflows

This project already implements custom Slack workflows using n8n. Here's how Claude Code integration compares:

### Current n8n Workflows

Located in `/home/user/Autonomous-Assignment-Program-Manager/n8n/workflows/`:

1. **slack_approve.json**: Custom `/scheduler approve` command
   - Approves or denies scheduling tasks via token-based authentication
   - Directly calls backend API endpoints
   - Returns formatted status updates with Block Kit

2. **slack_fix_it.json**: Custom `/scheduler fix-it` command
   - Triggers automated task recovery and retry logic
   - Supports parameters: mode, max_retries, auto-approve
   - Initiates background processes

3. **slack_sitrep.json**: Custom `/scheduler sitrep` command
   - Fetches and displays resilience report from backend API
   - Shows task metrics, success rates, and system health
   - Formatted with Block Kit for rich visualization

### Key Differences

| Feature | n8n Workflows | Claude Code Integration |
|---------|---------------|------------------------|
| **Purpose** | Direct API orchestration & status reporting | AI-powered code generation & debugging |
| **Trigger** | Slash commands (`/scheduler`) | @mentions (`@Claude`) |
| **Task Type** | Predefined operations (approve, fix, report) | Open-ended coding tasks |
| **Backend** | Custom REST API endpoints | Claude Code web sessions + GitHub |
| **Output** | JSON API responses formatted as Slack blocks | Code changes, PRs, and session transcripts |
| **Context** | User-provided parameters | Thread conversation history |
| **Automation** | Workflow-based (n8n visual programming) | AI-driven (natural language understanding) |

### When to Use Which

**Use n8n Workflows for:**
- Operational commands (approvals, status checks, triggers)
- Predefined business logic and workflows
- Direct database or API interactions
- Real-time system monitoring and alerts
- Repeatable, structured processes

**Use Claude Code Integration for:**
- Bug investigation and fixes
- Feature implementation from verbal descriptions
- Code refactoring and improvements
- Emergency debugging with conversational context
- Exploratory tasks requiring AI judgment

**Complementary Usage:**
The two approaches are complementary. n8n workflows handle operational automation while Claude Code handles development tasks. For example:
1. Use `/scheduler sitrep` to identify failing tasks
2. Discuss the issue in Slack thread
3. Tag `@Claude` to debug and fix the code
4. Use `/scheduler fix-it` to retry after the fix is deployed

## Prerequisites

### Required Accounts & Access

1. **Claude Account**
   - Pro, Max, Team, or Enterprise plan
   - Access to Claude Code on the web (visit [claude.ai/code](https://claude.ai/code))

2. **Slack Workspace**
   - Paid Slack plan (Standard, Plus, or Enterprise Grid)
   - Workspace admin privileges for initial installation

3. **GitHub Account**
   - Connected to Claude Code
   - At least one authenticated repository
   - Write permissions to create branches and pull requests

4. **Team Requirements**
   - Team or Enterprise Claude plan for multi-user access
   - Each user must authenticate their individual Claude account

### Verification Checklist

Before proceeding, verify:
- [ ] You have a paid Claude plan with Claude Code enabled
- [ ] You can access [claude.ai/code](https://claude.ai/code) and see the interface
- [ ] Your GitHub account is connected to Claude Code
- [ ] Your Slack workspace is on a paid plan
- [ ] You have workspace admin access (for initial setup)

## Step-by-Step Installation

### Step 1: Install Claude App in Slack

**For Workspace Administrators:**

1. Navigate to the [Slack App Marketplace](https://slack.com/apps)
2. Search for "Claude"
3. Click "Add to Slack"
4. Review the requested permissions:
   - Read messages in channels where Claude is mentioned
   - Post messages and updates
   - Access user information for attribution
5. Click "Allow" to approve the installation
6. Configure which channels Claude can access (if applicable)

### Step 2: Individual User Authentication

**For Each Team Member:**

1. In Slack, navigate to the **Apps** section in the left sidebar
2. Find and click on **Claude**
3. Click **Home** tab in the Claude app
4. Click **Connect Claude Account**
5. You'll be redirected to authenticate:
   - Log in with your Claude account credentials
   - Authorize the Slack integration
   - Grant permissions to access Claude Code
6. Return to Slack - you should see a success message

### Step 3: Configure Claude Code on the Web

1. Visit [claude.ai/code](https://claude.ai/code)
2. Click **Sign in** and authenticate
3. Navigate to **Settings** → **Integrations**
4. Click **Connect GitHub**
5. Authorize the GitHub app:
   - Select repositories to grant access
   - Choose at least the repositories you want Claude to work on
   - Confirm the installation
6. Verify repositories appear in your Claude Code dashboard

### Step 4: Configure Routing Mode

1. In Slack, open the **Claude app**
2. Go to the **Home** tab
3. Find the **Routing Mode** setting
4. Choose your preferred mode:
   - **Code + Chat**: Claude decides whether to route to Code or Chat
   - **Code Only**: All @mentions create Claude Code sessions
5. Save your preference

**Routing Mode Explained:**
- In **Code + Chat** mode, if Claude routes to Chat but you wanted code, click "Retry as Code"
- In **Code Only** mode, every @mention creates a coding session (best for dedicated dev channels)

### Step 5: Test the Integration

1. Create a test channel or use an existing development channel
2. Invite the Claude app: type `/invite @Claude`
3. Post a simple coding task:
   ```
   @Claude can you add a simple health check endpoint to our API?
   ```
4. Claude should respond with:
   - Acknowledgment of the task
   - Repository selection
   - Link to the Claude Code session
5. Monitor the thread for progress updates
6. When complete, you'll receive:
   - Session summary
   - "View Session" button
   - "Create PR" button (if changes were made)

## Example Use Cases for Residency Scheduling Context

Based on this project's architecture (Autonomous Assignment Program Manager for healthcare residency scheduling), here are practical examples:

### 1. Bug Investigation from Slack Reports

**Scenario:** Someone reports a scheduling conflict issue in Slack.

```
Team Member: "Hey, the scheduler assigned Dr. Smith to two shifts on 12/25.
Patient assignment #1234 and coverage #5678."

@Claude can you investigate why the scheduler allowed this double-booking
and fix the validation logic?
```

**Claude's Actions:**
- Gathers thread context (dates, assignment IDs)
- Opens a Claude Code session
- Searches for scheduling validation code
- Identifies missing conflict check
- Implements fix with tests
- Creates PR with detailed explanation

### 2. Feature Enhancement from Discussion

**Scenario:** Team discusses a needed feature conversationally.

```
Team discussion:
Person A: "We need to handle Hawaii-specific holidays differently"
Person B: "Yeah, Prince Kuhio Day and King Kamehameha Day aren't in our system"
Person C: "And we should mark them as required coverage days"

@Claude based on this discussion, can you add support for Hawaii state holidays
with required coverage flags? Look at how we handle federal holidays as a template.
```

**Claude's Actions:**
- Reviews conversation for requirements
- Finds existing holiday handling code
- Adds Hawaii state holidays to configuration
- Updates coverage requirement logic
- Creates tests for new holidays
- Generates PR with documentation

### 3. Quick Code Review Fix

**Scenario:** PR review discussion in Slack identifies an issue.

```
Reviewer shares in Slack:
"In PR #245, the absence request validation doesn't check if the date is in the past.
Someone could request retroactive time off."

@Claude can you add validation to the absence request endpoint to reject
requests with start dates before today?
```

**Claude's Actions:**
- Checks out the PR branch
- Locates absence validation code
- Adds date comparison logic
- Writes unit tests for past date rejection
- Updates the PR with new commits

### 4. Emergency Debugging with Error Context

**Scenario:** Production error gets posted to Slack.

```
Alert:
"500 Error in /api/scheduler/swap endpoint
Error: KeyError: 'resident_id' in swap_validation.py line 145"

Full traceback: [paste]

@Claude this is breaking shift swap requests. Can you debug and fix ASAP?
```

**Claude's Actions:**
- Analyzes error message and stack trace
- Opens the failing file at the specified line
- Identifies missing null check
- Implements defensive coding fix
- Adds error handling and logging
- Creates hotfix PR

### 5. Documentation from API Endpoint

**Scenario:** Need API documentation for a specific endpoint.

```
@Claude can you look at the /api/resilience/report endpoint and create
OpenAPI documentation for it? Include the response schema and example responses.
```

**Claude's Actions:**
- Finds the endpoint implementation
- Analyzes response structure
- Generates OpenAPI spec
- Adds example responses
- Creates documentation PR

### 6. Integration with Existing Workflows

**Scenario:** Combining Claude Code with n8n workflows.

```
[After running /scheduler sitrep]
Sitrep shows: 5 failed tasks in retry loop

Team discussion: "These keep failing because of the timezone conversion bug"

@Claude can you look at the timezone handling in our task scheduler?
The Hawaii → UTC conversion seems broken for DST boundaries.
```

**Claude's Actions:**
- Reviews timezone conversion code
- Identifies DST handling issue
- Implements proper timezone library usage
- Adds comprehensive timezone tests
- Creates PR with fix
- Team can then run `/scheduler fix-it` to retry failed tasks

## Security Considerations

### Authentication & Authorization

1. **Individual Account Linking**
   - Each user must authenticate their own Claude account
   - Slack identity linked to Claude identity
   - No shared credentials or API keys

2. **Repository Access Control**
   - Claude can only access GitHub repositories you've explicitly authorized
   - Repository permissions inherited from your GitHub account
   - Workspace admins cannot access users' private repos through Claude

3. **Token Management**
   - Slack bot tokens (xoxb-*) stored securely by Anthropic
   - OAuth tokens refreshed automatically
   - Tokens revocable via Slack App settings

### Data Privacy

1. **Message Context**
   - Claude reads messages in threads where it's mentioned
   - Only processes channels where the app is invited
   - Does not monitor or index all workspace messages

2. **Code Access**
   - Claude Code sessions use your authenticated repositories
   - No code sharing between different users' sessions
   - Session transcripts accessible only to the user who initiated them

3. **Data Retention**
   - Slack message context used only for the active session
   - Not permanently stored by Anthropic (follows standard Claude policies)
   - Session history follows Claude Code retention policies

### Best Practices

1. **Channel Separation**
   - Create dedicated development channels for code-related discussions
   - Don't invite Claude to channels with sensitive non-code discussions
   - Use private channels for confidential work

2. **Sensitive Data Handling**
   - Never paste API keys, passwords, or credentials in Slack
   - Use environment variables and secret management
   - Review Claude's proposed changes before merging PRs

3. **Access Auditing**
   - Monitor which repositories are connected to Claude Code
   - Periodically review GitHub app permissions
   - Check Slack audit logs for Claude app activity

4. **Least Privilege**
   - Only grant Claude access to necessary repositories
   - Use branch protection rules on main branches
   - Require PR reviews even for Claude-generated code

### Security Comparison: Official Integration vs. MCP Server

**Official Claude Code in Slack** (Recommended):
- ✅ Managed authentication by Anthropic
- ✅ Encrypted connections (TLS)
- ✅ OAuth-based authorization
- ✅ Enterprise security compliance
- ✅ Automatic token rotation
- ❌ Requires paid Slack plan
- ❌ Team/Enterprise Claude plan only

**Self-Hosted MCP Server** (Advanced):
- ⚠️ Manual security configuration required
- ⚠️ Plaintext config storage by default
- ⚠️ No built-in audit trails
- ⚠️ Requires infrastructure management
- ✅ Full control over deployment
- ✅ Can work with free Slack plans
- ❌ Significant security burden

**For Production Use:** Use the official integration unless you have specific requirements and dedicated security expertise.

### Incident Response

If you suspect unauthorized access:

1. **Immediate Actions:**
   - Revoke Claude app from Slack workspace (workspace admin)
   - Disconnect GitHub repositories from Claude Code
   - Rotate any API keys that may have been exposed

2. **Investigation:**
   - Review Slack audit logs for Claude app activity
   - Check GitHub audit logs for PR activity
   - Review Claude Code session history

3. **Recovery:**
   - Re-authenticate with fresh tokens
   - Re-configure with tighter permissions
   - Document the incident and lessons learned

## Limitations and Caveats

### Platform Limitations

1. **GitHub Only**
   - Currently only supports GitHub repositories
   - No GitLab, Bitbucket, or other Git providers
   - Self-hosted GitHub Enterprise may have limitations

2. **Channel Restrictions**
   - Only works in channels (public or private)
   - Does NOT work in direct messages (DMs)
   - Does NOT work in group DMs
   - Must be explicitly invited to each channel

3. **One PR Per Session**
   - Each Claude Code session creates a single PR
   - Cannot create multiple PRs in one session
   - For multi-repo changes, need multiple sessions

### Plan & Usage Limits

1. **Availability**
   - Beta feature - may change or be discontinued
   - Only available for Team and Enterprise Claude plans
   - Requires Claude Code web access (not CLI-only)

2. **Rate Limits**
   - Subject to your Claude plan's usage limits
   - Each coding session counts toward your limit
   - Complex tasks consume more of your quota
   - No additional charges beyond normal Claude pricing

3. **Slack Requirements**
   - Paid Slack plan required (Standard, Plus, or Enterprise Grid)
   - Free Slack workspaces cannot install the Claude app
   - Workspace admin must approve installation

### Functional Limitations

1. **Context Gathering**
   - Limited to recent messages in thread
   - Cannot access messages before Claude was invited
   - No access to private threads where not mentioned
   - Cannot read files or attachments directly (must be described)

2. **Task Complexity**
   - Best for focused, single-purpose tasks
   - Large refactors may hit token limits
   - Multi-step workflows better handled in web interface
   - Cannot maintain state across multiple sessions

3. **Repository Context**
   - Claude chooses repository based on context
   - May misidentify repository if multiple projects discussed
   - Use "Change Repo" button if wrong repository selected
   - Cannot work on multiple repositories simultaneously

4. **Code Review**
   - Claude-generated code requires human review
   - May not understand full project context
   - Can miss edge cases or business logic nuances
   - Should not auto-merge without review

### Integration-Specific Caveats

1. **Routing Ambiguity**
   - In "Code + Chat" mode, Claude may route incorrectly
   - Use "Retry as Code" button if misrouted
   - Be explicit: "this is a coding task" helps routing
   - Consider "Code Only" mode for dedicated dev channels

2. **Async Nature**
   - Sessions run asynchronously
   - Status updates may have delays
   - Cannot interrupt or redirect mid-session
   - Must wait for completion or cancel entirely

3. **Error Handling**
   - Authentication errors may require re-linking accounts
   - GitHub API failures may cause session failures
   - Slack notification failures won't stop the session
   - Check Claude Code web interface if Slack updates stop

### Comparison with Direct Web Usage

**Advantages of Slack Integration:**
- Conversation context automatically included
- Team visibility into coding tasks
- Easier handoff between discussion and implementation
- Status updates visible to stakeholders

**Disadvantages of Slack Integration:**
- Less control over session parameters
- Cannot inspect code in real-time
- Limited ability to iterate on changes
- Must use web interface for complex interactions

**Recommendation:** Use Slack integration for:
- Initial task creation from discussions
- Quick fixes and small features
- Situations requiring team visibility

Use web interface directly for:
- Complex multi-step tasks
- Iterative development
- Large refactors
- Learning and exploration

## Troubleshooting

### Claude Doesn't Respond to @mentions

**Possible Causes:**
- Claude app not invited to channel: Use `/invite @Claude`
- User account not authenticated: Check Claude App Home → "Connect Claude Account"
- Slack workspace not on paid plan
- Workspace admin hasn't approved Claude app

### "Retry as Code" Button Appears

**Meaning:** Claude routed your request to Chat instead of Code

**Solutions:**
- Click "Retry as Code" to force a coding session
- Be more explicit: "this is a coding task" or "write code to..."
- Switch to "Code Only" routing mode for dev channels

### Wrong Repository Selected

**Solutions:**
- Click "Change Repo" button in Claude's response
- Be explicit in your request: "in the scheduler-api repository..."
- Ensure the desired repository is connected in Claude Code settings

### Session Fails to Start

**Check:**
- GitHub repository access: Visit claude.ai/code → Settings
- Repository permissions: Ensure write access for PR creation
- Claude Code web access: Try creating a session directly at claude.ai/code
- Rate limits: Check your Claude plan usage

### No Status Updates in Slack

**Check:**
- Slack notifications enabled for Claude app
- Session still running: Check claude.ai/code for session status
- Slack API connectivity issues (check Slack status page)
- Thread not muted or archived

## Additional Resources

### Official Documentation
- [Claude Code in Slack Docs](https://code.claude.com/docs/en/slack)
- [Claude and Slack Overview](https://claude.com/claude-and-slack)
- [Claude Code and Slack Blog Post](https://claude.com/blog/claude-code-and-slack)

### Alternative Integration Methods
- [MCP Slack Server (atlasfutures)](https://github.com/atlasfutures/claude-mcp-slack) - Self-hosted MCP server
- [Slack MCP Server Guide (Composio)](https://composio.dev/blog/how-to-use-slack-mcp-server-with-claude-flawlessly)
- [Community Slack Bot (mpociot)](https://github.com/mpociot/claude-code-slack-bot) - Open source alternative

### News & Analysis
- [TechCrunch: Claude Code is coming to Slack](https://techcrunch.com/2025/12/08/claude-code-is-coming-to-slack-and-thats-a-bigger-deal-than-it-sounds/)
- [VentureBeat: Anthropic's Claude Code can now read your Slack messages](https://venturebeat.com/ai/anthropics-claude-code-can-now-read-your-slack-messages-and-write-code-for)
- [IT Pro: How to use Claude Code in Slack](https://www.itpro.com/software/development/claude-code-is-coming-to-slack-heres-how-to-use-it-what-it-can-do-and-how-to-get-access)

### Related Project Resources
- `/home/user/Autonomous-Assignment-Program-Manager/docs/guides/user-workflows.md` - User workflow documentation
- `/home/user/Autonomous-Assignment-Program-Manager/docs/guides/resilience-framework.md` - Resilience and error handling
- `/home/user/Autonomous-Assignment-Program-Manager/n8n/workflows/` - Existing n8n Slack integrations

---

## Revision History

- **2025-12-18**: Initial documentation created based on December 2024 announcement and beta features
- Based on official Anthropic documentation and community resources as of December 2024
