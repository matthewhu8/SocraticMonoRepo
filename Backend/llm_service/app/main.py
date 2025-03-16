# backend/llm_service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import httpx
from typing import Dict, List, Optional
import os
from pathlib import Path

app = FastAPI(title="LLM Microservice")

class Context(BaseModel):
    problem_id: int
    test_code: str
    question_index: int

class LLMRequest(BaseModel):
    query: str
    context: Context

class LLMResponse(BaseModel):
    response: str

# Configuration from environment variables
MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.1")
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://vector-service:8000")
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "/app/data/model_cache")
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "2048"))
MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "512"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Create cache directory if it doesn't exist
Path(MODEL_CACHE_DIR).mkdir(parents=True, exist_ok=True)

print(f"Loading {MODEL_NAME} model...")
try:
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        cache_dir=MODEL_CACHE_DIR,
        trust_remote_code=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        use_cache=True,
        cache_dir=MODEL_CACHE_DIR,
        trust_remote_code=True
    )
    print(f"{MODEL_NAME} model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    raise

def format_prompt(system_prompt: str, context: str, query: str) -> str:
    """Format the prompt according to Mistral's instruction format."""
    return f"""<s>[INST] {system_prompt}

{context}

Student: {query} [/INST]"""

async def get_hidden_values(problem_id: int, query: str) -> Optional[str]:
    """Search for hidden values specific to this problem."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{VECTOR_SERVICE_URL}/search_hidden_values",
                json={
                    "query": query,
                    "problem_id": problem_id,
                }
            )
            response.raise_for_status()
            data = response.json()
            
            if data["results"]:
                # If we found hidden values, format them for the LLM
                hidden_values = "\nHidden Values Found:\n"
                for result in data["results"]:
                    hidden_values += f"- {result['content']}\n"
                return hidden_values
            return None
            
    except Exception as e:
        print(f"Error fetching hidden values: {e}")
        return None

async def get_topic_context(problem_id: int, query: str) -> str:
    """Get relevant topic information for the problem."""
    try:
        async with httpx.AsyncClient() as client:
            # First get the problem topic
            topic_response = await client.get(
                f"{VECTOR_SERVICE_URL}/problems/{problem_id}/topic"
            )
            topic_response.raise_for_status()
            topic_data = topic_response.json()
            
            # Then search for relevant materials using both query and topic
            context_response = await client.post(
                f"{VECTOR_SERVICE_URL}/search_materials",
                json={
                    "query": query,
                    "topic": topic_data["topic"],
                    "problem_id": problem_id,
                    "limit": 3
                }
            )
            context_response.raise_for_status()
            context_data = context_response.json()
            
            # Format the teaching materials
            context = "\nRelevant Teaching Materials:\n"
            for material in context_data["results"]:
                context += f"- {material['content']}\n"
                
            return context
            
    except Exception as e:
        print(f"Error fetching topic context: {e}")
        return ""

@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    try:
        # First check if this is a request for hidden values
        hidden_values = await get_hidden_values(
            request.context.problem_id,
            request.query
        )
        
        # Get topic context if no hidden values found
        topic_context = "" if hidden_values else await get_topic_context(
            request.context.problem_id,
            request.query
        )
        
        # Construct the prompt based on what we found
        if hidden_values:
            system_prompt = """You are a helpful teaching assistant. The student is asking about a hidden value in the problem. 
Since they specifically asked for it, you can provide the hidden value from the context below."""
        else:
            system_prompt = """You are a helpful teaching assistant. Use the provided teaching materials to help the student 
understand the problem and guide them towards the solution. Don't give away answers directly, but provide helpful hints and explanations."""
        
        full_prompt = format_prompt(
            system_prompt,
            hidden_values if hidden_values else topic_context,
            request.query
        )

        print(f"Processing query with context...")
        inputs = tokenizer(full_prompt, return_tensors="pt", truncation=True, max_length=MAX_LENGTH)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=MAX_NEW_TOKENS,
                temperature=TEMPERATURE,
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

