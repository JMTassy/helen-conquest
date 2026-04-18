import json
import os
import urllib.request
import urllib.error
from typing import List, Dict


class OpenAIAdapter:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        self.base = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def generate(self, messages: List[Dict], temperature: float = 0.2) -> str:
        if not self.api_key:
            return "[OPENAI_API_KEY not set]"
        url = self.base.rstrip("/") + "/responses"
        payload = {
            "model": self.model,
            "input": messages,
            "temperature": temperature,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # Responses API: output_text is at top-level sometimes; fallback to first output
            if "output_text" in data:
                return data.get("output_text", "")
            outputs = data.get("output", [])
            if outputs and "content" in outputs[0]:
                parts = outputs[0].get("content", [])
                if parts and "text" in parts[0]:
                    return parts[0].get("text", "")
            return ""
        except urllib.error.HTTPError as e:
            return f"[OpenAI HTTP {e.code}] {e.reason}"
        except Exception as e:
            return f"[OpenAI error] {e}"
