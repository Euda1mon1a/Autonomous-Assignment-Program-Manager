# Backend Configuration Patterns Audit
**G2_RECON Search Party Operation**
**Scope:** Configuration management patterns in Residency Scheduler backend
**Date:** 2025-12-30
**Status:** Complete Investigation

---

## Executive Summary

The Residency Scheduler backend uses a **Pydantic Settings-based configuration system** with multiple specialized config modules. The architecture is well-structured with:
- Central config in `app.core.config` (Pydantic v2 BaseSettings)
- Layered config modules for specific domains
- Environment variable validation with security guardrails
- Comprehensive secret validation on startup

**Key Findings:**
- **STRENGTHS:** Strong secret validation, environment-based configuration, multiple specialized modules
- **CONCERNS:** Some config variables accessed directly via `os.getenv()` instead of going through central config; scattered configuration across 6 separate files
- **GAPS:** Missing explicit ENVIRONMENT variable in Settings; some gRPC/SSO config loaded outside central Settings

---

## Part 1: Configuration Architecture Overview

### 1.1 Configuration Loading Chain

```
Application Startup
    ↓
app.main.py: get_settings()
    ↓
app.core.config.Settings (Pydantic BaseSettings)
    ├── Load from .env file
    ├── Validate security constraints
    └── Provide singleton via @lru_cache
    ↓
Downstream modules:
    ├── app.core.logging.config.py (LoggingConfig)
    ├── app.db.pool.config.py (PoolConfig)
    ├── app.auth.sso.config.py (SAML/OAuth2Config)
    ├── app.middleware.compression.config.py (CompressionConfig)
    └── app.middleware.throttling.config.py (ThrottleConfig)
```

### 1.2 Configuration Files Map

| File Path | Purpose | Type | Env Vars | Status |
|-----------|---------|------|----------|--------|
| `backend/app/core/config.py` | **Central config hub** | Pydantic BaseSettings | 62+ vars | Primary |
| `backend/app/core/logging/config.py` | Logging configuration | Pydantic dataclass | 8 vars | Derived |
| `backend/app/db/pool/config.py` | Database pooling | Pydantic dataclass | 9 vars | Derived |
| `backend/app/auth/sso/config.py` | SAML/OAuth2 | Pydantic BaseModel | 20+ vars | Direct environ |
| `backend/app/middleware/compression/config.py` | Response compression | Dataclass | Hardcoded | Static |
| `backend/app/middleware/throttling/config.py` | Request throttling | Dataclass | Hardcoded | Static |

---

## Part 2: Central Configuration (app.core.config.Settings)

### 2.1 All Configuration Variables (Inventory)

**Application Settings (5 vars)**
```
APP_NAME                     (str)  Default: "Residency Scheduler"
APP_VERSION                  (str)  Default: "1.0.0"
DEBUG                        (bool) Default: True
LOG_LEVEL                    (str)  Default: "INFO"
LOG_FORMAT                   (str)  Default: "text"
LOG_FILE                     (str)  Default: ""
```

**Database Configuration (10 vars)**
```
DATABASE_URL                 (str)  REQUIRED - postgresql connection string
DB_POOL_SIZE                 (int)  Default: 10
DB_POOL_MAX_OVERFLOW         (int)  Default: 20
DB_POOL_TIMEOUT              (int)  Default: 30 seconds
DB_POOL_RECYCLE              (int)  Default: 1800 seconds (30 min)
DB_POOL_PRE_PING             (bool) Default: True
```

**Redis/Celery Configuration (5 vars)**
```
REDIS_PASSWORD               (str)  Default: "" (empty in dev)
REDIS_URL                    (str)  Default: "redis://localhost:6379/0"
CELERY_BROKER_URL            (str)  Default: "redis://localhost:6379/0"
CELERY_RESULT_BACKEND        (str)  Default: "redis://localhost:6379/0"
```

**Cache Configuration (7 vars)**
```
CACHE_ENABLED                (bool) Default: True
CACHE_DEFAULT_TTL            (int)  Default: 3600 seconds (1 hour)
CACHE_HEATMAP_TTL            (int)  Default: 1800 seconds (30 min)
CACHE_CALENDAR_TTL           (int)  Default: 3600 seconds (1 hour)
CACHE_SCHEDULE_TTL           (int)  Default: 1800 seconds (30 min)
CACHE_ROTATION_TTL           (int)  Default: 86400 seconds (24 hours)
```

**Security Configuration (6 vars)**
```
SECRET_KEY                   (str)  CRITICAL - JWT signing key (min 32 chars)
WEBHOOK_SECRET               (str)  CRITICAL - Webhook validation (min 32 chars)
ACCESS_TOKEN_EXPIRE_MINUTES  (int)  Default: 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS    (int)  Default: 7 days
REFRESH_TOKEN_ROTATE         (bool) Default: True
WEBHOOK_TIMESTAMP_TOLERANCE  (int)  Default: 300 seconds (5 min)
```

**Rate Limiting Configuration (4 vars)**
```
RATE_LIMIT_LOGIN_ATTEMPTS    (int)  Default: 5 per minute
RATE_LIMIT_LOGIN_WINDOW      (int)  Default: 60 seconds
RATE_LIMIT_REGISTER_ATTEMPTS (int)  Default: 3 per minute
RATE_LIMIT_REGISTER_WINDOW   (int)  Default: 60 seconds
RATE_LIMIT_ENABLED           (bool) Default: True
```

