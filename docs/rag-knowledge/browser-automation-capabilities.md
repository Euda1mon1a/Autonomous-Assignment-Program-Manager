# Browser Automation Capabilities (Claude in Chrome)

> **doc_type:** technical_doc
> **Last Updated:** 2026-01-16
> **Topic:** browser automation, chrome extension, research platforms
> **Keywords:** browser automation, perplexity blocked, gemini automation, web research, form input, screenshots, ExtensionsSettings policy

---

## Overview

Claude Code has browser automation capabilities through the `claude-in-chrome` MCP extension. This document captures which platforms support automation, which are blocked, and recommended workarounds.

---

## Platform Compatibility

### Fully Automatable Platforms

The following platforms allow full browser automation:

| Platform | URL | Automation Status | Notes |
|----------|-----|-------------------|-------|
| **Google Gemini** | gemini.google.com | FULL ACCESS | Primary research platform |
| **Google AI Studio** | aistudio.google.com | FULL ACCESS | API testing, model playground |
| **Wikipedia** | wikipedia.org | FULL ACCESS | General knowledge |
| **General websites** | varies | FULL ACCESS | Most sites work |

### Blocked Platforms

The following platforms block browser automation via enterprise security policies:

| Platform | URL | Automation Status | Cause | Workaround |
|----------|-----|-------------------|-------|------------|
| **Perplexity** | perplexity.ai | ALL CONTENT SCRIPTS BLOCKED | ExtensionsSettings policy | Use WebSearch tool instead |

### Why Perplexity is Blocked

Perplexity uses Chrome's **ExtensionsSettings enterprise policy** to block ALL content script injection. This security measure prevents any browser extension from:
- Reading page content (DOM, accessibility tree)
- Executing JavaScript
- Taking screenshots
- Interacting with page elements

**Error message you'll see:**
> "ExtensionsSettings policy"

**The only workaround is to use Claude's built-in `WebSearch` tool**, which bypasses the browser entirely.

---

## Tool Availability by Platform

| Tool | Gemini | AI Studio | Perplexity | General Sites |
|------|:------:|:---------:|:----------:|:-------------:|
| `navigate` | YES | YES | YES | YES |
| `read_page` | YES | YES | BLOCKED | YES |
| `get_page_text` | YES | YES | BLOCKED | YES |
| `computer` (screenshot) | YES | YES | BLOCKED | YES |
| `find` | YES | YES | BLOCKED | YES |
| `form_input` | PARTIAL | YES | BLOCKED | YES |
| `javascript_tool` | YES | YES | BLOCKED | YES |
| `click` | YES | YES | BLOCKED | YES |
| `scroll` | YES | YES | BLOCKED | YES |

**Note:** `form_input` is marked PARTIAL on Gemini because the input uses a DIV-based textbox, which requires the click + type pattern instead of direct form input.

---

## Research Workflow Patterns

### Gemini Research Workflow (Recommended)

The recommended pattern for AI-assisted research using browser automation:

1. **Navigate:** Open gemini.google.com
2. **Click input:** Click on the text input area to focus
3. **Type query:** Enter the research question
4. **Submit:** Press Enter or click Send button
5. **Wait:** Allow Gemini to process (especially with "Thinking" mode)
6. **Scroll:** Navigate through the full response
7. **Expand sources:** Click "Sources" button to reveal citations
8. **Extract URLs:** Read source URLs from the sidebar
9. **Export:** Write findings to scratchpad for persistence

### DIV Textbox Pattern

Many modern sites (including Gemini) use DIV-based contenteditable textboxes instead of `<input>` elements. The standard `form_input` tool may not work. Use this pattern instead:

1. **Click** on the text area to focus it
2. **Type** content using keyboard simulation
3. **Press Enter** or click submit button

---

## Fallback Strategy for Research

When browser automation fails, use this fallback hierarchy:

| Priority | Platform | Method | When to Use |
|----------|----------|--------|-------------|
| 1 (Primary) | Google Gemini | Full browser automation | Default for research tasks |
| 2 (Secondary) | Google AI Studio | Browser automation | API testing, model comparison |
| 3 (Tertiary) | WebSearch tool | Built-in Claude tool | When browser blocked or unavailable |
| 4 (Last resort) | Navigate only | Open URL for user | Let user read manually |

