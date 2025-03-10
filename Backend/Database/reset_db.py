from sqlalchemy import create_engine
from .config import SQLALCHEMY_DATABASE_URL
from .models import Base

def reset_database():
    """Drop all tables and recreate them"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset complete!")

if __name__ == "__main__":
    reset_database() 