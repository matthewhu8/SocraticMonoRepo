import httpx
from typing import Dict, Any, Optional

class ConversationService:
    def __init__(self, llm_service_url: str):
        """Initialize the ConversationService with the LLM service URL."""
        self.llm_service_url = llm_service_url
        self.sessions = {}  # In-memory session storage (could be replaced with Redis)
    
    async def process_query(
        self, 
        query: str, 
        problem_id: int, 
        user_id: str = "anonymous",
        test_code: Optional[str] = None,
        question_index: Optional[int] = None
    ) -> str:
        """Process a user query and return a response."""
        # Get or create session
        session_key = f"{user_id}_{problem_id}"
        if session_key not in self.sessions:
            self.sessions[session_key] = []
        
        # Add user message to session
        self.sessions[session_key].append({
            "role": "user",
            "content": query
        })
        
        # Prepare context for LLM
        context = {
            "problem_id": problem_id,
            "test_code": test_code,
            "question_index": question_index,
            "conversation_history": self.sessions[session_key]
        }
        
        # Call LLM service
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.llm_service_url}/generate",
                json={
                    "query": query,
                    "context": context
                }
            )
            
            if response.status_code != 200:
                raise ValueError(f"Failed to get response from LLM service: {response.text}")
            
            llm_response = response.json().get("response", "I'm sorry, I couldn't process your request.")
        
        # Add assistant response to session
        self.sessions[session_key].append({
            "role": "assistant",
            "content": llm_response
        })
        
        return llm_response
    
    def get_conversation_history(self, user_id: str, problem_id: int) -> list:
        """Get the conversation history for a user and problem."""
        session_key = f"{user_id}_{problem_id}"
        return self.sessions.get(session_key, []) 