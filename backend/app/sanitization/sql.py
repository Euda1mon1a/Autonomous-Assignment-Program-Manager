"""
SQL injection prevention and sanitization module.

This module provides functions to detect and prevent SQL injection attacks.
Note: The application uses SQLAlchemy ORM which provides protection against
SQL injection by default. These functions are for additional validation and
for cases where raw SQL might be used.

Key features:
- Detect SQL injection patterns
- Validate SQL identifiers (table/column names)
- Sanitize input for parameterized queries
- Pattern-based attack detection
"""

import re


class SQLInjectionError(Exception):
    """Exception raised when SQL injection is detected."""

    pass


# Common SQL injection patterns to detect
SQL_INJECTION_PATTERNS = [
    # Comment-based injection
    r"--",
    r"/\*",
    r"\*/",
    r"#",
    # Union-based injection
    r"\bunion\b.*\bselect\b",
    r"\bor\b.*\b=\b.*\b(or|and)\b",
    # Boolean-based injection
    r"'\s*(or|and)\s*'?\w*'?\s*=\s*'?\w*'?",
    r'"\s*(or|and)\s*"?\w*"?\s*=\s*"?\w*"?',
    r"1\s*=\s*1",
    r"'\s*or\s*'1'\s*=\s*'1",
    r'"\s*or\s*"1"\s*=\s*"1',
    # Time-based injection
    r"\bsleep\s*\(",
    r"\bwaitfor\s+delay\b",
    r"\bbenchmark\s*\(",
    # Stacked queries
    r";\s*(drop|delete|update|insert|create|alter)\s+",
    # System commands
    r"\bexec\s*\(",
    r"\bexecute\s*\(",
    r"\bxp_cmdshell\b",
    # Information schema access
    r"\binformation_schema\b",
    r"\bsys\.\b",
    r"\bsystem\.\b",
    # Database-specific functions
    r"\bload_file\s*\(",
    r"\boutfile\s+",
    r"\bdumpfile\s+",
    # Subqueries
    r"\bselect\b.*\bfrom\b.*\bwhere\b",
]

# Keywords that should not appear in user input
DANGEROUS_SQL_KEYWORDS = {
    "select",
    "insert",
    "update",
    "delete",
    "drop",
    "create",
    "alter",
    "truncate",
    "exec",
    "execute",
    "union",
    "declare",
    "cast",
    "information_schema",
    "sysobjects",
    "syscolumns",
    "xp_cmdshell",
    "sp_executesql",
    "openrowset",
    "openquery",
}

# Valid identifier pattern (alphanumeric + underscore, must start with letter)
VALID_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")


def detect_sql_injection(input_string: str, strict: bool = True) -> bool:
    """
    Detect potential SQL injection patterns in input string.

    Uses pattern matching to identify common SQL injection techniques.
    This is a defense-in-depth measure; SQLAlchemy ORM provides primary protection.

    Args:
        input_string: String to check for SQL injection patterns
        strict: If True, use stricter detection (more false positives)

    Returns:
        True if SQL injection patterns detected, False otherwise

    Example:
        >>> detect_sql_injection("' OR '1'='1")
        True
        >>> detect_sql_injection("normal user input")
        False
        >>> detect_sql_injection("SELECT * FROM users")
        True
    """
    if not input_string:
        return False

    input_lower = input_string.lower()

    # Check for SQL injection patterns
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, input_lower, re.IGNORECASE):
            return True

    # In strict mode, also check for dangerous keywords
    if strict:
        words = re.findall(r"\b\w+\b", input_lower)
        for word in words:
            if word in DANGEROUS_SQL_KEYWORDS:
                return True

    # Check for multiple SQL statements (semicolon followed by keyword)
    if ";" in input_string:
        parts = input_string.split(";")
        if len(parts) > 1:
            for part in parts[1:]:
                part_stripped = part.strip().lower()
                if part_stripped and part_stripped.split()[0] in DANGEROUS_SQL_KEYWORDS:
                    return True

    return False


