#!/usr/bin/env python3
"""Run a command with env vars loaded for Codex worktree automation.

This wrapper resolves the common Codex worktree problem where backend tests run
without `DATABASE_URL` because the worktree has no local env file.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _git_output(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], text=True).strip()
    except Exception:
        return ""


def _env_candidates() -> list[Path]:
    candidates: list[Path] = []
    seen: set[Path] = set()

    def add_env_files(root: Path) -> None:
        for filename in (".env", ".env.codex"):
            env_file = root / filename
            if env_file.exists() and env_file not in seen:
                candidates.append(env_file)
                seen.add(env_file)

    repo_root_raw = _git_output(["rev-parse", "--show-toplevel"])
    repo_root = Path(repo_root_raw).resolve() if repo_root_raw else None

    if repo_root:
        add_env_files(repo_root)

    common_dir_raw = _git_output(["rev-parse", "--git-common-dir"])
    if common_dir_raw:
        common_dir_path = Path(common_dir_raw)
        if not common_dir_path.is_absolute() and repo_root:
            common_dir_path = (repo_root / common_dir_path).resolve()
        else:
            common_dir_path = common_dir_path.resolve()
        primary_root = common_dir_path.parent
        add_env_files(primary_root)

    return candidates


def _parse_env_file(path: Path) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]
        parsed[key] = value
    return parsed


def _hydrate_env(base_env: dict[str, str]) -> dict[str, str]:
    env = dict(base_env)

    for env_file in _env_candidates():
        values = _parse_env_file(env_file)
        for key, value in values.items():
            existing = env.get(key)
            if existing is None or existing == "":
                env[key] = value

    if not env.get("DATABASE_URL") and env.get("DB_PASSWORD"):
        env["DATABASE_URL"] = (
            f"postgresql://scheduler:{env['DB_PASSWORD']}@localhost:5432/"
            "residency_scheduler"
        )

    return env


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: codex_worktree_env_exec.py -- <command> [args...]", file=sys.stderr)
        return 2

    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]
    if not args:
        print("No command provided.", file=sys.stderr)
        return 2

    env = _hydrate_env(os.environ)
    completed = subprocess.run(args, env=env)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
