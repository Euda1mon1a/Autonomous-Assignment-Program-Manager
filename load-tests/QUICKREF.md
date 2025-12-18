***REMOVED*** Rate Limiting Attack Tests - Quick Reference

***REMOVED******REMOVED*** Files Created

***REMOVED******REMOVED******REMOVED*** 1. /home/user/Autonomous-Assignment-Program-Manager/load-tests/utils/auth.js
Authentication utilities module providing:
- Login helpers (form-data and JSON)
- Token management functions
- Request validation helpers
- JWT token utilities

***REMOVED******REMOVED******REMOVED*** 2. /home/user/Autonomous-Assignment-Program-Manager/load-tests/scenarios/rate-limit-attack.js
Rate limiting attack simulation with 4 scenarios:
- **Brute Force Login**: Tests login rate limit (5/min)
- **API Flooding**: Tests API rate limit (30 req/s)
- **Schedule Gen Spam**: Tests schedule generation limit (1/10s)
- **Distributed Attack**: Tests overall system resilience

**Duration**: ~100 seconds
**Custom Metrics**: rate_limit_triggers, blocked_requests, requests_until_limit, etc.

***REMOVED******REMOVED******REMOVED*** 3. /home/user/Autonomous-Assignment-Program-Manager/load-tests/scenarios/auth-security.js
Authentication security tests with 5 scenarios:
- **Token Validation Load**: 100 concurrent users with valid tokens
- **Invalid Token Rejection**: Tests various invalid token formats
- **Token Expiry Handling**: Tests token lifecycle
- **Concurrent Authentication**: 100 login attempts/second
- **Session Management**: Realistic user session simulation

**Duration**: ~11 minutes
**Custom Metrics**: token_validation_time, invalid_token_rejections, etc.

***REMOVED******REMOVED******REMOVED*** 4. /home/user/Autonomous-Assignment-Program-Manager/load-tests/README.md
Comprehensive documentation including:
- Installation instructions
- Usage examples
- Environment variable configuration
- Results interpretation guide
- Troubleshooting tips
- CI/CD integration examples

***REMOVED******REMOVED******REMOVED*** 5. /home/user/Autonomous-Assignment-Program-Manager/load-tests/run-load-tests.sh
Test runner script with options:
- `--rate-limit-only`: Run only rate limit tests
- `--auth-only`: Run only auth security tests
- `--base-url URL`: Override base URL
- `--results-dir DIR`: Custom results directory
- `--skip-wait`: Skip cooldown between tests

***REMOVED******REMOVED******REMOVED*** 6. /home/user/Autonomous-Assignment-Program-Manager/load-tests/preflight-check.sh
Pre-flight validation script that checks:
- k6 installation
- Docker daemon status
- Application containers running
- Backend API accessibility
- Redis connection
- PostgreSQL database
- Authentication endpoint
- Test user existence
- Results directory

***REMOVED******REMOVED*** Quick Start

1. **Run pre-flight check:**
   ```bash
   cd /home/user/Autonomous-Assignment-Program-Manager/load-tests
   ./preflight-check.sh
   ```

2. **Run all tests:**
   ```bash
   ./run-load-tests.sh
   ```

3. **Run individual test:**
   ```bash
   k6 run scenarios/rate-limit-attack.js
   k6 run scenarios/auth-security.js
   ```

***REMOVED******REMOVED*** Expected Rate Limits

From nginx.conf and backend configuration:

| Endpoint | Limit | Window |
|----------|-------|--------|
| Login | 5 requests | per minute |
| API | 30 requests | per second |
| Schedule Generation | 1 request | per 10 seconds |
| General | 10 requests | per second |

***REMOVED******REMOVED*** Test Thresholds

***REMOVED******REMOVED******REMOVED*** Rate Limit Attack Test

```javascript
thresholds: {
    'rate_limit_triggers': ['count>0'],           // Must trigger
    'requests_until_limit': ['p95<15'],           // Trigger within 15 req
    'rate_limit_response_time': ['p95<50'],       // Fast rejection <50ms
    'server_errors': ['count==0'],                // No 5xx errors
    'legitimate_after_cooldown': ['count>0'],     // Recovery works
}
```

***REMOVED******REMOVED******REMOVED*** Auth Security Test

