# Epidemiology Implementation Roadmap

**Project:** Workforce Epidemiology Module
**Timeline:** 4 phases over 3 months
**Goal:** Predict and prevent burnout epidemics using disease transmission models

---

## Phase 1: Quick Wins (Week 1-2) ⚡

### 1.1 Superspreader Detection

**Leverage existing:**
- `hub_analysis.py` → faculty centrality scores
- `homeostasis.py` → allostatic load tracking
- `behavioral_network.py` → stress visibility (martyrs)

**New code:**
```python
# backend/app/resilience/epidemiology/superspreader.py

class SuperspreaderDetector:
    """Identify faculty who disproportionately spread burnout."""

    def identify_superspreaders(
        self,
        centrality_scores: list[FacultyCentrality],  # From hub_analysis
        allostatic_loads: dict[UUID, float],         # From homeostasis
        behavioral_roles: dict[UUID, BehavioralRole], # From behavioral_network
    ) -> list[SuperspreaderProfile]:
        """
        Calculate superspreader scores using:
        - Network centrality (40%)
        - Stress visibility (30%)
        - Burnout duration (20%)
        - Spatial centrality (10%)

        Returns top 20% as superspreaders.
        """
        pass
```

**Integration:**
- Add `identify_superspreaders()` method to `ResilienceService`
- Display on dashboard: "5 stress superspreaders detected"
- Generate containment recommendations

**Testing:**
- Unit test: Mock 100 faculty, verify top 20% flagged
- Integration test: Run on real swap network, verify centrality correlation

**Deliverable:** Dashboard shows superspreader count + alert when critical superspreader detected

---

### 1.2 R₀ Calculator & Epidemic Threshold Monitor

**Leverage existing:**
- `homeostasis.py` → allostatic load (disease state)
- `behavioral_network.py` → swap network (contact graph)
- `utilization.py` → current utilization

**New code:**
```python
# backend/app/resilience/epidemiology/reproduction_number.py

class BurnoutR0Calculator:
    """Calculate basic reproduction number for burnout spread."""

    def calculate_r0(
        self,
        faculty_id: UUID,
        network: nx.Graph,
        current_allostatic_load: float,
    ) -> float:
        """
        R₀ = transmission_rate × burnout_duration × contact_rate

        Transmission rate varies by load severity:
        - Load <60: 0.0 (not infectious)
        - Load 60-70: 0.01
        - Load 70-80: 0.03
        - Load >80: 0.05
        """
        pass

class EpidemicThresholdMonitor:
    """Alert when R₀ crosses epidemic threshold (1.0)."""

    def check_epidemic_risk(
        self,
        faculty_network: nx.Graph,
        allostatic_loads: dict[UUID, float],
    ) -> dict:
        """
        Calculate mean R₀ across burned-out faculty.

        Status:
        - R₀ < 0.5: Controlled
        - R₀ 0.5-0.9: Warning
        - R₀ 0.9-1.5: Epidemic threshold
        - R₀ > 1.5: Exponential spread
        """
        pass
```

**Integration:**
- Add to health check: `epidemic_risk = self.check_epidemic_risk(...)`
- Escalate defense level when R₀ > 1.0
- Display on dashboard: "R₀: 1.8 ⚠️ EPIDEMIC"

**Testing:**
- Unit test: Verify R₀ calculation formula
- Scenario test: High utilization (90%) → R₀ > 1
- Scenario test: Low utilization (60%) → R₀ < 1

**Deliverable:** Dashboard gauge showing current R₀ + epidemic status

---

### 1.3 Dashboard Integration

**New panel: Epidemic Risk Assessment**

