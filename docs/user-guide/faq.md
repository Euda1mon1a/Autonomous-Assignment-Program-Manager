# Frequently Asked Questions (FAQ)

This FAQ answers common questions about using the Residency Scheduler application.

---

## Table of Contents

1. [General Questions](#general-questions)
2. [Access and Permissions](#access-and-permissions)
3. [Scheduling Questions](#scheduling-questions)
4. [People Management](#people-management)
5. [Absences and Time Off](#absences-and-time-off)
6. [Compliance Questions](#compliance-questions)
7. [Export and Printing](#export-and-printing)
8. [Technical Questions](#technical-questions)
9. [Military-Specific Questions](#military-specific-questions)

---

## General Questions

### What is the Residency Scheduler?

The Residency Scheduler is a web application designed to manage medical residency program scheduling while ensuring compliance with ACGME (Accreditation Council for Graduate Medical Education) requirements. It automates schedule generation, tracks absences, monitors compliance, and provides reporting tools.

### Who should use this system?

| Role | Use Case |
|------|----------|
| **Program Coordinators** | Primary users for daily scheduling operations |
| **Program Directors/Admins** | System configuration and oversight |
| **Faculty** | View schedules and compliance status |
| **Residents** | View their assignments (if access provided) |

### Is my data secure?

Yes. The system includes:
- Encrypted password storage
- Secure session management
- Role-based access control
- Audit logging

### Can I use this on my phone?

Yes, the application is responsive and works on mobile devices. However, for complex tasks like schedule generation, a tablet or computer is recommended for the best experience.

---

## Access and Permissions

### How do I get an account?

Contact your program administrator. They will create your account and assign the appropriate role.

### Why can't I see the Settings page?

The Settings page is only available to Admin users. Coordinators and Faculty do not have access. If you need settings changed, contact your program administrator.

### How do I reset my password?

Currently, password resets must be done by your program administrator. Contact them to reset your password.

### Can multiple people use the system at the same time?

Yes. The system supports multiple simultaneous users. Changes are saved immediately and visible to all users.

### What's the difference between Coordinator and Admin?

| Feature | Coordinator | Admin |
|---------|-------------|-------|
| View schedules | Yes | Yes |
| Manage people | Yes | Yes |
| Manage templates | Yes | Yes |
| Manage absences | Yes | Yes |
| Generate schedules | Yes | Yes |
| Export data | Yes | Yes |
| **Change settings** | No | Yes |
| **Configure ACGME parameters** | No | Yes |

---

## Scheduling Questions

### Which scheduling algorithm should I use?

| Algorithm | Best For | Speed | Quality |
|-----------|----------|-------|---------|
| **Greedy** | Quick drafts, simple schedules | Fast | Good |
| **Min Conflicts** | Most standard schedules | Moderate | Better |
| **CP-SAT** | Final schedules, complex constraints | Slower | Optimal |

**Recommendation**: Start with Greedy for initial planning, use Min Conflicts for standard work, and use CP-SAT for final schedules where compliance is critical.

### How far in advance can I generate schedules?

You can generate schedules for any date range. However, for best results:
- Generate one block (4 weeks) at a time for CP-SAT
- Monthly generation is common for Min Conflicts
- Greedy can handle longer ranges but may be less optimal

### Why is my schedule showing compliance violations?

Violations appear when the generated schedule breaks ACGME rules:
- **80-hour violation**: Resident scheduled for too many hours
- **1-in-7 violation**: Resident lacks required day off
- **Supervision violation**: Insufficient faculty coverage

See the [Compliance](compliance.md) guide for resolution steps.

### Can I manually adjust the schedule after generation?

Yes. After generation, you can:
- Swap assignments between residents
- Add or remove assignments
- Make one-off changes

After manual changes, always re-check compliance.

### What happens to existing schedules when I regenerate?

Regenerating for a date range will replace existing assignments for those dates. Previous data is overwritten.

### Why did schedule generation fail?

Common causes:
| Reason | Solution |
|--------|----------|
| Not enough residents | Add residents or reduce requirements |
| Too many absences | Check if coverage is possible |
| Invalid templates | Verify template settings |
| Invalid date range | Ensure end date > start date |

---

## People Management

### How do I add a new resident?

1. Go to **People**
2. Click **+ Add Person**
3. Enter name, select "Resident", choose PGY level
4. Click **Save**

See [People Management](people-management.md) for details.

### How do I update PGY levels at the start of the year?

1. Go to **People**
2. Edit each resident
3. Update PGY level (e.g., 1 → 2)
4. Save changes

Do this for all residents before generating the new year's schedules.

### What happens if I delete a person who has scheduled assignments?

Their assignments will be affected. It's best to:
1. Remove or reassign their scheduled slots first
2. Then delete the person record

### How do I add a faculty member?

1. Go to **People**
2. Click **+ Add Person**
3. Enter name, select "Faculty"
4. Add specialties if applicable
5. Click **Save**

---

## Absences and Time Off

### What types of absences can I record?

| Type | Use For |
|------|---------|
| **Vacation** | Annual leave, PTO |
| **Medical** | Sick days, appointments |
| **Deployment** | Military active duty |
| **TDY** | Temporary duty assignments |
| **Conference** | CME, medical meetings |
| **Family Emergency** | Personal emergencies |

### What's the difference between Deployment and TDY?

| Type | Duration | Typical Use |
|------|----------|-------------|
| **Deployment** | Longer (months) | Active duty, overseas assignments |
| **TDY** | Shorter (days-weeks) | Training, temporary work |

### How do absences affect scheduling?

When an absence is recorded:
- The person is marked unavailable for those dates
- Schedule generation will not assign them during the absence
- Existing assignments should be reviewed and reassigned

### Can I add a last-minute absence?

Yes. Add the absence through the Absences page, then:
1. Check Dashboard for coverage impact
2. Regenerate affected dates if needed
3. Or manually reassign duties

---

## Compliance Questions

### What is ACGME?

ACGME (Accreditation Council for Graduate Medical Education) is the organization that accredits residency programs in the United States. They set requirements for work hours, supervision, and educational standards.

### What are the ACGME rules being monitored?

| Rule | Requirement |
|------|-------------|
| **80-Hour Rule** | Max 80 hours/week averaged over 4 weeks |
| **1-in-7 Rule** | One 24-hour period off every 7 days |
| **Supervision Ratios** | PGY-1: 1:2, PGY-2/3: 1:4 |

### How is the 80-hour average calculated?

It's a rolling 4-week average:
```
(Week 1 hours + Week 2 + Week 3 + Week 4) ÷ 4 ≤ 80 hours
```

### What if my program has an exception to ACGME rules?

ACGME rarely grants exceptions. If your program has documented exceptions:
1. Contact your Admin to adjust settings
2. Document the exception for accreditation records

### How often should I check compliance?

- **Daily**: Quick check of compliance cards on Dashboard
- **After any schedule change**: Full compliance review
- **Weekly**: Detailed review of any patterns
- **Monthly**: Comprehensive audit for records

---

## Export and Printing

### How do I export the schedule to Excel?

1. Go to Dashboard
2. Click **Export Excel** in Quick Actions
3. File will download automatically

### Can I print the schedule?

Yes:
1. Export to Excel
2. Open the Excel file
3. Print from Excel (can adjust page setup)

### How do I export the people list?

1. Go to **People**
2. Click **Export** dropdown
3. Choose **CSV** or **JSON**

### What's the difference between CSV and JSON exports?

| Format | Best For |
|--------|----------|
| **CSV** | Opening in Excel, Google Sheets, data analysis |
| **JSON** | System integration, programming, backups |

---

## Technical Questions

### What browsers are supported?

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

### Why is the page loading slowly?

Common causes and solutions:
- **Network issues**: Check internet connection
- **Browser cache**: Clear cache and cookies
- **Too many tabs**: Close unused browser tabs
- **Large operation**: Generation may take time - be patient

### My changes aren't saving. What should I do?

1. Check for error messages
2. Verify network connection
3. Refresh and check if data persisted
4. Try different browser
5. Contact IT if persistent

### I'm getting an error. What should I do?

1. Note the exact error message
2. Try refreshing the page
3. Try different browser
4. If persistent, contact support with:
   - Error message
   - What you were doing
   - Browser and version

---

## Military-Specific Questions

### How do I handle deployment orders?

1. Go to **Absences**
2. Click **+ Add Absence**
3. Select the resident
4. Choose **Type**: Deployment
5. Enter dates
6. Add order number in "Deployment Orders" field
7. Save

See [Common Workflows](common-workflows.md) for detailed procedure.

### How is TDY different from regular absence?

TDY (Temporary Duty) is specifically tracked for military programs:
- Has dedicated "TDY" type
- Includes TDY Location field
- Often shorter than deployments
- Common for training courses

### How do I plan around a resident's deployment?

1. Record the deployment absence as soon as orders received
2. Regenerate schedules for the deployment period
3. Review workload distribution among remaining residents
4. Check compliance regularly during the deployment

### What if deployment dates change?

1. Go to **Absences**
2. Find the deployment record
3. Click **Edit**
4. Update start/end dates
5. Regenerate affected schedules

---

## More Questions?

### In-App Help

Click **Help** in the navigation bar for:
- Quick Reference Card
- Glossary
- This FAQ

### Documentation

This user guide provides comprehensive coverage:
- [Getting Started](getting-started.md)
- [Dashboard](dashboard.md)
- [People Management](people-management.md)
- [Templates](templates.md)
- [Absences](absences.md)
- [Compliance](compliance.md)
- [Schedule Generation](schedule-generation.md)
- [Exporting Data](exporting-data.md)
- [Settings](settings.md)
- [Common Workflows](common-workflows.md)
- [Troubleshooting](troubleshooting.md)

### Still Need Help?

Contact:
- **Program Administrator**: For account and permission issues
- **IT Support**: For technical issues
- **Program Coordinator**: For process questions

---

*Can't find your question? Contact your program administrator.*
