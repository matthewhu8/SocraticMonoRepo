from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Create an absolute path to the Backend folder
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = os.path.join(BASE_DIR, "socratic.db")

# Use absolute path for SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")
print(f"Using database at: {DB_PATH}")

# Create database directory if it doesn't exist
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Add echo=False to suppress SQL logs if that's causing warnings
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 