```typescript
// frontend/src/components/resilience/EpidemicRiskPanel.tsx

export function EpidemicRiskPanel() {
  const { data } = useEpidemicRisk();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Epidemic Risk Assessment</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* R₀ Gauge */}
          <div>
            <Label>Burnout R₀</Label>
            <Progress value={data.r0 * 50} /> {/* Scale to 0-100 */}
            <p className="text-sm">{data.r0.toFixed(1)} - {data.status}</p>
          </div>

          {/* Prevalence */}
          <div>
            <Label>Burned Out</Label>
            <p>{data.prevalence}%</p>
          </div>

          {/* Superspreaders */}
          <div>
            <Label>Superspreaders Detected</Label>
            <p>{data.superspreader_count}</p>
            <Button onClick={() => viewSuperspreaders()}>View Details</Button>
          </div>

          {/* Urgent Actions */}
          {data.recommendations.length > 0 && (
            <Alert variant="destructive">
              <AlertTitle>🚨 Urgent Actions</AlertTitle>
              <ul>
                {data.recommendations.map(rec => <li key={rec}>{rec}</li>)}
              </ul>
            </Alert>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

**API Endpoint:**
```python
# backend/app/api/routes/resilience.py

@router.get("/epidemic-risk")
async def get_epidemic_risk(
    db: Session = Depends(get_db),
    service: ResilienceService = Depends(get_resilience_service),
):
    """Get epidemic risk assessment."""
    return service.check_epidemic_status()
```

**Deliverable:** Live dashboard showing epidemic risk metrics

---

## Phase 2: Contact Tracing (Week 3-4) 🔍

### 2.1 Contact Tracing Protocol

**Leverage existing:**
- `behavioral_network.py` → swap network (contact graph)
- `homeostasis.py` → allostatic load changes (infection events)
- `homeostasis.detect_positive_feedback_risks()` → trigger event

**New code:**
```python
# backend/app/resilience/epidemiology/contact_tracing.py

class ContactTracingProtocol:
    """Trace contacts of burned-out faculty for pre-emptive intervention."""

    def trace_and_intervene(
        self,
        outbreak_case: UUID,  ***REMOVED*** who just burned out
        network: nx.Graph,    # Swap network
        allostatic_loads: dict[UUID, float],
    ) -> list[InterventionRecommendation]:
        """
        Identify contacts and assess exposure:

        1st degree contacts (direct swap partners):
        - Load >60: Already infected → immediate intervention
        - Load 45-60: Exposed high-risk → preventive workload reduction
        - Load 30-45: Exposed moderate → enhanced monitoring

        2nd degree contacts (contacts of contacts):
        - Load >50: Monitor for increase

        Returns prioritized intervention list.
        """
        pass

    def monitor_contact_load_changes(
        self,
        traced_contacts: list[UUID],
        db: Session,
    ):
        """Track allostatic load weekly for traced contacts."""
        pass
```

**Integration:**
- Hook into `homeostasis.detect_positive_feedback_risks()`
- When burnout detected (load jump >20 in 30 days), trigger contact tracing
- Create decision queue items for interventions
- Store tracing results in database

**Workflow:**
```
1. Homeostasis detects: Dr. Smith load 50 → 75 in 30 days
2. Trigger: contact_tracing.trace_and_intervene(dr_smith_id)
3. Identify: Drs. Jones (load 55), Lee (load 42), Patel (load 65)
4. Queue decisions:
   - Dr. Patel: Immediate workload reduction (already burned out)
   - Dr. Jones: Preventive intervention (exposed high-risk)
   - Dr. Lee: Enhanced monitoring
5. Track weekly: Monitor Jones & Lee for load increases
```

**Testing:**
- Mock network: 1 burned out → 5 contacts
- Verify correct risk classification
- Integration test: Run on real swap network

**Deliverable:** Automated contact tracing triggered on burnout detection

---

### 2.2 Intervention Tracking

**Database schema:**
```sql
CREATE TABLE contact_tracing_events (
    id UUID PRIMARY KEY,
    outbreak_case_id UUID REFERENCES persons(id),
    detected_at TIMESTAMP,
    contacts_traced INTEGER,
    interventions_queued INTEGER,
    r0_at_detection FLOAT,
    status VARCHAR -- 'active', 'resolved'
);

