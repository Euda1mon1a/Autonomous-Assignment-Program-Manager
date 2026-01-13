"""Proxy Coverage API routes.

Answers "Who is covering for whom" - critical for situational awareness.
Consolidates all coverage relationships across the scheduling system:
- Remote surrogates
- Swap coverage (absorb/exchange)
- Backup call coverage
- Absence coverage
"""

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_active_user
from app.db.session import get_db
from app.models.absence import Absence
from app.models.assignment import Assignment
from app.models.block import Block
from app.models.call_assignment import CallAssignment
from app.models.person import Person
from app.models.swap import SwapRecord
from app.models.user import User
from app.schemas.proxy_coverage import (
    CoverageCountByType,
    CoverageRelationship,
    CoverageStats,
    CoverageStatus,
    CoverageType,
    PersonCoverageSummary,
    PersonRef,
    ProxyCoverageFilter,
    ProxyCoverageResponse,
    TopCoverer,
)

# Remote locations that may have surrogates
REMOTE_LOCATIONS = {"Hilo", "Okinawa", "Kapiolani"}

router = APIRouter()


def _person_to_ref(person: Person) -> PersonRef:
    """Convert Person model to PersonRef schema."""
    return PersonRef(
        id=person.id,
        name=person.name,
        pgy_level=person.pgy_level,
        role_type="resident" if person.pgy_level else "faculty",
    )


