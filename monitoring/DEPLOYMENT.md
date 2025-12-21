# Monitoring Stack Deployment Guide

## Quick Reference

### Development Deployment
```bash
# Use base configuration with all ports exposed
docker-compose -f docker-compose.monitoring.yml up -d
```

### Production Deployment
```bash
# ALWAYS use the production override to secure ports
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d
```

## Pre-Deployment Checklist

### Security Requirements

- [ ] **Copy and configure `.env` file**
  ```bash
  cp .env.example .env
  nano .env
  ```

- [ ] **Set strong Grafana admin password**
  ```bash
  # Generate secure password
  python -c 'import secrets; print(secrets.token_urlsafe(32))'
  # Add to .env: GRAFANA_ADMIN_PASSWORD=<generated_password>
  ```

- [ ] **Configure alert notification channels**
  - Set SMTP credentials for email alerts
  - Set Slack webhook URL (if using Slack)
  - Set PagerDuty service key (if using PagerDuty)

- [ ] **Verify network configuration**
  - Ensure `app-network` Docker network exists
  - Backend services must be on same network for metrics scraping

### Production-Specific Configuration

- [ ] **Use production override file** (removes port exposure)

- [ ] **Set up reverse proxy** (nginx/Traefik) with:
  - SSL/TLS certificates (Let's Encrypt recommended)
  - Authentication (OAuth2, basic auth, or Grafana's built-in auth)
  - Rate limiting
  - IP allowlisting (if applicable)

- [ ] **Configure monitoring persistence**
  - Verify Docker volumes for data retention
  - Set up backup strategy (see README.md)

## Deployment Steps

### 1. Initial Setup

```bash
# Navigate to monitoring directory
cd monitoring/

# Create .env from template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Deploy Stack

```bash
# PRODUCTION: Deploy with security hardening
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d

# Verify all containers started
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  ps
```

### 3. Verify Health

```bash
# Check all services are healthy
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  ps

# Expected output: All services should show "Up" and "healthy" status
```

### 4. Configure Access

#### Option A: Reverse Proxy (Recommended)

Create nginx configuration for Grafana:

```nginx
upstream grafana {
    server localhost:3000;  # Internal Docker network
}

server {
    listen 443 ssl http2;
    server_name monitoring.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/monitoring.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monitoring.yourdomain.com/privkey.pem;

    # Security headers
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

#### Option B: SSH Tunnel (Admin Access)

```bash
# From your local machine
ssh -L 3001:localhost:3001 user@production-server

# Access Grafana at http://localhost:3001
```

### 5. First Login

```bash
# Access Grafana (via reverse proxy or tunnel)
# URL: https://monitoring.yourdomain.com OR http://localhost:3001

# Default credentials (from .env):
# Username: admin
# Password: <GRAFANA_ADMIN_PASSWORD from .env>

# IMMEDIATELY change default password after first login!
```

### 6. Verify Monitoring

- [ ] Check Prometheus targets: Settings → Data Sources → Prometheus → Explore
- [ ] Verify dashboards load correctly
- [ ] Test alert routing (send test alert)
- [ ] Check log ingestion (Loki data source)

## Post-Deployment

### Monitoring the Monitoring

Set up external health checks for the monitoring stack itself:

```bash
# Add to your uptime monitoring service (UptimeRobot, Pingdom, etc.)
# Endpoint: https://monitoring.yourdomain.com/api/health
```

### Backup Configuration

```bash
# Set up automated backups
# See scripts/backup-monitoring.sh for implementation

# Add to crontab
0 2 * * * /path/to/monitoring/scripts/backup-monitoring.sh
```

### Regular Maintenance

- [ ] **Weekly**: Review alerts and adjust thresholds
- [ ] **Monthly**: Update container images for security patches
- [ ] **Quarterly**: Review and prune old metrics data

## Troubleshooting

### Services Not Starting

```bash
# View logs
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml logs

# Check specific service
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml logs grafana
```

### Cannot Access Grafana

```bash
# Verify container is running
docker ps | grep grafana

# Check if reverse proxy is configured correctly
nginx -t

# Verify DNS resolution
nslookup monitoring.yourdomain.com
```

### Prometheus Not Scraping

```bash
# SSH tunnel to Prometheus
ssh -L 9090:localhost:9090 user@production-server

# Access http://localhost:9090/targets
# Check target status and error messages
```

### Alerts Not Firing

```bash
# Check Alertmanager logs
docker-compose -f docker-compose.monitoring.yml -f docker-compose.monitoring.prod.yml logs alertmanager

# Verify SMTP/Slack/PagerDuty credentials in .env
# Test notification channels in Alertmanager UI
```

## Rollback

```bash
# Stop monitoring stack
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  down

# Data persists in Docker volumes
# Restart to restore
docker-compose \
  -f docker-compose.monitoring.yml \
  -f docker-compose.monitoring.prod.yml \
  up -d
```

## Security Incident Response

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

## Support

- **Documentation**: See [README.md](README.md) for detailed information
- **Architecture**: Review monitoring architecture diagram in README.md
- **Alerts**: Check `prometheus/rules/*.yml` for alert definitions
- **Dashboards**: Located in `grafana/dashboards/` directory

---

**Remember**: In production, ALWAYS use the production override file. Never expose monitoring ports directly to the internet.
