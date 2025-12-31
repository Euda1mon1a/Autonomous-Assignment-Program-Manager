# QUALITY GATES TEST SUITE - Validation & Confidence

> **Purpose:** Ensure SEARCH_PARTY probe outputs meet quality standards before synthesis
> **Created:** 2025-12-31
> **Focus:** Output validation, discrepancy detection, and confidence aggregation

---

## Overview

Quality gates are automated checks that prevent low-quality results from reaching synthesis, ensuring accuracy and consistency.

### Three-Tier Quality Framework

| Tier | Test | Responsibility | Failure Action |
|------|------|-----------------|-----------------|
| **1** | Output Validation | Probe-level format checks | Reject malformed output |
| **2** | Discrepancy Detection | Cross-probe consistency | Flag high variance |
| **3** | Confidence Aggregation | Synthesis-ready confidence | Block low-confidence results |

---

## Test 1: Probe Output Validation

### Objective
Validate that all probe outputs conform to expected schema before acceptance by orchestrator.

### Test Scenario

Deploy 10 probes on consistent target, validate each output independently.

### Setup

```yaml
Validation Layers:
  1. Schema validation (JSON structure)
  2. Type validation (field types correct)
  3. Range validation (values within bounds)
  4. Completeness (all required fields present)
  5. Semantic validation (results logically coherent)

Test Cases:
  - Valid output (should PASS)
  - Missing required field (should REJECT)
  - Wrong data type (should REJECT)
  - Out-of-range value (should REJECT)
  - Truncated/corrupted JSON (should REJECT)
  - Semantically inconsistent (should REJECT/FLAG)
```

### Execution Steps

1. **Define Output Schema**
   ```json
   {
     "probe_id": "string, required",
     "probe_name": "string, required",
     "target_path": "string, required",
     "execution_time_ms": "integer, >0, required",
     "findings": {
       "type": "object",
       "properties": {
         "security_issues": {
           "type": "array",
           "items": {
             "type": "object",
             "properties": {
               "severity": "enum: critical|high|medium|low",
               "description": "string",
               "line_number": "integer, >=0"
             },
             "required": ["severity", "description"]
           },
           "required": true
         },
         "performance_issues": { "type": "array" },
         "code_quality": { "type": "object" }
       },
       "required": ["security_issues", "performance_issues"]
     },
     "confidence_score": "number, 0.0-1.0, required",
     "coverage_percent": "number, 0.0-100.0, required",
     "timestamp": "ISO8601 string, required",
     "errors": {
       "type": "array",
       "items": "string"
     }
   }
   ```

2. **Create Test Probes**
   ```bash
   # Valid output
   ./test_generators/probe_output.sh --valid

   # Missing field
   ./test_generators/probe_output.sh --missing-field=confidence_score

   # Wrong type
   ./test_generators/probe_output.sh --wrong-type=confidence_score:string

   # Out of range
   ./test_generators/probe_output.sh --out-of-range=confidence_score:1.5

   # Corrupted JSON
   ./test_generators/probe_output.sh --corrupt-json

   # Semantically bad
   ./test_generators/probe_output.sh --semantic-error
   ```

3. **Deploy Validation Test**
   ```bash
   ./test_runners/quality_test.sh \
     --test=output_validation \
     --test-cases=10 \
     --schema=probe_output_schema.json \
     --log-rejections
   ```

4. **Verify Validation Results**

### Test Cases & Expected Results

#### Test Case 1: Valid Output

```json
{
  "probe_id": "probe_001",
  "probe_name": "SECURITY_SCANNER",
  "target_path": "/src/auth.py",
  "execution_time_ms": 2450,
  "findings": {
    "security_issues": [
      {
        "severity": "high",
        "description": "SQL injection vulnerability in query",
        "line_number": 42
      }
    ],
    "performance_issues": []
  },
  "confidence_score": 0.94,
  "coverage_percent": 87.3,
  "timestamp": "2025-12-31T10:15:30Z",
  "errors": []
}
```

**Expected:** ✓ PASS (all validations succeed)

#### Test Case 2: Missing Required Field

```json
{
  "probe_id": "probe_002",
  "probe_name": "SECURITY_SCANNER",
  "target_path": "/src/auth.py",
  "execution_time_ms": 2450,
  "findings": { ... },
  // Missing: confidence_score
  "coverage_percent": 87.3,
  "timestamp": "2025-12-31T10:15:30Z"
}
```

