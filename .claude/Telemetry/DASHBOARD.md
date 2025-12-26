# AI Infrastructure Weekly Dashboard Template

> **Week of**: [YYYY-MM-DD to YYYY-MM-DD]
> **Generated**: [YYYY-MM-DD HH:MM UTC]
> **Period**: [Week N of YYYY]
> **Baseline**: [First week tracked: YYYY-MM-DD]

---

## Executive Summary

### Key Highlights
- 📊 **Total Agent Invocations**: [N] ([±X%] vs last week)
- ✅ **Completion Rate**: [X.X%] ([±X.X%] vs target of 95%)
- 📚 **New Learnings Captured**: [N] ([±X] vs last week)
- 🧪 **Test Coverage**: [XX.X%] ([±X.X%] vs last week)
- 🚨 **Incidents**: [N] ([±X] vs last week)

### Status Indicators
| Metric | Status | Trend | Notes |
|--------|--------|-------|-------|
| Skill Success Rate | 🟢 Green | ↗️ Improving | Above 90% threshold |
| Learning Implementation | 🟡 Yellow | → Stable | 78% (below 80% target) |
| Incident Rate | 🟢 Green | ↘️ Decreasing | 1.2/week (down from 2.3) |
| Test Coverage | 🟢 Green | ↗️ Improving | +0.4% this week |
| Context Utilization | 🟡 Yellow | ↗️ Increasing | p95 at 85% (approaching 90% threshold) |

**Legend**:
- 🟢 **Green**: Meeting or exceeding targets
- 🟡 **Yellow**: Within acceptable range but needs monitoring
- 🔴 **Red**: Below threshold, action required
- ⚫ **Black**: Critical failure, immediate intervention

---

## 1. Skill Performance

### Top Skills by Usage

| Rank | Skill Name | Invocations | Success Rate | Avg Duration | Trend |
|------|------------|-------------|--------------|--------------|-------|
| 1 | systematic-debugger | 47 | 95.7% | 4m 32s | ↗️ +12 |
| 2 | constraint-preflight | 34 | 100.0% | 1m 18s | → +1 |
| 3 | test-writer | 28 | 92.9% | 3m 05s | ↘️ -5 |
| 4 | acgme-compliance | 19 | 100.0% | 2m 42s | ↗️ +4 |
| 5 | code-review | 15 | 93.3% | 5m 15s | → 0 |
| 6 | schedule-optimization | 12 | 91.7% | 8m 47s | ↗️ +3 |
| 7 | database-migration | 8 | 100.0% | 6m 22s | ↗️ +2 |
| 8 | security-audit | 6 | 100.0% | 7m 08s | → -1 |
| 9 | pr-reviewer | 5 | 100.0% | 4m 55s | → 0 |
| 10 | swap-management | 4 | 100.0% | 3m 38s | → +1 |

**Total Invocations**: 178 (+17 from last week, +10.6%)

### Skills with Errors

| Skill Name | Total Errors | Error Rate | Top Error Type | Action Taken |
|------------|--------------|------------|----------------|--------------|
| test-writer | 2 | 7.1% | AsyncIO event loop conflict | Updated skill prompt with async guidance |
| systematic-debugger | 2 | 4.3% | Context window saturation | Added context management tips |

**Total Skill Errors**: 4 (2.2% overall error rate, well below 5% threshold 🟢)

### Skill Performance Deep Dive

#### systematic-debugger
- **Invocations**: 47 (highest usage)
- **Success Rate**: 95.7% (45/47)
- **Median Duration**: 4m 32s (within target)
- **p95 Duration**: 12m 18s
- **Context Utilization**: p95 at 88% (approaching saturation)
- **Errors**: 2 (both due to context window hitting 95%)
- **Action Items**:
  - ✅ Add context management guidance to skill
  - ⏳ Consider splitting into sub-skills for large codebases

#### constraint-preflight
- **Invocations**: 34 (critical pre-commit gate)
- **Success Rate**: 100% ✅
- **Median Duration**: 1m 18s (excellent performance)
- **Notes**: No errors, consistent performance. Gold standard skill.

