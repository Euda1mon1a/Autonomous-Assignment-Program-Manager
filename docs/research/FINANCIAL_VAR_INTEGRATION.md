# Financial Value-at-Risk (VaR) Integration for Residency Scheduling

> **Status**: Research & Design
> **Version**: 1.0
> **Last Updated**: 2025-12-26
> **Research Domain**: Financial Risk Management → Workforce Resilience
> **Target**: Cross-disciplinary resilience framework enhancement

---

## Executive Summary

This research document explores the application of **Financial Value-at-Risk (VaR)** methodologies—originally developed for quantifying market risk in trading portfolios—to medical residency scheduling. By treating schedule elements (coverage, compliance, workload) as "risky assets" subject to uncertainty, we can leverage decades of financial risk management research to predict, measure, and mitigate scheduling failures.

**Key Innovation**: Just as financial institutions ask "What is the worst expected loss over the next 10 days with 95% confidence?", residency programs can ask "What is the worst expected coverage shortfall over the next 4 weeks with 95% confidence?" This paradigm shift enables:

- **Quantitative risk budgeting** across rotations and time periods
- **Portfolio optimization** for schedule diversity and correlation management
- **Stress testing** against extreme scenarios (pandemic, mass deployment, sudden departures)
- **Tail risk management** via Expected Shortfall (CVaR) for "black swan" events
- **Regulatory compliance** through transparent, auditable risk metrics

### Cross-Disciplinary Mapping

| Financial Concept | Scheduling Analog | Benefit |
|-------------------|-------------------|---------|
| **Portfolio VaR** | Schedule risk across all rotations | Holistic risk view |
| **Asset volatility** | Workload/coverage variance | Stability measurement |
| **Correlation** | Cross-rotation dependencies | Diversification guidance |
| **Stress testing** | Extreme event scenarios | Contingency validation |
| **Expected Shortfall** | Tail risk (catastrophic failures) | Black swan preparation |
| **Risk budgeting** | Allocation of "risk capacity" | Resource optimization |
| **Monte Carlo simulation** | Schedule scenario generation | Probabilistic forecasting |

---

## Table of Contents

