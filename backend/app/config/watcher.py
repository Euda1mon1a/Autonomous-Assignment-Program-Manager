"""Configuration file watcher module.

Monitors configuration files for changes and triggers hot reload.
"""

import asyncio
import logging
import threading
from pathlib import Path
from typing import Callable, List, Optional, Set

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """Handles file system events for configuration files."""

    def __init__(
        self,
        watched_files: Set[Path],
        on_change_callback: Callable[[Path], None],
    ):
        """
        Initialize the file handler.

        Args:
            watched_files: Set of files to watch
            on_change_callback: Callback to invoke when file changes
        """
        super().__init__()
        self.watched_files = watched_files
        self.on_change_callback = on_change_callback
        self._debounce_timers: dict[Path, threading.Timer] = {}
        self._debounce_delay = 1.0  # Wait 1 second before processing change

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path).resolve()

        # Check if this is a watched file
        if file_path in self.watched_files:
            logger.info(f"Configuration file modified: {file_path}")
            self._debounced_change(file_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation events.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path).resolve()

        # Check if this is a watched file
        if file_path in self.watched_files:
            logger.info(f"Configuration file created: {file_path}")
            self._debounced_change(file_path)

    def _debounced_change(self, file_path: Path) -> None:
        """
        Debounce file changes to avoid multiple rapid reloads.

        Args:
            file_path: Path to changed file
        """
        # Cancel existing timer for this file
        if file_path in self._debounce_timers:
            self._debounce_timers[file_path].cancel()

        # Create new timer
        timer = threading.Timer(
            self._debounce_delay,
            self._execute_change,
            args=[file_path],
        )
        self._debounce_timers[file_path] = timer
        timer.start()

    def _execute_change(self, file_path: Path) -> None:
        """
        Execute the change callback.

        Args:
            file_path: Path to changed file
        """
        try:
            self.on_change_callback(file_path)
        except Exception as e:
            logger.error(f"Error in config change callback: {e}", exc_info=True)
        finally:
            # Remove timer
            self._debounce_timers.pop(file_path, None)


class ConfigWatcher:
    """Watches configuration files for changes and triggers hot reload."""

    def __init__(
        self,
        config_files: Optional[List[Path]] = None,
        auto_reload: bool = True,
    ):
        """
        Initialize the configuration watcher.

        Args:
            config_files: List of configuration files to watch
            auto_reload: Whether to automatically reload on file changes
        """
        self.config_files: Set[Path] = set()
        self.auto_reload = auto_reload
        self.observer: Optional[Observer] = None
        self._callbacks: List[Callable[[Path], None]] = []
        self._running = False
        self._lock = threading.Lock()

        # Add initial config files
        if config_files:
            for file_path in config_files:
                self.add_file(file_path)

    def add_file(self, file_path: Path) -> None:
        """
        Add a file to watch.

        Args:
            file_path: Path to configuration file
        """
        resolved_path = file_path.resolve()

        if resolved_path in self.config_files:
            logger.debug(f"File already being watched: {resolved_path}")
            return

        self.config_files.add(resolved_path)
        logger.info(f"Added file to watch list: {resolved_path}")

        # If watcher is running, restart to pick up new file
        if self._running:
            self.restart()

    def remove_file(self, file_path: Path) -> None:
        """
        Remove a file from watch list.

        Args:
            file_path: Path to configuration file
        """
        resolved_path = file_path.resolve()

        if resolved_path in self.config_files:
            self.config_files.remove(resolved_path)
            logger.info(f"Removed file from watch list: {resolved_path}")

            # If watcher is running, restart to update watch list
            if self._running:
                self.restart()

    def register_callback(self, callback: Callable[[Path], None]) -> None:
        """
        Register a callback to be invoked when config files change.

        Args:
            callback: Callback function that takes file path as argument
        """
        if callback not in self._callbacks:
            self._callbacks.append(callback)
            logger.info(f"Registered config change callback: {callback.__name__}")

    def unregister_callback(self, callback: Callable[[Path], None]) -> None:
        """
        Unregister a callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._callbacks:
            self._callbacks.remove(callback)
            logger.info(f"Unregistered config change callback: {callback.__name__}")

    def _on_file_change(self, file_path: Path) -> None:
        """
        Handle file change event.

        Args:
            file_path: Path to changed file
        """
        logger.info(f"Configuration file changed: {file_path}")

        # Invoke all registered callbacks
        for callback in self._callbacks:
            try:
                callback(file_path)
            except Exception as e:
                logger.error(
                    f"Error in callback {callback.__name__}: {e}",
                    exc_info=True,
                )

    def start(self) -> None:
        """
        Start watching configuration files.

        Raises:
            RuntimeError: If no files are being watched
        """
        with self._lock:
            if self._running:
                logger.warning("Config watcher is already running")
                return

            if not self.config_files:
                raise RuntimeError("No configuration files to watch")

            # Create observer
            self.observer = Observer()

            # Get unique directories to watch
            directories = {file_path.parent for file_path in self.config_files}

            # Create event handler
            handler = ConfigFileHandler(
                watched_files=self.config_files,
                on_change_callback=self._on_file_change,
            )

            # Schedule observer for each directory
            for directory in directories:
                if directory.exists():
                    self.observer.schedule(
                        handler,
                        str(directory),
                        recursive=False,
                    )
                    logger.info(f"Watching directory: {directory}")
                else:
                    logger.warning(f"Directory does not exist: {directory}")

            # Start observer
            self.observer.start()
            self._running = True
            logger.info("Configuration watcher started")

    def stop(self) -> None:
        """Stop watching configuration files."""
        with self._lock:
            if not self._running:
                logger.warning("Config watcher is not running")
                return

            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                self.observer = None

            self._running = False
            logger.info("Configuration watcher stopped")

    def restart(self) -> None:
        """Restart the configuration watcher."""
        logger.info("Restarting configuration watcher...")
        self.stop()
        self.start()

    def is_running(self) -> bool:
        """
        Check if watcher is running.

        Returns:
            bool: True if running, False otherwise
        """
        return self._running

    async def start_async(self) -> None:
        """
        Start the watcher in async context.

        This runs the watcher in a background thread.
        """
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.start)

    async def stop_async(self) -> None:
        """Stop the watcher in async context."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.stop)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_async()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop_async()
