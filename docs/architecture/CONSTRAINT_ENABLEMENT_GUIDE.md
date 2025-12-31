# Constraint Enablement Guide

## Overview

This guide explains which constraints are enabled by default, which are disabled, why they are disabled, and when you should enable them.

**Key Insight**: The constraint system is working correctly. All constraints that are disabled are **intentionally disabled by default** for opt-in usage. The enable/disable logic exists and works properly.

## Quick Reference

### Always Enabled (Cannot Disable)

These constraints enforce regulatory compliance and basic scheduling requirements:

| Constraint | Category | Purpose |
|------------|----------|---------|
| `Availability` | ACGME | Enforces resident/faculty availability |
| `EightyHourRule` | ACGME | 80-hour per week duty limit |
| `OneInSevenRule` | ACGME | 1-in-7 day off requirement |
| `SupervisionRatio` | ACGME | Faculty supervision ratios by PGY level |
| `OnePersonPerBlock` | CAPACITY | Exactly one person per block-rotation |
| `ClinicCapacity` | CAPACITY | Clinic maximum occupancy limits |
| `MaxPhysiciansInClinic` | CAPACITY | Maximum faculty supervising same clinic |
| `Coverage` | COVERAGE | All required rotations must be covered |
| `Equity` | EQUITY | Balanced assignment distribution |
| `Continuity` | EQUITY | Continuity of care for repeated assignments |

### Disabled By Default (Opt-In)

These constraints are disabled by default and can be enabled when needed:

| Constraint | Category | Enable When | Dependencies |
|------------|----------|-------------|--------------|
| `OvernightCallGeneration` | CALL | Automatic call scheduling desired | None |
| `PostCallAutoAssignment` | CALL | Post-call activities auto-assigned | `OvernightCallGeneration` |
| `FMITWeekBlocking` | FMIT | Strict FMIT week blocking needed | None |
| `FMITMandatoryCall` | FMIT | FMIT includes mandatory weekend call | None |
| `FMITResidentClinicDay` | FMIT | Resident clinic during FMIT | None |
| `SMResidentFacultyAlignment` | SPECIALTY | Sports Medicine program exists | None |
| `SMFacultyNoRegularClinic` | SPECIALTY | SM faculty only does SM clinic | `SMResidentFacultyAlignment` |
| `ZoneBoundary` | RESILIENCE | Aggressive resilience (Tier 2) | None |
| `PreferenceTrail` | RESILIENCE | Aggressive resilience (Tier 2) | None |
| `N1Vulnerability` | RESILIENCE | Aggressive resilience (Tier 2) | None |

## Detailed Constraint Descriptions

### ACGME Constraints (Always Enabled)

#### Availability
- **Status**: ENABLED
- **Priority**: CRITICAL
- **Purpose**: Ensures residents and faculty are only assigned to blocks when they are available (not on leave, deployment, or absence).
- **Cannot disable**: Required for regulatory compliance

#### EightyHourRule
- **Status**: ENABLED
- **Priority**: CRITICAL
- **Weight**: 1000.0
- **Purpose**: Enforces 80-hour per week duty limit (rolling 4-week average) as required by ACGME.
- **Cannot disable**: Required for regulatory compliance

#### OneInSevenRule
- **Status**: ENABLED
- **Priority**: CRITICAL
- **Weight**: 1000.0
- **Purpose**: Enforces 1-in-7 day off requirement as required by ACGME.
- **Cannot disable**: Required for regulatory compliance

#### SupervisionRatio
- **Status**: ENABLED
- **Priority**: CRITICAL
- **Weight**: 1000.0
- **Purpose**: Ensures proper faculty supervision ratios by PGY level.
- **Cannot disable**: Required for regulatory compliance

### Capacity Constraints (Always Enabled)

#### OnePersonPerBlock
- **Status**: ENABLED
- **Priority**: CRITICAL
- **Purpose**: Ensures exactly one person is assigned to each block-rotation combination.
- **Cannot disable**: Required for valid schedules

#### ClinicCapacity
- **Status**: ENABLED
- **Priority**: HIGH
- **Purpose**: Enforces clinic maximum occupancy limits to prevent overcrowding.

#### MaxPhysiciansInClinic
- **Status**: ENABLED
- **Priority**: HIGH
- **Purpose**: Limits maximum number of faculty supervising the same clinic simultaneously.

