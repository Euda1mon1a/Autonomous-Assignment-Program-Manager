"""Tests for message queue adapters and utilities."""

import asyncio
import json
import os
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.messaging.queue import (
    DeliveryMode,
    Message,
    QueueConfig,
    RabbitMQAdapter,
    RedisQueueAdapter,
    RetryPolicy,
    create_queue_adapter,
)


class TestRetryPolicy:
    """Test suite for RetryPolicy."""

    def test_default_values(self):
        """Test RetryPolicy default values."""
        policy = RetryPolicy()
        assert policy.max_retries == 3
        assert policy.initial_delay == 1.0
        assert policy.max_delay == 300.0
        assert policy.exponential_base == 2.0
        assert policy.jitter == 0.1

    def test_custom_values(self):
        """Test RetryPolicy with custom values."""
        policy = RetryPolicy(
            max_retries=5,
            initial_delay=2.0,
            max_delay=600.0,
            exponential_base=3.0,
            jitter=0.2,
        )
        assert policy.max_retries == 5
        assert policy.initial_delay == 2.0
        assert policy.max_delay == 600.0
        assert policy.exponential_base == 3.0
        assert policy.jitter == 0.2

    def test_get_delay_exponential_backoff(self):
        """Test exponential backoff calculation."""
        policy = RetryPolicy(
            initial_delay=1.0, exponential_base=2.0, jitter=0.0, max_delay=1000.0
        )

        # Attempt 0: 1.0 * (2^0) = 1.0
        delay0 = policy.get_delay(0)
        assert delay0 == 1.0

        # Attempt 1: 1.0 * (2^1) = 2.0
        delay1 = policy.get_delay(1)
        assert delay1 == 2.0

        # Attempt 2: 1.0 * (2^2) = 4.0
        delay2 = policy.get_delay(2)
        assert delay2 == 4.0

        # Attempt 3: 1.0 * (2^3) = 8.0
        delay3 = policy.get_delay(3)
        assert delay3 == 8.0

    def test_get_delay_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        policy = RetryPolicy(
            initial_delay=1.0, exponential_base=2.0, jitter=0.0, max_delay=5.0
        )

        # Attempt 10 would be 1024.0, but should be capped at 5.0
        delay = policy.get_delay(10)
        assert delay == 5.0

    def test_get_delay_with_jitter(self):
        """Test delay calculation with jitter."""
        policy = RetryPolicy(
            initial_delay=10.0, exponential_base=2.0, jitter=0.5, max_delay=1000.0
        )

        # With jitter, delay should be in range [base, base * 1.5]
        base_delay = 10.0
        max_jitter = base_delay * 1.5

        delays = [policy.get_delay(0) for _ in range(100)]

        # All delays should be >= base_delay and <= max_jitter
        assert all(base_delay <= d <= max_jitter for d in delays)

        # Delays should vary (not all the same due to randomness)
        assert len(set(delays)) > 1


class TestQueueConfig:
    """Test suite for QueueConfig."""

    def test_default_values(self):
        """Test QueueConfig default values."""
        config = QueueConfig()
        assert config.backend == "redis"
        assert config.url == "redis://localhost:6379/0"
        assert config.exchange == "scheduler.events"
        assert config.exchange_type == "topic"
        assert config.default_queue == "scheduler.default"
        assert config.dlx_exchange == "scheduler.dlx"
        assert config.dlx_queue == "scheduler.dead_letters"
        assert config.prefetch_count == 10
        assert config.message_ttl is None
        assert config.max_priority == 10
        assert config.connection_timeout == 30.0
        assert config.reconnect_delay == 5.0

    def test_custom_values(self):
        """Test QueueConfig with custom values."""
        config = QueueConfig(
            backend="rabbitmq",
            url="amqp://user:pass@localhost:5672/",
            exchange="custom.exchange",
            prefetch_count=20,
        )
        assert config.backend == "rabbitmq"
        assert config.url == "amqp://user:pass@localhost:5672/"
        assert config.exchange == "custom.exchange"
        assert config.prefetch_count == 20

    def test_from_env(self, monkeypatch):
        """Test loading configuration from environment variables."""
        monkeypatch.setenv("MESSAGE_QUEUE_BACKEND", "rabbitmq")
        monkeypatch.setenv("MESSAGE_QUEUE_URL", "amqp://test:test@localhost/")
        monkeypatch.setenv("MESSAGE_QUEUE_EXCHANGE", "test.exchange")
        monkeypatch.setenv("MESSAGE_QUEUE_PREFETCH_COUNT", "15")
        monkeypatch.setenv("MESSAGE_QUEUE_TTL", "60000")
        monkeypatch.setenv("MESSAGE_QUEUE_MAX_PRIORITY", "5")

        config = QueueConfig.from_env()

        assert config.backend == "rabbitmq"
        assert config.url == "amqp://test:test@localhost/"
        assert config.exchange == "test.exchange"
        assert config.prefetch_count == 15
        assert config.message_ttl == 60000
        assert config.max_priority == 5

    def test_from_env_defaults(self, monkeypatch):
        """Test from_env uses defaults when env vars not set."""
        # Clear any existing env vars
        for key in os.environ.copy():
            if key.startswith("MESSAGE_QUEUE_"):
                monkeypatch.delenv(key, raising=False)

        config = QueueConfig.from_env()

        assert config.backend == "redis"
        assert config.url == "redis://localhost:6379/0"
        assert config.prefetch_count == 10


