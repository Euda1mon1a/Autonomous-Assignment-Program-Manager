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
│  │  21 skills   │   │  16+ tools   │   │  TypeScript  │         │
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

#### Quick Comparison (Updated December 2025)

| Tool | What It Does | Agentic? | Best Use Case |
|------|--------------|----------|---------------|
| **Claude Code Web** | Full agentic development | Yes (files, git, commands) | Primary development |
| **Claude for Chrome** | Browser agent with computer use | Yes (click, type, navigate) | Web automation, multi-tab workflows |
| **Comet** (Perplexity) | AI browser with assistant | Yes (full browser control) | Research, shopping, task automation |
| **Atlas** (OpenAI) | ChatGPT-native browser | Yes (Agent Mode) | Research, form filling, web tasks |
| **Dia** (Browser Company) | AI-first browser | Yes (AI in URL bar) | Everyday browsing with AI assistance |
| **Gemini in Chrome** | Google AI sidebar | Yes (rolling out) | Multi-tab research, Google ecosystem |

> **The landscape has shifted dramatically.** As of late 2025, most major browser tools are now agentic. The question is no longer "agentic or not?" but rather "what kind of agency do you need?"
>
> - **Code agency** (files, git, terminal) → Claude Code
> - **Browser agency** (click, type, navigate web) → Claude for Chrome, Comet, Atlas, Dia
> - **Ecosystem agency** (Google Calendar, Docs, etc.) → Gemini in Chrome

#### Claude for Chrome (Browser Agent)

Claude for Chrome is now a **full agentic browser assistant** that can see, click, type, and navigate web pages autonomously.

**Current capabilities (as of late 2025):**
- **Computer use in browser**: Click, type, scroll, navigate across web pages
- **Multi-tab workflows**: Work across multiple tabs simultaneously
- **Scheduled tasks**: Set up recurring automated workflows
- **Form filling**: Complete forms, manage calendar, draft emails
- **Workflow recording**: "Teach" Claude by recording your actions
- **Claude Code integration**: Connects with Claude Code for development tasks

**Safety measures:**
- Blocked from high-risk categories (financial services, adult content)
- Requires explicit approval for publishing, purchasing, sharing personal data
- Attack mitigations reduced success rate from 23.6% to 11.2%

**Availability:** Beta for all Max plan subscribers after initial 1,000-user pilot.

**What it still IS NOT:**
- A coding environment (cannot edit local files)
- Connected to your local filesystem
- A replacement for Claude Code for development work

**When to use:** Web automation, form filling, email management, calendar tasks, multi-step browser workflows. For actual code editing, use Claude Code.

#### Agentic Browsers (Comet, Atlas, Dia)

These are full browsers with AI agents built in—not extensions, but standalone applications that reimagine browsing around AI.

**What Agentic Browsers DO Well:**
- Automate repetitive web tasks (filling forms, clicking through workflows)
- Extract data from websites
- Navigate complex web UIs
- Research across multiple sites
- Test web applications from a user perspective
- Background task processing (work while you do other things)

**What Agentic Browsers DON'T Do:**
- Edit code files in your repository
- Run terminal commands (npm, pytest, git)
- Access your local filesystem
- Load project-specific skills or MCP tools
- Integrate with your development workflow

#### Comet (Perplexity)

Perplexity's AI-powered browser, released July 2025 and now free for all users.

**Key features:**
- **Comet Assistant**: Sidecar AI that sees your page and answers questions
- **Agentic task execution**: Book hotels, comparison shop, schedule meetings, fill forms
- **Built-in tools**: Discover (news), Spaces (project organization), Shopping, Travel, Finance, Sports
- **Voice interaction**: Hands-free task automation
- **Background Assistant** (Max users): Works on multiple tasks simultaneously in background
- **Privacy-first**: Most processing done locally

**November 2025 updates:** Completely reimagined assistant that can work longer on more complex jobs.

