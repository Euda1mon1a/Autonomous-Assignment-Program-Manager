# Enhanced Swap Auto-Matcher Usage Guide

## Overview

The `SwapAutoMatcher` service provides intelligent auto-matching for FMIT swap requests using multiple scoring factors. It helps identify the best swap matches based on preferences, availability, history, and workload balance.

## Quick Start

```python
from sqlalchemy.orm import Session
from app.services.swap_auto_matcher import SwapAutoMatcher
from app.schemas.swap_matching import MatchingCriteria

# Initialize with default criteria
matcher = SwapAutoMatcher(db=session)

# Or with custom criteria
custom_criteria = MatchingCriteria(
    preference_alignment_weight=0.40,
    date_proximity_weight=0.25,
    minimum_score_threshold=0.5,
    max_matches_per_request=10
)
matcher = SwapAutoMatcher(db=session, criteria=custom_criteria)
```

## Core Methods

### 1. Find Compatible Swaps

Find all compatible swap matches for a specific request:

```python
from uuid import UUID

request_id = UUID("...")
compatible_matches = matcher.find_compatible_swaps(request_id)

for match in compatible_matches:
    print(f"Match: {match.faculty_a_name} <-> {match.faculty_b_name}")
    print(f"Weeks: {match.week_a} <-> {match.week_b}")
    print(f"Mutual: {match.is_mutual}")
```

### 2. Score Swap Compatibility

Calculate a detailed compatibility score between two requests:

```python
from app.models.swap import SwapRecord

request_a = db.query(SwapRecord).filter(...).first()
request_b = db.query(SwapRecord).filter(...).first()

score = matcher.score_swap_compatibility(request_a, request_b)
print(f"Compatibility Score: {score:.2f}")  # 0.0 to 1.0
```

### 3. Suggest Optimal Matches

Get ranked matches with detailed explanations:

```python
# Get top 5 matches
ranked_matches = matcher.suggest_optimal_matches(request_id, top_k=5)

for ranked_match in ranked_matches:
    print(f"\nMatch Score: {ranked_match.compatibility_score:.2f}")
    print(f"Priority: {ranked_match.priority.value}")
    print(f"Explanation: {ranked_match.explanation}")
    print(f"Acceptance Probability: {ranked_match.estimated_acceptance_probability:.0%}")
    print(f"Recommended Action: {ranked_match.recommended_action}")

    # Detailed scoring breakdown
    breakdown = ranked_match.scoring_breakdown
    print(f"  - Date Proximity: {breakdown.date_proximity_score:.2f}")
    print(f"  - Preference Alignment: {breakdown.preference_alignment_score:.2f}")
    print(f"  - Workload Balance: {breakdown.workload_balance_score:.2f}")
    print(f"  - History: {breakdown.history_score:.2f}")
    print(f"  - Availability: {breakdown.availability_score:.2f}")

    # Check warnings
    if ranked_match.warnings:
        print("  Warnings:")
        for warning in ranked_match.warnings:
            print(f"    - {warning}")
```

### 4. Auto-Match Pending Requests

Process all pending swap requests at once:

```python
# Run batch auto-matching
result = matcher.auto_match_pending_requests()

print(f"Processed: {result.total_requests_processed} requests")
print(f"Found: {result.total_matches_found} total matches")
print(f"Execution Time: {result.execution_time_seconds:.2f}s")

# Review high-priority matches
print(f"\nHigh Priority Matches: {len(result.high_priority_matches)}")
for auto_match in result.high_priority_matches:
    print(f"  Request {auto_match.request_id}")
    print(f"    Best Match Score: {auto_match.best_match.compatibility_score:.2f}")
    print(f"    Priority: {auto_match.best_match.priority.value}")

# Review successful matches
for auto_match in result.successful_matches:
    print(f"\nRequest: {auto_match.request_id}")
    print(f"  Faculty: {auto_match.faculty_id}")
    print(f"  Source Week: {auto_match.source_week}")
    print(f"  Matches Found: {auto_match.matches_found}")
    if auto_match.best_match:
        print(f"  Best Match: {auto_match.best_match.match.faculty_b_name}")

# Review requests with no matches
if result.no_matches:
    print(f"\nRequests with no matches: {len(result.no_matches)}")
```

### 5. Proactive Swap Suggestions

Suggest beneficial swaps for a faculty member even without an active request:

```python
faculty_id = UUID("...")
suggestions = matcher.suggest_proactive_swaps(faculty_id, limit=5)

for suggestion in suggestions:
    print(f"\nSuggestion for {suggestion.faculty_name}:")
    print(f"  Current Week: {suggestion.current_week}")
    print(f"  Swap with: {suggestion.suggested_partner_name}")
    print(f"  Get Week: {suggestion.partner_week}")
    print(f"  Benefit Score: {suggestion.benefit_score:.2f}")
    print(f"  Reason: {suggestion.reason}")
    print(f"  Action: {suggestion.action_text}")
```

