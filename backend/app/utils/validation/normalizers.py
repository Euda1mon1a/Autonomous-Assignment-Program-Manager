"""
Data normalization utility functions.

Normalizes data to standard formats:
- Phone numbers
- Names
- Emails
- Addresses
"""

import re
import unicodedata


def normalize_phone(phone: str, default_country_code: str = "1") -> str:
    """
    Normalize phone number to standard format.

    Args:
        phone: Phone number to normalize
        default_country_code: Default country code (default: "1" for US)

    Returns:
        str: Normalized phone number (digits only)
    """
    if not phone:
        return ""

    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    # Add country code if not present (US: 11 digits)
    if len(digits) == 10:
        digits = default_country_code + digits

    return digits


def normalize_name(name: str) -> str:
    """
    Normalize person name to standard format.

    Args:
        name: Name to normalize

    Returns:
        str: Normalized name (title case, cleaned whitespace)
    """
    if not name:
        return ""

    # Normalize Unicode characters
    name = unicodedata.normalize("NFKC", name)

    # Remove extra whitespace
    name = " ".join(name.split())

    # Title case (preserving special names like McDonald, O'Brien)
    parts = []
    for part in name.split():
        # Handle hyphenated names
        if "-" in part:
            hyphen_parts = [p.capitalize() for p in part.split("-")]
            parts.append("-".join(hyphen_parts))
        # Handle apostrophes (O'Brien, D'Angelo)
        elif "'" in part:
            apos_parts = [p.capitalize() for p in part.split("'")]
            parts.append("'".join(apos_parts))
        else:
            parts.append(part.capitalize())

    return " ".join(parts)


def normalize_email(email: str) -> str:
    """
    Normalize email address to standard format.

    Args:
        email: Email address to normalize

    Returns:
        str: Normalized email (lowercase, trimmed)
    """
    if not email:
        return ""

    # Trim and lowercase
    email = email.strip().lower()

    # Normalize Unicode
    email = unicodedata.normalize("NFKC", email)

    return email


def normalize_text(
    text: str,
    lowercase: bool = False,
    remove_extra_whitespace: bool = True,
) -> str:
    """
    Normalize text to standard format.

    Args:
        text: Text to normalize
        lowercase: Convert to lowercase
        remove_extra_whitespace: Remove extra whitespace

    Returns:
        str: Normalized text
    """
    if not text:
        return ""

    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)

    # Remove extra whitespace if requested
    if remove_extra_whitespace:
        text = " ".join(text.split())

    # Lowercase if requested
    if lowercase:
        text = text.lower()

    return text.strip()


def normalize_date_string(
    date_string: str,
    input_format: str = "%Y-%m-%d",
) -> str:
    """
    Normalize date string to ISO format (YYYY-MM-DD).

    Args:
        date_string: Date string to normalize
        input_format: Expected input format

    Returns:
        str: Normalized date string (ISO format)

    Raises:
        ValueError: If date string cannot be parsed
    """
    from datetime import datetime

    if not date_string:
        return ""

    try:
        dt = datetime.strptime(date_string.strip(), input_format)
        return dt.strftime("%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Cannot parse date '{date_string}' with format '{input_format}'") from e


def normalize_specialty(specialty: str) -> str:
    """
    Normalize medical specialty name.

    Args:
        specialty: Specialty name to normalize

    Returns:
        str: Normalized specialty name
    """
    # Common specialty abbreviations to full names
    specialty_map = {
        "fm": "Family Medicine",
        "fam med": "Family Medicine",
        "sports med": "Sports Medicine",
        "sm": "Sports Medicine",
        "derm": "Dermatology",
        "peds": "Pediatrics",
        "ob/gyn": "Obstetrics and Gynecology",
        "obgyn": "Obstetrics and Gynecology",
        "im": "Internal Medicine",
        "em": "Emergency Medicine",
        "psych": "Psychiatry",
        "rad": "Radiology",
        "anes": "Anesthesiology",
        "path": "Pathology",
    }

    normalized = normalize_text(specialty, lowercase=True)

    # Check if it's an abbreviation
    if normalized in specialty_map:
        return specialty_map[normalized]

    # Return title case version
    return normalize_name(specialty)


def normalize_rotation_name(rotation: str) -> str:
    """
    Normalize rotation name.

    Args:
        rotation: Rotation name to normalize

    Returns:
        str: Normalized rotation name
    """
    # Common rotation abbreviations
    rotation_map = {
        "fmit": "FMIT",
        "clinic": "Clinic",
        "inpt": "Inpatient",
        "inpatient": "Inpatient",
        "ob": "OB/GYN",
        "peds": "Pediatrics",
        "er": "Emergency",
        "ed": "Emergency",
    }

    normalized = normalize_text(rotation, lowercase=True)

    if normalized in rotation_map:
        return rotation_map[normalized]

    return normalize_name(rotation)


def normalize_boolean(value: str | bool | int) -> bool:
    """
    Normalize various representations of boolean values.

    Args:
        value: Value to normalize (can be string, bool, or int)

    Returns:
        bool: Normalized boolean value

    Examples:
        >>> normalize_boolean("yes")
        True
        >>> normalize_boolean("no")
        False
        >>> normalize_boolean(1)
        True
        >>> normalize_boolean("false")
        False
    """
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    if isinstance(value, str):
        value_lower = value.lower().strip()
        true_values = ["true", "yes", "y", "1", "on", "t"]
        false_values = ["false", "no", "n", "0", "off", "f"]

        if value_lower in true_values:
            return True
        elif value_lower in false_values:
            return False

    raise ValueError(f"Cannot normalize '{value}' to boolean")
