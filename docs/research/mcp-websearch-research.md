# MCP Tools Research - Comprehensive Guide

> **Date:** 2026-01-28
> **Purpose:** Research on Model Context Protocol (MCP) servers for web search, development, security, and project-specific needs

---

## Executive Summary

The Model Context Protocol (MCP) has become the universal standard for AI-to-tool integrations since its launch by Anthropic in November 2024. In January 2026, **MCP Apps** launched as the first official MCP extension, enabling interactive UI components within AI conversations. Multiple mature web search MCP servers now exist, providing real-time information access.

---

## 1. MCP Overview

### What is MCP?

MCP (Model Context Protocol) is an open-source standard for connecting AI applications to external systems. Think of MCP like a **USB-C port for AI applications** - providing a standardized way to connect AI applications to external systems.

### Key Stats (2026)
- **7,890+ servers** listed on PulseMCP directory (updated daily)
- **500+ business apps** connectable via platforms like Composio
- Supported by: Claude, ChatGPT, VS Code, Goose, and many more

---

## 2. Web Search MCP Servers

### Top Providers Comparison

| Provider | Free Tier | Key Strengths | Best For |
|----------|-----------|---------------|----------|
| **Brave Search** | 2,000 queries/month | Privacy-focused, 30B+ page index, comprehensive operators | General web search, privacy-conscious use |
| **Tavily** | 1,000 credits/month (~33 searches/day) | Optimized for factual info, strong citations | Research requiring citations |
| **Perplexity** | Varies | Real-time search + reasoning models | Deep research, complex analysis |
| **Exa** | Varies | Academic papers, company data, GitHub | Specialized searches (academic, code) |
| **DuckDuckGo** | Free | Privacy, no API key needed | Quick searches, privacy |

### Official MCP Server Implementations

#### Brave Search
```json
{
  "mcpServers": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/brave-search-mcp"],
      "env": {
        "BRAVE_API_KEY": "your_key_here"
      }
    }
  }
}
```

**Supported Operators:**
- `site:`, `-site:` - Domain filtering
- `filetype:/ext:` - File type filtering
- `intitle:`, `inurl:`, `inbody:` - Content location
- `before:`, `after:` - Date filtering
- `lang:`, `loc:` - Language/location

#### Tavily Search
```json
{
  "mcpServers": {
    "tavily": {
      "command": "npx",
      "args": ["-y", "@tavily/mcp-server"],
      "env": {
        "TAVILY_API_KEY": "your_key_here"
      }
    }
  }
}
```

**Features:**
- Domain filtering via `include_domains`/`exclude_domains`
- Citation support built-in
- Optimized for factual information retrieval

#### Perplexity (Official)
```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "your_key_here"
      }
    }
  }
}
```

**Available Tools:**
| Tool | Model | Best For |
|------|-------|----------|
| `search` | Search API | Current info, news, facts |
| `chat` | sonar-pro | Quick questions, conversational |
| `deep_research` | sonar-deep-research | Comprehensive research, detailed reports |
| `reasoning` | sonar-reasoning-pro | Logical problems, complex analysis |

**Environment Variables:**
- `STRIP_THINKING=true` - Remove thinking tags, save tokens
- `PERPLEXITY_LOG_LEVEL=DEBUG|INFO|WARN|ERROR` - Logging level

### Unified Search Solutions

#### mcp-omnisearch
Provides unified access to multiple providers through a single interface:
- Tavily, Brave, Kagi (search engines)
- Perplexity, FastGPT (AI tools)
- Jina AI, Kagi (content processing)

**Repository:** https://github.com/spences10/mcp-omnisearch

#### One Search MCP
Intelligently routes queries to optimal provider (Brave, Tavily, or Wikipedia) based on query type.

---

## 3. Research Tools

### Perplexity Deep Research

**Installation via Smithery:**
```bash
npx -y @smithery/cli install @arjunkmrm/perplexity-deep-research --client claude
```

