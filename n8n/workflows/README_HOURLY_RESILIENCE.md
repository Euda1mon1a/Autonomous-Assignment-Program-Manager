# Hourly Resilience Health Check Workflow

## Overview

This n8n workflow performs automated hourly health checks of the Residency Scheduler's resilience system and sends alerts based on severity levels. It implements a multi-tiered alerting strategy aligned with the Defense-in-Depth framework.

## Features

### 1. **Automated Hourly Monitoring**
- Runs every hour on the hour (cron: `0 * * * *`)
- Queries resilience health endpoint
- Retrieves load shedding status
- Enriches data with computed metrics

### 2. **Five-Level Severity Routing**

Based on the Defense-in-Depth framework, alerts are routed by severity:

| Severity | Status | Actions |
|----------|--------|---------|
| **GREEN** | Healthy | Log metrics only - no alerts |
| **YELLOW** | Warning | Slack warning to #ops channel |
| **ORANGE** | Degraded | Slack alert + Email to coordinators |
| **RED** | Critical | Slack alert + Email + PagerDuty (if configured) |
| **BLACK** | Emergency | Slack alert + Email + PagerDuty (if configured) |

### 3. **Rich Slack Notifications**

Slack messages include:
- Color-coded severity indicators
- Utilization metrics (rate, level, buffer)
- Defense level and load shedding status
- Crisis mode and contingency compliance (N-1/N-2)
- Immediate actions required
- Watch items for monitoring
- Redundancy issues
- Active fallback schedules
- Link to full dashboard

### 4. **Email Alerts**

Triggered for ORANGE/RED/BLACK levels:
- Formatted plain text and HTML emails
- Priority flagging (high/urgent)
- Complete status summary
- Actionable immediate actions
- Dashboard link for details

### 5. **PagerDuty Integration**

For RED/BLACK critical alerts (optional):
- Creates incident with full context
- Links to dashboard
- Includes custom details for on-call engineers

### 6. **Metrics Logging**

All checks log structured metrics for trend analysis:
- Overall status and severity
- Utilization metrics
- Defense and load shedding levels
- Contingency compliance
- Action counts

## Setup Instructions

### Prerequisites

1. **n8n instance** running and accessible
2. **Backend API** deployed and accessible
3. **Slack workspace** with webhook configured
4. **Email SMTP** credentials (SendGrid, AWS SES, or similar)
5. **PagerDuty account** (optional, for critical alerts)

### Environment Variables

Configure these environment variables in your n8n instance:

#### Required

```bash
# Backend API base URL (no trailing slash)
API_BASE_URL=https://scheduler-api.example.com

# Slack webhook for #ops channel
SLACK_WEBHOOK_OPS=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Coordinator email addresses (comma-separated)
COORDINATOR_EMAILS=coordinator1@example.com,coordinator2@example.com

# SMTP sender address
SMTP_FROM_EMAIL=scheduler@example.com
```

#### Optional

```bash
# PagerDuty integration key (for critical alerts)
PAGERDUTY_KEY=your-pagerduty-integration-key
```

### SMTP Credentials

Configure SMTP credentials in n8n:

1. Go to **Settings > Credentials**
2. Add new **SMTP** credential with ID: `smtp-credentials`
3. Configure your SMTP provider:
   - **Host**: smtp.gmail.com (or your provider)
   - **Port**: 587 (TLS) or 465 (SSL)
   - **Username**: your-email@example.com
   - **Password**: your-app-password

### Import Workflow

1. Open n8n web interface
2. Go to **Workflows**
3. Click **Import from File**
4. Select `hourly_resilience_check.json`
5. Click **Import**

### Activate Workflow

1. Open the imported workflow
2. Click **Activate** toggle in top-right
3. Workflow will run on next hour mark

## Workflow Architecture

