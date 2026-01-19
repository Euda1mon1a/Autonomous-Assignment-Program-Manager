# Experimental Analytics Platform Roadmap

> **Version:** 1.0 | **Created:** 2026-01-19 | **Status:** Planning
> **Primary Users:** Program Coordinators, PD/APD
> **Secondary Users:** Researchers, Data Scientists

---

## Executive Summary

This roadmap extends the existing Scheduling Laboratory (`/admin/scheduling`) into a comprehensive experimental analytics platform capable of:

1. **A/B Testing** - Compare scheduling algorithms with statistical rigor
2. **Survival Analysis** - Predict time-to-burnout and intervention timing
3. **Factorial Design** - Multi-factor schedule optimization experiments
4. **Hypothesis Testing** - Validate resilience interventions with proper statistics
5. **Predicted vs Actual** - Track model accuracy over time

### Current State Assessment

| Component | Status | Location |
|-----------|--------|----------|
| Scheduling Lab UI | ✅ Ready | `frontend/src/app/admin/scheduling/page.tsx` (1,792 lines) |
| A/B Testing Backend | ✅ Ready | `backend/app/experiments/ab_testing.py` (1,503 lines) |
| Chart Components | ✅ Partial | `frontend/src/components/admin/*Chart.tsx` |
| Statistical Libraries | ⚠️ Underutilized | scipy, statsmodels installed but ~30% used |
| Outcome Data Collection | ❌ Missing | Need to build from scratch |
| Bayesian Framework | ❌ Missing | Need PyMC + arviz |
| Survival Analysis | ❌ Missing | Need lifelines library |
| Effect Size Reporting | ❌ Missing | Need pingouin or wrapper functions |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXPERIMENTAL ANALYTICS PLATFORM                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    FRONTEND (Next.js 14)                            │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │    │
│  │  │ Experiment│ │ Survival  │ │ Factorial │ │ Predicted │           │    │
│  │  │ Dashboard │ │ Analysis  │ │  Design   │ │ vs Actual │           │    │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘           │    │
│  │        │             │             │             │                  │    │
│  │  ┌─────┴─────────────┴─────────────┴─────────────┴─────┐           │    │
│  │  │              Shared Chart Components                 │           │    │
│  │  │  (Recharts + Custom Statistical Visualizations)     │           │    │
│  │  └─────────────────────────┬───────────────────────────┘           │    │
│  └────────────────────────────┼────────────────────────────────────────┘    │
│                               │ TanStack Query                              │
│  ┌────────────────────────────┼────────────────────────────────────────┐    │
│  │                    BACKEND (FastAPI)                                │    │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐           │    │
│  │  │ /api/v1/  │ │ /api/v1/  │ │ /api/v1/  │ │ /api/v1/  │           │    │
│  │  │experiments│ │ survival  │ │ factorial │ │ outcomes  │           │    │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘           │    │
│  │        │             │             │             │                  │    │
│  │  ┌─────┴─────────────┴─────────────┴─────────────┴─────┐           │    │
│  │  │              Statistical Services Layer              │           │    │
│  │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │           │    │
│  │  │  │ Frequentist │ │  Bayesian   │ │  Survival   │    │           │    │
│  │  │  │ (scipy)     │ │  (PyMC)     │ │ (lifelines) │    │           │    │
│  │  │  └─────────────┘ └─────────────┘ └─────────────┘    │           │    │
│  │  └─────────────────────────────────────────────────────┘           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    DATA LAYER (PostgreSQL)                          │    │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │    │
│  │  │ experiments │ │  outcomes   │ │ predictions │ │  surveys    │   │    │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Collection Foundation

**Goal:** Build the outcome tracking infrastructure needed for all experiments.

> **Critical Insight:** You have historical Excel schedules but no outcome data. Before running any rigorous experiments, we need to collect baseline outcomes.

### 1.1 Outcome Data Model

```sql
-- Core outcome tracking tables

CREATE TABLE outcome_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resident_id UUID NOT NULL REFERENCES residents(id),
    event_type VARCHAR(50) NOT NULL,  -- 'burnout_survey', 'acgme_violation', 'sick_call', 'swap_request'
    event_date DATE NOT NULL,
    schedule_id UUID REFERENCES schedules(id),
    block_number INTEGER,

    -- Event-specific data (JSONB for flexibility)
    payload JSONB NOT NULL DEFAULT '{}',

    -- Metadata
    source VARCHAR(50) NOT NULL,  -- 'manual_entry', 'survey', 'system_detected', 'excel_import'
    recorded_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- For survival analysis: was this event censored?
    is_censored BOOLEAN DEFAULT FALSE,
    censoring_reason VARCHAR(100)
);

CREATE TABLE burnout_surveys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    resident_id UUID NOT NULL REFERENCES residents(id),
    survey_date DATE NOT NULL,

    -- Maslach Burnout Inventory subscales (industry standard)
    emotional_exhaustion DECIMAL(4,2),  -- 0-54 scale
    depersonalization DECIMAL(4,2),     -- 0-30 scale
    personal_accomplishment DECIMAL(4,2), -- 0-48 scale (inverse)

    -- Composite score for analysis
    burnout_score DECIMAL(5,2) GENERATED ALWAYS AS (
        (emotional_exhaustion / 54.0 * 100) +
        (depersonalization / 30.0 * 100) -
        (personal_accomplishment / 48.0 * 100)
    ) STORED,

    -- Risk classification
    burnout_risk VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN emotional_exhaustion >= 27 OR depersonalization >= 10 THEN 'HIGH'
            WHEN emotional_exhaustion >= 17 OR depersonalization >= 6 THEN 'MODERATE'
            ELSE 'LOW'
        END
    ) STORED,

    -- Link to schedule context
    schedule_id UUID REFERENCES schedules(id),
    current_rotation VARCHAR(100),
    weeks_on_rotation INTEGER,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE schedule_predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES schedules(id),
    prediction_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    model_version VARCHAR(50) NOT NULL,

    -- Predicted metrics
    predicted_coverage DECIMAL(5,2),
    predicted_violations INTEGER,
    predicted_fairness DECIMAL(5,4),
    predicted_burnout_risk DECIMAL(5,4),

    -- Confidence intervals (95%)
    coverage_ci_lower DECIMAL(5,2),
    coverage_ci_upper DECIMAL(5,2),
    violations_ci_lower INTEGER,
    violations_ci_upper INTEGER,

    -- For Bayesian: credible intervals
    coverage_credible_lower DECIMAL(5,2),
    coverage_credible_upper DECIMAL(5,2),

    -- Track prediction accuracy
    actual_coverage DECIMAL(5,2),
    actual_violations INTEGER,
    actual_fairness DECIMAL(5,4),

    -- Prediction error (populated after actuals known)
    mae_coverage DECIMAL(5,2),
    mae_violations DECIMAL(5,2),

    evaluated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for common queries
CREATE INDEX idx_outcome_events_resident ON outcome_events(resident_id, event_date);
CREATE INDEX idx_outcome_events_type ON outcome_events(event_type, event_date);
CREATE INDEX idx_burnout_surveys_risk ON burnout_surveys(burnout_risk, survey_date);
CREATE INDEX idx_predictions_schedule ON schedule_predictions(schedule_id, prediction_date);
```

### 1.2 Survey Integration UI

**New Tab:** Add "Outcomes" tab to Scheduling Laboratory

```
┌─────────────────────────────────────────────────────────────────┐
│ [Config] [Experiments] [Metrics] [History] [Overrides]          │
│ [Solver 3D] [Schedule 3D] [📊 Outcomes] [🔬 Analytics]          │
└─────────────────────────────────────────────────────────────────┘
```

**Outcomes Tab Features:**
- Quick burnout survey entry (Maslach mini-scale, ~5 min)
- Batch import from external survey tools (REDCap, Qualtrics)
- ACGME violation logging with schedule context
- Sick call / swap request correlation tracking
- Data quality dashboard (missing data, survey completion rates)

### 1.3 Excel Import Enhancement

Extend existing Excel import to capture historical outcomes:

```typescript
// frontend/src/features/excel-import/OutcomeImporter.tsx

interface HistoricalOutcomeRow {
  residentId: string;
  date: string;
  eventType: 'survey' | 'violation' | 'sick_call' | 'swap';
  // Flexible payload based on event type
  payload: Record<string, unknown>;
}

// Map Excel columns to outcome schema
const OUTCOME_COLUMN_MAPPINGS = {
  survey: {
    emotionalExhaustion: ['EE', 'Emotional Exhaustion', 'ee_score'],
    depersonalization: ['DP', 'Depersonalization', 'dp_score'],
    personalAccomplishment: ['PA', 'Personal Accomplishment', 'pa_score'],
  },
  violation: {
    violationType: ['Type', 'Violation Type', 'ACGME Rule'],
    hoursWorked: ['Hours', 'Hours Worked', 'Total Hours'],
  },
};
```

### 1.4 Backend Services

