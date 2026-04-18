import os
from .kernel import GovernanceVM
from .memory import MemoryKernel
from .storage_run_trace import RunTrace
from .adapters import LLMAdapter
from .soul import HELEN_SYSTEM_PROMPT
from .wulmoji import WULmoji
from .weather import WeatherService
from .hal import HAL
from .districts import DistrictManager
from .streets import StreetManager
from .agents import Planner, Worker, Critic, Archivist
from .town.idempotence import IdempotenceManager
from typing import Dict, Any, List, Optional

class HELEN:
    """
    Cognitive OS (HELEN).
    Reflective, narrative-capable interface layer.
    """
    def __init__(self, kernel: GovernanceVM, memory: MemoryKernel, adapter: LLMAdapter):
        self.kernel = kernel
        self.memory = memory
        self.adapter = adapter
        self.hal = HAL(adapter)
        self.districts = DistrictManager()
        self.streets = StreetManager()

        # Non-sovereign trace for CWL EMOGLYPH (narrative only)
        self.run_trace = RunTrace()

        # Initialize Agent Stack
        self.planner = Planner("Planner", adapter)
        self.worker = Worker("Worker", adapter)
        self.critic = Critic("Critic", adapter)
        self.archivist = Archivist("Archivist", adapter)
        self.idempotence = IdempotenceManager(
            index_path=os.path.join(os.path.dirname(kernel.ledger_path), "idempotence_index_v1.ndjson")
        )

        # Default session context
        self.current_district = "oracle_town"
        self.current_street = "marketing"
        self.location = "San Francisco"

    def speak(self, user_message: str) -> str:
        # 1. Access Context
        weather = WeatherService.get_weather(self.location)
        district = self.districts.get_district(self.current_district)
        street = self.streets.get_street(self.current_street)

        # 2. Access Memory (non-sovereign facts only)
        history = self.memory.get_history()

        # Inject Identity & Context as System Message
        context_str = f"\n{district.get_context()}\n{street.get_context()}\nExternal Weather: {weather['display']}"
        context = [{"metadata": {"role": "system"}, "content": HELEN_SYSTEM_PROMPT + context_str}] + history

        # 3. Reflection Logic using LLM Adapter
        her_response = self.adapter.generate(user_message, context)

        # 4. HAL Review (Informational telemetry, NOT binding)
        hal_verdict = self.hal.review({"type": "chat", "content": her_response}, context)

        # 5. Format Output (WULmoji Header)
        status_color = WULmoji.get_color_for_status("success")  # Default
        if hal_verdict.get("verdict") == "BLOCK":
            status_color = WULmoji.CRITICAL
        elif hal_verdict.get("verdict") == "WARN":
            status_color = WULmoji.WARNING

        header = WULmoji.header(status_color)

        formatted_output = f"""{header}

[HER]
{her_response}

[WEATHER_CONTEXT]
📍 {weather['display']}
🌡️ Condition: {weather['condition_emoji']} {WeatherService.get_risk_color(weather['condition_emoji'])}

[HAL - Informational Telemetry Only]
- Verdict: {hal_verdict.get('verdict', 'UNKNOWN')}
- Reasons: {', '.join(hal_verdict.get('reasons', []))}
- Checks: {'Determinism Check Passed' if hal_verdict.get('verdict') != 'BLOCK' else 'Action Not Recommended'}
"""

        # 6. Log to Memory (non-sovereign facts only, NO hal_verdict here)
        self.memory.add_fact(
            key="user_input",
            value=user_message,
            actor="user",
            status="OBSERVED"
        )
        self.memory.add_fact(
            key="helen_response",
            value=her_response,
            actor="helen",
            status="CONFIRMED"
        )

        # 7. Log to RunTrace (aesthetic/telemetry, non-authoritative)
        self.run_trace.log_hal_verdict(hal_verdict, context="chat_reflection")

        return formatted_output

    def run_task(self, task_description: str) -> Dict[str, Any]:
        """Runs a structured task through the Agent pipeline (non-sovereign)."""
        # 1. Idempotence Check
        input_hash = self.idempotence.compute_input_hash(task_description, "task_execution", {"district": self.current_district})
        reservation = self.idempotence.reserve_input(input_hash)
        if not reservation["reserved"]:
            return {
                "status": "idempotent_hit",
                "message": "Task already processed.",
                "outcome": reservation["existing_outcome"]
            }

        # 2. Access Context
        weather = WeatherService.get_weather(self.location)
        district = self.districts.get_district(self.current_district)
        street = self.streets.get_street(self.current_street)

        context_str = f"\n{district.get_context()}\n{street.get_context()}\nExternal Weather: {weather['display']}"
        full_system_prompt = HELEN_SYSTEM_PROMPT + context_str

        # 3. Logic (Planner -> Worker -> Critic -> Archivist)
        self.kernel.propose({"type": "tool_call_v1", "tool_name": "Planner", "input": task_description})
        plan = self.planner.generate(task_description, full_system_prompt)
        self.kernel.propose({"type": "tool_result_v1", "tool_name": "Planner", "result_summary": plan[:100]})

        self.kernel.propose({"type": "tool_call_v1", "tool_name": "Worker", "input": plan})
        draft = self.worker.generate(task_description, plan)
        self.kernel.propose({"type": "tool_result_v1", "tool_name": "Worker", "result_summary": draft[:100]})

        self.kernel.propose({"type": "tool_call_v1", "tool_name": "Critic", "input": draft})
        feedback = self.critic.generate(draft, plan)
        self.kernel.propose({"type": "tool_result_v1", "tool_name": "Critic", "result_summary": feedback[:100]})

        self.kernel.propose({"type": "tool_call_v1", "tool_name": "Archivist", "input": feedback})
        final_artifact = self.archivist.generate(draft, feedback)
        self.kernel.propose({"type": "tool_result_v1", "tool_name": "Archivist", "result_summary": final_artifact[:100]})

        # 4. Log facts to memory (non-sovereign)
        self.memory.add_fact(
            key="task_input",
            value=task_description,
            actor="user",
            status="OBSERVED"
        )
        self.memory.add_fact(
            key="task_artifact",
            value=final_artifact[:200],  # Summary only
            actor="helen",
            status="CONFIRMED"
        )

        # 5. HAL Review (informational telemetry)
        proposal = {
            "type": "task_execution",
            "task": task_description,
            "input_hash": input_hash,
            "artifact_summary": final_artifact[:100],
            "district": self.current_district,
            "street": self.current_street,
            "weather": weather
        }
        context = [{"metadata": {"role": "system"}, "content": full_system_prompt}]
        hal_verdict = self.hal.review(proposal, context)

        # Log verdict to run_trace (telemetry, NOT binding)
        self.run_trace.log_hal_verdict(hal_verdict, context="task_execution")

        # 6. Kernel proposal (verdict is informational)
        receipt = self.kernel.propose(proposal, verdict="submitted")  # Non-sovereign verdict

        # 7. Finalize Idempotence
        self.idempotence.finalize_input(input_hash, {
            "seq": receipt.seq,
            "hash": receipt.payload_hash,
            "timestamp": receipt.timestamp
        })

        return {
            "plan": plan,
            "artifact": final_artifact,
            "hal_telemetry": hal_verdict,  # Renamed from hal_verdict to clarify non-sovereign status
            "receipt": receipt,
            "message": f"Task '{task_description}' processed (logged to memory and run_trace)."
        }