### Coverage Constraints (Always Enabled)

#### Coverage
- **Status**: ENABLED
- **Priority**: HIGH
- **Weight**: 1000.0
- **Purpose**: Ensures all required rotations are covered every day.
- **Highly recommended**: Critical for operational continuity

### Equity Constraints (Always Enabled)

#### Equity
- **Status**: ENABLED
- **Priority**: MEDIUM
- **Weight**: 10.0
- **Purpose**: Promotes balanced assignment distribution across residents and faculty.

#### Continuity
- **Status**: ENABLED
- **Priority**: MEDIUM
- **Weight**: 5.0
- **Purpose**: Promotes continuity of care by preferring repeated assignments to same rotations.

### Call Constraints (Opt-In)

#### OvernightCallGeneration
- **Status**: DISABLED by default
- **Priority**: HIGH
- **Purpose**: Automatically generates overnight call assignments for Sunday through Thursday.
- **Enable when**:
  - You want automatic call scheduling
  - You have defined call coverage requirements
  - You prefer algorithmic call assignment over manual scheduling
- **Disable reason**: Call may be manually scheduled or handled by external system
- **How to enable**:
  ```python
  manager = ConstraintManager()
  manager.enable("OvernightCallGeneration")
  # OR
  manager = ConstraintManager.create_default()
  manager.enable("OvernightCallGeneration")
  ```

#### PostCallAutoAssignment
- **Status**: DISABLED by default
- **Priority**: HIGH
- **Dependencies**: `OvernightCallGeneration`
- **Purpose**: Automatically assigns PCAT (Post-Call Attending) and DO (Direct Observation) activities after overnight call.
- **Enable when**:
  - You have enabled `OvernightCallGeneration`
  - You want post-call activities automatically scheduled
  - You use PCAT/DO activities in your program
- **Disable reason**: Depends on `OvernightCallGeneration`, may be manually scheduled
- **How to enable**:
  ```python
  manager = ConstraintManager()
  manager.enable("OvernightCallGeneration")
  manager.enable("PostCallAutoAssignment")
  # OR use preset
  from app.scheduling.constraints.config import get_constraint_config
  config = get_constraint_config()
  config.apply_preset("call_scheduling")
  ```

### FMIT Constraints (Opt-In)

#### FMITWeekBlocking
- **Status**: DISABLED by default
- **Priority**: HIGH
- **Purpose**: Blocks other assignments during FMIT (Friday inpatient) weeks.
- **Enable when**:
  - FMIT weeks should be exclusive (no other assignments)
  - Faculty cannot have clinic or other duties during FMIT week
- **Disable reason**: FMIT may allow some other assignments, handled by other constraints
- **How to enable**:
  ```python
  manager.enable("FMITWeekBlocking")
  ```

#### FMITMandatoryCall
- **Status**: DISABLED by default
- **Priority**: HIGH
- **Purpose**: Ensures FMIT faculty takes Friday/Saturday overnight call during their FMIT week.
- **Enable when**:
  - FMIT includes mandatory weekend call duty
  - You want to enforce this requirement in solver
- **Disable reason**: May use separate call scheduling, not all programs require this
- **How to enable**:
  ```python
  manager.enable("FMITMandatoryCall")
  ```

#### FMITResidentClinicDay
- **Status**: DISABLED by default
- **Priority**: MEDIUM
- **Purpose**: Enforces resident clinic day constraints during FMIT weeks.
- **Enable when**:
  - Residents must have specific clinic days during FMIT
  - You want to enforce clinic scheduling during FMIT
- **Disable reason**: Clinic scheduling may be flexible, not all programs need this
- **How to enable**:
  ```python
  manager.enable("FMITResidentClinicDay")
  ```

### Specialty Constraints (Conditional)

#### SMResidentFacultyAlignment
- **Status**: DISABLED by default
- **Priority**: HIGH
- **Purpose**: Ensures Sports Medicine residents are scheduled with Sports Medicine faculty.
- **Enable when**:
  - Your program has a Sports Medicine track
  - SM residents must be supervised by SM faculty
  - SM clinic requires specialized faculty supervision
