<div align="center">

# ⚡ DevTrack

### API Monitoring & Observability Platform

**Real-time uptime tracking · Response time analytics · Failure alerting · Structured logging**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://postgresql.org)
[![JWT](https://img.shields.io/badge/Auth-JWT-000000?style=flat-square&logo=jsonwebtokens&logoColor=white)](https://jwt.io)
[![APScheduler](https://img.shields.io/badge/Scheduler-APScheduler-FF6B35?style=flat-square)](https://apscheduler.readthedocs.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000?style=flat-square)](https://github.com/psf/black)

---

*DevTrack is a backend-first API monitoring platform that continuously probes your registered endpoints, tracks uptime SLAs, records latency trends, and surfaces failures before your users do — all through a clean REST interface and lightweight dashboard.*

[Getting Started](#-installation--local-setup) · [API Docs](#-api-endpoints-overview) · [Architecture](#-system-architecture) · [Deployment](#-deployment)

</div>

---

## 📋 Table of Contents

- [Feature Highlights](#-feature-highlights)
- [Tech Stack](#-tech-stack)
- [System Architecture](#-system-architecture)
- [Project Structure](#-project-structure)
- [Installation & Local Setup](#-installation--local-setup)
- [Environment Variables](#-environment-variables)
- [Database Setup](#-database-setup)
- [Running the Project](#-running-the-project)
- [API Endpoints Overview](#-api-endpoints-overview)
- [Authentication Flow](#-authentication-flow)
- [Monitoring Workflow](#-monitoring-workflow)
- [Screenshots](#-screenshots)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Feature Highlights

| Category | Features |
|---|---|
| **Monitoring** | Automated HTTP health checks via APScheduler · configurable polling intervals · multi-endpoint support |
| **Observability** | Response time tracking · uptime percentage calculation · failure streak detection |
| **Alerting** | Failure logging with timestamps · status-change events · historical incident timeline |
| **Auth** | JWT-based session management · OTP email verification · secure password hashing |
| **API** | Full REST API for endpoint CRUD · paginated log queries · dashboard summary endpoint |
| **Logging** | Structured JSON logging · request tracing · scheduler job audit trail |
| **Developer UX** | Auto-generated OpenAPI/Swagger docs · clean error responses · environment-based config |

---

## 🛠 Tech Stack

```
Backend Framework   FastAPI 0.110+        Async-first, OpenAPI auto-docs, Pydantic v2
Database            PostgreSQL 15+        Relational storage for endpoints, logs, users
ORM / Migrations    SQLAlchemy 2.0        Async ORM · Alembic for schema migrations
Task Scheduling     APScheduler 3.x       In-process scheduler driving health check jobs
Authentication      python-jose + bcrypt  JWT signing/verification · password hashing
Email / OTP         FastAPI-Mail           SMTP email delivery for OTP verification
Validation          Pydantic v2           Request/response schema enforcement
Logging             Python logging + JSON Structured log output for observability pipelines
Server              Uvicorn               ASGI server for production deployment
```

---

## 🏗 System Architecture

DevTrack follows a clean layered architecture: an HTTP layer for user-facing APIs, a service layer encapsulating business logic, a scheduler layer running independently for background probing, and a persistence layer backed by PostgreSQL.

```mermaid
graph TB
    subgraph Client["Client Layer"]
        UI[Dashboard / Browser]
        EXT[External API Consumers]
    end

    subgraph API["FastAPI Application"]
        direction TB
        RO[Router Layer<br/>auth · endpoints · logs · dashboard]
        MW[Middleware<br/>JWT Validation · Request Logging · CORS]
        SVC[Service Layer<br/>MonitorService · AuthService · LogService]
        DEP[Dependencies<br/>DB Session · Current User · Rate Limit]
    end

    subgraph Scheduler["Background Scheduler (APScheduler)"]
        JM[Job Manager]
        HC[Health Check Worker]
        RP[Retry Policy]
    end

    subgraph DB["Persistence Layer"]
        PG[(PostgreSQL)]
        subgraph Tables
            T1[users]
            T2[endpoints]
            T3[check_logs]
            T4[otp_tokens]
        end
    end

    subgraph Notif["Notification Layer"]
        SMTP[SMTP / Email]
    end

    UI --> RO
    EXT --> RO
    RO --> MW
    MW --> SVC
    SVC --> DEP
    DEP --> PG
    SVC --> SMTP

    JM --> HC
    HC --> RP
    HC -->|probe registered endpoints| T2
    HC -->|write results| T3
    HC -->|update uptime stats| T2

    PG --- T1
    PG --- T2
    PG --- T3
    PG --- T4
```

### Key Design Decisions

**Scheduler isolation** — APScheduler runs within the same process but maintains its own thread pool, ensuring health check jobs don't block request handling. The job registry is seeded from the database at startup and dynamically updated when endpoints are added or removed.

**Append-only log model** — `check_logs` is never updated in-place; every health check result is a new row. Uptime percentages and P95 latency are computed from aggregated queries, giving a full historical audit trail.

**Auth separation** — OTP tokens are stored in a dedicated table with TTL enforcement at the application layer, keeping the `users` table clean and the verification flow stateless between steps.

---

## 📁 Project Structure

```
devtrack/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app factory, lifespan hooks, router registration
│   ├── auth.py                  # JWT utilities, password hashing, token validation
│   ├── crud.py                  # Database operations (create, read, update, delete)
│   ├── database.py              # SQLAlchemy engine + session factory
│   ├── models.py                # ORM models — User, Endpoint, CheckLog, OTPToken
│   ├── schemas.py               # Pydantic request/response schemas
│   │
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py              # /auth/register, /auth/login, /auth/verify-otp
│   │   ├── endpoints.py         # CRUD routes for monitored API endpoints
│   │   └── logs.py              # Check log queries and failure history
│   │
│   └── services/
│       ├── __init__.py
│       ├── email.py             # OTP email delivery via SMTP
│       ├── monitor.py           # Health check execution + result persistence
│       └── scheduler.py        # APScheduler setup and job registration
│
├── frontend/
│   ├── index.html               # Monitoring dashboard UI
│   ├── script.js                # Dashboard logic — fetch + render check data
│   └── style.css                # Dashboard styles
│
├── requirements.txt
└── README.md
```

---

## 🚀 Installation & Local Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- A virtual environment manager (`venv` or `pyenv`)
- An SMTP account (Gmail app password recommended for development)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/devtrack.git
cd devtrack
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your database credentials, secret keys, and SMTP settings
```

---

## 🔐 Environment Variables

```ini
# .env.example

# ── Application ───────────────────────────────────────────────
APP_ENV=development
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# ── Database ──────────────────────────────────────────────────
DATABASE_URL=postgresql+asyncpg://devtrack_user:your_password@localhost:5432/devtrack_db

# ── Security ──────────────────────────────────────────────────
SECRET_KEY=your-256-bit-random-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# ── OTP / Email ───────────────────────────────────────────────
OTP_EXPIRE_MINUTES=10
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@devtrack.io
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_STARTTLS=true
MAIL_SSL_TLS=false

# ── Scheduler ─────────────────────────────────────────────────
DEFAULT_CHECK_INTERVAL_SECONDS=60
MAX_CONCURRENT_CHECKS=10
CHECK_TIMEOUT_SECONDS=10
```

> **Security note:** Never commit your `.env` file. The `.env.example` is the only file that belongs in version control.

---

## 🗄 Database Setup

### 1. Create the database and user

```sql
-- Run as PostgreSQL superuser (psql -U postgres)
CREATE USER devtrack_user WITH PASSWORD 'your_password';
CREATE DATABASE devtrack_db OWNER devtrack_user;
GRANT ALL PRIVILEGES ON DATABASE devtrack_db TO devtrack_user;
```

### 2. Run Alembic migrations

```bash
# Apply all migrations to bring the schema to the latest version
alembic upgrade head

# Check current migration state
alembic current

# View migration history
alembic history --verbose
```

### 3. Database schema overview

```
users           → id, email, hashed_password, is_verified, created_at
otp_tokens      → id, user_id (FK), token, expires_at, is_used
endpoints       → id, user_id (FK), name, url, method, headers (JSONB),
                  interval_seconds, is_active, uptime_pct, last_checked_at
check_logs      → id, endpoint_id (FK), status_code, response_time_ms,
                  is_success, error_message, checked_at
```

---

## ▶ Running the Project

### Development server (with auto-reload)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --no-access-log
```

Once running, the API is available at:

| Interface | URL |
|---|---|
| REST API | `http://localhost:8000` |
| Swagger UI | `http://localhost:8000/docs` |
| ReDoc | `http://localhost:8000/redoc` |
| OpenAPI JSON | `http://localhost:8000/openapi.json` |

---

## 📡 API Endpoints Overview

### Authentication

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | ❌ | Register new user account |
| `POST` | `/api/v1/auth/verify-otp` | ❌ | Verify email via OTP code |
| `POST` | `/api/v1/auth/login` | ❌ | Authenticate and receive JWT |
| `POST` | `/api/v1/auth/refresh` | ✅ | Refresh access token |
| `POST` | `/api/v1/auth/logout` | ✅ | Invalidate refresh token |

### Endpoint Management

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/endpoints` | ✅ | List all monitored endpoints (paginated) |
| `POST` | `/api/v1/endpoints` | ✅ | Register a new endpoint for monitoring |
| `GET` | `/api/v1/endpoints/{id}` | ✅ | Get endpoint detail + current stats |
| `PATCH` | `/api/v1/endpoints/{id}` | ✅ | Update endpoint config (URL, interval, etc.) |
| `DELETE` | `/api/v1/endpoints/{id}` | ✅ | Remove endpoint and cancel its scheduler job |
| `POST` | `/api/v1/endpoints/{id}/toggle` | ✅ | Pause or resume monitoring |

### Logs & History

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/logs` | ✅ | Query check logs (filterable, paginated) |
| `GET` | `/api/v1/logs/{endpoint_id}` | ✅ | Logs for a specific endpoint |
| `GET` | `/api/v1/logs/{endpoint_id}/failures` | ✅ | Only failed checks (status ≥ 400 or timeout) |

### Dashboard

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/dashboard/summary` | ✅ | Aggregated uptime, latency, failure counts |
| `GET` | `/api/v1/dashboard/uptime` | ✅ | Per-endpoint uptime percentages |
| `GET` | `/api/v1/dashboard/latency` | ✅ | Response time trends (1h / 24h / 7d) |

---

## 🔑 Authentication Flow

DevTrack uses a two-step registration flow (email + OTP) followed by stateless JWT authentication.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant API as FastAPI
    participant DB as PostgreSQL
    participant Mail as SMTP

    User->>API: POST /auth/register {email, password}
    API->>DB: Create user (is_verified=false)
    API->>DB: Generate OTP token (TTL: 10min)
    API->>Mail: Send OTP email
    API-->>User: 201 {message: "Check your email"}

    User->>API: POST /auth/verify-otp {email, otp}
    API->>DB: Validate OTP (not expired, not used)
    DB-->>API: Token valid
    API->>DB: Mark user is_verified=true, OTP is_used=true
    API-->>User: 200 {message: "Email verified"}

    User->>API: POST /auth/login {email, password}
    API->>DB: Fetch user, verify password hash
    DB-->>API: User record
    API-->>User: 200 {access_token, refresh_token, token_type}

    Note over User,API: Subsequent authenticated requests
    User->>API: GET /endpoints (Authorization: Bearer <token>)
    API->>API: Decode & validate JWT signature + expiry
    API-->>User: 200 {endpoints: [...]}
```

**Token structure:**
- **Access token** — short-lived (60 min), carries `sub` (user_id) and `email` claims
- **Refresh token** — long-lived (7 days), stored reference in DB, rotated on each use
- **OTP** — 6-digit numeric code, single-use, 10-minute TTL

---

## 📊 Monitoring Workflow

The scheduler is bootstrapped at application startup. It loads all active endpoints from the database and schedules an `IntervalTrigger` job for each. Jobs run in a background thread pool and do not block the ASGI event loop.

```mermaid
flowchart TD
    A([App Startup]) --> B[Load active endpoints from DB]
    B --> C[Register APScheduler jobs\none per endpoint]
    C --> D{Scheduler running}

    D -->|Every interval_seconds| E[Execute health check job]
    E --> F[HTTP request to endpoint URL]
    F --> G{Response received?}

    G -->|Yes| H{Status code\n== expected?}
    G -->|Timeout / Network error| I[Log failure\nerror_message = exception]

    H -->|Yes| J[Log success\nrecord response_time_ms]
    H -->|No| K[Log failure\nrecord actual status_code]

    J --> L[Update endpoint:\nlast_checked_at, uptime_pct]
    I --> L
    K --> L

    L --> M{Consecutive\nfailures ≥ threshold?}
    M -->|Yes| N[Emit alert event\nfuture: webhook / email]
    M -->|No| D

    N --> D

    style A fill:#1a1a2e,color:#fff
    style D fill:#16213e,color:#fff
    style J fill:#0f3460,color:#fff
    style I fill:#533483,color:#fff
    style K fill:#533483,color:#fff
    style N fill:#e94560,color:#fff
```

**Uptime calculation** is a rolling window query:

```sql
SELECT
    COUNT(*) FILTER (WHERE is_success = true)::FLOAT
    / NULLIF(COUNT(*), 0) * 100 AS uptime_pct
FROM check_logs
WHERE endpoint_id = $1
  AND checked_at >= NOW() - INTERVAL '24 hours';
```

---

## 📸 Screenshots

> *Replace the placeholders below with actual screenshots after deployment.*

### Dashboard Summary
```
[ Screenshot: /screenshots/dashboard-summary.png ]
Uptime overview cards · Top failing endpoints · 24h latency sparklines
```

### Endpoint Detail View
```
[ Screenshot: /screenshots/endpoint-detail.png ]
Response time chart · Uptime calendar · Recent check log table
```

### Swagger UI
```
[ Screenshot: /screenshots/swagger-ui.png ]
Auto-generated OpenAPI documentation at /docs
```

### Failure Incident Timeline
```
[ Screenshot: /screenshots/failure-timeline.png ]
Chronological log of all failed checks with error messages
```

---

## 🔭 Future Improvements

- **Webhook & Slack alerts** — push notifications to external channels on status change events
- **Multi-region probing** — run health checks from geographically distributed agents
- **SLA reporting** — monthly uptime PDF reports with P50/P95/P99 latency breakdowns
- **Certificate expiry monitoring** — alert before SSL certificates expire
- **Custom assertion rules** — validate response body content, not just status codes
- **Rate limiting** — per-user API rate limits with Redis-backed sliding windows
- **Prometheus metrics endpoint** — expose `/metrics` for Grafana scraping
- **WebSocket live feed** — push real-time check results to the dashboard without polling
- **Team workspaces** — multi-user accounts with role-based access control (RBAC)
- **Incident management** — acknowledge, resolve, and annotate incidents from the API

---

## 🤝 Contributing

Contributions are welcome. Please follow these steps:

1. **Fork** the repository and create a feature branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Write tests** for any new functionality (pytest, located in `tests/`)
   ```bash
   pytest tests/ -v --cov=app
   ```

3. **Lint and format** before committing
   ```bash
   black app/ tests/
   ruff check app/ tests/
   ```

4. **Open a pull request** with a clear description of the change and any related issue numbers.

For significant changes, please open an issue first to discuss the approach.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2024 DevTrack Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

<div align="center">

Built with FastAPI · PostgreSQL · APScheduler

*If DevTrack is useful to you, consider leaving a ⭐ on GitHub.*

</div>