**Expected:** ✗ REJECT
**Error:** `VALIDATION_ERROR: Missing required field 'confidence_score'`

#### Test Case 3: Wrong Data Type

```json
{
  ...
  "confidence_score": "0.94",  // Should be number, not string
  ...
}
```

**Expected:** ✗ REJECT
**Error:** `VALIDATION_ERROR: Field 'confidence_score' should be number, got string`

#### Test Case 4: Out of Range

```json
{
  ...
  "confidence_score": 1.5,  // Should be 0.0-1.0
  "coverage_percent": 150   // Should be 0.0-100.0
  ...
}
```

**Expected:** ✗ REJECT
**Error:** `VALIDATION_ERROR: 'confidence_score' out of range [0.0, 1.0]: 1.5`

#### Test Case 5: Corrupted JSON

```
{
  "probe_id": "probe_005",
  "findings": [CORRUPTED, data],
  "confidence_score": 0.88,
```

**Expected:** ✗ REJECT
**Error:** `VALIDATION_ERROR: Malformed JSON - unexpected token`

#### Test Case 6: Semantic Inconsistency

```json
{
  ...
  "coverage_percent": 0.0,  // Claims no coverage
  "findings": {
    "security_issues": [
      { "severity": "critical", "description": "..." }  // But found critical issue
    ]
  },
  "confidence_score": 0.95  // High confidence despite no coverage
}
```

**Expected:** ⚠ FLAG
**Warning:** `SEMANTIC_WARNING: Findings detected but coverage is 0%`
**Severity:** HIGH (probe working contradicts coverage)

### Success Criteria

- [ ] Valid outputs: 100% pass
- [ ] Missing fields: 100% rejected
- [ ] Wrong types: 100% rejected
- [ ] Out of range: 100% rejected
- [ ] Corrupted JSON: 100% rejected
- [ ] Semantic issues: 100% flagged

### Expected Output

```
=== QUALITY TEST 1: OUTPUT VALIDATION ===

Schema: probe_output_schema.json
Test Cases: 10

Results:
  Valid (1): PASS ✓
  Missing field (1): REJECT ✓
  Wrong type (1): REJECT ✓
  Out of range (1): REJECT ✓
  Corrupted JSON (1): REJECT ✓
  Semantic error (1): FLAG ✓
  Valid edge cases (4): PASS ✓

Validation Metrics:
  Pass Rate: 100% (5/5 valid)
  Rejection Rate: 100% (5/5 invalid)
  False Positives: 0
  False Negatives: 0

Coverage:
  Schema coverage: 100%
  Edge cases: 4/4
  Error paths: 5/5

TEST_PASS: Quality gates correctly reject/accept outputs
```

---

## Test 2: Discrepancy Detection

### Objective
Detect and flag high variance across probes, indicating inconsistent analysis or data quality issues.

### Test Scenario

Deploy 10 probes on same target; measure output consistency and flag high discrepancies.

### Setup

```yaml
Discrepancy Metrics:
  1. Finding variance: Do all probes agree on findings?
  2. Confidence variance: Do probes have similar confidence?
  3. Coverage variance: Do probes cover similar code areas?
  4. Severity distribution: Do probes rate severity similarly?

Thresholds:
  Finding agreement: >80% for critical/high
  Confidence std dev: <0.15 (acceptable spread)
  Coverage agreement: ±10% acceptable
  Severity disagreement: <20% for same finding

Test Patterns:
  - Consistent probes (should pass)
  - One outlier probe (should flag)
  - Two conflicting groups (should escalate)
  - Complete disagreement (should reject)
```

### Execution Steps

1. **Deploy Consistent Probes**
   ```bash
   ./test_runners/quality_test.sh \
     --test=discrepancy_detection \
     --probes=10 \
     --target=consistent_target \
     --scenario=all_consistent \
     --measure-variance
   ```

2. **Deploy with One Outlier**
   ```bash
   # Probe 1-9: Normal analysis
   # Probe 10: Gives wildly different results
   ./test_runners/quality_test.sh \
     --test=discrepancy_detection \
     --probes=10 \
     --target=consistent_target \
     --scenario=one_outlier \
     --outlier_probe=10
   ```

