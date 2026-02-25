import uuid
from datetime import datetime

from app.resilience.exotic.foam_topology import (
    FoamCell,
    FoamFilm,
    FoamStructure,
    FoamTopologyScheduler,
    T1Event,
)


def test_foam_cell_creation():
    res_id = uuid.uuid4()
    block_id = uuid.uuid4()
    cell = FoamCell(cell_id="c1", resident_id=res_id, block_id=block_id, volume=1.5)
    assert cell.cell_id == "c1"
    assert cell.resident_id == res_id
    assert cell.volume == 1.5
    assert len(cell.neighbors) == 0


def test_foam_structure_add_remove():
    foam = FoamStructure()
    c1 = FoamCell(cell_id="c1", resident_id=uuid.uuid4(), block_id=uuid.uuid4())
    c2 = FoamCell(cell_id="c2", resident_id=uuid.uuid4(), block_id=uuid.uuid4())

    foam.add_cell(c1)
    foam.add_cell(c2)
    assert len(foam.cells) == 2

    foam.add_neighbor("c1", "c2", 0.8)
    assert "c2" in foam.cells["c1"].neighbors
    assert len(foam.films) == 1

    # Remove cell should remove associated films
    foam.remove_cell("c1")
    assert "c1" not in foam.cells
    assert len(foam.films) == 0
    assert "c1" not in foam.cells["c2"].neighbors


def test_foam_topology_scheduler():
    scheduler = FoamTopologyScheduler(random_seed=42)

    # Mock assignments
    assignments = [
        {
            "id": uuid.uuid4(),
            "person_id": uuid.uuid4(),
            "block_id": uuid.uuid4(),
            "workload": 1.0,
        },
        {
            "id": uuid.uuid4(),
            "person_id": uuid.uuid4(),
            "block_id": uuid.uuid4(),
            "workload": 0.5,
        },
        {
            "id": uuid.uuid4(),
            "person_id": uuid.uuid4(),
            "block_id": uuid.uuid4(),
            "workload": 1.2,
        },
        {
            "id": uuid.uuid4(),
            "person_id": uuid.uuid4(),
            "block_id": uuid.uuid4(),
            "workload": 0.8,
        },
    ]

    scheduler.initialize_from_schedule(assignments, constraints=[])

    # We expect some cells and random initial films
    assert len(scheduler.foam.cells) == 4

    # Evolve the topology
    events = scheduler.evolve(steps=20)

    # Check if swaps were recommended
    swaps = scheduler.find_optimal_swaps(n=5)
    assert isinstance(swaps, list)

    # Check that pressures have changed
    for c in scheduler.foam.cells.values():
        assert c.age > 0