#### test-writer
- **Invocations**: 28
- **Success Rate**: 92.9% (26/28)
- **Errors**: 2 (AsyncIO event loop conflicts when generating async tests)
- **Action Items**:
  - ✅ COMPLETED: Updated skill with async test patterns (2025-12-24)
  - ⏳ Monitor for recurrence next week

---

## 2. Agent Performance

### Agent Activity Summary

| Agent | Invocations | Completion Rate | Rollback Rate | Median TTR | Tool Calls (avg) |
|-------|-------------|-----------------|---------------|------------|------------------|
| claude-sonnet-4.5 | 143 | 96.5% | 1.4% | 4m 12s | 18.3 |
| o1-pro | 12 | 100.0% | 0.0% | 8m 45s | 5.2 |
| claude-opus-4.5 | 8 | 100.0% | 0.0% | 6m 30s | 12.8 |

**Total Agent Tasks**: 163 (+15 from last week)

### Time to Resolution (TTR) Distribution

```
Percentile | Duration
-----------|----------
p50 (median) | 4m 12s  (target: <5m) ✅
p75          | 7m 35s
p90          | 11m 42s
p95          | 14m 18s (target: <15m) ✅
p99          | 22m 05s
max          | 28m 12s
```

### Rollback Analysis

**Total Rollbacks**: 2 (1.4% of tasks, well below 2% threshold 🟢)

| Date | Agent | Task | Reason | Recovery |
|------|-------|------|--------|----------|
| 2025-12-22 | claude-sonnet-4.5 | Database migration | Failed test after migration | Reverted migration, added test-first workflow |
| 2025-12-25 | claude-sonnet-4.5 | API refactor | Breaking change to existing endpoint | Rolled back, added deprecation path |

**Learnings Created**: 2 (LEARN-2025-043, LEARN-2025-044)

### Agent Task Types

| Task Type | Count | Success Rate | Avg Duration |
|-----------|-------|--------------|--------------|
| Debugging | 58 | 96.6% | 5m 22s |
| Testing | 32 | 93.8% | 3m 18s |
| Documentation | 24 | 100.0% | 2m 45s |
| Refactoring | 18 | 100.0% | 6m 12s |
| Feature Implementation | 12 | 91.7% | 12m 30s |
| Code Review | 10 | 100.0% | 4m 55s |
| Migration | 9 | 88.9% | 8m 08s |

---

## 3. Learning Capture

### Learning Velocity

```
Week 1 (Dec 5-11):   ████████ 8 entries
Week 2 (Dec 12-18):  ████████████ 12 entries
Week 3 (Dec 19-25):  ██████████ 10 entries
Week 4 (Dec 26-Jan 1): ██████████████ 14 entries  ← Current week

Trend: +75% increase over 4-week period
Average: 11 entries/week
```

### Learnings by Severity

| Severity | Count | % of Total | Implemented | Implementation Rate |
|----------|-------|------------|-------------|---------------------|
| 🔴 Critical | 3 | 21% | 3 | 100% ✅ |
| 🟡 Warning | 6 | 43% | 4 | 67% |
| ℹ️ Info | 5 | 36% | 3 | 60% |
| **Total** | **14** | **100%** | **10** | **71%** 🟡 |

**Target**: 80% implementation rate (currently at 71%, needs improvement)

### Learnings by Source

| Source | Count | Avg Time to Implementation |
|--------|-------|----------------------------|
| Incident | 4 | 1.2 days ✅ |
| Observation | 6 | 4.5 days |
| Experiment | 2 | 6.0 days |
| User Feedback | 1 | 2.0 days |
| Code Review | 1 | 3.0 days |

**Insight**: Incident-driven learnings are implemented fastest (urgency bias).

### Recent High-Impact Learnings

| ID | Date | Summary | Status | Impact |
|----|------|---------|--------|--------|
| LEARN-2025-045 | Dec 26 | Calendar edge cases in ACGME validator | 🟢 Implemented | Prevented compliance violations |
| LEARN-2025-044 | Dec 25 | API breaking changes need deprecation path | 🟡 In Progress | Improved API stability |
| LEARN-2025-043 | Dec 22 | Database migrations require test-first approach | 🟢 Implemented | Eliminated migration rollbacks |
| LEARN-2025-042 | Dec 21 | Async test patterns for test-writer skill | 🟢 Implemented | Reduced test generation errors |

