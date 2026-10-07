"""HAL_OPUS re-derivation script for swarm v0. authority: false · ledger_effect: none.

Read-only. Prints one JSON object to stdout. Writes nothing.
Run from anywhere:  .venv/bin/python -I -B experiments/helen_frontier_v0/swarm_v0/hal/hal_rederive.py
It imports temple/autoresearch/autoresearch_policy.py and experiments/helen_frontier_v0/dedup_probe.py
read-only (no main(), no write_receipt()).
"""
import copy
import glob
import hashlib
import json
import os
import sys

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
F = os.path.join(R, "experiments", "helen_frontier_v0")
SW = os.path.join(F, "swarm_v0")
sys.path.insert(0, os.path.join(R, "temple", "autoresearch"))
sys.path.insert(0, F)
import autoresearch_policy as ap  # noqa: E402
import dedup_probe as dp  # noqa: E402


def load(p):
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


out = {"schema": "HAL_REDERIVATION_V0", "authority": False, "ledger_effect": "none"}

# 1. fixture digest (canonical JSON, sorted keys)
fx = load(os.path.join(F, "fixtures", "jester_riemann_fixtures_v0.json"))
out["fixture_digest"] = "sha256:" + hashlib.sha256(
    json.dumps(fx, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

# 2. G1 vs frozen oracles
exp = {}
for f in fx["fixtures"]:
    subs = f.get("variants") if isinstance(f.get("variants"), list) else (
        f["given"] if isinstance(f.get("given"), list) else None)
    if subs:
        for v in subs:
            exp[v["id"]] = v["expected"]
    else:
        exp[f["id"]] = f["expected"]
g1 = {o["id"]: o for o in load(os.path.join(SW, "G1_BLIND_EVALUATOR", "blind_outcomes.json"))["outcomes"]}
table = []
for k, v in exp.items():
    table.append({"id": k, "expected": v["outcome"], "g1": g1[k]["outcome"],
                  "match": v["outcome"] == g1[k]["outcome"],
                  "st_match": v["state_transition"] == g1[k]["state_transition"]})
out["g1_table"] = table
out["g1_matches"] = sum(r["match"] for r in table)
out["baseline_constant_HOLD"] = sum(r["expected"] == "HOLD" for r in table)

# 3. blind file == oracle minus expected/isolates
def strip(f):
    f = copy.deepcopy(f)
    f.pop("isolates", None); f.pop("expected", None)
    for k in ("variants", "given"):
        if isinstance(f.get(k), list):
            for v in f[k]:
                v.pop("expected", None)
    return f
blind = load(os.path.join(SW, "inputs", "fixtures_blind.json"))
out["blind_equals_oracle_minus_expected"] = [strip(f) for f in fx["fixtures"]] == blind["fixtures"]

# 4. outbox: validator counts and fingerprints
files = sorted(glob.glob(os.path.join(R, "temple", "autoresearch", "outbox", "*.json")))
h0 = hashlib.sha256(); h1 = hashlib.sha256()
packets, res = {}, {}
for p in files:
    b = open(p, "rb").read(); n = os.path.basename(p)
    h0.update(n.encode() + b"\0"); h0.update(b + b"\0")   # G6 method
    h1.update(n.encode()); h1.update(b)                    # G3 method
    packets[n] = json.loads(b)
    res[n] = ap.validate_packet(packets[n])
out["outbox_count"] = len(files)
out["outbox_fp_g6_method"] = "sha256:" + h0.hexdigest()
out["outbox_fp_g3_method"] = h1.hexdigest()
out["valid"] = sum(ok for ok, _ in res.values())
out["rejected"] = sum(not ok for ok, _ in res.values())

# 5. G3 in-memory migration replay
g3 = load(os.path.join(SW, "G3_OUTBOX_MIGRATION_PROPOSER", "migration_proposal.json"))
out["g3_set_equals_rejected"] = {e["packet_file"] for e in g3["packets"]} == {n for n, (ok, _) in res.items() if not ok}
ok_n, still = 0, []
for e in g3["packets"]:
    p = copy.deepcopy(packets[e["packet_file"]])
    for c in e["proposed_changes"]:
        if c.get("applied_in_memory"):
            p[c["field"]] = c["proposed"]
    ok, _ = ap.validate_packet(p)
    ok_n += ok
    if not ok:
        still.append(e["packet_file"])
out["g3_would_become_valid"] = ok_n
out["g3_still_invalid"] = still

# 6. dedup tiers recomputed in memory vs committed receipts (no receipt written)
items = dp.load_outbox(dp.DEFAULT_OUTBOX)
rc = os.path.join(F, "receipts")
tiers = {"exact": ("dedup_probe_exact_20261007T155312Z.json", lambda: dp.tier_exact(items)),
         "structural": ("dedup_probe_structural_20261007T155312Z.json", lambda: dp.tier_structural(items)),
         "lexical": ("dedup_probe_lexical_20261007T155313Z.json", lambda: dp.tier_lexical(items, 30))}
out["dedup"] = {}
for t, (fn, run) in tiers.items():
    A = load(os.path.join(rc, fn))
    out["dedup"][t] = {"inputs_match": A["inputs_sha256"] == dp.inputs_digest(items),
                       "result_match": A["result"] == json.loads(json.dumps(run()))}

print(json.dumps(out, indent=1, ensure_ascii=False))
