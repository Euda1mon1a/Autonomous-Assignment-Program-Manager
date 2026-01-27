# Moltbot + Local LLM Setup Guide

> **Purpose:** Hardware recommendations and setup for running Moltbot with local LLMs for autonomous development
> **Last Updated:** 2026-01-27

---

## Overview

This guide covers setting up **Moltbot** (formerly Clawdbot) as your always-on AI assistant, with options for both cloud APIs (Claude, GPT) and local LLMs via Ollama. The goal: interact primarily via Slack, with VPN fallback for direct access.

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your Workflow                              │
│                                                                 │
│   Laptop/Phone ──► Slack ──► Moltbot ──┬──► Claude API (cloud)  │
│        │                               │                        │
│        └──► VPN ──► SSH ──► Terminal   └──► Ollama (local LLM)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## What is Moltbot?

[Moltbot](https://github.com/moltbot/moltbot) is a self-hosted AI assistant with 60,000+ GitHub stars. It was renamed from "Clawdbot" after an Anthropic trademark request.

**Key Features:**
- **Persistent memory** across conversations
- **Full system access** - shell, browser, files
- **50+ integrations** - Slack, WhatsApp, Telegram, iMessage, Signal, Discord
- **Proactive notifications** - it can reach out to you
- **Local LLM support** via Ollama
- **Multi-model** - use Claude for complex tasks, local LLMs for simple ones

---

## Hardware Recommendations

### Option A: Mac Mini (Best for iMessage + Local LLMs)

**Mac Mini M2 Base ($599) or M4 ($599-799)**

| Spec | M2 Base | M4 (Recommended) |
|------|---------|------------------|
| CPU | 8-core | 10-core |
| GPU | 10-core | 10-core |
| Unified Memory | 8GB | **16GB minimum** |
| Storage | 256GB | 512GB+ |
| Local LLM Capability | Small models (7B) | Medium models (14B-32B) |

**Upgrade to 24GB RAM** if you want to run larger local models like Qwen3-32B or DeepSeek-Coder-33B.

**Pros:**
- Native iMessage integration (unique to macOS)
- Apple Silicon is efficient for inference
- Low power (~15-30W idle)
- Silent operation

### Option B: Mini PC + GPU (Best for Serious Local LLMs)

**Beelink/GMKTec with external GPU or desktop build**

| Component | Budget (~$800) | Performance (~$1500) |
|-----------|----------------|----------------------|
| CPU | Intel i5-12400 | AMD Ryzen 7 7800X3D |
| RAM | 32GB DDR4 | 64GB DDR5 |
| GPU | RTX 3060 12GB | **RTX 4090 24GB** |
| Storage | 1TB NVMe | 2TB NVMe |
| Local LLM | 7B-13B models | **32B-70B models** |

**GPU VRAM Requirements:**

| VRAM | Recommended Models |
|------|-------------------|
| 8GB | Llama 3.2 3B, Qwen2.5-7B (Q4) |
| 12GB | DeepSeek-Coder-7B, Qwen2.5-14B (Q4) |
| 16GB | Qwen2.5-32B (Q4), Llama 3.1 8B |
| **24GB** | **DeepSeek-V2 (21B active), Qwen3-32B, Gemma 2 27B** |
| 48GB+ | Llama 3.1 70B, Qwen2 72B |

### Option C: Cloud VPS (No Hardware)

If you don't want local hardware:

| Provider | Spec | Cost/Month |
|----------|------|------------|
| Hetzner Cloud | CPX41 (8 vCPU, 16GB) | ~$25 |
| RunPod | RTX 4090 (on-demand) | ~$0.44/hr |
| Vast.ai | RTX 3090 spot | ~$0.15/hr |

---

## Software Stack

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Your Server                          │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  Moltbot    │  │   Ollama    │  │    Tailscale VPN    │  │
│  │  (Gateway)  │◄─┤  (Local LLM)│  │   (Remote Access)   │  │
│  └──────┬──────┘  └─────────────┘  └─────────────────────┘  │
│         │                                                   │
│  ┌──────┴──────────────────────────────────────────────┐    │
│  │                    Channels                          │    │
│  │  • Slack  • Telegram  • iMessage  • Discord  • Web  │    │
│  └──────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Recommended Local LLMs for Coding (2026)

Based on [current benchmarks](https://nutstudio.imyfone.com/llm-tips/best-llm-for-coding/):

| Model | Size | Best For | HumanEval | VRAM Needed |
|-------|------|----------|-----------|-------------|
| **Qwen3-Coder-32B** | 32B | Coding (100+ languages) | 91.0% | 20GB (Q4) |
| **DeepSeek-Coder-V2** | 21B active | Coding specialist | 90.2% | 16GB |
| DeepSeek-V3.2 | 37B active | Reasoning + coding | 92.1% | 24GB |
| Llama 3.1 70B | 70B | General + coding | 81.7% | 48GB (Q4) |
| Qwen2.5-14B | 14B | Good balance | 78.3% | 10GB (Q4) |
| Llama 3.2 3B | 3B | Fast, lightweight | 62.1% | 4GB |

**My Recommendation:**
- **Primary:** Claude Opus 4.5 via API (complex tasks, this repo)
- **Secondary:** Qwen3-Coder-32B via Ollama (quick tasks, private code)

---

## Installation Guide

### Step 1: Base System (Ubuntu Server 24.04)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essentials
sudo apt install -y \
    git curl wget htop tmux vim \
    build-essential

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Install Node.js 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs
```

### Step 2: Install Tailscale (VPN)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate and enable SSH
sudo tailscale up --ssh

# Get your Tailscale IP
tailscale ip -4
# Example: 100.64.x.x

# Now you can SSH from anywhere via: ssh user@100.64.x.x
```

### Step 3: Install Ollama (Local LLMs)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Pull recommended models
ollama pull qwen2.5-coder:32b    # Best for coding (20GB)
ollama pull qwen2.5:14b          # Good general purpose (10GB)
ollama pull llama3.2:3b          # Fast, lightweight (2GB)

# Verify
ollama list
```

### Step 4: Install Moltbot

```bash
# Clone Moltbot
git clone https://github.com/moltbot/moltbot.git
cd moltbot

# Install dependencies
npm install

# Copy example config
cp .env.example .env
```

### Step 5: Configure Moltbot

Edit `.env`:

```bash
# Primary AI Provider (Claude for complex tasks)
ANTHROPIC_API_KEY=sk-ant-your-key-here
DEFAULT_MODEL=claude-opus-4-5-20251101

# Local LLM via Ollama (for quick/private tasks)
OLLAMA_API_KEY=ollama-local
OLLAMA_HOST=http://127.0.0.1:11434

# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# GitHub (for repo access)
GITHUB_TOKEN=ghp_your-token

# Security
GATEWAY_SECRET=generate-a-strong-secret-here

# Working Directory
WORKSPACE_DIR=/home/user/repos
```

### Step 6: Configure Ollama Provider

Create `config/providers/ollama.yaml`:

```yaml
# Moltbot Ollama Configuration
# Docs: https://docs.molt.bot/providers/ollama

provider: ollama
enabled: true
baseUrl: http://127.0.0.1:11434/v1

models:
  # Coding specialist - use for code tasks
  qwen2.5-coder:32b:
    contextWindow: 32768
    costPerMillionTokens: 0  # Local = free
    capabilities:
      - code
      - chat

  # General purpose
  qwen2.5:14b:
    contextWindow: 32768
    costPerMillionTokens: 0
    capabilities:
      - chat
      - reasoning

  # Fast responses
  llama3.2:3b:
    contextWindow: 8192
    costPerMillionTokens: 0
    capabilities:
      - chat

# Auto-route based on task
routing:
  code: qwen2.5-coder:32b
  chat: qwen2.5:14b
  quick: llama3.2:3b
```

### Step 7: Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. **Create New App** → **From scratch**
3. Name: "Moltbot" (or your preferred name)

**OAuth Scopes** (Bot Token):
```
app_mentions:read
channels:history
channels:read
chat:write
files:read
files:write
im:history
im:read
im:write
reactions:read
reactions:write
users:read
```

**Socket Mode:** Enable and create App-Level Token with `connections:write`

**Event Subscriptions:**
- `app_mention`
- `message.im`
- `message.channels` (optional)

**Install to Workspace** and copy tokens to `.env`

### Step 8: Start Moltbot

```bash
# Start in tmux for persistence
tmux new -s moltbot

# Run Moltbot
npm start

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t moltbot
```

### Step 9: Auto-Start on Boot

```bash
sudo tee /etc/systemd/system/moltbot.service << 'EOF'
[Unit]
Description=Moltbot AI Assistant
After=network.target ollama.service

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/moltbot
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable moltbot
sudo systemctl start moltbot
```

---

## Usage Patterns

### Via Slack (Primary)

```
# Direct message to Moltbot
You: Review the PR at https://github.com/org/repo/pull/123

Moltbot: I'll review that PR for you...
[Uses Claude Opus for complex analysis]

# Quick question (routes to local LLM)
You: What's the syntax for Python list comprehension?

Moltbot: [Uses local Qwen for fast response]
```

### Model Selection in Slack

```
# Force specific model
You: @moltbot --model ollama/qwen2.5-coder:32b refactor this function

# Use Claude for complex tasks
You: @moltbot --model claude-opus-4-5 analyze the architecture of this repo
```

### Via VPN + Terminal (Fallback)

```bash
# SSH to your Moltbot server
ssh user@100.64.x.x  # Tailscale IP

# Run Claude Code directly
cd ~/repos/Autonomous-Assignment-Program-Manager
claude

# Or attach to Moltbot logs
journalctl -u moltbot -f
```

---

## Cost Optimization Strategy

### Hybrid Approach (Recommended)

| Task Type | Model | Cost |
|-----------|-------|------|
| Complex reasoning | Claude Opus 4.5 | $15/M input, $75/M output |
| Code generation | Claude Sonnet 4 | $3/M input, $15/M output |
| Quick questions | Local Qwen 14B | **$0** |
| Code completion | Local Qwen-Coder 32B | **$0** |
| Simple chat | Local Llama 3B | **$0** |

**Estimated Monthly Costs:**
- Heavy use (50% Claude, 50% local): ~$30-50/month
- Light use (20% Claude, 80% local): ~$10-20/month
- Local only: ~$5/month (electricity)

### Auto-Routing Rules

Configure in Moltbot to auto-select models:

```yaml
# config/routing.yaml
rules:
  # Use Claude for this specific repo
  - match:
      workspace: "Autonomous-Assignment-Program-Manager"
    model: claude-opus-4-5-20251101

  # Use local for general coding
  - match:
      intent: code
    model: ollama/qwen2.5-coder:32b

  # Use local for quick responses
  - match:
      estimated_tokens: < 500
    model: ollama/llama3.2:3b

  # Default to Claude Sonnet
  - default:
    model: claude-sonnet-4-20250514
```

---

## Security Considerations

### Network Security

```bash
# Firewall - only allow Tailscale
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 100.64.0.0/10  # Tailscale range
sudo ufw enable

# Don't expose Moltbot web UI to internet!
# Access only via Tailscale VPN
```

### API Key Security

```bash
# Never commit .env
echo ".env" >> .gitignore

# Use environment variables, not config files for secrets
# Rotate API keys quarterly
```

### Ollama Security

```bash
# Bind Ollama to localhost only (default)
# In /etc/systemd/system/ollama.service:
Environment="OLLAMA_HOST=127.0.0.1:11434"
```

---

## Troubleshooting

### Moltbot Not Responding in Slack

```bash
# Check service status
sudo systemctl status moltbot

# Check logs
journalctl -u moltbot -n 100

# Verify Slack tokens
grep SLACK .env

# Restart
sudo systemctl restart moltbot
```

### Ollama Models Not Loading

```bash
# Check Ollama status
sudo systemctl status ollama

# Check available models
ollama list

# Check VRAM usage
nvidia-smi  # For NVIDIA GPUs

# Pull model again if corrupted
ollama rm qwen2.5-coder:32b
ollama pull qwen2.5-coder:32b
```

### Out of Memory (OOM)

```bash
# Use smaller quantization
ollama pull qwen2.5-coder:32b-q4_0  # 4-bit instead of default

# Or use smaller model
ollama pull qwen2.5-coder:14b
```

---

## Quick Start Checklist

- [ ] Choose hardware (Mac Mini M4 or Mini PC + GPU)
- [ ] Install Ubuntu Server 24.04
- [ ] Install Docker, Node.js 22+
- [ ] Install and configure Tailscale VPN
- [ ] Install Ollama and pull models
- [ ] Clone and configure Moltbot
- [ ] Create Slack app and get tokens
- [ ] Configure `.env` with all credentials
- [ ] Start Moltbot and verify Slack connection
- [ ] Enable auto-start with systemd
- [ ] Test from Slack on phone/laptop
- [ ] Test VPN access from remote location

---

## Resources

- [Moltbot GitHub](https://github.com/moltbot/moltbot)
- [Moltbot Docs - Ollama Provider](https://docs.molt.bot/providers/ollama)
- [Awesome Moltbot Skills](https://github.com/VoltAgent/awesome-moltbot-skills)
- [Ollama Model Library](https://ollama.com/library)
- [Best LLMs for Coding 2026](https://nutstudio.imyfone.com/llm-tips/best-llm-for-coding/)
- [Tailscale Documentation](https://tailscale.com/kb/)

---

## Summary

**Recommended Setup:**

| Component | Choice | Cost |
|-----------|--------|------|
| Hardware | Mac Mini M4 24GB | $799 one-time |
| VPN | Tailscale | Free |
| Primary AI | Claude Opus 4.5 | ~$30/month |
| Local LLM | Qwen3-Coder-32B | $0 |
| Interface | Slack | Free |

This gives you:
- 24/7 AI assistant accessible from anywhere
- Slack as primary interface (works on phone)
- VPN fallback for direct terminal access
- Local LLMs for privacy and cost savings
- Claude for complex tasks requiring best-in-class reasoning

---

*Last updated: 2026-01-27*
