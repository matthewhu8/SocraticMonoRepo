#!/usr/bin/env python3
"""
Test script to verify database connection and create tables.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get the absolute path to the Backend folder
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.path.join(BASE_DIR, "socratic.db")

print(f"Checking database at: {DB_PATH}")

# Create database URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine and session
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import models and create tables
from app.database.models import Base

# Create all tables
Base.metadata.create_all(bind=engine)

# Test session creation
db = SessionLocal()
try:
    # Check connection by executing a simple query
    # Need to use text() for raw SQL with SQLAlchemy 2.0
    result = db.execute(text("SELECT 1")).fetchone()
    print(f"Database connection successful: {result}")
finally:
    db.close()

print("Database tables created successfully.")
print(f"SQLite database is ready at: {DB_PATH}") 