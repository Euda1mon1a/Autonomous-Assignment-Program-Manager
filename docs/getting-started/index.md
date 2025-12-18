# Getting Started

Welcome to Residency Scheduler! This guide will help you get up and running quickly.

## Prerequisites

### Required Software

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Git** for version control

### For Local Development (Optional)

- **Python** 3.11+
- **Node.js** 18+ and **npm** 9+
- **PostgreSQL** 15
- **Redis** 7

---

## Quick Installation

=== "Docker (Recommended)"

    The easiest way to run Residency Scheduler:

    ```bash
    # Clone the repository
    git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
    cd Autonomous-Assignment-Program-Manager

    # Copy environment file
    cp .env.example .env

    # Start all services
    docker-compose up -d

    # View logs
    docker-compose logs -f
    ```

=== "Local Development"

    For development with hot reloading:

    **Backend:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    alembic upgrade head
    uvicorn app.main:app --reload
    ```

    **Frontend:**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

---

## Verify Installation

### Check Services

```bash
docker-compose ps
```

Expected output:
```
NAME                    STATUS
backend                 Up
frontend                Up
db                      Up
redis                   Up
```

### Test Endpoints

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

## Next Steps

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-cog: [Installation](installation.md)
Detailed installation instructions for all platforms.
</div>

<div class="feature-card" markdown>
### :material-rocket-launch: [Quick Start](quickstart.md)
First steps after installation.
</div>

<div class="feature-card" markdown>
### :material-wrench: [Configuration](configuration.md)
Environment variables and settings.
</div>

</div>

---

## Need Help?

- Check the [Troubleshooting](../troubleshooting.md) guide
- Review the [User Guide](../user-guide/index.md) for feature explanations
- Read the [User Workflows Guide](../guides/user-workflows.md) for comprehensive examples
- See the [Configuration Guide](configuration.md) for environment setup
- Open a [GitHub Issue](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager/issues) for bugs

---

## Related Documentation

- **[Installation Guide](installation.md)** - Detailed installation steps
- **[Configuration](configuration.md)** - Environment variables and settings
- **[Quick Start](quickstart.md)** - First steps after installation
- **[User Guide](../user-guide/index.md)** - Using the application
- **[Admin Manual](../admin-manual/index.md)** - System administration
- **[Architecture](../architecture/index.md)** - Technical architecture
- **[Documentation Index](../README.md)** - Complete documentation map
