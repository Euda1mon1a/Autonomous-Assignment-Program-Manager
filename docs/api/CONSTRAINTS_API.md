***REMOVED*** Constraint Management API

The Constraint Management API provides endpoints for viewing and managing scheduling constraint configurations. Constraints control how the schedule generation algorithm balances competing requirements like ACGME compliance, coverage needs, workload distribution, and resilience metrics.

***REMOVED******REMOVED*** Base URL

```
/constraints
```

***REMOVED******REMOVED*** Endpoints Overview

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/constraints/status` | GET | Get status of all constraints |
| `/constraints` | GET | List all constraints (alias) |
| `/constraints/enabled` | GET | List enabled constraints only |
| `/constraints/disabled` | GET | List disabled constraints only |
| `/constraints/category/{category}` | GET | List constraints by category |
| `/constraints/{name}` | GET | Get specific constraint details |
| `/constraints/{name}/enable` | POST | Enable a constraint |
| `/constraints/{name}/disable` | POST | Disable a constraint |
| `/constraints/preset/{preset}` | POST | Apply a constraint preset |

---

***REMOVED******REMOVED*** Constraint Overview Endpoints

***REMOVED******REMOVED******REMOVED*** Get Constraint Status

**Purpose:** Get comprehensive status of all constraints with enabled/disabled counts.

```http
GET /constraints/status
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
{
  "constraints": [
    {
      "name": "acgme_80_hour_rule",
      "enabled": true,
      "priority": 100,
      "weight": 10.0,
      "category": "ACGME",
      "description": "Enforce 80-hour work week limit averaged over 4 weeks",
      "dependencies": [],
      "enable_condition": null,
      "disable_reason": null
    },
    {
      "name": "coverage_minimum",
      "enabled": true,
      "priority": 90,
      "weight": 8.0,
      "category": "COVERAGE",
      "description": "Ensure minimum coverage requirements are met",
      "dependencies": ["shift_assignment"],
      "enable_condition": null,
      "disable_reason": null
    },
    {
      "name": "experimental_time_crystal",
      "enabled": false,
      "priority": 20,
      "weight": 2.0,
      "category": "EXPERIMENTAL",
      "description": "Time crystal anti-churn scheduling (Tier 4)",
      "dependencies": ["schedule_stability"],
      "enable_condition": "Enable for Block 11+ when stability is critical",
      "disable_reason": "Experimental feature - use with caution"
    }
  ],
  "total": 35,
  "enabled_count": 28,
  "disabled_count": 7
}
```

**Schema:** `ConstraintListResponse`

***REMOVED******REMOVED******REMOVED******REMOVED*** Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Unique constraint identifier |
| `enabled` | boolean | Whether constraint is active |
| `priority` | integer | Execution priority (higher = earlier) |
| `weight` | float | Constraint weight in solver |
| `category` | string | Constraint category (see below) |
| `description` | string | Human-readable description |
| `dependencies` | string[] | Required constraints that must be enabled |
| `enable_condition` | string | Recommendation for when to enable (nullable) |
| `disable_reason` | string | Warning or reason for being disabled (nullable) |

***REMOVED******REMOVED******REMOVED******REMOVED*** Constraint Categories

| Category | Description | Examples |
|----------|-------------|----------|
| `ACGME` | ACGME compliance requirements | 80-hour rule, 1-in-7 rule, supervision ratios |
| `COVERAGE` | Coverage and staffing requirements | Minimum coverage, shift assignments |
| `CAPACITY` | Workload and capacity constraints | Utilization limits, burnout prevention |
| `FAIRNESS` | Equitable distribution | Workload balance, preference fairness |
| `PREFERENCE` | Personal preferences | Vacation requests, shift preferences |
| `RESILIENCE` | Resilience framework constraints | N-1/N-2 contingency, defense in depth |
| `EXPERIMENTAL` | Experimental features (Tier 4+) | Time crystal, spin glass, exotic concepts |

***REMOVED******REMOVED******REMOVED******REMOVED*** Notes
- Priority values: 100 (critical) → 1 (low priority)
- Weight values: Used by solver to balance competing constraints
- Dependencies: Parent constraints must be enabled first

---

***REMOVED******REMOVED******REMOVED*** List All Constraints

**Purpose:** Alias for `/constraints/status` - returns the same response.

```http
GET /constraints
```

Same response as `GET /constraints/status`.

---

***REMOVED******REMOVED******REMOVED*** List Enabled Constraints

**Purpose:** Get only the constraints that are currently active.

```http
GET /constraints/enabled
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
[
  {
    "name": "acgme_80_hour_rule",
    "enabled": true,
    "priority": 100,
    "weight": 10.0,
    "category": "ACGME",
    "description": "Enforce 80-hour work week limit averaged over 4 weeks",
    "dependencies": [],
    "enable_condition": null,
    "disable_reason": null
  },
  {
    "name": "coverage_minimum",
    "enabled": true,
    "priority": 90,
    "weight": 8.0,
    "category": "COVERAGE",
    "description": "Ensure minimum coverage requirements are met",
    "dependencies": ["shift_assignment"],
    "enable_condition": null,
    "disable_reason": null
  }
]
```

**Schema:** `List[ConstraintStatusResponse]`

***REMOVED******REMOVED******REMOVED******REMOVED*** Notes
- Returns constraints currently used by the schedule generator
- Sorted by priority (highest first)

---

***REMOVED******REMOVED******REMOVED*** List Disabled Constraints

**Purpose:** Get constraints that are currently inactive.

```http
GET /constraints/disabled
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
[
  {
    "name": "experimental_time_crystal",
    "enabled": false,
    "priority": 20,
    "weight": 2.0,
    "category": "EXPERIMENTAL",
    "description": "Time crystal anti-churn scheduling (Tier 4)",
    "dependencies": ["schedule_stability"],
    "enable_condition": "Enable for Block 11+ when stability is critical",
    "disable_reason": "Experimental feature - use with caution"
  }
]
```

**Schema:** `List[ConstraintStatusResponse]`

***REMOVED******REMOVED******REMOVED******REMOVED*** Notes
- Useful for identifying optional constraints that could be enabled
- Check `disable_reason` for warnings before enabling experimental features

---

***REMOVED******REMOVED******REMOVED*** List Constraints by Category

**Purpose:** Filter constraints by category (ACGME, COVERAGE, RESILIENCE, etc.).

```http
GET /constraints/category/{category}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Constraint category (case-insensitive) |

