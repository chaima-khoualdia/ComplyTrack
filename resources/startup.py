import json
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from db import get_session
from models import Startup, StartupProcedure
from schemas import (
    StartupCreate, 
    StartupResponse, 
    StartupUpdate, 
    StartupCreatedResponse
)
from services import (
    auto_assign_procedures, 
    list_startup_procedures
)

router = APIRouter(prefix="/startups", tags=["startups"])


@router.get("/", response_model=list[StartupResponse])
def list_startups(session: Session = Depends(get_session)):
    """List all startups."""
    return session.exec(select(Startup)).all()

@router.get("/{startup_id}", response_model=StartupResponse)
def get_startup(startup_id: int, session: Session = Depends(get_session)):
    """Get a startup by ID."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup

@router.get("/by-matricule/{matricule}", response_model=StartupResponse)
def get_by_matricule(matricule: str, session: Session = Depends(get_session)):
    """Get a startup by matricule fiscal."""
    stmt = select(Startup).where(Startup.matricule_fiscal == matricule)
    startup = session.exec(stmt).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup

@router.post("/", response_model=StartupCreatedResponse)
def create_startup(
    startup_data: StartupCreate, 
    session: Session = Depends(get_session)
):
    """
    Create a new startup and automatically assign matching procedures.
    Returns startup details along with all auto-assigned procedures and their steps.
    Procedures are assigned based on legal_form, industry, size, and location metadata.
    """
    # Check if matricule already exists
    existing = session.exec(
        select(Startup).where(Startup.matricule_fiscal == startup_data.matricule_fiscal)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Matricule fiscal already registered")
    
    # Check if RNE already exists
    existing_rne = session.exec(
        select(Startup).where(Startup.rne_number == startup_data.rne_number)
    ).first()
    if existing_rne:
        raise HTTPException(status_code=400, detail="RNE number already registered")
    
    # Create startup
    startup = Startup(
        founder_id=startup_data.founder_id,
        name=startup_data.name,
        matricule_fiscal=startup_data.matricule_fiscal,
        rne_number=startup_data.rne_number,
        legal_form=startup_data.legal_form,
        field=startup_data.field,
        sector=startup_data.sector,
        size=startup_data.size,
        location=startup_data.location,
        badge_status="red",
        created_at=datetime.utcnow()
    )
    session.add(startup)
    session.commit()
    session.refresh(startup)
    
    # Auto-assign procedures based on startup attributes
    try:
        auto_assign_procedures(
            startup.id,
            startup.legal_form,
            startup.field,
            startup.size,
            startup.location,
            session
        )
    except Exception as e:
        # Log error but don't fail startup creation
        print(f"Error auto-assigning procedures: {e}")
    
    # Get assigned procedures with full details
    try:
        procedures = list_startup_procedures(startup.id, session)
    except Exception as e:
        print(f"Error fetching assigned procedures: {e}")
        procedures = []
    
    # Build response with startup and procedures
    return {
        "id": startup.id,
        "founder_id": startup.founder_id,
        "name": startup.name,
        "matricule_fiscal": startup.matricule_fiscal,
        "rne_number": startup.rne_number,
        "legal_form": startup.legal_form,
        "field": startup.field,
        "sector": startup.sector,
        "size": startup.size,
        "location": startup.location,
        "badge_status": startup.badge_status,
        "created_at": startup.created_at,
        "procedures": procedures
    }

@router.put("/{startup_id}", response_model=StartupResponse)
def update_startup(
    startup_id: int,
    startup_update: StartupUpdate,
    session: Session = Depends(get_session)
):
    """Update a startup's information."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Update only provided fields
    for field, value in startup_update.dict(exclude_unset=True).items():
        if value is not None:
            setattr(startup, field, value)
    
    session.add(startup)
    session.commit()
    session.refresh(startup)
    return startup

@router.delete("/{startup_id}")
def delete_startup(startup_id: int, session: Session = Depends(get_session)):
    """Delete a startup and cascade delete all related startup_procedure records."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Cascade delete all startup_procedure records for this startup
    startup_procedures = session.exec(
        select(StartupProcedure).where(StartupProcedure.startup_id == startup_id)
    ).all()
    
    for sp in startup_procedures:
        session.delete(sp)
    
    # Delete the startup
    session.delete(startup)
    session.commit()
    return {"message": "Startup and related procedures deleted successfully"}