```
┌─────────────────┐
│ Cron Trigger    │
│ (Every hour)    │
└────────┬────────┘
         │
         ├──────────────────────────┐
         │                          │
         ▼                          ▼
┌─────────────────┐      ┌─────────────────┐
│ Get Resilience  │      │ Get Load        │
│ Health          │      │ Shedding Status │
└────────┬────────┘      └────────┬────────┘
         │                        │
         └────────┬───────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Parse & Enrich  │
         │ Data            │
         └────────┬────────┘
                  │
                  ├────────────────────┐
                  │                    │
                  ▼                    ▼
         ┌─────────────────┐  ┌─────────────────┐
         │ Format Slack    │  │ Log Metrics     │
         │ Message         │  │ for Trends      │
         └────────┬────────┘  └─────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Route by        │
         │ Severity        │
         └────┬─┬─┬─┬──────┘
              │ │ │ │
     GREEN────┘ │ │ │
              YELLOW│ │
               ORANGE│
                  RED/BLACK
                     │
                     ├─> Slack Alert
                     ├─> Email Coordinators
                     └─> PagerDuty (if configured)
```

## Data Flow

### 1. Health Check Query

```http
GET /api/v1/resilience/health
```

Response includes:
- `overall_status`: healthy, warning, degraded, critical, emergency
- `utilization`: rate, level, buffer
- `defense_level`: PREVENTION, CONTROL, SAFETY_SYSTEMS, CONTAINMENT, EMERGENCY
- `load_shedding_level`: NORMAL, YELLOW, ORANGE, RED, BLACK, CRITICAL
- `crisis_mode`: boolean
- `n1_pass`, `n2_pass`: contingency compliance
- `phase_transition_risk`: low, moderate, high, critical
- `active_fallbacks`: array of active scenarios
- `immediate_actions`: array of required actions
- `watch_items`: array of items to monitor
- `redundancy_status`: array of service redundancy

### 2. Load Shedding Query

```http
GET /api/v1/resilience/load-shedding
```

Response includes:
- `level`: current load shedding level
- `activities_suspended`: array
- `activities_protected`: array
- `capacity_available`: number
- `capacity_demand`: number

### 3. Data Enrichment

The workflow:
1. Maps `overall_status` to severity (GREEN/YELLOW/ORANGE/RED/BLACK)
2. Calculates flags (isCritical, hasImmediateActions, etc.)
3. Adds emoji indicators for visualization
4. Prepares routing metadata

### 4. Slack Formatting

Slack Block Kit message includes:
- Header with severity emoji
- Utilization metrics section
- System status section
- Redundancy issues (if any)
- Immediate actions (if any)
- Watch items (if any)
- Active fallbacks (if any)
- Footer with timestamp and dashboard link

### 5. Severity Routing

Switch node routes based on severity:
- **Output 0 (GREEN)**: Log only
- **Output 1 (YELLOW)**: Slack warning
- **Output 2 (ORANGE)**: Slack + Email
- **Output 3 (RED)**: Slack + Email + PagerDuty
- **Output 4 (BLACK)**: Slack + Email + PagerDuty

## Customization

### Adjust Alert Thresholds

Edit the `Parse and Enrich Data` function to customize severity mapping:

```javascript
const severityMap = {
  'healthy': 'GREEN',
  'warning': 'YELLOW',   // Customize threshold
  'degraded': 'ORANGE',  // Customize threshold
  'critical': 'RED',     // Customize threshold
  'emergency': 'BLACK'
};
```

### Add Additional Metrics

Extend the health check query to include additional endpoints:

```javascript
// Add in workflow
{
  "parameters": {
    "url": "={{ $env.API_BASE_URL }}/api/v1/resilience/tier2/status"
  },
  "name": "Get Tier 2 Status"
}
```

### Custom Notification Channels

Add nodes for additional channels:
- Microsoft Teams webhook
- SMS via Twilio
- Custom webhook to internal systems
- Database logging

### Modify Cron Schedule

Change the schedule in the trigger node:

```json
{
  "parameters": {
    "rule": {
      "interval": [
        {
          "field": "cronExpression",
          "expression": "*/15 * * * *"  // Every 15 minutes
        }
      ]
    }
  }
}
```

Common schedules:
- `0 * * * *` - Every hour (default)
- `*/30 * * * *` - Every 30 minutes
- `*/15 * * * *` - Every 15 minutes
- `0 */6 * * *` - Every 6 hours
- `0 9,17 * * *` - 9 AM and 5 PM daily

