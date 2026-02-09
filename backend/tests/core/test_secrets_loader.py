"""Tests for secrets loader (macOS Keychain integration)."""

from unittest.mock import MagicMock, patch

from app.core.secrets_loader import (
    MANAGED_SECRETS,
    SERVICE_NAME,
    initialize_secrets_from_keychain,
)


# ==================== Constants ====================


class TestConstants:
    def test_service_name(self):
        assert SERVICE_NAME == "residency-scheduler"

    def test_managed_secrets_is_list(self):
        assert isinstance(MANAGED_SECRETS, list)

    def test_managed_secrets_not_empty(self):
        assert len(MANAGED_SECRETS) > 0

    def test_managed_secrets_contains_secret_key(self):
        assert "SECRET_KEY" in MANAGED_SECRETS

    def test_managed_secrets_contains_db_password(self):
        assert "DB_PASSWORD" in MANAGED_SECRETS

    def test_managed_secrets_contains_webhook_secret(self):
        assert "WEBHOOK_SECRET" in MANAGED_SECRETS

    def test_managed_secrets_all_strings(self):
        for s in MANAGED_SECRETS:
            assert isinstance(s, str)

    def test_managed_secrets_all_uppercase(self):
        for s in MANAGED_SECRETS:
            assert s == s.upper(), f"{s} should be UPPER_SNAKE_CASE"


# ==================== No keyring available ====================


class TestNoKeyring:
    @patch.dict("sys.modules", {"keyring": None, "keyring.errors": None})
    def test_returns_gracefully_without_keyring(self):
        """When keyring is not installed, function returns without error."""
        # The function catches ImportError internally; mock the import mechanism
        with patch(
            "app.core.secrets_loader.initialize_secrets_from_keychain",
            wraps=initialize_secrets_from_keychain,
        ):
            # Direct call — uses the real function which tries to import keyring
            # We can't easily block the import from inside the function,
            # so we test the no-keyring path via a mock that raises ImportError
            pass  # Covered by mock_keyring_import_error test below


class TestKeyringImportError:
    def test_import_error_handled(self):
        """ImportError from keyring import is caught and logged."""
        import builtins

        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "keyring" or name == "keyring.errors":
                raise ImportError("No module named 'keyring'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            # Should not raise
            initialize_secrets_from_keychain()


# ==================== Env var precedence ====================


class TestEnvPrecedence:
    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_env_var_takes_precedence(self, mock_env):
        """If env var is set, keychain is not queried for it."""
        mock_env["SECRET_KEY"] = "from-env"

        mock_keyring = MagicMock()
        mock_keyring.get_password = MagicMock(return_value=None)
        mock_keyring_errors = MagicMock()
        mock_keyring.errors = mock_keyring_errors

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            initialize_secrets_from_keychain()

        # SECRET_KEY should not have been queried
        calls = [c[0] for c in mock_keyring.get_password.call_args_list]
        secret_key_calls = [c for c in calls if c[1] == "SECRET_KEY"]
        assert len(secret_key_calls) == 0
        # And the value should still be from env
        assert mock_env["SECRET_KEY"] == "from-env"


# ==================== Keychain loading ====================


class TestKeychainLoading:
    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_loads_from_keychain(self, mock_env):
        """Values found in keychain are set in os.environ."""
        mock_keyring = MagicMock()

        def fake_get(service, key):
            if key == "SECRET_KEY":
                return "keychain-secret"
            return None

        mock_keyring.get_password = MagicMock(side_effect=fake_get)
        mock_keyring_errors = MagicMock()
        mock_keyring.errors = mock_keyring_errors

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            initialize_secrets_from_keychain()

        assert mock_env.get("SECRET_KEY") == "keychain-secret"

    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_keychain_none_not_set(self, mock_env):
        """If keychain returns None, env var is not set."""
        mock_keyring = MagicMock()
        mock_keyring.get_password = MagicMock(return_value=None)
        mock_keyring_errors = MagicMock()
        mock_keyring.errors = mock_keyring_errors

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            initialize_secrets_from_keychain()

        # None of the managed secrets should be set
        for key in MANAGED_SECRETS:
            assert key not in mock_env

    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_keychain_empty_string_not_set(self, mock_env):
        """If keychain returns empty string, env var is not set (falsy)."""
        mock_keyring = MagicMock()
        mock_keyring.get_password = MagicMock(return_value="")
        mock_keyring_errors = MagicMock()
        mock_keyring.errors = mock_keyring_errors

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            initialize_secrets_from_keychain()

        for key in MANAGED_SECRETS:
            assert key not in mock_env


# ==================== KeyringError handling ====================


class TestKeyringError:
    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_keyring_error_caught(self, mock_env):
        """KeyringError is caught and secret is classified as not_found."""
        mock_keyring = MagicMock()

        # Create a real exception class to raise
        class FakeKeyringError(Exception):
            pass

        mock_keyring_errors = MagicMock()
        mock_keyring_errors.KeyringError = FakeKeyringError
        mock_keyring.errors = mock_keyring_errors

        mock_keyring.get_password = MagicMock(
            side_effect=FakeKeyringError("Keychain locked")
        )

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            # Should not raise
            initialize_secrets_from_keychain()

        # No secrets should be set
        for key in MANAGED_SECRETS:
            assert key not in mock_env


# ==================== Multiple secrets ====================


class TestMultipleSecrets:
    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_mixed_sources(self, mock_env):
        """Some from env, some from keychain, some missing."""
        mock_env["DB_PASSWORD"] = "env-db-pass"

        mock_keyring = MagicMock()

        def fake_get(service, key):
            if key == "SECRET_KEY":
                return "kc-secret"
            if key == "WEBHOOK_SECRET":
                return "kc-webhook"
            return None

        mock_keyring.get_password = MagicMock(side_effect=fake_get)
        mock_keyring_errors = MagicMock()
        mock_keyring.errors = mock_keyring_errors

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            initialize_secrets_from_keychain()

        # DB_PASSWORD kept from env
        assert mock_env["DB_PASSWORD"] == "env-db-pass"
        # SECRET_KEY and WEBHOOK_SECRET loaded from keychain
        assert mock_env["SECRET_KEY"] == "kc-secret"
        assert mock_env["WEBHOOK_SECRET"] == "kc-webhook"
        # REDIS_PASSWORD not in keychain, should not be set
        assert "REDIS_PASSWORD" not in mock_env

    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_all_from_env(self, mock_env):
        """If all secrets already in env, keychain is not queried."""
        for key in MANAGED_SECRETS:
            mock_env[key] = f"env-{key}"

        mock_keyring = MagicMock()
        mock_keyring.get_password = MagicMock(return_value="should-not-use")
        mock_keyring_errors = MagicMock()
        mock_keyring.errors = mock_keyring_errors

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            initialize_secrets_from_keychain()

        # keyring.get_password should not have been called at all
        mock_keyring.get_password.assert_not_called()

    @patch("app.core.secrets_loader.os.environ", new_callable=dict)
    def test_service_name_passed_to_keyring(self, mock_env):
        """Keyring is queried with the correct service name."""
        mock_keyring = MagicMock()
        mock_keyring.get_password = MagicMock(return_value=None)
        mock_keyring_errors = MagicMock()
        mock_keyring.errors = mock_keyring_errors

        with patch.dict(
            "sys.modules",
            {"keyring": mock_keyring, "keyring.errors": mock_keyring_errors},
        ):
            initialize_secrets_from_keychain()

        # All calls should use SERVICE_NAME as first arg
        for call in mock_keyring.get_password.call_args_list:
            assert call[0][0] == SERVICE_NAME
