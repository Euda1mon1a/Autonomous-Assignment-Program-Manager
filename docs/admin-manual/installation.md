***REMOVED*** Installation and Deployment Guide

***REMOVED******REMOVED*** Overview

This guide provides step-by-step instructions for installing and deploying the Residency Scheduler application. It covers both Docker-based and manual deployment methods.

***REMOVED******REMOVED*** Table of Contents

1. [Prerequisites](***REMOVED***prerequisites)
2. [Docker Deployment (Recommended)](***REMOVED***docker-deployment-recommended)
3. [Manual Deployment](***REMOVED***manual-deployment)
4. [SSL/TLS Configuration](***REMOVED***ssltls-configuration)
5. [Reverse Proxy Setup](***REMOVED***reverse-proxy-setup)
6. [Post-Installation Steps](***REMOVED***post-installation-steps)
7. [Upgrading](***REMOVED***upgrading)
8. [Troubleshooting Installation](***REMOVED***troubleshooting-installation)

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** Hardware Requirements

| Environment | CPU | RAM | Storage |
|-------------|-----|-----|---------|
| Development | 2 cores | 4 GB | 20 GB |
| Production | 4+ cores | 8+ GB | 50+ GB |

***REMOVED******REMOVED******REMOVED*** Software Requirements

**For Docker Deployment:**

```bash
***REMOVED*** Verify Docker installation
docker --version    ***REMOVED*** Requires 20.10+
docker compose version  ***REMOVED*** Requires 2.0+
```

**For Manual Deployment:**

```bash
***REMOVED*** Verify software versions
python3 --version   ***REMOVED*** Requires 3.11+
node --version      ***REMOVED*** Requires 20+
npm --version       ***REMOVED*** Requires 10+
psql --version      ***REMOVED*** Requires 15+
nginx -v            ***REMOVED*** Requires 1.18+
```

***REMOVED******REMOVED******REMOVED*** Network Requirements

| Port | Service | Direction |
|------|---------|-----------|
| 80 | HTTP | Inbound |
| 443 | HTTPS | Inbound |
| 8000 | Backend API | Internal |
| 3000 | Frontend | Internal |
| 5432 | PostgreSQL | Internal |

---

***REMOVED******REMOVED*** Docker Deployment (Recommended)

***REMOVED******REMOVED******REMOVED*** Step 1: Clone Repository

```bash
***REMOVED*** Clone the repository
git clone https://github.com/your-org/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager
```

***REMOVED******REMOVED******REMOVED*** Step 2: Configure Environment

```bash
***REMOVED*** Copy example environment file
cp .env.example .env

***REMOVED*** Edit with your production values
nano .env
```

Required environment variables:

```bash
***REMOVED*** Database password - use a strong, unique password
DB_PASSWORD=<generate-strong-password>

***REMOVED*** JWT secret key - generate with: python3 -c "import secrets; print(secrets.token_urlsafe(64))"
SECRET_KEY=<generate-64-char-secret>

***REMOVED*** Application mode
DEBUG=false

***REMOVED*** CORS origins - set to your production domain
CORS_ORIGINS=["https://your-domain.com"]

***REMOVED*** Frontend API URL
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

***REMOVED******REMOVED******REMOVED*** Step 3: Build and Start Services

```bash
***REMOVED*** Build containers
docker compose build

***REMOVED*** Start all services
docker compose up -d

***REMOVED*** Verify services are running
docker compose ps

***REMOVED*** Expected output:
***REMOVED*** NAME                           STATUS
***REMOVED*** residency-scheduler-db         Up (healthy)
***REMOVED*** residency-scheduler-backend    Up
***REMOVED*** residency-scheduler-frontend   Up
```

***REMOVED******REMOVED******REMOVED*** Step 4: Run Database Migrations

```bash
***REMOVED*** Execute migrations
docker compose exec backend alembic upgrade head

***REMOVED*** Verify migration status
docker compose exec backend alembic current
```

***REMOVED******REMOVED******REMOVED*** Step 5: Create Initial Admin User

```bash
***REMOVED*** Access backend container shell
docker compose exec backend python

***REMOVED*** In Python shell:
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

***REMOVED******REMOVED******REMOVED*** Step 6: Verify Installation

```bash
***REMOVED*** Check backend health
curl http://localhost:8000/health

***REMOVED*** Check frontend
curl http://localhost:3000

***REMOVED*** View logs
docker compose logs -f
```

---

***REMOVED******REMOVED*** Manual Deployment

***REMOVED******REMOVED******REMOVED*** Step 1: Install System Dependencies

```bash
***REMOVED*** Update system packages
sudo apt update && sudo apt upgrade -y

***REMOVED*** Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

***REMOVED*** Install Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs

***REMOVED*** Install PostgreSQL 15
sudo apt install postgresql-15 postgresql-contrib-15

***REMOVED*** Install Nginx
sudo apt install nginx

***REMOVED*** Install additional dependencies
sudo apt install git build-essential libpq-dev
```

