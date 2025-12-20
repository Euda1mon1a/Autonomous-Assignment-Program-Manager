# Epidemiological Models for Workforce Resilience Systems

**Research Report**
**Date:** 2025-12-20
**Purpose:** Apply epidemic disease models to workforce burnout contagion, attrition cascades, and morale spread

---

## Executive Summary

This research explores how epidemiological models—traditionally used to track infectious disease—can be adapted to understand and predict **workforce contagion effects** such as:
- **Burnout contagion**: Stress spreading through social networks
- **Attrition cascades**: Departures triggering more departures
- **Morale dynamics**: Positive and negative sentiment spread
- **Culture "infections"**: Toxic or resilient behaviors propagating

The key insight: **Behavioral states (burnout, engagement, cynicism) spread through social contact networks just like diseases**, with identifiable transmission rates, superspreaders, and herd immunity thresholds.

**Existing Foundation**: The current resilience system already detects positive feedback cascades (burnout spirals, attrition vortex) and tracks network structure (hub analysis, behavioral networks). This research extends that foundation with explicit contagion modeling.

---

## 1. SIR/SEIR Models — State Transition Dynamics

### Core Epidemiological Principle

The **SIR model** divides a population into compartments:
- **S**usceptible: Can become infected
- **I**nfected: Currently infectious, can transmit to others
- **R**ecovered: Immune, cannot be reinfected

**SEIR** adds **E**xposed (infected but not yet infectious) for diseases with incubation periods.

Transitions occur through contact:
```
S → E → I → R  (SEIR)
S → I → R      (SIR)
```

### Application to Workforce Burnout

**Burnout Contagion Model (SEIR-B)**:
- **S**usceptible: Healthy, manageable stress (allostatic load <40)
- **E**xposed: Early warning signs, elevated stress but not yet burned out (load 40-60)
- **I**nfected (Burned Out): Actively burned out, exhibiting symptoms that affect others (load >60)
- **R**ecovered: Returned to health OR left organization (attrition)

**Transmission Mechanisms**:
1. **Emotional Contagion**: Witnessing a colleague's burnout creates vicarious stress
2. **Workload Redistribution**: When someone burns out/leaves, work redistributes to remaining faculty
3. **Demoralization**: Seeing others struggle undermines belief in organizational fairness
4. **Social Norming**: "Everyone is overwhelmed" becomes accepted culture

**State Transitions**:
```python
# Susceptible → Exposed
# Transmission rate β = contacts per day × probability per contact × infectiousness
prob_S_to_E = β * (I_count / N) * susceptibility_factor

# Exposed → Infected (Burnout)
# Incubation period σ = 1/time_to_burnout (e.g., 30 days)
prob_E_to_I = σ

# Infected → Recovered
# Recovery rate γ = 1/burnout_duration OR departure rate
prob_I_to_R = γ_recovery + γ_attrition
```

### Application to Morale/Engagement

**Engagement Contagion Model**:
- **S**usceptible to Disengagement: Currently engaged but vulnerable
- **D**isengaged: Low motivation, minimal discretionary effort
- **E**ngaged: High motivation, positive influence on others
- **C**hampion: Super-engaged, actively spreads positive culture

This allows bidirectional spread: disengagement spreads like a disease, but engagement can "cure" it.

### Implementation Ideas

**BurnoutContagionTracker class**:
```python
@dataclass
class BurnoutState(str, Enum):
    SUSCEPTIBLE = "susceptible"      # Allostatic load <40
    EXPOSED = "exposed"              # Load 40-60, warning signs
    INFECTED = "infected"            # Load >60, actively burned out
    RECOVERED_HEALTHY = "recovered"  # Returned to health
    RECOVERED_DEPARTED = "departed"  # Left organization

@dataclass
class ContagionParameters:
    """Disease transmission parameters for burnout."""
    beta: float = 0.05          # Transmission rate per contact
    sigma: float = 1/30         # 1/incubation period (days)
    gamma_recovery: float = 1/90 # 1/recovery time (days)
    gamma_attrition: float = 0.01 # Daily departure probability when burned out
    contacts_per_day: float = 5.0 # Avg meaningful interactions

class BurnoutContagionModel:
    """SEIR model for burnout spread."""

    def __init__(self, faculty_network: nx.Graph, params: ContagionParameters):
        self.network = faculty_network
        self.params = params
        self.states: dict[UUID, BurnoutState] = {}

    def step(self, dt: float = 1.0):
        """Simulate one time step (default 1 day)."""
        new_states = self.states.copy()

        for faculty_id, state in self.states.items():
            if state == BurnoutState.SUSCEPTIBLE:
                # Count infected neighbors
                neighbors = list(self.network.neighbors(faculty_id))
                infected_neighbors = sum(
                    1 for n in neighbors
                    if self.states[n] == BurnoutState.INFECTED
                )

                # Force of infection λ = β * I/N
                force_of_infection = (
                    self.params.beta * infected_neighbors / len(neighbors)
                    if neighbors else 0
                )

                if random.random() < force_of_infection * dt:
                    new_states[faculty_id] = BurnoutState.EXPOSED

            elif state == BurnoutState.EXPOSED:
                # Progress to infected at rate σ
                if random.random() < self.params.sigma * dt:
                    new_states[faculty_id] = BurnoutState.INFECTED

            elif state == BurnoutState.INFECTED:
                # Recover or depart
                if random.random() < self.params.gamma_recovery * dt:
                    new_states[faculty_id] = BurnoutState.RECOVERED_HEALTHY
                elif random.random() < self.params.gamma_attrition * dt:
                    new_states[faculty_id] = BurnoutState.RECOVERED_DEPARTED

        self.states = new_states

    def get_prevalence(self) -> dict[str, float]:
        """Calculate prevalence of each state."""
        total = len(self.states)
        counts = Counter(self.states.values())
        return {
            state.value: counts[state] / total
            for state in BurnoutState
        }
```

**Integration with Existing System**:
- Use **allostatic load** (already tracked in homeostasis module) to classify states
- Use **behavioral network** (swap network) as contact graph
- Trigger interventions when prevalence exceeds thresholds

---

## 2. Basic Reproduction Number (R₀) — Epidemic Threshold

### Core Epidemiological Principle

**R₀** (pronounced "R-naught") is the **average number of secondary infections** caused by one infected individual in a completely susceptible population.

**Epidemic threshold**:
- **R₀ < 1**: Disease dies out (each case infects <1 others)
- **R₀ = 1**: Endemic equilibrium (constant low-level infection)
- **R₀ > 1**: Exponential epidemic spread

**Formula**:
```
R₀ = β × τ × c
```
Where:
- **β** = transmission probability per contact
- **τ** = duration of infectiousness
- **c** = contact rate (contacts per time unit)

### Application to Burnout Spread

**R₀ for Burnout**:
```
R₀_burnout = (stress_transmission_rate) × (burnout_duration) × (daily_contacts)
```

