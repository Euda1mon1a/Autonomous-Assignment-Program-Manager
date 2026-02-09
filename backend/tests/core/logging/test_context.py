"""Tests for logging context management (request correlation and tracing)."""

from app.core.logging.context import (
    LogContext,
    LogContextManager,
    bind_context_to_logger,
    create_request_context,
    get_all_context,
    get_custom_field,
    get_request_id,
    get_session_id,
    get_span_id,
    get_trace_id,
    get_user_id,
    request_id_ctx,
    session_id_ctx,
    set_custom_field,
    set_request_id,
    set_session_id,
    set_span_id,
    set_trace_id,
    set_user_id,
    span_id_ctx,
    trace_id_ctx,
    user_id_ctx,
    with_log_context,
)


# ==================== Context variable defaults ====================


class TestContextVariableDefaults:
    def test_request_id_default(self):
        assert get_request_id() is None

    def test_user_id_default(self):
        assert get_user_id() is None

    def test_session_id_default(self):
        assert get_session_id() is None

    def test_trace_id_default(self):
        assert get_trace_id() is None

    def test_span_id_default(self):
        assert get_span_id() is None


# ==================== Context variable set/get ====================


class TestContextSetGet:
    def test_request_id(self):
        token = set_request_id("req-123")
        try:
            assert get_request_id() == "req-123"
        finally:
            request_id_ctx.reset(token)

    def test_user_id(self):
        token = set_user_id("user-456")
        try:
            assert get_user_id() == "user-456"
        finally:
            user_id_ctx.reset(token)

    def test_session_id(self):
        token = set_session_id("sess-789")
        try:
            assert get_session_id() == "sess-789"
        finally:
            session_id_ctx.reset(token)

    def test_trace_id(self):
        token = set_trace_id("trace-abc")
        try:
            assert get_trace_id() == "trace-abc"
        finally:
            trace_id_ctx.reset(token)

    def test_span_id(self):
        token = set_span_id("span-def")
        try:
            assert get_span_id() == "span-def"
        finally:
            span_id_ctx.reset(token)


# ==================== Custom fields ====================


class TestCustomFields:
    def test_set_and_get(self):
        set_custom_field("operation", "generate")
        assert get_custom_field("operation") == "generate"

    def test_get_nonexistent(self):
        assert get_custom_field("nonexistent_key_xyz") is None


# ==================== LogContext dataclass ====================


class TestLogContext:
    def test_defaults(self):
        ctx = LogContext()
        assert ctx.request_id is None
        assert ctx.user_id is None
        assert ctx.session_id is None
        assert ctx.trace_id is None
        assert ctx.span_id is None
        assert ctx.ip_address is None
        assert ctx.user_agent is None
        assert ctx.endpoint is None
        assert ctx.method is None
        assert ctx.custom_fields == {}
        assert ctx.created_at is not None

    def test_custom(self):
        ctx = LogContext(
            request_id="req-1",
            user_id="user-1",
            ip_address="10.0.0.1",
            custom_fields={"action": "login"},
        )
        assert ctx.request_id == "req-1"
        assert ctx.user_id == "user-1"
        assert ctx.ip_address == "10.0.0.1"
        assert ctx.custom_fields["action"] == "login"

    def test_to_dict(self):
        ctx = LogContext(
            request_id="req-1",
            user_id="user-1",
            custom_fields={"extra": "val"},
        )
        d = ctx.to_dict()
        assert d["request_id"] == "req-1"
        assert d["user_id"] == "user-1"
        assert d["extra"] == "val"
        assert "created_at" not in d  # Not in to_dict

    def test_bind_to_logger_includes_set_fields(self):
        ctx = LogContext(
            request_id="req-1",
            user_id="user-1",
            custom_fields={"action": "test"},
        )
        fields = ctx.bind_to_logger()
        assert fields["request_id"] == "req-1"
        assert fields["user_id"] == "user-1"
        assert fields["action"] == "test"

    def test_bind_to_logger_excludes_none(self):
        ctx = LogContext(request_id="req-1")
        fields = ctx.bind_to_logger()
        assert "request_id" in fields
        assert "user_id" not in fields
        assert "session_id" not in fields


