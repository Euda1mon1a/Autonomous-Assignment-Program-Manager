"""
What-If Scenario Analysis for Fatigue Impact.

This module enables program directors to test schedule changes before
committing them, showing predicted fatigue impact on residents.

Features:
1. Single assignment change impact analysis
2. Multi-assignment scenario comparison
3. Shift swap fatigue impact prediction
4. Optimization suggestions for fatigue reduction
5. Comparative visualization data export

Use Cases:
- "What if I move Dr. Smith's call from Monday to Wednesday?"
- "What's the fatigue impact of adding this night shift?"
- "Which of these three schedule options has lowest fatigue risk?"
- "Who can safely cover this emergency shift?"
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Any
from uuid import UUID, uuid4
from copy import deepcopy

from app.frms.three_process_model import (
    ThreeProcessModel,
    AlertnessState,
    EffectivenessScore,
)
from app.frms.performance_predictor import (
    PerformancePredictor,
    PerformanceDegradation,
    ScheduleFeatures,
)

logger = logging.getLogger(__name__)


@dataclass
class WhatIfScenario:
    """
    Definition of a what-if scenario to test.

    Represents a proposed change to the schedule for impact analysis.
    """

    scenario_id: str
    name: str
    description: str
    changes: list[dict]  # List of assignment changes
    created_at: datetime = field(default_factory=datetime.now)

    # Change types:
    # {"action": "add", "person_id": ..., "block_id": ..., "rotation_type": ...}
    # {"action": "remove", "assignment_id": ...}
    # {"action": "swap", "assignment1_id": ..., "assignment2_id": ...}
    # {"action": "move", "assignment_id": ..., "new_block_id": ...}

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "name": self.name,
            "description": self.description,
            "changes": self.changes,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class FatigueImpactReport:
    """
    Report of fatigue impact from a scenario.

    Compares baseline (current schedule) to proposed (after changes).
    """

    scenario_id: str
    scenario_name: str
    analysis_time: datetime

    # Baseline metrics (current schedule)
    baseline_metrics: dict[str, Any] = field(default_factory=dict)

    # Proposed metrics (after changes)
    proposed_metrics: dict[str, Any] = field(default_factory=dict)

    # Impact summary
    impact_summary: dict[str, Any] = field(default_factory=dict)

    # Per-person impact
    person_impacts: list[dict] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    # Holographic export data
    visualization_data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize to dictionary for API response."""
        return {
            "scenario_id": self.scenario_id,
            "scenario_name": self.scenario_name,
            "analysis_time": self.analysis_time.isoformat(),
            "baseline_metrics": self.baseline_metrics,
            "proposed_metrics": self.proposed_metrics,
            "impact_summary": self.impact_summary,
            "person_impacts": self.person_impacts,
            "recommendations": self.recommendations,
            "visualization_data": self.visualization_data,
        }