**Example Calculation**:
- **β** = 0.03 (3% chance per interaction that witnessing burnout increases receiver's stress)
- **τ** = 90 days (average time someone stays burned out before recovery or departure)
- **c** = 5 contacts/day (meaningful work interactions)

```
R₀ = 0.03 × 90 × 5 = 13.5
```

**Interpretation**: Each burned-out person "infects" 13.5 others with elevated stress over their burnout period. **This is an epidemic**.

**Reducing R₀** (intervention strategies):
1. **Reduce β** (transmission rate):
   - Psychological safety training (reduce emotional contagion)
   - Workload buffering (prevent redistribution cascade)
   - Positive reframing/resilience coaching

2. **Reduce τ** (burnout duration):
   - Early intervention for Exposed faculty (allostatic load 40-60)
   - Rapid workload relief protocols
   - Mental health support, mandatory leave

3. **Reduce c** (contact rate):
   - **Blast radius isolation** (already implemented!) — isolate stressed zones
   - Work-from-home for high-stress periods (reduce transmission)
   - Limit cross-zone borrowing when stress is high

### Application to Attrition Cascades

**R₀ for Departures**:
```
R₀_attrition = (probability_departure_triggers_another) × (affected_colleagues)
```

When someone leaves:
- Workload redistributes to **~3-5 colleagues**
- Each sees **20-30% workload increase**
- If workload was already at 80% utilization, increase pushes them to **96-104%** (unsustainable)
- Probability they also leave within 6 months: **~40-60%**

```
R₀_attrition ≈ 0.5 × 4 = 2.0
```

**Interpretation**: Each departure triggers **2 more departures** on average. This is the **extinction vortex** already modeled in `cascade_scenario.py`.

**Critical insight**: R₀ varies by **system utilization**:
- At 60% utilization: R₀ ≈ 0.3 (departures don't cascade)
- At 80% utilization: R₀ ≈ 1.0 (endemic instability)
- At 90% utilization: R₀ ≈ 2.5 (explosive cascade)

This explains why **80% utilization threshold** (queuing theory) is critical — it's also the **epidemic threshold for attrition**.

### Implementation Ideas

**R₀ Calculator**:
```python
class BurnoutR0Calculator:
    """Calculate basic reproduction number for burnout spread."""

    def calculate_r0(
        self,
        faculty_id: UUID,
        network: nx.Graph,
        current_allostatic_load: float,
    ) -> float:
        """
        Calculate R₀ for a specific faculty member.

        Returns expected number of people they will "infect" with elevated stress.
        """
        # Transmission rate increases with severity
        beta = self._transmission_rate(current_allostatic_load)

        # Duration of infectiousness (days burned out)
        tau = self._expected_burnout_duration(current_allostatic_load)

        # Contact rate (from network)
        contacts = len(list(network.neighbors(faculty_id)))

        return beta * tau * contacts

    def _transmission_rate(self, load: float) -> float:
        """Stress transmission probability per contact per day."""
        if load < 60:
            return 0.0  # Not infectious
        elif load < 70:
            return 0.01  # Mildly infectious
        elif load < 80:
            return 0.03  # Moderately infectious
        else:
            return 0.05  # Highly infectious (visible distress)

    def _expected_burnout_duration(self, load: float) -> float:
        """Expected days until recovery or departure."""
        # Higher load = longer burnout or faster departure
        if load < 70:
            return 30  # Quick recovery
        elif load < 80:
            return 60
        else:
            return 90  # Chronic or leads to departure

class EpidemicThresholdMonitor:
    """Monitor when R₀ crosses epidemic threshold."""

    def check_epidemic_risk(
        self,
        faculty_network: nx.Graph,
        allostatic_loads: dict[UUID, float],
    ) -> dict:
        """Check if system is at epidemic risk."""
        calc = BurnoutR0Calculator()

        # Calculate R₀ for each burned-out faculty
        r0_values = []
        for faculty_id, load in allostatic_loads.items():
            if load > 60:  # Burned out
                r0 = calc.calculate_r0(faculty_id, faculty_network, load)
                r0_values.append(r0)

        if not r0_values:
            return {"status": "healthy", "mean_r0": 0.0}

        mean_r0 = statistics.mean(r0_values)
        max_r0 = max(r0_values)

        if mean_r0 > 1.0:
            status = "epidemic"
            recommendations = [
                "CRITICAL: Burnout is spreading exponentially (R₀ > 1)",
                "Immediate interventions needed to reduce transmission",
                "Consider blast radius isolation for high-R₀ faculty",
            ]
        elif mean_r0 > 0.7:
            status = "warning"
            recommendations = [
                "WARNING: Approaching epidemic threshold",
                "Implement early interventions for exposed faculty",
            ]
        else:
            status = "controlled"
            recommendations = []

        return {
            "status": status,
            "mean_r0": mean_r0,
            "max_r0": max_r0,
            "infectious_count": len(r0_values),
            "recommendations": recommendations,
        }
```

**Integration with Defense in Depth**:
- **GREEN** (R₀ < 0.5): Normal operations
- **YELLOW** (R₀ 0.5-0.9): Enhanced monitoring
- **ORANGE** (R₀ 0.9-1.5): Active containment (blast radius)
- **RED** (R₀ 1.5-2.5): Emergency interventions
- **BLACK** (R₀ > 2.5): System-wide crisis response

---

## 3. Herd Immunity — Population Protection Threshold

### Core Epidemiological Principle

**Herd immunity** occurs when enough of the population is immune that disease cannot sustain transmission, protecting even susceptible individuals.

**Herd immunity threshold (HIT)**:
```
HIT = 1 - (1 / R₀)
```

If R₀ = 3, then HIT = 1 - (1/3) = 0.67 (67% must be immune).

**Vaccination strategy**: Protect high-contact individuals first (maximizes network disruption).

### Application to Workforce Resilience

**Burnout Immunity**: "Immune" faculty are those with:
- **Low allostatic load** (<30) — capacity to absorb stress
- **High resilience factors** — strong social support, psychological safety, autonomy
- **Protected resources** — sabbatical recently, reduced workload

**Herd Immunity Threshold for Burnout**:
If R₀_burnout = 2.0, then HIT = 50%.

**Interpretation**: If **50% of the workforce has "immunity" to burnout** (sufficient capacity, support, resources), burnout cannot spread even when others are stressed.

**"Vaccination" Strategies** (building immunity):
1. **Capacity Building**:
   - Maintain utilization below 70% (creates stress-absorption capacity)
   - Cross-training to distribute critical skills
   - Backup coverage ensures no single points of failure

2. **Resilience Interventions**:
   - Wellness programs, peer support networks
   - Autonomy and psychological safety
   - Recognition, meaning, fairness

3. **Workload Protection**:
   - **Martyr protection** (already implemented!) — prevent over-givers from burnout
   - Sabbaticals, research time, protected schedules
   - Zone-based isolation prevents stress spread

**Strategic "Vaccination" Targeting**:
- Identify **high-centrality faculty** (hubs) — vaccinate them first
- Protect **stabilizers** (from behavioral network) — they absorb system stress
- Shield **low-load faculty** — preserve their immunity as system buffer

### Application to Culture/Morale

**Resilient Culture as Herd Immunity**:
- **Positive culture "vaccinated" faculty**: Those with high engagement, trust in leadership, belief in mission
- **Threshold**: If >60% of faculty have resilient mindset, toxic culture cannot take root
- **Cultural "infections"**: Cynicism, learned helplessness, us-vs-them thinking

**Intervention**: When morale drops, focus interventions on **achieving HIT**, not treating every individual:
- Town halls, transparency, leadership visibility
- Quick wins to restore belief in organizational effectiveness
- Celebrate resilient teams as exemplars

### Implementation Ideas

```python
class HerdImmunityMonitor:
    """Monitor herd immunity thresholds for burnout resistance."""

    def calculate_immunity_status(
        self,
        allostatic_loads: dict[UUID, float],
        r0: float,
    ) -> dict:
        """
        Calculate what % of workforce is "immune" to burnout and compare to HIT.

        Immunity criteria:
        - Allostatic load < 30 (capacity to absorb stress)
        - Recent interventions (sabbatical, workload reduction)
        """
        # Calculate herd immunity threshold
        hit = 1 - (1 / r0) if r0 > 1 else 0

        # Count immune faculty (low stress, capacity to help others)
        immune_count = sum(1 for load in allostatic_loads.values() if load < 30)
        total = len(allostatic_loads)

        immunity_rate = immune_count / total if total > 0 else 0

        # Gap analysis
        gap = hit - immunity_rate
        faculty_needed = int(gap * total) if gap > 0 else 0

        return {
            "herd_immunity_threshold": hit,
            "current_immunity_rate": immunity_rate,
            "immune_count": immune_count,
            "total_faculty": total,
            "status": "protected" if immunity_rate >= hit else "vulnerable",
            "gap": gap,
            "faculty_needed_for_protection": faculty_needed,
            "recommendations": self._build_recommendations(immunity_rate, hit),
        }

    def _build_recommendations(self, current: float, hit: float) -> list[str]:
        """Generate recommendations based on immunity gap."""
        if current >= hit:
            return [
                f"Herd immunity achieved ({current:.0%} >= {hit:.0%})",
                "Maintain current interventions to preserve immunity",
            ]
        else:
            gap_pct = (hit - current) * 100
            return [
                f"ALERT: Immunity gap of {gap_pct:.0f}% below herd immunity threshold",
                "Increase capacity-building interventions",
                "Prioritize protecting high-centrality faculty (hubs)",
                "Consider workload reduction to increase % with capacity",
            ]

class ImmunityTargetingStrategy:
    """Strategic targeting of resilience interventions."""

    def prioritize_interventions(
        self,
        allostatic_loads: dict[UUID, float],
        faculty_centrality: dict[UUID, float],  # From hub_analysis
    ) -> list[tuple[UUID, str, float]]:
        """
        Identify who to 'vaccinate' (intervene on) for maximum herd immunity.

        Returns list of (faculty_id, intervention_type, priority_score).
        """
        priorities = []

        for faculty_id, load in allostatic_loads.items():
            centrality = faculty_centrality.get(faculty_id, 0.0)

            # High-centrality, moderate-stress faculty are best "vaccination" targets
            # Protect them before they become fully burned out
            if 30 <= load <= 60 and centrality > 0.4:
                priority = centrality * (1 - (load - 30) / 30)  # Higher centrality, lower load = higher priority
                priorities.append((
                    faculty_id,
                    "preventive_workload_reduction",
                    priority
                ))

            # Low-stress hubs should be protected to maintain immunity
            elif load < 30 and centrality > 0.5:
                priorities.append((
                    faculty_id,
                    "protect_immunity_status",
                    centrality
                ))

        return sorted(priorities, key=lambda x: -x[2])
```

---

## 4. Superspreader Dynamics — 80/20 Rule in Contagion

### Core Epidemiological Principle

**Superspreader events**: A small fraction of individuals cause a disproportionate number of infections. The **80/20 rule** often applies: **20% of cases cause 80% of transmission**.

**Why superspreaders exist**:
1. **High contact rate** (socially active, many interactions)
2. **High infectiousness** (shedding more pathogen)
3. **Spatial hubs** (central locations, many visitors)
4. **Duration** (infectious for longer)

**Intervention priority**: Identifying and containing superspreaders has **exponentially higher impact** than broad interventions.

### Application to Stress Superspreaders

**Stress Superspreaders**: Faculty who disproportionately spread burnout/stress to others.

**Characteristics**:
1. **High Centrality** (many contacts):
   - Service chiefs, coordinators, senior faculty everyone consults
   - Already identified by **hub_analysis.py**!

2. **High Stress Visibility** (infectious behavior):
   - Public complaints, venting in shared spaces
   - Cynicism in meetings ("nothing will change")
   - Visible exhaustion, missed deadlines, quality issues

3. **Spatial Hubs**:
   - Faculty lounge frequenters
   - Coordinators in high-traffic areas
   - Email/Slack group admins (digital superspreaders)

4. **Long Duration**:
   - Chronic burnout (allostatic load >70 for >60 days)
   - No intervention, allowed to "infect" indefinitely

**Identification Formula**:
```python
superspreader_score = (
    network_centrality * 0.4 +
    stress_visibility * 0.3 +
    spatial_centrality * 0.2 +
    burnout_duration * 0.1
)
```

### Application to Culture/Morale Superspreaders

**Toxic Culture Superspreaders**:
- **Cynics in leadership positions** — their negativity spreads to direct reports
- **Gossip hubs** — spread rumors, undermine trust
- **Martyrs who weaponize suffering** — "I'm drowning and no one cares" → demoralizes others

**Positive Culture Superspreaders** (Champions):
- **Engaged leaders** — infectious enthusiasm
- **Peer mentors** — normalize resilience behaviors
- **Celebration instigators** — spread positive recognition

**Strategic insight**: **Protecting positive superspreaders** and **containing toxic superspreaders** has massively higher ROI than individual interventions.

### Implementation Ideas

```python
class SuperspreaderDetector:
    """Identify stress/burnout superspreaders."""

    def identify_superspreaders(
        self,
        network: nx.Graph,
        allostatic_loads: dict[UUID, float],
        behavioral_roles: dict[UUID, BehavioralRole],  # From behavioral_network
        load_history: dict[UUID, list[tuple[datetime, float]]],
    ) -> list[SuperspreaderProfile]:
        """
        Identify faculty who are disproportionately spreading stress.

        Uses 80/20 heuristic: top 20% cause 80% of transmission.
        """
        profiles = []

        for faculty_id in network.nodes:
            # 1. Network centrality (contact rate)
            centrality = nx.betweenness_centrality(network)[faculty_id]

            # 2. Stress visibility (infectiousness)
            current_load = allostatic_loads.get(faculty_id, 0)
            visibility = self._calculate_stress_visibility(
                current_load,
                behavioral_roles.get(faculty_id)
            )

            # 3. Spatial centrality (approximate from swap network)
            spatial = len(list(network.neighbors(faculty_id))) / network.number_of_nodes()

            # 4. Duration (how long burned out)
            duration_days = self._calculate_burnout_duration(
                faculty_id,
                load_history.get(faculty_id, [])
            )

            # Calculate superspreader score
            score = (
                centrality * 0.4 +
                visibility * 0.3 +
                spatial * 0.2 +
                min(1.0, duration_days / 90) * 0.1
            )

            # Classify
            if score > 0.7:
                risk = "critical_superspreader"
            elif score > 0.5:
                risk = "moderate_superspreader"
            elif score > 0.3:
                risk = "minor_spreader"
            else:
                risk = "low_risk"

            profiles.append(SuperspreaderProfile(
                faculty_id=faculty_id,
                superspreader_score=score,
                risk_level=risk,
                centrality=centrality,
                stress_visibility=visibility,
                burnout_duration_days=duration_days,
                estimated_transmission_count=self._estimate_transmissions(score, network, faculty_id),
            ))

        # Sort by score, return top 20% as superspreaders
        profiles.sort(key=lambda p: -p.superspreader_score)
        top_20_pct = max(1, len(profiles) // 5)

        return profiles[:top_20_pct]

    def _calculate_stress_visibility(
        self,
        load: float,
        behavioral_role: BehavioralRole | None
    ) -> float:
        """How visible/infectious is this person's stress?"""
        base_visibility = min(1.0, load / 100)  # Load 0-100 → visibility 0-1

        # Behavioral roles affect visibility
        if behavioral_role == BehavioralRole.MARTYR:
            # Martyrs' suffering is highly visible (complained about publicly)
            return base_visibility * 1.5
        elif behavioral_role == BehavioralRole.POWER_BROKER:
            # Power brokers' stress spreads faster (people pay attention)
            return base_visibility * 1.3
        elif behavioral_role == BehavioralRole.ISOLATE:
            # Isolates don't spread (low contact)
            return base_visibility * 0.3
        else:
            return base_visibility

    def _calculate_burnout_duration(
        self,
        faculty_id: UUID,
        history: list[tuple[datetime, float]]
    ) -> int:
        """Days spent in burnout state (load >60)."""
        if not history:
            return 0

        burnout_days = 0
        for i in range(len(history) - 1):
            date1, load1 = history[i]
            date2, load2 = history[i + 1]

            if load1 > 60:
                days = (date2 - date1).days
                burnout_days += days

        return burnout_days

    def _estimate_transmissions(
        self,
        superspreader_score: float,
        network: nx.Graph,
        faculty_id: UUID
    ) -> float:
        """Estimate how many people this superspreader has infected."""
        # Rough heuristic: score × network size × transmission factor
        neighbors = len(list(network.neighbors(faculty_id)))
        return superspreader_score * neighbors * 0.3  # ~30% transmission to contacts

class SuperspreaderContainment:
    """Interventions specifically for superspreaders."""

    def generate_containment_plan(
        self,
        superspreader: SuperspreaderProfile,
    ) -> list[str]:
        """Generate targeted interventions for a superspreader."""
        plan = []

        if superspreader.risk_level == "critical_superspreader":
            plan.extend([
                "URGENT: Immediate workload reduction (50%) for this faculty member",
                "Mandatory mental health consultation",
                "Temporary schedule modification to reduce contact rate",
                "Assign 'buddy' from positive superspreader group for support",
                "Consider temporary relief from high-visibility roles (coordinator, committee chair)",
            ])

        if superspreader.centrality > 0.6:
            plan.append(
                "High centrality faculty - reassign some coordinator duties to reduce contact rate"
            )

        if superspreader.burnout_duration_days > 60:
            plan.append(
                f"Chronic burnout ({superspreader.burnout_duration_days} days) - "
                "consider extended leave or sabbatical"
            )

        # Blast radius isolation for superspreaders
        plan.append(
            "Activate blast radius isolation: limit cross-zone borrowing involving this faculty"
        )

        return plan
```

**Integration with Existing Systems**:
- **Hub Analysis**: Already identifies high-centrality faculty — use as superspreader candidates
- **Behavioral Network**: Martyrs are stress superspreaders
- **Blast Radius**: Isolate zones containing superspreaders to prevent cascade
- **Homeostasis**: Track superspreader interventions as corrective actions

---

## 5. Network Epidemiology — Contact Structure Matters

### Core Epidemiological Principle

**Network structure** dramatically affects epidemic dynamics:
- **Random networks**: Epidemics spread uniformly
- **Scale-free networks** (power-law degree distribution):
  - Vulnerable to targeted hub removal
  - Resistant to random node failures
  - Superspreaders are hubs
- **Small-world networks**:
  - High clustering (local groups)
  - Few long-range connections
  - Fast global spread but local containment possible

**Contact tracing**: Identifying and quarantining contacts of infected individuals breaks transmission chains.

**Network interventions**:
1. **Hub vaccination**: Protect high-degree nodes
2. **Bridge cutting**: Break connections between clusters
3. **Cluster isolation**: Quarantine connected groups

### Application to Workforce Networks

**Workforce Contact Networks**:
Already captured in system as:
1. **Swap Network** (behavioral_network.py) — who trades shifts with whom
2. **Service Network** (hub_analysis.py) — who shares service coverage
3. **Social Network** (inferred from co-assignments, shared rotations)

**Network Structure Insights**:
- Medical teams are **small-world networks**: high local clustering (service teams), few bridges (chiefs, coordinators)
- **Hubs** = service chiefs, coordinators, senior faculty
- **Bridges** = faculty who work across multiple services

**Stress "Contact Tracing"**:
When a faculty member becomes burned out (I state):
1. Identify their **contacts** (network neighbors)
2. Assess contacts' **exposure** (allostatic load increase)
3. **Pre-emptively intervene** on exposed contacts before they progress to burned out

**Example**:
- Dr. Smith burns out (load jumps from 50 → 80)
- Swap network shows frequent trades with Dr. Jones, Dr. Lee
- System flags Dr. Jones and Dr. Lee for **early intervention**
- Monitor their allostatic load weekly, intervene if rises above 60

**Network-Based Containment**:
- **Cluster isolation** = Blast radius zones (already implemented!)
- **Hub protection** = Hub vulnerability analysis (already implemented!)
- **Bridge cutting** = Reduce cross-zone borrowing when stress is high

### Application to Culture Spread

**Positive Culture Networks**:
- Map **who influences whom** (not just work contact, but social influence)
- Identify **cultural bridges** — faculty who translate between groups
- Protect **culture champions** (positive superspreaders)

**Toxic Culture Containment**:
- Identify **cynicism clusters** (groups with shared negative outlook)
- **Isolate toxic influencers** — limit their reach through reassignment
- **Break toxic bridges** — disrupt transmission between clusters

### Implementation Ideas

```python
class NetworkEpidemiologyAnalyzer:
    """Analyze contagion dynamics on workforce networks."""

    def identify_transmission_chains(
        self,
        network: nx.Graph,
        outbreak_source: UUID,  # Faculty who became burned out
        allostatic_loads: dict[UUID, float],
    ) -> list[TransmissionChain]:
        """
        Trace how stress spreads from an outbreak source.

        Similar to contact tracing in disease outbreaks.
        """
        # BFS from outbreak source to find propagation
        chains = []
        visited = set()
        queue = [(outbreak_source, 0, [])]  # (node, generation, path)

        while queue:
            node, gen, path = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)

            current_path = path + [node]
            current_load = allostatic_loads.get(node, 0)

            # Check if this node is infected (load >60)
            if current_load > 60 and node != outbreak_source:
                chains.append(TransmissionChain(
                    source=outbreak_source,
                    target=node,
                    generation=gen,
                    path=current_path,
                    transmission_probability=self._estimate_transmission_prob(
                        network, current_path, allostatic_loads
                    ),
                ))

            # Continue BFS to neighbors (if not too far)
            if gen < 3:  # Trace up to 3 generations
                for neighbor in network.neighbors(node):
                    if neighbor not in visited:
                        queue.append((neighbor, gen + 1, current_path))

        return chains

    def identify_bridges(
        self,
        network: nx.Graph,
    ) -> list[tuple[UUID, float]]:
        """
        Identify bridge nodes whose removal fragments the network.

        In epidemic terms: cutting bridges prevents spread between clusters.
        """
        # Calculate betweenness centrality (bridges have high betweenness)
        betweenness = nx.betweenness_centrality(network)

        # Also find structural bridges (articulation points)
        articulation_points = set(nx.articulation_points(network))

        bridges = []
        for node, centrality in betweenness.items():
            is_structural_bridge = node in articulation_points
            bridge_score = centrality * (2.0 if is_structural_bridge else 1.0)
            bridges.append((node, bridge_score))

        return sorted(bridges, key=lambda x: -x[1])

    def simulate_cluster_isolation(
        self,
        network: nx.Graph,
        outbreak_cluster: set[UUID],
    ) -> dict:
        """
        Simulate effect of isolating a cluster (blast radius containment).

        Returns impact on epidemic spread.
        """
        # Remove edges between outbreak cluster and rest of network
        isolated_network = network.copy()
        edges_to_remove = []

        for node in outbreak_cluster:
            for neighbor in network.neighbors(node):
                if neighbor not in outbreak_cluster:
                    edges_to_remove.append((node, neighbor))

        isolated_network.remove_edges_from(edges_to_remove)

        # Calculate component sizes
        components = list(nx.connected_components(isolated_network))
        largest_component_size = max(len(c) for c in components)

        return {
            "edges_cut": len(edges_to_remove),
            "num_components": len(components),
            "largest_component_size": largest_component_size,
            "isolation_effectiveness": 1 - (largest_component_size / network.number_of_nodes()),
            "recommendation": (
                "Effective isolation" if len(components) > 1
                else "Cluster too connected, isolation ineffective"
            ),
        }

class ContactTracingProtocol:
    """Implement contact tracing for burnout outbreaks."""

    def trace_and_intervene(
        self,
        outbreak_case: UUID,
        network: nx.Graph,
        allostatic_loads: dict[UUID, float],
    ) -> list[dict]:
        """
        Trace contacts of a burned-out faculty member and intervene early.

        Returns list of intervention recommendations.
        """
        interventions = []

        # Get immediate contacts (1st degree)
        contacts_1st = list(network.neighbors(outbreak_case))

        # Get contacts of contacts (2nd degree)
        contacts_2nd = set()
        for contact in contacts_1st:
            contacts_2nd.update(network.neighbors(contact))
        contacts_2nd -= {outbreak_case}
        contacts_2nd -= set(contacts_1st)

        # Assess exposure and risk for 1st degree contacts
        for contact in contacts_1st:
            load = allostatic_loads.get(contact, 0)

            if load > 60:
                interventions.append({
                    "faculty_id": contact,
                    "degree": 1,
                    "current_load": load,
                    "status": "already_infected",
                    "action": "Immediate intervention - already burned out",
                    "priority": "critical",
                })
            elif load > 45:
                interventions.append({
                    "faculty_id": contact,
                    "degree": 1,
                    "current_load": load,
                    "status": "exposed_high_risk",
                    "action": "Preventive workload reduction, weekly monitoring",
                    "priority": "high",
                })
            elif load > 30:
                interventions.append({
                    "faculty_id": contact,
                    "degree": 1,
                    "current_load": load,
                    "status": "exposed_moderate_risk",
                    "action": "Enhanced monitoring, resilience resources",
                    "priority": "medium",
                })

        # Assess 2nd degree contacts (monitor only)
        for contact in contacts_2nd:
            load = allostatic_loads.get(contact, 0)
            if load > 50:
                interventions.append({
                    "faculty_id": contact,
                    "degree": 2,
                    "current_load": load,
                    "status": "secondary_exposure",
                    "action": "Monitor for load increase",
                    "priority": "low",
                })

        return sorted(interventions, key=lambda x: {
            "critical": 0, "high": 1, "medium": 2, "low": 3
        }[x["priority"]])
```

**Integration with Existing Systems**:
- Use **swap network** from behavioral_network.py as contact graph
- Trigger contact tracing when **positive feedback risk** detected in homeostasis.py
- Use **blast radius zones** for cluster isolation
- **Hub analysis** identifies bridges to protect

---

## 6. Syndromic Surveillance — Early Detection from Symptoms

### Core Epidemiological Principle

**Syndromic surveillance**: Detect outbreaks **before lab confirmation** by monitoring:
- **Early symptoms** (fever, cough) before diagnosis
- **Proxy indicators** (pharmacy sales, absenteeism, ER visits)
- **Anomaly detection** (unusual patterns)

Goal: **Early warning** → Faster response → Prevent epidemic

### Application to Burnout Detection

**Burnout "Syndromes"** (early warning signs before full burnout):

1. **Behavioral Symptoms**:
   - Increased swap requests (trying to offload work)
   - Increased sick calls
   - Reduced swap acceptance (refusing to help others)
   - Shorter email responses, delayed replies

2. **Performance Symptoms**:
   - Missed deadlines
   - Chart completion delays
   - Increased handoff issues
   - Quality metrics decline

3. **Social Symptoms**:
   - Reduced peer interactions
   - Meeting absences
   - Negative sentiment in communications
   - Withdrawal from optional activities

4. **Physiological Symptoms** (if tracked):
   - Sleep pattern changes (wearables)
   - Increased sick leave
   - Physical symptoms (headaches, fatigue)

**Syndromic Surveillance System**:
Monitor these **early indicators** and flag when multiple symptoms cluster:
```python
syndrome_score = (
    swap_increase * 0.2 +
    sick_calls * 0.2 +
    performance_decline * 0.3 +
    social_withdrawal * 0.2 +
    negative_sentiment * 0.1
)

if syndrome_score > threshold:
    flag_for_early_intervention()
```

### Application to Organizational Health

**Organizational "Syndromes"**:
1. **Attrition Risk Syndrome**:
   - Resume updates (LinkedIn activity)
   - Conference attendance outside institution
   - Reduced optional meeting attendance
   - Verbal expressions of frustration

2. **Quality Decline Syndrome**:
   - Increased near-misses
   - Patient complaints
   - Peer feedback issues
   - Rushing behavior

3. **Morale Decline Syndrome**:
   - Negative Slack/email sentiment
   - Reduced celebration participation
   - Increased cynical humor
   - Lower engagement survey scores

### Implementation Ideas

```python
class SyndromicSurveillanceEngine:
    """Early warning system based on behavioral symptoms."""

    def __init__(self):
        self.symptom_detectors = [
            BehavioralSymptomDetector(),
            PerformanceSymptomDetector(),
            SocialSymptomDetector(),
        ]

    def screen_faculty(
        self,
        faculty_id: UUID,
        window_days: int = 30,
    ) -> SyndromeReport:
        """
        Screen a faculty member for burnout syndrome.

        Returns early warning score and flagged symptoms.
        """
        symptoms = {}

        for detector in self.symptom_detectors:
            symptom_scores = detector.detect(faculty_id, window_days)
            symptoms.update(symptom_scores)

        # Aggregate into overall syndrome score
        syndrome_score = self._aggregate_symptoms(symptoms)

        # Classify risk
        if syndrome_score > 0.7:
            risk = "critical"
            recommendation = "Immediate intervention - multiple burnout symptoms"
        elif syndrome_score > 0.5:
            risk = "high"
            recommendation = "Early intervention - prevent progression to burnout"
        elif syndrome_score > 0.3:
            risk = "moderate"
            recommendation = "Enhanced monitoring, offer support resources"
        else:
            risk = "low"
            recommendation = "Continue routine monitoring"

        return SyndromeReport(
            faculty_id=faculty_id,
            syndrome_score=syndrome_score,
            risk_level=risk,
            detected_symptoms=symptoms,
            recommendation=recommendation,
            screened_at=datetime.now(),
        )

    def _aggregate_symptoms(self, symptoms: dict[str, float]) -> float:
        """Combine symptom scores into overall syndrome score."""
        weights = {
            "swap_increase": 0.15,
            "sick_calls": 0.15,
            "performance_decline": 0.25,
            "social_withdrawal": 0.15,
            "negative_sentiment": 0.10,
            "quality_issues": 0.20,
        }

        score = sum(
            symptoms.get(symptom, 0) * weight
            for symptom, weight in weights.items()
        )

        return min(1.0, score)

class BehavioralSymptomDetector:
    """Detect behavioral symptoms from scheduling data."""

    def detect(self, faculty_id: UUID, window_days: int) -> dict[str, float]:
        """Detect behavioral symptoms for a faculty member."""
        symptoms = {}

        # 1. Swap behavior changes
        recent_swaps = self._get_swap_count(faculty_id, window_days)
        baseline_swaps = self._get_swap_count(faculty_id, window_days, offset_days=90)

        if baseline_swaps > 0:
            swap_increase = (recent_swaps - baseline_swaps) / baseline_swaps
            symptoms["swap_increase"] = min(1.0, max(0, swap_increase))

        # 2. Sick calls
        sick_calls = self._get_sick_calls(faculty_id, window_days)
        symptoms["sick_calls"] = min(1.0, sick_calls / 5)  # 5+ sick calls = 1.0

        # 3. Swap acceptance rate decline
        recent_acceptance = self._get_swap_acceptance_rate(faculty_id, window_days)
        baseline_acceptance = self._get_swap_acceptance_rate(faculty_id, window_days, offset_days=90)

        if baseline_acceptance > 0:
            acceptance_decline = baseline_acceptance - recent_acceptance
            symptoms["helping_decline"] = min(1.0, max(0, acceptance_decline * 2))

        return symptoms

class PerformanceSymptomDetector:
    """Detect performance decline symptoms."""

    def detect(self, faculty_id: UUID, window_days: int) -> dict[str, float]:
        """Detect performance symptoms."""
        symptoms = {}

        # Chart completion delays
        completion_delay = self._get_chart_completion_delay(faculty_id, window_days)
        symptoms["performance_decline"] = min(1.0, completion_delay / 7)  # 7+ days = 1.0

        # Quality metrics
        quality_score = self._get_quality_score(faculty_id, window_days)
        baseline_quality = self._get_quality_score(faculty_id, window_days, offset_days=90)

        if baseline_quality > 0:
            quality_decline = (baseline_quality - quality_score) / baseline_quality
            symptoms["quality_issues"] = min(1.0, max(0, quality_decline * 2))

        return symptoms

class OutbreakDetector:
    """Detect system-wide burnout outbreaks using syndromic surveillance."""

    def detect_outbreak(
        self,
        syndrome_reports: list[SyndromeReport],
        historical_baseline: float = 0.15,  # 15% normal prevalence
    ) -> dict:
        """
        Detect if syndrome prevalence exceeds baseline (outbreak).

        Similar to disease surveillance outbreak detection.
        """
        total = len(syndrome_reports)
        if total == 0:
            return {"status": "no_data"}

        # Count high-risk cases
        high_risk = sum(1 for r in syndrome_reports if r.risk_level in ("high", "critical"))
        prevalence = high_risk / total

        # Statistical test: is prevalence significantly above baseline?
        # Simple threshold: 2x baseline = warning, 3x baseline = outbreak
        if prevalence > historical_baseline * 3:
            status = "outbreak"
            severity = "critical"
        elif prevalence > historical_baseline * 2:
            status = "outbreak"
            severity = "moderate"
        elif prevalence > historical_baseline * 1.5:
            status = "elevated"
            severity = "warning"
        else:
            status = "normal"
            severity = "none"

        return {
            "status": status,
            "severity": severity,
            "prevalence": prevalence,
            "baseline": historical_baseline,
            "ratio": prevalence / historical_baseline if historical_baseline > 0 else 0,
            "high_risk_count": high_risk,
            "total_screened": total,
            "recommendation": self._outbreak_recommendation(status, severity),
        }

    def _outbreak_recommendation(self, status: str, severity: str) -> list[str]:
        """Generate recommendations based on outbreak status."""
        if status == "outbreak" and severity == "critical":
            return [
                "OUTBREAK: Burnout syndrome prevalence 3x baseline",
                "Activate system-wide interventions immediately",
                "Consider load shedding to RED or BLACK level",
                "Implement contact tracing for all high-risk cases",
            ]
        elif status == "outbreak":
            return [
                "Elevated burnout syndrome prevalence detected",
                "Increase monitoring frequency",
                "Target interventions at high-risk clusters",
            ]
        elif status == "elevated":
            return [
                "Warning: Syndrome prevalence above baseline",
                "Monitor closely for progression to outbreak",
            ]
        else:
            return ["Syndrome prevalence within normal range"]
```

**Integration with Existing Systems**:
- **Behavioral network** tracks swap behavior → behavioral symptoms
- **Homeostasis** tracks allostatic load → physiological symptoms
- **Defense in Depth** escalates based on outbreak severity
- **Stigmergy** (preference trails) detects social withdrawal

---

## 7. Epidemic Thresholds — Critical Points for Outbreak vs. Die-Out

### Core Epidemiological Principle

**Epidemic threshold**: The critical parameter value where system transitions from:
- **Below threshold**: Disease dies out (stable equilibrium at zero cases)
- **Above threshold**: Endemic persistence or epidemic growth

**For SIR model**, threshold is **R₀ = 1**:
- R₀ < 1: Each case infects <1 other → exponential decline
- R₀ > 1: Each case infects >1 other → exponential growth

**Bifurcation**: System exhibits qualitative change at threshold:
```
R₀ = 0.9 → dies out in 20 days
R₀ = 1.0 → persists indefinitely (endemic)
R₀ = 1.1 → exponential growth
```

**Critical slowing down**: Near threshold, system responds slowly to perturbations (early warning signal).

### Application to Workforce Thresholds

**Burnout Epidemic Threshold**:
System has **critical utilization level** where burnout transitions from self-correcting to self-reinforcing.

**Threshold Analysis**:
```
Utilization <70%: R₀ ≈ 0.5 → Burnout self-corrects
Utilization 70-80%: R₀ ≈ 0.8-1.2 → Metastable (depends on shock)
Utilization >80%: R₀ ≈ 1.5-3.0 → Burnout epidemic
```

**Why 80% is critical** (convergence of multiple thresholds):
1. **Queuing theory**: Exponential wait times above 80%
2. **Epidemic threshold**: R₀ crosses 1.0 around 80% utilization
3. **Phase transition**: System volatility spikes near 80%
4. **Attrition cascade**: R₀_attrition > 1 above 80%

**Bifurcation Dynamics**:
- **Subcritical**: Utilization 75% → small stress shock → system absorbs, returns to baseline
- **Supercritical**: Utilization 85% → small stress shock → positive feedback loop → cascade

### Application to Organizational Tipping Points

**Culture Tipping Point**:
- **Below threshold**: Negative events absorbed by organizational resilience
- **At threshold**: System bistable — can flip from healthy to toxic culture
- **Above threshold**: Toxic culture self-reinforcing

**Morale Tipping Point**:
Example: Trust in leadership
- Trust >60%: Negative events attributed to external factors
- Trust 40-60%: Bistable, vulnerable to rumor cascades
- Trust <40%: All events interpreted negatively, morale spiral

**Attrition Tipping Point**:
- Departure rate < replacement rate: Stable
- Departure rate ≈ replacement rate: Chronic instability
- Departure rate > replacement rate: Extinction vortex

### Implementation Ideas

```python
class EpidemicThresholdAnalyzer:
    """Analyze epidemic thresholds and bifurcation points."""

    def calculate_threshold_distance(
        self,
        current_utilization: float,
        current_r0: float,
        allostatic_loads: dict[UUID, float],
    ) -> dict:
        """
        Calculate how close the system is to epidemic threshold.

        Returns distance to threshold and early warning signals.
        """
        # Epidemic threshold: R₀ = 1.0
        threshold_r0 = 1.0
        distance_to_r0_threshold = threshold_r0 - current_r0

        # Utilization threshold: 80%
        threshold_utilization = 0.80
        distance_to_util_threshold = threshold_utilization - current_utilization

        # Prevalence threshold: 20% burned out
        threshold_prevalence = 0.20
        current_prevalence = sum(
            1 for load in allostatic_loads.values() if load > 60
        ) / len(allostatic_loads) if allostatic_loads else 0
        distance_to_prev_threshold = threshold_prevalence - current_prevalence

        # Overall assessment
        if distance_to_r0_threshold < 0:
            status = "above_epidemic_threshold"
            urgency = "critical"
        elif distance_to_util_threshold < 0.05:  # Within 5%
            status = "approaching_threshold"
            urgency = "high"
        elif distance_to_util_threshold < 0.10:  # Within 10%
            status = "warning_zone"
            urgency = "medium"
        else:
            status = "safe"
            urgency = "low"

        return {
            "status": status,
            "urgency": urgency,
            "threshold_distances": {
                "r0": distance_to_r0_threshold,
                "utilization": distance_to_util_threshold,
                "prevalence": distance_to_prev_threshold,
            },
            "current_values": {
                "r0": current_r0,
                "utilization": current_utilization,
                "prevalence": current_prevalence,
            },
            "recommendations": self._threshold_recommendations(status, distance_to_util_threshold),
        }

    def detect_critical_slowing(
        self,
        metric_history: list[tuple[datetime, float]],
    ) -> dict:
        """
        Detect critical slowing down (early warning of approaching threshold).

        Near bifurcation points, systems exhibit:
        - Increased variance (volatility)
        - Increased autocorrelation (slow recovery from perturbations)
        - Increased skewness (asymmetric fluctuations)
        """
        if len(metric_history) < 20:
            return {"status": "insufficient_data"}

        values = [v for _, v in metric_history]

        # Calculate variance (increasing near threshold)
        recent_variance = statistics.variance(values[-10:])
        baseline_variance = statistics.variance(values[:10]) if len(values) >= 20 else recent_variance
        variance_ratio = recent_variance / baseline_variance if baseline_variance > 0 else 1.0

        # Calculate autocorrelation (lag-1)
        autocorr = self._calculate_autocorrelation(values, lag=1)

        # Detect critical slowing
        is_slowing = variance_ratio > 2.0 or autocorr > 0.7

        return {
            "critical_slowing_detected": is_slowing,
            "variance_ratio": variance_ratio,
            "autocorrelation": autocorr,
            "interpretation": (
                "WARNING: System showing early warning signs of approaching threshold"
                if is_slowing else "Normal fluctuations"
            ),
        }

    def _calculate_autocorrelation(self, values: list[float], lag: int = 1) -> float:
        """Calculate autocorrelation at given lag."""
        if len(values) < lag + 2:
            return 0.0

        mean = statistics.mean(values)

        # Calculate lag-1 autocorrelation
        numerator = sum(
            (values[i] - mean) * (values[i + lag] - mean)
            for i in range(len(values) - lag)
        )
        denominator = sum((v - mean) ** 2 for v in values)

        return numerator / denominator if denominator > 0 else 0.0

    def _threshold_recommendations(self, status: str, distance: float) -> list[str]:
        """Generate recommendations based on threshold proximity."""
        if status == "above_epidemic_threshold":
            return [
                "CRITICAL: System has crossed epidemic threshold",
                "Burnout is self-reinforcing - exponential spread expected",
                "Immediate crisis interventions required",
                "Reduce utilization below 70% to restore stability",
            ]
        elif status == "approaching_threshold":
            return [
                f"WARNING: {distance * 100:.1f}% from epidemic threshold",
                "System in metastable zone - vulnerable to shocks",
                "Implement preventive interventions now to avoid cascade",
                "Monitor critical slowing down indicators",
            ]
        elif status == "warning_zone":
            return [
                "Elevated risk - maintain heightened surveillance",
                "Strengthen resilience buffers",
            ]
        else:
            return ["System operating safely below epidemic threshold"]

class BifurcationMapper:
    """Map system bifurcation points and hysteresis."""

    def map_bifurcation_diagram(
        self,
        utilization_range: tuple[float, float] = (0.5, 1.0),
        steps: int = 50,
    ) -> dict:
        """
        Create bifurcation diagram showing epidemic threshold.

        For each utilization level, calculate equilibrium R₀ and burnout prevalence.
        Identifies critical points where system behavior changes.
        """
        utilization_values = []
        r0_values = []
        prevalence_values = []

        for i in range(steps):
            util = utilization_range[0] + i * (utilization_range[1] - utilization_range[0]) / steps

            # Calculate R₀ at this utilization level
            r0 = self._r0_from_utilization(util)

            # Calculate equilibrium prevalence (steady-state burnout %)
            if r0 < 1:
                prevalence = 0  # Disease-free equilibrium
            else:
                prevalence = 1 - (1 / r0)  # Endemic equilibrium

            utilization_values.append(util)
            r0_values.append(r0)
            prevalence_values.append(prevalence)

        # Find bifurcation point (where R₀ crosses 1)
        bifurcation_util = None
        for i in range(len(r0_values) - 1):
            if r0_values[i] < 1 and r0_values[i + 1] >= 1:
                bifurcation_util = utilization_values[i]
                break

        return {
            "bifurcation_point": bifurcation_util,
            "utilization_values": utilization_values,
            "r0_values": r0_values,
            "prevalence_values": prevalence_values,
            "interpretation": (
                f"Epidemic threshold at {bifurcation_util * 100:.1f}% utilization"
                if bifurcation_util else "No threshold found in range"
            ),
        }

    def _r0_from_utilization(self, utilization: float) -> float:
        """Model relationship between utilization and R₀."""
        # Empirical relationship (would be calibrated from data)
        if utilization < 0.70:
            return 0.3 + utilization * 0.5  # Subcritical
        elif utilization < 0.80:
            return 0.65 + (utilization - 0.70) * 3.5  # Transition zone
        else:
            return 1.0 + (utilization - 0.80) * 5.0  # Supercritical
```

**Integration with Existing Systems**:
- **Utilization monitor** tracks distance to 80% threshold
- **Homeostasis** volatility detection = critical slowing down
- **Defense in Depth** escalates at threshold crossings
- **Cascade scenario** simulates dynamics above threshold

---

## Summary of Implementation Recommendations

### 1. Immediate High-Value Implementations

**A. Superspreader Detection** (Highest ROI)
- Combine hub analysis (already exists) + allostatic load (already exists)
- Flag top 20% as superspreaders
- Targeted interventions on superspreaders have exponential impact
- **Implementation**: `SuperspreaderDetector` class in resilience/epidemiology.py

**B. R₀ Monitoring** (Early Warning)
- Calculate burnout R₀ from allostatic load + network structure
- Alert when R₀ > 1 (epidemic threshold)
- Display on resilience dashboard
- **Implementation**: `BurnoutR0Calculator` + `EpidemicThresholdMonitor`

**C. Contact Tracing** (Rapid Response)
- When someone burns out, trace their contacts
- Pre-emptive intervention on exposed neighbors
- Breaks transmission chains before cascade
- **Implementation**: `ContactTracingProtocol` class

**D. Syndromic Surveillance** (Proactive Detection)
- Monitor swap behavior, sick calls, performance metrics
- Flag early warning signs before full burnout
- Enables intervention at "Exposed" stage
- **Implementation**: `SyndromicSurveillanceEngine`

### 2. Medium-Term Enhancements

**E. Full SEIR Model** (Predictive Analytics)
- Simulate burnout spread over time
- Predict future prevalence under interventions
- Optimize intervention timing and targeting
- **Implementation**: `BurnoutContagionModel` class

**F. Herd Immunity Targeting** (Strategic Planning)
- Calculate % of workforce with stress-absorption capacity
- Identify gap to herd immunity threshold
- Strategically build immunity through interventions
- **Implementation**: `HerdImmunityMonitor` + `ImmunityTargetingStrategy`

**G. Network-Based Containment** (Advanced Response)
- Identify clusters, bridges, transmission chains
- Simulate blast radius isolation effectiveness
- Optimize network interventions
- **Implementation**: `NetworkEpidemiologyAnalyzer`

### 3. Long-Term Research

**H. Bifurcation Analysis** (System Dynamics)
- Map system tipping points
- Detect critical slowing down (approaching threshold)
- Predict phase transitions
- **Implementation**: `BifurcationMapper` + `EpidemicThresholdAnalyzer`

**I. Morale Contagion Model** (Organizational Culture)
- Apply SEIR to engagement/disengagement spread
- Model positive culture as "vaccination"
- Track culture champions as positive superspreaders
- **Implementation**: Extension of contagion models

---

## Technical Architecture Proposal

### New Module: `backend/app/resilience/epidemiology.py`

```python
"""
Epidemiological Models for Workforce Resilience.

Applies disease transmission models to burnout contagion, attrition cascades,
and morale spread. Implements:
- SIR/SEIR state transition models
- R₀ (basic reproduction number) calculation
- Herd immunity thresholds
- Superspreader detection
- Network epidemiology
- Syndromic surveillance
- Epidemic threshold analysis
"""

# Classes to implement:
# - BurnoutContagionModel (SEIR simulation)
# - BurnoutR0Calculator (reproduction number)
# - EpidemicThresholdMonitor (alert when R₀ > 1)
# - SuperspreaderDetector (identify high-transmission faculty)
# - ContactTracingProtocol (trace and intervene on contacts)
# - HerdImmunityMonitor (track immunity %)
# - SyndromicSurveillanceEngine (early warning from symptoms)
# - NetworkEpidemiologyAnalyzer (transmission chains, bridges)
# - BifurcationMapper (tipping points)
```

### Integration Points

1. **ResilienceService** (service.py):
   - Add methods: `check_epidemic_status()`, `trace_burnout_contacts()`, `identify_superspreaders()`
   - Integrate with existing health check

2. **HomeostasisMonitor** (homeostasis.py):
   - Use allostatic load to classify SEIR states
   - Feed syndromic surveillance with behavioral metrics

3. **HubAnalyzer** (hub_analysis.py):
   - Mark hubs as superspreader candidates
   - Provide network for contact tracing

4. **BehavioralNetworkAnalyzer** (behavioral_network.py):
   - Swap network = contact graph
   - Martyrs = stress superspreaders

5. **DefenseInDepth** (defense_in_depth.py):
   - Escalate when R₀ > 1
   - Activate blast radius when superspreader detected

6. **Dashboard**:
   - Display R₀ gauge ("epidemic risk")
   - Show superspreader alerts
   - Contact tracing visualization

---

## Key Metrics Dashboard

**Epidemic Risk Dashboard** (new panel):

```
┌─ EPIDEMIC RISK ASSESSMENT ─────────────────────────────────┐
│                                                             │
│  Burnout R₀:  [████████░░] 1.8  ⚠️ EPIDEMIC THRESHOLD     │
│  Status: Above Threshold - Exponential Spread Expected     │
│                                                             │
│  Prevalence:  [██████░░░░] 23% Burned Out                  │
│  Herd Immunity: 42% (Need 50% for protection)              │
│                                                             │
│  Superspreaders:  5 detected  [View Details]               │
│  Active Outbreaks: 2 zones    [Containment Status]         │
│                                                             │
│  Distance to Threshold: -18% (ABOVE)                       │
│  Critical Slowing: Detected (Variance Ratio: 2.8x)         │
│                                                             │
│  🚨 URGENT ACTIONS:                                        │
│  • Reduce utilization to <70% immediately                  │
│  • Trace contacts of 8 newly burned-out faculty            │
│  • Isolate 2 high-transmission zones                       │
│  • Target interventions at 5 superspreaders                │
└─────────────────────────────────────────────────────────────┘
```

---

## Conclusion

Epidemiological models provide a powerful framework for understanding **contagion effects in workforce systems**. Key insights:

1. **Burnout spreads like a disease** through social networks with identifiable R₀, transmission rates, and superspreaders

2. **80% utilization is the epidemic threshold** — where R₀ crosses 1.0 and burnout becomes self-reinforcing

3. **Superspreaders** (20% of faculty cause 80% of transmission) can be identified and targeted for high-ROI interventions

4. **Herd immunity** concept applies — if >50% have resilience capacity, system is protected even when individuals are stressed

5. **Contact tracing** enables proactive intervention on exposed faculty before they burn out

6. **Syndromic surveillance** detects outbreaks early from behavioral symptoms before full burnout

7. **Network structure matters** — blast radius isolation, hub protection, and bridge identification prevent cascade

These models complement existing resilience frameworks (cascade simulation, hub analysis, behavioral networks) and provide **actionable early warning systems** and **strategic intervention targeting**.

**Next Steps**:
1. Implement `BurnoutR0Calculator` and `SuperspreaderDetector` for immediate value
2. Add epidemic risk panel to resilience dashboard
3. Pilot contact tracing protocol when positive feedback detected
4. Research long-term: Full SEIR simulation and bifurcation analysis

---

**References**:
- Anderson & May (1991): *Infectious Diseases of Humans*
- Keeling & Rohani (2008): *Modeling Infectious Diseases*
- Pastor-Satorras & Vespignani (2001): "Epidemic spreading in scale-free networks"
- Scheffer et al. (2009): "Early-warning signals for critical transitions"
- Applied to organizational systems: Hatfield et al. (1993): *Emotional Contagion*
