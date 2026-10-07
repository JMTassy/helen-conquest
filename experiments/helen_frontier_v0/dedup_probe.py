"""Dedup probe — the cheap-rejection tier of the cost rule, measured on the real outbox.

Three tiers, weakest first (AGENTS.md@helen-os 51a4109f: "use the weakest
sufficient mechanism"):

  exact      sha256 of normalised text                       stdlib
  structural template-aware: parse the scanner boilerplate
             and group by source path (same path scanned
             twice = real duplicate; shared template = not)  stdlib
  lexical    word-Jaccard and char-5-gram Jaccard             stdlib
  embedding  google/embeddinggemma-2, text-only, CPU, float32 optional deps

Every tier emits a DEDUP_PROBE_RECEIPT_V0 (authority=false, ledger_effect=none)
with input digest, counts per threshold, timings and the top pairs for manual
review. A similarity score is a 🟨 interpretation — a *candidate* duplicate —
never an observation and never a rejection by itself. Nothing here writes to
the outbox, the corpus or the ledger.

Usage:
  python dedup_probe.py --tier exact structural lexical [--outbox PATH] [--top 25]
  python dedup_probe.py --tier embedding [--dims 768 256] [--model google/embeddinggemma-2]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
DEFAULT_OUTBOX = REPO_ROOT / "temple" / "autoresearch" / "outbox"
RECEIPTS = HERE / "receipts"

LEXICAL_THRESHOLDS = (0.5, 0.6, 0.7, 0.8, 0.9)
EMBED_THRESHOLDS = (0.80, 0.85, 0.90, 0.95)
TEXT_FIELD_ORDER = ("summary", "hypothesis", "title")


# ----------------------------------------------------------------------------- inputs
def packet_text(d: dict[str, Any]) -> tuple[str, str]:
    """Pick the first non-empty text field in TEXT_FIELD_ORDER. Returns (field, text)."""
    for k in TEXT_FIELD_ORDER:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return k, v.strip()
    return "", ""


def load_outbox(outbox: Path) -> list[dict[str, Any]]:
    items = []
    for f in sorted(outbox.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            items.append({"file": f.name, "pid": f.stem, "field": "", "text": "", "error": str(exc)})
            continue
        field, text = packet_text(d)
        items.append({"file": f.name, "pid": d.get("packet_id") or f.stem, "field": field, "text": text,
                      "finding_type": d.get("finding_type")})
    return items


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def inputs_digest(items: list[dict[str, Any]]) -> str:
    h = hashlib.sha256()
    for it in items:
        h.update(it["file"].encode()); h.update(b"\x00"); h.update(normalise(it["text"]).encode()); h.update(b"\x01")
    return h.hexdigest()


# ----------------------------------------------------------------------------- tiers
def tier_exact(items: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[str]] = {}
    for it in items:
        if not it["text"]:
            continue
        key = hashlib.sha256(normalise(it["text"]).encode()).hexdigest()
        buckets.setdefault(key, []).append(it["pid"])
    groups = [sorted(v) for v in buckets.values() if len(v) > 1]
    return {"duplicate_groups": sorted(groups), "packets_in_groups": sum(len(g) for g in groups)}


SCANNER_TEMPLATE = re.compile(r"^Scanner findings in (?P<path>\S+): signals=\[(?P<signals>[^\]]*)\]", re.S)


def tier_structural(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Template-aware grouping. The scanner emits 'Scanner findings in <path>: signals=[...]';
    two such packets share most words by construction. Only the same <path> is a duplicate."""
    by_path: dict[str, list[str]] = {}
    free_form: list[str] = []
    for it in items:
        if not it["text"]:
            continue
        m = SCANNER_TEMPLATE.match(it["text"])
        if m:
            by_path.setdefault(m.group("path"), []).append(it["pid"])
        else:
            free_form.append(it["pid"])
    dup_groups = sorted(sorted(v) for v in by_path.values() if len(v) > 1)
    return {"template_shaped": sum(len(v) for v in by_path.values()), "free_form": len(free_form),
            "distinct_source_paths": len(by_path), "same_path_duplicate_groups": dup_groups,
            "packets_in_duplicate_groups": sum(len(g) for g in dup_groups),
            "note": "template-shaped packets pairwise share ~75% of word tokens by construction; "
                    "lexical similarity between them measures the template, not the distinction"}


def _words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9_]{3,}", normalise(text))}


def _shingles(text: str, n: int = 5) -> set[str]:
    t = normalise(text)
    return {t[i:i + n] for i in range(max(0, len(t) - n + 1))}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


def tier_lexical(items: list[dict[str, Any]], top: int) -> dict[str, Any]:
    texted = [it for it in items if it["text"]]
    W = {it["pid"]: _words(it["text"]) for it in texted}
    S = {it["pid"]: _shingles(it["text"]) for it in texted}
    pairs = []
    for a, b in combinations(texted, 2):
        jw = jaccard(W[a["pid"]], W[b["pid"]]); js = jaccard(S[a["pid"]], S[b["pid"]])
        pairs.append((max(jw, js), jw, js, a["pid"], b["pid"]))
    pairs.sort(reverse=True)
    counts = {str(t): sum(1 for p in pairs if p[0] >= t) for t in LEXICAL_THRESHOLDS}
    return {"pairs_compared": len(pairs), "counts_at_or_above": counts,
            "top_pairs": [{"score": round(p[0], 4), "word_jaccard": round(p[1], 4), "char5_jaccard": round(p[2], 4),
                           "a": p[3], "b": p[4]} for p in pairs[:top]]}


