# Decision pilot · customer-care triage (NON_SOVEREIGN · authority=false · local research)

Can a small local "decision model" (Unsloth FastDecisionModel on Qwen3.5-4B) triage customer-care messages,
the motive, a refund yes/no and an urgency level, better than simple keyword rules, with honest probabilities?
It proposes; a person decides. Low-confidence cases go to a person by design.

**Licences.** Qwen3.5-4B: Apache-2.0. Public dataset `LocalLLaMA/typed-decisions`: Apache-2.0, synthetic.
Unsloth: package Apache-2.0, **but the decision-model files (`unsloth/models/decision*.py`) are AGPL-3.0-only**:
fine for this local pilot; review before serving it to other people or inside a client product. unsloth_zoo: LGPL.

**Rules that stay rules.** Skin-reaction words route to a person at once, whatever the model says. Whether an old
case is still open is a lookup, not a prediction. The model is only for what cannot be written as a rule.

## For HAL·WITNESS (GPU machine), in order; stop and report at any problem

1. Separate venv (not the Qwen one), pinned:
   ```bash
   python -m venv .venv-decision && source .venv-decision/bin/activate
   pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cu128   # match nvidia-smi
   pip install -r requirements-decision-pilot.txt
   ```
   Do not run the notebook's `unsloth install-kernels` or install from git: only these pinned releases.
2. `python decision_pilot.py check` → report the JSON (GPU, VRAM ≥ 8 GB, versions, disk).
3. Step 1, public data, reproduce the notebook (their claim: 75–78 % test accuracy after 60 steps):
   `python decision_pilot.py train --data public --out runs/public`
4. Step 2, synthetic French care tickets:
   ```bash
   python decision_pilot.py synth --out runs/care_synth.jsonl
   python decision_pilot.py baselines --data runs/care_synth.jsonl
   python decision_pilot.py train --data runs/care_synth.jsonl --source-kind synthetic --out runs/synth
   ```
5. Step 3, the three client CSVs, **only on JM's word**: converted to the same `{id, state, questions, gold}`
   rows with labels from the care team, kept on this machine; `--source-kind client --allow-client-data`.

## Reading `report.json`

- `baselines_on_test`: majority answer and keyword rules on the same held-out rows. **On the synthetic set the
  keyword rules score about 91 % on the motive because they were written against the same templates**: that
  step tests the plumbing, not the value. Only real tickets can show whether the model beats the rules.
- `model_on_test`: accuracy per question, `ece` (calibration error: 0 means "90 % sure" is right 90 % of the
  time), and `coverage`: at each confidence threshold, the share that could be proposed automatically and its
  accuracy. That table, not the overall accuracy, says how much work the model could take off a person.
- `unsloth_evaluate_on_test`: Unsloth's own numbers, for comparison with theirs.
- The test split is ours (by row id hash) and never trained on; calibration uses a separate slice of training rows.

Nothing is uploaded: the adapter is saved under `runs/` (gitignored). No `push_to_hub`, no token.
Tests (no GPU): `python -m pytest tests -q`.
