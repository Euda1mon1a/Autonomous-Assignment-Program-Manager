"""Configuration registry module.

Central registry for configuration with hot reload, change notifications,
and rollback capabilities.
"""

import asyncio
import logging
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config.loader import ConfigLoader, ConfigLoadError
from app.config.validator import ConfigValidationError, ConfigValidator
from app.config.watcher import ConfigWatcher
from app.core.config import Settings

logger = logging.getLogger(__name__)


class ConfigChangeEvent:
    """Event triggered when configuration changes."""

    def __init__(
        self,
        old_config: Settings,
        new_config: Settings,
        changed_fields: list[str],
        source: str = "unknown",
    ):
        """
        Initialize config change event.

        Args:
            old_config: Previous configuration
            new_config: New configuration
            changed_fields: List of fields that changed
            source: Source of the change (e.g., "file", "api", "manual")
        """
        self.old_config = old_config
        self.new_config = new_config
        self.changed_fields = changed_fields
        self.source = source
        self.timestamp = datetime.utcnow()

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConfigChangeEvent(changed_fields={self.changed_fields}, "
            f"source={self.source}, timestamp={self.timestamp})"
        )


class ConfigRegistry:
    """
    Central registry for application configuration.

    Provides:
    - Hot reload capabilities
    - Change notifications
    - Rollback on errors
    - Configuration validation
    """

    def __init__(
        self,
        loader: ConfigLoader | None = None,
        validator: ConfigValidator | None = None,
        watcher: ConfigWatcher | None = None,
        enable_auto_reload: bool = True,
    ):
        """
        Initialize the configuration registry.

        Args:
            loader: Configuration loader instance
            validator: Configuration validator instance
            watcher: Configuration watcher instance
            enable_auto_reload: Enable automatic reload on file changes
        """
        self.loader = loader or ConfigLoader()
        self.validator = validator or ConfigValidator()
        self.watcher = watcher or ConfigWatcher(auto_reload=enable_auto_reload)
        self.enable_auto_reload = enable_auto_reload

        # Current configuration
        self._current_config: Settings | None = None

        # Configuration history for rollback
        self._config_history: list[Settings] = []
        self._max_history = 10

        # Change notification callbacks
        self._change_callbacks: list[Callable[[ConfigChangeEvent], None]] = []

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        # Track if registry is initialized
        self._initialized = False

        # Register file watcher callback
        if self.enable_auto_reload:
            self.watcher.register_callback(self._on_file_change)

    async def initialize(self) -> None:
        """
        Initialize the configuration registry.

        Loads initial configuration and starts file watcher.

        Raises:
            ConfigLoadError: If initial load fails
        """
        if self._initialized:
            logger.warning("Config registry already initialized")
            return

        logger.info("Initializing configuration registry...")

        try:
            # Load initial configuration
            await self.reload()

            # Add .env file to watcher
            env_file = self.loader.get_env_file_path()
            if env_file.exists():
                self.watcher.add_file(env_file)

            # Start file watcher
            if self.enable_auto_reload:
                await self.watcher.start_async()

            self._initialized = True
            logger.info("Configuration registry initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize config registry: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the configuration registry."""
        logger.info("Shutting down configuration registry...")

        if self.watcher.is_running():
            await self.watcher.stop_async()

        self._initialized = False
        logger.info("Configuration registry shutdown complete")

    async def reload(self, validate: bool = True) -> Settings:
        """
        Reload configuration from files.

        Args:
            validate: Whether to validate new configuration

        Returns:
            Settings: Reloaded configuration

        Raises:
            ConfigLoadError: If reload fails
            ConfigValidationError: If validation fails
        """
        async with self._lock:
            try:
                logger.info("Reloading configuration...")

                # Save current config for rollback
                old_config = self._current_config

                # Load new configuration
                new_config = await asyncio.to_thread(self.loader.reload)

                # Validate if requested
                if validate and old_config:
                    await asyncio.to_thread(
                        self.validator.validate,
                        new_config.model_dump(),
                        old_config,
                    )

                # Update current config
                self._update_config(new_config, old_config, source="file")

                logger.info("Configuration reloaded successfully")
                return new_config

            except (ConfigLoadError, ConfigValidationError) as e:
                logger.error(f"Configuration reload failed: {e}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error during reload: {e}", exc_info=True)
                raise ConfigLoadError(f"Reload failed: {e}")

    async def update(
        self,
        updates: dict[str, Any],
        validate: bool = True,
        source: str = "api",
    ) -> Settings:
        """
        Update configuration with partial changes.

        Args:
            updates: Dictionary of configuration updates
            validate: Whether to validate the changes
            source: Source of the update

        Returns:
            Settings: Updated configuration

        Raises:
            ConfigValidationError: If validation fails
        """
        async with self._lock:
            if not self._current_config:
                raise RuntimeError("Configuration not initialized")

            try:
                logger.info(f"Updating configuration: {list(updates.keys())}")

                # Save current config for rollback
                old_config = self._current_config

                # Process updates
                processed_updates = await asyncio.to_thread(
                    self.loader.load_partial,
                    updates,
                )

                # Validate partial update
                if validate:
                    merged_config = await asyncio.to_thread(
                        self.validator.validate_partial,
                        processed_updates,
                        old_config,
                    )
                    new_config = Settings(**merged_config)
                else:
                    # Merge with current config without validation
                    merged_dict = old_config.model_dump()
                    merged_dict.update(processed_updates)
                    new_config = Settings(**merged_dict)

                # Update current config
                self._update_config(new_config, old_config, source=source)

                logger.info("Configuration updated successfully")
                return new_config

            except ConfigValidationError as e:
                logger.error(f"Configuration update validation failed: {e}")
                raise

            except Exception as e:
                logger.error(f"Configuration update failed: {e}", exc_info=True)
                raise ConfigValidationError(f"Update failed: {e}")

    def _update_config(
        self,
        new_config: Settings,
        old_config: Settings | None,
        source: str = "unknown",
    ) -> None:
        """
        Update current configuration and notify listeners.

        Args:
            new_config: New configuration
            old_config: Previous configuration (for history)
            source: Source of the change
        """
        # Add old config to history
        if old_config and old_config != new_config:
            self._config_history.append(old_config)
            if len(self._config_history) > self._max_history:
                self._config_history.pop(0)

        # Update current config
        self._current_config = new_config

        # Detect changed fields
        changed_fields = self._detect_changes(old_config, new_config)

        # Notify listeners
        if changed_fields and old_config:
            event = ConfigChangeEvent(
                old_config=old_config,
                new_config=new_config,
                changed_fields=changed_fields,
                source=source,
            )
            self._notify_change(event)

    def _detect_changes(
        self,
        old_config: Settings | None,
        new_config: Settings,
    ) -> list[str]:
        """
        Detect which fields changed between configurations.

        Args:
            old_config: Old configuration
            new_config: New configuration

        Returns:
            List[str]: List of changed field names
        """
        if not old_config:
            return []

        changed = []
        old_dict = old_config.model_dump()
        new_dict = new_config.model_dump()

        for key in new_dict.keys():
            if old_dict.get(key) != new_dict.get(key):
                changed.append(key)

        return changed

    def _notify_change(self, event: ConfigChangeEvent) -> None:
        """
        Notify all registered callbacks of configuration change.

        Args:
            event: Configuration change event
        """
        logger.info(
            f"Notifying {len(self._change_callbacks)} listeners of config change"
        )

        for callback in self._change_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(
                    f"Error in config change callback {callback.__name__}: {e}",
                    exc_info=True,
                )

    def _on_file_change(self, file_path: Path) -> None:
        """
        Handle configuration file change.

        Args:
            file_path: Path to changed file
        """
        logger.info(f"Configuration file changed: {file_path}")

        # Reload configuration (run in event loop)
        try:
            # Create task to reload
            loop = asyncio.get_event_loop()
            loop.create_task(self._safe_reload())
        except RuntimeError:
            # No event loop, reload synchronously
            logger.warning("No event loop available, reloading synchronously")
            try:
                new_config = self.loader.reload()
                self.validator.validate(
                    new_config.model_dump(),
                    self._current_config,
                )
                self._update_config(new_config, self._current_config, source="file")
            except Exception as e:
                logger.error(f"Synchronous reload failed: {e}", exc_info=True)

    async def _safe_reload(self) -> None:
        """Safely reload configuration with error handling."""
        try:
            await self.reload()
        except Exception as e:
            logger.error(f"Auto-reload failed: {e}", exc_info=True)

    async def rollback(self, steps: int = 1) -> Settings | None:
        """
        Rollback configuration to a previous version.

        Args:
            steps: Number of steps to roll back

        Returns:
            Optional[Settings]: Rolled back configuration, or None if not available

        Raises:
            ValueError: If rollback steps are invalid
        """
        async with self._lock:
            if steps < 1:
                raise ValueError("Rollback steps must be at least 1")

            if len(self._config_history) < steps:
                logger.warning(
                    f"Cannot rollback {steps} steps, only {len(self._config_history)} "
                    f"versions available"
                )
                return None

            # Get previous config
            previous_config = self._config_history[-(steps)]

            # Update current config
            self._current_config = previous_config

            # Remove rolled back versions from history
            self._config_history = self._config_history[:-steps]

            logger.info(f"Rolled back configuration {steps} step(s)")
            return previous_config

    def register_change_callback(
        self,
        callback: Callable[[ConfigChangeEvent], None],
    ) -> None:
        """
        Register callback for configuration changes.

        Args:
            callback: Callback function
        """
        if callback not in self._change_callbacks:
            self._change_callbacks.append(callback)
            logger.info(f"Registered config change callback: {callback.__name__}")

    def unregister_change_callback(
        self,
        callback: Callable[[ConfigChangeEvent], None],
    ) -> None:
        """
        Unregister configuration change callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            logger.info(f"Unregistered config change callback: {callback.__name__}")

    def get_current_config(self) -> Settings | None:
        """
        Get current configuration.

        Returns:
            Optional[Settings]: Current configuration, or None if not initialized
        """
        return self._current_config

    def get_config_history(self) -> list[Settings]:
        """
        Get configuration history.

        Returns:
            List[Settings]: List of previous configurations
        """
        return self._config_history.copy()

    def is_initialized(self) -> bool:
        """
        Check if registry is initialized.

        Returns:
            bool: True if initialized, False otherwise
        """
        return self._initialized

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.shutdown()


# Global registry instance
config_registry = ConfigRegistry()
