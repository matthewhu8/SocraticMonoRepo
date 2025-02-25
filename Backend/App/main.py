from fastapi import FastAPI, HTTPException 
from pydantic import BaseModel
from .Modules.Conversation.conversation_service import ConversationService
from .Modules.Conversation.llm_client import call_llm
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

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

convo_service = ConversationService(call_llm=call_llm)

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        response_text = convo_service.process_query(request.query, request.problem_id)
        return ChatResponse(response=response_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history")
def chat_history(problem_id: int):
    return {"history": "Coming soon!"}

@app.get("/chat/settings")
def chat_settings(problem_id: int):
    return {"settings": "Coming soon!"}
    