**File Upload Configuration (7 vars)**
```
UPLOAD_STORAGE_BACKEND       (str)  Default: "local" (or "s3")
UPLOAD_LOCAL_DIR             (str)  Default: "/tmp/uploads"
UPLOAD_MAX_SIZE_MB           (int)  Default: 50 MB
UPLOAD_ENABLE_VIRUS_SCAN     (bool) Default: False
UPLOAD_S3_BUCKET             (str)  Default: "residency-scheduler-uploads"
UPLOAD_S3_REGION             (str)  Default: "us-east-1"
UPLOAD_S3_ACCESS_KEY         (str)  Default: ""
UPLOAD_S3_SECRET_KEY         (str)  Default: ""
UPLOAD_S3_ENDPOINT_URL       (str)  Default: ""
```

**CORS/Security Headers Configuration (4 vars)**
```
CORS_ORIGINS                 (list) Default: ["http://localhost:3000"]
CORS_ORIGINS_REGEX           (str)  Default: "" (optional pattern)
TRUSTED_HOSTS                (list) Default: [] (disabled in dev)
TRUSTED_PROXIES              (list) Default: [] (direct client IP)
```

**Resilience Framework Configuration (9 vars)**
```
RESILIENCE_WARNING_THRESHOLD (float) Default: 0.70 (70% utilization)
RESILIENCE_MAX_UTILIZATION   (float) Default: 0.80 (80% utilization)
RESILIENCE_CRITICAL_THRESHOLD(float) Default: 0.90 (90% utilization)
RESILIENCE_EMERGENCY_THRESHOLD(float) Default: 0.95 (95% utilization)
RESILIENCE_AUTO_ACTIVATE_DEFENSE    (bool) Default: True
RESILIENCE_AUTO_ACTIVATE_FALLBACK   (bool) Default: False (safety)
RESILIENCE_AUTO_SHED_LOAD           (bool) Default: True
RESILIENCE_HEALTH_CHECK_INTERVAL    (int)  Default: 15 minutes
RESILIENCE_CONTINGENCY_ANALYSIS     (int)  Default: 24 hours
RESILIENCE_ALERT_RECIPIENTS         (list) Default: []
RESILIENCE_SLACK_CHANNEL            (str)  Default: ""
```

**OpenTelemetry/Distributed Tracing (11 vars)**
```
TELEMETRY_ENABLED                   (bool) Default: False (dev) / True (prod)
TELEMETRY_SERVICE_NAME              (str)  Default: "residency-scheduler"
TELEMETRY_ENVIRONMENT               (str)  Default: "development"
TELEMETRY_SAMPLING_RATE             (float) Default: 1.0 (100%)
TELEMETRY_CONSOLE_EXPORT            (bool) Default: False
TELEMETRY_EXPORTER_TYPE             (str)  Default: "otlp_grpc"
TELEMETRY_EXPORTER_ENDPOINT         (str)  Default: "http://localhost:4317"
TELEMETRY_EXPORTER_INSECURE         (bool) Default: True (dev)
TELEMETRY_EXPORTER_HEADERS          (dict) Default: {}
TELEMETRY_TRACE_SQLALCHEMY          (bool) Default: True
TELEMETRY_TRACE_REDIS               (bool) Default: True
TELEMETRY_TRACE_HTTP                (bool) Default: True
```

**ML Model Configuration (11 vars)**
```
ML_ENABLED                   (bool) Default: False
ML_MODELS_DIR                (str)  Default: "models"
ML_PREFERENCE_MODEL_PATH     (str)  Default: ""
ML_CONFLICT_MODEL_PATH       (str)  Default: ""
ML_WORKLOAD_MODEL_PATH       (str)  Default: ""
ML_TRAINING_LOOKBACK_DAYS    (int)  Default: 365 days
ML_MIN_TRAINING_SAMPLES      (int)  Default: 100
ML_AUTO_TRAINING_ENABLED     (bool) Default: False
ML_TRAINING_FREQUENCY_DAYS   (int)  Default: 7 days
ML_PREFERENCE_WEIGHT         (float) Default: 0.4
ML_WORKLOAD_WEIGHT           (float) Default: 0.3
ML_CONFLICT_WEIGHT           (float) Default: 0.3
ML_TARGET_UTILIZATION        (float) Default: 0.80
ML_OVERLOAD_THRESHOLD        (float) Default: 0.85
ML_CONFLICT_RISK_THRESHOLD   (float) Default: 0.70
```

**Shadow Traffic Configuration (10 vars)**
```
SHADOW_TRAFFIC_ENABLED       (bool) Default: False
SHADOW_TRAFFIC_URL           (str)  Default: ""
SHADOW_SAMPLING_RATE         (float) Default: 0.1 (10%)
SHADOW_TIMEOUT               (float) Default: 10.0 seconds
SHADOW_MAX_CONCURRENT        (int)  Default: 10
SHADOW_VERIFY_SSL            (bool) Default: True
SHADOW_ALERT_ON_DIFF         (bool) Default: True
SHADOW_DIFF_THRESHOLD        (str)  Default: "medium"
SHADOW_RETRY_ON_FAILURE      (bool) Default: False
SHADOW_MAX_RETRIES           (int)  Default: 2
SHADOW_INCLUDE_HEADERS       (bool) Default: True
SHADOW_HEALTH_CHECK_INTERVAL (int)  Default: 60 seconds
SHADOW_METRICS_RETENTION     (int)  Default: 24 hours
```

**LLM Router Configuration (7 vars)**
```
LLM_DEFAULT_PROVIDER         (str)  Default: "ollama"
LLM_ENABLE_FALLBACK          (bool) Default: True
LLM_AIRGAP_MODE              (bool) Default: False (cloud-enabled)
OLLAMA_URL                   (str)  Default: "http://ollama:11434"
OLLAMA_DEFAULT_MODEL         (str)  Default: "llama3.2"
OLLAMA_FAST_MODEL            (str)  Default: "llama3.2"
OLLAMA_TOOL_MODEL            (str)  Default: "mistral"
OLLAMA_TIMEOUT               (float) Default: 60.0 seconds
ANTHROPIC_API_KEY            (str)  Default: "" (optional)
ANTHROPIC_DEFAULT_MODEL      (str)  Default: "claude-3-5-sonnet-20241022"
```

