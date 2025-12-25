from sqlmodel import SQLModel, Field, Relationship

class Source(SQLModel, table=True):
    __tablename__ = "sources"

    id: int = Field(primary_key=True)
    step_id: int = Field(foreign_key="steps.id", nullable=False)
    name: str = Field(nullable=False)
    url: str = Field(nullable=False)

    step: "Step" = Relationship(back_populates="sources")
