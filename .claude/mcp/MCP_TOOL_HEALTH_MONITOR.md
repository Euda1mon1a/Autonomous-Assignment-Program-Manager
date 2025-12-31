# MCP Tool Health Monitor

**Purpose**: Continuously monitor health of all 34+ MCP tools with proactive alerting
**Scope**: Tool performance, availability, reliability, and resource usage
**Version**: 1.0
**Last Updated**: 2025-12-31

---

## Health Monitoring Overview

```
Health Status Polling (every 5 minutes)
  │
  ├─→ Tool Performance Metrics
  │   ├─ Execution time (latency)
  │   ├─ Success rate (% completing)
  │   └─ Error rate (% failing)
  │
  ├─→ Resource Usage
  │   ├─ API response time
  │   ├─ Database query time
  │   └─ Memory consumption estimate
  │
  ├─→ Circuit Breaker Status
  │   ├─ CLOSED: Normal operation
  │   ├─ OPEN: Failing, reject requests
  │   └─ HALF_OPEN: Testing recovery
  │
  ├─→ Dependency Health
  │   ├─ API availability
  │   ├─ Database connectivity
  │   └─ Required services
  │
  └─→ Historical Trends
      ├─ 7-day performance
      ├─ Degradation detection
      └─ Capacity forecasting
```

---

## Health Check Protocols

### Per-Tool Health Checks (Category 1: Scheduling)

**validate_schedule**

```python
async def health_check_validate_schedule():
    """Check validate_schedule tool health."""

    health = ToolHealth(
        tool_name="validate_schedule",
        timestamp=datetime.now(),
    )

    # Test 1: Latency SLA
    start = time.time()
    try:
        result = await validate_schedule(
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
        )
        latency_ms = (time.time() - start) * 1000
        health.latency_ms = latency_ms
        health.latency_healthy = latency_ms < 100.0  # SLA: <100ms
    except asyncio.TimeoutError:
        health.latency_healthy = False
        health.last_error = "Timeout"

    # Test 2: Data Quality
    health.data_complete = len(result.assignments) > 0
    health.data_consistent = validate_schedule_consistency(result)

    # Test 3: Error Rate (from logs)
    health.error_rate = get_recent_error_rate("validate_schedule", window=3600)

    # Test 4: Dependency Check
    health.database_available = await test_db_connection()
    health.api_healthy = await test_backend_api()

    # Synthesize
    health.status = determine_status(health)  # HEALTHY / DEGRADED / CRITICAL
    health.confidence = calculate_health_score(health)  # 0-1

    return health


SCHEDULING_TOOLS = {
    "validate_schedule": {
        "latency_sla_ms": 100,
        "timeout_ms": 5000,
        "required_dependencies": ["database", "backend_api"],
        "health_check_interval_seconds": 300,
        "alert_threshold": 0.7,  # Alert if health < 0.7
    },
    "detect_conflicts": {
        "latency_sla_ms": 100,
        "timeout_ms": 5000,
        "required_dependencies": ["database"],
        "health_check_interval_seconds": 300,
        "alert_threshold": 0.65,
    },
    "run_contingency_analysis": {
        "latency_sla_ms": 2000,  # More complex
        "timeout_ms": 10000,
        "required_dependencies": ["database", "solver"],
        "health_check_interval_seconds": 600,
        "alert_threshold": 0.60,
    },
}
```

### Per-Tool Health Checks (Category 2: Early Warning)

**Early Warning Tools** - Lighter health checks (less critical path)

```python
EARLY_WARNING_TOOLS = {
    "detect_burnout_precursors": {
        "latency_sla_ms": 500,
        "timeout_ms": 5000,
        "required_dependencies": ["database"],
        "health_check_interval_seconds": 600,
        "alert_threshold": 0.50,  // Lower threshold, not critical
    },
    "run_spc_analysis": {
        "latency_sla_ms": 50,
        "timeout_ms": 2000,
        "required_dependencies": [],  // Pure calculation
        "health_check_interval_seconds": 600,
        "alert_threshold": 0.75,  // Statistical tool, high accuracy needed
    },
    "calculate_fire_danger_index": {
        "latency_sla_ms": 100,
        "timeout_ms": 2000,
        "required_dependencies": [],
        "health_check_interval_seconds": 600,
        "alert_threshold": 0.70,
    },
}
```

