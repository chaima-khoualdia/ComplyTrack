from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import StartupProcedure, Procedure, Step, Startup
from schemas import (
    StartupProcedureAssign, 
    StartupProcedureResponse, 
    StartupProcedureWithDetails,
    StepToggle,
    StepResponse
)

router = APIRouter(prefix="/startup_procedures", tags=["startup_procedures"])

def calculate_progress(startup_procedure: StartupProcedure, session: Session) -> float:
    """
    Calculate progress percentage for a startup procedure.
    
    Args:
        startup_procedure: StartupProcedure instance
        session: Database session
    
    Returns:
        Progress percentage as float rounded to 2 decimals (0.00 to 100.00)
    """
    # Query all steps for this procedure
    steps_stmt = select(Step).where(Step.procedure_id == startup_procedure.procedure_id)
    total_steps = len(session.exec(steps_stmt).all())
    
    # Count completed steps
    completed_count = len(startup_procedure.completed_step_ids or [])
    
    # Calculate percentage
    if total_steps == 0:
        return 0.0
    
    return round((completed_count / total_steps * 100), 2)

@router.post("/startup/{startup_id}/procedures", response_model=list[StartupProcedureResponse])
def assign_procedures_to_startup(
    startup_id: int, 
    assignment: StartupProcedureAssign,
    session: Session = Depends(get_session)
):
    """Assign one or more procedures to a startup."""
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    created_assignments = []
    for procedure_id in assignment.procedure_ids:
        # Verify procedure exists
        procedure = session.get(Procedure, procedure_id)
        if not procedure:
            raise HTTPException(status_code=404, detail=f"Procedure {procedure_id} not found")
        
        # Check if already assigned
        existing = session.exec(
            select(StartupProcedure)
            .where(StartupProcedure.startup_id == startup_id)
            .where(StartupProcedure.procedure_id == procedure_id)
        ).first()
        
        if existing:
            created_assignments.append(existing)
            continue
        
        # Create assignment
        startup_procedure = StartupProcedure(
            startup_id=startup_id,
            procedure_id=procedure_id,
            completed_step_ids=[]
        )
        session.add(startup_procedure)
        created_assignments.append(startup_procedure)
    
    session.commit()
    for sp in created_assignments:
        session.refresh(sp)
    
    # Calculate progress for response
    response = []
    for sp in created_assignments:
        progress = calculate_progress(sp, session)
        
        response.append(StartupProcedureResponse(
            id=sp.id,
            startup_id=sp.startup_id,
            procedure_id=sp.procedure_id,
            completed_step_ids=sp.completed_step_ids or [],
            progress_percent=progress,
            assigned_at=sp.assigned_at
        ))
    
    return response

@router.get("/startup/{startup_id}/procedures", response_model=list[StartupProcedureWithDetails])
def list_startup_procedures(
    startup_id: int,
    session: Session = Depends(get_session)
):
    """List all procedures assigned to a startup with their steps."""
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise HTTPException(status_code=404, detail="Startup not found")
    
    # Get all startup procedures
    stmt = select(StartupProcedure).where(StartupProcedure.startup_id == startup_id)
    startup_procedures = session.exec(stmt).all()
    
    results = []
    for sp in startup_procedures:
        # Get procedure details
        procedure = session.get(Procedure, sp.procedure_id)
        if not procedure:
            continue
        
        # Get steps for this procedure
        steps_stmt = select(Step).where(Step.procedure_id == sp.procedure_id).order_by(Step.order)
        steps = session.exec(steps_stmt).all()
        
        completed_count = len(sp.completed_step_ids or [])
        total = len(steps)
        progress = calculate_progress(sp, session)
        
        results.append(StartupProcedureWithDetails(
            id=sp.id,
            startup_id=sp.startup_id,
            procedure_id=sp.procedure_id,
            procedure_name=procedure.name,
            procedure_description=procedure.description,
            completed_step_ids=sp.completed_step_ids or [],
            total_steps=total,
            completed_steps=completed_count,
            progress_percent=progress,
            assigned_at=sp.assigned_at,
            steps=[StepResponse(
                id=s.id,
                procedure_id=s.procedure_id,
                name=s.name,
                description=s.description,
                order=s.order,
                is_required=s.is_required
            ) for s in steps]
        ))
    
    return results

@router.patch("/{startup_procedure_id}/step", response_model=StartupProcedureResponse)
def toggle_step_completion(
    startup_procedure_id: int,
    step_toggle: StepToggle,
    session: Session = Depends(get_session)
):
    """Mark a step as completed or incomplete for a startup's procedure."""
    sp = session.get(StartupProcedure, startup_procedure_id)
    if not sp:
        raise HTTPException(status_code=404, detail="Startup procedure assignment not found")
    
    # Verify step exists and belongs to this procedure
    step = session.get(Step, step_toggle.step_id)
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    
    if step.procedure_id != sp.procedure_id:
        raise HTTPException(
            status_code=400, 
            detail="Step does not belong to this procedure"
        )
    
    # Initialize if None
    if sp.completed_step_ids is None:
        sp.completed_step_ids = []
    
    # Toggle completion
    if step_toggle.completed:
        if step_toggle.step_id not in sp.completed_step_ids:
            sp.completed_step_ids.append(step_toggle.step_id)
    else:
        if step_toggle.step_id in sp.completed_step_ids:
            sp.completed_step_ids.remove(step_toggle.step_id)
    
    session.add(sp)
    session.commit()
    session.refresh(sp)
    
    # Calculate progress for response
    progress = calculate_progress(sp, session)
    
    return StartupProcedureResponse(
        id=sp.id,
        startup_id=sp.startup_id,
        procedure_id=sp.procedure_id,
        completed_step_ids=sp.completed_step_ids or [],
        progress_percent=progress,
        assigned_at=sp.assigned_at
    )

@router.delete("/{startup_procedure_id}")
def delete_startup_procedure(
    startup_procedure_id: int,
    session: Session = Depends(get_session)
):
    """Remove a procedure assignment from a startup."""
    sp = session.get(StartupProcedure, startup_procedure_id)
    if not sp:
        raise HTTPException(status_code=404, detail="Startup procedure assignment not found")
    
    session.delete(sp)
    session.commit()
    
    return {"message": "Procedure assignment deleted successfully"}
