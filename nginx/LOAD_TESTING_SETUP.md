# Load Testing Setup Guide

This guide explains how to configure and use the nginx load testing infrastructure for the Residency Scheduler application.

## Overview

The load testing configuration provides:

- **Enhanced connection pooling**: 100 keepalive connections with 10,000 requests/connection
- **Relaxed rate limits**: Up to 100 req/s (vs 30 req/s in production)
- **Security controls**: IP whitelisting + secret key authentication
- **Detailed metrics**: JSON logging with timing data for performance analysis
- **Dedicated endpoints**: `/api/loadtest/*` routes with optimized settings

## Quick Start

### 1. Generate Load Test Secret Key

```bash
# Generate a secure random key (32+ characters)
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

**Output example:**
```
9KvXH7JZrP4mQwN3TyB8DxC6FgL2AhW5EsRtYuI1OpVz
```

### 2. Configure the Secret Key

Edit `/home/user/Autonomous-Assignment-Program-Manager/nginx/conf.d/load-testing.conf`:

```nginx
map $http_x_load_test_key $load_test_mode {
    default 0;
    # Replace with your generated key
    "9KvXH7JZrP4mQwN3TyB8DxC6FgL2AhW5EsRtYuI1OpVz" 1;
}
```

**Security note:** Store this key securely. Treat it like a password.

### 3. Configure IP Whitelist (Optional)

If running load tests from external CI/CD servers, add their IPs to `load-testing.conf`:

```nginx
geo $load_test_whitelist {
    default 0;

    # Default whitelisted networks (already configured)
    127.0.0.1/32 1;        # Localhost
    ::1/128 1;             # IPv6 localhost
    10.0.0.0/8 1;          # Private network
    172.16.0.0/12 1;       # Docker networks
    192.168.0.0/16 1;      # Local network

    # Add your CI/CD servers here:
    203.0.113.0/24 1;      # Example: Jenkins server subnet
    198.51.100.50/32 1;    # Example: Specific load test runner
}
```

### 4. Enable Load Test Locations

Edit `/home/user/Autonomous-Assignment-Program-Manager/nginx/conf.d/default.conf`:

Add this line inside the `server` block (around line 50, after the logging configuration):

```nginx
server {
    listen 443 ssl http2;
    # ... other configuration ...

    access_log /var/log/nginx/residency-scheduler.access.log json_combined;
    error_log /var/log/nginx/residency-scheduler.error.log warn;

    # Add this line:
    include /etc/nginx/snippets/loadtest-locations.conf;

    # ... rest of server block ...
}
```

### 5. Test Configuration Syntax

```bash
# If using Docker
docker compose exec nginx nginx -t

# Or directly if nginx is installed
nginx -t
```

**Expected output:**
```
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 6. Reload Nginx

```bash
# Docker
docker compose exec nginx nginx -s reload

# Or restart the container
docker compose restart nginx
```

## Usage Examples

### Basic API Request with Load Test Key

```bash
curl -H "X-Load-Test-Key: YOUR_SECRET_KEY_HERE" \
     http://localhost/api/loadtest/persons
```

### Load Test with K6

Create `loadtest.js`:

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

// Load test configuration
export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 50 },   // Ramp to 50 users
    { duration: '2m', target: 100 },  // Steady at 100 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],   // Error rate < 1%
  },
};

const BASE_URL = 'http://localhost';
const LOAD_TEST_KEY = __ENV.LOAD_TEST_KEY || 'YOUR_SECRET_KEY_HERE';

export default function() {
  const params = {
    headers: {
      'X-Load-Test-Key': LOAD_TEST_KEY,
      'Content-Type': 'application/json',
    },
  };

  // Test various endpoints
  const endpoints = [
    '/api/loadtest/persons',
    '/api/loadtest/rotations',
    '/api/loadtest/assignments',
  ];

  endpoints.forEach(endpoint => {
    const res = http.get(`${BASE_URL}${endpoint}`, params);

    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
    });
  });

  sleep(1);
}
```

Run the test:

```bash
# Set the load test key as environment variable
export LOAD_TEST_KEY="YOUR_SECRET_KEY_HERE"

# Run K6
k6 run loadtest.js

# Or with Docker
docker run --rm -i --network=host -e LOAD_TEST_KEY=$LOAD_TEST_KEY \
  grafana/k6 run - <loadtest.js
```

### Load Test with Apache Bench (ab)

```bash
# 1000 requests, 10 concurrent connections
ab -n 1000 -c 10 \
   -H "X-Load-Test-Key: YOUR_SECRET_KEY_HERE" \
   http://localhost/api/loadtest/persons
