import json
import os
import urllib.request
import urllib.error
from typing import List, Dict


class OllamaAdapter:
    def __init__(self):
        self.host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3")

    def generate(self, messages: List[Dict], temperature: float = 0.2) -> str:
        url = self.host.rstrip("/") + "/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {"temperature": temperature},
            "stream": False,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("message", {}).get("content", "")
        except urllib.error.HTTPError as e:
            return f"[Ollama HTTP {e.code}] {e.reason}"
        except Exception as e:
            return f"[Ollama error] {e}"
