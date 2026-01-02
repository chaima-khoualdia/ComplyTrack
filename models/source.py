from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    url: str = Field(nullable=False)
    description: Optional[str] = Field(default=None)
    type: str = Field(nullable=False)  # "law", "portal", "guide"
    country: str = Field(default="Tunisia", nullable=False)
    language: str = Field(default="fr", nullable=False)  # "fr", "ar", "en"
    last_verified: Optional[datetime] = Field(default=None)
