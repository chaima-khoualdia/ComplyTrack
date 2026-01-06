from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class Request(SQLModel, table=True):
    __tablename__ = "requests"

    id: int = Field(primary_key=True)
    worker_user_id: int = Field(foreign_key="users.id", nullable=False)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    owner_user_id: int = Field(foreign_key="users.id", nullable=False)
    status: str = Field(default="pending", nullable=False)  # pending, approved, active, rejected
    invitation_code: Optional[str] = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: Optional[datetime] = Field(default=None, nullable=True)

    worker: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Request.worker_user_id]"}
    )
    startup: "Startup" = Relationship(back_populates="requests")
    owner: "User" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Request.owner_user_id]"}
    )
