"""
Data masking utilities for anonymization.

Provides various masking strategies for different data types:
- Redaction: Complete removal with placeholder
- Hashing: One-way hash transformation
- Partial masking: Show partial data (e.g., last 4 digits)
- Tokenization: Replace with random token
- Format-preserving masking: Maintain data format

Usage:
    from app.privacy.maskers import EmailMasker, PhoneMasker, NameMasker

    email_masker = EmailMasker()
    masked = email_masker.mask("john.doe@example.com")
    # Returns: "j***@example.com" or similar based on strategy
"""

import hashlib
import re
import secrets
import string
from abc import ABC, abstractmethod


class BaseMasker(ABC):
    """Base class for data maskers."""

    @abstractmethod
    def mask(self, value: str) -> str:
        """
        Mask a value.

        Args:
            value: Original value to mask

        Returns:
            Masked value
        """
        pass

    def unmask(self, value: str) -> str:
        """
        Unmask a value (if reversible).

        Args:
            value: Masked value

        Returns:
            Original value

        Raises:
            NotImplementedError: If masking is not reversible
        """
        raise NotImplementedError("This masking strategy is not reversible")


class RedactionMasker(BaseMasker):
    """
    Simple redaction masker - replaces value with placeholder.

    Examples:
        - "john@example.com" -> "[REDACTED]"
        - "555-1234" -> "[REDACTED]"
    """

    def __init__(self, placeholder: str = "[REDACTED]"):
        """
        Initialize redaction masker.

        Args:
            placeholder: Placeholder text to use
        """
        self.placeholder = placeholder

    def mask(self, value: str) -> str:
        """Replace value with placeholder."""
        return self.placeholder


class HashMasker(BaseMasker):
    """
    One-way hash masker using SHA-256.

    Examples:
        - "john@example.com" -> "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
    """

    def __init__(self, algorithm: str = "sha256", truncate: int | None = None):
        """
        Initialize hash masker.

        Args:
            algorithm: Hash algorithm to use (sha256, sha512, md5)
            truncate: Optional truncation length for hash output
        """
        self.algorithm = algorithm
        self.truncate = truncate

    def mask(self, value: str) -> str:
        """Generate hash of value."""
        if self.algorithm == "sha256":
            hash_obj = hashlib.sha256(value.encode())
        elif self.algorithm == "sha512":
            hash_obj = hashlib.sha512(value.encode())
        elif self.algorithm == "md5":
            hash_obj = hashlib.md5(value.encode(), usedforsecurity=False)
        else:
            raise ValueError(f"Unsupported hash algorithm: {self.algorithm}")

        hash_value = hash_obj.hexdigest()

        if self.truncate:
            return hash_value[: self.truncate]

        return hash_value


class PartialMasker(BaseMasker):
    """
    Partial masker - shows beginning/end of value, masks middle.

    Examples:
        - "john@example.com" (show_start=2, show_end=4) -> "jo*****.com"
        - "555-123-4567" (show_start=0, show_end=4) -> "***-***-4567"
    """

    def __init__(self, show_start: int = 1, show_end: int = 4, mask_char: str = "*"):
        """
        Initialize partial masker.

        Args:
            show_start: Number of characters to show at start
            show_end: Number of characters to show at end
            mask_char: Character to use for masking
        """
        self.show_start = show_start
        self.show_end = show_end
        self.mask_char = mask_char

    def mask(self, value: str) -> str:
        """Partially mask value."""
        if len(value) <= (self.show_start + self.show_end):
            # Value too short, mask entirely
            return self.mask_char * len(value)

        start = value[: self.show_start]
        end = value[-self.show_end :] if self.show_end > 0 else ""
        middle_length = len(value) - self.show_start - self.show_end
        middle = self.mask_char * min(middle_length, 5)  # Cap asterisks for readability

        return f"{start}{middle}{end}"


