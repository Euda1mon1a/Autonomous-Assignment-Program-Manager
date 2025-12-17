---
hide:
  - navigation
  - toc
---

<div class="hero-section" markdown>

# Residency Scheduler

**A comprehensive medical residency scheduling system with ACGME compliance**

Built with the spirit of caring for those who care for others

[Get Started](getting-started/index.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager){ .md-button }

</div>

---

## Key Features

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-calendar-clock: Automated Scheduling
Constraint-based algorithm generates ACGME-compliant schedules automatically, saving hours of manual work.
</div>

<div class="feature-card" markdown>
### :material-shield-check: ACGME Compliance
Real-time monitoring of 80-hour rule, 1-in-7 day off, and supervision ratios with violation tracking.
</div>

<div class="feature-card" markdown>
### :material-account-group: Role-Based Access
Secure multi-user system with Admin, Coordinator, Faculty, and Resident roles with appropriate permissions.
</div>

<div class="feature-card" markdown>
### :material-swap-horizontal: Swap Marketplace
5-factor auto-matching algorithm helps residents find compatible shift swaps efficiently.
</div>

<div class="feature-card" markdown>
### :material-chart-line: Analytics Dashboard
Coverage, fairness, and workload metrics with Pareto optimization for balanced scheduling.
</div>

<div class="feature-card" markdown>
### :material-shield-alert: Resilience Framework
80% utilization monitoring, N-1/N-2 contingency analysis, and Defense in Depth safety levels.
</div>

</div>

---

## Quick Start

=== "Docker (Recommended)"

    ```bash
    # Clone the repository
    git clone https://github.com/Euda1mon1a/Autonomous-Assignment-Program-Manager.git
    cd Autonomous-Assignment-Program-Manager

    # Configure environment
    cp .env.example .env
    # Edit .env with your settings

    # Start all services
    docker-compose up -d

    # Access the application
    # Frontend: http://localhost:3000
    # API Docs: http://localhost:8000/docs
    ```

=== "Local Development"

    ```bash
    # Backend
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    alembic upgrade head
    uvicorn app.main:app --reload

    # Frontend (in another terminal)
    cd frontend
    npm install
    npm run dev
    ```

---

## Tech Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Frontend** | Next.js + React + TypeScript | 14.2.35 / 18.2.0 |
| **Backend** | FastAPI + Python | 0.109.0 / 3.11+ |
| **Database** | PostgreSQL + SQLAlchemy | 15 / 2.0 |
| **Task Queue** | Celery + Redis | 5.6 / 7 |
| **Optimization** | OR-Tools, PuLP, pymoo | Latest |

---

## Project Status

| Component | Status |
|-----------|--------|
| Backend API | <span class="status-badge production">Production Ready</span> |
| Frontend UI | <span class="status-badge production">Production Ready</span> |
| ACGME Compliance | <span class="status-badge production">Fully Implemented</span> |
| Resilience Framework | <span class="status-badge production">Production Ready</span> |
| Documentation | <span class="status-badge production">Complete</span> |

---

## Documentation Sections

<div class="feature-grid" markdown>

<div class="feature-card" markdown>
### :material-rocket-launch: [Getting Started](getting-started/index.md)
Installation, setup, and first steps with Residency Scheduler.
</div>

<div class="feature-card" markdown>
### :material-book-open: [User Guide](user-guide/index.md)
Learn how to use all features of the application.
</div>

<div class="feature-card" markdown>
### :material-cog: [Admin Manual](admin-manual/index.md)
System administration and configuration guides.
</div>

<div class="feature-card" markdown>
### :material-api: [API Reference](api/index.md)
Complete REST API documentation for developers.
</div>

<div class="feature-card" markdown>
### :material-sitemap: [Architecture](architecture/index.md)
System design, components, and technical decisions.
</div>

<div class="feature-card" markdown>
### :material-code-braces: [Development](development/index.md)
Contributing guidelines and development setup.
</div>

</div>

---

<div style="text-align: center; margin-top: 3rem; opacity: 0.7;">

Made with :material-heart:{ .pulse } by dedicated healthcare technology professionals

</div>
