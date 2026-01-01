"""
Constants for Bio-Inspired Optimization Algorithms.

This module centralizes default parameter values used across genetic algorithms,
particle swarm optimization, ant colony optimization, and NSGA-II implementations.
These values are tuned for typical residency scheduling problems.

Constant Categories
-------------------

**Fitness Evaluation Constants**
    Default weights for multi-objective scalarization and ACGME thresholds.
    ACGME compliance is weighted highest (0.30) as regulatory requirement.

**Population Initialization Constants**
    Chromosome density and diversity sampling parameters.

**PSO Constants**
    Swarm size, inertia, cognitive/social coefficients for weight optimization.
    Default configuration balances exploration and exploitation.

**ACO Constants**
    Colony size, alpha/beta (pheromone/heuristic importance), evaporation.
    Tuned for rotation sequence optimization.

**NSGA-II Constants**
    Population size, genetic operator rates for multi-objective optimization.
    Larger default population (100) for Pareto front diversity.

Parameter Tuning Guidelines
---------------------------

**For smaller problems** (< 20 residents):

.. code-block:: python

    # Reduce population sizes
    population_size = int(NSGA2_DEFAULT_POPULATION_SIZE * 0.6)
    swarm_size = int(PSO_DEFAULT_SWARM_SIZE * 0.6)
    colony_size = int(ACO_DEFAULT_COLONY_SIZE * 0.6)

**For larger problems** (> 50 residents):

.. code-block:: python

    # Increase population sizes and iterations
    population_size = int(NSGA2_DEFAULT_POPULATION_SIZE * 1.5)
    max_generations = int(NSGA2_DEFAULT_MAX_GENERATIONS * 1.5)

**For faster runtime** (interactive/real-time):

.. code-block:: python

    # Aggressive early stopping, smaller populations
    population_size = 30
    max_generations = 50
    early_stop_generations = 15

**For better solution quality** (overnight runs):

.. code-block:: python

    # Larger populations, more iterations
    population_size = 200
    max_generations = 500
    early_stop_generations = 100

Objective Weight Rationale
--------------------------

The default weights sum to 1.0 and prioritize:

1. **ACGME Compliance (0.30)**: Regulatory requirement, non-negotiable
2. **Coverage (0.25)**: Need assignments for operational schedule
3. **Fairness (0.15)**: Workload distribution matters for morale
4. **Preferences (0.10)**: Resident satisfaction is important but flexible
5. **Learning Goals (0.10)**: Educational variety can be adjusted
6. **Continuity (0.10)**: Rotation stability is nice-to-have

Customize for your program's priorities:

.. code-block:: python

    # Fairness-focused (resident wellbeing priority)
    weights = {
        "coverage": 0.20,
        "fairness": 0.35,
        "acgme_compliance": 0.25,
        "preferences": 0.10,
        "learning_goals": 0.05,
        "continuity": 0.05,
    }

    # Education-focused (academic priority)
    weights = {
        "coverage": 0.20,
        "fairness": 0.10,
        "acgme_compliance": 0.25,
        "preferences": 0.05,
        "learning_goals": 0.30,
        "continuity": 0.10,
    }

Usage
-----

Import constants for algorithm configuration:

.. code-block:: python

    from app.scheduling.bio_inspired.constants import (
        DEFAULT_COVERAGE_WEIGHT,
        PSO_DEFAULT_SWARM_SIZE,
        ACO_DEFAULT_ALPHA,
        NSGA2_DEFAULT_POPULATION_SIZE,
    )

All constants are module-level for easy access and modification.
"""

# ==============================================================================
# Fitness Evaluation Constants
# ==============================================================================

# Default objective weights for multi-objective scalarization
DEFAULT_COVERAGE_WEIGHT = 0.25
DEFAULT_FAIRNESS_WEIGHT = 0.15
DEFAULT_PREFERENCES_WEIGHT = 0.10
DEFAULT_LEARNING_GOALS_WEIGHT = 0.10
DEFAULT_ACGME_COMPLIANCE_WEIGHT = 0.30
DEFAULT_CONTINUITY_WEIGHT = 0.10

# ACGME compliance approximation
MAX_BLOCKS_PER_WEEK = 13  # ~80 hours at 6 hours/block
APPROXIMATE_BLOCKS_PER_WEEK = 10  # Used for weekly chunk calculations
ACGME_WEEKLY_LIMIT_BLOCKS = 13  # Maximum blocks per week threshold

# ==============================================================================
# Population Initialization Constants
# ==============================================================================

# Chromosome density variation range
DENSITY_VARIATION_MIN = 0.8
DENSITY_VARIATION_RANGE = 0.4