**Best for:** Research, shopping, travel planning, general web automation.

#### Atlas (OpenAI)

OpenAI's ChatGPT-native browser, released October 2025.

**Key features:**
- **Agent Mode**: ChatGPT handles tasks autonomously—"you can watch or don't have to"
- **Built on Chromium**: Familiar Chrome-like experience
- **"Take control" / "Stop" buttons**: Override AI actions at any time
- **Deep ChatGPT integration**: AI accompanies you everywhere across the web

**Availability:** macOS now, Windows/iOS/Android coming. Free tier available, Agent Mode requires paid ChatGPT subscription.

**Security concerns:** Some researchers found it blocked only 5.8% of phishing attacks in tests. Prompt injection risks exist with Agent Mode.

**Best for:** Researchers, students, professionals who need automated web research.

#### Dia (Browser Company → Atlassian)

AI-first browser from the makers of Arc, acquired by Atlassian for $610M.

**Key features:**
- **AI in URL bar**: Type commands to search, summarize, multitask
- **Skill-based AI**: Shopping skill sees your Amazon/Anthropologie history; writing skill knows your email style
- **Privacy-focused**: Data encrypted on device, only sent to cloud for milliseconds
- **Atlassian integration**: Jira, Linear, and other productivity tools
- **Arc features coming**: Sidebar mode, picture-in-picture, custom keyboard shortcuts

**Design philosophy:** Minimalist (like Chrome/Safari) vs Arc's power-user complexity.

**Best for:** Everyday browsing with AI assistance, especially for Atlassian users.

#### Gemini in Chrome

Google's AI integration in Chrome—now rolling out agentic capabilities.

**Current capabilities (late 2025):**
- **Multi-tab context**: Uses up to 10 open tabs to provide relevant responses
- **Gemini Live**: Real-time voice conversations from any tab
- **Agentic browsing** (rolling out): Click, scroll, type on websites (confirms final step like purchases)
- **Tab recall**: Find previously visited sites with natural language
- **Google app integration**: Calendar, Tasks, Drive, Docs/Sheets/Slides, Maps, YouTube
- **AI Mode in address bar**: Complex questions with follow-ups
- **Security**: Gemini Nano detects scams, can auto-change compromised passwords

**Agentic features coming:**
- "Tell Gemini in Chrome what you want to get done, and it acts on web pages on your behalf"
- Book haircuts, order groceries, complete multi-step web tasks

**Availability:** Free for Mac/Windows desktop users in US. iOS coming soon.

**Best for:** Users in the Google ecosystem who want AI assistance integrated with Calendar, Docs, Gmail, etc.

#### Choosing the Right Agentic Tool

Now that most tools are agentic, the question is: **what kind of agency do you need?**

| You want... | Use | Why |
|-------------|-----|-----|
| Edit code, run tests, git operations | **Claude Code** | Only tool with filesystem + terminal access |
| Web automation (forms, booking, shopping) | **Claude for Chrome, Comet, Atlas** | Browser agency |
| Google ecosystem integration | **Gemini in Chrome** | Calendar, Docs, Gmail, Drive integration |
| Research with AI summaries | **Comet, Dia** | Built for information gathering |
| ChatGPT-native experience | **Atlas** | If you're already in OpenAI ecosystem |
| Atlassian/Jira integration | **Dia** | Following Atlassian acquisition |

#### When You DON'T Want Agency

Sometimes you want AI to **observe without acting**—a second pair of eyes, not a pair of hands.

