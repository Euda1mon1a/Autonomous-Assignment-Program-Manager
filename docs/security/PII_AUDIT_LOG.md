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
