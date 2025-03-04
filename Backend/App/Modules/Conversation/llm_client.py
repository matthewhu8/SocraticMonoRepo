# backend/app/modules/conversation/llm_client.py

# import requests

# LLM_SERVICE_URL = "http://localhost:8001/generate"  # Updated for local development

# def call_llm(prompt: str, max_tokens: int = 128) -> str:
#     print(f"\n Now calling the LLM!")
#     payload = {"prompt": prompt, "max_tokens": max_tokens}
#     response = requests.post(LLM_SERVICE_URL, json=payload)
#     print(response)
#     response.raise_for_status()  # Raises an error if the HTTP request failed
#     return response.json()["completion"]

from openai import OpenAI
import os


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set your API key from an environment variable.

def call_llm(prompt: str) -> str:
    """
    Calls an external LLM API (OpenAI's GPT-3.5-turbo in this case)
    using the provided prompt, and returns the model's response.
    """
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=[
        # You can adjust the system message as needed.
        {"role": "system", "content": "You are a Socratic tutor that provides guiding hints without giving away the final answer."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=256,
    top_p=1.0,
    frequency_penalty=0,
    presence_penalty=0)
    # Return the generated text from the assistant's message.
    return response.choices[0].message.content.strip()
