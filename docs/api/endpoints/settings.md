***REMOVED*** Settings Endpoints

Base path: `/api/settings`

Manages system-wide configuration settings for scheduling behavior, ACGME compliance parameters, and other application preferences.

***REMOVED******REMOVED*** Endpoints Overview

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Get current settings | No |
| POST | `/` | Replace all settings | No |
| PATCH | `/` | Partial update settings | No |
| DELETE | `/` | Reset to defaults | No |

---

***REMOVED******REMOVED*** GET /api/settings

Returns the current system settings.

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl http://localhost:8000/api/settings
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "scheduling_algorithm": "greedy",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

---

***REMOVED******REMOVED*** POST /api/settings

Replaces all settings with the provided values. Any missing fields will use default values.

***REMOVED******REMOVED******REMOVED*** Request Body

```json
{
  "scheduling_algorithm": "cp_sat",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

| Field | Type | Constraints | Default |
|-------|------|-------------|---------|
| `scheduling_algorithm` | string | `greedy`, `cp_sat`, `pulp` | `greedy` |
| `work_hours_per_week` | integer | 40-100 | 80 |
| `max_consecutive_days` | integer | 1-7 | 6 |
| `min_days_off_per_week` | integer | 1-3 | 1 |
| `pgy1_supervision_ratio` | string | Format: "1:N" | `1:2` |
| `pgy2_supervision_ratio` | string | Format: "1:N" | `1:4` |
| `pgy3_supervision_ratio` | string | Format: "1:N" | `1:4` |
| `enable_weekend_scheduling` | boolean | - | `true` |
| `enable_holiday_scheduling` | boolean | - | `false` |
| `default_block_duration_hours` | integer | 1-12 | 4 |

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "scheduling_algorithm": "cp_sat",
    "work_hours_per_week": 80,
    "max_consecutive_days": 6,
    "min_days_off_per_week": 1,
    "pgy1_supervision_ratio": "1:2",
    "pgy2_supervision_ratio": "1:4",
    "pgy3_supervision_ratio": "1:4",
    "enable_weekend_scheduling": true,
    "enable_holiday_scheduling": false,
    "default_block_duration_hours": 4
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

```json
{
  "scheduling_algorithm": "cp_sat",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": false,
  "default_block_duration_hours": 4
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 422 | Validation error (invalid values) |

---

***REMOVED******REMOVED*** PATCH /api/settings

Partially updates settings. Only provided fields are changed; others remain unchanged.

***REMOVED******REMOVED******REMOVED*** Request Body

Only include fields you want to change:

```json
{
  "scheduling_algorithm": "hybrid",
  "enable_holiday_scheduling": true
}
```

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "scheduling_algorithm": "hybrid",
    "enable_holiday_scheduling": true
  }'
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `200 OK`

Returns the complete settings object with updated values:

```json
{
  "scheduling_algorithm": "hybrid",
  "work_hours_per_week": 80,
  "max_consecutive_days": 6,
  "min_days_off_per_week": 1,
  "pgy1_supervision_ratio": "1:2",
  "pgy2_supervision_ratio": "1:4",
  "pgy3_supervision_ratio": "1:4",
  "enable_weekend_scheduling": true,
  "enable_holiday_scheduling": true,
  "default_block_duration_hours": 4
}
```

***REMOVED******REMOVED******REMOVED*** Errors

| Status | Description |
|--------|-------------|
| 422 | Validation error |

---

***REMOVED******REMOVED*** DELETE /api/settings

Resets all settings to their default values.

***REMOVED******REMOVED******REMOVED*** Example Request

```bash
curl -X DELETE http://localhost:8000/api/settings
```

***REMOVED******REMOVED******REMOVED*** Response

**Status:** `204 No Content`

---

***REMOVED******REMOVED*** Settings Reference

***REMOVED******REMOVED******REMOVED*** Scheduling Algorithm

Controls the algorithm used for automatic schedule generation.

| Value | Description |
|-------|-------------|
| `greedy` | Fast heuristic assignment (default) |
| `cp_sat` | Google OR-Tools constraint programming |
| `pulp` | PuLP linear programming |

