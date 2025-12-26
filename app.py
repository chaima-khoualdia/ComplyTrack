from fastapi import FastAPI
from db import init_db
from resources import (user, startup, compliance_status, investor_request, reminder, source, badge, progress, startup_procedure)

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(user.router)
app.include_router(startup.router)
app.include_router(source.router)
app.include_router(reminder.router)
app.include_router(compliance_status.router)
app.include_router(investor_request.router)
app.include_router(badge.router)
app.include_router(progress.router)
app.include_router(startup_procedure.router)