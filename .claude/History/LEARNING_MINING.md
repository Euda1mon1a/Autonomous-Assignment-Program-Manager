# Learning Mining Guide for META_UPDATER

> **Purpose**: How META_UPDATER systematically mines learning entries to improve AI infrastructure
> **Last Updated**: 2025-12-26
> **Audience**: META_UPDATER skill, Human maintainers

---

## Table of Contents

1. [Overview](#overview)
2. [Mining Workflow](#mining-workflow)
3. [Query Patterns](#query-patterns)
4. [Aggregation Strategies](#aggregation-strategies)
5. [Priority Scoring](#priority-scoring)
6. [Skill Update Proposals](#skill-update-proposals)
7. [Implementation Tracking](#implementation-tracking)
8. [Examples](#examples)

---

## Overview

**Learning Mining** is the process by which META_UPDATER:
1. Scans all learning entries (`.claude/History/LEARN-*.md`)
2. Identifies patterns, recurring themes, and gaps
3. Scores learnings by priority (recency, severity, frequency)
4. Generates skill update proposals
5. Tracks implementation and measures impact

### Goals

- **Continuous Improvement**: Evolve skills based on real-world experience
- **Pattern Recognition**: Identify recurring issues before they become systemic
- **Knowledge Transfer**: Codify human expertise into reusable skills
- **Metrics-Driven**: Use data to prioritize high-impact improvements

### Mining Frequency

| Frequency | Trigger | Purpose |
|-----------|---------|---------|
| **Weekly** | Every Monday 9 AM | Routine learning review, dashboard generation |
| **On-Demand** | After critical incident | Immediate pattern analysis |
| **Monthly** | First Monday of month | Comprehensive skill audit |
| **Quarterly** | End of quarter | Strategic planning, skill lifecycle decisions |

---

## Mining Workflow

### Phase 1: Discovery

```bash
# 1. Scan for new learning entries
NEW_ENTRIES=$(find .claude/History -name "LEARN-*.md" -mtime -7)

# 2. Parse metadata from frontmatter
for entry in $NEW_ENTRIES; do
  extract_metadata "$entry"  # id, date, type, severity, source, status, tags
done

# 3. Index by various dimensions
index_by_severity
index_by_component
index_by_skill
index_by_tags
```

**Output**: Structured dataset of all learnings with metadata

### Phase 2: Analysis

```python
# Aggregate learnings by multiple dimensions
learnings_df = load_learning_entries()

# Group by tags to find patterns
tag_frequency = learnings_df['tags'].explode().value_counts()

# Group by component to find hotspots
component_issues = learnings_df.groupby('component').agg({
    'id': 'count',
    'severity': lambda x: (x == 'critical').sum()
})

# Temporal analysis (are issues increasing?)
weekly_trends = learnings_df.set_index('date').resample('W').size()

# Related learnings (same root cause?)
cluster_related_learnings(learnings_df)
```

**Output**:
- Tag frequency distribution
- Component hotspots
- Temporal trends
- Related learning clusters

### Phase 3: Prioritization

```python
# Score each learning for priority
def calculate_priority_score(learning: dict) -> float:
    """
    Calculate priority score (0-100) based on multiple factors.

    Factors:
    - Severity: critical=40, warning=20, info=10
    - Recency: Exponential decay (recent=high)
    - Frequency: Similar learnings boost score
    - Implementation: Not implemented = higher priority
    - Impact: Blast radius from metadata
    """
    score = 0

    # Severity weight (40 points max)
    severity_weights = {'critical': 40, 'warning': 20, 'info': 10}
    score += severity_weights.get(learning['severity'], 0)

    # Recency weight (30 points max)
    days_ago = (datetime.now() - learning['date']).days
    recency_score = 30 * math.exp(-0.05 * days_ago)  # Exponential decay
    score += recency_score

    # Frequency weight (20 points max)
    similar_count = count_similar_learnings(learning)
    frequency_score = min(20, similar_count * 5)
    score += frequency_score

    # Implementation status (10 points bonus if not implemented)
    if learning['status'] != 'implemented':
        score += 10

    # Impact multiplier (blast radius)
    if 'critical' in learning.get('blast_radius', '').lower():
        score *= 1.5

    return min(100, score)  # Cap at 100
```

**Output**: Priority-ranked list of learnings

### Phase 4: Pattern Extraction

```python
# Extract actionable patterns
def extract_patterns(learnings: list[dict]) -> list[dict]:
    """
    Identify recurring patterns that warrant skill updates.

    Pattern types:
    1. Recurring Error: Same error type across multiple learnings
    2. Missing Guardrail: Edge case not caught by existing skills
    3. New Best Practice: Successful approach worth codifying
    4. Knowledge Gap: Domain area with no dedicated skill
    """
    patterns = []

    # 1. Recurring errors (3+ occurrences)
    error_groups = group_by_field(learnings, 'error_type')
    for error_type, group in error_groups.items():
        if len(group) >= 3:
            patterns.append({
                'type': 'recurring_error',
                'name': error_type,
                'frequency': len(group),
                'learnings': [l['id'] for l in group],
                'suggested_action': 'Add guardrail to prevent recurrence'
            })

    # 2. Missing guardrails (severity=critical, status=implemented)
    critical_implemented = [l for l in learnings
                           if l['severity'] == 'critical'
                           and l['status'] == 'implemented']
    for learning in critical_implemented:
        if 'edge_case' in learning.get('tags', []):
            patterns.append({
                'type': 'missing_guardrail',
                'name': f"Edge case: {learning['summary']}",
                'frequency': 1,
                'learnings': [learning['id']],
                'suggested_action': f"Update {learning.get('affected_skill', 'unknown')} skill"
            })

    # 3. New best practices (source=experiment, outcome=success)
    experiments = [l for l in learnings if l['source'] == 'experiment']
    for exp in experiments:
        if 'success' in exp.get('outcome', '').lower():
            patterns.append({
                'type': 'best_practice',
                'name': exp['summary'],
                'frequency': 1,
                'learnings': [exp['id']],
                'suggested_action': 'Codify as skill guidance'
            })

    # 4. Knowledge gaps (5+ learnings in area with no skill)
    component_counts = count_by_component(learnings)
    existing_skills = load_skill_names()
    for component, count in component_counts.items():
        if count >= 5 and component not in existing_skills:
            patterns.append({
                'type': 'knowledge_gap',
                'name': component,
                'frequency': count,
                'learnings': [l['id'] for l in learnings if l['component'] == component],
                'suggested_action': f'Create new skill: {component}'
            })

    return sorted(patterns, key=lambda p: p['frequency'], reverse=True)
```

**Output**: List of actionable patterns with suggested actions

### Phase 5: Proposal Generation

```python
# Generate skill update proposals
def generate_proposals(patterns: list[dict]) -> list[dict]:
    """
    Create concrete skill update proposals from patterns.

    Proposal structure:
    - skill_name: Which skill to update (or "NEW" for new skill)
    - change_type: "enhancement" | "bugfix" | "new_skill" | "deprecation"
    - priority: 1-5 (1=highest)
    - effort: "low" | "medium" | "high"
    - impact: "low" | "medium" | "high"
    - rationale: Why this change?
    - diff: Proposed changes to skill prompt/logic
    """
    proposals = []

    for pattern in patterns:
        if pattern['type'] == 'recurring_error':
            proposals.append({
                'skill_name': infer_skill_from_learnings(pattern['learnings']),
                'change_type': 'enhancement',
                'priority': 2 if pattern['frequency'] >= 5 else 3,
                'effort': 'medium',
                'impact': 'high' if pattern['frequency'] >= 5 else 'medium',
                'rationale': f"Prevent recurring {pattern['name']} error ({pattern['frequency']} occurrences)",
                'diff': generate_guardrail_diff(pattern),
                'evidence': pattern['learnings']
            })

        elif pattern['type'] == 'knowledge_gap':
            proposals.append({
                'skill_name': f"{pattern['name']}-skill",
                'change_type': 'new_skill',
                'priority': 1 if pattern['frequency'] >= 10 else 2,
                'effort': 'high',
                'impact': 'high',
                'rationale': f"No dedicated skill for {pattern['name']} ({pattern['frequency']} related learnings)",
                'diff': generate_new_skill_template(pattern),
                'evidence': pattern['learnings']
            })

        # ... similar logic for other pattern types

    # Sort by priority, then impact
    return sorted(proposals, key=lambda p: (p['priority'], -impact_score(p['impact'])))
```

**Output**: Prioritized list of skill update proposals

---

## Query Patterns

### Finding Learnings by Severity

```bash
# Critical learnings in the last 30 days
grep -l "severity: critical" .claude/History/LEARN-*.md | \
  xargs ls -lt | \
  head -n 30
```

```python
# Python equivalent
from pathlib import Path
import yaml
from datetime import datetime, timedelta

def find_critical_learnings(days: int = 30) -> list[dict]:
    """Find critical learnings within the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    learnings = []

    for path in Path('.claude/History').glob('LEARN-*.md'):
        with open(path) as f:
            content = f.read()
            # Parse YAML frontmatter
            if content.startswith('---'):
                frontmatter = yaml.safe_load(content.split('---')[1])
                if (frontmatter.get('severity') == 'critical' and
                    datetime.fromisoformat(frontmatter['date']) >= cutoff):
                    learnings.append({
                        'path': str(path),
                        **frontmatter
                    })

    return sorted(learnings, key=lambda x: x['date'], reverse=True)
```

### Finding Learnings by Component

```bash
# Learnings affecting the scheduler
grep -l "component.*scheduler" .claude/History/LEARN-*.md
```

```python
def find_learnings_by_component(component: str) -> list[dict]:
    """Find all learnings affecting a specific component."""
    learnings = []

    for path in Path('.claude/History').glob('LEARN-*.md'):
        with open(path) as f:
            content = f.read()
            if f'component: {component}' in content or f'- {component}' in content:
                # Parse and append
                learnings.append(parse_learning(path))

    return learnings
```

### Finding Unimplemented Learnings

```bash
# Learnings that haven't been implemented yet
grep -l "status: draft\\|status: validated" .claude/History/LEARN-*.md
```

```python
def find_unimplemented_learnings(min_age_days: int = 7) -> list[dict]:
    """Find learnings older than N days that aren't implemented."""
    cutoff = datetime.now() - timedelta(days=min_age_days)
    learnings = []

    for path in Path('.claude/History').glob('LEARN-*.md'):
        frontmatter = parse_frontmatter(path)
        if (frontmatter.get('status') in ['draft', 'validated'] and
            datetime.fromisoformat(frontmatter['date']) <= cutoff):
            learnings.append({
                'path': str(path),
                'age_days': (datetime.now() - datetime.fromisoformat(frontmatter['date'])).days,
                **frontmatter
            })

    return sorted(learnings, key=lambda x: x['age_days'], reverse=True)
```

### Finding Related Learnings

```python
def find_related_learnings(learning_id: str) -> list[dict]:
    """Find learnings related to a given learning entry."""
    # Load the learning
    learning = load_learning_by_id(learning_id)
    related = []

    # Strategy 1: Explicit references in "Related Learnings" section
    if 'related_to' in learning:
        for ref_id in learning['related_to']:
            related.append(load_learning_by_id(ref_id))

    # Strategy 2: Same tags (intersection)
    learning_tags = set(learning.get('tags', []))
    for path in Path('.claude/History').glob('LEARN-*.md'):
        other = parse_learning(path)
        if other['id'] == learning_id:
            continue
        other_tags = set(other.get('tags', []))
        overlap = len(learning_tags & other_tags)
        if overlap >= 2:  # At least 2 tags in common
            related.append({
                'overlap_score': overlap,
                **other
            })

    # Strategy 3: Text similarity (TF-IDF or embedding-based)
    # ... (advanced, optional)

    return sorted(related, key=lambda x: x.get('overlap_score', 0), reverse=True)
```

---

## Aggregation Strategies

### Temporal Aggregation (Trends)

```python
import pandas as pd

def analyze_temporal_trends() -> pd.DataFrame:
    """Analyze learning creation trends over time."""
    learnings = load_all_learnings()
    df = pd.DataFrame(learnings)
    df['date'] = pd.to_datetime(df['date'])

    # Resample by week
    weekly = df.set_index('date').resample('W').agg({
        'id': 'count',  # Total learnings per week
        'severity': lambda x: (x == 'critical').sum()  # Critical per week
    })
    weekly.columns = ['total_learnings', 'critical_learnings']

    # Calculate moving average
    weekly['ma_4week'] = weekly['total_learnings'].rolling(4).mean()

    # Detect trends
    weekly['trend'] = 'stable'
    weekly.loc[weekly['total_learnings'] > weekly['ma_4week'] * 1.2, 'trend'] = 'increasing'
    weekly.loc[weekly['total_learnings'] < weekly['ma_4week'] * 0.8, 'trend'] = 'decreasing'

    return weekly
```

### Component Aggregation (Hotspots)

```python
def identify_component_hotspots(min_count: int = 3) -> list[dict]:
    """Find components with high incident rates."""
    learnings = load_all_learnings()

    # Count by component
    component_counts = {}
    for learning in learnings:
        for component in learning.get('affected_components', []):
            if component not in component_counts:
                component_counts[component] = {
                    'total': 0,
                    'critical': 0,
                    'warning': 0,
                    'info': 0,
                    'learnings': []
                }
            component_counts[component]['total'] += 1
            component_counts[component][learning['severity']] += 1
            component_counts[component]['learnings'].append(learning['id'])

    # Filter and sort
    hotspots = [
        {'component': comp, **data}
        for comp, data in component_counts.items()
        if data['total'] >= min_count
    ]
    return sorted(hotspots, key=lambda x: x['critical'] * 3 + x['warning'], reverse=True)
```

### Skill Aggregation (Coverage)

```python
def analyze_skill_coverage() -> dict:
    """Analyze which skills are referenced in learnings."""
    learnings = load_all_learnings()
    skills = load_all_skills()

    coverage = {}
    for skill_name in skills:
        coverage[skill_name] = {
            'learnings_referencing': 0,
            'learnings_updated_as_result': 0,
            'last_updated': get_skill_last_updated(skill_name),
            'learning_ids': []
        }

    for learning in learnings:
        # Check if learning mentions skill
        for skill_name in skills:
            if skill_name in learning.get('tags', []) or \
               skill_name in learning.get('content', ''):
                coverage[skill_name]['learnings_referencing'] += 1
                coverage[skill_name]['learning_ids'].append(learning['id'])

                # Check if learning led to skill update
                if f"Update skill: {skill_name}" in learning.get('action_items', []):
                    coverage[skill_name]['learnings_updated_as_result'] += 1

    # Identify skills with gaps
    for skill_name, data in coverage.items():
        if data['learnings_referencing'] >= 3 and data['learnings_updated_as_result'] == 0:
            data['needs_update'] = True
        else:
            data['needs_update'] = False

    return coverage
```

### Tag Aggregation (Themes)

```python
def extract_recurring_themes(min_frequency: int = 3) -> list[dict]:
    """Find recurring themes from tag analysis."""
    learnings = load_all_learnings()

    # Flatten all tags
    all_tags = []
    for learning in learnings:
        all_tags.extend(learning.get('tags', []))

    # Count frequencies
    from collections import Counter
    tag_freq = Counter(all_tags)

    # Extract recurring themes
    themes = []
    for tag, count in tag_freq.most_common():
        if count >= min_frequency:
            # Find learnings with this tag
            related_learnings = [
                l for l in learnings if tag in l.get('tags', [])
            ]

            themes.append({
                'theme': tag,
                'frequency': count,
                'learnings': [l['id'] for l in related_learnings],
                'severity_breakdown': {
                    'critical': sum(1 for l in related_learnings if l['severity'] == 'critical'),
                    'warning': sum(1 for l in related_learnings if l['severity'] == 'warning'),
                    'info': sum(1 for l in related_learnings if l['severity'] == 'info')
                }
            })

    return themes
```

---

## Priority Scoring

### Scoring Algorithm

```python
class LearningPriorityScorer:
    """
    Calculate priority scores for learning entries.

    Score components (0-100 scale):
    - Severity: 40 points (critical=40, warning=20, info=10)
    - Recency: 30 points (exponential decay over 90 days)
    - Frequency: 20 points (similar learnings boost score)
    - Implementation Status: 10 points (unimplemented gets bonus)
    - Impact Multiplier: 1.0x-2.0x (blast radius modifier)
    """

    def __init__(self):
        self.severity_weights = {
            'critical': 40,
            'warning': 20,
            'info': 10
        }
        self.recency_half_life = 30  # days

    def calculate_score(self, learning: dict, all_learnings: list[dict]) -> float:
        """Calculate composite priority score."""
        score = 0

        # 1. Severity (40 points max)
        score += self.severity_weights.get(learning['severity'], 0)

        # 2. Recency (30 points max)
        days_ago = (datetime.now() - datetime.fromisoformat(learning['date'])).days
        recency_score = 30 * math.exp(-math.log(2) * days_ago / self.recency_half_life)
        score += recency_score

        # 3. Frequency (20 points max)
        similar_count = self._count_similar_learnings(learning, all_learnings)
        frequency_score = min(20, similar_count * 4)
        score += frequency_score

        # 4. Implementation status (10 points)
        if learning.get('status') != 'implemented':
            score += 10

        # 5. Impact multiplier
        blast_radius = learning.get('blast_radius', '').lower()
        if 'entire system' in blast_radius or 'high' in blast_radius:
            score *= 2.0
        elif 'multiple' in blast_radius or 'medium' in blast_radius:
            score *= 1.5

        return min(100, score)

    def _count_similar_learnings(self, learning: dict, all_learnings: list[dict]) -> int:
        """Count learnings with similar tags or components."""
        count = 0
        learning_tags = set(learning.get('tags', []))
        learning_components = set(learning.get('affected_components', []))

        for other in all_learnings:
            if other['id'] == learning['id']:
                continue

            other_tags = set(other.get('tags', []))
            other_components = set(other.get('affected_components', []))

            # Check tag overlap
            if len(learning_tags & other_tags) >= 2:
                count += 1
            # Check component overlap
            elif len(learning_components & other_components) >= 1:
                count += 0.5

        return int(count)

    def rank_learnings(self, learnings: list[dict]) -> list[dict]:
        """Rank all learnings by priority score."""
        scored = []
        for learning in learnings:
            score = self.calculate_score(learning, learnings)
            scored.append({
                'score': score,
                **learning
            })

        return sorted(scored, key=lambda x: x['score'], reverse=True)
```

### Priority Buckets

```python
def categorize_by_priority(learnings: list[dict]) -> dict:
    """Categorize learnings into priority buckets."""
    scorer = LearningPriorityScorer()
    ranked = scorer.rank_learnings(learnings)

    return {
        'P1_Critical_Urgent': [l for l in ranked if l['score'] >= 80],
        'P2_High_Priority': [l for l in ranked if 60 <= l['score'] < 80],
        'P3_Medium_Priority': [l for l in ranked if 40 <= l['score'] < 60],
        'P4_Low_Priority': [l for l in ranked if 20 <= l['score'] < 40],
        'P5_Backlog': [l for l in ranked if l['score'] < 20]
    }
```

---

## Skill Update Proposals

### Proposal Template

```python
class SkillUpdateProposal:
    """Structured proposal for skill updates."""

    def __init__(
        self,
        skill_name: str,
        change_type: str,  # "enhancement" | "bugfix" | "new_skill" | "deprecation"
        priority: int,  # 1-5 (1=highest)
        effort: str,  # "low" | "medium" | "high"
        impact: str,  # "low" | "medium" | "high"
        rationale: str,
        evidence_learnings: list[str],  # Learning IDs
        proposed_diff: str  # Markdown diff of proposed changes
    ):
        self.skill_name = skill_name
        self.change_type = change_type
        self.priority = priority
        self.effort = effort
        self.impact = impact
        self.rationale = rationale
        self.evidence_learnings = evidence_learnings
        self.proposed_diff = proposed_diff
        self.created_at = datetime.now()
        self.status = "proposed"  # proposed | approved | implemented | rejected

    def to_markdown(self) -> str:
        """Generate markdown proposal document."""
        return f"""# Skill Update Proposal: {self.skill_name}

**Created**: {self.created_at.strftime('%Y-%m-%d')}
**Priority**: P{self.priority}
**Effort**: {self.effort.capitalize()}
**Impact**: {self.impact.capitalize()}
**Status**: {self.status}

## Change Type
{self.change_type.replace('_', ' ').title()}

## Rationale
{self.rationale}

## Evidence
Based on the following learning entries:
{''.join(f"- {lid}\n" for lid in self.evidence_learnings)}

## Proposed Changes

```diff
{self.proposed_diff}
```

## Implementation Checklist
- [ ] Update skill prompt/logic
- [ ] Add test cases if applicable
- [ ] Update skill documentation
- [ ] Notify users if breaking change
- [ ] Deploy and monitor

## Approval
- [ ] Approved by META_UPDATER
- [ ] Reviewed by human maintainer (if high-effort or high-impact)
"""
```

### Diff Generation

```python
def generate_skill_diff(pattern: dict) -> str:
    """Generate proposed diff for skill update."""
    if pattern['type'] == 'recurring_error':
        # Add guardrail to prevent error
        return f"""
+ ## Guardrail: Prevent {pattern['name']}
+
+ Before performing [OPERATION], verify:
+ - [ ] Condition A is met
+ - [ ] Edge case B is handled
+ - [ ] Validation C passes
+
+ If any check fails, halt and alert the user.
"""

    elif pattern['type'] == 'missing_guardrail':
        # Add specific edge case handling
        return f"""
+ ## Edge Case: {pattern['name']}
+
+ **Background**: [Explain edge case from learning]
+
+ **Detection**: Watch for [TRIGGER CONDITIONS]
+
+ **Handling**:
+ 1. [Step 1]
+ 2. [Step 2]
+ 3. [Step 3]
"""

    elif pattern['type'] == 'best_practice':
        # Add best practice guidance
        return f"""
+ ## Best Practice: {pattern['name']}
+
+ When [SITUATION], prefer [APPROACH] because [REASON].
+
+ **Example**:
+ ```
+ [CODE EXAMPLE]
+ ```
"""

    else:
        return "# TODO: Manual diff creation required"
```

### Approval Workflow

```python
def approve_proposal(proposal: SkillUpdateProposal) -> bool:
    """
    Automated approval logic for skill update proposals.

    Auto-approve if:
    - Priority 1-2 AND Low effort AND Medium+ impact
    - Bugfix type (any priority, any effort)
    - Enhancement with clear evidence (3+ learnings)

    Require human review if:
    - High effort
    - New skill creation
    - Deprecation
    - Priority 4-5 (low priority)
    """
    # Auto-approve conditions
    if (proposal.priority <= 2 and
        proposal.effort == 'low' and
        proposal.impact in ['medium', 'high']):
        proposal.status = "approved"
        return True

    if proposal.change_type == 'bugfix':
        proposal.status = "approved"
        return True

    if (proposal.change_type == 'enhancement' and
        len(proposal.evidence_learnings) >= 3):
        proposal.status = "approved"
        return True

    # Require human review
    proposal.status = "needs_review"
    notify_human_reviewer(proposal)
    return False
```

---

## Implementation Tracking

### Tracking Proposal Lifecycle

```python
class ProposalTracker:
    """Track skill update proposals from creation to deployment."""

    def __init__(self):
        self.proposals_db = load_proposals()  # JSON or database

    def create_proposal(self, proposal: SkillUpdateProposal) -> str:
        """Create a new proposal and assign ID."""
        proposal_id = f"PROP-{datetime.now().strftime('%Y-%m')}-{len(self.proposals_db) + 1:03d}"
        self.proposals_db[proposal_id] = proposal.to_dict()
        save_proposals(self.proposals_db)
        return proposal_id

    def update_status(self, proposal_id: str, new_status: str, notes: str = ""):
        """Update proposal status with timestamp."""
        proposal = self.proposals_db[proposal_id]
        proposal['status'] = new_status
        proposal['status_history'].append({
            'status': new_status,
            'timestamp': datetime.now().isoformat(),
            'notes': notes
        })
        save_proposals(self.proposals_db)

    def track_implementation(self, proposal_id: str, commit_hash: str, pr_number: int):
        """Link proposal to implementation."""
        proposal = self.proposals_db[proposal_id]
        proposal['implementation'] = {
            'commit': commit_hash,
            'pr': pr_number,
            'deployed_at': datetime.now().isoformat()
        }
        proposal['status'] = 'implemented'
        save_proposals(self.proposals_db)

    def measure_impact(self, proposal_id: str, metric_deltas: dict):
        """Record impact metrics after deployment."""
        proposal = self.proposals_db[proposal_id]
        proposal['impact_metrics'] = metric_deltas
        save_proposals(self.proposals_db)
```

### Impact Measurement

```python
def measure_proposal_impact(proposal_id: str, days_after: int = 14) -> dict:
    """
    Measure impact of implemented proposal.

    Compare metrics before/after implementation:
    - Error rate for affected skill
    - Related incident rate
    - Learning entries on same topic
    - User satisfaction (if available)
    """
    proposal = load_proposal(proposal_id)
    impl_date = datetime.fromisoformat(proposal['implementation']['deployed_at'])

    # Define measurement window
    before_start = impl_date - timedelta(days=days_after)
    before_end = impl_date
    after_start = impl_date
    after_end = impl_date + timedelta(days=days_after)

    # Measure metrics
    metrics = {}

    # 1. Skill error rate
    skill_name = proposal['skill_name']
    metrics['error_rate_before'] = calculate_error_rate(skill_name, before_start, before_end)
    metrics['error_rate_after'] = calculate_error_rate(skill_name, after_start, after_end)
    metrics['error_rate_delta'] = metrics['error_rate_after'] - metrics['error_rate_before']

    # 2. Incident rate (related to this skill/component)
    affected_components = proposal.get('affected_components', [])
    metrics['incident_rate_before'] = calculate_incident_rate(affected_components, before_start, before_end)
    metrics['incident_rate_after'] = calculate_incident_rate(affected_components, after_start, after_end)
    metrics['incident_rate_delta'] = metrics['incident_rate_after'] - metrics['incident_rate_before']

    # 3. New learnings on same topic
    related_tags = extract_tags_from_evidence(proposal['evidence_learnings'])
    metrics['new_learnings_before'] = count_learnings_by_tags(related_tags, before_start, before_end)
    metrics['new_learnings_after'] = count_learnings_by_tags(related_tags, after_start, after_end)
    metrics['new_learnings_delta'] = metrics['new_learnings_after'] - metrics['new_learnings_before']

    return metrics
```

---

## Examples

### Example 1: Recurring Error Pattern

**Scenario**: 3 learning entries about AsyncIO event loop conflicts in test generation

**Mining Process**:
```python
# 1. Query for async-related learnings
async_learnings = find_learnings_by_tag('async')
# Result: LEARN-2025-039, LEARN-2025-042, LEARN-2025-046

# 2. Aggregate and analyze
pattern = {
    'type': 'recurring_error',
    'name': 'AsyncIO event loop conflict',
    'frequency': 3,
    'learnings': ['LEARN-2025-039', 'LEARN-2025-042', 'LEARN-2025-046'],
    'affected_skill': 'test-writer'
}

# 3. Calculate priority score
# - Severity: warning (20 points)
# - Recency: 5, 12, 18 days ago (avg 11.7 days) → 22 points
# - Frequency: 3 occurrences → 12 points
# - Unimplemented: all implemented → 0 bonus
# Total: 54 points (P3 Medium Priority)

# 4. Generate proposal
proposal = SkillUpdateProposal(
    skill_name='test-writer',
    change_type='enhancement',
    priority=3,
    effort='low',
    impact='medium',
    rationale="Add AsyncIO handling guidance to prevent event loop conflicts when generating async tests",
    evidence_learnings=pattern['learnings'],
    proposed_diff="""
+ ## AsyncIO Test Patterns
+
+ When generating tests for async functions, ensure:
+
+ 1. **Use pytest-asyncio**: Mark tests with `@pytest.mark.asyncio`
+ 2. **Avoid nested event loops**: Don't call `asyncio.run()` inside test
+ 3. **Fixture scoping**: Use `scope="function"` for async fixtures
+
+ **Example**:
+ ```python
+ import pytest
+
+ @pytest.mark.asyncio
+ async def test_async_function():
+     result = await my_async_function()
+     assert result == expected
+ ```
"""
)

# 5. Auto-approve (low effort, medium impact, clear evidence)
approve_proposal(proposal)  # Returns True

# 6. Implement
implement_skill_update(proposal)

# 7. Track impact (14 days later)
impact = measure_proposal_impact(proposal.id, days_after=14)
# Result: Error rate decreased from 7.1% to 0%, 0 new related learnings
```

### Example 2: Knowledge Gap (New Skill Creation)

**Scenario**: 8 learning entries related to API versioning and breaking changes

**Mining Process**:
```python
# 1. Query for API-related learnings
api_learnings = find_learnings_by_component('api')
# Result: 12 learnings total

# Filter for versioning/breaking change theme
versioning_learnings = [
    l for l in api_learnings
    if 'versioning' in l['tags'] or 'breaking_change' in l['tags']
]
# Result: 8 learnings (LEARN-2025-031 through LEARN-2025-044)

# 2. Identify knowledge gap
existing_skills = load_all_skills()
# No dedicated skill for API versioning

# 3. Pattern extraction
pattern = {
    'type': 'knowledge_gap',
    'name': 'API Versioning',
    'frequency': 8,
    'learnings': [l['id'] for l in versioning_learnings]
}

# 4. Priority score
# - Severity: mix (1 critical, 4 warning, 3 info) → avg 20 points
# - Recency: recent cluster (last 30 days) → 25 points
# - Frequency: 8 occurrences → 20 points (maxed)
# - Unimplemented: 5 not implemented → 10 bonus
# - Impact: Multiple API routes affected → 1.5x multiplier
# Total: (20+25+20+10) * 1.5 = 112.5 → capped at 100 (P1 Critical)

# 5. Generate new skill proposal
proposal = SkillUpdateProposal(
    skill_name='api-versioning',
    change_type='new_skill',
    priority=1,
    effort='high',
    impact='high',
    rationale="Create dedicated skill for API versioning to prevent breaking changes (8 related learnings, including 1 critical incident)",
    evidence_learnings=[l['id'] for l in versioning_learnings],
    proposed_diff="""
# Create new file: .claude/skills/api-versioning.md

---
name: api-versioning
description: API versioning and backwards compatibility expertise
version: 1.0.0
tags: [api, versioning, breaking_changes, backwards_compatibility]
---

## Purpose
Ensure API changes maintain backwards compatibility and follow proper versioning practices.

## When to Use
- Adding new API endpoints
- Modifying existing endpoint schemas
- Deprecating API features
- Planning API v2, v3, etc.

## Workflow
[... full skill definition ...]
"""
)

# 6. Require human review (new skill creation = high effort)
approve_proposal(proposal)  # Returns False, status = "needs_review"

# Human approves after review
manual_approve(proposal.id)

# 7. Implement new skill
create_new_skill(proposal)

# 8. Measure impact (30 days later, longer window for new skill)
impact = measure_proposal_impact(proposal.id, days_after=30)
# Result: 0 new API breaking changes, developer confidence increased
```

### Example 3: Component Hotspot

**Scenario**: Scheduling engine has 12 learnings in the last 2 months

**Mining Process**:
```python
# 1. Identify hotspots
hotspots = identify_component_hotspots(min_count=5)
# Result: [
#   {'component': 'scheduler', 'total': 12, 'critical': 3, 'warning': 6, 'info': 3},
#   {'component': 'validator', 'total': 7, 'critical': 2, 'warning': 4, 'info': 1},
#   ...
# ]

# 2. Analyze scheduler hotspot
scheduler_learnings = find_learnings_by_component('scheduler')

# Group by sub-theme
themes = extract_recurring_themes_from_learnings(scheduler_learnings)
# Result: [
#   {'theme': 'calendar_edge_cases', 'frequency': 5},
#   {'theme': 'performance', 'frequency': 4},
#   {'theme': 'timezone_handling', 'frequency': 3}
# ]

# 3. Prioritize sub-themes
top_theme = themes[0]  # calendar_edge_cases

# 4. Generate targeted proposal
proposal = SkillUpdateProposal(
    skill_name='acgme-compliance',  # Affected skill
    change_type='enhancement',
    priority=2,
    effort='medium',
    impact='high',
    rationale=f"Scheduler component has 12 learnings (3 critical), with 5 related to {top_theme['theme']}",
    evidence_learnings=[...],  # Top 5 calendar edge case learnings
    proposed_diff="""
+ ## Calendar Edge Case Checklist
+
+ Before validating schedules, verify handling of:
+ - [ ] Month boundaries (e.g., Dec 31 → Jan 1)
+ - [ ] Year boundaries (e.g., Dec 31 → Jan 1 New Year)
+ - [ ] Leap years (Feb 29)
+ - [ ] Daylight Saving Time transitions
+ - [ ] Holiday weekends (Friday → Monday spans)
+
+ **Test Template**:
+ ```python
+ @pytest.mark.parametrize("start,end,expected", [
+     ("2024-02-28", "2024-03-01", ...),  # Leap year
+     ("2024-12-31", "2025-01-02", ...),  # Year boundary
+ ])
+ def test_calendar_edge_case(start, end, expected):
+     ...
+ ```
"""
)

# 5. Auto-approve and implement
approve_proposal(proposal)
implement_skill_update(proposal)
```

---

## META_UPDATER Usage

### Weekly Mining Workflow

```bash
# Automated weekly run (every Monday 9 AM)
# Triggered by cron or CI/CD

#!/bin/bash
# .claude/scripts/weekly_mining.sh

set -e

echo "=== META_UPDATER Weekly Learning Mining ==="
echo "Week of: $(date +%Y-%m-%d)"

# 1. Scan for new learnings
echo "[1/6] Scanning for new learning entries..."
NEW_COUNT=$(find .claude/History -name "LEARN-*.md" -mtime -7 | wc -l)
echo "Found $NEW_COUNT new learning entries"

# 2. Run aggregation
echo "[2/6] Aggregating learnings..."
python .claude/scripts/aggregate_learnings.py --output .claude/Telemetry/learning_summary.json

# 3. Extract patterns
echo "[3/6] Extracting patterns..."
python .claude/scripts/extract_patterns.py --input .claude/Telemetry/learning_summary.json --output .claude/Telemetry/patterns.json

# 4. Generate proposals
echo "[4/6] Generating skill update proposals..."
python .claude/scripts/generate_proposals.py --patterns .claude/Telemetry/patterns.json --output .claude/Telemetry/proposals.json

# 5. Auto-approve eligible proposals
echo "[5/6] Reviewing proposals..."
python .claude/scripts/approve_proposals.py --proposals .claude/Telemetry/proposals.json

# 6. Generate dashboard
echo "[6/6] Generating weekly dashboard..."
python .claude/scripts/generate_dashboard.py --output ".claude/Telemetry/dashboards/weekly-$(date +%Y-%m-%d).md"

echo "=== Mining complete. Review proposals at .claude/Telemetry/proposals.json ==="
```

### On-Demand Mining (After Incident)

```python
# Triggered by critical incident

# 1. Load incident details
incident_id = "INC-2025-12-026"
incident = load_incident(incident_id)

# 2. Find related learnings
related_learnings = []
for learning_id in incident['learning_entries']:
    related_learnings.append(load_learning_by_id(learning_id))

# 3. Immediate pattern analysis
patterns = extract_patterns(related_learnings)

# 4. Generate high-priority proposals
for pattern in patterns:
    if pattern['type'] in ['recurring_error', 'missing_guardrail']:
        proposal = generate_emergency_proposal(pattern, priority=1)

        # Auto-approve for critical incidents
        proposal.status = 'approved'

        # Implement immediately
        implement_skill_update(proposal)

        # Notify team
        notify_slack(f"Emergency skill update deployed: {proposal.skill_name}")
```

---

## Best Practices

### DO

- ✅ **Run mining weekly**: Consistent cadence prevents backlog buildup
- ✅ **Prioritize by data**: Use scoring algorithm, not gut feel
- ✅ **Start small**: Implement low-effort, high-impact changes first
- ✅ **Measure impact**: Always track before/after metrics
- ✅ **Cross-reference**: Link proposals to evidence learnings
- ✅ **Automate approval**: Use clear criteria for auto-approval

### DON'T

- ❌ **Don't ignore low-priority learnings**: Backlog review monthly
- ❌ **Don't implement without evidence**: Minimum 2-3 related learnings
- ❌ **Don't skip impact measurement**: How do you know it worked?
- ❌ **Don't create overlapping skills**: Check for existing coverage first
- ❌ **Don't update skills in isolation**: Coordinate related changes

---

## Troubleshooting

### Problem: Too many proposals generated

**Solution**: Increase min_frequency threshold, adjust priority scoring

```python
# Increase thresholds
patterns = extract_patterns(learnings, min_frequency=5)  # Up from 3
proposals = [p for p in proposals if p['priority'] <= 3]  # Only P1-P3
```

### Problem: Proposals not getting implemented

**Solution**: Review backlog, adjust approval criteria, involve human reviewers

```python
# Analyze proposal backlog
backlog = [p for p in proposals if p['status'] == 'proposed']
print(f"{len(backlog)} proposals in backlog")

# Identify blockers
for proposal in backlog:
    if (datetime.now() - proposal['created_at']).days > 30:
        print(f"Stale proposal: {proposal['skill_name']} (effort={proposal['effort']})")
```

### Problem: Impact metrics don't show improvement

**Possible causes**:
1. **Measurement window too short**: Wait longer (30+ days)
2. **Wrong metrics tracked**: Review what's being measured
3. **Proposal didn't address root cause**: Investigate further learnings

---

**Remember**: Learning mining is not just data analysis—it's the feedback loop that makes the AI infrastructure self-improving. Every pattern extracted, every proposal implemented, every metric measured strengthens the system.
