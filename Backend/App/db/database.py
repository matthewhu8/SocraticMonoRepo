from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace these placeholders with your PostgreSQL credentials and database name.
# SQLALCHEMY_DATABASE_URL = "postgresql://your_username:your_password@localhost/your_dbname"
SQLALCHEMY_DATABASE_URL = "sqlite:///./socratic.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()