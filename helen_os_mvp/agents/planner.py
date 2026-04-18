def plan_task(adapter, prompt: str) -> str:
    messages = [
        {"role": "system", "content": "You are a planner. Return a short ordered plan."},
        {"role": "user", "content": prompt},
    ]
    return adapter.generate(messages)
