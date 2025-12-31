# MCP Confidence Framework

**Purpose**: Quantify confidence levels across MCP tool responses for reliability assessment
**Scope**: All 34+ MCP tools
**Version**: 1.0
**Last Updated**: 2025-12-31

---

## Overview

Each MCP tool response includes a `confidence_level` field (0.0 to 1.0) indicating the reliability of the result. This enables workflows to make informed decisions about whether to trust results, use fallbacks, or escalate for human review.

```
Confidence Factors:
├─ Data Quality (20%)
│  ├─ Completeness: % of required data available
│  ├─ Freshness: Age of underlying data (hours)
│  └─ Accuracy: Known data quality issues
│
├─ Tool Health (20%)
│  ├─ Execution Time: Within SLA or slow
│  ├─ Error Rate: % of requests failing recently
│  └─ Last Successful Run: When did it work last
│
├─ Algorithm Confidence (30%)
│  ├─ Model Certainty: Algorithm-specific certainty
│  ├─ Input Anomalies: Unusual data patterns
│  └─ Parameter Validity: Configuration appropriate
│
├─ Historical Accuracy (20%)
│  ├─ Prediction Accuracy: Against ground truth
│  ├─ False Positive Rate: Over-prediction of issues
│  └─ False Negative Rate: Under-detection of issues
│
└─ External Factors (10%)
   ├─ Data Staleness: > 24h old data
   ├─ Degraded Mode: Fallback algorithm
   └─ Partial Results: Some inputs missing
```

---

## Confidence Levels

### Level 0: No Confidence (0.0)

**When Used**:
- Tool failed/unavailable
- Result is placeholder
- Data completely unreliable
- Using degraded fallback algorithm

**User Action**:
- Don't trust result
- Escalate to human
- Retry operation

**Example**:
```json
{
  "result": null,
  "confidence_level": 0.0,
  "confidence_reason": "Tool unavailable - no data available",
  "recommendation": "Retry later or use manual process"
}
```

---

### Level 1: Very Low Confidence (0.1-0.25)

**When Used**:
- Tool slow/timeout, using cached data >24h old
- >50% of required input data missing
- Algorithm model uncertainty very high
- Known data quality issues affecting result
- Recent errors (>25% failure rate)

**User Action**:
- Treat with skepticism
- Escalate to human for decision
- Validate with alternative tool
- Do not use for critical decisions

**Example**:
```json
{
  "result": {...},
  "confidence_level": 0.12,
  "confidence_reason": "Using cached data 36 hours old",
  "factors": {
    "data_freshness": 0.0,
    "completeness": 0.3,
    "tool_health": 0.2
  },
  "recommendation": "Request fresh validation from coordinator"
}
```

---

### Level 2: Low Confidence (0.25-0.50)

**When Used**:
- Using cached data 12-24 hours old
- 25-50% of input data missing
- Tool slow but within timeout (degraded)
- Algorithm uncertainty moderate
- Tool failure rate 10-25%

**User Action**:
- Use with caution
- Preferably validate with second tool
- May use for minor decisions
- Log for trend analysis

**Example**:
```json
{
  "result": {...},
  "confidence_level": 0.38,
  "confidence_reason": "Cached data 18 hours old + 30% data missing",
  "factors": {
    "data_freshness": 0.5,
    "completeness": 0.7,
    "tool_health": 0.3,
    "algorithm_confidence": 0.5
  },
  "recommendation": "Validate with second tool before critical decision"
}
```

---

### Level 3: Moderate Confidence (0.50-0.75)

**When Used**:
- Fresh data (<6 hours old)
- 80%+ of input data available
- Tool performed normally
- Algorithm uncertainty within normal range
- Tool failure rate <5%

**User Action**:
- Reasonable to trust result
- OK for standard decisions
- Still recommend review for critical decisions
- Monitor for changes

**Example**:
```json
{
  "result": {...},
  "confidence_level": 0.62,
  "confidence_reason": "Fresh data, normal execution",
  "factors": {
    "data_freshness": 0.95,
    "completeness": 0.9,
    "tool_health": 0.8,
    "algorithm_confidence": 0.65
  },
  "recommendation": "Suitable for routine decision-making"
}
```

---

### Level 4: High Confidence (0.75-0.90)

**When Used**:
- Very fresh data (<2 hours old)
- 95%+ of input data available
- Tool fast + healthy
- Algorithm low uncertainty
- Tool failure rate <1%
- Validated against historical accuracy

**User Action**:
- Trust result
- Can use for important decisions
- Reasonable for autonomous execution
- Document decision for audit