## Testing

### Manual Execution

1. Open workflow in n8n
2. Click **Execute Workflow** button
3. Review execution in the **Executions** tab
4. Check Slack/Email for test messages

### Test Specific Severity Levels

Temporarily modify the severity mapping in the `Parse and Enrich Data` function:

```javascript
// Force ORANGE for testing
const severity = 'ORANGE';
```

Then execute workflow manually.

### Validate PagerDuty Integration

Ensure `PAGERDUTY_KEY` is set and trigger a RED alert:

```javascript
// Force RED severity
const severity = 'RED';
```

Check PagerDuty for incident creation.

## Monitoring

### Execution History

View all workflow executions:
1. Open workflow
2. Click **Executions** tab
3. Review success/failure status
4. Click individual executions for details

### Error Handling

Workflow errors are logged to n8n execution history. Common issues:

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | API_BASE_URL incorrect | Verify URL, check API health |
| `Unauthorized` | Missing auth credentials | Configure HTTP auth in node |
| `Slack webhook failed` | Invalid webhook URL | Regenerate Slack webhook |
| `SMTP error` | Invalid credentials | Verify SMTP settings |
| `PagerDuty error` | Invalid integration key | Check PagerDuty key |

### Enable Workflow Error Notifications

Configure n8n to notify on workflow failures:
1. Go to **Settings > Error Workflow**
2. Create error notification workflow
3. Set as global error handler

## Integration with Backend

### API Authentication

If your API requires authentication, add HTTP header auth:

```json
{
  "parameters": {
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth",
    "sendHeaders": true,
    "headerParameters": {
      "parameters": [
        {
          "name": "Authorization",
          "value": "Bearer YOUR_API_TOKEN"
        }
      ]
    }
  }
}
```

Or use Basic Auth:

```json
{
  "parameters": {
    "authentication": "genericCredentialType",
    "genericAuthType": "httpBasicAuth"
  }
}
```

### Rate Limiting

The workflow makes 2 API requests per hour. If you have aggressive rate limiting:

1. Reduce check frequency
2. Implement request throttling
3. Use API keys with higher limits

## Metrics and Trend Analysis

### Log Metrics Node

The `Log Metrics for Trends` node outputs structured data:

```json
{
  "timestamp": "2025-12-18T12:00:00Z",
  "overall_status": "warning",
  "severity": "YELLOW",
  "utilization_rate": 0.72,
  "utilization_level": "YELLOW",
  "buffer_remaining": 0.08,
  "defense_level": "CONTROL",
  "load_shedding_level": "NORMAL",
  "crisis_mode": false,
  "n1_pass": true,
  "n2_pass": true,
  "phase_transition_risk": "low",
  "active_fallbacks_count": 0,
  "immediate_actions_count": 1,
  "watch_items_count": 2,
  "has_redundancy_issues": false
}
```

### Implement Trend Storage

Add a database write node to store metrics:

```javascript
// Example: Write to PostgreSQL
{
  "parameters": {
    "operation": "insert",
    "table": "resilience_metrics",
    "columns": "timestamp, severity, utilization_rate, ...",
    "values": "={{$json.record}}"
  }
}
```

### Degradation Detection

Implement hourly comparison:

1. Query previous hour's metrics from database
2. Compare current vs. previous
3. Detect trends (improving, degrading, stable)
4. Add to alert message

Example:

```javascript
// In Parse and Enrich Data function
const previousUtilization = await getPreviousMetric('utilization_rate');
const degradationTrend = utilizationRate > previousUtilization ? 'worsening' : 'improving';
```

## Troubleshooting

### Workflow Not Executing

**Check:**
- Workflow is activated (toggle in top-right)
- Cron expression is valid
- n8n instance is running
- System time is correct

**Fix:**
```bash
# Verify cron expression
# Use https://crontab.guru/ to validate

# Check n8n logs
docker logs n8n-container
```

### API Requests Failing

**Check:**
- API_BASE_URL is correct (no trailing slash)
- Backend API is running and healthy
- Network connectivity between n8n and API
- Authentication credentials (if required)

