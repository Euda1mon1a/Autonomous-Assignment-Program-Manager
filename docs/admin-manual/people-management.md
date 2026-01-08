# People Management

> Last Updated: 2026-01-07

Bulk management of residents and faculty in the scheduling system.

---

## Access

**Route:** `/admin/people`
**Required Role:** Admin

---

## Features

### Search and Filter

Filter the people list using:
- **Search:** Type to filter by name or email
- **Type:** Filter by `resident` or `faculty`
- **PGY Level:** Filter residents by training year (PGY 1-5)

### Selection

- **Select All:** Checkbox in header selects all visible people
- **Individual:** Click checkbox next to any person
- **Keyboard:** `Escape` clears selection

### Bulk Actions

When people are selected, a toolbar appears at the bottom:

| Action | Description |
|--------|-------------|
| **Set PGY** | Change PGY level for selected residents |
| **Set Type** | Change between resident/faculty |
| **Delete** | Remove selected people (with confirmation) |

---

## Quick Reference

| Task | Steps |
|------|-------|
| Change PGY for multiple residents | 1. Filter by Type: Resident, 2. Select residents, 3. Click "Set PGY" dropdown, 4. Choose level |
| Delete inactive accounts | 1. Search for person, 2. Select checkbox, 3. Click "Delete", 4. Confirm |
| Promote residents to faculty | 1. Select residents, 2. Click "Set Type", 3. Choose "Faculty" |

---

## Data Table Columns

| Column | Description | Sortable |
|--------|-------------|----------|
| Name | Person's display name | Yes |
| Type | `resident` or `faculty` | Yes |
| PGY | Training year (residents only) | Yes |
| Email | Contact email | Yes |

Click column header to sort. Click again to reverse.

---

## Tips

- Bulk delete is **permanent** - there is no undo
- Changing a resident to faculty clears their PGY level
- Use filters to narrow down before bulk operations
- The count of selected items shows in the toolbar
