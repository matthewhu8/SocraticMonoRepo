from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String, index=True, nullable=True)
    code = Column(String, unique=True, index=True, nullable=False)
    questions = relationship("Question", secondary="test_questions", back_populates="tests")

class TestQuestion(Base):
    __tablename__ = "test_questions"
    test_id = Column(Integer, ForeignKey("tests.id"), primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id"), primary_key=True)
    position = Column(Integer)

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True, index=True)
    public_question = Column(Text, nullable=False)
    hidden_values = Column(JSON, nullable=False)
    answer = Column(Text, nullable=False)
    teacher_instructions = Column(Text)
    subject = Column(String)
    topic = Column(String)
    image_url = Column(String, nullable=True)

    tests = relationship("Test", secondary="test_questions", back_populates="questions")

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
    
    question_results = relationship("QuestionResult", back_populates="test_result")

class QuestionResult(Base):
    __tablename__ = "question_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    student_answer = Column(String, nullable=True)
    isCorrect = Column(Boolean, default=False)
    time_spent = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    
    test_result = relationship("TestResult", back_populates="question_results")
    chat_messages = relationship("ChatMessage", back_populates="question_result")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    question_result_id = Column(Integer, ForeignKey("question_results.id"))
    sender = Column(String)  # 'student' or 'ai'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    
    question_result = relationship("QuestionResult", back_populates="chat_messages") 