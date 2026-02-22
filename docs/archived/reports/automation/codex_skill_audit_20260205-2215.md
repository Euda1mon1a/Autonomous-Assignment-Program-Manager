# Codex Skill Audit

- Timestamp: `2026-02-05 22:15:56 HST`
- Repo: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager`

## Counts

- Total SKILL.md files found: `77`
- .codex/skills: `3`
- .claude/skills: `41`
- ~/.claude/skills: `33`
- Missing explicit frontmatter `name:` (fallback to folder name): `2`

## Duplicate Skill Names

- `codex-app-automation-triage`
  - [codex] /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.codex/skills/codex-app-automation-triage/SKILL.md
  - [claude] /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/skills/codex-app-automation-triage/SKILL.md
- `skill-creator`
  - [codex] /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.codex/skills/.system/skill-creator/SKILL.md
  - [home-claude] /Users/aaronmontgomery/.claude/skills/.system/skill-creator/SKILL.md
- `skill-installer`
  - [codex] /Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.codex/skills/.system/skill-installer/SKILL.md
  - [home-claude] /Users/aaronmontgomery/.claude/skills/.system/skill-installer/SKILL.md

## Quick Actions

- Run `scripts/ops/codex_cherry_pick_hunter.sh --save` before any worktree prune
- Keep high-signal skills in one canonical location to reduce routing ambiguity
- Add/normalize frontmatter `name:` where missing for reliable discovery
