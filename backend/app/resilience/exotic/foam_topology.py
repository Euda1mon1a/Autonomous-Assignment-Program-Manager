"""
Foam Topology Scheduler (Physics/Biology Pattern).

Inspired by foam bubble research (Penn Engineering, 2026), demonstrating that
bubbles continuously reorganize in patterns mirroring AI learning.

Key Concepts:
- FoamCell (Bubble) = Schedule Assignment (Resident + Block)
- FoamFilm (Interface) = Constraint margin between two assignments
- T1 Event (Topological swap) = Natural, constraint-neutral shift swap
- Pressure = Workload / fatigue stress

When constraint "film" shrinks to zero, it means a swap becomes highly
natural and constraint-neutral.
"""

import itertools
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class FoamCell:
    """
    A bubble in the foam = an assignment in the schedule.
    """

    cell_id: str
    resident_id: UUID
    block_id: UUID
    template_id: UUID | None = None

    neighbors: set[str] = field(default_factory=set)
    face_areas: dict[str, float] = field(default_factory=dict)
    volume: float = 1.0
    pressure: float = 0.0

    centroid: np.ndarray = field(default_factory=lambda: np.zeros(3))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    age: float = 0.0


@dataclass
class FoamFilm:
    """
    Interface between two bubbles = shared constraint boundary.
    """

    film_id: str
    cell_a: str
    cell_b: str

    area: float = 1.0
    tension: float = 1.0
    curvature: float = 0.0

    t1_threshold: float = 0.1
    t1_eligible: bool = True


@dataclass
class T1Event:
    """
    A topological rearrangement = schedule swap.
    """

    event_id: str
    timestamp: datetime

    film_collapsed: str
    cells_separating: tuple[str, str]
    cells_connecting: tuple[str, str]

    energy_before: float = 0.0
    energy_after: float = 0.0
    energy_delta: float = 0.0

    constraint_impacts: dict[str, float] = field(default_factory=dict)
    reversible: bool = True


@dataclass
class SwapRecommendation:
    """
    Output structure for suggested natural swaps.
    """

    resident_a: UUID
    resident_b: UUID
    block_a: UUID
    block_b: UUID
    energy_improvement: float
    constraint_margin: float
    natural_score: float


class FoamStructure:
    """
    Container and topological operations for the schedule's foam representation.
    """

    def __init__(self):
        self.cells: dict[str, FoamCell] = {}
        self.films: dict[str, FoamFilm] = {}

    def add_cell(self, cell: FoamCell) -> None:
        self.cells[cell.cell_id] = cell

    def remove_cell(self, cell_id: str) -> None:
        if cell_id in self.cells:
            # Remove all films associated with this cell
            films_to_remove = [
                f_id
                for f_id, film in self.films.items()
                if film.cell_a == cell_id or film.cell_b == cell_id
            ]
            for f_id in films_to_remove:
                self.remove_film(f_id)

            # Remove from neighbors' sets
            cell = self.cells[cell_id]
            for neighbor_id in cell.neighbors:
                if neighbor_id in self.cells:
                    self.cells[neighbor_id].neighbors.discard(cell_id)

            del self.cells[cell_id]

    def add_neighbor(self, cell_a: str, cell_b: str, initial_area: float = 1.0) -> None:
        if cell_a not in self.cells or cell_b not in self.cells:
            return

        # Create or update film
        film_id = self._get_film_id(cell_a, cell_b)
        if film_id not in self.films:
            film = FoamFilm(
                film_id=film_id, cell_a=cell_a, cell_b=cell_b, area=initial_area
            )
            self.films[film_id] = film
            self.cells[cell_a].neighbors.add(cell_b)
            self.cells[cell_b].neighbors.add(cell_a)

    def remove_film(self, film_id: str) -> None:
        if film_id in self.films:
            film = self.films[film_id]
            if film.cell_a in self.cells:
                self.cells[film.cell_a].neighbors.discard(film.cell_b)
            if film.cell_b in self.cells:
                self.cells[film.cell_b].neighbors.discard(film.cell_a)
            del self.films[film_id]

    def set_film_area(self, cell_a: str, cell_b: str, area: float) -> None:
        film_id = self._get_film_id(cell_a, cell_b)
        if film_id in self.films:
            self.films[film_id].area = area

    def _get_film_id(self, cell_a: str, cell_b: str) -> str:
        # Canonical order
        pair = sorted([cell_a, cell_b])
        return f"film_{pair[0]}_{pair[1]}"

    def cells_for_resident(self, resident_id: UUID) -> list[FoamCell]:
        return [c for c in self.cells.values() if c.resident_id == resident_id]

    def compute_local_energy(self, cell_a: FoamCell, cell_b: FoamCell) -> float:
        """
        Compute energy based on pressure (workload) and surface tension (constraints).
        Higher pressure differences or smaller film areas increase energy.
        """
        # Simplistic proxy: energy = |pressure_a - pressure_b| + sum(1 / (1 + film.area))
        pressure_delta = abs(cell_a.pressure - cell_b.pressure)

        energy = pressure_delta * 2.0  # arbitrary scaling

        for neighbor_id in cell_a.neighbors:
            film_id = self._get_film_id(cell_a.cell_id, neighbor_id)
            if film_id in self.films:
                energy += 1.0 / (1.0 + self.films[film_id].area)

        for neighbor_id in cell_b.neighbors:
            film_id = self._get_film_id(cell_b.cell_id, neighbor_id)
            if film_id in self.films:
                energy += 1.0 / (1.0 + self.films[film_id].area)

        return energy

    def simulate_t1_energy(
        self, film: FoamFilm, new_neighbors: tuple[str, str]
    ) -> float:
        """
        Simulate what the local energy would be if the swap happened.
        """
        if film.cell_a not in self.cells or film.cell_b not in self.cells:
            return float("inf")

        cell_a = self.cells[film.cell_a]
        cell_b = self.cells[film.cell_b]

        # A real T1 would swap the resident/block association, relieving pressure
        # if the pressures were misaligned with their new neighborhood.
        # Simplistic proxy: if new neighbors help equalize pressure, lower energy.
        simulated_pressure_a = (
            cell_a.pressure
            + sum(self.cells[n].pressure for n in new_neighbors if n != film.cell_b)
        ) / (len(new_neighbors) + 1)
        simulated_pressure_b = (
            cell_b.pressure
            + sum(self.cells[n].pressure for n in new_neighbors if n != film.cell_a)
        ) / (len(new_neighbors) + 1)

        sim_energy = abs(simulated_pressure_a - simulated_pressure_b) * 1.5

        # New films would form, assuming default area initially
        sim_energy += 2.0 / (1.0 + 1.0)  # two new standard films

        return sim_energy


