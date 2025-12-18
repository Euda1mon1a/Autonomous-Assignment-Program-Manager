# Human TODO

> Tasks that require human action (external accounts, manual configuration, etc.)

---

## Slack Integration Setup

- [ ] **Test Slack Webhook Connection**
  - Workspace: https://join.slack.com/t/testingground-hsm1341/shared_invite/zt-3ltx5db1c-~gEi1t5FDFrHpAKsqcd~gQ
  - Create an Incoming Webhook in the workspace
  - Test with a simple curl command
  - Add `SLACK_WEBHOOK_URL` to `monitoring/.env`

- [ ] **Set Up Slack App for ChatOps** (optional, for slash commands)
  - Create Slack App at https://api.slack.com/apps
  - Add slash command `/scheduler`
  - Add Bot Token Scopes: `chat:write`, `commands`, `users:read`
  - Install app to workspace
  - Copy Bot User OAuth Token for n8n

- [ ] **Create Slack Channels for Alerts**
  - `#alerts-critical`
  - `#alerts-warning`
  - `#alerts-database`
  - `#alerts-infrastructure`
  - `#residency-scheduler`
  - `#compliance-alerts`

---

## Other Pending Tasks

_(Add other human-required tasks here)_

---

*Last updated: 2025-12-17*
