from typing import Dict, Any, List
from .adapters import LLMAdapter

class HAL:
    """
    HAL (Higher-level Adversarial Layer).
    Responsible for vetting proposals and ensuring determinism.
    """
    def __init__(self, adapter: LLMAdapter):
        self.adapter = adapter

    def review(self, proposal: Dict[str, Any], context: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Produce a HAL verdict (PASS, WARN, BLOCK).
        """
        # In a real system, this would use specialized schemas.
        # Here we ask the adapter to provide a verdict in HAL format.
        prompt = f"""
        You are HAL. Review the following proposal:
        {proposal}
        
        Provide a verdict in JSON format:
        {{
            "verdict": "PASS" | "WARN" | "BLOCK",
            "reasons": ["List of sorted reasons"],
            "required_fixes": ["List of sorted fixes"],
            "mutations": []
        }}
        """
        
        response = self.adapter.generate(prompt, context)
        # Simple extraction logic for prototype
        import json
        try:
            # Look for JSON block
            if "{" in response:
                json_part = response[response.find("{"):response.rfind("}")+1]
                return json.loads(json_part)
        except:
            pass
            
        return {
            "verdict": "WARN",
            "reasons": ["MANUAL_REVIEW_REQUIRED"],
            "required_fixes": ["Ensure JSON compliance"],
            "mutations": []
        }
