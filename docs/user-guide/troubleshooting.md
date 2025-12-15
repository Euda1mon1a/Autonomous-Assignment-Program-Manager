# Troubleshooting Guide

This guide provides solutions to common issues you may encounter when using the Residency Scheduler.

---

## Table of Contents

1. [Login and Access Issues](#login-and-access-issues)
2. [Navigation Problems](#navigation-problems)
3. [People Management Issues](#people-management-issues)
4. [Template Issues](#template-issues)
5. [Absence Management Issues](#absence-management-issues)
6. [Schedule Generation Problems](#schedule-generation-problems)
7. [Compliance Issues](#compliance-issues)
8. [Export Problems](#export-problems)
9. [Performance Issues](#performance-issues)
10. [Browser-Specific Issues](#browser-specific-issues)

---

## Login and Access Issues

### Cannot Log In

**Symptoms**:
- "Invalid credentials" error
- Login button doesn't respond
- Page refreshes without logging in

**Solutions**:

| Problem | Solution |
|---------|----------|
| Wrong username/password | Verify credentials; check caps lock |
| Account locked | Contact administrator to unlock |
| Session expired | Clear cookies, try again |
| Browser issue | Try different browser |

**Step-by-step fix**:
1. Clear browser cache and cookies
2. Close all browser windows
3. Reopen browser
4. Navigate to login page
5. Enter credentials carefully
6. If still failing, contact administrator

### "Access Denied" After Login

**Symptoms**:
- Login succeeds but certain pages show "Access Denied"
- Features are missing or grayed out

**Solutions**:
- Verify your role has permission for that feature
- Contact administrator to check role assignment
- Role permissions:

| Feature | Faculty | Coordinator | Admin |
|---------|---------|-------------|-------|
| View schedules | Yes | Yes | Yes |
| Edit people | No | Yes | Yes |
| Settings | No | No | Yes |

### Session Timeout

**Symptoms**:
- Suddenly logged out
- "Session expired" message

**Solutions**:
1. Log back in
2. Check if you were inactive for extended period
3. If frequent timeouts, contact IT

---

## Navigation Problems

### Menu Items Missing

**Symptoms**:
- Navigation doesn't show expected items
- Settings link not visible

**Solutions**:
- Menu items depend on your role
- Faculty: Limited menu (Dashboard, Compliance, Help)
- Coordinator: Most items except Settings
- Admin: All items

If items are missing that should be visible:
1. Log out and log back in
2. Clear browser cache
3. Contact administrator to verify role

### Page Not Loading

**Symptoms**:
- Blank page
- Endless loading spinner
- Error message

**Solutions**:
1. Refresh the page (F5 or Ctrl+R)
2. Check internet connection
3. Try different browser
4. Clear cache and cookies
5. Contact IT if persistent

### Buttons Not Responding

**Symptoms**:
- Clicking buttons does nothing
- No visual feedback

**Solutions**:
1. Wait a moment (action may be processing)
2. Check for error messages
3. Refresh the page
4. Disable browser extensions (especially ad blockers)
5. Try different browser

---

## People Management Issues

### Cannot Add Person

**Symptoms**:
- "Save" button disabled
- Error message on save
- Person not appearing after save

**Solutions**:

| Error | Solution |
|-------|----------|
| "Name is required" | Fill in the name field |
| "Type is required" | Select Resident or Faculty |
| "PGY level required" | Select PGY level for residents |
| "Duplicate entry" | Person may already exist; search first |

### Cannot Edit Person

**Symptoms**:
- Edit button not visible
- Changes won't save

**Solutions**:
- Verify you have Coordinator or Admin role
- Check for required fields
- Ensure no validation errors

### Cannot Delete Person

**Symptoms**:
- Delete button disabled
- Error on delete attempt

**Solutions**:
- Person may have active assignments
- Remove or reassign their scheduled slots first
- Then try deleting again

### Person Not Showing in Dropdowns

**Symptoms**:
- When adding absence, person not in list
- Person card exists but not selectable

**Solutions**:
1. Refresh the page
2. Check if filter is applied
3. Verify person was saved successfully
4. Clear browser cache

---

## Template Issues

### Cannot Create Template

**Symptoms**:
- Create button disabled
- Error messages

**Solutions**:

| Error | Solution |
|-------|----------|
| "Name required" | Enter template name |
| "Abbreviation required" | Enter 2-6 character abbreviation |
| "Duplicate abbreviation" | Use different abbreviation |
| "Invalid ratio format" | Use format "1:2" or "1:4" |

### Template Not Used in Schedule

**Symptoms**:
- Template exists but not assigned
- Schedule doesn't include expected rotation

**Solutions**:
1. Verify template is active/enabled
2. Check if template requirements match available people
3. Verify date range includes template's applicable period
4. Check capacity settings

---

## Absence Management Issues

### Cannot Add Absence

**Symptoms**:
- Form won't submit
- Error messages

**Solutions**:

| Error | Solution |
|-------|----------|
| "Person required" | Select a person |
| "Type required" | Select absence type |
| "Invalid dates" | End date must be >= start date |
| "Overlapping absence" | Check for existing absence in same period |

### Absence Not Showing on Calendar

**Symptoms**:
- Added absence but calendar is empty
- Absence in list but not calendar

**Solutions**:
1. Check month navigation - is correct month displayed?
2. Check type filter - is it filtering out the type?
3. Refresh the page
4. Verify save was successful

### Calendar View Not Working

**Symptoms**:
- Calendar is blank
- Dates not clickable

**Solutions**:
1. Try List View as alternative
2. Refresh the page
3. Check JavaScript is enabled
4. Try different browser

---

## Schedule Generation Problems

### Generation Fails Immediately

**Symptoms**:
- Error message appears quickly
- "Cannot generate schedule"

**Solutions**:

| Error | Solution |
|-------|----------|
| "No residents available" | Check people list; add residents |
| "Invalid date range" | End date must be > start date |
| "No templates defined" | Create rotation templates |
| "Database error" | Contact administrator |

### Generation Takes Too Long

**Symptoms**:
- Progress bar stuck
- No response for several minutes

**Solutions**:

| Situation | Solution |
|-----------|----------|
| Large date range + CP-SAT | Try smaller range or different algorithm |
| Many constraints | Try Greedy or Min Conflicts first |
| System overload | Wait; try during off-peak hours |

**Timeout guidelines**:
- Greedy: Should complete in <1 minute
- Min Conflicts: Usually <5 minutes
- CP-SAT: May take 10-30 minutes for complex schedules

### Poor Coverage After Generation

**Symptoms**:
- Low coverage rate (<80%)
- Many unfilled slots

**Solutions**:
1. Check absence records - too many people out?
2. Check template capacity - requirements too high?
3. Check resident count - enough people available?
4. Try different algorithm

### Many Violations After Generation

**Symptoms**:
- Multiple ACGME violations
- Red compliance indicators

**Solutions**:
1. Try CP-SAT algorithm (guarantees compliance if possible)
2. Check if violations are resolvable (enough people?)
3. Review template supervision requirements
4. See [Compliance Issues](#compliance-issues) section

---

## Compliance Issues

### 80-Hour Violation Won't Clear

**Symptoms**:
- Reduced hours but still showing violation
- Violation persists after changes

**Solutions**:
1. Remember it's a **4-week average** - all 4 weeks matter
2. Check each week in the period
3. Calculate manually:
   ```
   (Week1 + Week2 + Week3 + Week4) / 4 must be ≤ 80
   ```
4. Regenerate schedule if manual adjustments not enough

### 1-in-7 Violation Won't Clear

**Symptoms**:
- Added day off but violation persists
- Can't find the violating period

**Solutions**:
1. Find the exact 7-day window
2. Ensure **24 continuous hours** off (not just "lighter day")
3. Verify no on-call or any duties on the off day
4. Check both ends of the 7-day window

### Supervision Violation Persists

**Symptoms**:
- Added faculty but still showing violation
- Ratio seems correct but error remains

**Solutions**:
1. Verify calculation:
   - PGY-1: Need 1 faculty per 2 residents
   - PGY-2/3: Need 1 faculty per 4 residents
2. Check if faculty is actually assigned (not just present)
3. Verify faculty assignment covers the specific time period
4. Mixed PGY levels = use stricter ratio

### Compliance Page Shows Stale Data

**Symptoms**:
- Made changes but compliance not updating
- Old violations still showing

**Solutions**:
1. Refresh the page
2. Navigate away and back
3. Clear browser cache
4. Changes may need schedule regeneration

---

## Export Problems

### Excel Export Not Downloading

**Symptoms**:
- Click export but nothing happens
- Browser seems to block download

**Solutions**:
1. Check browser download settings
2. Disable popup blocker for this site
3. Try different browser
4. Check downloads folder

### Excel File Won't Open

**Symptoms**:
- Download completes but file won't open
- "File corrupted" message

**Solutions**:
1. Re-download the file
2. Try opening with Google Sheets or LibreOffice
3. Check if file size is zero (incomplete download)
4. Clear browser cache and try again

### CSV Has Encoding Issues

**Symptoms**:
- Special characters display wrong
- Columns misaligned

**Solutions**:
1. Open in text editor first to inspect
2. When opening in Excel:
   - Use "Import" instead of "Open"
   - Select UTF-8 encoding
   - Choose comma delimiter

### Colors Not Showing in Export

**Symptoms**:
- Excel file has no colors
- Print preview shows no formatting

**Solutions**:
1. Ensure conditional formatting is enabled in Excel
2. Check if colors were stripped by email
3. Download fresh copy from application
4. Check printer settings for color printing

---

## Performance Issues

### Application is Slow

**Symptoms**:
- Pages take long to load
- Actions are delayed

**Solutions**:

| Cause | Solution |
|-------|----------|
| Network latency | Check internet connection |
| Browser overload | Close other tabs |
| Large dataset | Be patient; optimize searches |
| Server load | Try off-peak hours |

### Browser Crashes or Freezes

**Symptoms**:
- Browser becomes unresponsive
- "Page not responding" message

**Solutions**:
1. Close other browser tabs
2. Clear browser cache
3. Restart browser
4. Check available system memory
5. Try different browser

### Data Not Saving

**Symptoms**:
- Make changes but they disappear
- Have to enter data multiple times

**Solutions**:
1. Check network connection
2. Wait for save confirmation before navigating
3. Look for error messages
4. Refresh and check if data persisted

---

## Browser-Specific Issues

### Chrome Issues

| Issue | Solution |
|-------|----------|
| Export blocked | Allow downloads from this site |
| Page not loading | Disable extensions |
| Memory issues | Clear cache; close tabs |

### Firefox Issues

| Issue | Solution |
|-------|----------|
| Date picker not working | Update Firefox |
| Layout issues | Clear cache |
| SSL warnings | Check site certificate |

### Safari Issues

| Issue | Solution |
|-------|----------|
| Downloads not starting | Check Safari download settings |
| JavaScript errors | Enable JavaScript |
| Session issues | Allow cookies |

### Edge Issues

| Issue | Solution |
|-------|----------|
| Compatibility view | Disable compatibility mode |
| Extension conflicts | Disable extensions |
| Download issues | Check download folder |

### Recommended Browser Settings

For best experience:
- JavaScript: Enabled
- Cookies: Enabled for this site
- Popup blocker: Disabled for this site
- Cache: Clear periodically
- Extensions: Disable ad blockers for this site

---

## Getting Help

### When to Contact Support

Contact your administrator if:
- You've tried all applicable solutions
- The issue persists across browsers
- You see database or server errors
- Account or permission issues

### Information to Provide

When reporting issues, include:
1. What you were trying to do
2. What happened (exact error messages)
3. When it happened
4. Your browser and version
5. Steps to reproduce

### Support Channels

| Issue Type | Contact |
|------------|---------|
| Account/permissions | Program Administrator |
| Technical/system | IT Support |
| Process questions | Program Coordinator |

---

## Error Message Reference

### Common Error Messages

| Message | Meaning | Action |
|---------|---------|--------|
| "Session expired" | You've been logged out | Log in again |
| "Permission denied" | Your role can't do this | Check with admin |
| "Network error" | Connection problem | Check internet |
| "Validation error" | Form data invalid | Check required fields |
| "Server error" | Backend problem | Try later; contact IT |
| "Resource not found" | Data doesn't exist | Refresh; verify item exists |

---

## Related Guides

- [Getting Started](getting-started.md) - Basic usage
- [FAQ](faq.md) - Common questions
- [Common Workflows](common-workflows.md) - Step-by-step procedures

---

*Most issues can be resolved with a page refresh, cache clear, or trying a different browser.*
