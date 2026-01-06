from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
from db import get_session
from models import Startup, ComplianceStatus
from schemas import ComplianceStatusCreate, ComplianceStatusUpdate, ComplianceStatusResponse
from services.compliance_service import (
    compute_badge,
    summarize_statuses,
    get_startup_compliance_statuses,
    build_compliance_summary_from_procedures,
)
from services.procedures_service import get_procedure_by_id
from services.auth_service import require_roles

router = APIRouter(prefix="/compliance", tags=["compliance"])


@router.get("/summary/{startup_id}")
def get_compliance_summary(
    startup_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "investor", "startup", "owner", "worker")),
):
    """
    Get comprehensive compliance summary for a startup.
    
    Returns real compliance data from StartupProcedure records:
    - Summary counts (pending, in_progress, complete, overdue, total)
    - Badge status (green/yellow/red)
    - Compliance procedures grouped by domain with details
    
    This is the main endpoint for investor dashboards.
    """
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Build comprehensive summary from StartupProcedure records
    compliance_data = build_compliance_summary_from_procedures(startup_id, session)
    
    # Update startup badge status if it changed
    if startup.badge_status != compliance_data["badge_status"]:
        startup.badge_status = compliance_data["badge_status"]
        session.add(startup)
        session.commit()
    
    return {
        "startup_name": startup.name,
        "matricule_fiscal": startup.matricule_fiscal,
        "badge_status": compliance_data["badge_status"],
        "summary": compliance_data["summary"],
        "compliance_by_domain": compliance_data["compliance_by_domain"]
    }



