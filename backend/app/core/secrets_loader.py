"""
Secrets loader with macOS Keychain integration via the `keyring` library.

Provides a single entry-point function that attempts to populate os.environ
from the macOS Keychain for any secret that is not already set.  Environment
variables always take precedence so CI, Docker, and .env workflows are
unaffected.

Usage (typically called once at startup):

    from app.core.secrets_loader import initialize_secrets_from_keychain
    initialize_secrets_from_keychain()
"""

from __future__ import annotations

import os

from app.core.logging import get_logger

logger = get_logger(__name__)

SERVICE_NAME = "residency-scheduler"

MANAGED_SECRETS: list[str] = [
    "DB_PASSWORD",
    "REDIS_PASSWORD",
    "SECRET_KEY",
    "WEBHOOK_SECRET",
    "ANTHROPIC_API_KEY",
    "API_PASSWORD",
]


def initialize_secrets_from_keychain() -> None:
    """Load secrets from the macOS Keychain into ``os.environ``.

    For each key in ``MANAGED_SECRETS``:
      1. If the env var is already set, keep it (env takes precedence).
      2. Otherwise, attempt to read from the Keychain via ``keyring``.
      3. If found, set ``os.environ[key]`` to the retrieved value.

    Gracefully handles:
      - ``ImportError`` when ``keyring`` is not installed (e.g. Linux, CI).
      - ``keyring.errors.KeyringError`` when the Keychain is locked or
        unavailable.
    """
    try:
        import keyring
        import keyring.errors
    except ImportError:
        logger.debug(
            "keyring library not available — skipping Keychain secret loading. "
            "Install with: pip install keyring"
        )
        return

    loaded_from_keychain: list[str] = []
    already_in_env: list[str] = []
    not_found: list[str] = []

    for key in MANAGED_SECRETS:
        # Environment variable takes precedence
        if os.environ.get(key):
            already_in_env.append(key)
            continue

        try:
            value = keyring.get_password(SERVICE_NAME, key)
        except keyring.errors.KeyringError as exc:
            logger.warning(
                "Keychain lookup failed for %s: %s",
                key,
                exc,
            )
            not_found.append(key)
            continue

        if value:
            os.environ[key] = value
            loaded_from_keychain.append(key)
        else:
            not_found.append(key)

    # ------------------------------------------------------------------
    # Summary log
    # ------------------------------------------------------------------
    if loaded_from_keychain:
        logger.info(
            "Loaded %d secret(s) from Keychain: %s",
            len(loaded_from_keychain),
            ", ".join(loaded_from_keychain),
        )
    if already_in_env:
        logger.debug(
            "Kept %d secret(s) from environment: %s",
            len(already_in_env),
            ", ".join(already_in_env),
        )
    if not_found:
        logger.debug(
            "%d secret(s) not found in Keychain or environment: %s",
            len(not_found),
            ", ".join(not_found),
        )
