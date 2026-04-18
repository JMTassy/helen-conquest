"""
HELEN OS Test Suite with Avatar Interface v1.0

Features:
- Mock Ollama server for testing
- Avatar personality system
- Interactive testing interface
- Full HELEN multi-model testing
"""

import asyncio
import json
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import time

# ============================================================================
# AVATAR SYSTEM
# ============================================================================

class AvatarPersonality(Enum):
    """Avatar personality styles"""
    ASSISTANT = "assistant"      # Helpful, professional
    CREATIVE = "creative"        # Imaginative, playful
    ANALYTICAL = "analytical"    # Data-driven, logical
    MENTOR = "mentor"            # Teaching, guiding
    EXPLORER = "explorer"        # Curious, adventurous


@dataclass
class AvatarStyle:
    """Avatar visual and behavioral style"""
    name: str
    emoji: str
    greeting: str
    color: str
    personality: AvatarPersonality
    response_prefix: str
    thinking_phrase: str


class AvatarRegistry:
    """Collection of avatar personalities"""

    AVATARS = {
        "helen": AvatarStyle(
            name="HELEN",
            emoji="🧠",
            greeting="Hello! I'm HELEN, your multi-model AI companion.",
            color="\033[94m",  # Blue
            personality=AvatarPersonality.ASSISTANT,
            response_prefix="HELEN says:",
            thinking_phrase="HELEN is thinking...",
        ),
        "claude": AvatarStyle(
            name="Claude",
            emoji="🤖",
            greeting="Hi! I'm Claude, a helpful AI assistant.",
            color="\033[92m",  # Green
            personality=AvatarPersonality.ANALYTICAL,
            response_prefix="Claude:",
            thinking_phrase="Claude is analyzing...",
        ),
        "sage": AvatarStyle(
            name="Sage",
            emoji="🧙",
            greeting="Greetings, seeker of knowledge.",
            color="\033[95m",  # Magenta
            personality=AvatarPersonality.MENTOR,
            response_prefix="Sage whispers:",
            thinking_phrase="Sage contemplates...",
        ),
        "spark": AvatarStyle(
            name="Spark",
            emoji="⚡",
            greeting="Hey there! Ready for some creative exploration?",
            color="\033[93m",  # Yellow
            personality=AvatarPersonality.CREATIVE,
            response_prefix="Spark exclaims:",
            thinking_phrase="Spark is imagining...",
        ),
    }

    @classmethod
    def get_avatar(cls, name: str) -> AvatarStyle:
        """Get avatar by name"""
        return cls.AVATARS.get(name.lower(), cls.AVATARS["helen"])

    @classmethod
    def list_avatars(cls) -> Dict[str, str]:
        """List all available avatars"""
        return {
            name: f"{style.emoji} {style.name} - {style.greeting}"
            for name, style in cls.AVATARS.items()
        }


# ============================================================================
# MOCK OLLAMA SERVER
# ============================================================================

