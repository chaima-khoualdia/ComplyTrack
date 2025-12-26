from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime

class Procedure(SQLModel, table=True):
    __tablename__ = "procedures"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    steps: List["Step"] = Relationship(back_populates="procedure")
    startup_procedures: List["StartupProcedure"] = Relationship(back_populates="procedure")
