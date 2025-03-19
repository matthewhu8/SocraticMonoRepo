from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from .conversation_service import ConversationService
from dotenv import load_dotenv
import json

load_dotenv()

# Service URLs from environment variables
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://localhost:8001")
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8002")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://localhost:8003")

app = FastAPI(title="Socratic Main Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    problem_id: int
    query: str

class ChatResponse(BaseModel):
    response: str

class ChatQuery(BaseModel):
    problem_id: int
    query: str
    test_code: Optional[str] = None
    question_index: Optional[int] = None
    user_id: Optional[str] = "anonymous"

class TeachingMaterial(BaseModel):
    topic: str
    subject: str
    source: str    
    content: str


class TestData(BaseModel):
    name: str
    code: str
    questions: List[Dict[str, Any]]

class Question(BaseModel):
    public_question: str
    hidden_values: Optional[Dict[str, Any]] = {}
    answer: str
    formula: Optional[str] = None
    teacher_instructions: Optional[str] = None
    hint_level: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None

class TestCreate(BaseModel):
    name: str
    code: str
    questions: List[Question]

class TestResponse(BaseModel):
    id: int
    test_name: str
    code: str
    questions: List[Dict[str, Any]]

# Initialize services
convo_service = ConversationService(
    llm_service_url=LLM_SERVICE_URL,
    database_service_url=DATABASE_SERVICE_URL
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/chat")
async def chat(query: ChatQuery):
    """Process a chat query"""
    try:
        response = await convo_service.process_query(
            query.query, 
            query.problem_id, 
            query.user_id, 
            query.test_code, 
            query.question_index
        )
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/store-teaching-material")
async def store_teaching_material(teaching_material: TeachingMaterial):
    """Store a teaching material in the vector database."""
    async with httpx.AsyncClient() as client:
        try:
            await client.post(
                f"{VECTOR_SERVICE_URL}/store_teaching_material",
                json={
                    "topic": teaching_material.topic,
                    "subject": teaching_material.subject,
                    "source": teaching_material.source,
                    "content": teaching_material.content
                }
            )
            return {"message": "Teaching material stored successfully"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/tests", response_model=TestResponse)
async def create_test(test: TestCreate):
    """Create a new test with questions and store embeddings."""
    print("hello world")
    print(test)
    async with httpx.AsyncClient() as client:
        try:
            # 1. Create test in database
            test_response = await client.post(
                f"{DATABASE_SERVICE_URL}/tests",
                json={"test_name": test.name, "code": test.code}
            )
            test_response.raise_for_status()
            test_data = test_response.json()
            test_id = test_data["id"]
            
            # 2. Create questions and store embeddings
            questions = []
            for idx, question in enumerate(test.questions):
                # Create question in database
                print("storing a test question in database", question.public_question)
                question_response = await client.post(
                    f"{DATABASE_SERVICE_URL}/create-question",
                    json={
                        "public_question": question.public_question,
                        "hidden_values": question.hidden_values,
                        "answer": question.answer,
                        "formula": question.formula,
                        "teacher_instructions": question.teacher_instructions,
                        "hint_level": question.hint_level,
                        "subject": question.subject,
                        "topic": question.topic
                    }
                )
                question_response.raise_for_status()
                question_data = question_response.json()
                question_id = question_data["id"]
                
                # Create test-question relationship
                print("storing a test-question relationship in database", test_id, question_id)
                await client.post(
                    f"{DATABASE_SERVICE_URL}/test-questions",
                    json={
                        "test_id": test_id,
                        "question_id": question_id,
                        "position": idx
                    }
                )
                
                # Store entire problem in vector service
                print("storing an entire problem in vector service", question.public_question)
                await client.post(
                    f"{VECTOR_SERVICE_URL}/problems/",
                    json={
                        "problem_id": f"{test_id}_{question_id}",
                        "public_question": question.public_question,
                        "metadata": {
                            "test_code": test.code,
                            "question_id": question_id,
                            "answer": question.answer,
                            "subject": question.subject,
                            "topic": question.topic,
                            "hidden_values": question.hidden_values
                        }
                    }
                )

                # store individual hidden values in vector service
                for hidden_value in question.hidden_values:
                    print("storing one hidden value in vector service as a document", hidden_value, question.hidden_values[hidden_value])
                    await client.post(
                        f"{VECTOR_SERVICE_URL}/store_hidden_value",
                        json={
                            "problem_id": f"{test_id}_{question_id}",
                            "hidden_value": f"{hidden_value} = {question.hidden_values[hidden_value]}"
                        }
                    )
                
                questions.append(question_data)
            
            # 3. Get complete test with questions
            complete_test = await client.get(
                f"{DATABASE_SERVICE_URL}/tests/{test_id}"
            )
            complete_test.raise_for_status()
            test_data = complete_test.json()
            
            # Add questions to response
            test_data["questions"] = questions
            
            return test_data
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/tests/{code}", response_model=TestResponse)
async def get_test(code: str):
    """Get a test by its code."""
    async with httpx.AsyncClient() as client:
        try:
            # Get test from database - now includes questions
            test_response = await client.get(f"{DATABASE_SERVICE_URL}/tests/by-code/{code}")
            test_response.raise_for_status()
            test = test_response.json()
            
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")
        
            
            return test
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/tests/{code}/questions/{index}")
async def get_question(code: str, index: int):
    """Get a specific question from a test."""
    async with httpx.AsyncClient() as client:
        try:
            # Get test with questions already included
            test_response = await client.get(f"{DATABASE_SERVICE_URL}/tests/by-code/{code}")
            test_response.raise_for_status()
            test = test_response.json()
            
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")
            
            # Get questions from the test response
            questions = test["questions"]
            
            # Get specific question
            if index < 0 or index >= len(questions):
                raise HTTPException(status_code=404, detail="Question not found")
            
            return questions[index]
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.post("/similar-questions")
async def find_similar_questions(query: str, n_results: int = 5):
    """Find similar questions using vector similarity search."""
    async with httpx.AsyncClient() as client:
        try:
            # Search vector service
            search_response = await client.post(
                f"{VECTOR_SERVICE_URL}/search",
                json={"query": query, "n_results": n_results}
            )
            search_response.raise_for_status()
            results = search_response.json()
            
            # Get full question details from database
            detailed_results = []
            for result in results:
                question_id = result["metadata"]["question_id"]
                question_response = await client.get(
                    f"{DATABASE_SERVICE_URL}/questions/{question_id}"
                )
                question_response.raise_for_status()
                question_data = question_response.json()
                
                detailed_results.append({
                    **question_data,
                    "similarity_score": 1 - result["distance"]  # Convert distance to similarity
                })
            
            return detailed_results
            
        except httpx.HTTPError as e:
            raise HTTPException(status_code=500, detail=f"Service error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 