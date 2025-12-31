"""
Progress Service
Handles progress calculation and step completion tracking using procedures.json.
"""

from models import StartupProcedure
from services.procedure_loader import load_procedures, get_procedure_by_id
from sqlmodel import Session


def calculate_progress(
    startup_procedure: StartupProcedure, 
    procedures: list = None
) -> float:
    """
    Calculate progress percentage for a startup procedure.
    Uses completed_step_ids count vs total steps from procedures.json.
    
    Args:
        startup_procedure: StartupProcedure instance
        procedures: Optional pre-loaded procedures list
    
    Returns:
        Progress percentage as float rounded to 2 decimals (0.00 to 100.00)
    """
    if procedures is None:
        procedures = load_procedures()
    
    procedure = get_procedure_by_id(startup_procedure.procedure_id, procedures)
    if not procedure:
        return 0.0
    
    total_steps = len(procedure.get("steps", []))
    completed_count = len(startup_procedure.completed_step_ids or [])
    
    if total_steps == 0:
        return 0.0
    
    return round((completed_count / total_steps * 100), 2)


def toggle_step_completion(
    startup_procedure_id: int,
    step_id: int,
    completed: bool,
    session: Session
) -> dict:
    """
    Toggle a step's completion status for a startup procedure.
    Validates step exists in the procedure's steps from procedures.json.
    Updates completed_step_ids and recalculates progress_percent.
    
    Args:
        startup_procedure_id: ID of the StartupProcedure record
        step_id: ID of the step to toggle
        completed: True to mark complete, False to mark incomplete
        session: Database session
    
    Returns:
        Updated StartupProcedure details with progress
    
    Raises:
        ValueError: If StartupProcedure, Procedure, or Step not found
    """
    # Get StartupProcedure
    from models import StartupProcedure
    sp = session.get(StartupProcedure, startup_procedure_id)
    if not sp:
        raise ValueError(f"Startup procedure assignment {startup_procedure_id} not found")
    
    procedures = load_procedures()
    
    # Get procedure from JSON
    procedure = get_procedure_by_id(sp.procedure_id, procedures)
    if not procedure:
        raise ValueError(f"Procedure {sp.procedure_id} not found in procedures.json")
    
    # Verify step exists in procedure's steps
    step_exists = any(s["id"] == step_id for s in procedure.get("steps", []))
    if not step_exists:
        raise ValueError(
            f"Step {step_id} not found in procedure {sp.procedure_id}"
        )
    
    # Get current completed_step_ids (ensure it's a list)
    current_ids = sp.completed_step_ids if sp.completed_step_ids is not None else []
    
    # Create new list to force SQLAlchemy to detect changes
    new_ids = list(current_ids)
    
    # Toggle completion
    if completed:
        if step_id not in new_ids:
            new_ids.append(step_id)
    else:
        if step_id in new_ids:
            new_ids.remove(step_id)
    
    # Assign new list to trigger change detection
    sp.completed_step_ids = new_ids
    
    # Mark the field as modified to ensure SQLAlchemy persists the change
    from sqlalchemy.orm import attributes
    attributes.flag_modified(sp, 'completed_step_ids')
    
    # Save changes
    session.add(sp)
    session.commit()
    session.refresh(sp)
    
    # Calculate progress after refresh to ensure we have updated data
    progress = calculate_progress(sp, procedures)
    
    return {
        "id": sp.id,
        "startup_id": sp.startup_id,
        "procedure_id": sp.procedure_id,
        "completed_step_ids": sp.completed_step_ids or [],
        "progress_percent": progress,
        "assigned_at": sp.assigned_at
    }