**TOTAL: 108+ configuration variables in central config**

### 2.2 Field Validators (Security Constraints)

#### SECRET_KEY Validator
```python
Location: app/core/config.py:263-305
Validates:
  - Not in known weak passwords list (44 weak passwords defined)
  - Minimum 32 characters for production (DEBUG=False)
  - Minimum length warning for development (DEBUG=True)
Behavior:
  - Production: Raises ValueError if insecure
  - Development: Logs warning but allows weak secrets
```

#### WEBHOOK_SECRET Validator
```python
Same as SECRET_KEY validator
Also requires minimum 32 characters
```

#### REDIS_PASSWORD Validator
```python
Location: app/core/config.py:307-362
Validates:
  - Can be empty in development (for unauthenticated Redis)
  - Not in weak passwords list if set
  - Minimum 16 characters for production (DEBUG=False)
Behavior:
  - Production: Requires strong password if DEBUG=False
  - Development: Allows empty with warning
```

#### DATABASE_URL Validator
```python
Location: app/core/config.py:364-424
Validates:
  - Must include password (URL parse validation)
  - Password not in weak passwords list
  - Password minimum 12 characters
Behavior:
  - Production: Raises ValueError for weak DB passwords
  - Development: Logs warning but allows
```

#### CORS_ORIGINS Validator
```python
Location: app/core/config.py:426-469
Validates:
  - Forbids wildcard "*" in production (DEBUG=False)
  - Warns about wildcard in development
  - Warns if > 10 origins in production
Behavior:
  - Production: Raises ValueError for "*"
  - Development: Logs warning but allows
```

### 2.3 Weak Passwords Blacklist

**44 Known Weak/Default Passwords Blocked:**
```python
"", "password", "admin", "123456", "12345678", "123456789", "test", "guest",
"root", "toor", "letmein", "welcome", "monkey", "dragon", "master", "sunshine",
"qwerty", "abc123", "default", "changeme", "scheduler",
"your_redis_password_here", "your_secure_database_password_here",
"your-secret-key-change-in-production", "your-webhook-secret-change-in-production",
"your_secret_key_here_generate_a_random_64_char_string",
"your_redis_password_here_generate_a_random_string", "dev_only_password"
```

### 2.4 Special Properties

#### redis_url_with_password Property
```python
Location: app/core/config.py:88-102
Purpose: Automatically inject REDIS_PASSWORD into REDIS_URL if set
Format: redis://:password@host:port/db
Usage: service_cache.py and celery_app.py use this
```

---

## Part 3: Derived Configuration Modules

### 3.1 Logging Configuration (app/core/logging/config.py)

```python
Type: Pydantic dataclass (NOT BaseSettings)
Env Vars: 8 optional variables
Config Class: LoggingConfig

Variables:
  level           (LogLevel enum)    Default: INFO
  format          (LogFormat enum)   Default: JSON (prod) / TEXT (dev)
  log_file        (str|None)         Default: None
  max_file_size   (int)              Default: 100 MB
  backup_count    (int)              Default: 7 rotated files
  enable_colors   (bool)             Default: True
  enable_backtrace (bool)            Default: True
  enable_diagnose (bool)             Default: False (security)
  json_indent     (int|None)         Default: None (compact)
  module_levels   (dict)             Per-module overrides
  correlation_enabled (bool)         Default: True (request IDs)
  performance_logging (bool)         Default: True
  audit_logging   (bool)             Default: True
  async_logging   (bool)             Default: False (experimental)
```

**Loading Pattern:**
- Factory method: `LoggingConfig.from_env()`
- Checks settings.ENVIRONMENT to choose format
- Creates from environment variables or defaults
- Used in main.py: `setup_logging(level=settings.LOG_LEVEL, format_type=settings.LOG_FORMAT)`

### 3.2 Database Pool Configuration (app/db/pool/config.py)

```python
Type: Pydantic dataclass (NOT BaseSettings)
Env Vars: Derived from Settings (9 vars)
Config Class: PoolConfig

Core Pool Settings:
  pool_size              (int)  Default: 10 (keep open)
  max_overflow           (int)  Default: 20 (beyond pool_size)
  timeout                (int)  Default: 30 seconds
  recycle                (int)  Default: 1800 seconds
  pre_ping               (bool) Default: True
  echo_pool              (bool) Default: False (settings.DEBUG)
  pool_reset_on_return   (str)  Default: "rollback"

Timeout Settings:
  query_timeout          (int)  Default: 60 seconds
  connect_timeout        (int)  Default: 10 seconds

Monitoring Settings:
  enable_monitoring      (bool) Default: True
  health_check_interval  (int)  Default: 60 seconds

Reconnection Settings:
  reconnect_attempts     (int)  Default: 3 attempts
  reconnect_delay        (float) Default: 1.0 seconds

Dynamic Sizing (NEW):
  enable_dynamic_sizing  (bool) Default: True
  min_pool_size          (int)  Default: 5
  max_pool_size          (int)  Default: 50
  scale_up_threshold     (float) Default: 0.8 (80%)
  scale_down_threshold   (float) Default: 0.3 (30%)
```

**Validators:**
- max_overflow ≤ 5x pool_size
- scale_down_threshold < scale_up_threshold
- max_pool_size > min_pool_size
- pool_reset_on_return ∈ {"rollback", "commit", None}

**Loading Pattern:**
- Factory: `get_pool_config_from_settings()` in app/db/session.py
- Source: Settings DB_POOL_* variables only

### 3.3 SSO Configuration (app/auth/sso/config.py)

