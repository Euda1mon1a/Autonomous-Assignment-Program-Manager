# Claude Code CLI (CCCLI) Comprehensive Guide

> **Complete reference for Claude Code CLI usage, configuration, and skill integration**
>
> Last Updated: 2026-01-19 | Audience: Developers & AI Operators

---

## Table of Contents

1. [Overview](#overview)
2. [Installation & Setup](#installation--setup)
3. [Core CLI Commands](#core-cli-commands)
4. [Configuration Hierarchy](#configuration-hierarchy)
5. [Slash Commands](#slash-commands)
6. [Agent Skills](#agent-skills)
7. [Vercel Agent Skills Integration](#vercel-agent-skills-integration)
8. [MCP Server Integration](#mcp-server-integration)
9. [Hooks System](#hooks-system)
10. [Plugins](#plugins)
11. [Modes of Operation](#modes-of-operation)
12. [Project-Specific Configuration](#project-specific-configuration)
13. [Best Practices](#best-practices)
14. [Troubleshooting](#troubleshooting)

---

## Overview

Claude Code is Anthropic's official agentic coding tool that operates in your terminal, IDE, or web browser. It understands your codebase, executes routine tasks, explains complex code, and handles git workflows through natural language.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| **Codebase Understanding** | Indexes and comprehends your entire project |
| **Git Integration** | Commits, PRs, branches, conflict resolution |
| **Test Execution** | Runs tests, analyzes failures, generates fixes |
| **Multi-file Editing** | Coordinated changes across files |
| **MCP Integration** | Connects to external tools (JIRA, Slack, DBs) |
| **Skill System** | Extensible expertise via markdown packages |

### Interface Options

```
┌─────────────────────────────────────────────────────────┐
│                  Claude Code Interfaces                  │
├─────────────────────────────────────────────────────────┤
│  Terminal (CLI)  │  IDE Extensions  │  Web (claude.ai)  │
│  • Full control  │  • VS Code       │  • Async tasks    │
│  • Scripting     │  • Cursor        │  • & prefix       │
│  • Automation    │  • JetBrains     │  • Background     │
└─────────────────────────────────────────────────────────┘
```

---

## Installation & Setup

### Prerequisites

- Node.js 18+ (for `npx` commands)
- Git configured with SSH keys
- API key or Anthropic account

### Install Claude Code CLI

```bash
# Install globally via npm
npm install -g @anthropic-ai/claude-code

# Or use npx (no global install)
npx @anthropic-ai/claude-code

# Verify installation
claude --version
```

### Authentication

```bash
# Interactive login (opens browser)
claude auth login

# Or set API key directly
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify authentication
claude auth status
```

### First Run

```bash
# Navigate to your project
cd /path/to/your/project

# Start Claude Code
claude

# Claude will index your codebase on first run
```

---

## Core CLI Commands

### Basic Usage

```bash
# Start interactive session
claude

# Single prompt (non-interactive)
claude "explain the authentication flow"

# With specific file context
claude "review this file" @src/auth.py

# JSON output for scripting
claude --output-format json "list all API endpoints"
```

### CLI Flags

| Flag | Description | Example |
|------|-------------|---------|
| `--output-format` | Output format (text/json) | `--output-format json` |
| `--agent` | Override agent for session | `--agent opus` |
| `--agents` | Define custom subagents (JSON) | `--agents '{"name":"..."}'` |
| `--disable-slash-commands` | Disable all slash commands | Useful for automation |
| `--max-tokens` | Limit response tokens | `--max-tokens 4000` |
| `--dangerously-skip-permissions` | Skip permission prompts | CI/CD only |

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Escape` | Stop Claude mid-response |
| `Escape` (2x) | Show message history navigation |
| `Ctrl+C` | Exit Claude Code entirely |
| `Tab` | Autocomplete file paths, commands |
| `@` | Mention files for context |
| `/` | Invoke slash commands |

### Built-in Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/permissions` | Configure allowed commands |
| `/config` | View/edit configuration |
| `/memory` | View/edit memory files |
| `/model` | Switch model (Haiku/Sonnet/Opus) |
| `/compact` | Toggle compact output mode |
| `/cost` | Show token usage and costs |
| `/tasks` | Manage background tasks |
| `/plugin` | Install/manage plugins |

---

## Configuration Hierarchy

Claude Code uses layered JSON configuration with inheritance:

```
Priority (lowest → highest):
┌───────────────────────────────────────────┐
│ 1. Default settings (built-in)            │
├───────────────────────────────────────────┤
│ 2. User settings (~/.claude/settings.json)│
├───────────────────────────────────────────┤
│ 3. Project settings (.claude/settings.json)│
├───────────────────────────────────────────┤
│ 4. Local overrides (.claude/settings.local.json)│
└───────────────────────────────────────────┘
```

### Configuration Files

| File | Scope | Git Committed | Purpose |
|------|-------|---------------|---------|
| `~/.claude/settings.json` | Global (all projects) | No | Personal preferences |
| `.claude/settings.json` | Project (team) | Yes | Shared project config |
| `.claude/settings.local.json` | Project (personal) | No | Local overrides |
| `.mcp.json` | Project | Yes | MCP server connections |
| `CLAUDE.md` | Project | Yes | Project memory/context |

### Example User Settings

```json
// ~/.claude/settings.json
{
  "model": "sonnet",
  "outputStyle": "concise",
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(git *)",
      "Bash(pytest *)",
      "Read(*)",
      "Write(.claude/*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(* --force)"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "pattern": "Write(*.py)",
        "command": "ruff format {file}"
      }
    ]
  }
}
```

### Example Project Settings

```json
// .claude/settings.json
{
  "projectName": "Residency Scheduler",
  "defaultModel": "sonnet",
  "disabledMcpServers": ["unused-server"],
  "environment": {
    "PYTHONPATH": "./backend",
    "NODE_ENV": "development"
  },
  "skillsDirectory": ".claude/skills"
}
```

---

## Slash Commands

Slash commands are user-invoked prompts stored as Markdown files.

### Directory Structure

```
.claude/commands/           # Project-specific (shared)
├── commit.md
├── review-pr.md
└── domain/                 # Namespaced commands
    └── run-tests.md

~/.claude/commands/         # Personal (all projects)
├── my-workflow.md
└── debug-helper.md
```

### Command File Format

```markdown
# .claude/commands/commit.md

Create a git commit with the following guidelines:

1. Run `git status` to see changes
2. Run `git diff` to understand the changes
3. Write a commit message following conventional commits:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
4. Commit with `git commit -m "..."`

$ARGUMENTS  <!-- Optional: user arguments passed here -->
```

### Using Commands

```bash
# In Claude Code session:
/commit                          # Run commit command
/commit "quick fix for login"    # With arguments
/domain/run-tests                # Namespaced command
```

### Project Commands (This Repo)

Located in `.claude/commands/`:

| Command | Purpose |
|---------|---------|
| `/startup` | Initialize session with context |
| `/commit` | Create conventional commit |
| `/review-pr` | Review pull request |
| `/run-tests` | Execute test suite |
| `/lint-fix` | Auto-format code |
| `/health-check` | System health validation |

---

## Agent Skills

Skills are **model-invoked** expertise packages. Unlike slash commands (user-triggered), Claude decides when to activate skills based on context.

### How Skills Work

```
User: "Is this schedule ACGME compliant?"
       │
       ▼
┌──────────────────────────────────────┐
│  Claude detects "ACGME" keyword      │
│  Loads acgme-compliance skill        │
│  Applies domain expertise            │
│  Returns compliance analysis         │
└──────────────────────────────────────┘
```

### Skill Directory Structure

```
.claude/skills/
├── acgme-compliance/
│   ├── SKILL.md              # Core skill definition
│   ├── thresholds.md         # Supporting reference
│   └── exceptions.md         # Additional context
├── schedule-optimization/
│   └── SKILL.md
└── frontend-development/
    └── SKILL.md

~/.claude/skills/             # Global skills (all projects)
├── react-best-practices/
│   └── SKILL.md
└── web-design-guidelines/
    └── SKILL.md
```

### SKILL.md Format

```markdown
---
name: my-skill
description: Brief description for skill matching (max 1024 chars)
allowed-tools: Read, Grep, Glob  # Optional: restrict available tools
---

# Skill Title

## When This Skill Activates
- Condition 1
- Condition 2

## Procedures
1. Step one
2. Step two

## Escalation Rules
**Escalate to human when:**
1. Condition A
2. Condition B
```

### Progressive Loading

Skills use three-level loading to conserve context:

| Level | Loaded | Tokens | When |
|-------|--------|--------|------|
| 1. Metadata | name + description | ~100 | At startup |
| 2. Core | Full SKILL.md | ~500-2000 | On activation |
| 3. Supporting | reference.md, etc. | Variable | On demand |

### This Project's Skills (80+)

See `.claude/skills/` for the complete list. Key skills:

| Skill | Purpose |
|-------|---------|
| `acgme-compliance` | ACGME regulatory expertise |
| `schedule-optimization` | Constraint programming |
| `frontend-development` | Next.js/React patterns |
| `fastapi-production` | Async API patterns |
| `python-testing-patterns` | Advanced pytest |
| `security-audit` | HIPAA, OPSEC compliance |
| `database-migration` | Alembic expertise |
| `production-incident-responder` | Crisis response |

---

## Vercel Agent Skills Integration

Vercel released **Agent Skills** (January 2026) - an open-source package manager for AI coding agents.

### What Vercel Offers

| Skill | Rules | Purpose |
|-------|-------|---------|
| `react-best-practices` | 40+ | React/Next.js performance optimization |
| `web-design-guidelines` | 100+ | Accessibility and UX compliance |
| `vercel-deploy-claimable` | N/A | Deploy from chat conversations |

### Installation

```bash
# Install specific skills globally for Claude Code
npx add-skill vercel-labs/agent-skills --skill react-best-practices -g -a claude-code -y
npx add-skill vercel-labs/agent-skills --skill web-design-guidelines -g -a claude-code -y

# Install to current project (committed to git)
npx add-skill vercel-labs/agent-skills --skill react-best-practices

# Install all skills from a repo
npx add-skill vercel-labs/agent-skills
```

### Skill Installation Paths

| Agent | Installation Path |
|-------|-------------------|
| Claude Code | `~/.claude/skills/` (global) or `.claude/skills/` (project) |
| Cursor | `.cursor/skills/` |
| Codex | `.codex/skills/` |
| OpenCode | `.opencode/skills/` |

### Recommended Setup for This Project

```bash
# 1. Install Vercel's frontend skills globally
npx add-skill vercel-labs/agent-skills --skill react-best-practices -g -a claude-code -y
npx add-skill vercel-labs/agent-skills --skill web-design-guidelines -g -a claude-code -y

# 2. Skip vercel-deploy (we use Docker, not Vercel)
# Not needed: npx add-skill vercel-labs/agent-skills --skill vercel-deploy-claimable
```

### How Vercel Skills Complement Our Skills

| Our Skill | Vercel Skill | Relationship |
|-----------|--------------|--------------|
| `frontend-development` | `react-best-practices` | Our skill = what to build; Vercel = how to optimize |
| `react-typescript` | `web-design-guidelines` | Our skill = types; Vercel = accessibility |
| N/A | `vercel-deploy-claimable` | Not applicable (we use Docker) |

### Creating Shareable Skills

Export your skills in Vercel's format for community sharing:

```bash
# Create a skills repo structure
mkdir -p my-org/residency-scheduling-skills/skills

# Each skill follows the format:
my-org/residency-scheduling-skills/
├── skills/
│   ├── acgme-compliance/
│   │   └── SKILL.md
│   ├── shift-optimization/
│   │   └── SKILL.md
│   └── swap-safety/
│       └── SKILL.md
└── README.md

# Others can install via:
# npx add-skill my-org/residency-scheduling-skills
```

---

## MCP Server Integration

MCP (Model Context Protocol) enables Claude to connect to external tools and services.

### Configuration

MCP servers are configured in `.mcp.json` at project root:

```json
{
  "mcpServers": {
    "residency-scheduler": {
      "command": "python",
      "args": ["-m", "scheduler_mcp.server"],
      "cwd": "./mcp-server",
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "github": {
      "command": "npx",
      "args": ["@anthropic/mcp-server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### This Project's MCP Tools (34+)

| Tool Category | Example Tools |
|---------------|---------------|
| **Scheduling** | `generate_schedule`, `validate_schedule_tool` |
| **Compliance** | `check_mtf_compliance_tool`, `validate_acgme_compliance` |
| **Resilience** | `get_defense_level_tool`, `check_utilization_threshold_tool` |
| **Swaps** | `analyze_swap_candidates_tool`, `validate_swap` |
| **RAG** | `rag_search` (67+ documents indexed) |

### Context Window Warning

**Critical:** Too many MCP tools shrink your context window.

```
200K context window → 70K with all MCPs enabled
```

**Solution:** Disable unused servers:

```json
// .claude/settings.json
{
  "disabledMcpServers": ["unused-server-1", "unused-server-2"]
}
```

### MCP Server as Slash Commands

MCP servers can expose prompts that become slash commands:

```python
# In MCP server implementation
@mcp.prompt("compliance-check")
async def compliance_check_prompt(schedule_id: str):
    """Check ACGME compliance for a schedule"""
    return f"Validate ACGME compliance for schedule {schedule_id}"
```

Usage in Claude Code:

```bash
/mcp/residency-scheduler/compliance-check "schedule-123"
```

---

## Hooks System

Hooks execute custom commands at specific points in the conversation lifecycle.

### Hook Types

| Hook | When | Use Case |
|------|------|----------|
| `PreToolUse` | Before tool execution | Validation, logging |
| `PostToolUse` | After tool execution | Formatting, cleanup |
| `PreMessage` | Before Claude responds | Context injection |
| `PostMessage` | After Claude responds | Logging, metrics |
| `OnError` | On error | Alerting, recovery |

### Hook Configuration

```json
// ~/.claude/settings.json or .claude/settings.json
{
  "hooks": {
    "PostToolUse": [
      {
        "pattern": "Write(*.py)",
        "command": "ruff format {file} && ruff check {file} --fix"
      },
      {
        "pattern": "Write(*.ts)",
        "command": "npx prettier --write {file}"
      },
      {
        "pattern": "Write(*.tsx)",
        "command": "npx eslint --fix {file}"
      }
    ],
    "PreToolUse": [
      {
        "pattern": "Bash(git push *)",
        "command": "echo 'Running pre-push checks...' && npm test"
      }
    ]
  }
}
```

### Pattern Syntax

| Pattern | Matches |
|---------|---------|
| `Write(*.py)` | Any Python file write |
| `Bash(npm *)` | Any npm command |
| `Read(src/*)` | Any read in src directory |
| `Edit(*.{ts,tsx})` | TypeScript/TSX edits |

### Variables in Hooks

| Variable | Description |
|----------|-------------|
| `{file}` | File path being operated on |
| `{tool}` | Tool name |
| `{args}` | Tool arguments (JSON) |

---

## Plugins

Plugins bundle commands, agents, skills, hooks, and MCP configs into installable packages.

### Install Plugins

```bash
# In Claude Code session:
/plugin install github.com/user/my-plugin

# List installed plugins
/plugin list

# Remove plugin
/plugin remove my-plugin
```

### Plugin Structure

```
my-plugin/
├── plugin.json           # Plugin manifest
├── commands/             # Slash commands
│   └── my-command.md
├── skills/               # Agent skills
│   └── my-skill/
│       └── SKILL.md
├── agents/               # Custom agents
│   └── my-agent.json
├── hooks/                # Hook definitions
│   └── hooks.json
└── mcp/                  # MCP server configs
    └── servers.json
```

### Plugin Manifest

```json
// plugin.json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "My awesome plugin",
  "author": "Your Name",
  "components": {
    "commands": ["commands/"],
    "skills": ["skills/"],
    "agents": ["agents/"],
    "hooks": ["hooks/hooks.json"],
    "mcp": ["mcp/servers.json"]
  }
}
```

---

## Modes of Operation

### Interactive Mode (Default)

```bash
claude
> How does the scheduling engine work?
```

### Plan Mode

Engages extended thinking for complex strategies:

```bash
claude
> /plan

# Or trigger via keywords:
> "Let's plan the implementation of..."
> "think hard about how to refactor..."
```

**Use Plan Mode for:**
- Starting new features
- Complex refactoring
- Architectural decisions
- Multi-step implementations

### Background Tasks (Web)

Send tasks to run asynchronously:

```bash
# Prefix with & for background execution
> & Run the full test suite and report failures
```

### Thinking Triggers

Extended thinking levels (increasing compute):

| Trigger | Compute | Use Case |
|---------|---------|----------|
| `"think"` | Low | Simple reasoning |
| `"think hard"` | Medium | Complex analysis |
| `"think harder"` | High | Deep investigation |
| `"ultrathink"` | Maximum | Hardest problems |

---

## Project-Specific Configuration

### This Project's Setup

```
/home/user/Autonomous-Assignment-Program-Manager/
├── CLAUDE.md                    # Project memory (loaded every session)
├── .mcp.json                    # MCP server configuration
├── .claude/
│   ├── settings.json            # Project settings (team)
│   ├── settings.local.json      # Local overrides (gitignored)
│   ├── commands/                # Project slash commands
│   │   ├── startup.md
│   │   ├── commit.md
│   │   └── ...
│   ├── skills/                  # 80+ agent skills
│   │   ├── acgme-compliance/
│   │   ├── schedule-optimization/
│   │   └── ...
│   ├── Agents/                  # PAI agent specifications
│   │   ├── ORCHESTRATOR.md
│   │   ├── SCHEDULER.md
│   │   └── ...
│   └── Identities/              # Agent identity cards
│       └── *.identity.md
└── mcp-server/                  # MCP server implementation
    └── scheduler_mcp/
```

### CLAUDE.md Overview

The `CLAUDE.md` file is loaded every session and contains:

- Project overview and tech stack
- Code style requirements
- Security requirements (OPSEC/PERSEC)
- Files to never modify
- AI rules of engagement
- Common commands reference

### Recommended Session Start

```bash
# 1. Start Claude Code
claude

# 2. Initialize context
> /startup

# 3. Check system health
> /health-check

# 4. Begin work
> What are the open issues for the scheduler?
```

---

## Best Practices

### Context Management

1. **Use @-mentions sparingly** - Only include files Claude needs
2. **Clear context when switching tasks** - `/clear` between unrelated work
3. **Disable unused MCPs** - Each tool consumes context tokens
4. **Use skills over inline instructions** - Skills load on-demand

### Permission Configuration

```json
// Recommended permissions for this project
{
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(pytest *)",
      "Bash(ruff *)",
      "Bash(git add *)",
      "Bash(git commit *)",
      "Bash(git push *)",
      "Read(*)",
      "Glob(*)",
      "Grep(*)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push --force *)",
      "Bash(git push origin main)",
      "Bash(DROP *)",
      "Read(.env)"
    ]
  }
}
```

### Git Workflow

```bash
# Let Claude handle commits
> Create a commit for the current changes

# Let Claude create PRs
> Create a PR for this feature branch

# Review before merge
> Review PR #123 and summarize concerns
```

### Cost Optimization

| Action | Impact |
|--------|--------|
| Use Haiku for simple tasks | 100x cheaper than Opus |
| Enable compact output | Fewer response tokens |
| Clear context between tasks | Reset token accumulation |
| Use skills over repeated instructions | Amortize context |

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Command not found" | Verify installation: `which claude` |
| "Authentication failed" | Re-run `claude auth login` |
| "Context limit exceeded" | `/clear` or disable MCPs |
| "MCP server not responding" | Check server logs, restart |
| "Skill not activating" | Verify SKILL.md frontmatter |
| "Permission denied" | Update `/permissions` |

### Debug Mode

```bash
# Enable verbose logging
claude --verbose

# Check MCP connections
claude
> /config mcp

# Verify skill loading
claude
> What skills are available?
```

### Logs Location

```bash
# Claude Code logs
~/.claude/logs/

# MCP server logs
./mcp-server/logs/
```

### Reset Configuration

```bash
# Reset user settings
rm ~/.claude/settings.json

# Reset project settings
rm .claude/settings.json
rm .claude/settings.local.json

# Clear cache
rm -rf ~/.claude/cache/
```

---

## Quick Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│                  Claude Code CLI Quick Reference                │
├────────────────────────────────────────────────────────────────┤
│  START SESSION                                                  │
│    claude                    Start interactive session          │
│    claude "prompt"           One-shot query                     │
│    claude @file "prompt"     Query with file context            │
│                                                                 │
│  KEYBOARD                                                       │
│    Escape                    Stop response                      │
│    Escape x2                 Message history                    │
│    Tab                       Autocomplete                       │
│    @                         File mention                       │
│    /                         Slash command                      │
│                                                                 │
│  COMMANDS                                                       │
│    /help                     Show commands                      │
│    /clear                    Clear history                      │
│    /model sonnet             Switch model                       │
│    /permissions              Configure permissions              │
│    /plugin install <url>     Install plugin                     │
│                                                                 │
│  CONFIGURATION FILES                                            │
│    ~/.claude/settings.json   User settings                      │
│    .claude/settings.json     Project settings                   │
│    .mcp.json                 MCP servers                        │
│    CLAUDE.md                 Project memory                     │
│                                                                 │
│  DIRECTORIES                                                    │
│    ~/.claude/commands/       Personal commands                  │
│    .claude/commands/         Project commands                   │
│    ~/.claude/skills/         Personal skills                    │
│    .claude/skills/           Project skills                     │
│                                                                 │
│  VERCEL SKILLS                                                  │
│    npx add-skill <repo> -g -a claude-code                       │
└────────────────────────────────────────────────────────────────┘
```

---

## Related Documentation

- [Agent Skills Reference](../development/AGENT_SKILLS.md) - Complete skills documentation
- [Anthropic Skills Exploration](../planning/ANTHROPIC_SKILLS_EXPLORATION.md) - Skills architecture
- [MCP Tool Usage](MCP_TOOL_USAGE.md) - MCP integration guide
- [AI Agent User Guide](AI_AGENT_USER_GUIDE.md) - Agent setup
- [CLAUDE.md](../../CLAUDE.md) - Project guidelines

## External Resources

- [Claude Code Docs](https://code.claude.com/docs/en/cli-reference) - Official documentation
- [Vercel Agent Skills](https://github.com/vercel-labs/agent-skills) - Vercel's skill packages
- [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code) - Community resources
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices) - Anthropic guide

---

*This guide is maintained as part of the Residency Scheduler project. For updates, see the project's documentation.*
