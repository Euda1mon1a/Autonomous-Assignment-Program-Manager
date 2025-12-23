"""
Data anonymization service with audit trail support.

Provides comprehensive anonymization capabilities:
- PII detection and masking
- Multiple anonymization strategies
- Batch processing
- Audit trail tracking
- Reversible encryption support

Usage:
    from app.privacy.anonymizer import DataAnonymizer, AnonymizationConfig

    # Simple anonymization
    anonymizer = DataAnonymizer(db_session)
    result = anonymizer.anonymize_record(
        record=person_dict,
        fields=["email", "phone"],
        strategy="mask"
    )

    # Batch anonymization
    results = anonymizer.anonymize_batch(
        records=people_list,
        config=AnonymizationConfig(strategy="pseudonymize", k_anonymity=5)
    )
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.types import GUID
from app.privacy.detectors import PIIDetector, PIIScanner
from app.privacy.maskers import MaskerFactory
from app.privacy.strategies import (
    GeneralizationStrategy,
    KAnonymityStrategy,
    LDiversityStrategy,
    PseudonymizationStrategy,
)

logger = logging.getLogger(__name__)


class AnonymizationMethod(str, Enum):
    """Available anonymization methods."""

    MASK = "mask"  # Mask PII with masking strategy
    PSEUDONYMIZE = "pseudonymize"  # Reversible pseudonymization
    GENERALIZE = "generalize"  # Data generalization
    K_ANONYMITY = "k_anonymity"  # K-anonymity strategy
    L_DIVERSITY = "l_diversity"  # L-diversity strategy
    SUPPRESS = "suppress"  # Data suppression


class AnonymizationConfig(BaseModel):
    """Configuration for anonymization."""

    method: AnonymizationMethod = AnonymizationMethod.MASK
    fields: list[str] | None = Field(
        default=None, description="Specific fields to anonymize"
    )
    detect_pii: bool = Field(default=True, description="Auto-detect PII in fields")
    k_value: int = Field(default=5, description="K value for k-anonymity", ge=2)
    l_value: int = Field(default=3, description="L value for l-diversity", ge=2)
    quasi_identifiers: list[str] | None = Field(
        default=None, description="Quasi-identifier fields for k-anonymity"
    )
    sensitive_attributes: list[str] | None = Field(
        default=None, description="Sensitive attributes to protect"
    )
    encryption_key: str | None = Field(
        default=None, description="Encryption key for reversible pseudonymization"
    )
    preserve_format: bool = Field(
        default=False, description="Preserve data format when masking"
    )
    audit_trail: bool = Field(default=True, description="Create audit trail entry")
    batch_size: int = Field(default=100, description="Batch size for bulk operations")

    class Config:
        use_enum_values = True


class AnonymizationResult(BaseModel):
    """Result of anonymization operation."""

    success: bool
    anonymized_data: Any
    original_count: int
    anonymized_count: int
    audit_id: str | None = None
    errors: list[str] = Field(default_factory=list)
    pii_detected: dict[str, list[str]] = Field(
        default_factory=dict, description="Detected PII by field"
    )


class AnonymizationAudit(Base):
    """
    Audit trail for anonymization operations.

    Tracks when data was anonymized, by whom, and what method was used.
    """

    __tablename__ = "anonymization_audit"

    id = Column(GUID(), primary_key=True, default=uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    method = Column(String(50), nullable=False)
    record_count = Column(String(50))
    fields_anonymized = Column(Text)  # JSON string
    performed_by = Column(String(255))
    reversible = Column(String(10))  # "true" or "false"
    metadata = Column(Text)  # JSON string for additional info

    def __repr__(self):
        return f"<AnonymizationAudit(id={self.id}, method={self.method}, timestamp={self.timestamp})>"


class DataAnonymizer:
    """
    Main service for data anonymization.

    Provides unified interface for various anonymization strategies
    with PII detection and audit trail support.
    """

    def __init__(
        self,
        db: Session | None = None,
        pii_detector: PIIDetector | None = None,
        masker_factory: MaskerFactory | None = None,
    ):
        """
        Initialize data anonymizer.

        Args:
            db: Database session for audit trail (optional)
            pii_detector: Custom PII detector (creates default if None)
            masker_factory: Custom masker factory (creates default if None)
        """
        self.db = db
        self.pii_detector = pii_detector or PIIDetector()
        self.pii_scanner = PIIScanner(self.pii_detector)
        self.masker_factory = masker_factory or MaskerFactory()

    def anonymize_record(
        self,
        record: dict[str, Any],
        config: AnonymizationConfig | None = None,
        **kwargs,
    ) -> AnonymizationResult:
        """
        Anonymize a single record.

        Args:
            record: Record to anonymize
            config: Anonymization configuration
            **kwargs: Additional config overrides

        Returns:
            AnonymizationResult with anonymized data
        """
        config = config or AnonymizationConfig(**kwargs)

        try:
            # Detect PII if enabled
            pii_detected = {}
            if config.detect_pii:
                pii_detected = self.pii_detector.detect_in_dict(record)

            # Determine fields to anonymize
            fields_to_anonymize = config.fields or []
            if config.detect_pii and not fields_to_anonymize:
                # Use detected PII fields
                fields_to_anonymize = list(pii_detected.keys())

            # Apply anonymization
            if config.method == AnonymizationMethod.MASK:
                anonymized = self._mask_record(
                    record, fields_to_anonymize, pii_detected
                )
            elif config.method == AnonymizationMethod.PSEUDONYMIZE:
                anonymized = self._pseudonymize_record(
                    record, fields_to_anonymize, config
                )
            elif config.method == AnonymizationMethod.GENERALIZE:
                anonymized = self._generalize_record(record, config)
            else:
                return AnonymizationResult(
                    success=False,
                    anonymized_data=record,
                    original_count=1,
                    anonymized_count=0,
                    errors=[f"Method {config.method} requires batch processing"],
                )

            # Create audit trail
            audit_id = None
            if config.audit_trail and self.db:
                audit_id = self._create_audit_entry(
                    method=config.method.value,
                    record_count=1,
                    fields=fields_to_anonymize,
                    reversible=config.method == AnonymizationMethod.PSEUDONYMIZE,
                )

            return AnonymizationResult(
                success=True,
                anonymized_data=anonymized,
                original_count=1,
                anonymized_count=1,
                audit_id=str(audit_id) if audit_id else None,
                pii_detected={
                    k: [m.type.value for m in v] for k, v in pii_detected.items()
                },
            )

        except Exception as e:
            logger.error(f"Error anonymizing record: {e}", exc_info=True)
            return AnonymizationResult(
                success=False,
                anonymized_data=record,
                original_count=1,
                anonymized_count=0,
                errors=[str(e)],
            )

    def anonymize_batch(
        self,
        records: list[dict[str, Any]],
        config: AnonymizationConfig | None = None,
        **kwargs,
    ) -> AnonymizationResult:
        """
        Anonymize multiple records.

        Args:
            records: List of records to anonymize
            config: Anonymization configuration
            **kwargs: Additional config overrides

        Returns:
            AnonymizationResult with anonymized data
        """
        config = config or AnonymizationConfig(**kwargs)

        if not records:
            return AnonymizationResult(
                success=True, anonymized_data=[], original_count=0, anonymized_count=0
            )

        try:
            # Apply strategy based on method
            if config.method in (
                AnonymizationMethod.MASK,
                AnonymizationMethod.PSEUDONYMIZE,
                AnonymizationMethod.GENERALIZE,
            ):
                # Process each record individually
                anonymized_records = []
                for record in records:
                    result = self.anonymize_record(record, config)
                    if result.success:
                        anonymized_records.append(result.anonymized_data)
                    else:
                        anonymized_records.append(record)

                anonymized_data = anonymized_records
                success = True

            elif config.method == AnonymizationMethod.K_ANONYMITY:
                # Apply k-anonymity strategy
                strategy = KAnonymityStrategy(k=config.k_value)
                anonymized_data = strategy.apply(
                    records,
                    quasi_identifiers=config.quasi_identifiers or [],
                    sensitive_attributes=config.sensitive_attributes or [],
                )
                success = True

            elif config.method == AnonymizationMethod.L_DIVERSITY:
                # Apply l-diversity strategy
                if not config.sensitive_attributes:
                    raise ValueError(
                        "L-diversity requires sensitive_attributes to be specified"
                    )

                strategy = LDiversityStrategy(l=config.l_value)
                anonymized_data = strategy.apply(
                    records,
                    quasi_identifiers=config.quasi_identifiers or [],
                    sensitive_attribute=config.sensitive_attributes[0],
                )
                success = True

            else:
                return AnonymizationResult(
                    success=False,
                    anonymized_data=records,
                    original_count=len(records),
                    anonymized_count=0,
                    errors=[f"Unknown method: {config.method}"],
                )

            # Create audit trail
            audit_id = None
            if config.audit_trail and self.db:
                audit_id = self._create_audit_entry(
                    method=config.method.value,
                    record_count=len(records),
                    fields=config.fields or config.quasi_identifiers or [],
                    reversible=config.method == AnonymizationMethod.PSEUDONYMIZE,
                )

            return AnonymizationResult(
                success=success,
                anonymized_data=anonymized_data,
                original_count=len(records),
                anonymized_count=len(anonymized_data),
                audit_id=str(audit_id) if audit_id else None,
            )

        except Exception as e:
            logger.error(f"Error in batch anonymization: {e}", exc_info=True)
            return AnonymizationResult(
                success=False,
                anonymized_data=records,
                original_count=len(records),
                anonymized_count=0,
                errors=[str(e)],
            )

    def _mask_record(
        self, record: dict[str, Any], fields: list[str], pii_detected: dict[str, Any]
    ) -> dict[str, Any]:
        """Mask PII in record using appropriate maskers."""
        result = record.copy()

        for field in fields:
            if field not in result:
                continue

            value = result[field]
            if not isinstance(value, str):
                continue

            # Determine PII type for this field
            pii_type = None
            if field in pii_detected and pii_detected[field]:
                pii_type = pii_detected[field][0].type.value

            # Get appropriate masker
            masker = self.masker_factory.get_masker(pii_type or "default")
            result[field] = masker.mask(value)

        return result

    def _pseudonymize_record(
        self, record: dict[str, Any], fields: list[str], config: AnonymizationConfig
    ) -> dict[str, Any]:
        """Pseudonymize record using reversible encryption."""
        # Get or generate encryption key
        encryption_key = None
        if config.encryption_key:
            encryption_key = config.encryption_key.encode()

        strategy = PseudonymizationStrategy(
            encryption_key=encryption_key, use_encryption=True
        )

        return strategy.apply(record, fields=fields)

    def _generalize_record(
        self, record: dict[str, Any], config: AnonymizationConfig
    ) -> dict[str, Any]:
        """Generalize record data."""
        # Build generalization rules from config
        rules = {}
        for field in config.fields or []:
            # Default generalization for common field types
            if "age" in field.lower():
                rules[field] = {"type": "range", "bin_size": 10}
            elif "zip" in field.lower() or "postal" in field.lower():
                rules[field] = {"type": "prefix", "length": 3}
            elif "salary" in field.lower() or "income" in field.lower():
                rules[field] = {"type": "range", "bin_size": 10000}
            else:
                rules[field] = {"type": "prefix", "length": 3}

        strategy = GeneralizationStrategy(generalization_rules=rules)
        return strategy.apply(record)

    def _create_audit_entry(
        self, method: str, record_count: int, fields: list[str], reversible: bool
    ) -> UUID | None:
        """Create audit trail entry."""
        if not self.db:
            return None

        try:
            import json

            audit = AnonymizationAudit(
                id=uuid4(),
                method=method,
                record_count=str(record_count),
                fields_anonymized=json.dumps(fields),
                reversible="true" if reversible else "false",
                timestamp=datetime.utcnow(),
            )

            self.db.add(audit)
            self.db.commit()

            return audit.id

        except Exception as e:
            logger.error(f"Error creating audit entry: {e}")
            self.db.rollback()
            return None

    def get_audit_history(
        self, limit: int = 100, method: str | None = None
    ) -> list[AnonymizationAudit]:
        """
        Get audit history of anonymization operations.

        Args:
            limit: Maximum number of entries to return
            method: Filter by anonymization method

        Returns:
            List of audit entries
        """
        if not self.db:
            return []

        query = self.db.query(AnonymizationAudit)

        if method:
            query = query.filter(AnonymizationAudit.method == method)

        query = query.order_by(AnonymizationAudit.timestamp.desc()).limit(limit)

        return query.all()


class BatchAnonymizer:
    """
    Batch anonymization processor with progress tracking.

    Useful for anonymizing large datasets with memory efficiency.
    """

    def __init__(self, anonymizer: DataAnonymizer, batch_size: int = 100):
        """
        Initialize batch anonymizer.

        Args:
            anonymizer: DataAnonymizer instance
            batch_size: Number of records to process per batch
        """
        self.anonymizer = anonymizer
        self.batch_size = batch_size

    def process_in_batches(
        self,
        records: list[dict[str, Any]],
        config: AnonymizationConfig,
        progress_callback: Any = None,
    ) -> AnonymizationResult:
        """
        Process records in batches.

        Args:
            records: All records to anonymize
            config: Anonymization configuration
            progress_callback: Optional callback function(processed, total)

        Returns:
            Combined AnonymizationResult
        """
        total_records = len(records)
        all_anonymized = []
        all_errors = []

        for i in range(0, total_records, self.batch_size):
            batch = records[i : i + self.batch_size]

            result = self.anonymizer.anonymize_batch(batch, config)

            if result.success:
                all_anonymized.extend(result.anonymized_data)
            else:
                all_errors.extend(result.errors)

            # Progress callback
            if progress_callback:
                progress_callback(i + len(batch), total_records)

        return AnonymizationResult(
            success=len(all_errors) == 0,
            anonymized_data=all_anonymized,
            original_count=total_records,
            anonymized_count=len(all_anonymized),
            errors=all_errors,
        )
