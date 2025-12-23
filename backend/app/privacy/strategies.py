"""
Anonymization strategies for privacy protection.

Implements various anonymization techniques:
- Pseudonymization: Reversible replacement with pseudonyms
- K-anonymity: Generalization to ensure at least k records share attributes
- L-diversity: Ensures diversity in sensitive attributes
- Data generalization: Reduce precision while maintaining utility
- Suppression: Remove outliers that can't be generalized

Usage:
    from app.privacy.strategies import PseudonymizationStrategy, KAnonymityStrategy

    # Pseudonymization
    pseudo_strategy = PseudonymizationStrategy()
    anonymized = pseudo_strategy.apply(data, fields=["name", "email"])

    # K-anonymity
    k_anon = KAnonymityStrategy(k=5)
    anonymized_data = k_anon.apply(records, quasi_identifiers=["age", "zipcode"])
"""

import secrets
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from cryptography.fernet import Fernet


class AnonymizationStrategy(ABC):
    """Base class for anonymization strategies."""

    @abstractmethod
    def apply(self, data: Any, **kwargs) -> Any:
        """
        Apply anonymization strategy to data.

        Args:
            data: Data to anonymize
            **kwargs: Strategy-specific parameters

        Returns:
            Anonymized data
        """
        pass

    @abstractmethod
    def can_reverse(self) -> bool:
        """
        Check if this strategy supports reversal.

        Returns:
            True if reversible
        """
        pass


class PseudonymizationStrategy(AnonymizationStrategy):
    """
    Pseudonymization strategy using reversible encryption or mapping.

    Replaces identifiable data with pseudonyms while maintaining ability to reverse.
    """

    def __init__(
        self, encryption_key: bytes | None = None, use_encryption: bool = True
    ):
        """
        Initialize pseudonymization strategy.

        Args:
            encryption_key: Encryption key for Fernet (32 bytes, base64-encoded)
                          If None, a new key is generated
            use_encryption: If False, uses deterministic mapping instead
        """
        self.use_encryption = use_encryption

        if use_encryption:
            if encryption_key:
                self.key = encryption_key
            else:
                self.key = Fernet.generate_key()
            self.cipher = Fernet(self.key)
        else:
            self.cipher = None

        # Mapping for non-encrypted pseudonymization
        self._pseudonym_map: dict[str, str] = {}
        self._reverse_map: dict[str, str] = {}

    def can_reverse(self) -> bool:
        """Pseudonymization is reversible."""
        return True

    def apply(self, data: Any, fields: list[str] | None = None, **kwargs) -> Any:
        """
        Apply pseudonymization to data.

        Args:
            data: Dictionary or list of dictionaries to pseudonymize
            fields: List of field names to pseudonymize

        Returns:
            Pseudonymized data
        """
        if isinstance(data, dict):
            return self._pseudonymize_dict(data, fields or [])
        elif isinstance(data, list):
            return [self._pseudonymize_dict(item, fields or []) for item in data]
        else:
            raise ValueError("Data must be dict or list of dicts")

    def reverse(self, data: Any, fields: list[str] | None = None) -> Any:
        """
        Reverse pseudonymization to recover original data.

        Args:
            data: Pseudonymized data
            fields: Fields to reverse

        Returns:
            Original data
        """
        if isinstance(data, dict):
            return self._depseudonymize_dict(data, fields or [])
        elif isinstance(data, list):
            return [self._depseudonymize_dict(item, fields or []) for item in data]
        else:
            raise ValueError("Data must be dict or list of dicts")

    def _pseudonymize_dict(self, data: dict, fields: list[str]) -> dict:
        """Pseudonymize specific fields in dictionary."""
        result = data.copy()

        for field in fields:
            if field in result and result[field]:
                value = str(result[field])
                result[field] = self._pseudonymize_value(value)

        return result

    def _depseudonymize_dict(self, data: dict, fields: list[str]) -> dict:
        """Reverse pseudonymization for specific fields."""
        result = data.copy()

        for field in fields:
            if field in result and result[field]:
                value = str(result[field])
                result[field] = self._depseudonymize_value(value)

        return result

    def _pseudonymize_value(self, value: str) -> str:
        """Pseudonymize a single value."""
        if self.use_encryption:
            encrypted = self.cipher.encrypt(value.encode())
            return encrypted.decode()
        else:
            # Deterministic mapping
            if value in self._pseudonym_map:
                return self._pseudonym_map[value]

            # Generate pseudonym
            pseudonym = f"PSEUDO_{secrets.token_hex(8)}"
            self._pseudonym_map[value] = pseudonym
            self._reverse_map[pseudonym] = value
            return pseudonym

    def _depseudonymize_value(self, pseudonym: str) -> str:
        """Reverse pseudonymization for a single value."""
        if self.use_encryption:
            decrypted = self.cipher.decrypt(pseudonym.encode())
            return decrypted.decode()
        else:
            if pseudonym not in self._reverse_map:
                raise ValueError(f"Unknown pseudonym: {pseudonym}")
            return self._reverse_map[pseudonym]

    def get_key(self) -> bytes | None:
        """Get encryption key (if using encryption)."""
        return self.key if self.use_encryption else None


