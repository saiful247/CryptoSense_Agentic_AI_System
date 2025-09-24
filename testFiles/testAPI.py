from google import genai
import os

client = genai.Client(api_key="AIzaSyC_Qry3JDi01etv7ncMxQa8dLG480w-a_8")

resp = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="best agentic framework",
)
print(resp.text)
