from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Source
from schemas import SourceCreate, SourceResponse

router = APIRouter(prefix="/sources", tags=["sources"])

@router.get("/", response_model=list[SourceResponse])
def list_sources(session: Session = Depends(get_session)):
    """List all regulatory sources."""
    return session.exec(select(Source)).all()

@router.get("/by-type/{source_type}", response_model=list[SourceResponse])
def list_sources_by_type(source_type: str, session: Session = Depends(get_session)):
    """List sources by type (law, portal, guide)."""
    stmt = select(Source).where(Source.type == source_type)
    return session.exec(stmt).all()

@router.get("/{source_id}", response_model=SourceResponse)
def get_source(source_id: int, session: Session = Depends(get_session)):
    """Get a specific source by ID."""
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source

@router.post("/", response_model=SourceResponse)
def create_source(source_data: SourceCreate, session: Session = Depends(get_session)):
    """Create a new regulatory source."""
    source = Source(**source_data.model_dump())
    session.add(source)
    session.commit()
    session.refresh(source)
    return source

@router.put("/{source_id}", response_model=SourceResponse)
def update_source(source_id: int, source_data: SourceCreate, session: Session = Depends(get_session)):
    """Update an existing source."""
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    
    for key, value in source_data.model_dump().items():
        setattr(source, key, value)
    
    session.add(source)
    session.commit()
    session.refresh(source)
    return source

@router.delete("/{source_id}")
def delete_source(source_id: int, session: Session = Depends(get_session)):
    """Delete a source."""
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    session.delete(source)
    session.commit()
    return {"message": "Source deleted"}