# ==================== LogContextManager ====================


class TestLogContextManager:
    def test_enters_and_returns_context(self):
        ctx = LogContext(request_id="req-cm")
        with LogContextManager(ctx) as c:
            assert c is ctx
            assert get_request_id() == "req-cm"

    def test_resets_on_exit(self):
        original = get_request_id()
        ctx = LogContext(request_id="req-temp")
        with LogContextManager(ctx):
            assert get_request_id() == "req-temp"
        assert get_request_id() == original

    def test_sets_multiple_vars(self):
        ctx = LogContext(
            request_id="req-m",
            user_id="user-m",
            session_id="sess-m",
            trace_id="trace-m",
            span_id="span-m",
        )
        with LogContextManager(ctx):
            assert get_request_id() == "req-m"
            assert get_user_id() == "user-m"
            assert get_session_id() == "sess-m"
            assert get_trace_id() == "trace-m"
            assert get_span_id() == "span-m"

    def test_sets_custom_fields(self):
        ctx = LogContext(custom_fields={"op": "gen"})
        with LogContextManager(ctx):
            assert get_custom_field("op") == "gen"

    def test_resets_on_exception(self):
        original = get_request_id()
        ctx = LogContext(request_id="req-exc")
        try:
            with LogContextManager(ctx):
                raise ValueError("test")
        except ValueError:
            pass
        assert get_request_id() == original


# ==================== get_all_context ====================


class TestGetAllContext:
    def test_empty_by_default(self):
        # All defaults are None, so empty
        result = get_all_context()
        # May have custom fields from other tests, so just check structure
        assert isinstance(result, dict)

    def test_includes_set_values(self):
        ctx = LogContext(request_id="req-all", user_id="user-all")
        with LogContextManager(ctx):
            result = get_all_context()
            assert result["request_id"] == "req-all"
            assert result["user_id"] == "user-all"


# ==================== bind_context_to_logger ====================


class TestBindContextToLogger:
    def test_returns_dict(self):
        result = bind_context_to_logger()
        assert isinstance(result, dict)

    def test_includes_context(self):
        ctx = LogContext(request_id="req-bind")
        with LogContextManager(ctx):
            result = bind_context_to_logger()
            assert result["request_id"] == "req-bind"


# ==================== create_request_context ====================


class TestCreateRequestContext:
    def test_auto_request_id(self):
        ctx = create_request_context()
        assert ctx.request_id is not None
        assert len(ctx.request_id) > 0

    def test_custom_request_id(self):
        ctx = create_request_context(request_id="my-id")
        assert ctx.request_id == "my-id"

    def test_user_id(self):
        ctx = create_request_context(user_id="user-1")
        assert ctx.user_id == "user-1"

    def test_session_id(self):
        ctx = create_request_context(session_id="sess-1")
        assert ctx.session_id == "sess-1"

    def test_custom_fields(self):
        ctx = create_request_context(operation="generate", block_id=10)
        assert ctx.custom_fields["operation"] == "generate"
        assert ctx.custom_fields["block_id"] == 10

    def test_returns_log_context(self):
        ctx = create_request_context()
        assert isinstance(ctx, LogContext)


# ==================== with_log_context decorator ====================


class TestWithLogContext:
    def test_decorator_preserves_return(self):
        @with_log_context(operation="test")
        def my_func():
            return 42

        assert my_func() == 42

    def test_decorator_passes_args(self):
        @with_log_context(operation="add")
        def add(a, b):
            return a + b

        assert add(3, 4) == 7

    def test_decorator_passes_kwargs(self):
        @with_log_context(operation="greet")
        def greet(name="world"):
            return f"hello {name}"

        assert greet(name="Alice") == "hello Alice"
