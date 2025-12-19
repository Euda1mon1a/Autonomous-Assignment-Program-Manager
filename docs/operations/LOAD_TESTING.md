***REMOVED*** Load Testing Documentation

This document provides comprehensive guidance for load testing the Residency Scheduler application to ensure it meets performance and reliability requirements for healthcare scheduling.

---

***REMOVED******REMOVED*** Table of Contents

- [Overview](***REMOVED***overview)
- [SLO Definitions](***REMOVED***slo-definitions)
- [Load Testing Infrastructure](***REMOVED***load-testing-infrastructure)
- [Test Scenarios](***REMOVED***test-scenarios)
- [Running Load Tests](***REMOVED***running-load-tests)
- [Interpreting Results](***REMOVED***interpreting-results)
- [CI/CD Integration](***REMOVED***cicd-integration)
- [Incident Response](***REMOVED***incident-response)
- [Capacity Planning](***REMOVED***capacity-planning)
- [Healthcare-Specific Considerations](***REMOVED***healthcare-specific-considerations)
- [Troubleshooting](***REMOVED***troubleshooting)

---

***REMOVED******REMOVED*** Overview

***REMOVED******REMOVED******REMOVED*** Purpose of Load Testing

Load testing is critical for the Residency Scheduler application to ensure:

1. **Patient Safety**: Schedule generation and ACGME compliance validation must perform reliably under load
2. **Regulatory Compliance**: System must maintain 99.9% availability to support critical healthcare operations
3. **User Experience**: Coordinators, faculty, and administrators need responsive interfaces during peak usage
4. **Capacity Planning**: Understand system limits before adding new programs or users

***REMOVED******REMOVED******REMOVED*** Compliance Requirements

**Healthcare Availability Standards:**
- **Target Availability**: 99.9% (SLA requirement for patient-facing healthcare systems)
- **Maximum Planned Downtime**: 8.76 hours/year
- **ACGME Compliance**: Real-time validation must complete within SLO to prevent scheduling violations
- **Data Integrity**: No data loss or corruption under load conditions

***REMOVED******REMOVED******REMOVED*** Testing Philosophy

**Shift-Left Testing:**
- Run performance tests early in development cycle
- Catch regressions before production deployment
- Establish baselines during feature development

**Continuous Validation:**
- Automated load tests in CI/CD pipeline
- Regular production-like stress tests
- Quarterly capacity planning exercises

**Realistic Scenarios:**
- Test with production-like data volumes
- Simulate real user behavior patterns
- Include background tasks (Celery workers)

---

***REMOVED******REMOVED*** SLO Definitions

***REMOVED******REMOVED******REMOVED*** Service Level Objectives (SLOs)

These SLOs define acceptable performance under various load conditions. Violations trigger alerts and require investigation.

| Metric | Normal Target | Under Load | Critical |
|--------|--------------|------------|----------|
| **API P95 Latency** | < 500ms | < 2s | > 5s |
| **API P99 Latency** | < 1s | < 3s | > 10s |
| **Schedule Generation P95** | < 180s (3 min) | < 300s (5 min) | > 600s (10 min) |
| **ACGME Validation P95** | < 2s | < 5s | > 10s |
| **Error Rate** | < 0.1% | < 1% | > 5% |
| **Availability** | 99.99% | 99.9% | < 99% |
| **Database Query P95** | < 100ms | < 500ms | > 2s |
| **Celery Task Processing** | < 30s | < 120s | > 300s |
| **Concurrent Users** | 50+ | 100+ | N/A |
| **Throughput** | 100 req/s | 200 req/s | N/A |

***REMOVED******REMOVED******REMOVED*** Definitions

- **Normal**: Typical daily operations (business hours, < 50 concurrent users)
- **Under Load**: Peak usage scenarios (start of academic year, schedule generation, 50-100 users)
- **Critical**: Performance degradation requiring immediate incident response

***REMOVED******REMOVED******REMOVED*** SLO Measurement

Metrics are measured using:
- **k6 HTTP metrics**: Request duration, error rates
- **Prometheus metrics**: Application-level performance (`http_request_duration_seconds`)
- **Database metrics**: PostgreSQL query performance (`pg_stat_statements`)
- **Celery metrics**: Task completion times, queue depth

---

***REMOVED******REMOVED*** Load Testing Infrastructure

***REMOVED******REMOVED******REMOVED*** Tool: k6