def sanitize_sql_input(
    input_string: str, max_length: int | None = None, allow_wildcards: bool = False
) -> str:
    """
    Sanitize input for use in SQL queries.

    Note: This should be used in conjunction with parameterized queries,
    not as a replacement. SQLAlchemy handles parameterization automatically.

    Args:
        input_string: String to sanitize
        max_length: Maximum allowed length (truncate if exceeded)
        allow_wildcards: If True, allow SQL wildcards (% and _)

    Returns:
        Sanitized string

    Raises:
        SQLInjectionError: If SQL injection patterns are detected

    Example:
        >>> sanitize_sql_input("normal text")
        'normal text'
        >>> sanitize_sql_input("' OR '1'='1")
        Raises SQLInjectionError
    """
    if not input_string:
        return ""

    # Check for SQL injection patterns
    if detect_sql_injection(input_string, strict=True):
        raise SQLInjectionError(
            "Input contains patterns that may indicate SQL injection attempt"
        )

    # Truncate if max_length specified
    if max_length and len(input_string) > max_length:
        input_string = input_string[:max_length]

    # Remove SQL wildcards unless explicitly allowed
    if not allow_wildcards:
        input_string = input_string.replace("%", "").replace("_", "")

    # Remove null bytes
    input_string = input_string.replace("\x00", "")

    return input_string.strip()


def validate_identifier(identifier: str, max_length: int = 64) -> str:
    """
    Validate SQL identifier (table name, column name, etc.).

    Identifiers must:
    - Start with a letter
    - Contain only letters, numbers, and underscores
    - Not exceed max_length
    - Not be a SQL reserved word

    Args:
        identifier: Identifier to validate
        max_length: Maximum allowed length

    Returns:
        Validated identifier

    Raises:
        SQLInjectionError: If identifier is invalid or dangerous

    Example:
        >>> validate_identifier("users")
        'users'
        >>> validate_identifier("user_table_123")
        'user_table_123'
        >>> validate_identifier("'; DROP TABLE users--")
        Raises SQLInjectionError
    """
    if not identifier:
        raise SQLInjectionError("Identifier cannot be empty")

    if len(identifier) > max_length:
        raise SQLInjectionError(
            f"Identifier too long: {len(identifier)} chars (max: {max_length})"
        )

    # Check pattern
    if not VALID_IDENTIFIER_PATTERN.match(identifier):
        raise SQLInjectionError(
            f"Invalid identifier '{identifier}': must start with letter and "
            "contain only letters, numbers, and underscores"
        )

    # Check against dangerous keywords
    if identifier.lower() in DANGEROUS_SQL_KEYWORDS:
        raise SQLInjectionError(f"Identifier '{identifier}' is a reserved SQL keyword")

    return identifier


def validate_like_pattern(pattern: str, max_length: int = 100) -> str:
    """
    Validate and sanitize LIKE pattern for SQL queries.

    Allows wildcards (% and _) but prevents injection.

    Args:
        pattern: LIKE pattern to validate
        max_length: Maximum allowed length

    Returns:
        Validated pattern

    Raises:
        SQLInjectionError: If pattern contains dangerous content

    Example:
        >>> validate_like_pattern("user%")
        'user%'
        >>> validate_like_pattern("%test_pattern%")
        '%test_pattern%'
    """
    if not pattern:
        return ""

    if len(pattern) > max_length:
        raise SQLInjectionError(
            f"Pattern too long: {len(pattern)} chars (max: {max_length})"
        )

    # Remove wildcards temporarily for injection check
    temp_pattern = pattern.replace("%", "").replace("_", "")

    # Check for SQL injection in non-wildcard parts
    if detect_sql_injection(temp_pattern, strict=True):
        raise SQLInjectionError("LIKE pattern contains dangerous SQL patterns")

    # Remove null bytes
    pattern = pattern.replace("\x00", "")

    return pattern