3. **Deploy with Conflicts**
   ```bash
   # Probes 1-5: Finding A is critical
   # Probes 6-10: Finding A is low
   ./test_runners/quality_test.sh \
     --test=discrepancy_detection \
     --probes=10 \
     --target=consistent_target \
     --scenario=conflicting_groups \
     --measure-disagreement
   ```

4. **Measure Metrics**

### Metric Definitions

#### Finding Agreement

```python
def calculate_finding_agreement(probe_findings: list[dict]) -> float:
    """Calculate what % of critical/high findings are reported by >80% of probes."""

    all_findings = {}  # finding_id -> list[probe_ids]

    for probe in probes:
        for finding in probe.findings:
            if finding.severity in ['critical', 'high']:
                finding_id = f"{finding.location}:{finding.type}"
                if finding_id not in all_findings:
                    all_findings[finding_id] = []
                all_findings[finding_id].append(probe.id)

    # Calculate agreement rate
    agreement_rate = sum(
        1 for f_ids in all_findings.values()
        if len(f_ids) >= len(probes) * 0.8  # >80% agreement
    ) / len(all_findings)

    return agreement_rate  # 0.0-1.0
```

#### Confidence Variance

```python
def calculate_confidence_variance(probe_confidences: list[float]) -> tuple[float, float]:
    """Calculate mean and std dev of confidence scores."""
    mean = np.mean(probe_confidences)
    std_dev = np.std(probe_confidences)
    return mean, std_dev
```

#### Coverage Agreement

```python
def calculate_coverage_agreement(probe_coverages: list[float]) -> tuple[float, float]:
    """Calculate if probes cover similar code percentage."""
    mean_coverage = np.mean(probe_coverages)
    max_deviation = max(abs(c - mean_coverage) for c in probe_coverages)

    # Acceptable if no probe deviates >10% from mean
    acceptable = max_deviation <= 10.0  # percentage points

    return mean_coverage, max_deviation, acceptable
```

### Expected Results

#### Scenario 1: All Consistent

```
=== DISCREPANCY TEST: ALL CONSISTENT ===

Probes: 10
Finding Agreement: 96% (excellent)
Confidence Mean: 0.923, Std Dev: 0.032 (very tight)
Coverage Mean: 87.2%, Max Deviation: 1.8% (excellent)

Discrepancy Analysis:
  Finding disagreements: 1/45 findings (2%)
  Severity disagreements: 0 (perfect agreement)
  Coverage outliers: 0
  Confidence outliers: 0

Flags: NONE
Status: CONSISTENT_ANALYSIS ✓
Action: Proceed to synthesis with high confidence
```

#### Scenario 2: One Outlier

```
=== DISCREPANCY TEST: ONE OUTLIER ===

Probes: 10
Outlier Detected: probe_10

Comparison (Probes 1-9 vs Probe 10):
  Finding Agreement: 78% (acceptable, but low)
  Confidence:
    Probes 1-9: Mean 0.92, Std Dev 0.025
    Probe 10: 0.52 (OUTLIER: -0.40 from mean)
  Coverage:
    Probes 1-9: 87.2% ±1.8%
    Probe 10: 42.1% (OUTLIER: -45.1 from mean)

Outlier Analysis:
  Probe 10 confidence: 0.52 (>2 std dev from mean)
  Probe 10 coverage: 42.1% (>2 std dev from mean)
  Likely cause: Probe timeout, partial analysis, or target format issue

Recommendation:
  Flag probe_10 as unreliable (low confidence, partial coverage)
  Weight: 0.2 (vs 1.0 for other probes)
  Proceed with synthesis, but note outlier in report

Status: OUTLIER_DETECTED ⚠
Action: Downweight probe_10, continue synthesis
```

#### Scenario 3: Conflicting Groups

```
=== DISCREPANCY TEST: CONFLICTING GROUPS ===

Probes: 10
Groups Detected: 2 (5 probes each)

Group A (Probes 1-5):
  Key Finding: SQL injection in query() at line 42
  Severity: CRITICAL (5/5 agree)
  Confidence: 0.96 ± 0.03

Group B (Probes 6-10):
  Key Finding: SQL injection severity is MEDIUM (not critical)
  Severity: MEDIUM (5/5 agree)
  Confidence: 0.88 ± 0.05

Disagreement Analysis:
  Finding: Same (SQL injection detected)
  Severity: DISAGREEMENT (critical vs medium)
  Agreement: 50% (unacceptable)
  Std Dev: 0.18 (high variance)

Root Cause Hypothesis:
  Group B may be using older pattern database
  OR analyzing different code paths
  OR missing context

Recommendation:
  ESCALATE to human review
  Cannot automatically resolve Group A/B conflict
  Provide both analyses to human decision-maker

Status: CONFLICTING_ANALYSIS ✗
Action: Flag for human review, don't synthesize without approval
```

### Success Criteria

- [ ] Consistent scenario: 100% pass without flags
- [ ] Outlier scenario: Correctly identifies and downweights outlier
- [ ] Conflicting scenario: Escalates conflict for human review
- [ ] No false positives (legitimate variance not flagged)
- [ ] No false negatives (real conflicts detected)

### Expected Output

```
=== QUALITY TEST 2: DISCREPANCY DETECTION ===

Scenario 1 (Consistent):
  Detection Result: NO DISCREPANCY ✓
  Test Status: PASS

Scenario 2 (Outlier):
  Detection Result: OUTLIER DETECTED ⚠
  Outlier: probe_10 (confidence 0.52 vs mean 0.92)
  Test Status: PASS (correctly identified)

Scenario 3 (Conflicts):
  Detection Result: CONFLICTING GROUPS ✗
  Group A vs B: Severity disagreement (critical vs medium)
  Test Status: PASS (correctly escalated)

Overall Test Results:
  Consistent detection: ✓
  Outlier detection: ✓
  Conflict detection: ✓
  False positives: 0
  False negatives: 0

TEST_PASS: Discrepancy detection working correctly
```

---

## Test 3: Confidence Aggregation

### Objective
Validate that confidence scores are correctly aggregated across probes to create synthesis-ready confidence level.

### Test Scenario

Test multiple aggregation strategies and ensure final confidence reflects true quality.

### Setup

```yaml
Aggregation Strategies:
  1. Simple average: (c1 + c2 + ... + c10) / 10
  2. Weighted average: sum(ci * wi) where wi based on coverage/speed
  3. Conservative (min): Uses lowest confidence
  4. Robust (median): Uses median to reduce outlier impact
  5. Consensus-based: Only count >80% agreement

Quality Factors:
  - Finding agreement rate (higher = more confident)
  - Probe execution success rate
  - Coverage amount
  - Execution speed (fast might = incomplete)
  - Outlier presence
```

### Execution Steps

1. **Deploy Probes with Varied Quality**
   ```bash
   # Probe 1-3: High quality (95% confidence)
   # Probe 4-6: Medium quality (85% confidence)
   # Probe 7-9: Low quality (70% confidence)
   # Probe 10: Outlier (50% confidence)

   ./test_runners/quality_test.sh \
     --test=confidence_aggregation \
     --probes=10 \
     --quality-distribution=varied \
     --test-all-strategies
   ```

2. **Calculate Aggregate Confidence**
   ```python
   probe_confidences = [0.95, 0.96, 0.94, 0.85, 0.84, 0.86, 0.70, 0.72, 0.68, 0.50]

   # Strategy 1: Simple Average
   simple_avg = np.mean(probe_confidences)  # 0.80

   # Strategy 2: Weighted (by coverage * speed)
   weights = [1.0, 1.0, 0.95, 0.90, 0.85, 0.88, 0.70, 0.65, 0.60, 0.30]
   weighted_avg = np.average(probe_confidences, weights=weights)  # 0.82

   # Strategy 3: Conservative (minimum)
   conservative = min(probe_confidences)  # 0.50

   # Strategy 4: Robust (median)
   robust = np.median(probe_confidences)  # 0.80

   # Strategy 5: Consensus (>80% agreement)
   agreements = [c for c in probe_confidences if abs(c - np.median(probe_confidences)) < 0.15]
   consensus = len(agreements) / len(probe_confidences)  # 0.8 (80%)
   ```

3. **Compare Strategies**

### Strategy Comparison

| Strategy | Result | Pros | Cons | Use Case |
|----------|--------|------|------|----------|
| **Simple Average** | 0.80 | Easy to compute | Affected by outliers | General purpose |
| **Weighted** | 0.82 | Considers quality factors | More computation | Recommended |
| **Conservative** | 0.50 | Safe, prevents overconfidence | Too pessimistic | Critical systems |
| **Robust (Median)** | 0.80 | Outlier-resistant | Ignores weak probes | Mixed teams |
| **Consensus** | 0.80 | Reflects agreement | Less granular | Group decisions |