CREATE TABLE traced_contacts (
    id UUID PRIMARY KEY,
    tracing_event_id UUID REFERENCES contact_tracing_events(id),
    contact_id UUID REFERENCES persons(id),
    degree INTEGER, -- 1st or 2nd degree
    load_at_detection FLOAT,
    risk_level VARCHAR, -- 'critical', 'high', 'moderate', 'low'
    intervention_type VARCHAR,
    intervention_status VARCHAR,
    last_monitored TIMESTAMP
);
```

**Deliverable:** Database tables + tracking dashboard

---

## Phase 3: Syndromic Surveillance (Month 2) 🩺

### 3.1 Symptom Detection Engine

**Leverage existing:**
- `behavioral_network.py` → swap behavior tracking
- Assignment/leave records → sick calls, performance metrics

**New code:**
```python
# backend/app/resilience/epidemiology/syndromic_surveillance.py

class BehavioralSymptomDetector:
    """Detect early warning signs from scheduling behavior."""

    def detect(self, faculty_id: UUID, window_days: int = 30) -> dict[str, float]:
        """
        Monitor behavioral symptoms:
        - Swap increase (trying to offload work)
        - Sick calls spike
        - Swap acceptance decline (refusing to help)
        - Late responses (measure from email/Slack if available)

        Returns symptom scores (0-1) for each category.
        """
        pass

class PerformanceSymptomDetector:
    """Detect performance decline symptoms."""

    def detect(self, faculty_id: UUID, window_days: int = 30) -> dict[str, float]:
        """
        Monitor performance symptoms:
        - Chart completion delays
        - Quality metrics decline
        - Missed deadlines

        Returns symptom scores (0-1).
        """
        pass

class SyndromicSurveillanceEngine:
    """Aggregate symptoms into burnout syndrome score."""

    def screen_faculty(
        self,
        faculty_id: UUID,
        window_days: int = 30,
    ) -> SyndromeReport:
        """
        Run symptom detectors and aggregate:

        Syndrome Score = (
            swap_increase × 0.15 +
            sick_calls × 0.15 +
            performance_decline × 0.25 +
            social_withdrawal × 0.15 +
            quality_issues × 0.20 +
            helping_decline × 0.10
        )

        Risk classification:
        - Score >0.7: Critical → immediate intervention
        - Score 0.5-0.7: High → early intervention
        - Score 0.3-0.5: Moderate → enhanced monitoring
        - Score <0.3: Low → routine monitoring
        """
        pass
```

**Integration:**
- Run weekly screen for all faculty
- Flag high-risk cases for early intervention
- Track syndrome → actual burnout correlation (validate model)

**Testing:**
- Historical validation: Run on past data, compare syndrome scores 30 days before burnout
- Expected: High syndrome score predicts burnout with 70%+ accuracy

**Deliverable:** Weekly syndromic surveillance reports

---

### 3.2 Outbreak Detection

**New code:**
```python
class OutbreakDetector:
    """Detect system-wide burnout outbreaks."""

    def detect_outbreak(
        self,
        syndrome_reports: list[SyndromeReport],
        historical_baseline: float = 0.15,  # 15% normal prevalence
    ) -> dict:
        """
        Compare current prevalence to baseline:
        - 1.5x baseline: Elevated
        - 2x baseline: Outbreak (moderate)
        - 3x baseline: Outbreak (critical)

        Trigger system-wide response when threshold exceeded.
        """
        pass
```

**Deliverable:** Outbreak detection alerts

---

## Phase 4: Advanced Models (Month 3+) 🔬

### 4.1 Full SEIR Simulation

**New code:**
```python
# backend/app/resilience/epidemiology/seir_model.py

class BurnoutContagionModel:
    """Simulate burnout spread using SEIR dynamics."""

    def step(self, dt: float = 1.0):
        """
        Simulate one day:

        For each faculty:
        - Susceptible: Exposed if contact with Infected
        - Exposed: → Infected at rate σ (1/incubation_period)
        - Infected: → Recovered at rate γ (1/burnout_duration)

        Track prevalence over time, predict future states.
        """
        pass

    def predict_prevalence(self, days: int = 90) -> list[float]:
        """Forecast burnout prevalence over next N days."""
        pass
