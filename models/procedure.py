from sqlmodel import SQLModel, Field, Relationship
from typing import List

class Procedure(SQLModel, table=True):
    __tablename__ = "procedures"

    id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    description: str = Field(nullable=False)

    steps: list["Step"] = Relationship(back_populates="procedure")
