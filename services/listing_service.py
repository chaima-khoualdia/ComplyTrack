"""
Listing Service
Handles listing procedures assigned to a startup with their steps and progress.
"""

from sqlmodel import Session, select
from models import Startup, StartupProcedure
from services.procedure_loader import load_procedures, get_procedure_by_id
from services.progress_service import calculate_progress


def list_startup_procedures(
    startup_id: int,
    session: Session
) -> list:
    """
    List all procedures assigned to a startup with their steps and progress.
    Steps are loaded from procedures.json, not the database.
    
    Args:
        startup_id: ID of the startup
        session: Database session
    
    Returns:
        List of dictionaries with procedure details, steps, and progress
    
    Raises:
        ValueError: If startup not found
    """
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise ValueError(f"Startup {startup_id} not found")
    
    procedures = load_procedures()
    
    # Get all startup procedures from database
    stmt = select(StartupProcedure).where(StartupProcedure.startup_id == startup_id)
    startup_procedures = session.exec(stmt).all()
    
    results = []
    for sp in startup_procedures:
        # Get procedure details from JSON
        procedure = get_procedure_by_id(sp.procedure_id, procedures)
        if not procedure:
            continue
        
        # Get steps from JSON
        steps_list = procedure.get("steps", [])
        
        completed_count = len(sp.completed_step_ids or [])
        total_steps = len(steps_list)
        progress = calculate_progress(sp, procedures)
        
        results.append({
            "id": sp.id,
            "startup_id": sp.startup_id,
            "procedure_id": sp.procedure_id,
            "procedure_name": procedure.get("name", ""),
            "procedure_description": procedure.get("description", ""),
            "completed_step_ids": sp.completed_step_ids or [],
            "total_steps": total_steps,
            "completed_steps": completed_count,
            "progress_percent": progress,
            "assigned_at": sp.assigned_at,
            "steps": [
                {
                    "id": s.get("id"),
                    "procedure_id": sp.procedure_id,
                    "name": s.get("name", ""),
                    "description": s.get("description", ""),
                    "order": s.get("order", 0),
                    "is_required": s.get("is_required", True),
                }
                for s in steps_list
            ]
        })
    
    return results
