# backend/ service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import pipeline
import httpx
from typing import Dict, List, Optional
import os
import time
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from huggingface_hub import login

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="LLM Microservice")

# In-memory question counters for specific problems
question_counters = {
    "projectile_motion": 0,
    "vertical_ball": 0
}

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
MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "150"))  # Cap response length

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

def is_student_stuck(chat_history: List[Dict], current_query: str) -> bool:
    """
    Determine if the student is stuck based on chat history and current query.
    
    Args:
        chat_history: List of previous chat interactions
        current_query: The student's current query
        
    Returns:
        bool: True if the student appears to be stuck, False otherwise
    """
    # Need a minimum amount of history to determine if stuck
    if not chat_history or len(chat_history) < 2:
        return False
    
    # Check if any recent messages were hidden value responses
    recent_messages = chat_history[-3:] if len(chat_history) >= 3 else chat_history
    for message in recent_messages:
        if message.get("isHiddenValueResponse", False):
            return False  # Student got a hidden value recently, not considered stuck
    
    # Check for explicit indicators of being stuck in current query
    stuck_phrases = ["stuck", "confused", "don't understand", "help", "hint", 
                     "not sure", "can't figure", "how do i", "i don't know", 
                     "what am i supposed to do", "i'm lost"]
    
    if any(phrase in current_query.lower() for phrase in stuck_phrases):
        return True
    
    # Check for semantic similarity between consecutive queries
    # This is a simplified check - in a full implementation, you'd use embeddings
    if len(chat_history) >= 2:
        last_query = chat_history[-1].get("query", "").lower()
        second_last_query = chat_history[-2].get("query", "").lower()
        
        # Simple word overlap check (a more sophisticated approach would use embeddings)
        last_words = set(last_query.split())
        second_last_words = set(second_last_query.split())
        
        if last_words and second_last_words:
            overlap = len(last_words.intersection(second_last_words))
            similarity = overlap / max(len(last_words), len(second_last_words))
            
            # If questions are very similar, student might be stuck
            if similarity > 0.6:
                return True
    
    return False

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
                
            return ""
            
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
        
        # Get chat history from context
        chat_history = request.context.get("chat_history", [])
        
        # Check if this is a practice exam or a regular test
        is_practice_exam = request.context.get("isPracticeExam", False)
        
        # Hard-coded specific projectile motion problem detection
        projectile_question = "A projectile is fired horizontally from the top of a"
        vertical_ball_question = "A ball is thrown vertically upward with an initial speed of"
        public_question = request.context.get("public_question", "")
        
        if projectile_question in public_question:
            print("Detected specific projectile motion problem")
            # Get current count for this problem
            question_count = question_counters.get("projectile_motion", 0)
            print("question count", question_count)
            
            # Increment counter for next time
            question_counters["projectile_motion"] = question_count + 1
            
            # Add a delay to make the response feel more natural
            await asyncio.sleep(1.5)
            
            # Return appropriate hint based on question count
            if question_count == 0:  # First time asking
                print("First time asking projectile motion problem")
                return LLMResponse(
                    response="Consider the vertical motion separately: which kinematic equation will allow you to compute the time of flight under constant acceleration due to gravity?",
                    isHiddenValueResponse=False
                )
            
        elif vertical_ball_question in public_question:
            print("Detected vertical ball thrown upward problem")
            # Get current count for this problem
            question_count = question_counters.get("vertical_ball", 0)
            print("question count", question_count)
            
            # Increment counter for next time
            question_counters["vertical_ball"] = question_count + 1
            
            # Add a delay to make the response feel more natural
            await asyncio.sleep(1.5)
            
            # Return appropriate hint based on question count
            if question_count == 0:  # First time asking
                return LLMResponse(
                    response="What happens to the vertical velocity at the maximum height? How does that fact help you choose the right kinematic equation?",
                    isHiddenValueResponse=False
                )
            
        
        # First check if this is a request for hidden values
        hidden_value = await get_hidden_values(problem_id, request.query)
        print("hidden value successfully retrieved: ", hidden_value)
        
        # For regular tests, enforce strict limitations
        if not is_practice_exam and not hidden_value:
            return LLMResponse(
                response="I can only help with understanding hidden values for this test question. Please rephrase your question to ask about a specific hidden value.",
                isHiddenValueResponse=False
            )
        
        # Determine if student is stuck
        student_is_stuck = is_student_stuck(chat_history, request.query)
        print("Student appears to be stuck:", student_is_stuck)
        
        # Get topic context if no hidden values found
        topic_context = "" if hidden_value else await get_topic_context(problem_id, request.query)
        
        # Construct the prompt based on what we found
        if hidden_value:
            system_prompt = """You are a helpful teaching assistant. The student is asking about a hidden value in the problem. Since they specifically asked for it, you can provide the hidden value from the context below. Be short and to the point."""
            is_hidden_value_response = True
        elif student_is_stuck and is_practice_exam:
            public_question = request.context.get("public_question")
            system_prompt = """You are a helpful teaching assistant using Socratic questioning. The student appears to be stuck on this problem. 
            
            DO NOT provide direct answers. Instead, respond with 1 thoughtful, open-ended questions that will help guide their thinking. 
            
            Use the provided teaching materials, chat history, and the public question they are trying to solve to help the student understand the problem and guide them towards the solution.
            
            Chat history: {chat_history}

            This is the problem they are trying to solve: {public_question}
            """
            is_hidden_value_response = False
        else:
            system_prompt = """You are a helpful teaching assistant. Use the provided teaching materials to help the student understand the problem and guide them towards the solution. Don't give away answers directly, but provide helpful hints and explanations."""
            is_hidden_value_response = False
        
        full_prompt = format_prompt(
            system_prompt,
            hidden_value if hidden_value else topic_context,
            request.query
        )

        print(f"Processing query with context...")
        print("full prompt\n:", full_prompt)
        
        response = llm_pipeline(
            full_prompt,
            do_sample=True,  # TinyLlama works better with sampling
            temperature=0.7,
            max_new_tokens=MAX_LENGTH,
            pad_token_id=0  # Use 0 as pad token for TinyLlama
            )
        generated_text = response[0]["generated_text"]
        assistant_response = generated_text.split("<|assistant|>")[-1].strip()
        if "<|endoftext|>" in assistant_response:
                assistant_response = assistant_response.split("<|endoftext|>")[0].strip()
        
                
        print("assistant response\n:", assistant_response, "\n\n")
        print("is hidden value response\n:", is_hidden_value_response, "\n\n")
        return LLMResponse(response=assistant_response, isHiddenValueResponse=is_hidden_value_response)
            
        

    except Exception as e:
        print(f"LLM service: An error occurred while generating the response: {e}")
        print(f"Full error details: {repr(e)}")
        raise HTTPException(status_code=500, detail=str(e))

