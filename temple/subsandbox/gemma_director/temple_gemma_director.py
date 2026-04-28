#!/usr/bin/env python3
"""
TEMPLE_GEMMA_DIRECTOR_SANDBOX — cheap local imagination, gated by HAL+MAYOR.

NON_SOVEREIGN. Lives in temple/subsandbox/. Outputs are never canon, never
ledger entries. The point: spend $0 on local Gemma to propose 10 concepts,
let HAL reject the unsafe/off-brand/incoherent, let MAYOR rank+package the
top N as SHIP_CANDIDATE packets — only THEN spend Higgsfield/Seedance
credits on the survivors.

Pipeline:
  INTENT
    │
    ▼
  HER (Gemma)        — propose N concepts as JSON list
    │
    ▼
  TEMPLE LABEL       — stamp every concept NON_SOVEREIGN_SANDBOX
    │
    ▼
  HAL                — reject unsafe / incoherent / off-brand
    │
    ▼
  MAYOR              — rank by deterministic score, package top K as
                       MAYOR_PACKET_V1 with status READY_FOR_REDUCER
    │
    ▼
  Batch receipt      — GEMMA_DIRECTOR_BATCH_V1 sidecar in runs/

The REDUCER (sovereign) is NOT called from here. This pilot prepares the
case; it never pronounces SHIP.

Use for:
  - prompt variants
  - shot ideas
  - failure-class diagnosis
  - caption drafts
  - seed-pool descriptions

Do NOT use for:
  - canon
  - memory mutation
  - ledger writes
  - final quality judgment
  - safety validation

Usage:
  python3 temple_gemma_director.py "INTENT: a HELEN portrait, copper hair, blue-grey eyes, cyberpunk era"
  python3 temple_gemma_director.py --intent-file intent.txt --n 10 --top 3
  python3 temple_gemma_director.py --model huihui_ai/gemma-4-abliterated:e2b "INTENT..."
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SANDBOX_DIR = Path(__file__).resolve().parent
RUNS_DIR = SANDBOX_DIR / "runs"

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "aura-gemma4:latest"

HER_SYSTEM = (
    "You are a visual concept generator for HELEN OS renders. Given an INTENT, "
    "propose distinct concept variants. Each variant is 1-3 sentences specifying "
    "subject, era/setting, framing/shot, mood. If the subject is HELEN herself, "
    "include at least one identity marker: copper-red hair, blue-grey eyes, "
    "freckles, or fair skin.\n\n"
    "Output ONE JSON array of concept strings. Just the array. Nothing else."
)

# HAL firewall — same patterns as codex_pilot, plus content-level rules below.
HAL_FORBIDDEN_TEXT = [
    "town/ledger_v1.ndjson",
    "oracle_town/kernel",
    "helen_os/governance",
    "helen_os/schemas",
    "GOVERNANCE/CLOSURES",
    "mayor_",
    "rm -rf",
    "shutdown",
]

# HELEN identity markers — at least one required when the concept references HELEN.
HELEN_IDENTITY_MARKERS = [
    "copper", "red hair", "auburn",
    "blue-grey", "blue grey", "grey-blue", "grey blue",
    "freckle",
    "fair skin",
]

# Generic AI-slop signals that subtract from MAYOR's rank score.
SLOP_SIGNALS = [
    "amazing", "stunning", "innovative", "cutting-edge", "revolutionary",
    "breathtaking", "magical", "incredible",
]

# Cinematic terminology that adds to MAYOR's rank score.
CINEMA_SIGNALS = [
    "frame", "lens", "shot", "tripod", "f/", "mm,", "35mm", "85mm", "50mm",
    "tracking", "dolly", "tilt", "pan", "steadicam", "wide", "close-up",
    "medium shot", "establishing", "macro", "depth of field", "bokeh",
    "rim light", "key light", "fill light",
]


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def call_her(intent: str, n: int, model: str) -> tuple[list[str], dict]:
    """Ask Ollama for N concept variants. Returns (concepts, raw_meta)."""
    prompt = (
        f"{HER_SYSTEM}\n\nINTENT: {intent}\n\n"
        f"Generate {n} concept variants. Reply with a JSON array of {n} strings.\n\n"
    )
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.85},
    }).encode()
    req = urllib.request.Request(
        OLLAMA_ENDPOINT, data=body,
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode())
    raw = (data.get("response") or "").strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

    concepts: list[str] = []
    # Strict parse first
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            concepts = [str(x).strip() for x in parsed if str(x).strip()]
        elif isinstance(parsed, dict) and isinstance(parsed.get("concepts"), list):
            concepts = [str(x).strip() for x in parsed["concepts"] if str(x).strip()]
    except json.JSONDecodeError:
        pass
    # Fallback 1: greedy single-array spanning the whole output
    if not concepts:
        m = re.search(r"\[[\s\S]*\]", raw)
        if m:
            try:
                parsed = json.loads(m.group(0))
                if isinstance(parsed, list):
                    concepts = [str(x).strip() for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                pass
    # Fallback 2: handle Gemma's multi-array output [..],[..],[..] — flatten each
    if not concepts:
        for chunk in re.findall(r"\[[^\[\]]*\]", raw):
            try:
                parsed = json.loads(chunk)
                if isinstance(parsed, list):
                    concepts.extend(str(x).strip() for x in parsed if str(x).strip())
            except json.JSONDecodeError:
                continue

    meta = {
        "total_duration_ns": data.get("total_duration"),
        "eval_count": data.get("eval_count"),
        "raw_response_preview": raw[:300],
        "raw_response_len": len(raw),
    }
    return concepts, meta


def hal_check(concept: str, intent: str) -> dict:
    """Reject unsafe / incoherent / off-brand. Returns verdict dict."""
    forbidden = next((p for p in HAL_FORBIDDEN_TEXT if p in concept), None)
    coherent = bool(concept and 20 <= len(concept) <= 600)
    references_helen = any(
        m in intent.lower() or "helen" in concept.lower() for m in ("helen", "herself")
    )
    has_identity_marker = any(m in concept.lower() for m in HELEN_IDENTITY_MARKERS)
    on_brand = (not references_helen) or has_identity_marker

    reasons: list[str] = []
    if forbidden:
        reasons.append(f"forbidden_pattern:{forbidden}")
    if not coherent:
        reasons.append(f"incoherent:length={len(concept)}")
    if not on_brand:
        reasons.append("off_brand:missing_helen_identity_marker")

    verdict = "PASS" if not reasons else "REJECT"
    return {
        "verdict": verdict,
        "reasons": reasons,
        "checks": {
            "forbidden_pattern": forbidden,
            "coherent": coherent,
            "references_helen": references_helen,
            "has_identity_marker": has_identity_marker,
        },
    }


def mayor_rank(concept: str) -> float:
    """Deterministic rank score. Higher = better candidate for SHIP."""
    text = concept.lower()
    score = 5.0  # baseline
    score += sum(1 for w in CINEMA_SIGNALS if w in text)
    score -= 1.5 * sum(1 for w in SLOP_SIGNALS if w in text)
    if any(m in text for m in HELEN_IDENTITY_MARKERS):
        score += 1.0
    # Sweet-spot length: 60-300 chars
    if 60 <= len(concept) <= 300:
        score += 0.5
    elif len(concept) > 500:
        score -= 1.0
    return round(score, 2)


def mayor_packetize(concept: str, rank_score: float, idx: int, intent_sha: str) -> dict:
    """Build a MAYOR_PACKET_V1 for a single concept. status=READY_FOR_REDUCER."""
    return {
        "schema": "MAYOR_PACKET_V1",
        "authority_status": "NON_SOVEREIGN_PACKETIZER",
        "candidate_id": idx,
        "intent_sha256": intent_sha,
        "claim": "concept is canon-candidate for pilot render",
        "obligations": [
            "must produce I2V output within Higgsfield credit budget",
            "must preserve HELEN identity invariants if subject is HELEN",
            "must produce a NON_SOVEREIGN_RENDER_RECEIPT at schema v3 or higher",
            "operator must rate KEEP|REJECT + pipeline_score 1-10 + output_score 1-10",
        ],
        "receipts": [],  # empty until render runs
        "manifest": {
            "concept_text": concept,
            "concept_sha256": sha256_text(concept),
            "rank_score": rank_score,
        },
        "status": "READY_FOR_REDUCER",
    }


def write_batch_receipt(intent: str, model: str, concepts: list[str],
                        her_meta: dict, hal_results: list[dict],
                        ship_candidates: list[dict], rejections: list[dict]) -> Path:
    intent_sha = sha256_text(intent)
    receipt = {
        "schema": "GEMMA_DIRECTOR_BATCH_V1",
        "authority_status": "NON_SOVEREIGN_SANDBOX",
        "generated_at": now_iso(),
        "model": model,
        "intent_text": intent,
        "intent_sha256": intent_sha,
        "concepts_generated": len(concepts),
        "concepts_passed_hal": len(ship_candidates) + (len(concepts) - len(rejections) - len(ship_candidates)),
        "her_meta": her_meta,
        "ship_candidates": ship_candidates,
        "rejections": rejections,
    }
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out = RUNS_DIR / f"{ts}__{intent_sha[:12]}.json"
    out.write_text(json.dumps(receipt, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="TEMPLE Gemma director sandbox — concept proposer + HAL + MAYOR")
    ap.add_argument("intent", nargs="?", help="intent string (or use --intent-file)")
    ap.add_argument("--intent-file", type=Path)
    ap.add_argument("--n", type=int, default=10, help="number of concepts to propose (default 10)")
    ap.add_argument("--top", type=int, default=3, help="top K to packetize as SHIP_CANDIDATEs (default 3)")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"Ollama model (default {DEFAULT_MODEL})")
    args = ap.parse_args()

    intent = args.intent or (args.intent_file.read_text() if args.intent_file else "")
    intent = intent.strip()
    if not intent:
        print("ERROR: provide an intent string or --intent-file", file=sys.stderr)
        return 2
    if args.n < 1 or args.top < 1 or args.top > args.n:
        print(f"ERROR: --n {args.n} / --top {args.top} invalid (need top<=n, both>=1)", file=sys.stderr)
        return 2

    intent_sha = sha256_text(intent)
    print(f"[INTENT] {intent[:120]}{'…' if len(intent) > 120 else ''}")
    print(f"         sha256={intent_sha[:16]}…  model={args.model}  n={args.n}  top={args.top}")

    print(f"[HER]    proposing {args.n} concepts via {args.model}…")
    try:
        concepts, her_meta = call_her(intent, args.n, args.model)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"[HER]    FAIL: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    print(f"[HER]    received {len(concepts)} concept(s) in {her_meta.get('total_duration_ns', 0)/1e9:.1f}s")
    if not concepts:
        print(f"[HER]    raw preview: {her_meta['raw_response_preview']!r}")
        print("[HER]    no parseable concepts — abort", file=sys.stderr)
        path = write_batch_receipt(intent, args.model, [], her_meta, [], [], [])
        print(f"[REC]    {path}")
        return 1

    # HAL pass
    hal_results = []
    survivors: list[tuple[str, dict]] = []
    rejections: list[dict] = []
    for c in concepts:
        verdict = hal_check(c, intent)
        hal_results.append(verdict)
        if verdict["verdict"] == "PASS":
            survivors.append((c, verdict))
        else:
            rejections.append({"concept": c, "reasons": verdict["reasons"]})
    print(f"[HAL]    {len(survivors)} pass, {len(rejections)} reject")
    for r in rejections[:5]:
        print(f"         REJECT: {r['concept'][:60]}… ({', '.join(r['reasons'])})")

    # MAYOR pass: rank + packetize top K
    ranked = sorted(((c, mayor_rank(c)) for c, _ in survivors), key=lambda t: t[1], reverse=True)
    top_k = ranked[: args.top]
    ship_candidates = [
        mayor_packetize(c, score, idx + 1, intent_sha)
        for idx, (c, score) in enumerate(top_k)
    ]
    print(f"[MAYOR]  packaged {len(ship_candidates)} SHIP_CANDIDATE(s)")
    for cand in ship_candidates:
        m = cand["manifest"]
        print(f"         #{cand['candidate_id']}  score={m['rank_score']}  {m['concept_text'][:70]}…")

    receipt_path = write_batch_receipt(
        intent, args.model, concepts, her_meta, hal_results, ship_candidates, rejections,
    )
    print(f"[REC]    {receipt_path}")
    print()
    print("Cheap local imagination complete. Next: operator reviews ship_candidates,")
    print("decides which (if any) to spend Higgsfield/Seedance credits on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
