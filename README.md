# DevTrack - API Monitoring System

A REST API built with **FastAPI + PostgreSQL + SQLAlchemy** that lets you register API endpoints, trigger health checks, measure response times, and view uptime analytics.

---

## Project Structure

```
devtrack/
├── app/                     (Backend API)
│   ├── __init__.py
│   ├── main.py            # FastAPI app factory, middleware, router registration
│   ├── database.py        # SQLAlchemy engine, session, Base, get_db dependency
│   ├── models.py          # ORM models: Endpoint, CheckLog
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py            # Database access layer (no business logic)
│   ├── services/
│   │   ├── __init__.py
│   │   └── monitor.py     # Health check logic + summary analytics
│   └── routers/
│       ├── __init__.py
│       ├── endpoints.py   # /endpoints routes
│       └── logs.py        # /logs routes
├── frontend/                (Web UI)
│   ├── index.html         # Single-page application
│   ├── style.css          # Classic minimal theme
│   └── script.js          # Vanilla JavaScript, API integration
├── .env.example
├── requirements.txt
└── README.md
```

---

## 1. PostgreSQL Setup

### Install PostgreSQL (Ubuntu/Debian)
```bash
sudo apt update && sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Create the database and user
```bash
# Connect as the postgres superuser
sudo -u postgres psql          # Linux

# Inside psql:
CREATE USER devtrack_user WITH PASSWORD 'yourpassword';
CREATE DATABASE devtrack OWNER devtrack_user;
GRANT ALL PRIVILEGES ON DATABASE devtrack TO devtrack_user;
\q
```

---

## 2. Project Setup

### Clone / enter the project
```bash
cd devtrack
```

### Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate          # Linux / macOS
# venv\Scripts\activate           # Windows
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Configure environment variables
```bash
cp .env.example .env
# Edit .env and set your real DATABASE_URL
```

Your `.env` file should look like:
```
DATABASE_URL=postgresql://devtrack_user:yourpassword@localhost:5432/devtrack
```

---

## 3. Run the Backend API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API root:  http://localhost:8000/
- Swagger UI: http://localhost:8000/docs
- ReDoc:      http://localhost:8000/redoc

> Tables are created automatically on first startup via `metadata.create_all()`.

---

## 4. Run the Frontend

In a separate terminal, serve the frontend files:

```bash
cd frontend
python3 -m http.server 8080
```

Or use any HTTP server (nginx, Apache, etc.).

**Access the UI:** http://localhost:8080

The frontend connects to the API at `http://127.0.0.1:8000` and provides:
- Dashboard to view registered endpoints
- Register new endpoints for monitoring
- Trigger manual health checks
- View endpoint summary (uptime %, avg response time)
- View all check logs
- Download logs as text file

---

## 5. API Reference

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create a new user account |
| `POST` | `/auth/login` | Login and receive a Bearer token |

All `/endpoints/*` and `/logs/*` routes require:

`Authorization: Bearer <token>`

### Endpoint Management

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/endpoints/` | Register a new endpoint |
| `GET` | `/endpoints/` | List all endpoints |
| `GET` | `/endpoints/{id}` | Get a single endpoint |
| `DELETE` | `/endpoints/{id}/` | Delete endpoint + all its logs |

### Health Checks

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/endpoints/{id}/check/` | Trigger a health check |
| `GET` | `/endpoints/{id}/summary/` | Uptime % + avg response time |

### Logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/logs/` | All check logs (most recent first) |
| `GET` | `/endpoints/{id}/logs/` | Logs for a specific endpoint |

---

## 6. Example Requests

### Register + login

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}'

TOKEN=$(curl -sS -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' \
  | python3 -c 'import sys, json; print(json.load(sys.stdin)["access_token"])')
```

### Register an endpoint
```bash
curl -X POST http://localhost:8000/endpoints/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "GitHub API", "url": "https://api.github.com"}'
```

### Trigger a health check
```bash
curl -X POST http://localhost:8000/endpoints/1/check/ \
  -H "Authorization: Bearer $TOKEN"
```

### Get uptime summary
```bash
curl http://localhost:8000/endpoints/1/summary/ \
  -H "Authorization: Bearer $TOKEN"
```

### View logs
```bash
curl "http://localhost:8000/endpoints/1/logs/?limit=10" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 7. Architecture Notes

### Why this structure?

| Layer | File | Responsibility |
|-------|------|---------------|
| **ORM Models** | `models.py` | Database schema as Python classes |
| **Schemas** | `schemas.py` | Validate inputs, shape API responses |
| **CRUD** | `crud.py` | Pure DB queries - no HTTP or business logic |
| **Service** | `services/monitor.py` | Business logic - health checks, analytics |
| **Routers** | `routers/` | HTTP handlers - thin wrappers over CRUD/services |
| **App** | `main.py` | Wires everything together |

This separation means:
- **CRUD layer** is independently testable - just pass a mock `Session`
- **Service layer** can be reused by a background scheduler later (e.g. APScheduler)
- **Routers** stay thin and readable

### Key decisions
- `pool_pre_ping=True` on the engine ensures stale connections are recycled automatically
- `cascade="all, delete-orphan"` on the `Endpoint → CheckLog` relationship means deleting an endpoint cleans up all its logs
- `StatusEnum` is a native Python `enum` stored as a PostgreSQL `ENUM` type via SQLAlchemy - enforced at both the DB and application level
- Response time uses `time.perf_counter()` (monotonic, high-resolution) rather than `datetime.now()` for accuracy

---

## 8. Future Improvements

### Planned features:

- **Email Notifications** - Send email alerts when an endpoint goes DOWN or comes back UP
  - Configurable recipients per endpoint
  - Customizable alert thresholds (consecutive failures before alerting)
  - Email templates for clear, actionable notifications

- **Scheduled Health Checks** - Automatically monitor endpoints at regular intervals (e.g., every 5 minutes)
  - Use APScheduler or Celery for background tasks
  - Configurable check frequency per endpoint
  - Disable/pause monitoring for specific endpoints

- **Dashboard Enhancements**
  - Real-time status updates with WebSockets
  - Uptime graphs and trend analytics
  - Endpoint status history timeline
  - Response time trends and p95/p99 metrics

- **Authentication & Authorization**
  - User accounts and role-based access control
  - API key authentication for programmatic access
  - Multi-tenant support

- **Data Export**
  - Export logs and analytics to CSV/JSON
  - Scheduled report generation and delivery
  - Integration with external monitoring tools (Datadog, New Relic, etc.)

- **Advanced Monitoring**
  - Custom HTTP headers and authentication support
  - SSL/TLS certificate expiration monitoring
  - DNS resolution checks
  - Webhook notifications (Slack, Discord, etc.)

- **Infrastructure**
  - Docker and Docker Compose setup for easy deployment
  - Kubernetes manifests for scaling
  - CI/CD pipeline with GitHub Actions
  - Unit and integration test suite with pytest
