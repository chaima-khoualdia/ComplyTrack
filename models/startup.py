from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime

class Startup(SQLModel, table=True):
    __tablename__ = "startups"

    id: int = Field(primary_key=True)
    founder_id: int = Field(foreign_key="users.id", nullable=False)
    name: str = Field(nullable=False)
    matricule_fiscal: str = Field(unique=True, nullable=False)
    rne_number: str = Field(unique=True, nullable=False)

    legal_form: str = Field(nullable=False)   # e.g. "SARL", "SA"
    field: str = Field(nullable=False)        # e.g. "tech", "healthcare", "finance"
    sector: str = Field(nullable=False)       # e.g. "private", "public", "ngo"
    size: str = Field(nullable=False)         # e.g. "small", "medium", "large"
    location: str = Field(nullable=False)     # e.g. "Tunis", "Sfax", "Free Zone"

    badge_status: str = Field(default="red", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    founder: "User" = Relationship(back_populates="startups")
    compliance_statuses: List["ComplianceStatus"] = Relationship(back_populates="startup")
    reminders: List["Reminder"] = Relationship(back_populates="startup")
    investor_requests: List["InvestorRequest"] = Relationship(back_populates="startup")
    startup_procedures: List["StartupProcedure"] = Relationship(back_populates="startup")
