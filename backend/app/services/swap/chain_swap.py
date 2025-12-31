"""
Multi-party chain swap coordination.

Handles complex swap scenarios where more than two faculty members
are involved in a circular or chain swap pattern.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.swap import SwapRecord, SwapStatus, SwapType
from app.models.person import Person


logger = logging.getLogger(__name__)


@dataclass
class ChainNode:
    """Node in a swap chain."""

    faculty_id: UUID
    faculty_name: str
    gives_week: date
    receives_week: date
    swap_request_id: UUID | None = None


@dataclass
class SwapChain:
    """Represents a chain of connected swaps."""

    chain_id: str
    nodes: list[ChainNode]
    chain_type: str  # "cycle", "linear", "tree"
    total_swaps: int
    is_valid: bool
    validation_errors: list[str]


@dataclass
class ChainDiscoveryResult:
    """Result of chain discovery."""

    chains_found: list[SwapChain]
    total_participants: int
    execution_plan: list[dict[str, Any]]


class ChainSwapCoordinator:
    """
    Coordinates multi-party chain swaps.

    Uses graph algorithms to discover chains and cycles in swap
    requests, enabling complex multi-way swaps.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize chain swap coordinator.

        Args:
            db: Async database session
        """
        self.db = db

    async def discover_chains(
        self,
        max_chain_length: int = 5,
    ) -> ChainDiscoveryResult:
        """
        Discover all possible swap chains from pending requests.

        Args:
            max_chain_length: Maximum number of participants in a chain

        Returns:
            ChainDiscoveryResult with discovered chains
        """
        # Get all pending swap requests
        result = await self.db.execute(
            select(SwapRecord).where(SwapRecord.status == SwapStatus.PENDING)
        )
        pending_requests = list(result.scalars().all())

        if not pending_requests:
            return ChainDiscoveryResult(
                chains_found=[],
                total_participants=0,
                execution_plan=[],
            )

        # Build directed graph of swap preferences
        graph = nx.DiGraph()

        for request in pending_requests:
            # Add edge: source_faculty -> target_faculty for their desired swap
            if request.target_faculty_id:
                graph.add_edge(
                    str(request.source_faculty_id),
                    str(request.target_faculty_id),
                    swap_id=str(request.id),
                    source_week=request.source_week,
                    target_week=request.target_week,
                )

        # Find cycles (most valuable chain type)
        chains = []

        # Find all simple cycles
        try:
            cycles = list(nx.simple_cycles(graph))
        except Exception as e:
            logger.warning(f"Error finding cycles: {e}")
            cycles = []

        for cycle in cycles:
            if len(cycle) > max_chain_length:
                continue

            # Build chain from cycle
            chain = await self._build_chain_from_cycle(cycle, graph, pending_requests)
            if chain and chain.is_valid:
                chains.append(chain)

        # Also find linear chains (A->B->C but not back to A)
        linear_chains = self._find_linear_chains(graph, max_chain_length)
        for lc in linear_chains:
            chain = await self._build_chain_from_path(lc, graph, pending_requests)
            if chain and chain.is_valid:
                chains.append(chain)

        # Generate execution plan
        execution_plan = self._create_execution_plan(chains)

        total_participants = sum(len(chain.nodes) for chain in chains)

        return ChainDiscoveryResult(
            chains_found=chains,
            total_participants=total_participants,
            execution_plan=execution_plan,
        )

    async def execute_chain(
        self,
        chain: SwapChain,
        executed_by_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Execute a complete swap chain atomically.

        Args:
            chain: The swap chain to execute
            executed_by_id: User executing the chain

        Returns:
            Execution result dictionary
        """
        if not chain.is_valid:
            return {
                "success": False,
                "error": "Cannot execute invalid chain",
                "validation_errors": chain.validation_errors,
            }

        try:
            # Execute all swaps in the chain atomically
            executed_swaps = []

            for i, node in enumerate(chain.nodes):
                next_node = chain.nodes[(i + 1) % len(chain.nodes)]

                # Create or update swap record
                if node.swap_request_id:
                    # Update existing request
                    result = await self.db.execute(
                        select(SwapRecord).where(SwapRecord.id == node.swap_request_id)
                    )
                    swap = result.scalar_one_or_none()

                    if swap:
                        swap.status = SwapStatus.EXECUTED
                        swap.executed_at = datetime.utcnow()
                        swap.executed_by_id = executed_by_id
                        executed_swaps.append(str(swap.id))

            await self.db.commit()

            logger.info(
                f"Successfully executed chain {chain.chain_id} "
                f"with {len(chain.nodes)} participants"
            )

            return {
                "success": True,
                "chain_id": chain.chain_id,
                "participants": len(chain.nodes),
                "executed_swaps": executed_swaps,
            }

        except Exception as e:
            await self.db.rollback()
            logger.exception(f"Failed to execute chain {chain.chain_id}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def validate_chain(self, chain: SwapChain) -> tuple[bool, list[str]]:
        """
        Validate that a swap chain can be executed.

        Args:
            chain: The swap chain to validate

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Check minimum participants
        if len(chain.nodes) < 2:
            errors.append("Chain must have at least 2 participants")

        # Verify chain closure (for cycles)
        if chain.chain_type == "cycle":
            first_node = chain.nodes[0]
            last_node = chain.nodes[-1]

            if last_node.receives_week != first_node.gives_week:
                errors.append("Cycle does not close properly")

        # Check for conflicting weeks
        weeks_in_use = set()
        for node in chain.nodes:
            if node.gives_week in weeks_in_use:
                errors.append(f"Week {node.gives_week} used multiple times")
            weeks_in_use.add(node.gives_week)

        # Validate each faculty member can do the swap
        for node in chain.nodes:
            faculty = await self._get_faculty(node.faculty_id)
            if not faculty:
                errors.append(f"Faculty {node.faculty_id} not found")

        return len(errors) == 0, errors

    # ===== Private Helper Methods =====

    async def _build_chain_from_cycle(
        self,
        cycle: list[str],
        graph: nx.DiGraph,
        requests: list[SwapRecord],
    ) -> SwapChain | None:
        """Build a SwapChain object from a cycle."""
        nodes = []

        for i, faculty_id_str in enumerate(cycle):
            next_faculty_id_str = cycle[(i + 1) % len(cycle)]

            # Find the swap request edge
            edge_data = graph.get_edge_data(faculty_id_str, next_faculty_id_str)

            if not edge_data:
                return None

            faculty_id = UUID(faculty_id_str)
            faculty = await self._get_faculty(faculty_id)

            if not faculty:
                return None

            node = ChainNode(
                faculty_id=faculty_id,
                faculty_name=faculty.name,
                gives_week=edge_data["source_week"],
                receives_week=edge_data["target_week"] or edge_data["source_week"],
                swap_request_id=UUID(edge_data["swap_id"]) if edge_data.get("swap_id") else None,
            )

            nodes.append(node)

        chain = SwapChain(
            chain_id=f"cycle_{datetime.utcnow().timestamp()}",
            nodes=nodes,
            chain_type="cycle",
            total_swaps=len(nodes),
            is_valid=True,
            validation_errors=[],
        )

        # Validate the chain
        is_valid, errors = await self.validate_chain(chain)
        chain.is_valid = is_valid
        chain.validation_errors = errors

        return chain

    async def _build_chain_from_path(
        self,
        path: list[str],
        graph: nx.DiGraph,
        requests: list[SwapRecord],
    ) -> SwapChain | None:
        """Build a SwapChain object from a linear path."""
        nodes = []

        for i in range(len(path) - 1):
            faculty_id_str = path[i]
            next_faculty_id_str = path[i + 1]

            edge_data = graph.get_edge_data(faculty_id_str, next_faculty_id_str)

            if not edge_data:
                return None

            faculty_id = UUID(faculty_id_str)
            faculty = await self._get_faculty(faculty_id)

            if not faculty:
                return None

            node = ChainNode(
                faculty_id=faculty_id,
                faculty_name=faculty.name,
                gives_week=edge_data["source_week"],
                receives_week=edge_data["target_week"] or edge_data["source_week"],
                swap_request_id=UUID(edge_data["swap_id"]) if edge_data.get("swap_id") else None,
            )

            nodes.append(node)

        chain = SwapChain(
            chain_id=f"linear_{datetime.utcnow().timestamp()}",
            nodes=nodes,
            chain_type="linear",
            total_swaps=len(nodes),
            is_valid=True,
            validation_errors=[],
        )

        is_valid, errors = await self.validate_chain(chain)
        chain.is_valid = is_valid
        chain.validation_errors = errors

        return chain

    def _find_linear_chains(
        self,
        graph: nx.DiGraph,
        max_length: int,
    ) -> list[list[str]]:
        """Find linear chains (non-cyclic paths) in the graph."""
        chains = []

        # Find all simple paths up to max_length
        for source in graph.nodes():
            for target in graph.nodes():
                if source == target:
                    continue

                try:
                    paths = nx.all_simple_paths(
                        graph,
                        source,
                        target,
                        cutoff=max_length,
                    )

                    for path in paths:
                        if len(path) >= 2:  # At least 2 participants
                            chains.append(path)
                except nx.NetworkXNoPath:
                    continue

        return chains

    def _create_execution_plan(
        self,
        chains: list[SwapChain],
    ) -> list[dict[str, Any]]:
        """Create execution plan for discovered chains."""
        plan = []

        # Sort chains by total swaps (larger chains first)
        sorted_chains = sorted(
            chains,
            key=lambda c: c.total_swaps,
            reverse=True,
        )

        for chain in sorted_chains:
            plan.append({
                "chain_id": chain.chain_id,
                "chain_type": chain.chain_type,
                "participants": len(chain.nodes),
                "is_valid": chain.is_valid,
                "priority": "high" if chain.total_swaps >= 4 else "normal",
                "nodes": [
                    {
                        "faculty_id": str(node.faculty_id),
                        "faculty_name": node.faculty_name,
                        "gives": node.gives_week.isoformat(),
                        "receives": node.receives_week.isoformat(),
                    }
                    for node in chain.nodes
                ],
            })

        return plan

    async def _get_faculty(self, faculty_id: UUID) -> Person | None:
        """Get faculty member by ID."""
        result = await self.db.execute(
            select(Person).where(Person.id == faculty_id)
        )
        return result.scalar_one_or_none()
