# PII Sanitization SOP

> **Standard Operating Procedure for Sharing Schedule Data with Claude Code IDE**
> **Last Updated:** 2025-12-23

---

## Purpose

This SOP defines the process for sanitizing real schedule data so Claude Code IDE can assist with development tasks without exposure to PERSEC (Personal Security) or OPSEC (Operational Security) information.

---

## Quick Reference

```bash
# Sanitize data before sharing with Claude Code IDE
python scripts/sanitize_pii.py input.json sanitized.json

# Restore original data (user only - never share mapping file)
python scripts/sanitize_pii.py --reverse .sanitize/mapping_*.json sanitized.json restored.json
```

---

## When to Use This Process

| Scenario | Sanitize? | Notes |
|----------|-----------|-------|
| Sharing schedule JSON with IDE | **YES** | Always sanitize before pasting |
| Debugging assignment issues | **YES** | Use synthetic IDs in error reports |
| Database query results | **YES** | Sanitize before sharing |
| Code review (no data) | No | Code doesn't contain PII |
| Test data already synthetic | No | Test fixtures use synthetic data |

---

## Workflow

### Step 1: Export Data

Export the data you need to share from your local database or Airtable:

```bash
# Example: Export from database
docker-compose exec db psql -U scheduler -d residency_scheduler \
  -c "COPY (SELECT * FROM assignments WHERE block_number = 10) TO STDOUT WITH CSV HEADER" \
  > block10_export.csv

# Or use API export endpoint
curl -s http://localhost:8000/api/schedule/export?block=10 > block10_export.json
```

### Step 2: Sanitize the Data

Run the sanitization script:

```bash
cd /path/to/Autonomous-Assignment-Program-Manager
python scripts/sanitize_pii.py block10_export.json block10_sanitized.json
```

**Output:**
```
Mapping saved to: .sanitize/mapping_20231223_143022.json
NEVER COMMIT this file - it contains real→synthetic mapping

Sanitized data written to: block10_sanitized.json
Stats:
   - Names replaced: 47
   - Emails replaced: 47
   - Date offset: -15 days
```

### Step 3: Verify Sanitization

Before sharing, verify the sanitized file:

```bash
# Check for any remaining PII patterns
./scripts/pii-scan.sh

# Manually review the sanitized file
head -50 block10_sanitized.json
```

**Look for:**
- No real names (should see PGY1-01, FAC-PD, etc.)
- No .mil emails (should see user1@example.mil)
- No SSNs or phone numbers
- Dates should be shifted (relative timing preserved)

### Step 4: Share with Claude Code IDE

Now you can safely:
- Paste sanitized JSON in conversation
- Share sanitized files in your working directory
- Discuss specific assignments using synthetic IDs

**Example conversation:**
```
User: The schedule shows PGY2-03 has a conflict on 2024-01-15.
      Here's the relevant assignment data: [paste sanitized JSON]

Claude: Looking at PGY2-03's assignments, I see they're scheduled for
        both clinic and inpatient on that date...
```

### Step 5: Restore Original Data (If Needed)

If you need to apply changes back to real data:

```bash
# Use the mapping file to reverse sanitization
python scripts/sanitize_pii.py --reverse \
  .sanitize/mapping_20231223_143022.json \
  block10_sanitized.json \
  block10_restored.json
```

---

## Data Classification Reference

### REDACTED (Completely Removed)

| Field | Replacement | Reason |
|-------|-------------|--------|
| deployment_orders | [REDACTED] | OPSEC - movement patterns |
| deployment_location | [REDACTED] | OPSEC - unit locations |
| tdy_location | [REDACTED] | OPSEC - travel patterns |
| emergency_contact | [REDACTED] | PERSEC - family info |
| ssn | [REDACTED] | PII - identity theft |
| dod_id | [REDACTED] | PERSEC - military ID |

### REPLACED (With Synthetic Data)

| Field | Example Original | Example Synthetic |
|-------|------------------|-------------------|
| first_name | John | (removed) |
| last_name | Smith | (removed) |
| full_name | John Smith | PGY2-03 |
| email | john.smith@hospital.mil | user3@example.mil |
| date | 2024-01-15 | 2024-01-00 (offset) |

### PRESERVED (Safe to Share)

| Field | Reason |
|-------|--------|
| block_number | Scheduling structure |
| rotation_type | Activity categories |
| pgy_level | Training level (no individual ID) |
| role | Generic role classification |
| is_active | Status flag |

---

## Important Rules

### DO

- Always sanitize before sharing real data
- Use the sanitization script (don't manually edit)
- Keep mapping files local (never commit)
- Verify sanitization before sharing
- Use synthetic IDs in discussions

### DON'T

- Share raw database exports
- Commit mapping files to git
- Share .sanitize/ directory contents
- Manually type real names in conversations
- Screenshot real data

---

## Mapping File Security

The `.sanitize/` directory contains files that map real names to synthetic IDs.

**These files:**
- Are gitignored (verified in .gitignore)
- Should never be committed
- Should never be shared
- Are needed only for reversal
- Can be deleted after use

**If accidentally committed:**
1. Immediately remove from git history
2. Rotate any exposed credentials
3. Notify security team
4. See `docs/security/INCIDENT_RESPONSE.md`

---

## Integration with CI/CD

The PII scan in CI will catch:
- SSN patterns in code
- Unencrypted .mil emails
- Staged data files

If CI fails with PII warning, verify you haven't accidentally committed:
- Unsanitized data files
- Mapping files from .sanitize/
- Screenshots with real data

---

## Troubleshooting

### "File contains PII patterns" error

```bash
# Run the scanner to identify issues
./scripts/pii-scan.sh

# If false positive, check if it's in test data
grep -n "pattern" file.json
```

### Sanitization didn't replace all names

The script uses context (role, pgy_level) to generate appropriate synthetic IDs. If names aren't being replaced:

```python
# Ensure your data has role context
{
  "name": "John Smith",
  "role": "RESIDENT",  # Required for proper ID generation
  "pgy_level": 2       # Optional but helpful
}
```

### Need to share data that can't be sanitized

For truly sensitive operational data that can't be safely sanitized:
1. Describe the issue abstractly
2. Use hypothetical examples
3. Ask Claude to generate synthetic test data
4. Work with test fixtures instead

---

## Related Documentation

- [Data Security Policy](DATA_SECURITY_POLICY.md)
- [PII Audit Log](PII_AUDIT_LOG.md)
- [OPSEC Guidelines](../operations/OPSEC_GUIDELINES.md)
- [Incident Response](INCIDENT_RESPONSE.md)

---

*This SOP is reviewed quarterly. Last review: 2025-12-23*
