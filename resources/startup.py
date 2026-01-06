import json
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, date, timedelta
from db import get_session
from models import Startup, StartupProcedure, ComplianceStatus, Reminder, InvestorRequest
from schemas import (
    StartupCreate, 
    StartupResponse, 
    StartupUpdate, 
    StartupCreatedResponse
)
from services import initialize_startup_procedures
from services.compliance_service import sync_compliance_status_from_procedures
from services.auth_service import require_roles

router = APIRouter(prefix="/startups", tags=["startups"])


@router.get("/", response_model=list[StartupResponse])
def list_startups(
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "investor", "startup", "owner", "worker")),
):
    """List all startups."""
    return session.exec(select(Startup)).all()

@router.get("/{startup_id}", response_model=StartupResponse)
def get_startup(
    startup_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "investor", "startup", "owner", "worker")),
):
    """Get a startup by ID."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup

@router.get("/by-matricule/{matricule}", response_model=StartupResponse)
def get_by_matricule(
    matricule: str,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "investor", "startup", "owner", "worker")),
):
    """Get a startup by matricule fiscal."""
    stmt = select(Startup).where(Startup.matricule_fiscal == matricule)
    startup = session.exec(stmt).first()
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    return startup

@router.post("/", response_model=StartupCreatedResponse)
def create_startup(
    startup_data: StartupCreate, 
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "owner")),
):
    """
    Create a new startup and automatically populate procedures and compliance tracking.
    Owner users must use this endpoint after registration to create their startup.
    
    When a startup is created:
    1. One StartupProcedure record per applicable procedure (with procedure_name, domain, status, due_date)
    2. One ComplianceStatus record per domain (tracking overall domain completion)
    
    Returns startup details with procedures and compliance status.
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
    
    # Enforce founder ownership for owner role
    if current_user.role.lower() == "owner" and startup_data.founder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Owner users can only create their own startup")

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
    
    # Auto-populate procedures and compliance status
    try:
        initialize_startup_procedures(startup, session, mode="auto")
        # Sync compliance status for all domains based on procedures
        sync_compliance_status_from_procedures(startup.id, session)
    except Exception as e:
        # Log error but don't fail startup creation
        print(f"Error initializing procedures and compliance: {e}")
    
    # Get procedures and compliance status
    procedures = session.query(StartupProcedure).filter_by(startup_id=startup.id).all()
    compliance_statuses = session.query(ComplianceStatus).filter_by(startup_id=startup.id).all()
    
    # Build response
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
        "procedures": [
            {
                "id": p.id,
                "startup_id": p.startup_id,
                "procedure_id": p.procedure_id,
                "procedure_name": p.procedure_name,
                "domain": p.domain,
                "status": p.status,
                "due_date": p.due_date,
                "assigned_at": p.assigned_at,
                "completed_at": p.completed_at
            }
            for p in procedures
        ],
        "compliance_status": [
            {
                "id": c.id,
                "startup_id": c.startup_id,
                "domain": c.domain,
                "status": c.status,
                "due_date": c.due_date,
                "completed_at": c.completed_at
            }
            for c in compliance_statuses
        ]
    }

@router.put("/{startup_id}", response_model=StartupResponse)
def update_startup(
    startup_id: int,
    startup_update: StartupUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup")),
):
    """Update a startup's information."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    if current_user.role.lower() != "admin" and startup.founder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this startup")
    
    # Update only provided fields
    for field, value in startup_update.dict(exclude_unset=True).items():
        if value is not None:
            setattr(startup, field, value)
    
    session.add(startup)
    session.commit()
    session.refresh(startup)
    return startup

@router.delete("/{startup_id}")
def delete_startup(
    startup_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin")),
):
    """
    Delete a startup and cascade delete all related data.
    This removes:
    - StartupProcedure records
    - ComplianceStatus records
    - Reminder records
    - InvestorRequest records
    
    Deletes children first to avoid IntegrityError from NOT NULL startup_id constraint.
    """
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Delete all related records FIRST, before deleting startup
    # This prevents SQLAlchemy from trying to set startup_id=None
    
    # Delete StartupProcedure records
    startup_procedures = session.exec(
        select(StartupProcedure).where(StartupProcedure.startup_id == startup_id)
    ).all()
    for sp in startup_procedures:
        session.delete(sp)
    
    # Delete ComplianceStatus records
    compliance_statuses = session.exec(
        select(ComplianceStatus).where(ComplianceStatus.startup_id == startup_id)
    ).all()
    for cs in compliance_statuses:
        session.delete(cs)
    
    # Delete Reminder records
    reminders = session.exec(
        select(Reminder).where(Reminder.startup_id == startup_id)
    ).all()
    for reminder in reminders:
        session.delete(reminder)
    
    # Delete InvestorRequest records
    investor_requests = session.exec(
        select(InvestorRequest).where(InvestorRequest.startup_id == startup_id)
    ).all()
    for ir in investor_requests:
        session.delete(ir)
    
    # Flush to ensure all child deletions are processed before startup deletion
    session.flush()
    
    # Finally, delete the startup itself
    session.delete(startup)
    session.commit()
    
    return {"message": "Startup and all related data deleted successfully"}
