# Exporting Data

The Residency Scheduler provides multiple export options for schedules, people data, and absences. This guide covers all export formats and their use cases.

---

## Export Formats Overview

| Format | Best For | Available From |
|--------|----------|----------------|
| **Excel (.xlsx)** | Distribution, printing | Dashboard |
| **CSV** | Spreadsheet analysis | People, Absences |
| **JSON** | Data integration | People, Absences |

---

## Excel Export (Schedule)

The primary export format for schedule distribution.

### Accessing Excel Export

1. Go to **Dashboard**
2. Click **Export Excel** in Quick Actions

### What's Included

The Excel export contains:

```
+----------------------------------------------------------------+
|                    RESIDENCY SCHEDULE                           |
|                    January 2024 - Block 3                       |
+----------------------------------------------------------------+
|           | Mon 1/1 | Mon 1/1 | Tue 1/2 | Tue 1/2 | Wed 1/3 ... |
| Resident  |   AM    |   PM    |   AM    |   PM    |   AM    ... |
+----------------------------------------------------------------+
| PGY-1     |         |         |         |         |         ... |
+----------------------------------------------------------------+
| Dr. Smith |  CLN    |  INP    |  INP    |  INP    |  INP    ... |
| Dr. Jones |  INP    |  INP    |  CLN    |  CLN    |  OFF    ... |
| Dr. Brown |  OFF    |  OFF    |  ENDO   |  ENDO   |  CLN    ... |
+----------------------------------------------------------------+
| PGY-2     |         |         |         |         |         ... |
+----------------------------------------------------------------+
| Dr. Davis |  CALL   |  CALL   |  OFF    |  OFF    |  CLN    ... |
| Dr. White |  CLN    |  CLN    |  INP    |  INP    |  INP    ... |
+----------------------------------------------------------------+
```

### Excel Features

| Feature | Description |
|---------|-------------|
| **Color Coding** | Rotations colored by activity type |
| **PGY Grouping** | Residents organized by year |
| **Holiday Highlighting** | Federal holidays marked |
| **AM/PM Columns** | Morning and afternoon sessions |
| **Abbreviations** | Template abbreviations used |

### Color Legend in Export

| Color | Activity Type |
|-------|---------------|
| Blue | Clinic |
| Purple | Inpatient |
| Red | Procedure |
| Gray | Conference |
| Green | Elective |
| Orange | Call |
| Yellow | Holiday |

### Export Date Range

The Excel export includes the current 4-week block by default.

---

## CSV Export

Comma-separated values format for spreadsheet analysis.

### Accessing CSV Export

#### From People Page
1. Go to **People**
2. Click **Export** dropdown
3. Select **Export as CSV**

#### From Absences Page
1. Go to **Absences**
2. Switch to **List View**
3. Click **Export** dropdown
4. Select **Export as CSV**

### People CSV Format

```csv
id,name,type,pgy_level,email,specialties
1,Dr. Jane Smith,resident,1,jsmith@hospital.org,
2,Dr. Robert Johnson,faculty,,rjohnson@hospital.org,"Gastroenterology,Hepatology"
3,Dr. Michael Brown,resident,2,mbrown@hospital.org,
```

### Absences CSV Format

```csv
id,person_id,person_name,type,start_date,end_date,notes
1,1,Dr. Jane Smith,vacation,2024-02-15,2024-02-22,Annual leave
2,3,Dr. Michael Brown,deployment,2024-03-01,2024-06-30,Kuwait deployment
```

### CSV Use Cases

- Import into Excel/Google Sheets
- Data analysis
- Backup records
- Integration with other systems
- Reporting to GME office

---

## JSON Export

JavaScript Object Notation format for programmatic access.

### Accessing JSON Export

#### From People Page
1. Go to **People**
2. Click **Export** dropdown
3. Select **Export as JSON**

#### From Absences Page
1. Go to **Absences**
2. Click **Export** dropdown
3. Select **Export as JSON**

### People JSON Format

