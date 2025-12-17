# Database Schema

Data models and relationships.

---

## Overview

- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic

---

## Core Tables

### People & Assignments

```
Person
├── id (UUID)
├── name
├── email
├── type (resident/faculty)
├── pgy_level
└── specialty

Assignment
├── id (UUID)
├── block_id → Block
├── person_id → Person
├── role
└── created_at

Block
├── id (UUID)
├── date
├── period (AM/PM)
└── rotation_id → RotationTemplate
```

### Schedule Management

```
RotationTemplate
├── id (UUID)
├── name
├── type
├── capacity
└── supervision_ratio

Absence
├── id (UUID)
├── person_id → Person
├── type
├── start_date
├── end_date
└── notes
```

---

## Resilience Tables

```
ResilienceAlert
├── id (UUID)
├── level
├── message
├── resolved_at
└── created_at

ContingencyScenario
├── id (UUID)
├── description
├── impact_score
└── mitigation_plan
```

---

## Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```
