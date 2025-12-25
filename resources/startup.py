from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from db import get_session
from models import Startup, startup

router = APIRouter(prefix="/startups", tags=["startups"]) 

class Startups:
    @router.get("/", response_model=list[Startup])
    def list_startups(session: Session = Depends(get_session)):
        return session.exec(select(Startup)).all()

    @router.get("/{startup_id}", response_model=Startup)
    def get_startup(startup_id: int, session: Session = Depends(get_session)):
        startup = session.get(Startup, startup_id)
        if not startup:
            raise HTTPException(status_code=404, detail="Startup not found")
        return startup
    @router.get("/by-matricule/{matricule}", response_model=Startup)
    def get_by_matricule(matricule: str, session: Session = Depends(get_session)):
        stmt = select(Startup).where(Startup.matricule_fiscal == matricule)
        startup = session.exec(stmt).first()
        if not startup:
            raise HTTPException(status_code=404, detail="Startup not found")
        return startup
    @router.post("/", response_model=Startup)
    def create_startup(startup: Startup, session: Session = Depends(get_session)):
    # Ensure created_at set
        if getattr(startup, "created_at", None) is None:
            startup.created_at = datetime.utcnow()
    # Default badge status if missing
        if not getattr(startup, "badge_status", None):
            startup.badge_status = "red"
        session.add(startup)
        session.commit()
        session.refresh(startup)
        return startup
    @router.delete("/{startup_id}")
    def delete_startup(startup_id: int, session: Session = Depends(get_session)):
        startup = session.get(Startup, startup_id)
        if not startup:
            raise HTTPException(status_code=404, detail="Startup not found")
        session.delete(startup)
        session.commit()
        return {"message": "Startup deleted"}