```

### Load Test with Locust

Create `locustfile.py`:

```python
from locust import HttpUser, task, between
import os

class ResidencySchedulerUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Set load test headers"""
        self.load_test_key = os.getenv('LOAD_TEST_KEY', 'YOUR_SECRET_KEY_HERE')
        self.client.headers.update({
            'X-Load-Test-Key': self.load_test_key
        })

    @task(3)
    def list_persons(self):
        """Test persons endpoint (weight: 3)"""
        self.client.get("/api/loadtest/persons")

    @task(2)
    def list_rotations(self):
        """Test rotations endpoint (weight: 2)"""
        self.client.get("/api/loadtest/rotations")

    @task(1)
    def list_assignments(self):
        """Test assignments endpoint (weight: 1)"""
        self.client.get("/api/loadtest/assignments")

    @task(1)
    def get_metrics(self):
        """Check metrics during load test"""
        self.client.get("/api/loadtest/metrics")
```

Run Locust:

```bash
# Set environment variable
export LOAD_TEST_KEY="YOUR_SECRET_KEY_HERE"

# Start Locust web UI
locust -f locustfile.py --host=http://localhost

# Or headless mode
locust -f locustfile.py --host=http://localhost \
       --users 100 --spawn-rate 10 --run-time 5m --headless
```

### Schedule Generation Load Test

**Warning:** Schedule generation is resource-intensive. Start with low concurrency.

```bash
# Test with curl
curl -X POST \
     -H "X-Load-Test-Key: YOUR_SECRET_KEY_HERE" \
     -H "Content-Type: application/json" \
     -d '{"start_date":"2025-01-01","end_date":"2025-12-31"}' \
     http://localhost/api/loadtest/schedule/generate

# K6 script for schedule generation
export default function() {
  const params = {
    headers: {
      'X-Load-Test-Key': __ENV.LOAD_TEST_KEY,
      'Content-Type': 'application/json',
    },
  };

  const payload = JSON.stringify({
    start_date: '2025-01-01',
    end_date: '2025-12-31',
  });

  http.post('http://localhost/api/loadtest/schedule/generate', payload, params);

  sleep(60); // Wait 60 seconds between schedule generations
}
```

## Monitoring During Load Tests

### View Real-time Logs

```bash
# Load test specific logs (JSON format)
tail -f /var/log/nginx/loadtest.log

# Parse JSON for readability
tail -f /var/log/nginx/loadtest.log | jq '.'

# Filter slow requests (>1 second)
tail -f /var/log/nginx/loadtest.log | jq 'select(.request_time > "1")'
```

### Check Nginx Status

```bash
curl http://localhost/nginx_status
```

**Output:**
```
Active connections: 42
server accepts handled requests
 1234 1234 5678
Reading: 0 Writing: 4 Waiting: 38
```

### Monitor Backend Metrics

```bash
# Prometheus metrics from backend
curl http://localhost/api/loadtest/metrics

# Or with Docker
docker compose exec nginx curl backend:8000/metrics
```

### Monitor System Resources

```bash
# CPU and memory usage
docker stats

# Detailed container stats
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

## Rate Limit Comparison

| Endpoint Type | Normal Rate | Load Test Rate | Multiplier |
|---------------|-------------|----------------|------------|
| General pages | 10 req/s | 50 req/s | 5x |
| API endpoints | 30 req/s | 100 req/s | 3.3x |
| Schedule generation | 1 req/10s | 10 req/min | 100x |
| Login/auth | 5 req/min | N/A (not load tested) | - |

## Troubleshooting

### 403 Forbidden Error

**Problem:**
```json
{"error":"Load testing not allowed from this IP"}
```

**Solution:**
1. Check your IP: `curl ifconfig.me`
2. Add your IP to the `geo $load_test_whitelist` block in `load-testing.conf`
3. Reload nginx: `docker compose exec nginx nginx -s reload`

**Problem:**
```json
{"error":"Valid X-Load-Test-Key header required"}
```

**Solution:**
- Ensure you're sending the `X-Load-Test-Key` header with the correct value
- Verify the key matches the one in `load-testing.conf` (line 30)

### Rate Limiting During Load Test

If you're still hitting rate limits during load testing:

1. **Verify you're using load test endpoints**:
   - ✓ `/api/loadtest/persons` (relaxed limits)
   - ✗ `/api/persons` (normal limits)

2. **Check burst settings**: The burst allows temporary spikes. Increase if needed in `loadtest-locations.conf`:
   ```nginx
   limit_req zone=loadtest_api burst=500 nodelay;  # Increased from 200
   ```

3. **Monitor active connections**:
   ```bash
   watch -n 1 'curl -s http://localhost/nginx_status'
   ```

### Connection Pooling Not Working

**Symptoms:** High connection overhead, slow requests

**Check:**
1. Verify HTTP/1.1 is used (required for keepalive):
   ```bash
   curl -v -H "X-Load-Test-Key: YOUR_KEY" http://localhost/api/loadtest/persons 2>&1 | grep "HTTP"
   ```

2. Check if connections are being reused:
   ```bash
   # Monitor connection count
   netstat -an | grep :8000 | wc -l
   ```

3. Ensure load test tool supports connection reuse (K6, Locust do by default)

### Timeout Errors

**Problem:** 504 Gateway Timeout on schedule generation

**Solution:** Increase timeouts in `loadtest-locations.conf`:
```nginx
location /api/loadtest/schedule/generate {
    # Increase from 600s (10 min) to 1200s (20 min)
    proxy_send_timeout 1200s;
    proxy_read_timeout 1200s;

    # ... rest of config
}
```

## Security Best Practices

### ✅ DO

- **Use strong secrets**: Generate with `secrets.token_urlsafe(32)` or longer
- **Rotate keys**: Change the load test key periodically (quarterly)
- **Store securely**: Keep keys in environment variables or secret managers
- **Whitelist IPs**: Only allow known, trusted networks
- **Monitor logs**: Watch for unauthorized access attempts
- **Test in staging**: Run load tests in non-production environments first
- **Disable after use**: Comment out the include line when not actively load testing

### ❌ DON'T

- **Expose publicly**: Never allow load test endpoints on public internet
- **Use default keys**: Always replace `YOUR_LOAD_TEST_SECRET_KEY`
- **Commit secrets**: Don't check keys into version control
- **Skip monitoring**: Always monitor during load tests
- **Overload production**: Use realistic load test scenarios
- **Ignore errors**: Investigate and fix issues found during load testing

## Cleanup After Load Testing

### Disable Load Test Endpoints (Recommended)

If you're not actively running load tests, disable the endpoints:

1. **Comment out the include** in `conf.d/default.conf`:
   ```nginx
   # include /etc/nginx/snippets/loadtest-locations.conf;
   ```

2. **Reload nginx**:
   ```bash
   docker compose exec nginx nginx -s reload
   ```

### Archive Load Test Logs

```bash
# Create archive directory
mkdir -p /var/log/nginx/loadtest-archive

# Move old logs
mv /var/log/nginx/loadtest.log \
   /var/log/nginx/loadtest-archive/loadtest-$(date +%Y%m%d).log

# Compress
gzip /var/log/nginx/loadtest-archive/loadtest-*.log
```

## Advanced Configuration

### Multiple Load Test Environments

Support different keys for different environments:

```nginx
map $http_x_load_test_key $load_test_mode {
    default 0;
    "STAGING_LOAD_TEST_KEY_12345" 1;
    "CI_LOAD_TEST_KEY_67890" 1;
    "DEV_LOAD_TEST_KEY_ABCDE" 1;
}
```

### Custom Rate Limits Per Team

```nginx
# Define team-specific zones
limit_req_zone $http_x_team_id zone=team_alpha:10m rate=200r/s;
limit_req_zone $http_x_team_id zone=team_beta:10m rate=100r/s;

# Use in location blocks
location /api/loadtest/ {
    # Apply appropriate zone based on team
    limit_req zone=team_alpha burst=300 nodelay;
    # ... rest of config
}
```

### Gradual Rate Limit Increase

For gradual ramp-up scenarios:

```nginx
# Time-based rate limiting (slower during business hours)
map $hour $loadtest_rate_zone {
    default loadtest_api;           # 100 req/s
    ~^(09|10|11|12|13|14|15|16)$ loadtest_api_slow;  # 50 req/s
}

limit_req_zone $binary_remote_addr zone=loadtest_api_slow:10m rate=50r/s;
```

## Support and Resources

- **Nginx documentation**: https://nginx.org/en/docs/
- **K6 documentation**: https://k6.io/docs/
- **Locust documentation**: https://docs.locust.io/
- **Project README**: `/home/user/Autonomous-Assignment-Program-Manager/nginx/README.md`

## Changelog

- **2025-12-18**: Initial load testing configuration created
  - Added `load-testing.conf` with connection pooling and rate limits
  - Added `loadtest-locations.conf` snippet for easy inclusion
  - Updated nginx README with load testing documentation
