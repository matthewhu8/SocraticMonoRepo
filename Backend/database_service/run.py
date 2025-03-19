#!/usr/bin/env python3
"""
Script to run the database service.
"""
import uvicorn
import os
from pathlib import Path

# Ensure the database file exists
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.path.join(BASE_DIR, "socratic.db")
DB_DIR = os.path.dirname(DB_PATH)

# Create database directory if it doesn't exist
os.makedirs(DB_DIR, exist_ok=True)

if __name__ == "__main__":
    print(f"Starting database service. SQLite database at: {DB_PATH}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8001, reload=True) 