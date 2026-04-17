#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HELEN / STREET1 — PROXY METRICS ANALYZER (Hardened V2)
- Verifies hash chain cryptographically (recompute)
- Canonical JSON hashing (sorted keys)
- Fail-closed on ledger invalidity
- Schema-pinned event types
- Deterministic report canonicalization + sha outputs
"""

import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Set


ROOT = Path(__file__).resolve().parents[1]
EVENTS_PATH = ROOT / "runs" / "street1" / "events.ndjson"
OUT_DIR = ROOT / "runs" / "street1"
OUT_PRETTY = OUT_DIR / "interaction_proxy_metrics.json"
OUT_CANON = OUT_DIR / "interaction_proxy_metrics.canon.json"
OUT_SHA = OUT_DIR / "interaction_proxy_metrics.sha256"


# =========================
# Canon + Hash (deterministic)
# =========================

def canon(obj: Any) -> str:
    # Minimal deterministic canonical JSON:
    # - sort_keys=True
    # - separators no whitespace
    # - ensure_ascii=False (stable UTF-8)
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# =========================
# Hash-chain spec (mechanical)
# =========================
# Recommended chain rule:
# expected_hash = sha256(canon({"prev_hash": prev_hash, "event": event_without_hash_and_prev}))
#
# This makes:
# - reordering detectable
# - payload tampering detectable
# - prev_hash part of signed material

def compute_expected_hash(event_without_hash_and_prev: Dict[str, Any], prev_hash: str) -> str:
    payload = {"prev_hash": prev_hash, "event": event_without_hash_and_prev}
    return sha256_hex(canon(payload))


def verify_event_hash(ev_full: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Returns (ok, reason). Does NOT mutate input.
    """
    if "hash" not in ev_full or "prev_hash" not in ev_full:
        return False, "missing hash/prev_hash"

    ev_hash = ev_full.get("hash")
    ev_prev = ev_full.get("prev_hash")
    if not isinstance(ev_hash, str) or not isinstance(ev_prev, str):
        return False, "hash/prev_hash not strings"

    ev_wo = dict(ev_full)
    ev_wo.pop("hash", None)
    ev_wo.pop("prev_hash", None)

    expected = compute_expected_hash(ev_wo, ev_prev)
    if expected != ev_hash:
        return False, f"hash mismatch expected={expected[:12]} got={ev_hash[:12]}"
    return True, "ok"


# =========================
# Schema pinning
# =========================
# You can extend these, but do it intentionally.
KNOWN_TYPES: Set[str] = {
    "run_start",
    "run_end",
    "ws_in",                 # websocket input
    "npc_reply",
    "npc_npc",
    "npc_npc_trigger",
    "memory_extract",
    "fact_deprecated",
    "correction",
    # Oracle module (new)
    "oracle_forecast",
    # Human control gate (new)
    "human_review_request",
    "human_vote",
    "human_verdict",
    "action_commit",
    "oracle_dependency_alert",
}

# Minimal ledger validity: must have start & end
REQUIRED_TYPES: Set[str] = {"run_start", "run_end"}


# =========================
# Metrics computation
# =========================

