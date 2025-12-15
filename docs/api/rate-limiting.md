# Rate Limiting

The Residency Scheduler API implements rate limiting to ensure fair usage and protect against abuse.

## Overview

Rate limiting restricts the number of API requests a client can make within a specified time window. When limits are exceeded, the API returns a `429 Too Many Requests` response.

## Rate Limits

### Default Limits

| Limit Type | Requests | Time Window | Description |
|------------|----------|-------------|-------------|
| Per IP | 100 | 1 minute | Anonymous/unauthenticated requests |
| Per User | 1,000 | 1 hour | Authenticated user requests |
| Burst | 20 | 10 seconds | Short burst protection |

### Endpoint-Specific Limits

Some endpoints have additional restrictions due to computational cost:

| Endpoint | Limit | Window | Notes |
|----------|-------|--------|-------|
| `POST /api/schedule/generate` | 10 | 1 hour | Schedule generation is resource-intensive |
| `POST /api/auth/login` | 5 | 1 minute | Brute force protection |
| `POST /api/auth/register` | 3 | 1 hour | Registration abuse prevention |
| `GET /api/export/*` | 20 | 1 hour | Export operations |

## Rate Limit Headers

Every API response includes headers indicating the current rate limit status:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
X-RateLimit-Window: 60
```

### Header Descriptions

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum number of requests allowed in the current window |
| `X-RateLimit-Remaining` | Number of requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp (seconds) when the rate limit window resets |
| `X-RateLimit-Window` | Duration of the rate limit window in seconds |

## Rate Limit Exceeded Response

When rate limits are exceeded:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067200

{
  "detail": "Rate limit exceeded. Please retry after 45 seconds."
}
```

### Retry-After Header

The `Retry-After` header indicates how many seconds to wait before retrying:

```http
Retry-After: 45
```

## Client Implementation

### Python Example

```python
import time
import requests

class RateLimitedClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.session = requests.Session()
        if token:
            self.session.headers['Authorization'] = f'Bearer {token}'

    def request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"

        while True:
            response = self.session.request(method, url, **kwargs)

            # Check rate limit headers
            remaining = int(response.headers.get('X-RateLimit-Remaining', 100))
            reset_time = int(response.headers.get('X-RateLimit-Reset', 0))

            if response.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(response.headers.get('Retry-After', 60))
                print(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                continue

            # Proactive throttling when nearing limit
            if remaining < 10:
                wait_time = max(0, reset_time - time.time()) / remaining
                time.sleep(wait_time)

            return response

# Usage
client = RateLimitedClient('http://localhost:8000', token='your-token')
response = client.request('GET', '/api/people')
```

### JavaScript Example

```javascript
class RateLimitedClient {
  constructor(baseUrl, token = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  async request(method, path, options = {}) {
    const url = `${this.baseUrl}${path}`;
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    while (true) {
      const response = await fetch(url, {
        method,
        headers,
        ...options,
      });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
        console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
      }

      // Log rate limit status
      const remaining = response.headers.get('X-RateLimit-Remaining');
      const limit = response.headers.get('X-RateLimit-Limit');
      console.log(`Rate limit: ${remaining}/${limit} remaining`);

      return response;
    }
  }
}

// Usage
const client = new RateLimitedClient('http://localhost:8000', 'your-token');
const response = await client.request('GET', '/api/people');
const data = await response.json();
```

### cURL with Rate Limit Handling

```bash
#!/bin/bash

API_BASE="http://localhost:8000"
MAX_RETRIES=3

api_request() {
    local method=$1
    local path=$2
    local retries=0

    while [ $retries -lt $MAX_RETRIES ]; do
        response=$(curl -s -w "\n%{http_code}" -X "$method" \
            -H "Authorization: Bearer $TOKEN" \
            "$API_BASE$path")

        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')

        if [ "$http_code" = "429" ]; then
            retry_after=$(echo "$body" | jq -r '.detail' | grep -oP '\d+')
            echo "Rate limited. Waiting ${retry_after:-60} seconds..."
            sleep "${retry_after:-60}"
            ((retries++))
            continue
        fi

        echo "$body"
        return 0
    done

    echo "Max retries exceeded"
    return 1
}

# Usage
api_request GET /api/people
```

## Best Practices

### 1. Implement Exponential Backoff

When hitting rate limits, use exponential backoff:

```python
def exponential_backoff(attempt, base_delay=1, max_delay=60):
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter
```

### 2. Monitor Rate Limit Headers

Always check `X-RateLimit-Remaining` and slow down proactively:

```python
if remaining < limit * 0.1:  # Less than 10% remaining
    # Slow down requests
    time.sleep(1)
```

### 3. Cache Responses

Reduce API calls by caching responses where appropriate:

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_people(last_updated=None):
    # Cache expires every 5 minutes
    cache_key = datetime.now().replace(second=0, microsecond=0)
    cache_key = cache_key - timedelta(minutes=cache_key.minute % 5)
    return api_request('GET', '/api/people')
```

### 4. Batch Operations

When possible, use batch endpoints instead of multiple individual requests:

```bash
# Instead of multiple individual assignment creations
# Use bulk operations when available
curl -X DELETE "http://localhost:8000/api/assignments?start_date=2024-01-01&end_date=2024-01-31"
```

### 5. Use Webhooks

For real-time updates, consider webhooks instead of polling:

```python
# Instead of polling every minute
while True:
    check_schedule_updates()
    time.sleep(60)

# Subscribe to webhooks (when available)
subscribe_to_updates(callback_url)
```

## Rate Limiting Tiers

Different subscription tiers may have different limits:

| Tier | Per Minute | Per Hour | Schedule Generation |
|------|------------|----------|---------------------|
| Free | 60 | 500 | 5/hour |
| Standard | 100 | 1,000 | 10/hour |
| Premium | 300 | 5,000 | 50/hour |
| Enterprise | Custom | Custom | Custom |

*Note: Contact your administrator for tier information.*

## Troubleshooting

### Consistently Hitting Rate Limits

1. **Review request patterns**: Identify unnecessary repeated calls
2. **Implement caching**: Cache static or slowly-changing data
3. **Use batch endpoints**: Combine multiple operations
4. **Optimize polling frequency**: Reduce polling intervals
5. **Contact support**: Request limit increase if needed

### Sudden Rate Limit Errors

1. **Check for loops**: Ensure no infinite loops in code
2. **Review error handling**: Retries shouldn't create cascading requests
3. **Check shared IP**: Multiple users sharing IP may hit limits
4. **Review third-party integrations**: Other services may be consuming limits

## Monitoring

Monitor your rate limit usage:

```python
import logging

def log_rate_limit_status(response):
    limit = response.headers.get('X-RateLimit-Limit')
    remaining = response.headers.get('X-RateLimit-Remaining')
    reset = response.headers.get('X-RateLimit-Reset')

    usage_percent = (1 - int(remaining) / int(limit)) * 100

    if usage_percent > 80:
        logging.warning(f"Rate limit usage high: {usage_percent:.1f}%")
    elif usage_percent > 50:
        logging.info(f"Rate limit usage: {usage_percent:.1f}%")
```

---

*See also: [Error Handling](./errors.md) for 429 error details*
