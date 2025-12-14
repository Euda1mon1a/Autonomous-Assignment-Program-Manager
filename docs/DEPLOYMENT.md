***REMOVED*** Deployment Guide

***REMOVED******REMOVED*** Document Purpose

This document provides comprehensive deployment instructions for the Residency Scheduler application, covering Docker, manual deployment, and production configurations.

**Author:** Opus 4.5 (Opus-Tests)
**Status:** APPROVED FOR IMPLEMENTATION
**Last Updated:** 2024-12-14

---

***REMOVED******REMOVED*** Table of Contents

1. [Prerequisites](***REMOVED***prerequisites)
2. [Environment Variables](***REMOVED***environment-variables)
3. [Docker Deployment](***REMOVED***docker-deployment)
4. [Manual Deployment](***REMOVED***manual-deployment)
5. [SSL/HTTPS Configuration](***REMOVED***sslhttps-configuration)
6. [Monitoring & Logging](***REMOVED***monitoring--logging)
7. [Backup & Recovery](***REMOVED***backup--recovery)

---

***REMOVED******REMOVED*** Prerequisites

***REMOVED******REMOVED******REMOVED*** System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 4 GB | 8 GB |
| Storage | 20 GB | 50 GB |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

***REMOVED******REMOVED******REMOVED*** Software Requirements

**For Docker Deployment:**
- Docker Engine 20.10+
- Docker Compose 2.0+

**For Manual Deployment:**
- Python 3.11+
- Node.js 20 LTS
- PostgreSQL 15+
- Nginx (reverse proxy)

***REMOVED******REMOVED******REMOVED*** Verify Prerequisites

```bash
***REMOVED*** Docker
docker --version
docker compose version

***REMOVED*** Manual deployment
python3 --version
node --version
npm --version
psql --version
```

---

***REMOVED******REMOVED*** Environment Variables

***REMOVED******REMOVED******REMOVED*** Backend Environment Variables

Create a `.env` file in the project root:

```bash
***REMOVED*** Application Settings
APP_NAME="Residency Scheduler"
APP_VERSION="1.0.0"
DEBUG=false

***REMOVED*** Database Configuration
DATABASE_URL=postgresql://scheduler:your_secure_password@localhost:5432/residency_scheduler
DB_PASSWORD=your_secure_password

***REMOVED*** Security
SECRET_KEY=your-256-bit-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=1440

***REMOVED*** CORS (adjust for production domain)
CORS_ORIGINS='["https://your-domain.com"]'
```

***REMOVED******REMOVED******REMOVED*** Frontend Environment Variables

Create `.env.local` in the `frontend/` directory:

```bash
***REMOVED*** API URL
NEXT_PUBLIC_API_URL=https://api.your-domain.com

***REMOVED*** Optional: Analytics
NEXT_PUBLIC_GA_ID=UA-XXXXXXXX-X
```

***REMOVED******REMOVED******REMOVED*** Generate Secret Key

```bash
***REMOVED*** Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

***REMOVED******REMOVED******REMOVED*** Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | JWT signing key (256-bit) |
| `DEBUG` | No | `false` | Enable debug mode |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | Token expiration (24h) |

---

***REMOVED******REMOVED*** Docker Deployment

***REMOVED******REMOVED******REMOVED*** Quick Start

```bash
***REMOVED*** Clone the repository
git clone <repository-url>
cd Autonomous-Assignment-Program-Manager

***REMOVED*** Create environment file
cp .env.example .env
***REMOVED*** Edit .env with production values

***REMOVED*** Build and start services
docker compose up -d --build
```

***REMOVED******REMOVED******REMOVED*** Docker Compose Services

The `docker-compose.yml` defines three services:

| Service | Port | Description |
|---------|------|-------------|
| `postgres` | 5432 | PostgreSQL 15 database |
| `backend` | 8000 | FastAPI application |
| `frontend` | 3000 | Next.js application |

***REMOVED******REMOVED******REMOVED*** Production Docker Compose

For production, create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: residency-scheduler-db
    restart: always
    environment:
      POSTGRES_DB: residency_scheduler
      POSTGRES_USER: scheduler
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scheduler -d residency_scheduler"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: residency-scheduler-backend
    restart: always
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://scheduler:${DB_PASSWORD}@postgres:5432/residency_scheduler
      SECRET_KEY: ${SECRET_KEY}
      DEBUG: "false"
      CORS_ORIGINS: '["https://your-domain.com"]'
    expose:
      - "8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: residency-scheduler-frontend
    restart: always
    depends_on:
      - backend
    environment:
      NEXT_PUBLIC_API_URL: https://api.your-domain.com
    expose:
      - "3000"

  nginx:
    image: nginx:alpine
    container_name: residency-scheduler-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
```

