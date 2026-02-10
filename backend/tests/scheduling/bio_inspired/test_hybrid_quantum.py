"""Tests for hybrid GA-QUBO pipeline pure-logic components (no DB)."""

import numpy as np
import pytest

from app.scheduling.bio_inspired.hybrid_quantum import (
    DecompositionStrategy,
    HybridConfig,
    ProblemDecomposition,
)


# ---------------------------------------------------------------------------
# DecompositionStrategy enum
# ---------------------------------------------------------------------------


class TestDecompositionStrategy:
    def test_by_resident(self):
        assert DecompositionStrategy.BY_RESIDENT.value == "by_resident"

    def test_by_block_week(self):
        assert DecompositionStrategy.BY_BLOCK_WEEK.value == "by_block_week"

    def test_by_template(self):
        assert DecompositionStrategy.BY_TEMPLATE.value == "by_template"

    def test_adaptive(self):
        assert DecompositionStrategy.ADAPTIVE.value == "adaptive"

    def test_all_members(self):
        assert len(DecompositionStrategy) == 4


# ---------------------------------------------------------------------------
# HybridConfig defaults
# ---------------------------------------------------------------------------


class TestHybridConfig:
    def test_default_population_size(self):
        config = HybridConfig()
        assert config.population_size == 50

    def test_default_max_generations(self):
        config = HybridConfig()
        assert config.max_generations == 100

    def test_default_decomposition_strategy(self):
        config = HybridConfig()
        assert config.decomposition_strategy == DecompositionStrategy.ADAPTIVE

    def test_default_n_subproblems(self):
        config = HybridConfig()
        assert config.n_subproblems == 10

    def test_default_min_subproblem_size(self):
        config = HybridConfig()
        assert config.min_subproblem_size == 5

    def test_default_crossover_rate(self):
        config = HybridConfig()
        assert config.crossover_rate == 0.8

    def test_default_mutation_rate(self):
        config = HybridConfig()
        assert config.mutation_rate == 0.1

    def test_default_elite_size(self):
        config = HybridConfig()
        assert config.elite_size == 3

    def test_default_qubo_num_reads(self):
        config = HybridConfig()
        assert config.qubo_num_reads == 50

    def test_default_qubo_num_sweeps(self):
        config = HybridConfig()
        assert config.qubo_num_sweeps == 500

    def test_default_qubo_timeout(self):
        config = HybridConfig()
        assert config.qubo_timeout == 5.0

    def test_default_migration_enabled(self):
        config = HybridConfig()
        assert config.enable_migration is True

    def test_default_migration_interval(self):
        config = HybridConfig()
        assert config.migration_interval == 10

    def test_default_migration_size(self):
        config = HybridConfig()
        assert config.migration_size == 3

    def test_default_n_islands(self):
        config = HybridConfig()
        assert config.n_islands == 4

    def test_custom_config(self):
        config = HybridConfig(
            population_size=80,
            max_generations=200,
            n_islands=6,
            crossover_rate=0.9,
        )
        assert config.population_size == 80
        assert config.max_generations == 200
        assert config.n_islands == 6
        assert config.crossover_rate == 0.9


# ---------------------------------------------------------------------------
# ProblemDecomposition — factory methods
# ---------------------------------------------------------------------------