class TestMessage:
    """Test suite for Message."""

    def test_default_values(self):
        """Test Message default values."""
        msg = Message(body={"key": "value"})

        assert msg.body == {"key": "value"}
        assert msg.routing_key == ""
        assert msg.headers == {}
        assert msg.delivery_mode == DeliveryMode.PERSISTENT
        assert msg.priority == 5
        assert msg.correlation_id is None
        assert msg.reply_to is None
        assert msg.expiration is None
        assert msg.message_id is not None  # Auto-generated
        assert msg.timestamp is not None  # Auto-generated
        assert msg.content_type == "application/json"
        assert msg.content_encoding == "utf-8"

    def test_custom_values(self):
        """Test Message with custom values."""
        timestamp = datetime.utcnow()
        msg = Message(
            body={"test": "data"},
            routing_key="test.route",
            headers={"x-custom": "value"},
            delivery_mode=DeliveryMode.TRANSIENT,
            priority=10,
            correlation_id="corr-123",
            reply_to="reply.queue",
            expiration=60000,
            message_id="msg-123",
            timestamp=timestamp,
        )

        assert msg.body == {"test": "data"}
        assert msg.routing_key == "test.route"
        assert msg.headers == {"x-custom": "value"}
        assert msg.delivery_mode == DeliveryMode.TRANSIENT
        assert msg.priority == 10
        assert msg.correlation_id == "corr-123"
        assert msg.reply_to == "reply.queue"
        assert msg.expiration == 60000
        assert msg.message_id == "msg-123"
        assert msg.timestamp == timestamp

    def test_message_id_auto_generation(self):
        """Test that message_id is auto-generated if not provided."""
        msg1 = Message(body={})
        msg2 = Message(body={})

        assert msg1.message_id is not None
        assert msg2.message_id is not None
        assert msg1.message_id != msg2.message_id  # Should be unique

    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated if not provided."""
        msg = Message(body={})
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)


class TestMessageQueueAdapter:
    """Test suite for MessageQueueAdapter base class."""

    def test_serialize_message(self):
        """Test message serialization."""
        config = QueueConfig()
        adapter = RedisQueueAdapter(config)  # Use concrete implementation

        msg = Message(body={"key": "value", "number": 42, "nested": {"data": "test"}})

        serialized = adapter.serialize_message(msg)

        assert isinstance(serialized, bytes)
        deserialized = json.loads(serialized.decode("utf-8"))
        assert deserialized == msg.body

    def test_serialize_message_with_datetime(self):
        """Test message serialization with datetime objects."""
        config = QueueConfig()
        adapter = RedisQueueAdapter(config)

        now = datetime.utcnow()
        msg = Message(body={"timestamp": now})

        serialized = adapter.serialize_message(msg)
        deserialized = json.loads(serialized.decode("utf-8"))

        # Datetime should be converted to string
        assert isinstance(deserialized["timestamp"], str)

    def test_deserialize_message(self):
        """Test message deserialization."""
        config = QueueConfig()
        adapter = RedisQueueAdapter(config)

        data = {"key": "value", "number": 42}
        serialized = json.dumps(data).encode("utf-8")

        deserialized = adapter.deserialize_message(serialized)

        assert deserialized == data

    def test_deserialize_invalid_json(self):
        """Test deserialization with invalid JSON."""
        config = QueueConfig()
        adapter = RedisQueueAdapter(config)

        invalid_json = b"not valid json {{"

        with pytest.raises(json.JSONDecodeError):
            adapter.deserialize_message(invalid_json)

    def test_is_connected_initial_state(self):
        """Test is_connected property initial state."""
        config = QueueConfig()
        adapter = RedisQueueAdapter(config)

        assert adapter.is_connected is False


class TestCreateQueueAdapter:
    """Test suite for create_queue_adapter factory function."""

    def test_create_redis_adapter(self):
        """Test creating Redis adapter."""
        config = QueueConfig(backend="redis")
        adapter = create_queue_adapter(config)

        assert isinstance(adapter, RedisQueueAdapter)
        assert adapter.config == config

    def test_create_rabbitmq_adapter(self):
        """Test creating RabbitMQ adapter."""
        config = QueueConfig(backend="rabbitmq")
        adapter = create_queue_adapter(config)

        assert isinstance(adapter, RabbitMQAdapter)
        assert adapter.config == config

    def test_create_adapter_invalid_backend(self):
        """Test creating adapter with invalid backend."""
        config = QueueConfig(backend="invalid")

        with pytest.raises(ValueError, match="Unsupported message queue backend"):
            create_queue_adapter(config)

    def test_create_adapter_from_env(self, monkeypatch):
        """Test creating adapter from environment variables."""
        monkeypatch.setenv("MESSAGE_QUEUE_BACKEND", "redis")
        monkeypatch.setenv("MESSAGE_QUEUE_URL", "redis://localhost:6379/1")

        adapter = create_queue_adapter()

        assert isinstance(adapter, RedisQueueAdapter)
        assert adapter.config.backend == "redis"
        assert adapter.config.url == "redis://localhost:6379/1"


class TestRedisQueueAdapter:
    """Test suite for RedisQueueAdapter."""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful Redis connection."""
        config = QueueConfig(backend="redis")
        adapter = RedisQueueAdapter(config)

        # Mock redis connection
        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock()
            mock_from_url.return_value = mock_redis

            await adapter.connect()

            assert adapter.is_connected is True
            mock_from_url.assert_called_once()
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        """Test connecting when already connected."""
        config = QueueConfig(backend="redis")
        adapter = RedisQueueAdapter(config)
        adapter._connected = True

        with patch("redis.asyncio.from_url") as mock_from_url:
            await adapter.connect()
            # Should not attempt connection
            mock_from_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test Redis disconnection."""
        config = QueueConfig(backend="redis")
        adapter = RedisQueueAdapter(config)

        # Setup connected state
        mock_redis = AsyncMock()
        adapter._redis = mock_redis
        adapter._connected = True

        await adapter.disconnect()

        assert adapter.is_connected is False
        mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_message(self):
        """Test publishing message to Redis."""
        config = QueueConfig(backend="redis")
        adapter = RedisQueueAdapter(config)

        # Setup connected state
        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()
        mock_redis.expire = AsyncMock()
        adapter._redis = mock_redis
        adapter._connected = True

        msg = Message(body={"test": "data"}, routing_key="test.queue")

        result = await adapter.publish(msg)

        assert result is True
        mock_redis.lpush.assert_called_once()

        # Verify the key format
        call_args = mock_redis.lpush.call_args
        assert call_args[0][0] == f"{config.exchange}:test.queue"

    @pytest.mark.asyncio
    async def test_publish_not_connected(self):
        """Test publishing when not connected raises error."""
        config = QueueConfig(backend="redis")
        adapter = RedisQueueAdapter(config)

        msg = Message(body={"test": "data"})

        with pytest.raises(RuntimeError, match="Not connected to Redis"):
            await adapter.publish(msg)

    @pytest.mark.asyncio
    async def test_purge_queue(self):
        """Test purging Redis queue."""
        config = QueueConfig(backend="redis")
        adapter = RedisQueueAdapter(config)

        # Setup connected state
        mock_redis = AsyncMock()
        mock_redis.llen = AsyncMock(side_effect=[5, 2, 1])  # queue, processing, retry
        mock_redis.zcard = AsyncMock(return_value=1)
        mock_redis.delete = AsyncMock()
        adapter._redis = mock_redis
        adapter._connected = True

        count = await adapter.purge_queue("test.queue")

        assert count == 8  # 5 + 2 + 1
        mock_redis.delete.assert_called_once()


class TestRabbitMQAdapter:
    """Test suite for RabbitMQAdapter."""

    @pytest.mark.asyncio
    async def test_connect_import_error(self):
        """Test RabbitMQ connect with missing aio_pika."""
        config = QueueConfig(backend="rabbitmq")
        adapter = RabbitMQAdapter(config)

        with (
            patch(
                "builtins.__import__",
                side_effect=ImportError("No module named 'aio_pika'"),
            ),
            pytest.raises(ImportError),
        ):
            await adapter.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test RabbitMQ disconnection."""
        config = QueueConfig(backend="rabbitmq")
        adapter = RabbitMQAdapter(config)

        # Setup connected state
        mock_channel = AsyncMock()
        mock_channel.is_closed = False
        mock_connection = AsyncMock()
        mock_connection.is_closed = False

        adapter._channel = mock_channel
        adapter._connection = mock_connection
        adapter._connected = True

        await adapter.disconnect()

        assert adapter.is_connected is False
        mock_channel.close.assert_called_once()
        mock_connection.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_not_connected(self):
        """Test publishing when not connected raises error."""
        config = QueueConfig(backend="rabbitmq")
        adapter = RabbitMQAdapter(config)

        msg = Message(body={"test": "data"})

        with pytest.raises(RuntimeError, match="Not connected to RabbitMQ"):
            await adapter.publish(msg)

    @pytest.mark.asyncio
    async def test_declare_queue_not_connected(self):
        """Test declaring queue when not connected raises error."""
        config = QueueConfig(backend="rabbitmq")
        adapter = RabbitMQAdapter(config)

        with pytest.raises(RuntimeError, match="Not connected to RabbitMQ"):
            await adapter.declare_queue("test.queue")

    @pytest.mark.asyncio
    async def test_bind_queue_not_connected(self):
        """Test binding queue when not connected raises error."""
        config = QueueConfig(backend="rabbitmq")
        adapter = RabbitMQAdapter(config)

        with pytest.raises(RuntimeError, match="Not connected to RabbitMQ"):
            await adapter.bind_queue("test.queue", "test.exchange")


