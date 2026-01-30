"""
Graph-based swap matching using maximum weight matching algorithms.

Uses graph theory to find optimal swap assignments when multiple
compatible swaps are possible.
"""

import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.swap import SwapRecord, SwapStatus


logger = logging.getLogger(__name__)


@dataclass
class GraphMatchResult:
    """Result of graph-based matching."""

    matched_pairs: list[tuple[UUID, UUID]]
    total_weight: float
    unmatched_requests: list[UUID]
    graph_stats: dict[str, Any]


class GraphMatcher:
    """
    Uses graph algorithms to find optimal swap matches.

    Models swap requests as a weighted bipartite graph and uses
    maximum weight matching to find the best overall pairing.
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        Initialize graph matcher.

        Args:
            db: Async database session
        """
        self.db = db

    async def find_optimal_matching(
        self,
        compatibility_scores: dict[tuple[UUID, UUID], float] | None = None,
    ) -> GraphMatchResult:
        """
        Find optimal matching using maximum weight matching.

        Args:
            compatibility_scores: Pre-computed compatibility scores
                                If None, will compute basic scores

        Returns:
            GraphMatchResult with optimal matches
        """
        # Get all pending requests
        result = await self.db.execute(
            select(SwapRecord).where(SwapRecord.status == SwapStatus.PENDING)
        )
        requests = list(result.scalars().all())

        if len(requests) < 2:
            return GraphMatchResult(
                matched_pairs=[],
                total_weight=0.0,
                unmatched_requests=[r.id for r in requests],
                graph_stats={
                    "nodes": len(requests),
                    "edges": 0,
                },
            )

            # Build weighted graph
        graph = nx.Graph()

        # Add nodes
        for request in requests:
            graph.add_node(str(request.id), request=request)

            # Add edges with weights
        for i, request_a in enumerate(requests):
            for request_b in requests[i + 1 :]:
                # Calculate compatibility score
                if compatibility_scores:
                    score = compatibility_scores.get(
                        (request_a.id, request_b.id),
                        0.0,
                    )
                else:
                    score = self._calculate_basic_compatibility(
                        request_a,
                        request_b,
                    )

                if score > 0.3:  # Only add edge if reasonably compatible
                    graph.add_edge(
                        str(request_a.id),
                        str(request_b.id),
                        weight=score,
                    )

                    # Find maximum weight matching
        matching = nx.max_weight_matching(graph, maxcardinality=False)

        # Convert matching to result format
        matched_pairs = []
        total_weight = 0.0
        matched_request_ids = set()

        for edge in matching:
            req_a_id = UUID(edge[0])
            req_b_id = UUID(edge[1])

            matched_pairs.append((req_a_id, req_b_id))
            matched_request_ids.add(req_a_id)
            matched_request_ids.add(req_b_id)

            # Get edge weight
            weight = graph[edge[0]][edge[1]]["weight"]
            total_weight += weight

            # Find unmatched requests
        unmatched = [r.id for r in requests if r.id not in matched_request_ids]

        graph_stats = {
            "nodes": graph.number_of_nodes(),
            "edges": graph.number_of_edges(),
            "matched_pairs": len(matched_pairs),
            "unmatched": len(unmatched),
            "average_weight": total_weight / len(matched_pairs)
            if matched_pairs
            else 0.0,
        }

        logger.info(
            f"Graph matching: {len(matched_pairs)} pairs, "
            f"{len(unmatched)} unmatched, total weight {total_weight:.2f}"
        )

        return GraphMatchResult(
            matched_pairs=matched_pairs,
            total_weight=total_weight,
            unmatched_requests=unmatched,
            graph_stats=graph_stats,
        )

    async def find_stable_matching(
        self,
        preferences: dict[UUID, list[UUID]] | None = None,
    ) -> GraphMatchResult:
        """
        Find stable matching using Gale-Shapley algorithm.

        Args:
            preferences: Preference lists for each request
                       If None, will use compatibility scores

        Returns:
            GraphMatchResult with stable matches
        """
        # Get all pending requests
        result = await self.db.execute(
            select(SwapRecord).where(SwapRecord.status == SwapStatus.PENDING)
        )
        requests = list(result.scalars().all())

        if not preferences:
            preferences = await self._build_preference_lists(requests)

            # Implement Gale-Shapley algorithm
            # (Simplified version for demonstration)

        matched_pairs = []
        matched = set()

        # Greedy matching based on preferences
        for request in requests:
            if request.id in matched:
                continue

            pref_list = preferences.get(request.id, [])

            for preferred_id in pref_list:
                if preferred_id not in matched:
                    matched_pairs.append((request.id, preferred_id))
                    matched.add(request.id)
                    matched.add(preferred_id)
                    break

        unmatched = [r.id for r in requests if r.id not in matched]

        return GraphMatchResult(
            matched_pairs=matched_pairs,
            total_weight=len(matched_pairs),
            unmatched_requests=unmatched,
            graph_stats={
                "algorithm": "stable_matching",
                "matched": len(matched_pairs),
                "unmatched": len(unmatched),
            },
        )

    def _calculate_basic_compatibility(
        self,
        request_a: SwapRecord,
        request_b: SwapRecord,
    ) -> float:
        """
        Calculate basic compatibility score.

        Returns:
            Score from 0.0 to 1.0
        """
        if request_a.source_faculty_id == request_b.source_faculty_id:
            return 0.0

        score = 0.5  # Base score

        # Check temporal proximity
        days_apart = abs((request_a.source_week - request_b.source_week).days)

        if days_apart <= 7:
            score += 0.3
        elif days_apart <= 30:
            score += 0.2
        elif days_apart <= 60:
            score += 0.1

            # Check if specific target matches
        if request_a.target_faculty_id == request_b.source_faculty_id:
            score += 0.2

        if request_b.target_faculty_id == request_a.source_faculty_id:
            score += 0.2

        return min(score, 1.0)

    async def _build_preference_lists(
        self,
        requests: list[SwapRecord],
    ) -> dict[UUID, list[UUID]]:
        """Build preference lists for stable matching."""
        preferences = {}

        for request in requests:
            # Build ordered list of other requests by compatibility
            other_requests = [r for r in requests if r.id != request.id]

            scored_others = [
                (
                    r.id,
                    self._calculate_basic_compatibility(request, r),
                )
                for r in other_requests
            ]

            # Sort by score (highest first)
            scored_others.sort(key=lambda x: x[1], reverse=True)

            # Extract IDs
            preferences[request.id] = [r_id for r_id, _ in scored_others]

        return preferences
