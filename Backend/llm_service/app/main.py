# backend/ service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import httpx
from typing import Dict, List, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import login

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="LLM Microservice")

class LLMRequest(BaseModel):
    query: str
    context: Dict

class LLMResponse(BaseModel):
    response: str

# Try to authenticate with Hugging Face
hf_token = os.getenv("HUGGING_FACE_HUB_TOKEN")
if hf_token:
    print("Authenticating with Hugging Face...")
    login(token=hf_token)
else:
    print("Warning: No Hugging Face token found. Authentication may fail for gated models.")

# Configuration from environment variables - ensure MODEL_NAME from .env is used
MODEL_NAME = os.getenv("MODEL_NAME")
if not MODEL_NAME:
    print("Warning: MODEL_NAME not found in environment variables. Using default model.")
    MODEL_NAME = "microsoft/phi-2"  # Changed default to phi-2 which is more accessible
print(f"Using model: {MODEL_NAME}")

VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://localhost:8002")
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./model_cache")  # Using local directory
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))
DEVICE = os.getenv("DEVICE", "0")  # Use "0" for first GPU, "-1" for CPU

# Create cache directory if it doesn't exist
Path(MODEL_CACHE_DIR).mkdir(parents=True, exist_ok=True)

print(f"Loading {MODEL_NAME} model using pipeline...")
try:
    # Check if MPS (Metal Performance Shaders) is available on Mac
    import torch
    
    # Set device based on what's available
    if torch.backends.mps.is_available() and int(DEVICE) == 0:
        device_name = "mps"  # Use Metal Performance Shaders on Mac
        print("Using MPS (Metal) for GPU acceleration")
    elif torch.cuda.is_available() and int(DEVICE) == 0:
        device_name = "cuda"  # Use CUDA if available (non-Mac)
        print("Using CUDA for GPU acceleration")
    else:
        device_name = "cpu"
        print("GPU not available, falling back to CPU")
    
    # Initialize the pipeline with settings optimized for Mac GPU
    llm_pipeline = pipeline(
        "text-generation",
        model=MODEL_NAME,
        device=device_name,  # Use the detected device
        torch_dtype=torch.float16,  # Use half precision to reduce memory usage
        model_kwargs={
            "cache_dir": MODEL_CACHE_DIR,
            "low_cpu_mem_usage": True,
            "use_auth_token": hf_token
        },
        trust_remote_code=True
    )
    print(f"{MODEL_NAME} model loaded successfully on {device_name}!")
except Exception as e:
    print(f"Error loading model: {e}")
    print(f"Full error details: {repr(e)}")
    raise

def format_prompt(system_prompt: str, context: str, query: str) -> str:
    """Format the prompt according to TinyLlama chat format."""
    return f"""<|system|>
{system_prompt}

{context}
<|user|>
{query}
<|assistant|>"""

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
                
            return context
            
    except Exception as e:
        print('--------------------------------')
        print(f"Error fetching topic context: {e}")
        return ""

@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    try:
        print("\n request", request)   
        # Extract problem ID from context
        problem_id = f"{request.context.get('test_id')}_{request.context.get('question_id')}"
        
        # First check if this is a request for hidden values
        hidden_value = await get_hidden_values(problem_id, request.query)
        print("hidden value successfully retrieved: ", hidden_value)
        
        
        # Get topic context if no hidden values found
        topic_context = "" if hidden_value else await get_topic_context(problem_id, request.query)
        
        # Construct the prompt based on what we found
        if hidden_value:
            system_prompt = """You are a helpful teaching assistant. The student is asking about a hidden value in the problem. Since they specifically asked for it, you can provide the hidden value from the context below. Be short and to the point."""
        else:
            system_prompt = """You are a helpful teaching assistant. Use the provided teaching materials to help the student understand the problem and guide them towards the solution. Don't give away answers directly, but provide helpful hints and explanations."""
        
        full_prompt = format_prompt(
            system_prompt,
            hidden_value if hidden_value else topic_context,
            request.query
        )

        print(f"Processing query with context...")
        print("full prompt\n:", full_prompt)
        
        try:
            # Generate response using the pipeline - optimized for TinyLlama
            response = llm_pipeline(
                full_prompt,
                do_sample=True,  # TinyLlama works better with sampling
                temperature=0.7,
                max_new_tokens=MAX_LENGTH,
                pad_token_id=0  # Use 0 as pad token for TinyLlama
            )
            
            # Extract the generated text
            generated_text = response[0]["generated_text"]
            
            # Extract only the assistant's response - TinyLlama format
            assistant_response = generated_text.split("<|assistant|>")[-1].strip()
            # Remove EOS token if present
            if "<|endoftext|>" in assistant_response:
                assistant_response = assistant_response.split("<|endoftext|>")[0].strip()
            
            return LLMResponse(response=assistant_response)
            
        except Exception as inner_e:
            print(f"Error during model inference: {str(inner_e)}")
            print(f"Full error details: {repr(inner_e)}")
            raise HTTPException(status_code=500, detail=f"Model inference error: {str(inner_e)}")

    except Exception as e:
        print(f"LLM service: An error occurred while generating the response: {e}")
        print(f"Full error details: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

