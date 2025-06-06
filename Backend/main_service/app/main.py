from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form, Request
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Any, Optional
import httpx
import os
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
from .conversation_service import ConversationService
from dotenv import load_dotenv
import json
import requests

load_dotenv()

# Service URLs from environment variables
DATABASE_SERVICE_URL = os.getenv("DATABASE_SERVICE_URL", "http://database-service:8001")
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://vector-service:8002")
LLM_SERVICE_URL = os.getenv("LLM_SERVICE_URL", "http://llm-service:8003")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

app = FastAPI(title="Socratic Main Service")

# Update CORS middleware to support both local development and containerized environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React frontend in local development
        "http://localhost:80",    # Frontend in containerized environment
        "http://localhost",       # Frontend in containerized environment (default port 80)
        "http://frontend:80",     # Frontend service name in Docker network
        "http://frontend",
        "http://frontend-production-3661.up.railway.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication schema models
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    grade: Optional[str] = None

class TeacherCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    subject: Optional[str] = None
    school: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshToken(BaseModel):
    refresh_token: str

class ChatRequest(BaseModel):
    problem_id: int
    query: str

class ChatResponse(BaseModel):
    response: str

class ChatQuery(BaseModel):
    test_id: int
    test_code: str
    question_id: int
    public_question: str
    query: str
    user_id: int
    isPracticeExam: bool = False  # Flag to distinguish between test and practice exam queries

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
    isPracticeExam: bool = False
    questions: List[Question]

class TestResponse(BaseModel): # questions now contain 'id' field as well
    id: int
    test_name: str
    code: str
    isPracticeExam: bool = False
    questions: List[Dict[str, Any]]

class AnswerSubmission(BaseModel):
    user_id: int
    test_code: str
    question_id: int
    question_index: int
    answer: str

class TestFinishRequest(BaseModel):
    user_id: str
    test_id: Optional[int] = None
    test_code: str

class TestSessionStart(BaseModel):
    user_id: int
    test_id: int
    test_code: str
    question_ids: List[int]
    total_questions: int

# Initialize services
convo_service = ConversationService(
    llm_service_url=LLM_SERVICE_URL,
    database_service_url=DATABASE_SERVICE_URL,
    redis_url=REDIS_URL
)

# Authentication endpoints
@app.post("/api/auth/student/register")
async def register_student(student: StudentCreate):
    """Register a new student through the API Gateway pattern."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DATABASE_SERVICE_URL}/auth/student/register",
                json=student.model_dump()
            )
            response.raise_for_status()  # Raise exception for HTTP error responses
            return response.json()
        except httpx.HTTPStatusError as e:
            # Forward the exact error from the database service
            error_detail = e.response.json().get("detail", str(e))
            status_code = e.response.status_code
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@app.post("/api/auth/teacher/register")
async def register_teacher(teacher: TeacherCreate):
    """Register a new teacher through the API Gateway pattern."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DATABASE_SERVICE_URL}/auth/teacher/register",
                json=teacher.model_dump()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            status_code = e.response.status_code
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration error: {str(e)}")

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(login_data: UserLogin):
    """Login through the API Gateway pattern."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DATABASE_SERVICE_URL}/auth/login",
                json=login_data.model_dump()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            status_code = e.response.status_code
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")

@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(refresh: RefreshToken):
    """Refresh authentication token through the API Gateway pattern."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{DATABASE_SERVICE_URL}/auth/refresh",
                json=refresh.model_dump()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            status_code = e.response.status_code
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")

@app.get("/api/auth/student/me")
async def get_student_profile(request: Request):
    """Get student profile through the API Gateway pattern."""
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DATABASE_SERVICE_URL}/auth/student/me",
                headers={"Authorization": authorization}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            status_code = e.response.status_code
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Profile error: {str(e)}")

@app.get("/api/auth/teacher/me")
async def get_teacher_profile(request: Request):
    """Get teacher profile through the API Gateway pattern."""
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header is required")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{DATABASE_SERVICE_URL}/auth/teacher/me",
                headers={"Authorization": authorization}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json().get("detail", str(e))
            status_code = e.response.status_code
            raise HTTPException(status_code=status_code, detail=error_detail)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Profile error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/chat")
