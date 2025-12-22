"""
Training Data Pipeline - Prepares data for ML model training.

Extracts historical scheduling data from the database and prepares
feature matrices and labels for training ML models.
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

import numpy as np
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.assignment import Assignment
from app.models.block import Block
from app.models.conflict_alert import ConflictAlert
from app.models.faculty_preference import FacultyPreference
from app.models.person import Person
from app.models.rotation_template import RotationTemplate
from app.models.swap import SwapRequest

logger = logging.getLogger(__name__)


class TrainingDataPipeline:
    """
    Pipeline for extracting and preparing training data from database.

    Features:
    - Extracts historical assignments
    - Computes preference scores from swaps and feedback
    - Identifies conflicts and ACGME violations
    - Calculates workload metrics
    - Generates training datasets for all ML models
    """

    def __init__(self, db: AsyncSession | Session):
        """
        Initialize training data pipeline.

        Args:
            db: Async database session
        """
        self.db = db

    async def _execute(self, query):
        """Execute a query on either async or sync database sessions."""
        if isinstance(self.db, AsyncSession):
            return await self.db.execute(query)
        return self.db.execute(query)

    async def extract_preference_training_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_samples: int = 100,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """
        Extract training data for preference predictor.

        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            min_samples: Minimum number of samples required

        Returns:
            Tuple of (features DataFrame, labels array)
        """
        logger.info("Extracting preference training data...")

        # Default to last year if not specified
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        # Query assignments with related data
        query = (
            select(Assignment, Person, Block, RotationTemplate)
            .join(Person, Assignment.person_id == Person.id)
            .join(Block, Assignment.block_id == Block.id)
            .outerjoin(RotationTemplate, Assignment.rotation_template_id == RotationTemplate.id)
            .where(Block.date >= start_date.date())
            .where(Block.date <= end_date.date())
        )

        result = await self._execute(query)
        rows = result.all()

        logger.info(f"Found {len(rows)} historical assignments")

        if len(rows) < min_samples:
            logger.warning(f"Insufficient data: {len(rows)} < {min_samples} samples")

        # Extract features and labels
        features_list = []
        labels_list = []

        for assignment, person, block, rotation_template in rows:
            # Person data
            person_data = {
                "type": person.type,
                "pgy_level": person.pgy_level,
                "faculty_role": person.faculty_role,
            }

            # Rotation data
            rotation_data = {
                "name": rotation_template.name if rotation_template else "Unknown",
            }

            # Block data
            block_data = {
                "date": block.date,
                "time_of_day": block.time_of_day,
                "is_weekend": block.is_weekend,
                "is_holiday": block.is_holiday,
            }

            # Historical stats (simplified for training)
            historical_stats = {
                "avg_preference_score": 0.5,  # Placeholder
                "similar_count": 0,
                "swap_rate": 0.0,
                "current_workload": 0.0,
            }

            # Build feature dict (mimicking PreferencePredictor.extract_features)
            features = self._build_preference_features(
                person_data, rotation_data, block_data, historical_stats
            )

            # Calculate label (preference score)
            # Use assignment score if available, otherwise infer from swaps
            if assignment.score is not None:
                label = assignment.score
            else:
                # Check if this assignment was swapped (indicates low preference)
                was_swapped = await self._was_assignment_swapped(assignment.id)
                label = 0.3 if was_swapped else 0.7  # Default scores

            features_list.append(features)
            labels_list.append(label)

        # Convert to DataFrame and array
        X = pd.DataFrame(features_list)
        y = np.array(labels_list)

        logger.info(f"Extracted {len(X)} training samples with {len(X.columns)} features")

        return X, y

    async def extract_workload_training_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_samples: int = 50,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """
        Extract training data for workload optimizer.

        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            min_samples: Minimum number of samples required

        Returns:
            Tuple of (features DataFrame, optimal workload labels array)
        """
        logger.info("Extracting workload training data...")

        # Default to last year
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        # Get all people
        people_query = select(Person)
        result = await self._execute(people_query)
        people = result.scalars().all()

        features_list = []
        labels_list = []

        for person in people:
            # Get assignments for this person in time range
            assignments_query = (
                select(Assignment, Block)
                .join(Block, Assignment.block_id == Block.id)
                .where(Assignment.person_id == person.id)
                .where(Block.date >= start_date.date())
                .where(Block.date <= end_date.date())
            )

            assignments_result = await self._execute(assignments_query)
            assignment_rows = assignments_result.all()

            if not assignment_rows:
                continue

            # Person data
            person_data = {
                "type": person.type,
                "pgy_level": person.pgy_level,
                "faculty_role": person.faculty_role,
                "target_clinical_blocks": person.target_clinical_blocks or 48,
                "weekday_call_count": person.weekday_call_count or 0,
                "sunday_call_count": person.sunday_call_count or 0,
                "fmit_weeks_count": person.fmit_weeks_count or 0,
            }

            # Current assignments
            current_assignments = []
            for assignment, block in assignment_rows:
                current_assignments.append({
                    "rotation_name": assignment.activity_name,
                    "is_weekend": block.is_weekend,
                    "date": block.date,
                })

            # Historical data (placeholder)
            historical_data = {
                "avg_workload": 0.7,
                "max_workload": 0.9,
                "swap_rate": 0.1,
                "conflict_rate": 0.05,
            }

            # Build features
            features = self._build_workload_features(
                person_data, current_assignments, historical_data
            )

            # Calculate optimal workload (label)
            # Use 80% utilization as baseline, adjust based on actual performance
            target = person_data["target_clinical_blocks"]
            actual = len(current_assignments)
            utilization = actual / target if target > 0 else 0

            # Check if they had conflicts (would indicate overload)
            had_conflicts = await self._person_had_conflicts(person.id, start_date, end_date)

            if had_conflicts:
                optimal = max(0.0, utilization - 0.1)  # Reduce by 10% if had conflicts
            else:
                optimal = min(1.0, utilization)  # Current level is good

            # Clip to reasonable range
            optimal = np.clip(optimal, 0.0, 1.0)

            features_list.append(features)
            labels_list.append(optimal)

        X = pd.DataFrame(features_list)
        y = np.array(labels_list)

        logger.info(f"Extracted {len(X)} workload training samples")

        return X, y

    async def extract_conflict_training_data(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        min_samples: int = 100,
    ) -> tuple[pd.DataFrame, np.ndarray]:
        """
        Extract training data for conflict predictor.

        Args:
            start_date: Start date for historical data
            end_date: End date for historical data
            min_samples: Minimum number of samples required

        Returns:
            Tuple of (features DataFrame, conflict labels array)
        """
        logger.info("Extracting conflict training data...")

        # Default to last year
        if end_date is None:
            end_date = datetime.utcnow()
        if start_date is None:
            start_date = end_date - timedelta(days=365)

        # Get all assignments
        query = (
            select(Assignment, Person, Block)
            .join(Person, Assignment.person_id == Person.id)
            .join(Block, Assignment.block_id == Block.id)
            .where(Block.date >= start_date.date())
            .where(Block.date <= end_date.date())
        )

        result = await self._execute(query)
        rows = result.all()

        features_list = []
        labels_list = []

        for assignment, person, block in rows:
            # Get existing assignments for this person up to this block
            existing_query = (
                select(Assignment, Block)
                .join(Block, Assignment.block_id == Block.id)
                .where(Assignment.person_id == person.id)
                .where(Block.date <= block.date)
                .where(Assignment.id != assignment.id)
            )

            existing_result = await self._execute(existing_query)
            existing_rows = existing_result.all()

            # Person data
            person_data = {
                "type": person.type,
                "pgy_level": person.pgy_level,
                "weekday_call_count": person.weekday_call_count or 0,
                "sunday_call_count": person.sunday_call_count or 0,
            }

            # Proposed assignment (the one we're evaluating)
            proposed_assignment = {
                "date": block.date,
                "is_weekend": block.is_weekend,
                "is_holiday": block.is_holiday,
                "rotation_name": assignment.activity_name,
            }

            # Existing assignments
            existing_assignments = [
                {
                    "date": b.date,
                    "rotation_name": a.activity_name,
                }
                for a, b in existing_rows
            ]

            # Context data (placeholder)
            context_data = {
                "faculty_count_on_date": 5,
                "resident_count_on_date": 10,
                "historical_conflict_rate": 0.05,
                "recent_swap_count": 0,
                "coverage_level": 1.0,
            }

            # Build features
            features = self._build_conflict_features(
                person_data, proposed_assignment, existing_assignments, context_data
            )

            # Check if this assignment had a conflict
            had_conflict = await self._assignment_had_conflict(assignment.id)

            features_list.append(features)
            labels_list.append(1 if had_conflict else 0)

        X = pd.DataFrame(features_list)
        y = np.array(labels_list)

        logger.info(f"Extracted {len(X)} conflict training samples")

        return X, y

    def _build_preference_features(
        self,
        person_data: dict[str, Any],
        rotation_data: dict[str, Any],
        block_data: dict[str, Any],
        historical_stats: dict[str, Any],
    ) -> dict[str, Any]:
        """Build features for preference prediction (simplified version)."""
        features = {}

        # Person features
        features["is_faculty"] = 1 if person_data.get("type") == "faculty" else 0
        features["is_resident"] = 1 if person_data.get("type") == "resident" else 0
        features["pgy_level"] = person_data.get("pgy_level", 0) or 0

        ***REMOVED*** role encoding
        faculty_role = person_data.get("faculty_role", "")
        for role in ["pd", "apd", "oic", "dept_chief", "sports_med", "core"]:
            features[f"role_{role}"] = 1 if faculty_role == role else 0

        # Rotation features
        rotation_name = rotation_data.get("name", "")
        for rot_type in ["clinic", "inpatient", "procedures", "conference", "admin"]:
            features[f"rotation_{rot_type}"] = 1 if rot_type in rotation_name.lower() else 0

        # Temporal features
        block_date = block_data.get("date")
        if block_date:
            features["day_of_week"] = block_date.weekday()
            features["is_monday"] = 1 if block_date.weekday() == 0 else 0
            features["is_friday"] = 1 if block_date.weekday() == 4 else 0
            features["is_weekend"] = 1 if block_date.weekday() >= 5 else 0
            features["month"] = block_date.month
            features["quarter"] = (block_date.month - 1) // 3 + 1
            features["week_of_year"] = block_date.isocalendar()[1]
        else:
            features["day_of_week"] = 0
            features["is_monday"] = 0
            features["is_friday"] = 0
            features["is_weekend"] = 0
            features["month"] = 1
            features["quarter"] = 1
            features["week_of_year"] = 1

        # Time of day
        features["is_am"] = 1 if block_data.get("time_of_day") == "AM" else 0
        features["is_pm"] = 1 if block_data.get("time_of_day") == "PM" else 0
        features["is_holiday"] = 1 if block_data.get("is_holiday", False) else 0

        # Historical stats
        features["historical_preference_score"] = historical_stats.get("avg_preference_score", 0.5)
        features["num_similar_assignments"] = historical_stats.get("similar_count", 0)
        features["swap_rate"] = historical_stats.get("swap_rate", 0.0)
        features["workload_current"] = historical_stats.get("current_workload", 0.0)

        return features

    def _build_workload_features(
        self,
        person_data: dict[str, Any],
        current_assignments: list[dict[str, Any]],
        historical_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Build features for workload optimization."""
        features = {}

        # Person characteristics
        features["is_faculty"] = 1 if person_data.get("type") == "faculty" else 0
        features["is_resident"] = 1 if person_data.get("type") == "resident" else 0
        features["pgy_level"] = person_data.get("pgy_level", 0) or 0

        ***REMOVED*** role
        faculty_role = person_data.get("faculty_role", "")
        for role in ["pd", "apd", "oic", "dept_chief", "sports_med", "core"]:
            features[f"role_{role}"] = 1 if faculty_role == role else 0

        # Workload metrics
        features["target_clinical_blocks"] = person_data.get("target_clinical_blocks", 48)
        features["current_assignment_count"] = len(current_assignments)

        # Rotation type counts
        rotation_counts = {"clinic": 0, "inpatient": 0, "procedures": 0, "admin": 0, "other": 0}
        for assignment in current_assignments:
            rotation_name = assignment.get("rotation_name", "").lower()
            if "clinic" in rotation_name:
                rotation_counts["clinic"] += 1
            elif "inpatient" in rotation_name:
                rotation_counts["inpatient"] += 1
            elif "procedure" in rotation_name:
                rotation_counts["procedures"] += 1
            elif "admin" in rotation_name:
                rotation_counts["admin"] += 1
            else:
                rotation_counts["other"] += 1

        for rot_type, count in rotation_counts.items():
            features[f"assignments_{rot_type}"] = count

        # Workload concentration
        num_assignments = len(current_assignments)
        if num_assignments > 0:
            counts = [c for c in rotation_counts.values() if c > 0]
            diversity = sum((c / num_assignments) ** 2 for c in counts) if counts else 0
            features["workload_concentration"] = diversity
        else:
            features["workload_concentration"] = 0.0

        # Weekend burden
        weekend_count = sum(1 for a in current_assignments if a.get("is_weekend", False))
        features["weekend_assignment_count"] = weekend_count

        # Call counts
        features["call_count"] = person_data.get("weekday_call_count", 0)
        features["sunday_call_count"] = person_data.get("sunday_call_count", 0)
        features["fmit_weeks_count"] = person_data.get("fmit_weeks_count", 0)

        # Historical metrics
        features["historical_avg_workload"] = historical_data.get("avg_workload", 0.0)
        features["historical_max_workload"] = historical_data.get("max_workload", 0.0)
        features["historical_swap_rate"] = historical_data.get("swap_rate", 0.0)
        features["historical_conflict_rate"] = historical_data.get("conflict_rate", 0.0)

        # Utilization ratio
        target = features["target_clinical_blocks"]
        if target > 0:
            features["workload_utilization"] = num_assignments / target
        else:
            features["workload_utilization"] = 0.0

        return features

    def _build_conflict_features(
        self,
        person_data: dict[str, Any],
        proposed_assignment: dict[str, Any],
        existing_assignments: list[dict[str, Any]],
        context_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Build features for conflict prediction (simplified)."""
        features = {}

        # Person characteristics
        features["is_faculty"] = 1 if person_data.get("type") == "faculty" else 0
        features["is_resident"] = 1 if person_data.get("type") == "resident" else 0
        features["pgy_level"] = person_data.get("pgy_level", 0) or 0

        # Current workload
        features["current_assignment_count"] = len(existing_assignments)
        features["hours_this_week"] = len(existing_assignments) * 4
        features["approaching_80_hour_limit"] = 1 if features["hours_this_week"] >= 70 else 0
        features["exceeds_80_hour_limit"] = 1 if features["hours_this_week"] >= 80 else 0

        # Days worked
        unique_dates = set(a.get("date") for a in existing_assignments if "date" in a)
        features["days_worked_this_week"] = len(unique_dates)
        features["violates_1_in_7"] = 1 if len(unique_dates) >= 7 else 0
        features["max_consecutive_days"] = min(len(existing_assignments), 7)

        # Proposed assignment
        features["proposed_is_weekend"] = 1 if proposed_assignment.get("is_weekend", False) else 0
        features["proposed_is_holiday"] = 1 if proposed_assignment.get("is_holiday", False) else 0
        features["proposed_day_of_week"] = 0  # Simplified

        # Rotation type
        proposed_rotation = proposed_assignment.get("rotation_name", "").lower()
        features["proposed_is_clinic"] = 1 if "clinic" in proposed_rotation else 0
        features["proposed_is_inpatient"] = 1 if "inpatient" in proposed_rotation else 0
        features["proposed_is_procedure"] = 1 if "procedure" in proposed_rotation else 0

        # Same-day conflicts
        proposed_date = proposed_assignment.get("date")
        same_day = [a for a in existing_assignments if a.get("date") == proposed_date]
        features["same_day_assignment_count"] = len(same_day)
        features["has_same_day_conflict"] = 1 if len(same_day) > 0 else 0

        # Supervision
        if features["is_resident"]:
            supervision_ratio = 2 if features["pgy_level"] == 1 else 4
            features["supervision_ratio"] = supervision_ratio
            features["actual_supervision_ratio"] = context_data.get("resident_count_on_date", 1) / max(context_data.get("faculty_count_on_date", 1), 1)
            features["violates_supervision"] = 1 if features["actual_supervision_ratio"] > supervision_ratio else 0
        else:
            features["supervision_ratio"] = 0
            features["actual_supervision_ratio"] = 0
            features["violates_supervision"] = 0

        # Call counts
        features["call_count"] = person_data.get("weekday_call_count", 0)
        features["sunday_call_count"] = person_data.get("sunday_call_count", 0)

        # Context
        features["historical_conflict_rate"] = context_data.get("historical_conflict_rate", 0.0)
        features["recent_swap_count"] = context_data.get("recent_swap_count", 0)
        features["coverage_level"] = context_data.get("coverage_level", 1.0)
        features["understaffed"] = 1 if context_data.get("coverage_level", 1.0) < 0.8 else 0

        # Workload diversity
        rotation_types = [a.get("rotation_name", "") for a in existing_assignments]
        if rotation_types:
            unique_rotations = len(set(rotation_types))
            total_rotations = len(rotation_types)
            features["workload_diversity"] = unique_rotations / total_rotations if total_rotations > 0 else 0
        else:
            features["workload_diversity"] = 0

        return features

    async def _was_assignment_swapped(self, assignment_id: str) -> bool:
        """Check if an assignment was involved in a swap."""
        # Query swap requests related to this assignment
        query = select(func.count(SwapRequest.id)).where(
            SwapRequest.status == "completed",
            (SwapRequest.assignment_from_id == assignment_id)
            | (SwapRequest.assignment_to_id == assignment_id),
        )
        result = await self._execute(query)
        count = result.scalar()
        return count > 0

    async def _person_had_conflicts(
        self,
        person_id: str,
        start_date: datetime,
        end_date: datetime,
    ) -> bool:
        """Check if person had any conflicts in date range."""
        query = (
            select(func.count(ConflictAlert.id))
            .where(ConflictAlert.created_at >= start_date)
            .where(ConflictAlert.created_at <= end_date)
        )
        result = await self._execute(query)
        count = result.scalar()
        return count > 0

    async def _assignment_had_conflict(self, assignment_id: str) -> bool:
        """Check if an assignment resulted in a conflict."""
        # Simplified: check if there are any conflict alerts
        query = select(func.count(ConflictAlert.id)).where(
            ConflictAlert.severity.in_(["warning", "error", "critical"])
        )
        result = await self._execute(query)
        count = result.scalar()
        # Randomly assign some as conflicts for training (simplified)
        return (count % 5) == 0  # Simplified heuristic
