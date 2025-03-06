from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String, index=True, nullable=True)
    code = Column(String, unique=True, index=True, nullable=False)
    questions = Column(Text, nullable=False)  # Storing questions as a JSON string

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    test_code = Column(String, index=True)
    username = Column(String, index=True)
    score = Column(Float)
    total_questions = Column(Integer)
    correct_questions = Column(Integer)
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    
    # Relationship with question results
    question_results = relationship("QuestionResult", back_populates="test_result")

class QuestionResult(Base):
    __tablename__ = "question_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"))
    question_index = Column(Integer)
    student_answer = Column(String, nullable=True)
    is_correct = Column(Boolean, default=False)
    time_spent = Column(Integer)  # in seconds
    start_time = Column(DateTime)
    end_time = Column(DateTime, nullable=True)
    
    # Relationship with test result
    test_result = relationship("TestResult", back_populates="question_results")
    
    # Relationship with chat messages
    chat_messages = relationship("ChatMessage", back_populates="question_result")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    question_result_id = Column(Integer, ForeignKey("question_results.id"))
    sender = Column(String)  # 'student' or 'ai'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    
    # Relationship with question result
    question_result = relationship("QuestionResult", back_populates="chat_messages")
