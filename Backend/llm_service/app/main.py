# backend/ service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline, AutoModelForCausalLM
import httpx
from typing import Dict, List, Optional
import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import login, InferenceClient
import torch
from teapotai import TeapotAI


# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="LLM Microservice")

class LLMRequest(BaseModel):
    query: str
    context: Dict

class LLMResponse(BaseModel):
    response: str
    isHiddenValueResponse: bool

# Try to authenticate with Hugging Face
hf_token = os.getenv("HUGGING_FACE_HUB_TOKEN")
if hf_token:
    print("Authenticating with Hugging Face...")
    login(token=hf_token)
else:
    print("Warning: No Hugging Face token found. Authentication may fail for gated models.")

# Configuration from environment variables - ensure MODEL_NAME from .env is used
MODEL_NAME = os.getenv("MODEL_NAME", "mistralai/Mistral-7B-Instruct-v0.2")
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8002")
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./model_cache")  # Using local directory
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))
DEVICE = os.getenv("DEVICE", "0")  # Use "0" for first GPU, "-1" for CPU
MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "180"))  # Increased response length cap

# Create cache directory if it doesn't exist
print(f"Loading {MODEL_NAME} model using pipeline...")
try:
    # Initialize the pipeline with optimized settings
    llm_pipeline = pipeline(
        task="text-generation",
        model=MODEL_NAME,
        device=0,
        torch_dtype=torch.float16,  # Use half precision to reduce memory usage
        model_kwargs={
            "cache_dir": MODEL_CACHE_DIR,
            "low_cpu_mem_usage": True,
            "use_auth_token": hf_token,
            "attn_implementation": "eager",  # Use flash attention on CUDA
        },
        trust_remote_code=True 
    )
    print(f"{MODEL_NAME} model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
    print(f"Full error details: {repr(e)}")
    raise


def format_prompt(system_prompt: str, query: str) -> str:
    """Format the prompt according to Mistral instruction format."""
    return f"""<s>[INST] {system_prompt}

 here is the student's question:
{query} [/INST]"""

async def get_hidden_values(problem_id: str, query: str) -> Optional[str]:
    """Search for hidden values specific to this problem."""
    print("attempting to get hidden values from vector service")
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
            does_exist = data.get("has_hidden_values")
            if does_exist:
                # If we found hidden values, format them for the LLM
                return data["hidden_value"]
            return None
            
    except Exception as e:
        print('--------------------------------')
        print(f"Error fetching hidden values: {e}")
        return None

async def get_topic_context(problem_id: str, query: str) -> str:
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
                
            return ""
            
    except Exception as e:
        print('--------------------------------')
        print(f"Error fetching topic context: {e}")
        return ""


@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    try:
        problem_id = f"{request.context.get('test_id')}_{request.context.get('question_id')}"
        
        # Get chat history from context
        chat_history = request.context.get("chat_history", [])
        
        # Check if this is a practice exam or a regular test
        is_practice_exam = request.context.get("isPracticeExam", False)
        public_question = request.context.get("public_question", "")
            
        # First check if this is a request for hidden values
        try:
            hidden_value = await get_hidden_values(problem_id, request.query)
            print("hidden value successfully retrieved: ", hidden_value)
        except Exception as e:
            print(f"No hidden values found for this problem")
            hidden_value = None
        
        # For regular tests, enforce strict limitations
        if not is_practice_exam and not hidden_value:
            return LLMResponse(
                response="I can only help with understanding hidden values for this test question. Please rephrase your question to ask about a specific hidden value.",
                isHiddenValueResponse=False
            )
                
        # Get topic context if no hidden values found
        topic_context = "" if hidden_value else await get_topic_context(problem_id, request.query)
        
        # Construct the prompt based on what we found
        if hidden_value:
            system_prompt = f"""You are a helpful teaching assistant. The student is asking about a hidden value in the problem. Since they specifically asked for it, you can provide the hidden value from the context. Be clear and informative.

This is the problem they are trying to solve: {public_question}

Here is the hidden value: {hidden_value}"""
            is_hidden_value_response = True

        elif is_practice_exam:
            public_question = str(request.context.get("public_question"))
            
            system_prompt = f"""You are a helpful teaching assistant using Socratic questioning. If the student appears to be stuck on this problem, ask them a question that will help guide their thinking. 
DO NOT provide direct answers. If there is a helpful teaching material, use it to help the student understand the problem and guide them towards the solution.

Review the chat history to ensure you aren't repeating yourself; if you are, ask a different question. Build off of the previous question if possible.

Chat history: {chat_history}

The problem they are trying to solve: {public_question}

Helpful information: {topic_context}"""
            
            is_hidden_value_response = False
        
        full_prompt = format_prompt(
            system_prompt,
            request.query, 
        )

        print(f"Processing query with context...")

        assistant_response = teapot_ai.query(
            query=request.query,
            context=system_prompt,
        )

        # try:
        #     response = llm_pipeline(
        #         full_prompt,
        #         do_sample=True,
        #         temperature=TEMPERATURE,
        #         pad_token_id=0,
        #         num_return_sequences=1,
        #         early_stopping=False,
        #         use_cache=True,
        #         return_full_text=False
        #     )
        #     generated_text = response[0]["generated_text"]
            
        #     # two extraction methods for different model formats
        #     if "[/INST]" in full_prompt:
        #         assistant_response = generated_text.strip()
        #     else:
        #         assistant_response = generated_text.split("<|assistant|>")[-1].strip()
        #         if "<|endoftext|>" in assistant_response:
        #             assistant_response = assistant_response.split("<|endoftext|>")[0].strip()
        # except Exception as e:
        #     print(f"API call failed, falling back to local model: {e}")            
                
        return LLMResponse(response=assistant_response, isHiddenValueResponse=is_hidden_value_response)
            
        

    except Exception as e:
        print(f"LLM service: An error occurred while generating the response: {e}")
        print(f"Full error details: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Add health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