```

**Use cases:**
- Scenario testing: "If we reduce utilization to 70%, how fast does R₀ drop?"
- Intervention optimization: "Which intervention has highest impact?"
- Resource planning: "When will we need to hire?"

**Deliverable:** Simulation engine + scenario testing tool

---

### 4.2 Herd Immunity Analysis

**New code:**
```python
# backend/app/resilience/epidemiology/herd_immunity.py

class HerdImmunityMonitor:
    """Track workforce immunity to burnout."""

    def calculate_immunity_status(
        self,
        allostatic_loads: dict[UUID, float],
        r0: float,
    ) -> dict:
        """
        Immunity criteria: Allostatic load <30 (has capacity)

        Herd immunity threshold = 1 - (1/R₀)

        If R₀ = 2, need 50% immune to prevent spread.

        Returns:
        - Current immunity rate
        - Gap to threshold
        - Faculty needed for protection
        """
        pass

class ImmunityTargetingStrategy:
    """Strategic targeting of resilience interventions."""

    def prioritize_interventions(
        self,
        allostatic_loads: dict[UUID, float],
        faculty_centrality: dict[UUID, float],
    ) -> list[tuple[UUID, str, float]]:
        """
        Prioritize "vaccination" (capacity building) for:
        1. High-centrality, moderate-stress faculty (prevent progression)
        2. Low-stress hubs (maintain immunity)

        Returns sorted list of (faculty_id, intervention_type, priority).
        """
        pass
```

**Deliverable:** Herd immunity dashboard + strategic intervention targeting

---

### 4.3 Bifurcation Analysis

**New code:**
```python
# backend/app/resilience/epidemiology/bifurcation.py

class BifurcationMapper:
    """Map system tipping points."""

    def map_bifurcation_diagram(
        self,
        utilization_range: tuple[float, float] = (0.5, 1.0),
    ) -> dict:
        """
        For each utilization level, calculate equilibrium R₀.

        Identifies:
        - Bifurcation point (where R₀ crosses 1)
        - Hysteresis (different paths up vs down)

        Returns utilization vs. R₀ curve + critical point.
        """
        pass

class EpidemicThresholdAnalyzer:
    """Detect critical slowing down (early warning)."""

    def detect_critical_slowing(
        self,
        metric_history: list[tuple[datetime, float]],
    ) -> dict:
        """
        Monitor for early warning signals:
        - Increased variance (volatility)
        - Increased autocorrelation (slow recovery)

        Indicates approaching tipping point.
        """
        pass
```

**Deliverable:** Tipping point analysis + early warning system

---

## File Structure

```
backend/app/resilience/epidemiology/
├── __init__.py
├── superspreader.py          # Phase 1
├── reproduction_number.py    # Phase 1
├── contact_tracing.py        # Phase 2
├── syndromic_surveillance.py # Phase 3
├── seir_model.py            # Phase 4
├── herd_immunity.py         # Phase 4
└── bifurcation.py           # Phase 4

backend/app/models/
├── contact_tracing_event.py  # Phase 2
└── syndrome_report.py        # Phase 3

backend/app/api/routes/
└── epidemiology.py           # All phases

frontend/src/components/resilience/
├── EpidemicRiskPanel.tsx     # Phase 1
├── SuperspreaderList.tsx     # Phase 1
├── ContactTracingView.tsx    # Phase 2
└── SyndromeAlerts.tsx        # Phase 3

