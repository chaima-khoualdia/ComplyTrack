from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

class InvestorRequest(SQLModel, table=True):
    __tablename__ = "investor_requests"

    id: int = Field(primary_key=True)
    investor_id: int = Field(foreign_key="users.id", nullable=False)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    request_date: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    badge_status_at_request: str = Field(default="red", nullable=False)  # green, yellow, red

    investor: "User" = Relationship(back_populates="investor_requests")
    startup: "Startup" = Relationship(back_populates="investor_requests")