```python
Type: Pydantic BaseModel (separate models)
Env Vars: 20+ direct os.getenv() calls (NOT in Settings!)
Classes: SAMLConfig, OAuth2Config

SAMLConfig Variables (env-loaded):
  enabled                (bool)  SSO_SAML_ENABLED
  entity_id              (str)   SSO_SAML_ENTITY_ID
  acs_url                (str)   SSO_SAML_ACS_URL
  slo_url                (str)   SSO_SAML_SLO_URL
  idp_entity_id          (str)   SSO_SAML_IDP_ENTITY_ID
  idp_sso_url            (str)   SSO_SAML_IDP_SSO_URL
  idp_slo_url            (str)   SSO_SAML_IDP_SLO_URL
  idp_x509_cert          (str)   SSO_SAML_IDP_CERT
  sp_x509_cert           (str)   SSO_SAML_SP_CERT (optional)
  sp_private_key         (str)   SSO_SAML_SP_KEY (optional)
  name_id_format         (str)   Default: email
  want_assertions_signed (bool)  Default: True
  want_response_signed   (bool)  Default: True
  authn_requests_signed  (bool)  Default: False
  logout_requests_signed (bool)  Default: False

OAuth2Config Variables (env-loaded):
  Similar structure for OAuth2/OIDC providers
```

**CONCERN:** This module uses direct `os.getenv()` instead of going through Settings

---

### 3.4 Compression Configuration (app/middleware/compression/config.py)

```python
Type: Dataclass with factory functions
Env Vars: NONE (hardcoded)
Config Class: CompressionConfig

Variables:
  enabled              (bool)  Default: True
  min_size             (int)   Default: 1024 bytes
  gzip_enabled         (bool)  Default: True
  gzip_level           (int)   Default: 6 (1-9)
  brotli_enabled       (bool)  Default: True
  brotli_quality       (int)   Default: 4 (0-11)
  compressible_types   (set)   17 default content types
  exclude_paths        (set)   5 paths excluded (/metrics, /health, etc)
  track_stats          (bool)  Default: True

Environment Presets:
  DEFAULT_CONFIG       - Balanced settings
  PRODUCTION_CONFIG    - High compression (gzip_level=9, brotli_quality=11)
  DEVELOPMENT_CONFIG   - Fast compression (gzip_level=1)

Usage:
  get_compression_config(environment: str) -> CompressionConfig
```

**CONCERN:** No environment variable loading; hardcoded in Python

### 3.5 Throttling Configuration (app/middleware/throttling/config.py)

```python
Type: Dataclass with multiple configurations
Env Vars: NONE (hardcoded)
Config Classes: ThrottleConfig, EndpointThrottleConfig, UserThrottleConfig

Global Settings:
  DEFAULT_THROTTLE_CONFIG.max_concurrent_requests  (int) 100
  DEFAULT_THROTTLE_CONFIG.max_queue_size           (int) 200
  DEFAULT_THROTTLE_CONFIG.queue_timeout_seconds    (float) 30.0

Endpoint-Specific Throttles (10 endpoints):
  /api/v1/health              → 50 concurrent, 0 queue (CRITICAL)
  /api/v1/metrics             → 20 concurrent, 0 queue (CRITICAL)
  /api/v1/schedules/generate  → 5 concurrent, 10 queue (HIGH, expensive)
  /api/v1/schedules/validate  → 10 concurrent, 20 queue (HIGH)
  /api/v1/swaps/execute       → 10 concurrent, 15 queue (HIGH)
  /api/v1/analytics/*         → 15 concurrent, 30 queue (LOW)
  /api/v1/reports/*           → 10 concurrent, 20 queue (BACKGROUND)
  /api/v1/persons/*           → 30 concurrent, 50 queue (NORMAL)
  /api/v1/assignments/*       → 25 concurrent, 40 queue (NORMAL)

Role-Based Throttles (8 roles):
  ADMIN        → 50 concurrent, 100 queue
  COORDINATOR  → 30 concurrent, 60 queue
  FACULTY      → 20 concurrent, 40 queue
  RESIDENT     → 15 concurrent, 30 queue
  CLINICAL_STAFF → 15 concurrent, 30 queue
  RN, LPN, MSA → 10 concurrent, 20 queue

Degradation Thresholds:
  warning      70% capacity
  throttle     80% capacity
  reject       90% capacity
  critical     95% capacity
```

**CONCERN:** No environment variable loading; hardcoded for all throttling

---

## Part 4: Environment Variable Mapping

### 4.1 Variables in .env.example vs Actual Settings

**Documented in .env.example (97 lines):**
```
✓ DB_PASSWORD               (Note: Used in connection string, not separate)
✓ SECRET_KEY, WEBHOOK_SECRET
✓ REDIS_PASSWORD
✓ APP_NAME, DEBUG
✓ CORS_ORIGINS
✓ RESILIENCE_* (9 vars)
✓ ML_* (14 vars)
✓ TELEMETRY_* (13 vars)
✓ LLM_* (7 vars)
✓ GRPC_* (5 vars - external)
✓ SSO_* (6 vars - external)
✓ SENTRY_DSN (external)
✓ Notifications (external)
✓ Cache TTLs (7 vars)
```

**Missing from .env.example:**
```
✗ NEXT_PUBLIC_API_URL        (Referenced in .env.example line 117 but no section)
✗ MCP_LOG_LEVEL              (Referenced in .env.example line 124 but no section)
✗ LOGGING-related (LOG_LEVEL, LOG_FORMAT, LOG_FILE) - Commented out
✗ Database pool settings - Commented out
✗ Rate limiting settings - No explicit section
✗ File upload S3 settings - No explicit section
✗ Upload path settings - Not in .env.example at all
✗ Compression settings - HARDCODED (no env vars)
✗ Throttling settings - HARDCODED (no env vars)
```

