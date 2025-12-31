"""
Custom exceptions for CLI.
"""


class CLIError(Exception):
    """Base exception for CLI errors."""

    pass


class AuthenticationError(CLIError):
    """Raised when authentication fails."""

    pass


class APIError(CLIError):
    """Raised when API request fails."""

    def __init__(self, status_code: int, message: str):
        """
        Initialize API error.

        Args:
            status_code: HTTP status code
            message: Error message
        """
        self.status_code = status_code
        super().__init__(f"API Error {status_code}: {message}")


class ValidationError(CLIError):
    """Raised when input validation fails."""

    pass


class ConfigurationError(CLIError):
    """Raised when configuration is invalid."""

    pass


class DatabaseError(CLIError):
    """Raised when database operation fails."""

    pass
