"""
CLI configuration management.

Handles:
- Environment variable loading
- Configuration file parsing
- Default settings
- Profile management (dev, staging, prod)
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class CLIConfig(BaseSettings):
    """CLI configuration settings."""

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://scheduler:scheduler@localhost:5432/residency_scheduler",
        env="DATABASE_URL"
    )

    # API
    api_url: str = Field(
        default="http://localhost:8000",
        env="API_URL"
    )

    # Authentication
    api_token: Optional[str] = Field(default=None, env="CLI_API_TOKEN")

    # Output
    output_format: str = Field(default="table", env="CLI_OUTPUT_FORMAT")
    color_output: bool = Field(default=True, env="CLI_COLOR_OUTPUT")
    verbose: bool = Field(default=False, env="CLI_VERBOSE")

    # Profile
    profile: str = Field(default="dev", env="CLI_PROFILE")

    # Config file
    config_file: Path = Field(
        default=Path.home() / ".scheduler-cli" / "config.yaml",
        env="CLI_CONFIG_FILE"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_config() -> CLIConfig:
    """Get CLI configuration instance."""
    return CLIConfig()


def get_config_dir() -> Path:
    """Get CLI configuration directory."""
    config_dir = Path.home() / ".scheduler-cli"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_cache_dir() -> Path:
    """Get CLI cache directory."""
    cache_dir = get_config_dir() / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir
