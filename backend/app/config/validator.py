"""Configuration validation module.

Validates configuration data before applying changes to ensure
system integrity and prevent invalid configurations.
"""

import logging
from typing import Any

from pydantic import ValidationError

from app.core.config import Settings

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ConfigValidator:
    """Validates configuration data against defined schemas and rules."""

    # Fields that cannot be changed at runtime (require restart)
    IMMUTABLE_FIELDS: set[str] = {
        "DATABASE_URL",
        "CELERY_BROKER_URL",
        "CELERY_RESULT_BACKEND",
    }

    # Fields that require special validation
    CRITICAL_FIELDS: set[str] = {
        "SECRET_KEY",
        "WEBHOOK_SECRET",
        "RESILIENCE_MAX_UTILIZATION",
        "RESILIENCE_CRITICAL_THRESHOLD",
    }

    def __init__(self) -> None:
        """Initialize the configuration validator."""
        self.validation_errors: list[str] = []

    def validate(
        self,
        new_config: dict[str, Any],
        current_config: Settings | None = None,
    ) -> bool:
        """
        Validate configuration data.

        Args:
            new_config: New configuration dictionary to validate
            current_config: Current configuration for comparison (optional)

        Returns:
            bool: True if validation passes, False otherwise

        Raises:
            ConfigValidationError: If critical validation errors are found
        """
        self.validation_errors = []

        try:
            # Validate against Pydantic schema
            self._validate_schema(new_config)

            # Validate immutable fields haven't changed
            if current_config:
                self._validate_immutable_fields(new_config, current_config)

                # Validate critical fields
            self._validate_critical_fields(new_config)

            # Validate resilience thresholds
            self._validate_resilience_thresholds(new_config)

            # Validate rate limiting settings
            self._validate_rate_limiting(new_config)

            # Validate file upload settings
            self._validate_file_upload_settings(new_config)

            if self.validation_errors:
                error_msg = "\n".join(self.validation_errors)
                raise ConfigValidationError(
                    f"Configuration validation failed:\n{error_msg}"
                )

            logger.info("Configuration validation passed")
            return True

        except ValidationError as e:
            logger.error(f"Pydantic validation error: {e}")
            raise ConfigValidationError(f"Schema validation failed: {e}")

    def _validate_schema(self, config: dict[str, Any]) -> None:
        """
        Validate configuration against Pydantic schema.

        Args:
            config: Configuration dictionary

        Raises:
            ValidationError: If Pydantic validation fails
        """
        try:
            # Create Settings instance to validate schema
            Settings(**config)
        except ValidationError as e:
            logger.error(f"Schema validation failed: {e}")
            raise

    def _validate_immutable_fields(
        self,
        new_config: dict[str, Any],
        current_config: Settings,
    ) -> None:
        """
        Validate that immutable fields haven't changed.

        Args:
            new_config: New configuration dictionary
            current_config: Current configuration
        """
        for field in self.IMMUTABLE_FIELDS:
            new_value = new_config.get(field)
            current_value = getattr(current_config, field, None)

            if new_value is not None and new_value != current_value:
                self.validation_errors.append(
                    f"Field '{field}' is immutable and cannot be changed at runtime. "
                    f"Restart required for this change."
                )

    def _validate_critical_fields(self, config: dict[str, Any]) -> None:
        """
        Validate critical security and operational fields.

        Args:
            config: Configuration dictionary
        """
        # Validate SECRET_KEY
        secret_key = config.get("SECRET_KEY", "")
        if secret_key and len(secret_key) < 32:
            self.validation_errors.append(
                "SECRET_KEY must be at least 32 characters long"
            )

            # Validate WEBHOOK_SECRET
        webhook_secret = config.get("WEBHOOK_SECRET", "")
        if webhook_secret and len(webhook_secret) < 32:
            self.validation_errors.append(
                "WEBHOOK_SECRET must be at least 32 characters long"
            )

    def _validate_resilience_thresholds(self, config: dict[str, Any]) -> None:
        """
        Validate resilience framework thresholds.

        Ensures thresholds are in correct order and within valid ranges.

        Args:
            config: Configuration dictionary
        """
        warning = config.get("RESILIENCE_WARNING_THRESHOLD", 0.70)
        max_util = config.get("RESILIENCE_MAX_UTILIZATION", 0.80)
        critical = config.get("RESILIENCE_CRITICAL_THRESHOLD", 0.90)
        emergency = config.get("RESILIENCE_EMERGENCY_THRESHOLD", 0.95)

        # Validate ranges (0.0 to 1.0)
        thresholds = {
            "RESILIENCE_WARNING_THRESHOLD": warning,
            "RESILIENCE_MAX_UTILIZATION": max_util,
            "RESILIENCE_CRITICAL_THRESHOLD": critical,
            "RESILIENCE_EMERGENCY_THRESHOLD": emergency,
        }

        for name, value in thresholds.items():
            if not 0.0 <= value <= 1.0:
                self.validation_errors.append(
                    f"{name} must be between 0.0 and 1.0, got {value}"
                )

                # Validate ordering
        if not (warning <= max_util <= critical <= emergency):
            self.validation_errors.append(
                f"Resilience thresholds must be in ascending order: "
                f"WARNING ({warning}) <= MAX ({max_util}) <= "
                f"CRITICAL ({critical}) <= EMERGENCY ({emergency})"
            )

            # Warn about dangerous values
        if max_util > 0.85:
            logger.warning(
                f"RESILIENCE_MAX_UTILIZATION ({max_util}) is above recommended "
                f"maximum of 0.85. System may experience performance degradation."
            )

    def _validate_rate_limiting(self, config: dict[str, Any]) -> None:
        """
        Validate rate limiting configuration.

        Args:
            config: Configuration dictionary
        """
        login_attempts = config.get("RATE_LIMIT_LOGIN_ATTEMPTS", 5)
        register_attempts = config.get("RATE_LIMIT_REGISTER_ATTEMPTS", 3)

        if login_attempts < 1:
            self.validation_errors.append(
                "RATE_LIMIT_LOGIN_ATTEMPTS must be at least 1"
            )

        if register_attempts < 1:
            self.validation_errors.append(
                "RATE_LIMIT_REGISTER_ATTEMPTS must be at least 1"
            )

            # Warn about overly permissive settings
        if login_attempts > 20:
            logger.warning(
                f"RATE_LIMIT_LOGIN_ATTEMPTS ({login_attempts}) is very high. "
                f"Consider lowering to improve security."
            )

    def _validate_file_upload_settings(self, config: dict[str, Any]) -> None:
        """
        Validate file upload configuration.

        Args:
            config: Configuration dictionary
        """
        max_size = config.get("UPLOAD_MAX_SIZE_MB", 50)
        backend = config.get("UPLOAD_STORAGE_BACKEND", "local")

        if max_size < 1:
            self.validation_errors.append("UPLOAD_MAX_SIZE_MB must be at least 1")

        if max_size > 500:
            logger.warning(
                f"UPLOAD_MAX_SIZE_MB ({max_size}) is very large. "
                f"Consider implications for storage and bandwidth."
            )

        if backend not in ["local", "s3"]:
            self.validation_errors.append(
                f"UPLOAD_STORAGE_BACKEND must be 'local' or 's3', got '{backend}'"
            )

            # Validate S3 settings if S3 backend is configured
        if backend == "s3":
            required_s3_fields = ["UPLOAD_S3_BUCKET", "UPLOAD_S3_REGION"]
            for field in required_s3_fields:
                if not config.get(field):
                    self.validation_errors.append(
                        f"{field} is required when UPLOAD_STORAGE_BACKEND='s3'"
                    )

    def get_validation_errors(self) -> list[str]:
        """
        Get list of validation errors from last validation.

        Returns:
            List[str]: List of validation error messages
        """
        return self.validation_errors

    def validate_partial(
        self,
        partial_config: dict[str, Any],
        current_config: Settings,
    ) -> dict[str, Any]:
        """
        Validate partial configuration update.

        Merges partial config with current config and validates the result.

        Args:
            partial_config: Partial configuration to apply
            current_config: Current configuration

        Returns:
            Dict[str, Any]: Complete merged configuration

        Raises:
            ConfigValidationError: If validation fails
        """
        # Merge with current config
        merged_config = current_config.model_dump()
        merged_config.update(partial_config)

        # Validate merged config
        self.validate(merged_config, current_config)

        return merged_config