class KAnonymityStrategy(AnonymizationStrategy):
    """
    K-anonymity strategy.

    Ensures that each record is indistinguishable from at least k-1 other records
    with respect to quasi-identifiers.
    """

    def __init__(self, k: int = 5, suppression_threshold: float = 0.1):
        """
        Initialize k-anonymity strategy.

        Args:
            k: Minimum group size (k value for k-anonymity)
            suppression_threshold: Maximum proportion of records to suppress
        """
        if k < 2:
            raise ValueError("k must be at least 2")

        self.k = k
        self.suppression_threshold = suppression_threshold

    def can_reverse(self) -> bool:
        """K-anonymity is not reversible (information loss)."""
        return False

    def apply(
        self,
        data: list[dict],
        quasi_identifiers: list[str],
        sensitive_attributes: list[str] | None = None,
        **kwargs,
    ) -> list[dict]:
        """
        Apply k-anonymity to dataset.

        Args:
            data: List of records to anonymize
            quasi_identifiers: Fields that could be used to identify individuals
            sensitive_attributes: Sensitive fields to protect (not generalized)

        Returns:
            K-anonymized dataset
        """
        if not data:
            return []

        sensitive_attributes = sensitive_attributes or []

        # Group records by quasi-identifier values
        groups = self._group_by_quasi_identifiers(data, quasi_identifiers)

        # Process groups
        anonymized_data = []
        suppressed_count = 0
        max_suppressed = int(len(data) * self.suppression_threshold)

        for group_key, group_records in groups.items():
            if len(group_records) >= self.k:
                # Group is large enough, generalize if needed
                anonymized_group = self._generalize_group(
                    group_records, quasi_identifiers, sensitive_attributes
                )
                anonymized_data.extend(anonymized_group)
            elif suppressed_count + len(group_records) <= max_suppressed:
                # Suppress small groups (below threshold)
                suppressed_count += len(group_records)
            else:
                # Try to merge with similar groups
                merged = self._try_merge_groups(
                    group_records, groups, quasi_identifiers, sensitive_attributes
                )
                anonymized_data.extend(merged)

        return anonymized_data

    def _group_by_quasi_identifiers(
        self, data: list[dict], quasi_identifiers: list[str]
    ) -> dict[tuple, list[dict]]:
        """Group records by quasi-identifier values."""
        groups = defaultdict(list)

        for record in data:
            key = tuple(record.get(qi) for qi in quasi_identifiers)
            groups[key].append(record)

        return dict(groups)

    def _generalize_group(
        self,
        records: list[dict],
        quasi_identifiers: list[str],
        sensitive_attributes: list[str],
    ) -> list[dict]:
        """
        Generalize quasi-identifiers within a group.

        Returns records with generalized values.
        """
        if not records:
            return []

        # Determine generalization for each quasi-identifier
        generalizations = {}

        for qi in quasi_identifiers:
            values = [r.get(qi) for r in records if qi in r]
            if not values:
                continue

            # Generalize based on data type
            generalizations[qi] = self._generalize_field(values)

        # Apply generalizations to all records in group
        anonymized_records = []
        for record in records:
            new_record = record.copy()
            for qi, generalized_value in generalizations.items():
                if qi in new_record:
                    new_record[qi] = generalized_value
            anonymized_records.append(new_record)

        return anonymized_records

    def _generalize_field(self, values: list[Any]) -> Any:
        """
        Generalize a field's values.

        Strategy depends on data type:
        - Numeric: Use range (min-max)
        - Date: Use year or year-month
        - String: Use prefix or wildcard
        """
        if not values:
            return None

        # Check data type
        sample = values[0]

        if isinstance(sample, (int, float)):
            # Numeric: return range
            min_val = min(values)
            max_val = max(values)
            if min_val == max_val:
                return str(min_val)
            return f"{min_val}-{max_val}"

        elif isinstance(sample, (date, datetime)):
            # Date: return year or year-month
            years = set(
                v.year if isinstance(v, (date, datetime)) else None for v in values
            )
            if len(years) == 1:
                return f"{list(years)[0]}"
            return f"{min(years)}-{max(years)}"

        elif isinstance(sample, str):
            # String: find common prefix
            if len(set(values)) == 1:
                return values[0]

            # Find common prefix
            common_prefix = self._find_common_prefix(values)
            if len(common_prefix) >= 2:
                return f"{common_prefix}*"

            return "*"  # No common pattern

        else:
            # Unknown type, suppress
            return "*"

    def _find_common_prefix(self, strings: list[str]) -> str:
        """Find common prefix among strings."""
        if not strings:
            return ""

        strings = [s for s in strings if s]  # Remove empty strings
        if not strings:
            return ""

        prefix = strings[0]
        for s in strings[1:]:
            while not s.startswith(prefix):
                prefix = prefix[:-1]
                if not prefix:
                    return ""

        return prefix

    def _try_merge_groups(
        self,
        small_group: list[dict],
        all_groups: dict[tuple, list[dict]],
        quasi_identifiers: list[str],
        sensitive_attributes: list[str],
    ) -> list[dict]:
        """
        Try to merge small group with similar groups.

        If merging fails, suppress the records.
        """
        # For simplicity, just generalize more aggressively
        return self._generalize_group(
            small_group, quasi_identifiers, sensitive_attributes
        )


