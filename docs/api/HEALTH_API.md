# Health API

## Base Path

`/api/v1/health`

## Endpoints

- `GET /api/v1/health` - Root health check (same payload as liveness).
- `GET /api/v1/health/live` - Lightweight liveness probe.
- `GET /api/v1/health/ready` - Readiness probe for critical dependencies.
- `GET /api/v1/health/detailed` - Full health check across services.
- `GET /api/v1/health/deep` - Direct dependency connectivity checks.
- `GET /api/v1/health/services/{service_name}` - Single service health.
- `GET /api/v1/health/history` - Recent health check history.
- `GET /api/v1/health/metrics` - Health check metrics.
- `GET /api/v1/health/status` - Consolidated status summary.
- `GET /api/v1/health/dashboard` - Dashboard payload for UI monitoring.

## Unversioned Health Endpoints

These endpoints are exposed outside the versioned API and are used for basic status checks:

- `GET /health` - Basic health check.
- `GET /health/resilience` - Resilience system status summary.
- `GET /health/cache` - Cache subsystem status.