class FoamTopologyScheduler:
    """
    Implements continuous topological dynamics to find natural swaps.
    """

    def __init__(
        self,
        diffusion_rate: float = 0.1,
        t1_threshold: float = 0.15,
        coarsening_threshold: float = 0.1,
        random_seed: int | None = None,
    ):
        self.diffusion_rate = diffusion_rate
        self.t1_threshold = t1_threshold
        self.coarsening_threshold = coarsening_threshold
        self.rng = np.random.default_rng(random_seed)
        self.foam: FoamStructure = FoamStructure()
        self.t1_history: list[T1Event] = []

    def initialize_from_schedule(
        self, assignments: list[dict[str, Any]], constraints: list[Any]
    ) -> None:
        """
        Convert simple schedule assignments into FoamCells.
        assignments format: {"id": UUID, "person_id": UUID, "block_id": UUID, "workload": float}
        """
        self.foam = FoamStructure()

        for a in assignments:
            cell = FoamCell(
                cell_id=f"cell_{a['id']}",
                resident_id=a["person_id"],
                block_id=a["block_id"],
                volume=a.get("workload", 1.0),
                pressure=a.get(
                    "workload", 1.0
                ),  # simple correlation for initialization
            )
            self.foam.add_cell(cell)

        # Build random graph for demonstration of shared constraints
        # In reality, this would evaluate actual Constraints overlapping
        cell_ids = list(self.foam.cells.keys())
        for i in range(len(cell_ids)):
            for j in range(
                i + 1, min(i + 4, len(cell_ids))
            ):  # connect to a few next cells
                # Random film area to simulate varied constraint slack
                area = self.rng.uniform(0.01, 1.5)
                self.foam.add_neighbor(cell_ids[i], cell_ids[j], area)

    def detect_t1_candidates(self) -> list[T1Event]:
        """
        Find films approaching zero area.
        """
        candidates = []

        for film in self.foam.films.values():
            if film.area > self.t1_threshold or not film.t1_eligible:
                continue

            # Simulate outcome
            cell_a = self.foam.cells.get(film.cell_a)
            cell_b = self.foam.cells.get(film.cell_b)

            if not cell_a or not cell_b:
                continue

            # A real T1 would swap the resident/block association, relieving pressure
            # if the pressures were misaligned with their new neighborhood.
            # Identify common neighbors that might reconnect
            # In a true 2D foam, the neighbor topology changes deterministically.
            # Here we just pick a couple of neighbors.
            new_neighbors_list = sorted(
                list(
                    cell_a.neighbors.union(cell_b.neighbors)
                    - {cell_a.cell_id, cell_b.cell_id}
                )[:2]
            )
            if len(new_neighbors_list) < 2:
                continue
            new_neighbors = (new_neighbors_list[0], new_neighbors_list[1])

            energy_before = self.foam.compute_local_energy(cell_a, cell_b)
            energy_after = self.foam.simulate_t1_energy(film, new_neighbors)
            # If energy strictly drops or film is very small
            if energy_after < energy_before or film.area < 0.05:
                event = T1Event(
                    event_id=f"t1_{film.film_id}_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    film_collapsed=film.film_id,
                    cells_separating=(cell_a.cell_id, cell_b.cell_id),
                    cells_connecting=new_neighbors,  # type: ignore
                    energy_before=energy_before,
                    energy_after=energy_after,
                    energy_delta=energy_after - energy_before,
                )
                candidates.append(event)

        # Sort by best energy improvement (most negative delta)
        return sorted(candidates, key=lambda e: e.energy_delta)

    def find_optimal_swaps(self, n: int = 5) -> list[SwapRecommendation]:
        """
        Find top N swap opportunities.
        """
        candidates = self.detect_t1_candidates()
        recs = []

        for c in candidates[:n]:
            film = self.foam.films.get(c.film_collapsed)
            if not film:
                continue

            cell_a = self.foam.cells.get(c.cells_separating[0])
            cell_b = self.foam.cells.get(c.cells_separating[1])

            if not cell_a or not cell_b:
                continue

            # Natural score maps film area (0 to threshold) to (1.0 to 0.0)
            natural_score = max(0.0, 1.0 - (film.area / self.t1_threshold))

            rec = SwapRecommendation(
                resident_a=cell_a.resident_id,
                resident_b=cell_b.resident_id,
                block_a=cell_a.block_id,
                block_b=cell_b.block_id,
                energy_improvement=-c.energy_delta,
                constraint_margin=film.area,
                natural_score=natural_score,
            )
            recs.append(rec)

        return recs

    def evolve(self, steps: int = 10, dt: float = 0.01) -> list[T1Event]:
        """
        Evolve the foam dynamics: pressures equalize, films shrink/grow.
        """
        executed_events = []

        for _ in range(steps):
            # Gas diffusion (workload balancing)
            for film in self.foam.films.values():
                cell_a = self.foam.cells.get(film.cell_a)
                cell_b = self.foam.cells.get(film.cell_b)
                if not cell_a or not cell_b:
                    continue

                delta_p = cell_a.pressure - cell_b.pressure
                transfer = film.area * delta_p * dt * self.diffusion_rate

                # Flow from high to low
                cell_a.pressure -= transfer
                cell_b.pressure += transfer

            # Area changes (simulated constraint pressure changing)
            for film in list(self.foam.films.values()):
                # Random drift simulating changing conditions or solver searching
                drift = self.rng.normal(0, 0.05 * dt)
                film.area = max(0.0, film.area + drift)

            # Check and execute T1 events
            candidates = self.detect_t1_candidates()
            for candidate in candidates:
                if self._validate_and_execute_t1(candidate):
                    executed_events.append(candidate)
                    break  # Execute one per step to avoid cascade chaos

            # Age cells
            for cell in self.foam.cells.values():
                cell.age += dt

        self.t1_history.extend(executed_events)
        return executed_events

    def _validate_and_execute_t1(self, event: T1Event) -> bool:
        """
        Safely execute the T1 topological change.
        """
        # Collapse film
        if event.film_collapsed in self.foam.films:
            self.foam.remove_film(event.film_collapsed)

        # Disconnect separating cells
        c1_id, c2_id = event.cells_separating
        if c1_id in self.foam.cells and c2_id in self.foam.cells:
            self.foam.cells[c1_id].neighbors.discard(c2_id)
            self.foam.cells[c2_id].neighbors.discard(c1_id)

        # Connect new cells
        n1_id, n2_id = event.cells_connecting
        self.foam.add_neighbor(n1_id, n2_id, initial_area=self.t1_threshold)

        # Reset age
        for cell_id in event.cells_separating + event.cells_connecting:
            if cell_id in self.foam.cells:
                self.foam.cells[cell_id].age = 0.0

        return True
