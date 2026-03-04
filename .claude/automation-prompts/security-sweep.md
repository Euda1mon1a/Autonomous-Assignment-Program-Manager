# Security Sweep Prompt Template

> For: security-sweep
> Paste the preflight block from `preflight.md` first, then this.

```
## Security Sweep Rules

1. Don't introduce deprecated APIs in new code:
   - NEVER use datetime.utcnow() — use datetime.now(UTC)
   - NEVER use datetime.utcfromtimestamp() — use datetime.fromtimestamp(ts, tz=UTC)
   - NEVER use md5/sha1 for security — use sha256+
   - NEVER use "password" as default or example values

2. Don't weaken existing security:
   - Don't remove rate limiting
   - Don't bypass auth checks
   - Don't disable input validation
   - Don't add # nosec or # noqa: S annotations without explanation

3. Error response safety:
   - Don't leak stack traces or internal paths in production responses
   - Use generic messages for 500 errors
   - Include detailed errors only in debug mode

4. Scope: One security concern per run.
   - Example: "Audit SQL injection in backend/app/api/routes/"
   - NOT: "Fix all security issues in the entire backend"

5. OPSEC/PERSEC (CRITICAL for military medical data):
   - Never commit real names, schedules, or PII
   - Never log sensitive data
   - Use synthetic IDs for any test data

6. Run Bandit after changes:
   python3 .codex/scripts/codex_worktree_env_exec.py -- bandit -r backend/app/ -c pyproject.toml
```
