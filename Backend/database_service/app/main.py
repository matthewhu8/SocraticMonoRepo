from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta

from .database.database import get_db, engine
from .database.models import Base, Test, Question, TestQuestion, TestResult, QuestionResult, ChatMessage, StudentUser, TeacherUser
from .auth.utils import verify_password, get_password_hash, create_access_token, create_refresh_token
from .auth.schemas import TokenResponse, UserLogin, StudentCreate, TeacherCreate, StudentResponse, TeacherResponse, RefreshToken
from .auth.dependencies import get_current_user, get_current_student, get_current_teacher
from jose import jwt, JWTError
from .auth.utils import SECRET_KEY, ALGORITHM

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Database Service")

# Pydantic models for request/response
class OrmBaseModel(BaseModel):
    class Config:
        orm_mode = True

class TestBase(OrmBaseModel):
    test_name: Optional[str] = None
    code: str
    isPracticeExam: Optional[bool] = False

class TestCreate(TestBase):
    questions: List[Dict[str, Any]]

class QuestionBase(OrmBaseModel):
    public_question: str
    hidden_values: Dict[str, Any]
    answer: str
    formula: Optional[str] = None
    teacher_instructions: Optional[str] = None
    hint_level: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None

class TestQuestionCreate(OrmBaseModel):
    test_id: int
    question_id: int
    position: int

class TestResultBase(OrmBaseModel):
    test_code: str
    username: str
    score: Optional[float] = None
    total_questions: Optional[int] = None
    correct_questions: Optional[int] = None
    end_time: Optional[datetime] = None

class QuestionResultBase(OrmBaseModel):
    question_id: int
    student_answer: Optional[str] = None
    isCorrect: Optional[bool] = False
    time_spent: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None

class ChatMessageBase(OrmBaseModel):
    sender: str
    content: str
    timestamp: Optional[datetime] = None

# Response models
class ChatMessageResponse(ChatMessageBase):
    id: int
    question_result_id: int

class QuestionResultResponse(QuestionResultBase):
    id: int
    test_result_id: int
    chat_messages: List[ChatMessageResponse] = []

class TestResultResponse(TestResultBase):
    id: int
    start_time: datetime
    question_results: List[QuestionResultResponse] = []

class QuestionResponse(QuestionBase):
    id: int

class TestResponse(TestBase):
    id: int
    test_name: str
    code: str
    isPracticeExam: bool = False
    questions: List[QuestionResponse] = []

# Authentication endpoints
@app.post("/auth/student/register", response_model=StudentResponse)
async def register_student(student: StudentCreate, db: Session = Depends(get_db)):
    """Register a new student user."""
    # Check if email already exists
    db_student = db.query(StudentUser).filter(StudentUser.email == student.email).first()
    if db_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new student user with hashed password
    hashed_password = get_password_hash(student.password)
    db_student = StudentUser(
        name=student.name,
        email=student.email,
        hashed_password=hashed_password,
        grade=student.grade
    )
    
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    return db_student

@app.post("/auth/teacher/register", response_model=TeacherResponse)
async def register_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    """Register a new teacher user."""
    # Check if email already exists
    db_teacher = db.query(TeacherUser).filter(TeacherUser.email == teacher.email).first()
    if db_teacher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new teacher user with hashed password
    hashed_password = get_password_hash(teacher.password)
    db_teacher = TeacherUser(
        name=teacher.name,
        email=teacher.email,
        hashed_password=hashed_password,
        subject=teacher.subject,
        school=teacher.school
    )
    
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    
    return db_teacher

@app.post("/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate a user and return JWT tokens."""
    # Try to find user in student table
    student = db.query(StudentUser).filter(StudentUser.email == login_data.email).first()
    if student and verify_password(login_data.password, student.hashed_password):
        # Create token data for student
        token_data = {"sub": str(student.id), "type": "student"}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {"access_token": access_token, "refresh_token": refresh_token}
    
    # If not found in student table, try teacher table
    teacher = db.query(TeacherUser).filter(TeacherUser.email == login_data.email).first()
    if teacher and verify_password(login_data.password, teacher.hashed_password):
        # Create token data for teacher
        token_data = {"sub": str(teacher.id), "type": "teacher"}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        return {"access_token": access_token, "refresh_token": refresh_token}
    
    # If not found in either table, raise exception
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password",
        headers={"WWW-Authenticate": "Bearer"}
    )

