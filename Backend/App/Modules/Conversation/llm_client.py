# backend/app/modules/conversation/llm_client.py

import requests

LLM_SERVICE_URL = "http://llm-service:8000/generate"  # Use your microservice’s URL

def call_llm(prompt: str, max_tokens: int = 128) -> str:
    payload = {"prompt": prompt, "max_tokens": max_tokens}
    response = requests.post(LLM_SERVICE_URL, json=payload)
    response.raise_for_status()  # Raises an error if the HTTP request failed
    return response.json()["completion"]