**Tool Parameters:**
- `query` (required) - Search query
- `search_recency_filter` (optional) - Filter by: `month`, `week`, `day`, `hour`

### Deep-MCP (Multi-Provider)
Combines Google Gemini and Perplexity for comprehensive research:
```env
GOOGLE_API_KEY=your_google_api_key
PERPLEXITY_API_KEY=your_perplexity_api_key
```

**Repository:** https://github.com/sagiw/deep-mcp

---

## 4. Browser Automation MCP Servers

For dynamic content and interactive research:

### Playwright-based
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    }
  }
}
```

**Options:**
- `microsoft/playwright-mcp` - Official Microsoft implementation
- `executeautomation/playwright-mcp-server` - Community favorite
- `MDBs123/playwright-mcp` - Uses accessibility tree for efficiency

### Puppeteer-based
```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/puppeteer-mcp"]
    }
  }
}
```

**Capabilities:**
- Browser navigation, clicks, form filling
- Full-page and element screenshots
- JavaScript execution in browser context
- Console log monitoring
- Resource management

### Cloud-based Options
- **Browserbase** - Cloud browser automation
- **agent-infra/mcp-server-browser** - Remote browser connection support

---

## 5. MCP Apps (New in January 2026)

### Overview

MCP Apps is the **first official MCP extension**, enabling tools to return interactive UI components that render directly in conversations.

**Supported Clients:**
- Claude (web & desktop)
- ChatGPT
- VS Code (Insiders)
- Goose
- Postman
- MCPJam

### Use Cases
- Interactive dashboards
- Forms and multi-step workflows
- Data visualizations (charts, graphs)
- 3D visualizations (Three.js)
- Interactive maps
- Document viewers (PDF)
- Real-time system monitors

### SDK & Development

**Official Repository:** https://github.com/modelcontextprotocol/ext-apps

**Framework Support:**
- React, Vue, Svelte
- Preact, Solid
- Vanilla JS

**Client Integration:**
```javascript
// Using @mcp-ui/client package
import { MCPAppRenderer } from '@mcp-ui/client';

// Or use App Bridge module directly for custom implementations
```

### Security Features
- Iframe sandboxing
- Pre-declared templates for HTML content
- Auditable messages
- Host-managed approvals for UI-initiated tool calls

---

## 6. Claude Code Configuration Guide

### CLI Commands

```bash
# Add MCP server
claude mcp add [name] --scope user

# List configured servers
claude mcp list

# Remove server
claude mcp remove [name]

# Test server connection
claude mcp get [name]

# Interactive status view
/mcp
```

### Configuration Scopes

| Scope | File Location | Use Case |
|-------|--------------|----------|
| **User** | `~/.claude.json` | Available across all projects |
| **Project** | `.mcp.json` (project root) | Shareable with team |
| **Local** | Default | Private to you in current folder |

### Transport Types

- **stdio** - Standard input/output (most common)
- **SSE** - Server-Sent Events
- **HTTP** - HTTP transport

### HTTP Transport Example
```bash
claude mcp add --transport http --scope local my-mcp-server \
  https://your-mcp-server.com \
  --env API_KEY="your-api-key-here" \
  --header "API_Key: ${API_KEY}"
```

### Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `MCP_TIMEOUT` | Server startup timeout (ms) | `MCP_TIMEOUT=10000 claude` |
| `MAX_MCP_OUTPUT_TOKENS` | Increase token limit (default 10k) | `MAX_MCP_OUTPUT_TOKENS=50000` |

### Windows Note

On native Windows (not WSL), use `cmd /c` wrapper:
```bash
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

### Tool Search Optimization

When MCP tool descriptions consume >10% of context window, Claude Code automatically enables **Tool Search** - dynamically loading tools on-demand instead of preloading all.

---

## 7. Directory Resources

### Official Directories
- **Anthropic Connectors Directory** - Curated, built into Claude Desktop
- **GitHub Official** - https://github.com/modelcontextprotocol/servers

