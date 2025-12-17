# n8n Workflows for Slack ChatOps Integration

This directory contains n8n workflow files for integrating the Autonomous Assignment Program Manager with Slack and email, enabling ChatOps capabilities for task scheduling and management.

## Overview

The workflows provide the following capabilities:

1. **Slack Sitrep Command** - Get real-time status reports from the scheduler
2. **Slack Fix-It Command** - Trigger automated task recovery and retry mechanisms
3. **Slack Approve Command** - Approve or deny pending tasks via Slack
4. **Email Parser** - Automatically create tasks from incoming emails

## Workflows

### 1. Slack Sitrep Command (`slack_sitrep.json`)

**Purpose:** Provides real-time situation reports on scheduler health and task status.

**Slack Command:** `/scheduler sitrep`

**Flow:**
1. Receives Slack slash command via webhook
2. Calls `GET /api/resilience/report` endpoint
3. Formats response into Slack Block Kit message
4. Returns formatted status to Slack channel

**Response Includes:**
- Total, active, completed, and failed task counts
- Success rate percentage
- Recent task history (last 5 tasks)
- System health status
- Last update timestamp

**Example Usage:**
```
/scheduler sitrep
```

---

### 2. Slack Fix-It Command (`slack_fix_it.json`)

**Purpose:** Initiates automated task recovery and retry mechanisms.

**Slack Command:** `/scheduler fix-it mode=greedy [retries=3] [auto-approve]`

**Flow:**
1. Receives Slack slash command with parameters
2. Parses command parameters (mode, max_retries, auto_approve)
3. Calls `POST /api/scheduler/fix-it` endpoint
4. Formats execution results for Slack
5. Returns confirmation with execution ID

**Parameters:**
- `mode` - Recovery mode (greedy, conservative, balanced)
- `retries` - Maximum retry attempts (default: 3)
- `auto-approve` - Skip manual approval for fixes

**Example Usage:**
```
/scheduler fix-it mode=greedy
/scheduler fix-it mode=conservative retries=5
/scheduler fix-it mode=greedy auto-approve
```

---

### 3. Slack Approve Command (`slack_approve.json`)

**Purpose:** Approve or deny pending tasks that require manual review.

**Slack Command:** `/scheduler approve token=ABC123 [task=TASK_ID] [deny]`

**Flow:**
1. Receives Slack slash command with approval token
2. Validates required parameters
3. Calls `POST /api/scheduler/approve` endpoint
4. Formats approval results for Slack
5. Returns confirmation with approved/denied count

**Parameters:**
- `token` - Required approval token (provided by system)
- `task` - Optional specific task ID (approves all if omitted)
- `deny` - Flag to deny instead of approve

**Example Usage:**
```
/scheduler approve token=abc123xyz
/scheduler approve token=abc123xyz task=TASK-456
/scheduler approve token=abc123xyz deny
```

---

### 4. Email Parser (`email_parser.json`)

**Purpose:** Automatically parse incoming emails and create tasks from schedule requests.

**Trigger:** Incoming emails with subject containing "Schedule Request"

**Flow:**
1. Monitors INBOX for new emails via IMAP
2. Parses email content for task details
3. Validates parsed data
4. Creates task via `POST /api/tasks/create`
5. Sends confirmation or error email to sender

**Email Format:**

To create a task, send an email with subject "Schedule Request" and body containing:

```
Task Name: Update API documentation
Description: Update the REST API docs with new endpoints for v2.0
Priority: high
Due Date: 2025-12-31
Assigned To: John Doe
Category: documentation
Duration: 4 hours
Depends On: TASK-123, TASK-124
```

**Supported Fields:**
- Task Name (required) - Can be extracted from subject if not in body
- Description (required)
- Priority (optional) - high/medium/low (default: medium)
- Due Date (optional)
- Assigned To (optional)
- Category (optional) - default: general
- Duration (optional) - e.g., "4 hours", "2 days"
- Depends On (optional) - comma or semicolon separated task IDs

---

## Setup Instructions

### Prerequisites

1. **n8n Instance** - Self-hosted or cloud n8n instance (v1.0+)
2. **Slack Workspace** - Admin access to create Slack apps
3. **API Access** - Running instance of Autonomous Assignment Program Manager API
4. **Email Account** (for email parser) - IMAP-enabled email account

### Step 1: Import Workflows

