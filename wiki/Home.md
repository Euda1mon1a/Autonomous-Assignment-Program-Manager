***REMOVED*** Residency Scheduler Wiki

Welcome to the **Residency Scheduler** documentation wiki. This comprehensive scheduling system automates medical residency program scheduling while maintaining full ACGME compliance.

***REMOVED******REMOVED*** Quick Links

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

***REMOVED******REMOVED*** About the Project

***REMOVED******REMOVED******REMOVED*** What is Residency Scheduler?

Residency Scheduler is a **full-stack medical residency scheduling system** designed to:

- **Automate** schedule generation using constraint-based algorithms
- **Ensure compliance** with ACGME (Accreditation Council for Graduate Medical Education) regulations
- **Provide tools** for program coordinators, faculty, and administrators
- **Handle emergencies** with intelligent coverage systems
- **Track certifications** and procedure credentials

***REMOVED******REMOVED******REMOVED*** Key Features

***REMOVED******REMOVED******REMOVED******REMOVED*** Scheduling & Management
- Block-based scheduling (730 blocks per academic year)
- Rotation template management with capacity limits
- Smart assignment using greedy algorithms with constraint satisfaction
- Faculty supervision automatic assignment respecting ACGME ratios

***REMOVED******REMOVED******REMOVED******REMOVED*** ACGME Compliance
- **80-hour rule** monitoring (maximum 80 hours/week averaged over 4 weeks)
- **1-in-7 rule** enforcement (one 24-hour period off every 7 days)
- **Supervision ratios**:
  - PGY-1: 1 faculty per 2 residents
  - PGY-2/3: 1 faculty per 4 residents
- Violation tracking with severity levels

***REMOVED******REMOVED******REMOVED******REMOVED*** Advanced Features
- Emergency coverage system for deployments, TDY, medical emergencies
- Role-based access control (Admin, Coordinator, Faculty)
- Procedure credentialing with competency tracking
- FMIT swap system with conflict detection
- Multi-objective Pareto optimization
- Export to Excel and ICS calendar formats

***REMOVED******REMOVED******REMOVED******REMOVED*** Resilience & Monitoring
- 80% utilization threshold monitoring
- N-1/N-2 contingency analysis
- Defense in Depth framework (5 safety levels)
- Prometheus metrics and real-time monitoring
- Celery background tasks for automated health checks

---

***REMOVED******REMOVED*** Technology Stack

***REMOVED******REMOVED******REMOVED*** Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Task Queue**: Celery + Redis
- **Optimization**: Google OR-Tools, PuLP, pymoo

***REMOVED******REMOVED******REMOVED*** Frontend
- **Framework**: Next.js 14 (React 18)
- **Styling**: TailwindCSS 3.4
- **State Management**: TanStack Query
- **Animation**: Framer Motion

***REMOVED******REMOVED******REMOVED*** Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus
- **Workflow Automation**: n8n

---

***REMOVED******REMOVED*** Quick Start

```bash
***REMOVED*** Clone repository
git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
cd Autonomous-Assignment-Program-Manager

***REMOVED*** Configure environment
cp .env.example .env
***REMOVED*** Edit .env with your settings

***REMOVED*** Start all services
docker-compose up -d

***REMOVED*** Access application
***REMOVED*** Frontend:  http://localhost:3000
***REMOVED*** API:       http://localhost:8000
***REMOVED*** API Docs:  http://localhost:8000/docs
```

See [Getting Started](Getting-Started) for detailed instructions.

---

***REMOVED******REMOVED*** Project Status

***REMOVED******REMOVED******REMOVED*** Core Components

| Component | Status | Details |
|-----------|--------|---------|
| Backend API | Production Ready | FastAPI with 30+ route modules |
| Frontend UI | Production Ready | Next.js 14 with 11 feature modules |
| ACGME Compliance | Fully Implemented | 80-hour, 1-in-7, supervision rules |
| Resilience Framework | Production Ready | 5-level Defense in Depth |
| Documentation | Complete | Wiki + API Reference + User Guide |

***REMOVED******REMOVED******REMOVED*** Feature Status

| Feature | Status | Notes |
|---------|--------|-------|
| ICS Calendar Export | **Fully Implemented** | RFC 5545 compliant, person/rotation/bulk export |
| WebCal Subscriptions | **Fully Implemented** | Token-based auth, Google/Outlook/Apple support |
| FMIT Swap System | Production Ready | 5-factor auto-matching algorithm |
| Conflict Resolution | Production Ready | 5 resolution strategies |
| Analytics Dashboard | Production Ready | Coverage, fairness, workload metrics |
| Audit Trail | Production Ready | Full change history tracking |
| Excel Import/Export | Production Ready | Bulk data management |
| Role-Based Views | Production Ready | Admin, Coordinator, Faculty, Resident |

***REMOVED******REMOVED******REMOVED*** Test Coverage

| Category | Tests | Lines |
|----------|-------|-------|
| Backend Routes | 452+ | 12,180+ |
| Services | 100+ | 8,000+ |
| Integration | 50+ | 4,000+ |
| Calendar | 40+ | 1,100+ |

*Last updated: 2025-12-17*

---

***REMOVED******REMOVED*** Getting Help

- **User Guide**: Start with the [User Guide](User-Guide) for feature explanations
- **API Reference**: See [API Reference](API-Reference) for endpoint documentation
- **Troubleshooting**: Check [Troubleshooting](Troubleshooting) for common issues
- **GitHub Issues**: Report bugs or request features

---

***REMOVED******REMOVED*** License

This project is open source under the MIT License. Made with Aloha.
