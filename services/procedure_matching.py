"""
Procedure Matching Service
Handles automatic procedure assignment based on startup attributes and procedure metadata.
"""

from sqlmodel import Session
from models import StartupProcedure
from services.procedure_loader import load_procedures


def get_matching_procedures(
    legal_form: str,
    field: str,
    size: str,
    location: str = None
) -> list:
    """
    Get procedures that match a startup's attributes.
    Matches on legal_form, industry, size, and optionally location.
    
    Args:
        legal_form: Legal form (SARL, SA, etc.)
        field: Industry (tech, healthcare, finance, etc.)
        size: Size (small, medium, large)
        location: Location (optional, for free zone matching)
    
    Returns:
        List of procedure IDs that match the startup attributes
    """
    procedures = load_procedures()
    matching_ids = []
    
    for procedure in procedures:
        # Check legal form match
        legal_forms = procedure.get("legal_forms", [])
        if legal_forms and legal_form not in legal_forms:
            continue
        
        # Check industry match
        industries = procedure.get("industries", [])
        if industries and field not in industries and "all" not in industries:
            continue
        
        # Check size match
        sizes = procedure.get("sizes", [])
        if sizes and size not in sizes:
            continue
        
        # Check location match (for free zone)
        procedure_locations = procedure.get("locations", [])
        if procedure_locations:
            if not location or location not in procedure_locations:
                continue
        
        # All conditions passed, add to matching
        matching_ids.append(procedure["id"])
    
    return matching_ids


def auto_assign_procedures(
    startup_id: int,
    legal_form: str,
    field: str,
    size: str,
    location: str,
    session: Session
) -> list:
    """
    Automatically assign matching procedures to a startup based on its attributes.
    
    Args:
        startup_id: ID of the startup
        legal_form: Legal form
        field: Industry
        size: Company size
        location: Location
        session: Database session
    
    Returns:
        List of created StartupProcedure dicts with id, procedure_id, and empty completion
    
    Raises:
        ValueError: If startup not found
    """
    from models import Startup
    
    # Verify startup exists
    startup = session.get(Startup, startup_id)
    if not startup:
        raise ValueError(f"Startup {startup_id} not found")
    
    # Get matching procedure IDs
    matching_ids = get_matching_procedures(legal_form, field, size, location)
    
    # Create StartupProcedure records for matching procedures
    created_assignments = []
    
    for procedure_id in matching_ids:
        # Check if already assigned
        from sqlmodel import select
        existing = session.exec(
            select(StartupProcedure)
            .where(StartupProcedure.startup_id == startup_id)
            .where(StartupProcedure.procedure_id == procedure_id)
        ).first()
        
        if existing:
            created_assignments.append(existing)
            continue
        
        # Create new assignment
        sp = StartupProcedure(
            startup_id=startup_id,
            procedure_id=procedure_id,
            completed_step_ids=[]
        )
        session.add(sp)
        created_assignments.append(sp)
    
    session.commit()
    for sp in created_assignments:
        session.refresh(sp)
    
    # Return list of dicts
    result = []
    for sp in created_assignments:
        result.append({
            "id": sp.id,
            "startup_id": sp.startup_id,
            "procedure_id": sp.procedure_id,
            "completed_step_ids": sp.completed_step_ids or [],
            "progress_percent": 0.0,
            "assigned_at": sp.assigned_at
        })
    
    return result
