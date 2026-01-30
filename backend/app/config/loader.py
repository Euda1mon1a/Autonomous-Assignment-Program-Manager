"""Configuration loader module.

Loads configuration from environment variables and .env files,
with support for hot reload and environment merging.
"""

import logging
import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

from app.core.config import Settings

logger = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""

    pass


class ConfigLoader:
    """Loads configuration from files and environment variables."""

    def __init__(
        self,
        env_file: Path | None = None,
        env_file_encoding: str = "utf-8",
    ) -> None:
        """
        Initialize the configuration loader.

        Args:
            env_file: Path to .env file (defaults to .env in project root)
            env_file_encoding: Encoding for .env file
        """
        self.env_file = env_file or self._find_env_file()
        self.env_file_encoding = env_file_encoding
        self._last_modified: float | None = None

    def _find_env_file(self) -> Path:
        """
        Find .env file in project root.

        Returns:
            Path: Path to .env file

        Raises:
            ConfigLoadError: If .env file cannot be found
        """
        # Start from current file and go up to find project root
        current_dir = Path(__file__).resolve().parent
        for _ in range(5):  # Search up to 5 levels
            env_path = current_dir / ".env"
            if env_path.exists():
                logger.info(f"Found .env file at: {env_path}")
                return env_path
            current_dir = current_dir.parent

            # Default to backend/.env
        backend_root = Path(__file__).resolve().parent.parent.parent
        default_path = backend_root / ".env"
        logger.warning(f".env file not found, using default path: {default_path}")
        return default_path

    def load(self) -> Settings:
        """
        Load configuration from environment and .env file.

        Environment variables take precedence over .env file values.

        Returns:
            Settings: Loaded configuration

        Raises:
            ConfigLoadError: If configuration cannot be loaded
        """
        try:
            # Load from .env file
            env_values = self._load_env_file()

            # Merge with environment variables (env vars take precedence)
            merged_config = self._merge_with_environment(env_values)

            # Create Settings instance
            settings = Settings(**merged_config)

            # Track last modified time
            if self.env_file.exists():
                self._last_modified = self.env_file.stat().st_mtime

            logger.info("Configuration loaded successfully")
            return settings

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise ConfigLoadError(f"Configuration load failed: {e}")

    def _load_env_file(self) -> dict[str, Any]:
        """
        Load configuration from .env file.

        Returns:
            Dict[str, Any]: Configuration from .env file
        """
        if not self.env_file.exists():
            logger.warning(f".env file not found at: {self.env_file}")
            return {}

        try:
            # Use dotenv_values to parse .env file
            env_values = dotenv_values(
                self.env_file,
                encoding=self.env_file_encoding,
            )

            # Convert to proper types
            config = self._convert_types(env_values)

            logger.debug(f"Loaded {len(config)} values from .env file: {self.env_file}")
            return config

        except Exception as e:
            logger.error(f"Error reading .env file: {e}")
            raise ConfigLoadError(f"Failed to read .env file: {e}")

    def _merge_with_environment(
        self,
        file_config: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Merge .env file config with environment variables.

        Environment variables take precedence over file values.

        Args:
            file_config: Configuration from .env file

        Returns:
            Dict[str, Any]: Merged configuration
        """
        merged = file_config.copy()

        # Get all Settings field names
        settings_fields = Settings.model_fields.keys()

        # Override with environment variables
        for field in settings_fields:
            env_value = os.getenv(field)
            if env_value is not None:
                merged[field] = self._convert_value(field, env_value)

        return merged

    def _convert_types(self, env_values: dict[str, str | None]) -> dict[str, Any]:
        """
        Convert environment variable strings to appropriate types.

        Args:
            env_values: Raw environment variable values

        Returns:
            Dict[str, Any]: Converted values
        """
        config = {}

        for key, value in env_values.items():
            if value is None:
                continue

            config[key] = self._convert_value(key, value)

        return config

    def _convert_value(self, key: str, value: str) -> Any:
        """
        Convert a single environment variable to appropriate type.

        Args:
            key: Configuration key
            value: String value from environment

        Returns:
            Any: Converted value
        """
        # Boolean values
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

            # Integer values
        if value.isdigit():
            return int(value)

            # Float values
        try:
            if "." in value:
                return float(value)
        except ValueError:
            pass

            # List values (comma-separated)
        if key in [
            "CORS_ORIGINS",
            "TRUSTED_HOSTS",
            "RESILIENCE_ALERT_RECIPIENTS",
        ]:
            return [item.strip() for item in value.split(",") if item.strip()]

            # String value (default)
        return value

    def has_changed(self) -> bool:
        """
        Check if .env file has been modified since last load.

        Returns:
            bool: True if file has changed, False otherwise
        """
        if not self.env_file.exists():
            return False

        if self._last_modified is None:
            return True

        current_mtime = self.env_file.stat().st_mtime
        return current_mtime > self._last_modified

    def reload(self) -> Settings:
        """
        Reload configuration from files.

        Returns:
            Settings: Reloaded configuration

        Raises:
            ConfigLoadError: If reload fails
        """
        logger.info("Reloading configuration...")
        return self.load()

    def load_partial(self, updates: dict[str, Any]) -> dict[str, Any]:
        """
        Load partial configuration updates.

        Args:
            updates: Partial configuration updates

        Returns:
            Dict[str, Any]: Processed configuration updates
        """
        return self._convert_types(updates)

    def get_env_file_path(self) -> Path:
        """
        Get path to .env file.

        Returns:
            Path: Path to .env file
        """
        return self.env_file

    def get_config_dict(self) -> dict[str, Any]:
        """
        Load configuration as dictionary.

        Returns:
            Dict[str, Any]: Configuration dictionary

        Raises:
            ConfigLoadError: If loading fails
        """
        settings = self.load()
        return settings.model_dump()