1. [Background: VaR in Financial Risk Management](#background-var-in-financial-risk-management)
2. [VaR Calculation Methodologies](#var-calculation-methodologies)
3. [Expected Shortfall (CVaR) for Tail Risk](#expected-shortfall-cvar-for-tail-risk)
4. [Stress Testing Framework](#stress-testing-framework)
5. [Risk Aggregation Across Portfolios](#risk-aggregation-across-portfolios)
6. [Mapping VaR to Scheduling Risk](#mapping-var-to-scheduling-risk)
7. [Monte Carlo Simulation for Schedule Scenarios](#monte-carlo-simulation-for-schedule-scenarios)
8. [Risk Budgeting for Workload Distribution](#risk-budgeting-for-workload-distribution)
9. [Mathematical Formulations](#mathematical-formulations)
10. [Implementation Architecture](#implementation-architecture)
11. [Code Integration Points](#code-integration-points)
12. [Implementation Roadmap](#implementation-roadmap)
13. [References](#references)

---

## Background: VaR in Financial Risk Management

### Definition

**Value-at-Risk (VaR)** answers the question: *"What is the maximum loss I can expect over a given time horizon at a specified confidence level?"*

Formally: VaR(α) is the α-quantile of the loss distribution, where α is the confidence level (typically 95% or 99%).

**Example**: A trading desk with 1-day 95% VaR of $10 million expects that on 95% of days, losses will not exceed $10 million. Conversely, on 5% of days (roughly 1 in 20), losses may exceed this threshold.

### Historical Context

- **1990s**: J.P. Morgan popularizes VaR via RiskMetrics™ methodology
- **1996**: Basel Committee adopts VaR for bank capital requirements (Basel II)
- **2008 Financial Crisis**: VaR criticized for underestimating tail risk; Expected Shortfall gains prominence
- **2012**: Basel III introduces Expected Shortfall (ES) to complement VaR
- **2025**: VaR remains standard for daily risk monitoring; ES used for regulatory capital

### Advantages

1. **Single number simplicity**: Senior management can understand "We're at risk for $X"
2. **Comparability**: Risk across asset classes reduced to common metric
3. **Resource allocation**: VaR guides capital reserve sizing
4. **Regulatory acceptance**: Basel framework standardizes calculation

### Limitations

1. **Not coherent**: VaR violates subadditivity (portfolio VaR can exceed sum of individual VaRs)
2. **Ignores tail severity**: VaR answers "how often" but not "how bad"
3. **Model risk**: Different methodologies yield different VaR estimates
4. **Procyclical**: Increases during crises when volatility spikes (reactive, not proactive)

---

## VaR Calculation Methodologies

Financial institutions use three primary VaR calculation methods, each with distinct strengths and weaknesses.

### 1. Historical Simulation VaR

**Concept**: Use historical data directly without distributional assumptions. Apply past risk factor changes to current positions and identify the worst losses.

**Algorithm**:
1. Collect historical data (e.g., last 252 trading days)
2. Compute daily returns/changes
3. Apply these returns to current portfolio
4. Sort resulting P&L distribution
5. VaR = percentile corresponding to confidence level

**Example (Scheduling)**:
```python
# Historical weekly coverage shortfalls over past year (52 weeks)
historical_shortfalls = [0, 0, 1, 0, 2, 0, 0, 3, 0, 1, ...]  # hours understaffed

# 95% VaR: 5th percentile (worst 5% of weeks)
var_95 = np.percentile(historical_shortfalls, 95)
# Result: "We expect coverage shortfalls ≤ 4 hours on 95% of weeks"
```

**Strengths**:
- No distributional assumptions (captures fat tails, skewness naturally)
- Easy to explain and implement
- Incorporates actual market behavior

**Weaknesses**:
- Requires extensive historical data
- Assumes future resembles past (structural breaks problematic)
- Slow to react to regime changes
- Sample size determines accuracy

**Scheduling Application**: Use historical schedule violations (coverage gaps, ACGME breaches, swap failures) to estimate future risk.

---

### 2. Parametric (Variance-Covariance) VaR

**Concept**: Assume returns follow normal distribution. VaR calculated from mean and standard deviation.

**Formula**:
```
VaR(α) = μ + σ × Φ⁻¹(α)
```

Where:
- μ = mean return (often assumed 0 for short horizons)
- σ = standard deviation (volatility)
- Φ⁻¹(α) = inverse cumulative normal (e.g., -1.645 for 95% one-tailed)

**For portfolio**:
```
VaR_portfolio = √(w' Σ w) × Φ⁻¹(α)
```

Where:
- w = vector of position weights
- Σ = covariance matrix
- w' = transpose of w

**Example (Scheduling)**:
```python
# Weekly hours per resident (target = 60, σ = 8)
mu = 60
sigma = 8
confidence = 0.95

# 95% VaR for weekly hours exceeding target
z_score = norm.ppf(confidence)  # 1.645 for 95%
var_95 = mu + sigma * z_score   # 60 + 8 × 1.645 = 73.16 hours

# Interpretation: 95% of weeks, hours won't exceed 73.16
```

**Strengths**:
- Computationally fast (closed-form solution)
- Works well for linear portfolios (e.g., equities)
- Incorporates correlations via covariance matrix
- Minimal data requirements

**Weaknesses**:
- Normality assumption often violated (fat tails, skewness)
- Inaccurate for non-linear instruments (options)
- Underestimates tail risk

**Scheduling Application**: Model resident workload as normally distributed; use covariance to capture correlation between rotations.

---

### 3. Monte Carlo Simulation VaR

**Concept**: Generate thousands of random scenarios, re-price portfolio under each scenario, build P&L distribution, extract VaR percentile.

**Algorithm**:
1. Define stochastic process for risk factors (e.g., geometric Brownian motion)
2. Simulate 10,000+ scenarios using random sampling
3. Re-price portfolio under each scenario
4. Sort P&L results
5. VaR = percentile of simulated distribution

**Example (Scheduling)**:
```python
import numpy as np

def monte_carlo_coverage_var(n_simulations=10000, weeks=4, confidence=0.95):
    """
    Simulate coverage shortfalls over 4-week period.

    Risk factors:
    - Daily case arrivals (Poisson)
    - Resident absences (Binomial)
    - Average case duration (Log-Normal)
    """
    shortfalls = []

    for _ in range(n_simulations):
        total_shortfall = 0
        for week in range(weeks):
            # Simulate case arrivals (mean=50/week, Poisson)
            cases = np.random.poisson(lam=50)

            # Simulate resident absences (10 residents, 5% absence rate)
            absences = np.random.binomial(n=10, p=0.05)

            # Simulate case durations (mean=2h, log-normal)
            durations = np.random.lognormal(mean=np.log(2), sigma=0.3, size=cases)

            # Total demand
            demand_hours = durations.sum()

            # Available capacity (10 - absences) × 60 hours/week
            capacity_hours = (10 - absences) * 60

            # Shortfall (if demand exceeds capacity)
            week_shortfall = max(0, demand_hours - capacity_hours)
            total_shortfall += week_shortfall

        shortfalls.append(total_shortfall)

    # VaR: 95th percentile of shortfalls
    var_95 = np.percentile(shortfalls, 95)
    return var_95

# Result: "95% confident coverage shortfall won't exceed X hours over 4 weeks"
```

**Strengths**:
- Handles non-linear payoffs (options, derivatives)
- Captures complex dependencies
- Can model any distributional assumption
- Flexible for exotic scenarios

**Weaknesses**:
- Computationally expensive (millions of simulations)
- Model risk (garbage in, garbage out)
- Requires calibration to market data
- Black box nature complicates explanation

**Scheduling Application**: Most powerful method for residency scheduling—can model simultaneous risks (absences, emergencies, procedural delays).

---

## Expected Shortfall (CVaR) for Tail Risk

### Motivation: Beyond VaR

VaR has a critical flaw: **it ignores the severity of losses beyond the VaR threshold**.

**Example**: Two portfolios with identical 95% VaR of $10M:
- Portfolio A: Worst 5% of outcomes range $10M-$12M loss
- Portfolio B: Worst 5% of outcomes range $10M-$100M loss

VaR treats these as equivalent risk. **Expected Shortfall** distinguishes them.

### Definition

**Expected Shortfall (ES)**, also called **Conditional VaR (CVaR)** or **Average VaR (AVaR)**, is the expected loss given that VaR has been exceeded.

**Formula**:
```
ES(α) = E[Loss | Loss > VaR(α)]
```

In plain terms: ES answers "If we exceed VaR (worst 5% of days), what's the average loss?"

**Calculation (discrete historical data)**:
```python
def expected_shortfall(losses, confidence=0.95):
    """Calculate ES from historical loss distribution."""
    var = np.percentile(losses, confidence * 100)
    tail_losses = losses[losses >= var]
    es = tail_losses.mean()
    return es

# Example
losses = np.array([0, 1, 2, 3, 5, 8, 15, 25, 40, 100])  # Sorted
var_90 = np.percentile(losses, 90)  # 40
es_90 = losses[losses >= var_90].mean()  # (40 + 100) / 2 = 70
```

### Advantages of ES over VaR

1. **Coherent risk measure**: Satisfies subadditivity (ES of portfolio ≤ sum of ES)
2. **Captures tail severity**: Accounts for catastrophic losses
3. **Convex optimization**: Easier to optimize portfolios using ES
4. **Regulatory preference**: Basel III mandates ES for market risk capital

### 2025 Regulatory Context

**Basel III Fundamental Review of Trading Book (FRTB)**:
- Banks must report ES at 97.5% confidence (not VaR at 99%)
- ES captures "stressed period" tail behavior
- Liquidity horizons vary by asset class (10 days for equities, 120 days for structured credit)

### Scheduling Application: Coverage CVaR

**Scenario**: Residency program has 95% VaR of 4-hour weekly coverage shortfall.

**Question**: When shortfalls occur (worst 5% of weeks), how bad are they on average?

```python
# Historical weekly shortfalls (hours)
shortfalls = [0, 0, 1, 0, 0, 2, 0, 3, 0, 0, 1, 5, 0, 8, 0, 0, 12, ...]

# VaR: 95th percentile
var_95 = np.percentile(shortfalls, 95)  # 8 hours

# CVaR: Average of tail (worst 5%)
tail_shortfalls = shortfalls[shortfalls >= var_95]
cvar_95 = tail_shortfalls.mean()  # 14 hours

# Interpretation:
# - 95% of weeks, shortfalls ≤ 8 hours (VaR)
# - When shortfalls occur (5% of weeks), average = 14 hours (CVaR)
```

**Actionable Insight**: Maintain contingency reserves (float pool, per diem budget) sized to CVaR (14 hours), not just VaR (8 hours).

---

## Stress Testing Framework

### Purpose

Stress tests complement VaR by exploring **extreme but plausible scenarios** that may lie outside historical experience. VaR asks "What happens 95% of the time?" Stress testing asks "What happens when things go very wrong?"

### Federal Reserve 2025 Stress Test Scenarios

The Federal Reserve's 2025 stress tests provide a template for rigorous scenario analysis:

**Severely Adverse Scenario**:
- Severe global recession with GDP decline
- Unemployment peaks at 10% (5.9 percentage point increase)
- Residential/commercial real estate declines 30-40%
- Inflation falls from 2.7% to 1.3%
- Short-term rates drop from 4.4% to 0.1%

**Key Components**:
1. **Baseline scenario**: Expected conditions
2. **Adverse scenario**: Moderate recession
3. **Severely adverse**: Worst-case recession
4. **Exploratory scenarios**: Novel risks (e.g., nonbank financial sector shock)

### Stress Testing Methodologies

#### 1. Scenario Analysis

**Definition**: Create hypothetical events and measure impact.

**Financial Examples**:
- "What if interest rates rise 200 basis points overnight?"
- "What if equity markets drop 30%?"
- "What if credit spreads widen to 2008 levels?"

**Scheduling Examples**:
- **Pandemic scenario**: 30% of residents infected simultaneously for 2 weeks
- **Mass deployment**: 4 residents deployed on 48-hour notice (military TDY)
- **Exodus scenario**: 2 residents resign abruptly mid-year
- **Procedural crisis**: Major trauma event requiring 3 residents for 12 hours
- **ACGME audit**: External review reveals 80-hour violations requiring immediate remediation

#### 2. Sensitivity Analysis

**Definition**: Vary single parameter while holding others constant.

**Examples**:
- Vary resident absence rate: 1%, 5%, 10%, 20%
- Vary case arrival rate: +10%, +20%, +50%
- Vary procedure duration: Mean ± 1σ, ± 2σ, ± 3σ

```python
def sensitivity_analysis_coverage(base_residents=10, base_cases=50):
    """Test sensitivity to resident count."""
    results = []
    for residents in range(6, 15):  # Vary ±40%
        shortage_hours = calculate_coverage_gap(
            residents=residents,
            weekly_cases=base_cases
        )
        results.append({
            'residents': residents,
            'shortage': shortage_hours,
            'change_pct': (residents - base_residents) / base_residents * 100
        })
    return results
```

#### 3. Reverse Stress Testing

**Definition**: Work backward—identify scenarios that would cause system failure, then assess likelihood.

**Process**:
1. Define "failure" (e.g., complete coverage breakdown for 24+ hours)
2. Identify necessary conditions (e.g., 6+ residents unavailable + surge in cases)
3. Estimate probability of conditions aligning
4. Design mitigations to prevent failure

**Example**:
```
Failure mode: Zero attending coverage for orthopedic trauma

Required conditions:
- 2 ortho attendings on vacation (scheduled)
- 1 ortho attending sick (5% daily probability)
- 1 ortho attending called away for family emergency (1% daily)
- Backup from neighboring hospital unavailable (20% probability on weekends)

P(simultaneous) = 0.05 × 0.01 × 0.20 = 0.0001 (0.01%)
Expected frequency: 3.65 days/year (~4 incidents)

Mitigation: Cross-train general surgery attendings for ortho backup
```

### Scheduling Stress Test Architecture

```python
class ScheduleStressTest:
    """Stress testing framework for schedule resilience."""

    def __init__(self, schedule: Schedule):
        self.schedule = schedule
        self.scenarios = []

    def add_scenario(self, name: str, shock_function: callable, severity: str):
        """Register stress scenario."""
        self.scenarios.append({
            'name': name,
            'shock': shock_function,
            'severity': severity
        })

    def run_all_scenarios(self) -> dict:
        """Execute all stress tests."""
        results = {}
        for scenario in self.scenarios:
            shocked_schedule = scenario['shock'](self.schedule)
            results[scenario['name']] = {
                'coverage_gaps': self.measure_coverage_gaps(shocked_schedule),
                'acgme_violations': self.measure_acgme_violations(shocked_schedule),
                'burnout_risk': self.measure_burnout_risk(shocked_schedule),
                'severity': scenario['severity']
            }
        return results

    # Shock functions
    def pandemic_shock(self, schedule: Schedule) -> Schedule:
        """30% simultaneous infection for 2 weeks."""
        residents = schedule.get_all_residents()
        infected = random.sample(residents, k=int(len(residents) * 0.3))
        for resident in infected:
            schedule.mark_unavailable(resident, duration=timedelta(weeks=2))
        return schedule

    def deployment_shock(self, schedule: Schedule) -> Schedule:
        """4 residents deployed on 48h notice."""
        # Implementation...
        pass
```

---

## Risk Aggregation Across Portfolios

### Challenge: Portfolio Effects

Individual rotation risks don't simply add—they interact through **correlations**.

**Financial Analogy**:
- Portfolio of uncorrelated assets: Diversification reduces risk
- Portfolio of highly correlated assets: Diversification fails (2008 crisis)

**Scheduling Analogy**:
- Uncorrelated rotations: ER workload independent of surgical OR load
- Correlated rotations: Flu season simultaneously strains ER + ICU + inpatient wards

### Variance-Covariance Method

**Portfolio VaR Formula**:
```
σ_portfolio = √(w' Σ w)
```

Where:
- w = vector of rotation "weights" (time allocation)
- Σ = covariance matrix of rotation risks

**Example**:
```python
import numpy as np

# Three rotations: ER, ICU, Clinic
weights = np.array([0.4, 0.4, 0.2])  # 40% ER, 40% ICU, 20% Clinic

# Weekly workload standard deviations (hours)
sigma_er = 12
sigma_icu = 10
sigma_clinic = 5

# Correlation matrix (estimated from historical data)
correlation = np.array([
    [1.0, 0.6, 0.2],   # ER correlated with ICU (0.6), weakly with Clinic (0.2)
    [0.6, 1.0, 0.3],   # ICU moderately correlated with Clinic (0.3)
    [0.2, 0.3, 1.0]    # Clinic relatively independent
])

# Covariance matrix: Σ = D × R × D
# where D = diag([σ_er, σ_icu, σ_clinic])
stdevs = np.array([sigma_er, sigma_icu, sigma_clinic])
covariance = np.outer(stdevs, stdevs) * correlation

# Portfolio variance
portfolio_variance = weights.T @ covariance @ weights
portfolio_stdev = np.sqrt(portfolio_variance)  # ~8.9 hours

# 95% VaR (assuming normality)
var_95 = 1.645 * portfolio_stdev  # ~14.6 hours
```

**Insight**: Portfolio risk (14.6h) is **less** than weighted average of individual risks (0.4×12 + 0.4×10 + 0.2×5 = 9.8h × 1.645 = 16.1h) due to diversification.

### Copula-Based Aggregation (Advanced)

**Limitation of Correlation**: Linear correlation misses tail dependencies.

**Example**: ER and ICU may be uncorrelated under normal conditions but become highly correlated during pandemics (both surge simultaneously).

**Copulas** separate:
1. Marginal distributions (individual rotation risk profiles)
2. Dependence structure (how rotations move together)

**Common Copula Families**:
- **Gaussian copula**: Symmetric, no tail dependence
- **Student-t copula**: Symmetric with tail dependence (crisis correlations)
- **Clayton copula**: Lower tail dependence (shared downside risk)
- **Gumbel copula**: Upper tail dependence (shared upside risk)

**2025 Research**: Copula-DCC-GARCH models provide superior VaR/CVaR estimates during volatile periods by capturing time-varying correlations and asymmetric tail behavior.

### Downside Risk Approaches

**Traditional portfolio theory** (Markowitz) uses **standard deviation** as risk measure—penalizes both upside and downside volatility equally.

**Downside risk** (semi-variance) only penalizes returns **below target**.

**Formula**:
```
Downside Risk = √(E[min(0, R - T)²])
```

Where:
- R = return (or workload)
- T = target threshold

**Scheduling Application**:
```python
def calculate_downside_risk(weekly_hours, target=60):
    """Only count hours exceeding safe target."""
    excess_hours = np.maximum(0, weekly_hours - target)
    downside_variance = (excess_hours ** 2).mean()
    downside_risk = np.sqrt(downside_variance)
    return downside_risk

# Example
hours = np.array([58, 62, 75, 59, 80, 61, 70])
target = 60

# Standard deviation: 8.2 (penalizes 58h same as 75h)
std_dev = hours.std()

# Downside risk: 6.8 (only penalizes 75h, 80h, 70h)
downside = calculate_downside_risk(hours, target)
```

---

## Mapping VaR to Scheduling Risk

### Coverage VaR

**Definition**: Maximum expected coverage shortfall (hours) over planning horizon at given confidence level.

**Calculation**:
```python
def coverage_var(
    historical_shortfalls: list[float],
    confidence: float = 0.95,
    horizon_weeks: int = 4
) -> float:
    """
    Calculate Coverage VaR for given time horizon.

    Args:
        historical_shortfalls: Weekly coverage gaps (hours)
        confidence: Confidence level (0.95 = 95%)
        horizon_weeks: Planning horizon

    Returns:
        VaR estimate (hours of coverage risk)
    """
    # Aggregate to horizon (sum of weekly shortfalls)
    n_weeks = len(historical_shortfalls)
    horizon_shortfalls = []

    for i in range(n_weeks - horizon_weeks + 1):
        period_shortfall = sum(historical_shortfalls[i:i+horizon_weeks])
        horizon_shortfalls.append(period_shortfall)

    # VaR = percentile of aggregated distribution
    var = np.percentile(horizon_shortfalls, confidence * 100)
    return var

# Usage
weekly_gaps = [0, 1, 0, 2, 0, 0, 3, ...]  # 52 weeks historical
coverage_var_4wk = coverage_var(weekly_gaps, confidence=0.95, horizon_weeks=4)
# Result: "95% confident 4-week coverage gap won't exceed 8 hours"
```

**Dashboard Metric**:
```
Coverage VaR (4-week, 95%): 8.2 hours
Status: GREEN (within 10-hour contingency budget)
```

### Compliance VaR

**Definition**: Probability-weighted ACGME violation severity over planning horizon.

**Metrics**:
- **80-hour VaR**: Max expected weekly hours for individual resident
- **1-in-7 VaR**: Max expected consecutive days without 24-hour break
- **Supervision VaR**: Min expected supervision ratio (faculty:residents)

**Example (80-hour rule)**:
```python
def acgme_80hour_var(
    resident_hours_history: dict[str, list[float]],
    confidence: float = 0.99
) -> dict:
    """
    Calculate ACGME 80-hour compliance VaR.

    Returns:
        Dictionary of {resident_id: VaR_hours}
    """
    var_by_resident = {}
    for resident_id, weekly_hours in resident_hours_history.items():
        var = np.percentile(weekly_hours, confidence * 100)
        var_by_resident[resident_id] = var

    return var_by_resident

# Usage
history = {
    'R001': [65, 72, 68, 75, 70, 67, 71, ...],  # 52 weeks
    'R002': [60, 78, 62, 74, 69, 73, 66, ...],
    # ...
}

var_99 = acgme_80hour_var(history, confidence=0.99)
# Result: {'R001': 78.3, 'R002': 79.1, ...}

# Alert if any VaR > 80
violations = {r: v for r, v in var_99.items() if v > 80}
```

**Regulatory Reporting**:
- **Internal threshold**: 95% VaR < 75 hours (buffer for safety)
- **Regulatory threshold**: 99% VaR < 80 hours (hard limit)

### Workload VaR

**Definition**: Maximum expected workload imbalance (std dev of hours across residents).

**Goal**: Ensure equitable distribution—low workload variance means fair scheduling.

```python
def workload_distribution_var(
    weekly_hours_matrix: np.ndarray,
    confidence: float = 0.95
) -> float:
    """
    Calculate VaR for workload inequality.

    Args:
        weekly_hours_matrix: Shape (weeks, residents)

    Returns:
        VaR of weekly workload standard deviation
    """
    # Calculate std dev across residents for each week
    weekly_stdevs = weekly_hours_matrix.std(axis=1)

    # VaR = percentile of std dev distribution
    var = np.percentile(weekly_stdevs, confidence * 100)
    return var

# Example
hours_matrix = np.array([
    [60, 65, 58, 70, 62],  # Week 1: 5 residents
    [62, 68, 75, 60, 65],  # Week 2
    # ... 52 weeks
])

inequality_var = workload_distribution_var(hours_matrix, 0.95)
# Result: "95% of weeks, workload std dev ≤ 6.2 hours"
# Lower VaR = more equitable scheduling
```

---

## Monte Carlo Simulation for Schedule Scenarios

### Why Monte Carlo for Scheduling?

Medical scheduling involves **multiple stochastic processes**:
1. **Patient arrivals**: Random (Poisson process)
2. **Procedure durations**: Variable (Log-normal distribution)
3. **Resident absences**: Probabilistic (Binomial: sick, leave, deployment)
4. **Emergency cases**: Rare but high-impact (Extreme value distribution)

**Monte Carlo** captures interactions between these random variables to produce realistic scenario distributions.

### Algorithm Architecture

```python
class ScheduleMonteCarloSimulator:
    """
    Monte Carlo simulation for schedule risk analysis.
    """

    def __init__(
        self,
        n_simulations: int = 10000,
        time_horizon_weeks: int = 4,
        seed: int = 42
    ):
        self.n_simulations = n_simulations
        self.time_horizon = time_horizon_weeks
        np.random.seed(seed)

    def simulate_coverage_scenarios(
        self,
        base_schedule: Schedule,
        risk_factors: dict
    ) -> SimulationResults:
        """
        Generate scenarios and calculate risk metrics.

        Args:
            base_schedule: Current schedule
            risk_factors: Dict of stochastic parameters
                - case_arrival_rate: λ (Poisson)
                - case_duration_params: (μ, σ) for log-normal
                - absence_probability: p (Binomial)
                - emergency_rate: λ (Poisson)

        Returns:
            SimulationResults with VaR, CVaR, percentiles
        """
        results = {
            'coverage_shortfalls': [],
            'acgme_violations': [],
            'max_resident_hours': [],
            'workload_inequality': []
        }

        for sim in range(self.n_simulations):
            scenario_schedule = self._generate_scenario(
                base_schedule,
                risk_factors
            )

            # Measure outcomes
            results['coverage_shortfalls'].append(
                self._measure_coverage_gap(scenario_schedule)
            )
            results['acgme_violations'].append(
                self._count_acgme_violations(scenario_schedule)
            )
            results['max_resident_hours'].append(
                self._max_weekly_hours(scenario_schedule)
            )
            results['workload_inequality'].append(
                self._workload_std_dev(scenario_schedule)
            )

        return self._calculate_risk_metrics(results)

    def _generate_scenario(
        self,
        base_schedule: Schedule,
        risk_factors: dict
    ) -> Schedule:
        """Generate single stochastic scenario."""
        scenario = base_schedule.copy()

        for week in range(self.time_horizon):
            # Simulate patient arrivals
            n_cases = np.random.poisson(
                risk_factors['case_arrival_rate']
            )

            # Simulate case durations
            durations = np.random.lognormal(
                mean=np.log(risk_factors['case_duration_params'][0]),
                sigma=risk_factors['case_duration_params'][1],
                size=n_cases
            )

            # Simulate resident absences
            residents = scenario.get_available_residents(week)
            absences = np.random.binomial(
                n=len(residents),
                p=risk_factors['absence_probability']
            )
            absent_residents = random.sample(residents, k=absences)

            # Simulate emergencies
            n_emergencies = np.random.poisson(
                risk_factors['emergency_rate']
            )

            # Update scenario schedule
            scenario.apply_shocks(
                week=week,
                cases=n_cases,
                durations=durations,
                absences=absent_residents,
                emergencies=n_emergencies
            )

        return scenario

    def _calculate_risk_metrics(self, results: dict) -> SimulationResults:
        """Calculate VaR, CVaR, and percentiles from simulation."""
        metrics = {}

        for metric_name, values in results.items():
            values_array = np.array(values)

            metrics[metric_name] = {
                'mean': values_array.mean(),
                'std': values_array.std(),
                'var_95': np.percentile(values_array, 95),
                'var_99': np.percentile(values_array, 99),
                'cvar_95': values_array[values_array >= np.percentile(values_array, 95)].mean(),
                'cvar_99': values_array[values_array >= np.percentile(values_array, 99)].mean(),
                'percentiles': {
                    '50': np.percentile(values_array, 50),
                    '75': np.percentile(values_array, 75),
                    '90': np.percentile(values_array, 90),
                    '95': np.percentile(values_array, 95),
                    '99': np.percentile(values_array, 99),
                    '99.9': np.percentile(values_array, 99.9)
                }
            }

        return SimulationResults(metrics)
```

### Example: 4-Week Coverage Simulation

```python
# Initialize simulator
simulator = ScheduleMonteCarloSimulator(
    n_simulations=10000,
    time_horizon_weeks=4
)

# Define risk factors
risk_factors = {
    'case_arrival_rate': 50,  # Cases per week (Poisson λ)
    'case_duration_params': (2.0, 0.3),  # Mean=2h, σ=0.3 (log-normal)
    'absence_probability': 0.05,  # 5% weekly absence rate
    'emergency_rate': 1.5  # 1.5 emergencies per week
}

# Run simulation
results = simulator.simulate_coverage_scenarios(
    base_schedule=current_schedule,
    risk_factors=risk_factors
)

# Extract metrics
print("Coverage Shortfall Risk (hours):")
print(f"  Mean: {results.coverage_shortfalls['mean']:.2f}")
print(f"  VaR (95%): {results.coverage_shortfalls['var_95']:.2f}")
print(f"  CVaR (95%): {results.coverage_shortfalls['cvar_95']:.2f}")
print(f"  VaR (99%): {results.coverage_shortfalls['var_99']:.2f}")
print(f"  CVaR (99%): {results.coverage_shortfalls['cvar_99']:.2f}")

# Output:
# Coverage Shortfall Risk (hours):
#   Mean: 3.2
#   VaR (95%): 8.4
#   CVaR (95%): 14.7
#   VaR (99%): 18.3
#   CVaR (99%): 26.5
```

**Interpretation**:
- **On average**: Expect 3.2 hours shortfall over 4 weeks
- **95% of scenarios**: Shortfall ≤ 8.4 hours
- **When worst 5% occurs**: Average shortfall = 14.7 hours (CVaR)
- **99% of scenarios**: Shortfall ≤ 18.3 hours
- **When worst 1% occurs**: Average shortfall = 26.5 hours (extreme events)

**Actionable Decision**:
- Maintain **float pool** sized to CVaR₉₅ (14.7 hours)
- Maintain **emergency reserves** sized to CVaR₉₉ (26.5 hours)

---

## Risk Budgeting for Workload Distribution

### Concept: Allocate Risk Capacity

**Financial analogy**: Asset managers allocate capital across strategies based on risk contribution, not just expected return.

**Scheduling analogy**: Allocate "risky" assignments (high-variance rotations, call duties) to maintain overall risk within tolerance.

### Risk Contribution Analysis

**Marginal VaR**: How much does each rotation contribute to portfolio VaR?

**Formula**:
```
Risk Contribution_i = w_i × (∂VaR / ∂w_i)
```

For variance-covariance VaR:
```
Risk Contribution_i = w_i × (Σw)_i / σ_portfolio
```

**Example**:
```python
def calculate_risk_contributions(weights, covariance_matrix):
    """
    Calculate each rotation's contribution to portfolio VaR.

    Args:
        weights: Array of rotation allocations
        covariance_matrix: Rotation covariance matrix

    Returns:
        Risk contribution percentages
    """
    # Portfolio variance
    portfolio_variance = weights.T @ covariance_matrix @ weights
    portfolio_stdev = np.sqrt(portfolio_variance)

    # Marginal contributions
    marginal_contribs = (covariance_matrix @ weights) / portfolio_stdev

    # Total contributions
    risk_contribs = weights * marginal_contribs

    # Percentage contributions
    risk_pcts = risk_contribs / portfolio_stdev * 100

    return risk_pcts

# Three rotations: ER, ICU, Clinic
weights = np.array([0.4, 0.4, 0.2])
covariance = np.array([
    [144, 72, 12],   # ER variance=144, cov(ER,ICU)=72, cov(ER,Clinic)=12
    [72, 100, 15],   # ICU variance=100
    [12, 15, 25]     # Clinic variance=25
])

risk_contributions = calculate_risk_contributions(weights, covariance)
# Result: [52%, 41%, 7%]

print("Risk Contributions:")
print(f"  ER: {risk_contributions[0]:.1f}%")
print(f"  ICU: {risk_contributions[1]:.1f}%")
print(f"  Clinic: {risk_contributions[2]:.1f}%")
```

**Insight**: ER contributes 52% of portfolio risk despite being only 40% of time allocation. Consider:
1. Reduce ER allocation
2. Pair ER with low-risk rotations
3. Improve ER staffing stability (reduce variance)

### Risk Parity Approach

**Risk parity**: Allocate rotations such that each contributes **equally** to total risk.

**Algorithm**:
```python
from scipy.optimize import minimize

def risk_parity_objective(weights, covariance_matrix):
    """
    Objective: Minimize variance of risk contributions.

    Goal: All rotations contribute equally to portfolio risk.
    """
    portfolio_stdev = np.sqrt(weights.T @ covariance_matrix @ weights)
    marginal_contribs = (covariance_matrix @ weights) / portfolio_stdev
    risk_contribs = weights * marginal_contribs

    # Target: equal contributions (1/N each)
    n = len(weights)
    target_contrib = portfolio_stdev / n

    # Penalize deviations from equal contribution
    deviations = (risk_contribs - target_contrib) ** 2
    return deviations.sum()

def risk_parity_portfolio(covariance_matrix, constraints=None):
    """
    Optimize rotation allocation for equal risk contribution.
    """
    n = len(covariance_matrix)

    # Initial guess: equal weight
    init_weights = np.ones(n) / n

    # Constraints: weights sum to 1, all non-negative
    if constraints is None:
        constraints = [
            {'type': 'eq', 'fun': lambda w: w.sum() - 1},  # Sum = 1
        ]
    bounds = [(0, 1) for _ in range(n)]  # 0 ≤ w_i ≤ 1

    # Optimize
    result = minimize(
        fun=risk_parity_objective,
        x0=init_weights,
        args=(covariance_matrix,),
        method='SLSQP',
        bounds=bounds,
        constraints=constraints
    )

    return result.x

# Optimize rotation allocation
optimal_weights = risk_parity_portfolio(covariance)
print(f"Optimal allocation: ER={optimal_weights[0]:.1%}, ICU={optimal_weights[1]:.1%}, Clinic={optimal_weights[2]:.1%}")
# Result: ER=28%, ICU=32%, Clinic=40%
# (Reduces high-variance ER, increases low-variance Clinic)
```

### Risk Budget Allocation

**Risk budget**: Maximum tolerable risk (VaR or CVaR) that can be allocated.

**Example**: Program tolerates max 95% VaR of 12 hours weekly workload variance.

```python
def allocate_risk_budget(
    rotation_vars: dict,
    rotation_correlations: np.ndarray,
    total_risk_budget: float,
    constraints: dict = None
) -> dict:
    """
    Allocate time across rotations to stay within risk budget.

    Args:
        rotation_vars: {rotation_name: variance}
        rotation_correlations: Correlation matrix
        total_risk_budget: Max acceptable portfolio variance
        constraints: Min/max time per rotation

    Returns:
        Optimal allocation
    """
    rotations = list(rotation_vars.keys())
    n = len(rotations)

    # Build covariance matrix
    stdevs = np.array([np.sqrt(rotation_vars[r]) for r in rotations])
    covariance = np.outer(stdevs, stdevs) * rotation_correlations

    def portfolio_variance(weights):
        return weights.T @ covariance @ weights

    def risk_constraint(weights):
        """Ensure portfolio variance ≤ budget."""
        return total_risk_budget - portfolio_variance(weights)

    # Constraints
    constraint_list = [
        {'type': 'eq', 'fun': lambda w: w.sum() - 1},  # Sum = 1
        {'type': 'ineq', 'fun': risk_constraint}  # Variance ≤ budget
    ]

    # Bounds (min/max allocation per rotation)
    if constraints:
        bounds = [(constraints.get(r, {}).get('min', 0),
                   constraints.get(r, {}).get('max', 1))
                  for r in rotations]
    else:
        bounds = [(0, 1) for _ in range(n)]

    # Objective: Maximize "coverage quality" (placeholder—could be procedure count)
    # Here: uniform allocation subject to risk constraint
    init_weights = np.ones(n) / n

    result = minimize(
        fun=lambda w: -w.sum(),  # Dummy objective (feasibility problem)
        x0=init_weights,
        method='SLSQP',
        bounds=bounds,
        constraints=constraint_list
    )

    return {rotations[i]: result.x[i] for i in range(n)}
```

---

## Mathematical Formulations

### Parametric VaR (Normal Distribution)

**Single asset**:
```
VaR_α = μ + σ × Φ⁻¹(α)
```

**Portfolio** (matrix notation):
```
VaR_α = μ_p + √(w' Σ w) × Φ⁻¹(α)
```

Where:
- w = (w₁, w₂, ..., wₙ)' is weight vector
- Σ = n×n covariance matrix
- Φ⁻¹(α) = inverse standard normal CDF (z-score)

**Example**: For 95% confidence, Φ⁻¹(0.95) = 1.645

### Expected Shortfall

**Continuous distribution**:
```
ES_α = (1/(1-α)) ∫_{α}^{1} VaR_u du
```

**Normal distribution (closed form)**:
```
ES_α = μ + σ × [φ(Φ⁻¹(α)) / (1-α)]
```

Where φ(·) is standard normal PDF

**Example**: For 95% ES under normality:
```
ES_0.95 = μ + σ × [φ(1.645) / 0.05]
        = μ + σ × [0.1031 / 0.05]
        = μ + 2.063σ
```

Compare to VaR₀.₉₅ = μ + 1.645σ

### Marginal VaR

**Definition**: Change in portfolio VaR from small change in asset weight.

```
Marginal VaR_i = ∂VaR_p / ∂w_i = (Σw)_i / σ_p
```

**Component VaR** (risk contribution):
```
Component VaR_i = w_i × Marginal VaR_i
```

**Property** (Euler's theorem):
```
VaR_p = Σ Component VaR_i
```

### Monte Carlo VaR Convergence

**Standard error of VaR estimate**:
```
SE(VaR_α) ≈ (σ / √n) × √[α(1-α) / φ²(Φ⁻¹(α))]
```

Where:
- n = number of simulations
- σ = portfolio standard deviation

**Example**: For 95% VaR, 10,000 simulations, σ=10:
```
SE ≈ (10 / √10000) × √[0.95×0.05 / φ²(1.645)]
   ≈ 0.1 × √[0.0475 / 0.0106]
   ≈ 0.1 × 2.1
   ≈ 0.21
```

**Interpretation**: VaR estimate accurate to ±0.42 (95% CI)

---

## Implementation Architecture

### Module Structure

```
backend/app/resilience/financial_var/
├── __init__.py
├── var_calculator.py          # Core VaR calculation engines
├── expected_shortfall.py      # CVaR/ES methods
├── stress_testing.py          # Scenario analysis framework
├── monte_carlo.py             # MC simulation engine
├── risk_aggregation.py        # Portfolio VaR, correlation
├── risk_budgeting.py          # Risk parity, allocation
└── models.py                  # Data classes (VaRResult, StressScenario)
```

### Core Classes

```python
# var_calculator.py
class VaRCalculator:
    """Unified interface for VaR calculation methods."""

    def historical_var(
        self,
        data: np.ndarray,
        confidence: float = 0.95
    ) -> VaRResult:
        """Historical simulation VaR."""
        pass

    def parametric_var(
        self,
        mean: float,
        std: float,
        confidence: float = 0.95
    ) -> VaRResult:
        """Parametric (variance-covariance) VaR."""
        pass

    def monte_carlo_var(
        self,
        simulation_func: callable,
        n_simulations: int = 10000,
        confidence: float = 0.95
    ) -> VaRResult:
        """Monte Carlo VaR."""
        pass

# expected_shortfall.py
class ExpectedShortfallCalculator:
    """Calculate CVaR/ES from loss distributions."""

    def calculate_es(
        self,
        losses: np.ndarray,
        confidence: float = 0.95
    ) -> float:
        """Expected Shortfall from data."""
        pass

    def parametric_es(
        self,
        mean: float,
        std: float,
        confidence: float = 0.95,
        distribution: str = 'normal'
    ) -> float:
        """Parametric ES (normal, t-distribution, etc.)."""
        pass

# stress_testing.py
class StressTestFramework:
    """Scenario analysis and sensitivity testing."""

    def add_scenario(
        self,
        name: str,
        shock_function: callable
    ):
        """Register stress scenario."""
        pass

    def run_scenario(
        self,
        scenario_name: str,
        base_schedule: Schedule
    ) -> StressTestResult:
        """Execute single scenario."""
        pass

    def run_all_scenarios(
        self,
        base_schedule: Schedule
    ) -> dict[str, StressTestResult]:
        """Run full stress test suite."""
        pass

# monte_carlo.py
class MonteCarloSimulator:
    """MC simulation for schedule risk."""

    def simulate(
        self,
        base_schedule: Schedule,
        risk_factors: dict,
        n_simulations: int = 10000
    ) -> SimulationResults:
        """Run Monte Carlo simulation."""
        pass

# risk_aggregation.py
class RiskAggregator:
    """Portfolio risk calculation and decomposition."""

    def portfolio_var(
        self,
        weights: np.ndarray,
        covariance_matrix: np.ndarray,
        confidence: float = 0.95
    ) -> PortfolioVaR:
        """Calculate portfolio VaR."""
        pass

    def marginal_var(
        self,
        weights: np.ndarray,
        covariance_matrix: np.ndarray
    ) -> np.ndarray:
        """Marginal VaR for each component."""
        pass

    def risk_contributions(
        self,
        weights: np.ndarray,
        covariance_matrix: np.ndarray
    ) -> dict:
        """Risk contribution decomposition."""
        pass

# models.py
@dataclass
class VaRResult:
    """VaR calculation result."""
    var: float
    confidence: float
    method: str  # 'historical', 'parametric', 'monte_carlo'
    metadata: dict

@dataclass
class StressTestResult:
    """Stress test outcome."""
    scenario_name: str
    coverage_gaps: float
    acgme_violations: int
    max_resident_hours: float
    severity: str  # 'mild', 'moderate', 'severe', 'catastrophic'
```

### Integration Points

**1. Resilience Health Monitor (Celery Task)**
```python
@celery.task
def calculate_schedule_var():
    """Weekly VaR calculation for all risk dimensions."""
    calculator = VaRCalculator()

    # Coverage VaR
    coverage_var = calculator.historical_var(
        data=get_historical_coverage_gaps(),
        confidence=0.95
    )

    # Compliance VaR (ACGME)
    compliance_var = calculator.parametric_var(
        mean=get_avg_weekly_hours(),
        std=get_weekly_hours_std(),
        confidence=0.99
    )

    # Store results
    store_var_metrics(coverage_var, compliance_var)

    # Trigger alerts if VaR exceeds thresholds
    check_var_thresholds(coverage_var, compliance_var)
```

**2. Schedule Generator (Pre-Generation Risk Assessment)**
```python
def generate_schedule_with_risk_constraints(
    residents: list,
    rotations: list,
    max_coverage_var: float = 10.0  # hours
) -> Schedule:
    """Generate schedule respecting risk budget."""

    # Monte Carlo pre-assessment
    simulator = MonteCarloSimulator()
    risk_forecast = simulator.simulate(
        base_schedule=proposed_schedule,
        risk_factors=get_risk_factors(),
        n_simulations=1000
    )

    # Check risk budget
    if risk_forecast.coverage_var_95 > max_coverage_var:
        # Adjust schedule (add float, reduce variance)
        proposed_schedule = adjust_for_risk_budget(
            proposed_schedule,
            target_var=max_coverage_var
        )

    return proposed_schedule
```

**3. Dashboard API Endpoint**
```python
@router.get("/api/resilience/var-metrics")
async def get_var_metrics(db: AsyncSession = Depends(get_db)):
    """Fetch latest VaR metrics for dashboard."""

    return {
        'coverage_var': {
            '95': await get_latest_var('coverage', 0.95),
            '99': await get_latest_var('coverage', 0.99)
        },
        'compliance_var': {
            '95': await get_latest_var('compliance', 0.95),
            '99': await get_latest_var('compliance', 0.99)
        },
        'workload_var': {
            '95': await get_latest_var('workload', 0.95),
            '99': await get_latest_var('workload', 0.99)
        },
        'stress_tests': await get_latest_stress_test_results(),
        'risk_contributions': await get_rotation_risk_contributions()
    }
```

---

## Code Integration Points

### 1. Database Schema Extensions

```python
# backend/app/models/resilience_metrics.py
class VaRMetric(Base):
    __tablename__ = "var_metrics"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    metric_type: Mapped[str]  # 'coverage', 'compliance', 'workload'
    confidence_level: Mapped[float]  # 0.95, 0.99
    var_value: Mapped[float]
    cvar_value: Mapped[float]  # Expected Shortfall
    calculation_method: Mapped[str]  # 'historical', 'parametric', 'monte_carlo'
    time_horizon_weeks: Mapped[int]
    calculated_at: Mapped[datetime]
    metadata: Mapped[dict] = mapped_column(JSON)

class StressTestResult(Base):
    __tablename__ = "stress_test_results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scenario_name: Mapped[str]
    severity: Mapped[str]  # 'mild', 'moderate', 'severe', 'catastrophic'
    coverage_gap_hours: Mapped[float]
    acgme_violations: Mapped[int]
    max_resident_hours: Mapped[float]
    workload_inequality: Mapped[float]
    executed_at: Mapped[datetime]
    scenario_parameters: Mapped[dict] = mapped_column(JSON)
```

### 2. API Schema (Pydantic)

```python
# backend/app/schemas/var_metrics.py
class VaRMetricResponse(BaseModel):
    metric_type: str
    confidence_level: float
    var_value: float
    cvar_value: float
    calculation_method: str
    time_horizon_weeks: int
    calculated_at: datetime

    class Config:
        from_attributes = True

class StressTestResultResponse(BaseModel):
    scenario_name: str
    severity: str
    coverage_gap_hours: float
    acgme_violations: int
    max_resident_hours: float
    workload_inequality: float
    executed_at: datetime

    class Config:
        from_attributes = True

class RiskDashboardResponse(BaseModel):
    coverage_var_95: float
    coverage_var_99: float
    coverage_cvar_95: float
    compliance_var_99: float
    workload_var_95: float
    stress_test_results: list[StressTestResultResponse]
    risk_contributions: dict[str, float]  # {rotation_name: risk_pct}
```

### 3. Frontend Integration (Next.js/React)

```typescript
// frontend/src/components/resilience/VaRDashboard.tsx
interface VaRMetrics {
  coverage_var_95: number;
  coverage_var_99: number;
  coverage_cvar_95: number;
  compliance_var_99: number;
  workload_var_95: number;
  stress_test_results: StressTestResult[];
  risk_contributions: Record<string, number>;
}

export function VaRDashboard() {
  const { data: metrics, isLoading } = useQuery<VaRMetrics>({
    queryKey: ['var-metrics'],
    queryFn: () => api.get('/resilience/var-metrics').then(r => r.data),
    refetchInterval: 60000  // Update every minute
  });

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* VaR Cards */}
      <VaRCard
        title="Coverage VaR (95%)"
        value={metrics?.coverage_var_95}
        threshold={10}
        unit="hours"
      />
      <VaRCard
        title="Compliance VaR (99%)"
        value={metrics?.compliance_var_99}
        threshold={80}
        unit="hours/week"
        critical={true}
      />

      {/* Stress Test Heatmap */}
      <StressTestHeatmap results={metrics?.stress_test_results} />

      {/* Risk Contribution Chart */}
      <RiskContributionPieChart data={metrics?.risk_contributions} />
    </div>
  );
}
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)

**Deliverables**:
- [ ] Core VaR calculation module (`var_calculator.py`)
  - Historical VaR
  - Parametric VaR
  - Unit tests (>90% coverage)
- [ ] Expected Shortfall module (`expected_shortfall.py`)
  - Historical ES
  - Parametric ES (normal, t-distribution)
- [ ] Database schema migrations
  - `var_metrics` table
  - `stress_test_results` table
- [ ] API endpoints (GET only)
  - `/api/resilience/var-metrics`
  - `/api/resilience/stress-tests`

**Success Criteria**:
- VaR calculations match manual calculations (validation tests)
- API returns mock data successfully

---

### Phase 2: Monte Carlo Simulation (Weeks 3-4)

**Deliverables**:
- [ ] Monte Carlo simulator (`monte_carlo.py`)
  - Configurable risk factors
  - Scenario generation
  - Performance optimization (target: <10s for 10k simulations)
- [ ] Stress testing framework (`stress_testing.py`)
  - Scenario registry
  - Pandemic scenario
  - Deployment scenario
  - Exodus scenario
- [ ] Celery task for weekly VaR calculation
- [ ] Unit tests for MC simulation

**Success Criteria**:
- Monte Carlo VaR converges to analytical VaR for simple cases
- Stress tests run successfully for all registered scenarios
- Celery task executes without errors

---

### Phase 3: Risk Aggregation & Budgeting (Weeks 5-6)

**Deliverables**:
- [ ] Risk aggregation module (`risk_aggregation.py`)
  - Portfolio VaR
  - Marginal VaR
  - Risk contributions
- [ ] Risk budgeting module (`risk_budgeting.py`)
  - Risk parity optimization
  - Risk budget allocation
- [ ] Covariance estimation from historical schedules
- [ ] Integration with schedule generator
  - Pre-generation risk assessment
  - Risk budget constraints

**Success Criteria**:
- Risk contributions sum to portfolio VaR (Euler property)
- Risk parity optimizer converges
- Schedule generator respects risk budgets

---

### Phase 4: Dashboard & Visualization (Weeks 7-8)

**Deliverables**:
- [ ] Frontend VaR dashboard
  - VaR metric cards
  - Stress test heatmap
  - Risk contribution pie chart
  - Time series VaR trends
- [ ] Alert system integration
  - Trigger alerts when VaR exceeds thresholds
  - CVaR-based severity classification
- [ ] Documentation
  - API documentation
  - User guide for VaR dashboard
  - Administrator guide for configuring thresholds

**Success Criteria**:
- Dashboard updates in real-time (WebSocket or polling)
- Alerts fire correctly when thresholds breached
- Non-technical users can interpret VaR metrics

---

### Phase 5: Advanced Features (Weeks 9-12)

**Deliverables**:
- [ ] Copula-based risk aggregation
  - Student-t copula for tail dependence
  - Clayton/Gumbel copulas for asymmetric risk
- [ ] Backtesting framework
  - Compare VaR predictions to actual outcomes
  - Kupiec POF test (proportion of failures)
  - Christoffersen independence test
- [ ] Regulatory reporting
  - ACGME compliance VaR reports
  - Historical violation tracking
- [ ] Machine learning enhancements
  - GARCH models for time-varying volatility
  - Neural network VaR prediction

**Success Criteria**:
- Copula models improve tail risk estimates vs. normal copula
- Backtesting shows VaR is well-calibrated (5% violations for 95% VaR)
- Regulatory reports generated automatically

---

## References

### Academic Literature

1. **Value-at-Risk Foundations**
   - J.P. Morgan/Reuters (1996). *RiskMetrics™ Technical Document* (4th ed.). New York.
   - Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk* (3rd ed.). McGraw-Hill.

2. **Expected Shortfall / CVaR**
   - Artzner, P., Delbaen, F., Eber, J.M., & Heath, D. (1999). "Coherent Measures of Risk." *Mathematical Finance*, 9(3), 203-228.
   - Rockafellar, R.T. & Uryasev, S. (2000). "Optimization of Conditional Value-at-Risk." *Journal of Risk*, 2, 21-41.

3. **Monte Carlo Methods**
   - Glasserman, P. (2003). *Monte Carlo Methods in Financial Engineering*. Springer.
   - Kroese, D.P., Taimre, T., & Botev, Z.I. (2011). *Handbook of Monte Carlo Methods*. Wiley.

4. **Stress Testing**
   - Federal Reserve (2025). *2025 Supervisory Stress Test Methodology*. Board of Governors.
   - Breuer, T., Jandačka, M., Rheinberger, K., & Summer, M. (2009). "How to Find Plausible, Severe, and Useful Stress Scenarios." *International Journal of Central Banking*, 5(3), 205-224.

5. **Risk Aggregation**
   - Embrechts, P., McNeil, A.J., & Straumann, D. (2002). "Correlation and Dependence in Risk Management: Properties and Pitfalls." In *Risk Management: Value at Risk and Beyond* (pp. 176-223). Cambridge University Press.
   - Cherubini, U., Luciano, E., & Vecchiato, W. (2004). *Copula Methods in Finance*. Wiley.

6. **Risk Budgeting**
   - Maillard, S., Roncalli, T., & Teïletche, J. (2010). "The Properties of Equally Weighted Risk Contribution Portfolios." *Journal of Portfolio Management*, 36(4), 60-70.

### Industry Standards

- **Basel III**: Basel Committee on Banking Supervision (2019). *Minimum Capital Requirements for Market Risk*.
- **FRTB**: *Fundamental Review of the Trading Book* (2016, revised 2019).

### Web Resources

- [PyQuant News: Monte Carlo VaR](https://www.pyquantnews.com/the-pyquant-newsletter/quickly-compute-value-at-risk-with-monte-carlo)
- [Financial Edge: Conditional VaR](https://www.fe.training/free-resources/portfolio-management/conditional-value-at-risk/)
- [Federal Reserve 2025 Stress Tests](https://www.federalreserve.gov/publications/2025-stress-test-scenarios.htm)
- [Investment Risk Predictor: 2025 Portfolio Risk Assessment](https://myriskpredictor.com/articles/how-to-assess-portfolio-risk-2025.html)

---

## Conclusion

Financial Value-at-Risk (VaR) methodologies provide a **quantitative, transparent, and battle-tested framework** for managing residency scheduling risk. By treating schedules as portfolios of risky assets, programs can:

1. **Quantify uncertainty** via probabilistic forecasts (VaR/CVaR)
2. **Stress test** against extreme events (pandemic, mass deployment)
3. **Optimize allocation** using risk budgeting and portfolio theory
4. **Monitor tail risk** via Expected Shortfall for catastrophic scenarios
5. **Demonstrate compliance** through transparent, auditable metrics

**Key Innovations**:
- **Coverage VaR**: Worst expected coverage shortfall with confidence interval
- **Compliance VaR**: Probabilistic ACGME violation risk
- **Monte Carlo simulation**: Captures complex interactions between random variables
- **Risk budgeting**: Allocates "risk capacity" across rotations for optimal balance

This cross-disciplinary import from finance complements the existing resilience framework modules (SPC, epidemiology, Erlang C) by providing **forward-looking probabilistic risk assessment** and **scenario-based stress testing**.

**Next Steps**: Implement Phase 1 (foundation) to establish VaR calculation infrastructure, then progressively enhance with Monte Carlo, risk budgeting, and advanced features.

---

**Document Version**: 1.0
**Word Count**: ~5,800 words
**Last Updated**: 2025-12-26
**Author**: Cross-Disciplinary Resilience Research Team
**Related Documentation**:
- [Cross-Disciplinary Resilience Framework](../architecture/cross-disciplinary-resilience.md)
- [Materials Science Workforce Resilience](materials-science-workforce-resilience.md)
- [Epidemiology for Workforce Resilience](epidemiology-for-workforce-resilience.md)
- [Resilience Framework Guide](../guides/resilience-framework.md)
