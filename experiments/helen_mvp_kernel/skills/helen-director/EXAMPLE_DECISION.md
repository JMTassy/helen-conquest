# Example: HELEN DIRECTOR applied to test_director_prompt.txt

Input:

```
I have too many branches: HELEN OS, math_to_face, Higgsfield video, CONQUEST, and research. What should I do today?
```

---

## Output (per SKILL.md output format)

```
DIRECTOR DECISION:
Ship the HELEN Director skill MVP today, before any further branch.

WHY:
None of the existing branches has a steering layer. Without a director, every new branch compounds the chaos. The Director is the smallest unblocker for all of them.

NEXT 3 STEPS:
1. Create skills/helen-director/SKILL.md (done — this file).
2. Run the skill on this exact test prompt and record the structured output.
3. Emit DIRECTOR_DECISION_RECEIPT_V1 to temple/subsandbox/director/<run_id>/.

RECEIPT REQUIRED:
DIRECTOR_DECISION_RECEIPT_V1

NEXT COMMAND:
test helen-director with test_director_prompt.txt
```

---

## Notes

- This is the bootstrapping case: the test prompt asks "what should I do today?", and the Director's answer is "build me, then ask me again."
- After this MVP exists, the same skill handles the same kind of overload prompt for any future "too many branches" moment.
- Math bridge (see `MATH_TO_DIRECTOR_BRIDGE.md`) is optional and not invoked here — pure prose decision is sufficient for a meta-decision about the system's own architecture.
