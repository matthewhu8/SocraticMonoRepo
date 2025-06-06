from sqlalchemy import Boolean, Column, Integer, String, Float, JSON, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

# New models for authentication
class StudentUser(Base):
    __tablename__ = "student_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    grade = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationship to test results
    test_results = relationship("TestResult", back_populates="student")

class TeacherUser(Base):
    __tablename__ = "teacher_users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    subject = Column(String)
    school = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_name = Column(String, index=True, nullable=True)
    code = Column(String, unique=True, index=True, nullable=False)
    isPracticeExam = Column(Boolean, default=False)
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
    formula = Column(Text)
    teacher_instructions = Column(Text)
    hint_level = Column(String)
    subject = Column(String)
    topic = Column(String)
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
    
    # Add foreign key to student user
    student_id = Column(Integer, ForeignKey("student_users.id"), nullable=True)
    student = relationship("StudentUser", back_populates="test_results")
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