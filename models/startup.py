from sqlmodel import SQLModel, Field, Relationship
from typing import List
from datetime import datetime

class Startup(SQLModel, table=True):
    __tablename__ = "startups"

    id: int = Field(primary_key=True)
    founder_id: int = Field(foreign_key="users.id", nullable=False)
    name: str = Field(nullable=False)
    matricule_fiscal: str = Field(unique=True, nullable=False)
    rne_number: str = Field(unique=True, nullable=False)
    sector: str = Field(nullable=False)
    badge_status: str = Field(default="red", nullable=False)
    created_at: datetime = Field(nullable=False)

    founder: "User" = Relationship(back_populates="startups")
    compliance_statuses: List["ComplianceStatus"] = Relationship(back_populates="startup")
    reminders: List["Reminder"] = Relationship(back_populates="startup")
    investor_requests: List["InvestorRequest"] = Relationship(back_populates="startup")
