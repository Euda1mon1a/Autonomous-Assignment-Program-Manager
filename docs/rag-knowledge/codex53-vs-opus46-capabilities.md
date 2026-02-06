# Codex vs Opus Capability Delta (Verified 2026-02-06)

> Last verified: 2026-02-06
> Suggested doc_type: `ai_patterns`
> Audience: human operators, orchestrators, and agent maintainers

## Why this doc exists

This is a stable routing reference for deciding when to use Codex 5.3 workflows vs Claude Opus 4.6 workflows in this repository.

## Verified snapshot (as of 2026-02-06)

### Codex / GPT-5.3-Codex (OpenAI)

- OpenAI announced `GPT-5.3-Codex` on **February 5, 2026**.
- OpenAI describes it as stronger than GPT-5.2-Codex on coding plus stronger reasoning/professional knowledge, and **25% faster** for Codex users.
- OpenAI states interactive steering while the agent is running is a core behavior.
- Availability is stated for paid ChatGPT users in Codex app, CLI, IDE extension, and Codex web; OpenAI also states API access for `gpt-5.3-codex` is coming soon, and API-key workflows should continue using `gpt-5.2-codex` until rollout completes.
- Codex app `v260205` changelog also lists support for GPT-5.3-Codex, mid-turn steering, and file attachment/drop improvements.

### Claude Opus 4.6 (Anthropic)

- Anthropic announced Claude Opus 4.6 on **February 5, 2026**.
- Anthropic describes Opus 4.6 as improved for long agentic coding tasks, larger codebases, code review/debugging, and broader knowledge work.
- Anthropic states Opus 4.6 includes a **1M token context window in beta** (first for Opus class).
- Anthropic also announces related controls/features: Claude Code agent teams, API compaction, adaptive thinking, and effort controls.
- Anthropic states Opus 4.6 is available on claude.ai, API, and major cloud platforms.

## Practical differences for this repo

| Area | Codex (GPT-5.3-Codex) | Opus 4.6 | Repo impact |
|---|---|---|---|
| Repo-grounded execution | Strong fit for direct file edits + command execution in local worktrees | Strong reasoning, but this repo’s Codex automation/scripts are already tuned for Codex execution | Use Codex for integration changes, script wiring, and branch-safe cleanup workflows |
| Mid-task steering | Explicitly highlighted in Codex app/changelog | Available conceptually via effort/extended modes; different control surface | Use Codex when you want frequent in-flight course corrections during long edits |
| Long-context synthesis | Strong, but OpenAI messaging emphasizes computer work + execution loop | Anthropic explicitly emphasizes long-context retrieval, 1M beta, and deep research workflows | Use Opus-first for long synthesis drafts; then Codex for implementation and validation |
| API model availability | `gpt-5.3-codex` rollout to API stated as pending | `claude-opus-4-6` already exposed in Anthropic API | For API-key automations today, keep Codex API lane on `gpt-5.2-codex` where needed |
| Skills + workspace model | OpenAI docs/changelog support per-user (`~/.codex/skills`) and per-repo (`.codex/skills`) skills | N/A (Anthropic has separate ecosystem) | Supports shared skill patterns between human + repo-local automation, useful for dual-agent collaboration |

## Recommended routing in this repository

- Use **Opus 4.6 first** for:
  - large cross-document synthesis,
  - policy interpretation writeups,
  - high-context first-pass RAG drafting.
- Use **Codex 5.3 lane** for:
  - converting drafts into repository artifacts,
  - script/config wiring (`scripts/ops/*`, `.codex/*`, docs indexes),
  - verification commands and safety gates.
- Use **both in parallel** when outcome quality depends on both deep synthesis and low-friction repo execution.

## Minimal ingestion metadata

```yaml
doc_type: ai_patterns
source: codex53-vs-opus46-capabilities.md
scope: model-routing
verified_on: 2026-02-06
```

## Sources

- OpenAI Codex changelog: https://developers.openai.com/codex/changelog
- OpenAI GPT-5.3-Codex announcement: https://openai.com/index/introducing-gpt-5-3-codex/
- OpenAI developer changelog (skills/per-user/per-repo references): https://developers.openai.com/changelog
- Anthropic Opus announcement: https://www.anthropic.com/news/claude-opus-4-6
- Anthropic Opus model page: https://www.anthropic.com/claude/opus