- **Disable reason**: Only needed if Sports Medicine program exists
- **How to enable**:
  ```python
  manager.enable("SMResidentFacultyAlignment")
  # OR use preset
  config.apply_preset("sports_medicine")
  ```

#### SMFacultyNoRegularClinic
- **Status**: DISABLED by default
- **Priority**: HIGH
- **Dependencies**: `SMResidentFacultyAlignment`
- **Purpose**: Excludes SM faculty from regular clinic assignments.
- **Enable when**:
  - SM faculty only does SM clinic (no regular clinic)
  - You have enabled `SMResidentFacultyAlignment`
- **Disable reason**: Only needed if SM program exists and SM faculty is specialized
- **How to enable**:
  ```python
  manager.enable("SMResidentFacultyAlignment")
  manager.enable("SMFacultyNoRegularClinic")
  ```

### Resilience Constraints (Tiered)

#### Tier 1 (Enabled by Default in Resilience Mode)

##### HubProtection
- **Status**: ENABLED in resilience-aware mode
- **Priority**: MEDIUM
- **Weight**: 15.0
- **Purpose**: Protects hub resources (high-centrality faculty) from overload.
- **Already enabled**: If using `create_resilience_aware()`

##### UtilizationBuffer
- **Status**: ENABLED in resilience-aware mode
- **Priority**: MEDIUM
- **Weight**: 20.0
- **Purpose**: Maintains utilization below 80% threshold to prevent cascade failures.
- **Already enabled**: If using `create_resilience_aware()`

#### Tier 2 (Aggressive Resilience - Opt-In)

##### ZoneBoundary
- **Status**: DISABLED by default
- **Priority**: MEDIUM
- **Weight**: 12.0
- **Purpose**: Isolates scheduling zones to prevent cascade failures.
- **Enable when**:
  - You want aggressive resilience protection
  - You can tolerate more restrictive scheduling
  - You have identified zone boundaries in your program
- **Disable reason**: May be too restrictive for some use cases
- **How to enable**:
  ```python
  manager = ConstraintManager.create_resilience_aware(tier=2)
  # OR
  config.apply_preset("resilience_tier2")
  ```

##### PreferenceTrail
- **Status**: DISABLED by default
- **Priority**: MEDIUM
- **Weight**: 8.0
- **Purpose**: Tracks preference violations to identify stress patterns.
- **Enable when**:
  - You want aggressive resilience protection
  - You track faculty preferences systematically
- **Disable reason**: May be too restrictive for some use cases
- **How to enable**:
  ```python
  manager = ConstraintManager.create_resilience_aware(tier=2)
  ```

##### N1Vulnerability
- **Status**: DISABLED by default
- **Priority**: MEDIUM
- **Weight**: 25.0
- **Purpose**: Prevents single points of failure (N-1 vulnerability).
- **Enable when**:
  - You want aggressive resilience protection
  - You need to prevent critical dependencies on single individuals
- **Disable reason**: May be too restrictive, high weight may over-constrain solver
- **How to enable**:
  ```python
  manager = ConstraintManager.create_resilience_aware(tier=2)
  ```

## Configuration Presets

### Default
```python
manager = ConstraintManager.create_default()
```
- All ACGME, capacity, coverage, and equity constraints enabled
- Call, FMIT, SM, and Tier 2 resilience constraints disabled
- **Use when**: Standard scheduling without special features

### Minimal
```python
manager = ConstraintManager.create_minimal()
# OR
config = get_constraint_config()
config.apply_preset("minimal")
```
- Only essential constraints enabled (Availability, OnePersonPerBlock, Coverage)
- All optional constraints disabled
- **Use when**: Fast solving, testing, or simple schedules

### Strict
```python
manager = ConstraintManager.create_strict()
# OR
config.apply_preset("strict")
```
- All constraints enabled
- Soft constraint weights doubled
- **Use when**: Maximum quality, comprehensive checking

### Resilience Tier 1
```python
manager = ConstraintManager.create_resilience_aware(tier=1)
# OR
config.apply_preset("resilience_tier1")
```
- Core resilience constraints enabled (HubProtection, UtilizationBuffer)
- Tier 2 resilience disabled
- **Use when**: Basic resilience protection without over-constraining

### Resilience Tier 2
```python
manager = ConstraintManager.create_resilience_aware(tier=2)
# OR
config.apply_preset("resilience_tier2")
```
- All resilience constraints enabled
- **Use when**: Aggressive resilience protection, high-risk environments

