from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Startup, StartupProcedure
from schemas import (
    StartupProcedureWithDetails,
    StepToggle
)
from services import (
    list_startup_procedures,
    toggle_step_completion,
    delete_startup_procedure,
    load_procedures,
    get_procedure_by_id,
    calculate_progress
)


router = APIRouter(prefix="/startups", tags=["procedures"])


@router.get("/{startup_id}/procedures", response_model=list[StartupProcedureWithDetails])
def list_startup_procedures_all(
    startup_id: int,
    session: Session = Depends(get_session)
):
    """List all procedures assigned to a startup with their steps, completed_step_ids, and progress_percent."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    try:
        procedures = list_startup_procedures(startup_id, session)
        return [StartupProcedureWithDetails(**proc) for proc in procedures]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{startup_id}/procedures/{procedure_id}", response_model=StartupProcedureWithDetails)
def get_startup_procedure_by_id(
    startup_id: int,
    procedure_id: int,
    session: Session = Depends(get_session)
):
    """Get a specific procedure assigned to a startup with its steps and tracking state."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Find the StartupProcedure record
    stmt = select(StartupProcedure).where(
        StartupProcedure.startup_id == startup_id,
        StartupProcedure.procedure_id == procedure_id
    )
    startup_procedure = session.exec(stmt).first()
    
    if not startup_procedure:
        raise HTTPException(
            status_code=404, 
            detail=f"Procedure {procedure_id} not assigned to startup {startup_id}"
        )
    
    # Load procedure details from JSON
    procedures = load_procedures()
    procedure = get_procedure_by_id(procedure_id, procedures)
    
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found in procedures.json")
    
    # Build response with steps and progress
    steps_list = procedure.get("steps", [])
    completed_count = len(startup_procedure.completed_step_ids or [])
    total_steps = len(steps_list)
    progress = calculate_progress(startup_procedure, procedures)
    
    return StartupProcedureWithDetails(
        id=startup_procedure.id,
        startup_id=startup_procedure.startup_id,
        procedure_id=startup_procedure.procedure_id,
        procedure_name=procedure.get("name", ""),
        procedure_description=procedure.get("description", ""),
        completed_step_ids=startup_procedure.completed_step_ids or [],
        total_steps=total_steps,
        completed_steps=completed_count,
        progress_percent=progress,
        assigned_at=startup_procedure.assigned_at,
        steps=[
            {
                "id": s.get("id"),
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "order": s.get("order", 0),
                "is_required": s.get("is_required", True),
            }
            for s in steps_list
        ]
    )


@router.patch("/{startup_id}/procedures/{procedure_id}/steps/{step_id}", response_model=StartupProcedureWithDetails)
def toggle_procedure_step(
    startup_id: int,
    procedure_id: int,
    step_id: int,
    step_toggle: StepToggle,
    session: Session = Depends(get_session)
):
    """
    Mark a step as done or undone for a startup's procedure.
    Updates completed_step_ids, recalculates progress_percent, commits and refreshes,
    and returns the updated procedure with full details.
    """
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Find the StartupProcedure record
    stmt = select(StartupProcedure).where(
        StartupProcedure.startup_id == startup_id,
        StartupProcedure.procedure_id == procedure_id
    )
    startup_procedure = session.exec(stmt).first()
    
    if not startup_procedure:
        raise HTTPException(
            status_code=404, 
            detail=f"Procedure {procedure_id} not assigned to startup {startup_id}"
        )
    
    # Toggle the step using the service
    try:
        toggle_step_completion(startup_procedure.id, step_id, step_toggle.completed, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Refresh to get updated values
    session.refresh(startup_procedure)
    
    # Load procedure details from JSON
    procedures = load_procedures()
    procedure = get_procedure_by_id(procedure_id, procedures)
    
    if not procedure:
        raise HTTPException(status_code=404, detail="Procedure not found in procedures.json")
    
    # Build response with updated tracking state
    steps_list = procedure.get("steps", [])
    completed_count = len(startup_procedure.completed_step_ids or [])
    total_steps = len(steps_list)
    progress = calculate_progress(startup_procedure, procedures)
    
    return StartupProcedureWithDetails(
        id=startup_procedure.id,
        startup_id=startup_procedure.startup_id,
        procedure_id=startup_procedure.procedure_id,
        procedure_name=procedure.get("name", ""),
        procedure_description=procedure.get("description", ""),
        completed_step_ids=startup_procedure.completed_step_ids or [],
        total_steps=total_steps,
        completed_steps=completed_count,
        progress_percent=progress,
        assigned_at=startup_procedure.assigned_at,
        steps=[
            {
                "id": s.get("id"),
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "order": s.get("order", 0),
                "is_required": s.get("is_required", True),
            }
            for s in steps_list
        ]
    )


@router.delete("/{startup_id}/procedures/{procedure_id}")
def delete_procedure_assignment(
    startup_id: int,
    procedure_id: int,
    session: Session = Depends(get_session)
):
    """Remove a procedure assignment from a startup."""
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Find the StartupProcedure record
    stmt = select(StartupProcedure).where(
        StartupProcedure.startup_id == startup_id,
        StartupProcedure.procedure_id == procedure_id
    )
    startup_procedure = session.exec(stmt).first()
    
    if not startup_procedure:
        raise HTTPException(
            status_code=404, 
            detail=f"Procedure {procedure_id} not assigned to startup {startup_id}"
        )
    
    try:
        delete_startup_procedure(startup_procedure.id, session)
        return {"message": "Procedure assignment deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

