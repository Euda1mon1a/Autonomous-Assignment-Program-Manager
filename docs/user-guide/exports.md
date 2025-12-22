# Exporting Data

Export schedules and data from Residency Scheduler.

---

## Import/Export Page

For a unified import/export experience:

1. Navigate to **Import/Export** in the main navigation
2. Click the **Export** tab
3. Select the data type to export
4. Choose format (CSV, Excel, JSON)
5. Configure options and download

---

## Excel Export

Export schedules to Excel:

1. Go to **Schedule**
2. Click **Export** → **Excel**
3. Select:
    - Date range
    - Data to include
    - Formatting options
4. Click **Download**

---

## Calendar Export (ICS)

Download your schedule as an ICS file for one-time import:

1. Go to **My Schedule** (or any person's profile)
2. Click **Calendar Sync** button
3. Select **ICS File Download**
4. Choose how many weeks ahead to include (4-52 weeks)
5. Click **Sync Now**
6. Import the downloaded `.ics` file into your calendar app

---

## WebCal Subscription (Live Updates)

Subscribe to a live-updating calendar feed:

1. Go to **My Schedule**
2. Click **Calendar Sync** button
3. Copy the `webcal://` URL provided

### Setup Instructions

=== "Google Calendar"
    1. Open Google Calendar on desktop
    2. Click "+" next to "Other calendars"
    3. Select "From URL"
    4. Paste the `webcal://` URL
    5. Click "Add calendar"

=== "Apple Calendar"
    1. Open Calendar app
    2. File → New Calendar Subscription
    3. Paste the URL
    4. Click "Subscribe"

=== "Outlook"
    1. Open Outlook Calendar
    2. Click "Add calendar" → "From Internet"
    3. Paste the URL
    4. Click "OK"

### Subscription Features

- Automatically refreshes every 15 minutes
- Shows assignments 6 months ahead
- Includes location, role, and notes
- Secure token-based authentication
- Can be revoked at any time

---

## PDF Reports

Generate printable reports:

1. Navigate to desired view
2. Click **Export** → **PDF**
3. Configure report options
4. Click **Generate**

---

## Data Export Formats

| Format | Use Case |
|--------|----------|
| **Excel (.xlsx)** | Data analysis, external systems |
| **ICS** | Calendar import (one-time) |
| **WebCal** | Live calendar sync |
| **PDF** | Printing, documentation |
| **CSV** | Raw data export |