### Call Scheduling
```python
config = get_constraint_config()
config.apply_preset("call_scheduling")
```
- Enables `OvernightCallGeneration` and `PostCallAutoAssignment`
- **Use when**: Automatic call scheduling desired

### Sports Medicine
```python
config = get_constraint_config()
config.apply_preset("sports_medicine")
```
- Enables `SMResidentFacultyAlignment` and `SMFacultyNoRegularClinic`
- **Use when**: Sports Medicine program exists

## Using the CLI Tool

### View Status
```bash
python scripts/constraint_manager_cli.py status
```

### List All Constraints
```bash
python scripts/constraint_manager_cli.py list
```

### List Disabled Constraints
```bash
python scripts/constraint_manager_cli.py disabled
```

### Enable a Constraint
```bash
python scripts/constraint_manager_cli.py enable OvernightCallGeneration
```

### Apply a Preset
```bash
python scripts/constraint_manager_cli.py preset call_scheduling
```

### Test All Disabled Constraints
```bash
python scripts/constraint_manager_cli.py test-all
```

## Programmatic Usage

### In Scheduling Code
```python
from app.scheduling.constraints.manager import ConstraintManager

# Option 1: Start with default and customize
manager = ConstraintManager.create_default()
manager.enable("OvernightCallGeneration")
manager.enable("PostCallAutoAssignment")

# Option 2: Use configuration system
from app.scheduling.constraints.config import get_constraint_config

config = get_constraint_config()
config.apply_preset("call_scheduling")

# Then apply to manager
manager = ConstraintManager.create_default()
if config.is_enabled("OvernightCallGeneration"):
    manager.enable("OvernightCallGeneration")
```

### Environment-Based Configuration
```bash
# Set in .env or environment
export CONSTRAINT_PRESET=call_scheduling

# Configuration will auto-apply on import
```

## Troubleshooting

### Constraint Not Working After Enabling

**Problem**: Enabled constraint but it's not being applied.

**Solutions**:
1. Check if constraint has dependencies:
   ```python
   config = get_constraint_config()
   constraint = config.get("ConstraintName")
   print(constraint.dependencies)
   ```

2. Ensure dependencies are enabled:
   ```python
   for dep in constraint.dependencies:
       manager.enable(dep)
   ```

3. Verify constraint is actually enabled:
   ```python
   print(manager.get_enabled())
   ```

### Solver Infeasible After Enabling Constraint

**Problem**: Schedule generation fails after enabling constraint.

**Solutions**:
1. Check constraint weight (lower if too restrictive):
   ```python
   config = get_constraint_config()
   constraint = config.get("ConstraintName")
   constraint.weight = 5.0  # Lower weight
   ```

2. Try enabling dependencies:
   - `PostCallAutoAssignment` requires `OvernightCallGeneration`
   - `SMFacultyNoRegularClinic` requires `SMResidentFacultyAlignment`

3. Use minimal preset to isolate issue:
   ```python
   config.apply_preset("minimal")
   # Then enable constraints one by one
   ```

### Which Constraints Should I Enable?

**Answer depends on your use case**:

1. **Basic scheduling**: Use default preset (no changes needed)

2. **Automatic call scheduling**: Enable call constraints
   ```python
   config.apply_preset("call_scheduling")
   ```

3. **Sports Medicine program**: Enable SM constraints
   ```python
   config.apply_preset("sports_medicine")
   ```

4. **High resilience**: Use tier 2 resilience
   ```python
   manager = ConstraintManager.create_resilience_aware(tier=2)
   ```

5. **Fast solving**: Use minimal preset
   ```python
   manager = ConstraintManager.create_minimal()
   ```

## Summary

- **Enable/disable logic exists and works correctly**
- **Disabled constraints are intentionally disabled for opt-in usage**
- **All ACGME, capacity, coverage, and equity constraints are enabled by default**
- **Use presets for common configurations**
- **Use CLI tool for quick status checks**
- **Enable optional constraints based on your program's needs**

## See Also

- [Constraint System Architecture](./SOLVER_ALGORITHM.md)
- [ACGME Compliance](./ACGME_COMPLIANCE.md)
- [Resilience Framework](./cross-disciplinary-resilience.md)
