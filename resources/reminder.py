from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from db import get_session
from models import Reminder, reminder

router = APIRouter(prefix="/reminders", tags=["reminders"]) 

class Reminders:
    @router.get("/by-startup/{startup_id}", response_model=list[Reminder])
    def list_by_startup(startup_id: int, session: Session = Depends(get_session)):
        stmt = select(Reminder).where(Reminder.startup_id == startup_id)
        return session.exec(stmt).all()
    @router.get("/{reminder_id}", response_model=Reminder)
    def get_reminder(reminder_id: int, session: Session = Depends(get_session)):
        reminder = session.get(Reminder, reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        return reminder
    @router.post("/", response_model=Reminder)
    def create_reminder(reminder: Reminder, session: Session = Depends(get_session)):
        session.add(reminder)
        session.commit()
        session.refresh(reminder)
        return reminder
    @router.delete("/{reminder_id}")
    def delete_reminder(reminder_id: int, session: Session = Depends(get_session)):
        reminder = session.get(Reminder, reminder_id)
        if not reminder:
            raise HTTPException(status_code=404, detail="Reminder not found")
        session.delete(reminder)
        session.commit()
        return {"message": "Reminder deleted"}