### Per-Tool Health Checks (Category 3: Resilience)

**Resilience Tools** - Medium complexity

```python
RESILIENCE_TOOLS = {
    "check_utilization_threshold": {
        "latency_sla_ms": 50,
        "timeout_ms": 1000,
        "required_dependencies": [],
        "health_check_interval_seconds": 300,
        "alert_threshold": 0.85,  // Critical, must be reliable
    },
    "run_contingency_analysis_deep": {
        "latency_sla_ms": 5000,
        "timeout_ms": 30000,
        "required_dependencies": ["solver", "database"],
        "health_check_interval_seconds": 600,
        "alert_threshold": 0.55,  // Expensive, accept lower health
    },
    "calculate_blast_radius": {
        "latency_sla_ms": 1000,
        "timeout_ms": 5000,
        "required_dependencies": ["graph_analysis"],
        "health_check_interval_seconds": 600,
        "alert_threshold": 0.60,
    },
}
```

---

## Health Status Definitions

### HEALTHY (Green)

**Criteria**:
- Latency < SLA
- Success rate > 95%
- Error rate < 1%
- No recent timeouts
- All dependencies available
- Health score > 0.85

**Action**: Monitor normally

```json
{
  "status": "HEALTHY",
  "color": "GREEN",
  "latency_ms": 52,
  "success_rate_pct": 98.5,
  "error_rate_pct": 0.2,
  "dependencies_ok": true,
  "health_score": 0.92,
  "last_check": "2025-12-31T15:05:00Z",
  "recent_issues": []
}
```

---

### DEGRADED (Yellow)

**Criteria**:
- Latency near SLA (80-100% of SLA)
- Success rate 85-95%
- Error rate 1-5%
- Recent timeout or error
- One dependency slow
- Health score 0.65-0.85

**Action**: Increased monitoring, prepare fallbacks

```json
{
  "status": "DEGRADED",
  "color": "YELLOW",
  "latency_ms": 180,  // Above SLA
  "success_rate_pct": 92.0,
  "error_rate_pct": 1.5,
  "dependencies_ok": "partially",  // Database slow
  "health_score": 0.71,
  "last_check": "2025-12-31T15:05:00Z",
  "recent_issues": [
    "Tool latency trending upward (200ms 1h ago, 180ms now)",
    "Occasional timeouts (2 in last hour)",
    "Database query time increased"
  ],
  "recommendations": [
    "Monitor next hour closely",
    "Be ready to trigger fallback algorithm",
    "Check database connection pool"
  ]
}
```

---

### CRITICAL (Red)

**Criteria**:
- Latency >> SLA (>150% of SLA)
- Success rate < 85%
- Error rate > 5%
- Repeated timeouts
- Dependencies unavailable
- Health score < 0.65

**Action**: Alert leadership, trigger fallbacks, escalate

```json
{
  "status": "CRITICAL",
  "color": "RED",
  "latency_ms": 3500,
  "success_rate_pct": 78.0,
  "error_rate_pct": 8.5,
  "dependencies_ok": false,  // Database unavailable
  "health_score": 0.42,
  "last_check": "2025-12-31T15:05:00Z",
  "recent_issues": [
    "Tool timeout 5 times in last 30 minutes",
    "Error rate spike (0.5% → 8.5%)",
    "Backend API connection failures"
  ],
  "alerts_sent": [
    {
      "recipient": "coordinator@hospital.edu",
      "severity": "CRITICAL",
      "timestamp": "2025-12-31T15:03:15Z"
    }
  ],
  "recommendations": [
    "IMMEDIATE: Switch to fallback algorithm",
    "IMMEDIATE: Check backend API status",
    "Check database for locks/slow queries",
    "Restart MCP server if manual recovery needed"
  ]
}
```

---

## Circuit Breaker Configuration

### Circuit Breaker States

Each tool has an associated circuit breaker:

```
┌──────────────────────────────────────┐
│         CIRCUIT BREAKER              │
│  (Prevents cascading failures)       │
└──────────────────────────────────────┘

CLOSED (Normal)
├─ Requests pass through
├─ Failures counted
└─ If failure_count > threshold → OPEN

OPEN (Failing)
├─ Requests rejected immediately
├─ Fast-fail (no timeout delay)
├─ Waiting period: 30-60 seconds
└─ After wait → HALF_OPEN

HALF_OPEN (Testing Recovery)
├─ One test request allowed
├─ If succeeds → CLOSED
└─ If fails → back to OPEN
```

