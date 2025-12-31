"""
Test seed data for database initialization.

Provides pre-configured datasets for different testing needs:
- Minimal dataset: Fastest setup for unit tests
- Full year dataset: Complete academic year for integration tests
- Stress test dataset: Large-scale data for performance testing

Usage:
    from tests.seed_data import MinimalDataset

    # Seed database with minimal data
    data = MinimalDataset.seed(db)

    # Use seeded data in tests
    resident = data["residents"][0]
    assignments = data["assignments"]
"""

from tests.seed_data.full_year_dataset import FullYearDataset
from tests.seed_data.minimal_dataset import MinimalDataset
from tests.seed_data.stress_test_dataset import StressTestDataset

__all__ = [
    "MinimalDataset",
    "FullYearDataset",
    "StressTestDataset",
]
