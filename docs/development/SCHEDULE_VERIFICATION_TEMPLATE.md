# Schedule Generation Verification Template

> **Purpose:** Provide PROOF that schedule generation succeeded - not just claims
> **For:** Local Claude Code (IDE) to fill out after schedule generation
> **Audience:** Human administrator and Claude Web for analysis

---

## Instructions for Local Claude Code

After running schedule generation, you MUST fill out this template with actual command outputs. Do not paraphrase - paste exact results.

---

## Part 1: Database State Proof

### 1.1 Assignment Count

```bash
# Run this command:
docker compose exec db psql -U scheduler -d residency_scheduler -c \
  "SELECT COUNT(*) as total_assignments FROM assignments WHERE date BETWEEN '2026-03-12' AND '2026-04-08';"
```

**Actual Output:**
```
(paste output here)
```

### 1.2 Assignments by Person (First 20)

```bash
# Run this command:
docker compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT
  p.name,
  p.pgy_level,
  rt.abbreviation as rotation,
  rt.activity_type,
  a.date,
  a.time_of_day
FROM assignments a
JOIN people p ON a.person_id = p.id
JOIN rotation_templates rt ON a.rotation_template_id = rt.id
WHERE a.date BETWEEN '2026-03-12' AND '2026-04-08'
ORDER BY p.name, a.date, a.time_of_day
LIMIT 20;
"
```

**Actual Output:**
```
(paste output here)
```

### 1.3 Orphan Check (Causes ??? in UI)

```bash
# Run this command:
docker compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT
  'Missing person' as issue, COUNT(*) as count
FROM assignments a
LEFT JOIN people p ON a.person_id = p.id
WHERE p.id IS NULL AND a.date BETWEEN '2026-03-12' AND '2026-04-08'
UNION ALL
SELECT
  'Missing rotation' as issue, COUNT(*) as count
FROM assignments a
LEFT JOIN rotation_templates rt ON a.rotation_template_id = rt.id
WHERE rt.id IS NULL AND a.date BETWEEN '2026-03-12' AND '2026-04-08';
"
```

**Actual Output:**
```
(paste output here)
```

**Expected:** Both counts should be 0. Non-zero means FK integrity issues causing `???` in UI.

---

## Part 2: API Verification

### 2.1 Schedule Endpoint Response

```bash
# Get auth token first:
TOKEN=$(curl -s -X POST 'http://localhost:8000/api/v1/auth/login/json' \
  -H 'Content-Type: application/json' \
  -d '{"username": "admin", "password": "YOUR_PASSWORD"}' | jq -r '.access_token')

# Then fetch schedule:
curl -s "http://localhost:8000/api/v1/schedule?start_date=2026-03-12&end_date=2026-03-15" \
  -H "Authorization: Bearer $TOKEN" | jq '.assignments | length'
```

**Actual Output:**
```
(paste output here)
```

### 2.2 Validation Endpoint

```bash
curl -s -X POST 'http://localhost:8000/api/v1/schedule/validate' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"start_date": "2026-03-12", "end_date": "2026-04-08"}' | jq '.'
```

**Actual Output:**
```
(paste output here)
```

---

## Part 3: Coverage Summary

### 3.1 Daily Coverage Check

```bash
docker compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT
  a.date,
  a.time_of_day,
  COUNT(DISTINCT a.person_id) as people_assigned,
  COUNT(*) as total_assignments
FROM assignments a
WHERE a.date BETWEEN '2026-03-12' AND '2026-04-08'
GROUP BY a.date, a.time_of_day
ORDER BY a.date, a.time_of_day;
"
```

**Actual Output:**
```
(paste output here)
```

### 3.2 PGY Level Distribution

```bash
docker compose exec db psql -U scheduler -d residency_scheduler -c "
SELECT
  p.pgy_level,
  COUNT(*) as assignment_count
FROM assignments a
JOIN people p ON a.person_id = p.id
WHERE a.date BETWEEN '2026-03-12' AND '2026-04-08'
GROUP BY p.pgy_level
ORDER BY p.pgy_level;
"
```

**Actual Output:**
```
(paste output here)
```

---

## Part 4: ACGME Compliance Proof

### 4.1 Constraint Registration

```bash
docker compose exec backend python3 -c "
from app.scheduling.constraints.manager import ConstraintManager
mgr = ConstraintManager.create_default()
print(f'Total constraints: {len(mgr.constraints)}')
for c in mgr.constraints:
    print(f'  - {c.name} ({c.constraint_type})')
"
```

**Actual Output:**
```
(paste output here)
```

### 4.2 Violation Summary

```bash
# If there's a validation MCP tool or API endpoint:
curl -s "http://localhost:8000/api/v1/acgme/validate?block=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

**Actual Output:**
```
(paste output here)
```

---

## Part 5: Real Names Mapping (OPTIONAL - Local Only)

> **WARNING:** This section contains PII. Never commit to repository.

For the administrator to verify the schedule makes sense:

| Synthetic ID | Real Name | Role | Block 10 Rotation |
|--------------|-----------|------|-------------------|
| PGY1-01 | (fill in) | Resident | (fill in) |
| PGY1-02 | (fill in) | Resident | (fill in) |
| ... | ... | ... | ... |

---

## Part 6: Frontend Verification

### 6.1 Does the schedule display correctly?

- [ ] No `???` in assignment cells
- [ ] Names display correctly
- [ ] Rotation abbreviations show
- [ ] Color coding works
- [ ] Date range is correct (Mar 10 - Apr 6, 2026)

### 6.2 Screenshot (if possible)

Attach or describe what you see at `http://localhost:3000/schedule`

---

## Verification Summary

| Check | Pass/Fail | Notes |
|-------|-----------|-------|
| Assignment count > 0 | | |
| No orphan assignments | | |
| API returns data | | |
| Validation passes | | |
| All 25 constraints registered | | |
| Frontend displays correctly | | |
| No ??? in UI | | |

---

## Signature

**Verified by:** (Claude Code IDE session ID)
**Date:**
**Commit hash:**

---

*This template ensures LOCAL provides PROOF, not just claims.*
