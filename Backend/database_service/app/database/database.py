from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Create an absolute path to the Backend folder for SQLite
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = os.path.join(BASE_DIR, "socratic.db")
DEFAULT_SQLITE_URL = f"sqlite:///{DB_PATH}"

# PostgreSQL configuration (now as fallback)
DEFAULT_POSTGRES_URL = "postgresql://postgres:postgres@localhost:5432/socratic"

# Use SQLite by default, PostgreSQL as fallback
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)
print(f"Using database URL: {DATABASE_URL}")
DATABASE_URL = DEFAULT_SQLITE_URL # comment this out to use PostgreSQL

# Create SQLAlchemy engine with appropriate parameters
engine_args = {}
if "sqlite" in DATABASE_URL:
    # SQLite-specific arguments
    engine_args["connect_args"] = {"check_same_thread": False}
    # Create database directory if it doesn't exist for SQLite
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    print(f"Using SQLite database at: {DB_PATH}")

engine = create_engine(DATABASE_URL, echo=False, future=True, **engine_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 