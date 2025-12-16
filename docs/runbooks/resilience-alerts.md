***REMOVED*** Runbook: Resilience Framework Alerts

**Alert Names:** Defense Level Transitions, Utilization Warnings, Contingency Alerts
**Severity:** Info/Warning/Critical
**Service:** Resilience

***REMOVED******REMOVED*** Description

The resilience framework monitors system stress using queuing theory principles and activates defense levels when utilization thresholds are crossed.

***REMOVED******REMOVED*** Defense Levels

| Level | Color | Utilization | Response |
|-------|-------|-------------|----------|
| NORMAL | Green | < 70% | Normal operations |
| ELEVATED | Yellow | 70-80% | Increased monitoring |
| CONTAINMENT | Orange | 80-90% | Load shedding begins |
| CRISIS | Red | 90-95% | Aggressive load shedding |
| CASCADE | Black | > 95% | Emergency fallback |

***REMOVED******REMOVED*** Quick Reference

```bash
***REMOVED*** Check current resilience status
curl http://localhost:8000/health/resilience

***REMOVED*** Get detailed Tier 1-3 status
curl http://localhost:8000/api/resilience/status

***REMOVED*** Check Prometheus metrics
curl http://localhost:8000/metrics | grep resilience
```

***REMOVED******REMOVED*** Resolution by Defense Level

***REMOVED******REMOVED******REMOVED*** GREEN (Normal) - No Action Required

System operating normally. Monitor dashboards during high-activity periods.

***REMOVED******REMOVED******REMOVED*** YELLOW (Elevated) - Increased Monitoring

**Alert:** `ResilienceDefenseLevelYellow`

1. **Acknowledge alert** in AlertManager
2. **Review current load**
   ```bash
   curl http://localhost:8000/api/resilience/utilization
   ```
3. **Identify contributing factors**
   - High schedule generation requests
   - Unusually high API traffic
   - Batch processing running

4. **Preventive actions**
   - Defer non-critical batch jobs
   - Monitor for escalation
   - Notify team lead if persisting > 30 minutes

***REMOVED******REMOVED******REMOVED*** ORANGE (Containment) - Load Shedding Active

**Alert:** `ResilienceDefenseLevelOrange`

**Automated actions in progress:**
- Non-essential features disabled
- Background jobs paused
- Request rate limiting active

**Manual actions:**
1. **Verify load shedding is working**
   ```bash
   curl http://localhost:8000/api/resilience/load-shedding/status
   ```

2. **Identify root cause**
   - Traffic spike?
   - Runaway process?
   - Resource exhaustion?

3. **Consider manual interventions**
   - Scale up resources if available
   - Kill non-essential processes
   - Enable additional rate limiting

4. **Notify stakeholders**
   - Slack: ***REMOVED***incidents
   - Email: program coordinators

***REMOVED******REMOVED******REMOVED*** RED (Crisis) - Aggressive Intervention

**Alert:** `ResilienceDefenseLevelRed`

**IMMEDIATE ACTIONS:**

1. **Acknowledge and page on-call**

2. **Verify sacrifice hierarchy is active**
   ```bash
   curl http://localhost:8000/api/resilience/sacrifice-hierarchy/status
   ```

3. **Check what's being shed**
   - Analytics/reporting (first to go)
   - Non-critical notifications
   - Bulk operations
   - Read-only features

4. **Manual interventions**
   ```bash
   ***REMOVED*** Pause all background tasks
   curl -X POST http://localhost:8000/api/resilience/pause-background-tasks

   ***REMOVED*** Enable strict rate limiting
   curl -X POST http://localhost:8000/api/resilience/rate-limit/strict
   ```

5. **Prepare fallback activation** (if escalation continues)

***REMOVED******REMOVED******REMOVED*** BLACK (Cascade) - Emergency Fallback

**Alert:** `ResilienceDefenseLevelBlack`

**CRITICAL - All hands on deck**

1. **Activate fallback schedules**
   ```bash
   curl -X POST http://localhost:8000/api/resilience/fallback/activate \
     -d '{"scenario": "emergency"}'
   ```

2. **Notify all stakeholders**
   - Program Director
   - Chief Residents
   - IT leadership

3. **Switch to read-only mode if needed**
   ```bash
   curl -X POST http://localhost:8000/api/resilience/read-only/enable
   ```

4. **Document timeline** for post-incident review

5. **Recovery plan**
   - Identify failed components
   - Plan incremental restoration
   - Test before full re-activation

***REMOVED******REMOVED*** Utilization Monitoring

***REMOVED******REMOVED******REMOVED*** High Utilization Warning

**Alert:** `ResilienceUtilizationHigh`

```bash
***REMOVED*** Check current utilization breakdown
curl http://localhost:8000/api/resilience/utilization/breakdown

***REMOVED*** View resource allocation
curl http://localhost:8000/api/resilience/resources
```

**Actions:**
1. Review which resources are constrained
2. Identify optimization opportunities
3. Consider capacity planning

***REMOVED******REMOVED******REMOVED*** Contingency Analysis Alerts

**Alert:** `ResilienceN1ContingencyFailed`

Single point of failure detected. If one resource fails, system cannot maintain service.

```bash
***REMOVED*** Run contingency analysis
curl -X POST http://localhost:8000/api/resilience/contingency/analyze

***REMOVED*** View vulnerable points
curl http://localhost:8000/api/resilience/contingency/vulnerabilities
```

**Actions:**
1. Identify single points of failure
2. Cross-train faculty for critical roles
3. Update fallback schedules

***REMOVED******REMOVED*** Recovery Procedures

***REMOVED******REMOVED******REMOVED*** Returning to Normal Operations

1. **Verify underlying issue is resolved**

2. **Gradually re-enable features**
   ```bash
   curl -X POST http://localhost:8000/api/resilience/recovery/start
   ```

3. **Monitor for 30 minutes** after each level decrease

4. **Document lessons learned**

***REMOVED******REMOVED******REMOVED*** Post-Incident Checklist

- [ ] Timeline documented
- [ ] Root cause identified
- [ ] Thresholds reviewed (need adjustment?)
- [ ] Runbook updated if needed
- [ ] Stakeholders debriefed

***REMOVED******REMOVED*** Configuration Reference

Settings in `backend/app/core/config.py`:

| Setting | Default | Description |
|---------|---------|-------------|
| `RESILIENCE_WARNING_THRESHOLD` | 0.70 | Yellow level trigger |
| `RESILIENCE_MAX_UTILIZATION` | 0.80 | Orange level trigger |
| `RESILIENCE_AUTO_ACTIVATE_DEFENSE` | True | Auto level transitions |
| `RESILIENCE_AUTO_SHED_LOAD` | True | Auto load shedding |

***REMOVED******REMOVED*** Related Alerts

- `HighCPUUsage`
- `HighMemoryUsage`
- `APIServiceDown`
- `DatabaseConnectionsHigh`

---

*Last Updated: December 2024*
*Framework Reference: docs/RESILIENCE_FRAMEWORK.md*
