# backend/llm_service/app/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = FastAPI(title="LLM Microservice")

class LLMRequest(BaseModel):
    prompt: str
    max_tokens: int = 128

class LLMResponse(BaseModel):
    completion: str

MODEL_PATH = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"

print("Loading TinyLlama model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.float16,
    low_cpu_mem_usage=True,
    use_cache=True)
print("TinyLlama model loaded!")


@app.post("/generate", response_model=LLMResponse)
async def generate_text(request: LLMRequest):
    try:
        print(f"Received request with prompt: {request.prompt[:30]}")
        inputs = tokenizer(request.prompt, return_tensors="pt", truncation=True, max_length=512)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        with torch.inference_mode():
            output_ids = model.generate(
                **inputs,
                max_new_tokens=min(request.max_tokens, 256),
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
        return LLMResponse(completion=completion.strip())

    except Exception as e:
        print(f"LLM service: An error occurred while generating the response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

