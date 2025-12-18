# k6 Load Testing Framework

Comprehensive load testing suite for the Residency Scheduler API using [k6](https://k6.io/).

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Test Scenarios](#test-scenarios)
- [Running Tests](#running-tests)
- [Docker Usage](#docker-usage)
- [Interpreting Results](#interpreting-results)
- [Writing New Tests](#writing-new-tests)
- [Configuration](#configuration)
- [Metrics and Monitoring](#metrics-and-monitoring)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

---

## Overview

This load testing framework provides comprehensive performance testing for the Residency Scheduler API. It includes:

- **Multiple test scenarios**: Smoke, load, stress, spike, and soak tests
- **Authentication management**: JWT token caching and session handling
- **Test data generation**: Realistic data generators for all entities
- **Docker integration**: Run tests in containers with the backend
- **Metrics collection**: Integration with InfluxDB and Grafana (optional)
- **Configurable thresholds**: Performance SLOs for critical endpoints

### Test Types

| Test Type | Purpose | Duration | Max VUs |
|-----------|---------|----------|---------|
| **Smoke** | Basic functionality verification | 1 min | 5 |
| **Load** | Standard traffic simulation | 5 min | 50 |
| **Stress** | Find system breaking point | 10 min | 200 |
| **Spike** | Handle sudden traffic bursts | 5 min | 100 |
| **Soak** | Long-term stability | 1 hour | 20 |

---

## Prerequisites

### Local Installation

1. **Install k6**: Follow the [official installation guide](https://k6.io/docs/get-started/installation/)

   ```bash
   # macOS
   brew install k6

   # Ubuntu/Debian
   sudo gpg -k
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6

   # Windows (via Chocolatey)
   choco install k6
   ```

2. **Verify installation**:
   ```bash
   k6 version
   ```

### Docker Installation

If using Docker, k6 is included in the Docker Compose setup. No local installation needed.

---

## Quick Start

### 1. Setup Test Environment

Ensure the backend is running:

```bash
# From project root
docker-compose up -d backend db redis
```

### 2. Run Your First Test

```bash
cd load-tests

# Run a smoke test (basic functionality)
k6 run scenarios/smoke-test.js

# Or use npm scripts
npm run test:smoke
```

### 3. View Results

k6 outputs results to the console. Look for:
- HTTP request metrics (response times, throughput)
- Check pass/fail rates
- Threshold violations

---

## Test Scenarios

### Smoke Test

**Purpose**: Verify basic functionality with minimal load

```bash
npm run test:smoke
```

**What it tests**:
- Authentication endpoints
- Basic CRUD operations
- API health checks

**Duration**: ~1 minute  
**VUs**: 2-5

---

### Load Test

**Purpose**: Simulate normal production traffic

```bash
npm run test:load
```

**What it tests**:
- Sustained user load
- Common user workflows
- Response times under normal conditions

**Duration**: ~5 minutes  
**VUs**: Ramps from 10 → 30 → 50

**Thresholds**:
- p95 response time < 500ms
- Error rate < 1%

---

### Stress Test

**Purpose**: Find system limits and breaking points

```bash
npm run test:stress
```

**What it tests**:
- Gradual load increase
- System behavior at high load
- Recovery after peak load

**Duration**: ~10 minutes  
**VUs**: Ramps from 20 → 200

**Use cases**:
- Capacity planning
- Finding bottlenecks
- Testing auto-scaling

---

### Spike Test

**Purpose**: Validate handling of sudden traffic bursts

```bash
npm run test:spike
```

**What it tests**:
- Sudden traffic increase (10 → 100 VUs in 10 seconds)
- System stability during spikes
- Recovery after spike

**Duration**: ~5 minutes  
**VUs**: Sudden spike to 100

**Use cases**:
- Marketing campaign traffic
- News events
- Black Friday scenarios

---

### Soak Test

**Purpose**: Verify long-term stability and detect memory leaks

```bash
npm run test:soak
```

**What it tests**:
- Sustained load over time
- Memory leaks
- Resource exhaustion
- Performance degradation

**Duration**: 1 hour  
**VUs**: Constant 20 VUs

**Warning**: This test is resource-intensive. Run during off-hours.

---

## Running Tests

### Local Execution

```bash
cd load-tests

# Individual scenarios
k6 run scenarios/smoke-test.js
k6 run scenarios/load-test.js
k6 run scenarios/stress-test.js

# With custom VUs and duration
k6 run --vus 50 --duration 5m scenarios/load-test.js

# With environment variables
API_BASE_URL=http://localhost:8000 k6 run scenarios/load-test.js

# Save results to file
k6 run --out json=results/test-results.json scenarios/load-test.js
```

### NPM Scripts

```bash
# Smoke test
npm run test:smoke

# Load test
npm run test:load

# Stress test
npm run test:stress

# Spike test
npm run test:spike

# Soak test (long-running)
npm run test:soak

# All tests sequentially
npm run test:all
```

---

## Docker Usage

### Run Tests in Docker

```bash
# From project root
cd load-tests

# Smoke test
npm run test:docker:smoke

# Load test
npm run test:docker:load

# Stress test
npm run test:docker:stress

# Custom test
docker-compose -f docker-compose.k6.yml --profile load-testing run --rm k6 run /load-tests/scenarios/your-test.js
```

### With Metrics Collection

```bash
# Start InfluxDB + Grafana
npm run metrics:up

# Run tests with metrics
docker-compose -f docker-compose.k6.yml --profile load-testing-metrics run --rm k6 run \
  --out influxdb=http://influxdb:8086/k6 \
  /load-tests/scenarios/load-test.js

# View Grafana dashboard
# Open http://localhost:3001
# Username: admin, Password: admin

# Stop metrics
npm run metrics:down
```

---

## Interpreting Results

### Console Output

k6 provides real-time metrics during execution:

```
scenarios: (100.00%) 1 scenario, 50 max VUs, 5m30s max duration
✓ status is 200
✓ response time < 500ms

checks.........................: 98.50%  ✓ 19700    ✗ 300
data_received..................: 45 MB   150 kB/s
data_sent......................: 18 MB   60 kB/s
http_req_blocked...............: avg=1.2ms   min=0s   med=1ms    max=150ms  p(90)=2ms   p(95)=3ms
http_req_connecting............: avg=800µs   min=0s   med=600µs  max=100ms  p(90)=1.5ms p(95)=2ms
http_req_duration..............: avg=250ms   min=50ms med=230ms  max=2s     p(90)=400ms p(95)=500ms
  { expected_response:true }...: avg=245ms   min=50ms med=228ms  max=1.8s   p(90)=395ms p(95)=490ms
http_req_failed................: 1.50%   ✓ 300      ✗ 19700
http_req_receiving.............: avg=5ms     min=1ms  med=4ms    max=50ms   p(90)=8ms   p(95)=12ms
http_req_sending...............: avg=2ms     min=500µs med=1.5ms max=20ms   p(90)=3ms   p(95)=5ms
http_req_tls_handshaking.......: avg=0s      min=0s   med=0s     max=0s     p(90)=0s    p(95)=0s
http_req_waiting...............: avg=243ms   min=48ms med=224ms  max=1.9s   p(90)=393ms p(95)=488ms
http_reqs......................: 20000   66.66/s
iteration_duration.............: avg=750ms   min=200ms med=700ms max=3s     p(90)=1.2s  p(95)=1.5s
iterations.....................: 10000   33.33/s
vus............................: 50      min=10     max=50
vus_max........................: 50      min=50     max=50
```

### Key Metrics

| Metric | Description | Good Value |
|--------|-------------|------------|
| **http_req_duration** | Total request time | p95 < 500ms |
| **http_req_failed** | HTTP error rate | < 1% |
| **checks** | Custom check pass rate | > 95% |
| **http_reqs** | Requests per second | Depends on capacity |
| **vus** | Virtual users | As configured |

### Threshold Violations

If thresholds fail, k6 exits with code 99:

```
✗ http_req_duration...........: p(95)=850ms (threshold: p(95)<500ms)
```

**Action items**:
1. Investigate slow endpoints
2. Check database query performance
3. Review server logs
4. Consider optimization or scaling

---

## Writing New Tests

### Basic Test Structure

Create a new file in `scenarios/`:

```javascript
/**
 * My Custom Load Test
 */

import { check } from 'k6';
import { createTestOptions } from '../k6.config.js';
import { createSession } from '../utils/auth.js';
import { generatePerson } from '../utils/data-generators.js';

// Test configuration
export const options = createTestOptions({
  stages: [
    { duration: '1m', target: 10 },
    { duration: '3m', target: 10 },
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'],
  },
});

// Setup - runs once
export function setup() {
  const session = createSession('admin', 'AdminPassword123!');
  return { session };
}

// Main test - runs for each VU iteration
export default function (data) {
  const { session } = data;
  
  // Generate test data
  const person = generatePerson('resident');
  
  // Make requests
  const createRes = session.post(
    'http://localhost:8000/api/people',
    person,
    { name: 'create_person' }
  );
  
  // Validate response
  check(createRes, {
    'create person status is 201': (r) => r.status === 201,
    'person has id': (r) => {
      try {
        return JSON.parse(r.body).id !== undefined;
      } catch {
        return false;
      }
    },
  });
  
  // Think time (simulate user delay)
  sleep(1);
}

// Teardown - runs once at end
export function teardown(data) {
  // Cleanup if needed
  console.log('Test completed');
}
```

### Using Utilities

```javascript
import { 
  createSession, 
  getRandomTestUser 
} from '../utils/auth.js';

import {
  generatePerson,
  generateAssignment,
  generateAbsence,
} from '../utils/data-generators.js';

// Get random user
const user = getRandomTestUser();
const session = createSession(user.username, user.password);

// Generate test data
const resident = generatePerson('resident');
const faculty = generatePerson('faculty');
const absence = generateAbsence(resident.id);
```

---

## Configuration

### Environment Variables

Configure tests via environment variables:

```bash
# API Base URL
export API_BASE_URL=http://localhost:8000

# Test environment (local, docker, staging)
export TEST_ENV=local

# k6 output format
export K6_OUT=json=results/test.json

# Enable web dashboard
export K6_WEB_DASHBOARD=true
```

### k6.config.js

Main configuration file with:
- Base URL settings
- Default thresholds
- Load test stages
- HTTP parameters
- Rate limits

Edit `/load-tests/k6.config.js` to customize defaults.

---

## Metrics and Monitoring

### InfluxDB Integration

Store metrics in InfluxDB for historical analysis:

```bash
# Start InfluxDB
npm run metrics:up

# Run test with InfluxDB output
k6 run --out influxdb=http://localhost:8086/k6 scenarios/load-test.js

# Access InfluxDB UI
# http://localhost:8086
# Username: admin, Password: adminpassword
```

### Grafana Dashboards

Visualize metrics in Grafana:

```bash
# Ensure metrics stack is running
npm run metrics:up

# Access Grafana
# http://localhost:3001
# Username: admin, Password: admin

# Import k6 dashboard
# Dashboard ID: 2587 (from grafana.com)
```

### HTML Reports

Generate HTML reports:

```bash
k6 run --out json=results/test.json scenarios/load-test.js
k6 export --output html results/test.json > results/report.html
```

---

## Troubleshooting

### Common Issues

#### 1. Connection Refused

**Error**: `ECONNREFUSED` when connecting to API

**Solution**:
```bash
# Verify backend is running
docker-compose ps

# Check API URL
echo $API_BASE_URL

# Test connectivity
curl http://localhost:8000/health
```

#### 2. Authentication Failures

**Error**: Login returns 401 or 429 (rate limited)

**Solution**:
- Verify test user credentials match seeded database users
- Check rate limiting settings in backend
- Use token caching to reduce auth requests

#### 3. High Error Rates

**Error**: `http_req_failed` > 1%

**Solution**:
- Reduce VUs to find stable load level
- Check backend logs for errors
- Verify database performance
- Check resource constraints (CPU, memory)

#### 4. Slow Response Times

**Error**: Threshold violations for `http_req_duration`

**Solution**:
- Profile slow endpoints
- Check database query performance
- Review N+1 query issues
- Consider caching strategies

---

## Best Practices

### 1. Start Small

Begin with smoke tests before running large-scale tests:

```bash
npm run test:smoke  # Always run first
npm run test:load   # Then load test
npm run test:stress # Finally stress test
```

### 2. Use Realistic Data

Generate realistic test data that matches production patterns:

```javascript
// Good: Realistic distribution
const person = Math.random() > 0.7 
  ? generatePerson('resident')
  : generatePerson('faculty');

// Bad: Unrealistic uniform distribution
const person = generatePerson();
```

### 3. Think Time

Add realistic delays between requests:

```javascript
import { sleep } from 'k6';

export default function() {
  // Make request
  session.get('/api/people');
  
  // Simulate user reading time (1-3 seconds)
  sleep(Math.random() * 2 + 1);
}
```

### 4. Tag Your Requests

Use tags for detailed metrics:

```javascript
session.get('/api/people', { name: 'list_people', endpoint: 'people' });
session.post('/api/assignments', data, { name: 'create_assignment', endpoint: 'assignments' });
```

### 5. Clean Up Test Data

Remove test data after tests to avoid database bloat:

```javascript
export function teardown(data) {
  // Delete test entities created during load test
  // Implementation depends on your cleanup strategy
}
```

### 6. Monitor Resource Usage

Watch system resources during tests:

```bash
# CPU and memory
docker stats

# Backend logs
docker-compose logs -f backend

# Database connections
docker-compose exec db psql -U scheduler -c "SELECT count(*) FROM pg_stat_activity;"
```

### 7. Version Your Tests

Commit load tests to version control:
- Track performance over time
- Test performance impact of changes
- Enable CI/CD performance testing

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Nightly at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Start services
        run: docker-compose up -d
      
      - name: Wait for backend
        run: ./scripts/wait-for-it.sh localhost:8000 -t 60
      
      - name: Run smoke test
        run: |
          cd load-tests
          npm run test:docker:smoke
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: load-tests/results/
```

---

## Additional Resources

- [k6 Documentation](https://k6.io/docs/)
- [k6 Examples](https://k6.io/docs/examples/)
- [Performance Testing Best Practices](https://k6.io/docs/testing-guides/)
- [k6 Community Forum](https://community.k6.io/)

---

## Support

For questions or issues:
1. Check this README first
2. Review k6 documentation
3. Check project issues on GitHub
4. Contact the development team

---

**Last Updated**: 2025-12-18  
**Maintained By**: Residency Scheduler Team