def analyze_events(lines: List[str]) -> Dict[str, Any]:
    metrics: Dict[str, Any] = {
        "turns_completed": 0,
        "continuity_intact": True,
        "gwt_broadcast_score": 0,
        "metacognition_events": 0,
        "synergy_npc_triggers": 0,
        "total_facts_extracted": 0,
        "broken_hashes": [],
        "schema_errors": [],
        "unknown_event_types": [],
        "missing_required_types": [],
    }

    last_hash: Optional[str] = None
    extracted_facts_pool: Set[str] = set()
    seen_types: Set[str] = set()
    unknown_types: Set[str] = set()

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        try:
            ev_full = json.loads(line)
        except json.JSONDecodeError:
            metrics["continuity_intact"] = False
            metrics["broken_hashes"].append(f"Line {i}: json decode error")
            continue

        # Basic shape check
        if not isinstance(ev_full, dict):
            metrics["continuity_intact"] = False
            metrics["schema_errors"].append(f"Line {i}: event is not object")
            continue

        # (1) Continuity check (link)
        ev_hash = ev_full.get("hash")
        ev_prev = ev_full.get("prev_hash")

        # Fail-closed if missing
        if ev_hash is None or ev_prev is None:
            metrics["continuity_intact"] = False
            metrics["broken_hashes"].append(f"Line {i}: missing hash/prev_hash")
            continue

        if last_hash is not None and ev_prev != last_hash:
            metrics["continuity_intact"] = False
            metrics["broken_hashes"].append(f"Line {i}: prev_hash mismatch")

        # (2) Continuity check (recompute hash)
        ok, reason = verify_event_hash(ev_full)
        if not ok:
            metrics["continuity_intact"] = False
            metrics["broken_hashes"].append(f"Line {i}: {reason}")

        # Update last_hash only if hash is a string
        if isinstance(ev_hash, str):
            last_hash = ev_hash
        else:
            metrics["continuity_intact"] = False
            metrics["broken_hashes"].append(f"Line {i}: hash not string")
            continue

        # (3) Schema pin
        ev_type = ev_full.get("type")
        if isinstance(ev_type, str):
            seen_types.add(ev_type)
            if ev_type not in KNOWN_TYPES:
                unknown_types.add(ev_type)
        else:
            metrics["schema_errors"].append(f"Line {i}: missing/invalid type field")
            continue

        # (4) TURN COUNT
        # Support both your original websocket measure AND a fallback if ws_in absent.
        if ev_type == "ws_in" and ev_full.get("msg_type") == "C_CHAT_SEND":
            metrics["turns_completed"] += 1

        # Fallback: count user-turn-like events if you log them differently
        if ev_type == "user_msg":
            metrics["turns_completed"] += 1

        # (5) METACOGNITION (Facts & Deprecation)
        if ev_type == "memory_extract":
            facts = ev_full.get("facts", [])
            if isinstance(facts, list):
                metrics["total_facts_extracted"] += len(facts)
                for f in facts:
                    if isinstance(f, str):
                        extracted_facts_pool.add(f)
            else:
                metrics["schema_errors"].append(f"Line {i}: memory_extract facts not list")

        if ev_type in ("fact_deprecated", "correction"):
            metrics["metacognition_events"] += 1

        # (6) GWT (Broadcast / Reuse)
        # NOTE: This is intentionally a heuristic. Stronger approach: emit FACT::<hash> tokens.
        if ev_type == "npc_reply":
            text = ev_full.get("text", "")
            if isinstance(text, str):
                tl = text.lower()
                used_facts = sum(1 for f in extracted_facts_pool if isinstance(f, str) and f.lower()[:10] in tl)
                metrics["gwt_broadcast_score"] += used_facts
            else:
                metrics["schema_errors"].append(f"Line {i}: npc_reply text not string")

        # (7) SYNERGY
        if ev_type in ("npc_npc", "npc_npc_trigger"):
            metrics["synergy_npc_triggers"] += 1

    # Final schema results
    if unknown_types:
        metrics["unknown_event_types"] = sorted(list(unknown_types))
        metrics["schema_errors"].append(f"Unknown event types present: {sorted(list(unknown_types))}")

    missing = REQUIRED_TYPES - seen_types
    if missing:
        metrics["missing_required_types"] = sorted(list(missing))
        metrics["schema_errors"].append(f"Missing required types: {sorted(list(missing))}")

    return metrics


# =========================
# Main (fail-closed + deterministic outputs)
# =========================

def main() -> int:
    if not EVENTS_PATH.exists():
        print(f"[HAL] Missing ledger at {EVENTS_PATH}")
        return 2

    raw_lines = EVENTS_PATH.read_text(encoding="utf-8").splitlines()
    metrics = analyze_events(raw_lines)

    # Fail-closed policy:
    # - continuity must be intact
    # - no schema errors
    if (not metrics["continuity_intact"]) or metrics["schema_errors"]:
        status = "FAIL"
    else:
        status = "PASS"

    turns = metrics["turns_completed"]
    turns_safe = max(1, turns)

    synergy_index = metrics["synergy_npc_triggers"] / turns_safe
    meta_index = metrics["metacognition_events"]

    report = {
        "schema_version": "INTERACTION_PROXY_METRICS_V2",
        "inputs": {
            "events_path": str(EVENTS_PATH),
            "events_lines": len(raw_lines),
            "hash_spec": "sha256(canon({prev_hash,event_without_hash_prev}))",
            "known_types": sorted(list(KNOWN_TYPES)),
            "required_types": sorted(list(REQUIRED_TYPES)),
        },
        "raw_metrics": metrics,
        "indexes": {
            "synergy_index": round(synergy_index, 3),
            "metacognition_index": meta_index,
            "continuity_status": "PASS" if metrics["continuity_intact"] else "FAIL",
            "overall_status": status,
        },
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Write pretty + canonical + sha
    OUT_PRETTY.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    canon_report = canon(report)
    OUT_CANON.write_text(canon_report + "\n", encoding="utf-8")
    OUT_SHA.write_text(sha256_hex(canon_report) + "\n", encoding="utf-8")

    # Console summary (deterministic)
    print("⎈ HAL — PROXY METRICS COMPUTED ⎈")
    print(f" Turns            : {turns}")
    print(f" Continuity       : {'✅ INTACT' if metrics['continuity_intact'] else '❌ BROKEN'}")
    print(f" Schema errors    : {len(metrics['schema_errors'])}")
    print(f" Unknown types    : {metrics.get('unknown_event_types', [])}")
    print(f" GWT Spread       : {metrics['gwt_broadcast_score']} fact-mentions")
    print(f" Synergy (NPC-NPC): {metrics['synergy_npc_triggers']} cross-triggers")
    print(f" Metacognition    : {metrics['metacognition_events']} self-corrections")
    print(f" Overall          : {status}")
    print(f" Report SHA       : {OUT_SHA.read_text(encoding='utf-8').strip()}")

    # Exit non-zero on FAIL so CI blocks
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
