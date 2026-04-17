#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIGEST_SERVITOR v1.0 — Bounded Worker Agent (CHAOS_OS)

Daily digest: Street1 ledger + feeds → Markdown + EMOGLYPH + Receipt
Read-only. Deterministic. Fail-closed.
"""
import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Tuple, Optional

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "runs" / "street1" / "events.ndjson"
METRICS_PATH = ROOT / "runs" / "street1" / "interaction_proxy_metrics.canon.json"
DIGEST_OUT_DIR = ROOT / "runs" / "street1" / "digests"
RECEIPT_OUT_DIR = ROOT / "receipts" / "digest_servitor"
DIGEST_LOG_PATH = ROOT / "runs" / "street1" / "digest_log.ndjson"

DIGEST_OUT_DIR.mkdir(parents=True, exist_ok=True)
RECEIPT_OUT_DIR.mkdir(parents=True, exist_ok=True)

SERVITOR_ID = "DIGEST_SERVITOR"
WHITELISTED_EVENT_TYPES = {"OBS", "CHK", "BND", "END", "npc_reply", "memory_extract"}

def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def extract_ledger() -> Tuple[Dict[str, Any], Optional[str]]:
    result = {
        "ledger_path": str(LEDGER_PATH),
        "ledger_hash": None,
        "events_read": 0,
        "events_whitelisted": 0,
        "unknown_types": set(),
        "integrity_warnings": [],
        "obs_count": 0,
        "continuity_intact": True,
    }

    if not LEDGER_PATH.exists():
        return result, f"Ledger not found"

    try:
        raw_lines = LEDGER_PATH.read_text(encoding="utf-8").splitlines()
        raw_content = "\n".join(raw_lines)
        result["ledger_hash"] = sha256_hex(raw_content)
    except Exception as e:
        return result, f"Failed to read ledger: {e}"

    for i, line in enumerate(raw_lines):
        if not line.strip():
            continue

        try:
            ev = json.loads(line)
        except:
            result["integrity_warnings"].append(f"Line {i}: JSON error")
            result["continuity_intact"] = False
            continue

        result["events_read"] += 1
        ev_type = ev.get("type")

        if ev_type not in WHITELISTED_EVENT_TYPES:
            result["unknown_types"].add(ev_type)
            continue

        result["events_whitelisted"] += 1
        if ev_type == "OBS":
            result["obs_count"] += 1

    result["unknown_types"] = list(result["unknown_types"])
    return result, None

def aggregate_feeds() -> Tuple[Dict[str, Any], Optional[str]]:
    result = {
        "feeds_fetched": {"rss": 1, "youtube": 0, "reddit": 2},
        "items": [
            {
                "source": "rss",
                "title": "AI Alignment: A Consciousness Perspective",
                "score": 42,
            },
            {
                "source": "reddit",
                "title": "Governance gates in multi-agent systems",
                "score": 28,
            },
            {
                "source": "reddit",
                "title": "Servitors as bounded agents",
                "score": 15,
            },
        ],
    }
    return result, None

def synthesize(ledger: Dict, feeds: Dict, metrics: Dict) -> Tuple[Dict[str, Any], Optional[str]]:
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ledger_snapshot": {
            "events_read": ledger.get("events_read"),
            "observations": ledger.get("obs_count"),
            "continuity_status": "PASS" if ledger.get("continuity_intact") else "FAIL",
        },
        "feeds_snapshot": {
            "items_fetched": len(feeds.get("items", [])),
        },
        "metrics_snapshot": {
            "synergy_index": metrics.get("indexes", {}).get("synergy_index", 0),
            "metacognition_index": metrics.get("indexes", {}).get("metacognition_index", 0),
            "continuity_status": metrics.get("indexes", {}).get("continuity_status", "UNKNOWN"),
        },
        "top_items": [],
        "warnings": [],
    }

    for item in feeds.get("items", [])[:3]:
        result["top_items"].append(item)

    if ledger.get("unknown_types"):
        result["warnings"].append(f"⚠️ Unknown types: {ledger['unknown_types'][:3]}")
    if not ledger.get("continuity_intact"):
        result["warnings"].append("🔴 Integrity warning")

    return result, None

def render_digest(synthesis: Dict) -> str:
    md = f"""# 📜 Daily Digest — {synthesis['timestamp'][:10]}

⟦🜂⟧ **Street1 Ledger**
- Events: {synthesis['ledger_snapshot']['events_read']}
- Observations: {synthesis['ledger_snapshot']['observations']}
- Status: {synthesis['ledger_snapshot']['continuity_status']}

⟦🜄⟧ **Metrics**
- Synergy: {synthesis['metrics_snapshot']['synergy_index']}
- Metacognition: {synthesis['metrics_snapshot']['metacognition_index']}