**Example**:
```json
{
  "result": {...},
  "confidence_level": 0.83,
  "confidence_reason": "High-quality data, normal execution",
  "factors": {
    "data_freshness": 0.99,
    "completeness": 0.98,
    "tool_health": 0.95,
    "algorithm_confidence": 0.8
  },
  "recommendation": "Suitable for autonomous decision-making"
}
```

---

### Level 5: Very High Confidence (0.90-1.0)

**When Used**:
- Real-time data (<30 min old)
- Complete data (100%)
- Tool fast + very healthy
- Algorithm very high certainty
- Tool failure rate <0.1%
- Multiple validation sources agree
- Proven historical accuracy >95%

**User Action**:
- Full confidence in result
- Safe for autonomous execution
- Can be used for critical decisions
- Minimal human oversight needed

**Example**:
```json
{
  "result": {...},
  "confidence_level": 0.95,
  "confidence_reason": "Real-time data, multiple validations agree",
  "factors": {
    "data_freshness": 1.0,
    "completeness": 1.0,
    "tool_health": 0.98,
    "algorithm_confidence": 0.95,
    "cross_validation": 0.9
  },
  "recommendation": "Suitable for autonomous execution"
}
```

---

## Per-Tool Confidence Adjustments

### Scheduling Tools

**validate_schedule**:
- Base confidence: 0.90 (very reliable)
- Decrease by 0.1 if: Data >2h old
- Decrease by 0.15 if: Constraint engine degraded
- Increase by 0.05 if: Cross-validated

**detect_conflicts**:
- Base confidence: 0.85
- Decrease by 0.15 if: >10% assignments missing
- Decrease by 0.10 if: Tool slow (>1s)

**run_contingency_analysis**:
- Base confidence: 0.75 (computationally complex)
- Decrease by 0.20 if: Timeout (using cached)
- Decrease by 0.10 if: >25% personnel not analyzable

### Early Warning Tools

**detect_burnout_precursors**:
- Base confidence: 0.65 (early detection uncertain)
- Signal-dependent:
  - swap_requests: +0.10 (observable)
  - sick_calls: +0.05 (reportable)
  - preference_decline: -0.05 (subjective)

**run_spc_analysis**:
- Base confidence: 0.80
- Decrease by 0.10 if: <4 weeks history
- Increase by 0.05 if: >12 weeks history

**calculate_fire_danger_index**:
- Base confidence: 0.70 (multi-temporal)
- Decrease by 0.15 if: satisfaction data stale (>1 month)
- Decrease by 0.10 if: workload projection used

### Resilience Tools

**check_utilization_threshold**:
- Base confidence: 0.95 (simple calculation)
- Decrease by 0.05 if: Definitions mismatch
- Decrease by 0.10 if: Real-time data unavailable

**calculate_blast_radius**:
- Base confidence: 0.70 (graph analysis complex)
- Decrease by 0.15 if: Network incomplete
- Decrease by 0.10 if: Timeout (using cache)

**get_unified_critical_index**:
- Base confidence: 0.60 (aggregates multiple uncertain tools)
- Adjusted based on component confidences
- Formula: min(component_confidences) * 0.9 + mean(confidences) * 0.1

### Epidemiology Tools

**calculate_burnout_rt**:
- Base confidence: 0.55 (network analysis uncertain)
- Increase by 0.10 if: Network data recent (<7 days)
- Decrease by 0.15 if: Small sample size (<3 cases)

**simulate_burnout_contagion**:
- Base confidence: 0.50 (simulation inherently uncertain)
- Increase by 0.10 if: Validated parameters
- Decrease by 0.20 if: Major network changes

---

## Confidence Aggregation

When multiple tools feed into a decision, aggregate their confidence levels:

### Aggregation Strategies

**Strategy 1: Minimum (Conservative)**
```python
overall_confidence = min([tool1_confidence, tool2_confidence, tool3_confidence])
# Use when: All tools must be confident
# Example: Schedule validation (all checks must pass)
```

**Strategy 2: Weighted Average**
```python
overall_confidence = (
    tool1_confidence * weight1 +
    tool2_confidence * weight2 +
    tool3_confidence * weight3
) / (weight1 + weight2 + weight3)
# Use when: Some tools more important than others
# Example: Unified critical index
```

**Strategy 3: Harmonic Mean (Emphasis on Low Values)**
```python
overall_confidence = 3 / (1/conf1 + 1/conf2 + 1/conf3)
# Use when: Want to emphasize weak links
# Example: Safety-critical decision
```

