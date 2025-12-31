# Enhanced Swap System v2.0

Comprehensive swap management system for medical residency scheduling with advanced matching, validation, and analytics.

## Overview

The enhanced swap system provides a complete solution for managing schedule swaps between faculty members, including:

- **Advanced Matching**: Multiple matching algorithms (exact, fuzzy, graph-based)
- **Chain Swaps**: Multi-party swap coordination
- **ACGME Compliance**: Automated compliance checking
- **Coverage Validation**: Ensures adequate staffing levels
- **Skill Validation**: Credential and qualification verification
- **Smart Notifications**: Multi-channel notification system
- **Analytics & Trends**: Comprehensive metrics and trend analysis

## Architecture

```
swap/
├── swap_engine.py              # Core orchestration engine
├── compatibility_checker.py    # Compatibility analysis
├── chain_swap.py              # Multi-party chain swaps
│
├── matching/                   # Matching algorithms
│   ├── exact_matcher.py       # Perfect mutual matches
│   ├── graph_matcher.py       # Graph-based optimization
│   └── preference_scorer.py   # Preference-based scoring
│
├── validation/                 # Validation subsystem
│   ├── pre_swap_validator.py  # Pre-execution validation
│   ├── compliance_checker.py  # ACGME compliance
│   ├── coverage_validator.py  # Coverage requirements
│   └── skill_validator.py     # Credential validation
│
├── notifications/              # Notification subsystem
│   ├── swap_notifier.py       # Notification orchestrator
│   └── email_templates.py     # Email templates
│
└── analytics/                  # Analytics subsystem
    ├── swap_metrics.py        # Metrics collection
    └── trend_analyzer.py      # Trend analysis
```

## Core Components

### SwapEngine

The central orchestrator for all swap operations.

```python
from app.services.swap import SwapEngine

engine = SwapEngine(db)

# Create swap request
result = await engine.create_swap_request(
    source_faculty_id=faculty_a_id,
    source_week=date(2025, 5, 1),
    target_faculty_id=faculty_b_id,
    target_week=date(2025, 5, 8),
    swap_type=SwapType.ONE_TO_ONE,
    reason="Conference attendance",
    auto_match=True,
)

# Execute swap
result = await engine.execute_swap(
    swap_id=swap_id,
    executed_by_id=user_id,
)

# Rollback if needed
result = await engine.rollback_swap(
    swap_id=swap_id,
    reason="Error in schedule",
)
```

### Matching Algorithms

#### Exact Matcher

Finds perfect mutual matches where two faculty want exactly what each other has.

```python
from app.services.swap.matching import ExactMatcher

matcher = ExactMatcher(db)
matches = await matcher.find_exact_matches()

for match in matches:
    print(f"Perfect match: {match.faculty_a_id} <-> {match.faculty_b_id}")
```

#### Graph Matcher

Uses graph theory to find optimal swap assignments.

```python
from app.services.swap.matching import GraphMatcher

matcher = GraphMatcher(db)
result = await matcher.find_optimal_matching()

print(f"Matched {len(result.matched_pairs)} pairs")
print(f"Total weight: {result.total_weight}")
```

#### Preference Scorer

Scores matches based on faculty preferences and historical data.

```python
from app.services.swap.matching import PreferenceScorer

scorer = PreferenceScorer(db)
score = await scorer.score_match(request_a, request_b)

print(f"Compatibility: {score.overall_score:.1%}")
print(f"Preference match: {score.preference_match:.1%}")
```

### Chain Swaps

Coordinates multi-party circular or linear swap chains.

```python
from app.services.swap import ChainSwapCoordinator

coordinator = ChainSwapCoordinator(db)

# Discover swap chains
result = await coordinator.discover_chains(max_chain_length=5)

print(f"Found {len(result.chains_found)} chains")

for chain in result.chains_found:
    print(f"Chain: {len(chain.nodes)} participants")

    # Execute the chain
    if chain.is_valid:
        exec_result = await coordinator.execute_chain(chain)
```

### Validation

#### Pre-Swap Validator

Comprehensive pre-execution validation.

```python
from app.services.swap.validation import PreSwapValidator

validator = PreSwapValidator(db)
result = await validator.validate(swap)

if result.valid:
    print("Swap is valid")
else:
    print(f"Errors: {result.errors}")
    print(f"Warnings: {result.warnings}")
```

#### ACGME Compliance Checker

Ensures swaps maintain ACGME compliance.

```python
from app.services.swap.validation import ACGMEComplianceChecker

checker = ACGMEComplianceChecker(db)
result = await checker.check_compliance(swap)

if result.compliant:
    print("ACGME compliant")
else:
    print(f"Violations: {result.violations}")
```

#### Coverage Validator

Verifies adequate coverage after swap.