class TokenMasker(BaseMasker):
    """
    Token masker - replaces value with random token.

    Maintains a mapping for reversibility (if enabled).
    """

    def __init__(
        self, token_length: int = 16, reversible: bool = False, prefix: str = "TOK_"
    ):
        """
        Initialize token masker.

        Args:
            token_length: Length of generated token
            reversible: Whether to maintain mapping for unmasking
            prefix: Prefix for tokens
        """
        self.token_length = token_length
        self.reversible = reversible
        self.prefix = prefix
        self._token_map: dict[str, str] = {}  # token -> original
        self._reverse_map: dict[str, str] = {}  # original -> token

    def mask(self, value: str) -> str:
        """Generate and return random token."""
        # Check if we've already tokenized this value
        if self.reversible and value in self._reverse_map:
            return self._reverse_map[value]

        # Generate new token
        token_chars = string.ascii_uppercase + string.digits
        token = "".join(secrets.choice(token_chars) for _ in range(self.token_length))
        full_token = f"{self.prefix}{token}"

        # Store mapping if reversible
        if self.reversible:
            self._token_map[full_token] = value
            self._reverse_map[value] = full_token

        return full_token

    def unmask(self, value: str) -> str:
        """Unmask token to original value."""
        if not self.reversible:
            raise NotImplementedError("Token masker not configured for reversibility")

        if value not in self._token_map:
            raise ValueError(f"Unknown token: {value}")

        return self._token_map[value]


class FormatPreservingMasker(BaseMasker):
    """
    Format-preserving masker - maintains the format of the original data.

    Examples:
        - "555-123-4567" -> "842-957-3281" (random digits, same format)
        - "ABC-1234" -> "XYZ-5678" (random chars/digits, same pattern)
    """

    def __init__(self, preserve_special_chars: bool = True):
        """
        Initialize format-preserving masker.

        Args:
            preserve_special_chars: Whether to preserve special characters
        """
        self.preserve_special_chars = preserve_special_chars

    def mask(self, value: str) -> str:
        """Mask value while preserving format."""
        result = []

        for char in value:
            if char.isdigit():
                result.append(secrets.choice(string.digits))
            elif char.isalpha():
                if char.isupper():
                    result.append(secrets.choice(string.ascii_uppercase))
                else:
                    result.append(secrets.choice(string.ascii_lowercase))
            elif self.preserve_special_chars:
                result.append(char)
            else:
                result.append(secrets.choice(string.ascii_letters))

        return "".join(result)


class EmailMasker(BaseMasker):
    """
    Email-specific masker.

    Strategies:
    - partial: Show first char of username and domain -> "j***@e***.com"
    - hash: Hash username, preserve domain -> "a1b2c3d4@example.com"
    - domain_only: Redact username, preserve domain -> "[REDACTED]@example.com"
    """

    def __init__(self, strategy: str = "partial"):
        """
        Initialize email masker.

        Args:
            strategy: Masking strategy (partial, hash, domain_only)
        """
        self.strategy = strategy

    def mask(self, value: str) -> str:
        """Mask email address."""
        if "@" not in value:
            # Not a valid email, use basic masking
            return PartialMasker(show_start=1, show_end=4).mask(value)

        username, domain = value.split("@", 1)

        if self.strategy == "partial":
            masked_username = PartialMasker(show_start=1, show_end=0).mask(username)
            # Mask domain too
            if "." in domain:
                domain_parts = domain.split(".")
                masked_domain_name = PartialMasker(show_start=1, show_end=0).mask(
                    domain_parts[0]
                )
                masked_domain = f"{masked_domain_name}.{'.'.join(domain_parts[1:])}"
            else:
                masked_domain = PartialMasker(show_start=1, show_end=0).mask(domain)

            return f"{masked_username}@{masked_domain}"

        elif self.strategy == "hash":
            hashed_username = HashMasker(truncate=8).mask(username)
            return f"{hashed_username}@{domain}"

        elif self.strategy == "domain_only":
            return f"[REDACTED]@{domain}"

        else:
            raise ValueError(f"Unknown email masking strategy: {self.strategy}")


