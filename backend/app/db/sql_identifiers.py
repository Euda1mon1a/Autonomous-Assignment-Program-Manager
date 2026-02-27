"""Safe SQL identifier handling to prevent SQL injection.

PostgreSQL identifiers (table names, schema names, column names) cannot be
parameterized with bind variables. This module provides validation and quoting
to safely interpolate identifiers into SQL strings.
"""

import re

# Valid unquoted PostgreSQL identifier: starts with letter or underscore,
# followed by letters, digits, or underscores. Max 63 chars.
_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")


def validate_identifier(name: str) -> str:
    """Validate and quote a SQL identifier (table, schema, column name).

    Raises ValueError if the name contains invalid characters.
    Returns the identifier wrapped in double-quotes for safe interpolation.
    """
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(
            f"Invalid SQL identifier: {name!r}. "
            "Must match [a-zA-Z_][a-zA-Z0-9_]{{0,62}}."
        )
    return f'"{name}"'