**Scenarios where you want observation-only:**
- Learning how code works (you want explanations, not changes)
- Reviewing before committing (AI shouldn't auto-commit)
- Sensitive operations (you want confirmation at every step)
- Understanding before automating (research phase)

**How to get observation-only behavior:**
- In Claude Code: Ask questions without requesting changes
- In Claude for Chrome: Use chat mode instead of letting it take actions
- In Comet/Atlas: Don't enable Agent Mode
- In Gemini: Agentic features require explicit activation

**The trust ladder:**
1. Start with observation-only (AI explains, you act)
2. Graduate to supervised agency (AI acts, you approve each step)
3. Eventually use full agency for trusted tasks (AI completes multi-step workflows)

#### The "Same Model, Different Capabilities" Confusion

This is a common source of frustration:

> "I used Claude in [browser tool] and it couldn't edit my files. But it's the same Claude model!"

**The model is the same. The environment is not.**

Think of it like this:
- Claude Code = Claude with hands (can touch your files, run commands)
- Chrome Extension = Claude with eyes (can see webpages, but can't act on your code)
- Agentic Browser = Claude with browser hands (can click/type in browser, but can't touch your filesystem)

```
┌───────────────────────────────────────────────────────────────────────────┐
│              2025: THE AGENTIC LANDSCAPE (All Major Tools Are Agentic)     │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  The key question: WHAT KIND of agency do you need?                        │
│                                                                            │
│  ┌─────────────────────── CODE AGENCY ────────────────────────┐           │
│  │  (filesystem, git, terminal, tests)                         │           │
│  │                                                              │           │
│  │  ┌─────────────────┐  ┌─────────────────┐                   │           │
│  │  │  Claude Code    │  │   Antigravity   │                   │           │
│  │  │   Web/CLI/IDE   │  │                 │                   │           │
│  │  ├─────────────────┤  ├─────────────────┤                   │           │
│  │  │ ✓ Edit files    │  │ ✓ Edit files    │                   │           │
│  │  │ ✓ Git/GitHub    │  │ ✓ Git           │                   │           │
│  │  │ ✓ Run tests     │  │ ✓ Run tests     │                   │           │
│  │  │ ✓ Skills/MCP    │  │ ✓ Skills        │                   │           │
│  │  └─────────────────┘  └─────────────────┘                   │           │
│  │  USE FOR: Development, debugging, deployment                 │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                            │
│  ┌─────────────────────── BROWSER AGENCY ─────────────────────┐           │
│  │  (click, type, navigate, automate web tasks)                │           │
│  │                                                              │           │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐│           │
│  │  │  Claude    │ │   Comet    │ │   Atlas    │ │    Dia     ││           │
│  │  │ for Chrome │ │(Perplexity)│ │  (OpenAI)  │ │(Atlassian) ││           │
│  │  ├────────────┤ ├────────────┤ ├────────────┤ ├────────────┤│           │
│  │  │ ✓ Click    │ │ ✓ Click    │ │ ✓ Click    │ │ ✓ AI URL   ││           │
│  │  │ ✓ Type     │ │ ✓ Type     │ │ ✓ Type     │ │ ✓ Skills   ││           │
│  │  │ ✓ Navigate │ │ ✓ Navigate │ │ ✓ Navigate │ │ ✓ Jira     ││           │
│  │  │ ✓ Multi-tab│ │ ✓ Bkgnd    │ │ ✓ Agent    │ │ ✓ Privacy  ││           │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘│           │
│  │  USE FOR: Web automation, shopping, booking, forms          │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                            │
│  ┌─────────────────────── ECOSYSTEM AGENCY ───────────────────┐           │
│  │  (deep integration with specific platforms)                  │           │
│  │                                                              │           │
│  │  ┌─────────────────────────────────────────┐                │           │
│  │  │            Gemini in Chrome              │                │           │
│  │  ├─────────────────────────────────────────┤                │           │
│  │  │ ✓ Google Calendar, Docs, Sheets, Drive  │                │           │
│  │  │ ✓ Gmail, Maps, YouTube                  │                │           │
│  │  │ ✓ Multi-tab context (up to 10 tabs)     │                │           │
│  │  │ ✓ Gemini Live (voice)                   │                │           │
│  │  │ ✓ Agentic browsing (rolling out)        │                │           │
│  │  └─────────────────────────────────────────┘                │           │
│  │  USE FOR: Google Workspace power users                       │           │
│  └──────────────────────────────────────────────────────────────┘           │
│                                                                            │
│  ⚠️  NONE of the browser tools can edit local code files                   │
│  ⚠️  For THIS PROJECT: Use Claude Code (Web, CLI, or IDE)                  │
│                                                                            │
└───────────────────────────────────────────────────────────────────────────┘
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

**Available Skills (21 total):**

| Skill | Purpose |
|-------|---------|
| `acgme-compliance` | ACGME regulatory expertise |
| `automated-code-fixer` | Fix code issues with strict quality gates |
| `code-quality-monitor` | Enforce quality standards before commits |
| `code-review` | Review generated code for bugs, security, performance |
| `database-migration` | Alembic migration expertise and safe schema evolution |
| `fastapi-production` | Production-grade FastAPI patterns |
| `frontend-development` | Next.js 14, React, TailwindCSS patterns |
| `lint-monorepo` | Unified Python (Ruff) + TypeScript (ESLint) linting |
| `pdf` | PDF generation and extraction |
| `pr-reviewer` | Pull request review with quality gates |
| `production-incident-responder` | Crisis response using MCP resilience tools |
| `python-testing-patterns` | Advanced pytest patterns and fixtures |
| `react-typescript` | TypeScript for React/Next.js components |
| `safe-schedule-generation` | Backup-first schedule generation |
| `schedule-optimization` | Multi-objective optimization strategies |
| `security-audit` | Security auditing for healthcare/military contexts |
| `swap-management` | Shift swap workflow procedures |
| `systematic-debugger` | Systematic debugging workflow |
| `test-writer` | Test generation for pytest and Jest |
| `xlsx` | Excel import/export for schedules |

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
| "Review this code" | `code-review` |
| "Add a new database field" | `database-migration` |
| "Review this PR" | `pr-reviewer` |
| "Is this secure?" | `security-audit` |
| "Write tests for this" | `test-writer` |
| "Fix the lint errors" | `lint-monorepo` |
| "TypeScript error in component" | `react-typescript` |
| "Build a new page" | `frontend-development` |
| "Create a new API endpoint" | `fastapi-production` |
| "Debug this flaky test" | `python-testing-patterns` |
| "Investigate this bug" | `systematic-debugger` |
| "Generate a new schedule" | `safe-schedule-generation` |

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

## Admin MCP Chat Interface

The frontend includes a dedicated chat interface for administrators to interact with MCP tools using natural language.

### Components

| Component | Purpose |
|-----------|---------|
| `ClaudeCodeChat` | Main chat interface with streaming messages |
| `MCPCapabilitiesPanel` | Browse all 30+ MCP tools by category |

### Features

- **Chat Persistence**: Sessions survive page refresh (localStorage)
- **MCP Capabilities Panel**: Searchable tool browser with descriptions
- **Quick Prompts**: One-click common actions
- **Artifacts**: Download generated reports as JSON
- **Session History**: Last 20 sessions retained

### Usage

```tsx
import { ClaudeCodeChat, MCPCapabilitiesPanel } from '@/components/admin';

<div className="admin-layout">
  <MCPCapabilitiesPanel onSelectPrompt={(p) => setInput(p)} />
  <ClaudeCodeChat programId="..." adminId="..." />
</div>
```

### Documentation

- [MCP Admin Guide](../admin-manual/mcp-admin-guide.md) - Step-by-step workflows
- [Claude Chat Bridge](../development/CLAUDE_CHAT_BRIDGE.md) - Technical architecture

---

## Resources

- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Google ADK Docs](https://google.github.io/adk-docs/)
- [Antigravity Getting Started](https://codelabs.developers.google.com/getting-started-google-antigravity)
- [Agent Skills Specification](https://agentskills.io)
- [MCP Protocol Spec](https://modelcontextprotocol.io)