## Scoring Factors

The compatibility score (0.0 to 1.0) is calculated using these factors:

### 1. Date Proximity (Default Weight: 20%)
- **1.0**: Dates within 2 weeks
- **0.5-1.0**: Dates within max separation
- **0.0**: Dates too far apart

### 2. Preference Alignment (Default Weight: 35%)
- **1.0**: Perfect mutual preference match
- **0.8**: Both prefer each other's weeks (from preference lists)
- **0.6**: One-way match with target week alignment
- **0.4**: One party prefers the week
- **0.2**: Available but not preferred

### 3. Workload Balance (Default Weight: 15%)
- Considers how close each faculty is to their target workload
- Higher score when swap helps both parties balance workload
- Based on current assignments vs target weeks per year

### 4. Past Swap History (Default Weight: 15%)
- **Penalties**: Previous rejections between parties (up to -0.6)
- **Bonuses**: Previous successful swaps (up to +0.3)
- **Base**: Overall acceptance rates of both parties

### 5. Faculty Availability (Default Weight: 15%)
- **1.0**: Both available and prefer the weeks
- **0.5**: One prefers, one is available
- **0.0**: One or both have blocked weeks

### Blocking Penalty
- **1.0**: No blocked weeks (no penalty)
- **0.0**: One or both weeks are blocked (complete penalty)

## Customizing Matching Criteria

```python
criteria = MatchingCriteria(
    # Adjust scoring weights (must sum close to 1.0)
    date_proximity_weight=0.25,        # Emphasize date closeness
    preference_alignment_weight=0.40,   # Most important factor
    workload_balance_weight=0.15,
    history_weight=0.10,
    availability_weight=0.10,

    # Set thresholds
    minimum_score_threshold=0.5,       # Only show matches >= 0.5
    high_priority_threshold=0.80,      # High priority at >= 0.8

    # Configure constraints
    max_matches_per_request=10,        # Return up to 10 matches
    max_date_separation_days=60,       # Only match dates within 60 days
    require_mutual_availability=True,  # Both must be available
    exclude_blocked_weeks=True,        # Skip blocked weeks
    consider_past_rejections=True,     # Avoid past rejections

    # Historical analysis
    history_lookback_days=365,         # Look back 1 year
)

matcher = SwapAutoMatcher(db=session, criteria=criteria)
```

## Integration Examples

### API Endpoint Example

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.swap_auto_matcher import SwapAutoMatcher
from app.schemas.swap_matching import RankedMatch

router = APIRouter()

@router.get("/swaps/{request_id}/matches", response_model=list[RankedMatch])
def get_swap_matches(
    request_id: UUID,
    top_k: int = 5,
    db: Session = Depends(get_db)
):
    """Get optimal matches for a swap request."""
    matcher = SwapAutoMatcher(db)
    return matcher.suggest_optimal_matches(request_id, top_k)

@router.post("/swaps/auto-match-all")
def auto_match_all_pending(db: Session = Depends(get_db)):
    """Auto-match all pending swap requests."""
    matcher = SwapAutoMatcher(db)
    result = matcher.auto_match_pending_requests()
    return result
```

### Background Task Example

```python
from celery import Celery
from app.db.session import SessionLocal
from app.services.swap_auto_matcher import SwapAutoMatcher

app = Celery('tasks')

@app.task
def run_daily_auto_matching():
    """Run auto-matching as a daily background task."""
    db = SessionLocal()
    try:
        matcher = SwapAutoMatcher(db)
        result = matcher.auto_match_pending_requests()

        # Notify high-priority matches
        for auto_match in result.high_priority_matches:
            notify_faculty_of_match(auto_match)

        return {
            "status": "success",
            "matches_found": result.total_matches_found,
            "high_priority": len(result.high_priority_matches)
        }
    finally:
        db.close()
```

## Best Practices

1. **Use Default Criteria First**: Start with default matching criteria and adjust based on results
2. **Monitor High Priority**: Always check `high_priority_matches` for urgent situations
3. **Handle No Matches**: Provide feedback when `no_matches` list is not empty
4. **Check Warnings**: Review `warnings` in `RankedMatch` before notifying faculty
5. **Batch Processing**: Use `auto_match_pending_requests()` for scheduled jobs
6. **Proactive Suggestions**: Call `suggest_proactive_swaps()` when faculty view their schedule

## Performance Considerations

- **Batch Processing**: For many requests, use `auto_match_pending_requests()` instead of individual calls
- **Database Queries**: The matcher uses efficient queries but consider caching for high-traffic scenarios
- **Criteria Tuning**: Adjust `max_matches_per_request` and `max_date_separation_days` to balance thoroughness vs speed

## Future Enhancements

Potential improvements for future versions:
- Machine learning-based scoring
- Multi-way swaps (3+ parties)
- Temporal pattern recognition
- Integration with calendar systems
- Real-time notifications via WebSocket
