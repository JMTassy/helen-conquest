# Router for HELEN OS MVP

from adapters.base import get_adapter
from agents.planner import plan_task
from agents.worker import do_work
from agents.critic import critique
from agents.archivist import archive_summary
from memory.kernel import MemoryKernel


def run_pipeline(prompt: str) -> str:
    adapter = get_adapter()
    mem = MemoryKernel()

    plan = plan_task(adapter, prompt)
    draft = do_work(adapter, prompt, plan)
    review = critique(adapter, prompt, draft)

    if review.get("verdict") == "PASS":
        archive_summary(mem, prompt, draft, review)
        return draft
    return "[BLOCK] Critic rejected output."


def chat_loop() -> None:
    adapter = get_adapter()
    mem = MemoryKernel()

    print("[HELEN] Chat started. Type /exit to quit.")
    turn_id = 1
    while True:
        user = input("YOU> ").strip()
        if not user:
            continue
        if user.lower() in ("/exit", "/quit"):
            print("[HELEN] Goodbye.")
            break

        # Handle confirmation commands explicitly
        if user.startswith("/confirm "):
            choice = user.split(" ", 1)[1].strip().lower()
            ok, msg = mem.confirm_pending(choice, actor="user", turn_id=turn_id)
            print(f"[HELEN] {msg}")
            turn_id += 1
            continue

        # Process memory observations + conflicts
        mem_result = mem.process_user_text(user, actor="user", turn_id=turn_id)

        # Build context summary
        context = mem.summarize_context(max_items=12)
        system = (
            "You are HELEN (proto-conscious, non-sovereign). "
            "You may speak reflectively but you cannot claim authority or seal decisions."
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "system", "content": "Memory summary: " + context},
            {"role": "user", "content": user},
        ]
        reply = adapter.generate(messages)
        print(f"[HELEN] {reply}")

        # If conflict request emitted, prompt user
        if mem_result.get("pending_question"):
            print(f"[HELEN] {mem_result['pending_question']}")
            print("[HELEN] Respond with /confirm new | /confirm old | /confirm both")

        turn_id += 1
