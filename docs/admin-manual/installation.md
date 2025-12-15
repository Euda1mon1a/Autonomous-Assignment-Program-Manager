# Installation and Deployment Guide

## Overview

This guide provides step-by-step instructions for installing and deploying the Residency Scheduler application. It covers both Docker-based and manual deployment methods.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Deployment (Recommended)](#docker-deployment-recommended)
3. [Manual Deployment](#manual-deployment)
4. [SSL/TLS Configuration](#ssltls-configuration)
5. [Reverse Proxy Setup](#reverse-proxy-setup)
6. [Post-Installation Steps](#post-installation-steps)
7. [Upgrading](#upgrading)
8. [Troubleshooting Installation](#troubleshooting-installation)

---

## Prerequisites

### Hardware Requirements

| Environment | CPU | RAM | Storage |
|-------------|-----|-----|---------|
| Development | 2 cores | 4 GB | 20 GB |
| Production | 4+ cores | 8+ GB | 50+ GB |

### Software Requirements

**For Docker Deployment:**

```bash
# Verify Docker installation
docker --version    # Requires 20.10+
docker compose version  # Requires 2.0+
```

**For Manual Deployment:**

```bash
# Verify software versions
python3 --version   # Requires 3.11+
node --version      # Requires 20+
npm --version       # Requires 10+
psql --version      # Requires 15+
nginx -v            # Requires 1.18+
```

### Network Requirements

| Port | Service | Direction |
|------|---------|-----------|
| 80 | HTTP | Inbound |
| 443 | HTTPS | Inbound |
| 8000 | Backend API | Internal |
| 3000 | Frontend | Internal |
| 5432 | PostgreSQL | Internal |

---

## Docker Deployment (Recommended)

### Step 1: Clone Repository

```bash
# Clone the repository
git clone https://github.com/your-org/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your production values
nano .env
```

Required environment variables:

```bash
# Database password - use a strong, unique password
DB_PASSWORD=<generate-strong-password>

# JWT secret key - generate with: python3 -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=<generate-64-char-secret>

# Application mode
DEBUG=false

# CORS origins - set to your production domain
CORS_ORIGINS=["https://your-domain.com"]

# Frontend API URL
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

### Step 3: Build and Start Services

```bash
# Build containers
docker compose build

# Start all services
docker compose up -d

# Verify services are running
docker compose ps

# Expected output:
# NAME                           STATUS
# residency-scheduler-db         Up (healthy)
# residency-scheduler-backend    Up
# residency-scheduler-frontend   Up
```

### Step 4: Run Database Migrations

```bash
# Execute migrations
docker compose exec backend alembic upgrade head

# Verify migration status
docker compose exec backend alembic current
```

### Step 5: Create Initial Admin User

```bash
# Access backend container shell
docker compose exec backend python

# In Python shell:
>>> from app.db.session import SessionLocal
>>> from app.models.user import User
>>> from app.core.security import get_password_hash
>>>
>>> db = SessionLocal()
>>> admin = User(
...     username="admin",
...     email="admin@your-domain.com",
...     hashed_password=get_password_hash("your-secure-password"),
...     full_name="System Administrator",
...     role="admin",
...     is_active=True
... )
>>> db.add(admin)
>>> db.commit()
>>> exit()
```

### Step 6: Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# View logs
docker compose logs -f
```

---

## Manual Deployment

### Step 1: Install System Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

# Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15

# Install Nginx
sudo apt install nginx

# Install additional dependencies
sudo apt install git build-essential libpq-dev
```

### Step 2: Create Application User

```bash
# Create dedicated application user
sudo useradd -r -s /bin/false -d /opt/residency-scheduler scheduler

# Create application directories
sudo mkdir -p /opt/residency-scheduler
sudo chown scheduler:scheduler /opt/residency-scheduler
```

### Step 3: Configure PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

-- Create database and user
CREATE DATABASE residency_scheduler;
CREATE USER scheduler WITH ENCRYPTED PASSWORD 'your-secure-password';
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;
ALTER DATABASE residency_scheduler OWNER TO scheduler;

-- Enable required extensions
\c residency_scheduler
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\q
```

Configure PostgreSQL authentication in `/etc/postgresql/15/main/pg_hba.conf`:

```
# Add this line for local connections
local   residency_scheduler   scheduler                     md5
host    residency_scheduler   scheduler   127.0.0.1/32     md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

### Step 4: Deploy Backend

```bash
# Clone repository
cd /opt/residency-scheduler
sudo -u scheduler git clone https://github.com/your-org/Autonomous-Assignment-Program-Manager.git .

# Create virtual environment
cd backend
sudo -u scheduler python3.11 -m venv venv
sudo -u scheduler ./venv/bin/pip install --upgrade pip
sudo -u scheduler ./venv/bin/pip install -r requirements.txt

# Create environment file
sudo -u scheduler cat > /opt/residency-scheduler/.env << EOF
DATABASE_URL=postgresql://scheduler:your-secure-password@localhost:5432/residency_scheduler
SECRET_KEY=your-64-char-secret-key
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
EOF

# Run migrations
sudo -u scheduler ./venv/bin/alembic upgrade head
```

### Step 5: Create Backend Service

Create `/etc/systemd/system/residency-backend.service`:

```ini
[Unit]
Description=Residency Scheduler Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=scheduler
Group=scheduler
WorkingDirectory=/opt/residency-scheduler/backend
Environment="PATH=/opt/residency-scheduler/backend/venv/bin"
EnvironmentFile=/opt/residency-scheduler/.env
ExecStart=/opt/residency-scheduler/backend/venv/bin/gunicorn \
    app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 127.0.0.1:8000 \
    --access-logfile /var/log/residency-scheduler/access.log \
    --error-logfile /var/log/residency-scheduler/error.log
Restart=always
RestartSec=5
StandardOutput=append:/var/log/residency-scheduler/backend.log
StandardError=append:/var/log/residency-scheduler/backend-error.log

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Create log directory
sudo mkdir -p /var/log/residency-scheduler
sudo chown scheduler:scheduler /var/log/residency-scheduler

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable residency-backend
sudo systemctl start residency-backend
sudo systemctl status residency-backend
```

### Step 6: Deploy Frontend

```bash
cd /opt/residency-scheduler/frontend

# Install dependencies
sudo -u scheduler npm ci

# Create environment file
sudo -u scheduler cat > .env.local << EOF
NEXT_PUBLIC_API_URL=https://api.your-domain.com
EOF

# Build for production
sudo -u scheduler npm run build

# Install PM2 globally
sudo npm install -g pm2

# Start with PM2
sudo -u scheduler pm2 start npm --name "residency-frontend" -- start
sudo -u scheduler pm2 save

# Configure PM2 startup
pm2 startup systemd -u scheduler --hp /opt/residency-scheduler
```

---

## SSL/TLS Configuration

### Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

# Verify auto-renewal
sudo certbot renew --dry-run

# Check renewal timer
sudo systemctl status certbot.timer
```

### Using Custom Certificates

```bash
# Create certificate directory
sudo mkdir -p /etc/nginx/ssl

# Copy certificates
sudo cp your-certificate.crt /etc/nginx/ssl/
sudo cp your-private.key /etc/nginx/ssl/
sudo chmod 600 /etc/nginx/ssl/your-private.key
```

---

## Reverse Proxy Setup

### Nginx Configuration

Create `/etc/nginx/sites-available/residency-scheduler`:

```nginx
# Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# Upstream definitions
upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

# Main application
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    # Frontend proxy
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 60s;
    }

    # Health check (no auth required)
    location /health {
        proxy_pass http://backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}

# API server
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Rate limiting
    limit_req zone=api_limit burst=20 nodelay;

    # API proxy
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;

        # CORS headers (if needed)
        add_header Access-Control-Allow-Origin "https://your-domain.com" always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;

        if ($request_method = 'OPTIONS') {
            return 204;
        }
    }
}
```

Enable the configuration:

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/residency-scheduler /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Post-Installation Steps

### 1. Verify All Services

```bash
# Check service status
sudo systemctl status residency-backend
sudo systemctl status nginx
pm2 status

# Test endpoints
curl -k https://your-domain.com
curl -k https://api.your-domain.com/health
```

### 2. Configure Firewall

```bash
# Allow necessary ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# Verify rules
sudo ufw status
```

### 3. Set Up Log Rotation

Create `/etc/logrotate.d/residency-scheduler`:

```
/var/log/residency-scheduler/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 scheduler scheduler
    postrotate
        systemctl reload residency-backend 2>/dev/null || true
    endscript
}
```

### 4. Configure Automated Backups

See [Backup & Restore Guide](./backup-restore.md) for complete backup configuration.

---

## Upgrading

### Docker Upgrade Process

```bash
# Pull latest changes
git pull origin main

# Backup database first
docker compose exec db pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

# Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

# Run any new migrations
docker compose exec backend alembic upgrade head

# Verify services
docker compose ps
docker compose logs -f
```

### Manual Upgrade Process

```bash
# Stop services
sudo systemctl stop residency-backend
pm2 stop residency-frontend

# Backup database
pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

# Pull latest code
cd /opt/residency-scheduler
sudo -u scheduler git pull origin main

# Update backend
cd backend
sudo -u scheduler ./venv/bin/pip install -r requirements.txt
sudo -u scheduler ./venv/bin/alembic upgrade head

# Update frontend
cd ../frontend
sudo -u scheduler npm ci
sudo -u scheduler npm run build

# Restart services
sudo systemctl start residency-backend
pm2 start residency-frontend

# Verify
sudo systemctl status residency-backend
pm2 status
```

---

## Troubleshooting Installation

### Common Issues

#### Docker: Container Won't Start

```bash
# Check container logs
docker compose logs backend
docker compose logs db

# Verify environment variables
docker compose config

# Check port conflicts
sudo lsof -i :8000
sudo lsof -i :5432
```

#### Database Connection Failed

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U scheduler -h localhost -d residency_scheduler

# Check pg_hba.conf settings
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep scheduler
```

#### Backend Service Won't Start

```bash
# Check logs
sudo journalctl -u residency-backend -n 50

# Verify virtual environment
/opt/residency-scheduler/backend/venv/bin/python --version

# Test manual start
cd /opt/residency-scheduler/backend
./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

#### SSL Certificate Issues

```bash
# Verify certificate
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Check Nginx SSL configuration
sudo nginx -t
```

#### Permission Denied Errors

```bash
# Fix file ownership
sudo chown -R scheduler:scheduler /opt/residency-scheduler

# Fix log directory permissions
sudo chown -R scheduler:scheduler /var/log/residency-scheduler
sudo chmod 755 /var/log/residency-scheduler
```

---

## Installation Checklist

- [ ] System requirements verified
- [ ] Docker/dependencies installed
- [ ] Repository cloned
- [ ] Environment variables configured
- [ ] Database created and configured
- [ ] Migrations executed
- [ ] Initial admin user created
- [ ] SSL certificates installed
- [ ] Nginx configured
- [ ] Firewall configured
- [ ] Log rotation configured
- [ ] Backup automation set up
- [ ] All services verified running
- [ ] Health endpoints responding

---

*Last Updated: December 2024*