def escape_like_wildcards(text: str) -> str:
    """
    Escape SQL LIKE wildcards in text for literal matching.

    Escapes % and _ characters so they're treated as literal characters
    in LIKE queries, not wildcards.

    Args:
        text: Text to escape

    Returns:
        Text with wildcards escaped

    Example:
        >>> escape_like_wildcards("50% complete")
        '50\\% complete'
        >>> escape_like_wildcards("file_name.txt")
        'file\\_name.txt'
    """
    if not text:
        return ""

    # Escape backslash first, then wildcards
    text = text.replace("\\", "\\\\")
    text = text.replace("%", "\\%")
    text = text.replace("_", "\\_")

    return text


def is_safe_order_by(column: str, allowed_columns: set[str]) -> bool:
    """
    Validate ORDER BY column against whitelist.

    Prevents SQL injection through dynamic ORDER BY clauses.

    Args:
        column: Column name to use in ORDER BY
        allowed_columns: Set of allowed column names

    Returns:
        True if column is safe to use, False otherwise

    Example:
        >>> is_safe_order_by("created_at", {"id", "name", "created_at"})
        True
        >>> is_safe_order_by("id; DROP TABLE", {"id", "name"})
        False
    """
    if not column or not allowed_columns:
        return False

    # Remove DESC/ASC suffix if present
    column_clean = column.upper().replace(" DESC", "").replace(" ASC", "").strip()

    # Validate identifier format
    try:
        validate_identifier(column_clean)
    except SQLInjectionError:
        return False

    # Check against whitelist
    return column_clean.lower() in {c.lower() for c in allowed_columns}


def sanitize_numeric_id(value: str) -> int | None:
    """
    Sanitize and validate numeric ID input.

    Ensures the value is a valid integer and within safe range.

    Args:
        value: String representation of numeric ID

    Returns:
        Integer ID if valid, None otherwise

    Example:
        >>> sanitize_numeric_id("123")
        123
        >>> sanitize_numeric_id("abc")
        None
        >>> sanitize_numeric_id("123; DROP TABLE")
        None
    """
    if not value:
        return None

    # Remove whitespace
    value = value.strip()

    # Check if it's a valid integer
    try:
        numeric_id = int(value)
    except ValueError:
        return None

    # Check for reasonable range (prevent integer overflow attacks)
    if numeric_id < 0 or numeric_id > 2147483647:  # Max 32-bit signed int
        return None

    return numeric_id


def validate_table_name(table_name: str, allowed_tables: set[str]) -> str:
    """
    Validate table name against whitelist.

    This prevents SQL injection through dynamic table names.

    Args:
        table_name: Table name to validate
        allowed_tables: Set of allowed table names

    Returns:
        Validated table name

    Raises:
        SQLInjectionError: If table name is not in whitelist

    Example:
        >>> validate_table_name("users", {"users", "roles"})
        'users'
        >>> validate_table_name("unknown", {"users", "roles"})
        Raises SQLInjectionError
    """
    if not table_name or not allowed_tables:
        raise SQLInjectionError("Table name validation failed: empty input")

    # Validate identifier format
    validate_identifier(table_name)

    # Check against whitelist
    if table_name.lower() not in {t.lower() for t in allowed_tables}:
        raise SQLInjectionError(
            f"Table '{table_name}' is not in the allowed tables list"
        )

    return table_name


def check_query_complexity(query: str, max_length: int = 1000) -> bool:
    """
    Check if a query appears to be suspiciously complex.

    Useful for detecting potential injection attempts or DoS attacks.

    Args:
        query: Query string to check
        max_length: Maximum allowed query length

    Returns:
        True if query appears safe, False if suspiciously complex

    Example:
        >>> check_query_complexity("SELECT * FROM users")
        True
        >>> check_query_complexity("SELECT " + "* " * 1000 + "FROM users")
        False
    """
    if not query:
        return True

    # Check length
    if len(query) > max_length:
        return False

    # Check for excessive nesting (subqueries)
    if query.count("(") > 10 or query.count(")") > 10:
        return False

    # Check for excessive UNION statements
    union_count = len(re.findall(r"\bunion\b", query, re.IGNORECASE))
    if union_count > 3:
        return False

    return True
