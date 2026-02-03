#!/usr/bin/env python3
"""
Summarize Codex macOS app automation worktrees for a single repo.

Default: scan ~/.codex/worktrees, filter by this repo's origin URL,
and write a concise Markdown report.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
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
        # git@github.com:org/repo -> github.com/org/repo
        host, path = url[4:].split(":", 1)
        return f"{host}/{path}"
    if url.startswith("https://") or url.startswith("http://"):
        # https://github.com/org/repo -> github.com/org/repo
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
        "--output",
        default="",
        help="Output path for report (default: docs/reports/automation/codex_app_report_YYYYMMDD-HHMM.md)",
    )
    parser.add_argument(
        "--include-clean",
        action="store_true",
        help="Include clean worktrees in the report",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    origin_url = args.origin_url or try_run(
        ["git", "config", "--get", "remote.origin.url"], cwd=repo_root
    )
    origin_norm = normalize_remote(origin_url) if origin_url else ""

    root = Path(args.root).expanduser()
    candidates = list(iter_git_repos(root))

    rows = []
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

        row = {
            "path": str(wt),
            "branch": try_run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=wt),
            "head": try_run(["git", "log", "-1", "--oneline"], cwd=wt),
            "status_count": len(status_lines),
            "signal": signal,
            "noise": noise,
            "buckets": buckets,
            "status": status_lines,
            "diffstat": try_run(["git", "diff", "--stat"], cwd=wt),
        }
        rows.append(row)

    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    out_default = (
        Path("docs/reports/automation")
        / f"codex_app_report_{dt.datetime.now().strftime('%Y%m%d-%H%M')}.md"
    )
    output = Path(args.output) if args.output else out_default
    output.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Codex App Automation Report")
    lines.append("")
    lines.append(f"- Generated: {timestamp}")
    lines.append(f"- Worktree root: `{root}`")
    if origin_norm:
        lines.append(f"- Repo origin: `{origin_norm}`")
    lines.append(f"- Worktrees scanned: {len(candidates)}")
    lines.append(f"- Worktrees reported: {len(rows)}")
    lines.append("")

    if not rows:
        lines.append("No matching Codex worktrees with changes found.")
        output.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(str(output))
        return 0

    lines.append("## Summary")
    lines.append("")
    lines.append("| Worktree | Branch | Last commit | Changes | Signal | Noise |")
    lines.append("|---|---|---|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| `{row['path']}` | `{row['branch']}` | `{row['head']}` | "
            f"{row['status_count']} | {row['signal']} | {row['noise']} |"
        )
    lines.append("")

    lines.append("## Details")
    lines.append("")
    for row in rows:
        lines.append(f"### {row['path']}")
        lines.append(f"- Branch: `{row['branch']}`")
        lines.append(f"- Last commit: `{row['head']}`")
        lines.append(f"- Changes: {row['status_count']} (signal {row['signal']} / noise {row['noise']})")
        if row["buckets"]:
            buckets = ", ".join(f"{k}:{v}" for k, v in row["buckets"].items())
            lines.append(f"- Top-level buckets: {buckets}")
        lines.append("")
        if row["status"]:
            lines.append("Status:")
            lines.append("```")
            lines.extend(row["status"])
            lines.append("```")
        if row["diffstat"]:
            lines.append("Diffstat:")
            lines.append("```")
            lines.extend(row["diffstat"].splitlines()[:50])
            lines.append("```")
        lines.append("")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(str(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
