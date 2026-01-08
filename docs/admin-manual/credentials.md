# Procedure Credentials

> Last Updated: 2026-01-07

Manage faculty procedure credentialing with a visual matrix view.

---

## Access

**Route:** `/admin/credentials`
**Required Role:** Admin

---

## Overview

The credentials page displays a **Faculty x Procedure** matrix showing who is credentialed for which procedures. Each cell shows the credential status at a glance.

---

## Matrix View

### Status Icons

| Icon | Color | Meaning |
|------|-------|---------|
| Checkmark | Green | Active credential |
| Clock | Blue | Pending approval |
| X | Gray | Suspended |
| X | Red | Expired |
| Warning | Amber | Expiring soon (within 30 days) |
| `-` | Gray | No credential |

### Filtering

- **Specialty:** Filter procedures by medical specialty
- **Show Expiring Only:** Toggle to show only faculty with expiring credentials

---

## Managing Credentials

### Grant New Credential

1. Click an empty cell (`-`) in the matrix
2. Modal opens with "Grant Credential" form
3. Set:
   - **Status:** Active, Pending, Suspended, or Expired
   - **Competency Level:** Trainee, Qualified, Expert, or Master
   - **Expiration Date:** Optional expiration
   - **Notes:** Optional notes
4. Click "Grant"

### Edit Existing Credential

1. Click a cell with an existing credential icon
2. Modal opens with current values
3. Modify fields as needed
4. Click "Save"

### Revoke Credential

1. Click a cell with an existing credential
2. Click "Revoke" button (red)
3. Confirm the action

---

## Expiring Credentials Alert

When credentials are expiring within 30 days, an alert banner appears at the top:

| Severity | Days Until Expiry |
|----------|-------------------|
| Critical (Red) | 7 days or less |
| Warning (Amber) | 8-14 days |
| Info (Blue) | 15-30 days |

The banner shows counts by severity and lists individual credentials.

---

## Competency Levels

| Level | Description |
|-------|-------------|
| **Trainee** | Learning the procedure under supervision |
| **Qualified** | Can perform independently |
| **Expert** | Advanced proficiency, can train others |
| **Master** | Highest level, recognized authority |

---

## Quick Reference

| Task | Steps |
|------|-------|
| Grant credential | Click empty cell > Fill form > Grant |
| Update expiration | Click credential > Change date > Save |
| Revoke credential | Click credential > Revoke > Confirm |
| Find expiring credentials | Toggle "Show expiring only" |
| Filter by specialty | Select from Specialty dropdown |

---

## Tips

- Credentials without expiration dates never expire
- Use the "Show expiring only" filter before quarterly reviews
- Revoking a credential is permanent - consider setting status to "Suspended" instead
- The matrix scrolls horizontally if there are many procedures
