import os
import json
import requests
import hashlib
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class GatewayConfig:
    """Unified integration configuration."""
    backend: str = "ollama" # "ollama" or "claude"
    model: str = "mistral"
    api_key: Optional[str] = None
    base_url: str = "http://localhost:11434"
    max_tokens: int = 2000
    temperature: float = 0.7

class CTGateway:
    """Unified Gateway for ORACLE Town CT (Creative Town)."""

    def __init__(self, config: Optional[GatewayConfig] = None):
        if config is None:
            config = GatewayConfig()
        self.config = config
        self.cycle_count = 0

    def generate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        self.cycle_count += 1
        prompt = self._build_prompt(context)

        if self.config.backend == "claude":
            return self._query_claude(prompt, context)
        else:
            return self._query_ollama(prompt, context)

    def _query_claude(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        import anthropic
        api_key = self.config.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not set"}
        
        client = anthropic.Anthropic(api_key=api_key)
        try:
            message = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            return self._parse_response(response_text, context, self.config.model)
        except Exception as e:
            return {"error": f"Claude API error: {e}"}

    def _query_ollama(self, prompt: str, context: Dict[str, Any]) -> Dict[str, Any]:
        try:
            response = requests.post(
                f"{self.config.base_url}/api/chat",
                json={
                    "model": self.config.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False
                },
                timeout=120
            )
            response.raise_for_status()
            response_text = response.json().get("message", {}).get("content", "")
            return self._parse_response(response_text, context, self.config.model)
        except Exception as e:
            return {"error": f"Ollama error: {e}"}

    def _parse_response(self, text: str, context: Dict[str, Any], model: str) -> Dict[str, Any]:
        try:
            # Simple cleanup for potential markdown blocks
            clean_text = text.strip()
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:-3].strip()
            elif clean_text.startswith("```"):
                clean_text = clean_text[3:-3].strip()
                
            response_json = json.loads(clean_text)
            response_json["metadata"] = {
                "cycle": self.cycle_count,
                "model": model,
                "context": {
                    "last_decision": context.get("last_decision"),
                    "blocking_reasons": context.get("blocking_reasons", []),
                    "required_obligations": context.get("required_obligations", [])
                }
            }
            return response_json
        except json.JSONDecodeError as e:
            return {"error": f"Invalid JSON: {e}", "raw": text}

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        # Borrowed logic from original ct_gateway_claude.py
        last_decision = context.get("last_decision", "INITIAL")
        blocking_reasons = context.get("blocking_reasons", [])
        required_obligations = context.get("required_obligations", [])
        cycle_number = context.get("cycle_number", self.cycle_count)

        context_str = ""
        if last_decision != "INITIAL":
            context_str += f"Previous Decision: {last_decision}\n"
        if blocking_reasons:
            context_str += f"Blocking Reasons: {', '.join(blocking_reasons)}\n"
        if required_obligations:
            context_str += f"Required Obligations: {', '.join(required_obligations)}\n"

        return f"""You are a creative software engineer proposing code improvements.
Cycle: {cycle_number}
{context_str}
---
Generate a JSON object with exactly these keys:
1. "proposal_bundle": {{"name": string, "description_hash": "sha256:..."}}
2. "patches": [{{"diff": unified_diff, "rationale": string}}]
3. "metadata": {{"reasoning": string}}

Constraints:
- Output ONLY valid JSON
- NO authority language (ship, approve, pass)
- Diffs must be in unified format (--- a/ +++ b/)
"""
