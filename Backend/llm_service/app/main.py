# backend/llm_service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import httpx
from typing import Dict, List, Optional

app = FastAPI(title="LLM Microservice")

class Context(BaseModel):
    problem_id: int
    test_code: str
    question_index: int
    conversation_history: List[Dict[str, str]]

class LLMRequest(BaseModel):
    query: str
    context: Context

class LLMResponse(BaseModel):
    response: str

MODEL_PATH = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
VECTOR_SERVICE_URL = "http://vector_service:8002"  # Update with your vector service URL

print("Loading TinyLlama model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    use_cache=True)
print("TinyLlama model loaded!")

async def get_relevant_context(problem_id: int, query: str) -> str:
    """Fetch relevant context from vector service."""
    try:
        async with httpx.AsyncClient() as client:
            # Get problem details
            problem_response = await client.get(
                f"{VECTOR_SERVICE_URL}/problems/{problem_id}"
            )
            problem_response.raise_for_status()
            problem_data = problem_response.json()

            # Get relevant teaching materials
            context_response = await client.post(
                f"{VECTOR_SERVICE_URL}/search",
                json={
                    "query": query,
                    "problem_id": problem_id,
                    "limit": 3
                }
            )
            context_response.raise_for_status()
            context_data = context_response.json()

            # Combine problem and teaching material context
            context = f"""Problem: {problem_data['question']}
Answer: {problem_data['answer']}
Explanation: {problem_data['explanation']}

Relevant Teaching Materials:
"""
            for material in context_data['results']:
                context += f"- {material['content']}\n"

            return context
    except Exception as e:
        print(f"Error fetching context: {e}")
        return ""

def format_conversation_history(history: List[Dict[str, str]]) -> str:
    """Format conversation history into a string."""
    formatted = "\nConversation History:\n"
    for msg in history:
        role = "Student" if msg["role"] == "user" else "Assistant"
        formatted += f"{role}: {msg['content']}\n"
    return formatted

@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    try:
        # Get relevant context from vector service
        context = await get_relevant_context(
            request.context.problem_id,
            request.query
        )

        # Format conversation history
        conversation = format_conversation_history(request.context.conversation_history)

        # Construct the full prompt
        system_prompt = """You are a helpful teaching assistant. Use the provided context to help the student understand the problem and guide them towards the solution. Don't give away the answer directly, but provide helpful hints and explanations."""
        
        full_prompt = f"""{system_prompt}

{context}

{conversation}

Student: {request.query}
Assistant: """

        print(f"Processing query with context...")
        inputs = tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=2048)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                temperature=0.7,
                do_sample=True,
                top_k=40,
                num_beams=1,
                pad_token_id=tokenizer.eos_token_id,
                use_cache=True,
                repetition_penalty=1.1
            )

        completion = tokenizer.decode(
            output_ids[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )
        return LLMResponse(response=completion.strip())

    except Exception as e:
        print(f"LLM service: An error occurred while generating the response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

