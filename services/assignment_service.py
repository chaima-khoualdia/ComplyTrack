"""
Assignment Service
Handles procedure assignment to startups - creating and deleting StartupProcedure records.
Responsible only for database operations on StartupProcedure, not ComplianceStatus.
Also handles reminder creation for assigned procedures.
"""

from typing import List
from sqlmodel import Session, select
from datetime import datetime, timedelta
import json
from models import StartupProcedure, Startup
from services.procedures_service import load_procedures, get_procedure_by_id, get_matching_procedures
from services.compliance_service import sync_compliance_status_from_procedures
from services.reminder_service import create_reminders_on_initialization, create_reminders_on_assignment


def initialize_startup_procedures(
    startup: Startup,
    session: Session,
    mode: str = "auto"
) -> None:
    """
    Create StartupProcedure records for a startup and generate reminders.
    Also syncs ComplianceStatus records via compliance service.
    
    Args:
        startup: The Startup object
        session: Database session
        mode: "auto" for auto-assignment or "manual" for manual list (not used here)
    """
    if mode != "auto":
        return
    
    # Get applicable procedures based on startup attributes
    matching_ids = get_matching_procedures(
        legal_form=startup.legal_form,
        field=startup.field,
        size=startup.size,
        location=startup.location if startup.location != "Tunis" else None
    )
    
    procedures = load_procedures()
    
    # Create StartupProcedure records (one per procedure)
    for procedure_id in matching_ids:
        proc = get_procedure_by_id(procedure_id, procedures)
        if not proc:
            continue
        
        # Check if already exists
        existing = session.query(StartupProcedure).filter_by(
            startup_id=startup.id,
            procedure_id=procedure_id
        ).first()
        
        if existing:
            continue
        
        procedure_name = proc.get("name", "Unknown")
        domain = proc.get("domain", "other")
        due_days = proc.get("due_days", 30)  # Read from procedures.json, default to 30
        due_date = (startup.created_at + timedelta(days=due_days)).date()
        
        startup_procedure = StartupProcedure(
            startup_id=startup.id,
            procedure_id=procedure_id,
            procedure_name=procedure_name,
            domain=domain,
            status="pending",
            due_date=due_date,
            assigned_at=datetime.utcnow(),
            completed_step_ids=json.dumps([])  # Initialize as empty JSON array
        )
        session.add(startup_procedure)
    
    session.commit()
    
    # Create reminders for all assigned procedures
    create_reminders_on_initialization(startup, session)


def assign_procedures_to_startup(
    startup_id: int,
    procedure_ids: List[int],
    session: Session
) -> list:
    """
    Assign one or more procedures to a startup (manual assignment).
    Validates procedures exist in procedures.json and creates StartupProcedure records.
    Generates reminders based on due_days from procedures.json.
    Syncs compliance status after assignment.
    
    Args:
        startup_id: ID of the startup
        procedure_ids: List of procedure IDs to assign
        session: Database session
    
    Returns:
        List of created/existing StartupProcedure records
    
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

        # Get procedure details
        procedure_name = procedure.get("name", "Unknown")
        domain = procedure.get("domain", "other")
        due_days = procedure.get("due_days", 30)  # Read from procedures.json, default to 30
        due_date = (startup.created_at + timedelta(days=due_days)).date()

        # Create assignment with new model fields
        startup_procedure = StartupProcedure(
            startup_id=startup_id,
            procedure_id=procedure_id,
            procedure_name=procedure_name,
            domain=domain,
            status="pending",
            due_date=due_date,
            assigned_at=datetime.utcnow(),
            completed_step_ids=json.dumps([])  # Initialize as empty JSON array
        )
        session.add(startup_procedure)
        created_assignments.append(startup_procedure)
    
    session.commit()
    for sp in created_assignments:
        session.refresh(sp)
    
    # Create reminders for newly assigned procedures
    new_procedure_ids = [sp.procedure_id for sp in created_assignments]
    if new_procedure_ids:
        create_reminders_on_assignment(startup_id, new_procedure_ids, session)
    
    # Sync compliance status for all affected domains
    sync_compliance_status_from_procedures(startup_id, session)
    
    return created_assignments


def delete_startup_procedure(
    startup_procedure_id: int,
    session: Session
) -> dict:
    """
    Delete a startup procedure assignment and sync compliance status.
    
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
    
    startup_id = sp.startup_id
    session.delete(sp)
    session.commit()
    
    # Sync compliance status for all affected domains
    sync_compliance_status_from_procedures(startup_id, session)
    
    return {"message": "Procedure assignment deleted successfully"}

