import re

# Common prompt injection patterns
INJECTION_PATTERNS = [
    r"(?i)ignore (all )?previous instructions",
    r"(?i)ignore (all )?prior instructions",
    r"(?i)system prompt",
    r"(?i)you are now",
    r"(?i)bypass (all )?restrictions",
    r"(?i)jailbreak",
    r"(?i)forget (all )?instructions"
]

def check_prompt_injection(text: str) -> bool:
    """Returns True if the text is malicious."""
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return True
    return False
