"""
Assignment Service
Handles procedure assignment to startups and deletion of assignments.
"""

from typing import List
from sqlmodel import Session, select
from models import StartupProcedure, Startup
from services.procedure_loader import load_procedures, get_procedure_by_id
from services.progress_service import calculate_progress


def assign_procedures_to_startup(
    startup_id: int,
    procedure_ids: List[int],
    session: Session
) -> list:
    """
    Assign one or more procedures to a startup.
    Validates procedures exist in procedures.json and creates StartupProcedure records.
    Returns dicts with progress calculated from procedures.json.
    
    Args:
        startup_id: ID of the startup
        procedure_ids: List of procedure IDs to assign
        session: Database session
    
    Returns:
        List of dicts with assignment details and progress
    
    Raises:
        ValueError: If startup not found
        ValueError: If any procedure not found in procedures.json
    """
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise ValueError(f"Startup {startup_id} not found")
    
    procedures = load_procedures()
    created_assignments = []

    for procedure_id in procedure_ids:
        # Verify procedure exists in JSON
        procedure = get_procedure_by_id(procedure_id, procedures)
        if not procedure:
            raise ValueError(f"Procedure {procedure_id} not found in procedures.json")

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
    
    # Return dicts with progress calculated
    result = []
    for sp in created_assignments:
        progress = calculate_progress(sp, procedures)
        result.append({
            "id": sp.id,
            "startup_id": sp.startup_id,
            "procedure_id": sp.procedure_id,
            "completed_step_ids": sp.completed_step_ids or [],
            "progress_percent": progress,
            "assigned_at": sp.assigned_at
        })
    
    return result


def delete_startup_procedure(
    startup_procedure_id: int,
    session: Session
) -> dict:
    """
    Delete a startup procedure assignment.
    
    Args:
        startup_procedure_id: ID of the StartupProcedure to delete
        session: Database session
    
    Returns:
        Confirmation message dict
    
    Raises:
        ValueError: If StartupProcedure not found
    """
    sp = session.get(StartupProcedure, startup_procedure_id)
    if not sp:
        raise ValueError(f"Startup procedure assignment {startup_procedure_id} not found")
    
    session.delete(sp)
    session.commit()
    
    return {"message": "Procedure assignment deleted successfully"}