***REMOVED******REMOVED******REMOVED*** Step 2: Create Application User

```bash
***REMOVED*** Create dedicated application user
sudo useradd -r -s /bin/false -d /opt/residency-scheduler scheduler

***REMOVED*** Create application directories
sudo mkdir -p /opt/residency-scheduler
sudo chown scheduler:scheduler /opt/residency-scheduler
```

***REMOVED******REMOVED******REMOVED*** Step 3: Configure PostgreSQL

```bash
***REMOVED*** Switch to postgres user
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
***REMOVED*** Add this line for local connections
local   residency_scheduler   scheduler                     md5
host    residency_scheduler   scheduler   127.0.0.1/32     md5
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

***REMOVED******REMOVED******REMOVED*** Step 4: Deploy Backend

```bash
***REMOVED*** Clone repository
cd /opt/residency-scheduler
sudo -u scheduler git clone https://github.com/your-org/Autonomous-Assignment-Program-Manager.git .

***REMOVED*** Create virtual environment
cd backend
sudo -u scheduler python3.11 -m venv venv
sudo -u scheduler ./venv/bin/pip install --upgrade pip
sudo -u scheduler ./venv/bin/pip install -r requirements.txt

***REMOVED*** Create environment file
sudo -u scheduler cat > /opt/residency-scheduler/.env << EOF
DATABASE_URL=postgresql://scheduler:your-secure-password@localhost:5432/residency_scheduler
SECRET_KEY=your-64-char-secret-key
DEBUG=false
CORS_ORIGINS=["https://your-domain.com"]
EOF

***REMOVED*** Run migrations
sudo -u scheduler ./venv/bin/alembic upgrade head
```

***REMOVED******REMOVED******REMOVED*** Step 5: Create Backend Service

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
***REMOVED*** Create log directory
sudo mkdir -p /var/log/residency-scheduler
sudo chown scheduler:scheduler /var/log/residency-scheduler

***REMOVED*** Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable residency-backend
sudo systemctl start residency-backend
sudo systemctl status residency-backend
```

***REMOVED******REMOVED******REMOVED*** Step 6: Deploy Frontend

```bash
cd /opt/residency-scheduler/frontend

***REMOVED*** Install dependencies
sudo -u scheduler npm ci

***REMOVED*** Create environment file
sudo -u scheduler cat > .env.local << EOF
NEXT_PUBLIC_API_URL=https://api.your-domain.com
EOF

***REMOVED*** Build for production
sudo -u scheduler npm run build

***REMOVED*** Install PM2 globally
sudo npm install -g pm2

***REMOVED*** Start with PM2
sudo -u scheduler pm2 start npm --name "residency-frontend" -- start
sudo -u scheduler pm2 save

***REMOVED*** Configure PM2 startup
pm2 startup systemd -u scheduler --hp /opt/residency-scheduler
```

---

***REMOVED******REMOVED*** SSL/TLS Configuration

***REMOVED******REMOVED******REMOVED*** Using Let's Encrypt (Recommended)

```bash
***REMOVED*** Install Certbot
sudo apt install certbot python3-certbot-nginx

***REMOVED*** Obtain certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

***REMOVED*** Verify auto-renewal
sudo certbot renew --dry-run

***REMOVED*** Check renewal timer
sudo systemctl status certbot.timer
```

***REMOVED******REMOVED******REMOVED*** Using Custom Certificates

```bash
***REMOVED*** Create certificate directory
sudo mkdir -p /etc/nginx/ssl

***REMOVED*** Copy certificates
sudo cp your-certificate.crt /etc/nginx/ssl/
sudo cp your-private.key /etc/nginx/ssl/
sudo chmod 600 /etc/nginx/ssl/your-private.key
```

---

***REMOVED******REMOVED*** Reverse Proxy Setup

***REMOVED******REMOVED******REMOVED*** Nginx Configuration

Create `/etc/nginx/sites-available/residency-scheduler`:

```nginx
***REMOVED*** Rate limiting zone
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

***REMOVED*** Upstream definitions
upstream frontend {
    server 127.0.0.1:3000;
    keepalive 32;
}

upstream backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

***REMOVED*** HTTP to HTTPS redirect
server {
    listen 80;
    server_name your-domain.com api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

***REMOVED*** Main application
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ***REMOVED*** SSL configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    ***REMOVED*** Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';" always;

    ***REMOVED*** Frontend proxy
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

    ***REMOVED*** Health check (no auth required)
    location /health {
        proxy_pass http://backend/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}

***REMOVED*** API server
server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    ***REMOVED*** Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    ***REMOVED*** Rate limiting
    limit_req zone=api_limit burst=20 nodelay;

    ***REMOVED*** API proxy
    location / {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;

        ***REMOVED*** CORS headers (if needed)
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
***REMOVED*** Enable site
sudo ln -s /etc/nginx/sites-available/residency-scheduler /etc/nginx/sites-enabled/

***REMOVED*** Remove default site
sudo rm /etc/nginx/sites-enabled/default

***REMOVED*** Test configuration
sudo nginx -t

***REMOVED*** Reload Nginx
sudo systemctl reload nginx
```

