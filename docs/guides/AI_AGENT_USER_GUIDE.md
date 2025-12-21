# AI Agent User Guide

> **Complete guide to using AI agents with the Residency Scheduler**
>
> Covers: Skills, MCP Tools, Google ADK, and CLI platforms (Claude Code, Antigravity)

---

## Table of Contents

1. [Overview](#overview)
2. [The Three Pillars](#the-three-pillars)
3. [Quick Start](#quick-start)
4. [Skills Reference](#skills-reference)
5. [CLI Platforms](#cli-platforms)
6. [Model Selection](#model-selection)
7. [Evaluation & Testing](#evaluation--testing)
8. [Troubleshooting](#troubleshooting)

---

## Overview

This repository has a complete AI agent infrastructure:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI AGENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │   SKILLS     │   │  MCP TOOLS   │   │  ADK AGENTS  │         │
│  │  (Knowledge) │ + │  (Actions)   │ + │  (Testing)   │         │
│  │  6 skills    │   │  16+ tools   │   │  TypeScript  │         │
│  └──────────────┘   └──────────────┘   └──────────────┘         │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            ▼                                     │
│                   ┌────────────────┐                             │
│                   │  Backend API   │                             │
│                   │   (FastAPI)    │                             │
│                   └────────────────┘                             │
│                                                                  │
│  Supported Platforms:                                            │
│  • Claude Code (macOS/Linux/Windows)                            │
│  • Google Antigravity                                            │
│  • VS Code + Claude Extension                                    │
│  • Any MCP-compatible client                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## The Three Pillars

### 1. Skills (Domain Knowledge)

**What:** Packaged expertise in `.claude/skills/` folders

**Available Skills:**

| Skill | Purpose |
|-------|---------|
| `automated-code-fixer` | Fix code issues with strict quality gates |
| `code-quality-monitor` | Enforce quality standards before commits |
| `production-incident-responder` | Crisis response using MCP resilience tools |
| `acgme-compliance` | ACGME regulatory expertise |
| `swap-management` | Shift swap workflow procedures |
| `schedule-optimization` | Multi-objective optimization strategies |

**How They Work:**
```
You: "Is next week's schedule ACGME compliant?"

Claude:
1. Sees "ACGME" → loads acgme-compliance skill
2. Reads SKILL.md for procedures
3. Calls validate_acgme_compliance MCP tool
4. Interprets results using skill knowledge
5. Responds with compliance status + recommendations
```

### 2. MCP Tools (Actions)

**What:** Backend API wrappers that let agents take action

**Key Tools:**

| Tool | What It Does |
|------|--------------|
| `validate_acgme_compliance` | Check schedule against ACGME rules |
| `find_swap_matches` | Find compatible swap partners |
| `check_utilization_threshold` | Monitor 80% capacity limit |
| `run_contingency_analysis` | N-1/N-2 failure analysis |
| `get_defense_level` | Current resilience status |
| `execute_sacrifice_hierarchy` | Emergency load shedding |

### 3. ADK Agents (Testing)

**What:** TypeScript agents with automated evaluation

**Why It Matters:**
- Test that agents call correct tools
- Verify response quality
- Catch regressions before production
- Multi-model support (Gemini, Claude)

---

## Quick Start

### Option A: Claude Code (Recommended for macOS)

```bash
# Install Claude Code
brew install claude-code

# Navigate to repo
cd Autonomous-Assignment-Program-Manager

# Start Claude Code
claude

# Claude automatically loads skills from .claude/skills/
```

**First Interaction:**
```
You: Check if the schedule is ACGME compliant

Claude: [Activates acgme-compliance skill]
        [Calls validate_acgme_compliance tool]
        [Returns detailed compliance report]
```

### Option B: Google Antigravity

```bash
# Download from https://antigravityai.org/
# Install and open

# Open this repository folder
# Antigravity detects Skills and MCP automatically
```

**Agent Mode:**
1. Open Command Palette: `Cmd+Shift+P`
2. Select "Antigravity: Start Agent"
3. Choose agent type (Reviewer, Coder, etc.)
4. Agent has access to skills + tools

### Option C: ADK Web Interface

```bash
# Navigate to ADK module
cd agent-adk

# Install dependencies
npm install

# Set up API key
cp .env.example .env
# Edit .env with GOOGLE_GENAI_API_KEY

# Start web UI
npm run dev

# Open http://localhost:8000
```

---

## Skills Reference

### Using Skills

Skills activate automatically based on your question:

| You Say | Skill Activated |
|---------|-----------------|
| "Is the schedule compliant?" | `acgme-compliance` |
| "Find someone to swap with" | `swap-management` |
| "Optimize next month's schedule" | `schedule-optimization` |
| "Tests are failing" | `automated-code-fixer` |
| "The system is down" | `production-incident-responder` |
| "Check code quality" | `code-quality-monitor` |

### Skill Files

Each skill has this structure:

```
.claude/skills/
└── skill-name/
    ├── SKILL.md        # Core instructions (required)
    ├── reference.md    # Detailed procedures (optional)
    └── examples.md     # Example scenarios (optional)
```

### Creating Custom Skills

1. Create folder in `.claude/skills/`:
```bash
mkdir -p .claude/skills/my-skill
```

2. Create `SKILL.md`:
```markdown
---
name: my-skill
description: Brief description for Claude to match against
---

# My Skill

Detailed instructions here...

## When This Skill Activates
- Condition 1
- Condition 2

## Procedures
1. Step one
2. Step two
```

3. Test by asking about the topic

---

## CLI Platforms

### Claude Code

**Best For:** Daily development, code changes, git operations

**Installation:**
```bash
# macOS
brew install claude-code

# Linux
curl -fsSL https://claude.ai/install.sh | bash

# Windows
winget install Anthropic.ClaudeCode
```

**Key Commands:**
| Command | Purpose |
|---------|---------|
| `claude` | Start interactive session |
| `claude "question"` | One-shot query |
| `claude --model opus` | Use specific model |
| `/help` | In-session help |
| `/skills` | List available skills |
| `/mcp` | List MCP tools |

**Tips:**
- Skills load from `.claude/skills/` automatically
- MCP tools available if `mcp-server/` is configured
- Opus 4.5 is best for complex reasoning
- Sonnet is faster for simple tasks

### Google Antigravity

**Best For:** Multi-agent workflows, parallel task execution

**Installation:**
- Download from [antigravityai.org](https://antigravityai.org/)
- Requires 8GB RAM (16GB recommended)
- macOS, Linux, Windows supported

**Key Features:**
| Feature | Description |
|---------|-------------|
| Agent Mode | Autonomous task completion |
| Manager View | Run 5 agents in parallel |
| Review Mode | AI asks permission before actions |
| Autopilot | Full autonomous operation |

**Model Support:**
- Gemini 3 Pro/Flash (default)
- Claude Sonnet 4.5
- GPT-OSS

**Best Practices:**
1. Start in Review Mode for unfamiliar tasks
2. Use Manager View for parallel bug fixes
3. Switch to Autopilot for routine tasks
4. Always review generated tests

### VS Code + Extensions

**Options:**
- Claude extension (Anthropic official)
- Cursor (Claude-powered fork)
- Cline (Claude in VS Code)

**Setup with MCP:**
```json
// settings.json
{
  "claude.mcp.servers": {
    "scheduler": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "${workspaceFolder}/mcp-server"
    }
  }
}
```

---

## Model Selection

### When to Use Each Model

| Model | Best For | Cost | Speed |
|-------|----------|------|-------|
| **Claude Opus 4.5** | Complex reasoning, architecture | $$$ | Slow |
| **Claude Sonnet 4** | Daily coding, balanced | $$ | Medium |
| **Gemini 3 Pro** | Complex analysis | $$ | Medium |
| **Gemini 3 Flash** | Quick queries | $ | Fast |

### Recommended Configurations

**Development (Daily):**
```bash
# Claude Code
claude --model sonnet

# or in .claude/config
model: sonnet
```

**Complex Analysis:**
```bash
# Claude Code
claude --model opus

# ADK
ADK_MODEL=gemini-3-pro npm run dev
```

**Cost-Sensitive:**
```bash
# Gemini Flash
ADK_MODEL=gemini-3-flash npm run dev
```

---

## Evaluation & Testing

### Running ADK Evaluations

```bash
cd agent-adk

# Run all evaluation tests
npm run test:eval

# Run specific category
npm test -- --grep "ACGME"
npm test -- --grep "swap"
npm test -- --grep "resilience"
```

### What Gets Tested

| Category | Tests |
|----------|-------|
| ACGME | 80-hour detection, supervision ratios, days off |
| Swap | Partner matching, compliance validation |
| Resilience | Utilization, contingency, defense levels |
| Safety | PII protection, escalation triggers |

### Evaluation Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Tool Trajectory | > 90% | Called correct tools in order |
| Response Match | > 80% | Response contains expected info |
| Safety | 100% | No harmful outputs |

### Adding Test Cases

Edit `agent-adk/src/evaluation/test-cases.ts`:

```typescript
export const customTestCases: TestCase[] = [
  {
    id: 'custom-001',
    name: 'My test case',
    userMessage: 'What happens if X?',
    expectedToolCalls: [
      { name: 'my_tool', matchMode: 'contains' },
    ],
    expectedResponseContains: ['expected', 'words'],
    tags: ['custom'],
  },
];
```

---

## Troubleshooting

### Skills Not Loading

**Symptoms:** Agent doesn't use skill knowledge

**Fixes:**
1. Check skill is in `.claude/skills/` (not `skills/`)
2. Verify `SKILL.md` has correct frontmatter:
   ```yaml
   ---
   name: skill-name
   description: Must be descriptive enough to match
   ---
   ```
3. Description must match your query keywords

### MCP Tools Not Available

**Symptoms:** "Tool not found" errors

**Fixes:**
1. Start MCP server:
   ```bash
   cd mcp-server
   python -m scheduler_mcp.server
   ```
2. Check Claude Code config:
   ```bash
   cat ~/.claude/config.json
   ```
3. Verify server is running:
   ```bash
   curl http://localhost:5000/health
   ```

### ADK Won't Start

**Symptoms:** `npm run dev` fails

**Fixes:**
1. Check Node version:
   ```bash
   node --version  # Need >= 20.12.0
   ```
2. Install dependencies:
   ```bash
   cd agent-adk
   rm -rf node_modules
   npm install
   ```
3. Check API key:
   ```bash
   cat .env | grep GOOGLE
   ```

### Slow Responses

**Symptoms:** Agent takes >30 seconds

**Fixes:**
1. Use faster model (Flash > Pro > Opus)
2. Check backend API health
3. Reduce context by being specific
4. Clear conversation history

### Wrong Tool Called

**Symptoms:** Agent calls unrelated tools

**Fixes:**
1. Be more specific in your question
2. Check skill description matches intent
3. Update skill instructions to be clearer
4. Add examples to skill's `examples.md`

---

## Environment Variables

### Required

| Variable | Description |
|----------|-------------|
| `GOOGLE_GENAI_API_KEY` | For Gemini models |
| `ANTHROPIC_API_KEY` | For Claude models |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `ADK_MODEL` | `gemini-2.5-flash` | Default ADK model |
| `API_BASE_URL` | `http://localhost:8000/api` | Backend API |
| `VERTEX_AI_PROJECT_ID` | - | For Vertex AI |
| `VERTEX_AI_LOCATION` | `us-central1` | Vertex AI region |

### Setting Up

```bash
# Create .env file
cat > .env << 'EOF'
GOOGLE_GENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
ADK_MODEL=gemini-2.5-flash
API_BASE_URL=http://localhost:8000/api
EOF
```

---

## Summary Cheat Sheet

| Task | Command / Action |
|------|------------------|
| Start Claude Code | `claude` |
| Start Antigravity | Open app, select folder |
| Start ADK | `cd agent-adk && npm run dev` |
| Check compliance | "Is the schedule ACGME compliant?" |
| Find swap partner | "Who can I swap Tuesday with?" |
| Run evaluations | `npm run test:eval` |
| List skills | `/skills` in Claude Code |
| List MCP tools | `/mcp` in Claude Code |

---

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Google ADK Docs](https://google.github.io/adk-docs/)
- [Antigravity Getting Started](https://codelabs.developers.google.com/getting-started-google-antigravity)
- [Agent Skills Specification](https://agentskills.io)
- [MCP Protocol Spec](https://modelcontextprotocol.io)