@router.get("/startup/{startup_id}")
def list_by_startup(
    startup_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "investor", "startup", "owner", "worker")),
):
    """List all compliance statuses for a startup, grouped by domain."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    statuses = get_startup_compliance_statuses(startup_id, session)
    compliance_by_domain = _group_compliance_by_domain(statuses)
    
    return {
        "startup_name": startup.name,
        "matricule_fiscal": startup.matricule_fiscal,
        "badge_status": startup.badge_status,
        "compliance_by_domain": compliance_by_domain,
    }


@router.get("/badge/{identifier}")
def get_compliance_badge(
    identifier: str,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "investor", "startup", "owner", "worker")),
):
    """
    Get compliance badge for a startup (investor-facing).
    
    Identifier can be startup ID (integer) or matricule_fiscal (string).
    Returns: startup_name, matricule_fiscal, badge_status, summary, and compliance grouped by domain.
    Uses real-time data from StartupProcedure records.
    """
    startup = None
    
    # Try ID lookup first
    if identifier.isdigit():
        startup = session.get(Startup, int(identifier))
    
    # Try matricule_fiscal lookup
    if not startup:
        stmt = select(Startup).where(Startup.matricule_fiscal == identifier)
        startup = session.exec(stmt).first()
    
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Build comprehensive summary from StartupProcedure records
    compliance_data = build_compliance_summary_from_procedures(startup.id, session)
    
    # Update startup badge status if it changed
    if startup.badge_status != compliance_data["badge_status"]:
        startup.badge_status = compliance_data["badge_status"]
        session.add(startup)
        session.commit()
    
    return {
        "startup_name": startup.name,
        "matricule_fiscal": startup.matricule_fiscal,
        "badge_status": compliance_data["badge_status"],
        "summary": compliance_data["summary"],
        "compliance_by_domain": compliance_data["compliance_by_domain"]
    }


@router.get("/{startup_id}/{domain}", response_model=ComplianceStatusResponse)
def get_status(
    startup_id: int,
    domain: str,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "investor", "startup", "owner", "worker")),
):
    """Get compliance status for a specific startup and domain."""
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Query by startup_id and domain (natural key)
    statement = select(ComplianceStatus).where(
        ComplianceStatus.startup_id == startup_id,
        ComplianceStatus.domain == domain
    )
    status = session.exec(statement).first()
    
    if not status:
        raise HTTPException(
            status_code=404, 
            detail=f"Compliance status not found for startup {startup_id} in domain '{domain}'"
        )
    return status


@router.post("/", response_model=ComplianceStatusResponse)
def create_status(
    status_data: ComplianceStatusCreate,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
):
    """Create a new compliance status record."""
    # Verify startup exists
    startup = session.get(Startup, status_data.startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    status = ComplianceStatus(**status_data.model_dump())
    
    # Set completed_at if status is complete
    if status.status == "complete":
        status.completed_at = datetime.utcnow()
    
    session.add(status)
    session.commit()
    session.refresh(status)
    
    # Update badge after creating status
    _update_startup_badge(startup.id, session)
    
    return status


@router.put("/{startup_id}/{domain}")
def update_status(
    startup_id: int,
    domain: str,
    status_update: ComplianceStatusUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
):
    """Update a compliance status and return badge info with grouped compliance statuses."""
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Query by startup_id and domain
    statement = select(ComplianceStatus).where(
        ComplianceStatus.startup_id == startup_id,
        ComplianceStatus.domain == domain
    )
    status = session.exec(statement).first()
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Compliance status not found for startup {startup_id} in domain '{domain}'"
        )
    
    # Update only provided fields
    update_data = status_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(status, field, value)
    
    # Set completed_at if status becomes complete
    if status.status == "complete" and status.completed_at is None:
        status.completed_at = datetime.utcnow()
    
    session.add(status)
    session.commit()
    session.refresh(status)
    
    # Update badge after status change
    _update_startup_badge(status.startup_id, session)
    
    # Get startup and recompute badge with grouped compliance summary
    startup = session.get(Startup, status.startup_id)
    statuses = get_startup_compliance_statuses(status.startup_id, session)
    summary = summarize_statuses(statuses)
    compliance_by_domain = _group_compliance_by_domain(statuses)
    
    return {
        "startup_name": startup.name,
        "matricule_fiscal": startup.matricule_fiscal,
        "badge_status": startup.badge_status,
        "summary": summary,
        "compliance_by_domain": compliance_by_domain,
    }


@router.delete("/{startup_id}/{domain}")
def delete_status(
    startup_id: int,
    domain: str,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup")),
):
    """Delete a compliance status for a specific startup and domain."""
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Query by startup_id and domain
    statement = select(ComplianceStatus).where(
        ComplianceStatus.startup_id == startup_id,
        ComplianceStatus.domain == domain
    )
    status = session.exec(statement).first()
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Compliance status not found for startup {startup_id} in domain '{domain}'"
        )
    
    session.delete(status)
    session.commit()
    
    # Update badge after deletion
    _update_startup_badge(startup_id, session)
    
    return {"message": "Compliance status deleted"}


def _update_startup_badge(startup_id: int, session: Session) -> None:
    """
    Internal helper to compute and update startup badge status.
    Called after any compliance status change.
    """
    startup = session.get(Startup, startup_id)
    if not startup:
        return
    
    statuses = get_startup_compliance_statuses(startup_id, session)
    new_badge = compute_badge(statuses)
    
    if startup.badge_status != new_badge:
        startup.badge_status = new_badge
        session.add(startup)
        session.commit()
        session.refresh(startup)


def _group_compliance_by_domain(statuses: list[ComplianceStatus]) -> dict:
    """
    Group compliance statuses by domain with procedure details.
    
    Returns:
        {
            "domain_name": [
                {
                    "id": compliance_id,
                    "procedure_id": procedure_id,
                    "procedure_name": procedure_name,
                    "status": status,
                    "due_date": due_date,
                    "completed_at": completed_at
                },
                ...
            ],
            ...
        }
    """
    grouped = {}
    
    for status in statuses:
        domain = status.domain
        if domain not in grouped:
            grouped[domain] = []
        
        # Get procedure details
        proc = get_procedure_by_id(status.procedure_id)
        procedure_name = proc.get("name", "Unknown") if proc else "Unknown"
        
        grouped[domain].append({
            "id": status.id,
            "procedure_id": status.procedure_id,
            "procedure_name": procedure_name,
            "status": status.status,
            "due_date": status.due_date,
            "completed_at": status.completed_at,
            "domain": status.domain
        })
    
    return grouped
