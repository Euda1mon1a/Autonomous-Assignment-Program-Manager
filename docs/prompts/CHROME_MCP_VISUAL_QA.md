# Chrome MCP Visual QA Scripts — Excel Pipeline

> **Purpose:** Ready-to-paste prompts for Claude-in-Chrome MCP tools to perform visual QA and generate documentation for the Excel import/export pipeline.
> **Usage:** Copy a script block into any Claude session with Chrome MCP tools active.
> **Created:** 2026-02-25

---

## Script 1: Round-Trip Demo GIF

Records a GIF walkthrough of the full export → import → preview flow for coordinator training documentation.

### Prompt

```
Using your Chrome MCP tools, perform the following steps and record a GIF of the entire process:

1. Call tabs_context_mcp to see current tabs
2. Create a new tab with tabs_create_mcp to http://localhost:3000/login
3. Start gif_creator with filename "excel_round_trip_demo.gif"
4. Use form_input to log in:
   - Email: coordinator@test.mil
   - Password: TestPassword123!
5. Wait for redirect to dashboard
6. Navigate to http://localhost:3000/hub/import-export
7. Use read_page to capture the current state of the import/export hub
8. Click the "Export" tab using find + computer tools
9. Select the xlsx format option
10. Click the export button and wait 3 seconds for download
11. Use read_page to verify the download indicator appeared
12. Navigate to http://localhost:3000/import/half-day
13. Use read_page to capture the upload form
14. Use javascript_tool to verify the form fields render:
    document.querySelector('[data-testid="hd-file-input"]') !== null
    && document.querySelector('[data-testid="hd-block-number"]') !== null
    && document.querySelector('[data-testid="hd-stage-btn"]') !== null
15. Stop gif_creator

Report: the GIF file path, any console errors from read_console_messages, and whether all UI elements rendered correctly.
```

---

## Script 2: Import Wizard Visual Walkthrough

Visually verifies the half-day import wizard renders all three steps correctly.

### Prompt

```
Using your Chrome MCP tools:

1. Navigate to http://localhost:3000/login
2. Use form_input to log in as admin@test.mil / TestPassword123!
3. Navigate to http://localhost:3000/import/half-day
4. Use read_page to capture the upload step
5. Verify these elements exist using javascript_tool:
   - File input: document.querySelector('[data-testid="hd-file-input"]')
   - Block number: document.querySelector('[data-testid="hd-block-number"]')
   - Academic year: document.querySelector('[data-testid="hd-academic-year"]')
   - Stage button: document.querySelector('[data-testid="hd-stage-btn"]')
   - Step indicators showing "1. Upload", "2. Preview", "3. Draft"

6. Verify the step indicator "1. Upload" has the active styling (blue)
7. Use get_page_text to capture the full page text
8. Use read_console_messages with pattern "error|warn" to check for React errors

Report which elements are present, which are missing, and any console errors.
```

---

## Script 3: Batch Review Page Verification

Verifies the batch review page renders stats, diff viewer, and action buttons.

### Prompt

```
Using your Chrome MCP tools:

1. Navigate to http://localhost:3000/login and log in as admin@test.mil
2. Navigate to http://localhost:3000/import
3. Use read_page to see the import history table
4. Check if any batches exist using javascript_tool:
   document.querySelector('[data-testid="import-history-table"]')?.querySelectorAll('tbody tr').length
5. If batches exist, click the first "Review" button
6. On the batch review page, verify these elements:
   - Status badge: [data-testid="batch-status-badge"]
   - New assignments stat: [data-testid="batch-stat-new"]
   - Updates stat: [data-testid="batch-stat-updates"]
   - Conflicts stat: [data-testid="batch-stat-conflicts"]
   - Violations stat: [data-testid="batch-stat-violations"]
   - Apply button (if staged): [data-testid="batch-apply-btn"]
7. Use read_page to capture the full page state

Report the batch status, stat values, and whether the apply button is visible.
```

---

## Script 4: Native Excel Formatting Check

Opens an exported xlsx in the native macOS Excel app to verify conditional formatting renders correctly.

### Prompt

```
Using your Chrome MCP tools:

1. Navigate to http://localhost:3000/hub/import-export
2. Log in if needed (admin@test.mil / TestPassword123!)
3. Navigate to the Export tab
4. Trigger an xlsx export and wait for the download
5. Use the computer tool to:
   a. Open Finder and navigate to ~/Downloads
   b. Double-click the most recent .xlsx file to open in Excel
   c. Wait 5 seconds for Excel to load
   d. Take a screenshot of the Excel window
6. Save the screenshot as "mac_excel_formatting_check.png"
7. Use read_page on the Chrome tab to verify the export completed

Report: whether the file opened successfully in Excel, and describe the visual formatting you see in the screenshot (colored cells, header rows, etc.).

NOTE: This script requires Microsoft Excel to be installed on macOS. If Excel is not available, use Numbers instead.
```

---

## Notes

- All scripts assume the dev server is running at `http://localhost:3000`
- All scripts assume the backend API is running at `http://localhost:8000`
- Test credentials: `admin@test.mil` / `coordinator@test.mil` with password `TestPassword123!`
- GIF recordings are saved to the current working directory
- Console error checking uses `read_console_messages` with pattern filtering to avoid noise
- The `data-testid` attributes referenced here match those added in Phase 0 of the E2E testing roadmap
