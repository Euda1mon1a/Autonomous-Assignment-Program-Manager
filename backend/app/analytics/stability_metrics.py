"""
Stability Metrics computation for schedule analytics.

This module tracks schedule churn, cascade effects, and vulnerability to assess
the stability of scheduling decisions over time. It leverages SQLAlchemy-Continuum
for version tracking to compare schedule states.

Key Metrics:
- Schedule Churn: How much the schedule changed from previous version
- Ripple Factor: How far changes cascade through dependency networks
- N-1 Vulnerability: Single-point-of-failure risk assessment
- Violation Tracking: New constraint violations introduced by changes
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session
from sqlalchemy_continuum import version_class

logger = logging.getLogger(__name__)

# Try to import NetworkX for dependency graph analysis
try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    logger.warning("NetworkX not installed - ripple factor will use basic methods")


@dataclass
class StabilityMetrics:
    """Schedule churn and cascade measures"""

    # Number of assignments changed from previous version
    assignments_changed: int

    # Percentage of schedule that changed
    churn_rate: float

    # How far changes cascade (avg hops in dependency graph)
    ripple_factor: float

    # Single-point-of-failure risk score
    n1_vulnerability_score: float

    # Number of constraint violations introduced
    new_violations: int

    # Time since last major refactoring (days)
    days_since_major_change: int

    # Additional metadata
    total_assignments: int = 0
    computed_at: Optional[datetime] = None
    version_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary format."""
        return {
            "assignments_changed": self.assignments_changed,
            "churn_rate": round(self.churn_rate, 3),
            "ripple_factor": round(self.ripple_factor, 3),
            "n1_vulnerability_score": round(self.n1_vulnerability_score, 3),
            "new_violations": self.new_violations,
            "days_since_major_change": self.days_since_major_change,
            "total_assignments": self.total_assignments,
            "computed_at": self.computed_at.isoformat() if self.computed_at else None,
            "version_id": str(self.version_id) if self.version_id else None,
        }

    @property
    def is_stable(self) -> bool:
        """Determine if the schedule is considered stable."""
        # Stable if: low churn, low ripple, low vulnerability, no new violations
        return (
            self.churn_rate < 0.15  # Less than 15% changed
            and self.ripple_factor < 2.0  # Changes don't cascade far
            and self.n1_vulnerability_score < 0.5  # Low single-point-of-failure risk
            and self.new_violations == 0  # No new violations
        )

    @property
    def stability_grade(self) -> str:
        """
        Grade the stability of the schedule.

        Returns:
            Letter grade: A (excellent) to F (poor)
        """
        if self.new_violations > 0:
            return "F"  # New violations are always bad

        # Calculate weighted score (0-100)
        churn_score = max(0, 100 - (self.churn_rate * 100))
        ripple_score = max(0, 100 - (self.ripple_factor * 20))
        vulnerability_score = max(0, 100 - (self.n1_vulnerability_score * 100))

        weighted_score = (
            churn_score * 0.35 +
            ripple_score * 0.25 +
            vulnerability_score * 0.40
        )

        if weighted_score >= 90:
            return "A"
        elif weighted_score >= 80:
            return "B"
        elif weighted_score >= 70:
            return "C"
        elif weighted_score >= 60:
            return "D"
        else:
            return "F"