1. Log in to your n8n instance
2. Navigate to Workflows
3. Click "Import from File"
4. Import each JSON file from the `workflows/` directory
5. Activate each workflow after configuration

### Step 2: Configure Environment Variables

Set the following environment variables in your n8n instance:

```bash
# API Configuration
API_BASE_URL=http://your-api-server:8000

# Email Configuration (for email_parser workflow)
EMAIL_IMAP_HOST=imap.gmail.com
EMAIL_USER=scheduler@yourdomain.com
EMAIL_PASSWORD=your-app-password

# Optional: Authentication
API_AUTH_TOKEN=your-secret-token
```

**In n8n:**
- Go to Settings > Environment Variables
- Add each variable with appropriate values
- Restart n8n if required

### Step 3: Configure Slack App

#### Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" > "From scratch"
3. Name: "Scheduler Bot"
4. Select your workspace
5. Click "Create App"

#### Configure Slash Commands

For each workflow, create a slash command:

1. Go to "Slash Commands" in the Slack app settings
2. Click "Create New Command"

**Command 1: Sitrep**
- Command: `/scheduler`
- Request URL: `https://your-n8n-instance.com/webhook/slack-sitrep`
- Short Description: "Get scheduler status report"
- Usage Hint: `sitrep`

**Command 2: Fix-It**
- Command: `/scheduler`
- Request URL: `https://your-n8n-instance.com/webhook/slack-fix-it`
- Short Description: "Trigger fix-it recovery mode"
- Usage Hint: `fix-it mode=greedy [retries=3] [auto-approve]`

**Command 3: Approve**
- Command: `/scheduler`
- Request URL: `https://your-n8n-instance.com/webhook/slack-approve`
- Short Description: "Approve pending tasks"
- Usage Hint: `approve token=TOKEN [task=ID] [deny]`

#### Configure OAuth & Permissions

1. Go to "OAuth & Permissions"
2. Add the following Bot Token Scopes:
   - `chat:write` - Send messages
   - `commands` - Use slash commands
   - `users:read` - Read user information
3. Install the app to your workspace
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

#### Configure Interactivity

1. Go to "Interactivity & Shortcuts"
2. Enable Interactivity
3. Request URL: `https://your-n8n-instance.com/webhook/slack-interactive`
4. Save changes

### Step 4: Configure n8n Credentials

#### Slack OAuth2 API (for workflows)

1. In n8n, go to Credentials
2. Create new credential: "Slack OAuth2 API"
3. Enter:
   - OAuth Token: Your Bot User OAuth Token (from Step 3)
   - Or configure OAuth flow with Client ID and Secret
4. Save credential

#### HTTP Header Auth (for API calls)

1. In n8n, go to Credentials
2. Create new credential: "Header Auth"
3. Name: "Scheduler API Auth"
4. Header Name: `Authorization`
5. Value: `Bearer your-api-token`
6. Save credential

#### Gmail (for email_parser workflow)

1. In n8n, go to Credentials
2. Create new credential: "Gmail OAuth2"
3. Follow OAuth flow to authorize n8n
4. Save credential

### Step 5: Update Workflow Webhook URLs

For each workflow, update the webhook node:

1. Open workflow in n8n
2. Click the Webhook node
3. Copy the "Test URL" or "Production URL"
4. Update the corresponding Slack slash command Request URL
5. Save and activate the workflow

### Step 6: Test Workflows

#### Test Sitrep Command

In Slack:
```
/scheduler sitrep
```

Expected: Status report with task counts and health metrics

#### Test Fix-It Command

In Slack:
```
/scheduler fix-it mode=greedy
```

Expected: Confirmation message with execution ID

#### Test Approve Command

In Slack (use token from system notification):
```
/scheduler approve token=abc123
```

Expected: Confirmation with approved task count

#### Test Email Parser

Send email to configured address:
```
Subject: Schedule Request

Task Name: Test Task
Description: This is a test task
Priority: high
```

Expected: Confirmation email with task ID

---

## Environment Variables Reference

| Variable | Description | Required | Default | Example |
|----------|-------------|----------|---------|---------|
| `API_BASE_URL` | Base URL of scheduler API | Yes | - | `http://localhost:8000` |
| `API_AUTH_TOKEN` | Authentication token for API | No | - | `secret-token-123` |
| `EMAIL_IMAP_HOST` | IMAP server hostname | Email only | - | `imap.gmail.com` |
| `EMAIL_USER` | Email account username | Email only | - | `scheduler@example.com` |
| `EMAIL_PASSWORD` | Email account password | Email only | - | `app-password-xyz` |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token | No* | - | `xoxb-123-456-abc` |

