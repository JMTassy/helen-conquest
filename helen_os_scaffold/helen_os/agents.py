from typing import List, Dict, Any
from .adapters import LLMAdapter

class Agent:
    def __init__(self, name: str, adapter: LLMAdapter):
        self.name = name
        self.adapter = adapter

class Planner(Agent):
    def generate(self, task: str, context: str) -> List[str]:
        prompt = f"Plan for task: {task}\nContext: {context}\nReturn a simple list of steps."
        response = self.adapter.generate(prompt, [])
        return [s.strip() for s in response.split("\n") if s.strip()]

class Worker(Agent):
    def generate(self, task: str, plan: List[str]) -> str:
        prompt = f"Execute task: {task}\nPlan: {plan}\nProvide a draft."
        return self.adapter.generate(prompt, [])

class Critic(Agent):
    def generate(self, draft: str, plan: List[str]) -> str:
        prompt = f"Critique this draft based on the plan: {plan}\nDraft: {draft}"
        return self.adapter.generate(prompt, [])

class Archivist(Agent):
    def generate(self, draft: str, feedback: str) -> str:
        prompt = f"Synthesize final artifact.\nDraft: {draft}\nFeedback: {feedback}"
        return self.adapter.generate(prompt, [])
