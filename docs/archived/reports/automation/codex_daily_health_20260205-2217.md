# Codex Daily Health

- Timestamp: `2026-02-05 22:16:37 HST`
- Repo: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager`

## MCP Visibility

- codex mcp list: `ok`
- enabled rows detected: `2`

```text
Name        Command  Args                          Env                       Cwd  Status   Auth       
perplexity  npx      -y @perplexity-ai/mcp-server  PERPLEXITY_API_KEY=*****  -    enabled  Unsupported

Name                 Url                        Bearer Token Env Var  Status   Auth       
residency-scheduler  http://127.0.0.1:8081/mcp  -                     enabled  Unsupported
```

## Local MCP Server

- health endpoint: `ok`
- status: `healthy`
- api_credentials_configured: `true`

```json
{"status":"healthy","service":"residency-scheduler-mcp","version":"0.1.0","timestamp":"2026-02-06T08:16:38.070393Z","checks":{"mcp_server":"ok","api_key_configured":false,"api_credentials_configured":true}}
```

## Hook + Scanner Health

- codex_safety_audit: `pass`
- report: `docs/reports/automation/codex_safety_audit_20260205-2217.md`

```text
# Codex Safety Audit

- Timestamp: `2026-02-05 22:16:38 HST`
- Repo: `/Users/aaronmontgomery/Autonomous-Assignment-Program-Manager`

## Hook Audit

- pre-commit: `pre-commit 4.3.0`
- git hooks path: `.git/hooks`
- .git/hooks/pre-commit: `present`

### Security Scan Results

- pii-scan: `pass`
- gitleaks: `pass`

### pii-scan Output (tail)

```text
PII/OPSEC scanner (military medical data)................................Passed
```

### gitleaks Output (tail)

```text
Gitleaks - Detect secrets................................................Passed
```

**Result:** PASS


Saved report: docs/reports/automation/codex_safety_audit_20260205-2217.md
```

## Cherry-Pick Risk

- hunter report: `docs/reports/automation/codex_cherry_pick_hunter_20260205-2217.md`
- risk status: `attention required`

## Skill Drift

- codex_skill_audit: `ok`
- report: `docs/reports/automation/codex_skill_audit_20260205-2217.md`

## Automation Schedule Snapshot

- codex_app_schedule_status: `ok`

```text
ID                           TIME       STATUS   RRULE
---------------------------- ---------- -------- -----
check-for-bandit-issues      01:24      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=24;BYDAY=SU,MO,TU,WE,TH,FR,SA
check-for-mypy-issues        01:28      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=28;BYDAY=SU,MO,TU,WE,TH,FR,SA
ci-lite                      01:40      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=40;BYDAY=SU,MO,TU,WE,TH,FR,SA
codex-cherry-pick-hunter     01:54      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=54;BYDAY=SU,MO,TU,WE,TH,FR,SA
codex-daily-health           02:00      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=2;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA
codex-skill-audit            01:58      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=58;BYDAY=SU,MO,TU,WE,TH,FR,SA
codex-storage-hygiene        01:56      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=56;BYDAY=SU,MO,TU,WE,TH,FR,SA
codex-worktree-triage        01:02      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=2;BYDAY=SU,MO,TU,WE,TH,FR,SA
daily-bug-scan               01:05      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=5;BYDAY=SU,MO,TU,WE,TH,FR,SA
hook-pii-health-check        01:00      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA
inspiration                  01:50      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=50;BYDAY=SU,MO,TU,WE,TH,FR,SA
pre-release-check            01:20      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=20;BYDAY=SU,MO,TU,WE,TH,FR,SA
rag-ingest-readiness         01:08      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=8;BYDAY=SU,MO,TU,WE,TH,FR,SA
security-sweep               01:12      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=12;BYDAY=SU,MO,TU,WE,TH,FR,SA
test-gap-detection           01:16      ACTIVE   RRULE:FREQ=WEEKLY;BYHOUR=1;BYMINUTE=16;BYDAY=SU,MO,TU,WE,TH,FR,SA
```

## Overall

**Result:** ATTENTION REQUIRED