class TestCreateByResident:
    def test_shape(self):
        decomp = ProblemDecomposition.create_by_resident(5, 20)
        assert decomp.partition.shape == (5, 20)

    def test_n_subproblems(self):
        decomp = ProblemDecomposition.create_by_resident(5, 20)
        assert decomp.n_subproblems == 5

    def test_strategy(self):
        decomp = ProblemDecomposition.create_by_resident(5, 20)
        assert decomp.strategy == DecompositionStrategy.BY_RESIDENT

    def test_each_resident_has_own_partition(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        # Row 0 should all be 0, row 1 all 1, row 2 all 2
        for r_idx in range(3):
            assert np.all(decomp.partition[r_idx, :] == r_idx)

    def test_single_resident(self):
        decomp = ProblemDecomposition.create_by_resident(1, 10)
        assert decomp.n_subproblems == 1
        assert np.all(decomp.partition == 0)


class TestCreateByWeek:
    def test_shape(self):
        decomp = ProblemDecomposition.create_by_week(5, 20)
        assert decomp.partition.shape == (5, 20)

    def test_strategy(self):
        decomp = ProblemDecomposition.create_by_week(5, 20)
        assert decomp.strategy == DecompositionStrategy.BY_BLOCK_WEEK

    def test_default_blocks_per_week(self):
        decomp = ProblemDecomposition.create_by_week(3, 30, blocks_per_week=10)
        assert decomp.n_subproblems == 3  # 30/10 = 3 weeks

    def test_partial_last_week(self):
        decomp = ProblemDecomposition.create_by_week(2, 15, blocks_per_week=10)
        # ceil(15/10) = 2 weeks
        assert decomp.n_subproblems == 2

    def test_blocks_assigned_to_correct_week(self):
        decomp = ProblemDecomposition.create_by_week(2, 20, blocks_per_week=10)
        # Blocks 0-9 = week 0, blocks 10-19 = week 1
        assert np.all(decomp.partition[:, 0:10] == 0)
        assert np.all(decomp.partition[:, 10:20] == 1)

    def test_all_residents_same_week(self):
        decomp = ProblemDecomposition.create_by_week(3, 10, blocks_per_week=10)
        # All 3 residents, single week
        assert decomp.n_subproblems == 1
        assert np.all(decomp.partition == 0)


class TestCreateAdaptive:
    def test_shape(self):
        np.random.seed(42)
        decomp = ProblemDecomposition.create_adaptive(5, 20, n_subproblems=10)
        assert decomp.partition.shape == (5, 20)

    def test_strategy(self):
        np.random.seed(42)
        decomp = ProblemDecomposition.create_adaptive(5, 20)
        assert decomp.strategy == DecompositionStrategy.ADAPTIVE

    def test_default_n_subproblems(self):
        np.random.seed(42)
        decomp = ProblemDecomposition.create_adaptive(3, 10)
        assert decomp.n_subproblems == 10

    def test_values_in_range(self):
        np.random.seed(42)
        decomp = ProblemDecomposition.create_adaptive(5, 20, n_subproblems=7)
        assert np.all(decomp.partition >= 0)
        assert np.all(decomp.partition < 7)

    def test_randomness(self):
        np.random.seed(42)
        d1 = ProblemDecomposition.create_adaptive(5, 20, n_subproblems=10)
        np.random.seed(99)
        d2 = ProblemDecomposition.create_adaptive(5, 20, n_subproblems=10)
        # Different seeds should produce different partitions
        assert not np.array_equal(d1.partition, d2.partition)


# ---------------------------------------------------------------------------
# ProblemDecomposition — subproblem mask
# ---------------------------------------------------------------------------


class TestGetSubproblemMask:
    def test_mask_shape(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        mask = decomp.get_subproblem_mask(0)
        assert mask.shape == (3, 10)

    def test_mask_selects_correct_rows(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        mask = decomp.get_subproblem_mask(1)
        # Only row 1 should be True
        assert np.all(mask[1, :])
        assert not np.any(mask[0, :])
        assert not np.any(mask[2, :])

    def test_mask_for_week(self):
        decomp = ProblemDecomposition.create_by_week(2, 20, blocks_per_week=10)
        mask = decomp.get_subproblem_mask(0)
        # Week 0 = columns 0-9
        assert np.all(mask[:, 0:10])
        assert not np.any(mask[:, 10:20])


# ---------------------------------------------------------------------------
# ProblemDecomposition — merge solutions
# ---------------------------------------------------------------------------


class TestMergeSolutions:
    def test_empty_solutions(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        merged = decomp.merge_solutions()
        assert np.all(merged == 0)

    def test_merge_single_subproblem(self):
        decomp = ProblemDecomposition.create_by_resident(2, 5)
        sol = np.ones((2, 5), dtype=np.int32) * 3
        decomp.subproblem_solutions[0] = sol
        merged = decomp.merge_solutions()
        # Only row 0 should have value 3
        assert np.all(merged[0, :] == 3)
        assert np.all(merged[1, :] == 0)

    def test_merge_all_subproblems(self):
        decomp = ProblemDecomposition.create_by_resident(2, 5)
        sol0 = np.full((2, 5), 1, dtype=np.int32)
        sol1 = np.full((2, 5), 2, dtype=np.int32)
        decomp.subproblem_solutions[0] = sol0
        decomp.subproblem_solutions[1] = sol1
        merged = decomp.merge_solutions()
        assert np.all(merged[0, :] == 1)  # Row 0 = subproblem 0
        assert np.all(merged[1, :] == 2)  # Row 1 = subproblem 1

    def test_merge_weekly(self):
        decomp = ProblemDecomposition.create_by_week(2, 20, blocks_per_week=10)
        sol_week0 = np.full((2, 20), 5, dtype=np.int32)
        sol_week1 = np.full((2, 20), 9, dtype=np.int32)
        decomp.subproblem_solutions[0] = sol_week0
        decomp.subproblem_solutions[1] = sol_week1
        merged = decomp.merge_solutions()
        assert np.all(merged[:, 0:10] == 5)
        assert np.all(merged[:, 10:20] == 9)


# ---------------------------------------------------------------------------
# ProblemDecomposition — to_dict
# ---------------------------------------------------------------------------


class TestToDict:
    def test_returns_dict(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        d = decomp.to_dict()
        assert isinstance(d, dict)

    def test_strategy_value(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        d = decomp.to_dict()
        assert d["strategy"] == "by_resident"

    def test_n_subproblems(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        d = decomp.to_dict()
        assert d["n_subproblems"] == 3

    def test_partition_shape(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        d = decomp.to_dict()
        assert d["partition_shape"] == [3, 10]

    def test_time_fields(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        d = decomp.to_dict()
        assert "qubo_time" in d
        assert "merge_time" in d
        assert "total_energy" in d

    def test_subproblem_energies(self):
        decomp = ProblemDecomposition.create_by_resident(2, 5)
        decomp.subproblem_energies = {0: -10.0, 1: -5.0}
        d = decomp.to_dict()
        assert d["subproblem_energies"] == {0: -10.0, 1: -5.0}


# ---------------------------------------------------------------------------
# ProblemDecomposition — performance tracking defaults
# ---------------------------------------------------------------------------


class TestDecompositionDefaults:
    def test_empty_subproblem_solutions(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        assert decomp.subproblem_solutions == {}

    def test_empty_subproblem_energies(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        assert decomp.subproblem_energies == {}

    def test_zero_qubo_time(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        assert decomp.qubo_time == 0.0

    def test_zero_merge_time(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        assert decomp.merge_time == 0.0

    def test_zero_total_energy(self):
        decomp = ProblemDecomposition.create_by_resident(3, 10)
        assert decomp.total_energy == 0.0
