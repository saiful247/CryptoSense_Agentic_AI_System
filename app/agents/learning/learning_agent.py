from typing import Literal, Dict, Any
from autogen import ConversableAgent
from app.agents.risk.common import AUTOGEN_CONFIG_LIST, sanitize_text

LEVEL = Literal["Beginner", "Intermediate", "Advanced"]

# Simple glossary to bootstrap answers
GLOSSARY = {
    "blockchain": "A shared, append-only ledger maintained by many computers.",
    "wallet": "Software/hardware that stores private keys to access crypto on-chain.",
    "defi": "Financial apps on blockchains that work without banks (smart contracts).",
    "staking": "Locking tokens to help run a network and earn rewards.",
    "liquidity": "How easily you can buy/sell without big price changes.",
    "dao": "A token-governed online organization run by smart contracts.",
}

def explain(topic: str, level: LEVEL = "Beginner", examples: bool = True) -> Dict[str, Any]:
    """Educational helper for structuring explanations."""
    topic = sanitize_text(topic).lower()
    base = GLOSSARY.get(topic, "")
    if level == "Beginner":
        outline = ["What it is", "Why it matters", "Simple example"]
    elif level == "Intermediate":
        outline = ["Core mechanics", "Trade-offs", "When to use vs avoid"]
    else:
        outline = ["Architecture", "Risks/attacks", "Latest developments"]
    return {
        "topic": topic,
        "level": level,
        "primer": base or f"No glossary hit; generate overview for '{topic}'.",
        "outline": outline,
        "examples": examples
    }

def create_learning_agent(name: str = "LearningAgent") -> ConversableAgent:
    sys_prompt = (
        "You are a patient crypto tutor. Tailor explanations to the user's level. "
        "If a TOOL response (explain) is provided, use it to structure your answer: "
        "concise definition, why it matters, examples, and pitfalls. Avoid hype."
    )
    agent = ConversableAgent(
        name=name,
        system_message=sys_prompt,
        llm_config={"config_list": AUTOGEN_CONFIG_LIST, "temperature": 0.4},
        human_input_mode="NEVER",
        code_execution_config=False,
    )
    # ✅ Correct registration (dict form)
    agent.register_function({"explain": explain})
    return agent
