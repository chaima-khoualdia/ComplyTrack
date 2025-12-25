from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Source, source

router = APIRouter(prefix="/sources", tags=["sources"])

class Sources:
    @router.get("/", response_model=list[Source])
    def list_sources(session: Session = Depends(get_session)):
        return session.exec(select(Source)).all()

    @router.get("/by-step/{step_id}", response_model=list[Source])
    def list_sources_by_step(step_id: int, session: Session = Depends(get_session)):
        stmt = select(Source).where(Source.step_id == step_id)
        return session.exec(stmt).all()

    @router.get("/{source_id}", response_model=Source)
    def get_source(source_id: int, session: Session = Depends(get_session)):
        source = session.get(Source, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        return source
    @router.post("/", response_model=Source)
    def create_source(source: Source, session: Session = Depends(get_session)):
        session.add(source)
        session.commit()
        session.refresh(source)
        return source
    @router.delete("/{source_id}")
    def delete_source(source_id: int, session: Session = Depends(get_session)):
        source = session.get(Source, source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Source not found")
        session.delete(source)
        session.commit()
        return {"message": "Source deleted"}