@app.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh: RefreshToken, db: Session = Depends(get_db)):
    """Use a refresh token to get a new access token."""
    try:
        # Decode refresh token
        payload = jwt.decode(refresh.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if it's a refresh token
        if not payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user ID and type from token
        user_id = payload.get("sub")
        user_type = payload.get("type")
        
        if not user_id or not user_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token data",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Verify user exists
        if user_type == "student":
            user = db.query(StudentUser).filter(StudentUser.id == int(user_id)).first()
        else:
            user = db.query(TeacherUser).filter(TeacherUser.id == int(user_id)).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create new tokens
        token_data = {"sub": user_id, "type": user_type}
        new_access_token = create_access_token(token_data)
        new_refresh_token = create_refresh_token(token_data)
        
        return {"access_token": new_access_token, "refresh_token": new_refresh_token}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )

@app.get("/auth/student/me", response_model=StudentResponse)
async def get_student_me(current_user: StudentUser = Depends(get_current_student)):
    """Get the current student's information."""
    return current_user

@app.get("/auth/teacher/me", response_model=TeacherResponse)
async def get_teacher_me(current_user: TeacherUser = Depends(get_current_teacher)):
    """Get the current teacher's information."""
    return current_user

# Test endpoints
@app.post("/tests", response_model=TestResponse)
async def create_test(test: TestBase, db: Session = Depends(get_db)):
    """Create a new test entry in the database."""
    try:
        print(f"Creating test with name: {test.test_name}, code: {test.code}, isPracticeExam: {test.isPracticeExam}")
        
        # Create the test
        db_test = Test(test_name=test.test_name, code=test.code, isPracticeExam=test.isPracticeExam)
        db.add(db_test)
        db.commit()
        db.refresh(db_test)
        
        print(f"Test created with ID: {db_test.id}")
        return db_test
    except Exception as e:
        db.rollback()
        print(f"Error creating test: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating test: {str(e)}")

@app.get("/tests/by-code/{code}", response_model=TestResponse)
async def get_test_by_code(code: str, db: Session = Depends(get_db)):
    # Get the test and join with questions through TestQuestion
    # ordering the questions by their position
    db_test = db.query(Test).filter(Test.code == code).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Get questions for this test
    questions = db.query(Question)\
        .join(TestQuestion, Question.id == TestQuestion.question_id)\
        .filter(TestQuestion.test_id == db_test.id)\
        .order_by(TestQuestion.position)\
        .all()
    
    # Manually build the response by filling in each field
    return TestResponse(
        id=db_test.id,
        test_name=db_test.test_name,
        code=db_test.code,
        isPracticeExam=db_test.isPracticeExam,
        questions=[
            QuestionResponse(
                id=q.id,
                public_question=q.public_question,
                hidden_values=q.hidden_values,
                answer=q.answer,
                formula=q.formula,
                teacher_instructions=q.teacher_instructions,
                hint_level=q.hint_level,
                subject=q.subject,
                topic=q.topic
            ) for q in questions
        ]
    )

@app.get("/tests/{test_id}", response_model=TestResponse)
async def get_test(test_id: int, db: Session = Depends(get_db)):
    """Get a test by its ID with all associated questions."""
    db_test = db.query(Test).filter(Test.id == test_id).first()
    if not db_test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Get questions for this test using the same implementation as get_test_by_code
    questions = db.query(Question)\
        .join(TestQuestion, Question.id == TestQuestion.question_id)\
        .filter(TestQuestion.test_id == db_test.id)\
        .order_by(TestQuestion.position)\
        .all()
    
    # Manually build the response by filling in each field
    return TestResponse(
        id=db_test.id,
        test_name=db_test.test_name,
        code=db_test.code,
        isPracticeExam=db_test.isPracticeExam,
        questions=[
            QuestionResponse(
                id=q.id,
                public_question=q.public_question,
                hidden_values=q.hidden_values,
                answer=q.answer,
                formula=q.formula,
                teacher_instructions=q.teacher_instructions,
                hint_level=q.hint_level,
                subject=q.subject,
                topic=q.topic
            ) for q in questions
        ]
    )

# Question endpoints
@app.post("/create-question", response_model=QuestionResponse)
async def create_question(question: QuestionBase, db: Session = Depends(get_db)):
    print(question.public_question)
    db_question = Question(
        public_question=question.public_question,
        hidden_values=question.hidden_values,
        answer=question.answer,
        formula=question.formula,
        teacher_instructions=question.teacher_instructions,
        hint_level=question.hint_level,
        subject=question.subject,
        topic=question.topic
    )
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    # Manually construct the response
    return QuestionResponse(
        id=db_question.id,
        public_question=db_question.public_question,
        hidden_values=db_question.hidden_values,
        answer=db_question.answer,
        formula=db_question.formula,
        teacher_instructions=db_question.teacher_instructions,
        hint_level=db_question.hint_level,
        subject=db_question.subject,
        topic=db_question.topic
    )

