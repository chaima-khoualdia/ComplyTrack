from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Reminder
from services.reminder_service import get_upcoming_reminders, mark_reminder_as_sent
from services.scheduler_service import (
    get_scheduler_status,
    run_reminder_check_now,
    start_scheduler,
    stop_scheduler
)
from services.auth_service import require_roles

router = APIRouter(prefix="/reminders", tags=["reminders"]) 

class Reminders:
    @router.get("/by-startup/{startup_id}", response_model=list[Reminder])
    def list_by_startup(
        startup_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
    ):
        stmt = select(Reminder).where(Reminder.startup_id == startup_id)
        return session.exec(stmt).all()
    
    @router.get("/upcoming/{startup_id}", response_model=list[Reminder])
    def get_upcoming(
        startup_id: int,
        days_ahead: int = 30,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
    ):
        """Get upcoming reminders for a startup within the specified number of days"""
        return get_upcoming_reminders(startup_id, days_ahead, session)
    
    @router.get("/{reminder_id}", response_model=Reminder)
    def get_reminder(
        reminder_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
    ):
        reminder = session.get(Reminder, reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return reminder
    
    @router.post("/", response_model=Reminder)
    def create_reminder(
        reminder: Reminder,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
    ):
        session.add(reminder)
        session.commit()
        session.refresh(reminder)
        return reminder
    
    @router.patch("/{reminder_id}/mark-sent", response_model=Reminder)
    def mark_as_sent(
        reminder_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "startup", "owner", "worker")),
    ):
        """Mark a reminder as sent after email notification"""
        reminder = mark_reminder_as_sent(reminder_id, session)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return reminder
    
    @router.delete("/{reminder_id}")
    def delete_reminder(
        reminder_id: int,
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin", "startup")),
    ):
        reminder = session.get(Reminder, reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        session.delete(reminder)
        session.commit()
        return {"message": "Reminder deleted"}

    @router.get("/")
    def list_all_reminders(
        session: Session = Depends(get_session),
        current_user=Depends(require_roles("admin")),
    ):
        """List all reminders across all startups (admin-only)."""
        stmt = select(Reminder)
        return session.exec(stmt).all()
    
    @router.get("/scheduler/status")
    def scheduler_status(current_user=Depends(require_roles("admin"))):
        """Get the status of the automated reminder email scheduler"""
        return get_scheduler_status()
    
    @router.post("/scheduler/run-now")
    def run_scheduler_now(current_user=Depends(require_roles("admin"))):
        """Manually trigger the reminder email check immediately"""
        run_reminder_check_now()
        return {"message": "Reminder email check triggered successfully"}
    
    @router.post("/scheduler/start")
    def start_email_scheduler(current_user=Depends(require_roles("admin"))):
        """Manually start the scheduler (usually starts automatically on app startup)"""
        start_scheduler()
        return {"message": "Scheduler started successfully"}
    
    @router.post("/scheduler/stop")
    def stop_email_scheduler(current_user=Depends(require_roles("admin"))):
        """Stop the automated reminder email scheduler"""
        stop_scheduler()
        return {"message": "Scheduler stopped successfully"}
