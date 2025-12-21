***REMOVED*** Data Security Policy

**OPSEC/PERSEC Compliance for Schedule Data**

---

***REMOVED******REMOVED*** Overview

This repository is **public** and must not contain:
- Real resident/faculty names or identifiers
- Actual schedule assignments
- Absence/leave records with PII
- Any data that could identify military medical personnel

---

***REMOVED******REMOVED*** What's Protected

| Data Type | Why | Where It Lives |
|-----------|-----|----------------|
| **Resident Names** | PERSEC - identifies military personnel | Local only / Airtable |
| **Faculty Names** | PERSEC - identifies military personnel | Local only / Airtable |
| **Schedule Assignments** | OPSEC - reveals duty patterns | Local only / Airtable |
| **Absence Records** | OPSEC/PERSEC - reveals movements | Local only / Airtable |
| **TDY/Deployment Data** | OPSEC - reveals military movements | Local only / Airtable |

---

***REMOVED******REMOVED*** Gitignored Files

The following are excluded from version control:

```gitignore
***REMOVED*** Schedule data exports
docs/data/airtable_absences_*.json
docs/data/*_export.json

***REMOVED*** Environment files with credentials
.env
.env.local
*.env

***REMOVED*** Any data dumps
*.dump
*.sql
data/*.json
```

---

***REMOVED******REMOVED*** Using Test/Demo Data

For development and testing, use **sanitized data**:

***REMOVED******REMOVED******REMOVED*** Option 1: Synthetic Names
```python
***REMOVED*** Use obviously fake names
residents = ["Resident A", "Resident B", "Resident C"]
faculty = ["Dr. Smith", "Dr. Jones", "Dr. Williams"]
```

***REMOVED******REMOVED******REMOVED*** Option 2: Role-Based Identifiers
```python
***REMOVED*** Use role identifiers instead of names
residents = ["PGY1-01", "PGY1-02", "PGY2-01"]
faculty = ["FAC-PD", "FAC-APD", "FAC-OIC"]
```

***REMOVED******REMOVED******REMOVED*** Option 3: Faker Library
```python
from faker import Faker
fake = Faker()
resident_name = fake.name()  ***REMOVED*** Generates random name
```

---

***REMOVED******REMOVED*** Local Data Handling

Real data should only exist:
1. **Airtable** (primary source of truth)
2. **Local development database** (Docker volume)
3. **Local JSON exports** (gitignored)

Never:
- Commit real schedule data
- Share exports via Slack/email without encryption
- Store in cloud drives without encryption

---

***REMOVED******REMOVED*** If Data Is Accidentally Committed

1. **Immediately** remove from git history:
   ```bash
   git rm --cached <file>
   git commit -m "security: Remove sensitive data"
   git push --force-with-lease
   ```

2. **Notify**: Inform project leads of potential exposure

3. **Rotate credentials**: If API keys or passwords were exposed

4. **Document**: Record the incident and remediation

---

***REMOVED******REMOVED*** Reference

- **OPSEC**: Operations Security - protecting military operations
- **PERSEC**: Personal Security - protecting individual identities
- **PII**: Personally Identifiable Information
- **TDY**: Temporary Duty (military travel assignment)
- **C4**: Combat Casualty Care Course
- **HPSP**: Health Professions Scholarship Program
- **USU**: Uniformed Services University
