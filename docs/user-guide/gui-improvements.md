# GUI Improvements

User interface enhancements for residents, program leaders, and administrators.

---

## Overview

These high-impact GUI improvements enhance usability across all user roles:

| Component | Target Users | Benefit |
|-----------|-------------|---------|
| **Scheduled Hours Calculator** | Residents, Program Leaders | Proactive ACGME compliance |
| **Schedule Legend** | All Users | Quick rotation type reference |
| **Quick Swap Button** | Residents | One-click swap requests |
| **Upcoming Assignments** | Residents | 7-day look-ahead |
| **Coverage Impact Analysis** | Coordinators | Absence impact visibility |
| **Configuration Presets** | Admins | Save/load scheduling configs |
| **Breadcrumbs** | All Users | Context-aware navigation |
| **Copy/Share Buttons** | All Users | Easy schedule sharing |
| **Keyboard Shortcuts** | Power Users | Efficient navigation |
| **Progress Indicators** | All Users | Long operation feedback |

---

## Scheduled Hours Calculator

The **Scheduled Hours Calculator** provides transparency into projected work hours based on schedule assignments.

### Purpose

!!! warning "ACGME Compliance Protection"
    This tool helps identify potential ACGME violations **BEFORE** they occur, enabling proactive schedule adjustment and protecting the program from compliance investigations.

### Scheduled vs. Actual Hours

| Metric | Source | Purpose |
|--------|--------|---------|
| **Scheduled Hours** | This calculator | Projections from assignments for planning |
| **Actual Duty Hours** | MyEvaluations | Logged hours for compliance reporting |

!!! tip "Key Distinction"
    The Scheduled Hours Calculator shows what the **schedule projects**, not what residents actually work. Actual duty hours are logged separately in MyEvaluations for official ACGME reporting.

### What It Shows

1. **This Week (Scheduled)**: Projected hours for current week
2. **4-Week Projection**: Rolling average for ACGME 80-hour rule
3. **Week-over-Week Trend**: Workload direction indicator
4. **Scheduled Days Off**: ACGME 1-in-7 day off tracking
5. **Compliance Status**: On Track / Review Needed / Action Required

### Status Indicators

| Status | Color | Meaning | Action |
|--------|-------|---------|--------|
| **On Track** | Green | Under 90% of limit | No action needed |
| **Review Needed** | Amber | 90-100% of limit | Consider adjustments |
| **Action Required** | Red | At or over limit | Immediate review with PD |

### How Hours Are Calculated

The calculator estimates scheduled hours by rotation type:

| Rotation Type | Estimated Hours |
|---------------|-----------------|
| Call | 12 hours |
| Inpatient | 5 hours |
| Clinic | 4 hours |
| Procedure | 4 hours |
| Conference | 2 hours |
| Elective | 4 hours |
| Other | 4 hours (default) |

### Where to Find It

The Scheduled Hours Calculator appears on:
- **My Schedule** page (resident view)
- **Dashboard** summary (when enabled)
- **Admin Scheduling Lab** (preview mode)

---

## Schedule Legend

Color-coded legend for rotation types displayed on schedule cells.

### Usage

The legend maps colors to rotation categories:
- **Blue**: Inpatient rotations
- **Green**: Clinic/Outpatient
- **Purple**: Procedures
- **Orange**: Call/Overnight
- **Gray**: Administrative/Conference

### Display Modes

- **Compact**: Icon-only horizontal bar
- **Expanded**: Full labels with color swatches
- **Vertical**: Sidebar orientation for narrow spaces

---

## Quick Swap Button

One-click swap request directly from schedule cells.

### How to Use

1. Hover over any assignment in your schedule
2. Click the swap icon (appears on hover)
3. Select swap type:
    - **One-to-One**: Trade with another resident
    - **Absorb**: Give away shift (someone picks up)
4. Add optional note
5. Submit request

### Requirements

- Only your own assignments can be swapped
- Assignment must be in the future
- ACGME compliance is validated before submission

---

## Upcoming Assignments Preview

7-day look-ahead widget for residents.

### Features

- Shows next 7 days of assignments
- Color-coded by rotation type
- Quick view of workload distribution
- "Today" indicator for orientation

---

## Coverage Impact Analysis

Enhanced absence display with coverage impact.

### Impact Levels

| Level | Color | Meaning |
|-------|-------|---------|
| **Critical** | Red | Multiple concurrent absences affecting same slot |
| **High** | Orange | Key position uncovered |
| **Medium** | Yellow | Coverage available but stretched |
| **Low** | Blue | Easily covered |

### Alert Banner

When critical or high impact absences exist, a banner displays:
- Number of affected dates
- Link to coverage planning
- Quick action buttons

---

## Configuration Presets (Admin)

Save and load scheduling configurations for the Admin Scheduling Lab.

### Built-in Presets

- **Default**: Balanced across all constraints
- **ACGME Strict**: Maximum compliance focus
- **Coverage Priority**: Fill slots first, then optimize
- **Preference-Heavy**: Weight resident preferences

### Custom Presets

1. Configure scheduling parameters
2. Click **Save Preset**
3. Name your configuration
4. Preset is stored locally in browser

### Import/Export

- Export presets to JSON for sharing
- Import presets from colleagues
- Presets survive browser refresh

---

## Breadcrumbs

Context-aware navigation showing your current location.

### Auto-Generated

Breadcrumbs automatically generate from the URL path:
- Dashboard > Schedule > My Schedule
- Dashboard > Admin > Scheduling Lab > Results

### Home Link

Click the home icon to return to the dashboard from anywhere.

---

## Copy/Share Buttons

Easy schedule sharing functionality.

### Options

| Button | Action |
|--------|--------|
| **Copy Link** | Copy current page URL |
| **Share** | Native share (mobile) or copy |

### Usage

- Share specific dates with colleagues
- Save links to frequently accessed views
- Mobile: Uses native share sheet

---

## Keyboard Shortcuts

Expanded keyboard shortcuts for power users.

### Navigation

| Shortcut | Action |
|----------|--------|
| `G` then `D` | Go to Dashboard |
| `G` then `S` | Go to Schedule |
| `G` then `P` | Go to People |
| `G` then `A` | Go to Admin |
| `T` | Go to Today |

### Actions

| Shortcut | Action |
|----------|--------|
| `N` | New (context-sensitive) |
| `E` | Edit selected item |
| `?` | Show help / shortcuts |
| `Esc` | Close modal / cancel |
| `/` | Focus search |

### Finding Shortcuts

Press `?` anywhere to open the keyboard shortcut reference.

---

## Progress Indicators

Visual feedback for long-running operations.

### Variants

- **Inline**: Compact progress in button
- **Card**: Detailed progress with steps
- **Fullscreen**: Modal overlay for major operations

### Features

- Percentage progress bar
- Elapsed time tracking
- Estimated time remaining
- Step-by-step breakdown
- Success/error states

### Used In

- Schedule generation
- Bulk imports
- Report generation
- Data exports

---

## Best Practices

!!! tip "For Residents"
    - Check the **Scheduled Hours Calculator** weekly
    - Use the **7-day preview** for planning
    - Submit swap requests early with **Quick Swap**

!!! tip "For Program Leaders"
    - Monitor **Coverage Impact** for upcoming absences
    - Review **Scheduled Hours** projections for compliance
    - Address amber/red status indicators proactively

!!! tip "For Administrators"
    - Save successful configurations as **Presets**
    - Share presets with coordinators
    - Use **Keyboard Shortcuts** for efficiency
