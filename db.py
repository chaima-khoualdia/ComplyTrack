from sqlmodel import SQLModel, create_engine, Session
import os

# Use SQLite for development (creates a local file scos.db)
# In Docker, this will be at /app/data/scos.db (persisted to ./data/scos.db on host)
db_path = os.environ.get('DATABASE_PATH', './data/scos.db')
DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
