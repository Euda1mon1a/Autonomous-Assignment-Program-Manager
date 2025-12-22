"""
Schedule Scorer - ML-based schedule quality evaluation.

Uses trained ML models to score and evaluate schedule quality,
suggest improvements, and optimize assignments.
"""
import logging
from pathlib import Path
from typing import Any, Optional

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.ml.models.conflict_predictor import ConflictPredictor
from app.ml.models.preference_predictor import PreferencePredictor
from app.ml.models.workload_optimizer import WorkloadOptimizer

logger = logging.getLogger(__name__)


class ScheduleScorer:
    """
    Scores schedule quality using ML models.

    Combines predictions from:
    - Preference predictor: How much people will like their assignments
    - Workload optimizer: How balanced the workload is
    - Conflict predictor: How likely conflicts are to occur

    Provides overall quality score and improvement suggestions.
    """

    def __init__(
        self,
        preference_model_path: Optional[Path] = None,
        workload_model_path: Optional[Path] = None,
        conflict_model_path: Optional[Path] = None,
        db: Optional[AsyncSession] = None,
    ):
        """
        Initialize schedule scorer.

        Args:
            preference_model_path: Path to trained preference predictor
            workload_model_path: Path to trained workload optimizer
            conflict_model_path: Path to trained conflict predictor
            db: Database session for fetching additional data
        """
        self.db = db

        # Initialize ML models
        self.preference_predictor = PreferencePredictor(model_path=preference_model_path)
        self.workload_optimizer = WorkloadOptimizer(model_path=workload_model_path)
        self.conflict_predictor = ConflictPredictor(model_path=conflict_model_path)

        logger.info("Initialized ScheduleScorer with ML models")

    def score_schedule(
        self,
        schedule: dict[str, Any],
        weights: Optional[dict[str, float]] = None,
    ) -> dict[str, Any]:
        """
        Score overall schedule quality.

        Args:
            schedule: Dictionary with:
                - assignments: List of assignment dictionaries
                - people: List of person dictionaries with their assignments
                - metadata: Schedule metadata
            weights: Custom weights for scoring components
                - preference_weight: Weight for preference scores (default 0.4)
                - workload_weight: Weight for workload balance (default 0.3)
                - conflict_weight: Weight for conflict avoidance (default 0.3)

        Returns:
            Dictionary with overall score and component scores
        """
        # Default weights
        if weights is None:
            weights = {
                "preference_weight": 0.4,
                "workload_weight": 0.3,
                "conflict_weight": 0.3,
            }

        logger.info("Scoring schedule quality...")

        # Score components
        preference_score = self._score_preferences(schedule)
        workload_score = self._score_workload_balance(schedule)
        conflict_score = self._score_conflict_risk(schedule)

        # Calculate weighted overall score
        overall_score = (
            preference_score["average_score"] * weights["preference_weight"]
            + workload_score["balance_score"] * weights["workload_weight"]
            + conflict_score["safety_score"] * weights["conflict_weight"]
        )

        return {
            "overall_score": float(overall_score),
            "grade": self._score_to_grade(overall_score),
            "components": {
                "preference": preference_score,
                "workload": workload_score,
                "conflict": conflict_score,
            },
            "weights": weights,
        }

    def _score_preferences(self, schedule: dict[str, Any]) -> dict[str, Any]:
        """
        Score assignment preferences.

        Args:
            schedule: Schedule dictionary

        Returns:
            Preference scoring details
        """
        assignments = schedule.get("assignments", [])
        if not assignments:
            return {
                "average_score": 0.0,
                "distribution": {},
                "low_preference_count": 0,
            }

        # Score each assignment
        scores = []
        for assignment in assignments:
            score = self.preference_predictor.predict(
                person_data=assignment.get("person", {}),
                rotation_data=assignment.get("rotation", {}),
                block_data=assignment.get("block", {}),
                historical_stats=assignment.get("historical_stats"),
            )
            scores.append(score)

        # Calculate statistics
        avg_score = float(np.mean(scores))
        min_score = float(np.min(scores))
        max_score = float(np.max(scores))

        # Count low-preference assignments (score < 0.4)
        low_preference_count = sum(1 for s in scores if s < 0.4)

        # Distribution
        distribution = {
            "excellent": sum(1 for s in scores if s >= 0.8),
            "good": sum(1 for s in scores if 0.6 <= s < 0.8),
            "acceptable": sum(1 for s in scores if 0.4 <= s < 0.6),
            "poor": sum(1 for s in scores if s < 0.4),
        }

        return {
            "average_score": avg_score,
            "min_score": min_score,
            "max_score": max_score,
            "distribution": distribution,
            "low_preference_count": low_preference_count,
            "total_assignments": len(assignments),
        }

    def _score_workload_balance(self, schedule: dict[str, Any]) -> dict[str, Any]:
        """
        Score workload distribution balance.

        Args:
            schedule: Schedule dictionary

        Returns:
            Workload balance scoring details
        """
        people = schedule.get("people", [])
        if not people:
            return {
                "balance_score": 0.0,
                "fairness_metrics": {},
                "overloaded_count": 0,
            }

        # Calculate fairness metrics
        fairness = self.workload_optimizer.calculate_fairness_metric(people)

        # Identify overloaded people (above 85% utilization)
        overloaded = self.workload_optimizer.identify_overloaded(people, threshold=0.85)

        # Convert Gini coefficient to balance score (lower Gini = better balance)
        # Gini ranges from 0 (perfect equality) to 1 (perfect inequality)
        gini = fairness.get("gini_coefficient", 0.0)
        balance_score = 1.0 - gini

        # Penalize if there are overloaded people
        if overloaded:
            penalty = min(0.3, len(overloaded) * 0.05)
            balance_score = max(0.0, balance_score - penalty)

        return {
            "balance_score": float(balance_score),
            "fairness_metrics": fairness,
            "overloaded_count": len(overloaded),
            "overloaded_people": overloaded[:5],  # Top 5 most overloaded
            "total_people": len(people),
        }

    def _score_conflict_risk(self, schedule: dict[str, Any]) -> dict[str, Any]:
        """
        Score conflict risk.

        Args:
            schedule: Schedule dictionary

        Returns:
            Conflict risk scoring details
        """
        assignments = schedule.get("assignments", [])
        if not assignments:
            return {
                "safety_score": 1.0,
                "high_risk_count": 0,
                "average_risk": 0.0,
            }

        # Identify high-risk assignments
        high_risk = self.conflict_predictor.identify_high_risk_assignments(
            assignments, threshold=0.7
        )

        # Calculate average risk across all assignments
        risks = []
        for assignment in assignments:
            prob = self.conflict_predictor.predict_conflict_probability(
                person_data=assignment.get("person", {}),
                proposed_assignment=assignment.get("proposed", {}),
                existing_assignments=assignment.get("existing", []),
                context_data=assignment.get("context"),
            )
            risks.append(prob)

        avg_risk = float(np.mean(risks)) if risks else 0.0

        # Safety score is inverse of average risk
        safety_score = 1.0 - avg_risk

        # Penalize if there are high-risk assignments
        if high_risk:
            penalty = min(0.3, len(high_risk) * 0.05)
            safety_score = max(0.0, safety_score - penalty)

        # Risk distribution
        risk_distribution = {
            "critical": sum(1 for r in risks if r >= 0.8),
            "high": sum(1 for r in risks if 0.6 <= r < 0.8),
            "medium": sum(1 for r in risks if 0.4 <= r < 0.6),
            "low": sum(1 for r in risks if r < 0.4),
        }

        return {
            "safety_score": float(safety_score),
            "average_risk": avg_risk,
            "high_risk_count": len(high_risk),
            "high_risk_assignments": high_risk[:5],  # Top 5 highest risk
            "risk_distribution": risk_distribution,
            "total_assignments": len(assignments),
        }

    def suggest_improvements(
        self,
        schedule: dict[str, Any],
        max_suggestions: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Suggest schedule improvements.

        Args:
            schedule: Schedule dictionary
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of improvement suggestions, sorted by impact
        """
        suggestions = []

        # 1. Workload rebalancing suggestions
        people = schedule.get("people", [])
        if people:
            workload_suggestions = self.workload_optimizer.suggest_rebalancing(
                people, target_utilization=0.8
            )

            for suggestion in workload_suggestions[:5]:  # Top 5 workload suggestions
                suggestions.append({
                    "type": "workload_rebalancing",
                    "priority": suggestion.get("priority", 0),
                    "impact": "high",
                    "action": suggestion.get("action"),
                    "details": suggestion,
                })

        # 2. High-risk conflict assignments
        assignments = schedule.get("assignments", [])
        if assignments:
            high_risk = self.conflict_predictor.identify_high_risk_assignments(
                assignments, threshold=0.6
            )

            for risk_item in high_risk[:5]:  # Top 5 risky assignments
                suggestions.append({
                    "type": "conflict_mitigation",
                    "priority": risk_item["conflict_probability"],
                    "impact": "critical" if risk_item["conflict_probability"] >= 0.8 else "high",
                    "action": "review_or_reassign",
                    "details": risk_item,
                })

        # 3. Low-preference assignments
        for assignment in assignments:
            score = self.preference_predictor.predict(
                person_data=assignment.get("person", {}),
                rotation_data=assignment.get("rotation", {}),
                block_data=assignment.get("block", {}),
                historical_stats=assignment.get("historical_stats"),
            )

            if score < 0.3:  # Very low preference
                suggestions.append({
                    "type": "preference_improvement",
                    "priority": 1.0 - score,  # Lower score = higher priority
                    "impact": "medium",
                    "action": "consider_alternative",
                    "details": {
                        "assignment": assignment,
                        "preference_score": score,
                    },
                })

        # Sort by priority (highest first)
        suggestions.sort(key=lambda x: x["priority"], reverse=True)

        return suggestions[:max_suggestions]

    def compare_schedules(
        self,
        schedule_a: dict[str, Any],
        schedule_b: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Compare two schedules and determine which is better.

        Args:
            schedule_a: First schedule
            schedule_b: Second schedule

        Returns:
            Comparison results with winner and differences
        """
        score_a = self.score_schedule(schedule_a)
        score_b = self.score_schedule(schedule_b)

        overall_a = score_a["overall_score"]
        overall_b = score_b["overall_score"]

        # Determine winner
        if overall_a > overall_b:
            winner = "schedule_a"
            difference = overall_a - overall_b
        elif overall_b > overall_a:
            winner = "schedule_b"
            difference = overall_b - overall_a
        else:
            winner = "tie"
            difference = 0.0

        # Component comparison
        components_comparison = {}
        for component in ["preference", "workload", "conflict"]:
            a_score = score_a["components"][component]
            b_score = score_b["components"][component]
            components_comparison[component] = {
                "schedule_a": a_score,
                "schedule_b": b_score,
                "winner": "schedule_a" if a_score > b_score else "schedule_b" if b_score > a_score else "tie",
            }

        return {
            "winner": winner,
            "difference": float(difference),
            "schedule_a_score": score_a,
            "schedule_b_score": score_b,
            "components_comparison": components_comparison,
        }

    def _score_to_grade(self, score: float) -> str:
        """
        Convert numeric score to letter grade.

        Args:
            score: Score (0-1)

        Returns:
            Letter grade (A+ to F)
        """
        if score >= 0.95:
            return "A+"
        elif score >= 0.90:
            return "A"
        elif score >= 0.85:
            return "A-"
        elif score >= 0.80:
            return "B+"
        elif score >= 0.75:
            return "B"
        elif score >= 0.70:
            return "B-"
        elif score >= 0.65:
            return "C+"
        elif score >= 0.60:
            return "C"
        elif score >= 0.55:
            return "C-"
        elif score >= 0.50:
            return "D"
        else:
            return "F"

    def generate_report(self, schedule: dict[str, Any]) -> str:
        """
        Generate a human-readable report of schedule quality.

        Args:
            schedule: Schedule dictionary

        Returns:
            Markdown-formatted report
        """
        score_result = self.score_schedule(schedule)
        suggestions = self.suggest_improvements(schedule, max_suggestions=5)

        report = []
        report.append("# Schedule Quality Report\n")

        # Overall score
        report.append(f"## Overall Grade: {score_result['grade']}")
        report.append(f"**Score:** {score_result['overall_score']:.2%}\n")

        # Component scores
        report.append("## Component Scores\n")

        # Preference
        pref = score_result["components"]["preference"]
        report.append(f"### 1. Preference Score: {pref['average_score']:.2%}")
        report.append(f"- Total Assignments: {pref['total_assignments']}")
        report.append(f"- Low Preference Assignments: {pref['low_preference_count']}")
        report.append(f"- Distribution: Excellent={pref['distribution']['excellent']}, "
                     f"Good={pref['distribution']['good']}, "
                     f"Acceptable={pref['distribution']['acceptable']}, "
                     f"Poor={pref['distribution']['poor']}\n")

        # Workload
        workload = score_result["components"]["workload"]
        report.append(f"### 2. Workload Balance: {workload['balance_score']:.2%}")
        report.append(f"- Overloaded People: {workload['overloaded_count']}/{workload['total_people']}")
        report.append(f"- Gini Coefficient: {workload['fairness_metrics']['gini_coefficient']:.3f} "
                     f"(lower is more fair)")
        report.append(f"- Workload Range: {workload['fairness_metrics']['min_workload']:.1%} - "
                     f"{workload['fairness_metrics']['max_workload']:.1%}\n")

        # Conflict
        conflict = score_result["components"]["conflict"]
        report.append(f"### 3. Conflict Safety: {conflict['safety_score']:.2%}")
        report.append(f"- High Risk Assignments: {conflict['high_risk_count']}")
        report.append(f"- Average Risk: {conflict['average_risk']:.2%}")
        report.append(f"- Risk Distribution: Critical={conflict['risk_distribution']['critical']}, "
                     f"High={conflict['risk_distribution']['high']}, "
                     f"Medium={conflict['risk_distribution']['medium']}, "
                     f"Low={conflict['risk_distribution']['low']}\n")

        # Suggestions
        if suggestions:
            report.append("## Top Improvement Suggestions\n")
            for i, suggestion in enumerate(suggestions, 1):
                report.append(f"{i}. **{suggestion['type'].replace('_', ' ').title()}** "
                            f"(Impact: {suggestion['impact']})")
                report.append(f"   - Action: {suggestion['action']}")
                report.append(f"   - Priority: {suggestion['priority']:.2f}\n")

        return "\n".join(report)
