from sqlmodel import SQLModel, Field, Relationship
from typing import List
from datetime import datetime

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    password_hash: str = Field(nullable=False)
    role: str = Field(nullable=False)
    first_name: str = Field(nullable=False)
    last_name: str = Field(nullable=False)
    created_at: datetime = Field(nullable=False)

    startups: List["Startup"] = Relationship(back_populates="founder")
    investor_requests: List["InvestorRequest"] = Relationship(back_populates="investor")
