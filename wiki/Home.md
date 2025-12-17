# Residency Scheduler Wiki

Welcome to the **Residency Scheduler** documentation wiki. This comprehensive scheduling system automates medical residency program scheduling while maintaining full ACGME compliance.

## Quick Links

| Page | Description |
|------|-------------|
| [Getting Started](Getting-Started) | Installation, setup, and first steps |
| [Architecture](Architecture) | System design and component overview |
| [User Guide](User-Guide) | How to use the application |
| [API Reference](API-Reference) | REST API documentation |
| [Configuration](Configuration) | Environment variables and settings |
| [Development](Development) | Contributing and development setup |
| [Resilience Framework](Resilience-Framework) | Advanced resilience features |
| [Troubleshooting](Troubleshooting) | Common issues and solutions |

---

## About the Project

### What is Residency Scheduler?

Residency Scheduler is a **full-stack medical residency scheduling system** designed to:

- **Automate** schedule generation using constraint-based algorithms
- **Ensure compliance** with ACGME (Accreditation Council for Graduate Medical Education) regulations
- **Provide tools** for program coordinators, faculty, and administrators
- **Handle emergencies** with intelligent coverage systems
- **Track certifications** and procedure credentials

### Key Features

#### Scheduling & Management
- Block-based scheduling (730 blocks per academic year)
- Rotation template management with capacity limits
- Smart assignment using greedy algorithms with constraint satisfaction
- Faculty supervision automatic assignment respecting ACGME ratios

#### ACGME Compliance
- **80-hour rule** monitoring (maximum 80 hours/week averaged over 4 weeks)
- **1-in-7 rule** enforcement (one 24-hour period off every 7 days)
- **Supervision ratios**:
  - PGY-1: 1 faculty per 2 residents
  - PGY-2/3: 1 faculty per 4 residents
- Violation tracking with severity levels

#### Advanced Features
- Emergency coverage system for deployments, TDY, medical emergencies
- Role-based access control (Admin, Coordinator, Faculty)
- Procedure credentialing with competency tracking
- FMIT swap system with conflict detection
- Multi-objective Pareto optimization
- Export to Excel and ICS calendar formats

#### Resilience & Monitoring
- 80% utilization threshold monitoring
- N-1/N-2 contingency analysis
- Defense in Depth framework (5 safety levels)
- Prometheus metrics and real-time monitoring
- Celery background tasks for automated health checks

---

## Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Task Queue**: Celery + Redis
- **Optimization**: Google OR-Tools, PuLP, pymoo

### Frontend
- **Framework**: Next.js 14 (React 18)
- **Styling**: TailwindCSS 3.4
- **State Management**: TanStack Query
- **Animation**: Framer Motion

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus
- **Workflow Automation**: n8n

---

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Start all services
docker-compose up -d

# Access application
# Frontend:  http://localhost:3000
# API:       http://localhost:8000
# API Docs:  http://localhost:8000/docs
```

See [Getting Started](Getting-Started) for detailed instructions.

---

## Project Status

| Component | Status |
|-----------|--------|
| Backend API | Production Ready |
| Frontend UI | Production Ready |
| ACGME Compliance | Fully Implemented |
| Resilience Framework | Production Ready |
| Documentation | Complete |

---

## Getting Help

- **User Guide**: Start with the [User Guide](User-Guide) for feature explanations
- **API Reference**: See [API Reference](API-Reference) for endpoint documentation
- **Troubleshooting**: Check [Troubleshooting](Troubleshooting) for common issues
- **GitHub Issues**: Report bugs or request features

---

## License

This project is proprietary software for medical residency program management.