### Learnings Awaiting Implementation

| ID | Age (days) | Severity | Summary | Blocker |
|----|------------|----------|---------|---------|
| LEARN-2025-041 | 7 | Warning | Optimize schedule generation for large datasets | Requires solver refactor |
| LEARN-2025-038 | 12 | Info | Add resilience metrics to Grafana | Waiting on Prometheus exporter |
| LEARN-2025-035 | 18 | Warning | Improve swap auto-matcher precision | Needs domain expert review |

**Action**: Prioritize LEARN-2025-041 this week (aging, performance impact)

---

## 4. Code Quality Metrics

### Test Coverage

```
Subsystem       | Current | Last Week | Delta | Trend | Target
----------------|---------|-----------|-------|-------|-------
Backend         | 87.3%   | 86.9%     | +0.4% | ↗️    | >85% ✅
Frontend        | 78.5%   | 78.2%     | +0.3% | ↗️    | >75% ✅
MCP Server      | 82.1%   | 81.8%     | +0.3% | ↗️    | >80% ✅
Overall Average | 82.6%   | 82.3%     | +0.3% | ↗️    | >80% ✅
```

**Trend**: Steady improvement (+0.3% per week average over 4 weeks)

### Coverage by Component

| Component | Coverage | Delta | Files with <80% Coverage |
|-----------|----------|-------|---------------------------|
| Scheduling Engine | 94.2% | +0.2% | 0 |
| ACGME Validator | 96.8% | +1.2% | 0 |
| Resilience Framework | 89.4% | +0.8% | 2 |
| Swap System | 91.3% | -0.1% | 1 |
| API Routes | 85.7% | +0.5% | 5 |
| Controllers | 82.1% | +0.3% | 8 |
| Frontend Components | 78.5% | +0.3% | 12 |

**Action Items**:
- ⏳ Add tests for 2 resilience framework files (target: 95%)
- ⏳ Improve API route coverage (5 files below 80%)

### Linting & Type Coverage

```
Backend (Python):
├─ Lint Errors:     0      (target: 0) ✅
├─ Lint Warnings:   3      (target: <10) ✅
├─ Type Coverage:   98.7%  (target: 100%) 🟡
└─ Docstring Coverage: 96.4%  (target: 100%) 🟡

Frontend (TypeScript):
├─ Lint Errors:     0      (target: 0) ✅
├─ Lint Warnings:   7      (target: <10) ✅
├─ Type Coverage:   100.0% (target: 100%) ✅
└─ Strict Mode:     ✅ Enabled
```

**Action Items**:
- ⏳ Add type hints to 8 Python functions (backend/app/services/legacy.py)
- ⏳ Add docstrings to 12 public functions

### Security Findings

```
Category        | Open | Resolved This Week | Total Resolved
----------------|------|--------------------|-----------------
Critical        | 0    | 0                  | 3
High            | 0    | 1 ✅               | 8
Medium          | 0    | 2 ✅               | 15
Low             | 0    | 0                  | 22
Info            | 2    | 1                  | 18
```

**Resolved This Week**:
- ✅ SQL injection vulnerability in legacy query (backend/app/api/routes/legacy.py) - Migrated to SQLAlchemy ORM
- ✅ XSS risk in error messages (frontend/components/ErrorDisplay.tsx) - Added DOMPurify sanitization
- ✅ Sensitive data in logs (backend/app/core/logging.py) - Implemented log scrubbing

**Open Info-Level**:
- ℹ️ Outdated dependency: `requests` 2.28 → 2.31 (no known CVEs, low priority)
- ℹ️ Missing CSP header on `/health` endpoint (non-sensitive, accepted risk)

---

## 5. Incident & Error Tracking

### Incident Summary

**Total Incidents This Week**: 2 (down from 5 last week, -60% 🟢)