***REMOVED******REMOVED******REMOVED*** Deploy to Production

```bash
***REMOVED*** Build and start with production config
docker compose -f docker-compose.prod.yml up -d --build

***REMOVED*** View logs
docker compose -f docker-compose.prod.yml logs -f

***REMOVED*** Check service health
docker compose -f docker-compose.prod.yml ps
```

***REMOVED******REMOVED******REMOVED*** Docker Commands Reference

```bash
***REMOVED*** Stop all services
docker compose down

***REMOVED*** Rebuild specific service
docker compose build backend

***REMOVED*** View service logs
docker compose logs -f backend

***REMOVED*** Execute command in container
docker compose exec backend python -m pytest

***REMOVED*** Database backup
docker compose exec postgres pg_dump -U scheduler residency_scheduler > backup.sql

***REMOVED*** Scale services (if needed)
docker compose up -d --scale backend=3
```

---

***REMOVED******REMOVED*** Manual Deployment

***REMOVED******REMOVED******REMOVED*** 1. Database Setup

```bash
***REMOVED*** Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

***REMOVED*** Create database and user
sudo -u postgres psql

CREATE DATABASE residency_scheduler;
CREATE USER scheduler WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE residency_scheduler TO scheduler;
\q
```

***REMOVED******REMOVED******REMOVED*** 2. Backend Deployment

```bash
***REMOVED*** Create application directory
sudo mkdir -p /opt/residency-scheduler/backend
cd /opt/residency-scheduler/backend

***REMOVED*** Clone/copy application code
***REMOVED*** ...

***REMOVED*** Create virtual environment
python3 -m venv venv
source venv/bin/activate

***REMOVED*** Install dependencies
pip install -r requirements.txt

***REMOVED*** Set environment variables
export DATABASE_URL="postgresql://scheduler:password@localhost:5432/residency_scheduler"
export SECRET_KEY="your-secret-key"

***REMOVED*** Run migrations
alembic upgrade head

***REMOVED*** Start with Gunicorn (production WSGI server)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

***REMOVED******REMOVED******REMOVED*** 3. Backend Systemd Service

Create `/etc/systemd/system/residency-backend.service`:

```ini
[Unit]
Description=Residency Scheduler Backend
After=network.target postgresql.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/residency-scheduler/backend
Environment="PATH=/opt/residency-scheduler/backend/venv/bin"
EnvironmentFile=/opt/residency-scheduler/.env
ExecStart=/opt/residency-scheduler/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
***REMOVED*** Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable residency-backend
sudo systemctl start residency-backend
sudo systemctl status residency-backend
```

***REMOVED******REMOVED******REMOVED*** 4. Frontend Deployment

```bash
***REMOVED*** Navigate to frontend directory
cd /opt/residency-scheduler/frontend

***REMOVED*** Install dependencies
npm ci

***REMOVED*** Build for production
npm run build

***REMOVED*** Start with PM2 (process manager)
npm install -g pm2
pm2 start npm --name "residency-frontend" -- start
pm2 save
pm2 startup
```

***REMOVED******REMOVED******REMOVED*** 5. Nginx Configuration

Create `/etc/nginx/sites-available/residency-scheduler`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    ***REMOVED*** Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    ***REMOVED*** Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    ***REMOVED*** API documentation
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
    }
}
```

```bash
***REMOVED*** Enable site
sudo ln -s /etc/nginx/sites-available/residency-scheduler /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

***REMOVED******REMOVED*** SSL/HTTPS Configuration

***REMOVED******REMOVED******REMOVED*** Using Let's Encrypt (Recommended)

```bash
***REMOVED*** Install Certbot
sudo apt install certbot python3-certbot-nginx

***REMOVED*** Obtain certificate
sudo certbot --nginx -d your-domain.com -d api.your-domain.com

***REMOVED*** Test auto-renewal
sudo certbot renew --dry-run
```

***REMOVED******REMOVED******REMOVED*** Certificate Auto-Renewal

Certbot automatically creates a cron job. Verify:

```bash
sudo systemctl status certbot.timer
```

***REMOVED******REMOVED******REMOVED*** Self-Signed Certificate (Development)

```bash
***REMOVED*** Generate self-signed certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/residency-scheduler.key \
  -out /etc/ssl/certs/residency-scheduler.crt
