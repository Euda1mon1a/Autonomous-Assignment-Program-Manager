"""Tests for tenant isolation pure logic (no DB, no Redis).

The app.tenancy.models import fails outside the full app context
(SQLAlchemy reserved 'metadata' attribute on Tenant model),
so we mock the models and context imports before loading isolation.
"""

from __future__ import annotations

import asyncio
import sys
import threading
import types
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

# ---------------------------------------------------------------------------
# Stub out modules that fail to import outside full app context
# ---------------------------------------------------------------------------

# Create stub for app.tenancy.models
_models_stub = types.ModuleType("app.tenancy.models")
_models_stub.Tenant = MagicMock()
_models_stub.TenantAuditLog = MagicMock()
sys.modules.setdefault("app.tenancy.models", _models_stub)

# Create stub for app.tenancy.context
_context_stub = types.ModuleType("app.tenancy.context")
_context_stub.get_current_tenant_id = MagicMock(return_value=None)
sys.modules.setdefault("app.tenancy.context", _context_stub)

# Ensure app.tenancy package doesn't try its own heavy __init__
# Must set __path__ so Python treats it as a package (allows submodule imports)
import os as _os

_tenancy_stub = types.ModuleType("app.tenancy")
_tenancy_stub.__path__ = [
    _os.path.join(
        _os.path.dirname(
            _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        ),
        "app",
        "tenancy",
    )
]
sys.modules.setdefault("app.tenancy", _tenancy_stub)

from app.tenancy.isolation import (  # noqa: E402
    IsolationStrategy,
    QuotaExceededError,
    TenantConnectionPoolManager,
    TenantEncryptionService,
    TenantScope,
    get_tenant_schema,
    validate_schema_name,
)
import app.tenancy.isolation as isolation_module  # noqa: E402


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# IsolationStrategy constants
# ---------------------------------------------------------------------------


class TestIsolationStrategy:
    def test_schema_value(self):
        assert IsolationStrategy.SCHEMA == "schema"

    def test_row_level_value(self):
        assert IsolationStrategy.ROW_LEVEL == "row_level"


# ---------------------------------------------------------------------------
# get_tenant_schema
# ---------------------------------------------------------------------------


class TestGetTenantSchema:
    def test_generates_schema_name(self):
        tenant_id = UUID("12345678-1234-1234-1234-123456789abc")
        schema = get_tenant_schema(tenant_id)
        assert schema.startswith("tenant_")

    def test_uses_first_12_chars(self):
        tenant_id = UUID("abcdef01-2345-6789-abcd-ef0123456789")
        schema = get_tenant_schema(tenant_id)
        # UUID without hyphens: "abcdef0123456789abcdef0123456789"
        # First 12: "abcdef012345"
        assert schema == "tenant_abcdef012345"

    def test_different_tenants_different_schemas(self):
        t1 = uuid4()
        t2 = uuid4()
        assert get_tenant_schema(t1) != get_tenant_schema(t2)

    def test_deterministic(self):
        tenant_id = uuid4()
        assert get_tenant_schema(tenant_id) == get_tenant_schema(tenant_id)


# ---------------------------------------------------------------------------
# validate_schema_name
# ---------------------------------------------------------------------------


