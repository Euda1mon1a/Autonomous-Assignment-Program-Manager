# PII Audit Log

**Purpose**: Track PII/OPSEC/PERSEC audits to establish verified-clean baselines. If a leak is ever discovered, this log helps determine how far back to investigate.

---

## Audit #001 - Initial Baseline

| Field | Value |
|-------|-------|
| **Date** | 2025-12-23 |
| **Auditor** | Claude Code (AI-assisted) |
| **Commit** | `935c0bde9dacf595fdcd058b417ec207fcd2e9db` |
| **Branch** | `claude/view-current-activities-Qb2EH` |
| **Result** | **CLEAN** |

### Scan Coverage

| Category | Method | Result |
|----------|--------|--------|
| Human names | Regex scan for `[A-Z][a-z]+ [A-Z][a-z]+` patterns | Only mock data found |
| Email addresses | Regex scan for email patterns | Only mock/example emails |
| Phone numbers | Regex scan for `\d{3}[-.]?\d{3}[-.]?\d{4}` | None found |
| SSN patterns | Regex scan for `\d{3}[-]?\d{2}[-]?\d{4}` | None found |
| Medical titles + names | Regex scan for `Dr\.|MD|PGY-?[1-4]` + name | Only mock data |
| Data files | File extension scan (json, csv, xlsx, dump, sql) | See below |
| JSON name fields | Scan for `first_name`, `last_name` fields | None with real values |

### Data Files Status

| File | Status | Notes |
|------|--------|-------|
| `backend/examples/sample-data/Current AY 25-26 SANITIZED.xlsx` | **Manually Sanitized** | User-verified clean |
| `backend/examples/sample-data/sanitized block 8 and 9 faculty.xlsx` | **Manually Sanitized** | User-verified clean |
| `docs/data/*.json` | **Gitignored** | Not in repo |
| `*.dump`, `*.sql` | **Gitignored** | Not in repo |
| `.env*` | **Gitignored** | Not in repo |

### Mock Data Locations (Intentional - OK)

These files contain clearly fictional names for testing/examples:

| File | Mock Data Type |
|------|----------------|
| `backend/app/api/routes/audit.py` | `_generate_mock_users()` - Dr. Sarah Johnson, Dr. Michael Chen, etc. |
| `frontend/src/mocks/handlers.ts` | john.smith@hospital.org, jane.doe@hospital.org |
| `mcp-server/src/scheduler_mcp/tools.py` | Dr. Williams, Dr. Chen, Dr. Patel (example responses) |
| `mcp-server/tests/*.py` | Dr. Johnson (test fixtures) |
| `mcp-server/examples/*.py` | Dr. Smith, Dr. Martinez (example usage) |

### Gitignore Verification

The following patterns are properly gitignored:

```
# Verified in .gitignore
docs/data/airtable_absences_*.json
docs/data/*_export.json
docs/data/*.json
docs/data/*.csv
docs/data/people.json
*.dump
*.sql
.env
.env.local
.env.*.local
```

### Conclusion

Repository is clean of real PII as of this commit. All names in codebase are:
1. Clearly fictional mock data (Johnson, Chen, Smith, etc.)
2. Generic placeholders (user-001, admin@hospital.mil)
3. Role-based identifiers (PGY1-01, FAC-PD)

The xlsx files in `backend/examples/sample-data/` were manually sanitized by the repository owner before committing.

---

## How to Perform Future Audits

### Quick Scan Commands

```bash
# Human names pattern (will have false positives - review manually)
grep -rn --include="*.py" --include="*.ts" --include="*.json" \
  -E '\b[A-Z][a-z]+\s+[A-Z][a-z]+\b' \
  --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv

# Email addresses
grep -rn --include="*.py" --include="*.ts" --include="*.json" \
  -E '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}' \
  --exclude-dir=node_modules --exclude-dir=.git

# Phone numbers
grep -rn --include="*.py" --include="*.ts" \
  -E '\b\d{3}[-.]?\d{3}[-.]?\d{4}\b' \
  --exclude-dir=node_modules --exclude-dir=.git

# Check for tracked data files
git ls-files | grep -E "\.(xlsx|csv|dump|sql)$"

# Verify gitignore is working
git status --ignored | grep -E "(data|export|dump|sql)"
```

