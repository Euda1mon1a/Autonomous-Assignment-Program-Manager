"""
Constraint Rigidity Analysis using the (2,3)-Pebble Game Algorithm.

This module implements a graph-theoretic algorithm to identify rigid, flexible,
and over-constrained regions in scheduling constraint networks. The pebble game
helps detect:
- Rigid regions: Fully constrained (no additional constraints can be added)
- Flexible regions: Under-constrained (degrees of freedom remain)
- Stressed regions: Over-constrained (conflicting constraints, self-stress)

The (2,3)-Pebble Game simulates mechanical rigidity in 2D structures where each
node has 2 degrees of freedom (pebbles) and edges are constraints. A structure
is rigid if |E| ≤ 2|V| - 3 for all subgraphs.

Usage:
    analyzer = ConstraintRigidityAnalyzer()
    graph = analyzer.build_constraint_graph(tasks, constraints)
    result = analyzer.run_pebble_game(graph)
    stressed = analyzer.identify_stressed_regions()
    recommendations = analyzer.recommend_constraint_changes()
"""

from collections import deque
from typing import Any

import networkx as nx


class ConstraintRigidityAnalyzer:
    """
    Analyzes constraint networks using the (2,3)-Pebble Game algorithm.

    The pebble game identifies rigid and flexible components in constraint graphs.
    Each node starts with 2 pebbles representing degrees of freedom. Edges are
    "covered" by moving pebbles between nodes. If an edge cannot be covered,
    it's redundant (over-constrained).

    Attributes:
        graph: The constraint graph being analyzed
        pebbles: Mapping of nodes to their available pebbles
        edge_status: Status of each edge (independent/redundant)
        parent_map: Parent pointers for pebble search paths
    """

    def __init__(self) -> None:
        """Initialize the rigidity analyzer."""
        self.graph: nx.Graph | None = None
        self.pebbles: dict[str, list[str]] = {}  # node -> list of pebble ids
        self.edge_status: dict[
            tuple[str, str], str
        ] = {}  # edge -> "independent" or "redundant"
        self.parent_map: dict[str, str | None] = {}  # for pebble search

    def build_constraint_graph(
        self, tasks: list[dict[str, Any]], constraints: list[dict[str, Any]]
    ) -> nx.Graph:
        """
        Build a constraint graph from tasks and constraints.

        Args:
            tasks: List of task dictionaries with 'id' and optional metadata
            constraints: List of constraint dictionaries with 'type' and 'tasks'

        Returns:
            NetworkX graph where nodes are tasks and edges are constraints

        Example:
            tasks = [
                {'id': 'A', 'type': 'shift'},
                {'id': 'B', 'type': 'shift'}
            ]
            constraints = [
                {'type': 'no_overlap', 'tasks': ['A', 'B']}
            ]
        """
        graph = nx.Graph()

        # Add nodes for each task
        for task in tasks:
            task_id = task["id"]
            graph.add_node(task_id, **{k: v for k, v in task.items() if k != "id"})

        # Add edges for each constraint
        for i, constraint in enumerate(constraints):
            constraint_tasks = constraint.get("tasks", [])
            constraint_type = constraint.get("type", "unknown")

            # Most constraints are binary (between two tasks)
            if len(constraint_tasks) >= 2:
                # For multi-task constraints, create edges between all pairs
                for j in range(len(constraint_tasks)):
                    for k in range(j + 1, len(constraint_tasks)):
                        task_a = constraint_tasks[j]
                        task_b = constraint_tasks[k]

                        if task_a in graph and task_b in graph:
                            # Add edge with constraint metadata
                            graph.add_edge(
                                task_a,
                                task_b,
                                constraint_id=i,
                                constraint_type=constraint_type,
                            )

        self.graph = graph
        return graph

    def run_pebble_game(self, graph: nx.Graph) -> dict[str, Any]:
        """
        Run the (2,3)-Pebble Game algorithm to analyze rigidity.

        Algorithm:
        1. Assign 2 pebbles to each node (representing 2 degrees of freedom)
        2. For each edge (u,v):
           a. Try to find a pebble on u or v
           b. If found, place it on the edge (mark as independent)
           c. If not found, mark edge as redundant (over-constrained)
        3. Count remaining pebbles (degrees of freedom)

        Args:
            graph: NetworkX graph to analyze

        Returns:
            Dictionary with analysis results:
            - total_nodes: Number of nodes
            - total_edges: Number of edges
            - independent_edges: Number of successfully covered edges
            - redundant_edges: Number of uncoverable edges
            - degrees_of_freedom: Number of remaining pebbles
            - is_rigid: Whether graph is rigid (DoF = 0)
            - is_stressed: Whether graph is over-constrained (redundant edges exist)
        """
        self.graph = graph.copy()

        # Initialize: 2 pebbles per node
        self.pebbles = {}
        for node in self.graph.nodes():
            self.pebbles[node] = [f"{node}_p1", f"{node}_p2"]

        self.edge_status = {}
        independent_count = 0
        redundant_count = 0

        # Process each edge
        for u, v in self.graph.edges():
            # Check (2,3)-sparsity condition before trying to add the edge
            # For any subgraph, |E| <= 2|V| - 3
            # Check if adding this edge would violate sparsity in any subgraph
            if self._would_violate_sparsity(u, v):
                self.edge_status[(u, v)] = "redundant"
                redundant_count += 1
            else:
                # Try to find a pebble to cover this edge
                pebble_found = self._find_and_place_pebble(u, v)

                if pebble_found:
                    self.edge_status[(u, v)] = "independent"
                    independent_count += 1
                else:
                    self.edge_status[(u, v)] = "redundant"
                    redundant_count += 1

        # Count remaining pebbles (degrees of freedom)
        total_pebbles = sum(len(pebbles) for pebbles in self.pebbles.values())

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "independent_edges": independent_count,
            "redundant_edges": redundant_count,
            "degrees_of_freedom": total_pebbles,
            "is_rigid": total_pebbles == 0,
            "is_stressed": redundant_count > 0,
        }

    def _would_violate_sparsity(self, u: str, v: str) -> bool:
        """
        Check if adding edge (u,v) would violate (2,3)-sparsity.

        The (2,3)-sparsity condition: for any subgraph with |V'| >= 2,
        |E'| <= 2|V'| - 3

        This method checks all subgraphs reachable from u and v through
        independent edges.

        Args:
            u: First endpoint of candidate edge
            v: Second endpoint of candidate edge

        Returns:
            True if adding this edge would violate sparsity, False otherwise
        """
        # Find the subgraph of nodes connected by independent edges
        # that includes u and v
        connected_nodes = set()
        to_explore = {u, v}

        while to_explore:
            node = to_explore.pop()
            if node in connected_nodes:
                continue
            connected_nodes.add(node)

            # Explore neighbors through independent edges
            for neighbor in self.graph.neighbors(node):
                edge_key = (min(node, neighbor), max(node, neighbor))
                if (
                    edge_key in self.edge_status
                    and self.edge_status[edge_key] == "independent"
                ):
                    if neighbor not in connected_nodes:
                        to_explore.add(neighbor)

        # Count independent edges in this subgraph
        num_nodes = len(connected_nodes)
        num_edges = sum(
            1
            for edge_key, status in self.edge_status.items()
            if status == "independent"
            and edge_key[0] in connected_nodes
            and edge_key[1] in connected_nodes
        )

        # Check if adding one more edge would violate sparsity
        # |E| + 1 <= 2|V| - 3
        max_edges = 2 * num_nodes - 3
        would_violate = (num_edges + 1) > max_edges

        return would_violate

    def _find_and_place_pebble(self, u: str, v: str) -> bool:
        """
        Try to find a pebble on either endpoint and place it on the edge.

        This is the core of the pebble game. We search for a free pebble
        starting from either endpoint using directed search.

        The search works as follows:
        1. Check if u has a free pebble - if so, use it
        2. Check if v has a free pebble - if so, use it
        3. Search from u through already-covered edges for a free pebble
        4. Search from v through already-covered edges for a free pebble

        Args:
            u: First endpoint of edge
            v: Second endpoint of edge

        Returns:
            True if a pebble was found and placed, False otherwise
        """
        # Quick check: do either endpoint have free pebbles?
        if len(self.pebbles.get(u, [])) > 0:
            self.pebbles[u].pop()
            return True

        if len(self.pebbles.get(v, [])) > 0:
            self.pebbles[v].pop()
            return True

        # Need to search for a pebble through the graph
        # Try searching from u
        if self._search_for_pebble(u, set()):
            return True

        # Try searching from v
        if self._search_for_pebble(v, set()):
            return True

        return False

    def find_pebble(self, node: str, target: str, visited: set[str]) -> bool:
        """
        Public wrapper for _search_for_pebble for testing purposes.

        Args:
            node: Current node in search
            target: Target node (unused in current implementation)
            visited: Set of already visited nodes

        Returns:
            True if a pebble was found, False otherwise
        """
        return self._search_for_pebble(node, visited)

    def _search_for_pebble(self, start: str, visited: set[str]) -> bool:
        """
        Search for a free pebble using directed search along covered edges.

        This uses BFS to search through the graph, following only edges that
        are already independent (already have pebbles on them). This represents
        the "directed" nature of pebble search.

        Args:
            start: Starting node for search
            visited: Set of visited nodes to avoid cycles

        Returns:
            True if a pebble was found and taken, False otherwise
        """
        queue = deque([start])
        visited.add(start)

        while queue:
            node = queue.popleft()

            # Check if this node has a free pebble
            if len(self.pebbles.get(node, [])) > 0:
                self.pebbles[node].pop()
                return True

            # Explore neighbors through independent edges only
            for neighbor in self.graph.neighbors(node):
                if neighbor not in visited:
                    # Create normalized edge key (always smaller node first)
                    edge_key = (min(node, neighbor), max(node, neighbor))

                    # Can only traverse edges that are already covered (independent)
                    if (
                        edge_key in self.edge_status
                        and self.edge_status[edge_key] == "independent"
                    ):
                        visited.add(neighbor)
                        queue.append(neighbor)

        return False

    def rearrange_pebbles(self, node: str, target: str) -> bool:
        """
        Attempt to rearrange pebbles to make one available at the target.

        This is a more sophisticated version of pebble finding that explicitly
        tracks the rearrangement path.

        Args:
            node: Starting node for search
            target: Node where pebble is needed

        Returns:
            True if rearrangement succeeded, False otherwise
        """
        # Use BFS to find a pebble
        queue = deque([node])
        visited = {node}
        self.parent_map = {node: None}

        while queue:
            current = queue.popleft()

            # Found a node with a free pebble
            if len(self.pebbles.get(current, [])) > 0:
                # Remove the pebble from current
                self.pebbles[current].pop()
                return True

            # Explore neighbors
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    visited.add(neighbor)
                    self.parent_map[neighbor] = current
                    queue.append(neighbor)

        return False

    def identify_rigid_regions(self) -> list[set[str]]:
        """
        Identify rigid regions in the constraint graph.

        A region is rigid if it has no degrees of freedom (all pebbles are used).
        This uses the (2,3)-sparsity condition: a subgraph is rigid if it has
        exactly 2|V| - 3 independent edges.

        Returns:
            List of sets, where each set contains node IDs in a rigid region
        """
        if not self.graph or not self.edge_status:
            return []

        rigid_regions = []

        # Find connected components
        for component in nx.connected_components(self.graph):
            subgraph = self.graph.subgraph(component)
            num_nodes = len(component)
            num_edges = subgraph.number_of_edges()

            # Count independent edges in this component
            independent_edges = sum(
                1
                for edge in subgraph.edges()
                if self.edge_status.get((min(edge), max(edge)), "") == "independent"
            )

            # Rigid condition: exactly 2|V| - 3 independent edges
            expected_for_rigid = 2 * num_nodes - 3

            if num_nodes >= 2 and independent_edges >= expected_for_rigid:
                # This region is rigid or over-constrained
                rigid_regions.append(component)

        return rigid_regions

    def identify_flexible_regions(self) -> list[set[str]]:
        """
        Identify flexible (under-constrained) regions.

        A region is flexible if it has remaining degrees of freedom.

        Returns:
            List of sets, where each set contains node IDs in a flexible region
        """
        if not self.graph or not self.edge_status:
            return []

        flexible_regions = []

        for component in nx.connected_components(self.graph):
            subgraph = self.graph.subgraph(component)
            num_nodes = len(component)

            # Count pebbles remaining in this component
            pebbles_in_component = sum(
                len(self.pebbles.get(node, [])) for node in component
            )

            # Count independent edges
            independent_edges = sum(
                1
                for edge in subgraph.edges()
                if self.edge_status.get((min(edge), max(edge)), "") == "independent"
            )

            # Flexible if has degrees of freedom remaining
            expected_for_rigid = 2 * num_nodes - 3

            if (
                num_nodes >= 2
                and independent_edges < expected_for_rigid
                and pebbles_in_component > 0
            ):
                flexible_regions.append(component)

        return flexible_regions

    def identify_stressed_regions(self) -> list[set[str]]:
        """
        Identify over-constrained (stressed) regions.

        A region is stressed if it has redundant edges (edges that couldn't
        be covered with pebbles). These represent conflicting constraints.

        Returns:
            List of sets, where each set contains node IDs in a stressed region
        """
        if not self.graph or not self.edge_status:
            return []

        stressed_regions = []

        for component in nx.connected_components(self.graph):
            subgraph = self.graph.subgraph(component)

            # Check if this component has any redundant edges
            has_redundant = any(
                self.edge_status.get((min(edge), max(edge)), "") == "redundant"
                for edge in subgraph.edges()
            )

            if has_redundant:
                stressed_regions.append(component)

        return stressed_regions

    def get_degrees_of_freedom(self) -> int:
        """
        Calculate total degrees of freedom in the system.

        Returns:
            Number of remaining pebbles (unassigned degrees of freedom)
        """
        if not self.pebbles:
            return 0

        return sum(len(pebbles) for pebbles in self.pebbles.values())

    def recommend_constraint_changes(self) -> list[dict[str, Any]]:
        """
        Recommend constraint additions or removals to improve the system.

        Analyzes rigid, flexible, and stressed regions to suggest:
        - Removing redundant constraints from stressed regions
        - Adding constraints to flexible regions for stability

        Returns:
            List of recommendation dictionaries with:
            - action: "remove" or "add"
            - reason: Explanation of recommendation
            - region: Set of affected nodes
            - edge: Specific edge to modify (for remove actions)
            - severity: "high", "medium", or "low"
        """
        if not self.graph or not self.edge_status:
            return []

        recommendations = []

        # Analyze stressed regions (over-constrained)
        stressed_regions = self.identify_stressed_regions()
        for region in stressed_regions:
            subgraph = self.graph.subgraph(region)

            # Find redundant edges to remove
            for u, v in subgraph.edges():
                edge_key = (min(u, v), max(u, v))
                if self.edge_status.get(edge_key) == "redundant":
                    constraint_type = self.graph[u][v].get("constraint_type", "unknown")

                    recommendations.append(
                        {
                            "action": "remove",
                            "reason": "Redundant constraint causing over-constraint in region",
                            "region": region,
                            "edge": (u, v),
                            "constraint_type": constraint_type,
                            "severity": "high",
                        }
                    )

        # Analyze flexible regions (under-constrained)
        flexible_regions = self.identify_flexible_regions()
        for region in flexible_regions:
            num_nodes = len(region)
            subgraph = self.graph.subgraph(region)

            # Count current independent edges
            independent_edges = sum(
                1
                for edge in subgraph.edges()
                if self.edge_status.get((min(edge), max(edge)), "") == "independent"
            )

            # Calculate how many more edges needed for rigidity
            expected_for_rigid = 2 * num_nodes - 3
            deficit = expected_for_rigid - independent_edges

            if deficit > 0:
                recommendations.append(
                    {
                        "action": "add",
                        "reason": f"Region is under-constrained by {deficit} constraint(s)",
                        "region": region,
                        "missing_constraints": deficit,
                        "severity": "medium" if deficit <= 2 else "low",
                    }
                )

        return recommendations

    def get_constraint_graph_summary(self) -> dict[str, Any]:
        """
        Generate a summary of the constraint graph analysis.

        Returns:
            Dictionary with comprehensive analysis results
        """
        if not self.graph:
            return {
                "error": "No graph has been analyzed. Run build_constraint_graph first."
            }

        rigid_regions = self.identify_rigid_regions()
        flexible_regions = self.identify_flexible_regions()
        stressed_regions = self.identify_stressed_regions()
        recommendations = self.recommend_constraint_changes()

        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "degrees_of_freedom": self.get_degrees_of_freedom(),
            "num_rigid_regions": len(rigid_regions),
            "num_flexible_regions": len(flexible_regions),
            "num_stressed_regions": len(stressed_regions),
            "rigid_regions": [list(region) for region in rigid_regions],
            "flexible_regions": [list(region) for region in flexible_regions],
            "stressed_regions": [list(region) for region in stressed_regions],
            "recommendations": recommendations,
            "edge_breakdown": {
                "independent": sum(
                    1 for status in self.edge_status.values() if status == "independent"
                ),
                "redundant": sum(
                    1 for status in self.edge_status.values() if status == "redundant"
                ),
            },
        }