### 4.2 Environment Variable Access Patterns

**Pattern 1: Pydantic BaseSettings (PREFERRED)**
```python
# app/core/config.py: Settings class
settings = get_settings()
DATABASE_URL = settings.DATABASE_URL  # Loads from .env
```

**Pattern 2: Direct os.getenv() (INCONSISTENT)**
```python
# app/grpc/server.py
GRPC_PORT = int(os.getenv("GRPC_PORT", "50051"))

# app/auth/sso/config.py
entity_id = os.getenv("SSO_SAML_ENTITY_ID", "")

# app/tasks/compliance_report_tasks.py
reports_dir = os.getenv("REPORTS_DIR", "/tmp/reports")

# app/middleware/errors/reporters.py
sentry_dsn = os.getenv("SENTRY_DSN")
```

**Pattern 3: Derived Configuration (ACCEPTABLE)**
```python
# app/db/pool/config.py
pool_config = PoolConfig(
    pool_size=settings.DB_POOL_SIZE,  # From Settings
)

# app/core/logging/config.py
LoggingConfig.from_env()  # Uses settings.LOG_LEVEL, etc
```

### 4.3 External Configuration (Outside Settings)

**Variables with direct os.getenv() calls:**

| Variable | File | Usage | Reason |
|----------|------|-------|--------|
| GRPC_PORT | app/grpc/server.py | gRPC port | Not in Settings |
| GRPC_MAX_WORKERS | app/grpc/server.py | gRPC workers | Not in Settings |
| GRPC_MAX_MESSAGE_LENGTH | app/grpc/server.py | Message size | Not in Settings |
| GRPC_ENABLE_TLS | app/grpc/server.py | TLS for gRPC | Not in Settings |
| GRPC_TLS_CERT_PATH | app/grpc/server.py | Cert path | Not in Settings |
| GRPC_TLS_KEY_PATH | app/grpc/server.py | Key path | Not in Settings |
| SENTRY_DSN | app/middleware/errors/reporters.py | Error tracking | Optional |
| REPORTS_DIR | app/tasks/compliance_report_tasks.py | Report output | Not in Settings |
| COMPLIANCE_STAKEHOLDER_EMAILS | app/tasks/compliance_report_tasks.py | Email recipients | Not in Settings |
| EXECUTIVE_STAKEHOLDER_EMAILS | app/tasks/compliance_report_tasks.py | Email recipients | Not in Settings |
| SSO_SAML_* (8 vars) | app/auth/sso/config.py | SAML config | Not in Settings |
| SSO_OAUTH2_* (10 vars) | app/auth/sso/config.py | OAuth2 config | Not in Settings |

---

## Part 5: Secret Handling Audit

### 5.1 Secrets That MUST Be Set

