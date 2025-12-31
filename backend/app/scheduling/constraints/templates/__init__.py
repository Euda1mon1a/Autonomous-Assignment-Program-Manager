"""
Constraint Templates Package

This package contains templates for creating new constraints in the scheduling system.

Templates are organized by constraint type:
    - hard_constraint_template: Base hard constraint template
    - soft_constraint_template: Base soft constraint template
    - composite_constraint_template: Multi-constraint groups
    - temporal_constraint_template: Time-based constraints
    - resource_constraint_template: Resource allocation constraints
    - preference_constraint_template: Individual preferences
    - fairness_constraint_template: Equitable distribution
    - coverage_constraint_template: Coverage requirements
    - sequence_constraint_template: Ordered relationships
    - exclusion_constraint_template: Prohibition constraints

Usage:
    1. Copy a template file
    2. Implement constraint logic
    3. Add tests
    4. Register in constraint_manager.py

See README.md for detailed instructions.
"""

from .hard_constraint_template import MyConstraint as HardConstraintTemplate
from .soft_constraint_template import MyConstraint as SoftConstraintTemplate

__all__ = [
    "HardConstraintTemplate",
    "SoftConstraintTemplate",
]
