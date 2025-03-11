import httpx
from typing import List, Dict, Any, Optional

class ProblemService:
    def __init__(self, database_service_url: str, vector_service_url: str):
        """Initialize the ProblemService with service URLs."""
        self.database_service_url = database_service_url
        self.vector_service_url = vector_service_url
        
    async def create_test(self, name: str, code: str, questions: List[Dict[str, Any]]) -> Dict:
        """Create a new test with the given code and questions."""
        async with httpx.AsyncClient() as client:
            # Create test in database service
            db_response = await client.post(
                f"{self.database_service_url}/tests/",
                json={
                    "test_name": name,
                    "code": code,
                    "questions": questions
                }
            )
            
            if db_response.status_code != 200:
                raise ValueError(f"Failed to create test in database: {db_response.text}")
            
            test_data = db_response.json()
            
            # Store questions in vector service for similarity search
            for idx, question in enumerate(questions):
                vector_response = await client.post(
                    f"{self.vector_service_url}/problems/",
                    json={
                        "id": f"{code}_{idx}",
                        "text": question["public_question"],
                        "metadata": {
                            "test_code": code,
                            "question_id": idx,
                            "answer": question["answer"],
                            "hidden_values": question.get("hidden_values", {}),
                            "teacher_instructions": question.get("teacher_instructions"),
                            "subject": question.get("subject"),
                            "topic": question.get("topic")
                        }
                    }
                )
                
                if vector_response.status_code != 200:
                    # Log error but continue - vector storage is not critical
                    print(f"Warning: Failed to store question in vector service: {vector_response.text}")
            
            return test_data
    
    async def get_test_by_code(self, code: str) -> Optional[Dict]:
        """Retrieve a test by its code."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.database_service_url}/tests/{code}")
            if response.status_code == 404:
                return None
            elif response.status_code != 200:
                raise ValueError(f"Failed to retrieve test: {response.text}")
            
            return response.json()
    
    async def get_test_question(self, test_code: str, question_index: int) -> Optional[Dict]:
        """Get a specific question from a test."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.database_service_url}/tests/{test_code}/questions/{question_index}"
            )
            if response.status_code == 404:
                return None
            elif response.status_code != 200:
                raise ValueError(f"Failed to retrieve question: {response.text}")
            
            return response.json()
    
    async def get_similar_questions(self, test_code: str, question_id: int, limit: int = 5) -> List[Dict]:
        """Find questions similar to the given question."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.vector_service_url}/problems/{test_code}_{question_id}/similar",
                params={"limit": limit}
            )
            if response.status_code != 200:
                raise ValueError(f"Failed to find similar questions: {response.text}")
            
            return response.json().get("results", []) 