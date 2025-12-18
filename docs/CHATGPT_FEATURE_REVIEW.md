# ChatGPT Feature Review: Codex & Pulse

> **Date:** 2025-12-18
> **Purpose:** Questions to explore when evaluating OpenAI's Codex and Pulse for potential workflow improvements

---

## OpenAI Codex (Autonomous Coding Agent)

Codex is a cloud-based software engineering agent powered by codex-1 (optimized o3) and GPT-5-Codex. It can work autonomously for 7+ hours on complex tasks, running in isolated environments with full codebase access.

### Questions to Explore

#### 1. Multi-Agent Parallel Task Handling
Given our `PARALLEL_10_TERMINAL_ORCHESTRATION.md` approach:
- How does Codex coordinate multiple parallel agents working on the same codebase?
- What conflict resolution exists when agents touch the same files?
- Can you specify dependencies between parallel tasks?

#### 2. Test-Driven Iteration
Codex "iteratively runs tests until passing":
- Does it understand domain-specific test markers (e.g., `pytest -m acgme`)?
- How does it handle complex validation logic like ACGME compliance rules?
- Can it be configured with custom test commands beyond standard `pytest`/`npm test`?

#### 3. Large Refactor Capability
- Could it handle cross-cutting refactors like "convert resilience framework to async/await" across `backend/app/resilience/*.py`?
- How does it maintain consistency across multiple related files?
- What's the largest refactor scope it can handle reliably?

#### 4. PR Quality
- What do auto-generated PRs look like?
- Commit message style and description quality?
- Does it follow existing repo conventions?

#### 5. Codebase Understanding
- How well does it understand existing architecture patterns?
- Can it reference and follow patterns from `docs/ARCHITECTURE.md`?
- How does it handle domain-specific concepts (ACGME rules, medical scheduling)?

---

## ChatGPT Pulse (Proactive AI Assistant)

Pulse delivers personalized morning briefings based on chats, memory, and connected apps (Gmail, Google Calendar). Currently Pro-only ($200/month).

### Questions to Explore

#### 1. Calendar Integration for Scheduling Systems
- Could it surface alerts like "ACGME compliance deadline approaching"?
- Can it integrate with custom calendar data beyond Google Calendar?
- How would it handle medical residency schedule data?

#### 2. Proactive Research & Monitoring
- Can "overnight research based on chats" track GitHub issues and summarize them?
- Could it monitor CI/CD pipeline status and surface failures?
- How customizable are the research topics?

#### 3. Team Collaboration
- Can multiple team members share Pulse configurations?
- How does it handle project-specific context vs personal preferences?

---

## Comparison Points for Our Project

| Feature | Codex | Pulse | Our Current Approach |
|---------|-------|-------|---------------------|
| Parallel task execution | Cloud agents | N/A | 10-terminal orchestration |
| Test automation | Built-in iteration | N/A | pytest + Jest + Playwright |
| Proactive monitoring | Via PR reviews | Morning briefs | Celery background tasks |
| Calendar/scheduling | N/A | Google Calendar | Custom ACGME scheduler |

---

## Next Steps

1. [ ] Test Codex on a medium-complexity feature branch
2. [ ] Evaluate PR quality against our CONTRIBUTING.md standards
3. [ ] Assess Pulse calendar integration feasibility
4. [ ] Compare autonomous task completion times

---

## References

- [Introducing Codex | OpenAI](https://openai.com/index/introducing-codex/)
- [Introducing upgrades to Codex | OpenAI](https://openai.com/index/introducing-upgrades-to-codex/)
- [Introducing ChatGPT Pulse | OpenAI](https://openai.com/index/introducing-chatgpt-pulse/)
- [OpenAI launches ChatGPT Pulse | TechCrunch](https://techcrunch.com/2025/09/25/openai-launches-chatgpt-pulse-to-proactively-write-you-morning-briefs/)
