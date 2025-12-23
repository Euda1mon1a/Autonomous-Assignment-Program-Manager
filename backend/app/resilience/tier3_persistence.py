"""
Tier 3 Resilience Database Persistence Helpers.

Provides functions to persist Tier 3 component data to the database:
- Cognitive sessions and decisions
- Preference trails and signals
- Faculty centrality and hub analysis
- Protection plans and cross-training recommendations

These functions bridge the in-memory Tier 3 components with database storage.
"""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.resilience import (
    CognitiveDecisionRecord,
    CognitiveSessionRecord,
    CrossTrainingRecommendationRecord,
    FacultyCentralityRecord,
    HubProtectionPlanRecord,
    PreferenceTrailRecord,
    TrailSignalRecord,
)
from app.resilience.cognitive_load import (
    CognitiveSession,
    Decision,
    DecisionOutcome,
)
from app.resilience.hub_analysis import (
    CrossTrainingRecommendation,
    FacultyCentrality,
    HubProtectionPlan,
)
from app.resilience.stigmergy import (
    PreferenceTrail,
)

# =============================================================================
# Cognitive Load Persistence
# =============================================================================


def persist_cognitive_session(
    db: Session, session: CognitiveSession
) -> CognitiveSessionRecord:
    """
    Persist a cognitive session to the database.

    Args:
        db: Database session
        session: CognitiveSession object to persist

    Returns:
        Created CognitiveSessionRecord
    """
    record = CognitiveSessionRecord(
        id=session.id,
        user_id=session.user_id,
        started_at=session.started_at,
        ended_at=session.ended_at,
        max_decisions_before_break=session.max_decisions_before_break,
        total_cognitive_cost=session.total_cognitive_cost,
        decisions_count=session.decisions_count,
        breaks_taken=session.breaks_taken,
        final_state=session.current_state.value if session.ended_at else None,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_cognitive_session(
    db: Session, session: CognitiveSession
) -> CognitiveSessionRecord | None:
    """
    Update an existing cognitive session record.

    Args:
        db: Database session
        session: CognitiveSession with updated data

    Returns:
        Updated CognitiveSessionRecord or None
    """
    record = (
        db.query(CognitiveSessionRecord)
        .filter(CognitiveSessionRecord.id == session.id)
        .first()
    )

    if record:
        record.ended_at = session.ended_at
        record.total_cognitive_cost = session.total_cognitive_cost
        record.decisions_count = session.decisions_count
        record.breaks_taken = session.breaks_taken
        record.final_state = session.current_state.value
        db.commit()
        db.refresh(record)

    return record


def persist_decision(
    db: Session, decision: Decision, session_id: UUID = None
) -> CognitiveDecisionRecord:
    """
    Persist a decision to the database.

    Args:
        db: Database session
        decision: Decision object to persist
        session_id: Optional session this decision belongs to

    Returns:
        Created CognitiveDecisionRecord
    """
    record = CognitiveDecisionRecord(
        id=decision.id,
        session_id=session_id,
        category=decision.category.value,
        complexity=decision.complexity.value,
        description=decision.description,
        options=decision.options,
        recommended_option=decision.recommended_option,
        safe_default=decision.safe_default,
        has_safe_default=decision.has_safe_default,
        is_urgent=decision.is_urgent,
        can_defer=decision.can_defer,
        deadline=decision.deadline,
        context=decision.context,
        estimated_cognitive_cost=decision.get_cognitive_cost(),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_decision_resolution(
    db: Session,
    decision_id: UUID,
    outcome: DecisionOutcome,
    chosen_option: str,
    decided_by: str,
    actual_time_seconds: float = None,
) -> CognitiveDecisionRecord | None:
    """
    Update a decision record with resolution details.

    Args:
        db: Database session
        decision_id: ID of the decision
        outcome: How the decision was resolved
        chosen_option: What was chosen
        decided_by: Who made the decision
        actual_time_seconds: Time taken

    Returns:
        Updated CognitiveDecisionRecord or None
    """
    record = (
        db.query(CognitiveDecisionRecord)
        .filter(CognitiveDecisionRecord.id == decision_id)
        .first()
    )

    if record:
        record.outcome = outcome.value
        record.chosen_option = chosen_option
        record.decided_at = datetime.utcnow()
        record.decided_by = decided_by
        record.actual_time_seconds = actual_time_seconds
        db.commit()
        db.refresh(record)

    return record


def get_session_history(
    db: Session,
    user_id: UUID = None,
    limit: int = 50,
) -> list[CognitiveSessionRecord]:
    """
    Get cognitive session history.

    Args:
        db: Database session
        user_id: Filter by user (optional)
        limit: Max records to return

    Returns:
        List of CognitiveSessionRecord
    """
    query = db.query(CognitiveSessionRecord)

    if user_id:
        query = query.filter(CognitiveSessionRecord.user_id == user_id)

    return query.order_by(CognitiveSessionRecord.started_at.desc()).limit(limit).all()


# =============================================================================
# Stigmergy Persistence
# =============================================================================


def persist_preference_trail(
    db: Session, trail: PreferenceTrail
) -> PreferenceTrailRecord:
    """
    Persist or update a preference trail in the database.

    Args:
        db: Database session
        trail: PreferenceTrail object to persist

    Returns:
        Created or updated PreferenceTrailRecord
    """
    # Check if trail already exists
    existing = (
        db.query(PreferenceTrailRecord)
        .filter(PreferenceTrailRecord.id == trail.id)
        .first()
    )

    if existing:
        # Update existing record
        existing.strength = trail.strength
        existing.peak_strength = trail.peak_strength
        existing.reinforcement_count = trail.reinforcement_count
        existing.last_reinforced = trail.last_reinforced
        existing.last_evaporated = trail.last_evaporated
        db.commit()
        db.refresh(existing)
        return existing

    # Create new record
    record = PreferenceTrailRecord(
        id=trail.id,
        faculty_id=trail.faculty_id,
        trail_type=trail.trail_type.value,
        slot_id=trail.slot_id,
        slot_type=trail.slot_type,
        block_type=trail.block_type,
        service_type=trail.service_type,
        target_faculty_id=trail.target_faculty_id,
        strength=trail.strength,
        peak_strength=trail.peak_strength,
        evaporation_rate=trail.evaporation_rate,
        reinforcement_count=trail.reinforcement_count,
        last_reinforced=trail.last_reinforced,
        last_evaporated=trail.last_evaporated,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def persist_trail_signal(
    db: Session,
    trail_id: UUID,
    signal_type: str,
    strength_change: float,
) -> TrailSignalRecord:
    """
    Record a signal that updated a trail.

    Args:
        db: Database session
        trail_id: ID of the trail that was updated
        signal_type: Type of signal
        strength_change: Amount of change

    Returns:
        Created TrailSignalRecord
    """
    record = TrailSignalRecord(
        id=uuid.uuid4(),
        trail_id=trail_id,
        signal_type=signal_type,
        strength_change=strength_change,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def load_preference_trails(
    db: Session, faculty_id: UUID = None
) -> list[PreferenceTrailRecord]:
    """
    Load preference trails from database.

    Args:
        db: Database session
        faculty_id: Filter by faculty (optional)

    Returns:
        List of PreferenceTrailRecord
    """
    query = db.query(PreferenceTrailRecord)

    if faculty_id:
        query = query.filter(PreferenceTrailRecord.faculty_id == faculty_id)

    return query.all()


def delete_weak_trails(db: Session, min_strength: float = 0.01) -> int:
    """
    Delete trails that have evaporated below minimum strength.

    Args:
        db: Database session
        min_strength: Minimum strength threshold

    Returns:
        Number of trails deleted
    """
    count = (
        db.query(PreferenceTrailRecord)
        .filter(PreferenceTrailRecord.strength < min_strength)
        .delete()
    )
    db.commit()
    return count


# =============================================================================
# Hub Analysis Persistence
# =============================================================================


def persist_faculty_centrality(
    db: Session,
    centrality: FacultyCentrality,
) -> FacultyCentralityRecord:
    """
    Persist faculty centrality scores.

    Args:
        db: Database session
        centrality: FacultyCentrality object to persist

    Returns:
        Created FacultyCentralityRecord
    """
    record = FacultyCentralityRecord(
        id=uuid.uuid4(),
        faculty_id=centrality.faculty_id,
        faculty_name=centrality.faculty_name,
        degree_centrality=centrality.degree_centrality,
        betweenness_centrality=centrality.betweenness_centrality,
        eigenvector_centrality=centrality.eigenvector_centrality,
        pagerank=centrality.pagerank,
        composite_score=centrality.composite_score,
        services_covered=centrality.services_covered,
        unique_services=centrality.unique_services,
        total_assignments=centrality.total_assignments,
        replacement_difficulty=centrality.replacement_difficulty,
        risk_level=centrality.risk_level.value,
        is_hub=centrality.is_hub,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def persist_hub_analysis_results(
    db: Session,
    centrality_results: list[FacultyCentrality],
) -> list[FacultyCentralityRecord]:
    """
    Persist all centrality results from a hub analysis.

    Args:
        db: Database session
        centrality_results: List of FacultyCentrality results

    Returns:
        List of created FacultyCentralityRecord
    """
    records = []
    for centrality in centrality_results:
        record = persist_faculty_centrality(db, centrality)
        records.append(record)
    return records


def persist_hub_protection_plan(
    db: Session,
    plan: HubProtectionPlan,
    created_by: str = None,
) -> HubProtectionPlanRecord:
    """
    Persist a hub protection plan.

    Args:
        db: Database session
        plan: HubProtectionPlan object to persist
        created_by: User who created the plan

    Returns:
        Created HubProtectionPlanRecord
    """
    record = HubProtectionPlanRecord(
        id=plan.id,
        hub_faculty_id=plan.hub_faculty_id,
        hub_faculty_name=plan.hub_faculty_name,
        period_start=datetime.combine(plan.period_start, datetime.min.time()),
        period_end=datetime.combine(plan.period_end, datetime.min.time()),
        reason=plan.reason,
        workload_reduction=plan.workload_reduction,
        backup_assigned=plan.backup_assigned,
        backup_faculty_ids=[str(f) for f in plan.backup_faculty_ids]
        if plan.backup_faculty_ids
        else None,
        critical_only=plan.critical_only,
        status=plan.status,
        created_by=created_by,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def update_protection_plan_status(
    db: Session,
    plan_id: UUID,
    status: str,
) -> HubProtectionPlanRecord | None:
    """
    Update the status of a protection plan.

    Args:
        db: Database session
        plan_id: ID of the plan
        status: New status

    Returns:
        Updated HubProtectionPlanRecord or None
    """
    record = (
        db.query(HubProtectionPlanRecord)
        .filter(HubProtectionPlanRecord.id == plan_id)
        .first()
    )

    if record:
        record.status = status
        if status == "active":
            record.activated_at = datetime.utcnow()
        elif status == "completed":
            record.deactivated_at = datetime.utcnow()
        db.commit()
        db.refresh(record)

    return record


def persist_cross_training_recommendation(
    db: Session,
    recommendation: CrossTrainingRecommendation,
) -> CrossTrainingRecommendationRecord:
    """
    Persist a cross-training recommendation.

    Args:
        db: Database session
        recommendation: CrossTrainingRecommendation object to persist

    Returns:
        Created CrossTrainingRecommendationRecord
    """
    record = CrossTrainingRecommendationRecord(
        id=recommendation.id,
        skill=recommendation.skill,
        current_holders=[str(h) for h in recommendation.current_holders]
        if recommendation.current_holders
        else None,
        recommended_trainees=[str(t) for t in recommendation.recommended_trainees]
        if recommendation.recommended_trainees
        else None,
        priority=recommendation.priority.value,
        reason=recommendation.reason,
        estimated_training_hours=recommendation.estimated_training_hours,
        risk_reduction=recommendation.risk_reduction,
        status=recommendation.status,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_active_protection_plans(db: Session) -> list[HubProtectionPlanRecord]:
    """
    Get all active protection plans.

    Args:
        db: Database session

    Returns:
        List of active HubProtectionPlanRecord
    """
    return (
        db.query(HubProtectionPlanRecord)
        .filter(HubProtectionPlanRecord.status == "active")
        .all()
    )


def get_latest_centrality_scores(
    db: Session, limit: int = 50
) -> list[FacultyCentralityRecord]:
    """
    Get the most recent centrality scores.

    Args:
        db: Database session
        limit: Max records to return

    Returns:
        List of FacultyCentralityRecord
    """
    return (
        db.query(FacultyCentralityRecord)
        .order_by(FacultyCentralityRecord.calculated_at.desc())
        .limit(limit)
        .all()
    )


def get_pending_cross_training(db: Session) -> list[CrossTrainingRecommendationRecord]:
    """
    Get pending cross-training recommendations.

    Args:
        db: Database session

    Returns:
        List of pending CrossTrainingRecommendationRecord
    """
    return (
        db.query(CrossTrainingRecommendationRecord)
        .filter(CrossTrainingRecommendationRecord.status.in_(["pending", "approved"]))
        .order_by(CrossTrainingRecommendationRecord.priority.desc())
        .all()
    )