class MockOllamaServer:
    """Mock Ollama server for testing (simulates local LLM responses)"""

    def __init__(self):
        self.models = ["llama2", "mistral", "neural-chat"]
        self.request_count = 0
        self.token_count = 0
        self.latency_ms = 50  # Simulated latency

    def generate(self, model: str, prompt: str) -> Dict[str, Any]:
        """Simulate model generation"""
        self.request_count += 1

        # Simulate different models
        if model == "llama2":
            response = self._llama2_response(prompt)
        elif model == "mistral":
            response = self._mistral_response(prompt)
        elif model == "neural-chat":
            response = self._neural_chat_response(prompt)
        else:
            response = "I don't recognize that model."

        # Count tokens (rough estimate: ~4 chars per token)
        tokens = len(response) // 4
        self.token_count += tokens

        return {
            "model": model,
            "response": response,
            "tokens_used": tokens,
            "latency_ms": self.latency_ms,
            "timestamp": datetime.now().isoformat(),
        }

    def _llama2_response(self, prompt: str) -> str:
        """Generate Llama 2 style response"""
        responses = {
            "what": "Llama 2 is a large language model developed by Meta. It's trained on 2 trillion tokens of data and optimized for dialogue use cases.",
            "python": "Here's a simple Python function:\n\ndef hello_world():\n    print('Hello, World!')\n\nhello_world()  # Output: Hello, World!",
            "explain": "I'll break this down into key points: First, understand the fundamental concepts. Second, see how they relate. Third, apply them to your situation.",
            "default": "That's an interesting question! Let me think about that... Based on my training data, I can provide some helpful insights on this topic.",
        }

        for key in responses:
            if key.lower() in prompt.lower():
                return responses[key]
        return responses["default"]

    def _mistral_response(self, prompt: str) -> str:
        """Generate Mistral style response"""
        responses = {
            "code": "Let me provide a clean, efficient code example:\n\n```python\ndef solve(x):\n    return x * 2 + 1\n```\n\nThis solves the problem elegantly.",
            "math": "The solution is calculated as follows:\n1 + 1 = 2\n\nThis is fundamental arithmetic.",
            "explain": "The key insight is to break complex problems into simpler parts. Here are the main steps...",
            "default": "I'm Mistral, a capable language model. Your question is interesting, and here's what I can tell you...",
        }

        for key in responses:
            if key.lower() in prompt.lower():
                return responses[key]
        return responses["default"]

    def _neural_chat_response(self, prompt: str) -> str:
        """Generate Neural Chat style response"""
        responses = {
            "hi": "Hello! I'm Neural Chat, optimized for conversational interactions. How can I help you today?",
            "help": "I'm here to help! I can answer questions, explain concepts, write code, or have a friendly chat.",
            "creative": "Let me be creative about this: Imagine a world where AI and humans work together seamlessly...",
            "default": "That's a great question! Let me provide you with a thoughtful response based on my training.",
        }

        for key in responses:
            if key.lower() in prompt.lower():
                return responses[key]
        return responses["default"]

    def list_models(self) -> list:
        """List available models"""
        return self.models

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics"""
        return {
            "requests": self.request_count,
            "tokens": self.token_count,
            "models": self.models,
            "uptime": "running",
        }


# ============================================================================
# HELEN TEST INTERFACE
# ============================================================================

class HELENTestInterface:
    """Complete test interface with avatar support"""

    def __init__(self, avatar_name: str = "helen"):
        self.avatar = AvatarRegistry.get_avatar(avatar_name)
        self.ollama = MockOllamaServer()
        self.conversation_history = []
        self.current_model = "llama2"

        print(f"\n{self.avatar.color}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║                                                                ║")
        print(f"║          {self.avatar.emoji}  HELEN OS TEST SUITE WITH AVATAR  {self.avatar.emoji}         ║")
        print("║                                                                ║")
        print("║               Testing Multi-Model + Ollama Integration         ║")
        print("║                                                                ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        print(f"\033[0m\n")

        print(f"{self.avatar.color}{self.avatar.emoji} {self.avatar.greeting}\033[0m\n")

    def print_header(self, title: str) -> None:
        """Print section header"""
        print(f"\n{self.avatar.color}{'=' * 70}")
        print(f"  {self.avatar.emoji}  {title}")
        print(f"{'=' * 70}\033[0m\n")

    def test_ollama_connection(self) -> bool:
        """Test Ollama connection"""
        self.print_header("Testing Ollama Connection")

        try:
            models = self.ollama.list_models()
            print(f"✅ Ollama Mock Server Running")
            print(f"   Available models: {', '.join(models)}")
            print(f"   Status: Operational")
            return True
        except Exception as e:
            print(f"❌ Ollama connection failed: {e}")
            return False

    def test_model_generation(self) -> None:
        """Test model generation"""
        self.print_header("Testing Model Generation")

        test_prompts = [
            ("What is Python?", "llama2"),
            ("Write a Python function", "mistral"),
            ("Hello, how are you?", "neural-chat"),
        ]

        for prompt, model in test_prompts:
            print(f"\n📝 Prompt: {prompt}")
            print(f"   Model: {model}")
            print(f"   {self.avatar.thinking_phrase}")

            # Simulate thinking time
            time.sleep(0.5)

            response = self.ollama.generate(model, prompt)

            print(f"\n{self.avatar.color}{self.avatar.response_prefix}\033[0m")
            print(f"   {response['response'][:100]}..." if len(response['response']) > 100 else f"   {response['response']}")
            print(f"\n   ⏱️  Latency: {response['latency_ms']}ms")
            print(f"   📊 Tokens: {response['tokens_used']}")

            self.conversation_history.append({
                "prompt": prompt,
                "model": model,
                "response": response["response"],
                "tokens": response["tokens_used"],
            })

    def test_intelligent_routing(self) -> None:
        """Test intelligent model routing"""
        self.print_header("Testing Intelligent Routing")

        from helen_multimodel_dispatcher_v1 import create_dispatcher, TaskType, TaskContext

        dispatcher = create_dispatcher()

        task_types = [
            TaskType.CODING,
            TaskType.REASONING,
            TaskType.CREATIVE,
            TaskType.CONVERSATION,
        ]

        print("Testing routing decisions by task type:\n")

        for task_type in task_types:
            task = TaskContext(task_type=task_type, query="test")
            decision = dispatcher.select_model(task)
            print(f"  {task_type.value.upper()}")
            print(f"    └─ Selected: {decision.model_config.name}")
            print(f"    └─ Reason: {decision.reason}")
            print(f"    └─ Confidence: {decision.confidence:.0%}\n")

    def test_avatar_personalities(self) -> None:
        """Test different avatar personalities"""
        self.print_header("Testing Avatar Personalities")

        print("Available avatars:\n")

        for avatar_name, description in AvatarRegistry.list_avatars().items():
            print(f"  {description}")

        print("\n" + "=" * 70 + "\n")

    def interactive_session(self) -> None:
        """Interactive conversation session"""
        self.print_header("Interactive Session")

        print(f"Commands:")
        print(f"  • Type your question or prompt")
        print(f"  • 'models' - List available models")
        print(f"  • 'switch <model>' - Switch model (llama2/mistral/neural-chat)")
        print(f"  • 'stats' - Show statistics")
        print(f"  • 'history' - Show conversation history")
        print(f"  • 'quit' - Exit\n")

        while True:
            try:
                reset_color = '\033[0m'
                user_input = input(f"\n{self.avatar.color}[You]{reset_color} > ").strip()

                if not user_input:
                    continue

                if user_input.lower() == "quit":
                    reset = '\033[0m'
                    print(f"\n{self.avatar.color}{self.avatar.emoji} Goodbye!{reset}\n")
                    break

                elif user_input.lower() == "models":
                    print(f"\nAvailable models: {', '.join(self.ollama.list_models())}")
                    print(f"Current model: {self.current_model}")

                elif user_input.lower().startswith("switch "):
                    model = user_input[7:].strip()
                    if model in self.ollama.list_models():
                        self.current_model = model
                        print(f"✅ Switched to {model}")
                    else:
                        print(f"❌ Model '{model}' not available")

                elif user_input.lower() == "stats":
                    stats = self.ollama.get_stats()
                    print(f"\n📊 Statistics:")
                    print(f"   Requests: {stats['requests']}")
                    print(f"   Tokens: {stats['tokens']}")
                    print(f"   Models: {', '.join(stats['models'])}")

                elif user_input.lower() == "history":
                    if not self.conversation_history:
                        print("No conversation history yet")
                    else:
                        print(f"\n📜 Conversation History ({len(self.conversation_history)} messages):\n")
                        for i, msg in enumerate(self.conversation_history, 1):
                            print(f"{i}. [{msg['model']}] {msg['prompt'][:50]}...")
                            print(f"   Response: {msg['response'][:70]}...\n")

                else:
                    # Process user input
                    print(f"{self.avatar.thinking_phrase}")
                    time.sleep(0.5)

                    response = self.ollama.generate(self.current_model, user_input)

                    reset = '\033[0m'
                    print(f"\n{self.avatar.color}{self.avatar.response_prefix}{reset}")
                    print(f"{response['response']}\n")
                    print(f"⏱️  {response['latency_ms']}ms | 📊 {response['tokens_used']} tokens")

                    self.conversation_history.append({
                        "prompt": user_input,
                        "model": self.current_model,
                        "response": response["response"],
                        "tokens": response["tokens_used"],
                    })

            except KeyboardInterrupt:
                reset2 = '\033[0m'
                print(f"\n\n{self.avatar.color}{self.avatar.emoji} Session ended.{reset2}\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def run_full_test_suite(self) -> None:
        """Run complete test suite"""
        self.test_ollama_connection()
        self.test_model_generation()
        self.test_intelligent_routing()
        self.test_avatar_personalities()

        print(f"\n{self.avatar.color}")
        print("╔════════════════════════════════════════════════════════════════╗")
        print("║                  ✅ ALL TESTS COMPLETED                       ║")
        print("╚════════════════════════════════════════════════════════════════╝")
        reset4 = '\033[0m'
        print(f"{reset4}\n")

        self.print_final_stats()

        # Ask if user wants interactive session
        response = input("Would you like to start an interactive session? (yes/no): ").strip().lower()
        if response in ["yes", "y"]:
            self.interactive_session()

    def print_final_stats(self) -> None:
        """Print final statistics"""
        stats = self.ollama.get_stats()

        reset3 = '\033[0m'
        print(f"{self.avatar.color}📊 Test Results:{reset3}\n")
        print(f"  Total API Requests: {stats['requests']}")
        print(f"  Total Tokens Generated: {stats['tokens']}")
        print(f"  Conversation Messages: {len(self.conversation_history)}")
        print(f"  Avg Tokens per Request: {stats['tokens'] // max(1, stats['requests'])}")
        print()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Run HELEN OS test suite"""
    import sys

    # Get avatar from command line or use default
    avatar = sys.argv[1] if len(sys.argv) > 1 else "helen"

    # Create test interface
    test = HELENTestInterface(avatar)

    # Run tests
    test.run_full_test_suite()


if __name__ == "__main__":
    main()
