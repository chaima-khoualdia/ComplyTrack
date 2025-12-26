from sqlmodel import SQLModel, Field, Relationship
from typing import Optional

class Step(SQLModel, table=True):
    __tablename__ = "steps"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    procedure_id: int = Field(foreign_key="procedures.id", nullable=False)
    name: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    order: int = Field(nullable=False)
    is_required: bool = Field(default=True, nullable=False)
    
    procedure: "Procedure" = Relationship(back_populates="steps")