```

---

***REMOVED******REMOVED*** Monitoring & Logging

***REMOVED******REMOVED******REMOVED*** Health Checks

The application provides health check endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /` | Basic health check |
| `GET /health` | Detailed health status |

***REMOVED******REMOVED******REMOVED*** Docker Health Monitoring

```bash
***REMOVED*** View container health
docker compose ps

***REMOVED*** Real-time container stats
docker stats

***REMOVED*** View logs with timestamps
docker compose logs -f --timestamps
```

***REMOVED******REMOVED******REMOVED*** Log Aggregation

For production, configure log aggregation:

**Docker Logging Driver:**

```yaml
***REMOVED*** In docker-compose.prod.yml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Systemd Journal:**

```bash
***REMOVED*** View backend logs
sudo journalctl -u residency-backend -f

***REMOVED*** View logs since today
sudo journalctl -u residency-backend --since today
```

***REMOVED******REMOVED******REMOVED*** Application Metrics

Consider integrating:
- **Prometheus** for metrics collection
- **Grafana** for visualization
- **Sentry** for error tracking

***REMOVED******REMOVED******REMOVED*** Example Prometheus Config

```yaml
***REMOVED*** prometheus.yml
scrape_configs:
  - job_name: 'residency-scheduler'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

***REMOVED******REMOVED*** Backup & Recovery

***REMOVED******REMOVED******REMOVED*** Database Backup

**Manual Backup:**

```bash
***REMOVED*** Docker
docker compose exec postgres pg_dump -U scheduler residency_scheduler > backup_$(date +%Y%m%d).sql

***REMOVED*** Manual deployment
pg_dump -U scheduler -h localhost residency_scheduler > backup_$(date +%Y%m%d).sql
```

**Automated Backup Script:**

Create `/opt/residency-scheduler/backup.sh`:

```bash
***REMOVED***!/bin/bash
BACKUP_DIR="/opt/backups/residency-scheduler"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

***REMOVED*** Create backup directory if not exists
mkdir -p ${BACKUP_DIR}

***REMOVED*** Create backup
docker compose exec -T postgres pg_dump -U scheduler residency_scheduler > ${BACKUP_FILE}

***REMOVED*** Compress backup
gzip ${BACKUP_FILE}

***REMOVED*** Remove backups older than 30 days
find ${BACKUP_DIR} -name "*.sql.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

**Add to crontab:**

```bash
***REMOVED*** Run backup daily at 2 AM
0 2 * * * /opt/residency-scheduler/backup.sh >> /var/log/residency-backup.log 2>&1
```

***REMOVED******REMOVED******REMOVED*** Database Restore

```bash
***REMOVED*** Docker
cat backup.sql | docker compose exec -T postgres psql -U scheduler residency_scheduler

***REMOVED*** Manual deployment
psql -U scheduler -h localhost residency_scheduler < backup.sql
```

***REMOVED******REMOVED******REMOVED*** Disaster Recovery Checklist

1. **Daily:** Database backup
2. **Weekly:** Full system backup
3. **Monthly:** Test restore procedure
4. **Document:** Recovery steps and contacts

---

***REMOVED******REMOVED*** Troubleshooting

***REMOVED******REMOVED******REMOVED*** Common Issues

**Database Connection Failed:**
```bash
***REMOVED*** Check PostgreSQL is running
sudo systemctl status postgresql
docker compose ps postgres

***REMOVED*** Verify connection string
psql "postgresql://scheduler:password@localhost:5432/residency_scheduler"
```

**Port Already in Use:**
```bash
***REMOVED*** Find process using port
sudo lsof -i :8000
sudo lsof -i :3000

***REMOVED*** Kill process
sudo kill -9 <PID>
```

**Permission Denied:**
```bash
***REMOVED*** Fix file permissions
sudo chown -R www-data:www-data /opt/residency-scheduler
sudo chmod -R 755 /opt/residency-scheduler
```

**Container Won't Start:**
```bash
***REMOVED*** View detailed logs
docker compose logs --tail=100 backend

***REMOVED*** Rebuild without cache
docker compose build --no-cache backend
```

---

*End of Deployment Guide*
