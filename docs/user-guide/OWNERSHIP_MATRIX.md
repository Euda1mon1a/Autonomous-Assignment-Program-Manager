# File Ownership Matrix - User Guide Documentation

This matrix defines ownership and responsibilities for all files in the `docs/user-guide/` directory.

---

## Overview

| Total Files | Territory | Owner | Last Updated |
|-------------|-----------|-------|--------------|
| 13 | docs/user-guide/* | User Guide Team | December 2024 |

---

## File Ownership Matrix

| File | Purpose | Primary Owner | Secondary Owner | Status |
|------|---------|---------------|-----------------|--------|
| `README.md` | Index and overview | Documentation Lead | Program Coordinator | Active |
| `getting-started.md` | First steps tutorial | Documentation Lead | Training Specialist | Active |
| `dashboard.md` | Dashboard feature walkthrough | Documentation Lead | UX Designer | Active |
| `people-management.md` | People management guide | Documentation Lead | HR Coordinator | Active |
| `templates.md` | Rotation templates guide | Documentation Lead | Scheduling Manager | Active |
| `absences.md` | Absence management guide | Documentation Lead | HR Coordinator | Active |
| `compliance.md` | ACGME compliance guide | Documentation Lead | Compliance Officer | Active |
| `schedule-generation.md` | Schedule generation guide | Documentation Lead | Scheduling Manager | Active |
| `exporting-data.md` | Export functionality guide | Documentation Lead | IT Support | Active |
| `settings.md` | Admin settings guide | Documentation Lead | System Administrator | Active |
| `common-workflows.md` | Step-by-step workflows | Documentation Lead | Program Coordinator | Active |
| `troubleshooting.md` | Problem resolution guide | Documentation Lead | IT Support | Active |
| `faq.md` | Frequently asked questions | Documentation Lead | Support Team | Active |
| `glossary.md` | Term definitions | Documentation Lead | Medical Education | Active |
| `OWNERSHIP_MATRIX.md` | This file | Documentation Lead | Project Manager | Active |

---

## Responsibility Definitions

### Primary Owner
- Responsible for creating and maintaining content
- Reviews and approves changes
- Ensures accuracy and completeness
- Updates documentation when features change

### Secondary Owner
- Provides subject matter expertise
- Reviews content for accuracy
- Suggests updates based on user feedback
- Assists with specialized content

---

## Update Schedule

| Review Type | Frequency | Responsible Party |
|-------------|-----------|-------------------|
| Content accuracy | Quarterly | Primary Owner |
| Feature updates | As needed | Development Team → Primary Owner |
| User feedback integration | Monthly | Support Team → Primary Owner |
| Full documentation audit | Annually | Documentation Lead |

---

## Change Control Process

### Minor Updates (typos, clarifications)
1. Primary Owner can make directly
2. No review required
3. Update "Last Updated" date

### Major Updates (new features, restructuring)
1. Create draft changes
2. Secondary Owner reviews for accuracy
3. Primary Owner approves
4. Update version and date

### New Files
1. Documentation Lead creates or assigns
2. Define ownership in this matrix
3. Primary and Secondary Owners review
4. Add to README.md index

---

## File Descriptions

### Core Navigation Files

| File | Description |
|------|-------------|
| `README.md` | Main index with links to all guides, quick start summary |
| `getting-started.md` | Tutorial for new users, login through first tasks |

### Feature Walkthroughs

| File | Description |
|------|-------------|
| `dashboard.md` | Dashboard widgets, quick actions, data interpretation |
| `people-management.md` | Adding, editing, deleting residents and faculty |
| `templates.md` | Creating and managing rotation templates |
| `absences.md` | Recording and managing time off |
| `compliance.md` | Understanding and resolving ACGME violations |
| `schedule-generation.md` | Algorithm selection and schedule creation |
| `exporting-data.md` | Excel, CSV, and JSON export options |
| `settings.md` | System configuration (Admin only) |

### Reference Documents

| File | Description |
|------|-------------|
| `common-workflows.md` | Step-by-step procedures for common tasks |
| `troubleshooting.md` | Solutions to common problems |
| `faq.md` | Answers to frequently asked questions |
| `glossary.md` | Definitions of key terms |

---

## Cross-Reference Dependencies

Files that reference each other and should be updated together:

### Navigation Links
- `README.md` links to all other files
- All files link back to related guides

### Workflow Dependencies
```
getting-started.md
    ├── dashboard.md
    ├── people-management.md
    └── common-workflows.md

compliance.md
    ├── schedule-generation.md
    ├── settings.md
    └── common-workflows.md

troubleshooting.md
    ├── All feature files (for specific issues)
    └── faq.md (for question format)
```

### Term Definitions
- `glossary.md` should be updated when new terms are introduced in any file

---

## Quality Standards

### Content Requirements
- [ ] Clear, concise language
- [ ] Step-by-step instructions with numbered lists
- [ ] ASCII diagrams for visual representation
- [ ] Tables for quick reference
- [ ] Links to related guides
- [ ] Consistent formatting

### Technical Requirements
- [ ] Valid Markdown syntax
- [ ] Working internal links
- [ ] Proper heading hierarchy (H1 → H2 → H3)
- [ ] Code blocks for commands/examples
- [ ] No broken references

---

## Metrics and Tracking

### Documentation Health Indicators

| Metric | Target | Current |
|--------|--------|---------|
| Files with defined owners | 100% | 100% |
| Last update < 6 months | 100% | 100% |
| Cross-linked properly | 100% | 100% |
| Follows style guide | 100% | 100% |

---

## Contact Information

| Role | Contact Method |
|------|----------------|
| Documentation Lead | Project documentation channel |
| Technical Questions | Development team |
| Content Suggestions | Documentation repository issues |

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Dec 2024 | Documentation Team | Initial creation |

---

*This matrix ensures clear ownership and accountability for user guide documentation.*
