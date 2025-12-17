# Development Setup

Set up your development environment.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git
- PostgreSQL 15 (for local dev)
- Redis 7 (for local dev)

---

## Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
createdb residency_scheduler

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

---

## Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## Docker Development

For full-stack development with Docker:

```bash
# Start all services with hot reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# View logs
docker-compose logs -f backend
```

---

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- ESLint
- Prettier
- Tailwind CSS IntelliSense

### PyCharm

Configure:
- Python interpreter (venv)
- Django/FastAPI support
- Database tools
