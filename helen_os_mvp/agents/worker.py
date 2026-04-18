def do_work(adapter, prompt: str, plan: str) -> str:
    messages = [
        {"role": "system", "content": "You are a worker. Produce the draft solution."},
        {"role": "system", "content": "Plan: " + plan},
        {"role": "user", "content": prompt},
    ]
    return adapter.generate(messages)