class TestValidateSchemaName:
    def test_valid_name(self):
        validate_schema_name("tenant_abc123")  # should not raise

    def test_empty_name(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_schema_name("")

    def test_too_long(self):
        with pytest.raises(ValueError, match="exceeds PostgreSQL limit"):
            validate_schema_name("tenant_" + "a" * 60)

    def test_missing_prefix(self):
        with pytest.raises(ValueError, match="must start with"):
            validate_schema_name("schema_abc")

    def test_invalid_characters(self):
        with pytest.raises(ValueError, match="invalid characters"):
            validate_schema_name("tenant_abc; DROP TABLE")

    def test_valid_long_name(self):
        name = "tenant_" + "a" * 50  # 57 chars, under 63
        validate_schema_name(name)  # should not raise

    def test_exactly_63_chars(self):
        name = "tenant_" + "a" * 56  # 63 chars exactly
        validate_schema_name(name)  # should not raise

    def test_64_chars_fails(self):
        name = "tenant_" + "a" * 57  # 64 chars
        with pytest.raises(ValueError, match="exceeds PostgreSQL limit"):
            validate_schema_name(name)


# ---------------------------------------------------------------------------
# QuotaExceededError
# ---------------------------------------------------------------------------


class TestQuotaExceededError:
    def test_is_exception(self):
        assert issubclass(QuotaExceededError, Exception)

    def test_message(self):
        err = QuotaExceededError("quota exceeded")
        assert str(err) == "quota exceeded"

    def test_raises(self):
        with pytest.raises(QuotaExceededError):
            raise QuotaExceededError("test")


# ---------------------------------------------------------------------------
# TenantEncryptionService
# ---------------------------------------------------------------------------


class TestTenantEncryptionServiceInit:
    def test_with_valid_key(self):
        key = b"\x00" * 32
        svc = TenantEncryptionService(master_key=key)
        assert svc.master_key == key

    def test_without_key_generates_random(self):
        svc = TenantEncryptionService()
        assert len(svc.master_key) == 32

    def test_wrong_key_length(self):
        with pytest.raises(ValueError, match="32 bytes"):
            TenantEncryptionService(master_key=b"short")

    def test_wrong_key_length_too_long(self):
        with pytest.raises(ValueError, match="32 bytes"):
            TenantEncryptionService(master_key=b"\x00" * 64)


class TestTenantEncryptionServiceDeriveKey:
    def test_deterministic(self):
        svc = TenantEncryptionService(master_key=b"\x01" * 32)
        tid = uuid4()
        k1 = svc._derive_tenant_key(tid)
        k2 = svc._derive_tenant_key(tid)
        assert k1 == k2

    def test_different_tenants_different_keys(self):
        svc = TenantEncryptionService(master_key=b"\x01" * 32)
        k1 = svc._derive_tenant_key(uuid4())
        k2 = svc._derive_tenant_key(uuid4())
        assert k1 != k2

    def test_key_length(self):
        svc = TenantEncryptionService(master_key=b"\x01" * 32)
        key = svc._derive_tenant_key(uuid4())
        assert len(key) == 32

    def test_different_master_keys_different_derived(self):
        tid = uuid4()
        svc1 = TenantEncryptionService(master_key=b"\x01" * 32)
        svc2 = TenantEncryptionService(master_key=b"\x02" * 32)
        assert svc1._derive_tenant_key(tid) != svc2._derive_tenant_key(tid)


class TestTenantEncryptionServiceEncryptDecrypt:
    def _svc(self):
        return TenantEncryptionService(master_key=b"\xab" * 32)

    def test_encrypt_returns_string(self):
        svc = self._svc()
        tid = uuid4()
        result = _run(svc.encrypt_data(tid, b"hello"))
        assert isinstance(result, str)

    def test_encrypt_decrypt_roundtrip(self):
        svc = self._svc()
        tid = uuid4()
        plaintext = b"sensitive medical data"
        encrypted = _run(svc.encrypt_data(tid, plaintext))
        decrypted = _run(svc.decrypt_data(tid, encrypted))
        assert decrypted == plaintext

    def test_encrypt_string_roundtrip(self):
        svc = self._svc()
        tid = uuid4()
        text = "patient record 12345"
        encrypted = _run(svc.encrypt_string(tid, text))
        decrypted = _run(svc.decrypt_string(tid, encrypted))
        assert decrypted == text

    def test_different_nonces_each_time(self):
        svc = self._svc()
        tid = uuid4()
        e1 = _run(svc.encrypt_data(tid, b"same"))
        e2 = _run(svc.encrypt_data(tid, b"same"))
        assert e1 != e2  # Different nonces

    def test_cross_tenant_decrypt_fails(self):
        svc = self._svc()
        t1, t2 = uuid4(), uuid4()
        encrypted = _run(svc.encrypt_data(t1, b"secret"))
        with pytest.raises(RuntimeError, match="Decryption failed"):
            _run(svc.decrypt_data(t2, encrypted))

    def test_tampered_ciphertext_fails(self):
        svc = self._svc()
        tid = uuid4()
        encrypted = _run(svc.encrypt_data(tid, b"data"))
        # Tamper with the base64 content
        import base64

        raw = bytearray(base64.b64decode(encrypted))
        raw[-1] ^= 0xFF  # flip last byte
        tampered = base64.b64encode(bytes(raw)).decode()
        with pytest.raises(RuntimeError, match="Decryption failed"):
            _run(svc.decrypt_data(tid, tampered))

    def test_empty_plaintext(self):
        svc = self._svc()
        tid = uuid4()
        encrypted = _run(svc.encrypt_data(tid, b""))
        decrypted = _run(svc.decrypt_data(tid, encrypted))
        assert decrypted == b""

    def test_large_plaintext(self):
        svc = self._svc()
        tid = uuid4()
        plaintext = b"x" * 10000
        encrypted = _run(svc.encrypt_data(tid, plaintext))
        decrypted = _run(svc.decrypt_data(tid, encrypted))
        assert decrypted == plaintext

    def test_unicode_string_roundtrip(self):
        svc = self._svc()
        tid = uuid4()
        text = "Schedule: \u2713 Valid \u2022 Dr. M\u00fcller"
        encrypted = _run(svc.encrypt_string(tid, text))
        decrypted = _run(svc.decrypt_string(tid, encrypted))
        assert decrypted == text

    def test_invalid_base64_fails(self):
        svc = self._svc()
        tid = uuid4()
        with pytest.raises(RuntimeError, match="Decryption failed"):
            _run(svc.decrypt_data(tid, "not-valid-base64!!!"))


# ---------------------------------------------------------------------------
# TenantScope (constructor only, no DB)
# ---------------------------------------------------------------------------


class TestTenantScopeInit:
    def test_defaults(self):
        session = MagicMock()
        tid = uuid4()
        scope = TenantScope(session, tenant_id=tid)
        assert scope.tenant_id == tid
        assert scope.use_schema is False
        assert scope.bypass is False
        assert scope._original_schema is None

    def test_bypass_mode(self):
        session = MagicMock()
        scope = TenantScope(session, bypass=True)
        assert scope.bypass is True
        assert scope.tenant_id is None

    def test_schema_mode(self):
        session = MagicMock()
        scope = TenantScope(session, tenant_id=uuid4(), use_schema=True)
        assert scope.use_schema is True


# ---------------------------------------------------------------------------
# TenantConnectionPoolManager (constructor and pool config tracking)
# ---------------------------------------------------------------------------


class TestTenantConnectionPoolManagerInit:
    def test_creation(self):
        mgr = TenantConnectionPoolManager(database_url="postgresql://u:p@localhost/db")
        assert mgr.database_url == "postgresql://u:p@localhost/db"
        assert mgr.default_pool_size == 5
        assert mgr._pools == {}
        assert mgr._pool_configs == {}

    def test_custom_pool_size(self):
        mgr = TenantConnectionPoolManager(
            database_url="postgresql://u:p@localhost/db",
            default_pool_size=10,
        )
        assert mgr.default_pool_size == 10

    def test_get_session_no_pool(self):
        mgr = TenantConnectionPoolManager(database_url="postgresql://u:p@localhost/db")
        with pytest.raises(RuntimeError, match="No connection pool"):
            mgr.get_tenant_session(uuid4())

    def test_get_pool_stats_no_pool(self):
        mgr = TenantConnectionPoolManager(database_url="postgresql://u:p@localhost/db")
        stats = mgr.get_pool_stats(uuid4())
        assert stats == {"error": "No pool exists"}


def _install_pool_manager_fakes(monkeypatch):
    """Patch engine/session factory constructors used by pool manager."""
    engines: list[MagicMock] = []
    session_factories: list[MagicMock] = []
    constructor_lock = threading.Lock()

    def fake_create_engine(*_args, **kwargs):
        engine = MagicMock()
        engine.pool = MagicMock()
        engine.pool.size.return_value = kwargs.get("pool_size", 5)
        engine.pool.checkedout.return_value = 0
        engine.pool.overflow.return_value = 0
        with constructor_lock:
            engines.append(engine)
        return engine

    def fake_sessionmaker(*_args, **kwargs):
        factory = MagicMock()
        factory.kw = {"bind": kwargs["bind"]}
        factory.return_value = MagicMock(name="tenant_session")
        with constructor_lock:
            session_factories.append(factory)
        return factory

    monkeypatch.setattr(isolation_module, "create_engine", fake_create_engine)
    monkeypatch.setattr(isolation_module, "sessionmaker", fake_sessionmaker)
    return engines, session_factories


class TestTenantConnectionPoolManagerThreadSafety:
    def test_create_tenant_pool_concurrent_single_tenant_returns_one_pool(
        self, monkeypatch
    ):
        mgr = TenantConnectionPoolManager(database_url="postgresql://u:p@localhost/db")
        tenant_id = uuid4()
        engines, session_factories = _install_pool_manager_fakes(monkeypatch)

        thread_count = 16
        start_barrier = threading.Barrier(thread_count)
        result_lock = threading.Lock()
        returned_pools = []
        errors = []

        def worker():
            try:
                start_barrier.wait()
                pool = mgr.create_tenant_pool(tenant_id)
                with result_lock:
                    returned_pools.append(pool)
            except Exception as exc:  # pragma: no cover - should never happen
                with result_lock:
                    errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(thread_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        assert all(not thread.is_alive() for thread in threads)
        assert errors == []
        assert len(returned_pools) == thread_count
        assert len({id(pool) for pool in returned_pools}) == 1
        assert len(engines) == 1
        assert len(session_factories) == 1
        assert mgr._pools[tenant_id] is returned_pools[0]
        assert mgr._pool_configs[tenant_id]["pool_size"] == 5
        assert mgr._pool_configs[tenant_id]["max_overflow"] == 10

    def test_dispose_tenant_pool_concurrent_single_tenant_disposes_once(
        self, monkeypatch
    ):
        mgr = TenantConnectionPoolManager(database_url="postgresql://u:p@localhost/db")
        tenant_id = uuid4()
        engines, _ = _install_pool_manager_fakes(monkeypatch)
        mgr.create_tenant_pool(tenant_id)
        engine = engines[0]

        thread_count = 16
        start_barrier = threading.Barrier(thread_count)
        errors = []
        error_lock = threading.Lock()

        def worker():
            try:
                start_barrier.wait()
                mgr.dispose_tenant_pool(tenant_id)
            except Exception as exc:  # pragma: no cover - should never happen
                with error_lock:
                    errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(thread_count)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)

        assert all(not thread.is_alive() for thread in threads)
        assert errors == []
        assert engine.dispose.call_count == 1
        assert tenant_id not in mgr._pools
        assert tenant_id not in mgr._pool_configs

    def test_create_and_dispose_tenant_pool_concurrent_access_is_consistent(
        self, monkeypatch
    ):
        mgr = TenantConnectionPoolManager(database_url="postgresql://u:p@localhost/db")
        tenant_id = uuid4()
        _install_pool_manager_fakes(monkeypatch)

        thread_count = 12
        start_barrier = threading.Barrier(thread_count)
        errors = []
        error_lock = threading.Lock()

        def creator():
            try:
                start_barrier.wait()
                for _ in range(100):
                    mgr.create_tenant_pool(tenant_id)
            except Exception as exc:  # pragma: no cover - should never happen
                with error_lock:
                    errors.append(exc)

        def disposer():
            try:
                start_barrier.wait()
                for _ in range(100):
                    mgr.dispose_tenant_pool(tenant_id)
            except Exception as exc:  # pragma: no cover - should never happen
                with error_lock:
                    errors.append(exc)

        threads = []
        for _ in range(thread_count // 2):
            threads.append(threading.Thread(target=creator))
            threads.append(threading.Thread(target=disposer))

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert all(not thread.is_alive() for thread in threads)
        assert errors == []
        assert set(mgr._pools) == set(mgr._pool_configs)

        if tenant_id in mgr._pools:
            session = mgr.get_tenant_session(tenant_id)
            assert session is not None
        else:
            assert mgr.get_pool_stats(tenant_id) == {"error": "No pool exists"}