class TestIntegrationScenarios:
    """Integration test scenarios for message queue patterns."""

    @pytest.mark.asyncio
    async def test_publish_consume_pattern_redis(self):
        """Test publish-consume pattern with Redis adapter."""
        config = QueueConfig(backend="redis", default_queue="test.queue")
        adapter = RedisQueueAdapter(config)

        # Mock Redis client
        mock_redis = AsyncMock()
        messages_queue = []

        async def mock_lpush(key, value):
            messages_queue.append((key, value))
            return 1

        async def mock_brpop(key, timeout):
            await asyncio.sleep(0.01)  # Simulate blocking
            if messages_queue:
                key, value = messages_queue.pop(0)
                return (key.encode(), value)
            return None

        mock_redis.lpush = mock_lpush
        mock_redis.brpop = mock_brpop
        mock_redis.lrem = AsyncMock()
        mock_redis.ping = AsyncMock()

        adapter._redis = mock_redis
        adapter._connected = True

        # Publish message
        msg = Message(body={"action": "test"}, routing_key="test.queue")
        result = await adapter.publish(msg)

        assert result is True
        assert len(messages_queue) == 1

    @pytest.mark.asyncio
    async def test_message_routing_patterns(self):
        """Test different message routing patterns."""
        config = QueueConfig(exchange="events", exchange_type="topic")
        adapter = RedisQueueAdapter(config)

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock()
        adapter._redis = mock_redis
        adapter._connected = True

        # Test different routing patterns
        patterns = [
            "schedule.created",
            "schedule.updated",
            "assignment.changed",
            "conflict.detected",
        ]

        for pattern in patterns:
            msg = Message(body={"event": pattern}, routing_key=pattern)
            await adapter.publish(msg)

        # Verify all messages were published with correct routing keys
        assert mock_redis.lpush.call_count == len(patterns)
