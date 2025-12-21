"""
Privacy and data anonymization package.

Provides comprehensive privacy protection utilities including:
- PII (Personally Identifiable Information) detection
- Data masking and redaction
- Pseudonymization with reversible encryption
- K-anonymity and L-diversity strategies
- Audit trail for anonymization operations
- Batch processing support

Quick Start:
    from app.privacy import DataAnonymizer, AnonymizationConfig

    # Simple masking
    anonymizer = DataAnonymizer()
    result = anonymizer.anonymize_record(
        record={"name": "John Doe", "email": "john@example.com"},
        fields=["email"]
    )

    # K-anonymity for dataset
    from app.privacy import AnonymizationMethod

    config = AnonymizationConfig(
        method=AnonymizationMethod.K_ANONYMITY,
        k_value=5,
        quasi_identifiers=["age", "zipcode"]
    )
    result = anonymizer.anonymize_batch(records, config)

Modules:
    - detectors: PII detection utilities
    - maskers: Data masking strategies
    - strategies: Advanced anonymization strategies (k-anonymity, l-diversity)
    - anonymizer: Main anonymization service with audit trail
"""

from app.privacy.anonymizer import (
    AnonymizationConfig,
    AnonymizationMethod,
    AnonymizationResult,
    BatchAnonymizer,
    DataAnonymizer,
)
from app.privacy.detectors import PIIDetector, PIIMatch, PIIScanner, PIIType
from app.privacy.maskers import (
    BaseMasker,
    EmailMasker,
    HashMasker,
    MaskerFactory,
    NameMasker,
    PartialMasker,
    PhoneMasker,
    RedactionMasker,
    SSNMasker,
    TokenMasker,
)
from app.privacy.strategies import (
    AnonymizationStrategy,
    GeneralizationStrategy,
    KAnonymityStrategy,
    LDiversityStrategy,
    PseudonymizationStrategy,
)

__all__ = [
    # Main anonymizer
    "DataAnonymizer",
    "BatchAnonymizer",
    "AnonymizationConfig",
    "AnonymizationMethod",
    "AnonymizationResult",
    # PII Detection
    "PIIDetector",
    "PIIScanner",
    "PIIType",
    "PIIMatch",
    # Maskers
    "BaseMasker",
    "MaskerFactory",
    "RedactionMasker",
    "HashMasker",
    "PartialMasker",
    "TokenMasker",
    "EmailMasker",
    "PhoneMasker",
    "SSNMasker",
    "NameMasker",
    # Strategies
    "AnonymizationStrategy",
    "PseudonymizationStrategy",
    "KAnonymityStrategy",
    "LDiversityStrategy",
    "GeneralizationStrategy",
]

__version__ = "1.0.0"