class ScenarioAnalyzer:
    """
    Analyzes what-if scenarios for fatigue impact.

    Compares current schedule against proposed changes to predict
    how fatigue metrics would change.

    Usage:
        analyzer = ScenarioAnalyzer()

        scenario = WhatIfScenario(
            scenario_id="test_1",
            name="Move Dr. Smith's call",
            description="Move Monday night call to Wednesday",
            changes=[
                {"action": "move", "assignment_id": "...", "new_block_id": "..."}
            ]
        )

        report = analyzer.analyze(
            baseline_assignments=current_schedule,
            scenario=scenario,
            persons=residents,
            blocks=blocks
        )

        print(report.impact_summary)
    """

    def __init__(self) -> None:
        """Initialize scenario analyzer."""
        self.model = ThreeProcessModel()
        self.predictor = PerformancePredictor()

    def analyze(
        self,
        baseline_assignments: list[dict],
        scenario: WhatIfScenario,
        persons: list[dict],
        blocks: list[dict],
        analysis_window_days: int = 14,
    ) -> FatigueImpactReport:
        """
        Analyze fatigue impact of a scenario.

        Args:
            baseline_assignments: Current schedule assignments
            scenario: Proposed changes to analyze
            persons: List of person dicts
            blocks: List of block dicts
            analysis_window_days: Days to analyze impact

        Returns:
            FatigueImpactReport with comparison metrics
        """
        analysis_time = datetime.now()

        # Calculate baseline metrics
        baseline_metrics = self._calculate_metrics(
            baseline_assignments, persons, blocks, analysis_window_days
        )

        # Apply scenario changes to get proposed assignments
        proposed_assignments = self._apply_changes(
            deepcopy(baseline_assignments), scenario.changes, blocks
        )

        # Calculate proposed metrics
        proposed_metrics = self._calculate_metrics(
            proposed_assignments, persons, blocks, analysis_window_days
        )

        # Calculate impact summary
        impact_summary = self._calculate_impact(baseline_metrics, proposed_metrics)

        # Calculate per-person impacts
        person_impacts = self._calculate_person_impacts(
            baseline_assignments, proposed_assignments, persons, blocks
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(impact_summary, person_impacts)

        # Generate visualization data
        visualization_data = self._generate_visualization_data(
            baseline_metrics, proposed_metrics, person_impacts
        )

        report = FatigueImpactReport(
            scenario_id=scenario.scenario_id,
            scenario_name=scenario.name,
            analysis_time=analysis_time,
            baseline_metrics=baseline_metrics,
            proposed_metrics=proposed_metrics,
            impact_summary=impact_summary,
            person_impacts=person_impacts,
            recommendations=recommendations,
            visualization_data=visualization_data,
        )

        logger.info(
            f"Scenario analysis complete: {scenario.name} - "
            f"Impact: {impact_summary.get('overall_change', 'N/A')}"
        )

        return report

    def compare_scenarios(
        self,
        baseline_assignments: list[dict],
        scenarios: list[WhatIfScenario],
        persons: list[dict],
        blocks: list[dict],
    ) -> list[FatigueImpactReport]:
        """
        Compare multiple scenarios to find optimal option.

        Args:
            baseline_assignments: Current schedule
            scenarios: List of scenarios to compare
            persons: List of person dicts
            blocks: List of block dicts

        Returns:
            List of reports, sorted by overall fatigue impact (best first)
        """
        reports = []
        for scenario in scenarios:
            report = self.analyze(baseline_assignments, scenario, persons, blocks)
            reports.append(report)

            # Sort by overall fatigue score (lower is better)
        reports.sort(
            key=lambda r: r.proposed_metrics.get("avg_fatigue_score", float("inf"))
        )

        return reports

    def find_best_coverage(
        self,
        baseline_assignments: list[dict],
        block_to_cover: dict,
        eligible_persons: list[dict],
        blocks: list[dict],
    ) -> list[dict]:
        """
        Find best person to cover an uncovered shift based on fatigue.

        Args:
            baseline_assignments: Current schedule
            block_to_cover: Block that needs coverage
            eligible_persons: Persons who could potentially cover
            blocks: List of all blocks

        Returns:
            List of persons ranked by fatigue impact (best first)
        """
        results = []

        for person in eligible_persons:
            # Create scenario for this person covering
            scenario = WhatIfScenario(
                scenario_id=f"cover_{person.get('id')}_{block_to_cover.get('id')}",
                name=f"{person.get('name')} covers {block_to_cover.get('date')}",
                description=f"Assign {person.get('name')} to cover shift",
                changes=[
                    {
                        "action": "add",
                        "person_id": person.get("id"),
                        "block_id": block_to_cover.get("id"),
                        "rotation_type": block_to_cover.get(
                            "rotation_type", "coverage"
                        ),
                    }
                ],
            )

            report = self.analyze(baseline_assignments, scenario, [person], blocks)

            results.append(
                {
                    "person_id": person.get("id"),
                    "person_name": person.get("name"),
                    "fatigue_impact": report.impact_summary.get("fatigue_change", 0),
                    "post_coverage_effectiveness": report.proposed_metrics.get(
                        "min_effectiveness", 100
                    ),
                    "risk_level": report.proposed_metrics.get(
                        "highest_risk_level", "low"
                    ),
                    "recommendation": (
                        "SAFE"
                        if report.proposed_metrics.get("min_effectiveness", 100) >= 77
                        else "CAUTION"
                        if report.proposed_metrics.get("min_effectiveness", 100) >= 70
                        else "NOT RECOMMENDED"
                    ),
                }
            )

            # Sort by fatigue impact (lowest impact first)
        results.sort(key=lambda r: r["fatigue_impact"])

        return results

    def _calculate_metrics(
        self,
        assignments: list[dict],
        persons: list[dict],
        blocks: list[dict],
        window_days: int,
    ) -> dict:
        """Calculate comprehensive fatigue metrics for a schedule."""
        metrics = {
            "total_assignments": len(assignments),
            "persons_analyzed": len(persons),
            "analysis_window_days": window_days,
        }

        # Per-person analysis
        person_scores = {}
        all_effectiveness = []

        for person in persons:
            person_id = person.get("id")
            person_assignments = [
                a for a in assignments if a.get("person_id") == person_id
            ]

            # Create alertness state
            state = self.model.create_state(
                person_id=UUID(person_id) if isinstance(person_id, str) else person_id,
                timestamp=datetime.now(),
            )

            # Simulate through assignments
            for assignment in sorted(
                person_assignments, key=lambda a: a.get("date", date.min)
            ):
                # Update state for this assignment
                state = self.model.update_wakefulness(state, 6.0)  # 6 hour block
                all_effectiveness.append(
                    state.effectiveness.overall if state.effectiveness else 100
                )

                # Extract features for predictor
            features = self.predictor.extract_features(
                person_assignments, datetime.now()
            )
            prediction = self.predictor.predict(
                features,
                UUID(person_id) if isinstance(person_id, str) else person_id,
            )

            person_scores[person_id] = {
                "final_effectiveness": state.effectiveness.overall
                if state.effectiveness
                else 100,
                "degradation_probability": prediction.degradation_probability,
                "risk_level": prediction.clinical_risk.value,
                "assignments": len(person_assignments),
            }

        metrics["person_scores"] = person_scores

        # Aggregate metrics
        if all_effectiveness:
            metrics["avg_effectiveness"] = sum(all_effectiveness) / len(
                all_effectiveness
            )
            metrics["min_effectiveness"] = min(all_effectiveness)
            metrics["max_effectiveness"] = max(all_effectiveness)
        else:
            metrics["avg_effectiveness"] = 100
            metrics["min_effectiveness"] = 100
            metrics["max_effectiveness"] = 100

            # Calculate overall fatigue score (inverse of effectiveness)
        metrics["avg_fatigue_score"] = 100 - metrics["avg_effectiveness"]

        # Risk distribution
        risk_counts = {"low": 0, "moderate": 0, "high": 0, "severe": 0}
        for person_id, scores in person_scores.items():
            risk = scores.get("risk_level", "low")
            if risk in risk_counts:
                risk_counts[risk] += 1
            elif "high" in risk or "severe" in risk:
                risk_counts["high"] += 1
            else:
                risk_counts["moderate"] += 1

        metrics["risk_distribution"] = risk_counts
        metrics["highest_risk_level"] = (
            "severe"
            if risk_counts["severe"] > 0
            else "high"
            if risk_counts["high"] > 0
            else "moderate"
            if risk_counts["moderate"] > 0
            else "low"
        )

        return metrics

    def _apply_changes(
        self,
        assignments: list[dict],
        changes: list[dict],
        blocks: list[dict],
    ) -> list[dict]:
        """Apply scenario changes to assignments."""
        result = list(assignments)

        for change in changes:
            action = change.get("action")

            if action == "add":
                # Add new assignment
                new_assignment = {
                    "id": str(uuid4()),
                    "person_id": change.get("person_id"),
                    "block_id": change.get("block_id"),
                    "rotation_type": change.get("rotation_type", "general"),
                    "date": self._get_block_date(blocks, change.get("block_id")),
                }
                result.append(new_assignment)

            elif action == "remove":
                # Remove assignment by ID
                assignment_id = change.get("assignment_id")
                result = [a for a in result if a.get("id") != assignment_id]

            elif action == "move":
                # Move assignment to different block
                assignment_id = change.get("assignment_id")
                new_block_id = change.get("new_block_id")
                for a in result:
                    if a.get("id") == assignment_id:
                        a["block_id"] = new_block_id
                        a["date"] = self._get_block_date(blocks, new_block_id)
                        break

            elif action == "swap":
                # Swap two assignments
                id1 = change.get("assignment1_id")
                id2 = change.get("assignment2_id")
                a1 = next((a for a in result if a.get("id") == id1), None)
                a2 = next((a for a in result if a.get("id") == id2), None)
                if a1 and a2:
                    # Swap person_ids
                    a1["person_id"], a2["person_id"] = a2["person_id"], a1["person_id"]

        return result

    def _get_block_date(self, blocks: list[dict], block_id: str) -> date | None:
        """Get date for a block by ID."""
        for block in blocks:
            if block.get("id") == block_id:
                d = block.get("date")
                if isinstance(d, date):
                    return d
                if isinstance(d, str):
                    return date.fromisoformat(d)
        return None

    def _calculate_impact(
        self,
        baseline: dict,
        proposed: dict,
    ) -> dict:
        """Calculate impact summary comparing baseline to proposed."""
        return {
            "fatigue_change": (
                proposed.get("avg_fatigue_score", 0)
                - baseline.get("avg_fatigue_score", 0)
            ),
            "effectiveness_change": (
                proposed.get("avg_effectiveness", 100)
                - baseline.get("avg_effectiveness", 100)
            ),
            "min_effectiveness_change": (
                proposed.get("min_effectiveness", 100)
                - baseline.get("min_effectiveness", 100)
            ),
            "overall_change": (
                "IMPROVEMENT"
                if proposed.get("avg_fatigue_score", 0)
                < baseline.get("avg_fatigue_score", 0)
                else "NO_CHANGE"
                if proposed.get("avg_fatigue_score", 0)
                == baseline.get("avg_fatigue_score", 0)
                else "DEGRADATION"
            ),
            "risk_level_change": (
                f"{baseline.get('highest_risk_level', 'low')} → {proposed.get('highest_risk_level', 'low')}"
            ),
            "persons_improved": 0,  # TODO: Calculate
            "persons_degraded": 0,  # TODO: Calculate
        }

    def _calculate_person_impacts(
        self,
        baseline_assignments: list[dict],
        proposed_assignments: list[dict],
        persons: list[dict],
        blocks: list[dict],
    ) -> list[dict]:
        """Calculate per-person fatigue impact."""
        impacts = []

        for person in persons:
            person_id = person.get("id")

            baseline_person = [
                a for a in baseline_assignments if a.get("person_id") == person_id
            ]
            proposed_person = [
                a for a in proposed_assignments if a.get("person_id") == person_id
            ]

            # Calculate change
            baseline_count = len(baseline_person)
            proposed_count = len(proposed_person)

            impacts.append(
                {
                    "person_id": person_id,
                    "person_name": person.get("name", "Unknown"),
                    "baseline_assignments": baseline_count,
                    "proposed_assignments": proposed_count,
                    "change": proposed_count - baseline_count,
                    "impact": "increased"
                    if proposed_count > baseline_count
                    else "decreased"
                    if proposed_count < baseline_count
                    else "unchanged",
                }
            )

        return impacts

    def _generate_recommendations(
        self,
        impact_summary: dict,
        person_impacts: list[dict],
    ) -> list[str]:
        """Generate recommendations based on impact analysis."""
        recommendations = []

        overall = impact_summary.get("overall_change", "NO_CHANGE")

        if overall == "IMPROVEMENT":
            recommendations.append("This scenario IMPROVES overall fatigue levels")
        elif overall == "DEGRADATION":
            recommendations.append("WARNING: This scenario INCREASES fatigue risk")

        fatigue_change = impact_summary.get("fatigue_change", 0)
        if fatigue_change > 5:
            recommendations.append(
                f"Fatigue score increases by {fatigue_change:.1f}% - consider alternatives"
            )
        elif fatigue_change < -5:
            recommendations.append(
                f"Fatigue score decreases by {abs(fatigue_change):.1f}% - positive impact"
            )

        min_eff_change = impact_summary.get("min_effectiveness_change", 0)
        if min_eff_change < -10:
            recommendations.append(
                "ALERT: Minimum effectiveness drops significantly - review individual impacts"
            )

        if not recommendations:
            recommendations.append("Scenario has minimal fatigue impact")

        return recommendations

    def _generate_visualization_data(
        self,
        baseline: dict,
        proposed: dict,
        person_impacts: list[dict],
    ) -> dict:
        """Generate data for holographic visualization."""
        return {
            "comparison_chart": {
                "baseline": {
                    "avg_effectiveness": baseline.get("avg_effectiveness", 100),
                    "min_effectiveness": baseline.get("min_effectiveness", 100),
                    "fatigue_score": baseline.get("avg_fatigue_score", 0),
                },
                "proposed": {
                    "avg_effectiveness": proposed.get("avg_effectiveness", 100),
                    "min_effectiveness": proposed.get("min_effectiveness", 100),
                    "fatigue_score": proposed.get("avg_fatigue_score", 0),
                },
            },
            "risk_distribution": {
                "baseline": baseline.get("risk_distribution", {}),
                "proposed": proposed.get("risk_distribution", {}),
            },
            "person_heatmap": [
                {
                    "person_id": p.get("person_id"),
                    "change_magnitude": abs(p.get("change", 0)),
                    "direction": p.get("impact"),
                }
                for p in person_impacts
            ],
        }
