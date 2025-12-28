# Resilience Framework

Fault tolerance and system stability design.

---

## Overview

The resilience framework is inspired by cross-industry best practices:

- **Queuing Theory** - 80% utilization threshold
- **Power Grid Engineering** - N-1/N-2 contingency analysis
- **Nuclear Safety** - Defense in Depth levels
- **Immunology** - Anomaly detection via Artificial Immune Systems
- **Epidemiology** - Burnout contagion modeling
- **Structural Mechanics** - Schedule stability via tensegrity equilibrium

---

## Safety Levels

| Level | Color | Status | Response |
|-------|-------|--------|----------|
| 1 | :material-circle:{ style="color: #81C784" } Green | Normal | Routine operations |
| 2 | :material-circle:{ style="color: #FFD54F" } Yellow | Elevated | Increased monitoring |
| 3 | :material-circle:{ style="color: #FF8A65" } Orange | High | Active intervention |
| 4 | :material-circle:{ style="color: #E57373" } Red | Critical | Emergency procedures |
| 5 | :material-circle:{ style="color: #424242" } Black | Crisis | Fallback schedules |

---

## Key Features

### Utilization Monitoring

```
Warning:   75% utilization
Critical:  85% utilization
Emergency: 95% utilization
```

### Contingency Analysis

- N-1 analysis: Impact of single person absence
- N-2 analysis: Impact of two simultaneous absences
- Automatic vulnerability detection

### Fallback Schedules

Pre-computed backup schedules for instant crisis response.

---

## Cross-Disciplinary Extensions

Building on the core resilience framework, the system incorporates advanced monitoring techniques from eight additional industries:

### 1. SPC Monitoring (Semiconductor Manufacturing)

Statistical Process Control monitors scheduling metrics using control charts to detect anomalies before they become critical issues. Tracks trends, shifts, and outliers in workload distribution.

### 2. Process Capability (Six Sigma)

Measures the system's ability to meet scheduling constraints using Cp/Cpk indices. Quantifies how well the schedule stays within ACGME compliance boundaries, targeting "Six Sigma" (99.99966%) reliability.

### 3. Burnout Epidemiology

Applies SIR (Susceptible-Infected-Recovered) epidemic modeling to track burnout propagation through teams. Identifies high-risk individuals and predicts cascade effects when stress spreads across the schedule.

### 4. Erlang Coverage (Telecommunications)

Uses Erlang-C queueing formulas to calculate optimal staffing levels for target service levels. Ensures adequate coverage during peak demand while avoiding over-staffing.

### 5. Seismic Detection (Seismology)

Implements P-wave/S-wave analysis to detect early warning signals of schedule instability. Identifies precursor events that predict major disruptions, enabling proactive intervention.

### 6. Burnout Fire Index (Forestry)

Adapts wildfire risk indices (FWI) to measure burnout risk based on workload, fatigue accumulation, and recovery time. Provides danger ratings (Low/Moderate/High/Very High/Extreme) for individuals and teams.

### 7. Creep Fatigue (Materials Science)

Models cumulative stress damage over time, similar to metal fatigue under sustained load. Tracks how repeated high-workload periods degrade resilience even when individual shifts comply with ACGME rules.

### 8. Recovery Distance (Operations Research)

Measures schedule resilience by calculating the minimum number of edits needed to recover from n-1 shocks (single resource loss). Lower recovery distance indicates more robust schedules that can absorb disruptions with minimal manual intervention.

**For detailed implementation:** See [Cross-Disciplinary Resilience Extensions](cross-disciplinary-resilience.md)

---

## Background Tasks

Celery tasks run continuously:

- Health checks every 5 minutes
- Contingency analysis every 4 hours
- Alert notifications as needed

---

## Advanced Modules

### Artificial Immune System (AIS)

Detects schedule anomalies using biological immune principles:

- **Negative Selection**: Learns valid patterns, flags deviations
- **Clonal Selection**: Adaptive repair strategies
- **Location**: `backend/app/resilience/immune_system.py`

### Burnout Contagion Model

Models burnout spread through provider networks:

- **SIS Model**: Susceptible → Infected → Susceptible
- **Superspreader Detection**: High-centrality + high-burnout nodes
- **Location**: `backend/app/resilience/contagion_model.py`

### Equity Metrics

Measures workload fairness:

- **Gini Coefficient**: 0 = equal, 1 = unequal
- **Target**: G < 0.15 for medical scheduling
- **Location**: `backend/app/resilience/equity_metrics.py`

See **[Advanced Scheduling Architecture](advanced-scheduling.md)** for full details.

---

## Related Documentation

- **[Advanced Scheduling Architecture](advanced-scheduling.md)** - Cross-disciplinary algorithms (AIS, tensegrity, etc.)
- **[Complete Resilience Framework Guide](../guides/resilience-framework.md)** - Comprehensive implementation details
- **[Cross-Disciplinary Resilience Extensions](../guides/cross-disciplinary-resilience.md)** - Advanced monitoring from 7 industries
- **[System Architecture](overview.md)** - Overall system design
- **[Backend Architecture](backend.md)** - Backend implementation details
- **[Operations Metrics](../operations/metrics.md)** - Monitoring and metrics
- **[Libraries Research](../research/scheduling-libs-research.md)** - Library evaluation and recommendations
