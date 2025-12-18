# MACOS.md - macOS Deployment Reference for Claude

> **Purpose:** Quick reference for deploying this repository on macOS via Terminal
> **Last Updated:** 2025-12-18

---

## Prerequisites Check

Run these commands first to verify prerequisites:

```bash
# Check if Homebrew is installed
brew --version || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Check Docker
docker --version || brew install --cask docker

# Check Git
git --version || brew install git
```

**Important:** Docker Desktop must be running before proceeding.

```bash
# Start Docker Desktop
open -a Docker

# Wait for Docker to be ready (run until no error)
docker info
```

---

## Quick Deploy (Docker - Recommended)

```bash
# 1. Navigate to project root
cd ~/Autonomous-Assignment-Program-Manager  # Or wherever the repo is cloned

# 2. Copy environment file
cp .env.example .env

# 3. Generate and set secrets
SECRET_KEY=$(openssl rand -hex 32)
WEBHOOK_SECRET=$(openssl rand -hex 16)
echo "Add these to .env:"
echo "SECRET_KEY=$SECRET_KEY"
echo "WEBHOOK_SECRET=$WEBHOOK_SECRET"

# 4. Edit .env with required values
# Required: DB_PASSWORD, SECRET_KEY, WEBHOOK_SECRET, NEXT_PUBLIC_API_URL=http://localhost:8000

# 5. Start all services
docker-compose up -d

# 6. Verify deployment
docker-compose ps
curl http://localhost:8000/health
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## Local Development Setup

### Install Dependencies

```bash
brew install python@3.11 node@18 postgresql@15 redis k6
brew services start postgresql@15
brew services start redis
```

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
createdb residency_scheduler  # May need: brew services start postgresql@15
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

### Celery (new terminal, optional)

```bash
cd backend
source venv/bin/activate
../scripts/start-celery.sh both
```

---

## Essential Commands

### Docker

```bash
docker-compose up -d          # Start all services
docker-compose down           # Stop all services
docker-compose logs -f        # View all logs
docker-compose logs -f backend  # View backend logs
docker-compose restart backend  # Restart a service
docker-compose up -d --build  # Rebuild and start
docker-compose exec backend bash  # Shell into container
docker-compose exec db psql -U scheduler -d residency_scheduler  # Database shell
```

### Testing

```bash
# Backend
cd backend && source venv/bin/activate && pytest

# Frontend
cd frontend && npm test

# Load testing
cd load-tests && npm run test:smoke
```

### Database

```bash
# Migrations
cd backend && source venv/bin/activate
alembic upgrade head          # Apply migrations
alembic downgrade -1          # Rollback one
alembic revision --autogenerate -m "description"  # Create migration
```

### Homebrew Services

```bash
brew services list            # Show all services
brew services start postgresql@15
brew services start redis
brew services stop postgresql@15
brew services stop redis
```

---

## Common Issues & Fixes

### Docker not running
```bash
open -a Docker && sleep 10 && docker info
```

### Port in use
```bash
lsof -i :8000  # Find process
kill -9 <PID>  # Kill it
```

### PostgreSQL connection refused
```bash
brew services restart postgresql@15
psql -h localhost -U postgres -l  # Test connection
```

### Redis connection refused
```bash
brew services restart redis
redis-cli ping  # Should return PONG
```

### Python version issues
```bash
python3.11 -m venv venv
source venv/bin/activate
which python  # Should show venv path
```

### Permission denied
```bash
sudo chown -R $(whoami) ~/Autonomous-Assignment-Program-Manager
```

### Docker memory issues
Open Docker Desktop → Settings → Resources → Set Memory to 4GB+

---

## Environment Variables (.env)

**Required:**
```env
DB_PASSWORD=your_secure_password
SECRET_KEY=<64-char-from-openssl-rand-hex-32>
WEBHOOK_SECRET=<32-char-from-openssl-rand-hex-16>
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Optional:**
```env
DEBUG=false
CORS_ORIGINS=["http://localhost:3000"]
REDIS_URL=redis://localhost:6379/0
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

---

## First-Time Setup After Deploy

```bash
# Create admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "YourSecurePassword123!",
    "full_name": "Admin User",
    "role": "admin"
  }'
```

Then open http://localhost:3000 and log in.

---

## Contributing Discoveries Back

**IMPORTANT:** If you encounter and solve a new issue, or discover something useful during deployment, commit it back to the repo so future sessions benefit.

### When to Contribute

- Fixed an undocumented issue
- Found a better command or approach
- Encountered a new macOS-specific gotcha
- Updated a dependency version that matters

### How to Contribute

```bash
# 1. Create a branch (if not already on one)
git checkout -b fix/macos-<brief-description>

# 2. Update the relevant file:
#    - New issue/fix → Add to "Common Issues & Fixes" section in this file
#    - New command → Add to "Essential Commands" section
#    - Major discovery → Update docs/getting-started/macos-deploy.md

# 3. Commit with clear message
git add -A
git commit -m "docs(macos): Add fix for <issue description>"

# 4. Push to remote
git push -u origin fix/macos-<brief-description>

# 5. Tell the user the branch name so they can create a PR
```

### What to Document

For each discovery, include:
1. **Symptom** - What error/problem did you see?
2. **Cause** - Why did it happen? (if known)
3. **Fix** - The command(s) that solved it

Example format for this file:
```markdown
### <Issue name>
```bash
<fix command>
```
```

---

## Full Documentation

For detailed instructions, see:
- [Full macOS Deploy Guide](docs/getting-started/macos-deploy.md)
- [Project Guidelines](CLAUDE.md)
- [Troubleshooting](wiki/Troubleshooting.md)