```python
# backend/app/services/outcome_service.py

from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.outcomes import OutcomeEvent, BurnoutSurvey
from app.schemas.outcomes import OutcomeEventCreate, BurnoutSurveyCreate

class OutcomeService:
    """Service for recording and querying outcome data."""

    async def record_burnout_survey(
        self,
        db: AsyncSession,
        resident_id: UUID,
        survey_data: BurnoutSurveyCreate,
    ) -> BurnoutSurvey:
        """Record a burnout survey response with schedule context."""
        # Auto-link to current schedule assignment
        current_assignment = await self._get_current_assignment(db, resident_id)

        survey = BurnoutSurvey(
            resident_id=resident_id,
            survey_date=survey_data.survey_date or date.today(),
            emotional_exhaustion=survey_data.emotional_exhaustion,
            depersonalization=survey_data.depersonalization,
            personal_accomplishment=survey_data.personal_accomplishment,
            schedule_id=current_assignment.schedule_id if current_assignment else None,
            current_rotation=current_assignment.rotation_name if current_assignment else None,
        )

        db.add(survey)
        await db.commit()
        return survey

    async def get_burnout_trajectory(
        self,
        db: AsyncSession,
        resident_id: UUID,
        start_date: Optional[date] = None,
    ) -> list[BurnoutSurvey]:
        """Get burnout score trajectory for survival analysis."""
        ...

    async def calculate_time_to_event(
        self,
        db: AsyncSession,
        resident_id: UUID,
        event_type: str,
        threshold: float,
    ) -> Optional[int]:
        """Calculate days until outcome event (for survival analysis)."""
        ...
```

### 1.5 Deliverables

| Deliverable | Type | Priority |
|-------------|------|----------|
| `outcome_events` table + migration | Backend | P0 |
| `burnout_surveys` table + migration | Backend | P0 |
| `schedule_predictions` table + migration | Backend | P0 |
| Outcome recording API endpoints | Backend | P0 |
| "Outcomes" tab UI | Frontend | P0 |
| Burnout survey form component | Frontend | P0 |
| Excel outcome importer | Frontend | P1 |
| Data quality dashboard | Frontend | P1 |

---

## Phase 2: Statistical Infrastructure

**Goal:** Build the statistical analysis layer that supports both frequentist and Bayesian approaches.

### 2.1 New Dependencies

```toml
# Add to pyproject.toml [project.dependencies]

# Frequentist statistics (extend existing scipy usage)
pingouin = ">=0.5.4"  # Effect sizes, post-hoc tests, normality tests

# Bayesian statistics
pymc = ">=5.10.0"     # Probabilistic programming
arviz = ">=0.17.0"    # Bayesian visualization

# Survival analysis
lifelines = ">=0.28.0"  # Kaplan-Meier, Cox PH

# Experiment design
pyDOE2 = ">=1.5.0"    # Design of experiments
```

### 2.2 Statistical Service Layer

```python
# backend/app/analytics/hypothesis_testing.py

"""
Frequentist hypothesis testing service.

Wraps scipy.stats with proper effect size calculation and
power analysis for scheduling experiments.
"""

from dataclasses import dataclass
from typing import Literal
import numpy as np
from scipy import stats
from scipy.stats import power


@dataclass
class HypothesisTestResult:
    """Standardized result for all hypothesis tests."""
    test_name: str
    statistic: float
    p_value: float
    effect_size: float
    effect_size_interpretation: str  # 'small', 'medium', 'large'
    confidence_interval: tuple[float, float]
    sample_sizes: tuple[int, ...]
    power: float  # Post-hoc power
    significant: bool
    alpha: float

    # For reporting
    summary: str


class HypothesisTestingService:
    """Production hypothesis testing with effect sizes and power."""

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def independent_t_test(
        self,
        group_a: np.ndarray,
        group_b: np.ndarray,
        alternative: Literal['two-sided', 'less', 'greater'] = 'two-sided',
    ) -> HypothesisTestResult:
        """
        Independent samples t-test with Welch's correction.

        Use for: Comparing algorithm A vs algorithm B on a metric.
        """
        # Welch's t-test (unequal variances)
        statistic, p_value = stats.ttest_ind(
            group_a, group_b, equal_var=False, alternative=alternative
        )

        # Cohen's d effect size
        pooled_std = np.sqrt(
            ((len(group_a) - 1) * np.var(group_a, ddof=1) +
             (len(group_b) - 1) * np.var(group_b, ddof=1)) /
            (len(group_a) + len(group_b) - 2)
        )
        cohens_d = (np.mean(group_a) - np.mean(group_b)) / pooled_std

        # Effect size interpretation (Cohen's conventions)
        if abs(cohens_d) < 0.2:
            interpretation = 'negligible'
        elif abs(cohens_d) < 0.5:
            interpretation = 'small'
        elif abs(cohens_d) < 0.8:
            interpretation = 'medium'
        else:
            interpretation = 'large'

        # Confidence interval for mean difference
        mean_diff = np.mean(group_a) - np.mean(group_b)
        se_diff = np.sqrt(
            np.var(group_a, ddof=1) / len(group_a) +
            np.var(group_b, ddof=1) / len(group_b)
        )
        df = self._welch_df(group_a, group_b)
        t_crit = stats.t.ppf(1 - self.alpha / 2, df)
        ci = (mean_diff - t_crit * se_diff, mean_diff + t_crit * se_diff)

        # Post-hoc power
        observed_power = self._calculate_power_t_test(
            len(group_a), len(group_b), cohens_d, self.alpha
        )

        return HypothesisTestResult(
            test_name='Independent Samples t-test (Welch)',
            statistic=statistic,
            p_value=p_value,
            effect_size=cohens_d,
            effect_size_interpretation=interpretation,
            confidence_interval=ci,
            sample_sizes=(len(group_a), len(group_b)),
            power=observed_power,
            significant=p_value < self.alpha,
            alpha=self.alpha,
            summary=self._generate_summary('t-test', statistic, p_value, cohens_d, interpretation),
        )

    def paired_t_test(
        self,
        before: np.ndarray,
        after: np.ndarray,
    ) -> HypothesisTestResult:
        """
        Paired samples t-test for within-subject comparisons.

        Use for: Same residents before/after intervention.
        """
        ...

    def one_way_anova(
        self,
        *groups: np.ndarray,
        post_hoc: bool = True,
    ) -> HypothesisTestResult:
        """
        One-way ANOVA with optional Tukey HSD post-hoc.

        Use for: Comparing 3+ scheduling algorithms.
        """
        statistic, p_value = stats.f_oneway(*groups)

        # Eta-squared effect size
        grand_mean = np.mean(np.concatenate(groups))
        ss_between = sum(
            len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups
        )
        ss_total = sum(
            np.sum((g - grand_mean) ** 2) for g in groups
        )
        eta_squared = ss_between / ss_total

        # Post-hoc tests if significant
        post_hoc_results = None
        if post_hoc and p_value < self.alpha:
            # Tukey HSD (scipy 1.10+)
            post_hoc_results = stats.tukey_hsd(*groups)

        ...

    def chi_square_test(
        self,
        observed: np.ndarray,
        expected: np.ndarray | None = None,
    ) -> HypothesisTestResult:
        """
        Chi-square test for categorical data.

        Use for: Comparing violation rates across algorithms.
        """
        ...

    def calculate_sample_size(
        self,
        effect_size: float,
        power: float = 0.8,
        alpha: float = 0.05,
        test_type: Literal['t-test', 'anova', 'chi-square'] = 't-test',
    ) -> int:
        """
        A priori power analysis for sample size determination.

        Use for: Planning how many schedule runs needed.
        """
        from statsmodels.stats.power import TTestIndPower

        analysis = TTestIndPower()
        n = analysis.solve_power(
            effect_size=effect_size,
            power=power,
            alpha=alpha,
            ratio=1.0,  # Equal group sizes
            alternative='two-sided',
        )
        return int(np.ceil(n))

    def _welch_df(self, a: np.ndarray, b: np.ndarray) -> float:
        """Welch-Satterthwaite degrees of freedom."""
        va, vb = np.var(a, ddof=1), np.var(b, ddof=1)
        na, nb = len(a), len(b)
        num = (va / na + vb / nb) ** 2
        denom = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
        return num / denom

    def _generate_summary(self, test_name: str, stat: float, p: float,
                          effect: float, interpretation: str) -> str:
        """Generate human-readable summary for coordinators."""
        sig_text = "statistically significant" if p < self.alpha else "not statistically significant"
        return (
            f"{test_name}: t = {stat:.3f}, p = {p:.4f} ({sig_text}). "
            f"Effect size (Cohen's d) = {effect:.3f} ({interpretation})."
        )
```

### 2.3 Bayesian Analysis Service

