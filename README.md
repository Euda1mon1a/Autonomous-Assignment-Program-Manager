# Residency Scheduler

> **Last Updated:** 2025-12-18

<p align="center">
  <strong>A comprehensive medical residency scheduling system with ACGME compliance validation</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## Overview

Residency Scheduler is a production-ready, full-stack application designed to automate and optimize medical residency program scheduling while ensuring compliance with ACGME (Accreditation Council for Graduate Medical Education) requirements. Built with modern technologies, it provides an intuitive interface for program coordinators, faculty, and administrators to manage complex scheduling needs.

### Key Capabilities

- **Automated Schedule Generation** - Constraint-based algorithm that generates compliant schedules
- **ACGME Compliance Monitoring** - Real-time validation against 80-hour rule, 1-in-7 rule, and supervision ratios
- **Emergency Coverage System** - Handle military deployments, TDY assignments, and medical emergencies
- **Role-Based Access Control** - Secure multi-user system with admin, coordinator, and faculty roles
- **Export Functionality** - Generate Excel reports for external use

---

## Features

### Schedule Management
- **Rotation Templates**: Create reusable activity patterns (clinic, inpatient, procedures, conference) with capacity limits and specialty requirements
- **Smart Assignment**: Greedy algorithm with constraint satisfaction ensures optimal coverage
- **Block-Based Scheduling**: 730 blocks per academic year (365 days × AM/PM sessions)
- **Faculty Supervision**: Automatic assignment respecting ACGME supervision ratios

### ACGME Compliance
- **80-Hour Rule**: Maximum 80 hours/week averaged over rolling 4-week periods
- **1-in-7 Rule**: Guaranteed one 24-hour period off every 7 days
- **Supervision Ratios**:
  - PGY-1: 1 faculty per 2 residents
  - PGY-2/3: 1 faculty per 4 residents
- **Violation Tracking**: Severity-based alerts (Critical, High, Medium, Low)

### Absence Management
- Multiple absence types: vacation, deployment, TDY, medical, family emergency, conference
- Military-specific tracking (deployment orders, TDY locations)
- Calendar and list views
- Automatic availability matrix updates

### User Management
- JWT-based authentication with httpOnly secure cookies
- Rate limiting on authentication endpoints (5 login/min, 3 register/min)
- Eight user roles: Admin, Coordinator, Faculty, Resident, Clinical Staff, RN, LPN, MSA
- Activity logging and audit trails
- Full role-based access control (RBAC) with resource-level filtering
- Strong password requirements (12+ chars, complexity rules)

### Security Features
- **Authentication**: httpOnly cookies (XSS-resistant), bcrypt password hashing
- **Authorization**: Role-based access control with admin endpoint protection
- **Input Validation**: Pydantic schemas, file upload validation (size, type, content)
- **Path Security**: Path traversal prevention in file operations
- **Secret Management**: Startup validation rejects default/weak secrets
- **Error Handling**: Global exception handler prevents information leakage
- **API Protection**: Rate limiting, CORS configuration, production doc/metrics restrictions

### Procedure Credentialing
Track faculty qualifications for supervising medical procedures:
- **Procedure Definitions**: Define procedures with complexity levels, supervision ratios, and minimum PGY requirements
- **Faculty Credentials**: Track which faculty are qualified to supervise each procedure
- **Competency Levels**: Trainee, Qualified, Expert, Master designations
- **Expiration Tracking**: Automatic alerts for expiring credentials
- **Certification Management**: Track BLS, ACLS, PALS, and other required certifications
- **Compliance Monitoring**: Ensure qualified supervisors are scheduled for procedure blocks

See [API Documentation](docs/api/endpoints/credentials.md) for endpoint details.

### Resilience Framework
Built-in system resilience inspired by cross-industry best practices:
- **80% Utilization Threshold** - Queuing theory prevents cascade failures
- **N-1/N-2 Contingency Analysis** - Power grid-style vulnerability detection
- **Defense in Depth** - Nuclear engineering safety levels (GREEN→YELLOW→ORANGE→RED→BLACK)
- **Static Stability** - Pre-computed fallback schedules for instant crisis response
- **Sacrifice Hierarchy** - Triage-based load shedding when capacity is constrained
- **Prometheus Metrics** - Real-time monitoring and alerting
- **Celery Background Tasks** - Automated health checks and contingency analysis

See [Resilience Framework](docs/guides/resilience-framework.md) for detailed documentation.

### Dashboard & Reporting
- Schedule summary with compliance status
- Upcoming absences widget
- Quick action buttons
- Month-by-month compliance visualization

---

## Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 14.0.4 | React framework with App Router |
| React | 18.2.0 | UI component library |
| TypeScript | 5.0+ | Type-safe JavaScript |
| TailwindCSS | 3.3.0 | Utility-first CSS framework |
| TanStack Query | 5.17.0 | Data fetching and caching |
| Axios | 1.6.3 | HTTP client |
| date-fns | 3.1.0 | Date manipulation |
| Lucide React | 0.303.0 | Icon library |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.109.0 | High-performance web framework |
| SQLAlchemy | 2.0.25 | ORM with async support |
| Pydantic | 2.5.3 | Data validation |
| Alembic | 1.13.1 | Database migrations |
| python-jose | 3.3.0 | JWT token handling |
| passlib | 1.7.4 | Password hashing (bcrypt) |
| openpyxl | 3.1.2 | Excel export |
| NetworkX | 3.0+ | Graph analysis for hub vulnerability |
| Celery | 5.x | Background task processing |
| Redis | - | Message broker & result backend |
| Prometheus | - | Metrics and monitoring |

### Infrastructure
| Technology | Version | Purpose |
|------------|---------|---------|
| PostgreSQL | 15 | Primary database |
| Docker | Latest | Containerization |
| Docker Compose | Latest | Multi-container orchestration |

### Testing
| Technology | Purpose |
|------------|---------|
| pytest | Backend unit and integration testing |
| Jest | Frontend unit testing |
| React Testing Library | Component testing |
| Playwright | End-to-end testing |
| MSW | API mocking |

---

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git

### Running with Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the application
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs (Swagger UI)
# ReDoc:     http://localhost:8000/redoc
```

### Local Development

See [docs/SETUP.md](docs/SETUP.md) for detailed installation and configuration instructions.

#### Backend Quick Start
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

#### Frontend Quick Start
```bash
cd frontend
npm install
npm run dev
```

#### Background Tasks (Celery)
For resilience monitoring and automated tasks:

```bash
# Start Redis (required)
redis-server

# Start Celery worker and beat scheduler
cd backend
../scripts/start-celery.sh both

# Or start them separately
../scripts/start-celery.sh worker  # Background task worker
../scripts/start-celery.sh beat    # Periodic task scheduler

# Verify Celery is running
python verify_celery.py
```

See [Celery Setup](docs/archived/CELERY_SETUP_SUMMARY.md) for configuration reference.

---

## Project Structure

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/                 # API layer (routes, dependencies)
│   │   ├── core/                # Configuration, security, Celery
│   │   ├── db/                  # Database session management
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── repositories/        # Data access layer
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── services/            # Business logic layer
│   │   ├── scheduling/          # Scheduling engine & validator
│   │   ├── resilience/          # Resilience framework
│   │   │   ├── utilization.py   # 80% threshold monitoring
│   │   │   ├── defense_in_depth.py  # 5-level safety system
│   │   │   ├── contingency.py   # N-1/N-2 analysis (NetworkX)
│   │   │   ├── static_stability.py  # Fallback schedules
│   │   │   ├── sacrifice_hierarchy.py  # Load shedding
│   │   │   ├── metrics.py       # Prometheus metrics
│   │   │   ├── tasks.py         # Celery background tasks
│   │   │   └── service.py       # Resilience service
│   │   └── notifications/       # Alert delivery
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # Backend test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js App Router pages
│   │   ├── components/          # Reusable React components
│   │   ├── contexts/            # React Context providers
│   │   ├── lib/                 # API client & custom hooks
│   │   └── types/               # TypeScript type definitions
│   ├── __tests__/               # Jest unit tests
│   ├── e2e/                     # Playwright E2E tests
│   ├── Dockerfile
│   └── package.json
├── docs/                        # Project documentation
├── docker-compose.yml           # Production configuration
├── docker-compose.dev.yml       # Development configuration
└── README.md
```

---

## Screenshots

### Dashboard
*Overview with schedule summary, compliance alerts, and quick actions*

![Dashboard](docs/images/dashboard-placeholder.png)

### Schedule View
*Interactive calendar with drag-and-drop assignment management*

![Schedule](docs/images/schedule-placeholder.png)

### People Management
*Resident and faculty directory with filtering*

![People](docs/images/people-placeholder.png)

### Compliance Monitor
*ACGME compliance status and violation tracking*

![Compliance](docs/images/compliance-placeholder.png)

---

## Documentation

### Getting Started
| Document | Description |
|----------|-------------|
| [User Guide](USER_GUIDE.md) | Complete user guide |
| [Getting Started](docs/getting-started/index.md) | Installation and quickstart |
| [Configuration](docs/getting-started/configuration.md) | Environment setup |

