# Browser Automation Guide for AI-Assisted Research

> **Purpose:** Enable humans (and AI agents) to use browser automation tools effectively for research and web interaction
> **Last Updated:** 2026-01-16
> **Audience:** End users, coordinators, developers

---

## Overview

Claude Code has access to browser automation tools through the `claude-in-chrome` MCP extension. These tools allow Claude to:
- Navigate web pages
- Read page content
- Fill forms and click buttons
- Take screenshots
- Record GIFs of multi-step workflows

However, not all websites allow automation. This guide documents which platforms work and which don't.

---

## Platform Compatibility Matrix

| Platform | Navigation | Read Content | Screenshots | Form Input | Notes |
|----------|:----------:|:------------:|:-----------:|:----------:|-------|
| **Google Gemini** | Yes | Yes | Yes | Yes | Full automation support |
| **Google AI Studio** | Yes | Yes | Yes | Yes | Full automation support |
| **Perplexity.ai** | Yes | **BLOCKED** | **BLOCKED** | **BLOCKED** | Enterprise policy blocks extensions |
| **Google Scholar** | Yes | Partial | Yes | Partial | May require login for full access |
| **Wikipedia** | Yes | Yes | Yes | Yes | Full automation support |
| **General websites** | Yes | Yes | Yes | Yes | Most sites work |

### Why Perplexity is Blocked

Perplexity uses Chrome's **ExtensionsSettings enterprise policy** to block ALL content script injection. This is a security measure that prevents any browser extension from:
- Reading page content (DOM, accessibility tree)
- Executing JavaScript
- Taking screenshots
- Interacting with page elements

**Workaround:** Use Claude's built-in `WebSearch` tool instead, which bypasses browser entirely.

---

## Recommended Research Platforms

### 1. Google Gemini (gemini.google.com) - PRIMARY

**Status:** Fully supported for automated research

**Why Gemini Works Best:**
- Full DOM access for reading responses
- "Thinking" mode provides deep reasoning
- Sources sidebar with clickable citations
- No extension blocking policies

**Workflow:**
1. Claude navigates to gemini.google.com
2. Enters research query via click + type
3. Submits and waits for response
4. Scrolls through full response
5. Clicks "Sources" to expand citations
6. Extracts source URLs for verification

### 2. Google AI Studio (aistudio.google.com) - SECONDARY

**Status:** Fully supported

**Use Cases:**
- API key management
- Gemini API testing
- Model playground access
- Usage monitoring

### 3. Built-in WebSearch - FALLBACK

**Status:** Always available (no browser needed)

**When to Use:**
- Perplexity-style multi-source searches
- When browser extension is unavailable
- Quick fact-checking

---

## Step-by-Step: Gemini Research Workflow

### Prerequisites
1. Chrome browser with Claude-in-Chrome extension installed
2. Logged into your Google account

### Research Workflow

**Step 1: Open Gemini**
```
Claude uses navigate tool to open gemini.google.com
```

**Step 2: Enter Query**
- Claude clicks on the input field
- Types your research question
- Presses Enter or clicks Send

**Step 3: Wait for Response**
- Gemini processes with "Thinking" mode (if enabled)
- Claude waits for response to complete
- Scrolls through full content

**Step 4: Extract Sources**
- Click "Sources" in response
- Read sidebar with source URLs
- Claude captures URLs for verification

**Step 5: Export Findings**
- Claude writes findings to a scratchpad file
- Includes source URLs and key insights
- Returns summary to you

---

## Tool Reference

### Available Browser Tools

| Tool | Function | Use Case |
|------|----------|----------|
| `navigate` | Open a URL | Go to any webpage |
| `read_page` | Read page content | Extract text, find elements |
| `get_page_text` | Get all visible text | Quick content extraction |
| `computer` | Take screenshot | Visual capture |
| `find` | Search for elements | Locate buttons, links, forms |
| `form_input` | Fill form fields | Enter text in inputs |
| `javascript_tool` | Run JavaScript | Advanced interactions |
| `tabs_create_mcp` | Open new tab | Multi-tab workflows |
| `tabs_context_mcp` | List open tabs | Context awareness |
| `gif_creator` | Record GIF | Multi-step documentation |

### Tool Limitations

- **Cannot bypass security:** If a site blocks extensions, tools won't work
- **No password entry:** Never enter passwords via automation
- **No CAPTCHA solving:** Cannot complete human verification
- **Modal dialogs:** Avoid triggering alert/confirm popups (blocks automation)

---

## Troubleshooting

### Problem: "ExtensionsSettings policy" error

**Cause:** Website blocks all extension content scripts

**Solution:** Use a different platform or built-in WebSearch
```
Example: Instead of Perplexity, use Gemini for research
```

### Problem: Claude says "Tab doesn't exist"

**Cause:** Tab IDs from previous sessions are stale

**Solution:** Claude should call `tabs_context_mcp` to get fresh tab IDs

### Problem: Form input not working

**Cause:** Some sites use custom DIV-based textboxes instead of `<input>` elements

**Solution:** Use click + type pattern instead of direct form input
```
1. Click on the text area to focus
2. Type content character by character
3. Press Enter to submit
```

### Problem: Chrome vs Comet confusion

**Cause:** Multiple browser extensions or profiles

**Solution:** Ensure Claude-in-Chrome extension is:
1. Installed and enabled in Chrome
2. Connected (look for extension icon status)
3. Only one instance running

### Problem: Extension disconnected

**Symptoms:** Tools return errors about connection

**Solution:**
1. Refresh the Claude Code session
2. Reload the Chrome extension (disable/re-enable)
3. Restart Chrome if needed

---

## Use Cases for Human Users

### Supported Research Tasks

1. **Literature Review**
   > "Search Gemini for academic research on [topic] and compile findings with sources"

2. **Multi-Source Verification**
   > "Research [claim] across multiple sources and summarize the consensus"

3. **Technical Documentation**
   > "Look up the official documentation for [technology] and extract the key patterns"

4. **Competitive Analysis**
   > "Research [company/product] and compile their features and pricing"

### What Claude Cannot Do

- Enter passwords or financial information
- Complete CAPTCHA or human verification
- Access sites that block browser extensions
- Download files without your permission
- Access your browser history or bookmarks

---

## For Developers: Skill Integration

If building skills that use browser automation:

```yaml
# Good pattern - check platform compatibility
fallback_strategy:
  primary: gemini.google.com  # Full automation
  secondary: aistudio.google.com  # API-based
  tertiary: WebSearch tool  # Built-in fallback
```

See: `.claude/skills/deep-research/SKILL.md` for an example implementation.

---

## Related Resources

- `.claude/skills/deep-research/SKILL.md` - Automated research skill
- `.claude/Scratchpad/SESSION_2026-01-16_BROWSER_AUTOMATION_RECON.md` - Technical reconnaissance notes
- Claude Code documentation on browser tools

---

*This guide documents browser automation capabilities as of 2026-01-16. Platform policies may change.*