@app.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_question(question_id: int, db: Session = Depends(get_db)):
    db_question = db.query(Question).filter(Question.id == question_id).first()
    if not db_question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Manually construct the response
    return QuestionResponse(
        id=db_question.id,
        public_question=db_question.public_question,
        hidden_values=db_question.hidden_values,
        answer=db_question.answer,
        formula=db_question.formula,
        teacher_instructions=db_question.teacher_instructions,
        hint_level=db_question.hint_level,
        subject=db_question.subject,
        topic=db_question.topic
    )

# Test-Question relationship endpoints
@app.post("/test-questions")
async def create_test_question(test_question: TestQuestionCreate, db: Session = Depends(get_db)):
    # Check if actual test and question exist, and if not, raise an error (can't create a relationship if one of the entities doesn't exist)
    test = db.query(Test).filter(Test.id == test_question.test_id).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    question = db.query(Question).filter(Question.id == test_question.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    # Create relationship
    db_test_question = TestQuestion(
        test_id=test_question.test_id,
        question_id=test_question.question_id,
        position=test_question.position
    )
    db.add(db_test_question)
    db.commit()
    
    return {"test_id": test_question.test_id, "question_id": test_question.question_id}

@app.get("/test-questions", response_model=List[QuestionResponse])
async def get_test_questions(test_id: Optional[int] = None, db: Session = Depends(get_db)):
    if test_id:
        # Get questions for a specific test
        questions = db.query(Question)\
            .join(TestQuestion, Question.id == TestQuestion.question_id)\
            .filter(TestQuestion.test_id == test_id)\
            .order_by(TestQuestion.position)\
            .all()
        
        # Manually build the response by filling in each field
        return [
            QuestionResponse(
                id=q.id,
                public_question=q.public_question,
                hidden_values=q.hidden_values,
                answer=q.answer,
                formula=q.formula,
                teacher_instructions=q.teacher_instructions,
                hint_level=q.hint_level,
                subject=q.subject,
                topic=q.topic
            ) for q in questions
        ]
    else:
        # Get all test-question relationships
        test_questions = db.query(TestQuestion).all()
        return [{"test_id": tq.test_id, "question_id": tq.question_id, "position": tq.position} for tq in test_questions]

@app.delete("/test-questions/{test_id}/{question_id}")
async def delete_test_question(test_id: int, question_id: int, db: Session = Depends(get_db)):
    db_test_question = db.query(TestQuestion)\
        .filter(TestQuestion.test_id == test_id, TestQuestion.question_id == question_id)\
        .first()
    
    if not db_test_question:
        raise HTTPException(status_code=404, detail="Test-question relationship not found")
    
    db.delete(db_test_question)
    db.commit()
    
    return {"message": "Test-question relationship deleted"}

@app.post("/test-results/", response_model=TestResultResponse)
async def create_test_result(result: TestResultBase, db: Session = Depends(get_db)):
    db_result = TestResult(
        test_code=result.test_code,
        username=result.username,
        score=result.score,
        total_questions=result.total_questions,
        correct_questions=result.correct_questions,
        start_time=datetime.now(),
        end_time=result.end_time
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@app.post("/test-results/{result_id}/questions/", response_model=QuestionResultResponse)
async def add_question_result(result_id: int, question_result: QuestionResultBase, db: Session = Depends(get_db)):
    # Verify test result exists
    test_result = db.query(TestResult).filter(TestResult.id == result_id).first()
    if not test_result:
        raise HTTPException(status_code=404, detail=f"Test result with id {result_id} not found")
    
    # Create question result
    db_question_result = QuestionResult(
        test_result_id=result_id,
        question_id=question_result.question_id,
        student_answer=question_result.student_answer,
        isCorrect=question_result.isCorrect,
        time_spent=question_result.time_spent,
        start_time=question_result.start_time,
        end_time=question_result.end_time or datetime.now()
    )
    db.add(db_question_result)
    db.commit()
    db.refresh(db_question_result)
    
    return db_question_result

@app.post("/question-results/{result_id}/messages/", response_model=ChatMessageResponse)
async def add_chat_message(result_id: int, message: ChatMessageBase, db: Session = Depends(get_db)):
    # Verify question result exists
    question_result = db.query(QuestionResult).filter(QuestionResult.id == result_id).first()
    if not question_result:
        raise HTTPException(status_code=404, detail=f"Question result with id {result_id} not found")
    
    # Create chat message
    db_message = ChatMessage(
        question_result_id=result_id,
        sender=message.sender,
        content=message.content,
        timestamp=message.timestamp or datetime.now()
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    return db_message

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 