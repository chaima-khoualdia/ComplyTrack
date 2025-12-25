from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from db import get_session
from models import ComplianceStatus

router = APIRouter(prefix="/compliance", tags=["compliance"]) 

class ComplianceStatuses:
    @router.get("/by-startup/{startup_id}", response_model=list[ComplianceStatus])
    def list_by_startup(startup_id: int, session: Session = Depends(get_session)):
        stmt = select(ComplianceStatus).where(ComplianceStatus.startup_id == startup_id)
        return session.exec(stmt).all()

    @router.get("/{status_id}", response_model=ComplianceStatus)
    def get_status(status_id: int, session: Session = Depends(get_session)):
        status = session.get(ComplianceStatus, status_id)
        if not status:
            raise HTTPException(status_code=404, detail="Compliance status not found")
        return status
    @router.post("/", response_model=ComplianceStatus)
    def create_status(status: ComplianceStatus, session: Session = Depends(get_session)):
        # Ensure completed_at set if status is complete
        if status.status == "complete" and getattr(status, "completed_at", None) is None:
            status.completed_at = datetime.utcnow()
        session.add(status)
        session.commit()
        session.refresh(status)
        return status
    @router.put("/{status_id}", response_model=ComplianceStatus)
    def update_status(status_id: int, status_update: ComplianceStatus, session: Session = Depends(get_session)):
        status = session.get(ComplianceStatus, status_id)
        if not status:
            raise HTTPException(status_code=404, detail="Compliance status not found")
        for field, value in status_update.dict(exclude_unset=True).items():
            setattr(status, field, value)
        if status.status == "complete" and getattr(status, "completed_at", None) is None:
            status.completed_at = datetime.utcnow()
        session.add(status)
        session.commit()
        session.refresh(status)
        return status
    @router.delete("/{status_id}")
    def delete_status(status_id: int, session: Session = Depends(get_session)):
        status = session.get(ComplianceStatus, status_id)
        if not status:
            raise HTTPException(status_code=404, detail="Compliance status not found")
        session.delete(status)
        session.commit()
        return {"message": "Compliance status deleted"}