| Date | Severity | Component | Summary | MTTR | Status |
|------|----------|-----------|---------|------|--------|
| Dec 23 | 🟡 Warning | API | Rate limiter false positives for authenticated users | 45m | ✅ Resolved |
| Dec 26 | 🔴 Critical | Scheduler | ACGME validator month-boundary bug | 90m | ✅ Resolved |

### Incident Rate Trend

```
4 weeks ago:  ████████ 8 incidents
3 weeks ago:  ██████ 6 incidents
2 weeks ago:  █████ 5 incidents
Last week:    ████ 4 incidents
This week:    ██ 2 incidents  ← 50% reduction

Trend: Decreasing (-75% over 4 weeks) ✅
```

### Mean Time to Resolution (MTTR)

```
Severity    | Median MTTR | p95 MTTR | Target  | Status
------------|-------------|----------|---------|--------
Critical    | 90m         | 90m      | <120m   | ✅ Met
Warning     | 45m         | 45m      | <60m    | ✅ Met
Info        | N/A         | N/A      | <24h    | N/A
```

### Repeat Incidents

**Repeat Rate**: 0% (0 of 2 incidents this week were repeats) ✅

**Note**: LEARN-2025-045 (ACGME month-boundary bug) was a new discovery, not a repeat. Comprehensive fix applied with 15 new edge case tests.

### Root Cause Analysis

| Root Cause Category | Count | % of Total | Trend |
|---------------------|-------|------------|-------|
| Logic Errors | 1 | 50% | → Stable |
| Configuration Issues | 1 | 50% | → Stable |
| Dependency Issues | 0 | 0% | ↘️ Decreasing |
| Performance | 0 | 0% | → Stable |

---

## 6. Context & Resource Utilization

### Context Window Usage

```
Percentile | Utilization | Threshold | Status
-----------|-------------|-----------|--------
p50        | 62%         | N/A       | ✅ Normal
p75        | 78%         | N/A       | ✅ Normal
p90        | 85%         | 80%       | 🟡 Above threshold
p95        | 88%         | 90%       | 🟡 Approaching limit
p99        | 94%         | 95%       | 🔴 Near saturation
max        | 97%         | 100%      | 🔴 Critical
```

**Alert**: 3 tasks hit >90% context utilization this week (up from 1 last week)

**Action Items**:
- ⏳ Add context management to systematic-debugger skill
- ⏳ Implement sub-agent handoff for large codebases
- ⏳ Monitor for task complexity increase

### Tool Call Distribution

```
Percentile | Calls per Task | Threshold | Status
-----------|----------------|-----------|--------
p50        | 12             | N/A       | ✅ Normal
p75        | 24             | N/A       | ✅ Normal
p90        | 38             | 50        | ✅ Below threshold
p95        | 47             | 100       | ✅ Below threshold
p99        | 68             | 200       | ✅ Below threshold
max        | 89             | 500       | ✅ Well below limit
```

**Note**: No tool call loops detected this week ✅

### MCP Tool Performance

| Tool Name | Calls | Success Rate | p50 Latency | p95 Latency | SLA |
|-----------|-------|--------------|-------------|-------------|-----|
| validate_schedule | 28 | 100.0% | 0.8s | 1.6s | <2s ✅ |
| find_swap_candidates | 12 | 100.0% | 1.2s | 2.1s | <3s ✅ |
| calculate_utilization | 45 | 100.0% | 0.3s | 0.6s | <1s ✅ |
| detect_conflicts | 34 | 97.1% | 0.5s | 1.1s | <2s ✅ |

**Note**: `detect_conflicts` had 1 timeout (3.2s) on large dataset. Investigating optimization.

---

## 7. Alerts & Anomalies

### Alerts Triggered This Week

| Date | Metric | Current Value | Threshold | Severity | Resolution |
|------|--------|---------------|-----------|----------|------------|
| Dec 26 | `ai_context_window_utilization_percent` p95 | 88% | >85% | 🟡 Warning | Monitoring, will add context mgmt |
| Dec 24 | `ai_incident_repeat_rate` | 12.5% | >10% | 🟡 Warning | False positive (resolved as new issue) |

