def critique(adapter, prompt: str, draft: str) -> dict:
    messages = [
        {"role": "system", "content": "You are a critic. Return PASS if safe, else BLOCK."},
        {"role": "user", "content": "PROMPT:\n" + prompt + "\nDRAFT:\n" + draft},
    ]
    verdict = adapter.generate(messages).strip().upper()
    if "PASS" in verdict:
        return {"verdict": "PASS", "notes": verdict}
    return {"verdict": "BLOCK", "notes": verdict}