**Valid categories:**
- `ACGME` - ACGME compliance requirements
- `COVERAGE` - Coverage and staffing
- `CAPACITY` - Workload and capacity
- `FAIRNESS` - Equitable distribution
- `PREFERENCE` - Personal preferences
- `RESILIENCE` - Resilience framework
- `EXPERIMENTAL` - Experimental features

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
[
  {
    "name": "acgme_80_hour_rule",
    "enabled": true,
    "priority": 100,
    "weight": 10.0,
    "category": "ACGME",
    "description": "Enforce 80-hour work week limit averaged over 4 weeks",
    "dependencies": [],
    "enable_condition": null,
    "disable_reason": null
  },
  {
    "name": "acgme_1_in_7_rule",
    "enabled": true,
    "priority": 95,
    "weight": 9.0,
    "category": "ACGME",
    "description": "Ensure one 24-hour period off every 7 days",
    "dependencies": [],
    "enable_condition": null,
    "disable_reason": null
  }
]
```

**Schema:** `List[ConstraintStatusResponse]`

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid category: INVALID. Valid categories: ['ACGME', 'COVERAGE', 'CAPACITY', 'FAIRNESS', 'PREFERENCE', 'RESILIENCE', 'EXPERIMENTAL']"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Notes
- Returns both enabled and disabled constraints in the category
- Useful for auditing specific constraint types

---

***REMOVED******REMOVED******REMOVED*** Get Specific Constraint

**Purpose:** Get detailed information about a single constraint.

```http
GET /constraints/{name}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Constraint name (exact match) |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
{
  "name": "acgme_80_hour_rule",
  "enabled": true,
  "priority": 100,
  "weight": 10.0,
  "category": "ACGME",
  "description": "Enforce 80-hour work week limit averaged over 4 weeks",
  "dependencies": [],
  "enable_condition": null,
  "disable_reason": null
}
```

**Schema:** `ConstraintStatusResponse`

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Responses

**404 Not Found**
```json
{
  "detail": "Constraint 'invalid_name' not found"
}
```

---

***REMOVED******REMOVED*** Constraint Modification Endpoints

***REMOVED******REMOVED******REMOVED*** Enable Constraint

**Purpose:** Enable a specific constraint for schedule generation.

```http
POST /constraints/{name}/enable
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Constraint name to enable |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
{
  "success": true,
  "message": "Successfully enabled constraint 'workload_balance'",
  "constraint": {
    "name": "workload_balance",
    "enabled": true,
    "priority": 70,
    "weight": 5.0,
    "category": "FAIRNESS",
    "description": "Balance workload across all faculty",
    "dependencies": ["assignment_count"],
    "enable_condition": null,
    "disable_reason": null
  }
}
```

**Schema:** `ConstraintEnableResponse`

***REMOVED******REMOVED******REMOVED******REMOVED*** Response (Already Enabled)

```json
{
  "success": true,
  "message": "Constraint 'acgme_80_hour_rule' is already enabled",
  "constraint": { ... }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Responses

**404 Not Found**
```json
{
  "detail": "Constraint 'invalid_name' not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to enable constraint 'constraint_name'"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Notes
- Check `dependencies` field - parent constraints may need to be enabled first
- Enabling experimental constraints may affect schedule generation performance

---

***REMOVED******REMOVED******REMOVED*** Disable Constraint

**Purpose:** Disable a constraint to exclude it from schedule generation.

```http
POST /constraints/{name}/disable
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | string | Constraint name to disable |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
{
  "success": true,
  "message": "Successfully disabled constraint 'experimental_feature'",
  "constraint": {
    "name": "experimental_feature",
    "enabled": false,
    "priority": 20,
    "weight": 2.0,
    "category": "EXPERIMENTAL",
    "description": "Experimental scheduling feature",
    "dependencies": [],
    "enable_condition": null,
    "disable_reason": "Feature disabled by user"
  }
}
```

**Schema:** `ConstraintEnableResponse`

***REMOVED******REMOVED******REMOVED******REMOVED*** Response (Already Disabled)

```json
{
  "success": true,
  "message": "Constraint 'experimental_feature' is already disabled",
  "constraint": { ... }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Responses

**404 Not Found**
```json
{
  "detail": "Constraint 'invalid_name' not found"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to disable constraint 'constraint_name'"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Notes
- Disabling ACGME constraints may result in non-compliant schedules
- Check if other constraints depend on this constraint before disabling

---

***REMOVED******REMOVED******REMOVED*** Apply Constraint Preset

**Purpose:** Apply a predefined set of constraint configurations for common scenarios.

```http
POST /constraints/preset/{preset}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `preset` | string | Preset name (see valid presets below) |

**Valid Presets:**

| Preset | Description | Use Case |
|--------|-------------|----------|
| `minimal` | Only essential constraints | Initial testing, baseline schedules |
| `strict` | All constraints enabled, doubled weights | Maximum compliance and fairness |
| `resilience_tier1` | Core resilience constraints (80% util, N-1) | Standard resilience mode |
| `resilience_tier2` | All resilience constraints (Tier 1 + 2) | Enhanced resilience with SPC monitoring |
| `call_scheduling` | Call scheduling constraints | Night call, backup call optimization |
| `sports_medicine` | Sports medicine constraints | Athletic event coverage, weekend clinics |

***REMOVED******REMOVED******REMOVED******REMOVED*** Response

**Status:** 200 OK

```json
{
  "success": true,
  "message": "Successfully applied preset 'resilience_tier1'",
  "enabled_constraints": [
    "utilization_threshold_80",
    "n_minus_1_contingency",
    "defense_in_depth",
    "acgme_80_hour_rule",
    "coverage_minimum"
  ],
  "disabled_constraints": [
    "experimental_time_crystal",
    "spin_glass_solver",
    "quantum_optimization"
  ]
}
```

**Schema:** `PresetApplyResponse`

***REMOVED******REMOVED******REMOVED******REMOVED*** Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid preset: invalid_preset. Valid presets: ['minimal', 'strict', 'resilience_tier1', 'resilience_tier2', 'call_scheduling', 'sports_medicine']"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to apply preset"
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Notes
- Presets override individual constraint settings
- Use presets as starting points, then fine-tune individual constraints
- `strict` preset doubles all constraint weights for aggressive optimization

---

***REMOVED******REMOVED*** Preset Details

***REMOVED******REMOVED******REMOVED*** Minimal Preset

**Enabled Constraints:**
- `acgme_80_hour_rule` - ACGME work hour limit
- `acgme_1_in_7_rule` - Day off requirement
- `coverage_minimum` - Minimum coverage only

**Use Case:** Testing, baseline schedule generation, minimal viable schedule

---

***REMOVED******REMOVED******REMOVED*** Strict Preset

**Enabled Constraints:** All constraints

**Weight Modification:** All weights doubled

**Use Case:** Maximum compliance, fairness, and quality - may increase solver time

---

***REMOVED******REMOVED******REMOVED*** Resilience Tier 1 Preset

**Enabled Constraints:**
- All ACGME constraints
- `utilization_threshold_80` - 80% max utilization
- `n_minus_1_contingency` - N-1 vulnerability detection
- `defense_in_depth` - 5-tier defense levels
- `static_stability` - Pre-computed fallbacks

**Use Case:** Standard resilience mode for most deployments

---

***REMOVED******REMOVED******REMOVED*** Resilience Tier 2 Preset

**Enabled Constraints:** All Tier 1 + Strategic concepts
- `homeostasis` - Biological feedback loops
- `blast_radius_isolation` - Failure containment
- `spc_monitoring` - Statistical process control
- `erlang_coverage` - Queuing-based staffing

**Use Case:** Enhanced resilience with cross-industry analytics

---

***REMOVED******REMOVED******REMOVED*** Call Scheduling Preset

**Enabled Constraints:**
- ACGME constraints
- `call_rotation_fairness` - Equitable call distribution
- `backup_call_coverage` - Backup call assignments
- `post_call_rest` - Post-call recovery time
- `consecutive_call_limit` - Limit consecutive call nights

**Use Case:** Optimizing night call and backup call schedules

---

***REMOVED******REMOVED******REMOVED*** Sports Medicine Preset

**Enabled Constraints:**
- ACGME constraints
- `athletic_event_coverage` - Game day coverage
- `weekend_clinic_staffing` - Weekend clinic requirements
- `travel_time_buffer` - Time for event travel
- `injury_clinic_priority` - Injury clinic staffing

**Use Case:** Sports medicine programs with athletic event coverage

---

***REMOVED******REMOVED*** Common Workflows

***REMOVED******REMOVED******REMOVED*** Audit Current Configuration

```bash
***REMOVED*** 1. Get all constraint status
GET /constraints/status

***REMOVED*** 2. Check ACGME constraints specifically
GET /constraints/category/ACGME

***REMOVED*** 3. Identify disabled constraints
GET /constraints/disabled
```

***REMOVED******REMOVED******REMOVED*** Enable Resilience Framework

```bash
***REMOVED*** Apply Tier 1 resilience preset
POST /constraints/preset/resilience_tier1

***REMOVED*** Verify resilience constraints enabled
GET /constraints/category/RESILIENCE
```

***REMOVED******REMOVED******REMOVED*** Experiment with New Constraint

```bash
***REMOVED*** 1. Check constraint details
GET /constraints/experimental_time_crystal

***REMOVED*** 2. Enable experimentally
POST /constraints/experimental_time_crystal/enable

***REMOVED*** 3. Generate schedule and evaluate

***REMOVED*** 4. Disable if not helpful
POST /constraints/experimental_time_crystal/disable
```

***REMOVED******REMOVED******REMOVED*** Reset to Defaults

```bash
***REMOVED*** Apply minimal preset to start fresh
POST /constraints/preset/minimal

***REMOVED*** Then selectively enable needed constraints
POST /constraints/coverage_gaps/enable
POST /constraints/workload_balance/enable
```

---

***REMOVED******REMOVED*** Error Handling

All endpoints return standard HTTP error codes:

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 400 | Bad Request | Invalid category or preset name |
| 404 | Not Found | Constraint name doesn't exist |
| 500 | Internal Server Error | Configuration system error |

---

***REMOVED******REMOVED*** Related Documentation

- `backend/app/api/routes/constraints.py` - Implementation
- `backend/app/scheduling/constraints/config.py` - Constraint configuration system
- `docs/architecture/CONSTRAINT_SYSTEM.md` - Constraint architecture
- `docs/architecture/cross-disciplinary-resilience.md` - Resilience framework constraints
- `docs/architecture/TIME_CRYSTAL_ANTI_CHURN.md` - Time crystal constraint details