### Success Criteria

- [ ] Simple average correctly computes mean
- [ ] Weighted average correctly applies weights
- [ ] Conservative doesn't overestimate
- [ ] Robust handles outliers well
- [ ] Consensus reflects agreement
- [ ] Final confidence >= 0.70 (acceptable) or <= 0.60 (reject)
- [ ] Outliers properly downweighted

### Expected Output

```
=== QUALITY TEST 3: CONFIDENCE AGGREGATION ===

Probe Confidences:
  Probe 1-3: [0.95, 0.96, 0.94] (high)
  Probe 4-6: [0.85, 0.84, 0.86] (medium)
  Probe 7-9: [0.70, 0.72, 0.68] (low)
  Probe 10: [0.50] (outlier)

Aggregation Results:

  1. Simple Average:
     Result: 0.80
     Quality: GOOD (>0.70)
     Status: ✓ PASS

  2. Weighted Average:
     Weights: [1.0, 1.0, 0.95, 0.90, ...]
     Result: 0.82
     Quality: GOOD (>0.70)
     Status: ✓ PASS

  3. Conservative (Min):
     Result: 0.50
     Quality: MARGINAL (0.50 = borderline)
     Status: ⚠ FLAG (consider rejection)

  4. Robust (Median):
     Result: 0.80
     Quality: GOOD (>0.70)
     Status: ✓ PASS

  5. Consensus:
     Agreement: 80% of probes >0.15 from median
     Result: 0.80
     Quality: GOOD (>0.70)
     Status: ✓ PASS

Recommended Strategy: WEIGHTED AVERAGE
  Rationale: Accounts for probe quality variation
  Result: 0.82 confidence
  Synthesis Readiness: APPROVED

Quality Decision Matrix:
  ┌─ 0.90+: Approve immediately (very confident)
  ├─ 0.70-0.89: Approve with standard review (good)
  ├─ 0.60-0.69: Flag for manual review (marginal)
  └─ <0.60: Reject (too uncertain)

Final Recommendation:
  Aggregate Confidence: 0.82 (weighted)
  Decision: APPROVE FOR SYNTHESIS
  Notes: Outlier (probe_10) downweighted correctly
         Overall agreement good across groups

TEST_PASS: Confidence aggregation working correctly
```

---

## Running Quality Gate Tests

### Run All Quality Tests

```bash
./test_runners/quality_suite.sh --all
```

### Run Individual Test

```bash
./test_runners/quality_test.sh --test=output_validation
./test_runners/quality_test.sh --test=discrepancy_detection
./test_runners/quality_test.sh --test=confidence_aggregation
```

### Integration with SEARCH_PARTY

```python
# In orchestrator/synthesizer
from quality_gates import (
    validate_probe_output,
    detect_discrepancies,
    aggregate_confidence
)

for probe_result in probe_results:
    # Gate 1: Validate output
    try:
        validate_probe_output(probe_result, schema=PROBE_OUTPUT_SCHEMA)
    except ValidationError as e:
        logger.warning(f"Probe {probe_result.id} rejected: {e}")
        continue  # Skip this probe

    # Gate 2: Detect discrepancies
    if detect_discrepancies(all_results):
        logger.warning("High variance detected, flagging for review")

    # Gate 3: Aggregate confidence
    final_confidence = aggregate_confidence(
        [r.confidence for r in all_results],
        strategy="weighted"
    )

    if final_confidence < 0.60:
        logger.error("Confidence too low, rejecting synthesis")
        return None

    # All gates passed, proceed to synthesis
    return synthesize(filtered_results)
```

---

## Monitoring Quality Metrics

### Dashboard Metrics

```
Quality Gates Dashboard:
┌─ Output Validation
│  ├─ Acceptance Rate: 94.2%
│  ├─ Rejection Rate: 5.8%
│  └─ Most Common Error: Type mismatch
├─ Discrepancy Detection
│  ├─ Consistent Analyses: 87%
│  ├─ Flagged Outliers: 10%
│  └─ Escalated Conflicts: 3%
└─ Confidence Aggregation
   ├─ Mean Confidence: 0.82
   ├─ Low Confidence (<0.70): 5%
   └─ Recommended Strategy: Weighted Avg
```

---

**Last Updated:** 2025-12-31
**Status:** ACTIVE
