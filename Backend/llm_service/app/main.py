# backend/llm_service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM

app = FastAPI(title="LLM Microservice")

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: int = 128

class LLMResponse(BaseModel):
    completion: str

MODEL_PATH = "meta-llama/Llama-2-7b-hf"

print("Loading Llama model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, device_map="auto")
print("Llama model loaded!")

@app.post("/generate", response_model=LLMResponse)
def generate_text(request: LLMRequest):
    return LLMResponse(completion="Mocked LLM response! Welcome to socratic-chatbot!")
    try:
        # Tokenize the prompt and ensure tensors are on the correct device
        inputs = tokenizer(request.prompt, return_tensors="pt")
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Generate new tokens based on the prompt
        output_ids = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=0.7,
            do_sample=True
        )
        
        # Decode the generated tokens into text and remove the prompt from the result
        generated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
        completion = generated_text[len(request.prompt):].strip()
        return LLMResponse(completion=completion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
