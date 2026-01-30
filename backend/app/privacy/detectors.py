"""
PII (Personally Identifiable Information) detection utilities.

This module provides detectors for various types of PII including:
- Email addresses
- Phone numbers
- Social Security Numbers (SSN)
- Names
- IP addresses
- Credit card numbers
- Medical record numbers

Usage:
    from app.privacy.detectors import PIIDetector, PIIType

    detector = PIIDetector()
    results = detector.detect_all("Contact John at john@example.com or 555-1234")
    # Returns: [PIIMatch(type=PIIType.EMAIL, value='john@example.com', start=13, end=31), ...]
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PIIType(str, Enum):
    """Types of personally identifiable information."""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    NAME = "name"
    IP_ADDRESS = "ip_address"
    CREDIT_CARD = "credit_card"
    MEDICAL_RECORD = "medical_record"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    CUSTOM = "custom"


@dataclass
class PIIMatch:
    """Represents a detected PII match."""

    type: PIIType
    value: str
    start: int
    end: int
    confidence: float = 1.0
    metadata: dict[str, Any] | None = None


class PIIDetector:
    """
    Detector for personally identifiable information in text.

    Uses regex patterns and heuristics to identify PII.
    """

    # Regex patterns for PII detection
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    PHONE_PATTERN = re.compile(
        r"\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
    )

    SSN_PATTERN = re.compile(
        r"\b(?!000|666|9\d{2})([0-8]\d{2}|7([0-6]\d))([-\s]?)(?!00)\d{2}\3(?!0000)\d{4}\b"
    )

    IP_PATTERN = re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
    )

    # Credit card pattern (basic Luhn algorithm validation can be added)
    CREDIT_CARD_PATTERN = re.compile(
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b"
    )

    # Medical record number pattern (MRN) - common formats
    MRN_PATTERN = re.compile(
        r"\b(?:MRN|mrn|medical\s*record)[\s:]*([A-Z0-9]{6,12})\b", re.IGNORECASE
    )

    # Date of birth patterns
    DOB_PATTERN = re.compile(
        r"\b(?:DOB|dob|date\s*of\s*birth)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
        re.IGNORECASE,
    )

    # Common name prefixes/titles for name detection
    NAME_PREFIXES = {
        "dr",
        "doctor",
        "mr",
        "mrs",
        "ms",
        "miss",
        "prof",
        "professor",
        "capt",
        "captain",
        "lt",
        "lieutenant",
        "col",
        "colonel",
        "maj",
        "major",
        "sgt",
        "sergeant",
    }

    def __init__(
        self,
        enable_name_detection: bool = False,
        custom_patterns: dict[str, re.Pattern] | None = None,
    ) -> None:
        """
        Initialize PII detector.

        Args:
            enable_name_detection: Enable heuristic name detection (may have false positives)
            custom_patterns: Additional custom regex patterns to detect
        """
        self.enable_name_detection = enable_name_detection
        self.custom_patterns = custom_patterns or {}

    def detect_all(self, text: str) -> list[PIIMatch]:
        """
        Detect all types of PII in text.

        Args:
            text: Text to scan for PII

        Returns:
            List of PIIMatch objects representing detected PII
        """
        matches = []

        # Detect each PII type
        matches.extend(self.detect_emails(text))
        matches.extend(self.detect_phones(text))
        matches.extend(self.detect_ssn(text))
        matches.extend(self.detect_ip_addresses(text))
        matches.extend(self.detect_credit_cards(text))
        matches.extend(self.detect_medical_records(text))
        matches.extend(self.detect_dates_of_birth(text))

        if self.enable_name_detection:
            matches.extend(self.detect_names(text))

            # Detect custom patterns
        for pii_type, pattern in self.custom_patterns.items():
            matches.extend(
                self._detect_pattern(text, pattern, PIIType.CUSTOM, pii_type)
            )

            # Sort by position in text
        matches.sort(key=lambda m: m.start)

        return matches

    def detect_emails(self, text: str) -> list[PIIMatch]:
        """Detect email addresses."""
        return self._detect_pattern(text, self.EMAIL_PATTERN, PIIType.EMAIL)

    def detect_phones(self, text: str) -> list[PIIMatch]:
        """Detect phone numbers."""
        return self._detect_pattern(text, self.PHONE_PATTERN, PIIType.PHONE)

    def detect_ssn(self, text: str) -> list[PIIMatch]:
        """Detect Social Security Numbers."""
        return self._detect_pattern(text, self.SSN_PATTERN, PIIType.SSN)

    def detect_ip_addresses(self, text: str) -> list[PIIMatch]:
        """Detect IP addresses."""
        return self._detect_pattern(text, self.IP_PATTERN, PIIType.IP_ADDRESS)

    def detect_credit_cards(self, text: str) -> list[PIIMatch]:
        """Detect credit card numbers."""
        matches = self._detect_pattern(
            text, self.CREDIT_CARD_PATTERN, PIIType.CREDIT_CARD
        )

        # Validate using Luhn algorithm
        validated_matches = []
        for match in matches:
            if self._validate_luhn(match.value):
                validated_matches.append(match)

        return validated_matches

    def detect_medical_records(self, text: str) -> list[PIIMatch]:
        """Detect medical record numbers."""
        return self._detect_pattern(text, self.MRN_PATTERN, PIIType.MEDICAL_RECORD)

    def detect_dates_of_birth(self, text: str) -> list[PIIMatch]:
        """Detect dates of birth."""
        return self._detect_pattern(text, self.DOB_PATTERN, PIIType.DATE_OF_BIRTH)

    def detect_names(self, text: str) -> list[PIIMatch]:
        """
        Detect potential names using heuristics.

        Note: This is heuristic-based and may have false positives.
        Only enabled when enable_name_detection=True.
        """
        matches = []

        # Look for name prefixes followed by capitalized words
        pattern = re.compile(
            r"\b("
            + "|".join(self.NAME_PREFIXES)
            + r")\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b",
            re.IGNORECASE,
        )

        for match in pattern.finditer(text):
            matches.append(
                PIIMatch(
                    type=PIIType.NAME,
                    value=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    confidence=0.7,  # Lower confidence for heuristic detection
                    metadata={"prefix": match.group(1), "name": match.group(2)},
                )
            )

        return matches

    def detect_in_dict(self, data: dict[str, Any]) -> dict[str, list[PIIMatch]]:
        """
        Detect PII in dictionary values (recursively).

        Args:
            data: Dictionary to scan for PII

        Returns:
            Dictionary mapping field paths to detected PII matches
        """
        results = {}

        def scan_value(value: Any, path: str) -> None:
            if isinstance(value, str):
                matches = self.detect_all(value)
                if matches:
                    results[path] = matches
            elif isinstance(value, dict):
                for key, val in value.items():
                    scan_value(val, f"{path}.{key}" if path else key)
            elif isinstance(value, (list, tuple)):
                for idx, item in enumerate(value):
                    scan_value(item, f"{path}[{idx}]")

        scan_value(data, "")
        return results

    def _detect_pattern(
        self,
        text: str,
        pattern: re.Pattern,
        pii_type: PIIType,
        custom_name: str | None = None,
    ) -> list[PIIMatch]:
        """Helper method to detect PII using regex pattern."""
        matches = []

        for match in pattern.finditer(text):
            matches.append(
                PIIMatch(
                    type=pii_type,
                    value=match.group(0),
                    start=match.start(),
                    end=match.end(),
                    confidence=1.0,
                    metadata={"custom_type": custom_name} if custom_name else None,
                )
            )

        return matches

    def _validate_luhn(self, card_number: str) -> bool:
        """
        Validate credit card number using Luhn algorithm.

        Args:
            card_number: Credit card number string

        Returns:
            True if valid according to Luhn algorithm
        """
        # Remove spaces and dashes
        digits = "".join(c for c in card_number if c.isdigit())

        if not digits:
            return False

            # Luhn algorithm
        checksum = 0
        reverse_digits = digits[::-1]

        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            checksum += n

        return checksum % 10 == 0


class PIIScanner:
    """
    High-level scanner for detecting PII in various data structures.

    Provides convenient methods for scanning models, dictionaries, and lists.
    """

    def __init__(self, detector: PIIDetector | None = None) -> None:
        """
        Initialize PII scanner.

        Args:
            detector: PIIDetector instance to use (creates default if None)
        """
        self.detector = detector or PIIDetector()

    def scan_model(
        self, model: Any, exclude_fields: set[str] | None = None
    ) -> dict[str, list[PIIMatch]]:
        """
        Scan SQLAlchemy model instance for PII.

        Args:
            model: SQLAlchemy model instance
            exclude_fields: Set of field names to exclude from scanning

        Returns:
            Dictionary mapping field names to detected PII matches
        """
        exclude_fields = exclude_fields or set()
        results = {}

        # Get model columns
        if hasattr(model, "__table__"):
            for column in model.__table__.columns:
                if column.name in exclude_fields:
                    continue

                value = getattr(model, column.name, None)
                if isinstance(value, str):
                    matches = self.detector.detect_all(value)
                    if matches:
                        results[column.name] = matches

        return results

    def scan_records(
        self, records: list[Any], exclude_fields: set[str] | None = None
    ) -> list[dict[str, list[PIIMatch]]]:
        """
        Scan multiple records for PII.

        Args:
            records: List of model instances or dictionaries
            exclude_fields: Set of field names to exclude

        Returns:
            List of PII detection results for each record
        """
        results = []

        for record in records:
            if isinstance(record, dict):
                pii_matches = self.detector.detect_in_dict(record)
            else:
                pii_matches = self.scan_model(record, exclude_fields)

            results.append(pii_matches)

        return results

    def has_pii(self, text: str) -> bool:
        """
        Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected
        """
        return len(self.detector.detect_all(text)) > 0
