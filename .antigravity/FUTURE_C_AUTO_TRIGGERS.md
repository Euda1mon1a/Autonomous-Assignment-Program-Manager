# Auto Triggers Configuration (FUTURE - NOT ACTIVATED)

> **Status:** PLANNED - Do not enable until Manager View (B) is stable
> **Target:** After Manager View achieves reliable orchestration
> **Last Updated:** 2025-12-22

---

## What Auto Triggers Enable

Auto Triggers allow **external events** to start agent workflows without human initiation:

```
┌─────────────────────────────────────────────────────────────────┐
│                        AUTO TRIGGERS                             │
│              (Events start workflows automatically)              │
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Webhook │          │ Schedule│          │  Watch  │
   │ GitHub  │          │  Cron   │          │  Files  │
   │  push   │          │  Daily  │          │ Changes │
   └─────────┘          └─────────┘          └─────────┘
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Run     │          │ Run     │          │ Run     │
   │ Tests   │          │ Health  │          │ Lint    │
   │ + Fix   │          │ Check   │          │ + Fix   │
   └─────────┘          └─────────┘          └─────────┘
```

---

## Prerequisites (Must Complete First)

### From Manager View (B):
- [ ] Multi-agent coordination proven reliable
- [ ] Conflict resolution working
- [ ] Resource management stable
- [ ] No manual intervention needed for routine tasks

### Technical Requirements:
- [ ] Webhook endpoint secured
- [ ] Rate limiting configured
- [ ] Queue system for trigger overflow
- [ ] Notification system for trigger results
- [ ] Kill switch for runaway triggers

---

## Planned Trigger Types

### 1. Git Webhook Triggers
```yaml
triggers:
  - event: push
    branch: main
    action: run-tests-and-fix

  - event: pull_request
    action: code-review

  - event: issue_comment
    contains: "@claude fix"
    action: investigate-and-fix
```

### 2. Scheduled Triggers
```yaml
schedules:
  - cron: "0 6 * * *"  # Daily 6am
    action: health-check

  - cron: "0 0 * * 0"  # Weekly Sunday
    action: dependency-audit

  - cron: "0 */4 * * *"  # Every 4 hours
    action: resilience-check
```

### 3. File Watch Triggers
```yaml
watch:
  - path: "backend/app/**/*.py"
    event: save
    action: lint-and-format

  - path: "backend/tests/**/*"
    event: save
    action: run-affected-tests
```

### 4. n8n Workflow Triggers
```yaml
n8n:
  - workflow: "hourly_resilience_check"
    action: analyze-resilience-report

  - workflow: "schedule_generation"
    action: validate-generated-schedule
```

---

## Safety Requirements

### Kill Switch
```json
{
  "autoTriggers": {
    "killSwitch": {
      "enabled": true,
      "maxTriggersPerHour": 20,
      "maxConcurrentWorkflows": 3,
      "pauseOnError": true,
      "requireConfirmationAfter": 10
    }
  }
}
```

### Rate Limiting
- Max 20 triggers per hour
- Max 3 concurrent workflows
- Automatic pause if error rate >10%
- Human confirmation required after 10 unattended triggers

### Scope Limits
- Triggers cannot modify production data
- Triggers cannot push to main branch
- Triggers cannot delete files
- Triggers cannot run migrations

---

## Integration Points

### Claude for Chrome (Browser Agent)
- Schedule browser-based testing
- Automated UI verification
- Cross-browser compatibility checks

### Comet Browser
- Research automation
- Documentation updates
- External API testing

### n8n Workflows
- Existing hourly resilience checks
- Schedule generation validation
- Alert routing

---

## Activation Checklist

When ready to activate:

1. [ ] Verify Manager View stability metrics
2. [ ] Test with scheduled triggers first (lowest risk)
3. [ ] Add webhook triggers with strict rate limits
4. [ ] Monitor trigger patterns
5. [ ] Establish alert thresholds
6. [ ] Document rollback procedures

---

## Known Challenges to Address

1. **Runaway Triggers** - Loop detection, rate limiting
2. **Context Loss** - Triggers don't have conversation history
3. **Priority Conflicts** - Multiple triggers competing
4. **Debugging** - Tracing issues in automated runs
5. **Security** - Webhook authentication, injection prevention

---

## DO NOT ACTIVATE UNTIL:

- Manager View (B) has run successfully for at least 20 sessions
- Kill switch and rate limiting are fully tested
- Security review of webhook endpoints complete
- n8n integration validated
- Clear escalation path for failed triggers
