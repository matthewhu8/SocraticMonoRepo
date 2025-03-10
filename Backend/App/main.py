from fastapi import FastAPI, HTTPException, Depends 
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session  # Add this import
from .Modules.Conversation.conversation_service import ConversationService
from .Modules.Conversation.llm_client import call_llm
from .Modules.Problem.problem_service import ProblemService
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime


# Import database session dependency and Test model
from Database.session import engine, SessionLocal
from Database.models import Base
import json
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get a DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ChatRequest(BaseModel):
    problem_id: int
    query: str

class ChatResponse(BaseModel):
    response: str

convo_service = ConversationService(call_llm=call_llm)
problem_service = ProblemService()

class ChatQuery(BaseModel):
    problem_id: int
    query: str
    test_code: Optional[str] = None
    question_index: Optional[int] = None
    user_id: Optional[str] = "anonymous"

import os
from sqlalchemy import inspect


@app.post("/chat")
def chat(query: ChatQuery):
    print("chat endpoint called")
    try:
        response = convo_service.process_query(
            query.query, 
            query.problem_id, 
            query.user_id, 
            query.test_code, 
            query.question_index
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TestData(BaseModel):
    name: str
    code: str
    questions: List[Dict[str, Any]]


@app.post("/tests")
def store_test(test_data: TestData, db: Session = Depends(get_db)):  # Use Session instead of SessionLocal
    # Check required fields
    if not test_data.code or not test_data.questions:
        print("No code or questions provided")
        print("Test data", test_data)
        raise HTTPException(status_code=400, detail="Test code and questions are required.")
    
    try:
        result = problem_service.create_test(db, test_data.name, test_data.code, test_data.questions)
        return {"message": "Test created", "test": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tests/{code}")
def get_test(code: str, db: Session = Depends(get_db)): 
    print("retrieve test endpoint called", db)
    test = problem_service.get_test_by_code(db, code)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    return test

@app.get("/chat/history")
def chat_history(problem_id: int):
    return {"history": "Coming soon!"}

@app.get("/chat/settings")
def chat_settings(problem_id: int):
    return {"settings": "Coming soon!"}