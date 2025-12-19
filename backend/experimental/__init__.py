"""
Experimental Test Harness for Novel Scheduling Algorithms.

This package provides isolated testing infrastructure for experimental
scheduling approaches without contaminating production code paths.

Usage:
    python -m experimental.harness --branch quantum-physics --scenario standard
    python -m experimental.harness --compare-all --output reports/comparison.json

Branches tested:
    - quantum-physics: QUBO-based optimization
    - catalyst-concepts: Activation energy pathways
    - transcription-factors: Gene regulatory constraint networks

See docs/research/EXPERIMENTAL_RESEARCH_STRATEGY.md for full documentation.
"""

__version__ = "0.1.0"
