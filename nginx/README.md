# Nginx Reverse Proxy Configuration

This directory contains the nginx reverse proxy configuration for the Residency Scheduler application.

## Directory Structure

```
nginx/
├── nginx.conf                    # Main nginx configuration
├── Dockerfile                    # Docker image for nginx
├── docker-compose.nginx.yml      # Docker Compose service definitions
├── README.md                     # This file
├── conf.d/
│   ├── upstreams.conf           # Load balancing upstream definitions
│   ├── default.conf             # Main server configuration (HTTPS)
│   ├── load-testing.conf        # Load testing configuration
│   └── default-dev.conf.example # Development configuration template
├── snippets/
│   ├── ssl-params.conf          # SSL/TLS parameters
│   ├── security-headers.conf    # Security headers
│   ├── proxy-params.conf        # Proxy settings
│   ├── websocket-params.conf    # WebSocket proxy settings
│   ├── static-cache.conf        # Static file caching
│   └── loadtest-locations.conf  # Load testing location blocks
├── scripts/
│   ├── init-letsencrypt.sh      # Initialize Let's Encrypt certificates
│   ├── renew-certificates.sh    # Renew certificates (cron job)
│   └── generate-dhparam.sh      # Generate DH parameters
├── ssl/
│   └── .gitkeep                 # Placeholder for SSL files
└── certbot/                     # Created by init-letsencrypt.sh
    ├── conf/                    # Let's Encrypt configuration
    └── www/                     # ACME challenge files
```

## Quick Start

### Development (No SSL)

1. Copy the development configuration:
   ```bash
   cp nginx/conf.d/default-dev.conf.example nginx/conf.d/default.conf
   ```

2. Start with Docker Compose:
   ```bash
   docker compose -f docker-compose.yml -f nginx/docker-compose.nginx.yml up
   ```

3. Access the application at http://localhost

### Production (With SSL)

1. **Generate DH Parameters** (one-time setup):
   ```bash
   chmod +x nginx/scripts/*.sh
   ./nginx/scripts/generate-dhparam.sh
   ```

2. **Update Domain Configuration**:
   Edit `nginx/conf.d/default.conf` and replace `residency-scheduler.example.com` with your domain.

3. **Initialize SSL Certificates**:
   ```bash
   ./nginx/scripts/init-letsencrypt.sh your-domain.com admin@your-domain.com
   ```

4. **Start Services**:
   ```bash
   docker compose -f docker-compose.yml -f nginx/docker-compose.nginx.yml up -d
   ```

5. **Set Up Certificate Renewal** (cron job):
   ```bash
   # Add to crontab (run twice daily)
   0 3,15 * * * /path/to/nginx/scripts/renew-certificates.sh >> /var/log/certbot-renew.log 2>&1
   ```

## Features

### Security

- **TLS 1.2/1.3 Only**: Modern TLS protocols only
- **Strong Cipher Suite**: ECDHE with AES-GCM and ChaCha20-Poly1305
- **HSTS**: HTTP Strict Transport Security enabled
- **Security Headers**: Comprehensive headers including CSP, X-Frame-Options, etc.
- **Rate Limiting**: Protection against brute force and DoS attacks

### Performance

- **Gzip Compression**: Enabled for text-based content
- **Static File Caching**: Aggressive caching for immutable assets
- **Connection Pooling**: Keepalive connections to upstreams
- **HTTP/2**: Enabled for HTTPS connections

### Load Balancing

- **Backend Servers**: Least connections algorithm
- **Frontend Servers**: Round-robin distribution
- **WebSocket**: IP hash for sticky sessions
- **Health Checks**: Automatic failure detection and recovery

### Rate Limits

| Zone | Rate | Purpose |
|------|------|---------|
| `general` | 10 req/s | General pages |
| `api` | 30 req/s | API endpoints |
| `login` | 5 req/min | Authentication (brute force protection) |
| `schedule_gen` | 1 req/10s | Schedule generation (resource protection) |

### Load Testing Support

The nginx configuration includes dedicated support for authorized load testing with relaxed rate limits and enhanced connection pooling.

**Features:**
- **Header-based authentication**: Requires `X-Load-Test-Key` header
- **IP whitelisting**: Restricted to internal networks and CI/CD servers
- **Relaxed rate limits**: 100 req/s for load test endpoints (vs 30 req/s normal)
- **Enhanced connection pooling**: 100 keepalive connections with 10,000 requests/connection
- **Detailed logging**: JSON format with timing metrics for performance analysis

**Setup:**