@router.get("", response_model=ProxyCoverageResponse)
async def get_proxy_coverage(
    date_param: date = Query(
        default=None,
        alias="date",
        description="Date to show coverage for (defaults to today)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get proxy coverage dashboard showing who is covering for whom.

    Returns:
    - Active coverage relationships for the specified date
    - Upcoming scheduled coverage (next 7 days)
    - Coverage grouped by person providing coverage
    - Statistics on coverage distribution

    Example: GET /api/proxy-coverage?date=2025-01-15
    """
    if date_param is None:
        date_param = date.today()

    upcoming_end = date_param + timedelta(days=7)

    # Collect all coverage relationships
    active_coverage: list[CoverageRelationship] = []
    upcoming_coverage: list[CoverageRelationship] = []

    # Track by coverer for grouping
    coverage_by_coverer: dict[str, list[CoverageRelationship]] = defaultdict(list)
    coverage_by_covered: dict[str, list[CoverageRelationship]] = defaultdict(list)

    # === 1. Swap Coverage ===
    # Get executed swaps that result in coverage
    executed_swaps = (
        db.query(SwapRecord)
        .options(
            joinedload(SwapRecord.source_faculty),
            joinedload(SwapRecord.target_faculty),
        )
        .filter(SwapRecord.status == "executed")
        .filter(
            # Source week or target week falls within our range
            (SwapRecord.source_week >= date_param)
            | (SwapRecord.target_week >= date_param)
        )
        .filter(
            (SwapRecord.source_week <= upcoming_end)
            | (SwapRecord.target_week <= upcoming_end)
        )
        .all()
    )

    for swap in executed_swaps:
        # For ABSORB swaps: target absorbs source's shift (target covers for source)
        # For ONE_TO_ONE swaps: bidirectional exchange
        if swap.swap_type == "absorb":
            # Target is covering for source
            covering_person = _person_to_ref(swap.target_faculty)
            covered_person = _person_to_ref(swap.source_faculty)

            is_active = swap.source_week == date_param
            status = CoverageStatus.ACTIVE if is_active else CoverageStatus.SCHEDULED

            relationship = CoverageRelationship(
                id=f"swap-{swap.id}",
                covering_person=covering_person,
                covered_person=covered_person,
                coverage_type=CoverageType.SWAP_ABSORB,
                status=status,
                start_date=swap.source_week,
                end_date=swap.source_week,
                location=None,
                reason=swap.reason,
                swap_id=swap.id,
            )

            if is_active:
                active_coverage.append(relationship)
            else:
                upcoming_coverage.append(relationship)

            coverage_by_coverer[str(covering_person.id)].append(relationship)
            coverage_by_covered[str(covered_person.id)].append(relationship)

        else:  # one_to_one - bidirectional exchange
            # Source covers target's week, target covers source's week
            source_ref = _person_to_ref(swap.source_faculty)
            target_ref = _person_to_ref(swap.target_faculty)

            # Coverage 1: Source covering for target (on target's week)
            if swap.target_week:
                is_active1 = swap.target_week == date_param
                status1 = (
                    CoverageStatus.ACTIVE if is_active1 else CoverageStatus.SCHEDULED
                )

                rel1 = CoverageRelationship(
                    id=f"swap-{swap.id}-src",
                    covering_person=source_ref,
                    covered_person=target_ref,
                    coverage_type=CoverageType.SWAP_EXCHANGE,
                    status=status1,
                    start_date=swap.target_week,
                    end_date=swap.target_week,
                    location=None,
                    reason=swap.reason,
                    swap_id=swap.id,
                )

                if is_active1:
                    active_coverage.append(rel1)
                elif swap.target_week <= upcoming_end:
                    upcoming_coverage.append(rel1)

                coverage_by_coverer[str(source_ref.id)].append(rel1)
                coverage_by_covered[str(target_ref.id)].append(rel1)

            # Coverage 2: Target covering for source (on source's week)
            is_active2 = swap.source_week == date_param
            status2 = CoverageStatus.ACTIVE if is_active2 else CoverageStatus.SCHEDULED

            rel2 = CoverageRelationship(
                id=f"swap-{swap.id}-tgt",
                covering_person=target_ref,
                covered_person=source_ref,
                coverage_type=CoverageType.SWAP_EXCHANGE,
                status=status2,
                start_date=swap.source_week,
                end_date=swap.source_week,
                location=None,
                reason=swap.reason,
                swap_id=swap.id,
            )

            if is_active2:
                active_coverage.append(rel2)
            elif swap.source_week <= upcoming_end:
                upcoming_coverage.append(rel2)

            coverage_by_coverer[str(target_ref.id)].append(rel2)
            coverage_by_covered[str(source_ref.id)].append(rel2)

    # === 2. Remote Surrogate Coverage ===
    # Find assignments at remote locations for the date range
    remote_assignments = (
        db.query(Assignment)
        .join(Block, Assignment.block_id == Block.id)
        .join(Person, Assignment.person_id == Person.id)
        .options(
            joinedload(Assignment.person),
            joinedload(Assignment.rotation_template),
        )
        .filter(Block.date >= date_param)
        .filter(Block.date <= upcoming_end)
        .all()
    )

    # Track people at remote locations
    remote_people_by_date: dict[date, list[tuple[Person, str]]] = defaultdict(list)

    for assignment in remote_assignments:
        if (
            assignment.rotation_template
            and assignment.rotation_template.clinic_location
        ):
            loc = assignment.rotation_template.clinic_location
            if loc in REMOTE_LOCATIONS:
                block_date = assignment.block.date
                remote_people_by_date[block_date].append((assignment.person, loc))

    # For each person at remote location, create surrogate relationship if one exists
    # Note: Surrogates would typically be assigned via a separate mechanism
    # For now, we just show who is remote (surrogate can be added later)
    for block_date, remote_list in remote_people_by_date.items():
        seen_ids = set()
        for person, location in remote_list:
            if person.id in seen_ids:
                continue
            seen_ids.add(person.id)

            is_active = block_date == date_param

            # Create a coverage record showing remote assignment
            # Surrogate could be populated from a dedicated surrogate table
            relationship = CoverageRelationship(
                id=f"remote-{person.id}-{block_date}",
                covering_person=PersonRef(
                    id=uuid4(),  # Placeholder - no surrogate assigned yet
                    name="(Surrogate TBD)",
                    pgy_level=None,
                    role_type=None,
                ),
                covered_person=_person_to_ref(person),
                coverage_type=CoverageType.REMOTE_SURROGATE,
                status=CoverageStatus.ACTIVE if is_active else CoverageStatus.SCHEDULED,
                start_date=block_date,
                end_date=block_date,
                location=location,
                reason=f"Remote assignment at {location}",
                swap_id=None,
            )

            if is_active:
                active_coverage.append(relationship)
            else:
                upcoming_coverage.append(relationship)

    # === 3. Backup Call Coverage ===
    backup_calls = (
        db.query(CallAssignment)
        .options(joinedload(CallAssignment.person))
        .filter(CallAssignment.date >= date_param)
        .filter(CallAssignment.date <= upcoming_end)
        .filter(CallAssignment.call_type == "backup")
        .all()
    )

    for call in backup_calls:
        is_active = call.date == date_param

        # Find the primary call person for this date
        primary_call = (
            db.query(CallAssignment)
            .options(joinedload(CallAssignment.person))
            .filter(CallAssignment.date == call.date)
            .filter(CallAssignment.call_type.in_(["weekday", "sunday"]))
            .first()
        )

        if primary_call:
            relationship = CoverageRelationship(
                id=f"backup-{call.id}",
                covering_person=_person_to_ref(call.person),
                covered_person=_person_to_ref(primary_call.person),
                coverage_type=CoverageType.BACKUP_CALL,
                status=CoverageStatus.ACTIVE if is_active else CoverageStatus.SCHEDULED,
                start_date=call.date,
                end_date=call.date,
                location=None,
                reason="Backup call coverage",
                swap_id=None,
            )

            if is_active:
                active_coverage.append(relationship)
            else:
                upcoming_coverage.append(relationship)

            coverage_by_coverer[str(call.person.id)].append(relationship)
            coverage_by_covered[str(primary_call.person.id)].append(relationship)

    # === 4. Absence Coverage ===
    # Find people with absences and any coverage assignments
    absences_in_range = (
        db.query(Absence)
        .options(joinedload(Absence.person))
        .filter(Absence.start_date <= upcoming_end)
        .filter(Absence.end_date >= date_param)
        .all()
    )

    for absence in absences_in_range:
        is_active = absence.start_date <= date_param <= absence.end_date

        # Coverage for absence would need to be matched with a replacement
        # For now, create placeholder showing the absence
        relationship = CoverageRelationship(
            id=f"absence-{absence.id}",
            covering_person=PersonRef(
                id=uuid4(),  # Placeholder - no coverage assigned yet
                name="(Coverage TBD)",
                pgy_level=None,
                role_type=None,
            ),
            covered_person=_person_to_ref(absence.person),
            coverage_type=CoverageType.ABSENCE_COVERAGE,
            status=CoverageStatus.ACTIVE if is_active else CoverageStatus.SCHEDULED,
            start_date=absence.start_date,
            end_date=absence.end_date,
            location=None,
            reason=f"Absence: {absence.absence_type}",
            swap_id=None,
        )

        if is_active:
            active_coverage.append(relationship)
        else:
            upcoming_coverage.append(relationship)

    # === Build Statistics ===
    type_counts = Counter(r.coverage_type for r in active_coverage)
    by_type = CoverageCountByType(
        remote_surrogate=type_counts.get(CoverageType.REMOTE_SURROGATE, 0),
        swap_absorb=type_counts.get(CoverageType.SWAP_ABSORB, 0),
        swap_exchange=type_counts.get(CoverageType.SWAP_EXCHANGE, 0),
        backup_call=type_counts.get(CoverageType.BACKUP_CALL, 0),
        absence_coverage=type_counts.get(CoverageType.ABSENCE_COVERAGE, 0),
        temporary_proxy=type_counts.get(CoverageType.TEMPORARY_PROXY, 0),
    )

    # Count coverage per person (as coverer)
    coverer_counts = Counter(str(r.covering_person.id) for r in active_coverage)
    covered_counts = Counter(str(r.covered_person.id) for r in active_coverage)

    # Build top coverers
    top_coverers: list[TopCoverer] = []
    for person_id, count in coverer_counts.most_common(5):
        # Find person info from any relationship
        for rel in active_coverage:
            if str(rel.covering_person.id) == person_id:
                top_coverers.append(TopCoverer(person=rel.covering_person, count=count))
                break

    # Build most covered
    most_covered: list[TopCoverer] = []
    for person_id, count in covered_counts.most_common(5):
        for rel in active_coverage:
            if str(rel.covered_person.id) == person_id:
                most_covered.append(TopCoverer(person=rel.covered_person, count=count))
                break

    stats = CoverageStats(
        total_active=len(active_coverage),
        total_scheduled=len(upcoming_coverage),
        by_type=by_type,
        top_coverers=top_coverers,
        most_covered=most_covered,
    )

    # === Build by_coverer summaries ===
    # Get unique coverers from active coverage
    person_map: dict[str, PersonRef] = {}
    for rel in active_coverage + upcoming_coverage:
        person_map[str(rel.covering_person.id)] = rel.covering_person
        person_map[str(rel.covered_person.id)] = rel.covered_person

    by_coverer: list[PersonCoverageSummary] = []
    seen_coverers = set()

    for rel in active_coverage + upcoming_coverage:
        coverer_id = str(rel.covering_person.id)
        if (
            coverer_id not in seen_coverers
            and rel.covering_person.name != "(Surrogate TBD)"
            and rel.covering_person.name != "(Coverage TBD)"
        ):
            seen_coverers.add(coverer_id)
            providing = [
                r
                for r in active_coverage + upcoming_coverage
                if str(r.covering_person.id) == coverer_id
            ]
            receiving = [
                r
                for r in active_coverage + upcoming_coverage
                if str(r.covered_person.id) == coverer_id
            ]
            by_coverer.append(
                PersonCoverageSummary(
                    person=rel.covering_person,
                    providing=providing,
                    receiving=receiving,
                )
            )

    # Sort by number of coverage relationships (providing + receiving)
    by_coverer.sort(key=lambda s: len(s.providing) + len(s.receiving), reverse=True)

    return ProxyCoverageResponse(
        coverage_date=date_param,
        active_coverage=active_coverage,
        upcoming_coverage=upcoming_coverage,
        by_coverer=by_coverer,
        stats=stats,
        generated_at=datetime.utcnow(),
    )
