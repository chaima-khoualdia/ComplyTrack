import os
import logging
from fastapi import FastAPI
from db import init_db
from resources import (
    user,
    startup,
    compliance_status,
    investor_request,
    reminder,
    source,
    badge,
    startup_procedure,
    compliance_status,
    auth,
    request,
    stats,
)
from services.scheduler_service import start_scheduler, stop_scheduler

# Configure logging early and verbosely; force=True to override prior handlers
log_level_name = os.getenv("LOG_LEVEL", "DEBUG").upper()
log_level = getattr(logging, log_level_name, logging.DEBUG)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
)

for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
    logging.getLogger(logger_name).setLevel(log_level)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Startup API",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=True,
)

@app.on_event("startup")
def on_startup():
    init_db()
    # Start the scheduler for automated reminder emails
    logger.info("Starting automated reminder email scheduler...")
    start_scheduler()

@app.on_event("shutdown")
def on_shutdown():
    # Stop the scheduler gracefully
    logger.info("Stopping scheduler...")
    stop_scheduler()

# Give each router a clear prefix
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(startup.router)
app.include_router(source.router)
app.include_router(reminder.router)
app.include_router(compliance_status.router)
app.include_router(investor_request.router)
app.include_router(badge.router)
app.include_router(startup_procedure.router)
app.include_router(request.router)
app.include_router(stats.router)