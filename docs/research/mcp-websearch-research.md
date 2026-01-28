# MCP Web Search & Research Tools - Research Summary

> **Date:** 2026-01-28
> **Purpose:** Research on Model Context Protocol (MCP) apps and web search capabilities

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

## 8. Recommended Setup for This Project

Based on research needs for the Residency Scheduler project:

### Minimum Recommended Servers

```json
{
  "mcpServers": {
    "perplexity": {
      "command": "npx",
      "args": ["-y", "@perplexity-ai/mcp-server"],
      "env": {
        "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}",
        "STRIP_THINKING": "true"
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

### For Enhanced Research

Add Tavily for citation-heavy research:
```json
{
  "tavily": {
    "command": "npx",
    "args": ["-y", "@tavily/mcp-server"],
    "env": {
      "TAVILY_API_KEY": "${TAVILY_API_KEY}"
    }
  }
}
```

### For Dynamic Content

Add Playwright for scraping JavaScript-heavy sites:
```json
{
  "playwright": {
    "command": "npx",
    "args": ["-y", "@executeautomation/playwright-mcp-server"]
  }
}
```

---

## Sources

### MCP Apps & SDK
- [MCP Apps Official Announcement](http://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/)
- [MCP Apps Documentation](https://modelcontextprotocol.io/docs/extensions/apps)
- [ext-apps GitHub Repository](https://github.com/modelcontextprotocol/ext-apps)

### Web Search Providers
- [Perplexity MCP Server Docs](https://docs.perplexity.ai/guides/mcp-server)
- [Brave Search MCP Server](https://www.pulsemcp.com/servers/brave-search)
- [Tavily MCP Server](https://www.pulsemcp.com/servers/tavily-search)
- [Top 5 MCP Search Tools Evaluation](https://www.oreateai.com/blog/indepth-evaluation-of-the-top-5-popular-mcp-search-tools-in-2025-technical-analysis-and-developer-selection-guide-for-exa-brave-tavily-duckduckgo-and-perplexity/3badf1e2e4f4177c0a04d075c34186e3)

### Browser Automation
- [Playwright MCP Server](https://www.pulsemcp.com/servers/executeautomation-playwright)
- [Puppeteer MCP Server](https://www.pulsemcp.com/servers/twolven-puppeteer)
- [Browser Automation MCP Servers](https://github.com/TensorBlock/awesome-mcp-servers/blob/main/docs/browser-automation--web-scraping.md)

### Directories
- [PulseMCP Server Directory](https://www.pulsemcp.com/servers)
- [Awesome MCP Servers](https://github.com/punkpeye/awesome-mcp-servers)
- [Anthropic Connectors Directory FAQ](https://support.anthropic.com/en/articles/11596036-anthropic-mcp-directory-faq)

### Configuration Guides
- [Claude Code MCP Documentation](https://code.claude.com/docs/en/mcp)
- [MCPcat Setup Guide](https://mcpcat.io/guides/adding-an-mcp-server-to-claude-code/)
- [Configuring MCP Tools - Scott Spence](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