```python
# backend/app/analytics/bayesian_analysis.py

"""
Bayesian statistical analysis service.

Provides credible intervals, posterior distributions, and
Bayesian hypothesis testing as an alternative to frequentist methods.
"""

import pymc as pm
import arviz as az
import numpy as np
from dataclasses import dataclass


@dataclass
class BayesianResult:
    """Result from Bayesian analysis."""
    posterior_mean: float
    posterior_std: float
    credible_interval_95: tuple[float, float]
    credible_interval_89: tuple[float, float]  # More stable than 95%
    probability_of_superiority: float  # P(A > B)
    bayes_factor: float | None  # If hypothesis testing
    rope_decision: str  # 'reject', 'accept', 'undecided'
    trace: az.InferenceData  # For visualization
    summary: str


class BayesianAnalysisService:
    """Bayesian inference for scheduling experiments."""

    def __init__(self, rope_margin: float = 0.1):
        """
        Args:
            rope_margin: Region of Practical Equivalence margin.
                         Effects within [-rope, +rope] are practically zero.
        """
        self.rope_margin = rope_margin

    def compare_algorithms(
        self,
        algorithm_a_scores: np.ndarray,
        algorithm_b_scores: np.ndarray,
        metric_name: str = "coverage",
        samples: int = 4000,
    ) -> BayesianResult:
        """
        Bayesian comparison of two algorithms.

        More informative than p-values:
        - "There's a 94% probability that Algorithm A is better"
        - vs "p < 0.05"

        Args:
            algorithm_a_scores: Metric values from algorithm A runs
            algorithm_b_scores: Metric values from algorithm B runs
            metric_name: For labeling
            samples: MCMC samples (4000 is usually sufficient)
        """
        with pm.Model() as model:
            # Priors (weakly informative)
            mu_a = pm.Normal('mu_a', mu=np.mean(algorithm_a_scores), sigma=10)
            mu_b = pm.Normal('mu_b', mu=np.mean(algorithm_b_scores), sigma=10)
            sigma_a = pm.HalfNormal('sigma_a', sigma=5)
            sigma_b = pm.HalfNormal('sigma_b', sigma=5)

            # Likelihoods
            obs_a = pm.Normal('obs_a', mu=mu_a, sigma=sigma_a, observed=algorithm_a_scores)
            obs_b = pm.Normal('obs_b', mu=mu_b, sigma=sigma_b, observed=algorithm_b_scores)

            # Derived quantity: difference
            diff = pm.Deterministic('diff', mu_a - mu_b)

            # Sample
            trace = pm.sample(samples, return_inferencedata=True, progressbar=False)

        # Extract posterior for difference
        diff_samples = trace.posterior['diff'].values.flatten()

        # Credible intervals
        ci_95 = (np.percentile(diff_samples, 2.5), np.percentile(diff_samples, 97.5))
        ci_89 = (np.percentile(diff_samples, 5.5), np.percentile(diff_samples, 94.5))

        # Probability of superiority (A > B)
        prob_superior = np.mean(diff_samples > 0)

        # ROPE decision
        in_rope = np.mean(np.abs(diff_samples) < self.rope_margin)
        if ci_95[0] > self.rope_margin:
            rope_decision = 'A clearly better'
        elif ci_95[1] < -self.rope_margin:
            rope_decision = 'B clearly better'
        elif in_rope > 0.95:
            rope_decision = 'practically equivalent'
        else:
            rope_decision = 'undecided (need more data)'

        summary = (
            f"Bayesian comparison ({metric_name}): "
            f"P(A > B) = {prob_superior:.1%}. "
            f"95% CI for difference: [{ci_95[0]:.3f}, {ci_95[1]:.3f}]. "
            f"Decision: {rope_decision}."
        )

        return BayesianResult(
            posterior_mean=np.mean(diff_samples),
            posterior_std=np.std(diff_samples),
            credible_interval_95=ci_95,
            credible_interval_89=ci_89,
            probability_of_superiority=prob_superior,
            bayes_factor=None,  # Not using BF for this comparison
            rope_decision=rope_decision,
            trace=trace,
            summary=summary,
        )

    def estimate_burnout_rate(
        self,
        burnout_events: int,
        total_residents: int,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
    ) -> BayesianResult:
        """
        Bayesian estimation of burnout rate with credible interval.

        Uses Beta-Binomial conjugate model for fast, exact inference.

        Args:
            burnout_events: Number of burnout cases observed
            total_residents: Total residents in cohort
            prior_alpha, prior_beta: Beta prior parameters (1,1 = uniform)
        """
        # Posterior is Beta(alpha + events, beta + non-events)
        post_alpha = prior_alpha + burnout_events
        post_beta = prior_beta + (total_residents - burnout_events)

        from scipy.stats import beta

        posterior = beta(post_alpha, post_beta)
        mean = posterior.mean()
        std = posterior.std()
        ci_95 = posterior.ppf([0.025, 0.975])

        return BayesianResult(
            posterior_mean=mean,
            posterior_std=std,
            credible_interval_95=tuple(ci_95),
            credible_interval_89=tuple(posterior.ppf([0.055, 0.945])),
            probability_of_superiority=None,
            bayes_factor=None,
            rope_decision='N/A',
            trace=None,
            summary=f"Burnout rate: {mean:.1%} (95% CI: {ci_95[0]:.1%} - {ci_95[1]:.1%})",
        )
```

### 2.4 Survival Analysis Service

```python
# backend/app/analytics/survival_analysis.py

"""
Survival analysis for time-to-event outcomes.

Primary use: Predict time-to-burnout and identify risk factors.
"""

from dataclasses import dataclass
from typing import Optional
import numpy as np
import pandas as pd
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test


@dataclass
class SurvivalCurve:
    """Kaplan-Meier survival curve data."""
    time_points: np.ndarray
    survival_probabilities: np.ndarray
    confidence_lower: np.ndarray
    confidence_upper: np.ndarray
    median_survival: float | None
    events_observed: int
    censored_count: int


@dataclass
class HazardRatio:
    """Cox proportional hazards result."""
    covariate: str
    hazard_ratio: float
    confidence_interval: tuple[float, float]
    p_value: float
    interpretation: str  # e.g., "1.5x increased risk"


@dataclass
class SurvivalAnalysisResult:
    """Complete survival analysis result."""
    curves: dict[str, SurvivalCurve]  # Group name -> curve
    log_rank_p_value: float | None  # If comparing groups
    hazard_ratios: list[HazardRatio] | None  # If Cox PH fitted
    risk_factors: list[str]  # Significant predictors
    summary: str


class SurvivalAnalysisService:
    """Time-to-event analysis for burnout and other outcomes."""

    def kaplan_meier(
        self,
        durations: np.ndarray,
        event_observed: np.ndarray,
        group_labels: Optional[np.ndarray] = None,
    ) -> SurvivalAnalysisResult:
        """
        Kaplan-Meier survival curve estimation.

        Args:
            durations: Time until event (or censoring) in days/weeks
            event_observed: 1 if event occurred, 0 if censored
            group_labels: Optional grouping variable for comparison
        """
        curves = {}

        if group_labels is None:
            # Single curve
            kmf = KaplanMeierFitter()
            kmf.fit(durations, event_observed, label='Overall')
            curves['Overall'] = self._extract_curve(kmf)
            log_rank_p = None
        else:
            # Multiple curves with comparison
            unique_groups = np.unique(group_labels)
            fitters = {}

            for group in unique_groups:
                mask = group_labels == group
                kmf = KaplanMeierFitter()
                kmf.fit(durations[mask], event_observed[mask], label=str(group))
                curves[str(group)] = self._extract_curve(kmf)
                fitters[group] = kmf

            # Log-rank test for group differences
            if len(unique_groups) == 2:
                g1, g2 = unique_groups
                m1, m2 = group_labels == g1, group_labels == g2
                result = logrank_test(
                    durations[m1], durations[m2],
                    event_observed[m1], event_observed[m2]
                )
                log_rank_p = result.p_value
            else:
                log_rank_p = None  # Multi-group test more complex

        significant = log_rank_p is not None and log_rank_p < 0.05
        summary = self._generate_km_summary(curves, log_rank_p, significant)

        return SurvivalAnalysisResult(
            curves=curves,
            log_rank_p_value=log_rank_p,
            hazard_ratios=None,
            risk_factors=[],
            summary=summary,
        )

    def cox_proportional_hazards(
        self,
        data: pd.DataFrame,
        duration_col: str,
        event_col: str,
        covariates: list[str],
    ) -> SurvivalAnalysisResult:
        """
        Cox proportional hazards regression.

        Identifies risk factors for burnout while controlling for confounders.

        Args:
            data: DataFrame with outcomes and covariates
            duration_col: Column name for time-to-event
            event_col: Column name for event indicator (0/1)
            covariates: List of predictor column names

        Example covariates:
            - pgy_level (1, 2, 3)
            - night_float_weeks (cumulative)
            - avg_weekly_hours
            - consecutive_weekend_calls
            - rotation_type (categorical)
        """
        cph = CoxPHFitter()
        cph.fit(
            data[[duration_col, event_col] + covariates],
            duration_col=duration_col,
            event_col=event_col,
        )

        hazard_ratios = []
        risk_factors = []

        for covariate in covariates:
            hr = cph.hazard_ratios_[covariate]
            ci = cph.confidence_intervals_.loc[covariate]
            p_val = cph.summary.loc[covariate, 'p']

            if hr > 1:
                interp = f"{hr:.2f}x increased risk"
            else:
                interp = f"{1/hr:.2f}x decreased risk"

            hazard_ratios.append(HazardRatio(
                covariate=covariate,
                hazard_ratio=hr,
                confidence_interval=(ci['95% lower-bound'], ci['95% upper-bound']),
                p_value=p_val,
                interpretation=interp,
            ))

            if p_val < 0.05:
                risk_factors.append(covariate)

        summary = self._generate_cox_summary(hazard_ratios, risk_factors)

        return SurvivalAnalysisResult(
            curves={},  # Cox doesn't produce KM curves directly
            log_rank_p_value=None,
            hazard_ratios=hazard_ratios,
            risk_factors=risk_factors,
            summary=summary,
        )

    def predict_burnout_risk(
        self,
        model: CoxPHFitter,
        resident_data: pd.DataFrame,
        time_horizon: int = 90,  # days
    ) -> pd.DataFrame:
        """
        Predict burnout probability for each resident.

        Returns DataFrame with:
            - resident_id
            - burnout_probability_{time_horizon}d
            - risk_category (low/medium/high)
            - top_risk_factors
        """
        survival_probs = model.predict_survival_function(resident_data, times=[time_horizon])
        burnout_probs = 1 - survival_probs.iloc[0]

        results = resident_data.copy()
        results[f'burnout_probability_{time_horizon}d'] = burnout_probs
        results['risk_category'] = pd.cut(
            burnout_probs,
            bins=[0, 0.15, 0.35, 1.0],
            labels=['low', 'medium', 'high']
        )

        return results

    def _extract_curve(self, kmf: KaplanMeierFitter) -> SurvivalCurve:
        """Extract curve data from fitted KaplanMeierFitter."""
        return SurvivalCurve(
            time_points=kmf.survival_function_.index.values,
            survival_probabilities=kmf.survival_function_.values.flatten(),
            confidence_lower=kmf.confidence_interval_['KM_estimate_lower_0.95'].values,
            confidence_upper=kmf.confidence_interval_['KM_estimate_upper_0.95'].values,
            median_survival=kmf.median_survival_time_,
            events_observed=kmf.event_observed.sum(),
            censored_count=(~kmf.event_observed.astype(bool)).sum(),
        )

    def _generate_km_summary(self, curves: dict, p_value: float | None, significant: bool) -> str:
        """Generate human-readable Kaplan-Meier summary."""
        lines = []
        for name, curve in curves.items():
            median_str = f"{curve.median_survival:.0f} days" if curve.median_survival else "not reached"
            lines.append(f"  {name}: Median time-to-burnout = {median_str}")

        if p_value is not None:
            sig_str = "significantly different" if significant else "not significantly different"
            lines.append(f"  Groups are {sig_str} (log-rank p = {p_value:.4f})")

        return "Kaplan-Meier Analysis:\n" + "\n".join(lines)

    def _generate_cox_summary(self, hrs: list[HazardRatio], risk_factors: list[str]) -> str:
        """Generate human-readable Cox PH summary."""
        lines = ["Cox Proportional Hazards Analysis:", "Significant risk factors:"]
        for hr in hrs:
            if hr.covariate in risk_factors:
                lines.append(f"  - {hr.covariate}: HR = {hr.hazard_ratio:.2f} ({hr.interpretation})")
        return "\n".join(lines)
```