```python
from app.services.swap.validation import CoverageValidator

validator = CoverageValidator(db)
result = await validator.validate_coverage(swap)

if not result.adequate:
    print(f"Coverage gaps: {result.gaps}")
```

#### Skill Validator

Checks credential and qualification requirements.

```python
from app.services.swap.validation import SkillValidator

validator = SkillValidator(db)
result = await validator.validate_skills(swap)

if not result.qualified:
    print(f"Missing credentials: {result.missing_credentials}")
```

### Notifications

Multi-channel notification system with customizable templates.

```python
from app.services.swap.notifications import SwapNotifier

notifier = SwapNotifier(db)

# Notify on creation
await notifier.notify_swap_created(swap)

# Notify on execution
await notifier.notify_swap_executed(swap)

# Notify on match found
await notifier.notify_swap_match_found(
    swap,
    match_id,
    compatibility_score=0.95,
)
```

### Analytics

Comprehensive metrics and trend analysis.

```python
from app.services.swap.analytics import SwapMetricsCollector, SwapTrendAnalyzer

# Collect metrics
collector = SwapMetricsCollector(db)
metrics = await collector.collect_metrics(
    start_date=date(2025, 1, 1),
    end_date=date(2025, 3, 31),
)

print(f"Success rate: {metrics.success_rate:.1%}")
print(f"Average time to execution: {metrics.average_time_to_execution_days:.1f} days")

# Analyze trends
analyzer = SwapTrendAnalyzer(db)
trends = await analyzer.analyze_trends(days=90)

print(f"Trend: {trends.trend_direction}")
print(f"Change: {trends.change_percentage:+.1f}%")
print(f"Recommendations: {trends.recommendations}")
```

## Compatibility Checking

Advanced compatibility analysis with multiple scoring factors.

```python
from app.services.swap import CompatibilityChecker

checker = CompatibilityChecker(db, min_compatibility_score=0.6)

result = await checker.check_compatibility(request_a, request_b)

if result.compatible:
    score = result.score
    print(f"Overall: {score.overall_score:.1%}")
    print(f"Schedule: {score.schedule_compatibility:.1%}")
    print(f"Preference: {score.preference_alignment:.1%}")
    print(f"Workload: {score.workload_balance:.1%}")
```

## Integration with Existing System

The enhanced swap system integrates seamlessly with existing components:

```python
from app.services.swap import SwapEngine
from app.services.swap.validation import (
    PreSwapValidator,
    ACGMEComplianceChecker,
    CoverageValidator,
    SkillValidator,
)
from app.services.swap.matching import ExactMatcher, GraphMatcher
from app.services.swap.notifications import SwapNotifier

# Initialize engine
engine = SwapEngine(db)

# Register validators
engine.register_validator(PreSwapValidator(db))
engine.register_validator(ACGMEComplianceChecker(db))
engine.register_validator(CoverageValidator(db))
engine.register_validator(SkillValidator(db))

# Register matchers
engine.register_matcher(ExactMatcher(db))
engine.register_matcher(GraphMatcher(db))

# Register notifiers
engine.register_notifier(SwapNotifier(db))

# Now ready to use
result = await engine.create_swap_request(...)
```

## Testing

Comprehensive test suite included:

```bash
# Run all swap tests
pytest tests/services/swap/

# Run specific test file
pytest tests/services/swap/test_swap_engine.py

# Run with coverage
pytest tests/services/swap/ --cov=app.services.swap
```

## Performance Considerations

- **Async throughout**: All operations are async for optimal performance
- **Eager loading**: Uses SQLAlchemy selectinload to prevent N+1 queries
- **Batch operations**: Supports batch matching and validation
- **Caching**: Results can be cached for frequently accessed data

## Security

- **ACGME compliance enforced**: All swaps validated against regulations
- **Audit trail**: All operations logged
- **Role-based access**: Integration with existing auth system
- **Data validation**: Pydantic schemas for all inputs

## Military Context

Special considerations for military medical residency:

- **TDY/Deployment handling**: Integrated validation for military duties
- **OPSEC compliance**: No sensitive data in logs or error messages
- **Credential validation**: Military-specific certifications checked

## Future Enhancements

Planned features:

- [ ] Machine learning-based matching optimization
- [ ] Predictive analytics for swap volume
- [ ] Mobile notifications
- [ ] Integration with external calendar systems
- [ ] Automated conflict resolution
- [ ] Smart scheduling suggestions

## Version History

### v2.0.0 (2025-01-01)
- Complete system redesign
- Advanced matching algorithms
- Chain swap support
- Comprehensive validation
- Analytics and trends

### v1.0.0 (2024-06-01)
- Initial swap system
- Basic matching
- Simple validation

## Support

For issues or questions:
- See main project documentation
- Check test files for usage examples
- Review code comments for implementation details

## License

Part of the Residency Scheduler system.