1. **Configure load test secret**:
   ```bash
   # Generate secure key
   python -c 'import secrets; print(secrets.token_urlsafe(32))'

   # Edit nginx/conf.d/load-testing.conf
   # Replace YOUR_LOAD_TEST_SECRET_KEY with generated key
   ```

2. **Add CI/CD server IPs** (edit `nginx/conf.d/load-testing.conf`):
   ```nginx
   geo $load_test_whitelist {
       default 0;
       # Add your CI/CD server IPs
       203.0.113.0/24 1;    # Jenkins/GitLab CI
   }
   ```

3. **Enable load test locations** (edit `nginx/conf.d/default.conf`):
   ```nginx
   server {
       ...
       # Add this line inside the server block
       include /etc/nginx/snippets/loadtest-locations.conf;
       ...
   }
   ```

**Usage:**

```bash
# Example curl request
curl -H "X-Load-Test-Key: YOUR_SECRET" \
     http://localhost/api/loadtest/schedule/list

# Example K6 load test
import http from 'k6/http';
export default function() {
  const params = {
    headers: { 'X-Load-Test-Key': 'YOUR_SECRET' }
  };
  http.get('http://localhost/api/loadtest/persons', params);
}
```

**Load Test Rate Limits:**

| Zone | Rate | Purpose |
|------|------|---------|
| `loadtest_general` | 50 req/s | General load test endpoints |
| `loadtest_api` | 100 req/s | API load testing |
| `loadtest_schedule` | 10 req/min | Schedule generation testing |

**Monitoring:**

```bash
# View load test logs
tail -f /var/log/nginx/loadtest.log

# Check nginx status
curl http://localhost/nginx_status

# Monitor backend metrics during load test
curl http://localhost/api/loadtest/metrics
```

**Security Checklist:**
- ✓ Load test secret key is NOT the default value
- ✓ IP whitelist includes ONLY trusted networks
- ✓ Load test endpoints are NOT exposed to public internet
- ✓ Firewall rules prevent external access to `/api/loadtest/*` routes
- ✓ Load test key is stored in environment variables, not in code

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOMAIN` | Primary domain name | residency-scheduler.example.com |
| `TZ` | Timezone | UTC |

### Ports

| Port | Protocol | Description |
|------|----------|-------------|
| 80 | HTTP | Redirects to HTTPS / ACME challenges |
| 443 | HTTPS | Main application traffic |

### Upstream Servers

Configure in `conf.d/upstreams.conf`:

```nginx
upstream backend_servers {
    least_conn;
    server backend:8000 weight=5;
    # Add more servers for horizontal scaling
    # server backend-2:8000 weight=5;
}
```

## Troubleshooting

### Check nginx Configuration

```bash
docker compose exec nginx nginx -t
```

### Reload Configuration

```bash
docker compose exec nginx nginx -s reload
```

### View Logs

```bash
# Access logs
docker compose logs -f nginx

# Error logs
docker compose exec nginx tail -f /var/log/nginx/error.log
```

### SSL Certificate Issues

```bash
# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check certificate expiry
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Rate Limit Issues

If you're being rate limited during testing:

```bash
# Temporarily increase limits in conf.d/default.conf
limit_req zone=api burst=100 nodelay;
```

## File Ownership Matrix

| File | Owner | Description |
|------|-------|-------------|
| `nginx.conf` | DevOps | Main configuration - rarely changes |
| `conf.d/upstreams.conf` | DevOps | Load balancing - scale adjustments |
| `conf.d/default.conf` | DevOps | Server blocks - routing changes |
| `conf.d/load-testing.conf` | DevOps/QA | Load testing configuration |
| `snippets/ssl-params.conf` | DevOps | SSL settings - security updates |
| `snippets/security-headers.conf` | DevOps/Security | Security headers |
| `snippets/proxy-params.conf` | DevOps | Proxy settings |
| `snippets/websocket-params.conf` | DevOps | WebSocket config |
| `snippets/static-cache.conf` | DevOps | Caching rules |
| `snippets/loadtest-locations.conf` | DevOps/QA | Load testing locations |
| `scripts/*` | DevOps | Automation scripts |
| `Dockerfile` | DevOps | Container image |

## Security Considerations

1. **Never commit secrets**: SSL keys, certificates, or passwords
2. **Regularly update**: Keep nginx image and certbot updated
3. **Monitor logs**: Watch for suspicious patterns
4. **Test changes**: Use `nginx -t` before reloading
5. **Backup certificates**: Store Let's Encrypt credentials safely

## Contributing

When modifying nginx configuration:

1. Test locally with development configuration
2. Validate syntax with `nginx -t`
3. Test SSL with online tools (SSL Labs)
4. Document any rate limit changes
5. Update this README if adding new features
