# Deployment Prompt: Residency Scheduler Clone

Copy and paste the following prompt to deploy a complete clone of this stack.

---

## PROMPT TO DEPLOY

```
I need to deploy a complete clone of a medical residency scheduling application. Here are the full specifications:

## TECH STACK

**Backend:**
- Python 3.11+ with FastAPI 0.124.4
- SQLAlchemy 2.0 (async) with PostgreSQL 15
- Alembic migrations
- Celery 5.6 + Redis 7 for background jobs
- JWT authentication (python-jose + bcrypt)
- OR-Tools for constraint optimization

**Frontend:**
- Next.js 14.2 with TypeScript
- TailwindCSS 3.4
- TanStack React Query 5.17
- Framer Motion animations

**Infrastructure:**
- Docker + Docker Compose
- Nginx reverse proxy with SSL
- Prometheus + Grafana monitoring
- n8n workflow automation

---

## DIRECTORY STRUCTURE TO CREATE

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # FastAPI route handlers
│   │   ├── controllers/         # Business logic orchestration
│   │   ├── services/            # Domain logic
│   │   ├── repositories/        # Database queries
│   │   ├── models/              # SQLAlchemy models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── core/                # Config, security, database
│   │   ├── resilience/          # Resilience framework
│   │   ├── notifications/       # Notification system
│   │   └── main.py              # FastAPI app entry
│   ├── alembic/                 # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── components/          # Reusable UI components
│   │   ├── features/            # Feature modules
│   │   ├── contexts/            # React contexts
│   │   ├── lib/                 # Utilities
│   │   └── types/               # TypeScript definitions
│   ├── public/
│   ├── package.json
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.ts
│   └── .env.example
├── nginx/
│   ├── nginx.conf
│   ├── conf.d/
│   └── Dockerfile
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   ├── alertmanager/
│   └── docker-compose.monitoring.yml
├── n8n/
│   └── workflows/
├── docker-compose.yml
├── docker-compose.prod.yml
└── .env.example
```

---

## ENVIRONMENT VARIABLES NEEDED

Create `.env` with:

```env
# Database
DB_PASSWORD=your-secure-password-here
DATABASE_URL=postgresql://scheduler:${DB_PASSWORD}@db:5432/residency_scheduler
DB_POOL_SIZE=10
DB_POOL_MAX_OVERFLOW=20

# Security
SECRET_KEY=generate-64-char-random-token
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# API
CORS_ORIGINS=["http://localhost:3000"]
NEXT_PUBLIC_API_URL=http://localhost:8000

# Environment
ENVIRONMENT=development
```

---

## DOCKER COMPOSE SERVICES

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: scheduler
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: residency_scheduler
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U scheduler"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - CORS_ORIGINS=${CORS_ORIGINS}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    command: >
      sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"

  celery-worker:
    build: ./backend
    command: celery -A app.celery_app worker -l info -Q default,resilience,notifications,metrics
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
      - CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND}
    depends_on:
      - backend
      - redis

  celery-beat:
    build: ./backend
    command: celery -A app.celery_app beat -l info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CELERY_BROKER_URL=${CELERY_BROKER_URL}
    depends_on:
      - celery-worker

  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:

networks:
  default:
    name: app-network
```

---

## BACKEND DOCKERFILE

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1001 appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## FRONTEND DOCKERFILE

```dockerfile
FROM node:22-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package.json package-lock.json ./
RUN npm ci

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM base AS runner
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

---

## KEY PYTHON DEPENDENCIES (requirements.txt)

```
# Core
fastapi==0.124.4
uvicorn[standard]==0.38.0
starlette==0.37.2

# Database
sqlalchemy[asyncio]==2.0.45
asyncpg==0.30.0
psycopg2-binary==2.9.10
alembic==1.17.2

# Validation
pydantic==2.12.5
pydantic-settings==2.9.1
email-validator==2.2.0

# Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# Queue
celery==5.6.0
redis==5.2.1

# Optimization
ortools>=9.8.3296
pulp==2.7.0

# API
fastapi-pagination==0.12.36
slowapi==0.1.9

# Export
openpyxl==3.1.5
reportlab==4.4.6
python-docx==1.2.0
icalendar==6.1.3

# Monitoring
sentry-sdk==2.18.0
prometheus-fastapi-instrumentator==7.0.2

# Data
pandas==2.2.3
numpy==2.2.4
python-dateutil==2.9.0.post0

# Testing
pytest==8.4.0
pytest-asyncio==0.24.0
httpx==0.28.1
```

---

## KEY NODE DEPENDENCIES (package.json)

```json
{
  "dependencies": {
    "next": "14.2.35",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@tanstack/react-query": "^5.17.0",
    "axios": "^1.6.3",
    "tailwindcss": "^3.4.1",
    "framer-motion": "^12.23.26",
    "lucide-react": "^0.561.0",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "eslint": "^8.0.0",
    "postcss": "^8.4.35",
    "autoprefixer": "^10.4.17"
  }
}
```

---

## CORE DATABASE MODELS TO IMPLEMENT

1. **Person** - Users with roles (Admin, Coordinator, Faculty, Resident)
2. **Assignment** - Schedule assignments linking person to block
3. **Block** - Daily scheduling blocks (730 per academic year)
4. **Absence** - Leave, deployment, medical absences
5. **Certification** - BLS, ACLS, PALS tracking with expiration
6. **Procedure** - Medical procedures with supervision requirements
7. **Rotation_Template** - Reusable activity patterns
8. **Schedule_Run** - Schedule generation executions
9. **Conflict_Alert** - ACGME rule violation tracking
10. **Notification** - User notification system

---

## API ROUTES TO IMPLEMENT

- `/api/auth` - JWT login/logout
- `/api/people` - CRUD for users/faculty/residents
- `/api/assignments` - Schedule assignments
- `/api/schedule` - Schedule generation & management
- `/api/absences` - Leave tracking
- `/api/certifications` - Certification management
- `/api/procedures` - Procedure definitions
- `/api/calendar` - iCalendar export
- `/api/analytics` - Schedule metrics
- `/api/resilience` - System health & contingency
- `/api/export` - Excel/PDF generation
- `/health` - Health check endpoint

---

## DEPLOYMENT COMMANDS

```bash
# 1. Generate secrets
python -c "import secrets; print(secrets.token_urlsafe(64))"

# 2. Create .env file with generated secrets

# 3. Build and start
docker-compose build
docker-compose up -d

# 4. Verify health
curl http://localhost:8000/health
curl http://localhost:3000

# 5. View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

## OPTIONAL: ADD MONITORING STACK

Add Prometheus + Grafana:

```yaml
# monitoring/docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

---

Please create this complete stack with:
1. All Docker configurations
2. Backend with FastAPI, SQLAlchemy models, and API routes
3. Frontend with Next.js pages and components
4. Database migrations
5. Celery task definitions
6. Health check endpoints
7. Basic authentication system

Start with the infrastructure (Docker, configs) then build out the backend models and API, followed by the frontend UI.
```

---

## QUICK START (LOCAL DEVELOPMENT)

If you want to run the existing codebase locally:

```bash
# Clone the repo
git clone <repo-url>
cd Autonomous-Assignment-Program-Manager

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Generate a secret key and update .env
python -c "import secrets; print(secrets.token_urlsafe(64))"

# Build and run
docker-compose build
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## PRODUCTION DEPLOYMENT

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Initialize SSL (first time only)
./nginx/scripts/init-letsencrypt.sh your-domain.com admin@email.com

# Start monitoring stack
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```