We use [k6](https://k6.io/) for load testing due to:

- **JavaScript-based**: Easy to write and maintain test scenarios
- **High performance**: Written in Go, handles thousands of VUs efficiently
- **HTTP/2 support**: Matches modern browser behavior
- **Rich metrics**: Built-in analysis and custom metric support
- **CI/CD integration**: CLI-friendly with exit codes and JSON output

***REMOVED******REMOVED******REMOVED*** Project Structure

```
load-tests/
├── scenarios/              ***REMOVED*** Test scenario scripts
│   ├── api-baseline.js    ***REMOVED*** Basic API latency baseline
│   ├── concurrent-users.js ***REMOVED*** Multi-user simulation
│   ├── schedule-generation.js ***REMOVED*** Stress test schedule creation
│   └── rate-limit.js      ***REMOVED*** Security testing
├── utils/                  ***REMOVED*** Shared utilities
│   ├── auth.js            ***REMOVED*** JWT authentication helpers
│   └── data-generators.js ***REMOVED*** Test data creation
├── results/                ***REMOVED*** Test outputs (gitignored)
└── package.json           ***REMOVED*** npm scripts for test execution
```

***REMOVED******REMOVED******REMOVED*** Installation

***REMOVED******REMOVED******REMOVED******REMOVED*** Local Setup

```bash
***REMOVED*** Install k6 (macOS)
brew install k6

***REMOVED*** Install k6 (Linux)
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
  --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

***REMOVED*** Install k6 (Windows - Chocolatey)
choco install k6

***REMOVED*** Verify installation
k6 version

***REMOVED*** Install npm dependencies (for test utilities)
cd load-tests
npm install
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker Setup

```bash
***REMOVED*** Run k6 in Docker (useful for CI/CD)
docker run --rm -i grafana/k6 run - < scenarios/api-baseline.js

***REMOVED*** With custom environment variables
docker run --rm -i \
  -e BASE_URL=http://backend:8000 \
  grafana/k6 run - < scenarios/api-baseline.js
```

***REMOVED******REMOVED******REMOVED*** Configuration

Load tests are configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_URL` | `http://localhost:8000` | Backend API URL |
| `VUS` | `10` | Number of virtual users |
| `DURATION` | `30s` | Test duration |
| `ADMIN_EMAIL` | `admin@example.com` | Admin user email |
| `ADMIN_PASSWORD` | `admin_password_123` | Admin user password |
| `RATE_LIMIT_TEST` | `false` | Enable rate limit testing |
| `RESULTS_DIR` | `./results` | Output directory for results |

**Example:**
```bash
export BASE_URL=http://localhost:8000
export VUS=50
export DURATION=5m
k6 run scenarios/concurrent-users.js
```

---

***REMOVED******REMOVED*** Test Scenarios

***REMOVED******REMOVED******REMOVED*** Available Scenarios

| Scenario | Description | Command | Duration | Purpose |
|----------|-------------|---------|----------|---------|
| **API Baseline** | Establish P50/P95/P99 latency baselines for common endpoints | `npm run test:baseline` | 2 min | Detect regressions |
| **Concurrent Users** | Simulate 10-100 virtual users performing typical workflows | `npm run test:concurrent` | 5 min | Validate multi-user performance |
| **Schedule Generation** | Stress test schedule generation with varying complexity | `npm run test:schedule` | 10 min | Ensure core functionality scales |
| **ACGME Validation** | Test compliance checking under load | `npm run test:acgme` | 5 min | Critical path validation |
| **Rate Limit Validation** | Verify rate limiting protects against abuse | `npm run test:ratelimit` | 2 min | Security testing |
| **Database Stress** | Heavy read/write operations to test DB performance | `npm run test:database` | 5 min | Identify bottlenecks |
| **Full Suite** | Run all scenarios sequentially | `npm run test:all` | 30 min | Pre-deployment validation |

***REMOVED******REMOVED******REMOVED*** Scenario Details

***REMOVED******REMOVED******REMOVED******REMOVED*** 1. API Baseline

**Purpose**: Establish performance baselines for regression detection

**Test Flow**:
1. Authenticate as different user roles
2. Execute common API calls:
   - `GET /api/people` (list view)
   - `GET /api/assignments?start_date=X&end_date=Y` (filtered list)
   - `GET /api/blocks?date=X` (day view)
   - `GET /api/analytics/compliance` (dashboard)
3. Measure P50, P95, P99 latencies

**Success Criteria**:
- P95 < 500ms for read operations
- P99 < 1s for read operations
- Error rate < 0.1%

**Command**:
```bash
npm run test:baseline
***REMOVED*** or
k6 run --vus 10 --duration 2m scenarios/api-baseline.js
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 2. Concurrent Users

**Purpose**: Simulate realistic multi-user usage patterns

**Test Flow**:
1. Ramp up from 0 to 100 VUs over 1 minute
2. Maintain 100 VUs for 3 minutes
3. Ramp down over 1 minute
4. Each VU performs realistic workflow:
   - Login
   - View dashboard
   - Browse schedule (random dates)
   - View person details
   - Check compliance status
   - Think time between actions (1-3s)

**Success Criteria**:
- P95 < 2s during peak load
- Error rate < 1%
- All 100 VUs complete workflows

**Command**:
```bash
npm run test:concurrent
***REMOVED*** or
VUS=100 DURATION=5m k6 run scenarios/concurrent-users.js
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 3. Schedule Generation

**Purpose**: Stress test the most computationally intensive operation

**Test Flow**:
1. Authenticate as coordinator/admin
2. Submit schedule generation requests with varying parameters:
   - Date ranges: 30 days, 90 days, 365 days
   - Algorithms: greedy, constraint satisfaction
   - Optimization levels: basic, full
3. Poll for completion
4. Validate results

**Success Criteria**:
- P95 < 180s for 30-day schedules
- P95 < 300s for 90-day schedules
- No failures due to timeouts
- All generated schedules are ACGME compliant

**Command**:
```bash
npm run test:schedule
***REMOVED*** or
k6 run --vus 5 --duration 10m scenarios/schedule-generation.js
```

**Note**: Schedule generation is resource-intensive. Limit VUs to avoid overwhelming the system.

***REMOVED******REMOVED******REMOVED******REMOVED*** 4. ACGME Validation

**Purpose**: Ensure compliance validation performs under load

**Test Flow**:
1. Create/modify assignments in parallel
2. Trigger ACGME compliance validation
3. Measure validation time
4. Verify accuracy of results

**Success Criteria**:
- P95 < 2s for validation
- 100% accuracy (no false positives/negatives)
- No database deadlocks

**Command**:
```bash
npm run test:acgme
***REMOVED*** or
k6 run --vus 20 --duration 5m scenarios/acgme-validation.js
```

***REMOVED******REMOVED******REMOVED******REMOVED*** 5. Rate Limit Validation

**Purpose**: Verify rate limiting protects against abuse

**Test Flow**:
1. Attempt rapid authentication (exceed 5 login/min limit)
2. Verify 429 responses are returned
3. Wait for rate limit window to reset
4. Verify normal access restored

**Success Criteria**:
- Rate limits enforced correctly
- Legitimate users not blocked
- 429 status codes returned

**Command**:
```bash
npm run test:ratelimit
***REMOVED*** or
RATE_LIMIT_TEST=true k6 run scenarios/rate-limit.js
```

**Warning**: Do not run against production. May trigger security alerts.

---

***REMOVED******REMOVED*** Running Load Tests

***REMOVED******REMOVED******REMOVED*** Prerequisites

1. **Backend Running**: Ensure backend API is accessible
   ```bash
   ***REMOVED*** Start via Docker Compose
   docker-compose up -d backend db redis celery-worker

   ***REMOVED*** Verify health
   curl http://localhost:8000/health
   ```

2. **Test Data**: Populate database with realistic data
   ```bash
   cd backend
   python scripts/seed_test_data.py --people 100 --rotations 20 --blocks 365
   ```

3. **Test Users**: Create users for load testing
   ```bash
   ***REMOVED*** Create via API or directly in database
   python scripts/create_test_users.py
   ```

***REMOVED******REMOVED******REMOVED*** Local Execution

***REMOVED******REMOVED******REMOVED******REMOVED*** Run Individual Scenarios

```bash
cd load-tests

***REMOVED*** API baseline test
npm run test:baseline

***REMOVED*** Concurrent users (custom parameters)
VUS=50 DURATION=5m npm run test:concurrent

***REMOVED*** Schedule generation stress test
npm run test:schedule

***REMOVED*** ACGME validation
npm run test:acgme

***REMOVED*** Rate limit security test
npm run test:ratelimit
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Run Full Test Suite

```bash
***REMOVED*** Run all scenarios sequentially
npm run test:all

***REMOVED*** Results saved to load-tests/results/ directory
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Custom k6 Options

```bash
***REMOVED*** Custom virtual users and duration
k6 run --vus 50 --duration 5m scenarios/concurrent-users.js

***REMOVED*** Ramping stages
k6 run --stage 1m:10 --stage 3m:50 --stage 1m:0 scenarios/api-baseline.js

***REMOVED*** Output to JSON
k6 run --out json=results/output.json scenarios/api-baseline.js

***REMOVED*** Set custom thresholds
k6 run \
  --threshold http_req_duration=p95:500 \
  --threshold http_req_failed=rate:0.01 \
  scenarios/api-baseline.js
```

***REMOVED******REMOVED******REMOVED*** Docker Execution

```bash
***REMOVED*** Run in Docker (no local k6 installation needed)
docker run --rm -i \
  --network host \
  -e BASE_URL=http://localhost:8000 \
  -e VUS=50 \
  -e DURATION=5m \
  grafana/k6 run - < scenarios/concurrent-users.js

***REMOVED*** With results output
docker run --rm -i \
  -v $(pwd)/results:/results \
  grafana/k6 run --out json=/results/output.json - < scenarios/api-baseline.js
```

***REMOVED******REMOVED******REMOVED*** Environment-Specific Testing

***REMOVED******REMOVED******REMOVED******REMOVED*** Staging Environment

```bash
export BASE_URL=https://staging.scheduler.example.com
export ADMIN_EMAIL=admin@staging.example.com
export ADMIN_PASSWORD=$STAGING_ADMIN_PASSWORD

npm run test:concurrent
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Production Testing

**WARNING**: Only run read-heavy scenarios against production.

```bash
***REMOVED*** READ-ONLY test (safe for production)
export BASE_URL=https://scheduler.example.com
export VUS=10
export DURATION=2m

***REMOVED*** Only run baseline test (read operations)
k6 run scenarios/api-baseline-readonly.js
```

**Do NOT run**:
- Schedule generation tests (resource intensive)
- Rate limit tests (may block legitimate users)
- Database stress tests (may impact production)

---

***REMOVED******REMOVED*** Interpreting Results

***REMOVED******REMOVED******REMOVED*** k6 Output Structure

```
          /\      |‾‾| /‾‾/   /‾‾/
     /\  /  \     |  |/  /   /  /
    /  \/    \    |     (   /   ‾‾\
   /          \   |  |\  \ |  (‾)  |
  / __________ \  |__| \__\ \_____/ .io

  execution: local
     script: scenarios/api-baseline.js
     output: -

  scenarios: (100.00%) 1 scenario, 10 max VUs, 2m30s max duration
           * default: 10 looping VUs for 2m0s (gracefulStop: 30s)


running (2m00.1s), 00/10 VUs, 1234 complete and 0 interrupted iterations
default ✓ [======================================] 10 VUs  2m0s

     data_received..................: 12 MB  100 kB/s
     data_sent......................: 1.2 MB  10 kB/s
     http_req_blocked...............: avg=1.23ms   min=1µs    med=3µs     max=123ms  p(90)=5µs     p(95)=7µs
     http_req_connecting............: avg=1.12ms   min=0s     med=0s      max=110ms  p(90)=0s      p(95)=0s
   ✓ http_req_duration..............: avg=245ms    min=45ms   med=201ms   max=1.2s   p(90)=401ms   p(95)=512ms
       { expected_response:true }...: avg=245ms    min=45ms   med=201ms   max=1.2s   p(90)=401ms   p(95)=512ms
   ✓ http_req_failed................: 0.08%  ✓ 1         ✗ 1233
     http_req_receiving.............: avg=1.45ms   min=20µs   med=98µs    max=45ms   p(90)=2.1ms   p(95)=3.4ms
     http_req_sending...............: avg=156µs    min=10µs   med=45µs    max=12ms   p(90)=301µs   p(95)=567µs
     http_req_tls_handshaking.......: avg=0s       min=0s     med=0s      max=0s     p(90)=0s      p(95)=0s
     http_req_waiting...............: avg=243ms    min=44ms   med=200ms   max=1.19s  p(90)=399ms   p(95)=510ms
     http_reqs......................: 1234   10.3/s
     iteration_duration.............: avg=1.12s    min=1.01s  med=1.09s   max=2.5s   p(90)=1.23s   p(95)=1.34s
     iterations.....................: 1234   10.3/s
     vus............................: 10     min=10      max=10
     vus_max........................: 10     min=10      max=10
```

***REMOVED******REMOVED******REMOVED*** Key Metrics

| Metric | Description | What to Look For |
|--------|-------------|------------------|
| **http_req_duration** | Total request duration (send + wait + receive) | P95 should be within SLO |
| **http_req_failed** | Percentage of failed requests | Should be < 1% |
| **http_reqs** | Total requests per second (throughput) | Baseline for capacity |
| **http_req_waiting** | Time to first byte (TTFB) | Server processing time |
| **http_req_receiving** | Time to receive response body | Network/payload size |
| **iterations** | Completed test iterations | More = better sample size |
| **data_received** | Total data downloaded | Check for excessive payloads |

***REMOVED******REMOVED******REMOVED*** Check Marks (✓ vs ✗)

- **✓ http_req_duration**: All requests met threshold (< 500ms P95)
- **✗ http_req_failed**: Failed requests exceeded threshold (> 1%)

Thresholds are defined in test scripts:
```javascript
export const options = {
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% of requests < 500ms
    http_req_failed: ['rate<0.01'],    // < 1% error rate
  },
};
```

***REMOVED******REMOVED******REMOVED*** Percentiles Explained

- **P50 (median)**: 50% of requests faster than this value - typical experience
- **P90**: 90% of requests faster - most users' experience
- **P95**: 95% of requests faster - SLO target
- **P99**: 99% of requests faster - worst case for most users
- **max**: Slowest request - may indicate outliers/issues

***REMOVED******REMOVED******REMOVED*** When to Investigate

**🚨 Critical - Investigate Immediately**
- P95 > Critical threshold (e.g., > 5s for API)
- Error rate > 5%
- http_req_failed checks failing (✗)
- Increasing latency over time (degradation)

**⚠️ Warning - Review Before Deployment**
- P95 > Under Load threshold (e.g., > 2s for API)
- Error rate > 1%
- High variance (max >> P95)

**✅ Good - Meets SLO**
- P95 within Normal threshold
- Error rate < 0.1%
- Consistent performance over test duration

***REMOVED******REMOVED******REMOVED*** Trend Analysis

Compare results across test runs:

```bash
***REMOVED*** Save results with timestamps
k6 run --out json=results/baseline-$(date +%Y%m%d-%H%M%S).json scenarios/api-baseline.js

***REMOVED*** Compare P95 over time
jq -r '.metrics.http_req_duration.values."p(95)"' results/*.json
```

---

***REMOVED******REMOVED*** CI/CD Integration

***REMOVED******REMOVED******REMOVED*** GitHub Actions Workflow

Create `.github/workflows/load-tests.yml`:

```yaml
name: Load Tests

on:
  pull_request:
    branches: [main]
    paths:
      - 'backend/**'
      - 'load-tests/**'
  schedule:
    ***REMOVED*** Run nightly at 2 AM UTC
    - cron: '0 2 * * *'
  workflow_dispatch:
    inputs:
      duration:
        description: 'Test duration (e.g., 5m)'
        required: false
        default: '2m'
      vus:
        description: 'Virtual users'
        required: false
        default: '20'

jobs:
  load-test:
    runs-on: ubuntu-latest
    timeout-minutes: 30

    services:
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_USER: scheduler
          POSTGRES_PASSWORD: test_password
          POSTGRES_DB: residency_scheduler
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install backend dependencies
        run: |
          cd backend
          pip install -r requirements.txt

      - name: Run database migrations
        env:
          DATABASE_URL: postgresql://scheduler:test_password@localhost:5432/residency_scheduler
        run: |
          cd backend
          alembic upgrade head

      - name: Seed test data
        env:
          DATABASE_URL: postgresql://scheduler:test_password@localhost:5432/residency_scheduler
        run: |
          cd backend
          python scripts/seed_test_data.py --people 50 --rotations 10

      - name: Start backend server
        env:
          DATABASE_URL: postgresql://scheduler:test_password@localhost:5432/residency_scheduler
          REDIS_URL: redis://localhost:6379/0
          SECRET_KEY: test_secret_key_min_32_characters_long_for_jwt
        run: |
          cd backend
          uvicorn app.main:app --host 0.0.0.0 --port 8000 &
          sleep 10
          curl -f http://localhost:8000/health || exit 1

      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
            --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | \
            sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6

      - name: Run API baseline test
        env:
          BASE_URL: http://localhost:8000
          VUS: ${{ github.event.inputs.vus || '20' }}
          DURATION: ${{ github.event.inputs.duration || '2m' }}
        run: |
          cd load-tests
          k6 run \
            --out json=results/baseline.json \
            --summary-export=results/baseline-summary.json \
            scenarios/api-baseline.js

      - name: Run concurrent users test
        env:
          BASE_URL: http://localhost:8000
          VUS: ${{ github.event.inputs.vus || '20' }}
          DURATION: ${{ github.event.inputs.duration || '2m' }}
        run: |
          cd load-tests
          k6 run \
            --out json=results/concurrent.json \
            --summary-export=results/concurrent-summary.json \
            scenarios/concurrent-users.js

      - name: Check performance regression
        run: |
          cd load-tests
          ***REMOVED*** Extract P95 from results
          BASELINE_P95=$(jq -r '.metrics.http_req_duration.values."p(95)"' results/baseline-summary.json)

          ***REMOVED*** Fail if P95 > 500ms (SLO threshold)
          if (( $(echo "$BASELINE_P95 > 500" | bc -l) )); then
            echo "❌ Performance regression detected: P95 = ${BASELINE_P95}ms (threshold: 500ms)"
            exit 1
          else
            echo "✅ Performance within SLO: P95 = ${BASELINE_P95}ms"
          fi

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: load-test-results
          path: load-tests/results/
          retention-days: 30

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const summary = JSON.parse(fs.readFileSync('load-tests/results/baseline-summary.json', 'utf8'));
            const p95 = summary.metrics.http_req_duration.values['p(95)'];
            const errorRate = summary.metrics.http_req_failed.values.rate * 100;

            const comment = `***REMOVED******REMOVED*** 📊 Load Test Results

            | Metric | Value | Status |
            |--------|-------|--------|
            | P95 Latency | ${p95.toFixed(0)}ms | ${p95 < 500 ? '✅' : '❌'} |
            | Error Rate | ${errorRate.toFixed(2)}% | ${errorRate < 1 ? '✅' : '❌'} |
            | Requests/sec | ${summary.metrics.http_reqs.values.rate.toFixed(1)} | ℹ️ |

            **SLO**: P95 < 500ms, Error Rate < 1%
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

***REMOVED******REMOVED******REMOVED*** Automated Regression Detection

```bash
***REMOVED*** In CI, compare against baseline
BASELINE_P95=450  ***REMOVED*** From last successful run
CURRENT_P95=$(jq -r '.metrics.http_req_duration.values."p(95)"' results/current.json)

***REMOVED*** Fail if regression > 20%
THRESHOLD=$(echo "$BASELINE_P95 * 1.2" | bc)
if (( $(echo "$CURRENT_P95 > $THRESHOLD" | bc -l) )); then
  echo "Performance regression detected!"
  exit 1
fi
```

***REMOVED******REMOVED******REMOVED*** Alerting on Performance Degradation

**Slack Notification**:
```yaml
- name: Notify Slack on failure
  if: failure()
  uses: slackapi/slack-github-action@v1
  with:
    payload: |
      {
        "text": "🚨 Load test failed on ${{ github.ref }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Load Test Failure*\nBranch: ${{ github.ref }}\nRun: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}"
            }
          }
        ]
      }
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

---

***REMOVED******REMOVED*** Incident Response

***REMOVED******REMOVED******REMOVED*** What to Do When Load Tests Fail

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 1: Identify the Problem

**Check k6 Output:**
```
✗ http_req_duration..............: avg=3.2s     p(95)=8.5s   ← Exceeds 500ms SLO
✗ http_req_failed................: 5.2%                      ← Exceeds 1% error rate
```

**Common Failure Modes:**
1. **High Latency**: P95 > SLO (database bottleneck, slow queries)
2. **High Error Rate**: 5xx errors (crashes, timeouts, database connections)
3. **Increasing Latency**: Performance degrades over time (memory leak, connection pool exhaustion)
4. **Timeout Errors**: Requests don't complete (overwhelmed workers, deadlocks)

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 2: Collect Diagnostic Data

```bash
***REMOVED*** 1. Check backend logs
docker-compose logs backend --tail=1000 > backend-logs.txt

***REMOVED*** 2. Check database performance
docker-compose exec db psql -U scheduler -d residency_scheduler -c "
  SELECT query, calls, total_time, mean_time
  FROM pg_stat_statements
  ORDER BY total_time DESC
  LIMIT 20;
"

***REMOVED*** 3. Check Celery worker status
docker-compose exec celery-worker celery -A app.core.celery_app inspect active

***REMOVED*** 4. Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=http_request_duration_seconds

***REMOVED*** 5. Check system resources
docker stats --no-stream
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 3: Reproduce Locally

```bash
***REMOVED*** Run the failing test scenario locally
cd load-tests
VUS=50 DURATION=5m k6 run scenarios/concurrent-users.js

***REMOVED*** Enable verbose output
k6 run --http-debug scenarios/api-baseline.js

***REMOVED*** Run with fewer VUs to isolate issue
VUS=5 k6 run scenarios/concurrent-users.js
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 4: Analyze and Fix

**Common Issues and Solutions:**

| Issue | Symptoms | Solution |
|-------|----------|----------|
| **Database Connection Pool Exhaustion** | `sqlalchemy.exc.TimeoutError`, increasing latency | Increase pool size in `backend/app/db/session.py` |
| **Slow Queries** | High P95 on specific endpoints | Add database indexes, optimize query |
| **Memory Leak** | Increasing memory usage over time | Profile with `memory_profiler`, fix leaks |
| **Celery Queue Backlog** | Tasks not processing | Add more workers, optimize task code |
| **N+1 Queries** | Many DB queries per request | Use `selectinload()` for eager loading |
| **Rate Limit Too Strict** | 429 errors for legitimate traffic | Adjust rate limits in `backend/app/core/rate_limit.py` |

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 5: Validate Fix

```bash
***REMOVED*** Re-run load test
npm run test:concurrent

***REMOVED*** Compare before/after metrics
echo "Before: P95 = 8.5s, Error Rate = 5.2%"
echo "After:  P95 = 320ms, Error Rate = 0.1%"
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Step 6: Update Documentation

```markdown
***REMOVED******REMOVED*** Incident: High Latency on /api/assignments (2025-12-18)

**Symptoms**: P95 latency exceeded 8s during concurrent user test

**Root Cause**: N+1 query fetching person details for each assignment

**Fix**: Added `selectinload(Assignment.person)` in `backend/app/services/assignment_service.py`

**Validation**: P95 reduced from 8.5s to 320ms

**Prevention**: Added load test to CI/CD to catch regressions
```

***REMOVED******REMOVED******REMOVED*** Rollback Procedures

If a deployment causes performance degradation:

```bash
***REMOVED*** 1. Identify last good version
git log --oneline --graph

***REMOVED*** 2. Rollback Docker deployment
docker-compose down
git checkout <last-good-commit>
docker-compose up -d --build

***REMOVED*** 3. Verify rollback successful
npm run test:baseline

***REMOVED*** 4. Investigate issue in safe environment
git checkout <problematic-commit>
***REMOVED*** Test locally with load tests
```

***REMOVED******REMOVED******REMOVED*** Performance Debugging Checklist

- [ ] Check backend logs for errors
- [ ] Review slow query logs (PostgreSQL)
- [ ] Check database connection pool usage
- [ ] Monitor memory usage over time
- [ ] Verify Celery tasks processing
- [ ] Check Redis memory usage
- [ ] Review Prometheus metrics
- [ ] Profile slow endpoints with `py-spy` or `cProfile`
- [ ] Check for database deadlocks
- [ ] Verify indexes exist on frequently queried columns

---

***REMOVED******REMOVED*** Capacity Planning

***REMOVED******REMOVED******REMOVED*** Using Load Test Results for Scaling Decisions

***REMOVED******REMOVED******REMOVED******REMOVED*** Current Capacity Baseline

Run baseline tests to establish current capacity:

```bash
***REMOVED*** Measure maximum concurrent users before degradation
VUS=10 DURATION=2m npm run test:concurrent   ***REMOVED*** Baseline
VUS=50 DURATION=2m npm run test:concurrent   ***REMOVED*** 5x load
VUS=100 DURATION=2m npm run test:concurrent  ***REMOVED*** 10x load
VUS=200 DURATION=2m npm run test:concurrent  ***REMOVED*** 20x load

***REMOVED*** Find breaking point
***REMOVED*** Example results:
***REMOVED*** 10 VUs:  P95 = 320ms  ✅
***REMOVED*** 50 VUs:  P95 = 450ms  ✅
***REMOVED*** 100 VUs: P95 = 1.8s   ⚠️
***REMOVED*** 200 VUs: P95 = 8.5s   ❌ (exceeds SLO)

***REMOVED*** Conclusion: System capacity is ~75-100 concurrent users
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Connection Pool Sizing

**Formula**: `connections = ((core_count * 2) + effective_spindle_count)`

```python
***REMOVED*** backend/app/db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=20,          ***REMOVED*** Base pool size
    max_overflow=10,       ***REMOVED*** Additional connections under load
    pool_pre_ping=True,    ***REMOVED*** Verify connections before use
    pool_recycle=3600,     ***REMOVED*** Recycle connections hourly
)

***REMOVED*** Total connections available: 20 + 10 = 30
***REMOVED*** Ensure PostgreSQL max_connections > 30
```

**Load Test Validation**:
```bash
***REMOVED*** Test with pool_size=10 (baseline)
***REMOVED*** Test with pool_size=20 (2x)
***REMOVED*** Test with pool_size=40 (4x)

***REMOVED*** Compare P95 latency to find optimal size
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Memory and CPU Requirements per Concurrent User

**Profiling**:
```bash
***REMOVED*** Measure resource usage at different VU counts
VUS=10  k6 run scenarios/concurrent-users.js & docker stats --no-stream
VUS=50  k6 run scenarios/concurrent-users.js & docker stats --no-stream
VUS=100 k6 run scenarios/concurrent-users.js & docker stats --no-stream

***REMOVED*** Example results:
***REMOVED*** 10 VUs:  Backend 512 MB RAM, 25% CPU
***REMOVED*** 50 VUs:  Backend 1.2 GB RAM, 60% CPU
***REMOVED*** 100 VUs: Backend 2.1 GB RAM, 95% CPU ← Near capacity
```

**Recommendations**:
- **Memory**: ~20 MB per concurrent user + 512 MB base
- **CPU**: ~1% per concurrent user (4-core system)
- **Database**: ~50 MB per 10 concurrent users

**Scaling Formula**:
```
For N concurrent users:
- Backend RAM: 512 MB + (N * 20 MB)
- Backend CPU: 4 cores (for 100 users)
- Database RAM: 512 MB + (N * 5 MB)
- Database CPU: 2-4 cores
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Horizontal vs Vertical Scaling

**Vertical Scaling** (increase resources on single instance):
```yaml
***REMOVED*** docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '2'
          memory: 2G
```

**Horizontal Scaling** (add more instances):
```yaml
***REMOVED*** docker-compose.yml
services:
  backend:
    deploy:
      replicas: 3  ***REMOVED*** 3 backend instances
```

**Load Balancing**:
```nginx
***REMOVED*** nginx.conf
upstream backend {
    least_conn;  ***REMOVED*** Send to instance with fewest connections
    server backend-1:8000;
    server backend-2:8000;
    server backend-3:8000;
}
```

**Test Scaled Setup**:
```bash
***REMOVED*** Start 3 backend replicas
docker-compose up -d --scale backend=3

***REMOVED*** Run load test
VUS=150 DURATION=5m npm run test:concurrent

***REMOVED*** Verify load is distributed
docker stats backend-1 backend-2 backend-3
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Capacity Planning Timeline

| User Growth | Action Required | Testing |
|-------------|----------------|---------|
| < 50 users | Current setup sufficient | Monthly load tests |
| 50-100 users | Monitor metrics closely | Weekly load tests |
| 100-200 users | Vertical scaling (4 CPU, 4 GB RAM) | Load test before scaling |
| 200+ users | Horizontal scaling (2-3 replicas) | Nightly load tests |

---

***REMOVED******REMOVED*** Healthcare-Specific Considerations

***REMOVED******REMOVED******REMOVED*** Data Security During Testing

**No Real User Data in Load Tests:**
- ❌ **Never** use production database for load testing
- ❌ **Never** use real user names, personal identifiers
- ✅ Use synthetic test data (`scripts/seed_test_data.py`)
- ✅ Anonymize any data if seeding from production samples

**Test Data Generation**:
```python
***REMOVED*** scripts/seed_test_data.py
def create_test_person(index):
    return Person(
        first_name=f"TestUser{index}",     ***REMOVED*** Not real names
        last_name=f"Resident{index}",
        email=f"test.user{index}@example.com",
        role="RESIDENT",
        ssn=None,  ***REMOVED*** Never include SSNs
        dob=None,  ***REMOVED*** Avoid birthdates
    )
```

***REMOVED******REMOVED******REMOVED*** Audit Logging During Load Tests

Load tests generate significant audit log entries:

```python
***REMOVED*** Disable audit logging for load tests (if appropriate)
***REMOVED*** backend/app/core/config.py
class Settings(BaseSettings):
    ENABLE_AUDIT_LOGGING: bool = True
    LOAD_TEST_MODE: bool = False  ***REMOVED*** Set to True to reduce audit logs

***REMOVED*** Or filter load test activity
if not settings.LOAD_TEST_MODE:
    create_audit_log(user=current_user, action="VIEW_SCHEDULE")
```

**Tag Load Test Traffic**:
```javascript
// load-tests/utils/auth.js
export function getAuthHeaders(token) {
  return {
    'Authorization': `Bearer ${token}`,
    'X-Load-Test': 'true',  // Mark as load test
  };
}
```

**Filter in Backend**:
```python
***REMOVED*** Skip audit logging for load tests
if request.headers.get("X-Load-Test") != "true":
    create_audit_log(...)
```

***REMOVED******REMOVED******REMOVED*** Testing Disaster Recovery Scenarios

**Scenario: Database Failover**
```bash
***REMOVED*** 1. Start load test
VUS=50 DURATION=10m npm run test:concurrent &

***REMOVED*** 2. Simulate database failure (after 2 min)
sleep 120
docker-compose stop db

***REMOVED*** 3. Measure impact (error rate spike)
***REMOVED*** 4. Restart database
docker-compose start db

***REMOVED*** 5. Verify recovery (error rate returns to normal)
```

**Scenario: Redis Failure (Celery Broker)**
```bash
***REMOVED*** 1. Start load test
VUS=30 DURATION=5m npm run test:concurrent &

***REMOVED*** 2. Stop Redis
docker-compose stop redis

***REMOVED*** 3. Verify app remains functional (degraded mode)
***REMOVED*** Background tasks queue, but API still works

***REMOVED*** 4. Restart Redis
docker-compose start redis

***REMOVED*** 5. Verify tasks process
```

**Scenario: High Availability Testing**
```bash
***REMOVED*** Test with load balancer failover
***REMOVED*** 1. Start 3 backend replicas
docker-compose up -d --scale backend=3

***REMOVED*** 2. Start load test
VUS=100 DURATION=10m npm run test:concurrent &

***REMOVED*** 3. Kill one backend instance
docker-compose stop backend-1

***REMOVED*** 4. Verify no user-visible impact (traffic routes to backend-2, backend-3)
***REMOVED*** 5. Restart failed instance
docker-compose start backend-1
```

***REMOVED******REMOVED******REMOVED*** ACGME Compliance Under Load

Critical requirement: ACGME validation must remain accurate under load.

**Test Scenario**:
```javascript
// Verify compliance validation accuracy
import { check } from 'k6';

export default function() {
  // Create assignment that violates 80-hour rule
  const response = createAssignment({
    person_id: 123,
    hours: 85,  // Exceeds limit
  });

  // Verify violation is detected even under load
  check(response, {
    'compliance violation detected': (r) => r.json('acgme_violations').length > 0,
  });
}
```

**Validation**:
- Run concurrent user test
- Verify 100% accuracy of ACGME violation detection
- Check for false positives/negatives
- Ensure no data races in compliance calculations

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Common Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue: k6 Not Found

**Symptoms**: `k6: command not found`

**Solution**:
```bash
***REMOVED*** Install k6 (see Installation section)
brew install k6  ***REMOVED*** macOS
***REMOVED*** or
sudo apt-get install k6  ***REMOVED*** Linux

***REMOVED*** Verify
k6 version
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue: Connection Refused

**Symptoms**: `http_req_failed: 100%`, connection errors

**Solution**:
```bash
***REMOVED*** 1. Verify backend is running
curl http://localhost:8000/health

***REMOVED*** 2. Check Docker Compose status
docker-compose ps

***REMOVED*** 3. View backend logs
docker-compose logs backend

***REMOVED*** 4. Restart services
docker-compose restart backend
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue: Authentication Failures

**Symptoms**: `401 Unauthorized`, login check failures

**Solution**:
```bash
***REMOVED*** 1. Verify test users exist
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.models.person import Person
db = SessionLocal()
users = db.query(Person).filter(Person.email.like('%@example.com')).all()
print([u.email for u in users])
"

***REMOVED*** 2. Create test users
cd backend
python scripts/create_test_users.py

***REMOVED*** 3. Verify credentials in load test
export ADMIN_EMAIL=admin@example.com
export ADMIN_PASSWORD=admin_password_123
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue: Database Connection Errors

**Symptoms**: `sqlalchemy.exc.OperationalError`, connection timeouts

**Solution**:
```bash
***REMOVED*** 1. Check database is running
docker-compose exec db pg_isready -U scheduler

***REMOVED*** 2. Check connection pool size
***REMOVED*** backend/app/db/session.py
pool_size=20,
max_overflow=10,

***REMOVED*** 3. Reduce concurrent VUs if overwhelming database
VUS=10 k6 run scenarios/concurrent-users.js  ***REMOVED*** Instead of VUS=100
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue: High Error Rate (5xx)

**Symptoms**: `http_req_failed > 5%`, 500 Internal Server Error

**Solution**:
```bash
***REMOVED*** 1. Check backend logs for stack traces
docker-compose logs backend --tail=100

***REMOVED*** 2. Check for database errors
docker-compose logs db --tail=50

***REMOVED*** 3. Verify Celery workers are running
docker-compose ps celery-worker

***REMOVED*** 4. Check for resource exhaustion
docker stats --no-stream
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Issue: Inconsistent Results

**Symptoms**: Tests pass sometimes, fail other times

**Solution**:
```bash
***REMOVED*** 1. Run longer tests for better statistical significance
DURATION=10m k6 run scenarios/api-baseline.js

***REMOVED*** 2. Check for background processes affecting results
***REMOVED*** Stop other Docker containers, close browser tabs

***REMOVED*** 3. Use warmup period
k6 run --stage 30s:10 --stage 5m:50 --stage 30s:0 scenarios/concurrent-users.js
***REMOVED***          └─ warmup     └─ test      └─ cooldown

***REMOVED*** 4. Run multiple times and average
for i in {1..5}; do
  k6 run scenarios/api-baseline.js | grep "http_req_duration.*p(95)"
done
```

***REMOVED******REMOVED******REMOVED*** Getting Help

**Check Logs**:
```bash
***REMOVED*** Backend
docker-compose logs backend -f

***REMOVED*** Database
docker-compose logs db -f

***REMOVED*** k6 verbose output
k6 run --http-debug scenarios/api-baseline.js
```

**Enable Debug Mode**:
```bash
***REMOVED*** backend/.env
DEBUG=true

***REMOVED*** Restart backend
docker-compose restart backend
```

**Report Issues**:
- Include k6 output (full summary)
- Include backend logs (errors/warnings)
- Include system specs (CPU, RAM)
- Include test parameters (VUS, DURATION)

---

***REMOVED******REMOVED*** Additional Resources

***REMOVED******REMOVED******REMOVED*** Documentation
- [k6 Documentation](https://k6.io/docs/)
- [k6 Best Practices](https://k6.io/docs/testing-guides/test-best-practices/)
- [HTTP Performance Optimization](https://developer.mozilla.org/en-US/docs/Web/Performance)

***REMOVED******REMOVED******REMOVED*** Tools
- [k6 Cloud](https://k6.io/cloud/) - SaaS load testing platform
- [Grafana k6](https://grafana.com/grafana/dashboards/k6/) - Visualize k6 metrics
- [Artillery](https://www.artillery.io/) - Alternative load testing tool

***REMOVED******REMOVED******REMOVED*** Internal Documentation
- [Prometheus Metrics](./metrics.md)
- [Deployment Guide](./DEPLOYMENT_PROMPT.md)
- [Security Scanning](./SECURITY_SCANNING.md)
- [Backend Architecture](../architecture/backend.md)

---

**Last Updated**: 2025-12-18
**Review Schedule**: Quarterly
**Owner**: DevOps Team
