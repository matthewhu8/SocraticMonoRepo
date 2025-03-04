from sqlalchemy import Column, Integer, String, Text
from .database import Base

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    questions = Column(Text, nullable=False)  # Storing questions as a JSON string


