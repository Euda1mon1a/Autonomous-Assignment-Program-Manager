# LLM/Agents Governance Audit

Date: 2026-02-27  
Scope: `AGENTS.md`, `.codex/`, `.claude/`, `.agent/`, `.antigravity/`, and related policy/workflow/config cohesion.

## Executive Summary

The repo contains a powerful multi-agent operating surface, but governance and documentation are drifting from actual runtime behavior.

Primary issues:
1. Governance toggles are OFF by default while command docs imply active governance.
2. Some command/workflow references point to missing skills/assets.
3. Cross-client MCP configuration is inconsistent (port/package drift).
4. `.gitignore` rules conflict with committed guardrail and skill materials.

## Findings (By Severity)

### Critical

1. Governance controls are explicitly disabled.
- Evidence:
  - [`.claude/Governance/config.json:2`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Governance/config.json:2)
  - [`.claude/Governance/config.json:3`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Governance/config.json:3)
  - [`.claude/Governance/config.json:4`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Governance/config.json:4)
- Risk: policy assumptions in docs may not be enforced in practice.

2. `/governance` command delegates to a missing `governance` skill.
- Evidence:
  - Command delegation text at [`.claude/commands/governance.md:7`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/commands/governance.md:7)
  - Skill directory absent: `.claude/skills/governance` (not found)
- Risk: operator-facing control path appears available but may be non-functional.

### High

1. Capabilities registry drift from actual skills/commands.
- Evidence:
  - Claimed inventory in [`.claude/Governance/CAPABILITIES.md`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/Governance/CAPABILITIES.md)
  - Multiple command references that assume skills are present (e.g. [`fix-code.md:6`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/commands/fix-code.md:6), [`incident.md:6`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.claude/commands/incident.md:6))
- Risk: operator confusion and brittle automation routing.

2. Workflow docs reference assets no longer active/present.
- Evidence:
  - References in `.claude/workflows/*` to missing operational pieces (reported by explorer pass)
  - `.gitignore` explicitly ignores `.claude/Missions/` [`.gitignore:221`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:221)
- Risk: stale runbooks reduce incident response reliability.

3. `.codex` files are designated authoritative but remain within an ignored parent path.
- Evidence:
  - `AGENTS.md` points to `.codex/AGENTS.md` as authoritative
  - Parent ignore [`.gitignore:301`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:301)
- Risk: inconsistent treatment of guardrail artifacts across environments.

4. LLM/agent folders contribute heavily to tracked-vs-ignored contradictions.
- Evidence:
  - `.claude` session/skills rules [`.gitignore:217`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:217)-[`.gitignore:222`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:222)
  - `.agent/` ignored [`.gitignore:233`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.gitignore:233)
  - Contradiction counts show these are top contributors
- Risk: repository hygiene debt and accidental retention of local operational history.

### Medium

1. Antigravity docs conflict with active settings.
- Evidence:
  - README marks Manager View as FUTURE [`.antigravity/README.md:22`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.antigravity/README.md:22)
  - Settings mark Manager View active [`.antigravity/settings.json:35`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.antigravity/settings.json:35)
- Risk: operational misunderstanding during incident or handoff.

2. MCP config drift across clients/tools.
- Evidence:
  - `.codex/config.toml` uses `8081` [`.codex/config.toml:15`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.codex/config.toml:15)
  - `.mcp.json` uses `8080` [`.mcp.json:4`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.mcp.json:4)
  - `.codex/config.toml` and example use different Perplexity package names ([`.codex/config.toml:30`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.codex/config.toml:30), [`.codex/config.toml.example:30`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.codex/config.toml.example:30))
- Risk: setup failures and client-specific behavior drift.

3. Non-portable local paths appear in workflow/prompt docs.
- Evidence:
  - hardcoded `/home/user/...` patterns in `.agent`/`.claude` command and prompt materials (explorer pass)
- Risk: cross-machine reproducibility issues.

### Low

1. Local dev workflow doc contains explicit default credential text.
- Evidence: [`.agent/workflows/deploy-and-test.md:47`](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/.agent/workflows/deploy-and-test.md:47)
- Risk: minor but avoidable credential normalization in docs.

## Recommendations (Advice Only)

1. Choose one governance truth model:
- enable governance and restore missing skill path, or
- formally deprecate command paths and remove stale docs.
2. Auto-generate capabilities/skill indexes in CI and fail on unresolved references.
3. Reconcile MCP config authority per client and enforce consistency checks.
4. Resolve `.gitignore` policy contradictions for `.claude/.codex/.agent` by deciding what is versioned source vs local state.
5. Normalize doc paths to repo-relative patterns (`$REPO_ROOT`) and prune obsolete workflows.

## Related Reports

- [Master repo audit](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/reviews/2026-02-27_repo-audit_master.md)
- [.gitignore audit](/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager/docs/reviews/2026-02-27_gitignore-audit.md)