### 2.5 Deliverables

| Deliverable | Type | Priority |
|-------------|------|----------|
| Add pingouin, pymc, arviz, lifelines, pyDOE2 | Dependencies | P0 |
| `hypothesis_testing.py` service | Backend | P0 |
| `bayesian_analysis.py` service | Backend | P1 |
| `survival_analysis.py` service | Backend | P0 |
| API endpoints for statistical services | Backend | P0 |
| Unit tests for all statistical functions | Backend | P0 |

---

## Phase 3: Frontend Visualization Components

**Goal:** Build reusable chart components for statistical results.

### 3.1 New Chart Components

```
frontend/src/components/analytics/
├── KaplanMeierChart.tsx        # Survival curves
├── ForestPlot.tsx              # Hazard ratios from Cox PH
├── PosteriorDistribution.tsx   # Bayesian posterior visualization
├── EffectSizePlot.tsx          # Cohen's d with CI
├── PredictedVsActual.tsx       # Scatter + regression line
├── ConfusionMatrix.tsx         # For categorical predictions
├── ROPEPlot.tsx                # Region of Practical Equivalence
└── PowerCurve.tsx              # Sample size planning
```

### 3.2 Kaplan-Meier Survival Chart

```typescript
// frontend/src/components/analytics/KaplanMeierChart.tsx

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  Area,
  ComposedChart,
  ReferenceLine,
} from 'recharts';

interface SurvivalCurve {
  timePoints: number[];
  survivalProbabilities: number[];
  confidenceLower: number[];
  confidenceUpper: number[];
  medianSurvival: number | null;
  label: string;
}

interface KaplanMeierChartProps {
  curves: SurvivalCurve[];
  xAxisLabel?: string;
  yAxisLabel?: string;
  showConfidenceIntervals?: boolean;
  showMedianLines?: boolean;
  logRankPValue?: number;
  height?: number;
}

const COLORS = ['#8b5cf6', '#06b6d4', '#f59e0b', '#ef4444', '#22c55e'];

export function KaplanMeierChart({
  curves,
  xAxisLabel = 'Time (days)',
  yAxisLabel = 'Survival Probability',
  showConfidenceIntervals = true,
  showMedianLines = true,
  logRankPValue,
  height = 400,
}: KaplanMeierChartProps) {
  // Transform data for Recharts
  const chartData = useMemo(() => {
    // Merge all time points
    const allTimes = new Set<number>();
    curves.forEach(c => c.timePoints.forEach(t => allTimes.add(t)));
    const sortedTimes = Array.from(allTimes).sort((a, b) => a - b);

    return sortedTimes.map(time => {
      const point: Record<string, number> = { time };

      curves.forEach((curve, idx) => {
        const timeIdx = curve.timePoints.findIndex(t => t >= time);
        if (timeIdx >= 0) {
          point[`survival_${idx}`] = curve.survivalProbabilities[timeIdx];
          if (showConfidenceIntervals) {
            point[`ci_lower_${idx}`] = curve.confidenceLower[timeIdx];
            point[`ci_upper_${idx}`] = curve.confidenceUpper[timeIdx];
          }
        }
      });

      return point;
    });
  }, [curves, showConfidenceIntervals]);

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Survival Analysis</h3>
        {logRankPValue !== undefined && (
          <span className={`
            text-sm px-2 py-1 rounded
            ${logRankPValue < 0.05
              ? 'bg-emerald-500/20 text-emerald-400'
              : 'bg-slate-700 text-slate-300'
            }
          `}>
            Log-rank p = {logRankPValue.toFixed(4)}
          </span>
        )}
      </div>

      <ComposedChart
        width={600}
        height={height}
        data={chartData}
        margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis
          dataKey="time"
          stroke="#9ca3af"
          label={{ value: xAxisLabel, position: 'bottom', fill: '#9ca3af' }}
        />
        <YAxis
          domain={[0, 1]}
          stroke="#9ca3af"
          tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
          label={{ value: yAxisLabel, angle: -90, position: 'left', fill: '#9ca3af' }}
        />
        <Tooltip
          contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
          labelStyle={{ color: '#f1f5f9' }}
          formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
        />
        <Legend />

        {/* Reference line at 50% survival (median) */}
        {showMedianLines && (
          <ReferenceLine y={0.5} stroke="#6b7280" strokeDasharray="5 5" />
        )}

        {curves.map((curve, idx) => (
          <Fragment key={curve.label}>
            {/* Confidence interval area */}
            {showConfidenceIntervals && (
              <Area
                type="stepAfter"
                dataKey={`ci_upper_${idx}`}
                stroke="none"
                fill={COLORS[idx % COLORS.length]}
                fillOpacity={0.1}
              />
            )}

            {/* Main survival line */}
            <Line
              type="stepAfter"
              dataKey={`survival_${idx}`}
              name={curve.label}
              stroke={COLORS[idx % COLORS.length]}
              strokeWidth={2}
              dot={false}
            />
          </Fragment>
        ))}
      </ComposedChart>

      {/* Median survival times */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm">
        {curves.map((curve, idx) => (
          <div key={curve.label} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: COLORS[idx % COLORS.length] }}
            />
            <span className="text-slate-300">{curve.label}:</span>
            <span className="text-white font-medium">
              {curve.medianSurvival
                ? `Median = ${curve.medianSurvival.toFixed(0)} days`
                : 'Median not reached'
              }
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

### 3.3 Forest Plot for Hazard Ratios

```typescript
// frontend/src/components/analytics/ForestPlot.tsx

interface HazardRatioData {
  covariate: string;
  hazardRatio: number;
  ciLower: number;
  ciUpper: number;
  pValue: number;
}

interface ForestPlotProps {
  data: HazardRatioData[];
  referenceValue?: number; // Default: 1.0 (no effect)
  title?: string;
}

