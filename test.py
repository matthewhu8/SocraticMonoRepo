from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import os

response = client.chat.completions.create(model="gpt-3.5-turbo",
messages=[{"role": "user", "content": "Hello, world!"}])
print(response.choices[0].message.content)
