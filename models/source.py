from sqlmodel import SQLModel, Field, Relationship

class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: int = Field(primary_key=True)
    name: str = Field(nullable=False)
    url: str = Field(nullable=False)
