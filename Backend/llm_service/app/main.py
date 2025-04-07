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
VECTOR_SERVICE_URL = os.getenv("VECTOR_SERVICE_URL", "http://vector-service:8002")
MODEL_CACHE_DIR = os.getenv("MODEL_CACHE_DIR", "./model_cache")  # Using local directory
MAX_LENGTH = int(os.getenv("MAX_LENGTH", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.8"))
DEVICE = os.getenv("DEVICE", "0")  # Use "0" for first GPU, "-1" for CPU
MAX_RESPONSE_LENGTH = int(os.getenv("MAX_RESPONSE_LENGTH", "200"))  # Increased from 180 to 500

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

def format_chat_history(chat_history):
    """Convert chat history to structured message format."""
    messages = []
    for msg in chat_history:
        # Handle different chat history formats
        if isinstance(msg, dict):
            if "role" in msg and "content" in msg:
                # This is the format used in conversation_service.py
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
    return messages

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
        
        # Create system message based on context
        if hidden_value:
            system_message = "You are a helpful teaching assistant. The student is asking about a hidden value in the problem. Since they specifically asked for it, you can provide the hidden value from the context. Be clear and informative."
            is_hidden_value_response = True
        elif is_practice_exam:
            system_message = "You are a helpful teaching assistant using Socratic questioning. If the student appears to be stuck on this problem, ask them a question that will help guide their thinking. DO NOT provide direct answers. Review the chat history to avoid repeating questions."
            is_hidden_value_response = False
        
        # Create context message
        context_message = f"Problem: {public_question}\n\n"
        if hidden_value:
            context_message += f"Hidden value: {hidden_value}\n\n"
        elif topic_context:
            context_message += f"Helpful information: {topic_context}\n\n"
        
        # Format chat history as messages
        formatted_history = format_chat_history(chat_history)
        
        # Create the complete messages list
        messages = [
            {"role": "system", "content": system_message},
        ]
        
        # Add formatted history if available
        if formatted_history:
            messages.extend(formatted_history)
        
        # Add the current context and query
        messages.append({"role": "user", "content": context_message + f"Student question: {request.query}"})
        
        print(f"Processing query with structured chat format...")
        
        try:
            # Check if tokenizer supports chat templates
            if hasattr(llm_pipeline.tokenizer, "apply_chat_template"):
                # Use the model's native chat template
                print("using chat template")
                chat_text = llm_pipeline.tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
                print("chat text: \n", chat_text)
                # Generate response using the formatted text
                response = llm_pipeline(
                    chat_text,
                    do_sample=True,
                    temperature=TEMPERATURE,
                    max_new_tokens=MAX_RESPONSE_LENGTH,
                    pad_token_id=0,
                    num_return_sequences=1,
                    early_stopping=False,
                    use_cache=True,
                    return_full_text=False
                )
                
                assistant_response = response[0]["generated_text"].strip()
            else:
                # Fallback to traditional prompt format
                print("using traditional prompt format")
                system_prompt = f"{system_message}\n\n{context_message}"
                
                # Include chat history summary in the system prompt
                if chat_history:
                    history_summary = "Previous conversation:\n"
                    for msg in chat_history[-3:]:  # Only include last 3 messages
                        sender = "Student" if msg.get("sender") == "user" else "Assistant"
                        history_summary += f"{sender}: {msg.get('content', '')}\n"
                    system_prompt += f"\n\n{history_summary}"
                
                full_prompt = format_prompt(system_prompt, request.query)
                
                response = llm_pipeline(
                    full_prompt,
                    do_sample=True,
                    temperature=TEMPERATURE,
                    max_new_tokens=MAX_RESPONSE_LENGTH,
                    pad_token_id=0,
                    num_return_sequences=1,
                    early_stopping=False,
                    use_cache=True,
                    return_full_text=False
                )
                
                generated_text = response[0]["generated_text"]
                
                # Parse the response based on format
                if "[/INST]" in full_prompt:
                    assistant_response = generated_text.strip()
                else:
                    assistant_response = generated_text.split("<|assistant|>")[-1].strip()
                    if "<|endoftext|>" in assistant_response:
                        assistant_response = assistant_response.split("<|endoftext|>")[0].strip()
                
        except Exception as e:
            print(f"LLM generation error: {e}")
            assistant_response = "I'm sorry, I encountered an error while processing your request."
                
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

