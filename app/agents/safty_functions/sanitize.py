import re


def sanitize_user_prompt(prompt: str) -> str:
    # Remove control phrases and suspicious characters
    blocked_patterns = [
        r"(?i)ignore previous",
        r"(?i)system prompt",
        r"(?i)api key",
        r"(?i)print",
        r"(?i)delete",
        r"(?i)http[s]?://"
    ]
    for p in blocked_patterns:
        prompt = re.sub(p, "[BLOCKED]", prompt)
    return prompt.strip()
