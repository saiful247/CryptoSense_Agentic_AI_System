from autogen import ConversableAgent
import os
from dotenv import load_dotenv

load_dotenv()

config_list = [
    {
        # Use a valid Gemini model; adjust as needed (e.g., "gemini-1.5-pro")
        "model": "gemini-2.5-flash",
        "api_key": os.environ["GEMINI_API_KEY"],
        "api_type": "google"
    }
]

joke_agent = ConversableAgent(
    "joke_generation_agent",
    system_message="You are a helpful joke generation agent that creates funny and appropriate jokes.",
    llm_config={
        "config_list": config_list
    }
)

result = joke_agent.generate_reply(
    messages=[{"role": "user", "content": "Tell me a joke about AI."}]
)

print(result)
print("Final Result: ", result["content"])