class PhoneMasker(BaseMasker):
    """
    Phone number masker.

    Preserves format while masking digits.
    """

    def __init__(self, show_last_digits: int = 4):
        """
        Initialize phone masker.

        Args:
            show_last_digits: Number of digits to show at end
        """
        self.show_last_digits = show_last_digits

    def mask(self, value: str) -> str:
        """Mask phone number, showing only last N digits."""
        # Extract digits
        digits = "".join(c for c in value if c.isdigit())

        if len(digits) <= self.show_last_digits:
            # Too short, mask entirely
            return re.sub(r"\d", "*", value)

        # Mask all but last N digits
        mask_count = len(digits) - self.show_last_digits
        masked_index = 0

        result = []
        for char in value:
            if char.isdigit():
                if masked_index < mask_count:
                    result.append("*")
                    masked_index += 1
                else:
                    result.append(char)
            else:
                result.append(char)

        return "".join(result)


class SSNMasker(BaseMasker):
    """
    Social Security Number masker.

    Shows only last 4 digits: XXX-XX-1234
    """

    def mask(self, value: str) -> str:
        """Mask SSN, showing only last 4 digits."""
        # Extract digits
        digits = "".join(c for c in value if c.isdigit())

        if len(digits) != 9:
            # Invalid SSN, use basic masking
            return "XXX-XX-XXXX"

        last_four = digits[-4:]

        # Preserve original format
        if "-" in value:
            return f"XXX-XX-{last_four}"
        elif " " in value:
            return f"XXX XX {last_four}"
        else:
            return f"XXXXX{last_four}"


class NameMasker(BaseMasker):
    """
    Name masker.

    Strategies:
    - initial: "John Doe" -> "J. D."
    - first_only: "John Doe" -> "J*** Doe"
    - last_only: "John Doe" -> "John D***"
    - full: "John Doe" -> "[NAME REDACTED]"
    """

    def __init__(self, strategy: str = "initial"):
        """
        Initialize name masker.

        Args:
            strategy: Masking strategy (initial, first_only, last_only, full)
        """
        self.strategy = strategy

    def mask(self, value: str) -> str:
        """Mask name."""
        parts = value.split()

        if not parts:
            return value

        if self.strategy == "initial":
            return " ".join(f"{p[0]}." for p in parts)

        elif self.strategy == "first_only":
            if len(parts) == 1:
                return PartialMasker(show_start=1, show_end=0).mask(parts[0])
            return f"{PartialMasker(show_start=1, show_end=0).mask(parts[0])} {' '.join(parts[1:])}"

        elif self.strategy == "last_only":
            if len(parts) == 1:
                return PartialMasker(show_start=0, show_end=1).mask(parts[0])
            last = PartialMasker(show_start=0, show_end=1).mask(parts[-1])
            return f"{' '.join(parts[:-1])} {last}"

        elif self.strategy == "full":
            return "[NAME REDACTED]"

        else:
            raise ValueError(f"Unknown name masking strategy: {self.strategy}")


class MaskerFactory:
    """
    Factory for creating maskers based on PII type.

    Usage:
        factory = MaskerFactory()
        masker = factory.get_masker(PIIType.EMAIL)
        masked_value = masker.mask("john@example.com")
    """

    DEFAULT_MASKERS = {
        "email": EmailMasker,
        "phone": PhoneMasker,
        "ssn": SSNMasker,
        "name": NameMasker,
        "ip_address": PartialMasker,
        "credit_card": lambda: PartialMasker(show_start=0, show_end=4),
        "medical_record": HashMasker,
        "default": RedactionMasker,
    }

    def __init__(self, custom_maskers: dict[str, type[BaseMasker]] | None = None):
        """
        Initialize masker factory.

        Args:
            custom_maskers: Custom masker mappings to override defaults
        """
        self.maskers = self.DEFAULT_MASKERS.copy()
        if custom_maskers:
            self.maskers.update(custom_maskers)

    def get_masker(self, pii_type: str, **kwargs) -> BaseMasker:
        """
        Get masker for PII type.

        Args:
            pii_type: Type of PII (email, phone, ssn, etc.)
            **kwargs: Additional arguments to pass to masker constructor

        Returns:
            Masker instance
        """
        masker_class = self.maskers.get(pii_type, self.maskers["default"])

        # Handle callable factories
        if callable(masker_class) and not isinstance(masker_class, type):
            return masker_class()

        return masker_class(**kwargs)
