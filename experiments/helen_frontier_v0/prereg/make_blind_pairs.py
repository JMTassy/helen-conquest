"""Build pairs_blind.json from G2's annotated pairs: ids and texts only. Pure, deterministic, read-only on the outbox."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PAIRS = REPO / "experiments/helen_frontier_v0/swarm_v0/G2_EQUIVALENCE_ANNOTATOR/equivalence_pairs.json"
OUTBOX = REPO / "temple/autoresearch/outbox"
OUT = HERE / "pairs_blind.json"
FIELDS = ("summary", "hypothesis", "title", "finding")
FORBIDDEN_KEYS = {"label", "justification", "a_snippet", "b_snippet"}


def packet_text(d: dict) -> str:
    for k in FIELDS:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return re.sub(r"\s+", " ", v).strip()
    return ""


def index_outbox() -> dict[str, str]:
    idx: dict[str, str] = {}
    for f in sorted(OUTBOX.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        t = packet_text(d)
        idx[f.stem] = t
        if d.get("packet_id"):
            idx[d["packet_id"]] = t
    return idx


def build() -> dict:
    pairs = json.loads(PAIRS.read_text(encoding="utf-8"))["pairs"]
    idx = index_outbox()
    blind = []
    for i, p in enumerate(pairs):
        ta, tb = idx.get(p["a"], ""), idx.get(p["b"], "")
        if not ta or not tb:
            raise SystemExit(f"pair {i}: unresolved text for {p['a']!r} or {p['b']!r}")
        blind.append({"pair_index": i, "a": p["a"], "b": p["b"], "a_text": ta, "b_text": tb})
    out = {"schema": "G2_PAIRS_BLIND_V0", "authority": False, "n_pairs": len(blind), "pairs": blind}
    txt = json.dumps(out, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert not (FORBIDDEN_KEYS & set(re.findall(r'"(\w+)":', txt))), "label leakage"
    out["blind_pairs_sha256"] = hashlib.sha256(txt.encode()).hexdigest()
    return out


if __name__ == "__main__":
    out = build()
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} · {out['n_pairs']} pairs · sha256 {out['blind_pairs_sha256'][:12]}")
