# Schedule Management Guide

This guide covers everything you need to know about viewing, generating, and managing resident rotation schedules in the Residency Scheduler application.

## Table of Contents

- [Viewing the Schedule](#viewing-the-schedule)
- [Understanding the Calendar Layout](#understanding-the-calendar-layout)
- [Navigating Time Periods](#navigating-time-periods)
- [Generating a New Schedule](#generating-a-new-schedule)
- [Editing Assignments](#editing-assignments)
- [Understanding ACGME Compliance Indicators](#understanding-acgme-compliance-indicators)
- [Exporting Schedules](#exporting-schedules)
- [Filtering and Searching](#filtering-and-searching)
- [Best Practices](#best-practices)

## Viewing the Schedule

### Accessing the Schedule

There are two ways to view schedules:

1. **From the Dashboard**
   - Click on the "Schedule Summary" card
   - Or click "View Schedule" in Quick Actions

2. **From the Navigation**
   - Click "Schedule" in the top navigation bar
   - This is the main schedule page

### The Schedule Page

The Schedule page displays a grid view showing:
- **Rows:** People (residents and faculty), grouped by PGY level
- **Columns:** Days of the schedule period
- **Cells:** Individual assignments showing who is assigned where

The default view shows a 4-week block (28 days) starting from the current Monday.

## Understanding the Calendar Layout

### Grid Structure

The schedule uses a person-centric grid layout:

#### Column Headers (Top)
- **Day Name:** Mon, Tue, Wed, etc.
- **Date:** Month and day (e.g., Jan 15)
- **Weekend Shading:** Saturdays and Sundays have gray backgrounds

#### Row Headers (Left)
- **Person Name:** Resident or faculty member
- **Role/Level:** Shows PGY level for residents or "Faculty" for attendings
- **Grouping:** Residents are grouped by PGY level with visual separators

#### Individual Cells
Each cell represents one day for one person and shows:
- **Morning (AM) Assignment:** Top half of the cell
- **Afternoon (PM) Assignment:** Bottom half of the cell
- **Color Coding:** Different rotation types have different colors
- **Abbreviations:** Short codes for quick identification (e.g., "CLIN" for Clinic)

### Color Legend

Rotations are color-coded for quick visual identification:

| Color | Rotation Type | Example |
|-------|---------------|---------|
| Blue | Clinic | Outpatient Clinic |
| Purple | Inpatient | Ward Service, ICU |
| Red | Procedure | Surgery, Procedure Lab |
| Orange | Call | On-call duty |
| Green | Elective | Research, Away rotation |
| Gray | Conference | Didactics, Grand Rounds |

**Finding the legend:** The color legend appears in the top-right area of the Schedule page (visible on larger screens).

### Reading a Cell

Each cell can show:
- **Rotation Abbreviation** - Short code (e.g., "WARD", "CLIN")
- **Color Background** - Indicates rotation type
- **Hover Details** - Hover your mouse over a cell to see full rotation details

**Empty cells** mean no assignment for that half-day.

### PGY Grouping

Residents are automatically grouped by their training level:
- **PGY-1** section at the top
- **PGY-2** section in the middle
- **PGY-3** section below that
- **Faculty** section at the bottom

Visual separator lines appear between groups for easier reading.

### AM/PM Split

The schedule tracks half-day assignments:

- **AM (Morning):** Typically 7:00 AM - 12:00 PM
- **PM (Afternoon):** Typically 12:00 PM - 5:00 PM or later

This allows for:
- Half-day rotations
- Call coverage tracking
- Accurate hour calculations for ACGME compliance
- Flexibility in scheduling

## Navigating Time Periods

### Block Navigation Controls

Located just below the page title, you'll find navigation controls:

#### Previous/Next Block Buttons
- **Previous (←):** Go back one block (4 weeks)
- **Next (→):** Go forward one block

#### Quick Navigation
- **Today:** Jump to the current date
- **This Block:** Return to the current 4-week block

#### Date Range Pickers
- **Start Date Picker:** Select a custom start date
- **End Date Picker:** Select a custom end date
- Useful for viewing specific date ranges or longer periods

### Changing the View Period

**To view a specific date range:**
1. Click the Start Date picker
2. Select your desired start date
3. Click the End Date picker
4. Select your desired end date
5. The schedule will update automatically

**Common periods to view:**
- 4 weeks (28 days) - Standard block
- 1 month - Calendar month view
- 8 weeks - Two blocks
- Custom ranges for special planning needs

### Footer Information

At the bottom of the schedule page, you'll see:
- **Instructions:** "Hover over assignments to see details. Click on a cell to view or edit."
- **Day Count:** Shows how many days are currently displayed
- Helpful reminders about interacting with the schedule

## Generating a New Schedule

The schedule generator uses advanced algorithms to create optimal schedules while respecting constraints and ACGME rules.

### When to Generate a Schedule

Generate a new schedule when:
- Starting a new academic year
- Beginning a new block
- Significant changes to people or absences
- Current schedule has too many compliance violations
- You need to plan ahead for future blocks

### Opening the Generate Dialog

1. Navigate to the Dashboard or Schedule page
2. Click the **"Generate Schedule"** button
3. The Generate Schedule dialog will open

### Schedule Generation Form

#### Required Fields

**Start Date**
- Select the first day of your scheduling period
- Typically the first Monday of a block
- Must be a valid date

**End Date**
- Select the last day of your scheduling period
- Typically 28 days after start (4-week block)
- Must be after the start date

#### Algorithm Selection

Choose the scheduling algorithm to use:

**Greedy (Fast)**
- Fills assignments one at a time using a greedy approach
- Fastest option (seconds)
- Good for initial schedules or quick previews
- May not find the absolute best solution
- **Best for:** Quick generation, initial drafts

**CP-SAT (Optimal)**
- Uses Google OR-Tools constraint programming solver
- Guarantees ACGME compliance if solution exists
- Finds optimal assignments
- Slower (30-60 seconds typically)
- **Best for:** Final schedules, compliance-critical periods

**PuLP (Large Scale)**
- Linear programming approach
- Good for complex problems with many constraints
- Efficient for large residency programs
- Moderate speed
- **Best for:** Programs with many residents

**Hybrid (Best Quality)**
- Combines multiple solving approaches
- Tries multiple methods and picks the best result
- Slowest but highest quality
- **Best for:** When you need the absolute best schedule

**Recommendation:** Start with Greedy for quick feedback, then use CP-SAT or Hybrid for your final schedule.

#### Solver Timeout

Set how long the algorithm should run before stopping:
- **30 seconds (Quick)** - For fast results
- **60 seconds (Standard)** - Default, good balance
- **2 minutes (Extended)** - For complex schedules
- **5 minutes (Maximum)** - When you need the best possible solution

Longer timeouts allow the algorithm more time to optimize, but you'll wait longer.

#### PGY Level Filter

Optionally generate schedules for specific training levels:
- **All PGY Levels (default)** - Generate for everyone
- **PGY-1 Only** - Generate only for interns
- **PGY-2 Only** - Generate only for second-years
- **PGY-3 Only** - Generate only for third-years

Filtering is useful when:
- Different levels have different schedules
- You want to focus on one group at a time
- Testing schedule changes for a specific level

### Starting Schedule Generation

1. Fill in all required fields
2. Choose your algorithm and options
3. Click **"Generate Schedule"**
4. You'll see a "Generating schedule..." message with a loading indicator
5. Wait for the process to complete (time varies by algorithm)

**Don't close the browser** while generation is running!

### Understanding the Results

When generation completes, you'll see a results screen showing:

#### Status Banner

**Success (Green)**
- "Schedule Generated Successfully"
- All positions filled
- All constraints satisfied
- Ready to use

**Partial (Yellow/Amber)**
- "Partial Schedule Generated"
- Some positions couldn't be filled
- Most constraints satisfied
- May need manual adjustments

**Failed (Red)**
- "Schedule Generation Failed"
- Unable to find a valid schedule
- Too many constraints or insufficient resources
- Need to adjust requirements

#### Statistics

**Blocks Assigned**
- Shows X/Y format (e.g., "245/250")
- X = Successfully assigned blocks
- Y = Total blocks needed
- Percentage shown below

**Coverage Rate**
- Percentage of required positions filled
- 100% = Perfect coverage
- Lower percentages indicate gaps

#### Solver Details

For algorithm nerds and troubleshooting:
- Number of residents scheduled
- Solver coverage rate
- Branches explored (for CP-SAT)
- Conflicts resolved (for CP-SAT)

#### Validation Results

**All ACGME requirements met (Green check)**
- No violations detected
- Schedule is compliant
- Safe to use

**X violation(s) found (Yellow/Red warning)**
- List of rule violations
- Shows up to 5 violations
- "And X more..." if there are additional violations
- Review the Compliance page for full details

### After Generation

**If successful:**
1. Click **"Done"** to close the dialog
2. The schedule is now active
3. Review it on the Schedule page
4. Check the Compliance page to verify
5. Export it if needed

**If partial or failed:**
1. Review the error messages
2. Click **"Generate Another"** to try again with different settings
3. Consider:
   - Using a different algorithm
   - Increasing the timeout
   - Checking for conflicting constraints
   - Adding more people or reducing requirements

### Generation Tips

**For Best Results:**
- Ensure all people are added before generating
- Enter all known absences first
- Set up rotation templates with realistic capacity
- Start with a shorter time period for testing
- Use Greedy first to spot obvious issues
- Use CP-SAT or Hybrid for final schedules

**Common Issues:**
- **"No solution found"** - Too many constraints, try relaxing some requirements
- **Low coverage rate** - Not enough residents for all positions
- **Many violations** - Check template settings and supervision ratios
- **Takes too long** - Reduce time period or use a simpler algorithm

## Editing Assignments

Currently, schedule editing is done primarily through regeneration. Future versions may include direct editing.

### Current Workflow

To change assignments:
1. Adjust the underlying data (people, templates, absences)
2. Regenerate the schedule with updated information
3. Review the new schedule
4. Export or use as needed

### What You Can Edit

**Before Generation:**
- People (add, remove, edit)
- Rotation templates (capacity, requirements)
- Absences (add, edit, delete)
- Date ranges
- Algorithm settings

**After Generation:**
- Currently, regenerate with changes
- Future updates may add direct cell editing

## Understanding ACGME Compliance Indicators

The schedule system automatically monitors ACGME (Accreditation Council for Graduate Medical Education) requirements.

### Key ACGME Rules

#### 80-Hour Rule
- Residents cannot work more than 80 hours per week
- Calculated as a 4-week average
- Includes all clinical and educational activities
- **Why it matters:** Patient and resident safety

#### 1-in-7 Day Off Rule
- Residents must have at least one full day (24 hours) off every 7 days
- Averaged over 4 weeks
- No clinical duties during off days
- **Why it matters:** Prevents burnout and fatigue

#### Supervision Ratios
- **PGY-1:** Maximum 2 residents per 1 faculty member
- **PGY-2/3:** Maximum 4 residents per 1 faculty member
- Ensures adequate supervision for patient safety
- **Why it matters:** Training quality and patient care

### Compliance Indicators in the Schedule

**Visual Indicators:**
While viewing the schedule, you may see:
- Color-coded warnings on cells with issues
- Tooltips showing compliance problems
- Summary counts of violations

### Checking Compliance

**On the Compliance Page:**
1. Click "Compliance" in the navigation
2. Select the month to review
3. View summary cards for each rule
4. Review detailed violation list

**Compliance Summary Cards:**
- Green checkmark = Rule satisfied
- Red X = Violations found
- Count of violations shown

**Violation Details:**
Each violation shows:
- Severity level (Critical, High, Medium, Low)
- Rule type (80-hour, 1-in-7, supervision)
- Person affected
- Specific problem description

### Responding to Violations

**If you see violations:**
1. Review the violation details
2. Understand which rule was broken and why
3. Options to fix:
   - Regenerate the schedule with adjusted parameters
   - Add more faculty to improve ratios
   - Adjust resident assignments manually (if available)
   - Reduce clinical hour requirements
   - Add additional off days

**Prevention:**
- Set up templates with ACGME limits built in
- Use the CP-SAT algorithm for guaranteed compliance
- Review compliance before finalizing schedules
- Monitor continuously, not just at generation

## Exporting Schedules

Export schedules to share with residents, print, or integrate with other systems.

### Export Options

#### Excel Export (.xlsx)
- Full schedule in spreadsheet format
- Includes all assignments and dates
- Formatted for easy reading and printing
- Compatible with Microsoft Excel, Google Sheets, etc.

**To export to Excel:**
1. Navigate to the Schedule page
2. Look for the "Export Excel" button (typically near the top)
3. Click the button
4. File will download automatically
5. Open in your spreadsheet application

**Excel file includes:**
- All residents and their assignments
- Date headers
- Color coding (may vary by Excel version)
- PGY groupings

#### CSV Export
- Plain text comma-separated values
- Easy to import into other systems
- Good for data analysis

**To export to CSV:**
1. Look for the "Export" dropdown button
2. Select "Export as CSV"
3. File downloads to your computer

#### JSON Export
- Machine-readable format
- For developers and system integration
- Contains full data structure

**To export to JSON:**
1. Look for the "Export" dropdown button
2. Select "Export as JSON"
3. File downloads to your computer

### Printing the Schedule

**To print the schedule:**
1. Navigate to the Schedule page
2. Use your browser's print function (Ctrl+P or Cmd+P)
3. Adjust print settings as needed
4. Print or save as PDF

**Print Tips:**
- Use landscape orientation for better fit
- Adjust margins to maximize space
- Check "Print background colors" to preserve color coding
- Preview before printing to ensure good layout

### Sharing Schedules

**Best practices for sharing:**

**Via Email:**
- Export to Excel first
- Attach the file to your email
- Include relevant dates in the email subject
- CC relevant parties

**Posted Schedule:**
- Print the schedule
- Post in a common area
- Update regularly
- Include generation date

**Online Sharing:**
- Use your organization's file sharing system
- Upload the exported file
- Set appropriate permissions
- Keep previous versions for reference

## Filtering and Searching

### People Filtering

While viewing schedules, you may want to focus on specific people:

**By PGY Level:**
- Schedule page groups by PGY automatically
- Scroll to the relevant section
- PGY-1 at top, then PGY-2, PGY-3, Faculty

**By Name:**
- Use your browser's Find function (Ctrl+F or Cmd+F)
- Type the person's name
- Browser will highlight matches

### Date Filtering

Use the date range controls to focus on specific periods:

**View specific weeks:**
1. Use Previous/Next buttons to navigate by block
2. Or use date pickers for custom ranges

**Find a specific date:**
1. Use "Today" button to jump to current date
2. Or pick a date using the date picker
3. Schedule will adjust to show that date

### Rotation Type Filtering

To see all assignments of a specific type:
- Look for the color associated with that rotation type
- Scan the schedule visually for that color
- Or export to Excel and use spreadsheet filtering

## Best Practices

### Schedule Planning

**Do's:**
- Plan schedules at least one block in advance
- Enter all absences before generating
- Review compliance before finalizing
- Communicate schedule changes promptly
- Keep backup copies of schedules

**Don'ts:**
- Don't wait until the last minute to generate
- Don't ignore compliance violations
- Don't forget to account for holidays
- Don't over-constrain the algorithm
- Don't forget to notify affected parties of changes

### Regular Schedule Maintenance

**Weekly:**
- Review upcoming absences
- Check for any new scheduling conflicts
- Monitor compliance status
- Address urgent changes

**Monthly:**
- Generate next month's schedule
- Review and validate
- Export and distribute
- Archive previous month's schedule

**Quarterly:**
- Audit ACGME compliance trends
- Review resident rotation balance
- Update templates as needed
- Plan for academic year transitions

### Communication

**When publishing a schedule:**
1. Generate and validate the schedule
2. Review for obvious errors
3. Check compliance
4. Export to Excel
5. Share with stakeholders
6. Allow time for feedback
7. Make adjustments if needed
8. Finalize and post

**Schedule change notifications:**
- Notify affected people immediately
- Explain the reason for changes
- Provide updated schedule
- Allow questions and feedback

### Quality Checks

Before finalizing a schedule, verify:

- [ ] All required positions are filled
- [ ] No ACGME violations (or acceptable ones documented)
- [ ] All known absences are accommodated
- [ ] Supervision ratios are maintained
- [ ] Fair distribution of rotations
- [ ] Holidays are handled appropriately
- [ ] Call coverage is adequate
- [ ] Stakeholders have reviewed and approved

## Troubleshooting Common Issues

### "Schedule won't generate"

**Possible causes:**
- Too many constraints
- Insufficient residents for requirements
- Conflicting template rules
- Date range issues

**Solutions:**
- Try Greedy algorithm first to identify issues
- Check template capacity settings
- Verify all residents are active
- Reduce time period for testing

### "Low coverage rate"

**Possible causes:**
- Not enough residents
- Too many absences
- Template capacity too high
- Algorithm timeout too short

**Solutions:**
- Add more residents or reduce requirements
- Check if absences overlap too much
- Review template settings
- Increase solver timeout

### "Many compliance violations"

**Possible causes:**
- Template hour estimates too high
- Not enough off days
- Poor faculty-to-resident ratio
- Algorithm choice

**Solutions:**
- Use CP-SAT algorithm for compliance
- Review and adjust template hour settings
- Add more faculty coverage
- Reduce resident work requirements

### "Schedule looks wrong"

**Possible causes:**
- Old data being displayed
- Wrong date range selected
- Cached data

**Solutions:**
- Refresh the page (F5)
- Check the date range
- Clear browser cache
- Regenerate if needed

## Advanced Tips

### Multi-Block Planning

For planning multiple blocks at once:
1. Extend the end date to cover multiple blocks
2. Use CP-SAT or Hybrid algorithm
3. Increase timeout to 5 minutes
4. Review each block section individually

### Balancing Rotations

Ensure fair distribution:
- Track individual rotation history
- Manually review rotation counts
- Export and analyze in spreadsheet
- Adjust templates to promote balance

### Handling Special Situations

**Holidays:**
- Mark holidays in the system
- Reduce staffing requirements for those days
- Plan coverage in advance

**Transition periods:**
- Plan PGY level changes in July
- Update resident profiles before generating
- Consider orientation needs

**Vacations:**
- Enter all known vacations early
- Review absence calendar monthly
- Limit concurrent absences where possible

## Next Steps

Now that you understand schedule management:

- **Practice:** Try generating a test schedule
- **Explore:** Navigate through different time periods
- **Check Compliance:** Review the Compliance page
- **Learn About Absences:** Read the [Absences Guide](./absences.md)

---

[← Back: Getting Started](./getting-started.md) | [User Guide Home](./README.md) | [Next: Absences Guide →](./absences.md)