### Community Directories
| Directory | URL | Features |
|-----------|-----|----------|
| PulseMCP | https://pulsemcp.com/servers | 7,890+ servers, daily updates |
| Awesome MCP Servers | https://github.com/punkpeye/awesome-mcp-servers | Curated collection |
| MCP Server Finder | https://mcpserverfinder.com | Category-based search |
| FastMCP | https://fastmcp.me | Explore by category |

---

## 8. Database MCP Servers

### PostgreSQL MCP Servers

#### Reference Server (Read-Only)
```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/postgres-mcp"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

**Features:**
- Schema introspection (tables, columns, constraints, indexes)
- Read-only query execution
- Safe for production use

#### Postgres MCP Pro (Advanced)
```json
{
  "mcpServers": {
    "postgres-pro": {
      "command": "uvx",
      "args": ["postgres-mcp"]
    }
  }
}
```

**Repository:** https://github.com/crystaldba/postgres-mcp

**Additional Features:**
- Query execution plan analysis with hypothetical indexes
- Slow query identification via `pg_stat_statements`
- Index recommendations based on workload analysis
- Health checks: buffer cache, connections, vacuum status, invalid indexes
- Configurable read/write access

#### Full Access Server (Development Only)
```json
{
  "mcpServers": {
    "postgres-full": {
      "command": "npx",
      "args": ["-y", "mcp-postgres-full-access"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

**Repository:** https://github.com/syahiidkamil/mcp-postgres-full-access

**Warning:** Provides full read-write access. Use only in development environments.

### Redis MCP Server

```json
{
  "mcpServers": {
    "redis": {
      "command": "npx",
      "args": ["-y", "@redis/mcp-redis"],
      "env": {
        "REDIS_URL": "${REDIS_URL}"
      }
    }
  }
}
```

**Repository:** https://github.com/redis/mcp-redis

**Use Cases:**
- Cache inspection and debugging
- Celery queue monitoring
- Session management
- Key pattern analysis

---

## 9. DevOps & Infrastructure MCP Servers

### GitHub MCP Server

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@github/github-mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**Repository:** https://github.com/github/github-mcp-server

**Capabilities:**
- Repository management (create, fork, clone)
- Issue and PR operations (create, update, review, merge)
- Code search across repositories
- Branch and commit management
- CI/CD workflow monitoring
- File operations (read, create, update)

### Docker MCP Server

```json
{
  "mcpServers": {
    "docker": {
      "command": "npx",
      "args": ["-y", "@QuantGeekDev/docker-mcp"]
    }
  }
}
```

**Alternative - Docker MCP Toolkit:**
- One-click setup via Docker Desktop
- Pre-configured for Claude Desktop
- Documentation: https://docs.docker.com/ai/mcp-catalog-and-toolkit/

**Capabilities:**
- Container lifecycle management (start, stop, restart, remove)
- Image management (pull, build, list)
- Docker Compose operations
- Log retrieval and streaming
- Network and volume management

---

## 10. Communication MCP Servers

### Slack MCP Server (Official)

```json
{
  "mcpServers": {
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
        "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
      }
    }
  }
}
```

**Required Bot Token Scopes:**
- `channels:read`, `channels:history`
- `chat:write`
- `users:read`

**Capabilities:**
- Send messages to channels
- Read channel history
- List channels and users
- Post formatted messages (Block Kit support)

### Slack Notification MCP (Webhook-based)

```json
{
  "mcpServers": {
    "slack-notify": {
      "command": "npx",
      "args": ["-y", "slack-notification-mcp"],
      "env": {
        "SLACK_WEBHOOK_URL": "${SLACK_WEBHOOK_URL}"
      }
    }
  }
}
```

**Repository:** https://github.com/Zavdielx89/slack-notification-mcp

**Use Cases:**
- Task completion notifications
- Schedule change alerts
- On-call notifications
- Swap request alerts

### Email MCP Server

```json
{
  "mcpServers": {
    "email": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/email-mcp"],
      "env": {
        "SMTP_HOST": "${SMTP_HOST}",
        "SMTP_USER": "${SMTP_USER}",
        "SMTP_PASS": "${SMTP_PASS}"
      }
    }
  }
}
```

**Supports:** Gmail, Outlook, Yahoo, custom SMTP

---

## 11. Security MCP Servers

### MCP-Scan (Security Scanner)

```bash
# Installation
pip install mcp-scan

# Static scan - checks for tool poisoning, prompt injection
mcp-scan scan

# Proxy mode - real-time monitoring
mcp-scan proxy
```

**Repository:** https://github.com/invariantlabs-ai/mcp-scan

**Detects:**
- Tool poisoning attacks
- Cross-origin escalation
- Rug pull attacks
- Toxic flows
- PII exposure
- Indirect prompt injection

### OWASP ZAP MCP Server

```json
{
  "mcpServers": {
    "zap": {
      "command": "npx",
      "args": ["-y", "@lisberndt/zap-mcp"]
    }
  }
}
```

**Prerequisites:** OWASP ZAP running locally

**Capabilities:**
- Active vulnerability scanning
- Passive analysis
- Spider/crawler functionality
- AJAX crawling
- Configurable scan policies

### VSGuard MCP (OWASP ASVS)

```json
{
  "mcpServers": {
    "vsguard": {
      "command": "npx",
      "args": ["-y", "vsguard-mcp"]
    }
  }
}
```

**Features:**
- OWASP ASVS requirements guidance
- Semgrep-based vulnerability scanning
- Custom ASVS rules
- Real-time security recommendations

### OWASP MCP Top 10 Vulnerabilities

| # | Vulnerability | Description |
|---|---------------|-------------|
| 1 | Tool Poisoning | Malicious tools injecting harmful context |
| 2 | Prompt Injection | Untrusted input manipulating model behavior |
| 3 | Context Spoofing | Fake context misleading model decisions |
| 4 | Memory Poisoning | Corrupted memory/state affecting responses |
| 5 | Command Injection | Unsanitized input in system commands |
| 6 | Credential Exposure | Secrets in logs or model memory |
| 7 | Tool Interference | Tools affecting each other's behavior |
| 8 | Covert Channels | Hidden communication bypassing controls |
| 9 | Model Misbinding | Wrong model for security-critical tasks |
| 10 | State Manipulation | Tampering with protocol state |

**Resource:** https://owasp.org/www-project-mcp-top-10/

---

## 12. Calendar & Scheduling MCP Servers

### Google Calendar MCP

```json
{
  "mcpServers": {
    "google-calendar": {
      "command": "npx",
      "args": ["-y", "google-calendar-mcp"],
      "env": {
        "GOOGLE_CLIENT_ID": "${GOOGLE_CLIENT_ID}",
        "GOOGLE_CLIENT_SECRET": "${GOOGLE_CLIENT_SECRET}"
      }
    }
  }
}
```

**Repository:** https://github.com/nspady/google-calendar-mcp

**Features:**
- Multi-account support (work + personal)
- Multi-calendar queries
- Cross-account conflict detection
- Event CRUD operations
- Recurring event handling
- Free/busy queries
- Natural language scheduling

### Outlook Calendar MCP

```json
{
  "mcpServers": {
    "outlook-calendar": {
      "command": "npx",
      "args": ["-y", "outlook-calendar-mcp"]
    }
  }
}
```

**Features:**
- Event management
- Attendee status updates
- Free slot finding
- Meeting scheduling

### Combined Calendar MCP (cal-mcp)

Supports both Google Calendar and Microsoft Outlook in one integration.

**Repository:** https://lobehub.com/mcp/sms03-cal-mcp

---

## 13. Code Quality & Testing MCP Servers

### Code Checker MCP

```json
{
  "mcpServers": {
    "code-checker": {
      "command": "uvx",
      "args": ["mcp-code-checker"]
    }
  }
}
```

**Repository:** https://github.com/MarcusJellinghaus/mcp-code-checker

**Tools:**
- `run_pylint` - Python linting
- `run_pytest` - Test execution
- `run_mypy` - Type checking

### MCP Server Analyzer

```json
{
  "mcpServers": {
    "analyzer": {
      "command": "uvx",
      "args": ["mcp-server-analyzer"]
    }
  }
}
```

**Repository:** https://github.com/Anselmoo/mcp-server-analyzer

**Features:**
- Ruff linting and formatting
- Dead code detection (vulture)
- Complexity analysis (radon)
- Dependency checking

---

## 14. Pricing Models Summary

| Provider | Model | Free Tier | Paid |
|----------|-------|-----------|------|
| **Brave Search** | Usage-based | 2,000 queries/month (ongoing) | $3/1,000 queries |
| **Tavily** | Hybrid | 1,000 credits/month | $0.005-0.008/credit |
| **Perplexity** | Separate | API: None | $1/M tokens + request fees |
| **Exa** | Credits | ~$10-20 signup credits | $49/8,000 credits |
| **GitHub** | Free with limits | Included with account | Enterprise plans available |
| **Redis** | Self-hosted | Free (OSS) | Redis Cloud pricing |
| **PostgreSQL** | Self-hosted | Free (OSS) | Managed DB pricing |

**Note:** Perplexity consumer subscription ($20/mo Pro) provides only $5/month in API credits. API access is purely usage-based with no free tier.

---

## 15. Recommended Setup for This Project

Based on the Residency Scheduler's tech stack (PostgreSQL, Redis, Celery, Docker, GitHub) and requirements (military medical, ACGME compliance, security):

### Priority Tiers

| Tier | MCP Server | Rationale |
|------|------------|-----------|
| **High** | PostgreSQL | Database-heavy app, schema introspection, query debugging |
| **High** | GitHub | Active development, PR/issue management |
| **Medium** | Slack | Existing slack-bot/, schedule notifications |
| **Medium** | Docker | Multiple compose files, container management |
| **Medium** | Redis | Cache/Celery broker inspection |
| **Medium** | MCP-Scan | Security scanning (military/medical context) |
| **Low** | Brave Search | Research, documentation lookups |
| **Low** | Calendar | Schedule visualization (future integration) |

### Recommended Configuration

```json
{
  "mcpServers": {
    "postgres": {
      "command": "uvx",
      "args": ["postgres-mcp"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@github/github-mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "slack": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-slack"],
      "env": {
        "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
        "SLACK_TEAM_ID": "${SLACK_TEAM_ID}"
      }
    },
    "docker": {
      "command": "npx",
      "args": ["-y", "@QuantGeekDev/docker-mcp"]
    },
    "redis": {
      "command": "npx",
      "args": ["-y", "@redis/mcp-redis"],
      "env": {
        "REDIS_URL": "${REDIS_URL}"
      }
    },
    "brave-search": {
      "command": "npx",
      "args": ["-y", "@anthropic-ai/brave-search-mcp"],
      "env": {
        "BRAVE_API_KEY": "${BRAVE_API_KEY}"
      }
    }
  }
}
```

### Environment Variables Required

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/residency_scheduler

# GitHub (create at https://github.com/settings/tokens)
GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# Slack (create app at https://api.slack.com/apps)
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_TEAM_ID=T01234567

# Redis
REDIS_URL=redis://localhost:6379

# Brave Search (get at https://api-dashboard.search.brave.com)
BRAVE_API_KEY=BSA_xxxxxxxxxxxx
```

### Security Scanning Setup

```bash
# Install MCP-Scan
pip install mcp-scan

# Run before deploying new MCP servers
mcp-scan scan

# For continuous monitoring during development
mcp-scan proxy
```

### Use Cases for This Project

| Task | MCP Server | Example |
|------|------------|---------|
| Debug slow queries | PostgreSQL | Analyze `pg_stat_statements`, recommend indexes |
| Review PRs | GitHub | Get PR diff, check CI status, post review |
| Alert on schedule changes | Slack | Notify coordinators of swap approvals |
| Troubleshoot containers | Docker | Check logs, restart services |
| Inspect Celery tasks | Redis | Monitor queue depth, failed tasks |
| Research ACGME rules | Brave Search | Look up compliance requirements |

---

## Sources

### MCP Apps & SDK
- [MCP Apps Official Announcement](http://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/)
- [MCP Apps Documentation](https://modelcontextprotocol.io/docs/extensions/apps)
- [ext-apps GitHub Repository](https://github.com/modelcontextprotocol/ext-apps)

### Web Search Providers
- [Perplexity MCP Server Docs](https://docs.perplexity.ai/guides/mcp-server)
- [Perplexity Pricing](https://docs.perplexity.ai/getting-started/pricing)
- [Brave Search MCP Server](https://www.pulsemcp.com/servers/brave-search)
- [Tavily MCP Server](https://www.pulsemcp.com/servers/tavily-search)
- [Exa Pricing](https://exa.ai/pricing)
- [Top 5 MCP Search Tools Evaluation](https://www.oreateai.com/blog/indepth-evaluation-of-the-top-5-popular-mcp-search-tools-in-2025-technical-analysis-and-developer-selection-guide-for-exa-brave-tavily-duckduckgo-and-perplexity/3badf1e2e4f4177c0a04d075c34186e3)

### Database MCP Servers
- [PostgreSQL MCP Server (Official)](https://www.pulsemcp.com/servers/modelcontextprotocol-postgres)
- [Postgres MCP Pro](https://github.com/crystaldba/postgres-mcp)
- [PostgreSQL Full Access MCP](https://github.com/syahiidkamil/mcp-postgres-full-access)
- [pgEdge Postgres MCP](https://www.pgedge.com/blog/introducing-the-pgedge-postgres-mcp-server)
- [Redis MCP Server](https://github.com/redis/mcp-redis)

### DevOps & Infrastructure
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/get-started/)

### Communication
- [Slack MCP Server (Official)](https://github.com/modelcontextprotocol/servers)
- [Slack Notification MCP](https://github.com/Zavdielx89/slack-notification-mcp)
- [Slack MCP Server (korotovsky)](https://github.com/korotovsky/slack-mcp-server)

### Security
- [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/)
- [OWASP MCP Security Guide](https://genai.owasp.org/resource/cheatsheet-a-practical-guide-for-securely-using-third-party-mcp-servers-1-0/)
- [MCP-Scan](https://github.com/invariantlabs-ai/mcp-scan)
- [OWASP ZAP MCP Server](https://www.pulsemcp.com/servers/lisberndt-zap)

### Calendar & Scheduling
- [Google Calendar MCP](https://github.com/nspady/google-calendar-mcp)
- [Outlook Calendar MCP](https://www.pulsemcp.com/servers/merajmehrabi-outlook-calendar)
- [Microsoft Outlook Calendar MCP Reference](https://learn.microsoft.com/en-us/microsoft-agent-365/mcp-server-reference/calendar)

### Browser Automation
- [Playwright MCP Server](https://www.pulsemcp.com/servers/executeautomation-playwright)
- [Puppeteer MCP Server](https://www.pulsemcp.com/servers/twolven-puppeteer)
- [Browser Automation MCP Servers](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/browser-automation--web-scraping.md)

### Directories
- [PulseMCP Server Directory](https://www.pulsemcp.com/servers)
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers)
- [Anthropic Connectors Directory FAQ](https://support.anthropic.com/en/articles/11596036-anthropic-mcp-directory-faq)
- [Official MCP Servers Repository](https://github.com/modelcontextprotocol/servers)

### Configuration Guides
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [MCPcat Setup Guide](https://mcpcat.io/guides/adding-an-mcp-server-to-claude-code/)
- [Configuring MCP Tools - Scott Spence](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
