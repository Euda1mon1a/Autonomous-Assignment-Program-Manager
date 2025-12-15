***REMOVED*** Getting Started Tutorial

This tutorial will guide you through your first steps with the Residency Scheduler application.

---

***REMOVED******REMOVED*** Prerequisites

Before you begin, ensure you have:
- A valid user account (contact your program administrator if needed)
- A modern web browser (Chrome, Firefox, Safari, or Edge)
- Network access to the application URL

---

***REMOVED******REMOVED*** Step 1: Accessing the Application

***REMOVED******REMOVED******REMOVED*** Opening the Application

1. Open your web browser
2. Navigate to your organization's Residency Scheduler URL
3. You'll see the login screen

```
Example URLs:
- Production: https://scheduler.yourorganization.com
- Development: http://localhost:3000
```

---

***REMOVED******REMOVED*** Step 2: Logging In

***REMOVED******REMOVED******REMOVED*** Login Process

1. **Enter your username** in the first field
2. **Enter your password** in the second field
3. Click the **Sign In** button

```
+----------------------------------+
|        Residency Scheduler       |
+----------------------------------+
|                                  |
|  Username: [________________]    |
|                                  |
|  Password: [________________]    |
|                                  |
|        [    Sign In    ]         |
|                                  |
+----------------------------------+
```

***REMOVED******REMOVED******REMOVED*** First Login

If this is your first login:
- Use the temporary password provided by your administrator
- You may be prompted to change your password
- Choose a strong password with at least 8 characters

***REMOVED******REMOVED******REMOVED*** Login Issues

| Problem | Solution |
|---------|----------|
| Invalid credentials | Double-check username and password |
| Account locked | Contact your program administrator |
| Forgot password | Contact your program administrator |

---

***REMOVED******REMOVED*** Step 3: Understanding the Dashboard

After logging in, you'll see the Dashboard - your home screen.

***REMOVED******REMOVED******REMOVED*** Dashboard Layout

```
+------------------------------------------------------------------+
|  [Logo] Residency Scheduler                    [User] [Help] [?] |
+------------------------------------------------------------------+
|  Dashboard | People | Templates | Absences | Compliance | Settings|
+------------------------------------------------------------------+
|                                                                   |
|  +------------------+    +------------------+                     |
|  | Schedule Summary |    | Compliance Alert |                    |
|  | - Current block  |    | - Status: OK     |                    |
|  | - 45 assignments |    | - 0 violations   |                    |
|  +------------------+    +------------------+                     |
|                                                                   |
|  +------------------+    +------------------------------------+   |
|  | Upcoming Absences|    | Quick Actions                      |  |
|  | - Dr. Smith (Vac)|    | [Generate] [Export] [Add] [View]  |  |
|  | - Dr. Jones (TDY)|    +------------------------------------+   |
|  +------------------+                                             |
|                                                                   |
+------------------------------------------------------------------+
```

***REMOVED******REMOVED******REMOVED*** Dashboard Widgets

| Widget | Purpose |
|--------|---------|
| **Schedule Summary** | Shows current scheduling block overview |
| **Compliance Alert** | Quick status of ACGME compliance |
| **Upcoming Absences** | Lists near-term scheduled time off |
| **Quick Actions** | Buttons for common tasks |

---

***REMOVED******REMOVED*** Step 4: Navigation Basics

***REMOVED******REMOVED******REMOVED*** Main Navigation Bar

The navigation bar at the top provides access to all sections:

| Menu Item | Description | Access |
|-----------|-------------|--------|
| **Dashboard** | Home screen with overview | All users |
| **People** | Resident and faculty management | Coordinator, Admin |
| **Templates** | Rotation definitions | Coordinator, Admin |
| **Absences** | Time off tracking | Coordinator, Admin |
| **Compliance** | ACGME monitoring | All users |
| **Help** | Documentation and FAQ | All users |
| **Settings** | System configuration | Admin only |

***REMOVED******REMOVED******REMOVED*** Navigation Tips

- Click the **logo** or **Dashboard** to return home from any page
- Use **breadcrumbs** (when available) to navigate back
- The current page is **highlighted** in the navigation bar

---

***REMOVED******REMOVED*** Step 5: Your First Tasks

***REMOVED******REMOVED******REMOVED*** For Coordinators and Admins

