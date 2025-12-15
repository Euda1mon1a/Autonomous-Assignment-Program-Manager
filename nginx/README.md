***REMOVED*** Nginx Reverse Proxy Configuration

This directory contains the nginx reverse proxy configuration for the Residency Scheduler application.

***REMOVED******REMOVED*** Directory Structure

```
nginx/
├── nginx.conf                    ***REMOVED*** Main nginx configuration
├── Dockerfile                    ***REMOVED*** Docker image for nginx
├── docker-compose.nginx.yml      ***REMOVED*** Docker Compose service definitions
├── README.md                     ***REMOVED*** This file
├── conf.d/
│   ├── upstreams.conf           ***REMOVED*** Load balancing upstream definitions
│   ├── default.conf             ***REMOVED*** Main server configuration (HTTPS)
│   └── default-dev.conf.example ***REMOVED*** Development configuration template
├── snippets/
│   ├── ssl-params.conf          ***REMOVED*** SSL/TLS parameters
│   ├── security-headers.conf    ***REMOVED*** Security headers
│   ├── proxy-params.conf        ***REMOVED*** Proxy settings
│   ├── websocket-params.conf    ***REMOVED*** WebSocket proxy settings
│   └── static-cache.conf        ***REMOVED*** Static file caching
├── scripts/
│   ├── init-letsencrypt.sh      ***REMOVED*** Initialize Let's Encrypt certificates
│   ├── renew-certificates.sh    ***REMOVED*** Renew certificates (cron job)
│   └── generate-dhparam.sh      ***REMOVED*** Generate DH parameters
├── ssl/
│   └── .gitkeep                 ***REMOVED*** Placeholder for SSL files
└── certbot/                     ***REMOVED*** Created by init-letsencrypt.sh
    ├── conf/                    ***REMOVED*** Let's Encrypt configuration
    └── www/                     ***REMOVED*** ACME challenge files
```

***REMOVED******REMOVED*** Quick Start

***REMOVED******REMOVED******REMOVED*** Development (No SSL)

1. Copy the development configuration:
   ```bash
   cp nginx/conf.d/default-dev.conf.example nginx/conf.d/default.conf
   ```

2. Start with Docker Compose:
   ```bash
   docker compose -f docker-compose.yml -f nginx/docker-compose.nginx.yml up
   ```

3. Access the application at http://localhost

***REMOVED******REMOVED******REMOVED*** Production (With SSL)

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
   ***REMOVED*** Add to crontab (run twice daily)
   0 3,15 * * * /path/to/nginx/scripts/renew-certificates.sh >> /var/log/certbot-renew.log 2>&1
   ```

***REMOVED******REMOVED*** Features

***REMOVED******REMOVED******REMOVED*** Security

- **TLS 1.2/1.3 Only**: Modern TLS protocols only
- **Strong Cipher Suite**: ECDHE with AES-GCM and ChaCha20-Poly1305
- **HSTS**: HTTP Strict Transport Security enabled
- **Security Headers**: Comprehensive headers including CSP, X-Frame-Options, etc.
- **Rate Limiting**: Protection against brute force and DoS attacks

***REMOVED******REMOVED******REMOVED*** Performance

- **Gzip Compression**: Enabled for text-based content
- **Static File Caching**: Aggressive caching for immutable assets
- **Connection Pooling**: Keepalive connections to upstreams
- **HTTP/2**: Enabled for HTTPS connections

***REMOVED******REMOVED******REMOVED*** Load Balancing

- **Backend Servers**: Least connections algorithm
- **Frontend Servers**: Round-robin distribution
- **WebSocket**: IP hash for sticky sessions
- **Health Checks**: Automatic failure detection and recovery

***REMOVED******REMOVED******REMOVED*** Rate Limits

| Zone | Rate | Purpose |
|------|------|---------|
| `general` | 10 req/s | General pages |
| `api` | 30 req/s | API endpoints |
| `login` | 5 req/min | Authentication (brute force protection) |
| `schedule_gen` | 1 req/10s | Schedule generation (resource protection) |

***REMOVED******REMOVED*** Configuration Reference

***REMOVED******REMOVED******REMOVED*** Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DOMAIN` | Primary domain name | residency-scheduler.example.com |
| `TZ` | Timezone | UTC |

***REMOVED******REMOVED******REMOVED*** Ports

| Port | Protocol | Description |
|------|----------|-------------|
| 80 | HTTP | Redirects to HTTPS / ACME challenges |
| 443 | HTTPS | Main application traffic |

***REMOVED******REMOVED******REMOVED*** Upstream Servers

Configure in `conf.d/upstreams.conf`:

```nginx
upstream backend_servers {
    least_conn;
    server backend:8000 weight=5;
    ***REMOVED*** Add more servers for horizontal scaling
    ***REMOVED*** server backend-2:8000 weight=5;
}
```

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Check nginx Configuration

```bash
docker compose exec nginx nginx -t
```

***REMOVED******REMOVED******REMOVED*** Reload Configuration

```bash
docker compose exec nginx nginx -s reload
```

***REMOVED******REMOVED******REMOVED*** View Logs

```bash
***REMOVED*** Access logs
docker compose logs -f nginx

***REMOVED*** Error logs
docker compose exec nginx tail -f /var/log/nginx/error.log
```

***REMOVED******REMOVED******REMOVED*** SSL Certificate Issues

```bash
***REMOVED*** Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

***REMOVED*** Check certificate expiry
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

***REMOVED******REMOVED******REMOVED*** Rate Limit Issues

If you're being rate limited during testing:

```bash
***REMOVED*** Temporarily increase limits in conf.d/default.conf
limit_req zone=api burst=100 nodelay;
```

***REMOVED******REMOVED*** File Ownership Matrix

| File | Owner | Description |
|------|-------|-------------|
| `nginx.conf` | DevOps | Main configuration - rarely changes |
| `conf.d/upstreams.conf` | DevOps | Load balancing - scale adjustments |
| `conf.d/default.conf` | DevOps | Server blocks - routing changes |
| `snippets/ssl-params.conf` | DevOps | SSL settings - security updates |
| `snippets/security-headers.conf` | DevOps/Security | Security headers |
| `snippets/proxy-params.conf` | DevOps | Proxy settings |
| `snippets/websocket-params.conf` | DevOps | WebSocket config |
| `snippets/static-cache.conf` | DevOps | Caching rules |
| `scripts/*` | DevOps | Automation scripts |
| `Dockerfile` | DevOps | Container image |

***REMOVED******REMOVED*** Security Considerations

1. **Never commit secrets**: SSL keys, certificates, or passwords
2. **Regularly update**: Keep nginx image and certbot updated
3. **Monitor logs**: Watch for suspicious patterns
4. **Test changes**: Use `nginx -t` before reloading
5. **Backup certificates**: Store Let's Encrypt credentials safely

***REMOVED******REMOVED*** Contributing

When modifying nginx configuration:

1. Test locally with development configuration
2. Validate syntax with `nginx -t`
3. Test SSL with online tools (SSL Labs)
4. Document any rate limit changes
5. Update this README if adding new features