### Tool Circuit Breaker Configuration

```python
CIRCUIT_BREAKER_CONFIG = {
    "validate_schedule": {
        "failure_threshold": 5,  // Open after 5 failures
        "failure_window_seconds": 60,  // In 60s window
        "timeout_seconds": 5.0,
        "half_open_timeout_seconds": 3.0,
        "half_open_max_calls": 1,  // Test 1 request
        "recovery_timeout_seconds": 30,  // Wait 30s before testing
        "exponential_backoff": True,  // Wait longer on repeated failures
    },

    "detect_conflicts": {
        "failure_threshold": 5,
        "failure_window_seconds": 60,
        "timeout_seconds": 5.0,
        ...
    },

    "run_contingency_analysis_deep": {
        "failure_threshold": 3,  // Lower threshold for expensive tool
        "failure_window_seconds": 120,  // Longer window
        "timeout_seconds": 30.0,  // Longer timeout
        "half_open_max_calls": 1,
        "recovery_timeout_seconds": 60,  // Longer recovery wait
        "exponential_backoff": True,
    },

    "detect_burnout_precursors": {
        "failure_threshold": 10,  // Higher threshold, not critical
        "failure_window_seconds": 300,  // Longer window
        "timeout_seconds": 5.0,
        ...
    },
}
```

### Circuit Breaker State Transitions

```python
class CircuitBreaker:
    """Track and enforce circuit breaker pattern."""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_failure_time = None
        self.open_time = None
        self.half_open_test_pending = False

    async def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""

        if self.state == "OPEN":
            if self._should_try_recovery():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker open. Retry in {self._time_until_retry()}s"
                )

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Reset on success."""
        self.state = "CLOSED"
        self.failure_count = 0

    def _on_failure(self):
        """Track failure."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = "OPEN"
            self.open_time = time.time()

    def _should_try_recovery(self) -> bool:
        """Check if ready for recovery test."""
        elapsed = time.time() - self.open_time
        return elapsed >= self.config.recovery_timeout_seconds

    def _time_until_retry(self) -> float:
        """Time until next recovery attempt."""
        elapsed = time.time() - self.open_time
        return self.config.recovery_timeout_seconds - elapsed
```

### Breaker Status Dashboard

```json
{
  "timestamp": "2025-12-31T15:05:00Z",
  "total_breakers": 34,
  "breaker_states": {
    "closed": 32,
    "open": 1,
    "half_open": 1
  },
  "breakers": [
    {
      "tool_name": "validate_schedule",
      "state": "CLOSED",
      "health": "HEALTHY",
      "failures_recent": 0,
      "last_failure": null
    },
    {
      "tool_name": "run_contingency_analysis_deep",
      "state": "OPEN",
      "health": "CRITICAL",
      "failures_recent": 5,
      "last_failure": "2025-12-31T15:03:00Z",
      "recovery_retry_in_seconds": 23,
      "fallback": "Using cached contingency data"
    },
    {
      "tool_name": "calculate_blast_radius",
      "state": "HALF_OPEN",
      "health": "DEGRADED",
      "test_pending": true,
      "test_deadline": "2025-12-31T15:06:00Z"
    }
  ]
}
```

---

## Tool Performance Dashboard

### Metrics Collected Per Tool

```
Real-time metrics (last 5 minutes):
├─ Current latency (milliseconds)
├─ Success rate (%)
├─ Error rate (%)
├─ Timeout count
├─ Circuit breaker state
└─ Health score (0-1)

Historical trends (7+ days):
├─ Average latency trend
├─ Success rate trend
├─ Error rate trend
├─ Capacity utilization
└─ Forecasted degradation
```

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────┐
│ MCP TOOL HEALTH DASHBOARD                               │
└─────────────────────────────────────────────────────────┘

System Overview:
├─ Total Tools: 34
├─ Healthy: 32 (GREEN)
├─ Degraded: 1 (YELLOW)
├─ Critical: 1 (RED)
└─ Health Score: 0.88 (HIGH)

