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


def build_compliance_summary_from_procedures(startup_id: int, session: Session) -> dict:
    """
    Build a comprehensive compliance summary from StartupProcedure records.
    
    Groups procedures by domain, calculates status counts, and determines badge status.
    Uses actual procedure data (not ComplianceStatus) for real-time compliance view.
    
    Args:
        startup_id: ID of the startup
        session: Database session
        
    Returns:
        Dictionary with:
        - summary: counts of pending, in_progress, complete, overdue, total
        - badge_status: "green", "yellow", or "red"
        - compliance_by_domain: grouped procedures by domain with details
    """
    from models import StartupProcedure
    from datetime import date
    
    # Get all procedures for this startup
    procedures = session.query(StartupProcedure).filter_by(
        startup_id=startup_id
    ).order_by(StartupProcedure.domain, StartupProcedure.due_date).all()
    
    if not procedures:
        return {
            "summary": {
                "pending": 0,
                "in_progress": 0,
                "complete": 0,
                "overdue": 0,
                "total": 0
            },
            "badge_status": "yellow",
            "compliance_by_domain": {}
        }
    
    # Update overdue status based on current date
    today = date.today()
    for proc in procedures:
        if proc.status not in ["completed", "complete"] and proc.due_date < today:
            proc.status = "overdue"
            session.add(proc)
    session.commit()
    
    # Build summary counts
    summary = {
        "pending": sum(1 for p in procedures if p.status == "pending"),
        "in_progress": sum(1 for p in procedures if p.status == "in_progress"),
        "complete": sum(1 for p in procedures if p.status in ["completed", "complete"]),
        "overdue": sum(1 for p in procedures if p.status == "overdue"),
        "total": len(procedures)
    }
    
    # Determine badge status
    has_overdue = any(p.status == "overdue" for p in procedures)
    all_complete = all(p.status in ["completed", "complete"] for p in procedures)
    
    if has_overdue:
        badge_status = "red"
    elif all_complete:
        badge_status = "green"
    else:
        badge_status = "yellow"
    
    # Group procedures by domain
    compliance_by_domain = {}
    for proc in procedures:
        domain = proc.domain
        if domain not in compliance_by_domain:
            compliance_by_domain[domain] = []
        
        compliance_by_domain[domain].append({
            "id": proc.id,
            "procedure_id": proc.procedure_id,
            "procedure_name": proc.procedure_name,
            "status": proc.status,
            "due_date": proc.due_date.isoformat() if proc.due_date else None,
            "completed_at": proc.completed_at.isoformat() if proc.completed_at else None,
            "domain": proc.domain
        })
    
    return {
        "summary": summary,
        "badge_status": badge_status,
        "compliance_by_domain": compliance_by_domain
    }
