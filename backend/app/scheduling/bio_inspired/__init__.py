"""
Bio-Inspired Optimization for Multi-Objective Schedule Optimization.

This module implements evolutionary and swarm-based optimization algorithms
that complement the existing QUBO quantum approach. These algorithms excel at:

1. Multi-objective optimization with Pareto front discovery
2. Exploring diverse solution spaces
3. Balancing competing objectives (fairness vs preferences vs learning goals)
4. Adaptive search responding to problem structure

Algorithms Implemented:
- Genetic Algorithm (GA): Population-based search with crossover/mutation
- NSGA-II: Non-dominated Sorting GA for multi-objective optimization
- Particle Swarm Optimization (PSO): Swarm intelligence for continuous optimization
- Ant Colony Optimization (ACO): Path finding for rotation sequences
- Hybrid GA-QUBO: Evolutionary problem decomposition with quantum solving

The Evolutionary Lens:
Bio-inspired algorithms view scheduling as an evolutionary process where:
- Chromosomes encode complete schedules
- Fitness functions evaluate multiple objectives simultaneously
- Selection pressure guides the population toward better solutions
- Diversity maintenance prevents premature convergence
- Pareto fronts reveal trade-off surfaces for decision makers

Integration Points:
- Works with existing SchedulingContext and ConstraintManager
- Returns standard SolverResult format
- Can be combined with QUBO solvers in hybrid pipelines
- Exports evolution data for visualization and analysis
"""

from app.scheduling.bio_inspired.base import (
    BioInspiredSolver,
    Chromosome,
    FitnessVector,
    Individual,
    PopulationStats,
)
from app.scheduling.bio_inspired.genetic_algorithm import (
    GeneticAlgorithmSolver,
    CrossoverOperator,
    MutationOperator,
    SelectionOperator,
)
from app.scheduling.bio_inspired.nsga2 import (
    NSGA2Solver,
    ParetoFront,
    CrowdingDistance,
)
from app.scheduling.bio_inspired.particle_swarm import (
    ParticleSwarmSolver,
    Particle,
    SwarmTopology,
)
from app.scheduling.bio_inspired.ant_colony import (
    AntColonySolver,
    AntPath,
    PheromoneMatrix,
)
from app.scheduling.bio_inspired.hybrid_quantum import (
    HybridGAQUBOSolver,
    ProblemDecomposition,
)
from app.scheduling.bio_inspired.visualization import (
    FitnessLandscapeVisualizer,
    EvolutionTracker,
)
from app.scheduling.bio_inspired.export import (
    ParetoExporter,
    EvolutionExporter,
)

__all__ = [
    # Base classes
    "BioInspiredSolver",
    "Chromosome",
    "FitnessVector",
    "Individual",
    "PopulationStats",
    # Genetic Algorithm
    "GeneticAlgorithmSolver",
    "CrossoverOperator",
    "MutationOperator",
    "SelectionOperator",
    # NSGA-II
    "NSGA2Solver",
    "ParetoFront",
    "CrowdingDistance",
    # Particle Swarm
    "ParticleSwarmSolver",
    "Particle",
    "SwarmTopology",
    # Ant Colony
    "AntColonySolver",
    "AntPath",
    "PheromoneMatrix",
    # Hybrid
    "HybridGAQUBOSolver",
    "ProblemDecomposition",
    # Visualization
    "FitnessLandscapeVisualizer",
    "EvolutionTracker",
    # Export
    "ParetoExporter",
    "EvolutionExporter",
]
