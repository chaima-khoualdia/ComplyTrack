from sqlmodel import SQLModel, Field

class ProcedureProgress(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    startup_id: int = Field(foreign_key="startups.id", nullable=False)
    procedure_id: int = Field(nullable=False)  # matches JSON procedure id
    steps_completed: int = Field(default=0, nullable=False)
