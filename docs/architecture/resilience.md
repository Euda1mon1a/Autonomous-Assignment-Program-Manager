# Resilience Framework

Fault tolerance and system stability design.

---

## Overview

The resilience framework is inspired by cross-industry best practices:

- **Queuing Theory** - 80% utilization threshold
- **Power Grid Engineering** - N-1/N-2 contingency analysis
- **Nuclear Safety** - Defense in Depth levels

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

Building on the core resilience framework, the system incorporates advanced monitoring techniques from seven additional industries:

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

**For detailed implementation:** See [Cross-Disciplinary Resilience Extensions](../guides/cross-disciplinary-resilience.md)

---

## Background Tasks

Celery tasks run continuously:

- Health checks every 5 minutes
- Contingency analysis every 4 hours
- Alert notifications as needed

---

## Related Documentation

- **[Complete Resilience Framework Guide](../guides/resilience-framework.md)** - Comprehensive implementation details
- **[Cross-Disciplinary Resilience Extensions](../guides/cross-disciplinary-resilience.md)** - Advanced monitoring from 7 industries
- **[System Architecture](overview.md)** - Overall system design
- **[Backend Architecture](backend.md)** - Backend implementation details
- **[Operations Metrics](../operations/metrics.md)** - Monitoring and metrics