backend/tests/resilience/epidemiology/
├── test_superspreader.py
├── test_r0_calculator.py
├── test_contact_tracing.py
└── test_syndromic_surveillance.py
```

---

## Success Metrics

### Phase 1 (Week 1-2):
- ✅ Dashboard shows R₀ value
- ✅ Superspreaders identified and listed
- ✅ Alert when R₀ > 1.0

### Phase 2 (Week 3-4):
- ✅ Contact tracing triggered automatically on burnout detection
- ✅ Pre-emptive interventions queued for exposed contacts
- ✅ 5+ contacts traced per burnout case

### Phase 3 (Month 2):
- ✅ Weekly syndrome screening for all faculty
- ✅ Early detection: Flag syndrome 30 days before burnout with 70%+ accuracy
- ✅ Outbreak detection alerts

### Phase 4 (Month 3+):
- ✅ SEIR simulation predicts prevalence 90 days out
- ✅ Herd immunity gap identified
- ✅ Bifurcation point mapped (threshold utilization identified)

---

## Resource Requirements

### Development:
- **Phase 1:** 1 developer × 2 weeks = 80 hours
- **Phase 2:** 1 developer × 2 weeks = 80 hours
- **Phase 3:** 1 developer × 4 weeks = 160 hours
- **Phase 4:** 1 developer × 4 weeks = 160 hours
- **Total:** ~480 hours (3 person-months)

### Infrastructure:
- Database: Add 2 tables (contact_tracing_events, syndrome_reports)
- Compute: Weekly screening job (minimal, <1 min runtime)
- Storage: ~1KB per faculty per week (trivial)

### Data Requirements:
- Existing: Swap network, allostatic load, centrality scores
- New: Optional performance metrics (chart delays, quality scores)

---

## Risk Mitigation

**Risk 1: Model accuracy**
- Mitigation: Validate on historical data, tune parameters
- Fallback: Use as early warning indicator, not definitive diagnosis

**Risk 2: Privacy concerns (contact tracing)**
- Mitigation: Anonymize in reports, access control
- Policy: Contact tracing for intervention only, not discipline

**Risk 3: Alert fatigue**
- Mitigation: Threshold tuning, priority levels
- UX: Actionable alerts only, not FYI

**Risk 4: Integration complexity**
- Mitigation: Phase 1 uses existing data, minimal new dependencies
- Architecture: New epidemiology module independent of core resilience

---

## Dependencies

**Blocked by:** None (uses existing infrastructure)

**Blocks:** None (additive feature)

**Integrates with:**
- hub_analysis.py (centrality scores)
- homeostasis.py (allostatic load, positive feedback detection)
- behavioral_network.py (swap network, behavioral roles)
- defense_in_depth.py (escalation when R₀ > 1)
- blast_radius.py (zone isolation)

---

## Documentation Updates

**Required:**
- API docs for `/api/resilience/epidemic-risk` endpoint
- User guide: "Understanding Epidemic Risk Metrics"
- Admin guide: "Configuring Contact Tracing Thresholds"
- Architecture docs: "Epidemiology Module Design"

**Optional:**
- Research paper: "Applying Epidemiological Models to Workforce Resilience"
- Case study: "Preventing Burnout Epidemic at X Institution"

---

## Next Action Items

**Immediate (this week):**
1. Review this roadmap with stakeholders
2. Set up epidemiology module directory structure
3. Write unit tests for `BurnoutR0Calculator` (TDD)
4. Implement `SuperspreaderDetector` (reuse existing hub_analysis)

**Week 2:**
5. Implement `EpidemicThresholdMonitor`
6. Add dashboard panel
7. Deploy Phase 1 to staging
8. Validate on real data

**Checkpoints:**
- End of Week 2: Phase 1 demo (superspreader detection + R₀ monitoring)
- End of Week 4: Phase 2 demo (contact tracing workflow)
- End of Month 2: Phase 3 demo (syndromic surveillance)
- End of Month 3: Phase 4 demo (SEIR simulation)

---

**Status:** Ready to begin
**Owner:** Engineering team
**Stakeholders:** Resilience team, clinical leadership
**Priority:** High (prevents cascade events)

---

*For questions, contact the resilience team or refer to:*
- `/docs/research/epidemiology-for-workforce-resilience.md` (full research)
- `/docs/research/epidemiology-executive-summary.md` (quick reference)
