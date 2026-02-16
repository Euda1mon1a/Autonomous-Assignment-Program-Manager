# Codex Safe Prune Plan

- Timestamp: `2026-02-05 22:13:18 HST`
- Worktree root: `/Users/aaronmontgomery/.codex/worktrees`
- Base ref: `origin/main`
- Excluded IDs: `bad1`
- Mode: `plan-only`

## BLUF

- Worktrees scanned: `5`
- Prune-ready now: `4`
- Excluded by policy: `1`
- Blocked (dirty/unique): `0`

Safe prune set: `2a44,8667,aa99,b55a`

## Plan Table

| ID | Dirty | Unique | Decision | Reason |
|---|---:|---:|---|---|
| `2a44` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `8667` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `aa99` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `b55a` | 0 | 0 | `prune-ready` | clean + no unique commits |
| `bad1` | 2 | 5 | `keep` | explicitly excluded |

## Manual Command (Plan Mode)

```bash
rm -rf "/Users/aaronmontgomery/.codex/worktrees/2a44"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/8667"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/aa99"
rm -rf "/Users/aaronmontgomery/.codex/worktrees/b55a"
```

## Notes

- This plan intentionally excludes `bad1` unless you remove it from `--exclude-ids`.
- Re-run this script before any destructive cleanup to account for new commits.

