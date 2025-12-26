from sqlmodel import SQLModel, create_engine, Session
from models import ProcedureProgress, startup, User
# Use SQLite for development (creates a local file scos.db)
DATABASE_URL = "sqlite:///./scos.db"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
