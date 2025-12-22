# Conflict Resolution

The conflict resolution system helps identify and resolve scheduling issues before they impact operations.

---

## Overview

Navigate to **Conflicts** from the main navigation to access the Conflict Dashboard. This view shows all detected scheduling conflicts with tools to resolve them.

---

## Conflict Types

| Type | Description | Severity |
|------|-------------|----------|
| **Scheduling Overlap** | Same person assigned to multiple locations | Critical |
| **ACGME Violation** | Work hour or duty limits exceeded | Critical |
| **Supervision Missing** | No faculty assigned for required supervision | High |
| **Capacity Exceeded** | Too many people in one location | Medium |
| **Absence Conflict** | Person scheduled during approved absence | High |
| **Qualification Mismatch** | Assignment requires credentials person lacks | Medium |
| **Coverage Gap** | Location has insufficient staffing | High |

---

## Viewing Conflicts

### Conflict Dashboard

The dashboard provides an at-a-glance view of all conflicts:

1. **Summary Cards** - Total counts by severity
2. **Filter Bar** - Filter by type, severity, date range, or person
3. **Conflict List** - Detailed view of each conflict

### Conflict Details

Click any conflict to see:

- **Affected Parties** - People involved
- **Date/Time** - When the conflict occurs
- **Impact** - What the conflict affects
- **Suggested Resolutions** - AI-powered suggestions

---

## Resolving Conflicts

### AI-Powered Suggestions

The system analyzes each conflict and suggests resolutions:

1. Open a conflict
2. Click **View Suggestions**
3. Review the proposed changes
4. Click **Apply** to implement

Each suggestion shows:
- What changes will be made
- Impact on other schedules
- ACGME compliance status

### Manual Override

For complex situations, use manual override:

1. Click **Manual Override** on a conflict
2. Select the action to take
3. Provide justification (required)
4. Click **Apply Override**

!!! warning "Manual Overrides"
    Manual overrides bypass automatic validation. Ensure you understand
    the compliance implications before proceeding.

---

## Batch Resolution

Resolve multiple conflicts at once:

1. Select conflicts using checkboxes
2. Click **Batch Resolve**
3. Choose a resolution strategy:
   - **Auto-resolve All** - Apply AI suggestions
   - **Ignore All** - Mark as acknowledged
   - **Custom** - Apply same action to all
4. Confirm the action

---

## Conflict History

View past conflicts and resolutions:

1. Click **History** tab
2. Filter by date range or status
3. See what was resolved and how

### Patterns View

Identify recurring conflict patterns:

- Which locations have frequent conflicts
- Common time periods for issues
- People with repeated conflicts

---

## Conflict Statuses

| Status | Description |
|--------|-------------|
| **Active** | Unresolved, needs attention |
| **In Progress** | Being worked on |
| **Resolved** | Fixed, conflict eliminated |
| **Ignored** | Acknowledged but not changed |
| **Escalated** | Sent to supervisor |

---

## Best Practices

!!! tip "Daily Review"
    Check the conflict dashboard each morning before the day begins.

!!! tip "Address Critical First"
    Prioritize critical and high-severity conflicts that affect patient care.

!!! tip "Document Overrides"
    Always provide clear justification when using manual overrides.

!!! tip "Monitor Patterns"
    Use the patterns view weekly to identify systemic issues.

---

## Related Documentation

- **[Compliance Monitoring](compliance.md)** - ACGME rule enforcement
- **[Schedule Management](schedule.md)** - Editing schedules
- **[Absences](absences.md)** - Managing time off
