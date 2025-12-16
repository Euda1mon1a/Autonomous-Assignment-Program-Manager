# Developer Documentation

> **Last Updated:** 2025-12-16

Welcome to the Residency Scheduler developer documentation. This guide provides comprehensive information for developers contributing to or extending the application.

## Quick Navigation

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

## Project Overview

Residency Scheduler is a full-stack web application for medical residency program scheduling with ACGME compliance. The application consists of:

- **Backend**: Python/FastAPI REST API with SQLAlchemy ORM
- **Frontend**: Next.js/React with TypeScript and TailwindCSS
- **Database**: PostgreSQL 15+
- **Infrastructure**: Docker and Docker Compose

## Tech Stack Summary

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Core language |
| FastAPI | 0.109+ | Web framework |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.5+ | Data validation |
| Alembic | 1.13+ | Database migrations |
| pytest | 7.0+ | Testing framework |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | 20+ | Runtime |
| Next.js | 14+ | React framework |
| TypeScript | 5.0+ | Type-safe JavaScript |
| TanStack Query | 5.17+ | Data fetching |
| TailwindCSS | 3.3+ | Styling |
| Jest | 29+ | Unit testing |
| Playwright | 1.40+ | E2E testing |

## Getting Started

### Fastest Path to Development

```bash
# 1. Clone the repository
git clone https://github.com/your-org/residency-scheduler.git
cd residency-scheduler

# 2. Copy environment file
cp .env.example .env

# 3. Start with Docker
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

For detailed setup instructions, see [Environment Setup](./environment-setup.md).

## Repository Structure

```
residency-scheduler/
├── backend/                 # Python FastAPI backend
│   ├── app/                 # Application code
│   │   ├── api/routes/      # REST endpoint handlers
│   │   ├── core/            # Configuration and security
│   │   ├── db/              # Database session and types
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── schemas/         # Pydantic validation schemas
│   │   ├── scheduling/      # Scheduling engine and validators
│   │   └── services/        # Business logic services
│   ├── alembic/             # Database migrations
│   ├── tests/               # pytest test suite
│   └── requirements.txt     # Python dependencies
├── frontend/                # Next.js frontend
│   ├── src/                 # Source code
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # React components
│   │   ├── contexts/        # React Context providers
│   │   ├── lib/             # API client and hooks
│   │   └── types/           # TypeScript definitions
│   ├── __tests__/           # Jest unit tests
│   ├── e2e/                 # Playwright E2E tests
│   └── package.json         # Node.js dependencies
├── docs/                    # Documentation
│   ├── development/         # Developer documentation (this folder)
│   └── *.md                 # Other documentation
├── docker-compose.yml       # Production Docker config
├── docker-compose.dev.yml   # Development Docker config
└── README.md                # Project overview
```

## Key Concepts

### ACGME Compliance

The application enforces ACGME (Accreditation Council for Graduate Medical Education) requirements:

- **80-Hour Rule**: Maximum 80 hours/week averaged over 4 weeks
- **1-in-7 Rule**: One 24-hour period off every 7 days
- **Supervision Ratios**: Faculty-to-resident ratios by PGY level
- **Continuous Duty Limits**: Maximum consecutive working hours

### Scheduling Engine

The scheduling engine uses constraint satisfaction algorithms to:

1. Generate compliant schedules automatically
2. Validate existing schedules against ACGME rules
3. Handle emergency coverage and absences
4. Optimize for fairness and coverage requirements

### Data Model

Core entities:

- **Person**: Residents and faculty members
- **Block**: Schedulable time slots (AM/PM sessions)
- **Assignment**: Links people to blocks with roles
- **Absence**: Vacation, deployment, medical leave tracking
- **RotationTemplate**: Reusable activity patterns

## Development Workflow

1. **Fork & Clone**: Fork the repository and clone locally
2. **Branch**: Create a feature branch from `main`
3. **Develop**: Make changes following style guidelines
4. **Test**: Run tests and ensure coverage
5. **Commit**: Use conventional commit messages
6. **PR**: Open a pull request for review

For detailed workflow, see [Workflow](./workflow.md).

## Support

- **Documentation**: Start with this developer guide
- **Issues**: Search existing issues or create new ones
- **Questions**: Use the "question" label on GitHub issues

---

*Last Updated: December 2024*
