#!/usr/bin/env python3
"""
Script to run the database service.
"""
import uvicorn
import os
from pathlib import Path
from app.database.models import Base
from app.database.database import engine

# Create all tables in the database
Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "PostgreSQL database")
    print(f"Starting database service with {database_url}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True) 