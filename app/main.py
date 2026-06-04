from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, ensure_schema
from app import models
from app.routers import endpoints, logs, auth
from app.services.scheduler import start_scheduler, stop_scheduler

app = FastAPI(
    title="DevTrack",
    description=(
        "A production-grade API monitoring system. "
        "Register endpoints, trigger health checks, and view uptime analytics."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
   allow_origins=[
    "http://localhost:8080",
    "http://127.0.0.1:8080",
    "http://0.0.0.0:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(endpoints.router)
app.include_router(logs.router)
app.include_router(auth.router)


@app.on_event("startup")
def startup_event() -> None:
    models.Base.metadata.create_all(bind=engine)
    ensure_schema()
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event() -> None:
    stop_scheduler()


@app.get("/", tags=["Health"])
def root():
    return {"service": "DevTrack", "status": "running", "docs": "/docs"}