---

## Common Errors and Solutions

### Error: "ExtensionsSettings policy"

**Cause:** The website uses Chrome enterprise policy to block all extension content scripts.

**Solution:** This cannot be bypassed. Use one of these alternatives:
- Switch to Google Gemini for research
- Use the built-in `WebSearch` tool
- Navigate and let the user read manually

### Error: "Tab doesn't exist" or Invalid Tab ID

**Cause:** Tab IDs from previous sessions are stale or the tab was closed.

**Solution:**
1. Call `tabs_context_mcp` to get fresh tab IDs
2. Never reuse tab IDs from previous sessions
3. Create a new tab if the target doesn't exist

### Error: Form input fails silently

**Cause:** The site uses custom DIV-based textboxes instead of `<input>` elements.

**Solution:** Use the click + type pattern:
1. Click on the text area to focus
2. Type content using keyboard simulation
3. Press Enter to submit

### Error: Modal dialog blocks automation

**Cause:** JavaScript `alert()`, `confirm()`, or `prompt()` dialogs block all browser events.

**Solution:**
- Avoid actions that trigger these dialogs
- Warn the user if unavoidable
- User must manually dismiss the dialog

---

## Tool Reference

### Available Browser Automation Tools

| Tool | Purpose | Common Use Case |
|------|---------|-----------------|
| `mcp__claude-in-chrome__navigate` | Open a URL | Navigate to any webpage |
| `mcp__claude-in-chrome__read_page` | Read page content | Extract text, find elements |
| `mcp__claude-in-chrome__get_page_text` | Get visible text | Quick content extraction |
| `mcp__claude-in-chrome__computer` | Take screenshot | Visual capture and analysis |
| `mcp__claude-in-chrome__find` | Search for elements | Locate buttons, links, forms |
| `mcp__claude-in-chrome__form_input` | Fill form fields | Enter text in standard inputs |
| `mcp__claude-in-chrome__javascript_tool` | Run JavaScript | Advanced DOM interactions |
| `mcp__claude-in-chrome__tabs_create_mcp` | Open new tab | Multi-tab workflows |
| `mcp__claude-in-chrome__tabs_context_mcp` | List open tabs | Get fresh tab IDs |
| `mcp__claude-in-chrome__gif_creator` | Record GIF | Document multi-step workflows |

---

## Security and Privacy Constraints

Browser automation tools **cannot and must not**:

- Enter passwords or authentication credentials
- Complete CAPTCHA or human verification
- Bypass enterprise security policies
- Download files without explicit user permission
- Access browser history, bookmarks, or saved passwords
- Enter financial information (credit cards, bank accounts)
- Modify security permissions or access controls

---

## Platform-Specific Notes

### Google Gemini

- **Best for:** Deep research with "Thinking" mode
- **Authentication:** Uses user's Google SSO automatically
- **Input method:** Click + type (DIV textbox)
- **Sources:** Available via sidebar after response completes
- **Rate limits:** Standard Google usage limits apply

### Google AI Studio

- **Best for:** API key management, model playground testing
- **Authentication:** Uses user's Google SSO automatically
- **Full access to:** Gemini 3 API, usage monitoring, app creation

### General Websites

- **Most sites work** unless they use enterprise extension blocking
- **Check for** CAPTCHA, login requirements, rate limiting
- **Avoid** sites that require JavaScript-heavy single-page apps with complex state

---

## Related Resources

- Human-readable guide: `docs/guides/BROWSER_AUTOMATION_GUIDE.md`
- Technical recon notes: `.claude/Scratchpad/SESSION_2026-01-16_BROWSER_AUTOMATION_RECON.md`
- Deep research skill: `.claude/skills/deep-research/SKILL.md`

---

*This document is optimized for RAG search. Query examples: "which platforms support browser automation", "why is perplexity blocked", "how to input text in gemini", "browser automation fallback strategy"*
