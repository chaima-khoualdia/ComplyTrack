from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime

class ComplianceStatus(SQLModel, table=True):
    __tablename__ = "compliance_status"

    id: int = Field(primary_key=True)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    status: str = Field(nullable=False)  # pending, in_progress, complete, overdue
    due_date: date = Field(nullable=False)
    completed_at: datetime = Field(nullable=False)

    startup: "Startup" = Relationship(back_populates="compliance_statuses")