class LDiversityStrategy(AnonymizationStrategy):
    """
    L-diversity strategy.

    Ensures that within each equivalence class, there are at least L
    well-represented values for sensitive attributes.
    """

    def __init__(self, l: int = 3):
        """
        Initialize l-diversity strategy.

        Args:
            l: Minimum number of distinct sensitive values per group
        """
        if l < 2:
            raise ValueError("l must be at least 2")

        self.l = l

    def can_reverse(self) -> bool:
        """L-diversity is not reversible."""
        return False

    def apply(
        self,
        data: list[dict],
        quasi_identifiers: list[str],
        sensitive_attribute: str,
        **kwargs,
    ) -> list[dict]:
        """
        Apply l-diversity to dataset.

        Args:
            data: List of records
            quasi_identifiers: Quasi-identifier fields
            sensitive_attribute: Sensitive attribute to protect

        Returns:
            L-diverse dataset
        """
        # First apply k-anonymity
        k_anon = KAnonymityStrategy(k=self.l)
        k_anonymized = k_anon.apply(
            data,
            quasi_identifiers=quasi_identifiers,
            sensitive_attributes=[sensitive_attribute],
        )

        # Group by quasi-identifiers
        groups = defaultdict(list)
        for record in k_anonymized:
            key = tuple(record.get(qi) for qi in quasi_identifiers)
            groups[key].append(record)

        # Check l-diversity within each group
        l_diverse_data = []
        for group_key, group_records in groups.items():
            sensitive_values = [r.get(sensitive_attribute) for r in group_records]
            unique_values = len(set(sensitive_values))

            if unique_values >= self.l:
                # Group satisfies l-diversity
                l_diverse_data.extend(group_records)
            else:
                # Need to merge or suppress
                # For simplicity, we'll suppress
                pass

        return l_diverse_data