# Population diversity sampling
DIVERSITY_SAMPLE_SIZE = 20  # Sample size for pairwise similarity

# ==============================================================================
# Particle Swarm Optimization (PSO) Constants
# ==============================================================================

# Population parameters
PSO_DEFAULT_SWARM_SIZE = 50
PSO_DEFAULT_MAX_ITERATIONS = 200

# PSO algorithm parameters
PSO_DEFAULT_INERTIA_WEIGHT = 0.7  # w: momentum
PSO_DEFAULT_COGNITIVE_COEFF = 1.5  # c1: attraction to personal best
PSO_DEFAULT_SOCIAL_COEFF = 1.5  # c2: attraction to global/local best
PSO_DEFAULT_VELOCITY_CLAMP = 0.5  # Max velocity magnitude

# Adaptive inertia parameters
PSO_INERTIA_MIN = 0.4
PSO_INERTIA_MAX = 0.9

# Search space bounds
PSO_DEFAULT_DIMENSION = 6  # Number of objective weights to optimize
PSO_POSITION_MIN = 0.0
PSO_POSITION_MAX = 1.0

# Convergence parameters
PSO_EARLY_STOP_ITERATIONS = 30
PSO_CONVERGENCE_THRESHOLD = 0.001  # Fitness improvement threshold
PSO_LOG_INTERVAL = 20  # Log progress every N iterations

# Velocity initialization
PSO_VELOCITY_RANGE_MULTIPLIER = 0.1

# Topology parameters
PSO_RANDOM_TOPOLOGY_MIN_NEIGHBORS = 3  # Minimum neighbors in random topology

# Weight normalization
PSO_MIN_WEIGHT_VALUE = 0.001  # Minimum weight to prevent zeros

# Schedule generation parameters
PSO_DENSITY_BASE = 0.3
PSO_DENSITY_RANGE = 0.4
PSO_ASSIGNMENT_MULTIPLIER = 0.3
PSO_WEEKLY_LOOKBACK_BLOCKS = 10

# ==============================================================================
# Ant Colony Optimization (ACO) Constants
# ==============================================================================

# Population parameters
ACO_DEFAULT_COLONY_SIZE = 50
ACO_DEFAULT_MAX_ITERATIONS = 200

# ACO algorithm parameters
ACO_DEFAULT_ALPHA = 1.0  # Pheromone importance
ACO_DEFAULT_BETA = 2.0  # Heuristic importance
ACO_DEFAULT_EVAPORATION_RATE = 0.1
ACO_DEFAULT_INITIAL_PHEROMONE = 1.0

# Elite ant strategies
ACO_DEFAULT_ELITE_COUNT = 5
ACO_DEFAULT_ELITE_FACTOR = 2.0

# Pheromone bounds
ACO_MIN_PHEROMONE = 0.01
ACO_MAX_PHEROMONE = 10.0

# Local search parameters
ACO_LOCAL_SEARCH_ITERATIONS = 5
ACO_TOP_K_FOR_LOCAL_SEARCH = 5

# Convergence parameters
ACO_EARLY_STOP_ITERATIONS = 30
ACO_CONVERGENCE_THRESHOLD = 0.001
ACO_LOG_INTERVAL = 20

# Heuristic matrix parameters
ACO_UNAVAILABLE_SLOT_HEURISTIC = 0.1
ACO_UNASSIGNED_BOOST = 1.5

# Pheromone analysis
ACO_HOTSPOT_PERCENTILE = 90  # Percentile for identifying high-pheromone regions
ACO_STRONG_TRANSITION_THRESHOLD = 2.0  # Pheromone level for preferred transitions

# ==============================================================================
# NSGA-II Constants
# ==============================================================================

# Population parameters
NSGA2_DEFAULT_POPULATION_SIZE = 100
NSGA2_DEFAULT_MAX_GENERATIONS = 200

# Genetic operators
NSGA2_DEFAULT_CROSSOVER_RATE = 0.9
NSGA2_DEFAULT_MUTATION_RATE = 0.1

# Selection parameters
NSGA2_DEFAULT_TOURNAMENT_SIZE = 2  # Binary tournament

# Convergence parameters
NSGA2_EARLY_STOP_GENERATIONS = 50
NSGA2_CONVERGENCE_THRESHOLD = 0.001  # Hypervolume stability threshold
NSGA2_LOG_INTERVAL = 20

# Pareto front analysis
NSGA2_TOP_RISK_RESIDENTS = 5  # Number of highest-risk residents to track

# ==============================================================================
# Common Constants
# ==============================================================================

# General convergence
CONVERGENCE_IMPROVEMENT_THRESHOLD = 0.001

# Logging intervals
DEFAULT_LOG_INTERVAL = 20  # Log every 20 iterations/generations
