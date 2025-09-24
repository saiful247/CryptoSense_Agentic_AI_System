from google import genai
import os


resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="best agentic framework",
)
print(resp.text)