***REMOVED******REMOVED******REMOVED******REMOVED*** Task 1: Add Your First Resident

1. Click **People** in the navigation
2. Click **Add Person** button
3. Fill in the form:
   - Name: "Jane Smith"
   - Type: "Resident"
   - PGY Level: "1"
   - Email: "jsmith@example.com"
4. Click **Save**

***REMOVED******REMOVED******REMOVED******REMOVED*** Task 2: Create a Rotation Template

1. Click **Templates** in the navigation
2. Click **New Template** button
3. Fill in:
   - Name: "Inpatient Ward"
   - Activity Type: "Inpatient"
   - Abbreviation: "INP"
   - Max Residents: 3
4. Click **Create**

***REMOVED******REMOVED******REMOVED******REMOVED*** Task 3: Record an Absence

1. Click **Absences** in the navigation
2. Click **Add Absence** button
3. Select:
   - Person: "Jane Smith"
   - Type: "Vacation"
   - Start Date: [pick a date]
   - End Date: [pick end date]
4. Click **Save**

***REMOVED******REMOVED******REMOVED*** For Faculty (View-Only)

***REMOVED******REMOVED******REMOVED******REMOVED*** Viewing Your Schedule

1. Click **Dashboard** to see the schedule overview
2. Review assignments and coverage status

***REMOVED******REMOVED******REMOVED******REMOVED*** Checking Compliance

1. Click **Compliance** in the navigation
2. Review the three compliance cards
3. Use the month navigation to check different periods

---

***REMOVED******REMOVED*** Step 6: Quick Actions Explained

The Dashboard provides four quick action buttons:

***REMOVED******REMOVED******REMOVED*** Generate Schedule
Opens a dialog to create a new schedule:
- Select date range
- Choose algorithm
- Click Generate

***REMOVED******REMOVED******REMOVED*** Export Excel
Downloads the current schedule as an Excel file:
- Color-coded by rotation type
- Organized by PGY level
- Ready for printing/distribution

***REMOVED******REMOVED******REMOVED*** Add Person
Navigates to People page with the add form open:
- Quick way to add residents or faculty

***REMOVED******REMOVED******REMOVED*** View Templates
Navigates to Templates page:
- Review and manage rotation definitions

---

***REMOVED******REMOVED*** Step 7: Understanding Your Role

***REMOVED******REMOVED******REMOVED*** What Can You Do?

| Action | Faculty | Coordinator | Admin |
|--------|---------|-------------|-------|
| View schedules | Yes | Yes | Yes |
| View compliance | Yes | Yes | Yes |
| Add/edit people | No | Yes | Yes |
| Add/edit templates | No | Yes | Yes |
| Add/edit absences | No | Yes | Yes |
| Generate schedules | No | Yes | Yes |
| Export data | Yes | Yes | Yes |
| Change settings | No | No | Yes |

---

***REMOVED******REMOVED*** Step 8: Getting Help

***REMOVED******REMOVED******REMOVED*** In-App Help Resources

1. **Help Page**: Click "Help" in navigation for:
   - Quick Reference Card
   - Glossary of Terms
   - FAQ

2. **Tooltips**: Hover over icons for explanations

3. **This Documentation**: Comprehensive guides for all features

***REMOVED******REMOVED******REMOVED*** External Support

- **Program Administrator**: For account issues, permissions, process questions
- **IT Support**: For technical issues, browser problems, access issues

---

***REMOVED******REMOVED*** What's Next?

Now that you're familiar with the basics, explore these guides:

1. **[Dashboard Overview](dashboard.md)** - Learn all dashboard features
2. **[People Management](people-management.md)** - Master resident/faculty management
3. **[Common Workflows](common-workflows.md)** - Step-by-step task guides
4. **[Troubleshooting](troubleshooting.md)** - Solve common issues

---

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Esc` | Close modal dialogs |
| `Enter` | Submit forms |
| `Tab` | Navigate between fields |

***REMOVED******REMOVED******REMOVED*** Browser Recommendations

| Browser | Minimum Version |
|---------|-----------------|
| Chrome | 90+ |
| Firefox | 88+ |
| Safari | 14+ |
| Edge | 90+ |

---

*Welcome to Residency Scheduler! We're here to make your scheduling easier.*