┌─────────────────────────────────────────────────────────┐
│ Category: Scheduling Tools                              │
├─────────────────────────────────────────────────────────┤
│ Tool                    │ Status  │ Latency │ Health    │
│ validate_schedule       │ GREEN   │ 52ms    │ 0.92      │
│ detect_conflicts        │ GREEN   │ 48ms    │ 0.94      │
│ run_contingency...      │ RED     │ 15200ms │ 0.42 ⚠️   │
│ analyze_swap_candidates │ GREEN   │ 95ms    │ 0.87      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ Category: Early Warning Tools                           │
├─────────────────────────────────────────────────────────┤
│ Tool                    │ Status  │ Latency │ Health    │
│ detect_burnout_precurs  │ GREEN   │ 120ms   │ 0.81      │
│ run_spc_analysis        │ GREEN   │ 35ms    │ 0.95      │
│ calculate_fire_danger   │ GREEN   │ 78ms    │ 0.88      │
│ predict_burnout_mag     │ YELLOW  │ 280ms   │ 0.68 ⚠️   │
└─────────────────────────────────────────────────────────┘

[More categories...]

Recent Alerts:
1. [CRITICAL] run_contingency_analysis_deep timeout spike
   └─ 5 failures in 30 minutes, circuit breaker opened
2. [MEDIUM] predict_burnout_magnitude latency increase
   └─ Trending upward, monitor for degradation
3. [INFO] System health improving over past 24h
   └─ No new critical issues

Top Priority Actions:
1. Investigate contingency analysis timeout root cause
2. Monitor burnout prediction latency trend
3. Review recent database performance changes
```

### Detailed Tool View

```json
{
  "tool_name": "run_contingency_analysis_deep",
  "category": "resilience",
  "status": "CRITICAL",
  "health_score": 0.42,
  "health_grade": "F",

  "performance": {
    "latency_ms": {
      "current": 15200,
      "sla": 2000,
      "compliance": 0.13,
      "trend": "increasing"
    },
    "success_rate_pct": {
      "current": 78.0,
      "target": 95.0,
      "trend": "decreasing"
    },
    "error_rate_pct": {
      "current": 8.5,
      "target": 1.0,
      "trend": "increasing"
    }
  },

  "reliability": {
    "circuit_breaker_state": "OPEN",
    "failures_last_hour": 5,
    "timeouts_last_hour": 3,
    "last_error": "Solver timeout",
    "last_failure_time": "2025-12-31T15:03:00Z"
  },

  "dependencies": {
    "backend_api": "HEALTHY",
    "database": "DEGRADED",  // Slow queries
    "solver": "CRITICAL",  // Not responding
    "graph_library": "HEALTHY"
  },

  "recent_events": [
    {
      "time": "2025-12-31T15:03:00Z",
      "event": "FAILURE",
      "error": "Solver timeout after 30s",
      "recovery": "Using cached result"
    },
    {
      "time": "2025-12-31T15:02:00Z",
      "event": "TIMEOUT",
      "duration_seconds": 30.1,
      "expected_seconds": 5.0
    }
  ],

  "root_cause_analysis": {
    "primary_suspect": "Solver service unresponsive",
    "secondary_suspects": [
      "Database slow (N-1 queries timing out)",
      "Graph analysis library memory exhaustion"
    ]
  },

  "recommended_actions": [
    {
      "priority": 1,
      "action": "Check solver service health",
      "estimated_time": "5 minutes"
    },
    {
      "priority": 2,
      "action": "Review database connection pool",
      "estimated_time": "10 minutes"
    },
    {
      "priority": 3,
      "action": "Monitor memory usage during recovery",
      "estimated_time": "ongoing"
    }
  ],

  "fallback_status": {
    "fallback_available": true,
    "fallback_type": "use_cached_analysis",
    "fallback_age_hours": 6,
    "fallback_quality": "degraded"
  }
}
```

---

## Health Check Scheduling

### Polling Intervals Per Tool Category

```
HIGH PRIORITY (Every 5 minutes):
├─ validate_schedule
├─ check_utilization_threshold
└─ get_defense_level

MEDIUM PRIORITY (Every 10 minutes):
├─ detect_conflicts
├─ run_contingency_analysis
├─ calculate_blast_radius
└─ get_unified_critical_index

LOW PRIORITY (Every 30 minutes):
├─ Early warning tools
├─ Epidemiology tools
└─ Specialized analytics

