from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from .database.database import get_db
from .database.models import Test, Question, TestQuestion, TestResult, QuestionResult, ChatMessage
from .database.queries import (
    create_test as db_create_test,
    get_test_by_code as db_get_test,
    create_chat_message as db_create_chat_message,
    create_question_result as db_create_question_result,
    update_question_result as db_update_question_result
)
import sqlite3

app = FastAPI(title="Database Service")

# Database connection
def get_db():
    conn = sqlite3.connect('socratic.db')
    conn.row_factory = sqlite3.Row
    return conn

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

class QuestionCreate(QuestionBase):
    pass

class TestQuestionCreate(BaseModel):
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

# Response models
class ChatMessage(ChatMessageBase):
    id: int
    question_result_id: int

    class Config:
        from_attributes = True

class QuestionResult(QuestionResultBase):
    id: int
    test_result_id: int
    chat_messages: List[ChatMessage] = []

    class Config:
        from_attributes = True

class TestResult(TestResultBase):
    id: int
    start_time: datetime
    question_results: List[QuestionResult] = []

    class Config:
        from_attributes = True

class Question(QuestionBase):
    id: int
    tests: List[Test] = []

    class Config:
        from_attributes = True

class Test(TestBase):
    id: int
    questions: List[Question] = []

    class Config:
        from_attributes = True

# Test endpoints
@app.post("/tests")
async def create_test(test: Test):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tests (test_name, code, created_at) VALUES (?, ?, ?)",
            (test.test_name, test.code, datetime.now())
        )
        conn.commit()
        test_id = cursor.lastrowid
        return {"id": test_id, "test_name": test.test_name, "code": test.code}
    finally:
        conn.close()

@app.get("/tests/{test_id}")
async def get_test(test_id: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tests WHERE id = ?", (test_id,))
        test = cursor.fetchone()
        if not test:
            raise HTTPException(status_code=404, detail="Test not found")
        return dict(test)
    finally:
        conn.close()

@app.get("/tests")
async def list_tests():
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tests")
        tests = cursor.fetchall()
        return [dict(test) for test in tests]
    finally:
        conn.close()

# Question endpoints
@app.post("/questions")
async def create_question(question: Question):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO questions 
            (public_question, hidden_values, answer, teacher_instructions, subject, topic)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                question.public_question,
                str(question.hidden_values),
                question.answer,
                question.teacher_instructions,
                question.subject,
                question.topic
            )
        )
        conn.commit()
        question_id = cursor.lastrowid
        return {"id": question_id, **question.dict()}
    finally:
        conn.close()

@app.get("/questions/{question_id}")
async def get_question(question_id: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        question = cursor.fetchone()
        if not question:
            raise HTTPException(status_code=404, detail="Question not found")
        return dict(question)
    finally:
        conn.close()

# Test-Question relationship endpoints
@app.post("/test-questions")
async def create_test_question(test_question: TestQuestion):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO test_questions (test_id, question_id, position) VALUES (?, ?, ?)",
            (test_question.test_id, test_question.question_id, test_question.position)
        )
        conn.commit()
        return {"test_id": test_question.test_id, "question_id": test_question.question_id}
    finally:
        conn.close()

@app.get("/test-questions")
async def get_test_questions(test_id: Optional[int] = None):
    conn = get_db()
    try:
        cursor = conn.cursor()
        if test_id:
            cursor.execute(
                """
                SELECT q.* FROM questions q
                JOIN test_questions tq ON q.id = tq.question_id
                WHERE tq.test_id = ?
                ORDER BY tq.position
                """,
                (test_id,)
            )
        else:
            cursor.execute("SELECT * FROM test_questions")
        results = cursor.fetchall()
        return [dict(row) for row in results]
    finally:
        conn.close()

@app.delete("/test-questions/{test_id}/{question_id}")
async def delete_test_question(test_id: int, question_id: int):
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM test_questions WHERE test_id = ? AND question_id = ?",
            (test_id, question_id)
        )
        conn.commit()
        return {"message": "Test-question relationship deleted"}
    finally:
        conn.close()

@app.post("/test-results/", response_model=TestResult)
async def create_test_result(result: TestResultBase, db: Session = Depends(get_db)):
    db_result = TestResult(**result.dict())
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result

@app.post("/test-results/{result_id}/questions/", response_model=QuestionResult)
async def add_question_result(
    result_id: int,
    question_result: QuestionResultBase,
    db: Session = Depends(get_db)
):
    try:
        return db_create_question_result(
            db,
            result_id,
            question_result.question_id,
            question_result.student_answer,
            question_result.isCorrect,
            question_result.time_spent
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/question-results/{result_id}/messages/", response_model=ChatMessage)
async def add_chat_message(
    result_id: int,
    message: ChatMessageBase,
    db: Session = Depends(get_db)
):
    try:
        return db_create_chat_message(
            db,
            result_id,
            message.sender,
            message.content
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001) 