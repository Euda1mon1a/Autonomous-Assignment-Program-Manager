# AI Agent User Guide

> **Complete guide to using AI agents with the Residency Scheduler**
>
> Covers: Skills, MCP Tools, Google ADK, and Claude Code (Web, CLI, IDE)

---

## Table of Contents

1. [Overview](#overview)
2. [Choosing Your Claude Interface](#choosing-your-claude-interface)
3. [The Three Pillars](#the-three-pillars)
4. [Quick Start](#quick-start)
5. [Skills Reference](#skills-reference)
6. [Claude Code Platforms](#claude-code-platforms)
7. [Model Selection](#model-selection)
8. [Evaluation & Testing](#evaluation--testing)
9. [Troubleshooting](#troubleshooting)

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

## Choosing Your Claude Interface

Before diving in, understand the difference between Claude's interfaces:

### Claude Code: Web, CLI, and IDE

Claude Code is available in three forms, all providing the same agentic development capabilities:

| Feature | Claude Code Web | Claude Code CLI | Claude Code IDE |
|---------|-----------------|-----------------|-----------------|
| **What It Is** | Browser-based interface at claude.ai/code | Terminal command-line tool | VS Code / Cursor extension |
| **File Access** | Full codebase via GitHub integration | Full local filesystem access | Full workspace access |
| **Code Editing** | Read, write, edit files | Read, write, edit files | Read, write, edit files |
| **Git Operations** | Full git integration | Full git integration | Full git integration |
| **MCP Tools** | Supported via GitHub repos | Full MCP support | Full MCP support |
| **Skills** | Loads from `.claude/skills/` | Loads from `.claude/skills/` | Loads from `.claude/skills/` |
| **Best For** | Remote development, cloud-first workflows | Local development, scripting | IDE-integrated workflows |

> **Note:** This project was primarily developed using **Claude Code Web**. The web interface provides full agentic capabilities without requiring local installation, making it ideal for rapid development across different machines.

### Claude Code Web (Primary Development Interface)

Claude Code Web is the browser-based version accessible at [claude.ai/code](https://claude.ai/code). Key features:

- **GitHub Integration**: Connect your repositories directly; Claude can read, edit, and commit
- **No Local Setup**: Works from any browser without installing CLI tools
- **Persistent Sessions**: Continue work across browser sessions
- **Same Capabilities**: Full file editing, git operations, and tool usage as CLI

**When to use Claude Code Web:**
- Working on cloud-hosted repositories
- Developing from multiple machines
- Quick iterations without local environment setup
- Collaborative development with remote repos

### Claude for macOS/Desktop (Chat App) vs Claude Code

| Feature | Claude for macOS | Claude Code (any platform) |
|---------|------------------|----------------------------|
| **What It Is** | Desktop chat application | Agentic development tool |
| **File Access** | Limited (can view attached files) | Full access to your codebase |
| **Code Editing** | Cannot edit files | Can read, write, and edit files |
| **Git Operations** | None | Full git integration |
| **MCP Tools** | Not available | Full MCP tool support |
| **Skills** | Not available | Loads skills from `.claude/skills/` |
| **Best For** | Research, writing, quick questions | Development, code changes, debugging |

### When to Use Each

**Use Claude for macOS (Desktop App) when:**
- Asking general questions not tied to your codebase
- Drafting documentation or writing content
- Research and brainstorming
- Analyzing individual files you upload manually
- Having conversations that don't require code changes

**Use Claude Code Web when:**
- Working on GitHub-hosted repositories
- Developing from any machine without local setup
- Rapid prototyping and iteration
- You want full agentic capabilities in a browser

**Use Claude Code CLI when:**
- Working with local files not on GitHub
- Scripting and automation workflows
- Deployment tasks requiring local system access
- macOS automation with OSAScript (see [IDE Setup for macOS](#ide-setup-for-macos))

**Use Claude Code IDE (VS Code/Cursor) when:**
- You prefer staying in your editor
- Integrating with existing IDE workflows
- Need side-by-side code viewing while chatting

### Decision Flowchart

```
Do you need to modify files in your codebase?
├── YES
│   └── Is your repo on GitHub and you're okay with browser-based work?
│       ├── YES → Use Claude Code Web
│       └── NO → Use Claude Code CLI or IDE
└── NO
    └── Do you need to read/analyze project files?
        ├── YES → Use Claude Code (Web, CLI, or IDE)
        └── NO
            └── Is this a coding-related question?
                ├── YES, about THIS project → Use Claude Code
                ├── YES, general coding → Either works
                └── NO → Use Claude for macOS
```

### IDE Integration Options

For developers who prefer staying in their editor:

| Option | Description | When to Use |
|--------|-------------|-------------|
| **Antigravity** | Full-featured IDE with Claude | Multi-agent workflows, parallel tasks |
| **VS Code + Claude Extension** | Claude in VS Code sidebar | Light IDE integration |
| **Cursor** | VS Code fork with native Claude | If you prefer Cursor's UX |
| **Cline** | Claude extension for VS Code | Alternative VS Code integration |

All IDE options provide file access and can use MCP tools when configured.

### ChatGPT Codex vs Claude Code (Common Confusion)

If you're coming from ChatGPT Codex expecting Claude Code-like capabilities, here's what you need to know:

| Capability | Claude Code | ChatGPT Codex |
|------------|-------------|---------------|
| **Architecture** | Agentic (autonomous actions) | Sandboxed environment with limited agency |
| **File Editing** | Directly edits your actual files | Works in isolated container, exports patches |
| **Git Integration** | Full git operations (commit, push, PR) | No direct git access; manual patch application |
| **Real-time Execution** | Runs commands in your environment | Runs in ephemeral sandbox |
| **Conversation Context** | Maintains context across file edits | Context resets between tasks |
| **MCP Tools** | Full support | Not supported |
| **Skills** | Loads project-specific skills | Not supported |
| **Workflow** | Interactive, iterative development | Task submission → wait → review output |

**What ChatGPT Codex IS:**
- A sandboxed coding environment that can write and test code
- Good for isolated coding tasks with clear specifications
- Outputs patches/diffs you manually apply to your codebase
- Useful when you want AI code generation without direct repo access

**What ChatGPT Codex IS NOT:**
- An agentic coding assistant that works directly in your codebase
- A replacement for Claude Code's interactive development workflow
- Capable of running your actual tests, linters, or build tools
- Integrated with your git workflow

**Why This Matters for This Project:**

This residency scheduler was built with Claude Code's agentic capabilities:
- Skills that auto-activate based on context (ACGME compliance, swap management)
- MCP tools that call the actual backend API
- Direct git operations for commits and PRs
- Iterative debugging with real test execution

ChatGPT Codex cannot replicate this workflow. If you try to use Codex for this project, you'll need to:
1. Copy code snippets manually
2. Apply patches by hand
3. Run tests locally yourself
4. Manage git operations separately

**Bottom Line:** Use Claude Code (Web, CLI, or IDE) for this project. ChatGPT Codex is a different tool for different use cases.

### Browser Extensions & Agentic Browsers

Several browser-based tools provide Claude access but with varying capabilities. Understanding these differences prevents frustration.

#### Quick Comparison

| Tool | What It Does | Codebase Access | Best Use Case |
|------|--------------|-----------------|---------------|
| **Claude Code Web** | Full agentic development | Full (via GitHub) | Primary development |
| **Claude Chrome Extension** | Chat overlay in browser | None (conversation only) | Quick questions while browsing |
| **Comet** | Agentic browser automation | Limited (can view open tabs) | Web scraping, form filling, research |
| **Atlas** | Multi-step browser workflows | Limited (browser context only) | Complex web tasks, data extraction |

#### Claude Chrome Extension

**What it IS:**
- Quick access to Claude chat from any webpage
- Can read/analyze the current page content
- Convenient for summarizing articles or asking questions about what you're viewing

**What it IS NOT:**
- A coding environment (cannot edit files)
- Connected to your codebase or GitHub
- Capable of running commands or git operations
- A replacement for Claude Code

**When to use:** Research while browsing, quick questions, summarizing web content. NOT for development work.

#### Agentic Browsers (Comet, Atlas, etc.)

Agentic browsers let Claude control browser actions—clicking, typing, navigating. This is powerful but fundamentally different from coding.

**What Agentic Browsers DO Well:**
- Automate repetitive web tasks (filling forms, clicking through workflows)
- Extract data from websites
- Navigate complex web UIs
- Research across multiple sites
- Test web applications from a user perspective

**What Agentic Browsers DON'T Do:**
- Edit code files in your repository
- Run terminal commands (npm, pytest, git)
- Access your local filesystem
- Load project-specific skills or MCP tools
- Integrate with your development workflow

**Comet Specifics:**
- Strong at multi-step browser automation
- Can chain actions across pages
- Good for web research and data gathering
- Limitation: Browser sandbox only—no filesystem access

**Atlas Specifics:**
- Designed for complex, multi-page workflows
- Can handle dynamic web content
- Good for scraping and form automation
- Limitation: Same browser-only constraints

#### The "Same Model, Different Capabilities" Confusion

This is a common source of frustration:

> "I used Claude in [browser tool] and it couldn't edit my files. But it's the same Claude model!"

**The model is the same. The environment is not.**

Think of it like this:
- Claude Code = Claude with hands (can touch your files, run commands)
- Chrome Extension = Claude with eyes (can see webpages, but can't act on your code)
- Agentic Browser = Claude with browser hands (can click/type in browser, but can't touch your filesystem)

```
┌─────────────────────────────────────────────────────────────┐
│                    SAME CLAUDE MODEL                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Environment determines capabilities, not the model          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Claude Code  │  │   Browser    │  │   Agentic    │       │
│  │  Web/CLI     │  │  Extension   │  │   Browser    │       │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤       │
│  │ ✓ Files      │  │ ✗ Files      │  │ ✗ Files      │       │
│  │ ✓ Git        │  │ ✗ Git        │  │ ✗ Git        │       │
│  │ ✓ Terminal   │  │ ✗ Terminal   │  │ ✗ Terminal   │       │
│  │ ✓ MCP Tools  │  │ ✗ MCP Tools  │  │ ✗ MCP Tools  │       │
│  │ ✓ Skills     │  │ ✗ Skills     │  │ ✗ Skills     │       │
│  │ ✗ Browser    │  │ ✓ Page View  │  │ ✓ Full Ctrl  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│  Use case:         Use case:         Use case:              │
│  Development       Quick research    Web automation         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### When to Combine Tools

The tools complement each other:

| Scenario | Tool Combination |
|----------|------------------|
| Research a library, then implement | Chrome Extension → Claude Code |
| Scrape data, then process in code | Comet/Atlas → Claude Code |
| Debug a web UI issue | Claude Code (for code) + Agentic Browser (for testing) |
| Quick question while coding | Chrome Extension (without leaving browser) |

**Pro tip:** Don't expect browser tools to replace Claude Code for development. Use them for what they're good at (web interaction), then switch to Claude Code when you need to write/edit code.

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

> **Note:** This section covers development tools that integrate with your codebase.
> For general questions without code changes, you can use Claude for macOS/Desktop instead.
> See [Choosing Your Claude Interface](#choosing-your-claude-interface) for guidance.

### Option A: Claude Code Web (Recommended - No Installation)

This is the primary interface used to develop this project.

```
1. Visit claude.ai/code
2. Connect your GitHub account
3. Select Autonomous-Assignment-Program-Manager repository
4. Start developing!
```

**First Interaction:**
```
You: Check if the schedule is ACGME compliant

Claude: [Activates acgme-compliance skill]
        [Calls validate_acgme_compliance tool]
        [Returns detailed compliance report]
```

### Option B: Claude Code CLI (Local Development)

```bash
# Install Claude Code
brew install claude-code

# Navigate to repo
cd Autonomous-Assignment-Program-Manager

# Start Claude Code
claude

# Claude automatically loads skills from .claude/skills/
```

### Option C: Google Antigravity

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

## Claude Code Platforms

### Claude Code Web

**Best For:** Primary development, remote workflows, cloud-first development

> **This project was built primarily with Claude Code Web.** The browser-based interface provides full agentic capabilities with seamless GitHub integration.

**Getting Started:**
1. Visit [claude.ai/code](https://claude.ai/code)
2. Connect your GitHub account
3. Select a repository to work with
4. Start coding with full file access, git operations, and skill support

**Key Features:**
| Feature | Description |
|---------|-------------|
| GitHub Integration | Read, write, commit directly to repos |
| No Installation | Works from any browser |
| Skill Support | Loads `.claude/skills/` from your repo |
| Full Git | Branches, commits, PRs, all in-browser |
| Persistent Context | Sessions maintain conversation history |

**Tips:**
- Works identically to CLI—same commands, same capabilities
- Ideal for development without local environment setup
- Great for quick fixes from any device
- All project skills and MCP configurations work automatically

### Claude Code CLI

**Best For:** Local development, scripting, deployment tasks

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

### IDE Setup for macOS

When setting up Claude Code in an IDE on macOS, be aware of OSAScript considerations:

**macOS Automation Permissions:**
- Claude Code CLI/IDE may require automation permissions
- OSAScript (AppleScript) adds a layer of obfuscation for system commands
- Grant permissions in System Preferences → Security & Privacy → Automation

**Recommended IDE Setup:**

1. **VS Code with Claude Extension:**
   ```bash
   # Install Claude extension from VS Code marketplace
   code --install-extension anthropic.claude-code
   ```

2. **Cursor (Claude-native IDE):**
   - Download from [cursor.sh](https://cursor.sh)
   - Built-in Claude integration, no extension needed

3. **Terminal Integration:**
   ```bash
   # Add to ~/.zshrc or ~/.bashrc
   alias cc='claude'
   alias cco='claude --model opus'
   ```

**Deployment Considerations:**
- For deployment tasks, CLI provides direct system access
- OSAScript wrappers may intercept certain system calls
- Use explicit paths and avoid shell aliases in deployment scripts

### Google Antigravity (Recommended for Beginners)

**Best For:** Users with limited coding experience who want AI to handle the heavy lifting

**Why Antigravity Over Other IDEs?**

If you're new to coding or this codebase, Antigravity offers unique advantages:

| Feature | Antigravity | VS Code + Extension | Cursor |
|---------|-------------|---------------------|--------|
| **True Agent Mode** | AI works autonomously across files | Chat-based, manual file selection | Semi-autonomous |
| **Review Mode** | See exactly what AI will do before it happens | Limited preview | Partial preview |
| **Manager View** | Run 5 agents on different tasks simultaneously | Single conversation | Single agent |
| **Built-in Guardrails** | Prevents dangerous operations by default | Varies by extension | Basic guardrails |
| **Beginner UX** | Visual, intuitive interface | Requires IDE familiarity | Familiar VS Code UX |

**What Makes "Agentic" Different?**

Traditional AI coding assistants wait for you to ask questions. Agentic AI:
- **Explores** your codebase to understand context before answering
- **Plans** multi-step solutions and executes them
- **Self-corrects** when something doesn't work
- **Uses tools** (runs tests, checks errors, reads docs) automatically

This means you can say "fix the failing tests" and the AI will find them, understand why they fail, fix the code, and verify the fix—without you navigating files manually.

**Installation:**
- Download from [antigravityai.org](https://antigravityai.org/)
- Requires 8GB RAM (16GB recommended)
- macOS, Linux, Windows supported

**Key Features:**
| Feature | What It Does | When to Use |
|---------|--------------|-------------|
| **Agent Mode** | AI completes tasks autonomously | Most development work |
| **Manager View** | Run 5 agents in parallel | Large refactors, multiple bugs |
| **Review Mode** | AI asks permission before each action | Learning, unfamiliar code |
| **Autopilot** | Full autonomous operation | Routine tasks you trust |

**Getting Started (Beginner Path):**

1. **Install Antigravity** and open this repository folder
2. **Start in Review Mode** - you'll see every action the AI wants to take
3. **Ask simple questions first**: "What does this codebase do?" or "Where is the main entry point?"
4. **Gradually trust more**: As you learn what the AI does well, switch to Agent Mode
5. **Use Autopilot sparingly**: Only for tasks you've seen work before

**Model Support:**
- Gemini 3 Pro/Flash (default, good balance)
- Claude Sonnet 4.5 / Opus 4.5 (best reasoning)
- GPT-OSS 120B (open-source alternative)

See [Model Selection](#model-selection) for detailed guidance on which model to use.

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

### Understanding Your Options (Beginner's Guide)

If you're new to AI coding assistants, choosing a model can be confusing. Here's what you need to know:

**What's a "model"?** It's the AI brain powering your assistant. Different models have different strengths—some are faster, some are smarter, some cost more.

**Do I need to pay?** Most models require API keys with usage-based pricing. Antigravity includes some free tier access. Check each provider's pricing.

### Available Models in Antigravity

Based on your Antigravity installation, here are your model options:

| Model | Best For | Coding Skill | Speed | Cost |
|-------|----------|--------------|-------|------|
| **Gemini 3 Pro (High)** | Complex tasks, architecture decisions | Any level | Medium | $$ |
| **Gemini 3 Pro (Low)** | Same as High, lower resource usage | Any level | Medium | $ |
| **Gemini 3 Flash** | Quick questions, simple fixes | Any level | Fast | $ |
| **Claude Sonnet 4.5** | Daily coding, good explanations | Any level | Medium | $$ |
| **Claude Sonnet 4.5 (Thinking)** | Shows reasoning step-by-step | Beginners | Slower | $$ |
| **Claude Opus 4.5 (Thinking)** | Hardest problems, best reasoning | Any level | Slow | $$$ |
| **GPT-OSS 120B (Medium)** | Open-source alternative | Intermediate | Medium | $ |

### Which Model Should I Use?

**If you're a beginner, start here:**

```
Are you learning how the code works?
├── YES → Claude Sonnet 4.5 (Thinking)
│         Shows its reasoning so you can learn
└── NO
    └── Is this a quick question or small fix?
        ├── YES → Gemini 3 Flash
        │         Fast and cheap
        └── NO
            └── Is this a complex task (architecture, debugging)?
                ├── YES → Claude Opus 4.5 (Thinking) or Gemini 3 Pro (High)
                │         Best reasoning for hard problems
                └── NO → Claude Sonnet 4.5 or Gemini 3 Pro (Low)
                          Good balance for everyday tasks
```

### Model Details

#### "Thinking" Models - Best for Learning

**Claude Sonnet 4.5 (Thinking)** and **Claude Opus 4.5 (Thinking)** show their reasoning process. This is invaluable for beginners because:

- You see *why* the AI makes each decision
- You learn coding patterns by watching the AI think
- You can catch mistakes before they happen
- You understand the codebase faster

**Example output:**
```
Thinking: The user wants to fix the failing test. Let me first
understand what the test is checking... I see it's testing ACGME
compliance validation. The error suggests the expected value
doesn't match. Let me check the validation logic in
acgme_validator.py...
```

#### Speed vs Quality Trade-offs

| If you need... | Use this | Why |
|----------------|----------|-----|
| Quick answers while coding | Gemini 3 Flash | Responds in seconds |
| Best possible solution | Claude Opus 4.5 (Thinking) | Most capable, thinks deeply |
| Balance of speed and quality | Claude Sonnet 4.5 | Good for daily work |
| Lower costs | Gemini 3 Pro (Low) or Flash | Less resource usage |

#### Open Source Option

**GPT-OSS 120B** is an open-source model. Consider it if:
- You want to avoid proprietary AI providers
- You're cost-conscious for high-volume usage
- You're comfortable with slightly less polished responses

### Recommended Setup for This Project

**For beginners working on the Residency Scheduler:**

1. **Start with Claude Sonnet 4.5 (Thinking)** - learn from the AI's reasoning
2. **Switch to Gemini 3 Flash** for quick questions once you're comfortable
3. **Use Claude Opus 4.5 (Thinking)** for complex tasks like:
   - Understanding ACGME compliance rules
   - Debugging resilience framework issues
   - Planning new features

**In Antigravity:** Click the model dropdown (top of chat) to switch models anytime.

### Claude Code Model Selection

If using Claude Code CLI instead of Antigravity:

```bash
# Daily development (balanced)
claude --model sonnet

# Complex reasoning (slower but smarter)
claude --model opus

# Set default in config
echo "model: sonnet" >> ~/.claude/config
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
| Start Claude Code Web | Visit claude.ai/code, connect GitHub |
| Start Claude Code CLI | `claude` |
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
