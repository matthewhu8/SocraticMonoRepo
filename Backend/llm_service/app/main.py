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
from huggingface_hub import login
import torch

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="LLM Microservice")

# In-memory question counters for specific problems
question_counters = {
    "economies_of_scale": 0,
    "leadership_styles": 0,
    "social_responsibility": 0,
    "pricing_strategies": 0
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
DEVICE = os.getenv("DEVICE", "-1")  # Use "0" for first GPU, "-1" for CPU
MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "50"))  # Cap response length

# Create cache directory if it doesn't exist
Path(MODEL_CACHE_DIR).mkdir(parents=True, exist_ok=True)

print(f"Loading {MODEL_NAME} model using pipeline...")
try:
    # Set device based on configuration and availability
    device_name = DEVICE
    
    # If set to 'mps', verify MPS is available
    if device_name == "mps" and not torch.backends.mps.is_available():
        print("MPS requested but not available, falling back to CPU")
        device_name = "cpu"
    # If set to 'cuda', verify CUDA is available
    elif (device_name == "cuda" or device_name == "0") and not torch.cuda.is_available():
        print("CUDA requested but not available, falling back to CPU")
        device_name = "cpu"
    elif device_name == "-1":
        device_name = "cpu"
    
    print(f"Using device: {device_name}")
    
    # Initialize the pipeline with optimized settings
    llm_pipeline = pipeline(
        task="text-generation",
        model=MODEL_NAME,
        device=device_name,
        torch_dtype=torch.float16,  # Use half precision to reduce memory usage
        model_kwargs={
            "cache_dir": MODEL_CACHE_DIR,
            "low_cpu_mem_usage": True,
            "use_auth_token": hf_token,
            "load_in_8bit": device_name != "mps",  # 8-bit quantization (not supported on MPS)
            "attn_implementation": "flash_attention_2" if device_name == "cuda" else "eager",  # Use flash attention on CUDA
        },
        trust_remote_code=True
    )
    print(f"{MODEL_NAME} model loaded successfully on {device_name}!")
except Exception as e:
    print(f"Error loading model: {e}")
    print(f"Full error details: {repr(e)}")
    raise


def format_prompt(system_prompt: str, context: str, query: str) -> str:
    """Format the prompt according to Mistral instruction format."""
    return f"""<s>[INST] {system_prompt}

{context}

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
        print("\n request", request)   
        # Extract problem ID from context
        problem_id = f"{request.context.get('test_id')}_{request.context.get('question_id')}"
        
        # Get chat history from context
        chat_history = request.context.get("chat_history", [])
        
        # Check if this is a practice exam or a regular test
        is_practice_exam = request.context.get("isPracticeExam", False)
        
        # Hard-coded specific projectile motion problem detection

        economies_of_scale = "Evaluate the impact of economies"
        leadership_styles = "different leadership styles can influence"
        social_responsibility = "Examine the role of corporate social responsibility"
        pricing_strategies = "Explain the key factors that influence pricing strategies"
        public_question = request.context.get("public_question", "")
        
        if economies_of_scale in public_question:
            question_count = question_counters.get("economies_of_scale")
            question_counters["economies_of_scale"] = question_count + 1
            await asyncio.sleep(3)
            
            if question_count == 0:  # First time asking
                print("First time asking economies of scale problem")
                return LLMResponse(
                    response="Consider both the cost advantages that can come from increased production levels and the potential challenges such as coordination difficulties and diminishing returns as the business grows.",
                    isHiddenValueResponse=False
                )
            
        elif leadership_styles in public_question:
            question_count = question_counters.get("leadership_styles", 0)            
            question_counters["leadership_styles"] = question_count + 1
            await asyncio.sleep(3)
            
            # Return appropriate hint based on question count
            if question_count == 0:  # First time asking
                return LLMResponse(
                    response="Reflect on various leadership approaches and link them to motivational theories. Think about how a the behavior of a leader might foster or hinder an environment that drives employee engagement.",
                    isHiddenValueResponse=False
                )
        elif social_responsibility in public_question:
            question_count = question_counters.get("social_responsibility", 0)
            question_counters["social_responsibility"] = question_count + 1
            await asyncio.sleep(3)
            
            if question_count == 0:  # First time asking
                return LLMResponse(
                    response="Analyze how CSR initiatives might build stakeholder trust and add value to the brand, while also considering any possible trade-offs or challenges involved in implementing these practices.",
                    isHiddenValueResponse=False
                )
        elif pricing_strategies in public_question:
            question_count = question_counters.get("pricing_strategies", 0)
            question_counters["pricing_strategies"] = question_count + 1
            await asyncio.sleep(3)
            
            if question_count == 0:  # First time asking
                return LLMResponse(
                    response="Consider internal factors such as cost structure and business objectives alongside external factors like market demand, competitor actions, and customer perceptions.",
                    isHiddenValueResponse=False
                )
            
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
            system_prompt = f"""You are a helpful teaching assistant. The student is asking about a hidden value in the problem. Since they specifically asked for it, you can provide the hidden value from the context. Be short and to the point.

IMPORTANT: Keep your response under 60 characters. Be concise and direct."""
            is_hidden_value_response = True
            llm_context = f"""
            This is the problem they are trying to solve: {public_question}

            Here is the hidden value: {hidden_value}
            """

        elif is_practice_exam:
            public_question = str(request.context.get("public_question"))
            
            system_prompt = f"""You are a helpful teaching assistant using Socratic questioning. If the student appears to be stuck on this problem, ask them a question that will help guide their thinking. 
            DO NOT provide direct answers. Use the provided teaching materials, chat history, and the public question they are trying to solve to help the student understand the problem and guide them towards the solution.
            
            IMPORTANT: Keep your response under 60 characters. Be concise and direct. 
            Review the chat history to ensure your questions to ensure you aren't asking the same question. Don't ask the same question twice.
            
            Chat history: {chat_history}

            This is the problem they are trying to solve: {public_question}
            """
            llm_context = f"""
            This is the problem they are trying to solve: {public_question}

            Here is the chat history: {chat_history}

            Here are some help teaching materials: {topic_context}
            """
            
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
            context = llm_context,
            do_sample=True,
            temperature=TEMPERATURE,
            max_new_tokens=MAX_RESPONSE_LENGTH,
            pad_token_id=0,
            num_return_sequences=1,
            early_stopping=True,
            use_cache=True,  # Enable KV caching for faster generation
            return_full_text=False  # Don't include prompt in output to save processing
            )
        generated_text = response[0]["generated_text"]
        
        # Extract the assistant's response from the generated text
        # For Mistral format, extract content between [/INST] and end
        if "[/INST]" in full_prompt:
            # This is for Mistral format
            assistant_response = generated_text.strip()
        else:
            # Fallback to previous extraction method
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