**Total Alerts**: 2 (1 actionable, 1 false positive)

### Anomalies Detected (SPC Rules)

| Metric | Anomaly Type | Details | Action |
|--------|--------------|---------|--------|
| `systematic-debugger` context usage | Upward trend | 8 consecutive increases (Rule 2) | Added to skill monitoring list |

**Note**: Using Western Electric SPC rules. Rule 2 = 8 consecutive points on same side of centerline.

---

## 8. META_UPDATER Activity

### Skill Updates This Week

| Skill | Update Type | Trigger | Status |
|-------|-------------|---------|--------|
| test-writer | Prompt enhancement | LEARN-2025-042 (AsyncIO patterns) | ✅ Deployed |
| systematic-debugger | Guardrail addition | Context saturation alerts | ⏳ In Review |
| constraint-preflight | Checklist expansion | LEARN-2025-045 (Calendar edge cases) | ✅ Deployed |

### Learning Mining Analysis

**Learnings Scanned**: 44 total (14 new this week)
**Patterns Identified**: 3
1. **Calendar edge cases**: Recurring theme in scheduling validators (5 learnings)
   - **Action**: Created comprehensive calendar test suite (DONE ✅)
2. **Async test patterns**: 3 learnings about AsyncIO in tests
   - **Action**: Updated test-writer skill (DONE ✅)
3. **API stability**: 2 learnings about breaking changes
   - **Action**: Created API versioning guide (IN PROGRESS ⏳)

### Proposed Skill Changes (Next Week)

1. **Create new skill**: `api-versioning` (recurrent pattern, no dedicated skill)
   - **Confidence**: High (3 related learnings in 2 weeks)
   - **Effort**: Medium (2-3 hours)
   - **Impact**: Prevent API breaking changes

2. **Enhance skill**: `schedule-optimization` (performance learnings)
   - **Confidence**: Medium (1 learning, but high impact)
   - **Effort**: High (requires solver expertise)
   - **Impact**: 30% faster schedule generation for large datasets

3. **Deprecate skill**: None recommended

---

## 9. Week-over-Week Comparison

| Metric | This Week | Last Week | Delta | Trend |
|--------|-----------|-----------|-------|-------|
| Total Agent Invocations | 163 | 148 | +15 (+10.1%) | ↗️ |
| Completion Rate | 96.5% | 95.3% | +1.2% | ↗️ |
| Rollback Rate | 1.4% | 2.7% | -1.3% | ↗️ Improving |
| Median TTR | 4m 12s | 4m 45s | -33s (-11.6%) | ↗️ Faster |
| New Learnings | 14 | 10 | +4 (+40%) | ↗️ |
| Learning Implementation Rate | 71% | 73% | -2% | ↘️ Needs attention |
| Incidents | 2 | 4 | -2 (-50%) | ↗️ Improving |
| MTTR (Critical) | 90m | 110m | -20m (-18%) | ↗️ Faster |
| Test Coverage | 82.6% | 82.3% | +0.3% | ↗️ |
| Lint Errors | 0 | 0 | 0 | → Stable |

**Overall Trend**: 🟢 Positive momentum across most metrics

---

## 10. Action Items for Next Week

### High Priority (Complete by Friday)

- [ ] **Context Management**: Implement context window monitoring in systematic-debugger skill
  - **Owner**: META_UPDATER
  - **Effort**: 2 hours
  - **Impact**: Prevent context saturation errors

- [ ] **Learning Implementation**: Clear backlog of 4 "Warning" severity learnings
  - **Owner**: Human Tech Lead
  - **Effort**: 4 hours
  - **Impact**: Improve implementation rate to >80%

- [ ] **Coverage Improvement**: Add tests for 5 API routes below 80% coverage
  - **Owner**: test-writer skill
  - **Effort**: 3 hours
  - **Impact**: Boost overall coverage to 83%+

### Medium Priority (Next 2 weeks)

- [ ] **Create api-versioning skill**: Prevent API breaking changes
  - **Owner**: META_UPDATER
  - **Effort**: 3 hours
  - **Impact**: Reduce API-related incidents

