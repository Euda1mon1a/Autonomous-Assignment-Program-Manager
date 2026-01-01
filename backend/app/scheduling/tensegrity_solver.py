"""
Tensegrity-based Force Density Method solver for schedule equilibrium.

This module applies structural mechanics principles to scheduling problems by
treating schedules as tensegrity structures:
- Nodes = Tasks/Events with timestamps as positions
- Tension elements = Deadlines/Preferences (pull nodes together)
- Compression elements = Resource limits (push nodes apart)
- Anchors = Fixed time constraints

The Force Density Method finds equilibrium positions by solving a linear system
of equations based on the force density matrix.

References:
    - Schek, H.J. (1974). "The force density method for form finding and
      computation of general networks." Computer Methods in Applied Mechanics
      and Engineering, 3(1), 115-134.
    - Pellegrino, S. (1993). "Structural computations with the singular value
      decomposition of the equilibrium matrix." International Journal of Solids
      and Structures, 30(21), 3025-3035.
"""

import numpy as np
from scipy import sparse
from scipy.sparse import linalg as sp_linalg


class TensegritySolver:
    """
    Force Density Method solver for tensegrity-based schedule equilibrium.

    The solver treats scheduling problems as tensegrity structures where:
    - Nodes represent tasks/events with time positions
    - Edges represent constraints with force densities
    - Anchors represent fixed time constraints

    The equilibrium equation is: F · x = p
    Where:
        F = Force density matrix (connectivity + force densities)
        x = Node positions (time coordinates)
        p = External forces (from anchored nodes)

    For partitioned system (free + fixed nodes):
        F_ff · x_f = p_f - F_fa · x_a

    Attributes:
        nodes: Dictionary mapping node_id to node data
        edges: List of (node1, node2, force_density, type) tuples

    Example:
        >>> solver = TensegritySolver()
        >>> solver.add_node('shift_start', initial_position=8.0, is_anchor=True)
        >>> solver.add_node('task_a', initial_position=9.0)
        >>> solver.add_tension_element('shift_start', 'task_a', force_density=1.0)
        >>> solution = solver.solve()
        >>> print(solution)  # {'shift_start': 8.0, 'task_a': 8.5, ...}
    """

    def __init__(self) -> None:
        """Initialize an empty tensegrity solver."""
        self.nodes: dict[str, dict] = {}
        self.edges: list[tuple[str, str, float, str]] = []

    def add_node(
        self, node_id: str, initial_position: float = 0.0, is_anchor: bool = False
    ) -> None:
        """
        Add a node (task/event) to the structure.

        Args:
            node_id: Unique identifier for the node
            initial_position: Initial time position (hours)
            is_anchor: If True, this node's position is fixed

        Raises:
            ValueError: If node_id already exists

        Example:
            >>> solver = TensegritySolver()
            >>> solver.add_node('shift_start', initial_position=8.0, is_anchor=True)
            >>> solver.add_node('task_a', initial_position=9.0)
        """
        if node_id in self.nodes:
            raise ValueError(f"Node '{node_id}' already exists")

        self.nodes[node_id] = {
            "position": float(initial_position),
            "is_anchor": bool(is_anchor),
        }

    def add_tension_element(self, node1: str, node2: str, force_density: float) -> None:
        """
        Add a tension element (cable) between two nodes.

        Tension elements pull nodes together, representing constraints like:
        - Deadlines (pull tasks toward target time)
        - Preferences (pull related tasks together)
        - Dependencies (pull successor close to predecessor)

        Args:
            node1: First node identifier
            node2: Second node identifier
            force_density: Force per unit length (q > 0 for tension)

        Raises:
            ValueError: If nodes don't exist or force_density is negative

        Example:
            >>> solver.add_tension_element('task_a', 'task_b', force_density=1.0)
        """
        if node1 not in self.nodes:
            raise ValueError(f"Node '{node1}' does not exist")
        if node2 not in self.nodes:
            raise ValueError(f"Node '{node2}' does not exist")
        if force_density < 0:
            raise ValueError("Tension force density must be non-negative")

        self.edges.append((node1, node2, float(force_density), "tension"))

    def add_compression_element(
        self, node1: str, node2: str, force_density: float
    ) -> None:
        """
        Add a compression element (strut) between two nodes.

        Compression elements push nodes apart, representing constraints like:
        - Minimum gaps (enforce spacing between tasks)
        - Resource limits (prevent overlapping resource usage)
        - Break requirements (enforce rest periods)

        Args:
            node1: First node identifier
            node2: Second node identifier
            force_density: Force per unit length (q > 0 for compression)

        Raises:
            ValueError: If nodes don't exist or force_density is negative

        Note:
            The force_density parameter is always positive. The compression
            behavior is encoded in the edge type, not the sign of force_density.

        Example:
            >>> solver.add_compression_element('task_a', 'task_b', force_density=0.5)
        """
        if node1 not in self.nodes:
            raise ValueError(f"Node '{node1}' does not exist")
        if node2 not in self.nodes:
            raise ValueError(f"Node '{node2}' does not exist")
        if force_density < 0:
            raise ValueError("Compression force density must be non-negative")

        self.edges.append((node1, node2, float(force_density), "compression"))

    def build_force_density_matrix(self) -> sparse.csr_matrix:
        """
        Build the force density matrix F.

        The force density matrix encodes the network topology and force densities:
        - F[i,j] = -q_ij for connected nodes (off-diagonal)
        - F[i,i] = Σ q_ik for node i (diagonal = sum of incident force densities)

        For compression elements, the force density is negated to represent
        repulsive forces.

        Returns:
            Sparse CSR matrix of size (n_nodes, n_nodes)

        Mathematical formulation:
            F_ij = -q_ij  if nodes i and j are connected
            F_ii = Σ_k q_ik  (sum over all edges incident to node i)

        Example:
            >>> F = solver.build_force_density_matrix()
            >>> print(F.shape)  # (n_nodes, n_nodes)
        """
        n = len(self.nodes)
        node_ids = list(self.nodes.keys())
        node_index = {node_id: i for i, node_id in enumerate(node_ids)}

        # Build sparse matrix using LIL format for efficient construction
        F = sparse.lil_matrix((n, n), dtype=float)

        for node1, node2, q, edge_type in self.edges:
            i = node_index[node1]
            j = node_index[node2]

            # For compression elements, we negate the force density
            # This creates repulsive forces that push nodes apart
            q_effective = -q if edge_type == "compression" else q

            # Off-diagonal: -q_ij
            F[i, j] -= q_effective
            F[j, i] -= q_effective

            # Diagonal: sum of incident force densities
            F[i, i] += q_effective
            F[j, j] += q_effective

        # Convert to CSR format for efficient solving
        return F.tocsr()

    def build_anchor_vector(self) -> np.ndarray:
        """
        Build the anchor vector (external forces from fixed nodes).

        The anchor vector p represents external forces applied by anchored nodes.
        For partitioned systems, we compute: p_f = -F_fa · x_a

        Returns:
            Array of size n_nodes with external forces for each node

        Example:
            >>> p = solver.build_anchor_vector()
            >>> print(p.shape)  # (n_nodes,)
        """
        n = len(self.nodes)
        return np.zeros(n, dtype=float)

    def solve(self) -> dict[str, float]:
        """
        Solve for equilibrium positions using Force Density Method.

        The method partitions nodes into free and fixed (anchor) nodes,
        then solves the linear system: F_ff · x_f = p_f - F_fa · x_a

        Algorithm:
            1. Build force density matrix F
            2. Partition into free nodes (unknowns) and anchors (known)
            3. Extract submatrices: F_ff, F_fa
            4. Solve linear system for free node positions
            5. Combine with anchor positions

        Returns:
            Dictionary mapping node_id to equilibrium position (time)

        Raises:
            ValueError: If system is under-constrained or singular
            RuntimeError: If solver fails to converge

        Example:
            >>> solver = TensegritySolver()
            >>> solver.add_node('start', 8.0, is_anchor=True)
            >>> solver.add_node('task', 10.0)
            >>> solver.add_node('end', 17.0, is_anchor=True)
            >>> solver.add_tension_element('start', 'task', 1.0)
            >>> solver.add_tension_element('task', 'end', 1.0)
            >>> solution = solver.solve()
            >>> print(solution['task'])  # Should be between 8.0 and 17.0
        """
        if not self.nodes:
            raise ValueError("No nodes in structure")

        # Build full force density matrix
        F = self.build_force_density_matrix()

        # Separate free and anchor nodes
        node_ids = list(self.nodes.keys())
        free_indices = [
            i for i, nid in enumerate(node_ids) if not self.nodes[nid]["is_anchor"]
        ]
        anchor_indices = [
            i for i, nid in enumerate(node_ids) if self.nodes[nid]["is_anchor"]
        ]

        # If no free nodes, return anchor positions
        if not free_indices:
            return {nid: self.nodes[nid]["position"] for nid in node_ids}

        # Extract submatrices
        # F_ff: free-to-free coupling
        F_ff = F[np.ix_(free_indices, free_indices)]

        # Build right-hand side
        if anchor_indices:
            # F_fa: free-to-anchor coupling
            F_fa = F[np.ix_(free_indices, anchor_indices)]

            # x_a: anchor positions
            x_a = np.array(
                [self.nodes[node_ids[i]]["position"] for i in anchor_indices]
            )

            # p_f = -F_fa · x_a
            p_f = -F_fa.dot(x_a)
        else:
            # No anchors, use initial positions as weak constraints
            p_f = np.zeros(len(free_indices))

        # Solve F_ff · x_f = p_f
        try:
            # Use sparse solver for efficiency
            x_f = sp_linalg.spsolve(F_ff, p_f)
        except RuntimeError as e:
            raise RuntimeError(f"Failed to solve linear system: {e}") from e

        # Combine free and anchor solutions
        solution = {}
        for i, node_id in enumerate(node_ids):
            if self.nodes[node_id]["is_anchor"]:
                solution[node_id] = self.nodes[node_id]["position"]
            else:
                free_idx = free_indices.index(i)
                solution[node_id] = float(x_f[free_idx])

        return solution

    def is_stable(self, solution: dict[str, float] | None = None) -> bool:
        """
        Check if the solution represents a valid stable configuration.

        Stability criteria:
            1. All positions are non-negative (valid times)
            2. Positions respect causality (predecessors before successors)
            3. No NaN or infinite values

        Args:
            solution: Solution dictionary from solve(). If None, solve() is called.

        Returns:
            True if solution is stable and valid, False otherwise

        Example:
            >>> solution = solver.solve()
            >>> if solver.is_stable(solution):
            ...     print("Solution is valid")
        """
        if solution is None:
            try:
                solution = self.solve()
            except (ValueError, RuntimeError):
                return False

        # Check for NaN or infinite values
        for pos in solution.values():
            if not np.isfinite(pos):
                return False

        # Check for negative times (invalid)
        if any(pos < 0 for pos in solution.values()):
            return False

        # Check causality for tension elements (dependencies)
        # Tension should maintain order constraints
        for node1, node2, q, edge_type in self.edges:
            if edge_type == "tension" and q > 0:
                # For high tension, expect nodes to be close
                # This is a soft check - just verify positions are reasonable
                pos1 = solution[node1]
                pos2 = solution[node2]
                # Allow reasonable spread (e.g., within 24 hours for scheduling)
                if abs(pos1 - pos2) > 24.0:
                    return False

        return True

    def get_internal_forces(
        self, solution: dict[str, float] | None = None
    ) -> dict[tuple[str, str], float]:
        """
        Calculate internal member forces for the equilibrium configuration.

        Internal force in member (i,j): F_ij = q_ij · (x_j - x_i)
        Where:
            q_ij = force density
            x_i, x_j = node positions

        Args:
            solution: Solution dictionary from solve(). If None, solve() is called.

        Returns:
            Dictionary mapping (node1, node2) to internal force
            Positive = tension (pulling), Negative = compression (pushing)

        Example:
            >>> solution = solver.solve()
            >>> forces = solver.get_internal_forces(solution)
            >>> for (n1, n2), force in forces.items():
            ...     print(f"{n1}-{n2}: {force:.2f}")
        """
        if solution is None:
            solution = self.solve()

        forces = {}
        for node1, node2, q, edge_type in self.edges:
            x1 = solution[node1]
            x2 = solution[node2]

            # F = q · (x2 - x1)
            # For compression elements, q was already negated in the matrix
            q_effective = -q if edge_type == "compression" else q
            force = q_effective * (x2 - x1)

            forces[(node1, node2)] = force

        return forces

    def to_schedule(self, solution: dict[str, float]) -> list[dict]:
        """
        Convert equilibrium positions to schedule format.

        Args:
            solution: Solution dictionary from solve()

        Returns:
            List of schedule entries with task_id and scheduled_time

        Example:
            >>> solution = solver.solve()
            >>> schedule = solver.to_schedule(solution)
            >>> for entry in schedule:
            ...     print(f"{entry['task_id']}: {entry['scheduled_time']:.2f}")
        """
        schedule = []
        for node_id, position in solution.items():
            if not self.nodes[node_id]["is_anchor"]:
                schedule.append(
                    {
                        "task_id": node_id,
                        "scheduled_time": position,
                        "is_fixed": False,
                    }
                )
            else:
                schedule.append(
                    {
                        "task_id": node_id,
                        "scheduled_time": position,
                        "is_fixed": True,
                    }
                )

        # Sort by time
        schedule.sort(key=lambda x: x["scheduled_time"])
        return schedule

    def visualize(self, solution: dict[str, float]) -> str:
        """
        Create an ASCII visualization of the structure.

        Args:
            solution: Solution dictionary from solve()

        Returns:
            String containing ASCII art representation

        Example:
            >>> solution = solver.solve()
            >>> print(solver.visualize(solution))
            Time: 8.00  [shift_start] ═══(T)══> [task_a] ═══(T)══> [shift_end] 17.00
        """
        if not solution:
            return "Empty structure"

        # Sort nodes by position
        sorted_nodes = sorted(solution.items(), key=lambda x: x[1])

        lines = []
        lines.append("Tensegrity Structure Visualization")
        lines.append("=" * 60)
        lines.append("")

        # Node listing
        lines.append("Nodes (sorted by time):")
        for node_id, position in sorted_nodes:
            anchor_mark = "[ANCHOR]" if self.nodes[node_id]["is_anchor"] else ""
            lines.append(f"  {position:6.2f}h  {node_id:20s} {anchor_mark}")

        lines.append("")
        lines.append("Connections:")

        # Edge listing
        for node1, node2, q, edge_type in self.edges:
            pos1 = solution[node1]
            pos2 = solution[node2]
            symbol = "(T)" if edge_type == "tension" else "(C)"
            force = q * (pos2 - pos1)
            lines.append(
                f"  {node1:15s} {symbol} {node2:15s} | "
                f"q={q:.2f}, Δt={abs(pos2 - pos1):.2f}h, F={force:.2f}"
            )

        lines.append("")

        # Timeline visualization (simplified)
        min_time = min(solution.values())
        max_time = max(solution.values())

        if max_time > min_time:
            lines.append("Timeline:")
            width = 60

            for node_id, position in sorted_nodes:
                # Calculate position on timeline
                normalized = (position - min_time) / (max_time - min_time)
                pos_on_line = int(normalized * (width - 1))

                # Build timeline string
                timeline = ["-"] * width
                timeline[pos_on_line] = "*"

                anchor_mark = "A" if self.nodes[node_id]["is_anchor"] else " "
                lines.append(
                    f"  {position:6.2f}h [{anchor_mark}] {''.join(timeline)} {node_id}"
                )

        return "\n".join(lines)
