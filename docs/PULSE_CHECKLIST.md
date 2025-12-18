# ChatGPT Pulse Morning Checklist

When reviewing ChatGPT/Pulse suggestions, don't dismiss things too quickly.
Session lesson: Docker Hardened Images news looked like "infra noise" but was directly applicable.

## Quick Triage Questions

### 1. Does this touch something we actually use?
- [ ] Check if we have the technology mentioned (Docker, K8s, specific libraries)
- [ ] `grep -r "keyword" .` or check package.json / requirements.txt
- [ ] If yes → dig deeper, don't dismiss

### 2. Is this regulatory/compliance news?
- [ ] ACGME rule changes → directly affects our validator
- [ ] HIPAA updates → affects data handling
- [ ] Military medical policy → affects Hawaii deployment context

### 3. Is this a "free upgrade" opportunity?
- [ ] Security patches that are drop-in replacements
- [ ] Performance improvements with minimal code change
- [ ] Example: DHI was literally a one-line Dockerfile change for 95% fewer CVEs

### 4. What research would help our architecture?
Good Pulse questions are about **trends and research**, not code:
- "What ACGME duty hour changes are being discussed?"
- "What research exists on schedule optimization and burnout?"
- "What's the state of constraint solvers in 2025?"

Bad Pulse questions (we're faster at these):
- "Write me a FastAPI endpoint for X"
- "Show me how to add Prometheus metrics"

## AI Tooling Setup

### GitHub Claude Integration
- [ ] Install GitHub App
- [ ] Configure ANTHROPIC_API_KEY secret
- [ ] Create claude.yml workflow
- [ ] Test @claude mention

### MCP Server Setup
- [ ] Review MCP integration opportunities
- [ ] Implement FastMCP server
- [ ] Connect to scheduling services
- [ ] Test with Claude Code

### Slack Claude Integration (if using Slack)
- [ ] Setup Slack app
- [ ] Configure workspace
- [ ] Test coding commands

## Today's Docker Update - Layman's Explanation

### What we changed
Switched from regular Docker images to "hardened" ones from `dhi.io`.

### What that means (no jargon)

**Before:** Our app containers were like houses built with standard materials. They work fine, but they have lots of doors and windows - some we use, many we don't. Each unused door is a potential break-in point.

**After:** Hardened images are like houses where we've bricked up every door and window we don't actually need. Same house inside, but way fewer ways for bad guys to get in.

### The numbers
- **95% fewer vulnerabilities** - That's not marketing fluff. Standard Python/Node images ship with hundreds of packages "just in case." DHI strips them out.
- **Same functionality** - Our app doesn't notice the difference. It still has Python, still has Node, still runs the same code.
- **Free** - Docker made this open source in December 2025. We just had to know it existed.

### What we had to change
1. One line in each Dockerfile: `FROM python:3.12` → `FROM dhi.io/python:3.12`
2. Healthchecks: `curl` isn't in hardened images (it's an attack surface), so we use Python/Node instead
3. Multi-stage builds: Keep build tools separate from runtime

### Why this matters for a medical scheduling app
- We handle PII (names, schedules, contact info)
- Healthcare apps are high-value targets
- Fewer vulnerabilities = smaller attack surface = less risk
- When (not if) a CVE drops, we're less likely to be affected

---

## Reminder

> "I dismissed the Docker news as chaff. I was wrong. Stay curious."

The value of Pulse isn't code snippets - it's surfacing things you wouldn't have searched for yourself.
