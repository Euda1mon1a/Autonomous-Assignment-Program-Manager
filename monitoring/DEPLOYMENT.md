***REMOVED*** Monitoring Stack Deployment Guide

***REMOVED******REMOVED*** Quick Reference

***REMOVED******REMOVED******REMOVED*** Development Deployment
```bash
***REMOVED*** Use base configuration with all ports exposed
docker-compose -f docker-compose.monitoring.yml up -d
```

***REMOVED******REMOVED******REMOVED*** Production Deployment
```bash
***REMOVED*** ALWAYS use the production override to secure ports
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d
```

***REMOVED******REMOVED*** Pre-Deployment Checklist

***REMOVED******REMOVED******REMOVED*** Security Requirements

- [ ] **Copy and configure `.env` file**
  ```bash
  cp .env.example .env
  nano .env
  ```

- [ ] **Set strong Grafana admin password**
  ```bash
  ***REMOVED*** Generate secure password
  python -c 'import secrets; print(secrets.token_urlsafe(32))'
  ***REMOVED*** Add to .env: GRAFANA_ADMIN_PASSWORD=<generated_password>
  ```

- [ ] **Configure alert notification channels**
  - Set SMTP credentials for email alerts
  - Set Slack webhook URL (if using Slack)
  - Set PagerDuty service key (if using PagerDuty)

- [ ] **Verify network configuration**
  - Ensure `app-network` Docker network exists
  - Backend services must be on same network for metrics scraping

***REMOVED******REMOVED******REMOVED*** Production-Specific Configuration

- [ ] **Use production override file** (removes port exposure)

- [ ] **Set up reverse proxy** (nginx/Traefik) with:
  - SSL/TLS certificates (Let's Encrypt recommended)
  - Authentication (OAuth2, basic auth, or Grafana's built-in auth)
  - Rate limiting
  - IP allowlisting (if applicable)

- [ ] **Configure monitoring persistence**
  - Verify Docker volumes for data retention
  - Set up backup strategy (see README.md)

***REMOVED******REMOVED*** Deployment Steps

***REMOVED******REMOVED******REMOVED*** 1. Initial Setup

```bash
***REMOVED*** Navigate to monitoring directory
cd monitoring/

***REMOVED*** Create .env from template
cp .env.example .env

***REMOVED*** Edit configuration
nano .env
```

***REMOVED******REMOVED******REMOVED*** 2. Deploy Stack

```bash
***REMOVED*** PRODUCTION: Deploy with security hardening
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d

***REMOVED*** Verify all containers started
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  ps
```

***REMOVED******REMOVED******REMOVED*** 3. Verify Health

```bash
***REMOVED*** Check all services are healthy
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  ps

***REMOVED*** Expected output: All services should show "Up" and "healthy" status
```

***REMOVED******REMOVED******REMOVED*** 4. Configure Access

***REMOVED******REMOVED******REMOVED******REMOVED*** Option A: Reverse Proxy (Recommended)

Create nginx configuration for Grafana:

```nginx
upstream grafana {
    server localhost:3000;  ***REMOVED*** Internal Docker network
}

server {
    listen 443 ssl http2;
    server_name monitoring.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/monitoring.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monitoring.yourdomain.com/privkey.pem;

    ***REMOVED*** Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    location / {
        proxy_pass http://grafana;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Option B: SSH Tunnel (Admin Access)

```bash
***REMOVED*** From your local machine
ssh -L 3001:localhost:3001 user@production-server

***REMOVED*** Access Grafana at http://localhost:3001
```

***REMOVED******REMOVED******REMOVED*** 5. First Login

```bash
***REMOVED*** Access Grafana (via reverse proxy or tunnel)
***REMOVED*** URL: https://monitoring.yourdomain.com OR http://localhost:3001

***REMOVED*** Default credentials (from .env):
***REMOVED*** Username: admin
***REMOVED*** Password: <GRAFANA_ADMIN_PASSWORD from .env>

***REMOVED*** IMMEDIATELY change default password after first login!
```

***REMOVED******REMOVED******REMOVED*** 6. Verify Monitoring

- [ ] Check Prometheus targets: Settings → Data Sources → Prometheus → Explore
- [ ] Verify dashboards load correctly
- [ ] Test alert routing (send test alert)
- [ ] Check log ingestion (Loki data source)

***REMOVED******REMOVED*** Post-Deployment

***REMOVED******REMOVED******REMOVED*** Monitoring the Monitoring

Set up external health checks for the monitoring stack itself:

```bash
***REMOVED*** Add to your uptime monitoring service (UptimeRobot, Pingdom, etc.)
***REMOVED*** Endpoint: https://monitoring.yourdomain.com/api/health
```

***REMOVED******REMOVED******REMOVED*** Backup Configuration

```bash
***REMOVED*** Set up automated backups
***REMOVED*** See scripts/backup-monitoring.sh for implementation

***REMOVED*** Add to crontab
0 2 * * * /path/to/monitoring/scripts/backup-monitoring.sh
```

***REMOVED******REMOVED******REMOVED*** Regular Maintenance

- [ ] **Weekly**: Review alerts and adjust thresholds
- [ ] **Monthly**: Update container images for security patches
- [ ] **Quarterly**: Review and prune old metrics data

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Services Not Starting

```bash
***REMOVED*** View logs
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml logs

***REMOVED*** Check specific service
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml logs grafana
```

***REMOVED******REMOVED******REMOVED*** Cannot Access Grafana

```bash
***REMOVED*** Verify container is running
docker ps | grep grafana

***REMOVED*** Check if reverse proxy is configured correctly
nginx -t

***REMOVED*** Verify DNS resolution
nslookup monitoring.yourdomain.com
```

***REMOVED******REMOVED******REMOVED*** Prometheus Not Scraping

```bash
***REMOVED*** SSH tunnel to Prometheus
ssh -L 9090:localhost:9090 user@production-server

***REMOVED*** Access http://localhost:9090/targets
***REMOVED*** Check target status and error messages
```

***REMOVED******REMOVED******REMOVED*** Alerts Not Firing

```bash
***REMOVED*** Check Alertmanager logs
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml logs alertmanager

***REMOVED*** Verify SMTP/Slack/PagerDuty credentials in .env
***REMOVED*** Test notification channels in Alertmanager UI
```

***REMOVED******REMOVED*** Rollback

```bash
***REMOVED*** Stop monitoring stack
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  down

***REMOVED*** Data persists in Docker volumes
***REMOVED*** Restart to restore
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d
```

***REMOVED******REMOVED*** Security Incident Response

If monitoring ports are accidentally exposed:

1. **Immediately stop the stack**
   ```bash
   docker-compose -f docker-compose.monitoring.yml down
   ```

2. **Redeploy with production override**
   ```bash
   docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml up -d
   ```

3. **Review access logs** for unauthorized access
   ```bash
   docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml logs grafana | grep -i login
   ```

4. **Rotate credentials**
   - Change Grafana admin password
   - Update .env with new passwords
   - Restart stack

***REMOVED******REMOVED*** Support

- **Documentation**: See [README.md](README.md) for detailed information
- **Architecture**: Review monitoring architecture diagram in README.md
- **Alerts**: Check `prometheus/rules/*.yml` for alert definitions
- **Dashboards**: Located in `grafana/dashboards/` directory

---

**Remember**: In production, ALWAYS use the production override file. Never expose monitoring ports directly to the internet.
