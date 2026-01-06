"""
Reminder Service
Handles creation of reminders for compliance procedures based on due_days from procedures.json
"""

from datetime import datetime, timedelta
from sqlmodel import Session
from models import Reminder, Startup, StartupProcedure
from services.procedures_service import get_procedure_by_id, load_procedures


def create_reminder_for_procedure(
    startup: Startup,
    procedure_id: int,
    session: Session
) -> Reminder:
    """
    Create a reminder for a procedure based on its due_days.
    
    Args:
        startup: The Startup object
        procedure_id: ID of the procedure
        session: Database session
    
    Returns:
        Created Reminder object
    
    Raises:
        ValueError: If procedure not found in procedures.json
    """
    procedures = load_procedures()
    procedure = get_procedure_by_id(procedure_id, procedures)
    
    if not procedure:
        raise ValueError(f"Procedure {procedure_id} not found in procedures.json")
    
    # Get due_days from procedure, default to 30 if not specified
    due_days = procedure.get("due_days", 30)
    procedure_name = procedure.get("name", "Unknown")
    
    # Calculate reminder date: startup registration date + due_days
    registration_date = startup.created_at.date() if isinstance(startup.created_at, datetime) else startup.created_at
    reminder_date = registration_date + timedelta(days=due_days)
    
    # Create message
    message = f"{procedure_name} due by {reminder_date.strftime('%Y-%m-%d')}"
    
    # Create reminder
    reminder = Reminder(
        startup_id=startup.id,
        reminder_date=reminder_date,
        message=message,
        status="pending"
    )
    
    session.add(reminder)
    return reminder


def create_reminders_for_startup(
    startup: Startup,
    procedure_ids: list,
    session: Session
) -> list:
    """
    Create reminders for multiple procedures assigned to a startup.
    
    Args:
        startup: The Startup object
        procedure_ids: List of procedure IDs
        session: Database session
    
    Returns:
        List of created Reminder objects
    """
    created_reminders = []
    
    for procedure_id in procedure_ids:
        try:
            # Check if reminder already exists
            existing = session.query(Reminder).filter(
                Reminder.startup_id == startup.id,
                Reminder.message.contains(str(procedure_id))  # Simple check based on message
            ).first()
            
            if not existing:
                reminder = create_reminder_for_procedure(startup, procedure_id, session)
                created_reminders.append(reminder)
        except ValueError:
            # Procedure not found, skip it
            continue
    
    return created_reminders


def create_reminders_on_assignment(
    startup_id: int,
    procedure_ids: list,
    session: Session
) -> list:
    """
    Create reminders when procedures are assigned to a startup.
    Called automatically when procedures are assigned.
    
    Args:
        startup_id: ID of the startup
        procedure_ids: List of procedure IDs being assigned
        session: Database session
    
    Returns:
        List of created Reminder objects
    """
    startup = session.get(Startup, startup_id)
    if not startup:
        raise ValueError(f"Startup {startup_id} not found")
    
    reminders = create_reminders_for_startup(startup, procedure_ids, session)
    session.commit()
    
    return reminders


def create_reminders_on_initialization(
    startup: Startup,
    session: Session
) -> list:
    """
    Create reminders for all procedures assigned during auto-initialization.
    Called after all StartupProcedure records are created.
    
    Args:
        startup: The Startup object
        session: Database session
    
    Returns:
        List of created Reminder objects
    """
    # Get all procedures assigned to this startup
    startup_procedures = session.query(StartupProcedure).filter(
        StartupProcedure.startup_id == startup.id
    ).all()
    
    procedure_ids = [sp.procedure_id for sp in startup_procedures]
    reminders = create_reminders_for_startup(startup, procedure_ids, session)
    session.commit()
    
    return reminders


def get_upcoming_reminders(
    startup_id: int,
    days_ahead: int = 30,
    session: Session = None
) -> list:
    """
    Get upcoming reminders for a startup within the specified number of days.
    
    Args:
        startup_id: ID of the startup
        days_ahead: Number of days to look ahead (default 30)
        session: Database session
    
    Returns:
        List of upcoming Reminder objects
    """
    if session is None:
        return []
    
    today = datetime.utcnow().date()
    deadline = today + timedelta(days=days_ahead)
    
    reminders = session.query(Reminder).filter(
        Reminder.startup_id == startup_id,
        Reminder.status == "pending",
        Reminder.reminder_date >= today,
        Reminder.reminder_date <= deadline
    ).order_by(Reminder.reminder_date).all()
    
    return reminders


def mark_reminder_as_sent(
    reminder_id: int,
    session: Session
) -> Reminder:
    """
    Mark a reminder as sent (after email notification is sent).
    
    Args:
        reminder_id: ID of the reminder
        session: Database session
    
    Returns:
        Updated Reminder object
    """
    reminder = session.get(Reminder, reminder_id)
    if reminder:
        reminder.status = "sent"
        session.add(reminder)
        session.commit()
        session.refresh(reminder)
    return reminder
