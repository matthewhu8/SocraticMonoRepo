import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC
import json
from redis import Redis

class ConversationService:
    def __init__(
        self,
        llm_service_url: str,
        database_service_url: str,
        redis_url: str = "redis://localhost:6379"
    ):
        """Initialize the ConversationService with service URLs and Redis connection."""
        self.llm_service_url = llm_service_url
        self.database_service_url = database_service_url
        self.redis = Redis.from_url(redis_url, decode_responses=True)
    
    def _get_session_key(self, user_id: str, test_id: int, question_id: int) -> str:
        """Generate Redis key for a specific test session."""
        return f"test_session:{user_id}:{test_id}:{question_id}"
    
    def _get_test_key(self, user_id: str, test_code: str) -> str:
        """Generate Redis key for overall test data."""
        return f"test:{user_id}:{test_code}" 
    
    async def start_test(self, user_id: str, test_code: str, total_questions: int) -> Dict:
        """Initialize a new test session."""
        test_key = self._get_test_key(user_id, test_code)
        test_data = {
            "user_id": user_id,
            "test_code": test_code,
            "status": "in_progress",
            "start_time": datetime.now(UTC).isoformat(),
            "total_questions": total_questions,
            "current_question": 0,
            "completed_questions": [],
            "total_time": 0
        }
        
        # Store test data with 24 hour expiry
        self.redis.setex(test_key, 24 * 60 * 60, json.dumps(test_data))
        return test_data
    
    async def process_query(
        self, 
        query: str, 
        user_id: str,
        test_code: str,
        question_id: int,
        test_id: int
    ) -> str:
        """Process a user query and return a response."""
        print("processing query", query, "for user", user_id, "test", test_id, "question", question_id, "test code", test_code)
        session_key = self._get_session_key(user_id, test_id, question_id)
        # test_key = self._get_test_key(user_id, test_code)
        print("session key", session_key)
        # Get or initialize question session
        session_data = self.redis.get(session_key)
        print("session data", session_data)

        if not session_data:
            print("no session data found, initializing new session")
            session_data = json.dumps({
                "chat_history": [],
                "start_time": datetime.now(UTC).isoformat(),
                "hints_used": 0,
                "student_answer": None,
                "is_correct": False,
                "question_id": question_id,
                "test_id": test_id
            })
        
        session_data = json.loads(session_data)
                
        # Add user message to chat history
        print("adding user message to chat history")
        session_data["chat_history"].append({
            "role": "user",
            "content": query,
            "timestamp": datetime.now(UTC).isoformat()
        })
        # Get LLM response
        print("making request to llm service")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.llm_service_url}/generate",
                json={
                    "query": query,
                    "context": {
                        "test_code": test_code,
                        "test_id": test_id,
                        "question_id": question_id,
                        "user_id": user_id,
                        "conversation_history": session_data["chat_history"]
                    }
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get response from LLM service: {response.text}")
            
            llm_response = response.json().get("response", "I'm sorry, I couldn't process your request.")
        
        # Add assistant response to chat history
        session_data["chat_history"].append({
            "role": "assistant",
            "content": llm_response,
            "timestamp": datetime.now(UTC).isoformat()
        })
        
        # Increment hints used if this was a hint request
        if "hint" in query.lower():
            session_data["hints_used"] += 1
        
        # Update Redis with session data (24 hour expiry)
        self.redis.setex(session_key, 24 * 60 * 60, json.dumps(session_data))
        
        return llm_response
    
    async def submit_answer(
        self,
        user_id: str,
        test_code: str,
        question_index: int,
        answer: str
    ) -> Dict:
        """Submit an answer for a question."""
        session_key = self._get_session_key(user_id, test_code, question_index)
        test_key = self._get_test_key(user_id, test_code)
        
        # Get session data
        session_data = json.loads(self.redis.get(session_key) or "{}")
        test_data = json.loads(self.redis.get(test_key) or "{}")
        
        if not session_data or not test_data:
            raise ValueError("No active test session found")
        
        # Update session data
        session_data["student_answer"] = answer
        session_data["end_time"] = datetime.now(UTC).isoformat()
        session_data["time_spent"] = (
            datetime.fromisoformat(session_data["end_time"]) -
            datetime.fromisoformat(session_data["start_time"])
        ).total_seconds()
        
        # TODO: Implement answer checking logic
        session_data["is_correct"] = True  # Placeholder
        
        # Update test data
        if question_index not in test_data["completed_questions"]:
            test_data["completed_questions"].append(question_index)
        test_data["current_question"] = question_index + 1
        
        # Store updated data
        self.redis.setex(session_key, 24 * 60 * 60, json.dumps(session_data))
        self.redis.setex(test_key, 24 * 60 * 60, json.dumps(test_data))
        
        return session_data
    
    async def finish_test(self, user_id: str, test_code: str) -> Dict:
        """Complete a test and prepare data for database storage."""
        test_key = self._get_test_key(user_id, test_code)
        test_data = json.loads(self.redis.get(test_key) or "{}")
        
        if not test_data:
            raise ValueError("No active test session found")
        
        # Calculate final results
        all_questions = []
        total_time = 0
        correct_answers = 0
        
        for q_index in range(test_data["total_questions"]):
            session_key = self._get_session_key(user_id, test_code, q_index)
            q_data = json.loads(self.redis.get(session_key) or "{}")
            
            if q_data:
                all_questions.append(q_data)
                total_time += q_data.get("time_spent", 0)
                if q_data.get("is_correct"):
                    correct_answers += 1
        
        # Prepare final test result
        final_result = {
            "user_id": user_id,
            "test_code": test_code,
            "start_time": test_data["start_time"],
            "end_time": datetime.now(UTC).isoformat(),
            "total_time": total_time,
            "total_questions": test_data["total_questions"],
            "correct_answers": correct_answers,
            "score": (correct_answers / test_data["total_questions"]) * 100,
            "questions": all_questions
        }
        
        # Store in database
        async with httpx.AsyncClient() as client:
            # Create test result
            test_result_response = await client.post(
                f"{self.database_service_url}/test-results",
                json={
                    "test_code": test_code,
                    "username": user_id,
                    "score": final_result["score"],
                    "total_questions": final_result["total_questions"],
                    "correct_questions": final_result["correct_answers"],
                    "start_time": final_result["start_time"],
                    "end_time": final_result["end_time"]
                }
            )
            test_result_response.raise_for_status()
            test_result_data = test_result_response.json()
            test_result_id = test_result_data["id"]
            
            # Store each question result
            for question in all_questions:
                # Create question result
                question_result_response = await client.post(
                    f"{self.database_service_url}/question-results",
                    json={
                        "test_result_id": test_result_id,
                        "question_id": question["problem_id"],
                        "student_answer": question["student_answer"],
                        "isCorrect": question["is_correct"],
                        "time_spent": question["time_spent"],
                        "start_time": question["start_time"],
                        "end_time": question["end_time"]
                    }
                )
                question_result_response.raise_for_status()
                question_result_data = question_result_response.json()
                
                # Store chat messages
                for message in question["chat_history"]:
                    await client.post(
                        f"{self.database_service_url}/chat-messages",
                        json={
                            "question_result_id": question_result_data["id"],
                            "sender": message["role"],  # 'user' or 'assistant'
                            "content": message["content"],
                            "timestamp": message["timestamp"]
                        }
                    )
        
        # Clean up Redis
        for q_index in range(test_data["total_questions"]):
            self.redis.delete(self._get_session_key(user_id, test_code, q_index))
        self.redis.delete(test_key)
        
        return final_result
    
    def get_conversation_history(
        self,
        user_id: str,
        test_code: str,
        question_index: int
    ) -> List[Dict]:
        """Get the conversation history for a specific question."""
        session_key = self._get_session_key(user_id, test_code, question_index)
        session_data = json.loads(self.redis.get(session_key) or "{}")
        return session_data.get("chat_history", []) 