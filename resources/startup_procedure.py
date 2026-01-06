from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime
import json
from db import get_session
from models import Startup, StartupProcedure, ComplianceStatus
from schemas import StartupProcedureResponse, StartupProcedureWithDetails, ProcedureStatusUpdate, StepToggle
from services.compliance_service import sync_compliance_status_from_procedures
from services.listing_service import list_startup_procedures, get_procedure_response
from services.procedures_service import load_procedures, get_procedure_by_id
from services.auth_service import require_roles


router = APIRouter(prefix="/startups", tags=["procedures"])


@router.get("/{startup_id}/procedures", response_model=list[StartupProcedureWithDetails])
def list_procedures(
    startup_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
):
    """List all procedures assigned to a startup with enriched details including steps."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    try:
        return list_startup_procedures(startup_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{startup_id}/procedures/{procedure_id}", response_model=StartupProcedureWithDetails)
def get_procedure(
    startup_id: int,
    procedure_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
):
    """Get a specific procedure assigned to a startup with enriched details including steps."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    procedure = session.query(StartupProcedure).filter_by(
        startup_id=startup_id,
        procedure_id=procedure_id
    ).first()
    
    if not procedure:
        raise HTTPException(
            status_code=404,
            detail=f"Procedure {procedure_id} not assigned to startup {startup_id}"
        )
    
    try:
        return get_procedure_response(procedure, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{startup_id}/procedures/{procedure_id}", response_model=StartupProcedureWithDetails)
def update_procedure_status(
    startup_id: int,
    procedure_id: int,
    status_update: ProcedureStatusUpdate,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
):
    """
    Update a procedure's status and/or step completion.
    
    Supports three use cases:
    1. Update status only: {"status": "in_progress"}
    2. Toggle step: {"step_id": 301, "completed": true}
    3. Both: {"status": "in_progress", "step_id": 301, "completed": true}
    
    Returns enriched procedure response with steps and updated progress.
    """
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    procedure = session.query(StartupProcedure).filter_by(
        startup_id=startup_id,
        procedure_id=procedure_id
    ).first()
    
    if not procedure:
        raise HTTPException(
            status_code=404,
            detail=f"Procedure {procedure_id} not assigned to startup {startup_id}"
        )
    
    # Load procedure definition from JSON to validate step if needed
    procedures = load_procedures()
    procedure_def = get_procedure_by_id(procedure_id, procedures)
    
    if not procedure_def:
        raise HTTPException(
            status_code=404,
            detail=f"Procedure {procedure_id} not found in procedures.json"
        )
    
    # Handle step tracking if step_id is provided
    if status_update.step_id is not None:
        # Verify step exists in the procedure
        steps = procedure_def.get("steps", [])
        step_ids = [s.get("id") for s in steps]
        
        if status_update.step_id not in step_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Step {status_update.step_id} not found in procedure {procedure_id}"
            )
        
        # Parse current completed_step_ids (stored as JSON string)
        try:
            completed_ids = json.loads(procedure.completed_step_ids or "[]")
        except (json.JSONDecodeError, TypeError):
            completed_ids = []
        
        # Update completed_step_ids based on toggle
        if status_update.completed:
            if status_update.step_id not in completed_ids:
                completed_ids.append(status_update.step_id)
        else:
            if status_update.step_id in completed_ids:
                completed_ids.remove(status_update.step_id)
        
        procedure.completed_step_ids = json.dumps(completed_ids)
    
    # Handle procedure status update if provided
    if status_update.status is not None:
        procedure.status = status_update.status
        
        # Set completed_at if status is completed
        if status_update.status == "completed" and procedure.completed_at is None:
            procedure.completed_at = datetime.utcnow()
        elif status_update.status != "completed":
            procedure.completed_at = None
    
    session.add(procedure)
    session.commit()
    session.refresh(procedure)
    
    # Sync ComplianceStatus for this domain
    try:
        sync_compliance_status_from_procedures(startup_id, procedure.domain, session)
    except Exception as e:
        print(f"Warning: Could not sync compliance status: {e}")
    
    try:
        return get_procedure_response(procedure, session)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{startup_id}/procedures/{procedure_id}")
def delete_procedure_assignment(
    startup_id: int,
    procedure_id: int,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup")),
):
    """Remove a procedure assignment from a startup."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    procedure = session.query(StartupProcedure).filter_by(
        startup_id=startup_id,
        procedure_id=procedure_id
    ).first()
    
    if not procedure:
        raise HTTPException(
            status_code=404,
            detail=f"Procedure {procedure_id} not assigned to startup {startup_id}"
        )
    
    domain = procedure.domain
    session.delete(procedure)
    session.commit()
    
    # Sync ComplianceStatus after deletion
    try:
        sync_compliance_status_from_procedures(startup_id, domain, session)
    except Exception as e:
        print(f"Warning: Could not sync compliance status: {e}")
    
    return {"message": "Procedure assignment deleted successfully"}


@router.patch("/{startup_id}/procedures/{procedure_id}/steps/{step_id}", response_model=StartupProcedureWithDetails)
def toggle_step_completion(
    startup_id: int,
    procedure_id: int,
    step_id: int,
    step_toggle: StepToggle,
    session: Session = Depends(get_session),
    current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
):
    """
    Toggle step completion within a procedure.
    
    Steps are defined in procedures.json but step completion is tracked per StartupProcedure.
    
    Args:
        startup_id: ID of the startup
        procedure_id: ID of the procedure (from procedures.json)
        step_id: ID of the step within the procedure
        step_toggle: {"completed": true/false}
        
    Returns:
        Enriched procedure response with updated steps and progress
    """
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Find the StartupProcedure assignment
    procedure = session.query(StartupProcedure).filter_by(
        startup_id=startup_id,
        procedure_id=procedure_id
    ).first()
    
    if not procedure:
        raise HTTPException(
            status_code=404,
            detail=f"Procedure {procedure_id} not assigned to startup {startup_id}"
        )
    
    # Load procedure definition from JSON
    procedures = load_procedures()
    procedure_def = get_procedure_by_id(procedure_id, procedures)
    
    if not procedure_def:
        raise HTTPException(
            status_code=404,
            detail=f"Procedure {procedure_id} not found in procedures.json"
        )
    
    # Verify step exists in the procedure
    steps = procedure_def.get("steps", [])
    step_ids = [s.get("id") for s in steps]
    
    if step_id not in step_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Step {step_id} not found in procedure {procedure_id}"
        )
    
    # Parse current completed_step_ids (stored as JSON string)
    try:
        completed_ids = json.loads(procedure.completed_step_ids or "[]")
    except (json.JSONDecodeError, TypeError):
        completed_ids = []
    
    # Update completed_step_ids based on toggle
    if step_toggle.completed:
        if step_id not in completed_ids:
            completed_ids.append(step_id)
    else:
        if step_id in completed_ids:
            completed_ids.remove(step_id)
    
    # Update the procedure record
    procedure.completed_step_ids = json.dumps(completed_ids)
    session.add(procedure)
    session.commit()
    session.refresh(procedure)
    
    try:
        return get_procedure_response(procedure, session)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))

