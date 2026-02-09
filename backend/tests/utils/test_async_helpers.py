"""Tests for async utility functions."""

import asyncio
import time

import pytest

from app.utils.async_helpers import (
    async_cache,
    gather_with_errors,
    retry_async,
    run_with_timeout,
)


class TestRunWithTimeout:
    """Tests for run_with_timeout."""

    @pytest.mark.asyncio
    async def test_completes_within_timeout(self):
        async def quick():
            return 42

        result = await run_with_timeout(quick(), timeout=1.0)
        assert result == 42

    @pytest.mark.asyncio
    async def test_raises_on_timeout(self):
        async def slow():
            await asyncio.sleep(10)
            return "never"

        with pytest.raises(asyncio.TimeoutError):
            await run_with_timeout(slow(), timeout=0.05)

    @pytest.mark.asyncio
    async def test_propagates_exception(self):
        async def failing():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            await run_with_timeout(failing(), timeout=1.0)


class TestGatherWithErrors:
    """Tests for gather_with_errors."""

    @pytest.mark.asyncio
    async def test_all_succeed(self):
        async def ok(n):
            return n

        results = await gather_with_errors(ok(1), ok(2), ok(3))
        assert results == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_some_fail(self):
        async def ok():
            return "ok"

        async def fail():
            raise ValueError("fail")

        results = await gather_with_errors(ok(), fail(), ok())
        assert results[0] == "ok"
        assert isinstance(results[1], ValueError)
        assert results[2] == "ok"

    @pytest.mark.asyncio
    async def test_all_fail(self):
        async def fail(msg):
            raise RuntimeError(msg)

        results = await gather_with_errors(fail("a"), fail("b"))
        assert all(isinstance(r, RuntimeError) for r in results)

    @pytest.mark.asyncio
    async def test_empty(self):
        results = await gather_with_errors()
        assert results == []


class TestRetryAsync:
    """Tests for retry_async."""

    @pytest.mark.asyncio
    async def test_succeeds_first_try(self):
        call_count = 0

        async def success():
            nonlocal call_count
            call_count += 1
            return "done"

        result = await retry_async(success, max_retries=3, delay=0.01)
        assert result == "done"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_succeeds_after_retries(self):
        call_count = 0

        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("not yet")
            return "success"

        result = await retry_async(flaky, max_retries=3, delay=0.01)
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_exhausts_retries_raises(self):
        async def always_fail():
            raise RuntimeError("always fails")

        with pytest.raises(RuntimeError, match="always fails"):
            await retry_async(always_fail, max_retries=2, delay=0.01)

    @pytest.mark.asyncio
    async def test_backoff_increases_delay(self):
        call_count = 0
        timestamps = []

        async def record_time():
            nonlocal call_count
            call_count += 1
            timestamps.append(time.monotonic())
            if call_count < 3:
                raise RuntimeError("retry")
            return "ok"

        await retry_async(record_time, max_retries=3, delay=0.05, backoff=2.0)
        assert len(timestamps) == 3
        # Second delay should be roughly 2x the first
        delay1 = timestamps[1] - timestamps[0]
        delay2 = timestamps[2] - timestamps[1]
        assert delay2 > delay1 * 1.5  # Allow some timing slack

    @pytest.mark.asyncio
    async def test_zero_retries_fails_immediately(self):
        call_count = 0

        async def fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("no retries")

        with pytest.raises(ValueError, match="no retries"):
            await retry_async(fail, max_retries=0, delay=0.01)
        assert call_count == 1


class TestAsyncCache:
    """Tests for async_cache decorator."""

    @pytest.mark.asyncio
    async def test_caches_result(self):
        call_count = 0

        @async_cache(ttl=60)
        async def expensive(x):
            nonlocal call_count
            call_count += 1
            return x * 2

        result1 = await expensive(5)
        result2 = await expensive(5)
        assert result1 == 10
        assert result2 == 10
        assert call_count == 1  # Only called once

    @pytest.mark.asyncio
    async def test_different_args_not_cached(self):
        call_count = 0

        @async_cache(ttl=60)
        async def compute(x):
            nonlocal call_count
            call_count += 1
            return x

        await compute(1)
        await compute(2)
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_ttl_expiration(self):
        call_count = 0

        @async_cache(ttl=0)  # Immediate expiration
        async def compute():
            nonlocal call_count
            call_count += 1
            return "result"

        await compute()
        # TTL=0 means the cached value is always stale
        await compute()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_clear_cache(self):
        call_count = 0

        @async_cache(ttl=60)
        async def compute():
            nonlocal call_count
            call_count += 1
            return "result"

        await compute()
        compute.clear_cache()
        await compute()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_kwargs_cached_separately(self):
        call_count = 0

        @async_cache(ttl=60)
        async def compute(x=1, y=2):
            nonlocal call_count
            call_count += 1
            return x + y

        await compute(x=1, y=2)
        await compute(x=1, y=3)
        assert call_count == 2
