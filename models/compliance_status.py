from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime
from typing import Optional

class ComplianceStatus(SQLModel, table=True):
    __tablename__ = "compliance_status"

    id: int = Field(primary_key=True)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    procedure_id: Optional[int] = Field(default=None, nullable=True)  # Reference to procedure in procedures.json (may be null for domain-level tracking)
    domain: str = Field(nullable=False)  # Domain category (e.g., tax_compliance, legal_registration)
    status: str = Field(nullable=False)  # pending, in_progress, completed, overdue
    due_date: date = Field(nullable=False)
    completed_at: Optional[datetime] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    startup: "Startup" = Relationship(back_populates="compliance_statuses")