def tier_embedding(items: list[dict[str, Any]], top: int, model_id: str, dims: tuple[int, ...]) -> dict[str, Any]:
    import numpy as np  # noqa: WPS433 - optional dependency
    import torch
    from sentence_transformers import SentenceTransformer

    texted = [it for it in items if it["text"]]
    texts = [it["text"] for it in texted]
    t0 = time.perf_counter()
    model = SentenceTransformer(
        model_id,
        config_kwargs={"vision_config": None, "audio_config": None},   # text-only, 270M
        model_kwargs={"torch_dtype": torch.float32},                   # never float16 (model card §4)
        device="cpu",
    )
    load_s = time.perf_counter() - t0
    revision = None
    try:
        revision = model.model_card_data.base_model_revision  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        pass
    out: dict[str, Any] = {"model": model_id, "revision": revision, "dtype": "float32", "device": "cpu",
                           "prompt_name": "SentenceSimilarity", "load_seconds": round(load_s, 2), "by_dim": {}}
    for dim in dims:
        t1 = time.perf_counter()
        emb = model.encode(texts, prompt_name="SentenceSimilarity", truncate_dim=dim, normalize_embeddings=True,
                           batch_size=16, convert_to_numpy=True)
        enc_s = time.perf_counter() - t1
        sims = emb @ emb.T
        pairs = []
        n = len(texted)
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((float(sims[i, j]), texted[i]["pid"], texted[j]["pid"]))
        pairs.sort(reverse=True)
        counts = {str(t): sum(1 for p in pairs if p[0] >= t) for t in EMBED_THRESHOLDS}
        out["by_dim"][str(dim)] = {
            "encode_seconds": round(enc_s, 2), "ms_per_text": round(1000 * enc_s / max(1, len(texts)), 1),
            "embeddings_sha256": hashlib.sha256(np.ascontiguousarray(emb, dtype=np.float32).tobytes()).hexdigest(),
            "pairs_compared": len(pairs), "counts_at_or_above": counts,
            "top_pairs": [{"cosine": round(p[0], 4), "a": p[1], "b": p[2]} for p in pairs[:top]],
        }
    return out


# ----------------------------------------------------------------------------- receipt
def write_receipt(tier: str, body: dict[str, Any], items: list[dict[str, Any]], wall_s: float, outbox: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snippets = {it["pid"]: {"field": it["field"], "snippet": it["text"][:160], "finding_type": it.get("finding_type")} for it in items}
    receipt = {
        "schema": "DEDUP_PROBE_RECEIPT_V0",
        "authority": False, "sovereign": False, "canon": False, "ledger_effect": "none",
        "meaning": "Scores are candidate duplicates (interpretation). No packet was modified or rejected.",
        "tier": tier,
        "generated_at_utc": stamp,
        "outbox": str(outbox.relative_to(REPO_ROOT)) if outbox.is_relative_to(REPO_ROOT) else str(outbox),
        "packets_total": len(items),
        "packets_with_text": sum(1 for it in items if it["text"]),
        "packets_without_text": sorted(it["pid"] for it in items if not it["text"]),
        "text_field_order": list(TEXT_FIELD_ORDER),
        "inputs_sha256": inputs_digest(items),
        "compute": {"wall_seconds": round(wall_s, 2), "cpu_count": os.cpu_count(), "python": sys.version.split()[0]},
        "result": body,
        "snippets_for_review": snippets,
    }
    RECEIPTS.mkdir(exist_ok=True)
    path = RECEIPTS / f"dedup_probe_{tier}_{stamp}.json"
    path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier", nargs="+", choices=["exact", "structural", "lexical", "embedding"], default=["exact", "structural", "lexical"])
    ap.add_argument("--outbox", type=Path, default=DEFAULT_OUTBOX)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--model", default="google/embeddinggemma-2")
    ap.add_argument("--dims", nargs="+", type=int, default=[768, 256])
    args = ap.parse_args(argv)

    items = load_outbox(args.outbox)
    for tier in args.tier:
        t0 = time.perf_counter()
        if tier == "exact":
            body = tier_exact(items)
        elif tier == "structural":
            body = tier_structural(items)
        elif tier == "lexical":
            body = tier_lexical(items, args.top)
        else:
            body = tier_embedding(items, args.top, args.model, tuple(args.dims))
        path = write_receipt(tier, body, items, time.perf_counter() - t0, args.outbox)
        print(f"[{tier}] receipt → {path.relative_to(REPO_ROOT)}")
        if tier == "exact":
            print(f"  exact duplicate groups: {len(body['duplicate_groups'])} · packets in groups: {body['packets_in_groups']}")
        elif tier == "structural":
            print(f"  template-shaped: {body['template_shaped']} · free-form: {body['free_form']} · "
                  f"same-path duplicate groups: {len(body['same_path_duplicate_groups'])}")
        elif tier == "lexical":
            print(f"  pairs: {body['pairs_compared']} · at/above: {body['counts_at_or_above']}")
        else:
            for dim, r in body["by_dim"].items():
                print(f"  dim {dim}: {r['ms_per_text']} ms/text · at/above: {r['counts_at_or_above']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