- [ ] **Optimize detect_conflicts MCP tool**: Address 1 timeout on large dataset
  - **Owner**: Human Developer + schedule-optimization skill
  - **Effort**: 4 hours
  - **Impact**: Improve MCP tool reliability

- [ ] **Type hint cleanup**: Add type hints to 8 remaining functions
  - **Owner**: Automated (code-review skill)
  - **Effort**: 1 hour
  - **Impact**: Reach 100% type coverage

### Low Priority (Nice to have)

- [ ] **Grafana Integration**: Export AI metrics to Prometheus/Grafana
  - **Owner**: Human DevOps
  - **Effort**: 8 hours
  - **Impact**: Better visualization for non-technical stakeholders

- [ ] **Skill Marketplace Exploration**: Research cross-project learning sharing
  - **Owner**: Human Tech Lead
  - **Effort**: 4 hours
  - **Impact**: Long-term infrastructure improvement

---

## 11. Recommendations

### For META_UPDATER

1. **Prioritize Context Management**: Implement sub-agent handoff for tasks >80% context utilization
2. **Create api-versioning skill**: Clear pattern with 3 recent learnings
3. **Monitor systematic-debugger**: Upward trend in context usage (SPC Rule 2 violation)

### For Human Maintainers

1. **Clear Learning Backlog**: 4 "Warning" learnings aging >7 days, need implementation
2. **Review LEARN-2025-041**: Schedule optimization learning (12 days old, performance impact)
3. **Celebrate Wins**: 50% reduction in incidents, 75% reduction over 4 weeks

### For Program Director

1. **No Clinical Action Needed**: System reliability improving, ACGME compliance maintained
2. **FYI**: Calendar edge case bug discovered and fixed proactively (LEARN-2025-045)
3. **Future Enhancement**: Consider Grafana dashboards for at-a-glance monitoring

---

## 12. Trend Analysis (4-Week View)

### Skill Usage Growth
```
systematic-debugger:  35 → 42 → 38 → 47  (+34% over 4 weeks)
constraint-preflight: 28 → 31 → 33 → 34  (+21%)
test-writer:          22 → 25 → 33 → 28  (+27%)
```

**Insight**: systematic-debugger usage accelerating (debugging-heavy sprint?)

### Quality Metrics Trend
```
Test Coverage:        81.9% → 82.0% → 82.3% → 82.6%  (+0.7% total)
Incident Rate:        8 → 6 → 4 → 2  (-75% reduction)
Learning Velocity:    8 → 12 → 10 → 14  (+75% increase)
```

**Insight**: Virtuous cycle - more learnings → fewer incidents → higher coverage

### Efficiency Metrics
```
Median TTR:           5m 12s → 4m 58s → 4m 45s → 4m 12s  (-19% faster)
Rollback Rate:        3.8% → 3.2% → 2.7% → 1.4%  (-63% improvement)
```

**Insight**: Agents becoming more efficient and accurate over time

---

## Appendix: Raw Data

### Data Sources
- Event Log: `.claude/Telemetry/events.jsonl` (2,847 events this week)
- Learning Entries: `.claude/History/LEARN-*.md` (44 total, 14 new)
- Git Commits: 23 commits this week
- Test Coverage: Pytest (backend), Jest (frontend), combined report
- CI/CD: GitHub Actions logs

### Calculation Methods
- **Success Rate**: `successful_outcomes / total_invocations`
- **Median TTR**: `percentile(duration_seconds, 0.50)`
- **Implementation Rate**: `learnings_with_status_implemented / total_learnings`
- **Trend Indicators**: `(this_week - last_week) / last_week * 100`

### Thresholds & Targets
- Skill Success Rate: >90%
- Agent Completion Rate: >95%
- Rollback Rate: <2%
- Learning Implementation Rate: >80%
- Test Coverage: >85% backend, >75% frontend
- Incident Repeat Rate: <10%
- MTTR (Critical): <120 minutes

---

**Generated by**: META_UPDATER v2.1.0
**Next Dashboard**: [YYYY-MM-DD] (auto-generated weekly)
**Questions?** See `.claude/Telemetry/README.md`
