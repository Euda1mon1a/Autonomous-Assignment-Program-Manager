"""
Configuration file management for CLI.

Handles:
- YAML configuration files
- Profile management (dev, staging, prod)
- Configuration validation
- Default settings
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from rich.console import Console

from cli.config import get_config_dir

console = Console()


class ConfigFile:
    """Manage CLI configuration file."""

    def __init__(self, profile: str = "dev"):
        """
        Initialize config file manager.

        Args:
            profile: Configuration profile (dev, staging, prod)
        """
        self.profile = profile
        self.config_dir = get_config_dir()
        self.config_file = self.config_dir / "config.yaml"

    def load(self) -> dict[str, Any]:
        """
        Load configuration from file.

        Returns:
            Configuration dictionary
        """
        if not self.config_file.exists():
            return self._get_defaults()

        try:
            with open(self.config_file) as f:
                config = yaml.safe_load(f)

            # Get profile-specific config or defaults
            return config.get(self.profile, self._get_defaults())

        except yaml.YAMLError as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            return self._get_defaults()

    def save(self, config: dict[str, Any]) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration dictionary to save
        """
        # Load existing config
        if self.config_file.exists():
            with open(self.config_file) as f:
                all_config = yaml.safe_load(f) or {}
        else:
            all_config = {}

        # Update profile-specific config
        all_config[self.profile] = config

        # Save to file
        with open(self.config_file, "w") as f:
            yaml.dump(all_config, f, default_flow_style=False)

        console.print(
            f"[green]Configuration saved for profile '{self.profile}'[/green]"
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        config = self.load()

        # Support dot notation (e.g., "database.url")
        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        config = self.load()

        # Support dot notation
        keys = key.split(".")
        current = config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

        self.save(config)

    def _get_defaults(self) -> dict[str, Any]:
        """Get default configuration."""
        return {
            "api": {
                "url": "http://localhost:8000",
                "timeout": 30,
            },
            "database": {
                "url": "postgresql+asyncpg://scheduler:scheduler@localhost:5432/residency_scheduler",
            },
            "output": {
                "format": "table",
                "color": True,
                "verbose": False,
            },
            "defaults": {
                "block_size": 4,  # weeks
                "academic_year": 2024,
            },
        }

    def list_profiles(self) -> list:
        """
        List all available configuration profiles.

        Returns:
            List of profile names
        """
        if not self.config_file.exists():
            return ["dev"]

        with open(self.config_file) as f:
            config = yaml.safe_load(f)

        return list(config.keys()) if config else ["dev"]

    def delete_profile(self, profile: str) -> None:
        """
        Delete a configuration profile.

        Args:
            profile: Profile name to delete
        """
        if not self.config_file.exists():
            console.print("[yellow]No configuration file exists[/yellow]")
            return

        with open(self.config_file) as f:
            config = yaml.safe_load(f)

        if profile in config:
            del config[profile]

            with open(self.config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)

            console.print(f"[green]Profile '{profile}' deleted[/green]")
        else:
            console.print(f"[yellow]Profile '{profile}' not found[/yellow]")

    def export_profile(self, profile: str, output_file: Path) -> None:
        """
        Export profile configuration to file.

        Args:
            profile: Profile name to export
            output_file: Output file path
        """
        config = ConfigFile(profile).load()

        with open(output_file, "w") as f:
            yaml.dump({profile: config}, f, default_flow_style=False)

        console.print(f"[green]Profile '{profile}' exported to {output_file}[/green]")

    def import_profile(self, input_file: Path) -> None:
        """
        Import profile configuration from file.

        Args:
            input_file: Input file path
        """
        with open(input_file) as f:
            imported = yaml.safe_load(f)

        # Load existing config
        if self.config_file.exists():
            with open(self.config_file) as f:
                config = yaml.safe_load(f) or {}
        else:
            config = {}

        # Merge imported profiles
        config.update(imported)

        # Save
        with open(self.config_file, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        console.print(f"[green]Profiles imported from {input_file}[/green]")