BACKGROUND (Every 60 minutes):
├─ Historical accuracy tracking
├─ Capacity forecasting
└─ Trend analysis
```

### Health Check Execution

```python
async def run_health_checks():
    """Run all health checks on schedule."""

    while True:
        now = datetime.now()

        # High priority checks (5 min)
        if now.minute % 5 == 0:
            await check_tools(priority="HIGH")

        # Medium priority checks (10 min)
        if now.minute % 10 == 0:
            await check_tools(priority="MEDIUM")

        # Low priority checks (30 min)
        if now.minute % 30 == 0:
            await check_tools(priority="LOW")

        # Background tasks (hourly)
        if now.minute == 0:
            await update_historical_trends()
            await forecast_capacity()

        await asyncio.sleep(60)  // Check every minute
```

---

## Health Recovery Procedures

### Auto-Recovery Triggers

```
Trigger 1: Circuit Breaker HALF_OPEN Test
├─ Automatically test every 30-60 seconds
├─ If success → Close circuit, resume normal
├─ If failure → Reopen, wait longer
└─ Exponential backoff: 30s → 60s → 120s

Trigger 2: Timeout-Induced Fallback
├─ Tool exceeds timeout threshold
├─ Automatically switch to cached/simplified result
├─ Log event for monitoring
└─ Continue serving results (degraded)

Trigger 3: Error Rate Spike
├─ If error rate > 5% for 5 minutes
├─ Automatically engage degraded mode
├─ Reduce service scope (skip optional checks)
└─ Alert coordinator

Trigger 4: Dependency Recovery
├─ Monitor dependent service health
├─ If dependency recovers → Gradually increase traffic
├─ Ramp up calls: 10% → 25% → 50% → 100%
└─ Monitor for stability at each level
```

### Manual Recovery

```
If auto-recovery fails:
1. Coordinator notified with full diagnostics
2. Options presented:
   ├─ Restart MCP server
   ├─ Restart dependency service
   ├─ Switch to manual scheduling
   └─ Page on-call engineer

3. After fix:
   ├─ Verify circuit breaker recovers
   ├─ Run health check on all tools
   ├─ Validate dependent workflows
   └─ Log resolution for post-mortem
```

---

## Alerting Logic

### Alert Severity Mapping

```
CRITICAL (Page on-call):
├─ Tool health < 0.40
├─ >50% of schedules marked degraded
├─ Database unavailable > 10 minutes
└─ Multiple tools in CRITICAL state

HIGH (Email + Dashboard alert):
├─ Tool health 0.40-0.65
├─ Single tool in CRITICAL state
├─ Error rate > 10%
└─ Utilization > 85%

MEDIUM (Dashboard notification):
├─ Tool health 0.65-0.80
├─ Trending toward critical
├─ Single tool DEGRADED
└─ Error rate 5-10%

LOW (Log for review):
├─ Tool health > 0.80 but < 0.90
├─ Informational events
└─ Historical trend tracking
```

### Alert Destination Routing

```python
alert_routing = {
    "CRITICAL": {
        "recipients": ["on_call_engineer@hospital.pagerduty.com"],
        "channels": ["sms", "phone", "email"],
        "escalation_after_minutes": 5,
    },
    "HIGH": {
        "recipients": ["coordinators@hospital.edu"],
        "channels": ["email", "slack"],
        "summary_frequency": "immediate",
    },
    "MEDIUM": {
        "recipients": ["dashboard_subscribers"],
        "channels": ["dashboard"],
        "summary_frequency": "hourly",
    },
    "LOW": {
        "recipients": ["logs"],
        "channels": ["logging_system"],
        "summary_frequency": "daily",
    },
}
```

---

## Metrics Retention

```
Real-time metrics: Keep 5 minutes
├─ Current latency, success rate, errors
└─ Used for live dashboard

Recent history: Keep 7 days
├─ Hourly aggregations
├─ Used for trend detection
└─ Used for alert decisions

Long-term history: Keep 90 days
├─ Daily aggregations
├─ Used for capacity planning
└─ Used for historical accuracy tracking

Archive: Keep indefinitely
├─ Incident records
├─ Recovery analysis
└─ Historical benchmarks
```

---

## References

- **Circuit Breaker Pattern**: Standard resilience design
- **Health Check Protocol**: Industry best practices (AWS, GCP)
- **Metrics Reference**: Prometheus-style metrics

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Monitoring Tool**: Prometheus + Grafana
**Alert System**: PagerDuty + Slack + Email
