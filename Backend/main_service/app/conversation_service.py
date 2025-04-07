import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, UTC
import json
from redis import Redis
import traceback
import asyncio
import requests

class ConversationService:
    def __init__(
        self,
        llm_service_url: str,
        database_service_url: str,
        redis_url: str = "redis://redis:6379"
    ):
        """Initialize the ConversationService with service URLs and Redis connection."""
        self.llm_service_url = llm_service_url
        self.database_service_url = database_service_url
        self.redis = Redis.from_url(redis_url, decode_responses=True)
    
    def _get_session_key(self, user_id: str, test_id: str, question_id: str) -> str:
        """Generate Redis key for a specific test session."""
        return f"test_session:{user_id}:{test_id}:{question_id}"
    
    def _get_test_key(self, user_id: str, test_id: str) -> str:
        """Generate Redis key for overall test data."""
        return f"test:{user_id}:{test_id}" 
    
    def _ensure_timestamp(self, timestamp_value) -> str:
        """Ensure a timestamp is in ISO format string."""
        if timestamp_value is None:
            return datetime.now(UTC).isoformat()
            
        if isinstance(timestamp_value, str):
            try:
                # Validate it's a proper ISO timestamp
                datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                return timestamp_value
            except ValueError:
                # If not valid, return current time
                print(f"Warning: Invalid timestamp format: {timestamp_value}")
                return datetime.now(UTC).isoformat()
        elif isinstance(timestamp_value, datetime):
            # If it's already a datetime object, just format it
            return timestamp_value.isoformat()
            
        # If it's not a string, datetime, or None, return current time
        print(f"Warning: Invalid timestamp type: {type(timestamp_value)}")
        return datetime.now(UTC).isoformat()
    
    async def start_test(self, user_id: int, test_id: int, test_code: str, list_question_ids: List[int], total_questions: int) -> Dict:
        """Initialize a new test session."""
        # Convert parameters to strings for consistent Redis keys
        user_id_str = str(user_id)
        test_id_str = str(test_id)
        
        # Create session key
        session_key = f"test:{user_id_str}:{test_id_str}"
        
        # Convert question IDs to strings since the database stores them as integers
        str_question_ids = [str(qid) for qid in list_question_ids]
            
        # Timestamp for session creation
        start_timestamp = self._ensure_timestamp(datetime.now(UTC).isoformat())
            
        test_data = {
            "user_id": user_id_str,
            "test_id": test_id_str,
            "test_code": test_code,
            "status": "in_progress",
            "start_time": start_timestamp,
            "list_question_ids": str_question_ids,
            "completed_questions": [],
            "total_questions": total_questions,
            "total_time": 0
        }
    
        print(f"Initializing test session for user {user_id_str}, test {test_id_str} with {len(str_question_ids)} questions")
        
        # Initialize session data for each question
        for question_id in str_question_ids:
            session_key_q = self._get_session_key(user_id_str, test_id_str, question_id)
            if not self.redis.exists(session_key_q):
                session_data = {
                    "chat_history": [],
                    "start_time": start_timestamp,
                    "end_time": None,
                    "hints_used": 0,
                    "student_answer": None,
                    "is_correct": False,
                    "question_id": question_id,
                    "test_id": test_id_str,
                    "time_spent": 0
                }
                self.redis.setex(session_key_q, 2 * 60 * 60, json.dumps(session_data))
        
        # Store test data with 24 hour expiry
        self.redis.setex(session_key, 2 * 60 * 60, json.dumps(test_data))
        return test_data
    
    async def process_query(
        self, 
        query: str, 
        user_id: int,
        test_code: str,
        question_id: int,
        public_question: str,
        test_id: int,
        is_practice_exam: bool = False
    ) -> str:
        """Process a user query and return a response."""
        session_key = self._get_session_key(str(user_id), str(test_id), str(question_id))
        test_key = self._get_test_key(str(user_id), str(test_id))
        
        # Get session data
        session_data = self.redis.get(session_key)
        test_data = self.redis.get(test_key)

        # If no session data exists, try to initialize from overall test data
        if not session_data:
            if not test_data:
                # No test session either, initialize a new session
                print("no session data found, initializing new session")
                session_data = json.dumps({
                    "chat_history": [],
                    "start_time": self._ensure_timestamp(datetime.now(UTC).isoformat()),
                    "hints_used": 0,
                    "student_answer": None,
                    "is_correct": False,
                    "question_id": question_id,
                    "test_id": test_id
                })
            else:
                # Initialize from test data
                test_data_obj = json.loads(test_data)
                if question_id not in test_data_obj.get("list_question_ids", []):
                    test_data_obj["list_question_ids"].append(question_id)
                    self.redis.setex(test_key, 24 * 60 * 60, json.dumps(test_data_obj))
                
                # Create new session for this question
                session_data = json.dumps({
                    "chat_history": [],
                    "start_time": self._ensure_timestamp(datetime.now(UTC).isoformat()),
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
            "timestamp": self._ensure_timestamp(datetime.now(UTC).isoformat())
        })
        print("\nchat history:", session_data["chat_history"])
        print()
        
        # Get LLM response
        print("making request to llm service")
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            try:
                response = await client.post(
                    f"{self.llm_service_url}/generate",
                    json={
                        "query": query,
                        "context": {
                            "test_code": test_code,
                            "test_id": test_id,
                            "question_id": question_id,
                            "user_id": user_id,
                            "conversation_history": (
                                session_data["chat_history"][-4:]
                                if len(session_data["chat_history"]) > 4
                                else session_data["chat_history"]
                            ),
                            "public_question": public_question,
                            "isPracticeExam": is_practice_exam
                        }
                    }
                )
                response.raise_for_status()  
                print("Request succeeded:", response.status_code)
            except Exception as e:
                print(f"Error in get_llm_response: {e}")
                traceback.print_exc()
                raise
            if response.status_code != 200:
                print(f"Failed to get response from LLM service: {response.text}")
                raise ValueError(f"Failed to get response from LLM service: {response.text}")
            
        llm_response = response.json().get("response", "I'm sorry, I couldn't process your request.")
        session_data["chat_history"].append({
            "role": "assistant",
            "content": llm_response,
            "isHiddenValueResponse": response.json().get("isHiddenValueResponse", False),
            "timestamp": self._ensure_timestamp(datetime.now(UTC).isoformat())
        })
        
        # Increment hints used if this was a hint request
        if "hint" in query.lower():
            session_data["hints_used"] += 1
        
        # Update Redis with session data (24 hour expiry)
        self.redis.setex(session_key, 24 * 60 * 60, json.dumps(session_data))
        
        return llm_response
    
    async def submit_answer(
        self,
        user_id: int,
        test_code: str,
        question_id: int,
        question_index: int,
        answer: str
    ) -> Dict:
        """Submit an answer for a question."""
        async with httpx.AsyncClient() as client:
            try:
                # Convert IDs to strings for consistent handling
                user_id_str = str(user_id)
                question_id_str = str(question_id)
                
                # Get the actual question to verify the answer
                question_response = await client.get(
                    f"{self.database_service_url}/questions/{question_id}"
                )
                question_response.raise_for_status()
                question_data = question_response.json()
                correct_answer = question_data.get("answer", "").strip()
                
                # Test if answer is correct (simple string comparison for now)
                # In a production system, you'd want more sophisticated answer validation
                is_correct = answer.strip() == correct_answer
                
                # Get test_id from test_code
                test_response = await client.get(
                    f"{self.database_service_url}/tests/by-code/{test_code}"
                )
                test_response.raise_for_status()
                test_data = test_response.json()
                test_id = test_data.get("id")
                test_id_str = str(test_id)
                
                # Get session and test data
                session_key = self._get_session_key(user_id_str, test_id_str, question_id_str)
                test_key = self._get_test_key(user_id_str, test_id_str)
                
                session_data_str = self.redis.get(session_key)
                test_data_str = self.redis.get(test_key)
                
                
                session_data = json.loads(session_data_str)
                test_data = json.loads(test_data_str)
                
                
                # Update session data
                session_data["student_answer"] = answer
                session_data["is_correct"] = is_correct
                session_data["end_time"] = self._ensure_timestamp(datetime.now(UTC).isoformat())
                
                # Calculate time spent if start_time exists
                if "start_time" in session_data:
                    try:
                        start = datetime.fromisoformat(session_data["start_time"].replace('Z', '+00:00'))
                        end = datetime.fromisoformat(session_data["end_time"].replace('Z', '+00:00'))
                        session_data["time_spent"] = int((end - start).total_seconds())
                    except (ValueError, TypeError):
                        session_data["time_spent"] = 0
                
                # Update test data
                if question_id_str not in test_data.get("completed_questions", []):
                    test_data.setdefault("completed_questions", []).append(question_id_str)
                
                # Make sure the question ID is in the list_question_ids
                if question_id_str not in test_data.get("list_question_ids", []):
                    test_data.setdefault("list_question_ids", []).append(question_id_str)
                
                # Calculate progress
                completed_count = len(test_data.get("completed_questions", []))
                total_count = test_data.get("total_questions", len(test_data.get("list_question_ids", [])))
                if total_count > 0:
                    progress = (completed_count / total_count) * 100
                else:
                    progress = 0
                test_data["progress"] = progress
                
                # Store updated data
                self.redis.setex(session_key, 24 * 60 * 60, json.dumps(session_data))
                self.redis.setex(test_key, 24 * 60 * 60, json.dumps(test_data))
                
                return {
                    "is_correct": is_correct,
                    "correct_answer": correct_answer,
                    "session_data": session_data,
                    "progress": progress
                }
            
            except Exception as e:
                print(f"Error in submit_answer: {e}")
                traceback.print_exc()
                raise e
    
    async def finish_test(self, user_id: str, test_id: str, request_data: Optional[Dict] = None):
        """Finish a test session by creating a test result with question results."""
        if not request_data:
            request_data = {}

        # Get test session
        session_key = f"test:{user_id}:{test_id}"
        session_data_str = self.redis.get(session_key)
        session_data = json.loads(session_data_str) if session_data_str else {
            "start_time": datetime.now(UTC).isoformat(),
            "list_question_ids": [],
            "test_code": request_data.get("test_code", "")
        }
        
        # Retrieve timestamps
        test_start_time = session_data.get('start_time', datetime.now(UTC).isoformat())
        test_end_time = datetime.now(UTC).isoformat()
        
        # Calculate test results based on question session data
        list_question_ids = session_data.get('list_question_ids', [])
        total_questions = len(list_question_ids)
        correct_answers = 0
        all_questions = []
        total_time = 0
        
        # Retrieve and process each question session
        for question_id in list_question_ids:
            q_session_key = self._get_session_key(str(user_id), str(test_id), str(question_id))
            q_session_data_str = self.redis.get(q_session_key)
            
            if q_session_data_str:
                q_data = json.loads(q_session_data_str)
                all_questions.append(q_data)
                total_time += q_data.get('time_spent', 0)
                if q_data.get('is_correct'):
                    correct_answers += 1
        
        # Calculate score
        score = 0
        if total_questions > 0:
            score = (correct_answers / total_questions) * 100
        
        # Create test result
        test_result_data = {
            "test_code": session_data.get('test_code', request_data.get("test_code", "")),
            "username": str(user_id),
            "score": score,
            "total_questions": total_questions,
            "correct_questions": correct_answers,
            "start_time": test_start_time,
            "end_time": test_end_time
        }
        
        try:
            # Create the test result
            test_result_response = requests.post(
                f"{self.database_service_url}/test-results/",
                json=test_result_data
            )
            test_result_response.raise_for_status()
            test_result = test_result_response.json()
            test_result_id = test_result.get("id")
            
            # Process question results
            for question in all_questions:
                # Format timestamps
                start_time = question.get('start_time')
                end_time = question.get('end_time')
                
                question_result = {
                    "question_id": question.get('question_id'),
                    "start_time": start_time,
                    "end_time": end_time or datetime.now(UTC).isoformat(),
                    "student_answer": question.get('student_answer', ''),
                    "isCorrect": question.get('is_correct', False),
                    "time_spent": question.get('time_spent', 0)
                }
                
                requests.post(
                    f"{self.database_service_url}/test-results/{test_result_id}/questions/",
                    json=question_result
                )
            
            # Clean up the session
            self.redis.delete(session_key)
            for question_id in list_question_ids:
                self.redis.delete(self._get_session_key(str(user_id), str(test_id), str(question_id)))
            
            # Prepare complete result to return
            result = {
                "id": test_result_id,
                "score": score,
                "correct_questions": correct_answers,
                "total_questions": total_questions,
                "time_spent": total_time,
                "start_time": test_start_time,
                "end_time": test_end_time
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"Error creating test result: {str(e)}")
            return {"error": f"Failed to save test result: {str(e)}"}
    
    def get_conversation_history(
        self,
        user_id: int,
        test_code: str,
        question_index: int
    ) -> List[Dict]:
        """Get the conversation history for a specific question."""
        session_key = self._get_session_key(str(user_id), test_code, str(question_index))
        session_data = json.loads(self.redis.get(session_key) or "{}")
        return session_data.get("chat_history", [])
    
    def _save_question_result(self, test_result_id, question):
        """Save an individual question result."""
        try:
            # Ensure timestamps are valid
            start_time = self._ensure_timestamp(question.get('start_time'))
            end_time = self._ensure_timestamp(question.get('end_time'))
            
            question_result = {
                "question_id": question.get('question_id'),
                "start_time": start_time,
                "end_time": end_time,
                "student_answer": question.get('student_answer', ''),
                "isCorrect": question.get('is_correct', False),
                "time_spent": question.get('time_spent', 0)
            }
            
            print(f"Saving question result for test {test_result_id}, question {question.get('question_id')}")
            
            response = requests.post(
                f"{self.database_service_url}/test-results/{test_result_id}/questions/",
                json=question_result
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error saving question result: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                print(f"Response error detail: {e.response.text}")
            return None
        except Exception as e:
            print(f"Unexpected error saving question result: {str(e)}")
            return None 