**Fix:**
```bash
# Test API endpoint manually
curl -X GET https://scheduler-api.example.com/api/v1/resilience/health

# Check n8n network
docker exec n8n-container curl API_BASE_URL/health
```

### Slack Messages Not Sending

**Check:**
- SLACK_WEBHOOK_OPS is valid
- Webhook hasn't been revoked
- Slack workspace is accessible
- Message payload is valid JSON

**Fix:**
```bash
# Test webhook manually
curl -X POST SLACK_WEBHOOK_OPS \
  -H 'Content-Type: application/json' \
  -d '{"text": "Test message"}'

# Regenerate webhook in Slack if needed
```

### Email Not Sending

**Check:**
- SMTP credentials are correct
- SMTP_FROM_EMAIL is valid
- Recipient emails exist
- SMTP server allows connection

**Fix:**
```javascript
// Test SMTP in n8n
// Create simple test workflow with Email Send node
// Check n8n logs for SMTP errors
```

### PagerDuty Not Triggering

**Check:**
- PAGERDUTY_KEY is set and valid
- Integration is configured in PagerDuty
- Service is active
- Escalation policy exists

**Fix:**
```bash
# Test PagerDuty API manually
curl -X POST https://events.pagerduty.com/v2/enqueue \
  -H 'Content-Type: application/json' \
  -d '{
    "routing_key": "YOUR_KEY",
    "event_action": "trigger",
    "payload": {
      "summary": "Test",
      "severity": "error",
      "source": "test"
    }
  }'
```

## Performance Considerations

### Execution Time

Typical workflow execution: **3-5 seconds**

- Health check: ~1-2s
- Load shedding check: ~0.5s
- Data processing: ~0.5s
- Notifications: ~1-2s

### Resource Usage

- **Memory**: ~50MB per execution
- **CPU**: Minimal (data transformation only)
- **Network**: ~10KB per execution

### Scaling

For high-frequency monitoring:
- Use n8n workers for parallel execution
- Implement request caching
- Batch multiple checks
- Use Redis for state management

## Security Considerations

### Credentials Management

**Never hardcode secrets in workflow JSON**

Use n8n credentials or environment variables:
- ✅ `={{ $env.SLACK_WEBHOOK_OPS }}`
- ✅ `={{ $credentials.slack_webhook }}`
- ❌ `https://hooks.slack.com/services/hardcoded/key`

### API Authentication

If API requires auth:
1. Use HTTP Header Auth credential type
2. Store token in n8n credential manager
3. Rotate tokens regularly

### Webhook Security

For Slack webhooks:
- Don't expose webhook URLs publicly
- Regenerate if compromised
- Use Slack's IP whitelist if available

### Email Security

- Use app passwords (not account passwords)
- Enable 2FA on email account
- Use dedicated service account
- Monitor for unauthorized access

## Maintenance

### Regular Tasks

**Weekly:**
- Review execution history for errors
- Check alert fatigue (too many alerts?)
- Verify Slack/Email delivery

**Monthly:**
- Review and update severity thresholds
- Analyze metrics trends
- Update email distribution list
- Test PagerDuty escalation

**Quarterly:**
- Rotate SMTP credentials
- Review workflow efficiency
- Update documentation
- Conduct disaster recovery test

### Upgrading

When upgrading n8n:
1. Export workflow JSON (backup)
2. Test in staging environment
3. Review release notes for breaking changes
4. Update workflow if needed
5. Deploy to production

## Reference Links

- [n8n Documentation](https://docs.n8n.io/)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder/)
- [Crontab Guru](https://crontab.guru/) - Cron expression validator
- [PagerDuty Events API](https://developer.pagerduty.com/docs/ZG9jOjExMDI5NTgw-events-api-v2-overview)
- [Resilience API Documentation](/docs/api/resilience.md)

## Support

For issues with this workflow:
1. Check this documentation
2. Review n8n execution logs
3. Test API endpoints manually
4. Check environment variables
5. Consult #engineering channel

## License

This workflow is part of the Residency Scheduler project and follows the same license as the main project.

---

**Last Updated:** 2025-12-18
**Version:** 1.0
**Maintainer:** Engineering Team
