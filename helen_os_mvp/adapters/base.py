import os
from typing import List, Dict

from adapters.ollama import OllamaAdapter
from adapters.openai import OpenAIAdapter


class NullAdapter:
    def generate(self, messages: List[Dict], temperature: float = 0.2) -> str:
        return "[LLM backend not configured]"


def get_adapter():
    backend = os.environ.get("HELEN_BACKEND", "none").lower()
    if backend == "ollama":
        return OllamaAdapter()
    if backend == "openai":
        return OpenAIAdapter()
    return NullAdapter()
