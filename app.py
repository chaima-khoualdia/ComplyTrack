from fastapi import FastAPI
from db import init_db
from resources import (user, startup, compliance_status, investor_request, procedure, reminder, source, badge, step)
app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(user.router)
app.include_router(startup.router)
app.include_router(procedure.router)
app.include_router(step.router)
app.include_router(source.router)
app.include_router(reminder.router)
app.include_router(compliance_status.router)
app.include_router(investor_request.router)
app.include_router(badge.router)