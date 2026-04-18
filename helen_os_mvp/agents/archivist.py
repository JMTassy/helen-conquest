from memory.kernel import MemoryKernel


def archive_summary(mem: MemoryKernel, prompt: str, draft: str, review: dict) -> None:
    summary = f"Task: {prompt}\nResult: {draft[:500]}"
    mem.append_observation(
        key="session.summary",
        value=summary,
        actor="assistant",
        status="OBSERVED",
        source={"turn_id": None, "message_id": None, "span": "archive"},
    )
