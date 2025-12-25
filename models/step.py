from sqlmodel import SQLModel, Field, Relationship

class Step(SQLModel, table=True):
    __tablename__ = "steps"

    id: int = Field(primary_key=True)
    procedure_id: int = Field(foreign_key="procedures.id", nullable=False)
    description: str = Field(nullable=False)
    order: int = Field(nullable=False)

    procedure: "Procedure" = Relationship(back_populates="steps")
    sources: list["Source"] = Relationship(back_populates="step")
