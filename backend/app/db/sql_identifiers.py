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


# PostgreSQL special search_path variables (passed through as-is)
_SEARCH_PATH_SPECIALS = frozenset(
    {'"$user"', "$user", "public", "pg_temp", "pg_catalog"}
)

# Matches a double-quoted identifier: "schema_name" or "MySchema"
_QUOTED_IDENTIFIER_RE = re.compile(r'^"([^"]+)"$')


def validate_search_path(search_path: str) -> str:
    """Validate a PostgreSQL search_path value (comma-separated schemas).

    SHOW search_path returns values like '"$user", public' which contain
    multiple schemas. Each component is validated individually.
    Handles: unquoted identifiers, quoted identifiers, and special variables
    ($user, public, pg_temp, pg_catalog).

    Returns the validated search_path string safe for SET search_path TO.
    """
    parts = [p.strip() for p in search_path.split(",")]
    safe_parts = []
    for part in parts:
        if not part:
            continue
        if part in _SEARCH_PATH_SPECIALS:
            safe_parts.append(part)
        elif _IDENTIFIER_RE.match(part):
            # Unquoted valid identifier — quote it for safety
            safe_parts.append(f'"{part}"')
        else:
            match = _QUOTED_IDENTIFIER_RE.match(part)
            if match:
                # Already double-quoted identifier (e.g. "MySchema") — validate inner
                inner = match.group(1)
                if _IDENTIFIER_RE.match(inner):
                    safe_parts.append(f'"{inner}"')
                else:
                    raise ValueError(
                        f"Invalid quoted identifier in search_path: {part!r}."
                    )
            else:
                raise ValueError(
                    f"Invalid search_path component: {part!r}. "
                    "Must be a valid identifier or a special variable."
                )
    return ", ".join(safe_parts)
