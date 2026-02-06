#!/usr/bin/env python3
"""
Security Guidance Hook for Claude Code (PreToolUse)

Adapted from Anthropic's official security-guidance plugin.
Source: https://github.com/anthropics/claude-code/tree/main/plugins/security-guidance

Checks Edit/Write operations for security anti-patterns and blocks with
a warning on first occurrence per session. Patterns checked:

  1. GitHub Actions workflow injection (command injection via untrusted inputs)
  2. child_process.exec (command injection)
  3. new Function() (code injection)
  4. eval() (code injection)
  5. dangerouslySetInnerHTML (XSS)
  6. document.write (XSS)
  7. innerHTML = (XSS)
  8. pickle (arbitrary code execution)
  9. os.system (command injection)
"""

import json
import os
import sys
from datetime import datetime

SECURITY_PATTERNS = [
    {
        "ruleName": "github_actions_workflow",
        "path_check": lambda path: ".github/workflows/" in path
        and (path.endswith(".yml") or path.endswith(".yaml")),
        "reminder": (
            "Security: GitHub Actions workflow edit detected.\n"
            "- Never use untrusted input (${{ github.event.* }}) directly in run: commands\n"
            "- Use env: variables with proper quoting instead\n"
            "- See: https://github.blog/security/vulnerability-research/"
            "how-to-catch-github-actions-workflow-injections-before-attackers-do/"
        ),
    },
    {
        "ruleName": "child_process_exec",
        "substrings": ["child_process.exec", "exec(", "execSync("],
        "reminder": (
            "Security: child_process.exec() detected — risk of command injection.\n"
            "Use execFile() or spawn() with argument arrays instead of shell strings."
        ),
    },
    {
        "ruleName": "new_function_injection",
        "substrings": ["new Function"],
        "reminder": (
            "Security: new Function() with dynamic strings can lead to code injection.\n"
            "Consider alternative approaches that don't evaluate arbitrary code."
        ),
    },
    {
        "ruleName": "eval_injection",
        "substrings": ["eval("],
        "reminder": (
            "Security: eval() executes arbitrary code — major security risk.\n"
            "Use JSON.parse() for data or alternative patterns that avoid code evaluation."
        ),
    },
    {
        "ruleName": "react_dangerously_set_html",
        "substrings": ["dangerouslySetInnerHTML"],
        "reminder": (
            "Security: dangerouslySetInnerHTML can cause XSS if used with untrusted content.\n"
            "Sanitize with DOMPurify or use safe alternatives."
        ),
    },
    {
        "ruleName": "document_write_xss",
        "substrings": ["document.write"],
        "reminder": (
            "Security: document.write() can be exploited for XSS.\n"
            "Use DOM methods like createElement() and appendChild() instead."
        ),
    },
    {
        "ruleName": "innerHTML_xss",
        "substrings": [".innerHTML =", ".innerHTML="],
        "reminder": (
            "Security: Setting innerHTML with untrusted content causes XSS.\n"
            "Use textContent for plain text or sanitize HTML with DOMPurify."
        ),
    },
    {
        "ruleName": "pickle_deserialization",
        "substrings": ["pickle"],
        "reminder": (
            "Security: pickle with untrusted content enables arbitrary code execution.\n"
            "Use JSON or other safe serialization formats."
        ),
    },
    {
        "ruleName": "os_system_injection",
        "substrings": ["os.system", "from os import system"],
        "reminder": (
            "Security: os.system() is vulnerable to command injection.\n"
            "Use subprocess.run() with shell=False and argument lists."
        ),
    },
    {
        "ruleName": "subprocess_shell_true",
        "substrings": ["shell=True"],
        "reminder": (
            "Security: subprocess with shell=True enables command injection.\n"
            "Use shell=False with argument lists: subprocess.run(['cmd', 'arg1', 'arg2'])"
        ),
    },
    {
        "ruleName": "sql_raw_query",
        "substrings": ["text(f\"", "text(f'", "execute(f\"", "execute(f'"],
        "reminder": (
            "Security: f-string in SQL query — risk of SQL injection.\n"
            "Use parameterized queries: text('SELECT ... WHERE id = :id').bindparams(id=val)"
        ),
    },
]


def get_state_file(session_id: str) -> str:
    return os.path.expanduser(f"~/.claude/security_warnings_state_{session_id}.json")


def load_state(session_id: str) -> set:
    state_file = get_state_file(session_id)
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_state(session_id: str, shown: set) -> None:
    state_file = get_state_file(session_id)
    try:
        os.makedirs(os.path.dirname(state_file), exist_ok=True)
        with open(state_file, "w") as f:
            json.dump(list(shown), f)
    except IOError:
        pass


def check_patterns(file_path: str, content: str):
    normalized = file_path.lstrip("/")
    for pattern in SECURITY_PATTERNS:
        if "path_check" in pattern and pattern["path_check"](normalized):
            return pattern["ruleName"], pattern["reminder"]
        if "substrings" in pattern and content:
            for sub in pattern["substrings"]:
                if sub in content:
                    return pattern["ruleName"], pattern["reminder"]
    return None, None


def main():
    try:
        input_data = json.loads(sys.stdin.read())
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        sys.exit(0)

    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    elif tool_name == "MultiEdit":
        content = " ".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    else:
        content = ""

    rule_name, reminder = check_patterns(file_path, content)
    if rule_name and reminder:
        session_id = input_data.get("session_id", "default")
        warning_key = f"{file_path}-{rule_name}"
        shown = load_state(session_id)
        if warning_key not in shown:
            shown.add(warning_key)
            save_state(session_id, shown)
            print(reminder, file=sys.stderr)
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
