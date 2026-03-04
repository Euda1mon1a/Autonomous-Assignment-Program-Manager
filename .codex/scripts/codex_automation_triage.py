#!/usr/bin/env python3
"""
Triage Codex macOS app worktrees, produce a plan, and optionally apply it.

Usage:
  # Create a triage plan (JSON)
  python3 scripts/ops/codex_automation_triage.py --plan

  # Apply a plan (cherry-pick/archive), requires clean repo
  python3 scripts/ops/codex_automation_triage.py --apply-plan <plan.json>
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Iterable


def run(cmd: list[str], cwd: Path | None = None) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def try_run(cmd: list[str], cwd: Path | None = None) -> str:
    try:
        return run(cmd, cwd=cwd)
    except Exception:
        return ""


def normalize_remote(url: str) -> str:
    url = url.strip()
    url = re.sub(r"\.git$", "", url)
    if url.startswith("git@") and ":" in url:
        host, path = url[4:].split(":", 1)
        return f"{host}/{path}"
    if url.startswith("https://") or url.startswith("http://"):
        url = re.sub(r"^https?://", "", url)
        return url
    return url


def iter_git_repos(root: Path, max_depth: int = 3) -> Iterable[Path]:
    root = root.expanduser()
    if not root.exists():
        return []
    for dirpath, dirnames, _ in os.walk(root):
        rel = Path(dirpath).relative_to(root)
        if len(rel.parts) > max_depth:
            dirnames[:] = []
            continue
        if (Path(dirpath) / ".git").exists():
            yield Path(dirpath)
            dirnames[:] = []


def parse_status_paths(status_lines: list[str]) -> list[str]:
    paths: list[str] = []
    for line in status_lines:
        if not line:
            continue
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if "->" in path:
            path = path.split("->", 1)[-1].strip()
        paths.append(path)
    return paths


def classify_paths(paths: list[str]) -> dict[str, int]:
    buckets: dict[str, int] = {}
    for path in paths:
        top = path.split("/", 1)[0] if "/" in path else path
        buckets[top] = buckets.get(top, 0) + 1
    return dict(sorted(buckets.items(), key=lambda kv: kv[0]))


def is_noise_path(path: str) -> bool:
    noise_patterns = [
        r"^\.claude/",
        r"^\.codex/",
        r"^backend/\.hypothesis/",
        r"^frontend/\.next/",
        r"^node_modules/",
        r"^dist/",
        r"^build/",
        r"^coverage/",
        r"^docs/reports/automation/",
        r"^frontend/src/types/api-generated",
        r"^frontend/src/types/api-generated-check",
        r"^package-lock\.json$",
        r"^pnpm-lock\.yaml$",
        r"^yarn\.lock$",
    ]
    return any(re.search(pat, path) for pat in noise_patterns)


def signal_summary(paths: list[str]) -> tuple[int, int]:
    noise = sum(1 for p in paths if is_noise_path(p))
    signal = len(paths) - noise
    return signal, noise


def recommend_action(paths: list[str], signal: int, noise: int) -> tuple[str, str]:
    if not paths:
        return "clean", "No changes"
    if signal == 0:
        return "ignore", "Only noise paths changed"
    return "review", "Potential signal (manual review recommended)"


def ensure_clean_repo(repo_root: Path) -> None:
    status = try_run(["git", "status", "--porcelain"], cwd=repo_root)
    if status:
        raise RuntimeError("Working tree is not clean; commit/stash before applying plan.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default="~/.codex/worktrees",
        help="Codex worktree root (default: ~/.codex/worktrees)",
    )
    parser.add_argument(
        "--origin-url",
        default="",
        help="Origin URL to match (defaults to current repo origin)",
    )
    parser.add_argument(
        "--plan",
        action="store_true",
        help="Write a triage plan JSON file to docs/reports/automation",
    )
    parser.add_argument(
        "--plan-out",
        default="",
        help="Path to write the plan JSON (default: docs/reports/automation/codex_app_plan_YYYYMMDD-HHMM.json)",
    )
    parser.add_argument(
        "--apply-plan",
        default="",
        help="Apply a triage plan JSON (cherry-pick/archive)",
    )
    parser.add_argument(
        "--target-branch",
        default="main",
        help="Branch to cherry-pick into (default: main)",
    )
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Auto-commit dirty worktrees before cherry-pick",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Use --no-verify when auto-committing in worktrees",
    )
    parser.add_argument(
        "--allow-delete",
        action="store_true",
        help="Allow deleting archived worktrees",
    )
    parser.add_argument(
        "--include-clean",
        action="store_true",
        help="Include clean worktrees in plan/report",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    origin_url = args.origin_url or try_run(
        ["git", "config", "--get", "remote.origin.url"], cwd=repo_root
    )
    origin_norm = normalize_remote(origin_url) if origin_url else ""

    root = Path(args.root).expanduser()
    candidates = list(iter_git_repos(root))

    rows: list[dict] = []
    for wt in candidates:
        wt_origin = try_run(
            ["git", "config", "--get", "remote.origin.url"], cwd=wt
        )
        if origin_norm and normalize_remote(wt_origin) != origin_norm:
            continue

        status = try_run(["git", "status", "--short"], cwd=wt)
        status_lines = status.splitlines() if status else []
        if not status_lines and not args.include_clean:
            continue

        paths = parse_status_paths(status_lines)
        signal, noise = signal_summary(paths)
        buckets = classify_paths(paths)
        action, note = recommend_action(paths, signal, noise)

        head = try_run(["git", "log", "-1", "--oneline"], cwd=wt)
        head_sha = try_run(["git", "log", "-1", "--format=%H"], cwd=wt)

        rows.append(
            {
                "path": str(wt),
                "branch": try_run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=wt),
                "head": head,
                "head_sha": head_sha,
                "status_count": len(status_lines),
                "signal": signal,
                "noise": noise,
                "buckets": buckets,
                "status": status_lines,
                "paths": paths,
                "recommended_action": action,
                "note": note,
            }
        )

    if args.plan or args.plan_out:
        out_default = (
            Path("docs/reports/automation")
            / f"codex_app_plan_{dt.datetime.now().strftime('%Y%m%d-%H%M')}.json"
        )
        output = Path(args.plan_out) if args.plan_out else out_default
        output.parent.mkdir(parents=True, exist_ok=True)
        plan = {
            "generated_at": dt.datetime.now().isoformat(),
            "worktree_root": str(root),
            "origin": origin_norm,
            "entries": rows,
        }
        output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
        print(str(output))
        return 0

    if args.apply_plan:
        ensure_clean_repo(repo_root)
        plan = json.loads(Path(args.apply_plan).read_text(encoding="utf-8"))
        entries = plan.get("entries", [])
        for entry in entries:
            action = entry.get("action") or entry.get("recommended_action")
            wt_path = Path(entry["path"])
            head_sha = entry.get("head_sha")
            if action == "archive":
                if not args.allow_delete:
                    print(f"Skip archive (allow-delete false): {wt_path}")
                    continue
                if wt_path.exists():
                    shutil.rmtree(wt_path)
                    print(f"Archived: {wt_path}")
                continue

            if action != "cherry-pick":
                continue

            dirty = bool(try_run(["git", "status", "--porcelain"], cwd=wt_path))
            if dirty and not args.auto_commit:
                print(f"Skip dirty worktree (no auto-commit): {wt_path}")
                continue

            if dirty:
                commit_msg = entry.get(
                    "commit_message",
                    f"codex automation: {entry.get('branch', 'worktree')}",
                )
                run(["git", "add", "-A"], cwd=wt_path)
                commit_cmd = ["git", "commit", "-m", commit_msg]
                if args.no_verify:
                    commit_cmd.append("--no-verify")
                run(commit_cmd, cwd=wt_path)
                head_sha = run(["git", "log", "-1", "--format=%H"], cwd=wt_path)

            if not head_sha:
                print(f"Skip cherry-pick (missing head sha): {wt_path}")
                continue

            run(["git", "checkout", args.target_branch], cwd=repo_root)
            run(["git", "cherry-pick", head_sha], cwd=repo_root)
            print(f"Cherry-picked {head_sha} from {wt_path}")

        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
