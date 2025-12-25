from sqlmodel import SQLModel, Field, Relationship
from datetime import date

class Reminder(SQLModel, table=True):
    __tablename__ = "reminders"

    id: int = Field(primary_key=True)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    reminder_date: date = Field(nullable=False)
    message: str = Field(nullable=False)
    status: str = Field(nullable=False)  # pending, sent, cancelled

    startup: "Startup" = Relationship(back_populates="reminders")