export function ForestPlot({
  data,
  referenceValue = 1.0,
  title = 'Hazard Ratios (Cox Proportional Hazards)',
}: ForestPlotProps) {
  // Sort by hazard ratio magnitude
  const sortedData = [...data].sort((a, b) => b.hazardRatio - a.hazardRatio);

  // Determine x-axis range (log scale)
  const minHR = Math.min(...data.map(d => d.ciLower));
  const maxHR = Math.max(...data.map(d => d.ciUpper));
  const xMin = Math.max(0.1, minHR * 0.8);
  const xMax = Math.min(10, maxHR * 1.2);

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>

      <div className="space-y-3">
        {sortedData.map((item) => {
          const significant = item.pValue < 0.05;
          const isRisk = item.hazardRatio > 1;

          // Calculate position on log scale
          const logMin = Math.log10(xMin);
          const logMax = Math.log10(xMax);
          const logHR = Math.log10(item.hazardRatio);
          const logLower = Math.log10(item.ciLower);
          const logUpper = Math.log10(item.ciUpper);

          const posHR = ((logHR - logMin) / (logMax - logMin)) * 100;
          const posLower = ((logLower - logMin) / (logMax - logMin)) * 100;
          const posUpper = ((logUpper - logMin) / (logMax - logMin)) * 100;
          const posRef = ((Math.log10(referenceValue) - logMin) / (logMax - logMin)) * 100;

          return (
            <div key={item.covariate} className="flex items-center gap-4">
              {/* Covariate name */}
              <div className="w-40 text-sm text-slate-300 truncate">
                {item.covariate}
              </div>

              {/* Forest plot bar */}
              <div className="flex-1 relative h-6">
                {/* Reference line */}
                <div
                  className="absolute top-0 bottom-0 w-px bg-slate-500"
                  style={{ left: `${posRef}%` }}
                />

                {/* Confidence interval line */}
                <div
                  className="absolute top-1/2 h-0.5 -translate-y-1/2 bg-slate-400"
                  style={{
                    left: `${posLower}%`,
                    width: `${posUpper - posLower}%`
                  }}
                />

                {/* Point estimate */}
                <div
                  className={`
                    absolute top-1/2 w-3 h-3 -translate-y-1/2 -translate-x-1/2
                    ${significant
                      ? isRisk ? 'bg-red-500' : 'bg-emerald-500'
                      : 'bg-slate-400'
                    }
                  `}
                  style={{
                    left: `${posHR}%`,
                    clipPath: 'polygon(50% 0%, 100% 50%, 50% 100%, 0% 50%)', // Diamond
                  }}
                />
              </div>

              {/* Numeric values */}
              <div className="w-48 text-sm flex gap-2">
                <span className={`font-mono ${significant ? 'text-white' : 'text-slate-400'}`}>
                  {item.hazardRatio.toFixed(2)}
                </span>
                <span className="text-slate-500">
                  ({item.ciLower.toFixed(2)}-{item.ciUpper.toFixed(2)})
                </span>
                <span className={`
                  ${item.pValue < 0.001 ? 'text-amber-400' :
                    item.pValue < 0.01 ? 'text-amber-300' :
                    item.pValue < 0.05 ? 'text-slate-300' : 'text-slate-500'}
                `}>
                  {item.pValue < 0.001 ? '***' :
                   item.pValue < 0.01 ? '**' :
                   item.pValue < 0.05 ? '*' : ''}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-4 pt-4 border-t border-slate-700 flex items-center gap-6 text-xs text-slate-400">
        <span>* p &lt; 0.05</span>
        <span>** p &lt; 0.01</span>
        <span>*** p &lt; 0.001</span>
        <span className="ml-auto">HR &gt; 1 = increased risk | HR &lt; 1 = protective</span>
      </div>
    </div>
  );
}
```

### 3.4 Predicted vs Actual Chart

```typescript
// frontend/src/components/analytics/PredictedVsActualChart.tsx

import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';

interface PredictionPoint {
  predicted: number;
  actual: number;
  label?: string;
  date?: string;
}

interface PredictedVsActualProps {
  data: PredictionPoint[];
  metricName: string;
  unit?: string;
  showPerfectLine?: boolean;
  showRegressionLine?: boolean;
}

export function PredictedVsActualChart({
  data,
  metricName,
  unit = '%',
  showPerfectLine = true,
  showRegressionLine = true,
}: PredictedVsActualProps) {
  // Calculate regression line
  const regression = useMemo(() => {
    const n = data.length;
    const sumX = data.reduce((s, d) => s + d.predicted, 0);
    const sumY = data.reduce((s, d) => s + d.actual, 0);
    const sumXY = data.reduce((s, d) => s + d.predicted * d.actual, 0);
    const sumXX = data.reduce((s, d) => s + d.predicted * d.predicted, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    // R-squared
    const meanY = sumY / n;
    const ssTotal = data.reduce((s, d) => s + (d.actual - meanY) ** 2, 0);
    const ssResidual = data.reduce((s, d) => s + (d.actual - (slope * d.predicted + intercept)) ** 2, 0);
    const rSquared = 1 - ssResidual / ssTotal;

    // MAE
    const mae = data.reduce((s, d) => s + Math.abs(d.actual - d.predicted), 0) / n;

    return { slope, intercept, rSquared, mae };
  }, [data]);

  // Determine axis range
  const allValues = data.flatMap(d => [d.predicted, d.actual]);
  const minVal = Math.min(...allValues) * 0.95;
  const maxVal = Math.max(...allValues) * 1.05;

  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">
          Predicted vs Actual: {metricName}
        </h3>
        <div className="flex gap-4 text-sm">
          <span className="text-slate-300">
            R² = <span className="text-white font-mono">{regression.rSquared.toFixed(3)}</span>
          </span>
          <span className="text-slate-300">
            MAE = <span className="text-white font-mono">{regression.mae.toFixed(2)}{unit}</span>
          </span>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 40, left: 40 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="predicted"
            type="number"
            domain={[minVal, maxVal]}
            stroke="#9ca3af"
            label={{
              value: `Predicted ${metricName} (${unit})`,
              position: 'bottom',
              fill: '#9ca3af',
              offset: 20,
            }}
          />
          <YAxis
            dataKey="actual"
            type="number"
            domain={[minVal, maxVal]}
            stroke="#9ca3af"
            label={{
              value: `Actual ${metricName} (${unit})`,
              angle: -90,
              position: 'left',
              fill: '#9ca3af',
              offset: 10,
            }}
          />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
            labelStyle={{ color: '#f1f5f9' }}
            formatter={(value: number, name: string) => [
              `${value.toFixed(2)}${unit}`,
              name === 'predicted' ? 'Predicted' : 'Actual'
            ]}
          />

          {/* Perfect prediction line (y = x) */}
          {showPerfectLine && (
            <ReferenceLine
              segment={[
                { x: minVal, y: minVal },
                { x: maxVal, y: maxVal }
              ]}
              stroke="#22c55e"
              strokeDasharray="5 5"
              strokeWidth={2}
            />
          )}

          {/* Regression line */}
          {showRegressionLine && (
            <ReferenceLine
              segment={[
                { x: minVal, y: regression.slope * minVal + regression.intercept },
                { x: maxVal, y: regression.slope * maxVal + regression.intercept }
              ]}
              stroke="#8b5cf6"
              strokeWidth={2}
            />
          )}

          {/* Data points */}
          <Scatter
            data={data}
            fill="#06b6d4"
            fillOpacity={0.7}
          />
        </ScatterChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-4 flex items-center gap-6 text-sm text-slate-400">
        {showPerfectLine && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-emerald-500" style={{ borderStyle: 'dashed' }} />
            <span>Perfect prediction (y = x)</span>
          </div>
        )}
        {showRegressionLine && (
          <div className="flex items-center gap-2">
            <div className="w-6 h-0.5 bg-violet-500" />
            <span>Regression line (y = {regression.slope.toFixed(2)}x + {regression.intercept.toFixed(2)})</span>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 3.5 Deliverables

| Deliverable | Type | Priority |
|-------------|------|----------|
| `KaplanMeierChart.tsx` | Frontend | P0 |
| `ForestPlot.tsx` | Frontend | P0 |
| `PredictedVsActualChart.tsx` | Frontend | P0 |
| `PosteriorDistribution.tsx` | Frontend | P1 |
| `EffectSizePlot.tsx` | Frontend | P1 |
| `PowerCurve.tsx` | Frontend | P2 |
| `ROPEPlot.tsx` | Frontend | P2 |

---

## Phase 4: New Dashboard Tabs

**Goal:** Integrate all components into the Scheduling Laboratory.

### 4.1 Tab Structure Update

```typescript
// Update TABS in frontend/src/app/admin/scheduling/page.tsx

const TABS: { id: AdminSchedulingTab; label: string; icon: React.ElementType }[] = [
  // Existing tabs
  { id: 'configuration', label: 'Configuration', icon: Settings },
  { id: 'experimentation', label: 'Experimentation', icon: Beaker },
  { id: 'metrics', label: 'Metrics', icon: BarChart3 },
  { id: 'history', label: 'History', icon: History },
  { id: 'overrides', label: 'Overrides', icon: Shield },
  { id: 'solver-viz', label: 'Solver 3D', icon: Eye },
  { id: 'schedule-3d', label: 'Schedule 3D', icon: Boxes },

  // New tabs
  { id: 'outcomes', label: 'Outcomes', icon: ClipboardList },      // Phase 1
  { id: 'survival', label: 'Survival', icon: Activity },           // Phase 4
  { id: 'ab-testing', label: 'A/B Tests', icon: GitBranch },       // Phase 4
  { id: 'predictions', label: 'Predictions', icon: TrendingUp },   // Phase 4
];
```

### 4.2 Survival Analysis Tab

```typescript
// frontend/src/app/admin/scheduling/tabs/SurvivalTab.tsx

export function SurvivalTab() {
  const [analysisType, setAnalysisType] = useState<'kaplan-meier' | 'cox'>('kaplan-meier');
  const [selectedOutcome, setSelectedOutcome] = useState('burnout');
  const [groupBy, setGroupBy] = useState<string | null>(null);

  const { data: survivalData, isLoading } = useSurvivalAnalysis({
    outcome: selectedOutcome,
    groupBy,
    analysisType,
  });

  const { data: riskFactors } = useCoxHazardRatios({
    enabled: analysisType === 'cox',
  });

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
        <div className="flex flex-wrap items-center gap-4">
          <div>
            <label className="text-sm text-slate-300 block mb-1">Analysis Type</label>
            <select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value as 'kaplan-meier' | 'cox')}
              className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
            >
              <option value="kaplan-meier">Kaplan-Meier Curves</option>
              <option value="cox">Cox Proportional Hazards</option>
            </select>
          </div>

          <div>
            <label className="text-sm text-slate-300 block mb-1">Outcome</label>
            <select
              value={selectedOutcome}
              onChange={(e) => setSelectedOutcome(e.target.value)}
              className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
            >
              <option value="burnout">Time to Burnout</option>
              <option value="violation">Time to ACGME Violation</option>
              <option value="sick_call">Time to Sick Call</option>
            </select>
          </div>

          {analysisType === 'kaplan-meier' && (
            <div>
              <label className="text-sm text-slate-300 block mb-1">Compare By</label>
              <select
                value={groupBy || ''}
                onChange={(e) => setGroupBy(e.target.value || null)}
                className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
              >
                <option value="">No grouping (overall)</option>
                <option value="pgy_level">PGY Level</option>
                <option value="rotation_type">Rotation Type</option>
                <option value="schedule_algorithm">Schedule Algorithm</option>
              </select>
            </div>
          )}
        </div>
      </div>

      {/* Visualization */}
      {isLoading ? (
        <div className="flex items-center justify-center h-96">
          <LoadingSpinner />
        </div>
      ) : analysisType === 'kaplan-meier' ? (
        <KaplanMeierChart
          curves={survivalData?.curves || []}
          logRankPValue={survivalData?.logRankPValue}
          xAxisLabel={`Days until ${selectedOutcome}`}
        />
      ) : (
        <ForestPlot
          data={riskFactors || []}
          title={`Risk Factors for ${selectedOutcome}`}
        />
      )}

      {/* Summary statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          label="Median Time to Event"
          value={survivalData?.medianSurvival || 'N/A'}
          unit="days"
        />
        <StatCard
          label="Events Observed"
          value={survivalData?.eventsObserved || 0}
        />
        <StatCard
          label="Censored"
          value={survivalData?.censoredCount || 0}
          subtitle="(ongoing/left program)"
        />
      </div>

      {/* Risk prediction table */}
      {analysisType === 'cox' && (
        <ResidentRiskTable
          predictions={survivalData?.predictions || []}
          timeHorizon={90}
        />
      )}
    </div>
  );
}
```

### 4.3 A/B Testing Tab

```typescript
// frontend/src/app/admin/scheduling/tabs/ABTestingTab.tsx

export function ABTestingTab() {
  const [selectedExperiment, setSelectedExperiment] = useState<string | null>(null);
  const [statisticalApproach, setStatisticalApproach] = useState<'frequentist' | 'bayesian'>('frequentist');

  const { data: experiments } = useExperiments();
  const { data: results } = useExperimentResults(selectedExperiment, statisticalApproach);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left: Experiment list */}
      <div className="space-y-4">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Experiments</h3>

          <div className="space-y-2">
            {experiments?.map(exp => (
              <button
                key={exp.id}
                onClick={() => setSelectedExperiment(exp.id)}
                className={`
                  w-full p-3 rounded-lg border text-left transition-all
                  ${selectedExperiment === exp.id
                    ? 'bg-violet-500/20 border-violet-500'
                    : 'bg-slate-800 border-slate-700 hover:border-slate-600'
                  }
                `}
              >
                <div className="flex items-center justify-between">
                  <span className="font-medium text-white">{exp.name}</span>
                  <StatusBadge status={exp.status} />
                </div>
                <div className="text-xs text-slate-300 mt-1">
                  {exp.variants.length} variants • {exp.sampleSize} runs
                </div>
              </button>
            ))}
          </div>

          <button className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium transition-all">
            <Plus className="w-4 h-4" />
            New Experiment
          </button>
        </div>

        {/* Statistical approach toggle */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <label className="text-sm text-slate-300 block mb-2">Statistical Approach</label>
          <div className="flex rounded-lg overflow-hidden border border-slate-700">
            <button
              onClick={() => setStatisticalApproach('frequentist')}
              className={`
                flex-1 px-4 py-2 text-sm font-medium transition-colors
                ${statisticalApproach === 'frequentist'
                  ? 'bg-violet-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }
              `}
            >
              Frequentist
            </button>
            <button
              onClick={() => setStatisticalApproach('bayesian')}
              className={`
                flex-1 px-4 py-2 text-sm font-medium transition-colors
                ${statisticalApproach === 'bayesian'
                  ? 'bg-violet-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }
              `}
            >
              Bayesian
            </button>
          </div>
        </div>
      </div>

      {/* Right: Results */}
      <div className="lg:col-span-2 space-y-6">
        {selectedExperiment && results ? (
          <>
            {/* Key metrics comparison */}
            <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                {statisticalApproach === 'frequentist' ? 'Hypothesis Test Results' : 'Bayesian Analysis'}
              </h3>

              {statisticalApproach === 'frequentist' ? (
                <FrequentistResults results={results} />
              ) : (
                <BayesianResults results={results} />
              )}
            </div>

            {/* Effect size visualization */}
            <EffectSizePlot
              metrics={results.metrics}
              approach={statisticalApproach}
            />

            {/* Sample size / power analysis */}
            <PowerAnalysisCard
              currentN={results.sampleSize}
              observedEffect={results.effectSize}
              observedPower={results.power}
            />
          </>
        ) : (
          <div className="flex items-center justify-center h-96 bg-slate-800/50 border border-slate-700 rounded-xl">
            <p className="text-slate-400">Select an experiment to view results</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

### 4.4 Predictions Tab

```typescript
// frontend/src/app/admin/scheduling/tabs/PredictionsTab.tsx

export function PredictionsTab() {
  const [selectedMetric, setSelectedMetric] = useState('coverage');
  const [timeRange, setTimeRange] = useState('30d');

  const { data: predictions } = usePredictionHistory({ metric: selectedMetric, range: timeRange });
  const { data: accuracy } = usePredictionAccuracy({ metric: selectedMetric });

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center gap-4">
        <select
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value)}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          <option value="coverage">Coverage %</option>
          <option value="violations">ACGME Violations</option>
          <option value="fairness">Fairness Score</option>
          <option value="burnout_risk">Burnout Risk</option>
        </select>

        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
        >
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
          <option value="90d">Last 90 days</option>
          <option value="all">All time</option>
        </select>
      </div>

      {/* Predicted vs Actual scatter plot */}
      <PredictedVsActualChart
        data={predictions || []}
        metricName={selectedMetric}
        unit={selectedMetric === 'violations' ? '' : '%'}
      />

      {/* Accuracy metrics over time */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Model Accuracy Trend</h3>
          <AccuracyTrendChart
            data={accuracy?.trend || []}
            metric="mae"
          />
        </div>

        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Calibration Plot</h3>
          <CalibrationChart
            data={accuracy?.calibration || []}
          />
        </div>
      </div>

      {/* Summary statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="R² Score"
          value={accuracy?.rSquared?.toFixed(3) || 'N/A'}
          interpretation={accuracy?.rSquared > 0.7 ? 'Good' : accuracy?.rSquared > 0.5 ? 'Moderate' : 'Poor'}
        />
        <StatCard
          label="Mean Absolute Error"
          value={accuracy?.mae?.toFixed(2) || 'N/A'}
          unit={selectedMetric === 'violations' ? '' : '%'}
        />
        <StatCard
          label="Predictions Made"
          value={accuracy?.totalPredictions || 0}
        />
        <StatCard
          label="Within 5% Accuracy"
          value={`${((accuracy?.within5Percent || 0) * 100).toFixed(0)}%`}
        />
      </div>
    </div>
  );
}
```

### 4.5 Deliverables

| Deliverable | Type | Priority |
|-------------|------|----------|
| Update TABS constant | Frontend | P0 |
| `SurvivalTab.tsx` | Frontend | P0 |
| `ABTestingTab.tsx` | Frontend | P0 |
| `PredictionsTab.tsx` | Frontend | P0 |
| `OutcomesTab.tsx` | Frontend | P0 |
| TanStack Query hooks for new APIs | Frontend | P0 |
| Integration tests | Frontend | P1 |

---

## Phase 5: Factorial Design & Advanced Experiments

**Goal:** Enable multi-factor experiments for schedule optimization.

### 5.1 Factorial Design Service

```python
# backend/app/analytics/factorial_design.py

"""
Design of Experiments (DOE) for scheduling optimization.

Enables systematic exploration of multiple factors (algorithm, constraints,
parameters) to identify optimal configurations.
"""

from dataclasses import dataclass
from typing import Literal
import numpy as np
import pandas as pd
from pyDOE2 import fullfact, ff2n, pbdesign, ccdesign


@dataclass
class Factor:
    """A factor in the experiment."""
    name: str
    levels: list  # e.g., ['greedy', 'cpSat', 'hybrid'] or [0.5, 0.75, 1.0]
    factor_type: Literal['categorical', 'continuous']


@dataclass
class ExperimentDesign:
    """A designed experiment specification."""
    design_type: str  # 'full_factorial', 'fractional', 'response_surface'
    factors: list[Factor]
    runs: pd.DataFrame  # Each row is an experimental run
    total_runs: int
    resolution: int | None  # For fractional factorials
    aliasing_structure: dict | None


class FactorialDesignService:
    """Generate and analyze factorial experiments."""

    def full_factorial(self, factors: list[Factor]) -> ExperimentDesign:
        """
        Generate full factorial design.

        Every combination of factor levels is tested.
        Runs = product of all level counts.

        Example:
            3 algorithms × 2 constraint sets × 2 timeout levels = 12 runs
        """
        level_counts = [len(f.levels) for f in factors]
        design_matrix = fullfact(level_counts)

        # Convert to actual factor values
        runs_data = []
        for row in design_matrix:
            run = {}
            for i, (factor, level_idx) in enumerate(zip(factors, row)):
                run[factor.name] = factor.levels[int(level_idx)]
            runs_data.append(run)

        return ExperimentDesign(
            design_type='full_factorial',
            factors=factors,
            runs=pd.DataFrame(runs_data),
            total_runs=len(runs_data),
            resolution=None,
            aliasing_structure=None,
        )

    def fractional_factorial(
        self,
        factors: list[Factor],
        resolution: int = 4,
    ) -> ExperimentDesign:
        """
        Generate fractional factorial design (2^(k-p)).

        Reduces runs while maintaining ability to estimate main effects.
        Resolution IV: Main effects not aliased with 2-factor interactions.

        Use when full factorial would require too many runs.
        """
        # Fractional factorial requires 2-level factors
        k = len(factors)
        design_matrix = ff2n(k)  # 2^k design, then we'll reduce

        # For now, use Plackett-Burman for screening if many factors
        if k > 7:
            design_matrix = pbdesign(k)

        # Map to factor levels
        runs_data = []
        for row in design_matrix:
            run = {}
            for i, (factor, level) in enumerate(zip(factors, row)):
                # Map -1/+1 to factor levels
                if level <= 0:
                    run[factor.name] = factor.levels[0]
                else:
                    run[factor.name] = factor.levels[-1]
            runs_data.append(run)

        return ExperimentDesign(
            design_type='fractional_factorial',
            factors=factors,
            runs=pd.DataFrame(runs_data),
            total_runs=len(runs_data),
            resolution=resolution,
            aliasing_structure=self._compute_aliasing(k, resolution),
        )

    def response_surface(
        self,
        factors: list[Factor],
        design_type: Literal['ccc', 'cci', 'ccf'] = 'ccc',
    ) -> ExperimentDesign:
        """
        Central Composite Design for response surface methodology.

        Enables modeling of nonlinear relationships and finding optima.

        Args:
            factors: Continuous factors only
            design_type: 'ccc' (circumscribed), 'cci' (inscribed), 'ccf' (face-centered)
        """
        k = len(factors)
        design_matrix = ccdesign(k, center=(4,), face=design_type)

        # Map coded values to actual factor levels
        runs_data = []
        for row in design_matrix:
            run = {}
            for i, (factor, coded_val) in enumerate(zip(factors, row)):
                # Map coded (-1, 0, +1, ±α) to actual values
                low, high = factor.levels[0], factor.levels[-1]
                mid = (low + high) / 2
                half_range = (high - low) / 2
                actual_val = mid + coded_val * half_range
                run[factor.name] = actual_val
            runs_data.append(run)

        return ExperimentDesign(
            design_type=f'response_surface_{design_type}',
            factors=factors,
            runs=pd.DataFrame(runs_data),
            total_runs=len(runs_data),
            resolution=None,
            aliasing_structure=None,
        )

    def analyze_factorial(
        self,
        design: ExperimentDesign,
        response: np.ndarray,
        response_name: str = 'coverage',
    ) -> dict:
        """
        Analyze factorial experiment results.

        Returns:
            - Main effects
            - Interaction effects (if full factorial)
            - ANOVA table
            - Optimal factor settings
        """
        import statsmodels.api as sm
        from statsmodels.formula.api import ols

        # Build data for analysis
        df = design.runs.copy()
        df[response_name] = response

        # Build formula for ANOVA
        factors = [f.name for f in design.factors]
        formula = f"{response_name} ~ " + " * ".join(factors)

        model = ols(formula, data=df).fit()
        anova_table = sm.stats.anova_lm(model, typ=2)

        # Extract main effects
        main_effects = {}
        for factor in design.factors:
            effect = df.groupby(factor.name)[response_name].mean()
            main_effects[factor.name] = effect.to_dict()

        # Find optimal settings
        optimal_idx = df[response_name].idxmax()
        optimal_settings = df.iloc[optimal_idx][factors].to_dict()

        return {
            'main_effects': main_effects,
            'anova_table': anova_table.to_dict(),
            'optimal_settings': optimal_settings,
            'optimal_response': df.iloc[optimal_idx][response_name],
            'r_squared': model.rsquared,
            'significant_factors': [
                f for f in factors
                if anova_table.loc[f, 'PR(>F)'] < 0.05
            ],
        }

    def _compute_aliasing(self, k: int, resolution: int) -> dict:
        """Compute aliasing structure for fractional factorial."""
        # Simplified aliasing info
        return {
            'resolution': resolution,
            'main_effects_clear': resolution >= 3,
            'two_factor_interactions_clear': resolution >= 4,
        }
```

### 5.2 Factorial Experiment UI

```typescript
// frontend/src/app/admin/scheduling/tabs/FactorialTab.tsx

export function FactorialTab() {
  const [factors, setFactors] = useState<Factor[]>([
    { name: 'algorithm', levels: ['greedy', 'cpSat', 'hybrid'], type: 'categorical' },
    { name: 'timeout_seconds', levels: [60, 180, 300], type: 'continuous' },
  ]);
  const [designType, setDesignType] = useState<'full' | 'fractional' | 'response_surface'>('full');

  const { data: design, isLoading: designLoading } = useFactorialDesign(factors, designType);
  const { data: results } = useFactorialResults(design?.id);

  return (
    <div className="space-y-6">
      {/* Factor configuration */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Experiment Factors</h3>

        <FactorEditor
          factors={factors}
          onChange={setFactors}
        />

        <div className="mt-4 flex items-center gap-4">
          <select
            value={designType}
            onChange={(e) => setDesignType(e.target.value as typeof designType)}
            className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white text-sm"
          >
            <option value="full">Full Factorial ({design?.totalRuns || '?'} runs)</option>
            <option value="fractional">Fractional Factorial (reduced runs)</option>
            <option value="response_surface">Response Surface (find optimum)</option>
          </select>

          <button
            onClick={() => generateDesign.mutate({ factors, designType })}
            disabled={generateDesign.isPending}
            className="px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white rounded-lg text-sm font-medium"
          >
            Generate Design
          </button>
        </div>
      </div>

      {/* Design matrix */}
      {design && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Experiment Design ({design.totalRuns} runs)
            </h3>
            <button
              onClick={() => runExperiment.mutate(design.id)}
              disabled={runExperiment.isPending}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium flex items-center gap-2"
            >
              <Play className="w-4 h-4" />
              Run All
            </button>
          </div>

          <DesignMatrixTable
            design={design}
            results={results}
          />
        </div>
      )}

      {/* Analysis results */}
      {results && (
        <>
          {/* Main effects plot */}
          <MainEffectsPlot
            effects={results.mainEffects}
            responseName="Coverage %"
          />

          {/* Interaction plot (if full factorial) */}
          {designType === 'full' && (
            <InteractionPlot
              data={results.interactions}
            />
          )}

          {/* ANOVA table */}
          <ANOVATable
            data={results.anovaTable}
            significanceLevel={0.05}
          />

          {/* Optimal settings */}
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-6">
            <h3 className="text-lg font-semibold text-emerald-400 mb-4">
              Optimal Configuration
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(results.optimalSettings).map(([factor, value]) => (
                <div key={factor} className="bg-slate-800 rounded-lg p-4">
                  <div className="text-sm text-slate-300">{factor}</div>
                  <div className="text-xl font-bold text-white">{value}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 text-emerald-400">
              Expected {results.responseName}: {results.optimalResponse.toFixed(2)}%
            </div>
          </div>
        </>
      )}
    </div>
  );
}
```

### 5.3 Deliverables

| Deliverable | Type | Priority |
|-------------|------|----------|
| `factorial_design.py` service | Backend | P1 |
| Factorial design API endpoints | Backend | P1 |
| `FactorialTab.tsx` | Frontend | P1 |
| `MainEffectsPlot.tsx` | Frontend | P1 |
| `InteractionPlot.tsx` | Frontend | P2 |
| `ANOVATable.tsx` | Frontend | P1 |
| Integration with experiment queue | Backend | P1 |

---

## Implementation Sequence

### Summary Timeline

| Phase | Description | Key Deliverables |
|-------|-------------|------------------|
| **Phase 1** | Data Collection Foundation | Outcome tables, survey UI, Excel import |
| **Phase 2** | Statistical Infrastructure | Hypothesis testing, Bayesian, survival services |
| **Phase 3** | Visualization Components | KM chart, forest plot, predicted vs actual |
| **Phase 4** | Dashboard Integration | New tabs: Outcomes, Survival, A/B, Predictions |
| **Phase 5** | Factorial Design | DOE service, factorial tab, optimization |

### Dependency Graph

```
Phase 1 (Data Collection)
    │
    ├──► Phase 2 (Stats Infrastructure)
    │        │
    │        └──► Phase 3 (Visualizations)
    │                  │
    │                  └──► Phase 4 (Dashboard Tabs)
    │                             │
    │                             └──► Phase 5 (Factorial Design)
    │
    └──► Can start collecting data immediately while building other phases
```

### Quick Wins (Can Do Now)

1. **Add statistical libraries** to requirements.txt
2. **Create hypothesis testing wrapper** using existing scipy
3. **Wire up existing chart components** to Metrics tab (currently showing placeholders)
4. **Add "Outcomes" tab** with basic survey form

---

## Appendix A: API Endpoint Specifications

### Outcomes API

```yaml
POST /api/v1/outcomes/surveys:
  description: Record a burnout survey
  body:
    resident_id: uuid
    emotional_exhaustion: float (0-54)
    depersonalization: float (0-30)
    personal_accomplishment: float (0-48)
    survey_date: date (optional, defaults to today)
  response:
    id: uuid
    burnout_score: float
    burnout_risk: enum (LOW, MODERATE, HIGH)

GET /api/v1/outcomes/surveys/{resident_id}:
  description: Get survey history for resident
  params:
    start_date: date (optional)
    end_date: date (optional)
  response:
    surveys: array of BurnoutSurvey

POST /api/v1/outcomes/events:
  description: Record an outcome event
  body:
    resident_id: uuid
    event_type: enum (burnout_survey, acgme_violation, sick_call, swap_request)
    event_date: date
    payload: object
    is_censored: boolean (optional)
  response:
    id: uuid
    created_at: datetime
```

### Statistical Analysis API

```yaml
POST /api/v1/analytics/hypothesis-test:
  description: Run hypothesis test
  body:
    test_type: enum (t-test-independent, t-test-paired, anova, chi-square)
    groups: array of arrays (numeric data)
    alpha: float (default 0.05)
    alternative: enum (two-sided, less, greater)
  response:
    test_name: string
    statistic: float
    p_value: float
    effect_size: float
    effect_size_interpretation: string
    confidence_interval: [float, float]
    power: float
    significant: boolean
    summary: string

POST /api/v1/analytics/bayesian-compare:
  description: Bayesian algorithm comparison
  body:
    group_a: array of floats
    group_b: array of floats
    metric_name: string
    rope_margin: float (default 0.1)
  response:
    posterior_mean: float
    credible_interval_95: [float, float]
    probability_of_superiority: float
    rope_decision: string
    summary: string

POST /api/v1/analytics/survival:
  description: Survival analysis
  body:
    analysis_type: enum (kaplan-meier, cox)
    durations: array of floats
    events: array of booleans
    group_labels: array of strings (optional)
    covariates: array of strings (for cox)
  response:
    curves: object (group -> curve data)
    log_rank_p_value: float (optional)
    hazard_ratios: array of HazardRatio (optional)
    summary: string

POST /api/v1/analytics/power:
  description: Power analysis / sample size calculation
  body:
    effect_size: float
    power: float (default 0.8)
    alpha: float (default 0.05)
    test_type: enum (t-test, anova, chi-square)
  response:
    required_n: integer
    explanation: string
```

### Predictions API

```yaml
POST /api/v1/predictions:
  description: Record a prediction
  body:
    schedule_id: uuid
    model_version: string
    predicted_coverage: float
    predicted_violations: integer
    coverage_ci_lower: float
    coverage_ci_upper: float
  response:
    id: uuid

PATCH /api/v1/predictions/{id}/actuals:
  description: Record actual outcomes for a prediction
  body:
    actual_coverage: float
    actual_violations: integer
  response:
    mae_coverage: float
    mae_violations: float

GET /api/v1/predictions/accuracy:
  description: Get prediction accuracy metrics
  params:
    metric: enum (coverage, violations, fairness)
    start_date: date
    end_date: date
  response:
    r_squared: float
    mae: float
    within_5_percent: float
    trend: array of {date, mae}
    calibration: array of {predicted_bin, actual_mean}
```

---

## Appendix B: Database Migration Plan

```python
# backend/alembic/versions/20260120_exp_analytics.py

"""Experimental analytics infrastructure.

Revision ID: 20260120_exp_analytics
Revises: [previous]
Create Date: 2026-01-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260120_exp_analytics'
down_revision = '[previous]'


def upgrade():
    # Outcome events (generic event log)
    op.create_table(
        'outcome_events',
        sa.Column('id', postgresql.UUID(), primary_key=True),
        sa.Column('resident_id', postgresql.UUID(), sa.ForeignKey('residents.id'), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('schedule_id', postgresql.UUID(), sa.ForeignKey('schedules.id')),
        sa.Column('block_number', sa.Integer()),
        sa.Column('payload', postgresql.JSONB(), server_default='{}'),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('recorded_by', postgresql.UUID(), sa.ForeignKey('users.id')),
        sa.Column('is_censored', sa.Boolean(), server_default='false'),
        sa.Column('censoring_reason', sa.String(100)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_outcome_events_resident', 'outcome_events', ['resident_id', 'event_date'])
    op.create_index('idx_outcome_events_type', 'outcome_events', ['event_type', 'event_date'])

    # Burnout surveys (specialized outcome)
    op.create_table(
        'burnout_surveys',
        sa.Column('id', postgresql.UUID(), primary_key=True),
        sa.Column('resident_id', postgresql.UUID(), sa.ForeignKey('residents.id'), nullable=False),
        sa.Column('survey_date', sa.Date(), nullable=False),
        sa.Column('emotional_exhaustion', sa.Numeric(4, 2)),
        sa.Column('depersonalization', sa.Numeric(4, 2)),
        sa.Column('personal_accomplishment', sa.Numeric(4, 2)),
        sa.Column('schedule_id', postgresql.UUID(), sa.ForeignKey('schedules.id')),
        sa.Column('current_rotation', sa.String(100)),
        sa.Column('weeks_on_rotation', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('idx_burnout_surveys_resident', 'burnout_surveys', ['resident_id', 'survey_date'])

    # Schedule predictions (for predicted vs actual tracking)
    op.create_table(
        'schedule_predictions',
        sa.Column('id', postgresql.UUID(), primary_key=True),
        sa.Column('schedule_id', postgresql.UUID(), sa.ForeignKey('schedules.id'), nullable=False),
        sa.Column('prediction_date', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('predicted_coverage', sa.Numeric(5, 2)),
        sa.Column('predicted_violations', sa.Integer()),
        sa.Column('predicted_fairness', sa.Numeric(5, 4)),
        sa.Column('predicted_burnout_risk', sa.Numeric(5, 4)),
        sa.Column('coverage_ci_lower', sa.Numeric(5, 2)),
        sa.Column('coverage_ci_upper', sa.Numeric(5, 2)),
        sa.Column('violations_ci_lower', sa.Integer()),
        sa.Column('violations_ci_upper', sa.Integer()),
        sa.Column('actual_coverage', sa.Numeric(5, 2)),
        sa.Column('actual_violations', sa.Integer()),
        sa.Column('actual_fairness', sa.Numeric(5, 4)),
        sa.Column('mae_coverage', sa.Numeric(5, 2)),
        sa.Column('mae_violations', sa.Numeric(5, 2)),
        sa.Column('evaluated_at', sa.DateTime(timezone=True)),
    )
    op.create_index('idx_predictions_schedule', 'schedule_predictions', ['schedule_id', 'prediction_date'])


def downgrade():
    op.drop_table('schedule_predictions')
    op.drop_table('burnout_surveys')
    op.drop_table('outcome_events')
```

---

## Appendix C: Testing Strategy

### Backend Statistical Tests

```python
# backend/tests/analytics/test_hypothesis_testing.py

import numpy as np
import pytest
from app.analytics.hypothesis_testing import HypothesisTestingService


class TestHypothesisTesting:
    """Test suite for frequentist hypothesis testing."""

    @pytest.fixture
    def service(self):
        return HypothesisTestingService(alpha=0.05)

    def test_t_test_significant_difference(self, service):
        """Two groups with known significant difference."""
        # Group A: mean=80, sd=5
        group_a = np.random.normal(80, 5, 50)
        # Group B: mean=75, sd=5 (different mean)
        group_b = np.random.normal(75, 5, 50)

        result = service.independent_t_test(group_a, group_b)

        assert result.significant is True
        assert result.p_value < 0.05
        assert result.effect_size > 0.5  # Large effect expected

    def test_t_test_no_difference(self, service):
        """Two groups from same distribution."""
        group_a = np.random.normal(80, 5, 50)
        group_b = np.random.normal(80, 5, 50)

        result = service.independent_t_test(group_a, group_b)

        # Should usually not be significant (type I error rate ~5%)
        # Can't assert definitively due to randomness
        assert result.p_value > 0.001  # Very unlikely to be highly significant

    def test_effect_size_interpretation(self, service):
        """Effect size categories are correct."""
        # Negligible effect
        result = service.independent_t_test(
            np.array([1, 2, 3, 4, 5]),
            np.array([1.1, 2.1, 3.1, 4.1, 5.1])
        )
        assert result.effect_size_interpretation in ['negligible', 'small']

    def test_sample_size_calculation(self, service):
        """Power analysis returns reasonable sample sizes."""
        n = service.calculate_sample_size(
            effect_size=0.5,  # Medium effect
            power=0.8,
            alpha=0.05,
        )

        # For d=0.5, power=0.8, n should be around 64 per group
        assert 50 < n < 80


# backend/tests/analytics/test_survival_analysis.py

class TestSurvivalAnalysis:
    """Test suite for survival analysis."""

    def test_kaplan_meier_single_group(self, service):
        """Basic KM curve estimation."""
        durations = np.array([10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
        events = np.array([1, 1, 1, 0, 1, 0, 1, 1, 0, 1])  # 1=event, 0=censored

        result = service.kaplan_meier(durations, events)

        assert 'Overall' in result.curves
        curve = result.curves['Overall']
        assert curve.survival_probabilities[0] == 1.0  # Starts at 100%
        assert curve.survival_probabilities[-1] < 1.0  # Decreases
        assert curve.events_observed == 7
        assert curve.censored_count == 3

    def test_kaplan_meier_group_comparison(self, service):
        """Compare two groups with log-rank test."""
        # Group A: better survival
        durations_a = np.array([50, 60, 70, 80, 90, 100, 110, 120])
        events_a = np.array([1, 0, 1, 0, 1, 0, 1, 0])

        # Group B: worse survival
        durations_b = np.array([10, 20, 30, 40, 50, 60, 70, 80])
        events_b = np.array([1, 1, 1, 1, 1, 1, 0, 1])

        durations = np.concatenate([durations_a, durations_b])
        events = np.concatenate([events_a, events_b])
        groups = np.array(['A'] * 8 + ['B'] * 8)

        result = service.kaplan_meier(durations, events, groups)

        assert 'A' in result.curves
        assert 'B' in result.curves
        assert result.log_rank_p_value is not None
        # Groups are clearly different
        assert result.log_rank_p_value < 0.1
```

---

*This roadmap provides a comprehensive path from current state to full experimental analytics capability. Start with Phase 1 data collection immediately—everything else depends on having outcome data to analyze.*