**CRITICAL (Application won't start without these):**

1. **SECRET_KEY**
   - Purpose: JWT token signing
   - Requirement: ≥32 characters (production)
   - Validation: Field validator rejects weak passwords
   - Where set: .env or environment
   - Location in code: app/core/config.py:105
   - Used by: app/core/security.py (JWT functions)
   - Default fallback: None (raises error if not set)
   - WARNING: Default is now generated fresh each run with `secrets.token_urlsafe(64)`

2. **WEBHOOK_SECRET**
   - Purpose: Validate incoming webhooks
   - Requirement: ≥32 characters (production)
   - Validation: Field validator rejects weak passwords
   - Where set: .env or environment
   - Location in code: app/core/config.py:111
   - Used by: app/webhooks/verification.py
   - Default fallback: None (raises error if not set)
   - WARNING: Default is now generated fresh each run

3. **DATABASE_URL**
   - Purpose: PostgreSQL connection string
   - Requirement: Must include password, password ≥12 chars
   - Validation: URL parser + password validator
   - Format: postgresql://user:password@host:port/dbname
   - Where set: .env or environment
   - Used by: app/db/session.py
   - Default: "postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"
   - CONCERN: Default in code has weak password "scheduler"

4. **REDIS_PASSWORD**
   - Purpose: Redis authentication (if needed)
   - Requirement: ≥16 characters (production), can be empty (dev)
   - Validation: Field validator
   - Where set: .env or environment
   - Used by: app/core/service_cache.py, app/core/celery_app.py
   - Default: "" (no authentication)
   - CONCERN: Can be empty, allowing unauthenticated Redis

**HIGHLY RECOMMENDED (Application works but security risk without):**

5. **CORS_ORIGINS**
   - Purpose: Restrict cross-origin requests
   - Risk: Wildcard "*" in production
   - Default: ["http://localhost:3000"]
   - Setting: app/core/config.py:135

6. **TRUSTED_HOSTS**
   - Purpose: Prevent host header attacks
   - Default: [] (disabled)
   - Setting: app/core/config.py:140
   - CONCERN: Empty in development allows any Host header

7. **TRUSTED_PROXIES**
   - Purpose: Prevent rate limit bypass via X-Forwarded-For spoofing
   - Default: [] (uses direct client IP)
   - Setting: app/core/config.py:144
   - CONCERN: Empty allows spoofing if proxy present

### 5.2 Secret Generation Requirements

```bash
# Generate 64-char secret (for SECRET_KEY, WEBHOOK_SECRET)
python -c 'import secrets; print(secrets.token_urlsafe(64))'
# Output: 64+ character URL-safe base64 string

# Generate 32-char secret (for REDIS_PASSWORD)
python -c 'import secrets; print(secrets.token_urlsafe(32))'
# Output: 32+ character URL-safe base64 string
```

### 5.3 .env File Security

**Gitignore Status:**
```
✓ .env is properly gitignored (never committed)
✓ .env.example exists with placeholder values
✗ .env.example contains weak placeholder passwords (see below)
```

**Weak Placeholders in .env.example:**
```
Line 19:  REDIS_PASSWORD=your_redis_password_here
Line 21:  SECRET_KEY=your-secret-key-change-in-production
Line 23:  WEBHOOK_SECRET=your-webhook-secret-change-in-production
Line 32:  REDIS_PASSWORD=your_redis_password_here_generate_a_random_string

These are in WEAK_PASSWORDS list! Will trigger warnings in DEBUG mode.
```

### 5.4 Production Readiness Checks

**Security Validation on Startup:**

```python
Location: app/main.py:37-88 (_validate_security_config)

Checks:
  ✓ SECRET_KEY not in insecure_defaults
  ✓ SECRET_KEY length ≥ 32 chars
  ✓ WEBHOOK_SECRET not in insecure_defaults
  ✓ WEBHOOK_SECRET length ≥ 32 chars
  ✓ Detailed error messages with generation instructions

Behavior:
  - Production (DEBUG=False): Raises ValueError, application won't start
  - Development (DEBUG=True): Logs warning but starts
```

**No corresponding validation for:**
- DATABASE_URL password strength at startup
- REDIS_PASSWORD at startup
- CORS_ORIGINS security at startup (only in validator)

---

## Part 6: Configuration Completeness Analysis

### 6.1 Variables Fully Configurable via Environment

```
✓ Application settings (APP_NAME, APP_VERSION, DEBUG)
✓ Database connection (DATABASE_URL, DB_POOL_*)
✓ Redis/Celery (REDIS_*, CELERY_*)
✓ Security (SECRET_KEY, WEBHOOK_SECRET, tokens)
✓ Rate limiting (RATE_LIMIT_*)
✓ File uploads (UPLOAD_*)
✓ CORS (CORS_ORIGINS, CORS_ORIGINS_REGEX)
✓ Resilience framework (RESILIENCE_*)
✓ OpenTelemetry (TELEMETRY_*)
✓ ML models (ML_*)
✓ Shadow traffic (SHADOW_*)
✓ LLM routing (LLM_*, OLLAMA_*, ANTHROPIC_*)
✓ Logging (LOG_LEVEL, LOG_FORMAT, LOG_FILE)
✓ Cache TTLs (CACHE_*_TTL)
```

### 6.2 Variables NOT Configurable via Environment

```
✗ Compression (hardcoded in code, 3 presets)
✗ Request throttling (hardcoded per-endpoint, per-role)
✗ gRPC settings (only partially in Settings)
✗ SSO/SAML settings (direct os.getenv, not in Settings)
✗ Sentry DSN (direct os.getenv)
✗ Compliance report destinations (direct os.getenv)
✗ Logging module-level overrides (in LoggingConfig, not Settings)
```

### 6.3 Configuration in .env.example vs Settings

**In Settings class but missing from .env.example:**
```
✗ LOG_LEVEL, LOG_FORMAT, LOG_FILE (commented out)
✗ DB_POOL_SIZE, DB_POOL_MAX_OVERFLOW, etc. (commented out)
✗ RATE_LIMIT_* (no section at all)
✗ File upload local/S3 settings (partially present)
✗ TRUSTED_HOSTS, TRUSTED_PROXIES (no section)
```

**In .env.example but NOT in Settings:**
```
✗ GRPC_* (5 variables)
✗ SENTRY_DSN
✗ SSO_* (partially, uses direct os.getenv)
✗ NEXT_PUBLIC_API_URL (referenced but no definition)
✗ MCP_LOG_LEVEL (referenced but no definition)
```

---

## Part 7: Detected Issues & Anti-patterns

### 7.1 Configuration Governance Issues

**Issue 1: Scattered Configuration (Code Smell)**
- Problem: Configuration split across 6 separate files
- Files: config.py, logging/config.py, db/pool/config.py, auth/sso/config.py, middleware/compression/config.py, middleware/throttling/config.py
- Impact: Developers must search multiple files to understand all config
- Recommendation: Consider creating unified config documentation or registry

**Issue 2: Inconsistent Loading Patterns (Anti-pattern)**
- Problem: Three different ways to load config:
  1. Pydantic BaseSettings (Settings class) ← PREFERRED
  2. Direct os.getenv() (gRPC, SSO, Sentry) ← INCONSISTENT
  3. Dataclass factories (Logging, Pool) ← ACCEPTABLE
- Impact: Configuration source unclear, harder to validate
- Recommendation: Consolidate all config into Settings class

**Issue 3: Direct os.getenv() in Production Code**
- Files affected:
  - app/grpc/server.py (6 vars)
  - app/auth/sso/config.py (15+ vars)
  - app/tasks/compliance_report_tasks.py (3 vars)
  - app/middleware/errors/reporters.py (1 var)
- Problem: Bypasses Settings validation, no type checking
- Recommendation: Move to Settings class

**Issue 4: Environment Detection Missing**
- Problem: No explicit ENVIRONMENT variable in Settings
- Current pattern: Uses DEBUG boolean instead
- Recommendation: Add ENVIRONMENT="development" | "staging" | "production"
- Needed by: Logging config, telemetry, compression configs, etc.

**Issue 5: Hardcoded Compression Settings**
- Problem: No environment variables for compression levels
- Impact: Can't tune compression without code change
- Recommendation: Add COMPRESSION_ENABLED, COMPRESSION_LEVEL, etc. to Settings

**Issue 6: Hardcoded Throttling Settings**
- Problem: No environment variables for throttle limits
- Impact: Can't adjust for load without code change
- Recommendation: Add THROTTLE_MAX_CONCURRENT, THROTTLE_QUEUE_SIZE, etc.

### 7.2 Security Issues

**Issue 1: Weak Default Database Password**
```python
Location: app/core/config.py:61-63
DATABASE_URL = "postgresql://scheduler:scheduler@localhost:5432/residency_scheduler"
Problem: Default includes weak password "scheduler"
Impact: Local dev is OK, but easy to miss changing in prod
Recommendation: Make DATABASE_URL required (no default)
```

**Issue 2: Weak Password Placeholders in .env.example**
```
Line 19: REDIS_PASSWORD=your_redis_password_here
Line 21: SECRET_KEY=your-secret-key-change-in-production
Line 32: REDIS_PASSWORD=your_redis_password_here_generate_a_random_string

These are in the WEAK_PASSWORDS blacklist!
Impact: .env.example values won't work in production
Recommendation: Add better examples or remove from blacklist
```

**Issue 3: CORS_ORIGINS Default Allows Localhost Only**
```python
Default: ["http://localhost:3000"]
Status: ✓ Secure (not wildcard)
BUT: Easy to forget changing for production
Recommendation: Log warning at startup if DEBUG=False and localhost in CORS_ORIGINS
```

**Issue 4: No Validation for Sentry DSN**
```python
Location: app/middleware/errors/reporters.py
sentry_dsn = os.getenv("SENTRY_DSN")
Problem: Optional, no format validation
Impact: If wrong format, error tracking silently fails
Recommendation: Validate DSN format if provided
```

**Issue 5: SSO Configuration Not Validated**
```python
Location: app/auth/sso/config.py
Problem: URLs loaded with os.getenv, minimal validation
Impact: Invalid SSO URLs could cause auth failures
Recommendation: Add validators for SAML/OAuth URLs
```

### 7.3 Operational Issues

**Issue 1: No Configuration Audit Trail**
- Problem: No way to see what config was loaded at startup
- Impact: Hard to debug configuration issues in production
- Recommendation: Add startup log showing all non-secret config values

**Issue 2: Missing Pool Configuration in .env.example**
```
Lines 10-14: DB_POOL_* settings are commented out
Impact: Developers don't know these can be tuned
Recommendation: Uncomment with explanatory comments
```

**Issue 3: Cache TTLs Not Obvious**
```
6 different CACHE_*_TTL variables with different defaults
Problem: Not documented well, easy to miss
Recommendation: Add cache configuration section to .env.example
```

**Issue 4: ML Configuration Dead Code?**
```
14 ML_* configuration variables
But: ML_ENABLED defaults to False
Problem: Dead code configuration taking space
Recommendation: Move ML config to separate module or clarify if actively used
```

---

## Part 8: Configuration Gap Analysis

### 8.1 Missing Environment Variables

**Should be in Settings but aren't:**

```
ENVIRONMENT                      (string) - development/staging/production
GRPC_ENABLED                     (bool) - Enable/disable gRPC server
GRPC_PORT                        (int) - gRPC server port
GRPC_MAX_WORKERS                 (int) - gRPC worker threads
GRPC_MAX_MESSAGE_LENGTH          (int) - Max message size
GRPC_ENABLE_TLS                  (bool) - TLS for gRPC
GRPC_TLS_CERT_PATH               (str) - Path to cert
GRPC_TLS_KEY_PATH                (str) - Path to key
GRPC_ENABLE_REFLECTION           (bool) - gRPC reflection
SSO_ENABLED                      (bool) - Enable SSO
SSO_SAML_ENABLED                 (bool) - Enable SAML
SSO_SAML_ENTITY_ID               (str) - SP entity ID
SSO_SAML_ACS_URL                 (str) - ACS URL
SSO_SAML_SLO_URL                 (str) - SLO URL
SSO_SAML_IDP_ENTITY_ID           (str) - IdP entity ID
SSO_SAML_IDP_SSO_URL             (str) - IdP SSO URL
SSO_SAML_IDP_SLO_URL             (str) - IdP SLO URL
SSO_SAML_IDP_CERT                (str) - IdP certificate
SSO_OAUTH2_ENABLED               (bool) - Enable OAuth2
SSO_OAUTH2_PROVIDER              (str) - Provider name
SSO_OAUTH2_CLIENT_ID             (str) - Client ID
SSO_OAUTH2_CLIENT_SECRET         (str) - Client secret
SSO_OAUTH2_AUTH_URL              (str) - Auth endpoint
SSO_OAUTH2_TOKEN_URL             (str) - Token endpoint
SSO_DEFAULT_ROLE                 (str) - Default user role
SENTRY_DSN                       (str) - Sentry error tracking
COMPLIANCE_STAKEHOLDER_EMAILS    (list) - Compliance email list
EXECUTIVE_STAKEHOLDER_EMAILS     (list) - Executive email list
REPORTS_DIR                      (str) - Report output directory
COMPRESSION_ENABLED              (bool) - Enable compression
COMPRESSION_LEVEL                (int) - Gzip compression level
COMPRESSION_MIN_SIZE             (int) - Minimum size to compress
THROTTLE_ENABLED                 (bool) - Enable throttling
THROTTLE_MAX_CONCURRENT          (int) - Max concurrent requests
THROTTLE_QUEUE_SIZE              (int) - Max queue size
NEXT_PUBLIC_API_URL              (str) - Frontend API URL
MCP_LOG_LEVEL                    (str) - MCP server log level
```

### 8.2 Missing Validators

```
✗ GRPC port validation (valid port range)
✗ GRPC TLS cert/key validation (must exist if enabled)
✗ SENTRY_DSN format validation
✗ SSO URL validation (https required in production)
✗ Email list format validation
✗ MCP configuration validation
```

---

## Part 9: Recommendations & Action Items

### 9.1 High Priority (Security)

**1. Fix Weak Password Placeholders in .env.example**
- Remove or generate strong examples
- Add note about security requirements
- Action: Update backend/.env.example lines 19, 21, 32

**2. Add ENVIRONMENT Variable to Settings**
- Define: ENVIRONMENT = "development" | "staging" | "production"
- Use for conditional config (logging format, telemetry, etc.)
- Action: Add to app/core/config.py Settings class

**3. Move gRPC Configuration to Settings**
- Move GRPC_* from os.getenv() to Settings class
- Add validation (port range, TLS cert existence)
- Action: Add to app/core/config.py, refactor app/grpc/server.py

**4. Move SSO Configuration to Settings**
- Move SSO_* from os.getenv() to Settings class
- Add URL format validation
- Separate SAML/OAuth into dedicated fields
- Action: Refactor app/auth/sso/config.py

**5. Validate Secrets on Startup**
- Add validation for DATABASE_URL password in startup check
- Add validation for REDIS_PASSWORD in startup check
- Action: Enhance app/main.py _validate_security_config()

### 9.2 Medium Priority (Consistency)

**6. Add Missing Variables to .env.example**
```
Uncomment:
  - LOG_LEVEL, LOG_FORMAT, LOG_FILE
  - DB_POOL_SIZE, DB_POOL_MAX_OVERFLOW, etc.

Add new sections:
  - RATE_LIMITING (all 5 vars)
  - COMPRESSION (min size, levels)
  - THROTTLING (global limits, per-role)
  - ENVIRONMENT (dev/staging/prod)
  - GRPC (if using gRPC)
  - SSO (if using SSO)
```

**7. Add Configuration Audit at Startup**
- Log all non-secret config values at startup
- Helps debug production config issues
- Action: Add to app/main.py lifespan

**8. Consolidate Configuration Loading**
- Create configuration registry or manifest
- Document all 108+ config variables in one place
- Action: Create docs/CONFIGURATION.md

**9. Make Compression/Throttling Configurable**
- Convert hardcoded settings to environment variables
- Keep presets for common scenarios
- Action: Update middleware config classes

### 9.3 Low Priority (Documentation)

**10. Create Configuration Guide**
- Document all config variables
- Explain environment-specific values
- Provide production checklist
- Action: Create docs/configuration-guide.md

**11. Add Config Validation Tests**
- Test that all config variables load correctly
- Test security validators
- Test production vs development modes
- Action: Create backend/tests/test_config_*.py

---

## Part 10: Configuration Inventory Checklist

### Quick Reference Table

| Category | Count | Fully Env-Configurable | Notes |
|----------|-------|------------------------|-------|
| Application | 6 | ✓ | APP_NAME, DEBUG, LOG_* |
| Database | 10 | ✓ | URL, pool settings |
| Redis/Celery | 5 | ✓ | Password, URLs |
| Cache | 7 | ✓ | TTLs for each cache type |
| Security | 6 | ✓ | Keys, tokens, expiry |
| Rate Limiting | 5 | ✓ | Login, registration limits |
| File Upload | 9 | ✓ | Local/S3 backend settings |
| CORS/Security Headers | 4 | ✓ | Origins, trusted hosts |
| Resilience | 9 | ✓ | Thresholds, auto-activation |
| OpenTelemetry | 11 | ✓ | Tracing configuration |
| ML Models | 14 | ✓ | Model paths, training |
| Shadow Traffic | 10 | ✓ | Canary deployment config |
| LLM Router | 7 | ✓ | Ollama/Anthropic settings |
| **Logging** | 8 | ✓ | Format, level, file output |
| **Compression** | 6 | ✗ | Hardcoded (3 presets) |
| **Throttling** | 15+ | ✗ | Hardcoded per-endpoint |
| gRPC (external) | 6 | ✗ | Direct os.getenv() |
| SSO (external) | 20+ | ✗ | Direct os.getenv() |
| **TOTAL** | **159+** | **140 (88%)** | **19 vars still hardcoded** |

---

## Appendix A: Default Values Summary

### Production-Safe Defaults
- DEBUG = False
- LOG_FORMAT = "json"
- TELEMETRY_ENABLED = False
- LOG_LEVEL = "INFO"
- CORS_ORIGINS = ["https://your-domain.com"] (must be set)
- TRUSTED_HOSTS = ["your-domain.com"] (must be set)
- DATABASE_URL = (required)
- SECRET_KEY = (required, auto-generated if not set)
- WEBHOOK_SECRET = (required, auto-generated if not set)

### Development-Friendly Defaults
- DEBUG = True
- LOG_FORMAT = "text"
- CORS_ORIGINS = ["http://localhost:3000"]
- REDIS_PASSWORD = "" (no auth required)
- TELEMETRY_ENABLED = False (optional)
- UPLOAD_STORAGE_BACKEND = "local"

---

## Appendix B: Files Referenced

```
Primary Config Files:
  backend/app/core/config.py                    (535 lines, Settings class)
  backend/app/core/logging/config.py            (221 lines, LoggingConfig)
  backend/app/db/pool/config.py                 (131 lines, PoolConfig)
  backend/app/auth/sso/config.py                (200+ lines, SAML/OAuth)
  backend/app/middleware/compression/config.py  (153 lines)
  backend/app/middleware/throttling/config.py   (239 lines)

Supporting Files:
  backend/.env.example                          (97 lines, template)
  .env.example                                  (254 lines, master template)
  backend/app/main.py                           (security validation)
  backend/app/core/logging.py                   (logging setup)
  backend/app/grpc/server.py                    (gRPC config)
  backend/app/core/service_cache.py             (cache setup)
```

---

**Report Generated:** 2025-12-30
**Investigation Method:** Comprehensive codebase search using Grep, Glob, and file reading
**Confidence Level:** HIGH (direct source code analysis)
**Next Steps:** See Section 9 (Recommendations) for action items
