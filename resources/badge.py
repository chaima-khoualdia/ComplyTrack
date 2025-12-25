from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Startup, ComplianceStatus

router = APIRouter(prefix="/public", tags=["public"]) 

class Badge:
    @router.get("/compliance-badge/{identifier}")
    def compliance_badge(identifier: str, session: Session = Depends(get_session)):
        startup = None
        if identifier.isdigit():
            startup = session.get(Startup, int(identifier))
        if not startup:
        # Try matricule fiscal lookup
            stmt = select(Startup).where(Startup.matricule_fiscal == identifier)
            startup = session.exec(stmt).first()
        if not startup:
            raise HTTPException(status_code=404, detail="Startup not found")

    # Compute summary from compliance statuses
        statuses = session.exec(
            select(ComplianceStatus).where(ComplianceStatus.startup_id == startup.id)
        ).all()
        summary = {
            "pending": sum(1 for s in statuses if s.status == "pending"),
            "in_progress": sum(1 for s in statuses if s.status == "in_progress"),
            "complete": sum(1 for s in statuses if s.status == "complete"),
            "overdue": sum(1 for s in statuses if s.status == "overdue"),
        }
        return {
            "startup_name": startup.name,
            "matricule_fiscal": startup.matricule_fiscal,
            "badge_status": startup.badge_status,
            "summary": summary,
        }