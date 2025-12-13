# Residency Scheduler

A standalone, production-ready residency scheduling application with ACGME compliance validation.

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: Next.js (React) + TailwindCSS
- **Database**: PostgreSQL

## Features

- **Rotation Templates**: Reusable activity patterns with constraints (clinic capacity, specialty requirements, ACGME supervision ratios)
- **Scheduling Engine**: Greedy algorithm with constraint-based assignment
- **ACGME Validation**: 80-hour rule, 1-in-7 days off, supervision ratios
- **Emergency Coverage**: Handle deployments, TDY, medical emergencies with automatic replacement finding
- **Calendar-First UI**: Clean, intuitive interface designed for clinicians

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Running with Docker

```bash
# Clone the repository
git clone <repository-url>
cd residency-scheduler

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
residency-scheduler/
├── backend/
│   ├── app/
│   │   ├── api/routes/       # API endpoints
│   │   ├── core/             # Configuration
│   │   ├── db/               # Database connection
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── scheduling/       # Scheduling engine
│   │   └── services/         # Business logic
│   ├── alembic/              # Database migrations
│   └── tests/                # Backend tests
├── frontend/
│   └── src/
│       ├── app/              # Next.js pages
│       ├── components/       # React components
│       ├── lib/              # API client & hooks
│       └── types/            # TypeScript types
├── docker-compose.yml        # Docker configuration
└── README.md
```

## API Endpoints

### People
- `GET /api/people` - List all people
- `GET /api/people/residents` - List residents
- `GET /api/people/faculty` - List faculty
- `POST /api/people` - Create person
- `PUT /api/people/{id}` - Update person
- `DELETE /api/people/{id}` - Delete person

### Rotation Templates
- `GET /api/rotation-templates` - List templates
- `POST /api/rotation-templates` - Create template
- `PUT /api/rotation-templates/{id}` - Update template
- `DELETE /api/rotation-templates/{id}` - Delete template

### Schedule
- `GET /api/schedule/{start_date}/{end_date}` - Get schedule
- `POST /api/schedule/generate` - Generate schedule
- `GET /api/schedule/validate` - Validate ACGME compliance
- `POST /api/schedule/emergency-coverage` - Handle emergency absence

### Absences
- `GET /api/absences` - List absences
- `POST /api/absences` - Create absence
- `PUT /api/absences/{id}` - Update absence
- `DELETE /api/absences/{id}` - Delete absence

## ACGME Compliance

The scheduler validates against ACGME requirements:

- **80-Hour Rule**: Maximum 80 hours/week averaged over 4 weeks
- **1-in-7 Rule**: One 24-hour period off every 7 days
- **Supervision Ratios**:
  - PGY-1: 1 faculty per 2 residents
  - PGY-2/3: 1 faculty per 4 residents

## Database Schema

- `people`: Residents and faculty members
- `blocks`: Half-day scheduling blocks (730/year: 365 days × AM/PM)
- `rotation_templates`: Reusable activity patterns with constraints
- `assignments`: The actual schedule
- `absences`: Leave, deployments, TDY
- `call_assignments`: Overnight and weekend call
- `schedule_runs`: Audit trail for generated schedules

## Development Timeline

- **Week 1**: Backend foundation (done)
- **Week 2**: Frontend foundation (done)
- **Week 3**: Advanced features
- **Weeks 4-8**: Security, testing, deployment
- **Weeks 9-13**: Polish, documentation, production

## License

MIT