**Strategy 4: Maximum (Optimistic)**
```python
overall_confidence = max([tool1_confidence, tool2_confidence, tool3_confidence])
# Use when: Any tool being confident is enough
# Example: Early warning detection (any signal matters)
```

### Implementation

```python
def aggregate_confidence(
    confidences: Dict[str, float],
    weights: Optional[Dict[str, float]] = None,
    method: str = "weighted_average",
) -> float:
    """Aggregate multiple confidence values."""

    if method == "minimum":
        return min(confidences.values())

    elif method == "maximum":
        return max(confidences.values())

    elif method == "weighted_average":
        if weights is None:
            weights = {k: 1.0 for k in confidences}

        total_weight = sum(weights.values())
        weighted_sum = sum(
            confidences[k] * weights.get(k, 0)
            for k in confidences
        )
        return weighted_sum / total_weight

    elif method == "harmonic_mean":
        n = len(confidences)
        return n / sum(1.0 / c for c in confidences.values() if c > 0)

    else:
        raise ValueError(f"Unknown aggregation method: {method}")
```

### Example: Compliance Check Aggregation

```python
compliance_components = {
    "acgme_80_hour": 0.95,
    "acgme_1_in_7": 0.92,
    "supervision_ratio": 0.88,
    "conflict_detection": 0.85,
    "spc_analysis": 0.70,
}

weights = {
    "acgme_80_hour": 0.3,      # Most critical
    "acgme_1_in_7": 0.2,
    "supervision_ratio": 0.2,
    "conflict_detection": 0.2,
    "spc_analysis": 0.1,        # Least critical
}

overall = aggregate_confidence(
    compliance_components,
    weights,
    method="weighted_average"
)
# Result: 0.89 (High confidence in compliance assessment)
```

---

## Confidence Decision Tree

Use this tree to determine whether to trust/use/escalate a result:

```
┌─ Confidence Level?
│
├─ 0.0 (No Confidence)
│  └─ Action: ESCALATE TO HUMAN
│     └─ Use fallback process
│
├─ 0.1-0.25 (Very Low)
│  └─ Action: REQUEST HUMAN REVIEW
│     ├─ Can't proceed autonomously
│     └─ Escalate to coordinator
│
├─ 0.25-0.50 (Low)
│  └─ Action: VALIDATE WITH SECOND TOOL
│     ├─ If second tool agrees (confidence > 0.75)
│     │  └─ Proceed with caution
│     └─ Else escalate to human
│
├─ 0.50-0.75 (Moderate)
│  └─ Action: PROCEED WITH LOGGING
│     ├─ OK for routine decisions
│     ├─ Document decision
│     └─ Monitor for issues
│
├─ 0.75-0.90 (High)
│  └─ Action: PROCEED (RECOMMENDED FOR HUMANS)
│     ├─ OK for autonomous execution
│     ├─ Monitor for feedback
│     └─ Trust result
│
└─ 0.90-1.0 (Very High)
   └─ Action: AUTONOMOUS EXECUTION
      ├─ Safe for critical decisions
      ├─ Minimal oversight needed
      └─ Full confidence in result
```

---

## Per-Workflow Confidence Thresholds

### Schedule Generation Workflow

```
Phase 1 (Pre-Generation):
├─ validate_schedule: Required >= 0.85
├─ detect_conflicts: Required >= 0.75
└─ If not met: Request manual review

Phase 2 (Contingency):
├─ run_contingency_analysis: Recommend >= 0.70
├─ calculate_blast_radius: Recommend >= 0.65
└─ If not met: Log warnings, continue

Phase 5 (Generator):
├─ Requires Phase 1-3 confidence >= 0.75 (weighted)
└─ If not met: Use simpler algorithm

Phase 6 (Validation):
├─ validate_schedule: Required >= 0.90
└─ If not met: Don't deploy
```

### Compliance Check Workflow

```
Minimum thresholds by rule:
├─ 80-Hour Rule: >= 0.85
├─ 1-in-7 Rest: >= 0.85
├─ Supervision Ratio: >= 0.80
├─ Conflict Detection: >= 0.75
└─ Advanced Metrics: >= 0.70

Overall compliance score:
├─ High confidence: >= 0.85 → Can deploy
├─ Medium confidence: 0.70-0.85 → Coordinator review
└─ Low confidence: < 0.70 → Request rerun/revalidation
```

### Swap Execution Workflow

