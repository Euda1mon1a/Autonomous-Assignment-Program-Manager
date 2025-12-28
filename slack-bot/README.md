# Claude Code Slack Bot

Bridge between Slack and your local Claude Code CLI. Message from your phone, Claude works on your codebase.

## Quick Start

### 1. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → From scratch
3. Enable **Socket Mode** (Settings → Socket Mode → Enable)
4. Add **Bot Token Scopes** (OAuth & Permissions):
   - `app_mentions:read`
   - `chat:write`
   - `im:history`
   - `im:read`
   - `im:write`
5. Enable **Events** (Event Subscriptions → Subscribe to bot events):
   - `app_mention`
   - `message.im`
6. Install to workspace

### 2. Get Tokens

From your Slack app settings, grab:
- **Bot User OAuth Token** (`xoxb-...`) from OAuth & Permissions
- **App-Level Token** (`xapp-...`) from Basic Information → App-Level Tokens (create one with `connections:write`)
- **Signing Secret** from Basic Information

### 3. Configure

```bash
cd slack-bot
cp .env.example .env
# Edit .env with your tokens
```

### 4. Run with Docker

```bash
# From project root
docker compose -f docker-compose.yml -f docker-compose.slack-bot.yml up -d slack-bot

# Check logs
docker compose logs -f slack-bot
```

### 5. Run Standalone (Dev)

```bash
cd slack-bot
npm install
npm run dev
```

## Usage

In Slack DM or channel (mention the bot):

```
# Set working directory (persists per thread)
cwd /app/workspace

# Give it tasks
@ClaudeBot fix the bug in scheduler.py where constraints aren't validated

# Check status
status
```

## Commands

| Command | Description |
|---------|-------------|
| `cwd /path` | Set working directory for this session |
| `status` | Show current working directory |
| Any other text | Sent to Claude Code as a prompt |

## Architecture

```
Slack Mobile/Desktop
    ↓ (Socket Mode)
slack-bot container
    ↓ (spawns)
claude CLI (-p mode)
    ↓
Your mounted repo (/app/workspace)
    ↓
Git commit/push → PR
```

## Notes

- Uses Claude CLI print mode (`-p`) for non-interactive operation
- 10 minute timeout per request
- Responses truncated to 4000 chars (Slack limit)
- Your repo is mounted at `/app/workspace`
- Git config and SSH keys mounted for commits/pushes
