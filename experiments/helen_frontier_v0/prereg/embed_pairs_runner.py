"""Embedding runner for the preregistered G2 probe. Needs network to huggingface.co once, then torch + sentence-transformers.

Reads ONLY pairs_blind.json (no labels exist in it). Writes scores.json with an OBSERVED block (measured facts) and an
ASSERTED block (configured values). Never consults equivalence_pairs.json. Never writes outside prereg/.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PROTO = json.loads((HERE / "PREREG_G2_EMBEDDING_V0.json").read_text(encoding="utf-8"))
BLIND = HERE / "pairs_blind.json"
OUT = HERE / "scores.json"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    import numpy as np
    import torch
    import sentence_transformers
    from sentence_transformers import SentenceTransformer

    blind = json.loads(BLIND.read_text(encoding="utf-8"))
    assert "label" not in json.dumps(blind), "runner must never see labels"
    m = PROTO["model"]
    t0 = time.perf_counter()
    model = SentenceTransformer(m["configured_id"], config_kwargs=m["loading"]["config_kwargs"],
                                model_kwargs={"torch_dtype": torch.float32}, device="cpu")
    load_s = time.perf_counter() - t0

    # OBSERVED: resolve the snapshot actually loaded, from the cache path, not from the model's say-so
    from huggingface_hub import constants as hfc
    snap_root = Path(hfc.HF_HUB_CACHE) / ("models--" + m["configured_id"].replace("/", "--")) / "snapshots"
    snaps = sorted(snap_root.glob("*"), key=lambda p: p.stat().st_mtime) if snap_root.exists() else []
    snap = snaps[-1] if snaps else None
    st = (snap / "model.safetensors") if snap else None
    observed = {
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "sentence_transformers_version": sentence_transformers.__version__,
        "resolved_snapshot_path": str(snap) if snap else None,
        "resolved_snapshot_commit": snap.name if snap else None,
        "model_safetensors_bytes": st.stat().st_size if st and st.exists() else None,
        "model_safetensors_sha256": sha256_file(st.resolve()) if st and st.exists() else None,
        "expected_bytes_match": (st.stat().st_size == m["expected_model_safetensors_bytes"]) if st and st.exists() else None,
        "blind_pairs_sha256": blind["blind_pairs_sha256"],
        "cpu_count": os.cpu_count(),
        "git_head": subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
        "load_seconds": round(load_s, 2),
    }
    texts = []
    for p in blind["pairs"]:
        texts += [p["a_text"], p["b_text"]]
    scores = {}
    for dim in (m["truncate_dim_primary"], m["truncate_dim_secondary_reported_only"]):
        t1 = time.perf_counter()
        emb = model.encode(texts, prompt_name="SentenceSimilarity", truncate_dim=dim, normalize_embeddings=True,
                           batch_size=16, convert_to_numpy=True)
        observed[f"encode_seconds_{dim}"] = round(time.perf_counter() - t1, 2)
        observed[f"embeddings_sha256_{dim}"] = hashlib.sha256(np.ascontiguousarray(emb, dtype=np.float32).tobytes()).hexdigest()
        scores[str(dim)] = [float(np.dot(emb[2 * i], emb[2 * i + 1])) for i in range(len(blind["pairs"]))]
    out = {
        "schema": "G2_EMBEDDING_SCORES_V0", "authority": False, "ledger_effect": "none",
        "prereg": "PREREG_G2_EMBEDDING_V0.json",
        "asserted": {"configured_id": m["configured_id"], "runtime_attestation": "UNVERIFIED — host does not attest executed weights"},
        "observed": observed,
        "pairs": [{"pair_index": p["pair_index"], "a": p["a"], "b": p["b"],
                   "score_768": scores["768"][i], "score_256": scores["256"][i]} for i, p in enumerate(blind["pairs"])],
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} · snapshot {observed['resolved_snapshot_commit']} · bytes match {observed['expected_bytes_match']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