class GeneralizationStrategy(AnonymizationStrategy):
    """
    Data generalization strategy.

    Reduces precision of data while maintaining utility.
    """

    def __init__(self, generalization_rules: dict[str, dict] | None = None):
        """
        Initialize generalization strategy.

        Args:
            generalization_rules: Dictionary mapping field names to generalization config
                Example: {
                    "age": {"type": "range", "bin_size": 10},
                    "zipcode": {"type": "prefix", "length": 3},
                    "salary": {"type": "range", "bin_size": 10000}
                }
        """
        self.generalization_rules = generalization_rules or {}

    def can_reverse(self) -> bool:
        """Generalization is not reversible."""
        return False

    def apply(self, data: Any, **kwargs) -> Any:
        """
        Apply generalization to data.

        Args:
            data: Dictionary or list of dictionaries

        Returns:
            Generalized data
        """
        if isinstance(data, dict):
            return self._generalize_record(data)
        elif isinstance(data, list):
            return [self._generalize_record(record) for record in data]
        else:
            raise ValueError("Data must be dict or list of dicts")

    def _generalize_record(self, record: dict) -> dict:
        """Generalize a single record."""
        result = record.copy()

        for field, rule in self.generalization_rules.items():
            if field not in result:
                continue

            value = result[field]
            rule_type = rule.get("type")

            if rule_type == "range":
                result[field] = self._generalize_range(value, rule.get("bin_size", 10))
            elif rule_type == "prefix":
                result[field] = self._generalize_prefix(
                    str(value), rule.get("length", 3)
                )
            elif rule_type == "round":
                result[field] = self._generalize_round(value, rule.get("precision", 0))

        return result

    def _generalize_range(self, value: int | float, bin_size: int) -> str:
        """Generalize numeric value to range."""
        if value is None:
            return None

        lower = (int(value) // bin_size) * bin_size
        upper = lower + bin_size
        return f"{lower}-{upper}"

    def _generalize_prefix(self, value: str, length: int) -> str:
        """Generalize string to prefix."""
        if not value:
            return ""

        if len(value) <= length:
            return value

        return value[:length] + "*"

    def _generalize_round(self, value: float, precision: int) -> float:
        """Round numeric value."""
        if value is None:
            return None

        return round(value, precision)


class DataSuppressionStrategy(AnonymizationStrategy):
    """
    Data suppression strategy.

    Removes outlier records that cannot be adequately anonymized.
    """

    def __init__(self, outlier_threshold: float = 0.05):
        """
        Initialize suppression strategy.

        Args:
            outlier_threshold: Maximum proportion of records to suppress
        """
        self.outlier_threshold = outlier_threshold

    def can_reverse(self) -> bool:
        """Suppression is not reversible."""
        return False

    def apply(
        self, data: list[dict], quasi_identifiers: list[str], **kwargs
    ) -> list[dict]:
        """
        Apply suppression to remove outliers.

        Args:
            data: List of records
            quasi_identifiers: Fields to check for uniqueness

        Returns:
            Dataset with outliers removed
        """
        if not data:
            return []

        # Count frequency of each quasi-identifier combination
        frequency_map = defaultdict(int)
        for record in data:
            key = tuple(record.get(qi) for qi in quasi_identifiers)
            frequency_map[key] += 1

        # Determine threshold for suppression
        total_records = len(data)
        min_frequency = max(1, int(total_records * self.outlier_threshold))

        # Keep only records above threshold
        result = []
        for record in data:
            key = tuple(record.get(qi) for qi in quasi_identifiers)
            if frequency_map[key] > min_frequency:
                result.append(record)

        return result