```javascript
thresholds: {
    'token_validation_time': ['p95<200', 'p99<500'],           // Fast validation
    'invalid_token_rejection_time': ['p95<100', 'p99<200'],    // Faster rejection
    'authentication_errors': ['count==0'],                      // No auth errors
    'http_req_duration{scenario:token_validation_load}': ['p95<500'],
    'http_req_duration{scenario:concurrent_auth}': ['p95<1000'],
}
```

***REMOVED******REMOVED*** Custom Metrics

***REMOVED******REMOVED******REMOVED*** Rate Limit Attack

- `rate_limit_triggers`: Times rate limiting was triggered
- `blocked_requests`: Requests blocked by rate limiting
- `legitimate_after_cooldown`: Successful requests after cooldown
- `rate_limit_response_time`: Time to return 429
- `server_errors`: Count of 5xx responses
- `requests_until_limit`: Number of requests until limit triggered

***REMOVED******REMOVED******REMOVED*** Auth Security

- `valid_token_requests`: Requests with valid tokens
- `invalid_token_requests`: Requests with invalid tokens
- `invalid_token_rejections`: Invalid tokens rejected
- `token_validation_time`: Valid token validation time
- `invalid_token_rejection_time`: Invalid token rejection time
- `authentication_errors`: Auth system errors
- `concurrent_login_success`: Successful concurrent logins
- `concurrent_login_failures`: Failed concurrent logins

***REMOVED******REMOVED*** Environment Variables

```bash
***REMOVED*** Base configuration
export K6_BASE_URL="http://localhost:8000"
export TEST_USERNAME="loadtest@example.com"
export TEST_PASSWORD="LoadTest123!@***REMOVED***"

***REMOVED*** Rate limit overrides
export LOGIN_RATE_LIMIT=5
export LOGIN_WINDOW_SECONDS=60
export API_RATE_LIMIT=30
export API_WINDOW_SECONDS=1
export SCHEDULE_GEN_RATE_LIMIT=1
export SCHEDULE_GEN_WINDOW_SECONDS=10
```

***REMOVED******REMOVED*** Interpreting Results

***REMOVED******REMOVED******REMOVED*** Success Indicators ✓

- Rate limiting triggers as expected
- 429 responses returned quickly (<50ms)
- No server errors (5xx)
- Legitimate requests succeed after cooldown
- Invalid tokens rejected consistently
- Token validation is fast (<200ms p95)

***REMOVED******REMOVED******REMOVED*** Failure Indicators ✗

- Rate limiting never triggers
- Server errors during rate limiting
- Slow rejection times (>100ms)
- Legitimate requests fail after cooldown
- Invalid tokens accepted
- Slow token validation (>500ms)

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** "Connection refused"
```bash
***REMOVED*** Check if app is running
docker-compose ps
curl http://localhost:8000/health
```

***REMOVED******REMOVED******REMOVED*** "Authentication failures"
```bash
***REMOVED*** Verify test user exists
docker-compose exec db psql -U scheduler -d residency_scheduler -c \
  "SELECT email, role FROM persons WHERE email = 'loadtest@example.com';"
```

***REMOVED******REMOVED******REMOVED*** "Rate limiting not triggering"
```bash
***REMOVED*** Check nginx config
docker-compose exec nginx cat /etc/nginx/nginx.conf | grep limit_req_zone

***REMOVED*** Check Redis
docker-compose exec redis redis-cli PING
docker-compose exec redis redis-cli KEYS "rate_limit:*"
```

***REMOVED******REMOVED*** Files Reference

```
load-tests/
├── utils/
│   └── auth.js                    ***REMOVED*** Auth utilities (11KB)
├── scenarios/
│   ├── rate-limit-attack.js       ***REMOVED*** Rate limit tests (16KB)
│   └── auth-security.js           ***REMOVED*** Auth security tests (18KB)
├── results/                       ***REMOVED*** Test results output
├── README.md                      ***REMOVED*** Full documentation
├── run-load-tests.sh              ***REMOVED*** Test runner script
├── preflight-check.sh             ***REMOVED*** Pre-flight validation
└── QUICKREF.md                    ***REMOVED*** This file
```

***REMOVED******REMOVED*** Next Steps

1. ✅ Run preflight check
2. ✅ Create test user if needed
3. ✅ Run tests
4. ✅ Review results
5. ✅ Tune rate limits if needed
6. ✅ Integrate into CI/CD

For detailed documentation, see: README.md
