# Quick Start Guide

Get your first schedule generated in minutes!

---

## Step 1: Create Admin Account

After installation, create your first administrator account:

=== "Web Interface"

    1. Navigate to http://localhost:3000
    2. Click **Register**
    3. Fill in your details
    4. Select **Admin** role

=== "API"

    ```bash
    curl -X POST http://localhost:8000/api/auth/register \
      -H "Content-Type: application/json" \
      -d '{
        "email": "admin@example.com",
        "password": "secure_password",
        "full_name": "Admin User",
        "role": "admin"
      }'
    ```

---

## Step 2: Configure Academic Year

1. Log in as admin
2. Navigate to **Settings** → **Academic Year**
3. Set the start and end dates for your academic year
4. Configure block settings (typically 730 blocks per year)

!!! tip "Block Configuration"
    Each day has 2 blocks: AM and PM. A typical academic year runs July 1 to June 30, resulting in 730 blocks.

---

## Step 3: Add People

Add residents and faculty members to the system.

### Manual Entry

1. Go to **People** → **Add Person**
2. Enter details:
    - **Name**: Full name
    - **Email**: Contact email
    - **Role**: Resident or Faculty
    - **PGY Level**: For residents (PGY-1, PGY-2, PGY-3)
    - **Specialty**: Primary specialty
3. Click **Save**

### Bulk Import

1. Go to **Settings** → **Import Data**
2. Download the Excel template
3. Fill in your data following the template format
4. Upload the completed file

---

## Step 4: Create Rotation Templates

Define your rotation types:

1. Go to **Templates** → **Create Template**
2. Configure:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Template identifier | "ICU", "Clinic", "Call" |
| **Type** | Rotation category | Clinical, Administrative |
| **Duration** | Length in blocks | 1-14 |
| **Capacity** | Max simultaneous residents | 2-5 |
| **Supervision Ratio** | Faculty-to-resident ratio | 1:2, 1:4 |

3. Save the template

---

## Step 5: Generate Your First Schedule

1. Go to **Schedule** → **Generate**
2. Select:
    - **Date Range**: Start and end dates
    - **Algorithm**: Greedy (fast) or CP-SAT (optimal)
    - **Priority Weights**: Adjust optimization priorities
3. Click **Generate Schedule**
4. Review the generated schedule
5. Check for compliance violations
6. Click **Publish** to make active

!!! success "Congratulations!"
    You've generated your first ACGME-compliant schedule!

---

## What's Next?

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-book-open: User Guide
Learn about all features in the [User Guide](../user-guide/index.md).
</div>

<div class="feature-card" markdown>
### :material-shield-check: Compliance
Understand [ACGME Compliance](../user-guide/compliance.md) monitoring.
</div>

<div class="feature-card" markdown>
### :material-swap-horizontal: Swaps
Set up the [Swap Marketplace](../user-guide/swaps.md) for residents.
</div>

</div>
