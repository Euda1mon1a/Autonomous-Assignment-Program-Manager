"""Tests for Celery application configuration."""

from celery import Celery

from app.core.celery_app import celery_app, get_celery_app


# ==================== Celery App Instance ====================


class TestCeleryAppInstance:
    def test_is_celery(self):
        assert isinstance(celery_app, Celery)

    def test_app_name(self):
        assert celery_app.main == "residency_scheduler"


# ==================== Serialization Config ====================


class TestSerializationConfig:
    def test_task_serializer(self):
        assert celery_app.conf.task_serializer == "json"

    def test_accept_content(self):
        assert "json" in celery_app.conf.accept_content

    def test_result_serializer(self):
        assert celery_app.conf.result_serializer == "json"


# ==================== Timezone Config ====================


class TestTimezoneConfig:
    def test_timezone_utc(self):
        assert celery_app.conf.timezone == "UTC"

    def test_enable_utc(self):
        assert celery_app.conf.enable_utc is True


# ==================== Task Config ====================


class TestTaskConfig:
    def test_track_started(self):
        assert celery_app.conf.task_track_started is True

    def test_time_limit(self):
        assert celery_app.conf.task_time_limit == 600

    def test_soft_time_limit(self):
        assert celery_app.conf.task_soft_time_limit == 540

    def test_soft_less_than_hard(self):
        assert celery_app.conf.task_soft_time_limit < celery_app.conf.task_time_limit

    def test_result_expires(self):
        assert celery_app.conf.result_expires == 3600


# ==================== Worker Config ====================


class TestWorkerConfig:
    def test_prefetch_multiplier(self):
        assert celery_app.conf.worker_prefetch_multiplier == 1

    def test_concurrency(self):
        assert celery_app.conf.worker_concurrency == 4


# ==================== Beat Schedule ====================


class TestBeatSchedule:
    def test_has_health_check(self):
        assert "resilience-health-check" in celery_app.conf.beat_schedule

    def test_has_contingency_analysis(self):
        assert "resilience-contingency-analysis" in celery_app.conf.beat_schedule

    def test_has_precompute_fallbacks(self):
        assert "resilience-precompute-fallbacks" in celery_app.conf.beat_schedule

    def test_has_utilization_forecast(self):
        assert "resilience-utilization-forecast" in celery_app.conf.beat_schedule

    def test_has_metrics_snapshot(self):
        assert "schedule-metrics-hourly-snapshot" in celery_app.conf.beat_schedule

    def test_has_metrics_cleanup(self):
        assert "schedule-metrics-daily-cleanup" in celery_app.conf.beat_schedule

    def test_has_export_scheduled(self):
        assert "export-run-scheduled" in celery_app.conf.beat_schedule

    def test_has_rotation_check(self):
        assert "security-check-scheduled-rotations" in celery_app.conf.beat_schedule

    def test_has_stack_health(self):
        assert "stack-health-periodic" in celery_app.conf.beat_schedule

    def test_health_check_task_name(self):
        task = celery_app.conf.beat_schedule["resilience-health-check"]
        assert task["task"] == "app.resilience.tasks.periodic_health_check"

    def test_health_check_queue(self):
        task = celery_app.conf.beat_schedule["resilience-health-check"]
        assert task["options"]["queue"] == "resilience"

    def test_all_tasks_have_schedule(self):
        for name, config in celery_app.conf.beat_schedule.items():
            assert "schedule" in config, f"{name} missing schedule"

    def test_all_tasks_have_task_key(self):
        for name, config in celery_app.conf.beat_schedule.items():
            assert "task" in config, f"{name} missing task key"


# ==================== Task Routes ====================


class TestTaskRoutes:
    def test_resilience_queue(self):
        routes = celery_app.conf.task_routes
        assert "app.resilience.tasks.*" in routes
        assert routes["app.resilience.tasks.*"]["queue"] == "resilience"

    def test_notifications_queue(self):
        routes = celery_app.conf.task_routes
        assert "app.notifications.tasks.*" in routes

    def test_metrics_queue(self):
        routes = celery_app.conf.task_routes
        assert "app.tasks.schedule_metrics_tasks.*" in routes
        assert routes["app.tasks.schedule_metrics_tasks.*"]["queue"] == "metrics"

    def test_exports_queue(self):
        routes = celery_app.conf.task_routes
        assert "app.exports.jobs.*" in routes
        assert routes["app.exports.jobs.*"]["queue"] == "exports"

    def test_security_queue(self):
        routes = celery_app.conf.task_routes
        assert "app.security.rotation_tasks.*" in routes
        assert routes["app.security.rotation_tasks.*"]["queue"] == "security"


# ==================== Task Queues ====================


class TestTaskQueues:
    def test_default_queue(self):
        assert "default" in celery_app.conf.task_queues

    def test_resilience_queue(self):
        assert "resilience" in celery_app.conf.task_queues

    def test_notifications_queue(self):
        assert "notifications" in celery_app.conf.task_queues

    def test_metrics_queue(self):
        assert "metrics" in celery_app.conf.task_queues

    def test_exports_queue(self):
        assert "exports" in celery_app.conf.task_queues

    def test_security_queue(self):
        assert "security" in celery_app.conf.task_queues

    def test_maintenance_queue(self):
        assert "maintenance" in celery_app.conf.task_queues


# ==================== get_celery_app ====================


class TestGetCeleryApp:
    def test_returns_same_instance(self):
        assert get_celery_app() is celery_app

    def test_is_celery(self):
        assert isinstance(get_celery_app(), Celery)


# ==================== Include Config ====================


class TestIncludeConfig:
    def test_includes_resilience_tasks(self):
        assert "app.resilience.tasks" in celery_app.conf.include

    def test_includes_notification_tasks(self):
        assert "app.notifications.tasks" in celery_app.conf.include

    def test_includes_metrics_tasks(self):
        assert "app.tasks.schedule_metrics_tasks" in celery_app.conf.include

    def test_includes_export_jobs(self):
        assert "app.exports.jobs" in celery_app.conf.include

    def test_includes_rotation_tasks(self):
        assert "app.security.rotation_tasks" in celery_app.conf.include
