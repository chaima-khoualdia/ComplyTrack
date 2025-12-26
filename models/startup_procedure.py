from sqlmodel import SQLModel, Field, Relationship, Column
from sqlalchemy import JSON
from typing import Optional
from datetime import datetime

class StartupProcedure(SQLModel, table=True):
    __tablename__ = "startup_procedures"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    procedure_id: int = Field(foreign_key="procedures.id", nullable=False)
    completed_step_ids: list = Field(default_factory=list, sa_column=Column(JSON))
    assigned_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    startup: "Startup" = Relationship(back_populates="startup_procedures")
    procedure: "Procedure" = Relationship(back_populates="startup_procedures")