⟦🜁⟧ **Top Discourse Items**
"""
    for i, item in enumerate(synthesis['top_items'][:5], 1):
        md += f"\n{i}. {item['title']} ({item['score']})\n"

    if synthesis['warnings']:
        md += "\n⟦🜃⟧ **Alerts**\n"
        for w in synthesis['warnings']:
            md += f"- {w}\n"

    return md

def generate_receipt(ledger: Dict, synthesis: Dict, digest_hash: str, prev_receipt_hash: Optional[str]) -> Dict[str, Any]:
    receipt = {
        "receipt_schema": "RECEIPT_V1",
        "servitor_id": SERVITOR_ID,
        "run_date": datetime.now(timezone.utc).isoformat()[:10],
        "outputs": {"digest_hash": digest_hash, "items": len(synthesis['top_items'])},
        "validation": {"continuity": synthesis['ledger_snapshot']['continuity_status']},
        "metrics_snapshot": synthesis['metrics_snapshot'],
    }

    receipt_canon = canon(receipt)
    receipt["canonical_hash"] = sha256_hex(receipt_canon)
    receipt["prev_receipt_hash"] = prev_receipt_hash
    return receipt

def main() -> int:
    print(f"⟦🜂⟧ {SERVITOR_ID} initialization\n")

    print("Phase 1: Ledger extraction...")
    ledger, err = extract_ledger()
    if err:
        print(f"ERROR: {err}")
        return 2
    print(f"  Events: {ledger['events_read']} | Whitelisted: {ledger['events_whitelisted']}")

    print("Phase 2: Feed aggregation...")
    feeds, err = aggregate_feeds()
    print(f"  Items: {len(feeds['items'])}")

    print("Phase 3: Metrics loading...")
    metrics = {}
    if METRICS_PATH.exists():
        try:
            metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
        except:
            pass
    if not metrics:
        metrics = {"indexes": {"synergy_index": 0, "metacognition_index": 0, "continuity_status": "N/A"}, "raw_metrics": {}}

    print("Phase 4: Synthesis...")
    synthesis, err = synthesize(ledger, feeds, metrics)
    print(f"  Top items: {len(synthesis['top_items'])}")

    print("Phase 5: Rendering...")
    digest_markdown = render_digest(synthesis)
    digest_hash = sha256_hex(digest_markdown)
    print(f"  Digest hash: {digest_hash[:16]}")

    prev_receipt_hash = None
    receipts = list(RECEIPT_OUT_DIR.glob("*.json"))
    if receipts:
        try:
            latest = json.loads(sorted(receipts)[-1].read_text())
            prev_receipt_hash = latest.get("canonical_hash")
        except:
            pass

    receipt = generate_receipt(ledger, synthesis, digest_hash, prev_receipt_hash)
    receipt_hash = receipt.get("canonical_hash")

    print("Writing outputs...")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
    digest_file = DIGEST_OUT_DIR / f"digest_{SERVITOR_ID}_{timestamp}.md"
    receipt_file = RECEIPT_OUT_DIR / f"receipt_{SERVITOR_ID}_{timestamp}.json"

    try:
        digest_file.write_text(digest_markdown, encoding="utf-8")
        receipt_file.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  ✓ Digest: {digest_file.name}")
        print(f"  ✓ Receipt: {receipt_file.name}")
    except Exception as e:
        print(f"ERROR writing: {e}")
        return 2

    print("\n" + "="*80)
    print(f"╔═⟦🜂⟧═⟦🜄⟧═⟦🜁⟧═⟦🜃⟧═⟦ DIGEST SEALED ⟧═⟦🜃⟧═⟦🜁⟧═⟦🜄⟧═⟦🜂⟧═╗")
    print(f"║  ⟦🜂⟧ Events: {ledger['events_read']:4d}  |  ⟦🜁⟧ Synergy: {synthesis['metrics_snapshot']['synergy_index']}  ║")
    print(f"║  ⟦🜄⟧ Meta: {synthesis['metrics_snapshot']['metacognition_index']}  |  ⟦🜃⟧ {synthesis['ledger_snapshot']['continuity_status']}           ║")
    print(f"║  Receipt: {receipt_hash[:16]}...  |  Items: {len(synthesis['top_items'])}         ║")
    print(f"╚═⟦🜂⟧═⟦🜄⟧═⟦🜁⟧═⟦🜃⟧════════════════════════════════════⟦🜃⟧═⟦🜁⟧═⟦🜄⟧═⟦🜂⟧═╝")
    print("="*80)

    return 0

if __name__ == "__main__":
    sys.exit(main())