```json
{
  "people": [
    {
      "id": "uuid-1",
      "name": "Dr. Jane Smith",
      "type": "resident",
      "pgy_level": 1,
      "email": "jsmith@hospital.org",
      "specialties": []
    },
    {
      "id": "uuid-2",
      "name": "Dr. Robert Johnson",
      "type": "faculty",
      "pgy_level": null,
      "email": "rjohnson@hospital.org",
      "specialties": ["Gastroenterology", "Hepatology"]
    }
  ],
  "exported_at": "2024-01-15T10:30:00Z",
  "total_count": 2
}
```

### Absences JSON Format

```json
{
  "absences": [
    {
      "id": "uuid-1",
      "person_id": "uuid-person-1",
      "person_name": "Dr. Jane Smith",
      "type": "vacation",
      "start_date": "2024-02-15",
      "end_date": "2024-02-22",
      "notes": "Annual leave",
      "is_blocking": true
    }
  ],
  "exported_at": "2024-01-15T10:30:00Z",
  "total_count": 1
}
```

### JSON Use Cases

- System integrations
- API-based workflows
- Backup and restore
- Custom reporting tools
- Data migration

---

## Export Step-by-Step Guides

### Exporting Schedule for Distribution

**Scenario**: Monthly schedule ready to share with residents

1. Generate the schedule (if not done)
2. Review on Dashboard
3. Check Compliance (resolve any violations)
4. Go to Dashboard
5. Click **Export Excel**
6. Save the file
7. Open to verify
8. Email or print for distribution

### Exporting People for GME Report

**Scenario**: Need resident roster for GME office

1. Go to **People**
2. Apply filters if needed (e.g., Residents only)
3. Click **Export** > **Export as CSV**
4. Open in Excel
5. Format as needed
6. Submit to GME

### Backing Up Absence Data

**Scenario**: End of year backup

1. Go to **Absences**
2. Switch to **List View**
3. Click **Export** > **Export as JSON**
4. Save with date in filename (e.g., `absences_2024_backup.json`)
5. Store securely

---

## Export Tips and Best Practices

### File Naming

Use descriptive names with dates:
- `schedule_jan2024_block3.xlsx`
- `residents_roster_20240115.csv`
- `absences_fy2024_backup.json`

### Storage

- Keep exports in organized folders
- Maintain date-based archives
- Follow your organization's retention policies

### Distribution

| Audience | Recommended Format |
|----------|-------------------|
| Residents | Excel (schedule) |
| GME Office | CSV or Excel |
| IT/Integration | JSON |
| Printing | Excel |

### Regular Exports

Create a schedule for regular exports:
- **Weekly**: Current schedule Excel
- **Monthly**: People and absences CSV
- **Quarterly**: Full JSON backup
- **Annually**: Complete archive

---

## Troubleshooting Exports

| Issue | Solution |
|-------|----------|
| Export button not working | Try different browser; check popup blocker |
| Excel file won't open | Ensure Excel installed; try LibreOffice |
| CSV encoding issues | Open in text editor first; check UTF-8 |
| JSON not valid | Use JSON validator; re-export |
| Colors not showing | Enable Excel formatting; check printer settings |
| Wrong date range | Verify current block selection |

### Browser Download Settings

If exports aren't downloading:
1. Check browser download settings
2. Allow downloads from the application domain
3. Check download folder location
4. Disable popup blockers temporarily

### Large File Exports

For large data sets:
- Export may take longer
- Wait for download to complete
- Don't navigate away during export

---

## Data Security Considerations

### Sensitive Information

Exports may contain:
- Names and contact information
- Medical leave details
- Deployment information

### Best Practices

1. **Secure storage**: Store exports in protected locations
2. **Limited sharing**: Share only with authorized personnel
3. **Delete old exports**: Remove outdated files
4. **Encryption**: Use encrypted storage/transfer for sensitive data
5. **Access control**: Limit who can export data

### HIPAA Considerations

While the scheduler primarily contains schedule data:
- Medical absence notes may be PHI-adjacent
- Follow your organization's HIPAA policies
- Consult compliance if uncertain

---

## Related Guides

- [Dashboard](dashboard.md) - Quick Actions and Excel export
- [People Management](people-management.md) - People data export
- [Absences](absences.md) - Absence data export
- [Getting Started](getting-started.md) - Navigation basics

---

*Regular exports ensure data accessibility and backup protection.*