---

***REMOVED******REMOVED*** Post-Installation Steps

***REMOVED******REMOVED******REMOVED*** 1. Verify All Services

```bash
***REMOVED*** Check service status
sudo systemctl status residency-backend
sudo systemctl status nginx
pm2 status

***REMOVED*** Test endpoints
curl -k https://your-domain.com
curl -k https://api.your-domain.com/health
```

***REMOVED******REMOVED******REMOVED*** 2. Configure Firewall

```bash
***REMOVED*** Allow necessary ports
sudo ufw allow 22/tcp      ***REMOVED*** SSH
sudo ufw allow 80/tcp      ***REMOVED*** HTTP
sudo ufw allow 443/tcp     ***REMOVED*** HTTPS
sudo ufw enable

***REMOVED*** Verify rules
sudo ufw status
```

***REMOVED******REMOVED******REMOVED*** 3. Set Up Log Rotation

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

***REMOVED******REMOVED******REMOVED*** 4. Configure Automated Backups

See [Backup & Restore Guide](./backup-restore.md) for complete backup configuration.

---

***REMOVED******REMOVED*** Upgrading

***REMOVED******REMOVED******REMOVED*** Docker Upgrade Process

```bash
***REMOVED*** Pull latest changes
git pull origin main

***REMOVED*** Backup database first
docker compose exec db pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

***REMOVED*** Rebuild and restart
docker compose down
docker compose build --no-cache
docker compose up -d

***REMOVED*** Run any new migrations
docker compose exec backend alembic upgrade head

***REMOVED*** Verify services
docker compose ps
docker compose logs -f
```

***REMOVED******REMOVED******REMOVED*** Manual Upgrade Process

```bash
***REMOVED*** Stop services
sudo systemctl stop residency-backend
pm2 stop residency-frontend

***REMOVED*** Backup database
pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

***REMOVED*** Pull latest code
cd /opt/residency-scheduler
sudo -u scheduler git pull origin main

***REMOVED*** Update backend
cd backend
sudo -u scheduler ./venv/bin/pip install -r requirements.txt
sudo -u scheduler ./venv/bin/alembic upgrade head

***REMOVED*** Update frontend
cd ../frontend
sudo -u scheduler npm ci
sudo -u scheduler npm run build

***REMOVED*** Restart services
sudo systemctl start residency-backend
pm2 start residency-frontend

***REMOVED*** Verify
sudo systemctl status residency-backend
pm2 status
```

---

***REMOVED******REMOVED*** Troubleshooting Installation

***REMOVED******REMOVED******REMOVED*** Common Issues

***REMOVED******REMOVED******REMOVED******REMOVED*** Docker: Container Won't Start

```bash
***REMOVED*** Check container logs
docker compose logs backend
docker compose logs db

***REMOVED*** Verify environment variables
docker compose config

***REMOVED*** Check port conflicts
sudo lsof -i :8000
sudo lsof -i :5432
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Database Connection Failed

```bash
***REMOVED*** Verify PostgreSQL is running
sudo systemctl status postgresql

***REMOVED*** Test connection
psql -U scheduler -h localhost -d residency_scheduler

***REMOVED*** Check pg_hba.conf settings
sudo cat /etc/postgresql/15/main/pg_hba.conf | grep scheduler
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Backend Service Won't Start

```bash
***REMOVED*** Check logs
sudo journalctl -u residency-backend -n 50

***REMOVED*** Verify virtual environment
/opt/residency-scheduler/backend/venv/bin/python --version

***REMOVED*** Test manual start
cd /opt/residency-scheduler/backend
./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

***REMOVED******REMOVED******REMOVED******REMOVED*** SSL Certificate Issues

```bash
***REMOVED*** Verify certificate
sudo certbot certificates

***REMOVED*** Force renewal
sudo certbot renew --force-renewal

***REMOVED*** Check Nginx SSL configuration
sudo nginx -t
```

***REMOVED******REMOVED******REMOVED******REMOVED*** Permission Denied Errors

```bash
***REMOVED*** Fix file ownership
sudo chown -R scheduler:scheduler /opt/residency-scheduler

***REMOVED*** Fix log directory permissions
sudo chown -R scheduler:scheduler /var/log/residency-scheduler
sudo chmod 755 /var/log/residency-scheduler
```

---

***REMOVED******REMOVED*** Installation Checklist

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
