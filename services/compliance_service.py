"""
Compliance Service
Handles compliance status tracking and badge computation logic.
"""

from sqlmodel import Session, select
from models import ComplianceStatus
from datetime import datetime


def compute_badge(statuses: list[ComplianceStatus]) -> str:
    """
    Compute compliance badge status based on compliance statuses.
    
    Logic:
    - RED: Any overdue compliance item
    - GREEN: All items complete and none overdue
    - YELLOW: In progress or pending items, none overdue
    
    Args:
        statuses: List of ComplianceStatus records for a startup
        
    Returns:
        Badge status: "red", "green", or "yellow"
    """
    if not statuses:
        return "yellow"  # No compliance items yet
    
    has_overdue = any(s.status == "overdue" for s in statuses)
    if has_overdue:
        return "red"
    
    all_complete = all(s.status == "complete" for s in statuses)
    if all_complete:
        return "green"
    
    return "yellow"


def summarize_statuses(statuses: list[ComplianceStatus]) -> dict:
    """
    Create a summary of compliance statuses by count.
    
    Args:
        statuses: List of ComplianceStatus records
        
    Returns:
        Dictionary with counts: {pending, in_progress, complete, overdue}
    """
    return {
        "pending": sum(1 for s in statuses if s.status == "pending"),
        "in_progress": sum(1 for s in statuses if s.status == "in_progress"),
        "complete": sum(1 for s in statuses if s.status == "complete"),
        "overdue": sum(1 for s in statuses if s.status == "overdue"),
        "total": len(statuses),
    }


def get_startup_compliance_statuses(startup_id: int, session: Session) -> list[ComplianceStatus]:
    """
    Get all compliance statuses for a startup.
    
    Args:
        startup_id: ID of the startup
        session: Database session
        
    Returns:
        List of ComplianceStatus records
    """
    stmt = select(ComplianceStatus).where(ComplianceStatus.startup_id == startup_id)
    return session.exec(stmt).all()


def mark_complete(status_id: int, session: Session) -> ComplianceStatus:
    """
    Mark a compliance status as complete with current timestamp.
    
    Args:
        status_id: ID of ComplianceStatus record
        session: Database session
        
    Returns:
        Updated ComplianceStatus
        
    Raises:
        ValueError: If status not found
    """
    status = session.get(ComplianceStatus, status_id)
    if not status:
        raise ValueError(f"Compliance status {status_id} not found")
    
    status.status = "complete"
    status.completed_at = datetime.utcnow()
    session.add(status)
    session.commit()
    session.refresh(status)
    return status


def sync_compliance_status_from_procedures(
    startup_id: int,
    domain: str,
    session: Session
) -> None:
    """
    Update ComplianceStatus for a domain based on its procedures' statuses.
    
    Logic:
    - If ALL procedures in domain are "completed" → mark ComplianceStatus as "completed"
    - If ANY procedure is "overdue" → mark ComplianceStatus as "overdue"
    - If ANY procedure is "in_progress" → mark ComplianceStatus as "in_progress"
    - Otherwise → keep as "pending"
    
    Args:
        startup_id: ID of the startup
        domain: Domain name (e.g., "tax_compliance")
        session: Database session
    """
    from models import StartupProcedure
    
    # Get all procedures for this domain
    domain_procedures = session.query(StartupProcedure).filter_by(
        startup_id=startup_id,
        domain=domain
    ).all()
    
    if not domain_procedures:
        return
    
    # Determine overall domain status based on procedures
    statuses = [proc.status for proc in domain_procedures]
    
    if all(s == "completed" for s in statuses):
        new_status = "completed"
        completed_at = datetime.utcnow()
    elif any(s == "overdue" for s in statuses):
        new_status = "overdue"
        completed_at = None
    elif any(s == "in_progress" for s in statuses):
        new_status = "in_progress"
        completed_at = None
    else:
        new_status = "pending"
        completed_at = None
    
    # Update ComplianceStatus
    compliance = session.query(ComplianceStatus).filter_by(
        startup_id=startup_id,
        domain=domain
    ).first()
    
    if compliance:
        compliance.status = new_status
        compliance.completed_at = completed_at
        session.add(compliance)
        session.commit()