```
Phase 1 (Validation): >= 0.80 required
Phase 2 (Candidates): >= 0.70 recommend
Phase 3 (Impact): >= 0.75 required
├─ If compliance fails: Block swap
└─ If impact fails: Manual review

Execution decision:
├─ All phases >= 0.75: Auto-execute (after mutual consent)
├─ Any phase < 0.75: Coordinator escalation
└─ Any critical < 0.80: Block execution
```

### Resilience Assessment Workflow

```
Phase 1 (Quick Status): >= 0.90 for alerts
Phase 2 (Contingency): >= 0.65 for planning
Phase 3 (Epidemiology): >= 0.60 for trend
Phase 4 (Analytics): >= 0.70 for insights
Phase 5 (Synthesis): >= 0.65 for overall index

Alerting thresholds:
├─ RED ALERT: Requires >= 0.85 confidence
├─ YELLOW ALERT: Requires >= 0.75 confidence
└─ INFO: Requires >= 0.60 confidence
```

---

## Confidence Transparency

Always include in responses:

```json
{
  "result": { ... },
  "confidence_level": 0.82,
  "confidence_grade": "HIGH",
  "confidence_factors": {
    "data_quality": 0.90,
    "tool_health": 0.85,
    "algorithm_certainty": 0.80,
    "historical_accuracy": 0.75,
    "external_factors": 0.80
  },
  "confidence_reason": "Fresh data, normal execution, proven accuracy",
  "potential_issues": [
    "Data updated 1.5 hours ago (slightly stale)",
    "One input parameter at default (not custom)"
  ],
  "recommendations": [
    "OK for autonomous decision",
    "Monitor for feedback"
  ],
  "confidence_documentation": {
    "methodology": "Weighted aggregation of 5 factors",
    "weights": {...},
    "calculation": "..."
  }
}
```

---

## Monitoring Confidence Trends

Track confidence metrics over time:

```python
confidence_metrics = {
    "tool_name": {
        "avg_confidence": 0.78,
        "min_confidence": 0.45,
        "max_confidence": 0.99,
        "std_deviation": 0.12,
        "trend": "improving",
        "last_30_days": {
            "high_confidence_pct": 65,  // >= 0.75
            "medium_confidence_pct": 25,  // 0.50-0.75
            "low_confidence_pct": 10,  // < 0.50
        }
    }
}
```

### Alert Conditions

```
ALERT: Tool average confidence dropping
├─ Trigger: 7-day average < (historical avg - 0.15)
├─ Action: Investigate tool health
└─ Review: Recent data quality changes

ALERT: High variance in confidence
├─ Trigger: std_deviation > 0.20
├─ Action: Inconsistent results detected
└─ Review: Tool parameters, data quality
```

---

## Examples

### Example 1: High-Confidence Schedule Validation

```json
{
  "tool": "validate_schedule",
  "result": {
    "is_compliant": true,
    "overall_compliance_rate": 0.98,
    "violations": []
  },
  "confidence_level": 0.94,
  "confidence_grade": "VERY_HIGH",
  "confidence_factors": {
    "data_freshness": 1.0,  // Real-time data
    "completeness": 0.99,   // All assignments present
    "tool_health": 0.98,    // Healthy, fast
    "algorithm_certainty": 0.90,  // Deterministic checks
    "historical_accuracy": 0.95   // 95% accuracy track record
  },
  "recommendation": "Safe for autonomous deployment"
}
```

### Example 2: Low-Confidence Contingency Analysis

```json
{
  "tool": "run_contingency_analysis_deep",
  "result": {
    "n1_failures": [...],
    "coverage_gaps": 12
  },
  "confidence_level": 0.42,
  "confidence_grade": "LOW",
  "confidence_factors": {
    "data_freshness": 0.7,   // Data 12h old
    "completeness": 0.6,     // 30% personnel data missing
    "tool_health": 0.3,      // Slow, timeout once
    "algorithm_certainty": 0.5,  // Graph analysis complex
    "historical_accuracy": 0.4   // Limited validation data
  },
  "issues": [
    "Tool timeout, using cached contingency from 12 hours ago",
    "30% of personnel assignments data unavailable",
    "Analysis slow (3.2 seconds vs 2.0s target)"
  ],
  "recommendation": "Validate with second tool or manual review before critical decision"
}
```

---

## References

- **MCP_TOOL_DEPENDENCY_GRAPH.md**: Tool availability affects confidence
- **WORKFLOW_ERROR_HANDLING.md**: Confidence degradation strategies
- **Individual tool documentation**: Tool-specific confidence adjustments

---

**Last Updated**: 2025-12-31
**Version**: 1.0
**Adopted**: All MCP tools
**Review Frequency**: Quarterly