### Technical Reference
| Document | Description |
|----------|-------------|
| [Architecture Overview](ARCHITECTURE.md) | System design and data flow |
| [API Documentation](docs/api/index.md) | REST API reference |
| [Resilience Framework](docs/guides/resilience-framework.md) | Cross-industry resilience concepts |
| [Development Setup](docs/development/setup.md) | Local development environment |

### Operations
| Document | Description |
|----------|-------------|
| [Admin Manual](docs/admin-manual/README.md) | System administration guide |
| [Security Scanning](docs/operations/SECURITY_SCANNING.md) | Security tools and practices |
| [Metrics & Monitoring](docs/operations/metrics.md) | Prometheus metrics reference |
| [Deployment](docs/operations/DEPLOYMENT_PROMPT.md) | Production deployment |

### Planning & Status
| Document | Description |
|----------|-------------|
| [Roadmap](ROADMAP.md) | Feature roadmap and milestones |
| [Strategic Decisions](STRATEGIC_DECISIONS.md) | Key project decisions |
| [Human TODO](HUMAN_TODO.md) | Tasks requiring human action |

### Archived Documentation
Historical session logs, implementation summaries, and reports are preserved in [docs/archived/](docs/archived/README.md).

---

## API Overview

### Authentication
```
POST /api/auth/register     # Create new user
POST /api/auth/login        # OAuth2 password flow
POST /api/auth/login/json   # JSON-based login
GET  /api/auth/me           # Current user info
```

### People
```
GET    /api/people              # List all (with filters)
GET    /api/people/residents    # List residents
GET    /api/people/faculty      # List faculty
POST   /api/people              # Create person
PUT    /api/people/{id}         # Update person
DELETE /api/people/{id}         # Delete person
```

### Schedule
```
POST /api/schedule/generate           # Generate schedule
GET  /api/schedule/validate           # Validate compliance
POST /api/schedule/emergency-coverage # Handle emergencies
```

### Absences
```
GET    /api/absences      # List absences
POST   /api/absences      # Create absence
PUT    /api/absences/{id} # Update absence
DELETE /api/absences/{id} # Delete absence
```

### Resilience & Monitoring
```
GET  /health/resilience              # Resilience system status
GET  /metrics                        # Prometheus metrics endpoint
POST /api/resilience/health-check    # Trigger manual health check
GET  /api/resilience/contingency     # Run N-1/N-2 analysis
POST /api/resilience/crisis          # Activate crisis response
GET  /api/resilience/fallbacks       # List available fallback schedules
```

See [API Reference](docs/API_REFERENCE.md) for complete documentation.

---

## Environment Variables

```bash
# Database Configuration
DB_PASSWORD=your_secure_password

# Security (REQUIRED - no defaults allowed in production)
SECRET_KEY=your_secret_key_here_min_32_chars  # Generate: python -c 'import secrets; print(secrets.token_urlsafe(32))'
WEBHOOK_SECRET=your_webhook_secret_min_32_chars

# Application Settings
DEBUG=false

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Redis (for Celery background tasks and rate limiting)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=your_redis_password  # Required for authenticated Redis

# Rate Limiting
RATE_LIMIT_LOGIN_ATTEMPTS=5
RATE_LIMIT_LOGIN_WINDOW=60
RATE_LIMIT_REGISTER_ATTEMPTS=3
RATE_LIMIT_REGISTER_WINDOW=60
RATE_LIMIT_ENABLED=true

# Monitoring Services (required - no defaults)
N8N_PASSWORD=your_n8n_password
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# Prometheus (optional)
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus_multiproc
```

> **Security Note**: The application will refuse to start in production (`DEBUG=false`) if `SECRET_KEY` or `WEBHOOK_SECRET` are empty or use default values.

---

## Running Tests

### Backend
```bash
cd backend
pytest                          # Run all tests
pytest -m acgme                 # ACGME compliance tests
pytest --cov=app --cov-report=html  # With coverage
```

### Frontend
```bash
cd frontend
npm test                        # Unit tests
npm run test:coverage           # With coverage
npm run test:ci                 # CI-optimized tests
npm run test:e2e                # E2E tests
npm run type-check              # TypeScript check (source only)
npm run lint:fix                # Auto-fix lint issues
npm run validate                # Run all checks (type-check, lint, test)
npm run audit                   # Security vulnerability check
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Quick Contribution Steps
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest` and `npm test`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [ACGME](https://www.acgme.org/) for residency program requirements
- [FastAPI](https://fastapi.tiangolo.com/) for the excellent Python web framework
- [Next.js](https://nextjs.org/) for the React framework
- [TailwindCSS](https://tailwindcss.com/) for utility-first CSS

---

<p align="center">
  Made with care for medical education programs
</p>