```bash
***REMOVED*** Set to optimal algorithm
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"scheduling_algorithm": "cp_sat"}'
```

***REMOVED******REMOVED******REMOVED*** Work Hours Settings

ACGME work hour limits and duty restrictions.

| Setting | Description | ACGME Requirement |
|---------|-------------|-------------------|
| `work_hours_per_week` | Maximum weekly hours | 80 hours averaged over 4 weeks |
| `max_consecutive_days` | Maximum consecutive duty days | Varies by program |
| `min_days_off_per_week` | Minimum days off per week | 1 day off in 7 |

```bash
***REMOVED*** Configure ACGME-compliant settings
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "work_hours_per_week": 80,
    "max_consecutive_days": 6,
    "min_days_off_per_week": 1
  }'
```

***REMOVED******REMOVED******REMOVED*** Supervision Ratios

Faculty-to-resident supervision ratios by PGY level.

| Setting | Format | ACGME Guideline |
|---------|--------|-----------------|
| `pgy1_supervision_ratio` | "1:N" | Maximum 1:2 for PGY-1 |
| `pgy2_supervision_ratio` | "1:N" | Typically 1:4 for PGY-2 |
| `pgy3_supervision_ratio` | "1:N" | Typically 1:4 for PGY-3 |

```bash
***REMOVED*** Set stricter supervision for procedures
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "pgy1_supervision_ratio": "1:1",
    "pgy2_supervision_ratio": "1:2",
    "pgy3_supervision_ratio": "1:3"
  }'
```

***REMOVED******REMOVED******REMOVED*** Scheduling Options

Controls when residents can be scheduled.

| Setting | Description | Default |
|---------|-------------|---------|
| `enable_weekend_scheduling` | Allow weekend assignments | `true` |
| `enable_holiday_scheduling` | Allow holiday assignments | `false` |
| `default_block_duration_hours` | Standard block length | 4 hours |

```bash
***REMOVED*** Enable holiday scheduling
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "enable_weekend_scheduling": true,
    "enable_holiday_scheduling": true
  }'
```

---

***REMOVED******REMOVED*** Usage Examples

***REMOVED******REMOVED******REMOVED*** View Current Settings

```bash
***REMOVED*** Get and display current settings
curl -s http://localhost:8000/api/settings | jq .
```

***REMOVED******REMOVED******REMOVED*** Configure for Strict ACGME Compliance

```bash
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{
    "scheduling_algorithm": "cp_sat",
    "work_hours_per_week": 80,
    "max_consecutive_days": 6,
    "min_days_off_per_week": 1,
    "pgy1_supervision_ratio": "1:2",
    "pgy2_supervision_ratio": "1:4",
    "pgy3_supervision_ratio": "1:4",
    "enable_weekend_scheduling": true,
    "enable_holiday_scheduling": false
  }'
```

***REMOVED******REMOVED******REMOVED*** Toggle Weekend Scheduling

```bash
***REMOVED*** Disable weekend scheduling
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"enable_weekend_scheduling": false}'

***REMOVED*** Re-enable weekend scheduling
curl -X PATCH http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d '{"enable_weekend_scheduling": true}'
```

***REMOVED******REMOVED******REMOVED*** Reset to Defaults

```bash
***REMOVED*** Reset all settings
curl -X DELETE http://localhost:8000/api/settings

***REMOVED*** Verify defaults
curl http://localhost:8000/api/settings
```

***REMOVED******REMOVED******REMOVED*** Backup and Restore Settings

```bash
***REMOVED*** Backup current settings
curl -s http://localhost:8000/api/settings > settings_backup.json

***REMOVED*** Restore settings
curl -X POST http://localhost:8000/api/settings \
  -H "Content-Type: application/json" \
  -d @settings_backup.json
```

---

***REMOVED******REMOVED*** Environment vs API Settings

Some settings can also be configured via environment variables. API settings take precedence.

| Environment Variable | API Setting | Description |
|---------------------|-------------|-------------|
| `DEFAULT_ALGORITHM` | `scheduling_algorithm` | Default scheduling algorithm |
| `MAX_WORK_HOURS` | `work_hours_per_week` | Maximum work hours |

---

*See also: [Schedule Generation](./schedule.md) for using these settings*
