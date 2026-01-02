from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, date

class StartupProcedure(SQLModel, table=True):
    __tablename__ = "startup_procedures"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    procedure_id: int = Field(nullable=False)  # References procedures.json
    procedure_name: str = Field(nullable=False)  # e.g., "Register SARL", "Tax Compliance"
    domain: str = Field(nullable=False)  # e.g., "legal_registration", "tax_compliance", "tech_ip_compliance"
    status: str = Field(default="pending", nullable=False)  # pending, in_progress, completed, overdue
    due_date: date = Field(nullable=False)
    assigned_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)
    completed_step_ids: Optional[str] = Field(default="[]", nullable=True)  # JSON list of completed step IDs for this procedure
    
    startup: "Startup" = Relationship(back_populates="startup_procedures")
