import re
from typing import Any, Union, Dict, List

# Common patterns for secrets
SECRET_PATTERNS = [
    (r"(?i)api_key[\"']?[:\s]+[\"']?([a-zA-Z0-9_\-]{16,})[\"']?", "api_key: [REDACTED]"),
    (r"(?i)bearer\s+([a-zA-Z0-9_\-\.]{16,})", "Bearer [REDACTED]"),
    (r"(?i)password[\"']?[:\s]+[\"']?([^\s\"']{4,})[\"']?", "password: [REDACTED]"),
    (r"(?i)sk-[a-zA-Z0-9]{20,}", "[OPENAI_KEY_REDACTED]")
]

def redact_secrets(content: Union[str, Dict, List]) -> Any:
    """
    Recursively redacts secrets from strings, dicts, and lists.
    """
    if isinstance(content, str):
        sanitized = content
        for pattern, replacement in SECRET_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized)
        return sanitized
    
    if isinstance(content, dict):
        return {k: redact_secrets(v) for k, v in content.items()}
    
    if isinstance(content, list):
        return [redact_secrets(item) for item in content]
    
    return content
