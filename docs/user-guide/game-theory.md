# Game Theory Analysis Dashboard

The Game Theory dashboard enables empirical testing of resilience configurations using Axelrod's Prisoner's Dilemma framework.

---

## Overview

This feature allows administrators to:

- Define configuration strategies that represent different operational approaches
- Run tournaments to compare strategies against each other
- Simulate evolutionary dynamics to find stable configurations
- Validate configurations against proven benchmarks

---

## Accessing the Dashboard

Navigate to **Admin > Game Theory** from the main sidebar.

The dashboard requires Administrator or Coordinator role access.

---

## Dashboard Tabs

### Overview Tab

The Overview tab shows summary statistics:

| Widget | Description |
|--------|-------------|
| **Active Strategies** | Number of defined configuration strategies |
| **Tournaments Run** | Total completed tournaments |
| **Evolution Simulations** | Total evolutionary simulations |
| **Most Successful Strategy** | Strategy with highest win rate |

---

### Strategies Tab

Manage configuration strategies that compete in tournaments.

#### Creating a Strategy

1. Click **Create Strategy**
2. Fill in the strategy details:
   - **Name**: Descriptive name (e.g., "Conservative 70%")
   - **Type**: Select behavior pattern
   - **Utilization Target**: Target resource utilization (0.0-1.0)
   - **Cross-Zone Borrowing**: Enable/disable resource sharing
   - **Sacrifice Willingness**: low, medium, or high

3. Click **Save**

#### Strategy Types

| Type | Behavior | Best For |
|------|----------|----------|
| **Cooperative** | Always shares resources | Stable environments |
| **Aggressive** | Maximizes own performance | Testing worst-case |
| **Tit for Tat** | Mirrors neighbor behavior | Adaptive response |
| **Grudger** | Cooperates until betrayed | Defensive posture |
| **Random** | Unpredictable actions | Chaos testing |
| **Custom** | User-defined logic | Special cases |

#### Validating a Strategy

Click **Validate** on any strategy to test it against the Tit for Tat benchmark:

| Result | Meaning |
|--------|---------|
| **Passed** | Strategy cooperates well with neighbors |
| **Failed** | Strategy is too aggressive for shared environments |

---

### Tournaments Tab

Run round-robin tournaments to compare strategies.

#### Creating a Tournament

1. Click **New Tournament**
2. Configure tournament settings:
   - **Name**: Tournament identifier
   - **Strategies**: Select 2+ strategies to compete
   - **Turns per Match**: Interactions per matchup (default: 200)
   - **Repetitions**: Times to repeat each matchup (default: 50)
   - **Noise**: Random action probability (default: 0)

3. Click **Start Tournament**

#### Reading Tournament Results

After completion, view:

- **Rankings**: Strategies ordered by total score
- **Payoff Matrix**: Heatmap showing scores for each pairing
- **Cooperation Rates**: How often each strategy cooperated
- **Match Details**: Individual matchup results

#### Interpreting the Payoff Matrix

The payoff matrix shows average scores for each strategy pairing:

```
                    Opponent
           Coop    TFT    Aggr
       ┌────────┬───────┬───────┐
 Self  │  3.0   │  3.0  │  0.5  │  Coop
       ├────────┼───────┼───────┤
       │  3.0   │  3.0  │  1.5  │  TFT
       ├────────┼───────┼───────┤
       │  4.5   │  1.5  │  1.0  │  Aggr
       └────────┴───────┴───────┘
```

- **3.0**: Mutual cooperation (both benefit)
- **1.0**: Mutual defection (both suffer)
- **4.5/0.5**: One exploits the other

---

### Evolution Tab

Simulate evolutionary dynamics using the Moran process.

#### Creating an Evolution Simulation

1. Click **New Evolution**
2. Configure settings:
   - **Name**: Simulation identifier
   - **Population Size**: Total agents (default: 100)
   - **Max Generations**: Limit on iterations (default: 500)
   - **Initial Mix**: Select strategies and their starting counts

3. Click **Start Evolution**

#### Reading Evolution Results

The evolution chart shows population dynamics over time:

- **X-axis**: Generation number
- **Y-axis**: Population count for each strategy
- **Fixation**: When one strategy reaches 100%

Key metrics:

| Metric | Meaning |
|--------|---------|
| **Winner** | Strategy that achieved fixation |
| **Generations to Fixation** | How quickly winner dominated |
| **Evolutionarily Stable** | Cannot be invaded by mutants |

#### What the Results Mean

- **TFT wins quickly**: Cooperative behavior is optimal
- **Aggressive wins**: Environment rewards competition (investigate)
- **No fixation**: Multiple viable strategies (meta-stable)

---

### Analysis Tab

Analyze your current system configuration.

#### Running Analysis

1. Click **Analyze Current Config**
2. Review the assessment:
   - **Strategy Classification**: What type your config resembles
   - **Matchup Results**: How it performs against standard opponents
   - **Production Readiness**: Whether it's suitable for deployment

#### Recommendations

The analysis provides actionable recommendations:

| Recommendation | Action |
|----------------|--------|
| "Too aggressive" | Lower utilization target, enable borrowing |
| "Too passive" | Consider moderate response to defection |
| "Production ready" | Configuration is well-balanced |

---

## Best Practices

### Testing New Configurations

1. Create strategy representing the new config
2. Validate against TFT benchmark
3. Run tournament against existing strategies
4. Run evolution to test stability
5. Deploy only if evolutionarily stable

### Interpreting Results

- **High cooperation rate + high score** = Good production candidate
- **Low cooperation rate + high score** = Exploits others, avoid
- **High cooperation rate + low score** = Too passive
- **Evolution winner** = Most robust choice

### Common Patterns

| Pattern | Interpretation |
|---------|---------------|
| TFT consistently wins | System rewards reciprocity |
| Aggressive wins short-term | But loses in evolution |
| Cooperative + TFT tie | Healthy cooperative environment |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Tournament takes too long | Reduce turns or repetitions |
| Evolution doesn't converge | Increase max generations |
| All strategies score equally | Add more diverse strategy types |
| Validation always fails | Check utilization target < 0.85 |

---

## Related Documentation

- [Game Theory API Reference](../api/game-theory.md)
- [Architecture Overview](../architecture/game-theory-framework.md)
- [Resilience Framework](../architecture/cross-disciplinary-resilience.md)