async def chat(query: ChatQuery):
    """Process a chat query"""
    print("chat query recieved in the backend", query)
    try:
        response = await convo_service.process_query(
            query.query, 
            query.user_id, 
            query.test_code, 
            query.question_id,
            query.public_question,
            query.test_id,
            query.isPracticeExam
        )
        print("main service response\n:", response)
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
            test_base = {
                "test_name": test.name,
                "code": test.code,
                "isPracticeExam": test.isPracticeExam
            }
            
            test_response = await client.post(
                f"{DATABASE_SERVICE_URL}/tests",
                json=test_base
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
        
@app.post("/submit-answer")
async def submit_answer(submission: AnswerSubmission):
    """Submit an answer for a question."""
    try:
        # Call the conversation service to submit the answer
        result = await convo_service.submit_answer(
            user_id=submission.user_id, 
            test_code=submission.test_code, 
            question_id=submission.question_id, 
            question_index=submission.question_index, 
            answer=submission.answer
        )
        
        # Return the result to the frontend
        response_data = {
            "is_correct": result["is_correct"],
            "progress": result["progress"]
        }
        
        return response_data
    except Exception as e:
        print(f"Error submitting answer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/finish-test")
async def finish_test(request: TestFinishRequest):
    """Complete a test and store results in the database."""
    try:
        # Log the incoming request data
        print(f"Finishing test for user: {request.user_id}, test_code: {request.test_code}")
        
        # Get test ID from test code if not provided
        if not request.test_id:
            async with httpx.AsyncClient() as client:
                test_response = await client.get(f"{DATABASE_SERVICE_URL}/tests/by-code/{request.test_code}")
                test_response.raise_for_status()
                test_data = test_response.json()
                test_id = test_data["id"]
        else:
            test_id = request.test_id
            
        print(f"Using test_id: {test_id} for test_code: {request.test_code}")
        
        # Call the conversation service to finish the test
        result = await convo_service.finish_test(
            user_id=request.user_id,
            test_id=str(test_id),
            request_data={"test_code": request.test_code}
        )
        
        if isinstance(result, dict) and "error" in result:
            print(f"Error finishing test: {result['error']}")
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Ensure the result has all required fields
        response_data = {
            "test_id": test_id,
            "id": result.get("id"),
            "score": result.get("score", 0),
            "correct_answers": result.get("correct_questions", 0),
            "total_questions": result.get("total_questions", 0),
            "total_time": result.get("time_spent", 0),
            "start_time": result.get("start_time"),
            "end_time": result.get("end_time")
        }
        
        print(f"Returning test results: {response_data}")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error finishing test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tests/{code}", response_model=TestResponse)
async def get_test(code: str, user_id: Optional[str] = None):
    """Get a test by its code and initialize a test session if user_id is provided."""
    async with httpx.AsyncClient() as client:
        try:
            # Get test from database - now includes questions
            test_response = await client.get(f"{DATABASE_SERVICE_URL}/tests/by-code/{code}")
            test_response.raise_for_status()
            test = test_response.json()
            
            if not test:
                raise HTTPException(status_code=404, detail="Test not found")
            
            # Initialize test session in Redis if user_id is provided
            if user_id:
                try:
                    # Extract question IDs
                    question_ids = [q["id"] for q in test["questions"]]
                    
                    # Log the initialization attempt
                    print(f"Starting test session for user_id: {user_id}, test_id: {test['id']}, with {len(question_ids)} questions")
                    
                    # Start test session
                    await convo_service.start_test(
                        user_id=user_id,
                        test_id=test["id"],
                        test_code=code,
                        list_question_ids=question_ids,
                        total_questions=len(question_ids)
                    )
                    print(f"Test session initialized successfully")
                except Exception as e:
                    print(f"Error initializing test session: {str(e)}")
                    # Continue even if session initialization fails - the test can still be rendered
            
            return test
            
        except httpx.HTTPException as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Service error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/tests/{code}/questions/{index}")
async def get_question(code: str, index: int):
    """Get a question from a test."""
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

@app.post("/start-test")
async def start_test(request: TestSessionStart):
    """Initialize a new test session in Redis."""
    try:
        result = await convo_service.start_test(
            request.user_id,
            request.test_id,
            request.test_code,
            request.question_ids
        )
        # Add total questions to test data
        result["total_questions"] = request.total_questions
        
        # Update Redis with the modified test data
        test_key = convo_service._get_test_key(request.user_id, request.test_id)
        convo_service.redis.setex(test_key, 24 * 60 * 60, json.dumps(result))
        
        return result
    except Exception as e:
        print(f"Error starting test: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  
