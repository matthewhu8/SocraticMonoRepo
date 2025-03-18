from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .database.database import get_db
from .database.models import Test, Question, TestQuestion, TestResult, QuestionResult, ChatMessage

app = FastAPI(title="Database Service")

# Pydantic models for request/response
class TestBase(BaseModel):
    test_name: Optional[str] = None
    code: str

class TestCreate(TestBase):
    questions: List[Dict[str, Any]]

class QuestionBase(BaseModel):
    public_question: str
    hidden_values: Dict[str, Any]
    answer: str
    teacher_instructions: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None


class TestQuestionCreate(BaseModel):
    test_id: int
    question_id: int
    position: int

class TestResultBase(BaseModel):
    test_code: str
    username: str
    score: Optional[float] = None
    total_questions: Optional[int] = None
    correct_questions: Optional[int] = None
    end_time: Optional[datetime] = None

class QuestionResultBase(BaseModel):
    question_id: int
    student_answer: Optional[str] = None
    isCorrect: Optional[bool] = False
    time_spent: Optional[int] = None
    start_time: datetime
    end_time: Optional[datetime] = None

class ChatMessageBase(BaseModel):
    sender: str
    content: str
    timestamp: Optional[datetime] = None

# Response models; INCOMPLETE
class ChatMessageResponse(ChatMessageBase):
    id: int
    question_result_id: int

    class Config:
        orm_mode = True

# INCOMPLETE
class QuestionResultResponse(QuestionResultBase):
    id: int
    test_result_id: int
    chat_messages: List[ChatMessageResponse] = []

    class Config:
        orm_mode = True
        
# INCOMPLETE
class TestResultResponse(TestResultBase):
    id: int
    start_time: datetime
    question_results: List[QuestionResultResponse] = []

    class Config:
        orm_mode = True

class QuestionResponse(QuestionBase):
    id: int

    class Config:
        orm_mode = True

class TestResponse(TestBase):
    id: int
    test_name: str
    code: str
    questions: List[QuestionResponse] = []

    class Config:
        orm_mode = True

# Test endpoints
@app.post("/tests", response_model=TestResponse)
async def create_test(test: TestBase, db: Session = Depends(get_db)):
    db_test = Test(test_name=test.test_name, code=test.code)
    db.add(db_test)
    db.commit()
    db.refresh(db_test)
    return db_test


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
        questions=[
            QuestionResponse(
                id=q.id,
                public_question=q.public_question,
                hidden_values=q.hidden_values,
                answer=q.answer,
                teacher_instructions=q.teacher_instructions,
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
        questions=[
            QuestionResponse(
                id=q.id,
                public_question=q.public_question,
                hidden_values=q.hidden_values,
                answer=q.answer,
                teacher_instructions=q.teacher_instructions,
                subject=q.subject,
                topic=q.topic
            ) for q in questions
        ]
    )

# Question endpoints
@app.post("/create-question", response_model=QuestionResponse)
async def create_question(question: QuestionBase, db: Session = Depends(get_db)):
    db_question = Question(
        public_question=question.public_question,
        hidden_values=question.hidden_values,
        answer=question.answer,
        teacher_instructions=question.teacher_instructions,
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
        teacher_instructions=db_question.teacher_instructions,
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
        teacher_instructions=db_question.teacher_instructions,
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
                teacher_instructions=q.teacher_instructions,
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