*Not required as environment variable if configured in n8n credentials

---

## Troubleshooting

### Workflow Not Triggering

**Problem:** Slack command doesn't trigger workflow

**Solutions:**
1. Verify webhook URL in Slack app settings matches n8n webhook URL
2. Check that workflow is activated in n8n
3. Review n8n execution logs for errors
4. Ensure n8n instance is publicly accessible

### API Connection Errors

**Problem:** "Connection refused" or "timeout" errors

**Solutions:**
1. Verify `API_BASE_URL` is correct and accessible from n8n
2. Check API server is running and healthy
3. Verify authentication credentials are correct
4. Check firewall/network settings

### Email Parser Not Working

**Problem:** Emails not being processed

**Solutions:**
1. Verify IMAP settings are correct
2. Check email credentials have IMAP access enabled
3. For Gmail: Enable "Less secure app access" or use App Password
4. Verify email subject contains "Schedule Request"
5. Check n8n execution logs for parsing errors

### Slack Message Formatting Issues

**Problem:** Slack messages display incorrectly

**Solutions:**
1. Verify Slack Block Kit JSON is valid
2. Test blocks at https://api.slack.com/tools/block-kit-builder
3. Check for escaped characters in function nodes
4. Review n8n function node output

### Authentication Failures

**Problem:** 401/403 errors from API

**Solutions:**
1. Verify `API_AUTH_TOKEN` is correct
2. Check credential configuration in n8n
3. Ensure header name matches API expectations
4. Review API logs for authentication errors

---

## Security Considerations

1. **Webhook Security**
   - Use HTTPS for all webhook URLs
   - Implement Slack request signing verification
   - Validate incoming request headers

2. **API Authentication**
   - Store API tokens in n8n credentials, not in workflow JSON
   - Use environment variables for sensitive data
   - Rotate tokens regularly

3. **Email Security**
   - Use app-specific passwords instead of account passwords
   - Enable 2FA on email account
   - Restrict email sender validation

4. **Access Control**
   - Limit Slack command access to specific channels
   - Implement user role validation in API
   - Log all command executions for audit

---

## Advanced Configuration

### Custom Response Formatting

To customize Slack message formatting, edit the "Format Response" function nodes:

```javascript
// Example: Add custom emoji based on priority
const priorityEmoji = {
  high: ':fire:',
  medium: ':warning:',
  low: ':information_source:'
};
```

### Adding Rate Limiting

To prevent command abuse, add rate limiting logic:

```javascript
// In webhook node, add rate limit check
const userId = $json.user_id;
const lastCall = $node["rateLimit"].json[userId];
const now = Date.now();

if (lastCall && (now - lastCall) < 60000) {
  return {
    json: {
      response_type: "ephemeral",
      text: "Please wait before using this command again."
    }
  };
}
```

### Email Template Customization

To support different email templates, modify the regex patterns in the email parser:

```javascript
// Add support for alternative field names
const taskName = extractField(/(?:Task Name|Subject|Title)[:\\s]+(.+?)(?:\\n|$)/i, body);
```

---

## Workflow Maintenance

### Updating Workflows

1. Export current workflow from n8n
2. Make changes to JSON file
3. Test in development environment
4. Import updated workflow to production
5. Activate updated workflow

### Monitoring

Monitor workflow executions:

1. Check n8n execution history regularly
2. Set up error notifications in n8n
3. Monitor API logs for errors
4. Track Slack command usage metrics

### Backup

Backup workflows regularly:

```bash
# Export all workflows
curl -X GET https://your-n8n-instance.com/api/v1/workflows \
  -H "Authorization: Bearer YOUR_API_KEY" \
  > workflows_backup.json
```

---

## Support and Resources

- **n8n Documentation:** https://docs.n8n.io/
- **Slack API Documentation:** https://api.slack.com/
- **Slack Block Kit Builder:** https://api.slack.com/tools/block-kit-builder
- **n8n Community Forum:** https://community.n8n.io/

---

## License

These workflows are part of the Autonomous Assignment Program Manager project.

---

## Changelog

### Version 1.0.0 (2025-12-17)
- Initial release
- Added Slack sitrep command workflow
- Added Slack fix-it command workflow
- Added Slack approve command workflow
- Added email parser workflow
- Complete documentation and setup instructions
