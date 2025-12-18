***REMOVED*** k6 Load Testing Framework

Comprehensive load testing suite for the Residency Scheduler API using [k6](https://k6.io/).

***REMOVED******REMOVED*** Table of Contents

- [Overview](***REMOVED***overview)
- [Prerequisites](***REMOVED***prerequisites)
- [Quick Start](***REMOVED***quick-start)
- [Test Scenarios](***REMOVED***test-scenarios)
- [Running Tests](***REMOVED***running-tests)
- [Docker Usage](***REMOVED***docker-usage)
- [Interpreting Results](***REMOVED***interpreting-results)
- [Writing New Tests](***REMOVED***writing-new-tests)
- [Configuration](***REMOVED***configuration)
- [Metrics and Monitoring](***REMOVED***metrics-and-monitoring)
- [Troubleshooting](***REMOVED***troubleshooting)
- [Best Practices](***REMOVED***best-practices)

---

***REMOVED******REMOVED*** Overview

This load testing framework provides comprehensive performance testing for the Residency Scheduler API. It includes:

- **Multiple test scenarios**: Smoke, load, stress, spike, and soak tests
- **Authentication management**: JWT token caching and session handling
- **Test data generation**: Realistic data generators for all entities
- **Docker integration**: Run tests in containers with the backend
- **Metrics collection**: Integration with InfluxDB and Grafana (optional)
- **Configurable thresholds**: Performance SLOs for critical endpoints

***REMOVED******REMOVED******REMOVED*** Test Types

| Test Type | Purpose | Duration | Max VUs |
|-----------|---------|----------|---------|
| **Smoke** | Basic functionality verification | 1 min | 5 |
| **Load** | Standard traffic simulation | 5 min | 50 |
| **Stress** | Find system breaking point | 10 min | 200 |
| **Spike** | Handle sudden traffic bursts | 5 min | 100 |
| **Soak** | Long-term stability | 1 hour | 20 |

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Local Installation

1. **Install k6**: Follow the [official installation guide](https://k6.io/docs/get-started/installation/)

   ```bash
   ***REMOVED*** macOS
   brew install k6

   ***REMOVED*** Ubuntu/Debian
   sudo gpg -k
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6

   ***REMOVED*** Windows (via Chocolatey)
   choco install k6
   ```

2. **Verify installation**:
   ```bash
   k6 version
   ```

***REMOVED******REMOVED******REMOVED*** Docker Installation

If using Docker, k6 is included in the Docker Compose setup. No local installation needed.

---

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** 1. Setup Test Environment

Ensure the backend is running:

```bash
***REMOVED*** From project root
docker-compose up -d backend db redis
```

***REMOVED******REMOVED******REMOVED*** 2. Run Your First Test

```bash
cd load-tests

***REMOVED*** Run a smoke test (basic functionality)
k6 run scenarios/smoke-test.js

***REMOVED*** Or use npm scripts
npm run test:smoke
```

***REMOVED******REMOVED******REMOVED*** 3. View Results

k6 outputs results to the console. Look for:
- HTTP request metrics (response times, throughput)
- Check pass/fail rates
- Threshold violations

---

***REMOVED******REMOVED*** Test Scenarios

***REMOVED******REMOVED******REMOVED*** Smoke Test

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

***REMOVED******REMOVED******REMOVED*** Load Test

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

***REMOVED******REMOVED******REMOVED*** Stress Test

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

***REMOVED******REMOVED******REMOVED*** Spike Test

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

***REMOVED******REMOVED******REMOVED*** Soak Test

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

***REMOVED******REMOVED*** Running Tests

***REMOVED******REMOVED******REMOVED*** Local Execution

```bash
cd load-tests

***REMOVED*** Individual scenarios
k6 run scenarios/smoke-test.js
k6 run scenarios/load-test.js
k6 run scenarios/stress-test.js

***REMOVED*** With custom VUs and duration
k6 run --vus 50 --duration 5m scenarios/load-test.js

***REMOVED*** With environment variables
API_BASE_URL=http://localhost:8000 k6 run scenarios/load-test.js

***REMOVED*** Save results to file
k6 run --out json=results/test-results.json scenarios/load-test.js
```

***REMOVED******REMOVED******REMOVED*** NPM Scripts

```bash
***REMOVED*** Smoke test
npm run test:smoke

***REMOVED*** Load test
npm run test:load

***REMOVED*** Stress test
npm run test:stress

***REMOVED*** Spike test
npm run test:spike

***REMOVED*** Soak test (long-running)
npm run test:soak

***REMOVED*** All tests sequentially
npm run test:all
```

---

***REMOVED******REMOVED*** Docker Usage

***REMOVED******REMOVED******REMOVED*** Run Tests in Docker

```bash
***REMOVED*** From project root
cd load-tests

***REMOVED*** Smoke test
npm run test:docker:smoke

***REMOVED*** Load test
npm run test:docker:load

***REMOVED*** Stress test
npm run test:docker:stress

***REMOVED*** Custom test
docker-compose -f docker-compose.k6.yml --profile load-testing run --rm k6 run /load-tests/scenarios/your-test.js
```

***REMOVED******REMOVED******REMOVED*** With Metrics Collection

```bash
***REMOVED*** Start InfluxDB + Grafana
npm run metrics:up

***REMOVED*** Run tests with metrics
docker-compose -f docker-compose.k6.yml --profile load-testing-metrics run --rm k6 run \
  --out influxdb=http://influxdb:8086/k6 \
  /load-tests/scenarios/load-test.js

***REMOVED*** View Grafana dashboard
***REMOVED*** Open http://localhost:3001
***REMOVED*** Username: admin, Password: admin

***REMOVED*** Stop metrics
npm run metrics:down
```

---

***REMOVED******REMOVED*** Interpreting Results

***REMOVED******REMOVED******REMOVED*** Console Output

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

***REMOVED******REMOVED******REMOVED*** Key Metrics

| Metric | Description | Good Value |
|--------|-------------|------------|
| **http_req_duration** | Total request time | p95 < 500ms |
| **http_req_failed** | HTTP error rate | < 1% |
| **checks** | Custom check pass rate | > 95% |
| **http_reqs** | Requests per second | Depends on capacity |
| **vus** | Virtual users | As configured |

***REMOVED******REMOVED******REMOVED*** Threshold Violations

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

***REMOVED******REMOVED*** Writing New Tests

***REMOVED******REMOVED******REMOVED*** Basic Test Structure

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

***REMOVED******REMOVED******REMOVED*** Using Utilities

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

***REMOVED******REMOVED*** Configuration

***REMOVED******REMOVED******REMOVED*** Environment Variables

Configure tests via environment variables:

```bash
***REMOVED*** API Base URL
export API_BASE_URL=http://localhost:8000

***REMOVED*** Test environment (local, docker, staging)
export TEST_ENV=local

***REMOVED*** k6 output format
export K6_OUT=json=results/test.json

***REMOVED*** Enable web dashboard
export K6_WEB_DASHBOARD=true
```

***REMOVED******REMOVED******REMOVED*** k6.config.js

Main configuration file with:
- Base URL settings
- Default thresholds
- Load test stages
- HTTP parameters
- Rate limits

Edit `/load-tests/k6.config.js` to customize defaults.

---

***REMOVED******REMOVED*** Metrics and Monitoring

***REMOVED******REMOVED******REMOVED*** InfluxDB Integration

Store metrics in InfluxDB for historical analysis:

```bash
***REMOVED*** Start InfluxDB
npm run metrics:up

***REMOVED*** Run test with InfluxDB output
k6 run --out influxdb=http://localhost:8086/k6 scenarios/load-test.js

***REMOVED*** Access InfluxDB UI
***REMOVED*** http://localhost:8086
***REMOVED*** Username: admin, Password: adminpassword
```

***REMOVED******REMOVED******REMOVED*** Grafana Dashboards

Visualize metrics in Grafana:

```bash
***REMOVED*** Ensure metrics stack is running
npm run metrics:up

***REMOVED*** Access Grafana
***REMOVED*** http://localhost:3001
***REMOVED*** Username: admin, Password: admin

***REMOVED*** Import k6 dashboard
***REMOVED*** Dashboard ID: 2587 (from grafana.com)
```

***REMOVED******REMOVED******REMOVED*** HTML Reports

Generate HTML reports:

```bash
k6 run --out json=results/test.json scenarios/load-test.js
k6 export --output html results/test.json > results/report.html
```

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Common Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. Connection Refused

**Error**: `ECONNREFUSED` when connecting to API

**Solution**:
```bash
***REMOVED*** Verify backend is running
docker-compose ps

***REMOVED*** Check API URL
echo $API_BASE_URL

***REMOVED*** Test connectivity
curl http://localhost:8000/health
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Authentication Failures

**Error**: Login returns 401 or 429 (rate limited)

**Solution**:
- Verify test user credentials match seeded database users
- Check rate limiting settings in backend
- Use token caching to reduce auth requests

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. High Error Rates

**Error**: `http_req_failed` > 1%

**Solution**:
- Reduce VUs to find stable load level
- Check backend logs for errors
- Verify database performance
- Check resource constraints (CPU, memory)

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. Slow Response Times

**Error**: Threshold violations for `http_req_duration`

**Solution**:
- Profile slow endpoints
- Check database query performance
- Review N+1 query issues
- Consider caching strategies

---

***REMOVED******REMOVED*** Best Practices

***REMOVED******REMOVED******REMOVED*** 1. Start Small

Begin with smoke tests before running large-scale tests:

```bash
npm run test:smoke  ***REMOVED*** Always run first
npm run test:load   ***REMOVED*** Then load test
npm run test:stress ***REMOVED*** Finally stress test
```

***REMOVED******REMOVED******REMOVED*** 2. Use Realistic Data

Generate realistic test data that matches production patterns:

```javascript
// Good: Realistic distribution
const person = Math.random() > 0.7 
  ? generatePerson('resident')
  : generatePerson('faculty');

// Bad: Unrealistic uniform distribution
const person = generatePerson();
```

***REMOVED******REMOVED******REMOVED*** 3. Think Time

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

***REMOVED******REMOVED******REMOVED*** 4. Tag Your Requests

Use tags for detailed metrics:

```javascript
session.get('/api/people', { name: 'list_people', endpoint: 'people' });
session.post('/api/assignments', data, { name: 'create_assignment', endpoint: 'assignments' });
```

***REMOVED******REMOVED******REMOVED*** 5. Clean Up Test Data

Remove test data after tests to avoid database bloat:

```javascript
export function teardown(data) {
  // Delete test entities created during load test
  // Implementation depends on your cleanup strategy
}
```

***REMOVED******REMOVED******REMOVED*** 6. Monitor Resource Usage

Watch system resources during tests:

```bash
***REMOVED*** CPU and memory
docker stats

***REMOVED*** Backend logs
docker-compose logs -f backend

***REMOVED*** Database connections
docker-compose exec db psql -U scheduler -c "SELECT count(*) FROM pg_stat_activity;"
```

***REMOVED******REMOVED******REMOVED*** 7. Version Your Tests

Commit load tests to version control:
- Track performance over time
- Test performance impact of changes
- Enable CI/CD performance testing

---

***REMOVED******REMOVED*** CI/CD Integration

***REMOVED******REMOVED******REMOVED*** GitHub Actions Example

```yaml
name: Load Tests

on:
  schedule:
    - cron: '0 2 * * *'  ***REMOVED*** Nightly at 2 AM
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

***REMOVED******REMOVED*** Additional Resources

- [k6 Documentation](https://k6.io/docs/)
- [k6 Examples](https://k6.io/docs/examples/)
- [Performance Testing Best Practices](https://k6.io/docs/testing-guides/)
- [k6 Community Forum](https://community.k6.io/)

---

***REMOVED******REMOVED*** Support

For questions or issues:
1. Check this README first
2. Review k6 documentation
3. Check project issues on GitHub
4. Contact the development team

---

**Last Updated**: 2025-12-18  
**Maintained By**: Residency Scheduler Team