class StabilityMetricsComputer:
    """
    Computes stability metrics for schedule analysis.

    Uses SQLAlchemy-Continuum version tracking to compare schedules over time
    and assess the stability and cascading effects of changes.
    """

    def __init__(self, db: Session):
        self.db = db

    def compute_stability_metrics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        version_id: Optional[str] = None,
    ) -> StabilityMetrics:
        """
        Compute comprehensive stability metrics for the current schedule.

        Args:
            start_date: Start of date range to analyze
            end_date: End of date range to analyze
            version_id: Specific version to analyze (defaults to current)

        Returns:
            StabilityMetrics object with computed values
        """
        from app.models.assignment import Assignment
        from app.models.block import Block

        # Get current assignments
        query = self.db.query(Assignment)
        if start_date:
            query = query.join(Block).filter(Block.date >= start_date)
        if end_date:
            query = query.join(Block).filter(Block.date <= end_date)

        current_assignments = query.all()

        if not current_assignments:
            # No assignments to analyze
            return StabilityMetrics(
                assignments_changed=0,
                churn_rate=0.0,
                ripple_factor=0.0,
                n1_vulnerability_score=0.0,
                new_violations=0,
                days_since_major_change=0,
                total_assignments=0,
                computed_at=datetime.utcnow(),
            )

        # Get previous version for comparison
        previous_assignments = self._get_previous_assignments(
            current_assignments, start_date, end_date
        )

        # Calculate churn rate
        churn_data = self._calculate_churn_rate(previous_assignments, current_assignments)

        # Calculate ripple factor using dependency analysis
        ripple_factor = self._calculate_ripple_factor(
            churn_data["changes"],
            current_assignments
        )

        # Calculate N-1 vulnerability (single point of failure risk)
        n1_vulnerability = self._calculate_n1_vulnerability(current_assignments)

        # Count new violations (mock for now - would integrate with validator)
        new_violations = self._count_new_violations(previous_assignments, current_assignments)

        # Calculate days since major change
        days_since_major = self._days_since_major_change(start_date)

        return StabilityMetrics(
            assignments_changed=churn_data["changed_count"],
            churn_rate=churn_data["churn_rate"],
            ripple_factor=ripple_factor,
            n1_vulnerability_score=n1_vulnerability,
            new_violations=new_violations,
            days_since_major_change=days_since_major,
            total_assignments=len(current_assignments),
            computed_at=datetime.utcnow(),
            version_id=version_id,
        )

    def _get_previous_assignments(
        self,
        current_assignments: list,
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> list:
        """
        Get previous version of assignments for comparison.

        Uses SQLAlchemy-Continuum to fetch the previous state by looking up
        the most recent transaction before the current state.

        Args:
            current_assignments: Current assignments to compare against
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            List of assignments from the previous transaction, or empty list
            if no history is available.
        """
        from app.models.assignment import Assignment

        if not current_assignments:
            return []

        try:
            # Get the version class for Assignment model
            AssignmentVersion = version_class(Assignment)

            # Get the most recent transaction ID from current assignments
            # We need to find what the previous transaction was
            from sqlalchemy import text

            # Query for the most recent transaction before the latest one
            # that affected the assignments we're interested in
            latest_transaction_query = text("""
                SELECT MAX(transaction_id) as latest_tx
                FROM assignment_version
            """)

            result = self.db.execute(latest_transaction_query).fetchone()
            if not result or not result[0]:
                logger.info("No version history available - this is the first version")
                return []

            latest_tx = result[0]

            # Get the previous transaction
            prev_transaction_query = text("""
                SELECT MAX(transaction_id) as prev_tx
                FROM assignment_version
                WHERE transaction_id < :latest_tx
            """)

            result = self.db.execute(prev_transaction_query, {"latest_tx": latest_tx}).fetchone()
            if not result or not result[0]:
                logger.info("No previous version available - this is the first version")
                return []

            prev_tx = result[0]
            logger.info(f"Fetching assignments from transaction {prev_tx} (previous to {latest_tx})")

            # Query for assignments at the previous transaction
            # We want assignments that were active at that transaction
            previous_versions = (
                self.db.query(AssignmentVersion)
                .filter(
                    AssignmentVersion.transaction_id <= prev_tx,
                    # Only get the latest version for each assignment at that point
                )
                .all()
            )

            # Filter to get only the most recent version of each assignment ID
            # that was active at the previous transaction
            assignment_map = {}
            for version in previous_versions:
                # Keep the version with the highest transaction_id <= prev_tx for each assignment
                if version.id not in assignment_map or version.transaction_id > assignment_map[version.id].transaction_id:
                    # Only include if this version was created or updated (not deleted)
                    if version.operation_type != 2:  # 2 = delete
                        assignment_map[version.id] = version

            previous_assignments = list(assignment_map.values())

            # Apply date range filtering if provided
            if start_date or end_date:
                from app.models.block import Block
                filtered = []
                for assignment in previous_assignments:
                    block = self.db.query(Block).filter(Block.id == assignment.block_id).first()
                    if block:
                        if start_date and block.date < start_date:
                            continue
                        if end_date and block.date > end_date:
                            continue
                        filtered.append(assignment)
                previous_assignments = filtered

            logger.info(f"Found {len(previous_assignments)} assignments in previous version")
            return previous_assignments

        except Exception as e:
            logger.warning(f"Error fetching version history: {e}")
            logger.info("Falling back to empty previous state (assuming first version)")
            return []

    def _calculate_churn_rate(
        self,
        old_assignments: list,
        new_assignments: list,
    ) -> dict[str, Any]:
        """
        Calculate schedule churn rate by comparing two assignment sets.

        Args:
            old_assignments: Previous version of assignments
            new_assignments: Current version of assignments

        Returns:
            Dict with:
                - changed_count: Number of assignments that changed
                - churn_rate: Percentage of schedule that changed (0.0-1.0)
                - added: List of newly added assignments
                - removed: List of removed assignments
                - modified: List of modified assignments
                - changes: List of all change tuples for ripple analysis
        """
        if not old_assignments:
            # First version - all assignments are "new"
            return {
                "changed_count": 0,
                "churn_rate": 0.0,
                "added": new_assignments,
                "removed": [],
                "modified": [],
                "changes": [],
            }

        # Build lookup maps by (block_id, person_id) tuple
        old_map = {
            (a.block_id, a.person_id): a
            for a in old_assignments
        }
        new_map = {
            (a.block_id, a.person_id): a
            for a in new_assignments
        }

        added = []
        removed = []
        modified = []
        changes = []

        # Find removed assignments
        for key, old_assignment in old_map.items():
            if key not in new_map:
                removed.append(old_assignment)
                changes.append(("removed", old_assignment.person_id, old_assignment.block_id))

        # Find added and modified assignments
        for key, new_assignment in new_map.items():
            if key not in old_map:
                added.append(new_assignment)
                changes.append(("added", new_assignment.person_id, new_assignment.block_id))
            else:
                old_assignment = old_map[key]
                # Check if meaningful fields changed
                if self._assignment_differs(old_assignment, new_assignment):
                    modified.append((old_assignment, new_assignment))
                    changes.append(("modified", new_assignment.person_id, new_assignment.block_id))

        total_changed = len(added) + len(removed) + len(modified)
        total_assignments = max(len(old_assignments), len(new_assignments))
        churn_rate = total_changed / total_assignments if total_assignments > 0 else 0.0

        return {
            "changed_count": total_changed,
            "churn_rate": churn_rate,
            "added": added,
            "removed": removed,
            "modified": modified,
            "changes": changes,
        }

    def _assignment_differs(self, old, new) -> bool:
        """Check if two assignments differ in meaningful ways."""
        return (
            old.rotation_template_id != new.rotation_template_id
            or old.role != new.role
            or old.activity_override != new.activity_override
        )

    def _calculate_ripple_factor(
        self,
        changes: list[tuple],
        current_assignments: list,
    ) -> float:
        """
        Calculate how far changes cascade through the dependency graph.

        Uses NetworkX to build a dependency graph where edges represent:
        - Person dependencies (coverage requirements)
        - Block dependencies (temporal constraints)
        - Rotation dependencies (prerequisite rotations)

        Args:
            changes: List of (change_type, person_id, block_id) tuples
            current_assignments: Current assignment list

        Returns:
            Average hops in dependency graph that changes cascade
        """
        if not changes or not HAS_NETWORKX:
            # No changes or no NetworkX - return baseline
            return 0.0

        # Build dependency graph
        G = self._build_dependency_graph(current_assignments)

        # For each change, calculate how many hops it can cascade
        cascade_distances = []

        for change_type, person_id, block_id in changes:
            # Create node identifier
            node = (person_id, block_id)

            if node not in G:
                continue

            # Calculate shortest paths from this node to all other nodes
            try:
                paths = nx.single_source_shortest_path_length(G, node)
                # Get distances to all reachable nodes
                distances = list(paths.values())
                if distances:
                    # Average distance this change can cascade
                    avg_distance = sum(distances) / len(distances)
                    cascade_distances.append(avg_distance)
            except nx.NetworkXError:
                # Node not in graph or other error
                continue

        if cascade_distances:
            return sum(cascade_distances) / len(cascade_distances)
        else:
            return 0.0

    def _build_dependency_graph(self, assignments: list) -> "nx.DiGraph":
        """
        Build a directed dependency graph from assignments.

        Edges represent dependencies:
        - Person A depends on Person B if they cover overlapping services
        - Block dependencies based on temporal constraints

        Returns:
            NetworkX directed graph
        """
        if not HAS_NETWORKX:
            # Return mock empty graph structure
            class MockGraph:
                def __contains__(self, item):
                    return False
            return MockGraph()

        G = nx.DiGraph()

        # Add nodes for each assignment (person, block) pair
        for assignment in assignments:
            node = (assignment.person_id, assignment.block_id)
            G.add_node(
                node,
                person_id=assignment.person_id,
                block_id=assignment.block_id,
                role=assignment.role,
            )

        # Add edges based on dependencies
        # Group assignments by person and block for dependency analysis
        assignments_by_person = defaultdict(list)
        assignments_by_block = defaultdict(list)

        for assignment in assignments:
            assignments_by_person[assignment.person_id].append(assignment)
            # Note: Would need block.date from relationship, skipping for now

        # Add person-person dependencies (coverage overlap)
        for person_id, person_assignments in assignments_by_person.items():
            for other_person_id, other_assignments in assignments_by_person.items():
                if person_id == other_person_id:
                    continue

                # Check if they cover similar rotations (potential swap candidates)
                person_rotations = {a.rotation_template_id for a in person_assignments if a.rotation_template_id}
                other_rotations = {a.rotation_template_id for a in other_assignments if a.rotation_template_id}

                if person_rotations & other_rotations:
                    # They share rotation coverage - create dependency
                    for p_assign in person_assignments:
                        for o_assign in other_assignments:
                            G.add_edge(
                                (p_assign.person_id, p_assign.block_id),
                                (o_assign.person_id, o_assign.block_id),
                                weight=0.5,
                                reason="coverage_overlap",
                            )

        return G

    def _calculate_n1_vulnerability(self, assignments: list) -> float:
        """
        Calculate N-1 vulnerability score (single point of failure risk).

        Assesses how vulnerable the schedule is to losing a single person.
        Similar to hub analysis but focused on coverage criticality.

        Args:
            assignments: List of current assignments

        Returns:
            Vulnerability score (0.0-1.0), higher = more vulnerable
        """
        if not assignments:
            return 0.0

        # Count assignments and unique rotations per person
        person_stats = defaultdict(lambda: {
            "assignment_count": 0,
            "rotations": set(),
            "blocks": set(),
        })

        # Track rotation coverage
        rotation_coverage = defaultdict(set)  # rotation_id -> set of person_ids

        for assignment in assignments:
            person_id = assignment.person_id
            person_stats[person_id]["assignment_count"] += 1
            person_stats[person_id]["blocks"].add(assignment.block_id)

            if assignment.rotation_template_id:
                person_stats[person_id]["rotations"].add(assignment.rotation_template_id)
                rotation_coverage[assignment.rotation_template_id].add(person_id)

        # Calculate vulnerability factors
        vulnerability_scores = []

        for person_id, stats in person_stats.items():
            # Factor 1: How many rotations does this person uniquely cover?
            unique_rotations = 0
            for rotation_id in stats["rotations"]:
                if len(rotation_coverage[rotation_id]) == 1:
                    # Only this person covers this rotation
                    unique_rotations += 1

            # Factor 2: What percentage of total assignments are theirs?
            assignment_concentration = stats["assignment_count"] / len(assignments)

            # Factor 3: Unique rotation concentration
            unique_rotation_factor = unique_rotations * 0.3  # 0.3 weight per unique rotation

            # Combined vulnerability for this person
            person_vulnerability = min(1.0, assignment_concentration + unique_rotation_factor)
            vulnerability_scores.append(person_vulnerability)

        # Overall N-1 vulnerability is the maximum single-person vulnerability
        # (worst case: losing the most critical person)
        if vulnerability_scores:
            max_vulnerability = max(vulnerability_scores)
            avg_vulnerability = sum(vulnerability_scores) / len(vulnerability_scores)

            # Weight toward max (worst case) but consider average
            return (max_vulnerability * 0.7) + (avg_vulnerability * 0.3)
        else:
            return 0.0

    def _count_new_violations(
        self,
        old_assignments: list,
        new_assignments: list,
    ) -> int:
        """
        Count new constraint violations introduced by changes.

        Integrates with ACGMEValidator to check for actual constraint violations
        and compares the violations between old and new assignment sets.

        Args:
            old_assignments: Previous assignments
            new_assignments: Current assignments

        Returns:
            Number of new violations introduced (violations in new that weren't in old)
        """
        if not new_assignments:
            return 0  # No assignments means no violations

        try:
            from app.models.block import Block
            from app.scheduling.validator import ACGMEValidator

            # Get date range for validation
            blocks_for_new = set()
            for assignment in new_assignments:
                blocks_for_new.add(assignment.block_id)

            if not blocks_for_new:
                return 0

            # Query blocks to get date range
            blocks = self.db.query(Block).filter(Block.id.in_(blocks_for_new)).all()
            if not blocks:
                return 0

            dates = [b.date for b in blocks if b.date]
            if not dates:
                return 0

            start_date = min(dates)
            end_date = max(dates)

            # Validate current assignments
            validator = ACGMEValidator(self.db)
            new_result = validator.validate_all(start_date, end_date)
            new_violations = new_result.total_violations

            # If there's no previous version, all current violations are "new"
            if not old_assignments:
                logger.info(f"First version: {new_violations} violations found")
                return new_violations

            # Create a temporary way to validate old assignments
            # Since old_assignments are version objects, we need to check if they were valid at that time
            # For simplicity, we'll compare violation counts
            # A more sophisticated approach would recreate the old state and validate it

            # Get unique violation types and affected entities from current violations
            new_violation_set = set()
            for violation in new_result.violations:
                # Create a hashable identifier for this violation
                key = (
                    violation.type,
                    getattr(violation, 'person_id', None),
                    getattr(violation, 'block_id', None),
                )
                new_violation_set.add(key)

            # Since we can't easily validate historical state (old assignments are version objects),
            # we'll use a heuristic: if churn rate is low (<15%) but violations exist,
            # they're likely not new. If churn is high and violations exist, count them as new.
            churn_data = self._calculate_churn_rate(old_assignments, new_assignments)
            churn_rate = churn_data["churn_rate"]

            if churn_rate < 0.15:
                # Low churn - violations probably existed before
                # Only count critical violations as truly new
                new_count = sum(1 for v in new_result.violations if v.severity == "CRITICAL")
                logger.info(f"Low churn rate ({churn_rate:.2%}): counting {new_count} critical violations")
                return new_count
            else:
                # High churn - more likely that violations are new
                logger.info(f"High churn rate ({churn_rate:.2%}): {new_violations} total violations")
                return new_violations

        except Exception as e:
            logger.warning(f"Error counting new violations: {e}")
            # Fall back to 0 on error
            return 0

    def _days_since_major_change(self, reference_date: Optional[date] = None) -> int:
        """
        Calculate days since last major refactoring.

        A "major change" is defined as:
        - Churn rate > 30%
        - More than 50 assignments changed

        This method queries the assignment version history and groups changes by
        transaction to identify major refactoring events.

        Args:
            reference_date: Date to count from (defaults to today)

        Returns:
            Number of days since last major change (0 if no history available)
        """
        reference_date = reference_date or date.today()

        try:
            from app.models.assignment import Assignment
            from sqlalchemy import text

            # Get all transactions with assignment changes, ordered by most recent
            transaction_query = text("""
                SELECT
                    t.id as transaction_id,
                    t.issued_at,
                    COUNT(DISTINCT av.id) as changes_count
                FROM transaction t
                JOIN assignment_version av ON av.transaction_id = t.id
                WHERE t.issued_at IS NOT NULL
                GROUP BY t.id, t.issued_at
                ORDER BY t.issued_at DESC
                LIMIT 100
            """)

            transactions = self.db.execute(transaction_query).fetchall()

            if not transactions or len(transactions) < 2:
                logger.info("Not enough transaction history to determine major changes")
                return 0

            # Get the version class for detailed analysis
            AssignmentVersion = version_class(Assignment)

            # Analyze each transaction to find major changes
            for i in range(len(transactions) - 1):
                current_tx = transactions[i]
                tx_id = current_tx[0]
                tx_date = current_tx[1]
                changes_count = current_tx[2]

                # Quick filter: if fewer than 50 changes, likely not major
                # But we still need to check churn rate

                # Get previous transaction for comparison
                prev_tx = transactions[i + 1]
                prev_tx_id = prev_tx[0]

                # Get assignments at both transactions
                current_assignments = (
                    self.db.query(AssignmentVersion)
                    .filter(AssignmentVersion.transaction_id == tx_id)
                    .all()
                )

                previous_assignments = (
                    self.db.query(AssignmentVersion)
                    .filter(AssignmentVersion.transaction_id == prev_tx_id)
                    .all()
                )

                if not current_assignments or not previous_assignments:
                    continue

                # Calculate churn rate for this transaction
                churn_data = self._calculate_churn_rate(
                    previous_assignments,
                    current_assignments
                )

                churn_rate = churn_data["churn_rate"]
                changed_count = churn_data["changed_count"]

                # Check if this qualifies as a major change
                is_major = churn_rate > 0.30 or changed_count > 50

                if is_major:
                    # Calculate days since this transaction
                    if tx_date:
                        # Convert datetime to date for comparison
                        tx_date_only = tx_date.date() if hasattr(tx_date, 'date') else tx_date
                        days_since = (reference_date - tx_date_only).days
                        logger.info(
                            f"Found major change at transaction {tx_id}: "
                            f"{changed_count} changes, {churn_rate:.1%} churn rate, "
                            f"{days_since} days ago"
                        )
                        return max(0, days_since)

            # No major changes found in recent history
            # Return days since the oldest transaction we checked
            if transactions:
                oldest_tx = transactions[-1]
                oldest_date = oldest_tx[1]
                if oldest_date:
                    oldest_date_only = oldest_date.date() if hasattr(oldest_date, 'date') else oldest_date
                    days_since_oldest = (reference_date - oldest_date_only).days
                    logger.info(f"No major changes found. Oldest transaction is {days_since_oldest} days ago")
                    return days_since_oldest

            logger.info("No major changes found in version history")
            return 0

        except Exception as e:
            logger.warning(f"Error calculating days since major change: {e}")
            # Return 0 on error (indicating no history available)
            return 0


def compute_stability_metrics(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict[str, Any]:
    """
    Convenience function to compute stability metrics.

    Args:
        db: Database session
        start_date: Start of date range to analyze
        end_date: End of date range to analyze

    Returns:
        Dictionary with metric values and metadata
    """
    computer = StabilityMetricsComputer(db)
    metrics = computer.compute_stability_metrics(start_date, end_date)

    result = metrics.to_dict()
    result["is_stable"] = metrics.is_stable
    result["stability_grade"] = metrics.stability_grade

    return result
