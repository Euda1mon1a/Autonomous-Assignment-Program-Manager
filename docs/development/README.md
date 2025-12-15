***REMOVED*** Developer Documentation

Welcome to the Residency Scheduler developer documentation. This guide provides comprehensive information for developers contributing to or extending the application.

***REMOVED******REMOVED*** Quick Navigation

| Document | Description |
|----------|-------------|
| [Environment Setup](./environment-setup.md) | Local development environment configuration |
| [Architecture](./architecture.md) | Code architecture and design patterns |
| [Workflow](./workflow.md) | Development workflow and branching strategy |
| [Testing](./testing.md) | Testing guidelines and best practices |
| [Code Style](./code-style.md) | Code style and conventions |
| [Contributing](./contributing.md) | How to contribute to the project |
| [File Ownership](./FILE_OWNERSHIP.md) | File ownership and responsibility matrix |

---

***REMOVED******REMOVED*** Project Overview

Residency Scheduler is a full-stack web application for medical residency program scheduling with ACGME compliance. The application consists of:

- **Backend**: Python/FastAPI REST API with SQLAlchemy ORM
- **Frontend**: Next.js/React with TypeScript and TailwindCSS
- **Database**: PostgreSQL 15+
- **Infrastructure**: Docker and Docker Compose

***REMOVED******REMOVED*** Tech Stack Summary

***REMOVED******REMOVED******REMOVED*** Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.109+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.5+ | Data validation |
| Alembic | 1.13+ | Database migrations |
| pytest | 7.0+ | Testing framework |

***REMOVED******REMOVED******REMOVED*** Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | 20+ | Runtime |
| Next.js | 14+ | React framework |
| TypeScript | 5.0+ | Type-safe JavaScript |
| TanStack Query | 5.17+ | Data fetching |
| TailwindCSS | 3.3+ | Styling |
| Jest | 29+ | Unit testing |
| Playwright | 1.40+ | E2E testing |

***REMOVED******REMOVED*** Getting Started

***REMOVED******REMOVED******REMOVED*** Fastest Path to Development

```bash
***REMOVED*** 1. Clone the repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

***REMOVED*** 2. Copy environment file
cp .env.example .env

***REMOVED*** 3. Start with Docker
docker-compose up -d

***REMOVED*** 4. Access the application
***REMOVED*** Frontend: http://localhost:3000
***REMOVED*** Backend API: http://localhost:8000
***REMOVED*** API Docs: http://localhost:8000/docs
```

For detailed setup instructions, see [Environment Setup](./environment-setup.md).

***REMOVED******REMOVED*** Repository Structure

```
residency-scheduler/
├── backend/                 ***REMOVED*** Python FastAPI backend
│   ├── app/                 ***REMOVED*** Application code
│   │   ├── api/routes/      ***REMOVED*** REST endpoint handlers
│   │   ├── core/            ***REMOVED*** Configuration and security
│   │   ├── db/              ***REMOVED*** Database session and types
│   │   ├── models/          ***REMOVED*** SQLAlchemy ORM models
│   │   ├── schemas/         ***REMOVED*** Pydantic validation schemas
│   │   ├── scheduling/      ***REMOVED*** Scheduling engine and validators
│   │   └── services/        ***REMOVED*** Business logic services
│   ├── alembic/             ***REMOVED*** Database migrations
│   ├── tests/               ***REMOVED*** pytest test suite
│   └── requirements.txt     ***REMOVED*** Python dependencies
├── frontend/                ***REMOVED*** Next.js frontend
│   ├── src/                 ***REMOVED*** Source code
│   │   ├── app/             ***REMOVED*** Next.js App Router pages
│   │   ├── components/      ***REMOVED*** React components
│   │   ├── contexts/        ***REMOVED*** React Context providers
│   │   ├── lib/             ***REMOVED*** API client and hooks
│   │   └── types/           ***REMOVED*** TypeScript definitions
│   ├── __tests__/           ***REMOVED*** Jest unit tests
│   ├── e2e/                 ***REMOVED*** Playwright E2E tests
│   └── package.json         ***REMOVED*** Node.js dependencies
├── docs/                    ***REMOVED*** Documentation
│   ├── development/         ***REMOVED*** Developer documentation (this folder)
│   └── *.md                 ***REMOVED*** Other documentation
├── docker-compose.yml       ***REMOVED*** Production Docker config
├── docker-compose.dev.yml   ***REMOVED*** Development Docker config
└── README.md                ***REMOVED*** Project overview
```

***REMOVED******REMOVED*** Key Concepts

***REMOVED******REMOVED******REMOVED*** ACGME Compliance

The application enforces ACGME (Accreditation Council for Graduate Medical Education) requirements:

- **80-Hour Rule**: Maximum 80 hours/week averaged over 4 weeks
- **1-in-7 Rule**: One 24-hour period off every 7 days
- **Supervision Ratios**: Faculty-to-resident ratios by PGY level
- **Continuous Duty Limits**: Maximum consecutive working hours

***REMOVED******REMOVED******REMOVED*** Scheduling Engine

The scheduling engine uses constraint satisfaction algorithms to:

1. Generate compliant schedules automatically
2. Validate existing schedules against ACGME rules
3. Handle emergency coverage and absences
4. Optimize for fairness and coverage requirements

***REMOVED******REMOVED******REMOVED*** Data Model

Core entities:

- **Person**: Residents and faculty members
- **Block**: Schedulable time slots (AM/PM sessions)
- **Assignment**: Links people to blocks with roles
- **Absence**: Vacation, deployment, medical leave tracking
- **RotationTemplate**: Reusable activity patterns

***REMOVED******REMOVED*** Development Workflow

1. **Fork & Clone**: Fork the repository and clone locally
2. **Branch**: Create a feature branch from `main`
3. **Develop**: Make changes following style guidelines
4. **Test**: Run tests and ensure coverage
5. **Commit**: Use conventional commit messages
6. **PR**: Open a pull request for review

For detailed workflow, see [Workflow](./workflow.md).

***REMOVED******REMOVED*** Support

- **Documentation**: Start with this developer guide
- **Issues**: Search existing issues or create new ones
- **Questions**: Use the "question" label on GitHub issues

---

*Last Updated: December 2024*
