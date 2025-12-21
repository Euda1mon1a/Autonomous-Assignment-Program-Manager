# User Guide

Welcome to the Residency Scheduler User Guide. This comprehensive guide explains how to use all features of the application.

---

## Overview

Residency Scheduler is designed to help medical residency programs manage complex scheduling needs while maintaining full ACGME compliance.

### Who Should Read This Guide?

- **Program Coordinators** - Primary users managing schedules
- **Faculty Members** - Supervising residents and managing preferences
- **Residents** - Viewing schedules, requesting swaps, managing absences
- **Administrators** - System configuration and user management

---

## Guide Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-view-dashboard: [Dashboard](dashboard.md)
Overview of the main dashboard and navigation.
</div>

<div class="feature-card" markdown>
### :material-calendar: [Schedule Management](schedule.md)
Viewing, generating, and editing schedules.
</div>

<div class="feature-card" markdown>
### :material-account-group: [People Management](people.md)
Managing residents, faculty, and certifications.
</div>

<div class="feature-card" markdown>
### :material-calendar-remove: [Absences](absences.md)
Recording and managing time off.
</div>

<div class="feature-card" markdown>
### :material-swap-horizontal: [Swap Marketplace](swaps.md)
Requesting and managing shift swaps.
</div>

<div class="feature-card" markdown>
### :material-shield-check: [Compliance](compliance.md)
ACGME compliance monitoring and violations.
</div>

<div class="feature-card" markdown>
### :material-download: [Exporting Data](exports.md)
Export to Excel, PDF, and calendar formats.
</div>

<div class="feature-card" markdown>
### :material-gamepad-variant: [Game Theory Analysis](game-theory.md)
Test configurations using Axelrod's tournament framework.
</div>

</div>

---

## Quick Reference

### ACGME Rules Monitored

| Rule | Description | Threshold |
|------|-------------|-----------|
| **80-Hour Rule** | Weekly work hours | ≤80 hours/week avg |
| **1-in-7 Rule** | Day off frequency | 1 day off per 7 days |
| **24-Hour Limit** | Continuous duty | ≤24 hours continuous |
| **Supervision** | Faculty ratios | PGY-1: 1:2, PGY-2/3: 1:4 |

### Violation Severity Levels

| Level | Color | Response Required |
|-------|-------|------------------|
| **Critical** | :material-circle:{ style="color: #E57373" } Red | Immediate action |
| **High** | :material-circle:{ style="color: #FF8A65" } Orange | Same-day resolution |
| **Medium** | :material-circle:{ style="color: #FFD54F" } Yellow | Weekly review |
| **Low** | :material-circle:{ style="color: #4FC3F7" } Blue | Informational |

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| ++question++ | Show help |
| ++g++ ++d++ | Go to Dashboard |
| ++g++ ++s++ | Go to Schedule |
| ++g++ ++p++ | Go to People |
| ++n++ | New (context-sensitive) |
| ++e++ | Edit (when item selected) |
| ++escape++ | Close modal/cancel |

---

## Tips for Success

!!! tip "For Coordinators"
    - **Plan ahead**: Generate schedules 2-4 weeks in advance
    - **Review daily**: Check the daily manifest each morning
    - **Monitor compliance**: Review violations weekly
    - **Process swaps promptly**: Quick turnaround improves satisfaction

!!! tip "For Residents"
    - **Check your schedule daily**: Stay aware of upcoming assignments
    - **Request swaps early**: Earlier requests have more options
    - **Report absences promptly**: Helps coverage planning
    - **Use calendar sync**: Always have your schedule available

!!! tip "For Faculty"
    - **Review supervision assignments**: Ensure you're prepared
    - **Update availability**: Keep your schedule current
    - **Approve swaps timely**: Check pending requests regularly

---

## Need Help?

- **In-app help**: Click the :material-help-circle: icon in any section
- **Documentation**: Browse the sections above
- **Support**: Contact your system administrator
- **Issues**: [Report bugs](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues) via GitHub

---

## Related Documentation

- **[User Workflows Guide](../guides/user-workflows.md)** - Comprehensive workflow examples
- **[Scheduling Workflow](../guides/scheduling-workflow.md)** - Detailed scheduling guide
- **[Swap Management](../guides/swap-management.md)** - Complete swap system guide
- **[Resilience Framework](../guides/resilience-framework.md)** - Understanding system resilience
- **[Getting Started](../getting-started/index.md)** - Installation and setup
- **[Admin Manual](../admin-manual/index.md)** - System administration
- **[API Reference](../api/index.md)** - API integration
- **[Troubleshooting](../troubleshooting.md)** - Common issues
- **[Documentation Index](../README.md)** - Complete documentation map
