# DevTrack - API Monitoring System

A comprehensive REST API monitoring platform built with **FastAPI + PostgreSQL + SQLAlchemy**. Features include user authentication with OTP email verification, automated health checks with configurable intervals, real-time monitoring dashboards, and detailed uptime analytics.

---

## Features

- **User Authentication** — Registration with OTP email verification, JWT-based sessions, bcrypt password hashing
- **Endpoint Management** — Register and manage API endpoints with configurable health check intervals (sub-minute precision)
- **Automated Monitoring** — Background scheduler for periodic checks; manual triggers supported; detailed response metrics (status code, response time, errors)
- **Analytics & Reporting** — Historical check logs, response time statistics, uptime percentage calculations, error tracking
- **Email Notifications** — SMTP integration (Gmail, Outlook, Office 365, custom) with 6-digit OTP, 10-minute expiration
- **Web Dashboard** — Single-page application for real-time status visualization and historical analytics

---

## Project Structure

```
devtrack/
├── app/
│   ├── main.py                   # FastAPI app factory, middleware, router setup
│   ├── auth.py                   # JWT token creation and validation
│   ├── database.py               # SQLAlchemy engine, session, Base config
│   ├── models.py                 # ORM models: User, Endpoint, CheckLog
│   ├── schemas.py                # Pydantic request/response schemas
│   ├── crud.py                   # Database operations layer
│   ├── services/
│   │   ├── email.py              # SMTP email sending, OTP generation
│   │   ├── monitor.py            # Health check logic + analytics
│   │   └── scheduler.py          # APScheduler background job management
│   └── routers/
│       ├── auth.py               # /auth routes
│       ├── endpoints.py          # /endpoints routes
│       └── logs.py               # /logs routes
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── requirements.txt
├── .env.example
└── EMAIL_SETUP.md
```

---

## Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip or conda

---

## Setup & Installation

### 1. PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS
brew install postgresql && brew services start postgresql
```

Create the database:

```bash
sudo -u postgres psql
```
```sql
CREATE USER devtrack_user WITH PASSWORD 'yourpassword';
CREATE DATABASE devtrack OWNER devtrack_user;
GRANT ALL PRIVILEGES ON DATABASE devtrack TO devtrack_user;
\q
```

### 2. Python Environment

```bash
cd devtrack
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Database
DATABASE_URL=postgresql://devtrack_user:yourpassword@localhost:5432/devtrack

# JWT
JWT_SECRET=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_MINUTES=60

# SMTP (optional, for OTP verification)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Run the Application

Tables are created automatically on first startup.

```bash
# Backend (http://localhost:8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend — in a separate terminal (http://localhost:808/frontend)
cd frontend && python3 -m http.server 8080
```

Interactive API docs available at: http://localhost:8000/docs

---

## API Reference

All `/endpoints/*` and `/logs/*` routes require: `Authorization: Bearer <token>`

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register new user (sends OTP) |
| `POST` | `/auth/verify-otp` | Verify OTP and receive access token |
| `POST` | `/auth/login` | Login with username/password |

### Endpoint Management

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/endpoints/` | List all endpoints |
| `POST` | `/endpoints/` | Register a new endpoint |
| `GET` | `/endpoints/{id}` | Get endpoint details |
| `PUT` | `/endpoints/{id}` | Update endpoint |
| `DELETE` | `/endpoints/{id}/` | Delete endpoint and all its logs |
| `POST` | `/endpoints/{id}/check/` | Trigger a manual health check |
| `GET` | `/endpoints/{id}/summary/` | Uptime % and avg response time |

### Logs

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/logs/` | All check logs (most recent first) |
| `GET` | `/endpoints/{id}/logs/` | Logs for a specific endpoint |

---

## How It Works

1. **Register** — Create an account; OTP is sent to your email
2. **Verify** — Enter OTP to confirm email and receive a JWT
3. **Add Endpoints** — Register URLs to monitor with a check interval
4. **Automated Monitoring** — APScheduler sends HEAD/GET requests at the configured interval; status code, response time, and errors are recorded
5. **Analytics** — View uptime percentages, response time trends, and full check history from the dashboard

### Health Check Intervals (seconds)

`10` · `60` · `300` · `600` · `900` · `3600` · or any custom value

---

## Architecture

| Layer | File | Responsibility |
|-------|------|----------------|
| ORM Models | `models.py` | Database schema as Python classes |
| Schemas | `schemas.py` | Input validation and API response shaping |
| CRUD | `crud.py` | Pure DB queries — no HTTP or business logic |
| Services | `services/monitor.py` | Health check logic and analytics |
| Routers | `routers/` | Thin HTTP handlers over CRUD/services |
| App | `main.py` | Wires everything together |

**Key decisions:**
- `pool_pre_ping=True` recycles stale DB connections automatically
- `cascade="all, delete-orphan"` on `Endpoint → CheckLog` cleans up logs on endpoint deletion
- `StatusEnum` is enforced at both DB (PostgreSQL ENUM) and application level
- Response time uses `time.perf_counter()` (monotonic, high-resolution) for accuracy

### Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | FastAPI 0.111.0 + Uvicorn |
| Database | PostgreSQL + SQLAlchemy 2.0 |
| Auth | JWT + bcrypt |
| Scheduling | APScheduler 3.11 |
| Validation | Pydantic 2.7 |
| HTTP Client | Requests |
| Email | smtplib |
| Config | python-dotenv |

---

## Roadmap

- [ ] Email/webhook/Slack alerts on status changes
- [ ] SLA monitoring and reporting
- [ ] Real-time WebSocket dashboard updates
- [ ] Response time trend graphs (p95/p99)
- [ ] SSL/TLS certificate expiration monitoring
- [ ] Custom HTTP headers and auth support per endpoint
- [ ] CSV/JSON log export and scheduled reports
- [ ] Docker + Docker Compose setup
- [ ] API rate limiting and caching
- [ ] CI/CD pipeline with GitHub Actions + pytest suite