### Adding New Audit Entries

When performing a new audit, add an entry below with:
1. Date and auditor
2. Commit hash (`git rev-parse HEAD`)
3. What was scanned
4. Findings (clean or issues found)
5. Remediation steps if issues were found

---

## Audit History

| # | Date | Commit | Result | Notes |
|---|------|--------|--------|-------|
| 001 | 2025-12-23 | `935c0bd` | CLEAN | Initial baseline audit |

---

## Incident Response

If PII is discovered in the repository:

1. **Document** the finding in this log
2. **Remove** immediately (see DATA_SECURITY_POLICY.md)
3. **Scrub history** if in prior commits (use BFG Repo Cleaner)
4. **Notify** project leads
5. **Determine scope** using this audit log to identify the exposure window

The commit hash from the last clean audit tells you the boundary for investigation.

---

## Automated Scanning

### Pre-commit Hook (Active)

**Configuration:** `.pre-commit-config.yaml`
**Script:** `scripts/pii-scan.sh`

The pre-commit hook runs locally before every commit and checks for:
- SSN patterns (fails commit if found)
- Suspicious .mil email addresses (warning only)
- Staged data files (.csv, .dump, .sql)
- Staged .env files

This provides first-line defense before changes reach GitHub.

### GitHub Actions (Active)

**Workflow:** `.github/workflows/pii-scan.yml`

| Trigger | Frequency | What It Does |
|---------|-----------|--------------|
| PR to main | Every PR | Scans for PII patterns, blocks merge if SSNs found |
| Push to main | Every push | Same scan, results in workflow summary |
| Push to claude/** | Every AI commit | Scans AI-created branches for PII |
| Scheduled | Weekly (Sundays) | Proactive scan even without commits |
| Manual | On-demand | `workflow_dispatch` trigger in Actions tab |

**Scans performed:**
- Email patterns (excluding known mock domains)
- Phone numbers
- SSN patterns (fails build if found!)
- Military .mil domains
- Tracked data files (csv, dump, sql, xlsx)
- Gitignore effectiveness

### Future Options (Production)

#### Option 1: n8n Workflow
```
Trigger: Webhook on push / Scheduled
  → Checkout repo (or use GitHub API)
  → Run scan script
  → Send Slack alert if issues found
  → Update audit log via PR
```

n8n templates exist in `/n8n/workflows/` - create a `pii_scan.json` workflow.

#### Option 2: Claude Code API / Anthropic API
```python
# Periodic deep audit using Claude
import anthropic

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    messages=[{
        "role": "user",
        "content": f"Scan this codebase for PII leakage: {repo_contents}"
    }]
)
```

Benefits:
- Understands context (mock vs real data)
- Can identify subtle patterns regex misses
- Natural language audit reports

#### Option 3: Pre-commit Hook
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pii-scan
        name: PII Scanner
        entry: scripts/pii-scan.sh
        language: script
        pass_filenames: false
```

Blocks commits locally before they even reach GitHub.

#### Option 4: GitHub Secret Scanning
Enable GitHub's built-in secret scanning:
- Settings → Security → Secret scanning
- Automatically detects API keys, tokens, passwords

### Current Production Setup

1. **Pre-commit hook** - First line of defense (local) - **ACTIVE** (`scripts/pii-scan.sh`)
2. **GitHub Actions** - Second line (PR/push) - **ACTIVE** (`.github/workflows/pii-scan.yml`)
3. **Weekly scheduled scan** - Proactive review - **ACTIVE** (Sunday midnight UTC)
4. **GitHub Secret Scanning** - API key detection - Enable in repo settings

This layered approach catches issues at multiple stages.
